import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { PipelineRunsHistory } from '@/components/aprendizaje/PipelineRunsHistory'

describe('PipelineRunsHistory', () => {
  it('renderiza el título y la descripción', async () => {
    render(<PipelineRunsHistory />)
    expect(screen.getByText(/Historial de corridas/i)).toBeInTheDocument()
    expect(screen.getByText(/régimen 15-17 mayo/i)).toBeInTheDocument()
  })

  it('carga y muestra runs desde la API', async () => {
    render(<PipelineRunsHistory />)
    await waitFor(() => {
      expect(screen.getByText('run_20260516_2052')).toBeInTheDocument()
    })
    expect(screen.getByText('run_20260515_0001')).toBeInTheDocument()
    expect(screen.getByText('reapply_20260422_185810')).toBeInTheDocument()
  })

  it('muestra el contador de corridas en el footer', async () => {
    render(<PipelineRunsHistory />)
    await waitFor(() => {
      expect(screen.getByText(/3 corridas/i)).toBeInTheDocument()
    })
  })

  it('filtra por matching_version', async () => {
    render(<PipelineRunsHistory />)
    await waitFor(() => {
      expect(screen.getByText('run_20260516_2052')).toBeInTheDocument()
    })

    const versionSelect = screen.getByLabelText(/Matcher version/i) as HTMLSelectElement
    fireEvent.change(versionSelect, { target: { value: '3.5.4' } })

    await waitFor(() => {
      expect(screen.queryByText('run_20260516_2052')).not.toBeInTheDocument()
      expect(screen.getByText('reapply_20260422_185810')).toBeInTheDocument()
    })
  })

  it('limpia los filtros al hacer click en "Limpiar filtros"', async () => {
    render(<PipelineRunsHistory />)
    await waitFor(() => {
      expect(screen.getByText('run_20260516_2052')).toBeInTheDocument()
    })

    const versionSelect = screen.getByLabelText(/Matcher version/i) as HTMLSelectElement
    fireEvent.change(versionSelect, { target: { value: '3.5.4' } })

    await waitFor(() => {
      expect(screen.queryByText('run_20260516_2052')).not.toBeInTheDocument()
    })

    const clearBtn = screen.getByText(/Limpiar filtros/i)
    fireEvent.click(clearBtn)

    await waitFor(() => {
      expect(screen.getByText('run_20260516_2052')).toBeInTheDocument()
    })
  })

  it('muestra precision formateada como porcentaje', async () => {
    render(<PipelineRunsHistory />)
    await waitFor(() => {
      expect(screen.getAllByText('100.0%').length).toBeGreaterThan(0)
    })
  })
})
