import { readFileSync, existsSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, isAbsolute, join } from "node:path";

const __dirname = dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = join(__dirname, "..");

export const DEFAULT_FAQ_FILE = "FAQs_Parachute_SA_Guatemala_2026.txt";

/**
 * Carga (paso "Retrieval" de este RAG mínimo) el archivo de preguntas frecuentes
 * desde el file system y devuelve su contenido como texto plano.
 *
 * @param {string} [file] Ruta al archivo. Si es relativa se resuelve contra la
 *   raíz del repositorio. Por defecto: FAQs_Parachute_SA_Guatemala_2026.txt
 * @returns {{ path: string, content: string }}
 */
export function loadFaqContext(file = DEFAULT_FAQ_FILE) {
  const path = isAbsolute(file) ? file : join(REPO_ROOT, file);

  if (!existsSync(path)) {
    throw new Error(
      `No se encontró el archivo de preguntas frecuentes en: ${path}\n` +
        `Coloca el .txt en la raíz del proyecto o define la variable FAQ_FILE.`,
    );
  }

  const content = readFileSync(path, "utf8").trim();

  if (!content) {
    throw new Error(`El archivo de preguntas frecuentes está vacío: ${path}`);
  }

  return { path, content };
}
