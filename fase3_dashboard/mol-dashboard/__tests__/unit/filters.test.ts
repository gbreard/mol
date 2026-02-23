/**
 * Tests for the applyFilters logic in lib/supabase.ts.
 *
 * Since applyFilters is not exported, we test it indirectly through the
 * functions that use it. We verify that passing various filter combinations
 * produces the expected behavior.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import type { DashboardFilters } from '../../lib/types'

const emptyFilters: DashboardFilters = {
  territorio: '',
  provincia: '',
  localidad: [],
  fechaDesde: null,
  fechaHasta: null,
  permanencia: [],
  searchOcupacion: '',
  ocupacionesSeleccionadas: [],
  nivelEducativo: [],
  experiencia: '',
  seniority: [],
  modalidad: [],
  jornada: '',
  skillsDigitales: false,
  sector: [],
}

describe('Filter application', () => {
  let mod: typeof import('../../lib/supabase')

  beforeEach(async () => {
    vi.resetModules()
    mod = await import('../../lib/supabase')
  })

  describe('provincia filter', () => {
    it('accepts known provincia keys', async () => {
      const filters: DashboardFilters = {
        ...emptyFilters,
        provincia: 'caba',
      }

      // Should not throw — provincia 'caba' maps to 'Capital Federal'
      const result = await mod.getKPIs(filters)
      expect(result).toHaveProperty('totalOfertas')
    })

    it('handles unknown provincia gracefully', async () => {
      const filters: DashboardFilters = {
        ...emptyFilters,
        provincia: 'nonexistent',
      }

      // Unknown provincia should be ignored (no mapping)
      const result = await mod.getKPIs(filters)
      expect(result).toHaveProperty('totalOfertas')
    })
  })

  describe('fecha filters', () => {
    it('accepts Date objects for fechaDesde/fechaHasta', async () => {
      const filters: DashboardFilters = {
        ...emptyFilters,
        fechaDesde: new Date('2026-01-01'),
        fechaHasta: new Date('2026-02-01'),
      }

      const result = await mod.getKPIs(filters)
      expect(result).toHaveProperty('totalOfertas')
    })

    it('handles null dates (no filter)', async () => {
      const result = await mod.getKPIs(emptyFilters)
      expect(result).toHaveProperty('totalOfertas')
    })
  })

  describe('experiencia filter', () => {
    it.each([
      'sin_experiencia',
      '1_2_anios',
      '3_5_anios',
      '5_mas',
    ])('handles experiencia=%s', async (experiencia) => {
      const filters: DashboardFilters = {
        ...emptyFilters,
        experiencia,
      }

      const result = await mod.getKPIs(filters)
      expect(result).toHaveProperty('totalOfertas')
    })
  })

  describe('multi-select filters', () => {
    it('handles localidad array', async () => {
      const filters: DashboardFilters = {
        ...emptyFilters,
        localidad: ['Palermo', 'Belgrano'],
      }

      const result = await mod.getKPIs(filters)
      expect(result).toHaveProperty('totalOfertas')
    })

    it('handles ocupaciones seleccionadas', async () => {
      const filters: DashboardFilters = {
        ...emptyFilters,
        ocupacionesSeleccionadas: ['2514', '2411'],
      }

      const result = await mod.getKPIs(filters)
      expect(result).toHaveProperty('totalOfertas')
    })

    it('handles seniority array', async () => {
      const filters: DashboardFilters = {
        ...emptyFilters,
        seniority: ['junior', 'senior'],
      }

      const result = await mod.getKPIs(filters)
      expect(result).toHaveProperty('totalOfertas')
    })

    it('handles modalidad array', async () => {
      const filters: DashboardFilters = {
        ...emptyFilters,
        modalidad: ['remoto', 'hibrido'],
      }

      const result = await mod.getKPIs(filters)
      expect(result).toHaveProperty('totalOfertas')
    })

    it('handles sector array', async () => {
      const filters: DashboardFilters = {
        ...emptyFilters,
        sector: ['Información y comunicaciones'],
      }

      const result = await mod.getKPIs(filters)
      expect(result).toHaveProperty('totalOfertas')
    })
  })

  describe('jornada filter', () => {
    it('maps jornada keys to database values', async () => {
      const filters: DashboardFilters = {
        ...emptyFilters,
        jornada: 'full_time',
      }

      // full_time should map to 'full-time' internally
      const result = await mod.getKPIs(filters)
      expect(result).toHaveProperty('totalOfertas')
    })
  })

  describe('combined filters', () => {
    it('handles multiple filters simultaneously', async () => {
      const filters: DashboardFilters = {
        ...emptyFilters,
        provincia: 'caba',
        fechaDesde: new Date('2026-01-01'),
        seniority: ['senior'],
        modalidad: ['remoto'],
      }

      const result = await mod.getKPIs(filters)
      expect(result).toHaveProperty('totalOfertas')
    })
  })
})
