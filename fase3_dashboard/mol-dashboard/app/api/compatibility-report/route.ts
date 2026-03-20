import { NextRequest, NextResponse } from 'next/server'
import { requireAuth, requireRateLimit, isAuthError } from '@/lib/api-auth'
import { createClient } from '@supabase/supabase-js'
import { randomUUID } from 'crypto'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || ''
const supabaseServiceKey = process.env.SUPABASE_SERVICE_ROLE_KEY || process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || ''

const supabase = supabaseUrl && supabaseServiceKey
  ? createClient(supabaseUrl, supabaseServiceKey)
  : null

// Tipos
export interface SkillItem {
  uri?: string
  label: string
  type: 'skill' | 'knowledge' | 'transversal'
  source: 'esco' | 'esco_common' | 'argentina_approved' | 'argentina_emerging'
  description?: string
}

export interface ReportData {
  id: string
  token: string
  candidato_nombre: string
  candidato_dni?: string
  ocupacion_uri: string
  ocupacion_label: string
  ocupacion_isco: string
  oferta_id?: number
  oferta_titulo?: string
  origen: 'trabajador' | 'oficina_empleo'
  perfil_consolidado_version: string | null
  match_score: number
  skills_candidato: SkillItem[]
  skills_requeridas: SkillItem[]
  skills_cubiertas: SkillItem[]
  skills_gap: SkillItem[]
  estado: 'activo' | 'expirado' | 'revocado'
  vistas: number
  created_at: string
  expira_at: string
}

/**
 * GET /api/compatibility-report?token=abc123
 *
 * Retorna datos de un reporte por token.
 * Público — no requiere autenticación (el token es la "auth").
 * Incrementa contador de vistas.
 */
export async function GET(request: NextRequest) {
  const rateLimited = requireRateLimit(request, 'public')
  if (rateLimited) return rateLimited

  const { searchParams } = new URL(request.url)
  const token = searchParams.get('token')

  if (!token) {
    return NextResponse.json({ error: 'Token requerido' }, { status: 400 })
  }

  if (!supabase) {
    return NextResponse.json({ error: 'Supabase not configured' }, { status: 500 })
  }

  try {
    // Buscar reporte por token
    const { data: report, error } = await supabase
      .from('reportes_compatibilidad')
      .select('*')
      .eq('token', token)
      .single()

    if (error || !report) {
      return NextResponse.json({ error: 'Reporte no encontrado' }, { status: 404 })
    }

    // Verificar expiración
    if (report.estado === 'expirado' || new Date(report.expira_at) < new Date()) {
      return NextResponse.json({
        error: 'Reporte expirado',
        estado: 'expirado',
        expira_at: report.expira_at,
      }, { status: 410 })
    }

    // Verificar revocación
    if (report.estado === 'revocado') {
      return NextResponse.json({
        error: 'Reporte revocado',
        estado: 'revocado',
      }, { status: 410 })
    }

    // Incrementar vistas
    await supabase
      .from('reportes_compatibilidad')
      .update({
        vistas: (report.vistas || 0) + 1,
        ultima_vista_at: new Date().toISOString(),
      })
      .eq('token', token)

    // No exponer DNI en la respuesta API (solo en PDF)
    const { candidato_dni, ...safeReport } = report

    return NextResponse.json({ report: safeReport })
  } catch (error) {
    console.error('Error fetching report:', error)
    return NextResponse.json({ error: 'Error fetching report' }, { status: 500 })
  }
}

/**
 * POST /api/compatibility-report
 *
 * Crea un nuevo reporte de compatibilidad.
 * Requiere autenticación.
 *
 * Body: {
 *   candidato_nombre: string,
 *   candidato_dni?: string,
 *   ocupacion_uri: string,
 *   ocupacion_label: string,
 *   ocupacion_isco: string,
 *   oferta_id?: number,
 *   oferta_titulo?: string,
 *   origen: 'trabajador' | 'oficina_empleo',
 *   match_score: number,
 *   perfil_consolidado_version?: string,
 *   skills_candidato: SkillItem[],
 *   skills_requeridas: SkillItem[],
 *   skills_cubiertas: SkillItem[],
 *   skills_gap: SkillItem[],
 *   perfil_id?: string,
 * }
 */
