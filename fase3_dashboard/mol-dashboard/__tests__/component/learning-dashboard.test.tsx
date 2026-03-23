import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import LearningDashboard, { type LearningData } from '@/components/LearningDashboard'

vi.mock('recharts', () => ({
  LineChart: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  Line: () => null,
  XAxis: () => null,
  YAxis: () => null,
  CartesianGrid: () => null,
  Tooltip: () => null,
  ResponsiveContainer: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  Legend: () => null,
}))

const mockData: LearningData = {
  total_reglas_activas: 124,
  total_reglas_creadas: 156,
  tasa_error_actual: 3.2,
  tasa_error_inicial: 18.5,
  timeline_errores: [
    { fecha: '2026-01-01', tasa_error: 18.5, total_procesadas: 100 },
    { fecha: '2026-02-01', tasa_error: 8.0, total_procesadas: 500 },
    { fecha: '2026-03-01', tasa_error: 3.2, total_procesadas: 1200 },
  ],
  timeline_reglas: [
    { fecha: '2026-01-10', regla_id: 'R001', tipo: 'creada', descripcion: 'Regla para Gerente de Ventas' },
    { fecha: '2026-02-05', regla_id: 'R002', tipo: 'modificada', descripcion: 'Ajuste ISCO contador' },
  ],
  gold_set: [
    { oferta_id: 1, titulo: 'Programador Python', isco_esperado: '2512', isco_obtenido: '2512', correcto: true, score: 0.95 },
    { oferta_id: 2, titulo: 'Gerente de Ventas', isco_esperado: '1221', isco_obtenido: '2433', correcto: false, score: 0.61 },
    { oferta_id: 3, titulo: 'Contador', isco_esperado: '2411', isco_obtenido: '2411', correcto: true, score: 0.98 },
  ],
}

// ─── S28: LearningDashboard ───────────────────────────────────────────────────

describe('S28 — LearningDashboard', () => {
  it('muestra KPI reglas activas', () => {
    render(<LearningDashboard data={mockData} />)
    expect(screen.getByText('124')).toBeInTheDocument()
    expect(screen.getByText('Reglas activas')).toBeInTheDocument()
  })

  it('muestra tasa de error actual', () => {
    const { container } = render(<LearningDashboard data={mockData} />)
    expect(container.textContent).toContain('3.2%')
  })

  it('muestra mejora desde inicio', () => {
    const { container } = render(<LearningDashboard data={mockData} />)
    expect(container.textContent).toContain('−15.3%')
  })

  it('muestra timeline de reglas', () => {
    render(<LearningDashboard data={mockData} />)
    expect(screen.getByText('Regla para Gerente de Ventas')).toBeInTheDocument()
    expect(screen.getByText('creada')).toBeInTheDocument()
    expect(screen.getByText('modificada')).toBeInTheDocument()
  })

  it('muestra tabla gold set con resultados', () => {
    render(<LearningDashboard data={mockData} />)
    expect(screen.getByText('Programador Python')).toBeInTheDocument()
    expect(screen.getByText('Gerente de Ventas')).toBeInTheDocument()
  })

  it('badge gold set muestra % correctos', () => {
    render(<LearningDashboard data={mockData} />)
    expect(screen.getByLabelText('Gold Set: 67% correctos')).toBeInTheDocument()
  })

  it('filas incorrectas tienen fondo rojo', () => {
    const { container } = render(<LearningDashboard data={mockData} />)
    const rows = container.querySelectorAll('tr.bg-red-50')
    expect(rows.length).toBe(1)
  })

  it('sin eventos de reglas muestra mensaje vacío', () => {
    render(<LearningDashboard data={{ ...mockData, timeline_reglas: [] }} />)
    expect(screen.getByText('Sin eventos de reglas.')).toBeInTheDocument()
  })
})
