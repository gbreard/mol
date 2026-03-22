import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import OffersTab from '@/components/OffersTab'

describe('OffersTab', () => {
  it('renderiza cards con datos de ofertas', async () => {
    render(<OffersTab profileId="profile-1" />)
    await waitFor(() => expect(screen.getByText('Desarrollador React')).toBeInTheDocument())
    expect(screen.getByText(/TechCorp/)).toBeInTheDocument()
    expect(screen.getByText('85%')).toBeInTheDocument()
  })

  it('muestra skills cubiertas y gap', async () => {
    render(<OffersTab profileId="profile-1" />)
    await waitFor(() => screen.getByText('Desarrollador React'))
    expect(screen.getByText('JavaScript')).toBeInTheDocument()
    expect(screen.getByText('Docker')).toBeInTheDocument()
  })

  it('boton ver oferta tiene href correcto', async () => {
    render(<OffersTab profileId="profile-1" />)
    await waitFor(() => screen.getByText('Desarrollador React'))
    const link = screen.getByRole('link', { name: /ver oferta: desarrollador react/i })
    expect(link).toHaveAttribute('href', 'https://example.com/1')
  })

  it('filtro por provincia filtra resultados', async () => {
    render(<OffersTab profileId="profile-1" />)
    await waitFor(() => screen.getByText('Desarrollador React'))
    fireEvent.change(screen.getByLabelText('Filtrar por provincia'), {
      target: { value: 'CABA' },
    })
    await waitFor(() => {
      expect(screen.getByText('Desarrollador React')).toBeInTheDocument()
      expect(screen.queryByText('Analista de Datos')).not.toBeInTheDocument()
    })
  })

  it('filtro por modalidad filtra resultados', async () => {
    render(<OffersTab profileId="profile-1" />)
    await waitFor(() => screen.getByText('Analista de Datos'))
    fireEvent.change(screen.getByLabelText('Filtrar por modalidad'), {
      target: { value: 'presencial' },
    })
    await waitFor(() => {
      expect(screen.getByText('Analista de Datos')).toBeInTheDocument()
      expect(screen.queryByText('Desarrollador React')).not.toBeInTheDocument()
    })
  })

  it('empty state cuando no hay resultados', async () => {
    render(<OffersTab profileId="profile-1" />)
    await waitFor(() => screen.getByText('Desarrollador React'))
    // Filtrar por algo sin resultados
    fireEvent.change(screen.getByLabelText('Filtrar por provincia'), {
      target: { value: 'Mendoza' },
    })
    await waitFor(() =>
      expect(screen.getByText('No hay ofertas que coincidan')).toBeInTheDocument()
    )
  })

  it('boton reporte llama onGenerateReport', async () => {
    const onGenerateReport = vi.fn()
    render(<OffersTab profileId="profile-1" onGenerateReport={onGenerateReport} />)
    await waitFor(() => screen.getAllByText('Reporte')[0])
    fireEvent.click(screen.getAllByText('Reporte')[0])
    expect(onGenerateReport).toHaveBeenCalledWith(
      expect.objectContaining({ id_oferta: 1 })
    )
  })
})
