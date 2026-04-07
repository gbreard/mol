import { NextRequest, NextResponse } from 'next/server'
import { requireRateLimit } from '@/lib/api-auth'
import { createClient } from '@supabase/supabase-js'
import Groq from 'groq-sdk'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || ''
const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY || process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || ''

const supabase = supabaseUrl && supabaseKey
  ? createClient(supabaseUrl, supabaseKey)
  : null

let _groq: Groq | null = null
function getGroq(): Groq | null {
  if (_groq) return _groq
  const key = process.env.GROQ_API_KEY
  if (!key) return null
  _groq = new Groq({ apiKey: key })
  return _groq
}

const VPS_EMBED_URL = process.env.VPS_EMBED_URL || 'http://187.124.150.28:8082'
const VPS_EMBED_SECRET = process.env.VPS_EMBED_SECRET || ''

// ============================================================
// Step 1: Groq generates technical keywords
// ============================================================

async function extractKeywordsWithLLM(text: string): Promise<string[]> {
  const groq = getGroq()
  if (!groq) throw new Error('Groq not configured')

  const completion = await groq.chat.completions.create({
    model: 'llama-3.1-8b-instant',
    max_tokens: 150,
    temperature: 0.1,
    messages: [
      {
        role: 'system',
        content: `Dado un texto con experiencia laboral, generá 5-8 términos técnicos para buscar skills en la taxonomía ESCO.
Usá vocabulario técnico formal, no coloquial.

Ejemplos:
- Input: 'pongo inyecciones y tomo la presión'
  Output: ["administrar medicación", "medir signos vitales", "técnicas de enfermería", "cuidados de salud"]

- Input: 'hago páginas web con Python'
  Output: ["desarrollo web", "programación Python", "bases de datos", "aplicaciones informáticas"]

- Input: 'levanto paredes y hago revoques'
  Output: ["albañilería", "construcción de mampostería", "aplicar revoque", "trabajo en construcción"]

Retorná SOLO un JSON array de strings. Sin explicación.`
      },
      { role: 'user', content: text }
    ]
  })

  const raw = completion.choices[0]?.message?.content?.trim() ?? '[]'
  try {
    const cleaned = raw.replace(/```json|```/g, '').trim()
    const parsed = JSON.parse(cleaned)
    if (Array.isArray(parsed)) {
      return parsed.filter(s => typeof s === 'string' && s.length > 2).slice(0, 8)
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
    signal: AbortSignal.timeout(10000),
  })
  if (!res.ok) throw new Error(`Embed server error: ${res.status}`)
  const data = await res.json()
  return data.embeddings
}

// ============================================================
// Step 3: pgvector search per embedding
// ============================================================

async function searchByVector(embedding: number[], limit: number = 5) {
  if (!supabase) return []
  const { data } = await supabase.rpc('match_skills_by_embedding', {
    query_embedding: embedding,
    match_threshold: 0.4,
    match_count: limit,
  })
  return data ?? []
}

// ============================================================
// Fallback: keyword extraction (original method)
// ============================================================

