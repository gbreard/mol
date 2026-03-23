import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import MarketBenchmark, { type MarketBenchmarkData } from '@/components/MarketBenchmark'

const mockData: MarketBenchmarkData = {
  jurisdiccion: 'CABA',
  total_ofertas: 5200,
  total_perfiles: 1800,
  skills: [
    {
      uri: 'esco:1',
      label: 'Python',
      demanda_pct: 45,
      disponibilidad_pct: 18,
      brecha: 27,
      dificultad: 'alta',
      tendencia: 'subiendo',
    },
    {
      uri: 'esco:2',
      label: 'Excel',
      demanda_pct: 60,
      disponibilidad_pct: 55,
      brecha: 5,
      dificultad: 'baja',
      tendencia: 'estable',
    },
    {
      uri: 'esco:3',
      label: 'Atención al cliente',
      demanda_pct: 70,
      disponibilidad_pct: 65,
      brecha: 5,
      dificultad: 'media',
      tendencia: 'bajando',
    },
  ],
}

const noAlertData: MarketBenchmarkData = {
  ...mockData,
  skills: mockData.skills.filter((s) => s.dificultad !== 'alta'),
}

// ─── S19: MarketBenchmark ─────────────────────────────────────────────────────

describe('S19 — MarketBenchmark', () => {
  it('muestra cantidad de ofertas y perfiles', () => {
    const { container } = render(<MarketBenchmark data={mockData} />)
    // Locale may render as 5.200 (es-AR) or 5,200 (en-US/happy-dom)
    expect(container.textContent).toMatch(/5[.,]200/)
    expect(container.textContent).toMatch(/1[.,]800/)
  })

  it('muestra las skills en la tabla', () => {
    render(<MarketBenchmark data={mockData} />)
    expect(screen.getAllByText('Python').length).toBeGreaterThan(0)
    expect(screen.getByText('Excel')).toBeInTheDocument()
    expect(screen.getByText('Atención al cliente')).toBeInTheDocument()
  })

  it('muestra alerta de escasez para skills con dificultad alta', () => {
    render(<MarketBenchmark data={mockData} />)
    expect(screen.getByText(/escasez crítica en CABA/)).toBeInTheDocument()
    expect(screen.getByLabelText('Escasez crítica: Python')).toBeInTheDocument()
  })

  it('sin skills de dificultad alta no muestra alerta', () => {
    render(<MarketBenchmark data={noAlertData} />)
    expect(screen.queryByText(/escasez crítica/)).not.toBeInTheDocument()
  })

  it('muestra brechas con signo + para brechas positivas', () => {
    render(<MarketBenchmark data={mockData} />)
    expect(screen.getByLabelText('Brecha de Python: +27%')).toBeInTheDocument()
  })

  it('muestra badge de dificultad por skill', () => {
    render(<MarketBenchmark data={mockData} />)
    expect(screen.getByText('alta')).toBeInTheDocument()
    expect(screen.getByText('baja')).toBeInTheDocument()
    expect(screen.getByText('media')).toBeInTheDocument()
  })

  it('muestra íconos de tendencia', () => {
    render(<MarketBenchmark data={mockData} />)
    expect(screen.getByLabelText('Tendencia: subiendo')).toBeInTheDocument()
    expect(screen.getByLabelText('Tendencia: estable')).toBeInTheDocument()
    expect(screen.getByLabelText('Tendencia: bajando')).toBeInTheDocument()
  })
})
