/**
 * Unit tests para los filtros nuevos de getOfertasValidacion
 * (SPEC W F7/F8): soloDatosIncompletos, soloCorreccionManual, estadoRevision.
 *
 * Refs:
 *   docs/specs/spec_w/SPEC_W_etapa1_visualizador.md sección 2.1
 *   docs/specs/spec_w/DECISIONES_PRE_SPRINT_1.md (D8)
 *   migrations/024_1_spec_w_performance_filtros.sql
 *
 * Estrategia: mockear @supabase/supabase-js con un builder que graba las
 * llamadas a .eq/.is/.in para verificar que los WHERE correctos fueron
 * aplicados a la query.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'

type Call = { method: string; args: unknown[] }

let queryCalls: Call[]
let auditActionsRows: { id_oferta: string }[]
let mainQueryRows: Record<string, unknown>[]
let mainQueryCount: number
let mainQueryError: { message: string } | null

function makeChainableQuery(table: string) {
  const builder: Record<string, (...args: unknown[]) => unknown> = {}
  const record = (method: string) => (...args: unknown[]) => {
    queryCalls.push({ method: `${table}.${method}`, args })
    return builder
  }
  builder.select = record('select')
  builder.eq = record('eq')
  builder.is = record('is')
  builder.in = record('in')
  builder.lt = record('lt')
  builder.gte = record('gte')
  builder.like = record('like')
  builder.or = record('or')
  builder.not = record('not')
  builder.order = record('order')

  if (table === 'audit_actions') {
    // termina con thenable que resuelve con data
    builder.then = (cb: (v: unknown) => unknown) =>
      Promise.resolve({ data: auditActionsRows, error: null }).then(cb)
  } else {
    // ofertas_dashboard: termina con .range() que devuelve {data, count, error}
    builder.range = (...args: unknown[]) => {
      queryCalls.push({ method: `${table}.range`, args })
      return Promise.resolve({
        data: mainQueryRows,
        count: mainQueryCount,
        error: mainQueryError,
      })
    }
  }
  return builder
}

vi.mock('@supabase/supabase-js', () => ({
  createClient: () => ({
    from: (table: string) => makeChainableQuery(table),
    rpc: vi.fn(),
  }),
}))

beforeEach(() => {
  queryCalls = []
  auditActionsRows = []
  mainQueryRows = []
  mainQueryCount = 0
  mainQueryError = null
  process.env.NEXT_PUBLIC_SUPABASE_URL = 'https://test.supabase.co'
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY = 'test-anon-key'
})

async function importSupabase() {
  vi.resetModules()
  return import('../../lib/supabase')
}

function getCall(method: string): Call | undefined {
  return queryCalls.find((c) => c.method === method)
}

function getAllCalls(method: string): Call[] {
  return queryCalls.filter((c) => c.method === method)
}

// =============================================================================
// soloDatosIncompletos
// =============================================================================
describe('getOfertasValidacion — filtro soloDatosIncompletos (F7)', () => {
  it("aplica WHERE datos_incompletos=true cuando soloDatosIncompletos='true'", async () => {
    const mod = await importSupabase()
    await mod.getOfertasValidacion({ soloDatosIncompletos: 'true' })

    const eqCalls = getAllCalls('ofertas_dashboard.eq')
    const incompletoCall = eqCalls.find((c) => c.args[0] === 'datos_incompletos')
    expect(incompletoCall).toBeDefined()
    expect(incompletoCall!.args[1]).toBe(true)
  })

  it("NO aplica filtro cuando soloDatosIncompletos='' o undefined", async () => {
    const mod = await importSupabase()
    await mod.getOfertasValidacion({})

    const eqCalls = getAllCalls('ofertas_dashboard.eq')
    const incompletoCall = eqCalls.find((c) => c.args[0] === 'datos_incompletos')
    expect(incompletoCall).toBeUndefined()
  })
})

// =============================================================================
// soloCorreccionManual
// =============================================================================
describe('getOfertasValidacion — filtro soloCorreccionManual (F8)', () => {
  it("usa audit_actions para construir lista IN cuando soloCorreccionManual='true'", async () => {
    auditActionsRows = [{ id_oferta: 'OFERTA_A' }, { id_oferta: 'OFERTA_B' }]
    const mod = await importSupabase()
    await mod.getOfertasValidacion({ soloCorreccionManual: 'true' })

    // Verifica que consultó audit_actions con los filtros correctos
    const auditSelect = getCall('audit_actions.select')
    expect(auditSelect).toBeDefined()
    const auditEq = getAllCalls('audit_actions.eq').find((c) => c.args[0] === 'source')
    expect(auditEq!.args[1]).toBe('human')
    const auditNot = getCall('audit_actions.not')
    expect(auditNot).toBeDefined()
    expect(auditNot!.args[0]).toBe('action_type')

    // Verifica que la query principal usó .in con esos id_ofertas
    const inCall = getAllCalls('ofertas_dashboard.in').find((c) => c.args[0] === 'id_oferta')
    expect(inCall).toBeDefined()
    expect(inCall!.args[1]).toEqual(['OFERTA_A', 'OFERTA_B'])
  })

  it("devuelve vacío sin tocar ofertas_dashboard cuando no hay correcciones", async () => {
    auditActionsRows = []
    const mod = await importSupabase()
    const res = await mod.getOfertasValidacion({ soloCorreccionManual: 'true' })

    expect(res).toEqual({ ofertas: [], total: 0 })
    // No debe haber ejecutado .range() en ofertas_dashboard
    const rangeCalls = getAllCalls('ofertas_dashboard.range')
    expect(rangeCalls).toHaveLength(0)
  })

  it("NO consulta audit_actions cuando soloCorreccionManual está vacío", async () => {
    const mod = await importSupabase()
    await mod.getOfertasValidacion({})

    const auditSelect = getCall('audit_actions.select')
    expect(auditSelect).toBeUndefined()
  })
})

// =============================================================================
// estadoRevision
// =============================================================================
describe('getOfertasValidacion — filtro estadoRevision', () => {
  it("'revisada' => WHERE estado_revision='revisada'", async () => {
    const mod = await importSupabase()
    await mod.getOfertasValidacion({ estadoRevision: 'revisada' })

    const eqCalls = getAllCalls('ofertas_dashboard.eq')
    const estadoCall = eqCalls.find((c) => c.args[0] === 'estado_revision')
    expect(estadoCall).toBeDefined()
    expect(estadoCall!.args[1]).toBe('revisada')
  })

  it("'mal_extraida_total' => WHERE estado_revision='mal_extraida_total'", async () => {
    const mod = await importSupabase()
    await mod.getOfertasValidacion({ estadoRevision: 'mal_extraida_total' })

    const eqCalls = getAllCalls('ofertas_dashboard.eq')
    const estadoCall = eqCalls.find((c) => c.args[0] === 'estado_revision')
    expect(estadoCall!.args[1]).toBe('mal_extraida_total')
  })

  it("'pendiente' => WHERE estado_revision IS NULL (usa .is)", async () => {
    const mod = await importSupabase()
    await mod.getOfertasValidacion({ estadoRevision: 'pendiente' })

    const isCalls = getAllCalls('ofertas_dashboard.is')
    const estadoCall = isCalls.find((c) => c.args[0] === 'estado_revision')
    expect(estadoCall).toBeDefined()
    expect(estadoCall!.args[1]).toBeNull()
  })

  it("'' / undefined: no filtra por estado_revision", async () => {
    const mod = await importSupabase()
    await mod.getOfertasValidacion({})

    const eqCalls = getAllCalls('ofertas_dashboard.eq')
    const isCalls = getAllCalls('ofertas_dashboard.is')
    expect(eqCalls.find((c) => c.args[0] === 'estado_revision')).toBeUndefined()
    expect(isCalls.find((c) => c.args[0] === 'estado_revision')).toBeUndefined()
  })
})

// =============================================================================
// Combinaciones (AND)
// =============================================================================
describe('getOfertasValidacion — combinaciones (AND)', () => {
  it("estadoRevision='revisada' + portal='computrabajo' aplica ambos", async () => {
    const mod = await importSupabase()
    await mod.getOfertasValidacion({
      estadoRevision: 'revisada',
      portal: 'computrabajo',
    })

    const eqCalls = getAllCalls('ofertas_dashboard.eq')
    expect(eqCalls.find((c) => c.args[0] === 'estado_revision' && c.args[1] === 'revisada'))
      .toBeDefined()
    expect(eqCalls.find((c) => c.args[0] === 'portal' && c.args[1] === 'computrabajo'))
      .toBeDefined()
  })

  it("soloDatosIncompletos + runId combinan", async () => {
    const mod = await importSupabase()
    await mod.getOfertasValidacion({
      soloDatosIncompletos: 'true',
      runId: 'RUN_ABC',
    })

    const eqCalls = getAllCalls('ofertas_dashboard.eq')
    expect(eqCalls.find((c) => c.args[0] === 'datos_incompletos' && c.args[1] === true))
      .toBeDefined()
    expect(eqCalls.find((c) => c.args[0] === 'run_id' && c.args[1] === 'RUN_ABC'))
      .toBeDefined()
  })
})

// =============================================================================
// Regresión sobre filtros existentes
// =============================================================================
describe('getOfertasValidacion — regresión filtros existentes', () => {
  it("portal sigue aplicando .eq('portal', X)", async () => {
    const mod = await importSupabase()
    await mod.getOfertasValidacion({ portal: 'bumeran' })

    const eqCalls = getAllCalls('ofertas_dashboard.eq')
    expect(eqCalls.find((c) => c.args[0] === 'portal' && c.args[1] === 'bumeran'))
      .toBeDefined()
  })

  it("estadoValidacion='pendiente' sigue funcionando vía .is('validacion_humana', null)", async () => {
    const mod = await importSupabase()
    await mod.getOfertasValidacion({ estadoValidacion: 'pendiente' })

    const isCalls = getAllCalls('ofertas_dashboard.is')
    expect(isCalls.find((c) => c.args[0] === 'validacion_humana' && c.args[1] === null))
      .toBeDefined()
  })
})

// =============================================================================
// getOfertasConCorreccionManual helper aislado
// =============================================================================
describe('getOfertasConCorreccionManual', () => {
  it("devuelve ids únicos cuando audit_actions tiene duplicados", async () => {
    auditActionsRows = [
      { id_oferta: 'A' },
      { id_oferta: 'A' },
      { id_oferta: 'B' },
    ]
    const mod = await importSupabase()
    const ids = await mod.getOfertasConCorreccionManual()
    expect(ids.sort()).toEqual(['A', 'B'])
  })

  it("devuelve array vacío si no hay correcciones", async () => {
    auditActionsRows = []
    const mod = await importSupabase()
    const ids = await mod.getOfertasConCorreccionManual()
    expect(ids).toEqual([])
  })
})
