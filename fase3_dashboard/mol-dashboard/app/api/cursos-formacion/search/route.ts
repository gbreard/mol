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
export async function GET(request: NextRequest) {
  const client = getSupabaseAdmin()
  if (!client) return NextResponse.json({ error: 'Supabase no configurado' }, { status: 500 })

  const q = request.nextUrl.searchParams.get('q') || ''
  if (q.length < 2) return NextResponse.json({ cursos: [] })

  const { data, error } = await client.rpc('search_cursos_formacion', {
    query_text: q,
    max_results: 10,
  })

  if (error) return NextResponse.json({ error: error.message }, { status: 500 })
  return NextResponse.json({ cursos: data || [] })
}
