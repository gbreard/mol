import { NextRequest, NextResponse } from 'next/server'
import { requireAuth, requireAdmin, isAuthError } from '@/lib/api-auth'
import { createClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || ''
const supabaseServiceKey = process.env.SUPABASE_SERVICE_ROLE_KEY || process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || ''

const supabase = supabaseUrl && supabaseServiceKey
  ? createClient(supabaseUrl, supabaseServiceKey)
  : null

/**
 * GET /api/organizaciones
 * Retorna la organización del usuario actual + su rol
 * Si es admin, retorna todas.
 */
export async function GET(request: NextRequest) {
  const auth = await requireAuth(request)
  if (auth instanceof NextResponse) return auth
  if (isAuthError(auth)) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }

  if (!supabase) {
    return NextResponse.json({ error: 'Supabase not configured' }, { status: 500 })
  }

  try {
    if (auth.role === 'admin') {
      // Admin ve todas
      const { data, error } = await supabase
        .from('organizaciones')
        .select('*, user_organizaciones(user_id, rol_en_org, activo)')
        .order('nombre')

      if (error) throw error
      return NextResponse.json({ organizaciones: data || [] })
    }

    // Usuario normal: solo su org via RPC
    const { data, error } = await supabase.rpc('get_user_org')
    if (error) throw error

    return NextResponse.json({
      organizacion: data && data.length > 0 ? data[0] : null,
    })
  } catch (error) {
    console.error('Error fetching org:', error)
    return NextResponse.json({ error: 'Error fetching organization' }, { status: 500 })
  }
}

/**
 * POST /api/organizaciones
 * Crear organización (admin only)
 * Body: { nombre, tipo, jurisdiccion?, sector? }
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

    if (!body.nombre || !body.tipo) {
      return NextResponse.json({ error: 'nombre y tipo requeridos' }, { status: 400 })
    }

    if (!['oficina_empleo', 'empresa'].includes(body.tipo)) {
      return NextResponse.json({ error: 'tipo debe ser oficina_empleo o empresa' }, { status: 400 })
    }

    const { data, error } = await supabase
      .from('organizaciones')
      .insert({
        nombre: body.nombre,
        tipo: body.tipo,
        jurisdiccion: body.jurisdiccion || null,
        sector: body.sector || null,
        metadata: body.metadata || null,
      })
      .select()
      .single()

    if (error) throw error

    return NextResponse.json({ organizacion: data }, { status: 201 })
  } catch (error) {
    console.error('Error creating org:', error)
    return NextResponse.json({ error: 'Error creating organization' }, { status: 500 })
  }
}
