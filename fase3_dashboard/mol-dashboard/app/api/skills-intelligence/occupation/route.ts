import { NextRequest, NextResponse } from 'next/server'
import { requireRateLimit } from '@/lib/api-auth'
import { getOccupationMOLProfile } from '@/lib/supabase'

export const dynamic = 'force-dynamic'
export const revalidate = 0

/**
 * GET /api/skills-intelligence/occupation?uri=<esco_uri>
 * Retorna perfil de skills MOL para una ocupación específica
 */
export async function GET(request: NextRequest) {
  const limited = requireRateLimit(request);
  if (limited) return limited;

  try {
    const searchParams = request.nextUrl.searchParams
    const escoUri = searchParams.get('uri')

    if (!escoUri) {
      return NextResponse.json(
        { error: 'Missing uri parameter' },
        { status: 400 }
      )
    }

    const profile = await getOccupationMOLProfile(escoUri)

    if (!profile) {
      return NextResponse.json(
        { error: 'Occupation not found or has no MOL data' },
        { status: 404 }
      )
    }

    return NextResponse.json(profile)
  } catch (error) {
    console.error('Error in occupation profile API:', error)
    return NextResponse.json(
      { error: 'Error fetching occupation profile' },
      { status: 500 }
    )
  }
}
