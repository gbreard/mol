import Groq from 'groq-sdk'

// Modelos configurables: Groq retira modelos sin aviso (los Llama dieron 404 model_not_found).
// FAST = extracción de keywords; LARGE = análisis ocupacional y trayectoria.
// Son modelos de razonamiento: el reasoning consume tokens de max_completion_tokens.
export const GROQ_MODEL_FAST = process.env.GROQ_MODEL_FAST || 'openai/gpt-oss-20b'
export const GROQ_MODEL_LARGE = process.env.GROQ_MODEL_LARGE || 'openai/gpt-oss-120b'

let _groq: Groq | null = null

export function getGroq(): Groq | null {
  if (_groq) return _groq
  const key = process.env.GROQ_API_KEY
  if (!key) return null
  _groq = new Groq({ apiKey: key })
  return _groq
}
