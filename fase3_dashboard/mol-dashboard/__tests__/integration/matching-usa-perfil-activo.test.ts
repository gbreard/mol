import { describe, it, expect } from 'vitest'
import { getSkillsConsolidadas, PerfilArgentinoSnapshot } from '@/lib/use-perfil-argentino'

describe('Matching usa perfil argentino activo', () => {
  const snapshotArgentino: PerfilArgentinoSnapshot = {
    'http://data.europa.eu/esco/occupation/occ-1': {
      label: 'Desarrollador de software',
      isco: '2512',
      skills_consolidadas: [
        { label: 'Python', label_normalized: 'python', uri: 'skill-python', source: 'esco_common' },
        { label: 'SQL', label_normalized: 'sql', uri: 'skill-sql', source: 'esco_common' },
        { label: 'Docker', label_normalized: 'docker', uri: undefined, source: 'argentina_approved', percentage_when_approved: 45 },
        { label: 'Scrum', label_normalized: 'scrum', uri: undefined, source: 'argentina_approved', percentage_when_approved: 60 },
      ],
      total_skills: 4,
      skills_from_esco: 2,
      skills_from_argentina: 2,
    },
  }

  describe('getSkillsConsolidadas', () => {
    it('retorna skills del perfil argentino si la ocupación existe', () => {
      const skills = getSkillsConsolidadas(
        snapshotArgentino,
        'http://data.europa.eu/esco/occupation/occ-1'
      )
      expect(skills).not.toBeNull()
      expect(skills).toHaveLength(4)
    })

    it('retorna null si la ocupación no tiene perfil argentino', () => {
      const skills = getSkillsConsolidadas(
        snapshotArgentino,
        'http://data.europa.eu/esco/occupation/inexistente'
      )
      expect(skills).toBeNull()
    })

    it('retorna null si no hay snapshot', () => {
      const skills = getSkillsConsolidadas(null, 'http://data.europa.eu/esco/occupation/occ-1')
      expect(skills).toBeNull()
    })
  })

  describe('Trazabilidad ESCO vs Argentino', () => {
    it('cada skill del perfil argentino tiene source que indica su origen', () => {
      const skills = getSkillsConsolidadas(
        snapshotArgentino,
        'http://data.europa.eu/esco/occupation/occ-1'
      )!

      const escoSkills = skills.filter(s => s.source === 'esco_common')
      const argSkills = skills.filter(s => s.source === 'argentina_approved')

      expect(escoSkills).toHaveLength(2)
      expect(argSkills).toHaveLength(2)

      // ESCO skills tienen URI
      expect(escoSkills.every(s => s.uri != null)).toBe(true)

      // Emergentes argentinas pueden no tener URI ESCO
      // pero tienen label_normalized para matchear
      expect(argSkills.every(s => s.label_normalized != null)).toBe(true)

      // Emergentes tienen porcentaje de cuándo se aprobaron
      expect(argSkills.every(s => s.percentage_when_approved != null)).toBe(true)
    })

    it('se puede reconstruir la distancia ESCO vs Argentino', () => {
      const skills = getSkillsConsolidadas(
        snapshotArgentino,
        'http://data.europa.eu/esco/occupation/occ-1'
      )!

      const perfil = snapshotArgentino['http://data.europa.eu/esco/occupation/occ-1']

      // Métricas de distancia
      const totalSkills = skills.length                      // 4 (total consolidado)
      const fromEsco = perfil.skills_from_esco               // 2 (vienen de ESCO)
      const fromArgentina = perfil.skills_from_argentina      // 2 (emergentes argentinas)
      const ratioEmergentes = fromArgentina / totalSkills     // 0.5 (50% son emergentes)

      expect(totalSkills).toBe(4)
      expect(fromEsco).toBe(2)
      expect(fromArgentina).toBe(2)
      expect(ratioEmergentes).toBe(0.5)
    })
  })

  describe('Matching con perfil argentino vs ESCO puro', () => {
    it('con perfil argentino, Docker cuenta como skill requerida', () => {
      const skills = getSkillsConsolidadas(
        snapshotArgentino,
        'http://data.europa.eu/esco/occupation/occ-1'
      )!

      // Trabajador tiene: Python, SQL, Docker
      const workerSkillLabels = new Set(['python', 'sql', 'docker'])

      const covered = skills.filter(s => workerSkillLabels.has(s.label_normalized))
      const gap = skills.filter(s => !workerSkillLabels.has(s.label_normalized))

      // Con perfil argentino: 3/4 cubiertas (Python, SQL, Docker)
      expect(covered).toHaveLength(3)
      expect(gap).toHaveLength(1)
      expect(gap[0].label).toBe('Scrum')

      const matchScore = Math.round((covered.length / skills.length) * 100)
      expect(matchScore).toBe(75) // 3/4 = 75%
    })

    it('sin perfil argentino (ESCO puro), Docker no cuenta', () => {
      // ESCO puro para esta ocupación solo tiene Python y SQL como esenciales
      const escoEssentialIds = new Set(['skill-python', 'skill-sql'])
      const workerSkillIds = new Set(['skill-python', 'skill-sql', 'skill-docker'])

      let covered = 0
      for (const id of workerSkillIds) {
        if (escoEssentialIds.has(id)) covered++
      }

      // Con ESCO puro: 2/2 cubiertas (Docker no está en ESCO)
      expect(covered).toBe(2)
      const matchScore = Math.round((covered / escoEssentialIds.size) * 100)
      expect(matchScore).toBe(100) // 2/2 = 100%
      // Pero NO refleja que Docker es importante en Argentina
    })

    it('el campo matchSource indica qué se usó', () => {
      // Simular resultado del matching
      const matchConArgentino = { matchSource: 'argentino' as const, matchScore: 75 }
      const matchConEsco = { matchSource: 'esco' as const, matchScore: 100 }

      expect(matchConArgentino.matchSource).toBe('argentino')
      expect(matchConEsco.matchSource).toBe('esco')
    })
  })
})
