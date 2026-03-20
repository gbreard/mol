import { NextRequest, NextResponse } from 'next/server'
import { requireRateLimit } from '@/lib/api-auth'
import { createClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || ''
const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || ''

const supabase = supabaseUrl && supabaseKey
  ? createClient(supabaseUrl, supabaseKey)
  : null

export interface MatchingOffer {
  id_oferta: number
  titulo: string
  empresa: string
  provincia: string
  localidad: string
  modalidad: string
  fecha_publicacion: string
  url_oferta: string
  isco_code: string
  esco_occupation_label: string
  match_score: number
  skills_cubiertas: string[]
  skills_gap: string[]
}

/**
 * GET /api/matching-offers?isco_codes=2512,2514&skills=python,sql,docker&provincia=CABA&page=1&limit=20
 *
 * Retorna ofertas de ofertas_dashboard filtradas por ISCO codes (ocupaciones compatibles),
 * con gap personalizado calculado contra las skills del trabajador.
 */
export async function GET(request: NextRequest) {
  const rateLimited = requireRateLimit(request, 'public')
  if (rateLimited) return rateLimited

  const { searchParams } = new URL(request.url)
  const iscoCodes = searchParams.get('isco_codes')?.split(',').filter(Boolean) || []
  const workerSkills = searchParams.get('skills')?.split(',').map(s => s.trim().toLowerCase()).filter(Boolean) || []
  const provincia = searchParams.get('provincia')
  const modalidad = searchParams.get('modalidad')
  const page = parseInt(searchParams.get('page') || '1', 10)
  const limit = Math.min(parseInt(searchParams.get('limit') || '20', 10), 50)

  if (iscoCodes.length === 0) {
    return NextResponse.json({ offers: [], total: 0, message: 'isco_codes requerido' })
  }

  if (!supabase) {
    return NextResponse.json({ error: 'Supabase not configured' }, { status: 500 })
  }

  try {
    // Query ofertas filtradas por ISCO codes
    let query = supabase
      .from('ofertas_dashboard')
      .select('id_oferta, titulo, empresa, provincia, localidad, modalidad, fecha_publicacion_iso, url_oferta, isco_code, esco_occupation_label, skills_tecnicas_list, estado_oferta', { count: 'exact' })
      .in('isco_code', iscoCodes)
      .eq('estado_oferta', 'activa')
      .order('fecha_publicacion_iso', { ascending: false })

    if (provincia) {
      query = query.eq('provincia', provincia)
    }
    if (modalidad) {
      query = query.ilike('modalidad', `%${modalidad}%`)
    }

    // Paginación
    const from = (page - 1) * limit
    query = query.range(from, from + limit - 1)

    const { data: ofertas, error, count } = await query

    if (error) throw error

    // Calcular gap personalizado para cada oferta
    const workerSkillsSet = new Set(workerSkills)

    const results: MatchingOffer[] = (ofertas || []).map(oferta => {
      // Skills de la oferta (pueden estar en skills_tecnicas_list como array o string)
      let ofertaSkills: string[] = []
      if (Array.isArray(oferta.skills_tecnicas_list)) {
        ofertaSkills = oferta.skills_tecnicas_list.map((s: string) => s.toLowerCase())
      } else if (typeof oferta.skills_tecnicas_list === 'string') {
        ofertaSkills = oferta.skills_tecnicas_list.split(',').map((s: string) => s.trim().toLowerCase())
      }

      const cubiertas = ofertaSkills.filter(s => workerSkillsSet.has(s))
      const gap = ofertaSkills.filter(s => !workerSkillsSet.has(s))
      const matchScore = ofertaSkills.length > 0
        ? Math.round((cubiertas.length / ofertaSkills.length) * 100)
        : 0

      return {
        id_oferta: oferta.id_oferta,
        titulo: oferta.titulo || '',
        empresa: oferta.empresa || '',
        provincia: oferta.provincia || '',
        localidad: oferta.localidad || '',
        modalidad: oferta.modalidad || '',
        fecha_publicacion: oferta.fecha_publicacion_iso || '',
        url_oferta: oferta.url_oferta || '',
        isco_code: oferta.isco_code || '',
        esco_occupation_label: oferta.esco_occupation_label || '',
        match_score: matchScore,
        skills_cubiertas: cubiertas,
        skills_gap: gap,
      }
    })

    // Ordenar por match_score descendente
    results.sort((a, b) => b.match_score - a.match_score)

    return NextResponse.json({
      offers: results,
      total: count || 0,
      page,
      limit,
      isco_codes: iscoCodes,
    })
  } catch (error) {
    console.error('Error matching offers:', error)
    return NextResponse.json({ error: 'Error matching offers' }, { status: 500 })
  }
}
