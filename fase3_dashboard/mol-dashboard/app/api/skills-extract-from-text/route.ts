import { NextRequest, NextResponse } from 'next/server'
import { requireRateLimit } from '@/lib/api-auth'
import { createClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || ''
const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || ''

const supabase = supabaseUrl && supabaseKey
  ? createClient(supabaseUrl, supabaseKey)
  : null

interface ExtractedSkill {
  id: string
  label: string
  type: string
  description: string
  source: string
  L1: string
  L2: string
  confidence: 'high' | 'medium' | 'low'
  matchedKeyword: string
  uri: string
}

function normalize(text: string): string {
  return text.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '')
}

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

  const normalized = normalize(text)
  const words = normalized
    .replace(/[^a-z0-9\s]/g, ' ')
    .split(/\s+/)
    .filter(w => w.length >= 4 && !stopwords.has(w))

  return [...new Set(words)]
}

/**
 * POST /api/skills-extract-from-text
 * Body: { text: string }
 *
 * Extrae skills del texto libre usando:
 * 1. pg_trgm (trigrams) para buscar skills similares por label
 * 2. pgvector para expandir con skills semánticamente relacionadas
 */
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

    const keywords = extractKeywords(text)

    if (keywords.length === 0) {
      return NextResponse.json({
        results: [],
        keywords: [],
        message: 'No se identificaron términos laborales en el texto.',
      })
    }

    // Step 1: Search skills by trigram similarity for each keyword
    const skillMap = new Map<string, { uri: string; label: string; score: number; keyword: string }>()

    for (const keyword of keywords) {
      const { data: trgmResults } = await supabase.rpc('search_skills_by_text', {
        query_text: keyword,
        similarity_min: 0.2,
        max_results: 5,
      })

      for (const r of (trgmResults || [])) {
        const existing = skillMap.get(r.skill_uri)
        const newScore = r.text_similarity + (existing?.score || 0)
        if (!existing || newScore > existing.score) {
          skillMap.set(r.skill_uri, {
            uri: r.skill_uri,
            label: r.skill_label,
            score: newScore,
            keyword: existing?.keyword || keyword,
          })
        }
      }
    }

    // Step 2: For top trigram matches, expand with semantic neighbors via pgvector
    const topUris = Array.from(skillMap.values())
      .sort((a, b) => b.score - a.score)
      .slice(0, 8)
      .map(s => s.uri)

    if (topUris.length > 0) {
      const { data: expanded } = await supabase.rpc('expand_skills_semantic', {
        skill_uris: topUris,
        similarity_threshold: 0.75,
        max_per_skill: 3,
      })

      for (const r of (expanded || [])) {
        if (r.is_exact) continue
        if (skillMap.has(r.expanded_uri)) continue
        skillMap.set(r.expanded_uri, {
          uri: r.expanded_uri,
          label: r.expanded_label,
          score: r.similarity * 0.8,
          keyword: `≈ ${r.original_label}`,
        })
      }
    }

    // Step 3: Sort and format results
    const sorted = Array.from(skillMap.values())
      .sort((a, b) => b.score - a.score)
      .slice(0, 20)

    const results: ExtractedSkill[] = sorted.map(s => ({
      id: s.uri,
      uri: s.uri,
      label: s.label,
      type: 'skill',
      description: '',
      source: 'esco',
      L1: '',
      L2: '',
      confidence: s.score >= 0.5 ? 'high' : s.score >= 0.3 ? 'medium' : 'low',
      matchedKeyword: s.keyword,
    }))

    return NextResponse.json({
      results,
      keywords,
      text_length: text.length,
    })
  } catch (error) {
    console.error('Error extracting skills from text:', error)
    return NextResponse.json({ error: 'Error processing text' }, { status: 500 })
  }
}
