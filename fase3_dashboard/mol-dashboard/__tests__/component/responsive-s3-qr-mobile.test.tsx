import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, beforeAll } from 'vitest'
import CompatibilityReport, { type ReportData } from '@/components/CompatibilityReport'
import SkillsMapEditable, { type ReportSkillItem } from '@/components/SkillsMapEditable'
import AffinityMatrix from '@/components/AffinityMatrix'

const MOBILE_WIDTH = 375

const mockRequired: ReportSkillItem[] = [
  { uri: 'esco:001', label: 'JavaScript', type: 'skill', source: 'esco' },
  { uri: 'esco:002', label: 'Python', type: 'skill', source: 'esco' },
  { uri: 'arg:001', label: 'Trabajo en equipo ágil', type: 'transversal', source: 'argentina_approved' },
]

const mockCovered: ReportSkillItem[] = [
  { uri: 'esco:001', label: 'JavaScript', type: 'skill', source: 'esco' },
  { uri: 'esco:002', label: 'Python', type: 'skill', source: 'esco' },
]

const mockData: ReportData = {
  candidato_nombre: 'María González',
  ocupacion_label: 'Desarrolladora de software',
  ocupacion_isco: '2512',
  match_score: 67, // 2/3 cubiertos = 67%
  perfil_consolidado_version: 'v1.0',
  estado: 'activo',
  created_at: '2026-03-20T00:00:00Z',
  expira_at: '2026-05-20T00:00:00Z',
  skills_candidato: mockCovered,
  skills_requeridas: mockRequired,
  skills_cubiertas: mockCovered,
  skills_gap: [
    { uri: 'arg:001', label: 'Trabajo en equipo ágil', type: 'transversal', source: 'argentina_approved' },
  ],
}

describe('F2 — Responsive QR report mobile (375px)', () => {
  beforeAll(() => {
    Object.defineProperty(window, 'innerWidth', { writable: true, configurable: true, value: MOBILE_WIDTH })
  })

  describe('CompatibilityReport', () => {
    it('renderiza nombre del candidato', () => {
      render(<CompatibilityReport data={mockData} />)
      expect(screen.getByText('María González')).toBeInTheDocument()
    })

    it('muestra score de compatibilidad', () => {
      render(<CompatibilityReport data={mockData} />)
      expect(screen.getByText('67%')).toBeInTheDocument()
    })

    it('botón Restaurar original tiene min touch target', () => {
      render(<CompatibilityReport data={mockData} />)
      // Editar skills para que aparezca el botón Restaurar
      // El botón aparece cuando isEdited = true, lo forzamos via SkillsMapEditable
      // Verificamos que el botón tiene la clase min-h-[44px] cuando aparece
      // Primero necesitamos provocar una edición: hacemos click en Editar y quitamos una skill
      fireEvent.click(screen.getByText('Editar'))
      const quitarBtns = screen.getAllByLabelText(/Quitar/i)
      fireEvent.click(quitarBtns[0])
      const restaurar = screen.getByText('Restaurar original')
      expect(restaurar.className).toContain('min-h-[44px]')
    })

    it('no muestra DNI en ninguna parte del reporte', () => {
      render(<CompatibilityReport data={mockData} />)
      expect(screen.queryByText(/DNI/i)).not.toBeInTheDocument()
      expect(screen.queryByText(/documento/i)).not.toBeInTheDocument()
    })
  })

  describe('SkillsMapEditable — cards mobile', () => {
    it('renderiza todas las skills', () => {
      render(
        <SkillsMapEditable
          required={mockRequired}
          covered={mockCovered}
          onChange={() => {}}
        />
      )
      expect(screen.getAllByText('JavaScript').length).toBeGreaterThan(0)
      expect(screen.getAllByText('Python').length).toBeGreaterThan(0)
      expect(screen.getAllByText('Trabajo en equipo ágil').length).toBeGreaterThan(0)
    })

    it('badges de origen aparecen (ESCO y emergente)', () => {
      render(
        <SkillsMapEditable
          required={mockRequired}
          covered={mockCovered}
          onChange={() => {}}
        />
      )
      expect(screen.getAllByText('ESCO').length).toBeGreaterThan(0)
      expect(screen.getAllByText('emergente').length).toBeGreaterThan(0)
    })

    it('modo edición muestra botón quitar con touch target', () => {
      render(
        <SkillsMapEditable
          required={mockRequired}
          covered={mockCovered}
          onChange={() => {}}
        />
      )
      fireEvent.click(screen.getByText('Editar'))
      // Botones quitar en cards mobile tienen min-h-[44px]
      const quitarBtns = screen.getAllByLabelText(/Quitar/i)
      const mobileQuitarBtns = quitarBtns.filter(btn => btn.className.includes('min-h-[44px]'))
      expect(mobileQuitarBtns.length).toBeGreaterThan(0)
    })

    it('agregar competencia llama onChange', () => {
      const onChange = vi.fn()
      render(
        <SkillsMapEditable
          required={mockRequired}
          covered={mockCovered}
          onChange={onChange}
        />
      )
      fireEvent.click(screen.getByText('Editar'))
      const input = screen.getByLabelText('Agregar competencia')
      fireEvent.change(input, { target: { value: 'Nueva skill' } })
      fireEvent.click(screen.getByText('+ Agregar'))
      expect(onChange).toHaveBeenCalled()
    })

    it('botón Agregar tiene min touch target', () => {
      render(
        <SkillsMapEditable
          required={mockRequired}
          covered={mockCovered}
          onChange={() => {}}
        />
      )
      fireEvent.click(screen.getByText('Editar'))
      const agregarBtn = screen.getByText('+ Agregar')
      expect(agregarBtn.className).toContain('min-h-[44px]')
    })
  })

  describe('AffinityMatrix', () => {
    it('muestra competencias detectadas', () => {
      render(<AffinityMatrix detected={mockCovered} gaps={mockData.skills_gap} />)
      expect(screen.getByText('JavaScript')).toBeInTheDocument()
    })

    it('muestra brechas técnicas', () => {
      render(<AffinityMatrix detected={mockCovered} gaps={mockData.skills_gap} />)
      expect(screen.getByText('Python')).toBeInTheDocument()
    })

    it('muestra contadores correctos', () => {
      render(<AffinityMatrix detected={mockCovered} gaps={mockData.skills_gap} />)
      expect(screen.getByText(/Competencias detectadas \(2\)/)).toBeInTheDocument()
      expect(screen.getByText(/Brechas técnicas \(1\)/)).toBeInTheDocument()
    })
  })
})
