import { describe, it, expect } from 'vitest'
import {
  estadoOfertaBadge, sortOfertasRecientes, antiguedadOferta, formatFecha,
  periodoDesde, provinciaOfertas,
} from '@/lib/ofertas-estado'

describe('estadoOfertaBadge', () => {
  it('mapea los 5 estados de estado_ciclo', () => {
    expect(estadoOfertaBadge('activa').label).toBe('Activa')
    expect(estadoOfertaBadge('presunta_baja').label).toBe('Sin confirmar')
    for (const e of ['baja_confirmada', 'baja_inferida', 'baja_no_verificada', null, undefined]) {
      expect(estadoOfertaBadge(e).label).toBe('Cerrada')
    }
  })
})

describe('sortOfertasRecientes', () => {
  it('ordena por fecha DESC y desempata activa → presunta_baja → resto', () => {
    const ofertas = [
      { id: 'a', fecha_publicacion: '2026-08-10', estado_ciclo: 'baja_inferida' },
      { id: 'b', fecha_publicacion: '2026-08-21', estado_ciclo: 'baja_confirmada' },
      { id: 'c', fecha_publicacion: '2026-08-21', estado_ciclo: 'activa' },
      { id: 'd', fecha_publicacion: '2026-08-21', estado_ciclo: 'presunta_baja' },
      { id: 'e', fecha_publicacion: null, estado_ciclo: 'activa' },
    ]
    expect(sortOfertasRecientes(ofertas).map(o => o.id)).toEqual(['c', 'd', 'b', 'a', 'e'])
  })
})

describe('antiguedadOferta / formatFecha', () => {
  const hoy = new Date(2026, 9, 26) // 26/10/2026
  it('expresa la antigüedad en días, meses o años', () => {
    expect(antiguedadOferta('2026-10-26', hoy)).toBe('Publicado hoy')
    expect(antiguedadOferta('2026-10-21', hoy)).toBe('Publicado hace 5 días')
    expect(antiguedadOferta('2026-08-21', hoy)).toBe('Publicado hace 2 meses')
    expect(antiguedadOferta('2025-08-21', hoy)).toBe('Publicado hace 1 año')
    expect(antiguedadOferta(null, hoy)).toBe('')
  })
  it('formatea sin corrimiento de zona horaria', () => {
    expect(formatFecha('2026-07-12')).toBe('12/07/2026')
  })
})

describe('periodoDesde', () => {
  it('cuenta hacia atrás desde la última fecha con datos, no desde hoy', () => {
    expect(periodoDesde(30, '2026-08-21')).toBe('2026-07-22')
    expect(periodoDesde(7, '2026-08-21')).toBe('2026-08-14')
    expect(periodoDesde(null, '2026-08-21')).toBeNull()
  })
})

describe('provinciaOfertas', () => {
  it('normaliza al formato de ofertas_dashboard (CABA es "CABA")', () => {
    expect(provinciaOfertas('CABA')).toBe('CABA')
    expect(provinciaOfertas('Palermo, Capital Federal')).toBe('CABA')
    expect(provinciaOfertas('Ciudad Autónoma de Buenos Aires')).toBe('CABA')
    expect(provinciaOfertas('La Matanza, Buenos Aires')).toBe('Buenos Aires')
    expect(provinciaOfertas('Cordoba')).toBe('Córdoba')
    expect(provinciaOfertas('Rosario, Santa Fe')).toBe('Santa Fe')
    expect(provinciaOfertas('Atlantis')).toBeNull()
    expect(provinciaOfertas(null)).toBeNull()
  })
})
