import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@supabase/supabase-js'

// Supabase client con service role para API
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || ''
const supabaseServiceKey = process.env.SUPABASE_SERVICE_ROLE_KEY || process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || ''

const supabase = supabaseUrl && supabaseServiceKey
  ? createClient(supabaseUrl, supabaseServiceKey)
  : null

// Tipos
export interface SkillConsolidada {
  label: string
  label_normalized: string
  uri?: string
  source: 'esco_common' | 'argentina_approved'
  L1?: string
  L2?: string
  percentage_when_approved?: number
  approved_at?: string
  approved_by?: string
}

export interface EscoArgentinoEntry {
  esco_occupation_uri: string
  esco_occupation_label: string
  isco_code?: string
  skills_consolidadas: SkillConsolidada[]
  total_skills: number
  skills_from_esco: number
  skills_from_argentina: number
  cobertura_esco_essential?: number
  cobertura_esco_total?: number
  ofertas_count_snapshot?: number
  version: number
  updated_at: string
  updated_by?: string
  notas?: string
}

/**
 * GET /api/esco-argentino
 * Obtiene todas las ocupaciones consolidadas
 *
 * Query params:
 * - occupation: URI específica para obtener solo una
 */
export async function GET(request: NextRequest) {
  if (!supabase) {
    return NextResponse.json(
      { error: 'Supabase no configurado' },
      { status: 500 }
    )
  }

  try {
    const { searchParams } = new URL(request.url)
    const occupation = searchParams.get('occupation')

    let query = supabase
      .from('esco_argentino')
      .select('*')
      .order('updated_at', { ascending: false })

    if (occupation) {
      query = query.eq('esco_occupation_uri', occupation)
    }

    const { data, error } = await query

    if (error) throw error

    // Si pidieron una específica y no existe, 404
    if (occupation && (!data || data.length === 0)) {
      return NextResponse.json(
        { error: 'Ocupación no encontrada en ESCO Argentino' },
        { status: 404 }
      )
    }

    // Si pidieron una específica, devolver solo esa
    if (occupation) {
      return NextResponse.json(data[0])
    }

    // Devolver todas con estadísticas
    const stats = {
      total_ocupaciones: data?.length || 0,
      total_skills: data?.reduce((sum, o) => sum + (o.total_skills || 0), 0) || 0,
      total_from_esco: data?.reduce((sum, o) => sum + (o.skills_from_esco || 0), 0) || 0,
      total_from_argentina: data?.reduce((sum, o) => sum + (o.skills_from_argentina || 0), 0) || 0,
      ultima_actualizacion: data?.[0]?.updated_at || null
    }

    return NextResponse.json({
      stats,
      ocupaciones: data || []
    })

  } catch (error) {
    console.error('Error in GET esco-argentino:', error)
    return NextResponse.json(
      { error: 'Error interno del servidor' },
      { status: 500 }
    )
  }
}

/**
 * POST /api/esco-argentino
 * Guarda o actualiza una ocupación en ESCO Argentino
 *
 * Body:
 * - esco_occupation_uri: string (required)
 * - esco_occupation_label: string (required)
 * - isco_code?: string
 * - skills_consolidadas: SkillConsolidada[]
 * - cobertura_esco_essential?: number
 * - cobertura_esco_total?: number
 * - ofertas_count_snapshot?: number
 * - updated_by?: string
 * - notas?: string
 */
export async function POST(request: NextRequest) {
  if (!supabase) {
    return NextResponse.json(
      { error: 'Supabase no configurado' },
      { status: 500 }
    )
  }

  try {
    const body = await request.json()

    if (!body.esco_occupation_uri || !body.esco_occupation_label) {
      return NextResponse.json(
        { error: 'esco_occupation_uri y esco_occupation_label son requeridos' },
        { status: 400 }
      )
    }

    const skills = body.skills_consolidadas || []
    const skillsFromEsco = skills.filter((s: SkillConsolidada) => s.source === 'esco_common').length
    const skillsFromArgentina = skills.filter((s: SkillConsolidada) => s.source === 'argentina_approved').length

    // Verificar si existe para incrementar versión
    const { data: existing } = await supabase
      .from('esco_argentino')
      .select('version')
      .eq('esco_occupation_uri', body.esco_occupation_uri)
      .single()

    const newVersion = existing ? (existing.version || 0) + 1 : 1

    const record = {
      esco_occupation_uri: body.esco_occupation_uri,
      esco_occupation_label: body.esco_occupation_label,
      isco_code: body.isco_code || null,
      skills_consolidadas: skills,
      total_skills: skills.length,
      skills_from_esco: skillsFromEsco,
      skills_from_argentina: skillsFromArgentina,
      cobertura_esco_essential: body.cobertura_esco_essential || null,
      cobertura_esco_total: body.cobertura_esco_total || null,
      ofertas_count_snapshot: body.ofertas_count_snapshot || null,
      version: newVersion,
      updated_at: new Date().toISOString(),
      updated_by: body.updated_by || null,
      notas: body.notas || null
    }

    const { data, error } = await supabase
      .from('esco_argentino')
      .upsert(record, { onConflict: 'esco_occupation_uri' })
      .select()
      .single()

    if (error) throw error

    return NextResponse.json({
      success: true,
      message: existing ? 'Ocupación actualizada' : 'Ocupación creada',
      data
    })

  } catch (error) {
    console.error('Error in POST esco-argentino:', error)
    return NextResponse.json(
      { error: 'Error interno del servidor' },
      { status: 500 }
    )
  }
}

