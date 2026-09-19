# HDT5 Orquestacion: multiagente con OpenAI Agents SDK

Nuevo requisito de Parachute S.A.: el agente ahora debe poder **calendarizar una
cita revisando el clima antes** (Open-Meteo, coordenadas fijas de la pista de
aterrizaje, hasta 16 dias de prediccion, con criterios de viento, rafagas,
precipitacion y nubes para decidir si el salto es seguro).

Esta hoja pide resolver el mismo problema tres veces con tres arquitecturas de
orquestacion multiagente distintas, usando el [OpenAI Agents
SDK](https://openai.github.io/openai-agents-python/) apuntado a Groq:

* `centralizado.py`: arquitectura **centralizada**, un solo manager que expone
  agentes especialistas como herramienta (`Agent.as_tool()`).
* `jerarquico.py`: arquitectura **jerarquica**, un director que delega en dos
  submanagers, cada uno con sus propios workers.
* `descentralizado.py`: arquitectura **decentralizada**, agentes independientes
  que se transfieren la conversacion completa entre si (`handoff()`).

Los diagramas de cada arquitectura estan en [`diagrams/`](diagrams/) y las
respuestas a las preguntas de la hoja en [`respuestas.pdf`](respuestas.pdf)
(fuente en [`respuestas.md`](respuestas.md)).

## Como se abstrajo la logica de integracion

Parachute S.A. avisó que va a seguir agregando requisitos, así que toda la
lógica de negocio vive en `shared/`, separada de cómo se organizan los agentes:

* `shared/faqs.py`: búsqueda semántica en la tabla `faqs` de pgvector (la
  misma que llenó `hdt4/cargar.py`, no se duplica infraestructura).
* `shared/clima.py`: cliente de Open-Meteo, validación de fecha y el criterio
  de decisión (viento, ráfagas, precipitación, nubes).
* `shared/agenda.py`: revisa el clima y guarda la cita en `data/citas.json` si
  las condiciones lo permiten.
* `shared/tools.py`: envuelve esas tres funciones con `@function_tool` para el
  SDK, más un helper (`handoff_sin_bloqueo`) para el bug de Groq descrito abajo.
* `shared/model.py`: arma el modelo de Groq (`OpenAIChatCompletionsModel`) una
  sola vez, reusado por los tres programas.
* `shared/prompts.py`: los textos de instrucciones que comparten los agentes.
* `shared/cli.py`: el loop de terminal (`Bye` / `Ctrl+C`, historial de la
  conversación). Es idéntico para las tres arquitecturas.

Los tres programas (`centralizado.py`, `jerarquico.py`, `descentralizado.py`)
**solo difieren en cómo arman el grafo de agentes** con esas mismas piezas. Si
Parachute pide un requisito nuevo, se agrega una función en `shared/` y se
conecta al agente que corresponda en cada archivo, sin tocar el resto.

## Requisitos

* La base de datos de HDT4 tiene que estar arriba (HDT5 no trae la suya):
  ```bash
  cd ../hdt4
  docker compose up -d
  cd ../hdt5
  ```
* Python 3.11 o superior.
* Una API Key gratuita de Groq: <https://console.groq.com/keys>

## Instalacion

```bash
python -m venv .venv
# Windows PowerShell:  .venv\Scripts\Activate.ps1
# Linux o macOS:       source .venv/bin/activate
pip install -r requirements.txt
```

```bash
copy .env.example .env
# editar .env y pegar GROQ_API_KEY (se puede copiar del .env de hdt4)
```

## Uso

```bash
python centralizado.py
python jerarquico.py
python descentralizado.py
```

Cada uno abre un loop de terminal independiente. Escribe preguntas de FAQs o
pide agendar una cita (por ejemplo "quiero agendar una cita para el
2026-09-25"); para salir escribe `Bye` o presiona `Ctrl+C`.

## Sobre Open-Meteo

Coordenadas fijas: `14.013722, -90.771611`. Se verifico en vivo contra el
endpoint real (`https://api.open-meteo.com/v1/forecast`):

* El bloque `current` trae exactamente los 5 parametros que pide la hoja
  (`temperature_2m`, `precipitation`, `cloud_cover`, `wind_speed_10m`,
  `wind_gusts_10m`) para el clima de ahorita.
* El bloque `daily` de Open-Meteo **no** tiene esas variables (usa agregados
  como `temperature_2m_max`); el bloque `hourly` si las tiene, para cualquier
  hora de cualquier dia dentro del horizonte de prediccion.
* Por eso: si la fecha pedida es hoy, se usa `current`. Si es una fecha futura
  (1 a 16 dias), se usa `hourly` pidiendo `start_date`/`end_date` igual a esa
  fecha y se toma el mediodia (12:00) como hora representativa, ya que la cita
  no especifica hora. Mas de 16 dias, o una fecha pasada, se corrige sin llamar
  la API.
* El dia 16 exacto a veces viene con datos incompletos (limite del modelo de
  Open-Meteo); en ese caso se le pide al usuario una fecha un poco mas cercana
  en vez de fallar.

Criterio de decision (viento y rafagas en km/h, nubes en % de cobertura):

* Viento en superficie: ideal por debajo de 20; marginal entre 20 y 28 (solo
  tandem experimentado); prohibido por encima de 28.
* Rafagas: prohibido por encima de 35.
* Precipitacion: prohibido cualquier valor mayor a 0.0 mm.
* Nubes: ideal por debajo de 30%; marginal entre 30% y 75%; prohibido por
  encima de 75%.

El veredicto final es el peor nivel entre los cuatro factores. Solo se agenda
la cita si el veredicto no es `NO_SEGURO`.

## Nota tecnica: bug de Groq con handoffs sin datos

El SDK genera, por defecto, un `handoff()` sin argumentos con un JSON schema
`{"properties": {}, "required": []}`. Groq (a diferencia de la API real de
OpenAI) rechaza esa llamada con `400 'required' present but 'properties' is
missing`. Se verifico en vivo antes de escribir `descentralizado.py`. La
solucion, en `shared/tools.py::handoff_sin_bloqueo()`, es apagar
`strict_json_schema` en el objeto `Handoff` que arma `handoff()`.
