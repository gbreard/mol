import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import DictionaryEditor, { type DictEntry } from '@/components/DictionaryEditor'

const mockEntries: DictEntry[] = [
  { id: 'e1', key: 'programador', value: '2512', activa: true },
  { id: 'e2', key: 'contador público', value: '2411', activa: true },
  { id: 'e3', key: 'operario', value: '8181', activa: false },
]

// ─── S30: DictionaryEditor ────────────────────────────────────────────────────

describe('S30 — DictionaryEditor', () => {
  it('muestra las entradas del diccionario', () => {
    render(<DictionaryEditor tipo="sinonimos" entries={mockEntries} />)
    expect(screen.getByText('programador')).toBeInTheDocument()
    expect(screen.getByText('contador público')).toBeInTheDocument()
  })

  it('filas inactivas tienen opacidad reducida', () => {
    const { container } = render(<DictionaryEditor tipo="sinonimos" entries={mockEntries} />)
    const rows = container.querySelectorAll('tr.opacity-50')
    expect(rows.length).toBe(1)
  })

  it('filtro de búsqueda filtra entradas', () => {
    render(<DictionaryEditor tipo="sinonimos" entries={mockEntries} />)
    fireEvent.change(screen.getByLabelText('Buscar en sinonimos'), {
      target: { value: 'contador' },
    })
    expect(screen.getByText('contador público')).toBeInTheDocument()
    expect(screen.queryByText('programador')).not.toBeInTheDocument()
  })

  it('botón agregar muestra formulario', () => {
    render(<DictionaryEditor tipo="sinonimos" entries={mockEntries} />)
    fireEvent.click(screen.getByLabelText('Agregar entrada'))
    expect(screen.getByText('Nueva entrada')).toBeInTheDocument()
  })

  it('confirmar nueva entrada llama onAdd', async () => {
    const onAdd = vi.fn().mockResolvedValue(undefined)
    render(<DictionaryEditor tipo="sinonimos" entries={mockEntries} onAdd={onAdd} />)

    fireEvent.click(screen.getByLabelText('Agregar entrada'))
    fireEvent.change(screen.getByLabelText('Nuevo Término'), { target: { value: 'soldador' } })
    fireEvent.change(screen.getByLabelText('Nuevo Sinónimo ESCO'), { target: { value: '7212' } })
    fireEvent.click(screen.getByLabelText('Confirmar nueva entrada'))

    await waitFor(() => {
      expect(onAdd).toHaveBeenCalledWith(expect.objectContaining({ key: 'soldador', value: '7212' }))
    })
  })

  it('editar una entrada muestra inputs inline', () => {
    render(<DictionaryEditor tipo="sinonimos" entries={mockEntries} />)
    fireEvent.click(screen.getByLabelText('Editar programador'))
    expect(screen.getByLabelText('Editar Término de programador')).toBeInTheDocument()
  })

  it('guardar edición llama onEdit con id y cambios', async () => {
    const onEdit = vi.fn().mockResolvedValue(undefined)
    render(<DictionaryEditor tipo="sinonimos" entries={mockEntries} onEdit={onEdit} />)

    fireEvent.click(screen.getByLabelText('Editar programador'))
    const input = screen.getByLabelText('Editar Término de programador')
    fireEvent.change(input, { target: { value: 'desarrollador' } })
    fireEvent.click(screen.getByLabelText('Guardar cambios de programador'))

    await waitFor(() => {
      expect(onEdit).toHaveBeenCalledWith('e1', expect.objectContaining({ key: 'desarrollador' }))
    })
  })

  it('eliminar llama onDelete', () => {
    const onDelete = vi.fn()
    render(<DictionaryEditor tipo="sinonimos" entries={mockEntries} onDelete={onDelete} />)
    fireEvent.click(screen.getByLabelText('Eliminar programador'))
    expect(onDelete).toHaveBeenCalledWith('e1')
  })

  it('sin entradas muestra mensaje vacío', () => {
    render(<DictionaryEditor tipo="sinonimos" entries={[]} />)
    expect(screen.getByText(/No hay entradas/)).toBeInTheDocument()
  })

  it('funciona para tipo nlp_inference con columnas correctas', () => {
    render(<DictionaryEditor tipo="nlp_inference" entries={mockEntries} />)
    expect(screen.getByText('Keyword')).toBeInTheDocument()
    expect(screen.getByText('Valor inferido')).toBeInTheDocument()
  })

  it('botones tienen min touch target', () => {
    render(<DictionaryEditor tipo="sinonimos" entries={mockEntries} />)
    expect(screen.getByLabelText('Agregar entrada').className).toContain('min-h-[44px]')
    expect(screen.getByLabelText('Editar programador').className).toContain('min-h-[44px]')
  })
})
