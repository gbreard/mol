import { describe, it, expect } from 'vitest'
import { parseTrayectoria, parseAnalisis, buscarCurso, demandaLabel } from '@/lib/recomendacion-ia'
import { lineaUbicacionCurso, provinciaDisplay, esVirtual } from '@/lib/cursos'

const CURSOS = [{ titulo: 'albanileria' }, { titulo: 'soldadura nivel inicial' }]

describe('parseTrayectoria', () => {
  it('devuelve las secciones con los topes (3 alternativas, 3 pasos, 2 cursos)', () => {
    const raw = JSON.stringify({
      ocupacion: 'albañil',
      por_que: 'Cubrís la mayoría de lo que se pide.',
      alternativas: [1, 2, 3, 4].map(i => ({ ocupacion: `o${i}`, motivo: 'm' })),
      pasos: ['a', 'b', 'c', 'd'],
      formacion: [{ curso: 'albanileria', motivo: 'cubre lo que falta' }, { curso: 'Soldadura nivel inicial', motivo: 'x' }, { curso: 'albanileria', motivo: 'y' }],
    })
    const r = parseTrayectoria(raw, CURSOS)!
    expect(r.ocupacion).toBe('albañil')
    expect(r.alternativas).toHaveLength(3)
    expect(r.pasos).toEqual(['a', 'b', 'c'])
    expect(r.formacion.map(f => f.curso)).toEqual(['albanileria', 'soldadura nivel inicial'])
  })

  it('descarta cursos que no están en la lista filtrada (inventados)', () => {
    const raw = JSON.stringify({ ocupacion: 'x', por_que: 'y', formacion: [{ curso: 'Curso de liderazgo en Harvard', motivo: 'z' }] })
    expect(parseTrayectoria(raw, CURSOS)!.formacion).toEqual([])
  })

  it('null si el JSON no parsea o falta lo mínimo', () => {
    expect(parseTrayectoria('Te recomiendo soldador porque…', CURSOS)).toBeNull()
    expect(parseTrayectoria(JSON.stringify({ ocupacion: 'x' }), CURSOS)).toBeNull()
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
