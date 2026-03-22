import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import TransitionDemand, { type DemandOccupation } from '@/components/TransitionDemand'

const mockOccupations: DemandOccupation[] = [
  {
    ocupacion_label: 'Analista DevOps',
    isco: '2511',
    trend_pct: 35,
    match_score: 72,
    skills_gap: ['Kubernetes', 'CI/CD'],
    estimated_months: 6,
  },
  {
    ocupacion_label: 'Ingeniero de datos',
    isco: '2529',
    trend_pct: 28,
    match_score: 65,
    skills_gap: ['Spark', 'Airflow', 'dbt'],
    estimated_months: 9,
  },
]

describe('TransitionDemand', () => {
  it('tabla muestra todas las ocupaciones', () => {
    render(<TransitionDemand occupations={mockOccupations} />)
    expect(screen.getAllByText('Analista DevOps').length).toBeGreaterThan(0)
    expect(screen.getAllByText('Ingeniero de datos').length).toBeGreaterThan(0)
  })

  it('muestra tendencia % con signo +', () => {
    render(<TransitionDemand occupations={mockOccupations} />)
    expect(screen.getAllByText('+35%').length).toBeGreaterThan(0)
    expect(screen.getAllByText('+28%').length).toBeGreaterThan(0)
  })

  it('ordenado por match_score desc (accesibilidad)', () => {
    render(<TransitionDemand occupations={mockOccupations} />)
    const rows = screen.getAllByRole('row').slice(1) // skip header
    expect(rows[0]).toHaveTextContent('Analista DevOps') // 72% > 65%
    expect(rows[1]).toHaveTextContent('Ingeniero de datos')
  })

  it('muestra tiempo estimado en meses', () => {
    render(<TransitionDemand occupations={mockOccupations} />)
    expect(screen.getByText('6 meses')).toBeInTheDocument()
    expect(screen.getByText('9 meses')).toBeInTheDocument()
  })

  it('link ver cursos llama onViewCourses con isco', () => {
    const onViewCourses = vi.fn()
    render(<TransitionDemand occupations={mockOccupations} onViewCourses={onViewCourses} />)
    fireEvent.click(screen.getAllByLabelText('Ver cursos para Analista DevOps')[0])
    expect(onViewCourses).toHaveBeenCalledWith('2511')
  })

  it('link ver ofertas llama onViewOffers con isco', () => {
    const onViewOffers = vi.fn()
    render(<TransitionDemand occupations={mockOccupations} onViewOffers={onViewOffers} />)
    fireEvent.click(screen.getAllByLabelText('Ver ofertas para Analista DevOps')[0])
    expect(onViewOffers).toHaveBeenCalledWith('2511')
  })

  it('empty state cuando no hay ocupaciones', () => {
    render(<TransitionDemand occupations={[]} />)
    expect(screen.getByText(/No hay sugerencias/)).toBeInTheDocument()
  })
})
