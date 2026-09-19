# Agente de FAQs Parachute S.A. (CC3116)

Hoja de trabajo #5: Orquestación (sistemas multiagente).

Nuevo requisito de Parachute S.A.: el agente ahora puede calendarizar una cita
de salto revisando el clima antes (Open-Meteo, con un criterio de viento,
ráfagas, precipitación y nubes para decidir si es seguro saltar). El mismo
problema se resuelve con tres arquitecturas de orquestación multiagente
distintas, usando el OpenAI Agents SDK apuntado a Groq: centralizada
(`as_tool`, un manager), jerárquica (`as_tool` en dos niveles) y
decentralizada (`handoff` entre agentes independientes).

Todo el código está en [`hdt5/`](hdt5/). Doc detallada, diagramas de cada
arquitectura y las respuestas a las preguntas de la hoja en
[`hdt5/README.md`](hdt5/README.md).

## Los tres programas

* `hdt5/centralizado.py`: un manager delega en especialistas expuestos como
  herramienta.
* `hdt5/jerarquico.py`: un director delega en dos submanagers, cada uno con
  sus propios workers.
* `hdt5/descentralizado.py`: agentes independientes que se transfieren la
  conversación completa entre sí.

Diagramas de cada arquitectura en [`hdt5/diagrams/`](hdt5/diagrams/).
Respuestas a las preguntas de la hoja en
[`hdt5/respuestas.pdf`](hdt5/respuestas.pdf).

## Cómo inicializar la infraestructura

HDT5 reutiliza la misma base PostgreSQL con pgvector que llenó HDT4 (no trae
la suya propia). Requisitos: Docker con `docker compose`, Python 3.11 o
superior, una API Key gratuita de Groq (<https://console.groq.com/keys>).

```bash
# 1. levantar la base de HDT4 (contenedor parachute_pgvector, puerto 5434)
cd hdt4
docker compose up -d
cd ../hdt5

# 2. entorno de python
python -m venv .venv
# Windows PowerShell:  .venv\Scripts\Activate.ps1
# Linux o macOS:       source .venv/bin/activate
pip install -r requirements.txt

# 3. configuracion
copy .env.example .env
# editar .env y pegar GROQ_API_KEY (se puede copiar del .env de hdt4)

# 4. correr cualquiera de las tres arquitecturas
python centralizado.py
python jerarquico.py
python descentralizado.py
```

Para salir de cualquiera: `Bye` o `Ctrl+C`. Detalle completo (criterio de
decisión del clima, notas técnicas de compatibilidad con Groq, ejemplos) en
[`hdt5/README.md`](hdt5/README.md).

## Entregas anteriores

* Hoja de trabajo #3 (RAG simple, Node.js): código en la raíz (`src/`), ver el
  historial de git para su README.
* Hoja de trabajo #4 (pgvector + function calling, Python): código y doc en
  [`hdt4/`](hdt4/).
