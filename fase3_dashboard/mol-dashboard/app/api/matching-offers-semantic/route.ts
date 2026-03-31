import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || ''
const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || ''

const supabase = supabaseUrl && supabaseKey
  ? createClient(supabaseUrl, supabaseKey)
  : null

export interface SemanticMatchOffer {
  id_oferta: string
  titulo: string
  empresa: string
  provincia: string
  isco_code: string
  match_score: number
  skills_cubiertas: number
  skills_oferta_total: number
  skills_detalle: Array<{
    skill: string
    similarity: number
    matched_by: string
    exact: boolean
  }>
}

/**
 * GET /api/matching-offers-semantic?skill_uris=uri1,uri2&limit=20&threshold=0.55
 *
 * Matching semántico real con pgvector en 3 pasos:
 * 1. expand_skills_semantic (pgvector cosine en skills_embeddings — 14K rows, <1s)
 * 2. Buscar ofertas que tienen esas skills expandidas (index lookup en ofertas_skills)
 * 3. Calcular match score con info de similaridad del paso 1
 */
export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url)
  const skillUris = searchParams.get('skill_uris')?.split(',').filter(Boolean) || []
  const limit = Math.min(parseInt(searchParams.get('limit') || '20', 10), 100)
  const threshold = parseFloat(searchParams.get('threshold') || '0.55')

  if (skillUris.length === 0) {
    return NextResponse.json({ offers: [], total: 0, message: 'skill_uris requerido' })
  }

  if (!supabase) {
    return NextResponse.json({ error: 'Supabase not configured' }, { status: 500 })
  }

  try {
    // Step 1: Expand skills with pgvector (cosine similarity on 14K embeddings)
    const { data: expanded, error: expandError } = await supabase.rpc('expand_skills_semantic', {
      skill_uris: skillUris,
      similarity_threshold: threshold,
      max_per_skill: 8,
    })

    if (expandError) throw expandError

    // Build map: expanded_uri → { similarity, originalLabel, isExact }
    const expandedMap = new Map<string, { similarity: number; originalLabel: string; isExact: boolean }>()
    for (const row of (expanded || [])) {
      const existing = expandedMap.get(row.expanded_uri)
      if (!existing || row.similarity > existing.similarity) {
        expandedMap.set(row.expanded_uri, {
          similarity: row.similarity,
          originalLabel: row.original_label,
          isExact: row.is_exact,
        })
      }
    }

    const allExpandedUris = Array.from(expandedMap.keys())
    if (allExpandedUris.length === 0) {
      return NextResponse.json({ offers: [], total: 0, expanded_skills: 0 })
    }

    // Step 2: Find offers that have these expanded skills (index lookup, fast)
    const { data: matchedRows, error: matchError } = await supabase
      .from('ofertas_skills')
      .select('id_oferta, skill_uri, preferred_label')
      .in('skill_uri', allExpandedUris)
      .limit(2000)

    if (matchError) throw matchError
    if (!matchedRows || matchedRows.length === 0) {
      return NextResponse.json({ offers: [], total: 0, expanded_skills: allExpandedUris.length })
    }

    // Group by offer
    const byOffer = new Map<string, Array<{ skill_uri: string; preferred_label: string }>>()
    for (const row of matchedRows) {
      const oid = String(row.id_oferta)
      if (!byOffer.has(oid)) byOffer.set(oid, [])
      byOffer.get(oid)!.push(row)
    }

    // Sort by number of matched skills, take top candidates
    const topOfferIds = Array.from(byOffer.entries())
      .sort((a, b) => b[1].length - a[1].length)
      .slice(0, limit * 2)
      .map(([oid]) => oid)

    // Step 3: Get offer details
    const { data: ofertas } = await supabase
      .from('ofertas_dashboard')
      .select('id_oferta, titulo, empresa, provincia, isco_code')
      .in('id_oferta', topOfferIds)

    if (!ofertas || ofertas.length === 0) {
      return NextResponse.json({ offers: [], total: 0, expanded_skills: allExpandedUris.length })
    }

    const ofertaMap = new Map(ofertas.map(o => [String(o.id_oferta), o]))

    // Get total skills per offer for score calculation
    const { data: totalRows } = await supabase
      .from('ofertas_skills')
      .select('id_oferta, skill_uri')
      .in('id_oferta', topOfferIds)

    const totalByOffer = new Map<string, number>()
    for (const row of (totalRows || [])) {
      const oid = String(row.id_oferta)
      totalByOffer.set(oid, (totalByOffer.get(oid) || 0) + 1)
    }

    // Build results with similarity info from pgvector
    const results: SemanticMatchOffer[] = []

    for (const [oid, matchedSkills] of byOffer) {
      const oferta = ofertaMap.get(oid)
      if (!oferta) continue

      const totalSkills = totalByOffer.get(oid) || matchedSkills.length

      const detalle: SemanticMatchOffer['skills_detalle'] = []
      for (const ms of matchedSkills) {
        const match = expandedMap.get(ms.skill_uri)
        if (match) {
          detalle.push({
            skill: ms.preferred_label,
            similarity: Math.round(match.similarity * 1000) / 1000,
            matched_by: match.isExact ? '(exacto)' : match.originalLabel,
            exact: match.isExact,
          })
        }
      }

      if (detalle.length === 0) continue

      detalle.sort((a, b) => b.similarity - a.similarity)
      const matchScore = Math.round((detalle.length / totalSkills) * 1000) / 10

      results.push({
        id_oferta: oid,
        titulo: oferta.titulo || '',
        empresa: oferta.empresa || '',
        provincia: oferta.provincia || '',
        isco_code: oferta.isco_code || '',
        match_score: matchScore,
        skills_cubiertas: detalle.length,
        skills_oferta_total: totalSkills,
        skills_detalle: detalle,
      })
    }

    results.sort((a, b) => b.match_score - a.match_score)

    return NextResponse.json({
      offers: results.slice(0, limit),
      total: results.length,
      expanded_skills: allExpandedUris.length,
      original_skills: skillUris.length,
      threshold,
    })
  } catch (error) {
    console.error('Error semantic matching:', error)
    return NextResponse.json({ error: 'Error en matching semántico' }, { status: 500 })
  }
}
