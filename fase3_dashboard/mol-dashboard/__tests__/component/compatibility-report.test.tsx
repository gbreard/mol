import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import CompatibilityReport, { type ReportData } from '@/components/CompatibilityReport'

const mockData: ReportData = {
  candidato_nombre: 'Juan Perez',
  ocupacion_label: 'Desarrollador de software',
  ocupacion_isco: '2512',
  match_score: 78,
  perfil_consolidado_version: 'v1.0',
  estado: 'activo',
  created_at: '2026-03-18T00:00:00Z',
  expira_at: '2026-05-18T00:00:00Z',
  skills_candidato: [],
  skills_requeridas: [
    { uri: 'esco:001', label: 'JavaScript', type: 'skill', source: 'esco' },
    { uri: 'esco:002', label: 'Python', type: 'skill', source: 'esco' },
    { uri: 'esco:003', label: 'Docker', type: 'skill', source: 'esco' },
  ],
  skills_cubiertas: [
    { uri: 'esco:001', label: 'JavaScript', type: 'skill', source: 'esco' },
    { uri: 'esco:002', label: 'Python', type: 'skill', source: 'esco' },
  ],
  skills_gap: [
    { uri: 'esco:003', label: 'Docker', type: 'skill', source: 'esco' },
  ],
}

describe('CompatibilityReport', () => {
  it('renderiza con datos completos', () => {
    render(<CompatibilityReport data={mockData} />)
    expect(screen.getByText('Juan Perez')).toBeInTheDocument()
    expect(screen.getByText('Desarrollador de software')).toBeInTheDocument()
    expect(screen.getByText('2512')).toBeInTheDocument()
  })

  it('muestra porcentaje de compatibilidad calculado', () => {
    render(<CompatibilityReport data={mockData} />)
    // 2/3 = 67%
    expect(screen.getByText('67%')).toBeInTheDocument()
  })

  it('no muestra DNI en ninguna parte', () => {
    render(<CompatibilityReport data={mockData} />)
    expect(screen.queryByText(/DNI/i)).not.toBeInTheDocument()
    expect(screen.queryByText(/documento/i)).not.toBeInTheDocument()
  })

  it('editar skills recalcula el porcentaje', () => {
    render(<CompatibilityReport data={mockData} />)
    // Entrar en modo edición
    fireEvent.click(screen.getByText('Editar'))
    // Quitar Docker (faltante) → required queda con 2 skills, covered 2 → 100%
    fireEvent.click(screen.getByLabelText('Quitar Docker'))
    expect(screen.getByText('100%')).toBeInTheDocument()
    expect(screen.getByText('(recalculada)')).toBeInTheDocument()
  })

  it('restaurar vuelve al puntaje original', () => {
    render(<CompatibilityReport data={mockData} />)
    fireEvent.click(screen.getByText('Editar'))
    fireEvent.click(screen.getByLabelText('Quitar Docker'))
    // Ahora aparece el botón restaurar
    fireEvent.click(screen.getByText('Restaurar original'))
    expect(screen.getByText('67%')).toBeInTheDocument()
    expect(screen.queryByText('(recalculada)')).not.toBeInTheDocument()
  })

  it('muestra seccion Sobre el MOL', () => {
    render(<CompatibilityReport data={mockData} />)
    expect(screen.getByText('Sobre el MOL')).toBeInTheDocument()
    expect(screen.getByText(/OEDE/)).toBeInTheDocument()
  })
})
