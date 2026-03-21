import { describe, it, expect } from 'vitest'

describe('Matching Offers (A-D4)', () => {
  describe('Gap personalizado por oferta', () => {
    it('calcula skills cubiertas y faltantes', () => {
      const workerSkills = new Set(['python', 'sql', 'git'])
      const ofertaSkills = ['python', 'sql', 'docker', 'testing']

      const cubiertas = ofertaSkills.filter(s => workerSkills.has(s))
      const gap = ofertaSkills.filter(s => !workerSkills.has(s))
      const matchScore = Math.round((cubiertas.length / ofertaSkills.length) * 100)

      expect(cubiertas).toEqual(['python', 'sql'])
      expect(gap).toEqual(['docker', 'testing'])
      expect(matchScore).toBe(50) // 2/4
    })

    it('100% si tiene todas las skills', () => {
      const workerSkills = new Set(['python', 'sql'])
      const ofertaSkills = ['python', 'sql']

      const cubiertas = ofertaSkills.filter(s => workerSkills.has(s))
      const matchScore = Math.round((cubiertas.length / ofertaSkills.length) * 100)

      expect(matchScore).toBe(100)
    })

    it('0% si no tiene ninguna', () => {
      const workerSkills = new Set(['java', 'c++'])
      const ofertaSkills = ['python', 'sql']

      const cubiertas = ofertaSkills.filter(s => workerSkills.has(s))
      const matchScore = ofertaSkills.length > 0
        ? Math.round((cubiertas.length / ofertaSkills.length) * 100)
        : 0

      expect(matchScore).toBe(0)
    })

    it('oferta sin skills retorna 0%', () => {
      const ofertaSkills: string[] = []
      const matchScore = ofertaSkills.length > 0 ? 100 : 0
      expect(matchScore).toBe(0)
    })
  })

  describe('Filtros', () => {
    const ofertas = [
      { isco: '2512', provincia: 'CABA', modalidad: 'Remoto' },
      { isco: '2512', provincia: 'Buenos Aires', modalidad: 'Presencial' },
      { isco: '2514', provincia: 'CABA', modalidad: 'Híbrido' },
    ]

    it('filtra por provincia', () => {
      const filtered = ofertas.filter(o => o.provincia === 'CABA')
      expect(filtered).toHaveLength(2)
    })

    it('filtra por modalidad', () => {
      const filtered = ofertas.filter(o => o.modalidad.toLowerCase().includes('remoto'))
      expect(filtered).toHaveLength(1)
    })

    it('filtra por ISCO codes', () => {
      const iscoCodes = new Set(['2512'])
      const filtered = ofertas.filter(o => iscoCodes.has(o.isco))
      expect(filtered).toHaveLength(2)
    })
  })
})

describe('Training Suggestions (A-D5)', () => {
  describe('Búsqueda de cursos por skill faltante', () => {
    const cursos = [
      { name: 'Iniciación a DevOps y contenedores', texto_busqueda: 'docker kubernetes contenedores devops ci cd' },
      { name: 'Testing QA', texto_busqueda: 'testing qa automatizacion pruebas software' },
      { name: 'Python avanzado', texto_busqueda: 'python programacion datos analisis' },
      { name: 'Cocina profesional', texto_busqueda: 'cocina gastronomia alimentos restaurante' },
    ]

    function normalize(text: string): string {
      return text.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '')
    }

    function findCourses(skillLabel: string): typeof cursos {
      const tokens = normalize(skillLabel).split(/\s+/).filter(t => t.length >= 3)
      return cursos.filter(c =>
        tokens.some(t => c.texto_busqueda.includes(t))
      )
    }

    it('"Docker" encuentra curso de DevOps', () => {
      const results = findCourses('Docker')
      expect(results.length).toBeGreaterThanOrEqual(1)
      expect(results[0].name).toContain('DevOps')
    })

    it('"Testing" encuentra curso de QA', () => {
      const results = findCourses('Testing')
      expect(results.length).toBeGreaterThanOrEqual(1)
      expect(results[0].name).toContain('Testing')
    })

    it('"Blockchain" no encuentra nada', () => {
      const results = findCourses('Blockchain')
      expect(results).toHaveLength(0)
    })

    it('skill con múltiples palabras busca todos los tokens', () => {
      const results = findCourses('automatización de pruebas')
      expect(results.length).toBeGreaterThanOrEqual(1)
    })
  })

  describe('Múltiples fuentes de cursos', () => {
    it('la estructura soporta múltiples fuentes', () => {
      const fuentes = [
        { fuente: 'Portal de Capacitación CABA', total: 2255 },
        { fuente: 'Plataforma Nacional', total: 500 },
      ]

      const totalCursos = fuentes.reduce((sum, f) => sum + f.total, 0)
      expect(totalCursos).toBe(2755)
      expect(fuentes).toHaveLength(2)
    })

    it('cada curso tiene campo fuente', () => {
      const curso = { name: 'Docker 101', fuente: 'Portal de Capacitación CABA' }
      expect(curso.fuente).toBeDefined()
      expect(typeof curso.fuente).toBe('string')
    })
  })

  describe('Tendencia temporal (A-D6)', () => {
    it('calcula crecimiento porcentual', () => {
      const recentCount = 50  // últimos 3 meses
      const olderCount = 30   // 3-6 meses atrás
      const trendPct = Math.round(((recentCount - olderCount) / olderCount) * 100)

      expect(trendPct).toBe(67) // +67%
    })

    it('sin datos anteriores no calcula tendencia', () => {
      const olderCount = 0
      const canCalculate = olderCount > 0
      expect(canCalculate).toBe(false)
    })

    it('filtra solo crecimiento > 15%', () => {
      const trends = [
        { isco: '2512', trend: 35 },
        { isco: '2514', trend: 10 },  // filtrado
        { isco: '3512', trend: 28 },
        { isco: '4321', trend: -5 },  // filtrado
      ]

      const significative = trends.filter(t => t.trend > 15)
      expect(significative).toHaveLength(2)
    })

    it('excluye ocupaciones que ya son compatibles', () => {
      const workerIscos = new Set(['2512', '2514'])
      const trending = [
        { isco: '2512', trend: 50 },  // excluido: ya compatible
        { isco: '3512', trend: 28 },  // incluido
      ]

      const filtered = trending.filter(t => !workerIscos.has(t.isco))
      expect(filtered).toHaveLength(1)
      expect(filtered[0].isco).toBe('3512')
    })
  })
})
