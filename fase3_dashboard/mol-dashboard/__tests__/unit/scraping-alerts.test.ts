/**
 * Unit tests para la lógica de alertas del monitor de scraping (por cadencia).
 * lib/scraping-alerts.ts — funciones puras.
 */
import { describe, it, expect } from 'vitest'
import {
  horasSin, nivelAtraso, corridasEnCero, evaluarPortal,
  type PortalLive, type HistoryDay,
} from '@/lib/scraping-alerts'

const NOW = Date.parse('2026-09-01T14:00:00Z')
const hAntes = (h: number) => new Date(NOW - h * 3_600_000).toISOString()

const base: PortalLive = {
  portal: 'x', total: 1000, ultimo_scraping: hAntes(2),
  ultimos_7d: 100, hoy: 10, umbral_horas: 96, cadencia: 'bisemanal',
}

describe('horasSin', () => {
  it('calcula horas desde el último scraping', () => {
    expect(horasSin(hAntes(10), NOW)).toBeCloseTo(10, 1)
  })
  it('sin fecha → Infinity', () => {
    expect(horasSin(null, NOW)).toBe(Infinity)
    expect(horasSin('', NOW)).toBe(Infinity)
  })
})

describe('nivelAtraso', () => {
  it('ok bajo el umbral, warn hasta 2×, error a partir de 2×', () => {
    expect(nivelAtraso(10, 30)).toBe('ok')
    expect(nivelAtraso(40, 30)).toBe('warn')
    expect(nivelAtraso(70, 30)).toBe('error')
  })
})

describe('corridasEnCero', () => {
  const hist: HistoryDay[] = [
    { fecha: '2026-08-30', por_portal: { caba: 3 } },
    { fecha: '2026-08-31', por_portal: { caba: 0 } },
    { fecha: '2026-09-01', por_portal: { bumeran: 500 } }, // caba ausente = 0
  ]
  it('cuenta días recientes consecutivos en 0 (ausente = 0)', () => {
    // más reciente 09-01 (caba ausente=0), 08-31 (0), 08-30 (3) → 2 consecutivos
    expect(corridasEnCero('caba', hist, 3)).toBe(2)
  })
  it('corta al primer día con datos', () => {
    const h2: HistoryDay[] = [
      { fecha: '2026-09-01', por_portal: { caba: 0 } },
      { fecha: '2026-08-31', por_portal: { caba: 2 } },
      { fecha: '2026-08-30', por_portal: { caba: 0 } },
    ]
    expect(corridasEnCero('caba', h2, 3)).toBe(1)
  })
})

describe('evaluarPortal', () => {
  it('portal fresco → ok', () => {
    expect(evaluarPortal(base, [], NOW).nivel).toBe('ok')
  })

  it('bisemanal entre umbral y 2× → warn atrasado', () => {
    const p = { ...base, ultimo_scraping: hAntes(100) } // >96, <192
    const ev = evaluarPortal(p, [], NOW)
    expect(ev).toMatchObject({ nivel: 'warn', tipo: 'atrasado' })
  })

  it('bisemanal >2×umbral → error atrasado', () => {
    const p = { ...base, ultimo_scraping: hAntes(200) }
    expect(evaluarPortal(p, [], NOW)).toMatchObject({ nivel: 'error', tipo: 'atrasado' })
  })

  it('diario vivo con 0 hoy, pasada la hora de corte → corrió pero cero', () => {
    const p: PortalLive = {
      ...base, portal: 'indeed', cadencia: 'diaria', umbral_horas: 30,
      hoy: 0, total: 5000, ultimo_scraping: hAntes(20), // fresco aún (<60)
    }
    const ev = evaluarPortal(p, [], NOW, /*horaCorte*/ 0)
    expect(ev).toMatchObject({ nivel: 'warn', tipo: 'corrio_cero' })
  })

  it('diario con 0 hoy pero ANTES de la hora de corte → no dispara corrió-cero', () => {
    const p: PortalLive = {
      ...base, portal: 'indeed', cadencia: 'diaria', umbral_horas: 30,
      hoy: 0, total: 5000, ultimo_scraping: hAntes(20),
    }
    const ev = evaluarPortal(p, [], NOW, /*horaCorte*/ 25) // nunca pasa
    expect(ev.tipo).not.toBe('corrio_cero')
    expect(ev.nivel).toBe('ok') // 20h < umbral 30
  })

  it('CABA goteo: 3 corridas seguidas en cero → goteo_cero (aunque esté fresco)', () => {
    const hist: HistoryDay[] = [
      { fecha: '2026-08-30', por_portal: { caba: 0 } },
      { fecha: '2026-08-31', por_portal: { caba: 0 } },
      { fecha: '2026-09-01', por_portal: { caba: 0 } },
    ]
    const p: PortalLive = {
      portal: 'caba', total: 66, ultimo_scraping: hAntes(20), ultimos_7d: 0, hoy: 0,
      cadencia: 'goteo', umbral_horas: 96, cero_corridas: 3,
    }
    expect(evaluarPortal(p, hist, NOW)).toMatchObject({ nivel: 'warn', tipo: 'goteo_cero' })
  })

  it('CABA goteo: solo 2 días en cero → no dispara (goteo normal)', () => {
    const hist: HistoryDay[] = [
      { fecha: '2026-08-30', por_portal: { caba: 5 } },
      { fecha: '2026-08-31', por_portal: { caba: 0 } },
      { fecha: '2026-09-01', por_portal: { caba: 0 } },
    ]
    const p: PortalLive = {
      portal: 'caba', total: 66, ultimo_scraping: hAntes(20), ultimos_7d: 2, hoy: 2,
      cadencia: 'goteo', umbral_horas: 96, cero_corridas: 3,
    }
    expect(evaluarPortal(p, hist, NOW).tipo).not.toBe('goteo_cero')
  })
})
