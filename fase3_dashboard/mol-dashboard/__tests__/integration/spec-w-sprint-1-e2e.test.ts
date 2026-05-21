/**
 * Tests integrales end-to-end del Sprint 1 SPEC W Etapa 1 (sub-tarea D.4).
 *
 * Verifican la composición real de los endpoints POST/DELETE/GET de
 * audit-actions con getOfertasValidacion (lib/supabase.ts) sobre una BD
 * simulada en memoria. Cada test corre un flujo completo y valida que el
 * estado final sea consistente entre ofertas_dashboard y audit_actions.
 *
 * Refs:
 *   docs/specs/spec_w/SPEC_W_etapa1_visualizador.md (F4, F5, F6, F7, F8)
 *   docs/specs/spec_w/DECISIONES_PRE_SPRINT_1.md (Op 3, D8)
 *   migrations/024_spec_w_audit_actions.sql
 *   migrations/024_1_spec_w_performance_filtros.sql
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { NextRequest } from 'next/server'

// ============================================================================
// In-memory DB simulator
// ============================================================================

type Oferta = {
  id_oferta: string
  estado_revision: string | null
  datos_incompletos: boolean
  fecha_publicacion: string
  portal?: string
  // resto de columnas usadas por VALIDACION_SELECT (con defaults harmless)
  [key: string]: unknown
}

type AuditAction = {
  id: number
  id_oferta: string
  validador: string
  timestamp: string
  action_type: string
  target_type: string | null
  target_id: string | null
  target_value: string | null
  note: string | null
  run_id: string | null
  matching_version: string | null
  source: string
}

type Db = {
  ofertas: Map<string, Oferta>
  auditActions: AuditAction[]
  nextActionId: number
}

const db: Db = {
  ofertas: new Map(),
  auditActions: [],
  nextActionId: 1,
}

function resetDb() {
  db.ofertas.clear()
  db.auditActions.length = 0
  db.nextActionId = 1
}

function seedOferta(o: Partial<Oferta> & { id_oferta: string }) {
  const oferta: Oferta = {
    id_oferta: o.id_oferta,
    estado_revision: o.estado_revision ?? null,
    datos_incompletos: o.datos_incompletos ?? false,
    fecha_publicacion: o.fecha_publicacion ?? '2026-05-01',
    portal: o.portal ?? 'bumeran',
    ...o,
  }
  db.ofertas.set(o.id_oferta, oferta)
  return oferta
}

// ----------------------------------------------------------------------------
// Builder con filtros y terminadores (thenable)
// ----------------------------------------------------------------------------

type FilterOp =
  | { kind: 'eq'; col: string; val: unknown }
  | { kind: 'is'; col: string; val: unknown }
  | { kind: 'in'; col: string; vals: unknown[] }
  | { kind: 'lt'; col: string; val: number }
  | { kind: 'gte'; col: string; val: number }
  | { kind: 'like'; col: string; pattern: string }
  | { kind: 'or'; expr: string }
  | { kind: 'not_in'; col: string; vals: unknown[] }

function applyFilters(rows: Record<string, unknown>[], filters: FilterOp[]): Record<string, unknown>[] {
  return rows.filter((row) =>
    filters.every((f) => {
      switch (f.kind) {
        case 'eq':
          return row[f.col] === f.val
        case 'is':
          return row[f.col] === f.val
        case 'in':
          return f.vals.includes(row[f.col])
        case 'lt':
          return typeof row[f.col] === 'number' && (row[f.col] as number) < f.val
        case 'gte':
          return typeof row[f.col] === 'number' && (row[f.col] as number) >= f.val
        case 'like':
          // %X% naive contains
          if (typeof row[f.col] !== 'string') return false
          const pat = f.pattern.replace(/%/g, '')
          return (row[f.col] as string).toLowerCase().includes(pat.toLowerCase())
        case 'or':
          // No usado en los tests — devolvemos true (no-op)
          return true
        case 'not_in':
          return !f.vals.includes(row[f.col])
      }
    }),
  )
}

class QueryBuilder implements PromiseLike<unknown> {
  private op: 'select' | 'insert' | 'update' | 'delete' = 'select'
  private filters: FilterOp[] = []
  private insertPayload: Record<string, unknown> | null = null
  private updatePayload: Record<string, unknown> | null = null
  private selectCols = '*'
  private withCount = false
  private orderField: { col: string; ascending: boolean } | null = null

  constructor(private table: string) {}

  // ---------- mutators ----------
  select(cols?: string, opts?: { count?: 'exact' }) {
    this.selectCols = cols ?? '*'
    if (opts?.count === 'exact') this.withCount = true
    return this
  }
  insert(payload: Record<string, unknown>) {
    this.op = 'insert'
    this.insertPayload = payload
    return this
  }
  update(payload: Record<string, unknown>) {
    this.op = 'update'
    this.updatePayload = payload
    return this
  }
  delete() {
    this.op = 'delete'
    return this
  }

  // ---------- filters ----------
  eq(col: string, val: unknown) {
    this.filters.push({ kind: 'eq', col, val })
    return this
  }
  is(col: string, val: unknown) {
    this.filters.push({ kind: 'is', col, val })
    return this
  }
  in(col: string, vals: unknown[]) {
    this.filters.push({ kind: 'in', col, vals })
    return this
  }
  lt(col: string, val: number) {
    this.filters.push({ kind: 'lt', col, val })
    return this
  }
  gte(col: string, val: number) {
    this.filters.push({ kind: 'gte', col, val })
    return this
  }
  like(col: string, pattern: string) {
    this.filters.push({ kind: 'like', col, pattern })
    return this
  }
  or(expr: string) {
    this.filters.push({ kind: 'or', expr })
    return this
  }
  not(col: string, op: string, val: unknown) {
    if (op === 'in') {
      // val es string '(a,b,c)' o array
      const vals = typeof val === 'string'
        ? val.replace(/[()]/g, '').split(',').map((s) => s.trim())
        : (val as unknown[])
      this.filters.push({ kind: 'not_in', col, vals })
    }
    return this
  }
  order(col: string, opts: { ascending: boolean }) {
    this.orderField = { col, ascending: opts.ascending }
    return this
  }

  // ---------- terminators ----------
  async range(start: number, end: number) {
    return this.runSelect(start, end - start + 1)
  }
  async maybeSingle() {
    const res = await this.runSelect()
    return { data: res.data[0] ?? null, error: res.error }
  }
  async single() {
    if (this.op === 'insert') {
      return this.runInsert()
    }
    const res = await this.runSelect()
    if (!res.data[0]) return { data: null, error: { message: 'No rows returned' } }
    return { data: res.data[0], error: res.error }
  }

  // ---------- thenable fallback ----------
  then<TResult1 = unknown, TResult2 = never>(
    onfulfilled?: ((value: unknown) => TResult1 | PromiseLike<TResult1>) | null,
    onrejected?: ((reason: unknown) => TResult2 | PromiseLike<TResult2>) | null,
  ): PromiseLike<TResult1 | TResult2> {
    let result: Promise<unknown>
    if (this.op === 'update') {
      result = Promise.resolve(this.runUpdate())
    } else {
      // select default (sin range)
      result = Promise.resolve(this.runSelect())
    }
    return result.then(onfulfilled, onrejected)
  }

  // ---------- runners ----------
  private getRowsAsRecords(): Record<string, unknown>[] {
    if (this.table === 'ofertas_dashboard') {
      return [...db.ofertas.values()] as unknown as Record<string, unknown>[]
    }
    if (this.table === 'audit_actions') {
      return [...db.auditActions] as unknown as Record<string, unknown>[]
    }
    return []
  }

  private async runSelect(offset = 0, limit = Infinity) {
    let rows = this.getRowsAsRecords()
    rows = applyFilters(rows, this.filters)
    if (this.orderField) {
      const { col, ascending } = this.orderField
      rows.sort((a, b) => {
        const av = a[col]
        const bv = b[col]
        if (av == null && bv == null) return 0
        if (av == null) return 1
        if (bv == null) return -1
        if (av < bv) return ascending ? -1 : 1
        if (av > bv) return ascending ? 1 : -1
        return 0
      })
    }
    const total = rows.length
    const sliced = rows.slice(offset, offset + (limit === Infinity ? total : limit))
    return { data: sliced, count: this.withCount ? total : null, error: null }
  }

  private async runInsert() {
    if (this.table === 'audit_actions' && this.insertPayload) {
      const newAction: AuditAction = {
        id: db.nextActionId++,
        timestamp: new Date().toISOString(),
        id_oferta: String(this.insertPayload.id_oferta),
        validador: String(this.insertPayload.validador),
        action_type: String(this.insertPayload.action_type),
        target_type: (this.insertPayload.target_type as string | null) ?? null,
        target_id: (this.insertPayload.target_id as string | null) ?? null,
        target_value: (this.insertPayload.target_value as string | null) ?? null,
        note: (this.insertPayload.note as string | null) ?? null,
        run_id: (this.insertPayload.run_id as string | null) ?? null,
        matching_version: (this.insertPayload.matching_version as string | null) ?? null,
        source: (this.insertPayload.source as string) ?? 'human',
      }
      db.auditActions.push(newAction)
      return { data: { id: newAction.id }, error: null }
    }
    return { data: null, error: { message: 'insert no soportado en tabla ' + this.table } }
  }

  private async runUpdate() {
    if (this.table === 'ofertas_dashboard' && this.updatePayload) {
      const eqIdFilter = this.filters.find((f) => f.kind === 'eq' && f.col === 'id_oferta') as
        | { kind: 'eq'; col: string; val: string }
        | undefined
      if (!eqIdFilter) return { error: { message: 'update sin id_oferta filter' } }
      const oferta = db.ofertas.get(eqIdFilter.val)
      if (!oferta) return { error: { message: 'oferta no existe' } }
      Object.assign(oferta, this.updatePayload)
      return { error: null }
    }
    return { error: { message: 'update no soportado en tabla ' + this.table } }
  }
}

// ============================================================================
// Mocks: @supabase/supabase-js + lib/api-auth
// ============================================================================

vi.mock('@supabase/supabase-js', () => ({
  createClient: () => ({
    from: (table: string) => new QueryBuilder(table),
    rpc: vi.fn(),
  }),
}))

const adminAuth = {
  user: { id: 'admin-1', email: 'cyn@oede.gob.ar', user_metadata: { role: 'admin' } },
  role: 'admin',
}

vi.mock('@/lib/api-auth', () => ({
  requireAdmin: vi.fn(async () => adminAuth),
  isAuthError: vi.fn(() => false),
}))

// ============================================================================
// Helpers para invocar endpoints frescos en cada test
// ============================================================================

async function importPostRoute() {
  vi.resetModules()
  const mod = await import('../../app/api/audit-actions/route')
  mod._resetSupabaseAdminForTests?.()
  return mod
}

async function importDeleteRoute() {
  vi.resetModules()
  const mod = await import('../../app/api/audit-actions/[id]/route')
  mod._resetSupabaseAdminForTests?.()
  return mod
}

async function importGetRoute() {
  vi.resetModules()
  const mod = await import('../../app/api/oferta/[id]/audit-history/route')
  mod._resetSupabaseAdminForTests?.()
  return mod
}

async function importSupabase() {
  vi.resetModules()
  return import('../../lib/supabase')
}

function makePostReq(body: Record<string, unknown>) {
  return new NextRequest('http://localhost:3000/api/audit-actions', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
}

function makeDeleteReq(id: number) {
  return new NextRequest(`http://localhost:3000/api/audit-actions/${id}`, {
    method: 'DELETE',
  })
}

function makeGetReq(idOferta: string) {
  return new NextRequest(
    `http://localhost:3000/api/oferta/${idOferta}/audit-history`,
    { method: 'GET' },
  )
}

// ============================================================================
// Setup
// ============================================================================

beforeEach(() => {
  resetDb()
  process.env.SUPABASE_SERVICE_ROLE_KEY = 'test-key'
  process.env.NEXT_PUBLIC_SUPABASE_URL = 'https://test.supabase.co'
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY = 'test-anon-key'
})

// ============================================================================
// Tests
// ============================================================================

describe('SPEC W Sprint 1 — Integración end-to-end', () => {
  // --------------------------------------------------------------------------
  // Test 1: Flujo marcar revisada
  // --------------------------------------------------------------------------
  it('1. Marcar revisada: POST persiste audit_action + estado_revision + GET history la devuelve', async () => {
    seedOferta({ id_oferta: 'OF_001' })

    const { POST } = await importPostRoute()
    const postRes = await POST(
      makePostReq({
        id_oferta: 'OF_001',
        action_type: 'mark_revised',
        target_type: 'oferta_global',
      }),
    )
    expect(postRes.status).toBe(201)
    const postBody = await postRes.json()
    expect(postBody.success).toBe(true)
    expect(postBody.updated_estado_revision).toBe('revisada')

    // Estado en ofertas_dashboard actualizado
    expect(db.ofertas.get('OF_001')!.estado_revision).toBe('revisada')

    // audit_actions tiene la entrada
    expect(db.auditActions).toHaveLength(1)
    expect(db.auditActions[0].action_type).toBe('mark_revised')
    expect(db.auditActions[0].validador).toBe('cyn@oede.gob.ar')

    // GET history devuelve la acción
    const { GET } = await importGetRoute()
    const getRes = await GET(makeGetReq('OF_001'), {
      params: Promise.resolve({ id: 'OF_001' }),
    })
    expect(getRes.status).toBe(200)
    const getBody = await getRes.json()
    expect(getBody.total).toBe(1)
    expect(getBody.actions[0].action_type).toBe('mark_revised')
  })

  // --------------------------------------------------------------------------
  // Test 2: Flujo desmarcar revisada
  // --------------------------------------------------------------------------
  it('2. Desmarcar revisada: DELETE inserta unmark_revised y deja estado_revision=NULL', async () => {
    seedOferta({ id_oferta: 'OF_002' })

    const { POST } = await importPostRoute()
    const postRes = await POST(
      makePostReq({
        id_oferta: 'OF_002',
        action_type: 'mark_revised',
        target_type: 'oferta_global',
      }),
    )
    const { action_id } = await postRes.json()

    expect(db.ofertas.get('OF_002')!.estado_revision).toBe('revisada')
    expect(db.auditActions).toHaveLength(1)

    const { DELETE } = await importDeleteRoute()
    const delRes = await DELETE(makeDeleteReq(action_id), {
      params: Promise.resolve({ id: String(action_id) }),
    })
    expect(delRes.status).toBe(200)
    const delBody = await delRes.json()
    expect(delBody.reverted).toBe(true)

    // Acción original sigue + nueva inversa
    expect(db.auditActions).toHaveLength(2)
    expect(db.auditActions[1].action_type).toBe('unmark_revised')

    // estado_revision queda NULL
    expect(db.ofertas.get('OF_002')!.estado_revision).toBeNull()
  })

  // --------------------------------------------------------------------------
  // Test 3: Marcar mal extraída con nota
  // --------------------------------------------------------------------------
  it('3. Marcar mal extraída con nota: nota persiste en audit_actions', async () => {
    seedOferta({ id_oferta: 'OF_003' })

    const { POST } = await importPostRoute()
    const res = await POST(
      makePostReq({
        id_oferta: 'OF_003',
        action_type: 'mark_total_failure',
        target_type: 'oferta_global',
        note: 'Sistema interpretó "oficial" como militar — es operario.',
      }),
    )
    expect(res.status).toBe(201)
    const body = await res.json()
    expect(body.updated_estado_revision).toBe('mal_extraida_total')

    expect(db.ofertas.get('OF_003')!.estado_revision).toBe('mal_extraida_total')
    expect(db.auditActions).toHaveLength(1)
    expect(db.auditActions[0].action_type).toBe('mark_total_failure')
    expect(db.auditActions[0].note).toBe(
      'Sistema interpretó "oficial" como militar — es operario.',
    )
  })

  // --------------------------------------------------------------------------
  // Test 4: Rechazo de reversión granular
  // --------------------------------------------------------------------------
  it('4. DELETE sobre mark_task_incorrect devuelve 400 action_not_revertible', async () => {
    seedOferta({ id_oferta: 'OF_004' })

    const { POST } = await importPostRoute()
    const postRes = await POST(
      makePostReq({
        id_oferta: 'OF_004',
        action_type: 'mark_task_incorrect',
        target_type: 'task',
        target_value: 'Atender clientes',
      }),
    )
    const { action_id } = await postRes.json()
    expect(db.auditActions).toHaveLength(1)

    const { DELETE } = await importDeleteRoute()
    const delRes = await DELETE(makeDeleteReq(action_id), {
      params: Promise.resolve({ id: String(action_id) }),
    })
    expect(delRes.status).toBe(400)
    const body = await delRes.json()
    expect(body.error).toBe('action_not_revertible')
    expect(body.action_type).toBe('mark_task_incorrect')

    // Nada nuevo insertado, estado de oferta intacto
    expect(db.auditActions).toHaveLength(1)
    expect(db.ofertas.get('OF_004')!.estado_revision).toBeNull()
  })

  // --------------------------------------------------------------------------
  // Test 5: Filtro solo_datos_incompletos
  // --------------------------------------------------------------------------
  it('5. soloDatosIncompletos devuelve solo ofertas con datos_incompletos=true', async () => {
    seedOferta({ id_oferta: 'OF_A', datos_incompletos: true })
    seedOferta({ id_oferta: 'OF_B', datos_incompletos: false })
    seedOferta({ id_oferta: 'OF_C', datos_incompletos: true })

    const mod = await importSupabase()
    const res = await mod.getOfertasValidacion({ soloDatosIncompletos: 'true' })

    expect(res.total).toBe(2)
    const ids = res.ofertas.map((o) => o.id_oferta).sort()
    expect(ids).toEqual(['OF_A', 'OF_C'])

    const resBaseline = await mod.getOfertasValidacion({})
    expect(resBaseline.total).toBe(3)
  })

  // --------------------------------------------------------------------------
  // Test 6: Filtro solo_correccion_manual
  // --------------------------------------------------------------------------
  it('6. soloCorreccionManual filtra a ofertas con audit_action de corrección humana', async () => {
    seedOferta({ id_oferta: 'OF_X' })
    seedOferta({ id_oferta: 'OF_Y' })
    seedOferta({ id_oferta: 'OF_Z' })

    // OF_X: corrección humana (mark_task_incorrect) → debe aparecer
    const { POST } = await importPostRoute()
    await POST(
      makePostReq({
        id_oferta: 'OF_X',
        action_type: 'mark_task_incorrect',
        target_type: 'task',
        target_value: 'Tarea incorrecta',
      }),
    )

    // OF_Y: solo mark_revised (no es corrección de contenido) → NO debe aparecer
    await POST(
      makePostReq({
        id_oferta: 'OF_Y',
        action_type: 'mark_revised',
        target_type: 'oferta_global',
      }),
    )

    // OF_Z: sin acciones → NO debe aparecer

    const mod = await importSupabase()
    const res = await mod.getOfertasValidacion({ soloCorreccionManual: 'true' })

    const ids = res.ofertas.map((o) => o.id_oferta).sort()
    expect(ids).toEqual(['OF_X'])
    expect(res.total).toBe(1)
  })

  // --------------------------------------------------------------------------
  // Test 7: Filtro estado_revision='revisada'
  // --------------------------------------------------------------------------
  it('7. estadoRevision=revisada incluye marcada, NO la pendiente; viceversa para pendiente', async () => {
    seedOferta({ id_oferta: 'OF_R1' })
    seedOferta({ id_oferta: 'OF_R2' })

    // Marcar OF_R1 como revisada
    const { POST } = await importPostRoute()
    await POST(
      makePostReq({
        id_oferta: 'OF_R1',
        action_type: 'mark_revised',
        target_type: 'oferta_global',
      }),
    )

    const mod = await importSupabase()

    const revisadas = await mod.getOfertasValidacion({ estadoRevision: 'revisada' })
    expect(revisadas.ofertas.map((o) => o.id_oferta)).toEqual(['OF_R1'])
    expect(revisadas.total).toBe(1)

    const pendientes = await mod.getOfertasValidacion({ estadoRevision: 'pendiente' })
    expect(pendientes.ofertas.map((o) => o.id_oferta)).toEqual(['OF_R2'])
    expect(pendientes.total).toBe(1)
  })

  // --------------------------------------------------------------------------
  // Test 8: Combinación AND (estado_revision=pendiente + soloDatosIncompletos)
  // --------------------------------------------------------------------------
  it('8. AND: estadoRevision=pendiente + soloDatosIncompletos filtra por ambos', async () => {
    // Matriz de 4 ofertas que cubren las combinaciones (estado_revision × datos_incompletos):
    //   OF_AA: revisada, incompleta     → falla por estado
    //   OF_AB: revisada, completa       → falla por estado
    //   OF_BA: pendiente, incompleta    → PASA
    //   OF_BB: pendiente, completa      → falla por datos_incompletos
    seedOferta({ id_oferta: 'OF_AA', datos_incompletos: true })
    seedOferta({ id_oferta: 'OF_AB', datos_incompletos: false })
    seedOferta({ id_oferta: 'OF_BA', datos_incompletos: true })
    seedOferta({ id_oferta: 'OF_BB', datos_incompletos: false })

    // Marcar OF_AA y OF_AB como revisadas
    const { POST } = await importPostRoute()
    await POST(
      makePostReq({ id_oferta: 'OF_AA', action_type: 'mark_revised', target_type: 'oferta_global' }),
    )
    await POST(
      makePostReq({ id_oferta: 'OF_AB', action_type: 'mark_revised', target_type: 'oferta_global' }),
    )

    const mod = await importSupabase()
    const res = await mod.getOfertasValidacion({
      estadoRevision: 'pendiente',
      soloDatosIncompletos: 'true',
    })

    expect(res.ofertas.map((o) => o.id_oferta)).toEqual(['OF_BA'])
    expect(res.total).toBe(1)
  })
})
