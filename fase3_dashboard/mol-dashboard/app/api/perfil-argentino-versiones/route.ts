import { NextRequest, NextResponse } from 'next/server'
import { requireAuth, requireAdmin, isAuthError } from '@/lib/api-auth'
import { createClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || ''
const supabaseServiceKey = process.env.SUPABASE_SERVICE_ROLE_KEY || process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || ''

const supabase = supabaseUrl && supabaseServiceKey
  ? createClient(supabaseUrl, supabaseServiceKey)
  : null

// Tipos
export interface PerfilVersion {
  id: string
  version: string
  total_skills: number
  total_emergentes_aprobadas: number
  total_ocupaciones: number
  nota: string | null
  creado_por: string | null
  activa: boolean
  created_at: string
}

export interface EstadoActual {
  ofertas_desde_ultimo_corte: number
  emergentes_pendientes: number
  skills_aprobadas_desde_corte: number
  ultima_version: string | null
}

/**
 * GET /api/perfil-argentino-versiones
 * Lista todas las versiones del perfil consolidado + estado actual
 * Requiere: autenticación (admin en práctica)
 */
export async function GET(request: NextRequest) {
  const auth = await requireAuth(request)
  if (auth instanceof NextResponse) return auth

  if (!supabase) {
    return NextResponse.json({ error: 'Supabase not configured' }, { status: 500 })
  }

  try {
    // Obtener todas las versiones
    const { data: versiones, error: vError } = await supabase
      .from('perfil_argentino_versiones')
      .select('id, version, total_skills, total_emergentes_aprobadas, total_ocupaciones, nota, creado_por, activa, created_at')
      .order('created_at', { ascending: false })

    if (vError) throw vError

    // Obtener versión activa
    const activa = versiones?.find(v => v.activa) || null

    // Calcular estado actual (cambios desde último corte)
    const ultimoCorteAt = activa?.created_at || '1970-01-01T00:00:00Z'

    // Contar emergentes pendientes (directo de la tabla, no por fecha)
    const { count: emergentes_pendientes_count } = await supabase
      .from('emergentes_pendientes')
      .select('id', { count: 'exact', head: true })
      .eq('estado', 'pendiente')

    const emergentes_pendientes = emergentes_pendientes_count || 0

    // Contar skills aprobadas desde último corte
    const { count: skills_aprobadas_count } = await supabase
      .from('emergentes_pendientes')
      .select('id', { count: 'exact', head: true })
      .eq('estado', 'aprobada')
      .gt('fecha_resolucion', ultimoCorteAt)

    const skills_aprobadas_desde_corte = skills_aprobadas_count || 0

    const estado_actual: EstadoActual = {
      ofertas_desde_ultimo_corte: 0, // TODO: calcular desde ofertas_dashboard
      emergentes_pendientes,
      skills_aprobadas_desde_corte,
      ultima_version: activa?.version || null,
    }

    return NextResponse.json({
      versiones: versiones || [],
      activa,
      estado_actual,
    })
  } catch (error) {
    console.error('Error fetching perfil versions:', error)
    return NextResponse.json(
      { error: 'Error fetching versions' },
      { status: 500 }
    )
  }
}

/**
 * POST /api/perfil-argentino-versiones
 * Crear nueva versión (corte de snapshot)
 * Requiere: admin
 * Body: { version: string, nota?: string }
 */
export async function POST(request: NextRequest) {
  const auth = await requireAdmin(request)
  if (auth instanceof NextResponse) return auth
  if (isAuthError(auth)) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }

  if (!supabase) {
    return NextResponse.json({ error: 'Supabase not configured' }, { status: 500 })
  }

  try {
    const body = await request.json()
    const { version, nota } = body

    if (!version || typeof version !== 'string') {
      return NextResponse.json(
        { error: 'version es requerido (string, ej: "v1.0")' },
        { status: 400 }
      )
    }

    // Verificar que la versión no exista
    const { data: existing } = await supabase
      .from('perfil_argentino_versiones')
      .select('id')
      .eq('version', version)
      .single()

    if (existing) {
      return NextResponse.json(
        { error: `La versión ${version} ya existe` },
        { status: 409 }
      )
    }

    // Llamar a la función SQL que congela el snapshot
    const { data, error } = await supabase.rpc('crear_version_perfil_argentino', {
      p_version: version,
      p_nota: nota || null,
      p_user_id: auth.user.id,
    })

    if (error) throw error

    // Obtener la versión recién creada
    const { data: nuevaVersion } = await supabase
      .from('perfil_argentino_versiones')
      .select('*')
      .eq('version', version)
      .single()

    return NextResponse.json({
      message: `Versión ${version} creada y activada`,
      version: nuevaVersion,
    }, { status: 201 })
  } catch (error) {
    console.error('Error creating version:', error)
    return NextResponse.json(
      { error: 'Error creating version' },
      { status: 500 }
    )
  }
}

/**
 * PATCH /api/perfil-argentino-versiones
 * Activar una versión (rollback) o desactivar
 * Requiere: admin
 * Body: { version_id: string, action: 'activar' }
 */
export async function PATCH(request: NextRequest) {
  const auth = await requireAdmin(request)
  if (auth instanceof NextResponse) return auth
  if (isAuthError(auth)) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }

  if (!supabase) {
    return NextResponse.json({ error: 'Supabase not configured' }, { status: 500 })
  }

  try {
    const body = await request.json()
    const { version_id, action } = body

    if (!version_id || action !== 'activar') {
      return NextResponse.json(
        { error: 'version_id y action="activar" requeridos' },
        { status: 400 }
      )
    }

    // Llamar a la función SQL de rollback
    const { error } = await supabase.rpc('activar_version_perfil', {
      p_version_id: version_id,
    })

    if (error) throw error

    return NextResponse.json({
      message: 'Versión activada',
    })
  } catch (error) {
    console.error('Error activating version:', error)
    return NextResponse.json(
      { error: 'Error activating version' },
      { status: 500 }
    )
  }
}
