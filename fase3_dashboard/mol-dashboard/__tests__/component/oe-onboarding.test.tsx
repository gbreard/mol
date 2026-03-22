import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import OEOnboarding from '@/components/OEOnboarding'
import ImportPreview, { type ImportRow, type ImportSummary } from '@/components/ImportPreview'
import ImportResult, { type ImportStats } from '@/components/ImportResult'

// ─── S12: OEOnboarding ────────────────────────────────────────────────────────

describe('S12 — OEOnboarding', () => {
  it('muestra bienvenida con nombre de usuario', () => {
    render(<OEOnboarding nombreUsuario="María" onUploadPersonas={vi.fn()} />)
    expect(screen.getByText(/Bienvenida\/o, María/)).toBeInTheDocument()
  })

  it('muestra nombre de la OE', () => {
    render(<OEOnboarding nombreOE="OE Avellaneda" onUploadPersonas={vi.fn()} />)
    expect(screen.getByText('OE Avellaneda')).toBeInTheDocument()
  })

  it('muestra las 3 cards: Personas, Vacantes, Cursos', () => {
    render(<OEOnboarding onUploadPersonas={vi.fn()} />)
    expect(screen.getByText('Personas')).toBeInTheDocument()
    expect(screen.getByText('Vacantes')).toBeInTheDocument()
    expect(screen.getByText('Cursos')).toBeInTheDocument()
  })

  it('Personas marcada como "mínimo para arrancar"', () => {
    render(<OEOnboarding onUploadPersonas={vi.fn()} />)
    expect(screen.getByText('mínimo para arrancar')).toBeInTheDocument()
  })

  it('Vacantes y Cursos marcadas como opcional', () => {
    render(<OEOnboarding onUploadPersonas={vi.fn()} />)
    const opcionales = screen.getAllByText('opcional')
    expect(opcionales.length).toBe(2)
  })

  it('hay 3 botones "Descargar template"', () => {
    render(<OEOnboarding onUploadPersonas={vi.fn()} />)
    const btns = screen.getAllByText('Descargar template')
    expect(btns.length).toBe(3)
  })

  it('hay 3 botones "Subir Excel"', () => {
    render(<OEOnboarding onUploadPersonas={vi.fn()} />)
    const btns = screen.getAllByText('Subir Excel')
    expect(btns.length).toBe(3)
  })

  it('botón atender manual llama onAtenderManual', () => {
    const onAtenderManual = vi.fn()
    render(<OEOnboarding onUploadPersonas={vi.fn()} onAtenderManual={onAtenderManual} />)
    fireEvent.click(screen.getByLabelText('Atender primer caso manualmente'))
    expect(onAtenderManual).toHaveBeenCalled()
  })

  it('botón atender manual tiene min touch target', () => {
    render(<OEOnboarding onUploadPersonas={vi.fn()} />)
    const btn = screen.getByLabelText('Atender primer caso manualmente')
    expect(btn.className).toContain('min-h-[44px]')
  })
})

// ─── S13: ImportPreview ───────────────────────────────────────────────────────

const mockRows: ImportRow[] = [
  { nombre: 'Juan Pérez', dni: '30123456', ocupacion: 'Albañil', skills: 'Soldadura' },
  { nombre: 'María López', dni: '31456789', ocupacion: 'Cajera', skills: null },
  { nombre: null, dni: null, ocupacion: 'Costurera', skills: 'Costura' },
]

const mockSummary: ImportSummary = {
  total: 150, con_ocupacion: 120, con_skills: 45, sin_datos: 30, sin_nombre: 3,
}

