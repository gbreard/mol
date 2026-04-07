import { NextRequest, NextResponse } from 'next/server'
import { createClient, SupabaseClient } from '@supabase/supabase-js'

let supabaseAdmin: SupabaseClient | null = null
function getSupabaseAdmin(): SupabaseClient | null {
  if (supabaseAdmin) return supabaseAdmin
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL
  const key = process.env.SUPABASE_SERVICE_ROLE_KEY
  if (!url || !key) return null
  supabaseAdmin = createClient(url, key, { auth: { autoRefreshToken: false, persistSession: false } })
  return supabaseAdmin
}

/**
 * GET /api/laboratorio/brecha-formacion
 * Params: estado, provincia, limit, offset
 */
export async function GET(request: NextRequest) {
  // TODO OE-11: restore requireAuth
  const client = getSupabaseAdmin()
  if (!client) return NextResponse.json({ error: 'Supabase no configurado' }, { status: 500 })

  const estado = request.nextUrl.searchParams.get('estado') || null
  const provincia = request.nextUrl.searchParams.get('provincia') || null
  const limit = parseInt(request.nextUrl.searchParams.get('limit') || '20')
  const offset = parseInt(request.nextUrl.searchParams.get('offset') || '0')

  try {
    let skills: any[] = []

    if (provincia) {
      const { data, error } = await client.rpc('get_brecha_formacion_provincia', {
        p_provincia: provincia,
        p_estado: estado,
        p_limit: limit,
      })
      if (error) throw error
      skills = data || []
    } else {
      const { data, error } = await client.rpc('get_brecha_formacion', {
        p_estado: estado,
        p_limit: limit,
        p_offset: offset,
      })
      if (error) throw error
      skills = data || []
    }

    // Resumen from pre-calculated table
    let resumen = { total_skills: 0, brechas: 0, cubiertas: 0, pct_brecha: 0 }
    const table = provincia ? 'brecha_formacion_provincial' : 'brecha_formacion_skills'

    let query = client.from(table).select('estado')
    if (provincia) query = query.eq('provincia', provincia)
    const { data: allRows } = await query

    if (allRows) {
      const brechas = allRows.filter((r: any) => r.estado === 'brecha').length
      const cubiertas = allRows.filter((r: any) => r.estado === 'cubierta').length
      const total = brechas + cubiertas
      resumen = {
        total_skills: total,
        brechas,
        cubiertas,
        pct_brecha: total > 0 ? Math.round((brechas / total) * 100) : 0,
      }
    }

    // Get calculado_en
    const { data: meta } = await client
      .from(table)
      .select('calculado_en')
      .limit(1)

    return NextResponse.json({
      skills,
      resumen,
      provincia,
      calculado_en: meta?.[0]?.calculado_en || null,
    })
  } catch (error) {
    console.error('Error en brecha-formacion:', error)
    return NextResponse.json(
      { error: `Error: ${(error as Error).message}` },
      { status: 500 }
    )
  }
}
