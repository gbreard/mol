import { NextRequest, NextResponse } from 'next/server'
import { requireRateLimit } from '@/lib/api-auth'
import { createClient } from '@supabase/supabase-js'
import { getGroq, GROQ_MODEL_FAST } from '@/lib/groq'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || ''
const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY || process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || ''

const supabase = supabaseUrl && supabaseKey
  ? createClient(supabaseUrl, supabaseKey)
  : null

const VPS_EMBED_URL = process.env.VPS_EMBED_URL || 'http://187.124.150.28:8082'
const VPS_EMBED_SECRET = process.env.VPS_EMBED_SECRET || ''

const NO_INTERPRETADO = 'No pudimos interpretar el texto, probá con la búsqueda por tarea.'

const GROQ_TIMEOUT_MS = 4000
const EMBED_TIMEOUT_MS = 4000

// Filtro de ruido: máximo 8, umbral por modo; si quedan menos de 3, se completa hasta 3 con >= 0.55
const MAX_RESULTS = 8
const MIN_RESULTS = 3
const MIN_SCORE_LLM = 0.60
const MIN_SCORE_FALLBACK = 0.62
const MIN_SCORE_FLOOR = 0.55
// Si la selección del LLM deja menos de 3, se completa con candidatos muy similares
const MIN_SCORE_COMPLETAR = 0.65

// DEMO: revisar después — competencias absurdas que siguen apareciendo
const EXCLUDED_LABELS = new Set([
  'criar cabras', 'caza', 'reaseguro', 'hacer piercings', 'colocar pendulos',
])

const LANGUAGES = [
  'ingles', 'frances', 'aleman', 'italiano', 'portugues', 'chino', 'mandarin', 'japones',
  'ruso', 'arabe', 'hebreo', 'albanes', 'griego', 'latin', 'neerlandes', 'holandes',
  'sueco', 'noruego', 'danes', 'finlandes', 'fines', 'polaco', 'checo', 'eslovaco',
  'hungaro', 'rumano', 'bulgaro', 'turco', 'coreano', 'hindi', 'catalan', 'gallego',
  'euskera', 'vasco', 'javanes', 'croata', 'serbio', 'esloveno', 'ucraniano', 'persa',
  'estonio', 'leton', 'lituano', 'islandes', 'irlandes', 'gales', 'maltes', 'guarani',
  'quechua', 'tailandes', 'vietnamita', 'indonesio', 'malayo', 'swahili', 'urdu', 'bengali',
]
const LANG_RE = LANGUAGES.join('|')
const LANG_SKILL_RE = new RegExp(
  `^((escribir|hablar|comprender|leer|entender|traducir|interactuar verbalmente)( en)?( el| la)? )?(lengua )?(${LANG_RE})( \\(.*\\))?$`
)
const TEXT_MENTIONS_LANG_RE = new RegExp(`\\b(idioma|idiomas|lengua|lenguas|bilingue|${LANG_RE})\\b`)

type SkillHit = { uri: string; label: string; score: number; keyword: string }

function normalize(s: string): string {
  return s.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '').trim()
}

/** Descarta exclusiones DEMO, idiomas no mencionados y lo que no llega al piso de 0.55. */
function hardFilter(hits: SkillHit[], text: string): SkillHit[] {
  const allowLanguages = TEXT_MENTIONS_LANG_RE.test(normalize(text))
  return hits.filter(h => {
    const label = normalize(h.label)
    if (EXCLUDED_LABELS.has(label)) return false
    if (!allowLanguages && LANG_SKILL_RE.test(label)) return false
    return h.score >= MIN_SCORE_FLOOR
  })
}

/** Selección del LLM con tope de 8; si quedó con menos de 3, completa con candidatos ≥ 0.65. */
function completarSeleccion(seleccion: SkillHit[], candidatos: SkillHit[]): SkillHit[] {
  const result = seleccion.slice(0, MAX_RESULTS)
  const elegidos = new Set(result.map(h => h.uri))
  for (const c of candidatos) {  // ordenados por score
    if (result.length >= MIN_RESULTS) break
    if (c.score >= MIN_SCORE_COMPLETAR && !elegidos.has(c.uri)) result.push(c)
  }
  return result
}

