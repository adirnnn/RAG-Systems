"""arquitectura jerarquica: un director arriba, dos managers medios, y workers
con una sola herramienta cada uno.

el usuario solo habla con el director. el director delega en el manager que
corresponda (as_tool); ese manager a su vez delega en su propio worker
(tambien as_tool). la peticion cruza dos niveles antes de llegar a la tool
real, y la respuesta sube de vuelta por los mismos dos niveles.
"""

from agents import Agent

from shared.cli import iniciar
from shared.model import construir_modelo
from shared.prompts import INSTRUCCIONES_FAQS, REGLAS_TEXTO_PLANO, instrucciones_manager
from shared.tools import agendar_cita, buscar_en_faqs, consultar_clima

modelo = construir_modelo()

# nivel worker: cada uno con una sola tool

agente_faqs = Agent(
    name="agente_faqs",
    instructions=INSTRUCCIONES_FAQS,
    model=modelo,
    tools=[buscar_en_faqs],
)

agente_clima = Agent(
    name="agente_clima",
    instructions=(
        "Eres el especialista en consultar el clima de la zona de salto de "
        "Parachute S.A. Usa siempre la herramienta consultar_clima (recibe la "
        "fecha en formato AAAA-MM-DD) y responde con lo que te devuelva, sin "
        "inventar datos. No agendas citas, solo informas el clima.\n"
        f"{REGLAS_TEXTO_PLANO}"
    ),
    model=modelo,
    tools=[consultar_clima],
)

agente_calendario = Agent(
    name="agente_calendario",
    instructions=(
        "Eres el especialista en agendar citas de salto de Parachute S.A. Usa "
        "siempre la herramienta agendar_cita (recibe la fecha en formato "
        "AAAA-MM-DD), que ya revisa el clima antes de confirmar. Si el "
        "resultado empieza con NO_SE_PUDO_AGENDAR, explica por que sin "
        "insistir; si empieza con CITA_CONFIRMADA, confirmala con los datos "
        "que te dio la herramienta.\n"
        f"{REGLAS_TEXTO_PLANO}"
    ),
    model=modelo,
    tools=[agendar_cita],
)

# nivel manager: cada uno delega en sus workers

manager_conocimiento = Agent(
    name="manager_conocimiento",
    instructions=instrucciones_manager(
        "manager de conocimiento",
        ["agente_faqs: responde preguntas frecuentes del evento."],
    ),
    model=modelo,
    tools=[
        agente_faqs.as_tool(
            tool_name="agente_faqs",
            tool_description="responde preguntas frecuentes de Parachute S.A. sobre el evento.",
        )
    ],
)

manager_operaciones = Agent(
    name="manager_operaciones",
    instructions=instrucciones_manager(
        "manager de operaciones",
        [
            "agente_clima: solo consulta el clima de una fecha, sin agendar nada.",
            "agente_calendario: agenda una cita de salto (revisa el clima antes de confirmar).",
        ],
    ),
    model=modelo,
    tools=[
        agente_clima.as_tool(
            tool_name="agente_clima",
            tool_description="consulta el clima de una fecha en la zona de salto, sin agendar.",
        ),
        agente_calendario.as_tool(
            tool_name="agente_calendario",
            tool_description="agenda una cita de salto revisando el clima antes de confirmar.",
        ),
    ],
)

# nivel director: el unico que habla con el usuario

director = Agent(
    name="director",
    instructions=instrucciones_manager(
        "director",
        [
            "manager_conocimiento: todo lo relacionado a preguntas frecuentes del evento.",
            "manager_operaciones: todo lo relacionado a clima y a agendar citas.",
        ],
    ),
    model=modelo,
    tools=[
        manager_conocimiento.as_tool(
            tool_name="manager_conocimiento",
            tool_description="maneja preguntas frecuentes de Parachute S.A. sobre el evento.",
        ),
        manager_operaciones.as_tool(
            tool_name="manager_operaciones",
            tool_description="maneja consultas de clima y agendamiento de citas de salto.",
        ),
    ],
)

if __name__ == "__main__":
    iniciar(director, "jerarquica")
