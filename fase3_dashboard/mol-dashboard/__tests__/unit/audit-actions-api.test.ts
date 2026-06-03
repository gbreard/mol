/**
 * Unit tests para los endpoints de audit-actions (SPEC W Etapa 1).
 *
 * Refs:
 *   docs/specs/spec_w/SPEC_W_etapa1_visualizador.md sección 3.2
 *   docs/specs/spec_w/DECISIONES_PRE_SPRINT_1.md (Op 3 para DELETE)
 *   migrations/024_spec_w_audit_actions.sql
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { NextRequest } from 'next/server'

// --- Mocks ---
const mockRequireAdmin = vi.fn()
const mockIsAuthError = vi.fn()

vi.mock('@/lib/api-auth', () => ({
  requireAdmin: (...args: unknown[]) => mockRequireAdmin(...args),
  isAuthError: (...args: unknown[]) => mockIsAuthError(...args),
}))

// Estado controlado para el cliente Supabase mockeado.
type FromResponse = {
  // payload final que devuelve la cadena cuando termina con maybeSingle/single
  result?: { data: unknown; error: { message: string } | null }
  // payload final cuando termina con .order() — array
  orderResult?: { data: unknown[]; error: { message: string } | null }
  // payload final cuando termina con .eq() (update sin select)
  updateResult?: { error: { message: string } | null }
}

const fromResponses = new Map<string, FromResponse[]>()

function pushResponse(table: string, response: FromResponse) {
  if (!fromResponses.has(table)) fromResponses.set(table, [])
  fromResponses.get(table)!.push(response)
}

function consumeResponse(table: string): FromResponse {
  const list = fromResponses.get(table)
  if (!list || list.length === 0) {
    throw new Error(`No mock response configured for table ${table}`)
  }
  return list.shift()!
}

vi.mock('@supabase/supabase-js', () => {
  return {
    createClient: () => ({
      from: (table: string) => {
        const response = consumeResponse(table)
        const builder: Record<string, unknown> = {}
        builder.select = (_cols?: string) => builder
        builder.insert = (_payload: unknown) => builder
        builder.update = (_payload: unknown) => builder
        builder.delete = () => builder
        builder.eq = (_col: string, _val: unknown) => {
          // Si la cadena fue update().eq() y no hay .select() después,
          // termina acá. Devolvemos thenable.
          if (response.updateResult !== undefined) {
            return Promise.resolve(response.updateResult)
          }
          return builder
        }
        builder.order = (_col: string, _opts: unknown) => {
          if (response.orderResult !== undefined) {
            return Promise.resolve(response.orderResult)
          }
          return builder
        }
        builder.maybeSingle = () => Promise.resolve(response.result!)
        builder.single = () => Promise.resolve(response.result!)
        return builder
      },
    }),
  }
})

const adminAuth = {
  user: { id: 'admin-1', email: 'cyn@oede.gob.ar', user_metadata: { role: 'admin' } },
  role: 'admin',
}

beforeEach(() => {
  vi.clearAllMocks()
  fromResponses.clear()
  mockRequireAdmin.mockResolvedValue(adminAuth)
  mockIsAuthError.mockReturnValue(false)
  process.env.SUPABASE_SERVICE_ROLE_KEY = 'test-key'
  process.env.NEXT_PUBLIC_SUPABASE_URL = 'https://test.supabase.co'
})

async function importPostRoute() {
  vi.resetModules()
  return import('../../app/api/audit-actions/route')
}

async function importDeleteRoute() {
  vi.resetModules()
  return import('../../app/api/audit-actions/[id]/route')
}

async function importGetRoute() {
  vi.resetModules()
  return import('../../app/api/oferta/[id]/audit-history/route')
}

function makePostReq(body: Record<string, unknown>) {
  return new NextRequest('http://localhost:3000/api/audit-actions', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
}

function makeDeleteReq() {
  return new NextRequest('http://localhost:3000/api/audit-actions/123', {
    method: 'DELETE',
  })
}

function makeGetReq() {
  return new NextRequest('http://localhost:3000/api/oferta/TEST_001/audit-history', {
    method: 'GET',
  })
}

// =============================================================================
// POST /api/audit-actions
// =============================================================================
describe('POST /api/audit-actions', () => {
  it('payload válido devuelve 201 + action_id', async () => {
    pushResponse('ofertas_dashboard', { result: { data: { id_oferta: 'TEST_001' }, error: null } })
    pushResponse('audit_actions', { result: { data: { id: 99 }, error: null } })

    const { POST } = await importPostRoute()
    const res = await POST(
      makePostReq({
        id_oferta: 'TEST_001',
        action_type: 'add_suggested_task',
        target_type: 'task',
        target_value: 'Atender clientes',
      }),
    )
    expect(res.status).toBe(201)
    const body = await res.json()
    expect(body.success).toBe(true)
    expect(body.action_id).toBe(99)
  })

  it('id_oferta inexistente devuelve 404', async () => {
    pushResponse('ofertas_dashboard', { result: { data: null, error: null } })

    const { POST } = await importPostRoute()
    const res = await POST(
      makePostReq({
        id_oferta: 'NO_EXISTE',
        action_type: 'mark_revised',
        target_type: 'oferta_global',
      }),
    )
    expect(res.status).toBe(404)
    const body = await res.json()
    expect(body.error).toContain('no existe')
  })

  it('action_type inválido devuelve 400', async () => {
    const { POST } = await importPostRoute()
    const res = await POST(
      makePostReq({
        id_oferta: 'TEST_001',
        action_type: 'invent_something',
      }),
    )
    expect(res.status).toBe(400)
    const body = await res.json()
    expect(body.error).toContain('action_type inválido')
  })

  it("mark_revised actualiza estado_revision='revisada'", async () => {
    pushResponse('ofertas_dashboard', { result: { data: { id_oferta: 'TEST_001' }, error: null } })
    pushResponse('audit_actions', { result: { data: { id: 100 }, error: null } })
    pushResponse('ofertas_dashboard', { updateResult: { error: null } })

    const { POST } = await importPostRoute()
    const res = await POST(
      makePostReq({
        id_oferta: 'TEST_001',
        action_type: 'mark_revised',
        target_type: 'oferta_global',
      }),
    )
    expect(res.status).toBe(201)
    const body = await res.json()
    expect(body.updated_estado_revision).toBe('revisada')
  })

  it("mark_total_failure actualiza estado_revision='mal_extraida_total'", async () => {
    pushResponse('ofertas_dashboard', { result: { data: { id_oferta: 'TEST_001' }, error: null } })
    pushResponse('audit_actions', { result: { data: { id: 101 }, error: null } })
    pushResponse('ofertas_dashboard', { updateResult: { error: null } })

    const { POST } = await importPostRoute()
    const res = await POST(
      makePostReq({
        id_oferta: 'TEST_001',
        action_type: 'mark_total_failure',
        target_type: 'oferta_global',
      }),
    )
    expect(res.status).toBe(201)
    const body = await res.json()
    expect(body.updated_estado_revision).toBe('mal_extraida_total')
  })

  it('unmark_revised setea estado_revision=NULL', async () => {
    pushResponse('ofertas_dashboard', { result: { data: { id_oferta: 'TEST_001' }, error: null } })
    pushResponse('audit_actions', { result: { data: { id: 102 }, error: null } })
    pushResponse('ofertas_dashboard', { updateResult: { error: null } })

    const { POST } = await importPostRoute()
    const res = await POST(
      makePostReq({
        id_oferta: 'TEST_001',
        action_type: 'unmark_revised',
        target_type: 'oferta_global',
      }),
    )
    expect(res.status).toBe(201)
    const body = await res.json()
    expect(body.updated_estado_revision).toBeNull()
  })

  it('mark_task_incorrect requiere target_value o target_id', async () => {
    const { POST } = await importPostRoute()
    const res = await POST(
      makePostReq({
        id_oferta: 'TEST_001',
        action_type: 'mark_task_incorrect',
        target_type: 'task',
      }),
    )
    expect(res.status).toBe(400)
    const body = await res.json()
    expect(body.error).toMatch(/target_value o target_id/)
  })
})

// =============================================================================
// DELETE /api/audit-actions/:id  (Op 3)
// =============================================================================
describe('DELETE /api/audit-actions/:id', () => {
  it('mark_revised: inserta unmark_revised + setea estado_revision=NULL', async () => {
    pushResponse('audit_actions', {
      result: {
        data: {
          id: 123,
          id_oferta: 'TEST_001',
          action_type: 'mark_revised',
          validador: 'cyn@oede.gob.ar',
          target_type: 'oferta_global',
        },
        error: null,
      },
    })
    pushResponse('audit_actions', { result: { data: { id: 124 }, error: null } })
    pushResponse('ofertas_dashboard', { updateResult: { error: null } })

    const { DELETE } = await importDeleteRoute()
    const res = await DELETE(makeDeleteReq(), { params: Promise.resolve({ id: '123' }) })
    expect(res.status).toBe(200)
    const body = await res.json()
    expect(body.reverted).toBe(true)
    expect(body.action_id).toBe(124)
  })

  it('mark_total_failure: inserta unmark_total_failure + setea estado_revision=NULL', async () => {
    pushResponse('audit_actions', {
      result: {
        data: {
          id: 125,
          id_oferta: 'TEST_002',
          action_type: 'mark_total_failure',
          validador: 'cyn@oede.gob.ar',
          target_type: 'oferta_global',
        },
        error: null,
      },
    })
    pushResponse('audit_actions', { result: { data: { id: 126 }, error: null } })
    pushResponse('ofertas_dashboard', { updateResult: { error: null } })

    const { DELETE } = await importDeleteRoute()
    const res = await DELETE(makeDeleteReq(), { params: Promise.resolve({ id: '125' }) })
    expect(res.status).toBe(200)
    const body = await res.json()
    expect(body.reverted).toBe(true)
    expect(body.action_id).toBe(126)
  })

  it('mark_task_incorrect: 400 action_not_revertible', async () => {
    pushResponse('audit_actions', {
      result: {
        data: {
          id: 127,
          id_oferta: 'TEST_001',
          action_type: 'mark_task_incorrect',
          validador: 'cyn@oede.gob.ar',
          target_type: 'task',
        },
        error: null,
      },
    })

    const { DELETE } = await importDeleteRoute()
    const res = await DELETE(makeDeleteReq(), { params: Promise.resolve({ id: '127' }) })
    expect(res.status).toBe(400)
    const body = await res.json()
    expect(body.error).toBe('action_not_revertible')
    expect(body.action_type).toBe('mark_task_incorrect')
  })

  it('id inexistente: 404', async () => {
    pushResponse('audit_actions', { result: { data: null, error: null } })

    const { DELETE } = await importDeleteRoute()
    const res = await DELETE(makeDeleteReq(), { params: Promise.resolve({ id: '9999' }) })
    expect(res.status).toBe(404)
    const body = await res.json()
    expect(body.error).toContain('no existe')
  })
})

// =============================================================================
// GET /api/oferta/:id/audit-history
// =============================================================================
describe('GET /api/oferta/:id/audit-history', () => {
  it('devuelve acciones ordenadas DESC', async () => {
    const sampleActions = [
      { id: 3, id_oferta: 'TEST_001', action_type: 'mark_revised', timestamp: '2026-05-19T10:00:00Z' },
      { id: 2, id_oferta: 'TEST_001', action_type: 'mark_task_incorrect', timestamp: '2026-05-18T10:00:00Z' },
      { id: 1, id_oferta: 'TEST_001', action_type: 'add_suggested_task', timestamp: '2026-05-17T10:00:00Z' },
    ]
    pushResponse('audit_actions', { orderResult: { data: sampleActions, error: null } })

    const { GET } = await importGetRoute()
    const res = await GET(makeGetReq(), { params: Promise.resolve({ id: 'TEST_001' }) })
    expect(res.status).toBe(200)
    const body = await res.json()
    expect(body.actions).toHaveLength(3)
    expect(body.total).toBe(3)
    expect(body.actions[0].id).toBe(3)
  })

  it('para oferta sin acciones devuelve array vacío', async () => {
    pushResponse('audit_actions', { orderResult: { data: [], error: null } })

    const { GET } = await importGetRoute()
    const res = await GET(makeGetReq(), { params: Promise.resolve({ id: 'TEST_VACIA' }) })
    expect(res.status).toBe(200)
    const body = await res.json()
    expect(body.actions).toEqual([])
    expect(body.total).toBe(0)
  })
})
