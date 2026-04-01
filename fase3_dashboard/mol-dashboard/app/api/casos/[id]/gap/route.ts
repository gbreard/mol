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
 * POST /api/casos/[id]/gap
 * Body: { occupation_uri: string }
 *
 * Calcula gap semántico entre perfil de la persona y ocupación destino.
 * Expand en paralelo: una llamada a expand_skills_semantic por skill (Promise.all).
 * La UI tiene el JSON con labels — la API solo retorna URIs y conteos.
 */
export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const client = getSupabaseAdmin()
  if (!client) return NextResponse.json({ error: 'Supabase no configurado' }, { status: 500 })

  const { id } = await params

  let body: { occupation_uri?: string }
  try {
    body = await request.json()
  } catch {
    return NextResponse.json({ error: 'Body inválido' }, { status: 400 })
  }

  if (!body.occupation_uri) {
    return NextResponse.json({ error: 'occupation_uri requerido' }, { status: 400 })
  }

  try {
    // 1. Verificar caso existe
    const { data: caso, error: casoError } = await client
      .from('casos')
      .select('id, persona_id')
      .eq('id', id)
      .maybeSingle()

    if (casoError) throw casoError
    if (!caso) return NextResponse.json({ error: 'Caso no encontrado' }, { status: 404 })

    // 2. Skills del perfil
    const { data: skillRows, error: skillsError } = await client
      .from('perfil_skills')
      .select('skill_uri, perfiles!inner(persona_id)')
      .eq('perfiles.persona_id', caso.persona_id)
      .neq('estado', 'descartada')

    if (skillsError) throw skillsError

    const personaSkillUris = (skillRows || []).map((r: any) => r.skill_uri).filter(Boolean)

    if (personaSkillUris.length === 0) {
      return NextResponse.json({ gap: null, mensaje: 'sin_skills' })
    }

    // 3. Expand en paralelo — una llamada por skill
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

    // 4. Extract occupation ID from URI to match with JSON skill IDs
    //    occupation_uri format: http://data.europa.eu/esco/occupation/UUID
    //    skill IDs in JSON are UUIDs, skill URIs are http://data.europa.eu/esco/skill/UUID
    //    We match by checking if "http://data.europa.eu/esco/skill/{json_skill_id}" is covered

    // The UI will send the occupation skills from the JSON.
    // But the API doesn't have the JSON — it only has the covered URIs.
    // The UI will use skills_cubiertas_uris to highlight which occupation skills are covered.

    const skillsCubiertasUris = Array.from(coveredMap.entries())
      .filter(([, v]) => !v.isExact || v.isExact) // all covered
      .map(([uri]) => uri)

    // Return the covered URIs and let the UI compute the gap against the JSON
    return NextResponse.json({
      skills_cubiertas_uris: skillsCubiertasUris,
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
