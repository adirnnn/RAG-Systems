# Agente de FAQs Parachute S.A. (RAG simple)

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
