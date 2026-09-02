import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { http, HttpResponse } from 'msw'
import { server } from '../mocks/server'
import ScrapingPage from '@/app/admin/scraping/page'

vi.mock('recharts', () => ({
  BarChart: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  Bar: () => null,
  XAxis: () => null,
  YAxis: () => null,
  CartesianGrid: () => null,
  Tooltip: () => null,
  ResponsiveContainer: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  Legend: () => null,
}))

describe('S23 — ScrapingPage (VPS data)', () => {
  it('muestra titulo y cantidad de fuentes', async () => {
    render(<ScrapingPage />)
    await waitFor(() => {
      expect(screen.getByText(/Scraping — Portales/i)).toBeInTheDocument()
    })
    // VPS mock has 6 portales
    expect(screen.getByText(/fuentes/)).toBeInTheDocument()
  })

  it('muestra cards con datos locales', async () => {
    render(<ScrapingPage />)
    await waitFor(() => {
      expect(screen.getAllByText(/^Total$/).length).toBeGreaterThanOrEqual(1)
    }, { timeout: 3000 })
    expect(screen.getAllByText(/Validadas/).length).toBeGreaterThan(0)
  })

  it('boton Actualizar recarga datos', async () => {
    render(<ScrapingPage />)
    await waitFor(() => {
      expect(screen.getByText(/Scraping — Portales/i)).toBeInTheDocument()
    })
    const btn = screen.getByRole('button', { name: /Actualizar/i })
    fireEvent.click(btn)
    await waitFor(() => {
      expect(screen.getByText(/Scraping — Portales/i)).toBeInTheDocument()
    })
  })

  it('toggle fecha scraping / fecha publicacion', async () => {
    render(<ScrapingPage />)
    await waitFor(() => {
      expect(screen.getByText(/Fecha scraping/i)).toBeInTheDocument()
    })
    const btnPub = screen.getByRole('button', { name: /Fecha publicacion/i })
    fireEvent.click(btnPub)
    expect(btnPub).toHaveClass('bg-white')
  })

  it('filtros de periodo presentes', async () => {
    render(<ScrapingPage />)
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /7 dias/i })).toBeInTheDocument()
    })
    expect(screen.getByRole('button', { name: /1 mes/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Todo/i })).toBeInTheDocument()
  })

  it('cards muestran Total / 7 dias / Hoy / Validadas', async () => {
    render(<ScrapingPage />)
    await waitFor(() => {
      expect(screen.getAllByText(/^Total$/).length).toBeGreaterThan(0)
    })
    expect(screen.getAllByText(/Validadas/).length).toBeGreaterThan(0)
    expect(screen.getAllByText(/7 dias/).length).toBeGreaterThan(0)
  })

  it('muestra cadena de datos', async () => {
    render(<ScrapingPage />)
    await waitFor(() => {
      expect(screen.getByText(/Cadena de datos/)).toBeInTheDocument()
    })
  })
})

// E2E: simular (por query mockeada) un portal atrasado y uno fresco, y verificar
// que la alerta por cadencia aparece SOLO para el atrasado — sin esperar rotura real.
describe('S23 — alertas por cadencia (simulación de portal atrasado)', () => {
  const iso = (msAgo: number) => new Date(Date.now() - msAgo).toISOString()
  const H = 3_600_000

  it('portal VPS atrasado dispara alerta; portal local fresco no', async () => {
    server.use(
      http.get('https://test.supabase.co/rest/v1/scraping_live_stats', () =>
        HttpResponse.json({
          id: 'current', total_ofertas: 25000,
          portales: {
            // fresco (local, diario): scrapeó hoy → sin alerta
            indeed: { total: 19000, ultimo_scraping: iso(2 * H), ultimos_7d: 300, hoy: 275,
                      origen: 'local', cadencia: 'diaria', umbral_horas: 30 },
            // atrasado (VPS, bisemanal): 10 días sin datos (>2×96h) → error
            bumeran: { total: 6000, ultimo_scraping: iso(240 * H), ultimos_7d: 0, hoy: 0,
                       origen: 'vps', cadencia: 'bisemanal', umbral_horas: 96 },
          },
          ultimo_scraping: iso(2 * H),
        }),
      ),
    )
    render(<ScrapingPage />)
    await waitFor(() => {
      // la alerta de atraso nombra a bumeran con su mensaje de umbral
      expect(screen.getByText(/sin datos hace \d+h \(umbral 96h\)/)).toBeInTheDocument()
    }, { timeout: 3000 })
    // no debe haber una alerta de atraso para indeed
    expect(screen.queryByText(/umbral 30h/)).not.toBeInTheDocument()
  })
})
