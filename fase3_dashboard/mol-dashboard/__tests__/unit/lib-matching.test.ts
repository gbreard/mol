import { describe, it, expect } from 'vitest'
import { calculateOccupationMatch, isEligibleMatch, compareMatches, capPerIsco, type RankableMatch } from '@/lib/matching'

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
  it('all skills at experto → matchScore = 100%, weightedScore = 100%', () => {
    const profile = essential.map(s => ({ skill_uri: PREFIX + s.id, nivel: 'experto' as const }))
    const result = calculateOccupationMatch(profile, essential, optional)
    expect(result.matchScore).toBe(100)
    expect(result.weightedScore).toBe(100)
    expect(result.sharedEssential).toHaveLength(5)
    expect(result.gapEssential).toHaveLength(0)
  })

  it('all skills at basico → cobertura 100%, ponderado 40%', () => {
    const profile = essential.map(s => ({ skill_uri: PREFIX + s.id, nivel: 'basico' as const }))
    const result = calculateOccupationMatch(profile, essential)
    expect(result.matchScore).toBe(100)
    expect(result.weightedScore).toBe(40)
  })

  it('mixed niveles → matchScore es cobertura, weightedScore pondera', () => {
    const profile = [
      { skill_uri: PREFIX + 'a', nivel: 'experto' as const },    // 1.00
      { skill_uri: PREFIX + 'b', nivel: 'avanzado' as const },   // 0.85
      { skill_uri: PREFIX + 'c', nivel: 'intermedio' as const }, // 0.65
      { skill_uri: PREFIX + 'd', nivel: 'basico' as const },    // 0.40
      // e not present → gap
    ]
    const result = calculateOccupationMatch(profile, essential)
    // cobertura = 4 / 5 = 80%; ponderado = 1.00 + 0.85 + 0.65 + 0.40 = 2.90 / 5 = 58%
    expect(result.matchScore).toBe(80)
    expect(result.weightedScore).toBe(58)
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

  it('nivel null → uses default weight (0.65) en el ponderado', () => {
    const profile = essential.map(s => ({ skill_uri: PREFIX + s.id, nivel: null }))
    const result = calculateOccupationMatch(profile, essential)
    expect(result.matchScore).toBe(100)
    expect(result.weightedScore).toBe(65)
  })

  it('optional skills tracked but not weighted', () => {
    const profile = [
      { skill_uri: PREFIX + 'a', nivel: 'experto' as const },
      { skill_uri: PREFIX + 'f', nivel: 'avanzado' as const }, // optional
    ]
    const result = calculateOccupationMatch(profile, essential, optional)
    // Only essential a counts: 1 / 5 = 20%
    expect(result.matchScore).toBe(20)
    expect(result.weightedScore).toBe(20)
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

const m = (o: Partial<RankableMatch>): RankableMatch => ({
  label: 'x', isco_code: '7212', matchScore: 50, weightedScore: 40, essentialTotal: 10, essentialCovered: 5, ...o,
})

describe('barandas del ranking', () => {
  it('exige ≥ 2 esenciales cubiertas de un total ≥ 5', () => {
    expect(isEligibleMatch(m({ essentialCovered: 1, essentialTotal: 2, matchScore: 50 }))).toBe(false)
    expect(isEligibleMatch(m({ essentialCovered: 3, essentialTotal: 4 }))).toBe(false)
    expect(isEligibleMatch(m({ essentialCovered: 2, essentialTotal: 5 }))).toBe(true)
  })

  it('excluye el gran grupo CIUO 0', () => {
    expect(isEligibleMatch(m({ isco_code: '0110' }))).toBe(false)
  })

  it('ordena por cobertura, después nivel ponderado, después avisos activos', () => {
    const a = m({ label: 'a', isco_code: '1111', matchScore: 60, weightedScore: 40 })
    const b = m({ label: 'b', isco_code: '2222', matchScore: 60, weightedScore: 50 })
    const c = m({ label: 'c', isco_code: '3333', matchScore: 60, weightedScore: 50 })
    const d = m({ label: 'd', isco_code: '4444', matchScore: 70, weightedScore: 10 })
    const activas = { '3333': 5, '2222': 1 }
    expect([a, b, c, d].sort((x, y) => compareMatches(x, y, activas)).map(x => x.label)).toEqual(['d', 'c', 'b', 'a'])
  })

  it('máximo 2 por CIUO de 4 dígitos en el top 10; el resto pasa después', () => {
    const lista = [
      ...['a', 'b', 'c'].map(l => ({ label: l, isco_code: '5223' })),
      ...Array.from({ length: 10 }, (_, i) => ({ label: `o${i}`, isco_code: `90${i}0` })),
    ]
    const r = capPerIsco(lista)
    expect(r.slice(0, 10).filter(x => x.isco_code === '5223')).toHaveLength(2)
    expect(r.map(x => x.label)).toContain('c')
    expect(r.findIndex(x => x.label === 'c')).toBeGreaterThanOrEqual(10)
    expect(r).toHaveLength(lista.length)
  })
})
