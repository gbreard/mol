import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || ''
const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || ''

const supabase = supabaseUrl && supabaseKey
  ? createClient(supabaseUrl, supabaseKey)
  : null

/**
 * GET /api/occupations/skills-by-isco?isco=5223&limit=15
 *
 * Devuelve las skills más frecuentes para un ISCO code,
 * extraídas de las ofertas reales en ofertas_skills.
 */
export async function GET(request: NextRequest) {
  const isco = request.nextUrl.searchParams.get('isco')
  const limit = parseInt(request.nextUrl.searchParams.get('limit') || '15', 10)

  if (!isco) {
    return NextResponse.json({ error: 'isco requerido' }, { status: 400 })
  }

  if (!supabase) {
    return NextResponse.json({ error: 'Supabase not configured' }, { status: 500 })
  }

  try {
    // Get offer IDs for this ISCO
    const { data: ofertas } = await supabase
      .from('ofertas_dashboard')
      .select('id_oferta')
      .eq('isco_code', isco)
      .limit(100)

    if (!ofertas || ofertas.length === 0) {
      return NextResponse.json({ skills: [], isco, message: 'Sin ofertas para este ISCO' })
    }

    const ofertaIds = ofertas.map(o => String(o.id_oferta))

    // Get most frequent skills across these offers
    const { data: skillRows } = await supabase
      .from('ofertas_skills')
      .select('skill_uri, preferred_label')
      .in('id_oferta', ofertaIds)

    if (!skillRows || skillRows.length === 0) {
      return NextResponse.json({ skills: [], isco })
    }

    // Count frequency
    const freq = new Map<string, { uri: string; label: string; count: number }>()
    for (const row of skillRows) {
      const existing = freq.get(row.skill_uri)
      if (existing) {
        existing.count++
      } else {
        freq.set(row.skill_uri, {
          uri: row.skill_uri,
          label: row.preferred_label,
          count: 1,
        })
      }
    }

    // Sort by frequency, top N
    const skills = Array.from(freq.values())
      .sort((a, b) => b.count - a.count)
      .slice(0, limit)
      .map((s, i) => ({
        uri: s.uri,
        label: s.label,
        type: 'skill' as const,
        description: '',
        source: 'esco' as const,
        essential: i < Math.ceil(limit * 0.6), // top 60% marked essential
        frequency: s.count,
        total_ofertas: ofertas.length,
      }))

    return NextResponse.json({ skills, isco, total_ofertas: ofertas.length })
  } catch (error) {
    console.error('Error getting skills by ISCO:', error)
    return NextResponse.json({ error: 'Error' }, { status: 500 })
  }
}
