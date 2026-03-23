import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import ComandosPage from '@/app/admin/scraping/comandos/page'

// ─── S24: Control de Comandos ─────────────────────────────────────────────────

describe('S24 — ComandosPage', () => {
  it('muestra título de la página', async () => {
    render(<ComandosPage />)
    await waitFor(() => {
      expect(screen.getByText(/Scraping — Comandos/i)).toBeInTheDocument()
    })
  })

  it('muestra historial de comandos con estados', async () => {
    render(<ComandosPage />)
    await waitFor(() => {
      expect(screen.getByText('Completado')).toBeInTheDocument()
    })
    expect(screen.getByText('Error')).toBeInTheDocument()
  })

  it('muestra el conteo de comandos en historial', async () => {
    render(<ComandosPage />)
    await waitFor(() => {
      expect(screen.getByText(/Historial \(2\)/i)).toBeInTheDocument()
    })
  })

  it('muestra mensaje de error del comando fallido', async () => {
    render(<ComandosPage />)
    await waitFor(() => {
      expect(screen.getByText(/Connection refused/i)).toBeInTheDocument()
    })
  })

  it('muestra botones de portales para lanzar scraping', async () => {
    render(<ComandosPage />)
    await waitFor(() => {
      expect(screen.getByText('Lanzar todos')).toBeInTheDocument()
    })
    expect(screen.getAllByText(/Sync VPS/i).length).toBeGreaterThan(0)
  })

  it('muestra log expandible al hacer click en "Ver log"', async () => {
    render(<ComandosPage />)
    await waitFor(() => {
      expect(screen.getByText('Ver log')).toBeInTheDocument()
    })
    fireEvent.click(screen.getByText('Ver log'))
    expect(screen.getByText(/Scraping finalizado/i)).toBeInTheDocument()
    expect(screen.getByText('Ocultar log')).toBeInTheDocument()
  })

  it('muestra calendario de scraping con portales', async () => {
    render(<ComandosPage />)
    await waitFor(() => {
      expect(screen.getByText(/Calendario de scraping/i)).toBeInTheDocument()
    })
    expect(screen.getByText('Activo')).toBeInTheDocument()
    expect(screen.getByText('Pausado')).toBeInTheDocument()
  })

  it('click en Editar activa modo edición del schedule', async () => {
    render(<ComandosPage />)
    await waitFor(() => {
      expect(screen.getAllByText('Editar').length).toBeGreaterThan(0)
    })
    fireEvent.click(screen.getAllByText('Editar')[0])
    expect(screen.getByText('Guardar')).toBeInTheDocument()
    expect(screen.getByText('Cancelar')).toBeInTheDocument()
  })
})
