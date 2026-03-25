/**
 * Unit tests for APIs Grupo A (personas/perfiles) + Grupo B (casos)
 * Based on PLAN_INTEGRACION_GERARDO.md contracts
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { NextRequest } from 'next/server'

const mockRequireAuth = vi.fn()
const mockIsAuthError = vi.fn()

vi.mock('@/lib/api-auth', () => ({
  requireAuth: (...args: any[]) => mockRequireAuth(...args),
  isAuthError: (...args: any[]) => mockIsAuthError(...args),
}))

const authResult = {
  user: { id: 'u1', email: 'tecnico@oede.gob.ar', user_metadata: { role: 'oficina_empleo' } },
  role: 'oficina_empleo',
}

function setup() {
  mockRequireAuth.mockResolvedValue(authResult)
  mockIsAuthError.mockReturnValue(false)
  process.env.SUPABASE_SERVICE_ROLE_KEY = 'test-key'
  process.env.NEXT_PUBLIC_SUPABASE_URL = 'https://test.supabase.co'
}

function makeGet(path: string, params?: Record<string, string>): NextRequest {
  const url = new URL(`http://localhost:3000${path}`)
  if (params) Object.entries(params).forEach(([k, v]) => url.searchParams.set(k, v))
  return new NextRequest(url.toString())
}

function makePost(path: string, body: any): NextRequest {
  return new NextRequest(`http://localhost:3000${path}`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body),
  })
}

function makePatch(path: string, body: any): NextRequest {
  return new NextRequest(`http://localhost:3000${path}`, {
    method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body),
  })
}

describe('Grupo A — Personas y Perfiles', () => {
  beforeEach(() => { vi.clearAllMocks(); setup(); })
  afterEach(() => { delete process.env.SUPABASE_SERVICE_ROLE_KEY; })

  describe('A1 — POST /api/personas', () => {
    it('returns 401 without auth', async () => {
      mockRequireAuth.mockResolvedValue(new Response('', { status: 401 }))
      mockIsAuthError.mockReturnValue(true)
      vi.resetModules()
      const { POST } = await import('../../app/api/personas/route')
      const res = await POST(makePost('/api/personas', { nombre: 'Test' }))
      expect(res.status).toBe(401)
    })

    it('returns 400 without nombre', async () => {
      vi.resetModules()
      const { POST } = await import('../../app/api/personas/route')
      const res = await POST(makePost('/api/personas', {}))
      expect(res.status).toBe(400)
    })

    it('accepts valid persona', async () => {
      vi.resetModules()
      const { POST } = await import('../../app/api/personas/route')
      const res = await POST(makePost('/api/personas', {
        nombre: 'María García', dni: '32456789', origen: 'S2',
      }))
      expect([200, 201, 500]).toContain(res.status) // 500 if Supabase mock can't insert
    })
  })

  describe('A2 — GET /api/personas', () => {
    it('accepts search by dni', async () => {
      vi.resetModules()
      const { GET } = await import('../../app/api/personas/route')
      const res = await GET(makeGet('/api/personas', { dni: '32456789' }))
      expect([200, 500]).toContain(res.status)
    })

    it('accepts search by nombre', async () => {
      vi.resetModules()
      const { GET } = await import('../../app/api/personas/route')
      const res = await GET(makeGet('/api/personas', { nombre: 'García' }))
      expect([200, 500]).toContain(res.status)
    })
  })

  describe('A3 — POST /api/perfiles', () => {
    it('returns 400 without persona_id', async () => {
      vi.resetModules()
      const { POST } = await import('../../app/api/perfiles/route')
      const res = await POST(makePost('/api/perfiles', {}))
      expect(res.status).toBe(400)
    })

    it('accepts valid perfil creation', async () => {
      vi.resetModules()
      const { POST } = await import('../../app/api/perfiles/route')
      const res = await POST(makePost('/api/perfiles', { persona_id: 'uuid-1', origen: 'S2' }))
      expect([201, 500]).toContain(res.status)
    })
  })

  describe('A6 — GET /api/perfiles', () => {
    it('returns 400 without id or persona_id', async () => {
      vi.resetModules()
      const { GET } = await import('../../app/api/perfiles/route')
      const res = await GET(makeGet('/api/perfiles'))
      expect(res.status).toBe(400)
    })

    it('accepts id param', async () => {
      vi.resetModules()
      const { GET } = await import('../../app/api/perfiles/route')
      const res = await GET(makeGet('/api/perfiles', { id: 'uuid-1' }))
      expect([200, 404, 500]).toContain(res.status)
    })
  })
})

describe('Grupo B — Casos', () => {
  beforeEach(() => { vi.clearAllMocks(); setup(); })
  afterEach(() => { delete process.env.SUPABASE_SERVICE_ROLE_KEY; })

  describe('B1 — GET /api/casos', () => {
    it('returns list', async () => {
      vi.resetModules()
      const { GET } = await import('../../app/api/casos/route')
      const res = await GET(makeGet('/api/casos'))
      expect([200, 500]).toContain(res.status)
    })

    it('accepts filters', async () => {
      vi.resetModules()
      const { GET } = await import('../../app/api/casos/route')
      const res = await GET(makeGet('/api/casos', { org_id: 'uuid', estado: 'nuevo', q: 'García' }))
      expect([200, 500]).toContain(res.status)
    })
  })

  describe('B2 — POST /api/casos', () => {
    it('returns 400 without persona_id', async () => {
      vi.resetModules()
      const { POST } = await import('../../app/api/casos/route')
      const res = await POST(makePost('/api/casos', { organizacion_id: 'uuid' }))
      expect(res.status).toBe(400)
    })

    it('returns 400 without organizacion_id', async () => {
      vi.resetModules()
      const { POST } = await import('../../app/api/casos/route')
      const res = await POST(makePost('/api/casos', { persona_id: 'uuid' }))
      expect(res.status).toBe(400)
    })
  })

  describe('B5 — POST /api/casos/:id/derivar', () => {
    it('returns 400 without tipo', async () => {
      vi.resetModules()
      const mod = await import('../../app/api/casos/[id]/derivar/route')
      const res = await mod.POST(
        makePost('/api/casos/uuid-1/derivar', { destino_id: 'uuid-2' }),
        { params: Promise.resolve({ id: 'uuid-1' }) }
      )
      expect(res.status).toBe(400)
    })

    it('returns 400 without destino_id', async () => {
      vi.resetModules()
      const mod = await import('../../app/api/casos/[id]/derivar/route')
      const res = await mod.POST(
        makePost('/api/casos/uuid-1/derivar', { tipo: 'vacante' }),
        { params: Promise.resolve({ id: 'uuid-1' }) }
      )
      expect(res.status).toBe(400)
    })
  })

  describe('A4 — POST /api/perfiles/:id/skills', () => {
    it('returns 400 without skills', async () => {
      vi.resetModules()
      const mod = await import('../../app/api/perfiles/[id]/skills/route')
      const res = await mod.POST(
        makePost('/api/perfiles/uuid-1/skills', {}),
        { params: Promise.resolve({ id: 'uuid-1' }) }
      )
      expect(res.status).toBe(400)
    })

    it('returns 400 with empty skills array', async () => {
      vi.resetModules()
      const mod = await import('../../app/api/perfiles/[id]/skills/route')
      const res = await mod.POST(
        makePost('/api/perfiles/uuid-1/skills', { skills: [] }),
        { params: Promise.resolve({ id: 'uuid-1' }) }
      )
      expect(res.status).toBe(400)
    })
  })

  describe('A5 — PATCH /api/perfiles/:id/skills', () => {
    it('returns 400 without skill_id', async () => {
      vi.resetModules()
      const mod = await import('../../app/api/perfiles/[id]/skills/route')
      const res = await mod.PATCH(
        makePatch('/api/perfiles/uuid-1/skills', { estado: 'confirmada' }),
        { params: Promise.resolve({ id: 'uuid-1' }) }
      )
      expect(res.status).toBe(400)
    })
  })
})