export async function POST(request: NextRequest) {
  const auth = await requireAuth(request)
  if (auth instanceof NextResponse) return auth
  if (isAuthError(auth)) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }

  if (!supabase) {
    return NextResponse.json({ error: 'Supabase not configured' }, { status: 500 })
  }

  try {
    const body = await request.json()

    // Validación básica
    if (!body.candidato_nombre || !body.ocupacion_uri || !body.ocupacion_label) {
      return NextResponse.json(
        { error: 'candidato_nombre, ocupacion_uri y ocupacion_label son requeridos' },
        { status: 400 }
      )
    }

    if (!Array.isArray(body.skills_candidato) || !Array.isArray(body.skills_requeridas)) {
      return NextResponse.json(
        { error: 'skills_candidato y skills_requeridas deben ser arrays' },
        { status: 400 }
      )
    }

    // Generar token único (UUID sin guiones)
    const token = randomUUID().replace(/-/g, '')

    // Expiración: 60 días
    const expiraAt = new Date()
    expiraAt.setDate(expiraAt.getDate() + 60)

    const reportData = {
      token,
      perfil_id: body.perfil_id || null,
      created_by: auth.user.id,
      origen: body.origen || 'trabajador',
      candidato_nombre: body.candidato_nombre,
      candidato_dni: body.candidato_dni || null,
      ocupacion_uri: body.ocupacion_uri,
      ocupacion_label: body.ocupacion_label,
      ocupacion_isco: body.ocupacion_isco || null,
      oferta_id: body.oferta_id || null,
      oferta_titulo: body.oferta_titulo || null,
      perfil_consolidado_version: body.perfil_consolidado_version || null,
      match_score: body.match_score || 0,
      skills_candidato: body.skills_candidato,
      skills_requeridas: body.skills_requeridas,
      skills_cubiertas: body.skills_cubiertas || [],
      skills_gap: body.skills_gap || [],
      estado: 'activo',
      expira_at: expiraAt.toISOString(),
      vistas: 0,
    }

    const { data, error } = await supabase
      .from('reportes_compatibilidad')
      .insert(reportData)
      .select()
      .single()

    if (error) throw error

    // URL del reporte
    const baseUrl = process.env.NEXT_PUBLIC_APP_URL || 'https://mol-nextjs.vercel.app'
    const reportUrl = `${baseUrl}/reporte/${token}`

    return NextResponse.json({
      report: data,
      token,
      url: reportUrl,
      expira_at: expiraAt.toISOString(),
    }, { status: 201 })
  } catch (error) {
    console.error('Error creating report:', error)
    return NextResponse.json({ error: 'Error creating report' }, { status: 500 })
  }
}

/**
 * PATCH /api/compatibility-report
 *
 * Revocar un reporte.
 * Requiere autenticación (solo el creador o admin).
 *
 * Body: { token: string, action: 'revocar' }
 */
export async function PATCH(request: NextRequest) {
  const auth = await requireAuth(request)
  if (auth instanceof NextResponse) return auth
  if (isAuthError(auth)) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }

  if (!supabase) {
    return NextResponse.json({ error: 'Supabase not configured' }, { status: 500 })
  }

  try {
    const body = await request.json()
    const { token, action } = body

    if (!token || action !== 'revocar') {
      return NextResponse.json(
        { error: 'token y action="revocar" requeridos' },
        { status: 400 }
      )
    }

    // Verificar que el reporte existe y es del usuario
    const { data: report } = await supabase
      .from('reportes_compatibilidad')
      .select('id, created_by')
      .eq('token', token)
      .single()

    if (!report) {
      return NextResponse.json({ error: 'Reporte no encontrado' }, { status: 404 })
    }

    if (report.created_by !== auth.user.id && auth.role !== 'admin') {
      return NextResponse.json({ error: 'No autorizado' }, { status: 403 })
    }

    const { error } = await supabase
      .from('reportes_compatibilidad')
      .update({ estado: 'revocado' })
      .eq('token', token)

    if (error) throw error

    return NextResponse.json({ message: 'Reporte revocado' })
  } catch (error) {
    console.error('Error revoking report:', error)
    return NextResponse.json({ error: 'Error revoking report' }, { status: 500 })
  }
}
