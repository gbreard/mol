export type NivelMaestria = 'basico' | 'intermedio' | 'avanzado' | 'experto'

export const NIVEL_WEIGHTS: Record<string, number> = {
  basico:     0.40,
  intermedio: 0.65,
  avanzado:   0.85,
  experto:    1.00,
  default:    0.65,
}

export interface ProfileSkill {
  skill_uri: string
  skill_label?: string
  nivel?: NivelMaestria | string | null
}

export interface OccupationSkill {
  id: string
  label: string
  L1?: string
  L2?: string
}

const ESCO_PREFIX = 'http://data.europa.eu/esco/skill/'

/**
 * Calcula la compatibilidad de un perfil con una ocupación.
 * - matchScore: cobertura de esenciales (cubiertas / total), el % visible.
 * - weightedScore: cobertura ponderada por nivel de maestría, solo para desempatar.
 * Reemplaza los cálculos duplicados de M2 y M3.
 */
export function calculateOccupationMatch(
  profileSkills: ProfileSkill[],
  essentialSkills: OccupationSkill[],
  optionalSkills: OccupationSkill[] = []
) {
  const profileMap = new Map<string, string | null>()
  for (const s of profileSkills) {
    profileMap.set(s.skill_uri, (s.nivel as string) ?? null)
  }

  const allOccUris = new Set([
    ...essentialSkills.map(s => ESCO_PREFIX + s.id),
    ...optionalSkills.map(s => ESCO_PREFIX + s.id),
  ])

  // Essential: ponderado por nivel
  let weightedCovered = 0
  const sharedEssential: OccupationSkill[] = []
  const gapEssential: OccupationSkill[] = []

  for (const skill of essentialSkills) {
    const uri = ESCO_PREFIX + skill.id
    if (profileMap.has(uri)) {
      const nivel = profileMap.get(uri)
      const weight = NIVEL_WEIGHTS[nivel || 'default'] ?? NIVEL_WEIGHTS.default
      weightedCovered += weight
      sharedEssential.push(skill)
    } else {
      gapEssential.push(skill)
    }
  }

  // Optional: sin peso (bonus)
  const sharedOptional: OccupationSkill[] = []
  const gapOptional: OccupationSkill[] = []

  for (const skill of optionalSkills) {
    const uri = ESCO_PREFIX + skill.id
    if (profileMap.has(uri)) {
      sharedOptional.push(skill)
    } else {
      gapOptional.push(skill)
    }
  }

  // Transferable
  const transferable = profileSkills.filter(s => !allOccUris.has(s.skill_uri))

  // 0-100
  const matchScore = essentialSkills.length > 0
    ? Math.round((sharedEssential.length / essentialSkills.length) * 100)
    : 0
  const weightedScore = essentialSkills.length > 0
    ? Math.round((weightedCovered / essentialSkills.length) * 100)
    : 0

  return {
    matchScore,
    weightedScore,
    weightedCovered,
    essentialTotal: essentialSkills.length,
    sharedEssential,
    sharedOptional,
    gapEssential,
    gapOptional,
    gapCount: gapEssential.length,
    transferable,
  }
}

// ============================================================
// Barandas del ranking de ocupaciones (M2 y M3)
// ============================================================

export interface RankableMatch {
  label: string
  isco_code: string
  matchScore: number
  weightedScore: number
  essentialTotal: number
  essentialCovered: number
}

export const MIN_ESSENTIAL_COVERED = 2
export const MIN_ESSENTIAL_TOTAL = 5
export const MAX_PER_ISCO_IN_TOP = 2
export const TOP_N = 10

// DEMO: revisar después — ocupaciones absurdas que sobreviven a las barandas
export const DEMO_EXCLUDED_OCCUPATIONS: string[] = [
  'funcionario del sector de la Defensa/funcionaria del sector de la Defensa',
  'operario de señalización vial/operaria de señalización vial',
]

/**
 * Una ocupación entra al ranking si cubre al menos 2 esenciales de un total de 5 o más
 * (con pocas esenciales, 1 de 2 = 50% subía artificialmente), no es del gran grupo
 * CIUO 0 (fuerzas armadas) y no está en la lista de exclusión.
 */
export function isEligibleMatch(m: RankableMatch): boolean {
  return m.essentialCovered >= MIN_ESSENTIAL_COVERED
    && m.essentialTotal >= MIN_ESSENTIAL_TOTAL
    && !m.isco_code.startsWith('0')
    && !DEMO_EXCLUDED_OCCUPATIONS.includes(m.label)
}

/** Orden: cobertura → nivel ponderado → avisos activos. */
export function compareMatches(a: RankableMatch, b: RankableMatch, activas: Record<string, number> = {}): number {
  return (b.matchScore - a.matchScore)
    || (b.weightedScore - a.weightedScore)
    || ((activas[b.isco_code] || 0) - (activas[a.isco_code] || 0))
}

/**
 * Como máximo 2 ocupaciones por CIUO de 4 dígitos en el top 10; las que sobran
 * pasan a continuación del top, en su orden.
 */
export function capPerIsco<T extends { isco_code: string }>(sorted: T[], max = MAX_PER_ISCO_IN_TOP, topN = TOP_N): T[] {
  const top: T[] = []
  const deferred: T[] = []
  const porIsco: Record<string, number> = {}
  let i = 0
  for (; i < sorted.length && top.length < topN; i++) {
    const m = sorted[i]
    if ((porIsco[m.isco_code] || 0) < max) {
      top.push(m)
      porIsco[m.isco_code] = (porIsco[m.isco_code] || 0) + 1
    } else {
      deferred.push(m)
    }
  }
  return [...top, ...deferred, ...sorted.slice(i)]
}

/**
 * Cursos útiles para cerrar una brecha: los que cubren al menos 2 competencias del gap
 * (o la única, si el gap es de 1).
 */
export function cursosQueCubrenVarias<T extends { skills_cubiertas: number }>(cursos: T[], gapSize: number): T[] {
  const minimo = gapSize <= 1 ? 1 : 2
  return cursos.filter(c => (c.skills_cubiertas || 0) >= minimo)
}
