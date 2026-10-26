import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { RecomendacionCard, TrayectoriaCard } from '@/components/oficina-empleo/RecomendacionCard'

const contexto = [
  { label: 'albañil', cubiertas: 12, esenciales_total: 19, avisos: 14, demanda: 'Demanda estable',
    cursos: [{ titulo: 'albanileria', institucion: 'CENTRO VECINAL ITUZAINGO', provincia: 'Cordoba', municipio: 'Cordoba', modalidad: 'PRESENCIAL' }] },
]

describe('RecomendacionCard', () => {
  it('chips de la UI, secciones y formación con institución/modalidad cruzadas de la lista', () => {
    render(
      <RecomendacionCard
        titulo="Recomendación personalizada"
        secciones={{
          ocupacion: 'Albañil', tituloPrincipal: 'Por qué esta opción', textoPrincipal: 'Cubrís casi todo.',
          tituloOpciones: 'Otras opciones', opciones: [{ ocupacion: 'pintor de obra', motivo: 'Comparte tareas.' }],
          tituloPasos: 'Próximos pasos', pasos: ['Anotate en el curso.'],
          formacion: [{ curso: 'albanileria', motivo: 'Cubre lo que te falta.' }, { curso: 'curso inventado', motivo: 'x' }],
        }}
        contexto={contexto}
        fechaMax="2026-08-21"
      />
    )
    expect(screen.getByText('12/19 esenciales')).toBeTruthy()
    expect(screen.getByText('14 avisos')).toBeTruthy()
    expect(screen.getByText('Demanda estable')).toBeTruthy()
    expect(screen.getByText(/albanileria · CENTRO VECINAL ITUZAINGO · Presencial \(Cordoba, Córdoba\)/)).toBeTruthy()
    expect(screen.queryByText(/curso inventado/)).toBeNull()
    expect(screen.getByText(/avisos publicados hasta el 21\/08\/2026/)).toBeTruthy()
  })
})

describe('TrayectoriaCard', () => {
  it('etiqueta corta, chips de la UI, secciones con título, pasos numerados y cierre', () => {
    render(
      <TrayectoriaCard
        reco={{
          ocupacion: 'Albañil',
          diagnostico: 'Demo, ya colocás ladrillos.',
          recomendacion: 'Es tu camino más directo.',
          alternativas: [{ ocupacion: 'Pintor de obra', comentario: 'Puede servir, pero hay pocos avisos.' }],
          pasos: [{ accion: 'Anotate en el curso de albanileria.', por_que: 'Cubre lo que te falta.' }],
          cierre: 'Vas por buen camino.',
        }}
        contexto={[{ ...contexto[0], label: 'albañil' }, { label: 'pintor de obra/pintora de obra', cubiertas: 5, esenciales_total: 20, avisos: 15, demanda: 'Demanda estable', cursos: [] }]}
        fechaMax="2026-08-21"
      />
    )
    expect(screen.getByText('Albañil')).toBeTruthy()
    expect(screen.getByText('12/19 esenciales')).toBeTruthy()
    for (const t of ['Tu situación', 'El camino que te recomendamos', 'Otras posibilidades', 'Cómo seguir']) expect(screen.getByText(t)).toBeTruthy()
    expect(screen.getByText('Pintor de obra')).toBeTruthy()
    expect(screen.getByText('Anotate en el curso de albanileria.').className).toContain('font-semibold')
    expect(screen.getByText('Vas por buen camino.').className).toContain('italic')
  })
})
