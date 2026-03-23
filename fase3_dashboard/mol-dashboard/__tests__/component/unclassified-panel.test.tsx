import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import UnclassifiedPanel, { type UnclassifiedItem } from '@/components/UnclassifiedPanel'

const mockItems: UnclassifiedItem[] = [
  { id: 'u1', label: 'Manejo de CRM', frecuencia: 120, ejemplos: ['usa CRM Salesforce', 'gestión CRM'] },
  { id: 'u2', label: 'Facturación AFIP', frecuencia: 45, ejemplos: ['factura electrónica AFIP'] },
  { id: 'u3', label: 'Punto de venta', frecuencia: 15, ejemplos: ['sistema POS'] },
]

// ─── S21: UnclassifiedPanel ───────────────────────────────────────────────────

describe('S21 — UnclassifiedPanel', () => {
  it('renderiza tabs skills y ocupaciones', () => {
    render(<UnclassifiedPanel items={mockItems} tipo="skills" />)
    expect(screen.getByText('Skills')).toBeInTheDocument()
    expect(screen.getByText('Ocupaciones')).toBeInTheDocument()
  })

  it('muestra los items', () => {
    render(<UnclassifiedPanel items={mockItems} tipo="skills" />)
    expect(screen.getByText('Manejo de CRM')).toBeInTheDocument()
    expect(screen.getByText('Facturación AFIP')).toBeInTheDocument()
  })

  it('muestra frecuencia por item', () => {
    render(<UnclassifiedPanel items={mockItems} tipo="skills" />)
    expect(screen.getByText('120 ofertas')).toBeInTheDocument()
  })

  it('filtro de frecuencia oculta items por debajo del mínimo', () => {
    render(<UnclassifiedPanel items={mockItems} tipo="skills" minFreq={50} />)
    expect(screen.getByText('Manejo de CRM')).toBeInTheDocument()
    expect(screen.queryByText('Facturación AFIP')).not.toBeInTheDocument()
  })

  it('cambiar filtro de frecuencia actualiza la lista', () => {
    render(<UnclassifiedPanel items={mockItems} tipo="skills" />)
    fireEvent.change(screen.getByLabelText('Filtrar por frecuencia mínima'), {
      target: { value: '100' },
    })
    expect(screen.getByText('Manejo de CRM')).toBeInTheDocument()
    expect(screen.queryByText('Facturación AFIP')).not.toBeInTheDocument()
  })

  it('botón Catalogar llama onCatalogar', () => {
    const onCatalogar = vi.fn()
    render(<UnclassifiedPanel items={mockItems} tipo="skills" onCatalogar={onCatalogar} />)
    fireEvent.click(screen.getAllByLabelText(/Catalogar/)[0])
    expect(onCatalogar).toHaveBeenCalledWith(mockItems[0])
  })

  it('botón Sinónimo llama onSinonimo', () => {
    const onSinonimo = vi.fn()
    render(<UnclassifiedPanel items={mockItems} tipo="skills" onSinonimo={onSinonimo} />)
    fireEvent.click(screen.getAllByLabelText(/Marcar.*sinónimo/)[0])
    expect(onSinonimo).toHaveBeenCalledWith(mockItems[0])
  })

  it('descartar oculta el item y llama onDescartar', () => {
    const onDescartar = vi.fn()
    render(<UnclassifiedPanel items={mockItems} tipo="skills" onDescartar={onDescartar} />)
    fireEvent.click(screen.getByLabelText('Descartar Manejo de CRM'))
    expect(screen.queryByText('Manejo de CRM')).not.toBeInTheDocument()
    expect(onDescartar).toHaveBeenCalledWith(mockItems[0])
  })

  it('sin items muestra mensaje vacío', () => {
    render(<UnclassifiedPanel items={[]} tipo="skills" />)
    expect(screen.getByText(/No hay skills sin clasificar/)).toBeInTheDocument()
  })

  it('botones tienen min touch target', () => {
    render(<UnclassifiedPanel items={mockItems} tipo="skills" />)
    expect(screen.getAllByLabelText(/Catalogar/)[0].className).toContain('min-h-[44px]')
    expect(screen.getAllByLabelText(/Marcar.*sinónimo/)[0].className).toContain('min-h-[44px]')
  })
})
