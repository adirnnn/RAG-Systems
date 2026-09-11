# Agente de FAQs Parachute S.A. (CC3116)

Hoja de trabajo #4: Herramientas (pgvector + function calling).

Version mas robusta del agente de FAQs de Parachute S.A. La base de conocimientos
es un dump grande (`Corpus_FAQs_Parachute_SA_2026.txt`, 120 fichas) que vive en
PostgreSQL con la extension pgvector. El agente ya no recibe todo el texto en el
prompt: consulta la base por medio de una herramienta (function calling)
registrada en el SDK. Si la pregunta no corresponde a ninguna ficha, el agente
admite que no puede responderla.

Todo el codigo esta en [`hdt4/`](hdt4/). Doc detallada en
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

Video corto sin voz mostrando `cargar.py` llenando la tabla y `agente.py`
respondiendo preguntas del corpus, incluida una fuera de dominio:

<https://youtu.be/URD2tdL6Pms>
