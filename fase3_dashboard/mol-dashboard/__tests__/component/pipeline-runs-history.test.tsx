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

  it('muestra columna Tipo con el source de cada run', async () => {
    render(<PipelineRunsHistory />)
    await waitFor(() => {
      expect(screen.getAllByText('manual').length).toBeGreaterThan(0)
      expect(screen.getByText('reapply_rules')).toBeInTheDocument()
    })
  })

  it('renderiza el filtro source con conteos', async () => {
    render(<PipelineRunsHistory />)
    await waitFor(() => {
      expect(screen.getByLabelText(/Tipo \(source\)/i)).toBeInTheDocument()
    })
    // El option text incluye el count, ej "manual (2)"
    const sel = screen.getByLabelText(/Tipo \(source\)/i) as HTMLSelectElement
    const options = Array.from(sel.options).map((o) => o.textContent)
    expect(options).toContain('manual (2)')
    expect(options).toContain('reapply_rules (1)')
  })

  it('filtra por source', async () => {
    render(<PipelineRunsHistory />)
    await waitFor(() => {
      expect(screen.getByText('reapply_20260422_185810')).toBeInTheDocument()
    })

    const sel = screen.getByLabelText(/Tipo \(source\)/i) as HTMLSelectElement
    fireEvent.change(sel, { target: { value: 'reapply_rules' } })

    await waitFor(() => {
      expect(screen.queryByText('run_20260516_2052')).not.toBeInTheDocument()
      expect(screen.getByText('reapply_20260422_185810')).toBeInTheDocument()
    })
  })
})
