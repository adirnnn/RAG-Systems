# Agente de FAQs Parachute S.A. (CC3116)

Este repo tiene dos entregas:

* Hoja de trabajo #3 (RAG simple, Node.js): raiz del repo, descrita abajo.
* Hoja de trabajo #4 (Herramientas, pgvector + function calling, Python): carpeta
  [`hdt4/`](hdt4/), ver [`hdt4/README.md`](hdt4/README.md). Resumen y pasos de
  infraestructura mas abajo en la seccion "Hoja de trabajo #4".

---

# Hoja de trabajo #3: Agente de FAQs (RAG simple)

Demo de terminal para la Hoja de trabajo #3 (CC3116, Sistemas RAG).

Un agente de preguntas frecuentes para la empresa Parachute S.A. que responde
solo con base en el archivo `FAQs_Parachute_SA_Guatemala_2026.txt`. Si la pregunta
no está cubierta por el documento, el agente lo admite en lugar de inventar una
respuesta.

## Arquitectura RAG (la más simple posible)

```
FAQs_Parachute_SA_Guatemala_2026.txt   (archivo en el file system)
        |
        v
[ retrieval ]   loadFaqContext() lee el archivo completo con fs.readFileSync
        |
        v
[ augmented ]   se inyecta todo el texto dentro del prompt de sistema
        |        (bloque <FAQS> ... </FAQS> mas la regla "responde solo con esto")
        v
[ generation ]  Groq, endpoint compatible con la API de OpenAI
        |        chat.completions.create({ model, messages })
        v
respuesta en la terminal
```

No hay embeddings, chunking ni base de datos vectorial: el corpus es pequeño, así
que se inyecta íntegro en el contexto. El historial de mensajes se guarda en
memoria durante la sesión para permitir preguntas de seguimiento.

* SDK: [`openai`](https://www.npmjs.com/package/openai) para Node.js, apuntado al
  endpoint de Groq con `baseURL`.
* Proveedor del modelo: [Groq](https://console.groq.com), tier gratuito y sin tarjeta.

## Requisitos

* Node.js 20.12 o superior (se usa `process.loadEnvFile` para leer el `.env`).
* Una API Key gratuita de Groq: <https://console.groq.com/keys>

## Instalación

```bash
npm install
copy .env.example .env
```

En Linux o macOS usa `cp .env.example .env` en lugar de `copy`.

Edita `.env` y coloca tu API Key:

```
GROQ_API_KEY=gsk_tu_api_key_aqui
GROQ_BASE_URL=https://api.groq.com/openai/v1
GROQ_MODEL=openai/gpt-oss-120b
```

El archivo `.env` está en `.gitignore`. Nunca subas tu API Key al repositorio.

## Uso

```bash
npm start
```

Se abre un loop interactivo. Escribe tus preguntas; para salir escribe `Bye` o
presiona `Ctrl+C`.

### Ejemplos

Preguntas dentro del documento:

* `¿Cuándo y dónde es el evento?`
* `¿Cuál es el límite de peso?`
* `¿Qué incluye el Paquete VIP?`
* `¿Puedo llevar mi GoPro?`

Pregunta fuera del documento (el agente admite que no sabe):

* `¿Hay estacionamiento en el lugar?`
* `¿Cuánto cuesta el Salto Tándem Básico?`

## Estructura

* `src/index.js`: punto de entrada. Carga el `.env`, arma el prompt de sistema,
  crea el cliente de Groq y corre el loop de preguntas y respuestas.
* `src/faq.js`: función `loadFaqContext()`, lee y valida el archivo de FAQs (paso
  de retrieval).
* `.env.example`: plantilla de variables de entorno.
* `FAQs_Parachute_SA_Guatemala_2026.txt`: base de conocimiento, la provee el cliente.

## Video

Video corto sin voz mostrando el funcionamiento (preguntas respondidas desde el
archivo, una pregunta fuera del archivo y la salida con `Bye` o `Ctrl+C`):

<https://youtu.be/rmmoUr4DaP4>

---

# Hoja de trabajo #4: Herramientas (pgvector + function calling)

Version mas robusta del agente. La base de conocimientos es ahora un dump grande
(`Corpus_FAQs_Parachute_SA_2026.txt`, 120 fichas) que vive en PostgreSQL con la
extension pgvector. El agente ya no recibe todo el texto en el prompt: consulta la
base por medio de una herramienta (function calling) registrada en el SDK.

Todo el codigo de HDT4 esta en [`hdt4/`](hdt4/). Doc detallada en
[`hdt4/README.md`](hdt4/README.md).

## Arquitectura

```
Corpus_FAQs_Parachute_SA_2026.txt
        |  hdt4/cargar.py  (una vez)
        v
parseo de 120 fichas  ->  sentence-transformers (MiniLM multilingue, 384 dimensiones)
        v
tabla faqs(..., embedding vector(384))  en PostgreSQL + pgvector, indice HNSW coseno
        |
        |  hdt4/agente.py  (loop de terminal)
        v
usuario pregunta  ->  LLM (Groq) llama la tool buscar_en_faqs(consulta, k)
        v
la tool embebe la consulta y hace  ORDER BY embedding <=> consulta  LIMIT k
        v
si el mejor score < UMBRAL  ->  el agente admite que no sabe
```

## Dos programas

* `hdt4/cargar.py`: llena la tabla de PostgreSQL con los embeddings del corpus.
* `hdt4/agente.py`: agente de terminal que responde usando la herramienta.

## Como inicializar la infraestructura

Requisitos: Docker con `docker compose`, Python 3.11 o superior, una API Key
gratuita de Groq (<https://console.groq.com/keys>). La primera corrida baja
`torch` y el modelo de embeddings (~200 MB).

```bash
cd hdt4

# 1. levantar PostgreSQL con pgvector (contenedor parachute_pgvector, puerto 5434)
docker compose up -d
docker compose ps

# 2. entorno de python
python -m venv .venv
# Windows PowerShell:  .venv\Scripts\Activate.ps1
# Linux o macOS:       source .venv/bin/activate
pip install -r requirements.txt

# 3. configuracion
copy .env.example .env
# editar .env y pegar GROQ_API_KEY (se puede copiar del .env de la raiz)

# 4. cargar los embeddings a la base
python cargar.py
# -> listo: 120 FAQs cargadas en la tabla faqs

# 5. correr el agente
python agente.py
```

Para salir del agente: `Bye` o `Ctrl+C`. Para apagar la base: `docker compose
stop` (o `docker compose down -v` para borrar tambien el volumen).

## Video

Pendiente de grabar: demostracion sin voz de `python cargar.py` llenando la tabla
y luego `python agente.py` respondiendo preguntas del corpus y admitiendo una
pregunta fuera de dominio.
