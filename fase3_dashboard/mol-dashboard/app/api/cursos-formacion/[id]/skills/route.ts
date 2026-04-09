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

// TODO OE-11: restore requireAuth
export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const client = getSupabaseAdmin()
  if (!client) return NextResponse.json({ error: 'Supabase no configurado' }, { status: 500 })

  const { id } = await params
  const cursoId = parseInt(id)
  if (isNaN(cursoId)) return NextResponse.json({ skills: [] })

  const { data, error } = await client.rpc('get_skills_by_curso', { p_curso_id: cursoId })

  if (error) return NextResponse.json({ error: error.message }, { status: 500 })
  return NextResponse.json({ skills: data || [] })
}
