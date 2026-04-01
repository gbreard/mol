import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || ''
const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || ''

const supabase = supabaseUrl && supabaseKey
  ? createClient(supabaseUrl, supabaseKey)
  : null

/**
 * GET /api/occupations/search-semantic?q=soldador
 * Búsqueda semántica de ocupaciones por pg_trgm en occupations_embeddings.
 */
export async function GET(request: NextRequest) {
  // TODO OE-11: restore requireAuth
  const q = request.nextUrl.searchParams.get('q') || ''
  if (!q || q.length < 2) {
    return NextResponse.json({ results: [] })
  }

  if (!supabase) {
    return NextResponse.json({ error: 'Supabase not configured' }, { status: 500 })
  }

  try {
    const { data, error } = await supabase.rpc('search_occupations_by_text', {
      query_text: q,
      similarity_min: 0.2,
      max_results: 10,
    })

    if (error) throw error

    return NextResponse.json({
      results: (data || []).map((o: any) => ({
        uri: o.occupation_uri,
        label: o.occupation_label,
        isco_code: o.isco_code,
        similarity: o.text_similarity,
      })),
    })
  } catch (error) {
    console.error('Error searching occupations:', error)
    return NextResponse.json({ error: 'Error searching' }, { status: 500 })
  }
}
