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

const GROQ_TIMEOUT_MS = 2500
const EMBED_TIMEOUT_MS = 4000

// Filtro de ruido: máximo 8, umbral por modo; si quedan menos de 3, se completa hasta 3 con >= 0.55
const MAX_RESULTS = 8
const MIN_RESULTS = 3
const MIN_SCORE_LLM = 0.60
const MIN_SCORE_FALLBACK = 0.62
const MIN_SCORE_FLOOR = 0.55

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

/** Aplica exclusiones, filtro de idiomas, umbral por modo y tope de 8. */
function filterNoise(hits: SkillHit[], text: string, minScore: number): SkillHit[] {
  const allowLanguages = TEXT_MENTIONS_LANG_RE.test(normalize(text))
  const candidates = hits.filter(h => {
    const label = normalize(h.label)
    if (EXCLUDED_LABELS.has(label)) return false
    if (!allowLanguages && LANG_SKILL_RE.test(label)) return false
    return h.score >= MIN_SCORE_FLOOR
  })
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
Usá vocabulario técnico formal, no coloquial.

Ejemplos:
- Input: 'pongo inyecciones y tomo la presión'
  Output: {"terminos": ["administrar medicación", "medir signos vitales", "técnicas de enfermería", "cuidados de salud"]}

- Input: 'hago páginas web con Python'
  Output: {"terminos": ["desarrollo web", "programación Python", "bases de datos", "aplicaciones informáticas"]}

- Input: 'levanto paredes y hago revoques'
  Output: {"terminos": ["albañilería", "construcción de mampostería", "aplicar revoque", "trabajo en construcción"]}

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

  const skillMap = new Map<string, SkillHit>()
  for (let i = 0; i < searchResults.length; i++) {
    for (const skill of searchResults[i]) {
      const existing = skillMap.get(skill.skill_uri)
      if (!existing || skill.similarity > existing.score) {
        skillMap.set(skill.skill_uri, {
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

        const hits = filterNoise(await searchSkills(keywords, 5, 0.4), text, MIN_SCORE_LLM)
        return NextResponse.json({
          results: toResults(hits),
          keywords,
          method: 'llm+bge-m3',
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
