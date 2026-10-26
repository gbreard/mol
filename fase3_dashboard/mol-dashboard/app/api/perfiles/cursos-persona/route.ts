import { NextRequest, NextResponse } from 'next/server'
import { requireAuth, isAuthError } from '@/lib/api-auth'
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
 * POST /api/perfiles/cursos-persona
 * Body: { gap_skill_uris: string[], provincia?: string | null }  (provincia en formato REGICE)
 *
 * Cursos REGICE para cerrar la brecha de una persona: presenciales solo de su provincia,
 * a distancia de cualquier provincia; primero los presenciales. Solo los que cubren al
 * menos 2 competencias del gap (o la única, si el gap es de 1). Sin provincia → solo
 * virtuales (no se busca en todo el país). Las pantallas sin persona usan /cursos-gap.
 */
export async function POST(request: NextRequest) {
  const auth = await requireAuth(request)
  if (isAuthError(auth)) return auth

  const client = getSupabaseAdmin()
  if (!client) return NextResponse.json({ error: 'Supabase no configurado' }, { status: 500 })

  let body: { gap_skill_uris?: string[]; provincia?: string | null }
  try {
    body = await request.json()
  } catch {
    return NextResponse.json({ error: 'Body inválido' }, { status: 400 })
  }

  const gap = Array.isArray(body.gap_skill_uris) ? body.gap_skill_uris : []
  const provincia = body.provincia || null
  if (gap.length === 0) return NextResponse.json({ cursos: [], provincia, sin_provincia: !provincia })

  const { data, error } = await client.rpc('get_cursos_para_persona', {
    p_gap_skill_uris: gap,
    p_provincia: provincia,
    p_min_cubiertas: gap.length <= 1 ? 1 : 2,
    p_max_por_grupo: 10,
  })
  if (error) {
    console.error('Error en cursos-persona:', error)
    return NextResponse.json({ error: 'Error buscando cursos' }, { status: 500 })
  }

  return NextResponse.json({ cursos: data || [], provincia, sin_provincia: !provincia })
}
