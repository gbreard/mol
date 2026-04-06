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
 * GET /api/perfiles/[id]/gap?occupation_uri=X
 *
 * Calcula gap semántico entre skills del perfil y ocupación destino.
 * Expand en paralelo: una llamada a expand_skills_semantic por skill.
 * Mismo algoritmo que POST /api/casos/[id]/gap pero con perfil_id directo y GET.
 */
export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const client = getSupabaseAdmin()
  if (!client) return NextResponse.json({ error: 'Supabase no configurado' }, { status: 500 })

  const { id: perfilId } = await params
  const occupationUri = request.nextUrl.searchParams.get('occupation_uri')

  if (!occupationUri) {
    return NextResponse.json({ error: 'occupation_uri requerido' }, { status: 400 })
  }

  try {
    // 1. Skills del perfil
    const { data: skillRows, error: skillsError } = await client
      .from('perfil_skills')
      .select('skill_uri')
      .eq('perfil_id', perfilId)
      .neq('estado', 'descartada')

    if (skillsError) throw skillsError

    const personaSkillUris = (skillRows || []).map((r: any) => r.skill_uri).filter(Boolean)

    if (personaSkillUris.length === 0) {
      return NextResponse.json({ gap: null, mensaje: 'sin_skills' })
    }

    // 2. Expand en paralelo — una llamada por skill
    const expandPromises = personaSkillUris.map((uri: string) =>
      client.rpc('expand_skills_semantic', {
        skill_uris: [uri],
        similarity_threshold: 0.65,
        max_per_skill: 3,
      }).then(res => {
        if (res.error) throw res.error
        return res.data || []
      })
    )

    const expandResults = await Promise.all(expandPromises)

    // Build set of covered URIs with best match info
    const coveredMap = new Map<string, { similarity: number; isExact: boolean }>()
    for (const rows of expandResults) {
      for (const r of rows) {
        const existing = coveredMap.get(r.expanded_uri)
        if (!existing || r.similarity > existing.similarity) {
          coveredMap.set(r.expanded_uri, {
            similarity: r.similarity,
            isExact: r.is_exact,
          })
        }
      }
    }

    // 3. Return covered URIs — UI computes gap against occupation JSON
    return NextResponse.json({
      skills_cubiertas_uris: Array.from(coveredMap.keys()),
      skills_cubiertas_detail: Object.fromEntries(
        Array.from(coveredMap.entries()).map(([uri, v]) => [uri, {
          similarity: Math.round(v.similarity * 1000) / 1000,
          is_exact: v.isExact,
        }])
      ),
      total_skills_perfil: personaSkillUris.length,
      total_expanded: coveredMap.size,
    })
  } catch (error) {
    console.error('Error calculando gap:', error)
    return NextResponse.json(
      { error: `Error calculando gap: ${(error as Error).message}` },
      { status: 500 }
    )
  }
}
