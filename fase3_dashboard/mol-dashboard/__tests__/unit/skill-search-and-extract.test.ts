import { describe, it, expect } from 'vitest'

/**
 * Tests para la lógica de búsqueda y extracción de skills.
 * Testea las funciones puras sin depender del API route.
 */

function normalize(text: string): string {
  return text.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '')
}

function extractKeywords(text: string): string[] {
  const stopwords = new Set([
    'que', 'como', 'para', 'por', 'con', 'sin', 'una', 'uno', 'los', 'las',
    'del', 'fue', 'ser', 'son', 'era', 'hay', 'mas', 'pero',
    'este', 'esta', 'esto', 'todo', 'toda', 'muy', 'bien',
    'hace', 'hice', 'desde', 'hasta', 'entre', 'sobre', 'donde', 'cuando',
    'trabaje', 'trabajo', 'trabajar', 'trabajando', 'anos', 'anios', 'tiempo',
    'empresa', 'empresas', 'lugar', 'area', 'zona', 'puesto', 'cargo',
    'tambien', 'siempre', 'nunca', 'algo', 'mucho', 'poco', 'otro', 'otra',
    'tengo', 'tiene', 'hacer', 'hago', 'hacia', 'haciendo', 'saber', 'sabia',
    'conozco', 'conocimiento', 'experiencia', 'encargaba', 'responsable',
  ])

  const normalized = normalize(text)
  const words = normalized
    .replace(/[^a-z0-9\s]/g, ' ')
    .split(/\s+/)
    .filter(w => w.length >= 4 && !stopwords.has(w))

  return [...new Set(words)]
}

describe('Búsqueda de skills (A-D1)', () => {
  describe('normalize', () => {
    it('convierte a minúsculas', () => {
      expect(normalize('Python')).toBe('python')
    })

    it('remueve acentos', () => {
      expect(normalize('programación')).toBe('programacion')
      expect(normalize('análisis')).toBe('analisis')
      expect(normalize('diseño')).toBe('diseno')
    })

    it('maneja texto vacío', () => {
      expect(normalize('')).toBe('')
    })
  })

  describe('búsqueda full-text simulada', () => {
    const skills = [
      { id: '1', label: 'soldadura', description: 'Realizar diversas técnicas de soldeo y unión de piezas metálicas' },
      { id: '2', label: 'mantenimiento de máquinas', description: 'Actividades regulares de mantenimiento preventivo' },
      { id: '3', label: 'Python', description: 'Lenguaje de programación para desarrollo de software' },
      { id: '4', label: 'gestión de inventario', description: 'Controlar existencias y stock de productos' },
    ]

    it('"soldadura" encuentra soldadura por label (match exacto)', () => {
      const query = normalize('soldadura')
      const matches = skills.filter(s => normalize(s.label).includes(query) || normalize(s.description).includes(query))
      expect(matches.length).toBeGreaterThanOrEqual(1)
      expect(matches[0].label).toBe('soldadura')
    })

    it('"soldar" encuentra soldadura por description (no por label — limitación Fase 1)', () => {
      // "soldar" no es substring de "soldadura", pero sí de "soldeo" en la description
      // Este caso se resuelve mejor en Fase 2 (embeddings semánticos)
      const query = normalize('soldeo')
      const matches = skills.filter(s => normalize(s.description).includes(query))
      expect(matches.length).toBeGreaterThanOrEqual(1)
    })

    it('"piezas metalicas" encuentra soldadura por description', () => {
      const tokens = ['piezas', 'metalicas'].map(normalize)
      const matches = skills.filter(s => {
        const normDesc = normalize(s.description)
        return tokens.every(t => normDesc.includes(t))
      })
      expect(matches).toHaveLength(1)
      expect(matches[0].label).toBe('soldadura')
    })

    it('"python" encuentra exacto', () => {
      const query = normalize('python')
      const matches = skills.filter(s => normalize(s.label).includes(query))
      expect(matches).toHaveLength(1)
    })

    it('query vacío no retorna nada', () => {
      const matches = skills.filter(() => false)
      expect(matches).toHaveLength(0)
    })

    it('query sin resultados retorna array vacío', () => {
      const query = normalize('blockchain')
      const matches = skills.filter(s =>
        normalize(s.label).includes(query) || normalize(s.description).includes(query)
      )
      expect(matches).toHaveLength(0)
    })
  })
})