/**
 * PATCH /api/esco-argentino
 * Agrega o quita una skill de una ocupación
 *
 * Body:
 * - esco_occupation_uri: string (required)
 * - action: 'add_skill' | 'remove_skill' (required)
 * - skill: SkillConsolidada (para add_skill)
 * - skill_label_normalized: string (para remove_skill)
 * - updated_by?: string
 */
export async function PATCH(request: NextRequest) {
  if (!supabase) {
    return NextResponse.json(
      { error: 'Supabase no configurado' },
      { status: 500 }
    )
  }

  try {
    const body = await request.json()

    if (!body.esco_occupation_uri || !body.action) {
      return NextResponse.json(
        { error: 'esco_occupation_uri y action son requeridos' },
        { status: 400 }
      )
    }

    // Obtener ocupación actual
    const { data: current, error: fetchError } = await supabase
      .from('esco_argentino')
      .select('*')
      .eq('esco_occupation_uri', body.esco_occupation_uri)
      .single()

    if (fetchError && fetchError.code !== 'PGRST116') throw fetchError

    let skills: SkillConsolidada[] = current?.skills_consolidadas || []

    if (body.action === 'add_skill') {
      if (!body.skill || !body.skill.label_normalized) {
        return NextResponse.json(
          { error: 'skill con label_normalized es requerido para add_skill' },
          { status: 400 }
        )
      }

      // Verificar que no exista ya
      const exists = skills.some(s => s.label_normalized === body.skill.label_normalized)
      if (exists) {
        return NextResponse.json(
          { error: 'La skill ya existe en este perfil' },
          { status: 409 }
        )
      }

      // Agregar skill con metadata
      skills.push({
        ...body.skill,
        approved_at: new Date().toISOString(),
        approved_by: body.updated_by || null
      })

    } else if (body.action === 'remove_skill') {
      if (!body.skill_label_normalized) {
        return NextResponse.json(
          { error: 'skill_label_normalized es requerido para remove_skill' },
          { status: 400 }
        )
      }

      skills = skills.filter(s => s.label_normalized !== body.skill_label_normalized)

    } else {
      return NextResponse.json(
        { error: 'action debe ser add_skill o remove_skill' },
        { status: 400 }
      )
    }

    // Recalcular conteos
    const skillsFromEsco = skills.filter(s => s.source === 'esco_common').length
    const skillsFromArgentina = skills.filter(s => s.source === 'argentina_approved').length

    // Actualizar o crear
    const record = {
      esco_occupation_uri: body.esco_occupation_uri,
      esco_occupation_label: body.esco_occupation_label || current?.esco_occupation_label || '',
      isco_code: body.isco_code || current?.isco_code || null,
      skills_consolidadas: skills,
      total_skills: skills.length,
      skills_from_esco: skillsFromEsco,
      skills_from_argentina: skillsFromArgentina,
      version: (current?.version || 0) + 1,
      updated_at: new Date().toISOString(),
      updated_by: body.updated_by || null
    }

    const { data, error } = await supabase
      .from('esco_argentino')
      .upsert(record, { onConflict: 'esco_occupation_uri' })
      .select()
      .single()

    if (error) throw error

    return NextResponse.json({
      success: true,
      message: body.action === 'add_skill' ? 'Skill agregada' : 'Skill removida',
      data
    })

  } catch (error) {
    console.error('Error in PATCH esco-argentino:', error)
    return NextResponse.json(
      { error: 'Error interno del servidor' },
      { status: 500 }
    )
  }
}

/**
 * DELETE /api/esco-argentino
 * Elimina una ocupación del ESCO Argentino
 *
 * Query params:
 * - occupation: URI de la ocupación a eliminar
 */
export async function DELETE(request: NextRequest) {
  if (!supabase) {
    return NextResponse.json(
      { error: 'Supabase no configurado' },
      { status: 500 }
    )
  }

  try {
    const { searchParams } = new URL(request.url)
    const occupation = searchParams.get('occupation')

    if (!occupation) {
      return NextResponse.json(
        { error: 'occupation query param es requerido' },
        { status: 400 }
      )
    }

    const { error } = await supabase
      .from('esco_argentino')
      .delete()
      .eq('esco_occupation_uri', occupation)

    if (error) throw error

    return NextResponse.json({
      success: true,
      message: 'Ocupación eliminada del ESCO Argentino'
    })

  } catch (error) {
    console.error('Error in DELETE esco-argentino:', error)
    return NextResponse.json(
      { error: 'Error interno del servidor' },
      { status: 500 }
    )
  }
}
