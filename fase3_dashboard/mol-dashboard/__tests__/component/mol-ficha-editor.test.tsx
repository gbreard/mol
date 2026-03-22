import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import MolFichaEditor from '@/components/MolFichaEditor'

// ─── S22: MolFichaEditor ──────────────────────────────────────────────────────

describe('S22 — MolFichaEditor', () => {
  it('renderiza como dialog con aria-label', () => {
    render(<MolFichaEditor />)
    expect(screen.getByRole('dialog', { name: 'Editor de ficha MOL' })).toBeInTheDocument()
  })

  it('tiene campos nombre, definición, ESCO y relaciones', () => {
    render(<MolFichaEditor />)
    expect(screen.getByLabelText('Nombre')).toBeInTheDocument()
    expect(screen.getByLabelText('Definición')).toBeInTheDocument()
    expect(screen.getByLabelText('ESCO relacionado (opcional)')).toBeInTheDocument()
    expect(screen.getByLabelText('Agregar relación')).toBeInTheDocument()
  })

  it('radio de tipo tiene las 3 opciones', () => {
    render(<MolFichaEditor />)
    expect(screen.getByLabelText('Tipo: skill')).toBeInTheDocument()
    expect(screen.getByLabelText('Tipo: knowledge')).toBeInTheDocument()
    expect(screen.getByLabelText('Tipo: ocupacion')).toBeInTheDocument()
  })

  it('select de categoría tiene las 5 opciones', () => {
    render(<MolFichaEditor />)
    const sel = screen.getByLabelText('Categoría') as HTMLSelectElement
    expect(sel.options.length).toBe(5)
  })

  it('guardar deshabilitado si nombre o definición vacíos', () => {
    render(<MolFichaEditor />)
    expect(screen.getByLabelText('Guardar ficha MOL')).toBeDisabled()
  })

  it('guardar habilitado con nombre y definición', () => {
    render(<MolFichaEditor initial={{ label: 'Python', definicion: 'Lenguaje de programación' }} />)
    expect(screen.getByLabelText('Guardar ficha MOL')).not.toBeDisabled()
  })

  it('guardar llama onSave con todos los campos', async () => {
    const onSave = vi.fn().mockResolvedValue(undefined)
    render(<MolFichaEditor initial={{ label: 'Python', definicion: 'Lenguaje de programación' }} onSave={onSave} />)
    fireEvent.click(screen.getByLabelText('Guardar ficha MOL'))
    await waitFor(() => {
      expect(onSave).toHaveBeenCalledWith(expect.objectContaining({
        label: 'Python',
        definicion: 'Lenguaje de programación',
        tipo: 'skill',
      }))
    })
  })

  it('agregar relación con botón +', () => {
    render(<MolFichaEditor />)
    fireEvent.change(screen.getByLabelText('Agregar relación'), { target: { value: 'Django' } })
    fireEvent.click(screen.getByLabelText('Confirmar relación'))
    expect(screen.getByText('Django')).toBeInTheDocument()
  })

  it('agregar relación con Enter', () => {
    render(<MolFichaEditor />)
    const input = screen.getByLabelText('Agregar relación')
    fireEvent.change(input, { target: { value: 'FastAPI' } })
    fireEvent.keyDown(input, { key: 'Enter' })
    expect(screen.getByText('FastAPI')).toBeInTheDocument()
  })

  it('quitar relación la elimina', () => {
    render(<MolFichaEditor initial={{ relaciones: ['Django', 'FastAPI'] }} />)
    fireEvent.click(screen.getByLabelText('Quitar relación Django'))
    expect(screen.queryByText('Django')).not.toBeInTheDocument()
    expect(screen.getByText('FastAPI')).toBeInTheDocument()
  })

  it('cerrar llama onClose', () => {
    const onClose = vi.fn()
    render(<MolFichaEditor onClose={onClose} />)
    fireEvent.click(screen.getByLabelText('Cerrar editor'))
    expect(onClose).toHaveBeenCalled()
  })

  it('botones tienen min touch target', () => {
    render(<MolFichaEditor initial={{ label: 'Python', definicion: 'Lenguaje' }} />)
    expect(screen.getByLabelText('Guardar ficha MOL').className).toContain('min-h-[44px]')
    expect(screen.getByLabelText('Cancelar edición').className).toContain('min-h-[44px]')
  })
})
