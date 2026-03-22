import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { describe, it, expect, beforeAll, vi } from 'vitest'
import FreeTextSkillExtractor from '@/components/FreeTextSkillExtractor'
import SkillSearchByTask from '@/components/SkillSearchByTask'
import SkillWithDefinition, { type SkillItem } from '@/components/SkillWithDefinition'

const TABLET_WIDTH = 768

const mockSkill: SkillItem = {
  uri: 'esco:001',
  label: 'Soldadura autógena',
  type: 'skill',
  description: 'Técnica de unión de metales mediante calor.',
  source: 'esco',
  confidence: 'confirmed',
  via: 'texto_libre',
}

describe('F3 — Responsive S2 tablet (768px)', () => {
  beforeAll(() => {
    Object.defineProperty(window, 'innerWidth', { writable: true, configurable: true, value: TABLET_WIDTH })
  })

  describe('SkillWithDefinition', () => {
    it('renderiza label y badges de tipo/origen', () => {
      render(
        <SkillWithDefinition
          skill={mockSkill}
          onConfidenceChange={vi.fn()}
          onRemove={vi.fn()}
        />
      )
      expect(screen.getByText('Soldadura autógena')).toBeInTheDocument()
      expect(screen.getByText('ESCO')).toBeInTheDocument()
      expect(screen.getByText('competencia')).toBeInTheDocument()
    })

    it('botones de confianza responden al click', () => {
      const onChange = vi.fn()
      render(
        <SkillWithDefinition
          skill={mockSkill}
          onConfidenceChange={onChange}
          onRemove={vi.fn()}
        />
      )
      fireEvent.click(screen.getByLabelText('Descartar'))
      expect(onChange).toHaveBeenCalledWith('esco:001', 'discarded')
    })

    it('botón quitar llama onRemove', () => {
      const onRemove = vi.fn()
      render(
        <SkillWithDefinition
          skill={mockSkill}
          onConfidenceChange={vi.fn()}
          onRemove={onRemove}
        />
      )
      fireEvent.click(screen.getByLabelText('Quitar skill'))
      expect(onRemove).toHaveBeenCalledWith('esco:001')
    })

    it('badge emergente visible para argentina_approved', () => {
      const emergente: SkillItem = { ...mockSkill, source: 'argentina_approved' }
      render(
        <SkillWithDefinition
          skill={emergente}
          onConfidenceChange={vi.fn()}
          onRemove={vi.fn()}
        />
      )
      expect(screen.getByText('emergente')).toBeInTheDocument()
    })
  })

  describe('FreeTextSkillExtractor — botón agregar visible sin hover', () => {
    it('muestra textarea y botón identificar', () => {
      render(<FreeTextSkillExtractor />)
      expect(screen.getByLabelText('Contá con tus palabras qué sabés hacer')).toBeInTheDocument()
      expect(screen.getByText('Identificar competencias')).toBeInTheDocument()
    })

    it('botón identificar deshabilitado con textarea vacío', () => {
      render(<FreeTextSkillExtractor />)
      const btn = screen.getByText('Identificar competencias')
      expect(btn).toBeDisabled()
    })

    it('botón identificar habilitado con texto', () => {
      render(<FreeTextSkillExtractor />)
      fireEvent.change(screen.getByLabelText('Contá con tus palabras qué sabés hacer'), {
        target: { value: 'Sé soldar y manejar tornos CNC' },
      })
      expect(screen.getByText('Identificar competencias')).not.toBeDisabled()
    })

    it('botón agregar individual tiene min touch target (no hover-only)', async () => {
      const mockFetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({
          skills: [
            { uri: 'esco:001', label: 'Soldadura', type: 'skill', description: 'Técnica metales', source: 'esco' },
          ],
        }),
      })
      vi.stubGlobal('fetch', mockFetch)

      render(<FreeTextSkillExtractor />)
      fireEvent.change(screen.getByLabelText('Contá con tus palabras qué sabés hacer'), {
        target: { value: 'Sé soldar' },
      })
      fireEvent.click(screen.getByText('Identificar competencias'))

      await waitFor(() => {
        const agregarBtn = screen.queryByLabelText('Agregar Soldadura al perfil')
        expect(agregarBtn).toBeInTheDocument()
        // No debe depender de hover — debe estar en el DOM siempre
        expect(agregarBtn?.className).toContain('min-h-[44px]')
      })

      vi.unstubAllGlobals()
    })
  })

  describe('SkillSearchByTask — tablet', () => {
    it('renderiza input de búsqueda', () => {
      render(<SkillSearchByTask />)
      expect(screen.getByLabelText('Buscar skills')).toBeInTheDocument()
    })

    it('muestra resultados al escribir', async () => {
      const mockFetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({
          results: [
            { uri: 'esco:002', label: 'Programación Python', type: 'skill', description: 'Lenguaje Python', source: 'esco' },
          ],
        }),
      })
      vi.stubGlobal('fetch', mockFetch)

      render(<SkillSearchByTask />)
      const input = screen.getByLabelText('Buscar skills')
      fireEvent.focus(input)
      fireEvent.change(input, { target: { value: 'Python' } })

      await waitFor(() => {
        expect(screen.getByText('Programación Python')).toBeInTheDocument()
      }, { timeout: 500 })

      vi.unstubAllGlobals()
    })
  })
})
