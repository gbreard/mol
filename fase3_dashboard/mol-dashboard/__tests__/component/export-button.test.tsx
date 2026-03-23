import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ExportButton, QuickExportButton } from '../../components/ExportButton'

const mockData = [
  { name: 'React', value: 450 },
  { name: 'Node.js', value: 380 },
]

const mockColumns = [
  { key: 'name', header: 'Skill' },
  { key: 'value', header: 'Cantidad' },
]

describe('ExportButton', () => {
  it('renders export button with label', () => {
    render(
      <ExportButton data={mockData} columns={mockColumns} filename="test" />
    )

    expect(screen.getByText('Exportar')).toBeInTheDocument()
  })

  it('renders without label when showLabel is false', () => {
    render(
      <ExportButton data={mockData} columns={mockColumns} filename="test" showLabel={false} />
    )

    expect(screen.queryByText('Exportar')).not.toBeInTheDocument()
  })

  it('shows dropdown menu on click', async () => {
    const user = userEvent.setup()

    render(
      <ExportButton data={mockData} columns={mockColumns} filename="test" />
    )

    await user.click(screen.getByText('Exportar'))

    expect(screen.getByText('Descargar CSV')).toBeInTheDocument()
    expect(screen.getByText('Descargar Excel')).toBeInTheDocument()
  })

  it('alerts when data is empty', async () => {
    const user = userEvent.setup()
    window.alert = vi.fn()
    const alertSpy = window.alert as ReturnType<typeof vi.fn>

    render(
      <ExportButton data={[]} columns={mockColumns} filename="test" />
    )

    await user.click(screen.getByText('Exportar'))
    await user.click(screen.getByText('Descargar CSV'))

    expect(alertSpy).toHaveBeenCalledWith('No hay datos para exportar')
    alertSpy.mockRestore()
  })
})

describe('QuickExportButton', () => {
  it('renders with custom label', () => {
    render(
      <QuickExportButton data={mockData} columns={mockColumns} filename="test" label="Exportar CSV" />
    )

    expect(screen.getByText('Exportar CSV')).toBeInTheDocument()
  })

  it('renders with default label', () => {
    render(
      <QuickExportButton data={mockData} columns={mockColumns} filename="test" />
    )

    expect(screen.getByText('CSV')).toBeInTheDocument()
  })

  it('alerts when data is empty', async () => {
    const user = userEvent.setup()
    window.alert = vi.fn()
    const alertSpy = window.alert as ReturnType<typeof vi.fn>

    render(
      <QuickExportButton data={[]} columns={mockColumns} filename="test" />
    )

    await user.click(screen.getByText('CSV'))

    expect(alertSpy).toHaveBeenCalledWith('No hay datos para exportar')
    alertSpy.mockRestore()
  })
})
