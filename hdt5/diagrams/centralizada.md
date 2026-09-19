# Arquitectura centralizada

Programa: [`../centralizado.py`](../centralizado.py)

Un solo manager habla con el usuario. Los especialistas estan expuestos como
herramienta (`Agent.as_tool()`): el manager decide a cual delegar, recibe su
resultado y redacta la respuesta final. Los especialistas nunca le
responden directo al usuario.

```mermaid
graph TD
    U["usuario"] --> M["agente_manager"]
    M -- "as_tool" --> F["agente_faqs"]
    M -- "as_tool" --> A["agente_agenda"]
    F --> TF[["buscar_en_faqs"]]
    A --> TC[["consultar_clima"]]
    A --> TA[["agendar_cita"]]
    TF -.-> DB[("tabla faqs, pgvector")]
    TC -.-> OM(("Open Meteo API"))
    TA -.-> OM
    TA -.-> ST[("data/citas.json")]
```