/** Aplica exclusiones, filtro de idiomas, umbral por modo y tope de 8. */
function filterNoise(hits: SkillHit[], text: string, minScore: number): SkillHit[] {
  const candidates = hardFilter(hits, text)
  const strong = candidates.filter(h => h.score >= minScore)
  if (strong.length >= MIN_RESULTS) return strong.slice(0, MAX_RESULTS)
  // candidates está ordenado por score: completar hasta 3 con los de >= 0.55
  return candidates.slice(0, MIN_RESULTS)
}

// ============================================================
// Step 1: Groq generates technical keywords
// ============================================================

async function extractKeywordsWithLLM(text: string): Promise<string[]> {
  const groq = getGroq()
  if (!groq) throw new Error('Groq not configured')

  const completion = await groq.chat.completions.create({
    model: GROQ_MODEL_FAST,
    max_completion_tokens: 1024,
    temperature: 0.1,
    reasoning_effort: 'low',
    response_format: { type: 'json_object' },
    messages: [
      {
        role: 'system',
        content: `Dado un texto con experiencia laboral, generá 5-8 términos técnicos para buscar skills en la taxonomía ESCO.
Usá vocabulario técnico formal, no coloquial: preferí verbos de tarea concretos ("colocar ladrillos") antes que nombres de área ("albañilería").

Ejemplos:
- Input: 'pongo inyecciones y tomo la presión'
  Output: {"terminos": ["administrar medicación", "medir signos vitales", "técnicas de enfermería", "cuidados de salud"]}

- Input: 'hago páginas web con Python'
  Output: {"terminos": ["desarrollo web", "programación Python", "bases de datos", "aplicaciones informáticas"]}

- Input: 'levanto paredes y hago revoques'
  Output: {"terminos": ["colocar ladrillos", "construir muros de mampostería", "aplicar revoque en paredes", "mezclar morteros para construcción"]}

Retorná SOLO un objeto JSON con la clave "terminos" (array de strings). Sin explicación.`
      },
      { role: 'user', content: text }
    ]
  }, { timeout: GROQ_TIMEOUT_MS, maxRetries: 0 })

  // Solo content: el reasoning del modelo no se lee
  const raw = completion.choices[0]?.message?.content?.trim() ?? '{}'
  try {
    const cleaned = raw.replace(/```json|```/g, '').trim()
    const parsed = JSON.parse(cleaned)
    const terms = Array.isArray(parsed) ? parsed : parsed?.terminos
    if (Array.isArray(terms)) {
      return terms.filter((s: unknown): s is string => typeof s === 'string' && s.length > 2).slice(0, 8)
    }
  } catch {
    const matches = raw.match(/"([^"]+)"/g)
    if (matches) return matches.map(m => m.replace(/"/g, '')).slice(0, 8)
  }
  return []
}

// ============================================================
// Step 1b: Groq selecciona, entre los candidatos, los que el texto respalda
// ============================================================

/**
 * Devuelve los candidatos que el relato respalda explícitamente (en el orden recibido),
 * o null si Groq falla, vence o no devuelve una selección válida.
 */
async function selectSupportedWithLLM(text: string, candidates: SkillHit[]): Promise<SkillHit[] | null> {
  const groq = getGroq()
  if (!groq || candidates.length === 0) return null
  try {
    const lista = candidates.map((c, i) => `${i + 1}. ${c.label}`).join('\n')
    const completion = await groq.chat.completions.create({
      model: GROQ_MODEL_FAST,
      max_completion_tokens: 1024,
      temperature: 0,
      reasoning_effort: 'low',
      response_format: { type: 'json_object' },
      messages: [
        {
          role: 'system',
          content: `Te paso el relato de experiencia laboral de una persona y una lista numerada de competencias candidatas.
Elegí SOLO las competencias que el relato respalda explícitamente: tareas o conocimientos que la persona dice que hace o hizo.
Cuenta como respaldada la forma técnica de una tarea que el relato menciona ("levanto paredes" respalda "colocar ladrillos"; "tomo la presión" respalda "medir la presión sanguínea"; "cobraba" respalda "tramitar pagos").
Descartá las que agregan tareas, materiales u oficios que el relato no menciona, las que solo comparten una palabra con el relato pero hablan de otra cosa (por ejemplo "presión del agua" para "tomo la presión") y las de un nivel de responsabilidad que el relato no menciona (por ejemplo "supervisar obras" si solo dice que levanta paredes).
Retorná SOLO un objeto JSON {"indices": [números de la lista]}. Sin explicación.`,
        },
        { role: 'user', content: `RELATO:\n${text}\n\nCANDIDATAS:\n${lista}` },
      ],
    }, { timeout: GROQ_TIMEOUT_MS, maxRetries: 0 })

    const raw = completion.choices[0]?.message?.content?.trim() ?? '{}'
    const indices = JSON.parse(raw.replace(/```json|```/g, '').trim())?.indices
    if (!Array.isArray(indices)) return null
    const elegidos = new Set(indices.filter((n: unknown): n is number => Number.isInteger(n)).map((n: number) => n - 1))
    const seleccion = candidates.filter((_, i) => elegidos.has(i))
    return seleccion.length > 0 ? seleccion : null
  } catch (err: any) {
    console.error('LLM selection fallback:', err?.message || err)
    return null
  }
}

// ============================================================
// Step 2: VPS BGE-M3 generates embeddings (batch)
// ============================================================

async function embedTexts(texts: string[]): Promise<number[][]> {
  const res = await fetch(`${VPS_EMBED_URL}/embed`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'x-embed-secret': VPS_EMBED_SECRET,
    },
    body: JSON.stringify({ texts }),
    signal: AbortSignal.timeout(EMBED_TIMEOUT_MS),
  })
  if (!res.ok) throw new Error(`Embed server error: ${res.status}`)
  const data = await res.json()
  return data.embeddings
}

