import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ActiveFilters } from '../../components/ActiveFilters'

const emptyFilters = {
  territorio: 'nacional',
  provincia: '',
  localidad: [] as string[],
  fechaDesde: null as Date | null,
  fechaHasta: null as Date | null,
  permanencia: [] as string[],
  searchOcupacion: '',
  ocupacionesSeleccionadas: [] as string[],
  sector: [] as string[],
}

describe('ActiveFilters', () => {
  it('renders nothing when no filters are active', () => {
    const { container } = render(
      <ActiveFilters filters={emptyFilters} onRemoveFilter={() => {}} />
    )

    expect(container.innerHTML).toBe('')
  })

  it('shows provincia filter badge', () => {
    render(
      <ActiveFilters
        filters={{ ...emptyFilters, provincia: 'caba' }}
        onRemoveFilter={() => {}}
      />
    )

    expect(screen.getByText(/Provincia: caba/)).toBeInTheDocument()
  })

  it('shows single localidad', () => {
    render(
      <ActiveFilters
        filters={{ ...emptyFilters, localidad: ['Palermo'] }}
        onRemoveFilter={() => {}}
      />
    )

    expect(screen.getByText(/Localidad: Palermo/)).toBeInTheDocument()
  })

  it('shows multiple localidades count', () => {
    render(
      <ActiveFilters
        filters={{ ...emptyFilters, localidad: ['Palermo', 'Belgrano', 'Recoleta'] }}
        onRemoveFilter={() => {}}
      />
    )

    expect(screen.getByText(/Localidades: 3 seleccionadas/)).toBeInTheDocument()
  })

  it('shows date filter', () => {
    render(
      <ActiveFilters
        filters={{
          ...emptyFilters,
          fechaDesde: new Date('2026-01-01'),
          fechaHasta: new Date('2026-02-01'),
        }}
        onRemoveFilter={() => {}}
      />
    )

    expect(screen.getByText(/Período:/)).toBeInTheDocument()
  })

  it('shows permanencia filter', () => {
    render(
      <ActiveFilters
        filters={{ ...emptyFilters, permanencia: ['alta'] }}
        onRemoveFilter={() => {}}
      />
    )

    expect(screen.getByText(/Permanencia: 1 seleccionada/)).toBeInTheDocument()
  })

  it('shows ocupaciones filter with count', () => {
    render(
      <ActiveFilters
        filters={{ ...emptyFilters, ocupacionesSeleccionadas: ['2514', '2411'] }}
        onRemoveFilter={() => {}}
      />
    )

    expect(screen.getByText(/Ocupaciones: 2 seleccionadas/)).toBeInTheDocument()
  })

  it('shows single sector', () => {
    render(
      <ActiveFilters
        filters={{ ...emptyFilters, sector: ['Tecnología'] }}
        onRemoveFilter={() => {}}
      />
    )

    expect(screen.getByText(/Sector: Tecnología/)).toBeInTheDocument()
  })

  it('shows multiple sectors count', () => {
    render(
      <ActiveFilters
        filters={{ ...emptyFilters, sector: ['Tecnología', 'Comercio'] }}
        onRemoveFilter={() => {}}
      />
    )

    expect(screen.getByText(/Sectores: 2 seleccionados/)).toBeInTheDocument()
  })

  it('calls onRemoveFilter with correct type when X is clicked', async () => {
    const user = userEvent.setup()
    const onRemove = vi.fn()

    render(
      <ActiveFilters
        filters={{ ...emptyFilters, provincia: 'caba' }}
        onRemoveFilter={onRemove}
      />
    )

    const removeButton = screen.getByLabelText(/Remover filtro/)
    await user.click(removeButton)

    expect(onRemove).toHaveBeenCalledWith('territorio')
  })

  it('shows multiple filter badges simultaneously', () => {
    render(
      <ActiveFilters
        filters={{
          ...emptyFilters,
          provincia: 'caba',
          permanencia: ['alta'],
          sector: ['Tecnología'],
        }}
        onRemoveFilter={() => {}}
      />
    )

    expect(screen.getByText('Filtros activos:')).toBeInTheDocument()
    expect(screen.getByText(/Provincia/)).toBeInTheDocument()
    expect(screen.getByText(/Permanencia/)).toBeInTheDocument()
    expect(screen.getByText(/Sector/)).toBeInTheDocument()
  })
})
