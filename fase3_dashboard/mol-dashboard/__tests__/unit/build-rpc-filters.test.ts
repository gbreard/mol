import { describe, it, expect } from 'vitest'
import { buildRPCFilters } from '@/lib/supabase'
import type { DashboardFilters } from '@/lib/types'

const emptyFilters: DashboardFilters = {
  territorio: '',
  provincia: '',
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
}

describe('buildRPCFilters', () => {
  it('returns empty object for undefined filters', () => {
    expect(buildRPCFilters()).toEqual({})
  })

  it('returns empty object for empty filters', () => {
    expect(buildRPCFilters(emptyFilters)).toEqual({})
  })

  it('maps provincia key to display name', () => {
    const result = buildRPCFilters({ ...emptyFilters, provincia: 'caba' })
    expect(result.provincia).toBe('Capital Federal')
  })

  it('converts fechaDesde to ISO date string', () => {
    const date = new Date('2026-02-15T10:30:00Z')
    const result = buildRPCFilters({ ...emptyFilters, fechaDesde: date })
    expect(result.fecha_desde).toBe('2026-02-15')
  })

  it('converts fechaHasta to ISO date string', () => {
    const date = new Date('2026-02-20T18:00:00Z')
    const result = buildRPCFilters({ ...emptyFilters, fechaHasta: date })
    expect(result.fecha_hasta).toBe('2026-02-20')
  })

  it('passes localidad array', () => {
    const result = buildRPCFilters({ ...emptyFilters, localidad: ['Palermo', 'Recoleta'] })
    expect(result.localidad).toEqual(['Palermo', 'Recoleta'])
  })

  it('passes seniority array', () => {
    const result = buildRPCFilters({ ...emptyFilters, seniority: ['junior', 'senior'] })
    expect(result.seniority).toEqual(['junior', 'senior'])
  })

  it('passes modalidad array', () => {
    const result = buildRPCFilters({ ...emptyFilters, modalidad: ['remoto'] })
    expect(result.modalidad).toEqual(['remoto'])
  })

  it('passes sector array', () => {
    const result = buildRPCFilters({ ...emptyFilters, sector: ['Información y comunicaciones'] })
    expect(result.sector).toEqual(['Información y comunicaciones'])
  })

  it('maps ocupacionesSeleccionadas to ocupaciones', () => {
    const result = buildRPCFilters({ ...emptyFilters, ocupacionesSeleccionadas: ['2514', '2411'] })
    expect(result.ocupaciones).toEqual(['2514', '2411'])
  })

  it('passes permanencia array', () => {
    const result = buildRPCFilters({ ...emptyFilters, permanencia: ['alta', 'media'] })
    expect(result.permanencia).toEqual(['alta', 'media'])
  })

  it('passes experiencia string', () => {
    const result = buildRPCFilters({ ...emptyFilters, experiencia: '3_5_anios' })
    expect(result.experiencia).toBe('3_5_anios')
  })

  it('passes jornada string', () => {
    const result = buildRPCFilters({ ...emptyFilters, jornada: 'full_time' })
    expect(result.jornada).toBe('full_time')
  })

  it('passes nivel_educativo array', () => {
    const result = buildRPCFilters({ ...emptyFilters, nivelEducativo: ['universitario'] })
    expect(result.nivel_educativo).toEqual(['universitario'])
  })

  it('ignores empty arrays', () => {
    const result = buildRPCFilters({ ...emptyFilters, seniority: [], sector: [] })
    expect(result.seniority).toBeUndefined()
    expect(result.sector).toBeUndefined()
  })

  it('builds multiple filters together', () => {
    const result = buildRPCFilters({
      ...emptyFilters,
      provincia: 'cordoba',
      seniority: ['senior'],
      modalidad: ['remoto'],
      experiencia: '5_mas',
    })
    expect(result).toEqual({
      provincia: 'Córdoba',
      seniority: ['senior'],
      modalidad: ['remoto'],
      experiencia: '5_mas',
    })
  })
})
