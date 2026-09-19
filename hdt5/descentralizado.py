"""arquitectura decentralizada: agentes pares que se transfieren la conversacion
con handoff, sin ningun supervisor que sintetice la respuesta final.

a diferencia de as_tool (donde el manager llama al especialista, recibe texto
de vuelta, y redacta la respuesta el mismo), con handoff el especialista
toma el control completo de la conversacion y le responde directo al usuario.
agente_recepcion, agente_faqs y agente_agenda son pares: cualquiera puede
transferirle el turno a cualquier otro segun lo que necesite el usuario.
"""

from agents import Agent

from shared.cli import iniciar
from shared.model import construir_modelo
from shared.prompts import INSTRUCCIONES_AGENDA, INSTRUCCIONES_FAQS, REGLAS_TEXTO_PLANO
from shared.tools import agendar_cita, buscar_en_faqs, consultar_clima, handoff_sin_bloqueo

modelo = construir_modelo()

agente_recepcion = Agent(
    name="agente_recepcion",
    instructions=(
        "Eres la recepcion del agente de Parachute S.A. No respondes preguntas "
        "por tu cuenta, solo transfieres la conversacion (handoff) al "
        "especialista correcto: agente_faqs si es una pregunta de informacion "
        "sobre el evento, agente_agenda si quiere saber el clima o agendar una "
        "cita. Si no esta claro, pregunta primero que necesita.\n"
        f"{REGLAS_TEXTO_PLANO}"
    ),
    model=modelo,
)

agente_faqs = Agent(
    name="agente_faqs",
    instructions=(
        INSTRUCCIONES_FAQS
        + "\nSi el usuario pide agendar una cita o preguntar el clima, "
        "transfierelo (handoff) a agente_agenda."
    ),
    model=modelo,
    tools=[buscar_en_faqs],
)

agente_agenda = Agent(
    name="agente_agenda",
    instructions=(
        INSTRUCCIONES_AGENDA
        + "\nSi el usuario vuelve a preguntar algo de informacion general del "
        "evento, transfierelo (handoff) a agente_faqs."
    ),
    model=modelo,
    tools=[consultar_clima, agendar_cita],
)

# malla de pares: cualquiera puede transferirle el turno a cualquier otro.
# se asignan despues de crear los 3 agentes porque los handoffs son circulares
# (faqs <-> agenda, y recepcion hacia los dos).
agente_recepcion.handoffs = [
    handoff_sin_bloqueo(agente_faqs, "cuando la consulta es sobre informacion del evento."),
    handoff_sin_bloqueo(agente_agenda, "cuando la consulta es sobre clima o agendar una cita."),
]
agente_faqs.handoffs = [
    handoff_sin_bloqueo(agente_agenda, "cuando el usuario quiere el clima o agendar una cita."),
    handoff_sin_bloqueo(agente_recepcion, "si la conversacion ya no es sobre faqs ni sobre agenda."),
]
agente_agenda.handoffs = [
    handoff_sin_bloqueo(agente_faqs, "cuando el usuario vuelve a preguntar algo del evento."),
    handoff_sin_bloqueo(agente_recepcion, "si la conversacion ya no es sobre clima ni sobre agenda."),
]

if __name__ == "__main__":
    iniciar(agente_recepcion, "decentralizada")
