import { render, screen, waitFor } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import ProcesamientoPage from '@/app/admin/procesamiento/page'

vi.mock('recharts', () => ({
  PieChart: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  Pie: ({ data }: { data: { name: string; value: number }[] }) => (
    <div>{data?.map(d => <span key={d.name}>{d.name}</span>)}</div>
  ),
  Cell: () => null,
  BarChart: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  Bar: () => null,
  XAxis: () => null,
  YAxis: () => null,
  CartesianGrid: () => null,
  Tooltip: () => null,
  Legend: () => null,
  ResponsiveContainer: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}))

// ─── S25-S27: Dashboard Procesamiento ────────────────────────────────────────

describe('S25-S27 — ProcesamientoPage', () => {
  it('muestra título de la página', async () => {
    render(<ProcesamientoPage />)
    await waitFor(() => {
      expect(screen.getByText('Procesamiento')).toBeInTheDocument()
    })
  })

  it('muestra las 4 barras de progreso del pipeline', async () => {
    render(<ProcesamientoPage />)
    await waitFor(() => {
      expect(screen.getByText('NLP')).toBeInTheDocument()
    })
    expect(screen.getByText('Matching')).toBeInTheDocument()
    expect(screen.getByText('Validadas')).toBeInTheDocument()
    expect(screen.getByText('En Supabase')).toBeInTheDocument()
  })

  it('muestra el último run en el subtítulo', async () => {
    render(<ProcesamientoPage />)
    await waitFor(() => {
      expect(screen.getByText(/2026-03-21/)).toBeInTheDocument()
    })
  })

  it('muestra gráfico de método de matching con leyenda', async () => {
    render(<ProcesamientoPage />)
    await waitFor(() => {
      expect(screen.getByText('Método de matching')).toBeInTheDocument()
    })
    expect(screen.getAllByText('Por regla').length).toBeGreaterThan(0)
    expect(screen.getAllByText(/Por sem/i).length).toBeGreaterThan(0)
  })

  it('muestra tabla de detalle de errores por tipo', async () => {
    render(<ProcesamientoPage />)
    await waitFor(() => {
      expect(screen.getByText('Detalle de errores')).toBeInTheDocument()
    })
    expect(screen.getByText('error_isco_incorrecto')).toBeInTheDocument()
    expect(screen.getByText('error_ubicacion_vacia')).toBeInTheDocument()
  })

  it('tabla de errores muestra severidades', async () => {
    render(<ProcesamientoPage />)
    await waitFor(() => {
      expect(screen.getByText('alto')).toBeInTheDocument()
    })
    expect(screen.getByText('medio')).toBeInTheDocument()
    expect(screen.getByText('bajo')).toBeInTheDocument()
  })

  it('muestra métricas dual (coinciden/difieren/score) del último run', async () => {
    render(<ProcesamientoPage />)
    await waitFor(() => {
      expect(screen.getByText(/Dual coinciden/i)).toBeInTheDocument()
    })
    expect(screen.getByText(/0\.851/)).toBeInTheDocument()
  })
})
