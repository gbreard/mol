/**
 * Unit tests for reconciliar_sistemas RPC
 * Tests: response structure, inconsistency detection, conteos
 */
import { describe, it, expect } from 'vitest'
import { mockReconciliacionOK, mockReconciliacionWarning } from '../mocks/fixtures/reconciliacion'

describe('reconciliar_sistemas RPC response', () => {
  describe('response structure', () => {
    it('has conteos, inconsistencias, estado', () => {
      expect(mockReconciliacionOK).toHaveProperty('conteos')
      expect(mockReconciliacionOK).toHaveProperty('inconsistencias')
      expect(mockReconciliacionOK).toHaveProperty('estado')
    })

    it('conteos has all required fields', () => {
      const { conteos } = mockReconciliacionOK
      expect(typeof conteos.local_total).toBe('number')
      expect(typeof conteos.local_con_nlp).toBe('number')
      expect(typeof conteos.supabase_ofertas).toBe('number')
      expect(typeof conteos.supabase_skills).toBe('number')
      expect(typeof conteos.supabase_sin_isco).toBe('number')
      expect(typeof conteos.supabase_sin_skills).toBe('number')
    })

    it('estado is valid value', () => {
      expect(['ok', 'warning', 'error']).toContain(mockReconciliacionOK.estado)
      expect(['ok', 'warning', 'error']).toContain(mockReconciliacionWarning.estado)
    })
  })

  describe('consistent state (all OK)', () => {
    it('estado is ok', () => {
      expect(mockReconciliacionOK.estado).toBe('ok')
    })

    it('has single ok inconsistency', () => {
      expect(mockReconciliacionOK.inconsistencias).toHaveLength(1)
      expect(mockReconciliacionOK.inconsistencias[0].severidad).toBe('ok')
    })

    it('local and supabase counts match', () => {
      const { conteos } = mockReconciliacionOK
      expect(conteos.local_total).toBe(conteos.supabase_ofertas)
      expect(conteos.supabase_sin_skills).toBe(0)
      expect(conteos.supabase_sin_isco).toBe(0)
    })
  })

  describe('inconsistent state (warning/error)', () => {
    it('estado reflects worst severity', () => {
      expect(mockReconciliacionWarning.estado).toBe('error')
    })

    it('detects ofertas faltantes', () => {
      const faltantes = mockReconciliacionWarning.inconsistencias.find(i => i.tipo === 'ofertas_faltantes')
      expect(faltantes).toBeDefined()
      expect(faltantes!.severidad).toBe('error')
      expect(faltantes!.diferencia).toBe(
        mockReconciliacionWarning.conteos.local_total - mockReconciliacionWarning.conteos.supabase_ofertas
      )
    })

    it('detects ofertas sin skills', () => {
      const sinSkills = mockReconciliacionWarning.inconsistencias.find(i => i.tipo === 'sin_skills')
      expect(sinSkills).toBeDefined()
      expect(sinSkills!.diferencia).toBe(2776)
      expect(sinSkills!.accion).toBe('backfill_skills')
    })

    it('detects ofertas sin ISCO', () => {
      const sinIsco = mockReconciliacionWarning.inconsistencias.find(i => i.tipo === 'sin_isco')
      expect(sinIsco).toBeDefined()
      expect(sinIsco!.diferencia).toBe(50)
    })

    it('each inconsistency has required fields', () => {
      for (const inc of mockReconciliacionWarning.inconsistencias) {
        expect(inc).toHaveProperty('tipo')
        expect(inc).toHaveProperty('severidad')
        expect(inc).toHaveProperty('mensaje')
        expect(inc).toHaveProperty('esperado')
        expect(inc).toHaveProperty('actual')
        expect(inc).toHaveProperty('diferencia')
        expect(typeof inc.mensaje).toBe('string')
        expect(typeof inc.diferencia).toBe('number')
      }
    })

    it('inconsistencies are sorted by severity (error first)', () => {
      const severities = mockReconciliacionWarning.inconsistencias.map(i => i.severidad)
      const errorIdx = severities.indexOf('error')
      const warningIdx = severities.indexOf('warning')
      expect(errorIdx).toBeLessThan(warningIdx)
    })
  })
})
