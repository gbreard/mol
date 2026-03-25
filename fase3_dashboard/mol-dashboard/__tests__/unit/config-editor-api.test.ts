/**
 * Unit tests for /api/config-editor route (I2)
 * Tests: GET (read config override/local), PUT (save with version), auth, validation
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { NextRequest } from 'next/server'

// Mock auth
const mockRequireAdmin = vi.fn()
const mockIsAuthError = vi.fn()

vi.mock('@/lib/api-auth', () => ({
  requireAdmin: (...args: any[]) => mockRequireAdmin(...args),
  isAuthError: (...args: any[]) => mockIsAuthError(...args),
}))

async function importRoute() {
  vi.resetModules()
  return import('../../app/api/config-editor/route')
}

function makeGetRequest(key?: string): NextRequest {
  const url = key
    ? `http://localhost:3000/api/config-editor?key=${key}`
    : 'http://localhost:3000/api/config-editor'
  return new NextRequest(url, { method: 'GET' })
}

function makePutRequest(body: Record<string, unknown>): NextRequest {
  return new NextRequest('http://localhost:3000/api/config-editor', {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
}

const VALID_CONFIGS = [
  'matching_rules_business',
  'nlp_inference_rules',
  'sinonimos_argentinos_esco',
  'skills_rules',
  'oficios_arg',
  'nlp_titulo_limpieza',
]

describe('/api/config-editor', () => {
  const adminResult = {
    user: { id: 'admin-1', email: 'admin@oede.gob.ar', user_metadata: { role: 'admin' } },
    role: 'admin',
  }

  beforeEach(() => {
    vi.clearAllMocks()
    mockRequireAdmin.mockResolvedValue(adminResult)
    mockIsAuthError.mockReturnValue(false)
    process.env.SUPABASE_SERVICE_ROLE_KEY = 'test-service-role-key'
    process.env.NEXT_PUBLIC_SUPABASE_URL = 'https://test.supabase.co'
  })

  afterEach(() => {
    delete process.env.SUPABASE_SERVICE_ROLE_KEY
  })

  describe('GET - read config', () => {
    it('returns 401 when not authenticated', async () => {
      const errorResponse = new Response(JSON.stringify({ error: 'No autorizado' }), { status: 401 })
      mockRequireAdmin.mockResolvedValue(errorResponse)
      mockIsAuthError.mockReturnValue(true)

      const { GET } = await importRoute()
      const res = await GET(makeGetRequest('matching_rules_business'))
      expect(res.status).toBe(401)
    })

    it('returns 400 when key is missing', async () => {
      const { GET } = await importRoute()
      const res = await GET(makeGetRequest())
      const data = await res.json()

      expect(res.status).toBe(400)
      expect(data.error).toContain('Config inválido')
    })

    it('returns 400 for invalid config key', async () => {
      const { GET } = await importRoute()
      const res = await GET(makeGetRequest('nonexistent_config'))
      const data = await res.json()

      expect(res.status).toBe(400)
      expect(data.error).toContain('Config inválido')
      expect(data.error).toContain('matching_rules_business')
    })

    it('accepts all valid config keys', async () => {
      const { GET } = await importRoute()
      for (const key of VALID_CONFIGS) {
        const res = await GET(makeGetRequest(key))
        // Should not be 400 (might be override or local)
        expect(res.status).not.toBe(400)
      }
    })

    it('returns override data when exists in Supabase', async () => {
      const { GET } = await importRoute()
      const res = await GET(makeGetRequest('matching_rules_business'))
      const data = await res.json()

      expect(res.status).toBe(200)
      expect(data.config_key).toBe('matching_rules_business')
      expect(data.source).toBe('override')
      expect(data.data).toBeTruthy()
      expect(data.version).toBeGreaterThan(0)
      expect(data.changelog).toBeDefined()
    })

    it('returns local fallback when no override', async () => {
      // oficios_arg has no override in our MSW handlers (returns null)
      const { GET } = await importRoute()
      const res = await GET(makeGetRequest('oficios_arg'))
      const data = await res.json()

      expect(res.status).toBe(200)
      expect(data.config_key).toBe('oficios_arg')
      expect(data.source).toBe('local')
      expect(data.data).toBeNull()
      expect(data.version).toBe(0)
    })

    it('returns 500 when Supabase is not configured', async () => {
      process.env.NEXT_PUBLIC_SUPABASE_URL = ''
      delete process.env.SUPABASE_SERVICE_ROLE_KEY

      const { GET } = await importRoute()
      const res = await GET(makeGetRequest('matching_rules_business'))
      const data = await res.json()

      expect(res.status).toBe(500)
      expect(data.error).toContain('Supabase')
    })
  })

  describe('PUT - save config', () => {
    it('returns 401 when not authenticated', async () => {
      const errorResponse = new Response(JSON.stringify({ error: 'No autorizado' }), { status: 401 })
      mockRequireAdmin.mockResolvedValue(errorResponse)
      mockIsAuthError.mockReturnValue(true)

      const { PUT } = await importRoute()
      const res = await PUT(makePutRequest({
        config_key: 'matching_rules_business',
        data: { reglas_forzar_isco: {} },
        action_summary: 'test',
      }))
      expect(res.status).toBe(401)
    })

    it('returns 400 for invalid config_key', async () => {
      const { PUT } = await importRoute()
      const res = await PUT(makePutRequest({
        config_key: 'invalid_key',
        data: {},
        action_summary: 'test',
      }))
      const data = await res.json()

      expect(res.status).toBe(400)
      expect(data.error).toContain('config_key')
    })

    it('returns 400 when data is missing', async () => {
      const { PUT } = await importRoute()
      const res = await PUT(makePutRequest({
        config_key: 'matching_rules_business',
        action_summary: 'test',
      }))
      const data = await res.json()

      expect(res.status).toBe(400)
      expect(data.error).toContain('data')
    })

    it('saves config and returns new version', async () => {
      const { PUT } = await importRoute()
      const res = await PUT(makePutRequest({
        config_key: 'matching_rules_business',
        data: { reglas_forzar_isco: { R1: { nombre: 'Test' } } },
        action_summary: 'Test save',
      }))
      const data = await res.json()

      expect(res.status).toBe(200)
      expect(data.config_key).toBe('matching_rules_business')
      expect(data.version).toBeDefined()
      expect(data.updated_by).toBe('admin@oede.gob.ar')
      expect(data.message).toContain('Config guardado')
    })

    it('uses admin email from auth result', async () => {
      mockRequireAdmin.mockResolvedValue({
        user: { id: 'u2', email: 'cynthia@oede.gob.ar', user_metadata: { role: 'admin' } },
        role: 'admin',
      })

      const { PUT } = await importRoute()
      const res = await PUT(makePutRequest({
        config_key: 'nlp_inference_rules',
        data: { some: 'data' },
        action_summary: 'Editar regla',
      }))
      const data = await res.json()

      expect(res.status).toBe(200)
      expect(data.updated_by).toBe('cynthia@oede.gob.ar')
    })

    it('defaults action_summary when not provided', async () => {
      const { PUT } = await importRoute()
      const res = await PUT(makePutRequest({
        config_key: 'matching_rules_business',
        data: { reglas_forzar_isco: {} },
      }))

      // Should not fail — action_summary is optional
      expect(res.status).toBe(200)
    })

    it('returns 500 when Supabase is not configured', async () => {
      process.env.NEXT_PUBLIC_SUPABASE_URL = ''
      delete process.env.SUPABASE_SERVICE_ROLE_KEY

      const { PUT } = await importRoute()
      const res = await PUT(makePutRequest({
        config_key: 'matching_rules_business',
        data: { reglas_forzar_isco: {} },
        action_summary: 'test',
      }))
      const data = await res.json()

      expect(res.status).toBe(500)
      expect(data.error).toContain('Supabase')
    })
  })
})
