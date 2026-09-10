# HDT4 Herramientas: RAG con pgvector y function calling

Version mas robusta del agente de FAQs de Parachute S.A. Ahora la base de
conocimientos (`Corpus_FAQs_Parachute_SA_2026.txt`, 120 fichas) vive en
PostgreSQL con la extension pgvector, y el agente la consulta por medio de una
herramienta registrada en el SDK (function calling), no metiendo todo el texto al
prompt.

Se entregan dos programas:

* `cargar.py`: parsea el corpus, calcula los embeddings y llena la tabla.
* `agente.py`: loop de terminal que responde preguntas usando la herramienta.

## Arquitectura

```
Corpus_FAQs_Parachute_SA_2026.txt
        |  cargar.py  (una vez)
        v
parseo de 120 fichas  ->  sentence-transformers (MiniLM multilingue, 384 dimensiones)
        v
tabla faqs(id, categoria, pregunta, respuesta, metadata jsonb, embedding vector(384))
en PostgreSQL + pgvector, con indice HNSW y distancia coseno
        |
        |  agente.py  (loop)
        v
el usuario pregunta  ->  el LLM (Groq) llama la tool buscar_en_faqs(consulta, k)
        v
la tool embebe la consulta y hace  ORDER BY embedding <=> consulta  LIMIT k
        v
si el mejor score < UMBRAL_SIMILITUD  ->  SIN_RESULTADOS
        v
el LLM redacta la respuesta solo con esas fichas, o admite que no sabe
```

La herramienta `buscar_en_faqs` es la unica fuente de informacion del agente. Si
no hay ninguna ficha por encima del umbral de similitud, el agente responde que no
tiene esa informacion. El loop sigue hasta que se escribe `Bye` o se presiona
`Ctrl+C`.

## Requisitos

* Docker con `docker compose` (o un PostgreSQL con pgvector propio).
* Python 3.11 o superior.
* Una API Key gratuita de Groq: <https://console.groq.com/keys>
* Salida a internet la primera vez (baja `torch` y el modelo de embeddings, mas o
  menos 200 MB en total).

## Como inicializar la infraestructura

Desde la carpeta `hdt4/`:

```bash
docker compose up -d
```

Eso levanta el contenedor `parachute_pgvector` con la imagen
`pgvector/pgvector:pg16`, expuesto en el puerto `5434` (el `5433` ya lo usa otro
contenedor en la maquina de desarrollo). El healthcheck marca `healthy` cuando la
base acepta conexiones:

```bash
docker compose ps
```

Para apagar la base sin borrar datos: `docker compose stop`. Para borrarla del
todo (incluye el volumen): `docker compose down -v`.

## Instalacion de dependencias

```bash
python -m venv .venv
```

Activar el entorno:

* Windows PowerShell: `.venv\Scripts\Activate.ps1`
* Linux o macOS: `source .venv/bin/activate`

```bash
pip install -r requirements.txt
```

## Configuracion

```bash
copy .env.example .env
```

En Linux o macOS usa `cp .env.example .env`.

Edita `.env` y pon tu `GROQ_API_KEY` (puedes copiarla del `.env` de la raiz del
repo, que se creo en la HDT3). El resto de valores ya vienen listos para la base
que levanta `docker compose`:

```
DATABASE_URL=postgresql://parachute:parachute@localhost:5434/parachute
GROQ_API_KEY=gsk_tu_api_key_aqui
GROQ_BASE_URL=https://api.groq.com/openai/v1
GROQ_MODEL=openai/gpt-oss-120b
EMBEDDING_MODEL=paraphrase-multilingual-MiniLM-L12-v2
CORPUS_FILE=../Corpus_FAQs_Parachute_SA_2026.txt
UMBRAL_SIMILITUD=0.35
```

El `.env` esta en `.gitignore`, nunca se sube.

## Uso

Primero el loader (llena la tabla, se puede correr las veces que quieras, hace
`TRUNCATE` antes de insertar):

```bash
python cargar.py
```

Salida esperada: `listo: 120 FAQs cargadas en la tabla faqs`.

Comprobacion rapida en la base:

```bash
docker compose exec db psql -U parachute -c "select count(*) from faqs;"
```

Despues el agente:

```bash
python agente.py
```

Se abre el loop. Escribe preguntas; para salir escribe `Bye` o presiona `Ctrl+C`.

### Ejemplos

Preguntas que estan en el corpus:

* `¿Hay parqueo disponible en el lugar del evento?`
* `¿A que hora abren las instalaciones?`
* `¿Se realizan saltos nocturnos?`
* `¿Que pasa si la pista de aterrizaje se inunda?`

Pregunta fuera del corpus (el agente admite que no sabe):

* `¿Quien gano el mundial de futbol 2022?`

## Estructura

* `docker-compose.yml`: define la base PostgreSQL con pgvector.
* `requirements.txt`: dependencias de Python.
* `db.py`: utilidades compartidas (entorno, conexion, esquema, modelo de embeddings).
* `cargar.py`: programa de carga.
* `agente.py`: agente de terminal con la herramienta `buscar_en_faqs`.
* `.env.example`: plantilla de variables de entorno.

## Notas de diseno

* Cada ficha del corpus es un chunk por si sola (son cortas y ya vienen
  separadas), asi que se usa una fila por FAQ.
* El vector se calcula sobre el texto de la `PREGUNTA`. La similitud pregunta
  contra pregunta da mejores matches que meter la respuesta, que en este corpus
  es texto repetido.
* El modelo de embeddings es `paraphrase-multilingual-MiniLM-L12-v2` (384
  dimensiones, corre local en CPU). Se probo primero con `all-MiniLM-L6-v2`, el
  que sugiere la hoja, pero es casi solo ingles y en espanol se enganchaba a
  frases sueltas como "el dia del evento" en vez del significado; la variante
  multilingue arregla eso sin cambiar el tamano del vector. Se puede cambiar con
  la variable `EMBEDDING_MODEL`.
* `UMBRAL_SIMILITUD` (similitud coseno, de 0 a 1) es un filtro grueso en la
  herramienta. Con el modelo multilingue las preguntas del dominio quedan sobre
  0.45 y las ajenas por debajo de 0.25, asi que `0.35` separa bien. La decision
  final de si una ficha responde o no la toma el agente leyendo las fichas.
* La primera llamada al LLM en cada turno usa `tool_choice="required"` para
  forzar la busqueda; las vueltas siguientes usan `"auto"`.
* El modelo por defecto es `openai/gpt-oss-120b`. En el tier gratuito de Groq a
  veces tarda; para un demo mas agil se puede poner `GROQ_MODEL=openai/gpt-oss-20b`
  en el `.env` (tambien soporta function calling).
