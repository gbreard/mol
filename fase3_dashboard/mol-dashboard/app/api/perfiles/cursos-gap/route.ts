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
 * POST /api/perfiles/cursos-gap
 * Body: { gap_skill_uris: string[], provincia?: string }
 *
 * Retorna cursos REGICE que cubren las skills del gap.
 */
export async function POST(request: NextRequest) {
  // TODO OE-11: restore requireAuth
  const client = getSupabaseAdmin()
  if (!client) return NextResponse.json({ error: 'Supabase no configurado' }, { status: 500 })

  let body: { gap_skill_uris?: string[]; provincia?: string }
  try {
    body = await request.json()
  } catch {
    return NextResponse.json({ cursos: [], total: 0, provincia_filtro: null })
  }

  const { gap_skill_uris, provincia } = body

  if (!gap_skill_uris || !Array.isArray(gap_skill_uris) || gap_skill_uris.length === 0) {
    return NextResponse.json({ cursos: [], total: 0, provincia_filtro: null })
  }

  try {
    const { data, error } = await client.rpc('get_cursos_for_gap', {
      p_gap_skill_uris: gap_skill_uris,
      p_provincia: provincia || null,
      p_max_results: 20,
    })

    if (error) throw error

    const cursos = (data || []).map((c: any) => ({
      ...c,
      pct_gap_cubierto: c.total_gap_skills > 0
        ? Math.round((c.skills_cubiertas / c.total_gap_skills) * 100)
        : 0,
    }))

    return NextResponse.json({
      cursos,
      total: cursos.length,
      provincia_filtro: provincia || null,
    })
  } catch (error) {
    console.error('Error en cursos-gap:', error)
    return NextResponse.json(
      { error: `Error buscando cursos: ${(error as Error).message}` },
      { status: 500 }
    )
  }
}
