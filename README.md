# Agente de FAQs — Parachute S.A. (RAG simple)

Demo de terminal para la **Hoja de trabajo #3 (CC3116 — Sistemas RAG)**.

Un agente de preguntas frecuentes para la empresa *Parachute S.A.* que responde
**únicamente** con base en el archivo `FAQs_Parachute_SA_Guatemala_2026.txt`.
Si la pregunta no está cubierta por el documento, el agente lo admite en lugar de
inventar una respuesta.

## Arquitectura RAG (la más simple posible)

```
FAQs_Parachute_SA_Guatemala_2026.txt   (archivo en el file system)
                │
                ▼
   [ Retrieval ]  loadFaqContext()  ── lee el archivo completo (fs.readFileSync)
                │
                ▼
   [ Augmented ]  se inyecta TODO el texto dentro del prompt de sistema
                │  (bloque <FAQS> ... </FAQS> + reglas de "responde solo con esto")
                ▼
   [ Generation ] Groq (endpoint compatible con la API de OpenAI)
                │  chat.completions.create({ model, messages })
                ▼
        Respuesta en la terminal
```

No hay embeddings, chunking ni base de datos vectorial: el corpus es pequeño, así
que se inyecta íntegro en el contexto. El historial de mensajes se mantiene en
memoria durante la sesión para permitir preguntas de seguimiento.

- SDK: [`openai`](https://www.npmjs.com/package/openai) (Node.js), apuntado al
  endpoint de Groq mediante `baseURL`.
- Proveedor del modelo: [Groq](https://console.groq.com) (tier gratuito, sin tarjeta).

## Requisitos

- Node.js **>= 20.6** (se usa el flag nativo `--env-file`).
- Una API Key gratuita de Groq: <https://console.groq.com/keys>

## Instalación

```bash
npm install
cp .env.example .env      # en Windows PowerShell: copy .env.example .env
```

Edita `.env` y coloca tu API Key:

```
GROQ_API_KEY=gsk_tu_api_key_aqui
GROQ_BASE_URL=https://api.groq.com/openai/v1
GROQ_MODEL=llama-3.3-70b-versatile
```

> El archivo `.env` está en `.gitignore`. **Nunca** subas tu API Key al repositorio.

## Uso

```bash
npm start
```

Se abre un loop interactivo. Escribe tus preguntas; para salir escribe **`Bye`**
o presiona **Ctrl-C**.

Si prefieres exportar las variables de entorno tú mismo (sin archivo `.env`):

```bash
npm run start:noenv
```

### Ejemplos

Preguntas **dentro** del documento:

- `¿Cuándo y dónde es el evento?`
- `¿Cuál es el límite de peso?`
- `¿Qué incluye el Paquete VIP?`
- `¿Puedo llevar mi GoPro?`

Pregunta **fuera** del documento (el agente admite que no sabe):

- `¿Hay estacionamiento en el lugar?`
- `¿Cuánto cuesta el Salto Tándem Básico?`

## Estructura

| Archivo | Rol |
|---|---|
| `src/index.js` | Punto de entrada: config, prompt de sistema, cliente Groq y loop REPL. |
| `src/faq.js` | `loadFaqContext()` — lee y valida el archivo de FAQs (paso de *retrieval*). |
| `.env.example` | Plantilla de variables de entorno. |
| `FAQs_Parachute_SA_Guatemala_2026.txt` | Base de conocimiento (provista por el cliente). |

## Video

Se adjunta un video corto (sin voz) mostrando el funcionamiento: preguntas
respondidas desde el archivo, una pregunta fuera del archivo y la salida con
`Bye` / `Ctrl-C`.
