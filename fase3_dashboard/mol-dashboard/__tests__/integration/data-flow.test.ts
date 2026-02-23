/**
 * Integration tests for data flow through the Supabase layer.
 * These verify that functions compose correctly and data transforms
 * produce the expected shapes.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'

describe('Data flow integration', () => {
  let mod: typeof import('../../lib/supabase')

  beforeEach(async () => {
    vi.resetModules()
    mod = await import('../../lib/supabase')
  })

  describe('KPIs → Dashboard consistency', () => {
    it('getKPIsOptimized derives from getInsightsRPC', async () => {
      const insights = await mod.getInsightsRPC()
      const kpis = await mod.getKPIsOptimized()

      if (insights) {
        expect(kpis.totalOfertas).toBe(insights.kpis.total_ofertas)
        expect(kpis.ocupacionesDistintas).toBe(insights.kpis.ocupaciones_distintas)
        expect(kpis.empresasActivas).toBe(insights.kpis.empresas_activas)
        expect(kpis.provincias).toBe(insights.kpis.provincias)
      }
    })

    it('getOfertasPorProvinciaOptimized derives from getInsightsRPC', async () => {
      const insights = await mod.getInsightsRPC()
      const provincias = await mod.getOfertasPorProvinciaOptimized()

      if (insights && provincias.length > 0) {
        // Each provincia should have jurisdiccion = provincia name
        expect(provincias[0].jurisdiccion).toBe(insights.provincias[0].provincia)
        expect(provincias[0].cantidad).toBe(insights.provincias[0].total)
      }
    })
  })

  describe('Ocupaciones ranking', () => {
    it('getTopOcupaciones returns sorted by cantidad desc', async () => {
      const top = await mod.getTopOcupaciones(10)

      for (let i = 1; i < top.length; i++) {
        expect(top[i - 1].cantidad).toBeGreaterThanOrEqual(top[i].cantidad)
      }
    })

    it('getTopOcupaciones respects limit', async () => {
      const top5 = await mod.getTopOcupaciones(5)
      expect(top5.length).toBeLessThanOrEqual(5)
    })

    it('each ocupacion has label and count', async () => {
      const top = await mod.getTopOcupaciones(10)

      top.forEach((o) => {
        expect(o).toHaveProperty('ocupacion')
        expect(o).toHaveProperty('cantidad')
        expect(typeof o.ocupacion).toBe('string')
        expect(typeof o.cantidad).toBe('number')
        expect(o.cantidad).toBeGreaterThan(0)
      })
    })
  })

  describe('Ofertas por modalidad', () => {
    it('returns array of modalidad objects', async () => {
      const result = await mod.getOfertasPorModalidad()

      expect(result).toBeInstanceOf(Array)
      result.forEach((r) => {
        expect(r).toHaveProperty('modalidad')
        expect(r).toHaveProperty('cantidad')
      })
    })

    it('is sorted by cantidad desc', async () => {
      const result = await mod.getOfertasPorModalidad()

      for (let i = 1; i < result.length; i++) {
        expect(result[i - 1].cantidad).toBeGreaterThanOrEqual(result[i].cantidad)
      }
    })
  })

  describe('getTotalOfertas', () => {
    it('returns a number', async () => {
      const total = await mod.getTotalOfertas()
      expect(typeof total).toBe('number')
    })

    it('returns 0 when supabase is unavailable', async () => {
      const origUrl = process.env.NEXT_PUBLIC_SUPABASE_URL
      process.env.NEXT_PUBLIC_SUPABASE_URL = ''
      vi.resetModules()
      const freshMod = await import('../../lib/supabase')

      const total = await freshMod.getTotalOfertas()
      expect(total).toBe(0)

      process.env.NEXT_PUBLIC_SUPABASE_URL = origUrl
    })
  })

  describe('getOfertasPorProvincia', () => {
    it('returns array sorted by cantidad desc', async () => {
      const provincias = await mod.getOfertasPorProvincia()

      expect(provincias).toBeInstanceOf(Array)
      for (let i = 1; i < provincias.length; i++) {
        expect(provincias[i - 1].cantidad).toBeGreaterThanOrEqual(provincias[i].cantidad)
      }
    })

    it('each entry has jurisdiccion, cantidad, porcentaje', async () => {
      const provincias = await mod.getOfertasPorProvincia()

      provincias.forEach((p) => {
        expect(p).toHaveProperty('jurisdiccion')
        expect(p).toHaveProperty('cantidad')
        expect(p).toHaveProperty('porcentaje')
        expect(typeof p.porcentaje).toBe('number')
      })
    })
  })

  describe('getLandingData', () => {
    it('returns all landing page data in one call', async () => {
      const data = await mod.getLandingData()

      expect(data).toHaveProperty('totalOfertas')
      expect(data).toHaveProperty('rangoSemana')
      expect(data).toHaveProperty('topOcupaciones')
      expect(data).toHaveProperty('topSkills')
      expect(data.topOcupaciones).toBeInstanceOf(Array)
      expect(data.topSkills).toBeInstanceOf(Array)
    })

    it('rangoSemana has date-like format', async () => {
      const data = await mod.getLandingData()

      // Format: "d/m y d/m"
      expect(data.rangoSemana).toMatch(/\d+\/\d+/)
    })
  })

  describe('Graceful degradation', () => {
    it('all getter functions handle null client gracefully', async () => {
      const origUrl = process.env.NEXT_PUBLIC_SUPABASE_URL
      process.env.NEXT_PUBLIC_SUPABASE_URL = ''
      vi.resetModules()
      const freshMod = await import('../../lib/supabase')

      // None of these should throw
      expect(await freshMod.getKPIs()).toEqual({
        totalOfertas: 0,
        ocupacionesDistintas: 0,
        empresasActivas: 0,
        provincias: 0,
      })
      expect(await freshMod.getOfertasPorProvincia()).toEqual([])
      expect(await freshMod.getTopOcupaciones()).toEqual([])
      expect(await freshMod.getOfertasPorModalidad()).toEqual([])
      expect(await freshMod.getOfertas()).toEqual({ ofertas: [], total: 0 })
      expect(await freshMod.getTopSkillsTecnicas()).toEqual([])
      expect(await freshMod.getTopSoftSkills()).toEqual([])
      expect(await freshMod.getTotalOfertas()).toBe(0)
      expect(await freshMod.getInsightsRPC()).toBeNull()

      process.env.NEXT_PUBLIC_SUPABASE_URL = origUrl
    })
  })
})
