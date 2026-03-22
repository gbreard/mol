import { describe, it, expect } from 'vitest'
import { mockDinamicaRPC } from '../mocks/fixtures/scraping-dinamica'

describe('get_scraping_dinamica RPC response', () => {
  describe('structure', () => {
    it('has dias, kpis, periodo', () => {
      expect(mockDinamicaRPC).toHaveProperty('dias')
      expect(mockDinamicaRPC).toHaveProperty('kpis')
      expect(mockDinamicaRPC).toHaveProperty('periodo')
    })

    it('dias entries have required fields', () => {
      const dia = mockDinamicaRPC.dias[0]
      expect(dia).toHaveProperty('fecha')
      expect(dia).toHaveProperty('ofertas_nuevas')
      expect(dia).toHaveProperty('ofertas_bajas')
      expect(dia).toHaveProperty('ofertas_republicadas')
      expect(dia).toHaveProperty('ofertas_activas')
      expect(dia).toHaveProperty('flujo_neto')
      expect(dia).toHaveProperty('tasa_rotacion')
      expect(dia).toHaveProperty('tasa_republicacion')
    })

    it('kpis has aggregate fields', () => {
      const { kpis } = mockDinamicaRPC
      expect(typeof kpis.total_nuevas).toBe('number')
      expect(typeof kpis.total_bajas).toBe('number')
      expect(typeof kpis.total_republicadas).toBe('number')
      expect(typeof kpis.flujo_neto_periodo).toBe('number')
      expect(typeof kpis.tasa_rotacion_promedio).toBe('number')
      expect(typeof kpis.vida_media_promedio).toBe('number')
    })
  })

  describe('data consistency', () => {
    it('flujo_neto = nuevas - bajas', () => {
      for (const dia of mockDinamicaRPC.dias) {
        expect(dia.flujo_neto).toBe(dia.ofertas_nuevas - dia.ofertas_bajas)
      }
    })

    it('tasa_rotacion is non-negative', () => {
      for (const dia of mockDinamicaRPC.dias) {
        expect(dia.tasa_rotacion).toBeGreaterThanOrEqual(0)
      }
    })

    it('dias are sorted chronologically', () => {
      const fechas = mockDinamicaRPC.dias.map(d => d.fecha)
      const sorted = [...fechas].sort()
      expect(fechas).toEqual(sorted)
    })

    it('flujo_neto_periodo equals sum of daily flujos', () => {
      const sumFlujo = mockDinamicaRPC.dias.reduce((s, d) => s + d.flujo_neto, 0)
      expect(mockDinamicaRPC.kpis.flujo_neto_periodo).toBe(sumFlujo)
    })
  })

  describe('market interpretations', () => {
    it('high tasa_rotacion indicates dynamic market', () => {
      expect(mockDinamicaRPC.kpis.tasa_rotacion_promedio).toBeGreaterThan(0.4)
    })

    it('positive flujo_neto_periodo means market is growing', () => {
      expect(mockDinamicaRPC.kpis.flujo_neto_periodo).toBeGreaterThan(0)
    })

    it('vida_media_promedio is reasonable (1-60 days)', () => {
      expect(mockDinamicaRPC.kpis.vida_media_promedio).toBeGreaterThan(0)
      expect(mockDinamicaRPC.kpis.vida_media_promedio).toBeLessThan(60)
    })
  })
})
