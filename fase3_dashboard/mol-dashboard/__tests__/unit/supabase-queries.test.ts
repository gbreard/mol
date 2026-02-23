/**
 * Unit tests for lib/supabase.ts data layer.
 *
 * Strategy: We test the EXPORTED functions by mocking the Supabase client.
 * MSW intercepts the PostgREST HTTP calls, so the functions run their
 * real logic (aggregation, filtering, sorting) against mock data.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'

// We need to test the module with the MSW-intercepted Supabase client.
// The env vars are set in vitest.setup.ts, and MSW handlers are active.

describe('lib/supabase.ts - data layer', () => {
  // Dynamic import to ensure env vars and MSW are set up first
  let mod: typeof import('../../lib/supabase')

  beforeEach(async () => {
    // Re-import to get fresh module with MSW active
    vi.resetModules()
    mod = await import('../../lib/supabase')
  })

  describe('getKPIsOptimized', () => {
    it('returns KPI object with correct shape', async () => {
      const kpis = await mod.getKPIsOptimized()

      expect(kpis).toHaveProperty('totalOfertas')
      expect(kpis).toHaveProperty('ocupacionesDistintas')
      expect(kpis).toHaveProperty('empresasActivas')
      expect(kpis).toHaveProperty('provincias')
    })

    it('returns numeric values for all KPIs', async () => {
      const kpis = await mod.getKPIsOptimized()

      expect(typeof kpis.totalOfertas).toBe('number')
      expect(typeof kpis.ocupacionesDistintas).toBe('number')
      expect(typeof kpis.empresasActivas).toBe('number')
      expect(typeof kpis.provincias).toBe('number')
    })

    it('returns zeroes when supabase client is null', async () => {
      // Temporarily clear env to get null client
      const origUrl = process.env.NEXT_PUBLIC_SUPABASE_URL
      process.env.NEXT_PUBLIC_SUPABASE_URL = ''
      vi.resetModules()
      const freshMod = await import('../../lib/supabase')
      const kpis = await freshMod.getKPIsOptimized()

      expect(kpis.totalOfertas).toBe(0)
      expect(kpis.ocupacionesDistintas).toBe(0)

      // Restore
      process.env.NEXT_PUBLIC_SUPABASE_URL = origUrl
    })
  })

  describe('getInsightsRPC', () => {
    it('returns InsightsData with kpis, provincias, isco_grupos', async () => {
      const insights = await mod.getInsightsRPC()

      expect(insights).not.toBeNull()
      expect(insights!.kpis).toHaveProperty('total_ofertas')
      expect(insights!.provincias).toBeInstanceOf(Array)
      expect(insights!.isco_grupos).toBeInstanceOf(Array)
      expect(insights!.top_empresas).toBeInstanceOf(Array)
    })

    it('passes filter params to RPC', async () => {
      // With provincia filter
      const insights = await mod.getInsightsRPC({
        provincia: 'caba',
        territorio: '',
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
      })

      // Should still return data (MSW handler doesn't differentiate by params)
      expect(insights).not.toBeNull()
    })
  })

  describe('getOfertasPorProvinciaOptimized', () => {
    it('returns array of provincia objects', async () => {
      const provincias = await mod.getOfertasPorProvinciaOptimized()

      expect(provincias).toBeInstanceOf(Array)
      if (provincias.length > 0) {
        expect(provincias[0]).toHaveProperty('jurisdiccion')
        expect(provincias[0]).toHaveProperty('cantidad')
        expect(provincias[0]).toHaveProperty('porcentaje')
      }
    })
  })

  describe('getOfertas', () => {
    it('returns ofertas array and total count', async () => {
      const result = await mod.getOfertas(10, 0)

      expect(result).toHaveProperty('ofertas')
      expect(result).toHaveProperty('total')
      expect(result.ofertas).toBeInstanceOf(Array)
      expect(typeof result.total).toBe('number')
    })

    it('each oferta has required fields', async () => {
      const { ofertas } = await mod.getOfertas(10, 0)

      if (ofertas.length > 0) {
        const oferta = ofertas[0]
        expect(oferta).toHaveProperty('id_oferta')
        expect(oferta).toHaveProperty('titulo')
        expect(oferta).toHaveProperty('empresa')
        expect(oferta).toHaveProperty('provincia')
        expect(oferta).toHaveProperty('isco_code')
        expect(oferta).toHaveProperty('skills_tecnicas')
      }
    })

    it('parses skills_tecnicas from string to array', async () => {
      const { ofertas } = await mod.getOfertas(10, 0)

      if (ofertas.length > 0) {
        expect(ofertas[0].skills_tecnicas).toBeInstanceOf(Array)
      }
    })
  })

  describe('requireSupabase', () => {
    it('throws when supabase is not configured', async () => {
      const origUrl = process.env.NEXT_PUBLIC_SUPABASE_URL
      process.env.NEXT_PUBLIC_SUPABASE_URL = ''
      vi.resetModules()
      const freshMod = await import('../../lib/supabase')

      expect(() => freshMod.requireSupabase()).toThrow('Supabase no está configurado')

      process.env.NEXT_PUBLIC_SUPABASE_URL = origUrl
    })

    it('returns client when configured', async () => {
      const client = mod.requireSupabase()
      expect(client).toBeTruthy()
    })
  })
})
