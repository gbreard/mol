import { describe, it, expect } from 'vitest'
import { calculateOccupationMatch, NIVEL_WEIGHTS } from '@/lib/matching'

const essential = [
  { id: 'a', label: 'Skill A' },
  { id: 'b', label: 'Skill B' },
  { id: 'c', label: 'Skill C' },
  { id: 'd', label: 'Skill D' },
  { id: 'e', label: 'Skill E' },
]

const optional = [
  { id: 'f', label: 'Skill F' },
]

const PREFIX = 'http://data.europa.eu/esco/skill/'

describe('calculateOccupationMatch', () => {
  it('all skills at experto → matchScore = 100%', () => {
    const profile = essential.map(s => ({ skill_uri: PREFIX + s.id, nivel: 'experto' as const }))
    const result = calculateOccupationMatch(profile, essential, optional)
    expect(result.matchScore).toBe(100)
    expect(result.sharedEssential).toHaveLength(5)
    expect(result.gapEssential).toHaveLength(0)
  })

  it('all skills at basico → matchScore = 40%', () => {
    const profile = essential.map(s => ({ skill_uri: PREFIX + s.id, nivel: 'basico' as const }))
    const result = calculateOccupationMatch(profile, essential)
    expect(result.matchScore).toBe(40)
  })

  it('mixed niveles → weighted matchScore', () => {
    const profile = [
      { skill_uri: PREFIX + 'a', nivel: 'experto' as const },    // 1.00
      { skill_uri: PREFIX + 'b', nivel: 'avanzado' as const },   // 0.85
      { skill_uri: PREFIX + 'c', nivel: 'intermedio' as const }, // 0.65
      { skill_uri: PREFIX + 'd', nivel: 'basico' as const },    // 0.40
      // e not present → gap
    ]
    const result = calculateOccupationMatch(profile, essential)
    // weighted = 1.00 + 0.85 + 0.65 + 0.40 = 2.90 / 5 = 58%
    expect(result.matchScore).toBe(58)
    expect(result.sharedEssential).toHaveLength(4)
    expect(result.gapEssential).toHaveLength(1)
    expect(result.gapEssential[0].id).toBe('e')
  })

  it('no profile skills → matchScore = 0', () => {
    const result = calculateOccupationMatch([], essential)
    expect(result.matchScore).toBe(0)
    expect(result.sharedEssential).toHaveLength(0)
    expect(result.gapEssential).toHaveLength(5)
  })

  it('no essential skills → matchScore = 0', () => {
    const profile = [{ skill_uri: PREFIX + 'a', nivel: 'experto' as const }]
    const result = calculateOccupationMatch(profile, [])
    expect(result.matchScore).toBe(0)
  })

  it('nivel null → uses default weight (0.65)', () => {
    const profile = essential.map(s => ({ skill_uri: PREFIX + s.id, nivel: null }))
    const result = calculateOccupationMatch(profile, essential)
    expect(result.matchScore).toBe(65)
  })

  it('optional skills tracked but not weighted', () => {
    const profile = [
      { skill_uri: PREFIX + 'a', nivel: 'experto' as const },
      { skill_uri: PREFIX + 'f', nivel: 'avanzado' as const }, // optional
    ]
    const result = calculateOccupationMatch(profile, essential, optional)
    // Only essential a counts: 1.00 / 5 = 20%
    expect(result.matchScore).toBe(20)
    expect(result.sharedOptional).toHaveLength(1)
    expect(result.sharedOptional[0].id).toBe('f')
  })

  it('transferable skills identified', () => {
    const profile = [
      { skill_uri: PREFIX + 'a', nivel: 'experto' as const },
      { skill_uri: PREFIX + 'z', nivel: 'avanzado' as const }, // not in occupation
    ]
    const result = calculateOccupationMatch(profile, essential, optional)
    expect(result.transferable).toHaveLength(1)
    expect(result.transferable[0].skill_uri).toBe(PREFIX + 'z')
  })
})
