import { NextRequest, NextResponse } from 'next/server'
import { requireRateLimit } from '@/lib/api-auth'
import { promises as fs } from 'fs'
import path from 'path'

/**
 * Skill del catálogo unificado (ESCO + emergentes argentinas)
 */
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
  alt_labels?: string[]
  equivalence_id?: string
}

interface SkillSearchResult {
  id: string
  label: string
  type: string
  description: string
  source: 'esco' | 'argentina_emerging'
  L1: string
  L2: string
  frequency: number  // essential + optional (ESCO) o occupations_count (emergente)
  matchType: 'label' | 'description'  // dónde matcheó
}

// Cache del catálogo en memoria (se carga una vez)
let catalogCache: CatalogSkill[] | null = null

async function loadCatalog(): Promise<CatalogSkill[]> {
  if (catalogCache) return catalogCache

  const filePath = path.join(process.cwd(), 'public', 'data', 'skills_searchable.json')
  const raw = await fs.readFile(filePath, 'utf-8')
  const data = JSON.parse(raw)
  catalogCache = data.skills as CatalogSkill[]
  return catalogCache
}

/**
 * Normaliza texto para búsqueda: lowercase, sin acentos
 */
function normalize(text: string): string {
  return text
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
}

/**
 * GET /api/skills-search?q=soldar&limit=20
 *
 * Búsqueda full-text en el catálogo unificado (16,633 skills).
 * Busca en label Y en description.
 * Retorna resultados ordenados: primero label match, después description match.
 *
 * Fase 1: búsqueda por substring normalizado.
 * Fase 2 (futuro): embeddings pre-calculados para matching semántico.
 */
export async function GET(request: NextRequest) {
  // Rate limit (público)
  const rateLimited = requireRateLimit(request, 'public')
  if (rateLimited) return rateLimited

  const { searchParams } = new URL(request.url)
  const query = searchParams.get('q')?.trim()
  const limitStr = searchParams.get('limit') || '20'
  const limit = Math.min(parseInt(limitStr, 10) || 20, 50)

  if (!query || query.length < 2) {
    return NextResponse.json({ results: [], query: query || '' })
  }

  try {
    const catalog = await loadCatalog()
    const normalizedQuery = normalize(query)

    // Separar en tokens para multi-palabra
    const tokens = normalizedQuery.split(/\s+/).filter(t => t.length >= 2)
    if (tokens.length === 0) {
      return NextResponse.json({ results: [], query })
    }

    // Buscar: primero label match, después description match
    const labelMatches: SkillSearchResult[] = []
    const descMatches: SkillSearchResult[] = []

    for (const skill of catalog) {
      const normalizedLabel = normalize(skill.label)
      const normalizedDesc = normalize(skill.description || '')
      // Also check alt_labels (equivalence variants)
      const normalizedAlts = (skill.alt_labels || []).map(normalize)

      // Todos los tokens deben matchear en label, alt_labels O description
      const allTokensInLabel = tokens.every(t => normalizedLabel.includes(t))
      const allTokensInAlts = normalizedAlts.some(alt => tokens.every(t => alt.includes(t)))
      const allTokensInDesc = tokens.every(t => normalizedDesc.includes(t))
      // Al menos un token en label/alts + resto en desc (match parcial)
      const someTokensInLabel = tokens.some(t =>
        normalizedLabel.includes(t) || normalizedAlts.some(alt => alt.includes(t))
      )
      const allTokensSomewhere = tokens.every(t =>
        normalizedLabel.includes(t) ||
        normalizedAlts.some(alt => alt.includes(t)) ||
        normalizedDesc.includes(t)
      )

      if (!allTokensSomewhere) continue

      const result: SkillSearchResult = {
        id: skill.id,
        label: skill.label,
        type: skill.type,
        description: skill.description || '',
        source: skill.source || 'esco',
        L1: skill.L1,
        L2: skill.L2,
        frequency: skill.source === 'argentina_emerging'
          ? (skill.occupations_count || 0)
          : (skill.essential + skill.optional),
        matchType: allTokensInLabel ? 'label' : 'description',
      }

      if (allTokensInLabel || allTokensInAlts) {
        labelMatches.push(result)
      } else if (someTokensInLabel && allTokensSomewhere) {
        // Tokens split between label and description — prioritize
        labelMatches.push({ ...result, matchType: 'label' })
      } else {
        descMatches.push(result)
      }
    }

    // Ordenar cada grupo por frecuencia (más usado primero)
    labelMatches.sort((a, b) => b.frequency - a.frequency)
    descMatches.sort((a, b) => b.frequency - a.frequency)

    // Label matches primero, después description matches
    const results = [...labelMatches, ...descMatches].slice(0, limit)

    return NextResponse.json({
      results,
      query,
      total: labelMatches.length + descMatches.length,
      catalog_size: catalog.length,
    })
  } catch (error) {
    console.error('Error searching skills:', error)
    return NextResponse.json(
      { error: 'Error searching skills' },
      { status: 500 }
    )
  }
}
