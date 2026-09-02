import { createInterface } from "node:readline/promises";
import { stdin as input, stdout as output } from "node:process";
import OpenAI from "openai";

import { loadFaqContext } from "./faq.js";

// intento cargar el archivo .env si existe, así no dependo de ninguna librería
// si no está, sigo con lo que haya en el entorno y no pasa nada
try {
  process.loadEnvFile(".env");
} catch {
  // no había archivo .env, las variables pueden venir del entorno igual
}

// leo la configuración del entorno y dejo valores por defecto por si acaso
const {
  GROQ_API_KEY,
  GROQ_BASE_URL = "https://api.groq.com/openai/v1",
  GROQ_MODEL = "openai/gpt-oss-120b",
  FAQ_FILE,
} = process.env;

// sin api key no puedo hacer nada, así que aviso y salgo
if (!GROQ_API_KEY) {
  console.error(
    "\nFalta la variable de entorno GROQ_API_KEY.\n" +
      'Copia ".env.example" a ".env", agrega tu API Key y ejecuta "npm start".\n',
  );
  process.exit(1);
}

// paso de retrieval: traigo el archivo de faqs desde el disco
let faq;
try {
  faq = loadFaqContext(FAQ_FILE);
} catch (err) {
  console.error(`\n${err.message}\n`);
  process.exit(1);
}

// paso de augmented: meto todo el texto del archivo dentro del prompt de sistema
// y le pongo reglas para que solo responda con eso y en texto plano
const SYSTEM_PROMPT = `Eres el asistente virtual de preguntas frecuentes de Parachute S.A. para su evento de paracaidismo en Guatemala.

REGLAS ESTRICTAS:
1. Responde SOLO con información que esté dentro del documento delimitado por <FAQS> y </FAQS>.
2. No uses conocimiento externo ni inventes datos que no aparezcan en el documento.
3. Si la respuesta no está en el documento, responde exactamente esto:
   "Lo siento, no tengo esa información en el documento de preguntas frecuentes. Puedes contactar a Parachute S.A. al +502 2300-0000 o al correo info@parachutesa.gt."
4. Responde en español, de forma breve y clara.
5. Escribe en texto plano, sin formato markdown: nada de asteriscos para negrita, ni viñetas, ni encabezados. La respuesta se muestra en una terminal.
6. Puedes usar el historial de la conversación para entender preguntas de seguimiento, pero la fuente de verdad siempre es el documento.

<FAQS>
${faq.content}
</FAQS>`;

// cliente de openai pero apuntado al endpoint de groq, que es compatible
const client = new OpenAI({ apiKey: GROQ_API_KEY, baseURL: GROQ_BASE_URL });

// acá voy guardando toda la conversación para que recuerde el contexto
const messages = [{ role: "system", content: SYSTEM_PROMPT }];

// palabras con las que el usuario puede salir del loop
const EXIT_WORDS = new Set(["bye", "adios", "adiós", "salir"]);

const rl = createInterface({ input, output });

function despedirse() {
  console.log("\nAgente> ¡Gracias por tu interés en Parachute S.A.! Hasta pronto.\n");
}

// si el usuario presiona Ctrl+C cierro todo de forma ordenada
rl.on("SIGINT", () => {
  despedirse();
  rl.close();
  process.exit(0);
});

console.log("========================================================");
console.log(" Agente de FAQs Parachute S.A. (evento 2026)");
console.log(` Modelo: ${GROQ_MODEL}  |  Fuente: ${faq.path}`);
console.log('  Escribe "Bye" o presiona Ctrl+C para salir.');
console.log("========================================================\n");

output.write("Tú> ");

// este for await se corta solo cuando se cierra la entrada (Ctrl+D o cuando
// le paso texto por pipe). el Ctrl+C lo manejo arriba con el evento SIGINT
for await (const linea of rl) {
  const pregunta = linea.trim();

  // si mandó una línea vacía solo vuelvo a pedir input
  if (!pregunta) {
    output.write("Tú> ");
    continue;
  }

  // si escribió una palabra de salida me despido y corto el loop
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
    // si la llamada falla saco la pregunta del historial para no dejarlo sucio
    messages.pop();
    console.error(`\nAgente> Ocurrió un error al consultar el modelo: ${err.message}\n`);
  }

  output.write("Tú> ");
}

rl.close();
