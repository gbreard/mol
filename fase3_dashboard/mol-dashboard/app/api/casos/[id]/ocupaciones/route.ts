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
 * GET /api/casos/[id]/ocupaciones
 *
 * Retorna ocupaciones ESCO compatibles con el perfil del caso,
 * usando match directo por cosine similarity (pgvector).
 */
export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const client = getSupabaseAdmin()
  if (!client) return NextResponse.json({ error: 'Supabase no configurado' }, { status: 500 })

  const { id } = await params

  try {
    // 1. Verificar que el caso existe
    const { data: caso, error: casoError } = await client
      .from('casos')
      .select('id, persona_id')
      .eq('id', id)
      .maybeSingle()

    if (casoError) throw casoError
    if (!caso) return NextResponse.json({ error: 'Caso no encontrado' }, { status: 404 })

    // 2. Leer skill_uris del perfil
    const { data: skillRows, error: skillsError } = await client
      .from('perfil_skills')
      .select('skill_uri, perfiles!inner(persona_id)')
      .eq('perfiles.persona_id', caso.persona_id)
      .neq('estado', 'descartada')

    if (skillsError) throw skillsError

    const skillUris = (skillRows || []).map((r: any) => r.skill_uri).filter(Boolean)

    if (skillUris.length === 0) {
      return NextResponse.json({
        ocupaciones: [],
        mensaje: 'sin_skills',
        total_skills_perfil: 0,
      })
    }

    // 3. Llamar RPC match_occupations_by_skills
    const { data: ocupaciones, error: rpcError } = await client.rpc('match_occupations_by_skills', {
      skill_uris: skillUris,
      similarity_threshold: 0.55,
      max_results: 10,
    })

    if (rpcError) throw rpcError

    return NextResponse.json({
      ocupaciones: (ocupaciones || []).map((o: any) => ({
        uri: o.occupation_uri,
        label: o.occupation_label,
        isco_code: o.isco_code,
        afinidad: Math.round(o.best_similarity * 1000) / 10,
        skills_matched: o.skills_matched,
      })),
      total_skills_perfil: skillUris.length,
    })
  } catch (error) {
    console.error('Error en ocupaciones del caso:', error)
    return NextResponse.json(
      { error: `Error buscando ocupaciones: ${(error as Error).message}` },
      { status: 500 }
    )
  }
}
