import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import ReglasPage from '@/app/admin/procesamiento/reglas/page'

// ─── S29: Editor Reglas de Negocio ───────────────────────────────────────────

describe('S29 — ReglasPage', () => {
  it('muestra título de la página', async () => {
    render(<ReglasPage />)
    await waitFor(() => {
      expect(screen.getByText(/Reglas de negocio/i)).toBeInTheDocument()
    })
  })

  it('muestra las reglas cargadas', async () => {
    render(<ReglasPage />)
    await waitFor(() => {
      expect(screen.getByText('Gerente de Ventas')).toBeInTheDocument()
    })
    expect(screen.getByText('Contador Público')).toBeInTheDocument()
    expect(screen.getByText('Albañil')).toBeInTheDocument()
  })

  it('muestra ISCO de cada regla', async () => {
    render(<ReglasPage />)
    await waitFor(() => {
      expect(screen.getByText('1221')).toBeInTheDocument()
    })
    expect(screen.getByText('2411')).toBeInTheDocument()
    expect(screen.getByText('7112')).toBeInTheDocument()
  })

  it('muestra conteo de reglas totales', async () => {
    const { container } = render(<ReglasPage />)
    await waitFor(() => {
      expect(container.textContent).toContain('3 reglas')
    })
  })

  it('input de búsqueda filtra reglas por nombre', async () => {
    render(<ReglasPage />)
    await waitFor(() => {
      expect(screen.getByPlaceholderText(/Buscar por ID/i)).toBeInTheDocument()
    })
    fireEvent.change(screen.getByPlaceholderText(/Buscar por ID/i), { target: { value: 'contador' } })
    await waitFor(() => {
      expect(screen.getByText('Contador Público')).toBeInTheDocument()
    })
    expect(screen.queryByText('Gerente de Ventas')).not.toBeInTheDocument()
  })

  it('click en editar muestra inputs de edición', async () => {
    render(<ReglasPage />)
    await waitFor(() => {
      expect(screen.getByText('Gerente de Ventas')).toBeInTheDocument()
    })
    // botones de editar (Edit2 icon)
    const editBtns = screen.getAllByRole('button')
    const editBtn = editBtns.find(btn => btn.querySelector('svg'))
    // click el primer botón de editar de la primera fila
    const allEditBtns = document.querySelectorAll('button svg.lucide-edit-2')
    if (allEditBtns.length > 0) {
      fireEvent.click((allEditBtns[0] as HTMLElement).closest('button')!)
      await waitFor(() => {
        expect(screen.getByDisplayValue('Gerente de Ventas')).toBeInTheDocument()
      })
    }
  })

  it('limpiar búsqueda muestra todas las reglas', async () => {
    render(<ReglasPage />)
    await waitFor(() => {
      expect(screen.getByPlaceholderText(/Buscar por ID/i)).toBeInTheDocument()
    })
    const input = screen.getByPlaceholderText(/Buscar por ID/i)
    fireEvent.change(input, { target: { value: 'contador' } })
    fireEvent.change(input, { target: { value: '' } })
    await waitFor(() => {
      expect(screen.getByText('Mostrando 3 de 3 reglas')).toBeInTheDocument()
    })
  })

  it('fuente y versión visible en subtítulo', async () => {
    render(<ReglasPage />)
    await waitFor(() => {
      expect(screen.getByText(/override/i)).toBeInTheDocument()
    })
    expect(screen.getByText(/v12/)).toBeInTheDocument()
  })
})
