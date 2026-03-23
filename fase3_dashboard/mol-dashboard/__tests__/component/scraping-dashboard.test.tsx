import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
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

// ─── S23: Dashboard Scraping ──────────────────────────────────────────────────

describe('S23 — ScrapingPage', () => {
  it('muestra título y cantidad de fuentes', async () => {
    render(<ScrapingPage />)
    await waitFor(() => {
      expect(screen.getByText(/Scraping — Portales/i)).toBeInTheDocument()
    })
    expect(screen.getByText(/6 fuentes/)).toBeInTheDocument()
  })

  it('muestra card por cada portal', async () => {
    render(<ScrapingPage />)
    await waitFor(() => {
      expect(screen.getAllByText(/37\.8%|41\.3%/).length).toBeGreaterThan(0)
    })
    // 6 portales → 6 badges de porcentaje del total
    expect(screen.getByText(/37\.8%/)).toBeInTheDocument()
    expect(screen.getByText(/41\.3%/)).toBeInTheDocument()
    expect(screen.getByText(/13\.3%/)).toBeInTheDocument()
  })

  it('muestra alertas de error y warning', async () => {
    render(<ScrapingPage />)
    await waitFor(() => {
      expect(screen.getByText(/caba sin ofertas hace 20 dias/i)).toBeInTheDocument()
    })
    expect(screen.getByText(/computrabajo sin ofertas hace 8 dias/i)).toBeInTheDocument()
  })

  it('botón Actualizar recarga datos', async () => {
    render(<ScrapingPage />)
    await waitFor(() => {
      expect(screen.getByText(/Scraping — Portales/i)).toBeInTheDocument()
    })
    const btn = screen.getByRole('button', { name: /Actualizar/i })
    fireEvent.click(btn)
    // carga de nuevo: spinner o datos siguen presentes
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

  it('filtros de periodo están presentes', async () => {
    render(<ScrapingPage />)
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /7 dias/i })).toBeInTheDocument()
    })
    expect(screen.getByRole('button', { name: /1 mes/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Todo/i })).toBeInTheDocument()
  })

  it('cards muestran columnas Scrapeadas / Procesadas / 7 dias', async () => {
    render(<ScrapingPage />)
    await waitFor(() => {
      expect(screen.getAllByText('Scrapeadas').length).toBeGreaterThan(0)
    })
    expect(screen.getAllByText('Procesadas').length).toBeGreaterThan(0)
    expect(screen.getAllByText('7 dias').length).toBeGreaterThan(0)
  })
})
