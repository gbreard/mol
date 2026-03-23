import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import TrainingImpact, { type TrainingImpactData } from '@/components/TrainingImpact'

const mockData: TrainingImpactData = {
  profile_id: 'p1',
  current_match: 60,
  max_potential_match: 85,
  gap_groups: [
    {
      skill_label: 'Python',
      courses: [
        {
          id: 1,
          name: 'Python para datos',
          certificacion: 'Certificado CABA',
          duracion: '3 meses',
          modalidad: 'Online',
          covers_skills: ['Python', 'Pandas'],
          url: 'https://example.com',
          delta_match: 15,
        },
        {
          id: 2,
          name: 'Intro Python',
          certificacion: '',
          duracion: '4 semanas',
          modalidad: 'Presencial',
          covers_skills: ['Python'],
          delta_match: 8,
        },
      ],
    },
    {
      skill_label: 'SQL',
      courses: [
        {
          id: 3,
          name: 'SQL básico',
          certificacion: '',
          duracion: '2 semanas',
          modalidad: 'Online',
          covers_skills: ['SQL'],
          delta_match: 10,
        },
      ],
    },
  ],
}

const emptyData: TrainingImpactData = {
  profile_id: 'p2',
  current_match: 90,
  max_potential_match: 90,
  gap_groups: [],
}

// ─── S17: TrainingImpact ──────────────────────────────────────────────────────

describe('S17 — TrainingImpact', () => {
  it('muestra compatibilidad actual y potencial', () => {
    const { container } = render(<TrainingImpact data={mockData} />)
    expect(container.textContent).toContain('60%')
    expect(container.textContent).toContain('85%')
  })

  it('muestra la mejora potencial total', () => {
    render(<TrainingImpact data={mockData} />)
    expect(screen.getByText('+25% mejora')).toBeInTheDocument()
  })

  it('muestra los grupos de brechas', () => {
    render(<TrainingImpact data={mockData} />)
    expect(screen.getByText('Python')).toBeInTheDocument()
    expect(screen.getByText('SQL')).toBeInTheDocument()
  })

  it('muestra los cursos con nombre', () => {
    render(<TrainingImpact data={mockData} />)
    expect(screen.getByText('Python para datos')).toBeInTheDocument()
    expect(screen.getByText('SQL básico')).toBeInTheDocument()
  })

  it('muestra delta match % por curso', () => {
    render(<TrainingImpact data={mockData} />)
    expect(screen.getByLabelText('Impacto: +15% compatibilidad')).toBeInTheDocument()
    expect(screen.getByLabelText('Impacto: +8% compatibilidad')).toBeInTheDocument()
  })

  it('hay un botón Derivar por curso', () => {
    render(<TrainingImpact data={mockData} />)
    const btns = screen.getAllByText('Derivar')
    expect(btns.length).toBe(3)
  })

  it('botón Derivar tiene min touch target', () => {
    render(<TrainingImpact data={mockData} />)
    const btn = screen.getAllByLabelText(/Derivar a/)[0]
    expect(btn.className).toContain('min-h-[44px]')
  })

  it('derivar llama onDerivar con id y nombre', () => {
    const onDerivar = vi.fn()
    render(<TrainingImpact data={mockData} onDerivar={onDerivar} />)
    fireEvent.click(screen.getAllByLabelText(/Derivar a/)[0])
    expect(onDerivar).toHaveBeenCalledWith(1, 'Python para datos')
  })

  it('después de derivar el botón cambia a "✓ Derivado"', () => {
    render(<TrainingImpact data={mockData} />)
    fireEvent.click(screen.getAllByLabelText(/Derivar a/)[0])
    expect(screen.getByText('✓ Derivado')).toBeInTheDocument()
  })

  it('sin brechas muestra mensaje vacío', () => {
    render(<TrainingImpact data={emptyData} />)
    expect(screen.getByText(/No hay brechas con cursos disponibles/)).toBeInTheDocument()
  })
})
