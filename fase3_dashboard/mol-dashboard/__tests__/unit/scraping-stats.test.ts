/**
 * Unit tests for get_scraping_stats and get_scraping_history RPCs
 * Tests: response structure, anomaly detection, portal stats, history
 */
import { describe, it, expect } from 'vitest'
import {
  mockScrapingStatsRPC,
  mockScrapingHistoryRPC,
  mockScrapingStatsAllOK,
} from '../mocks/fixtures/scraping-stats'

describe('get_scraping_stats RPC response', () => {
  describe('response structure', () => {
    it('has portales, totales, alertas, timestamp', () => {
      expect(mockScrapingStatsRPC).toHaveProperty('portales')
      expect(mockScrapingStatsRPC).toHaveProperty('totales')
      expect(mockScrapingStatsRPC).toHaveProperty('alertas')
      expect(mockScrapingStatsRPC).toHaveProperty('timestamp')
    })

    it('portales is array with required fields', () => {
      expect(mockScrapingStatsRPC.portales).toBeInstanceOf(Array)
      expect(mockScrapingStatsRPC.portales.length).toBeGreaterThan(0)

      const portal = mockScrapingStatsRPC.portales[0]
      expect(portal).toHaveProperty('portal')
      expect(portal).toHaveProperty('total')
      expect(portal).toHaveProperty('ultimos_7d')
      expect(portal).toHaveProperty('ultima_fecha')
      expect(portal).toHaveProperty('dias_sin_datos')
      expect(portal).toHaveProperty('porcentaje')
    })

    it('totales has aggregate fields', () => {
      const { totales } = mockScrapingStatsRPC
      expect(typeof totales.total_ofertas).toBe('number')
      expect(typeof totales.portales_activos).toBe('number')
      expect(typeof totales.ofertas_7d).toBe('number')
      expect(typeof totales.ofertas_30d).toBe('number')
      expect(totales.total_ofertas).toBeGreaterThan(0)
    })
  })

  describe('anomaly detection', () => {
    it('detects portal without data >3 days', () => {
      const cabaAlert = mockScrapingStatsRPC.alertas.find(
        (a: any) => a.portal === 'caba'
      )
      expect(cabaAlert).toBeDefined()
      expect(cabaAlert!.nivel).toBe('error')
      expect(cabaAlert!.mensaje).toContain('dias')
    })

    it('alertas have nivel, portal, mensaje, detalle', () => {
      for (const alerta of mockScrapingStatsRPC.alertas) {
        expect(alerta).toHaveProperty('nivel')
        expect(alerta).toHaveProperty('portal')
        expect(alerta).toHaveProperty('mensaje')
        expect(typeof alerta.mensaje).toBe('string')
      }
    })

    it('no alertas when all portals are healthy', () => {
      expect(mockScrapingStatsAllOK.alertas).toHaveLength(0)
    })
  })

  describe('portal stats', () => {
    it('porcentaje sums to ~100%', () => {
      const totalPct = mockScrapingStatsRPC.portales.reduce(
        (sum: number, p: any) => sum + p.porcentaje, 0
      )
      expect(totalPct).toBeGreaterThan(90)
      expect(totalPct).toBeLessThanOrEqual(101)
    })

    it('dias_sin_datos is non-negative integer', () => {
      for (const portal of mockScrapingStatsRPC.portales) {
        expect(portal.dias_sin_datos).toBeGreaterThanOrEqual(0)
        expect(Number.isInteger(portal.dias_sin_datos)).toBe(true)
      }
    })

    it('ultimos_7d <= total', () => {
      for (const portal of mockScrapingStatsRPC.portales) {
        expect(portal.ultimos_7d).toBeLessThanOrEqual(portal.total)
      }
    })
  })
})

describe('get_scraping_history RPC response', () => {
  describe('response structure', () => {
    it('has dias and periodo', () => {
      expect(mockScrapingHistoryRPC).toHaveProperty('dias')
      expect(mockScrapingHistoryRPC).toHaveProperty('periodo')
    })

    it('periodo has desde, hasta, dias', () => {
      const { periodo } = mockScrapingHistoryRPC
      expect(periodo).toHaveProperty('desde')
      expect(periodo).toHaveProperty('hasta')
      expect(periodo).toHaveProperty('dias')
      expect(typeof periodo.dias).toBe('number')
    })

    it('dias entries have fecha, total, por_portal', () => {
      expect(mockScrapingHistoryRPC.dias.length).toBeGreaterThan(0)
      const dia = mockScrapingHistoryRPC.dias[0]
      expect(dia).toHaveProperty('fecha')
      expect(dia).toHaveProperty('total')
      expect(dia).toHaveProperty('por_portal')
      expect(typeof dia.por_portal).toBe('object')
    })
  })

  describe('data consistency', () => {
    it('total equals sum of por_portal values', () => {
      for (const dia of mockScrapingHistoryRPC.dias) {
        const sumPortales = Object.values(dia.por_portal as Record<string, number>)
          .reduce((a: number, b: number) => a + b, 0)
        expect(dia.total).toBe(sumPortales)
      }
    })

    it('dias are sorted chronologically', () => {
      const fechas = mockScrapingHistoryRPC.dias.map((d: any) => d.fecha)
      const sorted = [...fechas].sort()
      expect(fechas).toEqual(sorted)
    })
  })
})