// ============================================================
// Step 3: pgvector search per embedding
// ============================================================

async function searchByVector(embedding: number[], limit: number, threshold: number) {
  if (!supabase) return []
  const { data } = await supabase.rpc('match_skills_by_embedding', {
    query_embedding: embedding,
    match_threshold: threshold,
    match_count: limit,
  })
  return data ?? []
}

/** Embebe los textos, busca por vector y deduplica por URI (gana el mejor score). */
async function searchSkills(texts: string[], limit: number, threshold: number): Promise<SkillHit[]> {
  const embeddings = await embedTexts(texts)
  const searchResults = await Promise.all(
    embeddings.map(emb => searchByVector(emb, limit, threshold))
  )

  // Dedup por label normalizado (que también deduplica por URI): ESCO tiene URIs
  // distintas con la misma etiqueta ("gestionar el inventario de vehículos" ×2)
  const skillMap = new Map<string, SkillHit>()
  for (let i = 0; i < searchResults.length; i++) {
    for (const skill of searchResults[i]) {
      const key = normalize(skill.skill_label)
      const existing = skillMap.get(key)
      if (!existing || skill.similarity > existing.score) {
        skillMap.set(key, {
          uri: skill.skill_uri,
          label: skill.skill_label,
          score: skill.similarity,
          keyword: texts[i],
        })
      }
    }
  }

  return Array.from(skillMap.values())
    .sort((a, b) => b.score - a.score)
    .slice(0, 20)
}

function toResults(hits: SkillHit[]) {
  return hits.map(s => ({
    id: s.uri, uri: s.uri, label: s.label,
    type: 'skill', description: '', source: 'esco',
    L1: '', L2: '',
    confidence: (s.score >= 0.7 ? 'high' : s.score >= 0.5 ? 'medium' : 'low') as 'high' | 'medium' | 'low',
    matchedKeyword: s.keyword,
  }))
}

// ============================================================
// Fallback sin LLM: frases del propio texto → BGE-M3
// ============================================================

