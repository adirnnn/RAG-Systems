import { createInterface } from "node:readline/promises";
import { stdin as input, stdout as output } from "node:process";
import OpenAI from "openai";

import { loadFaqContext } from "./faq.js";

// --- 1. Configuración desde el entorno -------------------------------------
const {
  GROQ_API_KEY,
  GROQ_BASE_URL = "https://api.groq.com/openai/v1",
  GROQ_MODEL = "llama-3.3-70b-versatile",
  FAQ_FILE,
} = process.env;

if (!GROQ_API_KEY) {
  console.error(
    "\nFalta la variable de entorno GROQ_API_KEY.\n" +
      'Copia ".env.example" a ".env", agrega tu API Key y ejecuta "npm start".\n',
  );
  process.exit(1);
}

// --- 2. "Retrieval": cargar el archivo de FAQs del file system ------------
let faq;
try {
  faq = loadFaqContext(FAQ_FILE);
} catch (err) {
  console.error(`\n${err.message}\n`);
  process.exit(1);
}

// --- 3. "Augmented": inyectar el contenido en el prompt de sistema -------
const SYSTEM_PROMPT = `Eres el asistente virtual de preguntas frecuentes de Parachute S.A. para su evento de paracaidismo en Guatemala.

REGLAS ESTRICTAS:
1. Responde ÚNICAMENTE con información contenida en el documento delimitado por <FAQS> y </FAQS>.
2. No uses conocimiento externo ni supongas datos que no aparezcan en el documento.
3. Si la respuesta no está en el documento, responde exactamente:
   "Lo siento, no tengo esa información en el documento de preguntas frecuentes. Puedes contactar a Parachute S.A. al +502 2300-0000 o al correo info@parachutesa.gt."
4. Responde en español, de forma breve y clara.
5. Puedes usar el historial de la conversación para entender preguntas de seguimiento, pero la fuente de verdad siempre es el documento.

<FAQS>
${faq.content}
</FAQS>`;

// --- 4. Cliente compatible con la API de OpenAI (Groq) -------------------
const client = new OpenAI({ apiKey: GROQ_API_KEY, baseURL: GROQ_BASE_URL });

// --- 5. Historial de la conversación (memoria de la sesión) -------------
const messages = [{ role: "system", content: SYSTEM_PROMPT }];

// --- 6. Loop de preguntas y respuestas --------------------------------
const EXIT_WORDS = new Set(["bye", "adios", "adiós", "salir"]);

const rl = createInterface({ input, output });

function despedirse() {
  console.log("\nAgente> ¡Gracias por tu interés en Parachute S.A.! Hasta pronto.\n");
}

// Ctrl-C: salida limpia
rl.on("SIGINT", () => {
  despedirse();
  rl.close();
  process.exit(0);
});

console.log("========================================================");
console.log(" Agente de FAQs - Parachute S.A. (evento 2026)");
console.log(` Modelo: ${GROQ_MODEL}  |  Fuente: ${faq.path}`);
console.log('  Escribe "Bye" o presiona Ctrl-C para salir.');
console.log("========================================================\n");

output.write("Tú> ");

// El iterador asíncrono termina solo al cerrar la entrada (EOF / Ctrl-D o
// stdin canalizado). Ctrl-C se maneja arriba con el evento "SIGINT".
for await (const linea of rl) {
  const pregunta = linea.trim();

  if (!pregunta) {
    output.write("Tú> ");
    continue;
  }

  if (EXIT_WORDS.has(pregunta.toLowerCase())) {
    despedirse();
    break;
  }

  messages.push({ role: "user", content: pregunta });

  try {
    const completion = await client.chat.completions.create({
      model: GROQ_MODEL,
      messages,
      temperature: 0.2,
    });

    const respuesta =
      completion.choices?.[0]?.message?.content?.trim() ||
      "(sin respuesta del modelo)";

    messages.push({ role: "assistant", content: respuesta });
    console.log(`\nAgente> ${respuesta}\n`);
  } catch (err) {
    // Quitar el turno del usuario que falló para no ensuciar el historial.
    messages.pop();
    console.error(`\nAgente> Ocurrió un error al consultar el modelo: ${err.message}\n`);
  }

  output.write("Tú> ");
}

rl.close();
