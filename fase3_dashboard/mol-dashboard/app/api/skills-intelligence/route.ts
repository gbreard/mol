import { NextRequest, NextResponse } from 'next/server'
import {
  getSkillsIntelligenceStats,
  getOccupationsWithMOLData
} from '@/lib/supabase'

export const dynamic = 'force-dynamic'
export const revalidate = 0

/**
 * GET /api/skills-intelligence
 * Retorna stats y lista de ocupaciones con datos MOL
 */
export async function GET(request: NextRequest) {
  try {
    const [stats, occupations] = await Promise.all([
      getSkillsIntelligenceStats(),
      getOccupationsWithMOLData()
    ])

    return NextResponse.json({
      stats,
      occupations,
      generated_at: new Date().toISOString()
    })
  } catch (error) {
    console.error('Error in skills-intelligence API:', error)
    return NextResponse.json(
      { error: 'Error fetching skills intelligence data' },
      { status: 500 }
    )
  }
}