/** Parte el relato en frases (comas, " y ", punto, punto y coma, saltos de línea). */
function splitPhrases(text: string): string[] {
  const phrases = text
    .split(/[,.;\n]+|\s+y\s+/i)
    .map(p => p.trim())
    .filter(p => p.length >= 4)
  return [...new Set(phrases)].slice(0, 10)
}

// ============================================================
// POST handler
// ============================================================

export async function POST(request: NextRequest) {
  const rateLimited = requireRateLimit(request, 'public')
  if (rateLimited) return rateLimited

  if (!supabase) {
    return NextResponse.json({ error: 'Supabase not configured' }, { status: 500 })
  }

  try {
    // Precalentamiento: despierta el VPS de embeddings sin procesar nada
    if (request.nextUrl.searchParams.get('warmup') === '1') {
      const ok = await fetch(`${VPS_EMBED_URL}/health`, { signal: AbortSignal.timeout(EMBED_TIMEOUT_MS) })
        .then(r => r.ok)
        .catch(() => false)
      return NextResponse.json({ warmup: true, vps: ok })
    }

    const body = await request.json()
    const { text } = body
    // DEMO: ?llm=0 fuerza el fallback sin LLM (para verificar 0.2 aunque Groq ande)
    const skipLLM = request.nextUrl.searchParams.get('llm') === '0'

    if (!text || typeof text !== 'string' || text.trim().length < 5) {
      return NextResponse.json({
        results: [],
        keywords: [],
        message: 'Texto muy corto. Escribí al menos una oración sobre tu experiencia.',
      })
    }

    // === PRIMARY: Groq → VPS embed → pgvector ===
    let llmError: string | undefined
    if (!skipLLM) {
      try {
        const keywords = await extractKeywordsWithLLM(text)
        if (keywords.length === 0) throw new Error('LLM returned empty keywords')

        // Candidatos (máx. 20) → Groq elige los que el texto respalda; si falla o vence,
        // quedan los candidatos con el filtro por umbral
        // Consultas: keywords del LLM + frases del propio relato (más candidatos concretos,
        // p.ej. "hago revoques"); la selección descarta los que no corresponden
        const consultas = [...new Set([...keywords, ...splitPhrases(text)])]
        const candidatos = await searchSkills(consultas, 5, 0.4)
        const filtrados = hardFilter(candidatos, text)
        const seleccion = await selectSupportedWithLLM(text, filtrados)
        const hits = seleccion ? completarSeleccion(seleccion, filtrados) : filterNoise(candidatos, text, MIN_SCORE_LLM)
        return NextResponse.json({
          results: toResults(hits),
          keywords: consultas,
          method: seleccion ? 'llm+bge-m3+seleccion' : 'llm+bge-m3',
          text_length: text.length,
        })
      } catch (err: any) {
        llmError = err?.message || String(err)
        console.error('LLM pipeline fallback:', llmError)
      }
    }

    // === FALLBACK 1: frases del texto → VPS embed → pgvector (sin LLM) ===
    const phrases = splitPhrases(text)
    if (phrases.length === 0) {
      return NextResponse.json({ results: [], keywords: [], method: 'bge-m3', message: NO_INTERPRETADO })
    }
    try {
      const hits = filterNoise(await searchSkills(phrases, 4, 0.55), text, MIN_SCORE_FALLBACK)
      return NextResponse.json({
        results: toResults(hits),
        keywords: phrases,
        method: 'bge-m3',
        text_length: text.length,
        ...(hits.length === 0 && { message: NO_INTERPRETADO }),
        ...(llmError && { _fallbackReason: llmError }),
      })
    } catch (err: any) {
      // === FALLBACK 2: VPS caído → sin resultados (el trigram devolvía basura) ===
      console.error('BGE-M3 fallback failed:', err?.message || err)
      return NextResponse.json({
        results: [],
        keywords: [],
        method: 'fallback',
        message: NO_INTERPRETADO,
        _fallbackReason: err?.message,
      })
    }
  } catch (error) {
    console.error('Error extracting skills from text:', error)
    return NextResponse.json({ error: 'Error processing text' }, { status: 500 })
  }
}
