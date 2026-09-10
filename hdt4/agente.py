"""agente de terminal: responde faqs consultando pgvector por medio de una herramienta."""

import json
import os
import sys
import time

from openai import OpenAI

from db import cargar_entorno, conectar, embeber, vector_literal, TABLA

# fuerzo utf-8 en la salida para que los acentos se vean bien en cualquier consola
for _flujo in (sys.stdout, sys.stderr):
    try:
        _flujo.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

# frase exacta cuando la herramienta no trae nada util
SIN_INFO = (
    "Lo siento, no tengo esa informacion en la base de conocimientos de "
    "Parachute S.A. Puedes escribir a soporte@parachutesa.gt."
)

SYSTEM_PROMPT = (
    "Eres el asistente de preguntas frecuentes de Parachute S.A. para su evento "
    "de paracaidismo en Guatemala 2026.\n\n"
    "COMO TRABAJAS:\n"
    "1. Para CADA pregunta del usuario primero llamas a la herramienta "
    "buscar_en_faqs. Es tu unica fuente de informacion.\n"
    "2. La herramienta devuelve varias fichas, cada una con su PREGUNTA y su "
    "RESPUESTA. Elige la ficha cuya PREGUNTA corresponda al tema que pregunta el "
    "usuario.\n"
    "3. Si alguna ficha corresponde, responde usando su RESPUESTA, resumida en 1 "
    "a 3 frases con tus palabras. Si esa RESPUESTA es un texto generico que "
    "remite a soporte, transmite eso mismo e incluye el correo de soporte que "
    "aparezca.\n"
    "4. Si la herramienta devuelve SIN_RESULTADOS, o si NINGUNA de las fichas "
    "trata el tema que pregunta el usuario, responde exactamente esto y nada "
    f'mas: "{SIN_INFO}"\n'
    "5. No uses conocimiento externo ni inventes datos que no esten en las "
    "fichas.\n"
    "6. Responde en espanol, en texto plano. Nada de markdown, asteriscos, "
    "vinetas ni lineas de guiones como separador.\n"
    "7. Puedes usar el historial para entender preguntas de seguimiento, pero "
    "siempre vuelves a consultar la herramienta."
)

# esquema de la herramienta que se registra en el sdk (function calling)
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "buscar_en_faqs",
            "description": (
                "Busca en la base de conocimientos de FAQs de Parachute S.A. por "
                "similitud semantica y devuelve las fichas mas parecidas a la "
                "consulta. Es la unica fuente de informacion permitida."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "consulta": {
                        "type": "string",
                        "description": "La pregunta o el tema a buscar, en lenguaje natural.",
                    },
                    "k": {
                        "type": "integer",
                        "description": "Cuantas fichas traer, por defecto 4.",
                    },
                },
                "required": ["consulta"],
            },
        },
    }
]

MAX_VUELTAS = 5


def _crear_con_reintento(cliente, **kw):
    # groq a veces corta la conexion, reintento un par de veces antes de rendirme
    ultimo = None
    for intento in range(3):
        try:
            return cliente.chat.completions.create(**kw)
        except Exception as e:  # noqa: BLE001
            ultimo = e
            time.sleep(1.5 * (intento + 1))
    raise ultimo


def buscar_en_faqs(conn, consulta, k=4):
    # esta funcion es lo que corre cuando el modelo llama a la herramienta
    umbral = float(os.environ.get("UMBRAL_SIMILITUD", "0.35"))
    k = max(1, min(int(k or 4), 10))
    vector = vector_literal(embeber([consulta])[0])

    with conn.cursor() as cur:
        cur.execute(
            f"""
            SELECT id, categoria, pregunta, respuesta,
                   1 - (embedding <=> %s::vector) AS score
            FROM {TABLA}
            ORDER BY embedding <=> %s::vector
            LIMIT %s
            """,
            (vector, vector, k),
        )
        filas = cur.fetchall()

    utiles = [f for f in filas if f[4] >= umbral]
    if not utiles:
        return "SIN_RESULTADOS"

    partes = []
    for id_, categoria, pregunta, respuesta, score in utiles:
        partes.append(
            f"[{id_}] categoria: {categoria} | score: {score:.2f}\n"
            f"PREGUNTA: {pregunta}\n"
            f"RESPUESTA: {respuesta}"
        )
    return "\n\n".join(partes)


def _turno(cliente, modelo, conn, historial):
    # trabajo sobre una copia, si algo falla no ensucio el historial real
    messages = list(historial)
    eleccion = "required"  # la primera llamada obliga a buscar

    for _ in range(MAX_VUELTAS):
        r = _crear_con_reintento(
            cliente,
            model=modelo,
            messages=messages,
            tools=TOOLS,
            tool_choice=eleccion,
            temperature=0.2,
            max_tokens=800,
        )
        msg = r.choices[0].message

        asistente = {"role": "assistant", "content": msg.content or ""}
        if msg.tool_calls:
            asistente["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                }
                for tc in msg.tool_calls
            ]
        messages.append(asistente)

        if not msg.tool_calls:
            return (msg.content or SIN_INFO), messages

        for tc in msg.tool_calls:
            try:
                args = json.loads(tc.function.arguments or "{}")
            except json.JSONDecodeError:
                args = {}

            if tc.function.name == "buscar_en_faqs":
                salida = buscar_en_faqs(
                    conn, args.get("consulta", ""), args.get("k", 4)
                )
            else:
                salida = "herramienta desconocida"

            messages.append(
                {"role": "tool", "tool_call_id": tc.id, "content": salida}
            )

        eleccion = "auto"  # despues de la primera, que el modelo decida

    return SIN_INFO, messages


def main():
    cargar_entorno()

    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        sys.exit("falta GROQ_API_KEY en el .env, copia .env.example a .env")

    cliente = OpenAI(
        api_key=api_key,
        base_url=os.environ.get("GROQ_BASE_URL", "https://api.groq.com/openai/v1"),
    )
    modelo = os.environ.get("GROQ_MODEL", "openai/gpt-oss-120b")

    print("conectando a la base y cargando el modelo de embeddings...")
    conn = conectar()
    conn.autocommit = True  # el agente solo hace SELECT, evita transacciones colgadas
    embeber(["texto para calentar el modelo"])  # lo cargo ahora, no en la primera pregunta

    historial = [{"role": "system", "content": SYSTEM_PROMPT}]
    salidas = {"bye", "adios", "adiós", "salir"}

    print("=" * 60)
    print(" Agente de FAQs Parachute S.A. (HDT4: pgvector + herramienta)")
    print(f" LLM: {modelo}  |  tabla: {TABLA}")
    print('  Escribe "Bye" o presiona Ctrl+C para salir.')
    print("=" * 60 + "\n")

    try:
        while True:
            try:
                pregunta = input("Tu> ").strip()
            except EOFError:
                break

            if not pregunta:
                continue
            if pregunta.lower() in salidas:
                break

            try:
                respuesta, historial = _turno(
                    cliente,
                    modelo,
                    conn,
                    historial + [{"role": "user", "content": pregunta}],
                )
                print(f"\nAgente> {respuesta}\n")
            except Exception as e:  # noqa: BLE001  un error de api o de db no debe tumbar el loop
                print(f"\nAgente> Ocurrio un error al responder: {e}\n")
    except KeyboardInterrupt:
        pass

    conn.close()
    print("\nAgente> Gracias por tu interes en Parachute S.A. Hasta pronto.\n")


if __name__ == "__main__":
    main()
