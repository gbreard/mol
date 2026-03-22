/**
 * Unit tests for /api/config-editor/preview route (I2)
 * Tests: POST (preview impacto), GET (sugerencias), auth, validation
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { NextRequest } from 'next/server'

// Mock auth — bypass real Supabase SSR auth
const mockRequireAdmin = vi.fn()
const mockIsAuthError = vi.fn()

vi.mock('@/lib/api-auth', () => ({
  requireAdmin: (...args: any[]) => mockRequireAdmin(...args),
  isAuthError: (...args: any[]) => mockIsAuthError(...args),
}))

// Dynamic import after mocks
async function importRoute() {
  vi.resetModules()
  return import('../../app/api/config-editor/preview/route')
}

function makePostRequest(body: Record<string, unknown>): NextRequest {
  return new NextRequest('http://localhost:3000/api/config-editor/preview', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
}

function makeGetRequest(): NextRequest {
  return new NextRequest('http://localhost:3000/api/config-editor/preview', {
    method: 'GET',
  })
}

describe('/api/config-editor/preview', () => {
  const adminResult = {
    user: { id: 'admin-1', email: 'admin@oede.gob.ar', user_metadata: { role: 'admin' } },
    role: 'admin',
  }

  beforeEach(() => {
    vi.clearAllMocks()
    // Default: admin authenticated
    mockRequireAdmin.mockResolvedValue(adminResult)
    mockIsAuthError.mockReturnValue(false)
    // Set env for Supabase admin client
    process.env.SUPABASE_SERVICE_ROLE_KEY = 'test-service-role-key'
    process.env.NEXT_PUBLIC_SUPABASE_URL = 'https://test.supabase.co'
  })

  afterEach(() => {
    delete process.env.SUPABASE_SERVICE_ROLE_KEY
  })

  describe('POST - preview impacto', () => {
    it('returns 401 when not authenticated', async () => {
      const errorResponse = new Response(JSON.stringify({ error: 'No autorizado' }), { status: 401 })
      mockRequireAdmin.mockResolvedValue(errorResponse)
      mockIsAuthError.mockReturnValue(true)

      const { POST } = await importRoute()
      const res = await POST(makePostRequest({ titulo_contiene: 'gerente', forzar_isco: '1221' }))
      expect(res.status).toBe(401)
    })

    it('returns 400 when forzar_isco is missing', async () => {
      const { POST } = await importRoute()
      const res = await POST(makePostRequest({ titulo_contiene: 'gerente' }))
      const data = await res.json()

      expect(res.status).toBe(400)
      expect(data.error).toContain('forzar_isco')
    })

    it('returns 400 when both titulo fields are missing', async () => {
      const { POST } = await importRoute()
      const res = await POST(makePostRequest({ forzar_isco: '1221' }))
      const data = await res.json()

      expect(res.status).toBe(400)
      expect(data.error).toContain('titulo_contiene')
    })

    it('calls RPC with titulo_contiene and returns impact data', async () => {
      const { POST } = await importRoute()
      const res = await POST(makePostRequest({
        titulo_contiene: 'gerente de ventas',
        forzar_isco: '1221',
      }))
      const data = await res.json()

      expect(res.status).toBe(200)
      expect(data).toHaveProperty('total_afectadas')
      expect(data).toHaveProperty('cambiarian')
      expect(data).toHaveProperty('ya_correctas')
      expect(data).toHaveProperty('distribucion_isco_actual')
      expect(data).toHaveProperty('ejemplos')
      expect(typeof data.total_afectadas).toBe('number')
    })

    it('calls RPC with titulo_contiene_alguno for multi-keyword', async () => {
      const { POST } = await importRoute()
      const res = await POST(makePostRequest({
        titulo_contiene_alguno: ['gerente', 'director'],
        forzar_isco: '1221',
      }))
      const data = await res.json()

      expect(res.status).toBe(200)
      expect(data).toHaveProperty('total_afectadas')
    })

    it('returns 500 when Supabase is not configured', async () => {
      process.env.NEXT_PUBLIC_SUPABASE_URL = ''
      delete process.env.SUPABASE_SERVICE_ROLE_KEY

      const { POST } = await importRoute()
      const res = await POST(makePostRequest({
        titulo_contiene: 'gerente',
        forzar_isco: '1221',
      }))
      const data = await res.json()

      expect(res.status).toBe(500)
      expect(data.error).toContain('Supabase')
    })
  })

  describe('GET - sugerencias', () => {
    it('returns 401 when not authenticated', async () => {
      const errorResponse = new Response(JSON.stringify({ error: 'No autorizado' }), { status: 401 })
      mockRequireAdmin.mockResolvedValue(errorResponse)
      mockIsAuthError.mockReturnValue(true)

      const { GET } = await importRoute()
      const res = await GET(makeGetRequest())
      expect(res.status).toBe(401)
    })

    it('returns suggestions array', async () => {
      const { GET } = await importRoute()
      const res = await GET(makeGetRequest())
      const data = await res.json()

      expect(res.status).toBe(200)
      expect(Array.isArray(data)).toBe(true)
    })

    it('suggestions have expected fields', async () => {
      const { GET } = await importRoute()
      const res = await GET(makeGetRequest())
      const data = await res.json()

      if (data.length > 0) {
        const suggestion = data[0]
        expect(suggestion).toHaveProperty('patron_titulo')
        expect(suggestion).toHaveProperty('isco_sugerido')
        expect(suggestion).toHaveProperty('ofertas_afectadas')
        expect(suggestion).toHaveProperty('tipo_sugerencia')
      }
    })

    it('returns 500 when Supabase is not configured', async () => {
      process.env.NEXT_PUBLIC_SUPABASE_URL = ''
      delete process.env.SUPABASE_SERVICE_ROLE_KEY

      const { GET } = await importRoute()
      const res = await GET(makeGetRequest())
      const data = await res.json()

      expect(res.status).toBe(500)
      expect(data.error).toContain('Supabase')
    })
  })
})
