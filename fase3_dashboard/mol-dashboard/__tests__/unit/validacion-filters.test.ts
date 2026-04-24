/**
 * Tests para el filtro search del panel de validación.
 *
 * Regresión del bug donde id_oferta usaba .eq. (match exacto) — fallaba con
 * prefijos/sufijos y no soportaba listas pegadas con coma.
 *
 * Estrategia: interceptar la request HTTP que hace getOfertasValidacion y
 * verificar el query string enviado a PostgREST.
 */
import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import { http, HttpResponse } from 'msw'
import { server } from '../mocks/server'

const SUPABASE_URL = 'https://test.supabase.co'

describe('getOfertasValidacion — filtro search', () => {
  let capturedUrl: URL | null = null
  let mod: typeof import('../../lib/supabase')

  beforeEach(async () => {
    capturedUrl = null
    server.use(
      http.get(`${SUPABASE_URL}/rest/v1/ofertas_dashboard`, ({ request }) => {
        capturedUrl = new URL(request.url)
        return HttpResponse.json([], {
          headers: { 'content-range': '0-0/0' },
        })
      })
    )
    mod = await import('../../lib/supabase')
  })

  afterEach(() => {
    server.resetHandlers()
  })

  it('sin search no aplica filtro de título/ID', async () => {
    await mod.getOfertasValidacion({}, 50, 0)
    expect(capturedUrl).not.toBeNull()
    expect(capturedUrl!.searchParams.get('or')).toBeNull()
    expect(capturedUrl!.searchParams.get('id_oferta')).toBeNull()
  })

  it('un solo término dispara ilike parcial en titulo, titulo_limpio e id_oferta', async () => {
    await mod.getOfertasValidacion({ search: '1118077' }, 50, 0)
    const or = capturedUrl!.searchParams.get('or')
    expect(or).toContain('titulo_limpio.ilike.%1118077%')
    expect(or).toContain('titulo.ilike.%1118077%')
    expect(or).toContain('id_oferta.ilike.%1118077%')
    // Ya no debería usar .eq. para id_oferta
    expect(or).not.toContain('id_oferta.eq.')
  })

  it('soporta IDs con sufijo _N (sub-ofertas multi-position)', async () => {
    await mod.getOfertasValidacion({ search: '7776515806_2' }, 50, 0)
    const or = capturedUrl!.searchParams.get('or')
    expect(or).toContain('id_oferta.ilike.%7776515806_2%')
  })

  it('lista de IDs separados por coma usa .in_() — exacto', async () => {
    await mod.getOfertasValidacion(
      { search: '8751081602,1118077151,7776515806_2' },
      50,
      0
    )
    const idOferta = capturedUrl!.searchParams.get('id_oferta')
    expect(idOferta).toBeTruthy()
    expect(idOferta).toContain('in.')
    expect(idOferta).toContain('8751081602')
    expect(idOferta).toContain('1118077151')
    expect(idOferta).toContain('7776515806_2')
    // No debería haber .or() cuando viene lista
    expect(capturedUrl!.searchParams.get('or')).toBeNull()
  })

  it('lista separada por espacios también funciona', async () => {
    await mod.getOfertasValidacion(
      { search: '8751081602 1118077151' },
      50,
      0
    )
    const idOferta = capturedUrl!.searchParams.get('id_oferta')
    expect(idOferta).toContain('in.')
    expect(idOferta).toContain('8751081602')
    expect(idOferta).toContain('1118077151')
  })

  it('lista pegada desde xlsx (newlines) se parsea', async () => {
    await mod.getOfertasValidacion(
      { search: '8751081602\n1118077151\n2175645' },
      50,
      0
    )
    const idOferta = capturedUrl!.searchParams.get('id_oferta')
    expect(idOferta).toContain('in.')
    expect(idOferta).toContain('2175645')
  })

  it('escapa caracteres PostgREST peligrosos en término único', async () => {
    await mod.getOfertasValidacion({ search: 'foo(bar):baz' }, 50, 0)
    const or = capturedUrl!.searchParams.get('or')
    // El término foo(bar):baz debe convertirse a "foo bar  baz" (sin paréntesis ni :)
    expect(or).toContain('%foo bar  baz%')
    // No debe aparecer el texto peligroso original
    expect(or).not.toContain('foo(bar)')
    expect(or).not.toContain(':baz')
  })

  it('mantiene otros filtros cuando hay search', async () => {
    await mod.getOfertasValidacion(
      { search: '1118077', iscoGroup: '5', portal: 'bumeran' },
      50,
      0
    )
    expect(capturedUrl!.searchParams.get('or')).toContain('id_oferta.ilike.%1118077%')
    expect(capturedUrl!.searchParams.get('isco_code')).toBe('like.5%')
    expect(capturedUrl!.searchParams.get('portal')).toBe('eq.bumeran')
  })
})
