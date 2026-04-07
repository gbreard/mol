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
 * Calcula matchScore ponderado por nivel de maestría.
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

  // matchScore: 0-100
  const matchScore = essentialSkills.length > 0
    ? Math.round((weightedCovered / essentialSkills.length) * 100)
    : 0

  return {
    matchScore,
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
