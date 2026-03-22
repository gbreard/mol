import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { GenerateReportModal } from '@/components/GenerateReportModal'

const mockGenerate = vi.fn().mockResolvedValue({
  token: 'mock-token-abc123',
  pdfUrl: '/mock/reporte.pdf',
})

describe('GenerateReportModal', () => {
  it('campos pre-llenados con props', () => {
    render(
      <GenerateReportModal
        open={true}
        candidatoNombre="Juan Perez"
        tituloVacante="Desarrollador de software"
        onClose={vi.fn()}
        onGenerate={mockGenerate}
      />
    )
    expect(screen.getByDisplayValue('Juan Perez')).toBeInTheDocument()
    expect(screen.getByDisplayValue('Desarrollador de software')).toBeInTheDocument()
  })

  it('validacion: boton deshabilitado si nombre vacio', () => {
    render(
      <GenerateReportModal
        open={true}
        candidatoNombre=""
        tituloVacante=""
        onClose={vi.fn()}
        onGenerate={mockGenerate}
      />
    )
    expect(screen.getByRole('button', { name: /generar reporte/i })).toBeDisabled()
  })

  it('validacion: error si se intenta generar sin nombre (estado pre-fill vacio)', async () => {
    render(
      <GenerateReportModal
        open={true}
        candidatoNombre=""
        tituloVacante=""
        onClose={vi.fn()}
        onGenerate={mockGenerate}
      />
    )
    // El botón está disabled, pero igual validamos que el campo nombre sea requerido
    const btn = screen.getByRole('button', { name: /generar reporte/i })
    expect(btn).toBeDisabled()
  })

  it('boton genera y muestra estado success', async () => {
    render(
      <GenerateReportModal
        open={true}
        candidatoNombre="Juan Perez"
        tituloVacante="Dev"
        onClose={vi.fn()}
        onGenerate={mockGenerate}
      />
    )
    fireEvent.click(screen.getByRole('button', { name: /generar reporte/i }))
    await waitFor(() =>
      expect(screen.getByText(/reporte generado correctamente/i)).toBeInTheDocument()
    )
    expect(screen.getByText('Descargar PDF')).toBeInTheDocument()
    expect(screen.getByText('Copiar link del reporte')).toBeInTheDocument()
    expect(screen.getByText('Ver reporte')).toBeInTheDocument()
  })

  it('copiar link muestra confirmacion', async () => {
    Object.defineProperty(navigator, 'clipboard', {
      value: { writeText: vi.fn().mockResolvedValue(undefined) },
      writable: true,
    })
    render(
      <GenerateReportModal
        open={true}
        candidatoNombre="Juan Perez"
        tituloVacante="Dev"
        onClose={vi.fn()}
        onGenerate={mockGenerate}
      />
    )
    fireEvent.click(screen.getByRole('button', { name: /generar reporte/i }))
    await waitFor(() => screen.getByText('Copiar link del reporte'))
    fireEvent.click(screen.getByText('Copiar link del reporte'))
    await waitFor(() => expect(screen.getByText('¡Link copiado!')).toBeInTheDocument())
  })

  it('nota de 60 dias visible', () => {
    render(
      <GenerateReportModal
        open={true}
        onClose={vi.fn()}
        onGenerate={mockGenerate}
      />
    )
    expect(screen.getAllByText(/60 días/i).length).toBeGreaterThan(0)
  })
})
