import { describe, it, expect } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { PerfilArgentinoAdmin } from '../../components/PerfilArgentinoAdmin'

describe('PerfilArgentinoAdmin', () => {
  it('renderiza el historial de versiones', async () => {
    render(<PerfilArgentinoAdmin />)

    await waitFor(() => {
      expect(screen.getAllByText('v1.0').length).toBeGreaterThanOrEqual(1)
    })

    expect(screen.getByText('admin@oede.gob.ar')).toBeInTheDocument()
    expect(screen.getByText('14.257')).toBeInTheDocument()
  })

  it('muestra badge "Activa" en la versión activa', async () => {
    render(<PerfilArgentinoAdmin />)

    await waitFor(() => {
      expect(screen.getByText('Activa')).toBeInTheDocument()
    })
  })

  it('botón "Crear nueva versión" abre el modal', async () => {
    render(<PerfilArgentinoAdmin />)

    await waitFor(() => {
      expect(screen.getByText('Crear nueva versión')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByText('Crear nueva versión'))

    expect(screen.getByText(/Confirmar corte/)).toBeInTheDocument()
    expect(screen.getByPlaceholderText(/Incorpora Docker/)).toBeInTheDocument()
  })

  it('cancelar cierra el modal', async () => {
    render(<PerfilArgentinoAdmin />)

    await waitFor(() => {
      fireEvent.click(screen.getByText('Crear nueva versión'))
    })

    fireEvent.click(screen.getByText('Cancelar'))

    await waitFor(() => {
      expect(screen.queryByPlaceholderText(/Incorpora Docker/)).not.toBeInTheDocument()
    })
  })

  it('muestra advertencia de emergentes pendientes en el modal', async () => {
    render(<PerfilArgentinoAdmin />)

    await waitFor(() => {
      fireEvent.click(screen.getByText('Crear nueva versión'))
    })

    expect(screen.getByText(/3 emergente/)).toBeInTheDocument()
  })

  it('no muestra botón rollback en la versión activa', async () => {
    render(<PerfilArgentinoAdmin />)

    await waitFor(() => {
      expect(screen.getAllByText('v1.0').length).toBeGreaterThanOrEqual(1)
    })

    // v1.0 es la única versión y está activa, no debe tener botón rollback
    expect(screen.queryByText('Rollback')).not.toBeInTheDocument()
  })
})
