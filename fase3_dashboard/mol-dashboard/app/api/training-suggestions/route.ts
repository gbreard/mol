import { NextRequest, NextResponse } from 'next/server'
import { requireRateLimit } from '@/lib/api-auth'
import { createClient } from '@supabase/supabase-js'
import { promises as fs } from 'fs'
import path from 'path'
import { readdirSync } from 'fs'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || ''
const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || ''

const supabase = supabaseUrl && supabaseKey
  ? createClient(supabaseUrl, supabaseKey)
  : null

interface Course {
  id: number
  name: string
  descripcion: string
  duracion: string
  certificacion: string
  modalidad: string
  lugar: string
  fuente: string
  texto_busqueda: string
}

interface CourseMatch {
  id: number
  name: string
  certificacion: string
  duracion: string
  modalidad: string
  fuente: string
  covers_skills: string[]
}

interface GapWithCourses {
  skill_label: string
  courses: CourseMatch[]
}

interface TransitionSuggestion {
  ocupacion_label: string
  isco: string
  trend_pct: number
  current_match: number
  skills_gap: string[]
  estimated_months: number
}

// Cache de cursos de todas las fuentes
let allCoursesCache: Course[] | null = null

/**
 * Carga cursos de TODOS los archivos en public/data/cursos/
 * Cada archivo es una fuente (CABA, nación, etc.)
 */
async function loadAllCourses(): Promise<Course[]> {
  if (allCoursesCache) return allCoursesCache

  const cursosDir = path.join(process.cwd(), 'public', 'data', 'cursos')
  let files: string[] = []

  try {
    files = readdirSync(cursosDir).filter(f => f.endsWith('.json'))
  } catch {
    return []
  }

  const allCourses: Course[] = []

  for (const file of files) {
    try {
      const raw = await fs.readFile(path.join(cursosDir, file), 'utf-8')
      const data = JSON.parse(raw)
      if (data.cursos && Array.isArray(data.cursos)) {
        allCourses.push(...data.cursos)
      }
    } catch {
      console.warn(`Error loading courses from ${file}`)
    }
  }

  allCoursesCache = allCourses
  return allCourses
}

function normalize(text: string): string {
  return text.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '')
}

/**
 * Busca cursos que cubren una skill faltante (full-text en texto_busqueda).
 */
function findCoursesForSkill(courses: Course[], skillLabel: string, limit = 5): CourseMatch[] {
  const normalizedSkill = normalize(skillLabel)
  const tokens = normalizedSkill.split(/\s+/).filter(t => t.length >= 3)

  if (tokens.length === 0) return []

  const matches: { course: Course; score: number }[] = []

  for (const course of courses) {
    const text = course.texto_busqueda || normalize(`${course.name} ${course.descripcion}`)
    const matchedTokens = tokens.filter(t => text.includes(t))

    if (matchedTokens.length > 0) {
      matches.push({
        course,
        score: matchedTokens.length / tokens.length,
      })
    }
  }

  return matches
    .sort((a, b) => b.score - a.score)
    .slice(0, limit)
    .map(({ course }) => ({
      id: course.id,
      name: course.name,
      certificacion: course.certificacion,
      duracion: course.duracion,
      modalidad: course.modalidad,
      fuente: course.fuente,
      covers_skills: [skillLabel],
    }))
}

/**
 * GET /api/training-suggestions?gaps=Docker,Testing,CI/CD&isco_codes=2512,2514&worker_skills=python,sql
 *
 * Retorna:
 * 1. Cursos agrupados por skill faltante
 * 2. Transición por demanda: ocupaciones en crecimiento accesibles
 */
