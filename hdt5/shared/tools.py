"""envoltorios @function_tool sobre la logica de negocio pura de shared/*.

estas son las tools que se reparten entre los agentes de las 3 arquitecturas.
la funcion de negocio (el "_raw") es identica en los 3 programas; lo unico que
cambia por arquitectura es a que agente se le da cada tool.
"""

from agents import function_tool, handoff
from agents.extensions.handoff_filters import remove_all_tools

from .agenda import agendar_cita_raw
from .clima import consultar_clima_raw
from .faqs import buscar_en_faqs_raw


@function_tool
def buscar_en_faqs(consulta: str, k: int = 4) -> str:
    """Busca en la base de conocimientos de FAQs de Parachute S.A. por similitud
    semantica y devuelve las fichas mas parecidas a la consulta.

    Args:
        consulta: la pregunta o el tema a buscar, en lenguaje natural.
        k: cuantas fichas traer, por defecto 4.
    """
    return buscar_en_faqs_raw(consulta, k)


@function_tool
def consultar_clima(fecha: str) -> str:
    """Consulta el pronostico del clima en la zona de salto para una fecha, sin
    agendar nada. Sirve para que el usuario decida si quiere reservar.

    Args:
        fecha: fecha en formato AAAA-MM-DD. Open-Meteo solo predice hasta 16
            dias hacia adelante desde hoy.
    """
    datos = consultar_clima_raw(fecha)
    if "error" in datos:
        return f"FECHA_INVALIDA: {datos['error']}"

    ev = datos["evaluacion"]
    problemas = "; ".join(ev["problemas"]) if ev["problemas"] else "ninguno"
    return (
        f"fecha={datos['fecha']} veredicto={ev['veredicto']} "
        f"temperatura={datos['temperatura']}C viento={datos['viento']}km/h "
        f"rafagas={datos['rafaga']}km/h precipitacion={datos['precipitacion']}mm "
        f"nubes={datos['nubes']}% problemas={problemas}"
    )


@function_tool
def agendar_cita(fecha: str, nombre: str | None = None) -> str:
    """Revisa el clima de la fecha pedida y, si las condiciones son seguras
    para saltar, agenda la cita. Si no son seguras, no agenda nada y explica
    por que.

    Args:
        fecha: fecha deseada para la cita, en formato AAAA-MM-DD.
        nombre: nombre de quien reserva, opcional.
    """
    return agendar_cita_raw(fecha, nombre)


def handoff_sin_bloqueo(agente, descripcion=None):
    """arma un handoff normal (sin datos extra), pero con dos ajustes que hicieron
    falta para que funcione bien contra groq (verificados en vivo antes de
    escribir descentralizado.py):

    1. apaga el json schema estricto. con strict_json_schema=True (el default
       del sdk), el handoff sin input_type genera un schema de tool con
       properties vacio y groq lo rechaza con un 400 ("'required' present but
       'properties' is missing"), algo que la api real de openai si tolera.

    2. input_filter=remove_all_tools. sin esto, el agente que recibe la
       conversacion ve en su historial el razonamiento y la llamada de handoff
       del agente anterior, y los modelos chicos (probado con gpt-oss-20b y
       tambien con 120b) se confunden: contestan cualquier cosa sin llamar su
       propia herramienta, como si el handoff ya fuera la respuesta. filtrando
       ese ruido, el agente nuevo ve la conversacion limpia y si usa su tool.
    """
    h = handoff(agente, tool_description_override=descripcion, input_filter=remove_all_tools)
    h.strict_json_schema = False
    return h
