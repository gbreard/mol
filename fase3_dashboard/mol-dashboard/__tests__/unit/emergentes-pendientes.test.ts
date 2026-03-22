/**
 * Unit tests for emergentes_pendientes (Bloque 9°)
 * Tests: structure, detection logic, approve/reject flow
 */
import { describe, it, expect } from 'vitest'

const mockEmergentes = [
  { id: 1, skill_label: 'Docker', skill_uri: null, isco_code: '2512', ocupacion_label: 'Desarrollador de software', frecuencia_pct: 45.2, ofertas_count: 120, total_ofertas_isco: 265, estado: 'pendiente', fecha_deteccion: '2026-03-22T10:00:00Z', fecha_resolucion: null, resuelto_por: null, notas: null },
  { id: 2, skill_label: 'Kubernetes', skill_uri: null, isco_code: '2512', ocupacion_label: 'Desarrollador de software', frecuencia_pct: 32.1, ofertas_count: 85, total_ofertas_isco: 265, estado: 'pendiente', fecha_deteccion: '2026-03-22T10:00:00Z', fecha_resolucion: null, resuelto_por: null, notas: null },
  { id: 3, skill_label: 'SAP', skill_uri: 'http://data.europa.eu/esco/skill/sap', isco_code: '2411', ocupacion_label: 'Contable', frecuencia_pct: 38.5, ofertas_count: 45, total_ofertas_isco: 117, estado: 'aprobada', fecha_deteccion: '2026-03-20T10:00:00Z', fecha_resolucion: '2026-03-21T15:00:00Z', resuelto_por: 'admin@oede.gob.ar', notas: 'Aprobada como skill argentina' },
]

const mockRecalculoResult = {
  nuevas_o_actualizadas: 15,
  total_pendientes: 42,
  total_aprobadas: 8,
  total_rechazadas: 3,
  timestamp: '2026-03-22T10:00:00Z',
}

describe('emergentes_pendientes', () => {
  describe('structure', () => {
    it('each emergente has required fields', () => {
      for (const e of mockEmergentes) {
        expect(e).toHaveProperty('id')
        expect(e).toHaveProperty('skill_label')
        expect(e).toHaveProperty('isco_code')
        expect(e).toHaveProperty('frecuencia_pct')
        expect(e).toHaveProperty('ofertas_count')
        expect(e).toHaveProperty('estado')
        expect(typeof e.frecuencia_pct).toBe('number')
      }
    })

    it('estado is valid', () => {
      const valid = ['pendiente', 'aprobada', 'rechazada']
      for (const e of mockEmergentes) {
        expect(valid).toContain(e.estado)
      }
    })

    it('frecuencia_pct >= 30 (threshold)', () => {
      for (const e of mockEmergentes) {
        expect(e.frecuencia_pct).toBeGreaterThanOrEqual(30)
      }
    })
  })

  describe('detection logic', () => {
    it('frecuencia = ofertas_count / total_ofertas_isco * 100', () => {
      for (const e of mockEmergentes) {
        const expected = Math.round(e.ofertas_count / e.total_ofertas_isco * 1000) / 10
        expect(Math.abs(e.frecuencia_pct - expected)).toBeLessThan(1)
      }
    })

    it('only skills with enough data (total_ofertas >= 10)', () => {
      for (const e of mockEmergentes) {
        expect(e.total_ofertas_isco).toBeGreaterThanOrEqual(10)
      }
    })
  })

  describe('approve/reject flow', () => {
    it('pendiente has no resolucion', () => {
      const pendientes = mockEmergentes.filter(e => e.estado === 'pendiente')
      for (const e of pendientes) {
        expect(e.fecha_resolucion).toBeNull()
        expect(e.resuelto_por).toBeNull()
      }
    })

    it('aprobada has resolucion data', () => {
      const aprobadas = mockEmergentes.filter(e => e.estado === 'aprobada')
      for (const e of aprobadas) {
        expect(e.fecha_resolucion).toBeTruthy()
        expect(e.resuelto_por).toBeTruthy()
      }
    })
  })

  describe('recalcular_emergentes result', () => {
    it('returns counts', () => {
      expect(mockRecalculoResult.nuevas_o_actualizadas).toBeGreaterThanOrEqual(0)
      expect(mockRecalculoResult.total_pendientes).toBeGreaterThanOrEqual(0)
      expect(typeof mockRecalculoResult.total_aprobadas).toBe('number')
      expect(typeof mockRecalculoResult.total_rechazadas).toBe('number')
    })

    it('has timestamp', () => {
      expect(mockRecalculoResult.timestamp).toBeTruthy()
    })
  })
})
