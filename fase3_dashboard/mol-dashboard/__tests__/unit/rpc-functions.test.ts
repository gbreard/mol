/**
 * Unit tests for RPC-based data functions in lib/supabase.ts
 *
 * These test the new RPC wrappers: getPanoramaData, getEvolucionPeriodos,
 * getDistribucionRequerimientos, getSkillsResumen, getSidebarCounts.
 * MSW intercepts the Supabase RPC HTTP calls.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'

describe('lib/supabase.ts - RPC functions', () => {
  let mod: typeof import('../../lib/supabase')

  beforeEach(async () => {
    vi.resetModules()
    mod = await import('../../lib/supabase')
  })

  describe('getPanoramaData', () => {
    it('returns panorama with kpis, top_ocupaciones, provincias, modalidad', async () => {
      const data = await mod.getPanoramaData()

      expect(data).toHaveProperty('kpis')
      expect(data).toHaveProperty('top_ocupaciones')
      expect(data).toHaveProperty('provincias')
      expect(data).toHaveProperty('modalidad')
    })

    it('kpis have correct numeric fields', async () => {
      const { kpis } = await mod.getPanoramaData()

      expect(typeof kpis.total_ofertas).toBe('number')
      expect(typeof kpis.ocupaciones_distintas).toBe('number')
      expect(typeof kpis.empresas_activas).toBe('number')
      expect(typeof kpis.provincias).toBe('number')
      expect(kpis.total_ofertas).toBeGreaterThan(0)
    })

    it('top_ocupaciones is an array of objects with ocupacion and cantidad', async () => {
      const { top_ocupaciones } = await mod.getPanoramaData()

      expect(top_ocupaciones).toBeInstanceOf(Array)
      expect(top_ocupaciones.length).toBeGreaterThan(0)
      expect(top_ocupaciones[0]).toHaveProperty('ocupacion')
      expect(top_ocupaciones[0]).toHaveProperty('cantidad')
    })

    it('provincias have jurisdiccion, cantidad, porcentaje', async () => {
      const { provincias } = await mod.getPanoramaData()

      expect(provincias.length).toBeGreaterThan(0)
      expect(provincias[0]).toHaveProperty('jurisdiccion')
      expect(provincias[0]).toHaveProperty('cantidad')
      expect(provincias[0]).toHaveProperty('porcentaje')
    })
  })

  describe('getKPIs (backward-compatible wrapper)', () => {
    it('returns legacy KPI format from RPC', async () => {
      const kpis = await mod.getKPIs()

      expect(kpis).toHaveProperty('totalOfertas')
      expect(kpis).toHaveProperty('ocupacionesDistintas')
      expect(kpis).toHaveProperty('empresasActivas')
      expect(kpis).toHaveProperty('provincias')
      expect(kpis.totalOfertas).toBeGreaterThan(0)
    })
  })

  describe('getTopOcupaciones (backward-compatible wrapper)', () => {
    it('returns sliced top ocupaciones', async () => {
      const top = await mod.getTopOcupaciones(3)

      expect(top).toBeInstanceOf(Array)
      expect(top.length).toBeLessThanOrEqual(3)
    })
  })

  describe('getOfertasPorProvincia (backward-compatible wrapper)', () => {
    it('returns provincia data from RPC', async () => {
      const provs = await mod.getOfertasPorProvincia()

      expect(provs).toBeInstanceOf(Array)
      expect(provs.length).toBeGreaterThan(0)
    })
  })

  describe('getOfertasPorModalidad (backward-compatible wrapper)', () => {
    it('returns modalidad data from RPC', async () => {
      const mods = await mod.getOfertasPorModalidad()

      expect(mods).toBeInstanceOf(Array)
      expect(mods.length).toBeGreaterThan(0)
      expect(mods[0]).toHaveProperty('modalidad')
      expect(mods[0]).toHaveProperty('cantidad')
    })
  })

  describe('getEvolucionPeriodos', () => {
    it('returns array of PeriodoEvolucion objects', async () => {
      const periodos = await mod.getEvolucionPeriodos()

      expect(periodos).toBeInstanceOf(Array)
      expect(periodos.length).toBeGreaterThan(0)
      expect(periodos[0]).toHaveProperty('label')
      expect(periodos[0]).toHaveProperty('ofertas')
      expect(periodos[0]).toHaveProperty('fechaDesde')
      expect(periodos[0]).toHaveProperty('fechaHasta')
      expect(periodos[0]).toHaveProperty('esPeriodoActual')
    })

    it('last period is marked as current', async () => {
      const periodos = await mod.getEvolucionPeriodos()
      const actual = periodos.find(p => p.esPeriodoActual)
      expect(actual).toBeDefined()
    })
  })

  describe('getDistribucionRequerimientos', () => {
    it('returns all distribution fields', async () => {
      const req = await mod.getDistribucionRequerimientos()

      expect(req).toHaveProperty('total')
      expect(req).toHaveProperty('educacion')
      expect(req).toHaveProperty('experiencia')
      expect(req).toHaveProperty('seniority')
      expect(req).toHaveProperty('modalidad')
      expect(req).toHaveProperty('genteCargo')
      expect(req).toHaveProperty('jornada')
    })

    it('total is a number', async () => {
      const req = await mod.getDistribucionRequerimientos()
      expect(typeof req.total).toBe('number')
    })

    it('educacion items have name, value, porcentaje', async () => {
      const { educacion } = await mod.getDistribucionRequerimientos()

      expect(educacion.length).toBeGreaterThan(0)
      expect(educacion[0]).toHaveProperty('name')
      expect(educacion[0]).toHaveProperty('value')
      expect(educacion[0]).toHaveProperty('porcentaje')
    })
  })

  describe('getSkillsResumen', () => {
    it('returns por_l1, digitales, top_skills', async () => {
      const data = await mod.getSkillsResumen()

      expect(data).toHaveProperty('por_l1')
      expect(data).toHaveProperty('digitales')
      expect(data).toHaveProperty('top_skills')
    })

    it('digitales has correct shape', async () => {
      const { digitales } = await mod.getSkillsResumen()

      expect(typeof digitales.digitales).toBe('number')
      expect(typeof digitales.no_digitales).toBe('number')
      expect(typeof digitales.total).toBe('number')
    })

    it('top_skills are sorted by value desc', async () => {
      const { top_skills } = await mod.getSkillsResumen()

      for (let i = 1; i < top_skills.length; i++) {
        expect(top_skills[i - 1].value).toBeGreaterThanOrEqual(top_skills[i].value)
      }
    })
  })

  describe('getSidebarCounts', () => {
    it('returns total_ofertas, sectores, ocupaciones_tree', async () => {
      const data = await mod.getSidebarCounts()

      expect(data).toHaveProperty('total_ofertas')
      expect(data).toHaveProperty('sectores')
      expect(data).toHaveProperty('ocupaciones_tree')
    })

    it('sectores have sector and count', async () => {
      const { sectores } = await mod.getSidebarCounts()

      expect(sectores.length).toBeGreaterThan(0)
      expect(sectores[0]).toHaveProperty('sector')
      expect(sectores[0]).toHaveProperty('count')
    })

    it('ocupaciones_tree has major_group and children', async () => {
      const { ocupaciones_tree } = await mod.getSidebarCounts()

      expect(ocupaciones_tree.length).toBeGreaterThan(0)
      expect(ocupaciones_tree[0]).toHaveProperty('major_group')
      expect(ocupaciones_tree[0]).toHaveProperty('children')
      expect(ocupaciones_tree[0].children).toBeInstanceOf(Array)
    })
  })

  describe('getTotalOfertas (uses panorama RPC)', () => {
    it('returns total count', async () => {
      const total = await mod.getTotalOfertas()
      expect(typeof total).toBe('number')
      expect(total).toBeGreaterThan(0)
    })
  })

  describe('getOcupacionesTree (backward-compatible)', () => {
    it('returns OcupacionTreeNode array', async () => {
      const tree = await mod.getOcupacionesTree()

      expect(tree).toBeInstanceOf(Array)
      expect(tree.length).toBeGreaterThan(0)
      expect(tree[0]).toHaveProperty('id')
      expect(tree[0]).toHaveProperty('label')
      expect(tree[0]).toHaveProperty('count')
      expect(tree[0]).toHaveProperty('children')
    })
  })
})
