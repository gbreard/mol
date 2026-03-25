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

  it('muestra cards con datos del VPS', async () => {
    render(<ScrapingPage />)
    await waitFor(() => {
      expect(screen.getAllByText(/Total VPS/).length).toBeGreaterThanOrEqual(1)
    }, { timeout: 3000 })
    expect(screen.getAllByText(/En Dashboard/).length).toBeGreaterThan(0)
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

  it('cards muestran Total VPS / 7 dias / Hoy / En Dashboard', async () => {
    render(<ScrapingPage />)
    await waitFor(() => {
      expect(screen.getAllByText(/Total VPS/).length).toBeGreaterThan(0)
    })
    expect(screen.getAllByText(/En Dashboard/).length).toBeGreaterThan(0)
    expect(screen.getAllByText(/7 dias/).length).toBeGreaterThan(0)
  })

  it('muestra total VPS en header', async () => {
    render(<ScrapingPage />)
    await waitFor(() => {
      expect(screen.getByText(/ofertas en VPS/)).toBeInTheDocument()
    })
  })
})