describe('S13 — ImportPreview', () => {
  it('muestra total de personas encontradas', () => {
    const { container } = render(<ImportPreview rows={mockRows} summary={mockSummary} onConfirm={vi.fn()} onCancel={vi.fn()} />)
    expect(container.textContent).toContain('150')
    expect(container.textContent).toContain('personas')
  })

  it('avisa cuántas se saltan por falta de nombre', () => {
    render(<ImportPreview rows={mockRows} summary={mockSummary} onConfirm={vi.fn()} onCancel={vi.fn()} />)
    expect(screen.getByText(/3 sin nombre/)).toBeInTheDocument()
  })

  it('muestra filas de la tabla con nombres', () => {
    render(<ImportPreview rows={mockRows} summary={mockSummary} onConfirm={vi.fn()} onCancel={vi.fn()} />)
    expect(screen.getByText('Juan Pérez')).toBeInTheDocument()
    expect(screen.getByText('María López')).toBeInTheDocument()
  })

  it('muestra resumen de estadísticas', () => {
    render(<ImportPreview rows={mockRows} summary={mockSummary} onConfirm={vi.fn()} onCancel={vi.fn()} />)
    expect(screen.getByText(/Con ocupación declarada/)).toBeInTheDocument()
    expect(screen.getByText(/Con skills explícitas/)).toBeInTheDocument()
  })

  it('botón confirmar incluye cantidad válida (147)', () => {
    render(<ImportPreview rows={mockRows} summary={mockSummary} onConfirm={vi.fn()} onCancel={vi.fn()} />)
    expect(screen.getByLabelText('Confirmar importación de 147')).toBeInTheDocument()
  })

  it('confirmar llama onConfirm', () => {
    const onConfirm = vi.fn()
    render(<ImportPreview rows={mockRows} summary={mockSummary} onConfirm={onConfirm} onCancel={vi.fn()} />)
    fireEvent.click(screen.getByLabelText('Confirmar importación de 147'))
    expect(onConfirm).toHaveBeenCalled()
  })

  it('cancelar llama onCancel', () => {
    const onCancel = vi.fn()
    render(<ImportPreview rows={mockRows} summary={mockSummary} onConfirm={vi.fn()} onCancel={onCancel} />)
    fireEvent.click(screen.getByLabelText('Cancelar importación'))
    expect(onCancel).toHaveBeenCalled()
  })

  it('botones tienen min touch target', () => {
    render(<ImportPreview rows={mockRows} summary={mockSummary} onConfirm={vi.fn()} onCancel={vi.fn()} />)
    expect(screen.getByLabelText('Cancelar importación').className).toContain('min-h-[44px]')
    expect(screen.getByLabelText('Confirmar importación de 147').className).toContain('min-h-[44px]')
  })
})

// ─── S14: ImportResult ────────────────────────────────────────────────────────

const mockStats: ImportStats = {
  total_importados: 147,
  con_skills_derivadas: 89,
  con_skills_declaradas: 45,
  sin_skills: 13,
}

describe('S14 — ImportResult', () => {
  it('muestra mensaje de éxito', () => {
    render(<ImportResult stats={mockStats} />)
    expect(screen.getByText('¡Importación completada!')).toBeInTheDocument()
  })

  it('muestra estadísticas correctas', () => {
    render(<ImportResult stats={mockStats} />)
    expect(screen.getByText('147')).toBeInTheDocument()
    expect(screen.getByText('89')).toBeInTheDocument()
    expect(screen.getByText('45')).toBeInTheDocument()
    expect(screen.getByText('13')).toBeInTheDocument()
  })

  it('muestra 3 botones de siguientes pasos', () => {
    render(<ImportResult stats={mockStats} />)
    expect(screen.getByLabelText('Ir al panel de casos')).toBeInTheDocument()
    expect(screen.getByLabelText('Importar vacantes')).toBeInTheDocument()
    expect(screen.getByLabelText('Importar cursos')).toBeInTheDocument()
  })

  it('botones tienen min touch target', () => {
    render(<ImportResult stats={mockStats} />)
    expect(screen.getByLabelText('Ir al panel de casos').className).toContain('min-h-[44px]')
    expect(screen.getByLabelText('Importar vacantes').className).toContain('min-h-[44px]')
    expect(screen.getByLabelText('Importar cursos').className).toContain('min-h-[44px]')
  })

  it('panel de casos llama onIrPanel', () => {
    const onIrPanel = vi.fn()
    render(<ImportResult stats={mockStats} onIrPanel={onIrPanel} />)
    fireEvent.click(screen.getByLabelText('Ir al panel de casos'))
    expect(onIrPanel).toHaveBeenCalled()
  })

  it('importar vacantes llama onImportarVacantes', () => {
    const onImportarVacantes = vi.fn()
    render(<ImportResult stats={mockStats} onImportarVacantes={onImportarVacantes} />)
    fireEvent.click(screen.getByLabelText('Importar vacantes'))
    expect(onImportarVacantes).toHaveBeenCalled()
  })
})
