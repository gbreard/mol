/**
 * Tests para los filtros del panel de validación.
 *
 * Cubre:
 * - Filtro search (regresión: id_oferta usaba .eq. fallaba con prefijos)
 * - Filtro runId (auditoría por corrida — habilita ver ofertas del régimen X)
 * - getRunsDisponibles (RPC + parser de fecha legible)
 *
 * Estrategia: interceptar la request HTTP que hace getOfertasValidacion y
 * verificar el query string enviado a PostgREST.
 */
import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import { http, HttpResponse } from 'msw'
import { server } from '../mocks/server'
import { mockRunsDisponibles } from '../mocks/fixtures/runs-disponibles'

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

describe('getOfertasValidacion — filtro runId', () => {
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

  it('sin runId no incluye filtro run_id en la query', async () => {
    await mod.getOfertasValidacion({}, 50, 0)
    expect(capturedUrl!.searchParams.get('run_id')).toBeNull()
  })

  it('con runId aplica eq sobre run_id', async () => {
    await mod.getOfertasValidacion({ runId: 'run_20260516_2052' }, 50, 0)
    expect(capturedUrl!.searchParams.get('run_id')).toBe('eq.run_20260516_2052')
  })

  it('runId combina correctamente con portal', async () => {
    await mod.getOfertasValidacion(
      { runId: 'run_20260516_2052', portal: 'computrabajo' },
      50,
      0
    )
    expect(capturedUrl!.searchParams.get('run_id')).toBe('eq.run_20260516_2052')
    expect(capturedUrl!.searchParams.get('portal')).toBe('eq.computrabajo')
  })

  it('runId combina con scoreRange (rango numérico)', async () => {
    await mod.getOfertasValidacion(
      { runId: 'run_20260516_1745', scoreRange: '0.3-0.5' },
      50,
      0
    )
    expect(capturedUrl!.searchParams.get('run_id')).toBe('eq.run_20260516_1745')
    expect(capturedUrl!.searchParams.get('occupation_match_score')).toContain('gte.0.3')
  })

  it('runId + validacion_humana + portal (tres filtros simultáneos)', async () => {
    await mod.getOfertasValidacion(
      { runId: 'run_20260516_2052', estadoValidacion: 'ok', portal: 'bumeran' },
      50,
      0
    )
    expect(capturedUrl!.searchParams.get('run_id')).toBe('eq.run_20260516_2052')
    expect(capturedUrl!.searchParams.get('validacion_humana')).toBe('eq.ok')
    expect(capturedUrl!.searchParams.get('portal')).toBe('eq.bumeran')
  })

  it('runId con search ambos coexisten', async () => {
    await mod.getOfertasValidacion(
      { runId: 'run_20260516_2052', search: 'cajero' },
      50,
      0
    )
    expect(capturedUrl!.searchParams.get('run_id')).toBe('eq.run_20260516_2052')
    expect(capturedUrl!.searchParams.get('or')).toContain('titulo.ilike.%cajero%')
  })

  it('runId vacío string no agrega filtro', async () => {
    await mod.getOfertasValidacion({ runId: '' }, 50, 0)
    expect(capturedUrl!.searchParams.get('run_id')).toBeNull()
  })
})

describe('getRunsDisponibles — RPC + parser fecha legible', () => {
  let mod: typeof import('../../lib/supabase')

  beforeEach(async () => {
    mod = await import('../../lib/supabase')
  })

  afterEach(() => {
    server.resetHandlers()
  })

  it('devuelve runs ordenados por run_id DESC (más reciente primero)', async () => {
    const runs = await mod.getRunsDisponibles()
    expect(runs.length).toBe(mockRunsDisponibles.length)
    for (let i = 0; i < runs.length - 1; i++) {
      expect(runs[i].run_id.localeCompare(runs[i + 1].run_id)).toBeGreaterThanOrEqual(0)
    }
  })

  it('parsea fecha legible de run_YYYYMMDD_HHMMSS', async () => {
    const runs = await mod.getRunsDisponibles()
    const r = runs.find((x) => x.run_id === 'run_20260516_2052')
    expect(r).toBeDefined()
    expect(r!.fecha_legible).toBe('16 May 2026, 20:52')
    expect(r!.n).toBe(471)
  })

  it('parsea fecha de prefijo reapply_', async () => {
    const runs = await mod.getRunsDisponibles()
    const r = runs.find((x) => x.run_id === 'reapply_20260219_203452')
    expect(r).toBeDefined()
    expect(r!.fecha_legible).toBe('19 Feb 2026, 20:34')
  })

  it('parsea fecha de prefijo spec_X_NAME_ con timestamp ISO', async () => {
    const runs = await mod.getRunsDisponibles()
    const r = runs.find((x) => x.run_id === 'spec_h_rematch_20260426T203656Z')
    expect(r).toBeDefined()
    expect(r!.fecha_legible).toBe('26 Abr 2026, 20:36')
  })

  it('devuelve fecha_legible null cuando el run_id no matchea el patrón', async () => {
    server.use(
      http.post(
        `${SUPABASE_URL}/rest/v1/rpc/get_runs_disponibles`,
        () => HttpResponse.json([{ run_id: 'custom_id_sin_fecha', n: 5 }]),
      ),
    )
    const runs = await mod.getRunsDisponibles()
    expect(runs[0].fecha_legible).toBeNull()
    expect(runs[0].n).toBe(5)
  })

  it('coerciona n string → number', async () => {
    server.use(
      http.post(
        `${SUPABASE_URL}/rest/v1/rpc/get_runs_disponibles`,
        () => HttpResponse.json([{ run_id: 'run_20260516_2052', n: '471' }]),
      ),
    )
    const runs = await mod.getRunsDisponibles()
    expect(typeof runs[0].n).toBe('number')
    expect(runs[0].n).toBe(471)
  })

  it('devuelve array vacío en error de RPC', async () => {
    server.use(
      http.post(
        `${SUPABASE_URL}/rest/v1/rpc/get_runs_disponibles`,
        () => HttpResponse.json({ message: 'oops' }, { status: 500 }),
      ),
    )
    const runs = await mod.getRunsDisponibles()
    expect(runs).toEqual([])
  })
})