function extractKeywords(text: string): string[] {
  const stopwords = new Set([
    'que', 'como', 'para', 'por', 'con', 'sin', 'una', 'uno', 'los', 'las',
    'del', 'den', 'des', 'fue', 'ser', 'son', 'era', 'hay', 'mas', 'pero',
    'este', 'esta', 'esto', 'esos', 'esas', 'todo', 'toda', 'muy', 'bien',
    'hace', 'hice', 'desde', 'hasta', 'entre', 'sobre', 'donde', 'cuando',
    'trabaje', 'trabajo', 'trabajar', 'trabajando', 'anos', 'anios', 'tiempo',
    'empresa', 'empresas', 'lugar', 'area', 'zona', 'puesto', 'cargo',
    'tambien', 'siempre', 'nunca', 'algo', 'mucho', 'poco', 'otro', 'otra',
    'tengo', 'tiene', 'hacer', 'hago', 'hacia', 'haciendo', 'saber', 'sabia',
    'conozco', 'conocimiento', 'experiencia', 'encargaba', 'responsable',
    'sabe', 'sabes', 'pueden', 'puede', 'cosas', 'cosa',
  ])

  const normalized = text.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '')
  const words = normalized
    .replace(/[^a-z0-9\s]/g, ' ')
    .split(/\s+/)
    .filter(w => w.length >= 4 && !stopwords.has(w))

  return [...new Set(words)]
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
    const body = await request.json()
    const { text } = body

    if (!text || typeof text !== 'string' || text.trim().length < 5) {
      return NextResponse.json({
        results: [],
        keywords: [],
        message: 'Texto muy corto. Escribí al menos una oración sobre tu experiencia.',
      })
    }

    // === PRIMARY: Groq → VPS embed → pgvector ===
    try {
      // Step 1: Groq keywords
      const keywords = await extractKeywordsWithLLM(text)
      if (keywords.length === 0) throw new Error('LLM returned empty keywords')

      // Step 2: VPS batch embedding
      const embeddings = await embedTexts(keywords)

      // Step 3: pgvector search in parallel
      const searchResults = await Promise.all(
        embeddings.map(emb => searchByVector(emb, 5))
      )

      // Step 4: Deduplicate by URI, keep best score
      const skillMap = new Map<string, { uri: string; label: string; score: number; keyword: string }>()
      for (let i = 0; i < searchResults.length; i++) {
        for (const skill of searchResults[i]) {
          const existing = skillMap.get(skill.skill_uri)
          if (!existing || skill.similarity > existing.score) {
            skillMap.set(skill.skill_uri, {
              uri: skill.skill_uri,
              label: skill.skill_label,
              score: skill.similarity,
              keyword: keywords[i],
            })
          }
        }
      }

      const sorted = Array.from(skillMap.values())
        .sort((a, b) => b.score - a.score)
        .slice(0, 20)

      return NextResponse.json({
        results: sorted.map(s => ({
          id: s.uri, uri: s.uri, label: s.label,
          type: 'skill', description: '', source: 'esco',
          L1: '', L2: '',
          confidence: (s.score >= 0.7 ? 'high' : s.score >= 0.5 ? 'medium' : 'low') as 'high' | 'medium' | 'low',
          matchedKeyword: s.keyword,
        })),
        keywords,
        method: 'llm+bge-m3',
        text_length: text.length,
      })
    } catch (err: any) {
      console.error('BGE-M3 pipeline fallback:', err?.message || err)

      // === FALLBACK: keyword extraction + trigram ===
      const keywords = extractKeywords(text)
      if (keywords.length === 0) {
        return NextResponse.json({
          results: [], keywords: [], method: 'fallback',
          message: 'No se identificaron competencias en el texto.',
        })
      }

      const skillMap = new Map<string, { uri: string; label: string; score: number; keyword: string }>()
      for (const keyword of keywords) {
        const { data } = await supabase.rpc('search_skills_by_text', {
          query_text: keyword, similarity_min: 0.2, max_results: 5,
        })
        for (const r of (data || [])) {
          const existing = skillMap.get(r.skill_uri)
          const newScore = r.text_similarity + (existing?.score || 0)
          if (!existing || newScore > existing.score) {
            skillMap.set(r.skill_uri, { uri: r.skill_uri, label: r.skill_label, score: newScore, keyword })
          }
        }
      }

      return NextResponse.json({
        results: Array.from(skillMap.values())
          .sort((a, b) => b.score - a.score)
          .slice(0, 20)
          .map(s => ({
            id: s.uri, uri: s.uri, label: s.label,
            type: 'skill', description: '', source: 'esco',
            L1: '', L2: '',
            confidence: (s.score >= 0.5 ? 'high' : s.score >= 0.3 ? 'medium' : 'low') as 'high' | 'medium' | 'low',
            matchedKeyword: s.keyword,
          })),
        keywords,
        method: 'fallback',
        text_length: text.length,
        _fallbackReason: err?.message,
      })
    }
  } catch (error) {
    console.error('Error extracting skills from text:', error)
    return NextResponse.json({ error: 'Error processing text' }, { status: 500 })
  }
}
