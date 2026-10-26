import { describe, it, expect } from 'vitest'
import { parseTrayectoria, parseAnalisis, buscarCurso, demandaLabel, etiquetaOcupacion } from '@/lib/recomendacion-ia'
import { lineaUbicacionCurso, provinciaDisplay, esVirtual, formatoTitulo, formatearCurso } from '@/lib/cursos'

const CURSOS = [{ titulo: 'albanileria' }, { titulo: 'soldadura nivel inicial' }]

describe('parseTrayectoria', () => {
  it('devuelve los párrafos y respeta los topes (2 alternativas, 3 pasos)', () => {
    const raw = JSON.stringify({
      ocupacion: 'Albañil',
      diagnostico: 'Demo, hoy ya colocás ladrillos. Te falta interpretar planos.',
      recomendacion: 'Es el camino más corto.',
      alternativas: [1, 2, 3].map(i => ({ ocupacion: `o${i}`, comentario: 'c' })),
      pasos: [1, 2, 3, 4].map(i => ({ accion: `a${i}`, por_que: 'p' })),
      cierre: 'Vas bien.',
    })
    const r = parseTrayectoria(raw)!
    expect(r.ocupacion).toBe('Albañil')
    expect(r.alternativas).toHaveLength(2)
    expect(r.pasos.map(p => p.accion)).toEqual(['a1', 'a2', 'a3'])
    expect(r.cierre).toBe('Vas bien.')
  })

  it('null si el JSON no parsea o falta diagnóstico o recomendación', () => {
    expect(parseTrayectoria('Te recomiendo soldador porque…')).toBeNull()
    expect(parseTrayectoria(JSON.stringify({ ocupacion: 'x', diagnostico: 'y' }))).toBeNull()
  })
})

describe('parseAnalisis', () => {
  it('parsea resumen, destinos y recomendaciones; null sin resumen', () => {
    const r = parseAnalisis(JSON.stringify({ resumen: 'r', destinos: [{ ocupacion: 'calderero', motivo: 'm' }], recomendaciones: ['a'] }), [])!
    expect(r.destinos[0].ocupacion).toBe('calderero')
    expect(r.formacion).toEqual([])
    expect(parseAnalisis('{}', [])).toBeNull()
  })
})

describe('helpers', () => {
  it('buscarCurso tolera mayúsculas, tildes y comillas', () => {
    expect(buscarCurso('"Albañilería"', [{ titulo: 'albañileria' }])?.titulo).toBe('albañileria')
  })
  it('etiquetaOcupacion: forma antes de "/" con mayúscula', () => {
    expect(etiquetaOcupacion('soldador/soldadora')).toBe('Soldador')
    expect(etiquetaOcupacion('albañil')).toBe('Albañil')
  })
  it('demandaLabel: un solo indicador', () => {
    expect(demandaLabel('creciendo')).toBe('Demanda en alza')
    expect(demandaLabel(null)).toBe('Sin datos de tendencia')
  })
  it('línea de ubicación: presencial con localidad; virtual "se puede cursar desde"', () => {
    expect(lineaUbicacionCurso({ institucion: 'CENTRO VECINAL', municipio: 'Cordoba', provincia: 'Cordoba', modalidad: 'PRESENCIAL' }, 'Córdoba'))
      .toBe('CENTRO VECINAL · Cordoba, Córdoba · Presencial')
    expect(lineaUbicacionCurso({ institucion: 'UTN', municipio: 'X', provincia: 'Jujuy', modalidad: 'DISTANCIA' }, 'Santa Fe'))
      .toBe('UTN · Virtual · se puede cursar desde Santa Fe')
    expect(provinciaDisplay('Capital federal')).toBe('CABA')
    expect(esVirtual({ modalidad: 'DISTANCIA' })).toBe(true)
  })
})

describe('formatoTitulo (REGICE)', () => {
  it('solo cambia mayúsculas: no completa truncados ni agrega tildes', () => {
    expect(formatoTitulo('ESCUELA MUNICIPAL DE OFIC')).toBe('Escuela Municipal de Ofic')
    expect(formatoTitulo('albanileria')).toBe('Albanileria')
    expect(formatoTitulo('soldadura de estructura inicial')).toBe('Soldadura de Estructura Inicial')
    expect(formatoTitulo('BINDERPLUS SRL')).toBe('Binderplus SRL')
    expect(formatoTitulo('INDUSTRIAS MONTECOR S.R.L')).toBe('Industrias Montecor S.R.L')
  })
  it('formatearCurso aplica a título, institución y localidad', () => {
    expect(formatearCurso({ titulo: 'pintura de obra', institucion: 'SERVICIO HABITACIONAL Y D', municipio: 'CORDOBA' }))
      .toEqual({ titulo: 'Pintura de Obra', institucion: 'Servicio Habitacional y D', municipio: 'Cordoba' })
  })
})