export async function GET(request: NextRequest) {
  const rateLimited = requireRateLimit(request, 'public')
  if (rateLimited) return rateLimited

  const { searchParams } = new URL(request.url)
  const gaps = searchParams.get('gaps')?.split(',').map(s => s.trim()).filter(Boolean) || []
  const iscoCodes = searchParams.get('isco_codes')?.split(',').filter(Boolean) || []
  const workerSkills = searchParams.get('worker_skills')?.split(',').map(s => s.trim().toLowerCase()).filter(Boolean) || []

  try {
    // 1. Cursos por brecha
    const courses = await loadAllCourses()
    const byGap: GapWithCourses[] = gaps.map(gap => ({
      skill_label: gap,
      courses: findCoursesForSkill(courses, gap),
    })).filter(g => g.courses.length > 0)

    // 2. Transición por demanda del mercado
    let transitionDemand: TransitionSuggestion[] = []

    if (supabase && iscoCodes.length > 0) {
      try {
        // Calcular tendencia: ofertas por ISCO en últimos 3 meses vs 3 meses anteriores
        const now = new Date()
        const threeMonthsAgo = new Date(now)
        threeMonthsAgo.setMonth(threeMonthsAgo.getMonth() - 3)
        const sixMonthsAgo = new Date(now)
        sixMonthsAgo.setMonth(sixMonthsAgo.getMonth() - 6)

        // Ofertas recientes (3 meses)
        const { data: recent } = await supabase
          .from('ofertas_dashboard')
          .select('isco_code, esco_occupation_label')
          .gte('fecha_publicacion_iso', threeMonthsAgo.toISOString().split('T')[0])
          .not('isco_code', 'is', null)

        // Ofertas anteriores (3-6 meses)
        const { data: older } = await supabase
          .from('ofertas_dashboard')
          .select('isco_code')
          .gte('fecha_publicacion_iso', sixMonthsAgo.toISOString().split('T')[0])
          .lt('fecha_publicacion_iso', threeMonthsAgo.toISOString().split('T')[0])
          .not('isco_code', 'is', null)

        if (recent && older) {
          // Contar por ISCO
          const recentCounts = new Map<string, { count: number; label: string }>()
          for (const r of recent) {
            const existing = recentCounts.get(r.isco_code)
            if (existing) {
              existing.count++
            } else {
              recentCounts.set(r.isco_code, { count: 1, label: r.esco_occupation_label || r.isco_code })
            }
          }

          const olderCounts = new Map<string, number>()
          for (const r of older) {
            olderCounts.set(r.isco_code, (olderCounts.get(r.isco_code) || 0) + 1)
          }

          // Calcular tendencia y filtrar crecimiento > 15%
          const trending: TransitionSuggestion[] = []

          for (const [isco, { count: recentCount, label }] of recentCounts) {
            // Excluir ocupaciones que ya son compatibles (están en isco_codes del trabajador)
            if (iscoCodes.includes(isco)) continue

            const olderCount = olderCounts.get(isco) || 0
            if (olderCount === 0) continue // No hay base de comparación

            const trendPct = Math.round(((recentCount - olderCount) / olderCount) * 100)
            if (trendPct <= 15) continue // Solo crecimiento significativo

            trending.push({
              ocupacion_label: label,
              isco,
              trend_pct: trendPct,
              current_match: 0, // TODO: calcular match real con perfil
              skills_gap: [], // TODO: calcular gap real
              estimated_months: 0,
            })
          }

          transitionDemand = trending
            .sort((a, b) => b.trend_pct - a.trend_pct)
            .slice(0, 10)
        }
      } catch (err) {
        console.warn('Error calculating trends:', err)
      }
    }

    // Fuentes disponibles
    const fuentes = [...new Set(courses.map(c => c.fuente))]

    return NextResponse.json({
      by_gap: byGap,
      transition_demand: transitionDemand,
      total_courses: courses.length,
      fuentes,
      gaps_searched: gaps.length,
      gaps_with_results: byGap.length,
    })
  } catch (error) {
    console.error('Error getting training suggestions:', error)
    return NextResponse.json({ error: 'Error getting suggestions' }, { status: 500 })
  }
}
