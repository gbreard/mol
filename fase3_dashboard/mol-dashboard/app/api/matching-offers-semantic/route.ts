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
 * GET /api/matching-offers-semantic?skill_uris=uri1,uri2&isco_codes=2411,2512&limit=30&threshold=0.60
 *
 * Matching semántico usando pgvector.
 * 1. Expande skills de la persona con similares semánticos (expand_skills_semantic RPC)
 * 2. Busca ofertas por ISCO codes
 * 3. Calcula match score semántico (exacto + similares)
 */
export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url)
  const skillUris = searchParams.get('skill_uris')?.split(',').filter(Boolean) || []
  const iscoCodes = searchParams.get('isco_codes')?.split(',').filter(Boolean) || []
  const limit = Math.min(parseInt(searchParams.get('limit') || '30', 10), 100)
  const threshold = parseFloat(searchParams.get('threshold') || '0.60')

  if (skillUris.length === 0) {
    return NextResponse.json({ offers: [], total: 0, message: 'skill_uris requerido' })
  }

  if (!supabase) {
    return NextResponse.json({ error: 'Supabase not configured' }, { status: 500 })
  }

  try {
    // Step 1: Expand skills semantically using pgvector
    const { data: expanded, error: expandError } = await supabase.rpc('expand_skills_semantic', {
      skill_uris: skillUris,
      similarity_threshold: threshold,
      max_per_skill: 5,
    })

    if (expandError) throw expandError

    // Build expanded URI map: uri -> { similarity, original_label, is_exact }
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

    // Step 2: Get offers filtered by ISCO codes
    let query = supabase
      .from('ofertas_dashboard')
      .select('id_oferta, titulo, empresa, provincia, isco_code')

    if (iscoCodes.length > 0) {
      query = query.in('isco_code', iscoCodes)
    }

    const { data: ofertas, error: ofertasError } = await query.limit(limit * 2)

    if (ofertasError) throw ofertasError
    if (!ofertas || ofertas.length === 0) {
      return NextResponse.json({ offers: [], total: 0, expanded_skills: allExpandedUris.length })
    }

    const ofertaIds = ofertas.map(o => String(o.id_oferta))
    const ofertaMap = new Map(ofertas.map(o => [String(o.id_oferta), o]))

    // Step 3: Get skills of these offers
    const { data: ofertaSkills, error: skillsError } = await supabase
      .from('ofertas_skills')
      .select('id_oferta, skill_uri, preferred_label')
      .in('id_oferta', ofertaIds)

    if (skillsError) throw skillsError

    // Group skills by offer
    const skillsByOffer = new Map<string, Array<{ skill_uri: string; preferred_label: string }>>()
    for (const row of (ofertaSkills || [])) {
      const oid = String(row.id_oferta)
      if (!skillsByOffer.has(oid)) skillsByOffer.set(oid, [])
      skillsByOffer.get(oid)!.push(row)
    }

    // Step 4: Calculate semantic match scores
    const results: SemanticMatchOffer[] = []

    for (const [oid, skills] of skillsByOffer) {
      const oferta = ofertaMap.get(oid)
      if (!oferta || skills.length === 0) continue

      const detalle: SemanticMatchOffer['skills_detalle'] = []
      let cubiertas = 0

      for (const os of skills) {
        const match = expandedMap.get(os.skill_uri)
        if (match && (match.isExact || match.similarity >= threshold)) {
          cubiertas++
          detalle.push({
            skill: os.preferred_label,
            similarity: Math.round(match.similarity * 1000) / 1000,
            matched_by: match.isExact ? '(exacto)' : match.originalLabel,
            exact: match.isExact,
          })
        }
      }

      if (cubiertas === 0) continue

      const matchScore = Math.round((cubiertas / skills.length) * 1000) / 10

      results.push({
        id_oferta: oid,
        titulo: oferta.titulo || '',
        empresa: oferta.empresa || '',
        provincia: oferta.provincia || '',
        isco_code: oferta.isco_code || '',
        match_score: matchScore,
        skills_cubiertas: cubiertas,
        skills_oferta_total: skills.length,
        skills_detalle: detalle.sort((a, b) => b.similarity - a.similarity),
      })
    }

    // Sort by match score
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
