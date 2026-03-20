import { NextRequest, NextResponse } from 'next/server'
import { requireRateLimit } from '@/lib/api-auth'
import { promises as fs } from 'fs'
import path from 'path'

interface CatalogSkill {
  id: string
  label: string
  type: string
  L1: string
  L2: string
  essential: number
  optional: number
  total: number
  description: string
  source: 'esco' | 'argentina_emerging'
  occupations_count?: number
}

interface ExtractedSkill {
  id: string
  label: string
  type: string
  description: string
  source: 'esco' | 'argentina_emerging'
  L1: string
  L2: string
  confidence: 'high' | 'medium' | 'low'
  matchedKeyword: string  // qué palabra del texto matcheó
}

// Cache
let catalogCache: CatalogSkill[] | null = null
let keywordIndex: Map<string, CatalogSkill[]> | null = null

async function loadCatalog(): Promise<CatalogSkill[]> {
  if (catalogCache) return catalogCache
  const filePath = path.join(process.cwd(), 'public', 'data', 'skills_searchable.json')
  const raw = await fs.readFile(filePath, 'utf-8')
  const data = JSON.parse(raw)
  catalogCache = data.skills as CatalogSkill[]
  return catalogCache
}

function normalize(text: string): string {
  return text.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '')
}

/**
 * Construye un índice invertido: keyword → skills que contienen esa keyword en su label.
 * Se construye una vez y se cachea.
 */
async function getKeywordIndex(): Promise<Map<string, CatalogSkill[]>> {
  if (keywordIndex) return keywordIndex

  const catalog = await loadCatalog()
  keywordIndex = new Map()

  for (const skill of catalog) {
    // Extraer palabras significativas del label (>= 4 chars)
    const words = normalize(skill.label)
      .split(/\s+/)
      .filter(w => w.length >= 4)

    for (const word of words) {
      if (!keywordIndex.has(word)) {
        keywordIndex.set(word, [])
      }
      keywordIndex.get(word)!.push(skill)
    }
  }

  return keywordIndex
}

/**
 * Extrae keywords significativas del texto del usuario.
 * Filtra stopwords y palabras cortas.
 */
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
  ])

  const normalized = normalize(text)
  const words = normalized
    .replace(/[^a-z0-9\s]/g, ' ')
    .split(/\s+/)
    .filter(w => w.length >= 4 && !stopwords.has(w))

  // Deduplicate preservando orden
  return [...new Set(words)]
}

/**
 * POST /api/skills-extract-from-text
 * Body: { text: string }
 *
 * Extrae skills del texto libre del trabajador.
 * Fase 1: extrae keywords del texto → busca en índice invertido del catálogo.
 * Fase 2 (futuro): embeddings del texto completo contra embeddings de skills.
 *
 * Retorna skills encontradas con nivel de confianza:
 * - high: keyword matchea exacto con label de skill
 * - medium: keyword es parte del label
 * - low: keyword matchea solo en description
 */
export async function POST(request: NextRequest) {
  const rateLimited = requireRateLimit(request, 'public')
  if (rateLimited) return rateLimited

  try {
    const body = await request.json()
    const { text } = body

    if (!text || typeof text !== 'string' || text.trim().length < 10) {
      return NextResponse.json({
        results: [],
        keywords: [],
        message: 'Texto muy corto. Escribí al menos una oración sobre tu experiencia.',
      })
    }

    const index = await getKeywordIndex()
    const catalog = await loadCatalog()
    const keywords = extractKeywords(text)

    if (keywords.length === 0) {
      return NextResponse.json({
        results: [],
        keywords: [],
        message: 'No se identificaron términos laborales en el texto.',
      })
    }

    // Buscar skills por cada keyword
    const skillScores = new Map<string, { skill: CatalogSkill; score: number; matchedKeyword: string }>()

    for (const keyword of keywords) {
      // Búsqueda exacta en índice
      const exactMatches = index.get(keyword) || []
      for (const skill of exactMatches) {
        const existing = skillScores.get(skill.id)
        const score = (existing?.score || 0) + 3  // peso alto por match exacto en label
        skillScores.set(skill.id, {
          skill,
          score,
          matchedKeyword: existing?.matchedKeyword || keyword,
        })
      }

      // Búsqueda parcial en label (keyword contenido en label)
      if (exactMatches.length === 0) {
        for (const skill of catalog) {
          const normLabel = normalize(skill.label)
          if (normLabel.includes(keyword) && !skillScores.has(skill.id)) {
            skillScores.set(skill.id, { skill, score: 2, matchedKeyword: keyword })
          }
        }
      }
    }

    // Ordenar por score y limitar
    const sorted = Array.from(skillScores.values())
      .sort((a, b) => b.score - a.score)
      .slice(0, 30)

    const results: ExtractedSkill[] = sorted.map(({ skill, score, matchedKeyword }) => ({
      id: skill.id,
      label: skill.label,
      type: skill.type,
      description: skill.description || '',
      source: skill.source || 'esco',
      L1: skill.L1,
      L2: skill.L2,
      confidence: score >= 3 ? 'high' : score >= 2 ? 'medium' : 'low',
      matchedKeyword,
    }))

    return NextResponse.json({
      results,
      keywords,
      text_length: text.length,
      catalog_size: catalog.length,
    })
  } catch (error) {
    console.error('Error extracting skills from text:', error)
    return NextResponse.json(
      { error: 'Error processing text' },
      { status: 500 }
    )
  }
}
