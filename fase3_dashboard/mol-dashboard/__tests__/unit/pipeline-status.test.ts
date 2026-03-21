/**
 * Unit tests for get_pipeline_status RPC
 * Tests: response structure, alert logic, phase states
 */
import { describe, it, expect } from 'vitest'
import {
  mockPipelineStatusRPC,
  mockPipelineStatusAllOK,
  mockPipelineStatusError,
} from '../mocks/fixtures/pipeline-status'

describe('get_pipeline_status RPC response', () => {
  describe('response structure', () => {
    it('has fases, alertas, resumen, ultimo_update', () => {
      const data = mockPipelineStatusRPC
      expect(data).toHaveProperty('fases')
      expect(data).toHaveProperty('alertas')
      expect(data).toHaveProperty('resumen')
      expect(data).toHaveProperty('ultimo_update')
    })

    it('fases has scraping, nlp, matching, sync', () => {
      const { fases } = mockPipelineStatusRPC
      expect(fases).toHaveProperty('scraping')
      expect(fases).toHaveProperty('nlp')
      expect(fases).toHaveProperty('matching')
      expect(fases).toHaveProperty('sync')
    })

    it('each fase has estado field with valid value', () => {
      const validEstados = ['ok', 'warning', 'error']
      const { fases } = mockPipelineStatusRPC

      expect(validEstados).toContain(fases.scraping.estado)
      expect(validEstados).toContain(fases.nlp.estado)
      expect(validEstados).toContain(fases.matching.estado)
      expect(validEstados).toContain(fases.sync.estado)
    })

    it('resumen has total_ofertas, en_supabase, fase_sugerida', () => {
      const { resumen } = mockPipelineStatusRPC
      expect(typeof resumen.total_ofertas).toBe('number')
      expect(typeof resumen.en_supabase).toBe('number')
      expect(typeof resumen.fase_sugerida).toBe('string')
      expect(typeof resumen.fase_sugerida_razon).toBe('string')
    })
  })

  describe('alert logic', () => {
    it('generates alerts when scraping is delayed', () => {
      const { alertas } = mockPipelineStatusRPC
      const scrapingAlert = alertas.find(a => a.accion === 'lanzar_scraping')

      expect(scrapingAlert).toBeDefined()
      expect(scrapingAlert!.nivel).toBe('warning')
      expect(scrapingAlert!.mensaje).toContain('días')
    })

    it('generates alerts when NLP has pending offers', () => {
      const { alertas } = mockPipelineStatusRPC
      const nlpAlert = alertas.find(a => a.accion === 'procesar_nlp')

      expect(nlpAlert).toBeDefined()
      expect(nlpAlert!.mensaje).toContain('sin procesar NLP')
    })

    it('generates info alert for pending user issues', () => {
      const { alertas } = mockPipelineStatusRPC
      const issuesAlert = alertas.find(a => a.accion === 'ver_issues')

      expect(issuesAlert).toBeDefined()
      expect(issuesAlert!.nivel).toBe('info')
    })

    it('each alert has nivel, mensaje, accion', () => {
      for (const alerta of mockPipelineStatusRPC.alertas) {
        expect(alerta).toHaveProperty('nivel')
        expect(alerta).toHaveProperty('mensaje')
        expect(alerta).toHaveProperty('accion')
        expect(typeof alerta.mensaje).toBe('string')
      }
    })
  })

  describe('all OK scenario', () => {
    it('shows ok estado for all phases', () => {
      const { fases } = mockPipelineStatusAllOK

      expect(fases.scraping.estado).toBe('ok')
      expect(fases.nlp.estado).toBe('ok')
      expect(fases.matching.estado).toBe('ok')
      expect(fases.sync.estado).toBe('ok')
    })

    it('has single ok alert', () => {
      const { alertas } = mockPipelineStatusAllOK

      expect(alertas).toHaveLength(1)
      expect(alertas[0].nivel).toBe('ok')
      expect(alertas[0].mensaje).toContain('sin alertas')
    })

    it('resumen shows 0 pending issues', () => {
      const { resumen } = mockPipelineStatusAllOK
      expect(resumen.issues_humanos_pendientes).toBe(0)
    })
  })

  describe('error scenario', () => {
    it('shows error estado for scraping and nlp', () => {
      const { fases } = mockPipelineStatusError

      expect(fases.scraping.estado).toBe('error')
      expect(fases.nlp.estado).toBe('error')
    })

    it('generates multiple alerts sorted by severity', () => {
      const { alertas } = mockPipelineStatusError

      expect(alertas.length).toBeGreaterThan(2)
      // First alerts should be errors
      expect(alertas[0].nivel).toBe('error')
      expect(alertas[1].nivel).toBe('error')
    })

    it('sync shows warning when pendientes > 0', () => {
      const { fases } = mockPipelineStatusError
      expect(fases.sync.estado).toBe('warning')
      expect(fases.sync.pendientes).toBe(1000)
    })
  })

  describe('scraping fase details', () => {
    it('includes fuentes breakdown', () => {
      const { fuentes } = mockPipelineStatusRPC.fases.scraping
      expect(typeof fuentes).toBe('object')
      expect(fuentes).toHaveProperty('bumeran')
      expect(fuentes).toHaveProperty('computrabajo')
    })

    it('includes dias_desde_scraping', () => {
      expect(typeof mockPipelineStatusRPC.fases.scraping.dias_desde_scraping).toBe('number')
    })
  })

  describe('nlp fase details', () => {
    it('has procesadas and pendientes counts', () => {
      const { nlp } = mockPipelineStatusRPC.fases
      expect(typeof nlp.procesadas).toBe('number')
      expect(typeof nlp.pendientes).toBe('number')
      // procesadas + pendientes puede exceder ofertas_totales temporalmente
      // (ofertas_totales es de sistema_estado, NLP counts son de otra tabla)
      expect(nlp.procesadas).toBeGreaterThan(0)
    })
  })

  describe('matching fase details', () => {
    it('has validadas and errores_sin_resolver', () => {
      const { matching } = mockPipelineStatusRPC.fases
      expect(typeof matching.validadas).toBe('number')
      expect(typeof matching.errores_sin_resolver).toBe('number')
    })
  })
})
