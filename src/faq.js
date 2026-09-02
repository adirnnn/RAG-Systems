import { readFileSync, existsSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, isAbsolute, join } from "node:path";

// saco la carpeta de este archivo para poder armar rutas desde la raíz del repo
const currentDir = dirname(fileURLToPath(import.meta.url));
const repoRoot = join(currentDir, "..");

export const DEFAULT_FAQ_FILE = "FAQs_Parachute_SA_Guatemala_2026.txt";

// esta función es el paso de retrieval del rag: agarra el txt del disco y me
// devuelve todo su contenido como texto para metérselo después al modelo
export function loadFaqContext(file = DEFAULT_FAQ_FILE) {
  // si me pasan una ruta relativa la armo desde la raíz del proyecto
  const path = isAbsolute(file) ? file : join(repoRoot, file);

  // si el archivo no está, mejor aviso claro y no sigo
  if (!existsSync(path)) {
    throw new Error(
      `No se encontró el archivo de preguntas frecuentes en: ${path}\n` +
        `Coloca el .txt en la raíz del proyecto o define la variable FAQ_FILE.`,
    );
  }

  const content = readFileSync(path, "utf8").trim();

  // si viene vacío tampoco tiene sentido continuar
  if (!content) {
    throw new Error(`El archivo de preguntas frecuentes está vacío: ${path}`);
  }

  return { path, content };
}