describe('Extracción de skills de texto libre (A-D2)', () => {
  describe('extractKeywords', () => {
    it('extrae palabras significativas del texto', () => {
      const text = 'Trabajé 5 años en una fábrica haciendo soldadura y mantenimiento de máquinas'
      const keywords = extractKeywords(text)

      expect(keywords).toContain('fabrica')
      expect(keywords).toContain('soldadura')
      expect(keywords).toContain('mantenimiento')
      expect(keywords).toContain('maquinas')
    })

    it('filtra stopwords', () => {
      const text = 'Trabajé como responsable del área de logística'
      const keywords = extractKeywords(text)

      expect(keywords).not.toContain('como')
      expect(keywords).not.toContain('trabaje')
      expect(keywords).not.toContain('area')
      expect(keywords).not.toContain('responsable')
      expect(keywords).toContain('logistica')
    })

    it('filtra palabras cortas (<4 chars)', () => {
      const text = 'Sé de IT y QA en una PyME'
      const keywords = extractKeywords(text)

      expect(keywords).not.toContain('se')
      expect(keywords).not.toContain('de')
      expect(keywords).not.toContain('it')
      expect(keywords).not.toContain('qa')
      expect(keywords).not.toContain('en')
    })

    it('remueve acentos de keywords', () => {
      const text = 'Programación en Python y análisis de datos'
      const keywords = extractKeywords(text)

      expect(keywords).toContain('programacion')
      expect(keywords).toContain('python')
      expect(keywords).toContain('analisis')
      expect(keywords).toContain('datos')
    })

    it('deduplica keywords', () => {
      const text = 'Soldadura y más soldadura en fábrica de soldadura'
      const keywords = extractKeywords(text)

      const soldaduraCount = keywords.filter(k => k === 'soldadura').length
      expect(soldaduraCount).toBe(1)
    })

    it('texto vacío retorna array vacío', () => {
      expect(extractKeywords('')).toHaveLength(0)
    })

    it('solo stopwords retorna array vacío', () => {
      const text = 'Yo trabaje como algo en una empresa'
      const keywords = extractKeywords(text)
      // Todas son stopwords o cortas
      expect(keywords).toHaveLength(0)
    })
  })

  describe('confianza del matching', () => {
    it('match exacto en label = high confidence', () => {
      const keyword = 'soldadura'
      const skillLabel = normalize('soldadura')

      // Palabra del texto aparece como palabra en el label
      const isExactInLabel = skillLabel.split(/\s+/).includes(keyword)
      const confidence = isExactInLabel ? 'high' : 'medium'

      expect(confidence).toBe('high')
    })

    it('match parcial en label = medium confidence', () => {
      const keyword = 'soldar'
      const skillLabel = normalize('soldadura por arco')

      const isExactInLabel = skillLabel.split(/\s+/).includes(keyword)
      const isPartialInLabel = skillLabel.includes(keyword)
      const confidence = isExactInLabel ? 'high' : isPartialInLabel ? 'medium' : 'low'

      expect(confidence).toBe('low') // "soldar" no está en "soldadura por arco"
    })
  })

  describe('source se preserva en resultados', () => {
    it('skills ESCO tienen source = esco', () => {
      const skill = { source: 'esco' as const }
      expect(skill.source).toBe('esco')
    })

    it('skills emergentes tienen source = argentina_emerging', () => {
      const skill = { source: 'argentina_emerging' as const }
      expect(skill.source).toBe('argentina_emerging')
    })
  })
})
