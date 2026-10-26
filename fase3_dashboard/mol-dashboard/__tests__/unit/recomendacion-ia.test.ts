import { describe, it, expect } from 'vitest'
import { parseTrayectoria, parseAnalisis, buscarCurso, demandaLabel, etiquetaOcupacion, pulirTexto, limitarPasosGenericos, imperativoVoseante } from '@/lib/recomendacion-ia'
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
    expect(formatoTitulo('CFP N° 401 SAN MARTIN')).toBe('CFP N° 401 San Martin')
  })
  it('formatearCurso aplica a título, institución y localidad', () => {
    expect(formatearCurso({ titulo: 'pintura de obra', institucion: 'SERVICIO HABITACIONAL Y D', municipio: 'CORDOBA' }))
      .toEqual({ titulo: 'Pintura de Obra', institucion: 'Servicio Habitacional y D', municipio: 'Cordoba' })
  })
})

describe('controles deterministas de la trayectoria', () => {
  it('voseo y sin promesas de velocidad', () => {
    expect(pulirTexto('Cubres menos competencias, pero puedes cerrar esas brechas rápidamente.'))
      .toBe('Cubrís menos competencias, pero podés cerrar esas brechas.')
    expect(pulirTexto('Hoy estás trabajando en obra y pronto vas a avanzar.')).toBe('Hoy trabajás en obra y vas a avanzar.')
  })

  it('máximo un paso genérico de la Oficina, los específicos primero', () => {
    const pasos = [
      { accion: 'Armá tu CV con el orientador.' },
      { accion: 'Anotate en la bolsa de empleo de la Oficina.' },
      { accion: 'Anotate al curso "Soldador y Herreria".' },
    ]
    expect(limitarPasosGenericos(pasos).map(p => p.accion)).toEqual([
      'Anotate al curso "Soldador y Herreria".',
      'Armá tu CV con el orientador.',
    ])
  })

  it('parseTrayectoria aplica los controles', () => {
    const r = parseTrayectoria(JSON.stringify({
      ocupacion: 'x', diagnostico: 'Tienes base.', recomendacion: 'Podés cerrar brechas rápidamente.',
      pasos: [{ accion: 'Armá tu CV.', por_que: 'a' }, { accion: 'Anotate en la bolsa de empleo.', por_que: 'b' }],
    }))!
    expect(r.diagnostico).toBe('Tenés base.')
    expect(r.recomendacion).toBe('Podés cerrar brechas.')
    expect(r.pasos).toHaveLength(1)
  })
})

describe('imperativo, absolutos y certificación (casos reales de Jorge y Ramón)', () => {
  it('pasa el primer verbo de infinitivo a imperativo voseante', () => {
    expect(imperativoVoseante('Armar tu CV con el orientador.')).toBe('Armá tu CV con el orientador.')
    expect(imperativoVoseante('Reforzar la lectura de planos.')).toBe('Reforzá la lectura de planos.')
    expect(imperativoVoseante('Anotarse en la bolsa de empleo.')).toBe('Anotate en la bolsa de empleo.')
    expect(imperativoVoseante('Pedir una entrevista de orientación.')).toBe('Pedí una entrevista de orientación.')
    expect(imperativoVoseante('Anotate al curso.')).toBe('Anotate al curso.')
    expect(imperativoVoseante('Armá tu CV.')).toBe('Armá tu CV.')
  })

  const reco = (pasos: { accion: string; por_que: string }[], extra: Record<string, string> = {}) =>
    parseTrayectoria(JSON.stringify({ ocupacion: 'Soldador', diagnostico: 'Jorge, tenés base.', recomendacion: 'Tiene sentido.', pasos, ...extra }))!

  it('saca la oración absoluta del por qué (Jorge, paso 1)', () => {
    const r = reco([{ accion: 'Anotate al curso Soldador y Herreria para cubrir unir metales.', por_que: 'Ese curso cubre exactamente las competencias que te faltan para completar el perfil de soldador.' }])
    expect(r.pasos[0].accion).toBe('Anotate al curso Soldador y Herreria para cubrir unir metales.')
    expect(r.pasos[0].por_que).toBe('')
  })

  it('saca la promesa de cubrir todo (Ramón, paso 2) y la certificación (Ramón, paso 1)', () => {
    const r = reco([
      { accion: 'Anotate al curso "Albanileria" para examinar materiales.', por_que: 'Ese curso cubre la competencia que te falta y te brinda certificación práctica.' },
      { accion: 'Reforzá la competencia de interpretar planos en 2D.', por_que: 'Mejorar esa habilidad te permitirá cubrir todas las competencias esenciales del puesto.' },
    ])
    expect(r.pasos[0].por_que).toBe('')
    expect(JSON.stringify(r)).not.toMatch(/certific|todas las competencias/i)
  })

  it('acción: corta el fragmento absoluto y conserva lo concreto', () => {
    const r = reco([{ accion: 'Armar tu CV con el orientador para completar el perfil de soldador.', por_que: 'Te ayuda.' }])
    expect(r.pasos[0].accion).toBe('Armá tu CV con el orientador.')
  })

  it('en el diagnóstico "todas las competencias" se mantiene (es correcto con 100% de cobertura)', () => {
    const r = reco([], { diagnostico: 'Armando, cubrís todas las competencias esenciales. Tenés base fuerte.' })
    expect(r.diagnostico).toBe('Armando, cubrís todas las competencias esenciales. Tenés base fuerte.')
  })
})
