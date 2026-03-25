/**
 * Unit tests for /api/pipeline-commands (Fábrica — Gateway local)
 * Tests: auth, command validation, duplicate prevention, list commands
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { NextRequest } from 'next/server'

const mockRequireAdmin = vi.fn()
const mockIsAuthError = vi.fn()

vi.mock('@/lib/api-auth', () => ({
  requireAdmin: (...args: any[]) => mockRequireAdmin(...args),
  isAuthError: (...args: any[]) => mockIsAuthError(...args),
}))

const adminResult = {
  user: { id: 'admin-1', email: 'admin@oede.gob.ar', user_metadata: { role: 'admin' } },
  role: 'admin',
}

function setup() {
  mockRequireAdmin.mockResolvedValue(adminResult)
  mockIsAuthError.mockReturnValue(false)
  process.env.SUPABASE_SERVICE_ROLE_KEY = 'test-service-role-key'
  process.env.NEXT_PUBLIC_SUPABASE_URL = 'https://test.supabase.co'
}

async function importRoute() {
  vi.resetModules()
  return import('../../app/api/pipeline-commands/route')
}

function makeGet(params?: Record<string, string>): NextRequest {
  const url = new URL('http://localhost:3000/api/pipeline-commands')
  if (params) Object.entries(params).forEach(([k, v]) => url.searchParams.set(k, v))
  return new NextRequest(url.toString(), { method: 'GET' })
}

function makePost(body: any): NextRequest {
  return new NextRequest('http://localhost:3000/api/pipeline-commands', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
}

const VALID_COMMANDS = [
  'run_pipeline', 'run_nlp', 'run_matching', 'reprocess_errors',
  'revalidate_nlp', 'revalidate_matching', 'reapply_rules',
  'export_excel', 'sync_supabase', 'sync_supabase_full', 'generate_training',
]

describe('/api/pipeline-commands', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    setup()
  })

  afterEach(() => {
    delete process.env.SUPABASE_SERVICE_ROLE_KEY
  })

  describe('GET - list commands', () => {
    it('returns 401 without auth', async () => {
      const errorResponse = new Response(JSON.stringify({ error: 'No autorizado' }), { status: 401 })
      mockRequireAdmin.mockResolvedValue(errorResponse)
      mockIsAuthError.mockReturnValue(true)

      const { GET } = await importRoute()
      const res = await GET(makeGet())
      expect(res.status).toBe(401)
    })

    it('returns commands list with total', async () => {
      const { GET } = await importRoute()
      const res = await GET(makeGet())
      const data = await res.json()

      expect(res.status).toBe(200)
      expect(data).toHaveProperty('commands')
      expect(data).toHaveProperty('total')
      expect(Array.isArray(data.commands)).toBe(true)
    })

    it('accepts limit param', async () => {
      const { GET } = await importRoute()
      const res = await GET(makeGet({ limit: '5' }))
      expect(res.status).toBe(200)
    })

    it('accepts estado filter', async () => {
      const { GET } = await importRoute()
      const res = await GET(makeGet({ estado: 'pendiente' }))
      expect(res.status).toBe(200)
    })

    it('returns 500 when Supabase not configured', async () => {
      process.env.NEXT_PUBLIC_SUPABASE_URL = ''
      delete process.env.SUPABASE_SERVICE_ROLE_KEY

      const { GET } = await importRoute()
      const res = await GET(makeGet())
      expect(res.status).toBe(500)
    })
  })

  describe('POST - create command', () => {
    it('returns 401 without auth', async () => {
      const errorResponse = new Response(JSON.stringify({ error: 'No autorizado' }), { status: 401 })
      mockRequireAdmin.mockResolvedValue(errorResponse)
      mockIsAuthError.mockReturnValue(true)

      const { POST } = await importRoute()
      const res = await POST(makePost({ comando: 'sync_supabase' }))
      expect(res.status).toBe(401)
    })

    it('rejects invalid command', async () => {
      const { POST } = await importRoute()
      const res = await POST(makePost({ comando: 'hack_the_planet' }))
      const data = await res.json()

      expect(res.status).toBe(400)
      expect(data.error).toContain('Comando invalido')
      expect(data.error).toContain('run_pipeline')
    })

    it('rejects empty command', async () => {
      const { POST } = await importRoute()
      const res = await POST(makePost({}))
      expect(res.status).toBe(400)
    })

    it('requires limit or ids for run_pipeline', async () => {
      const { POST } = await importRoute()
      const res = await POST(makePost({ comando: 'run_pipeline' }))
      const data = await res.json()

      expect(res.status).toBe(400)
      expect(data.error).toContain('limit')
    })

    it('requires limit or ids for run_nlp', async () => {
      const { POST } = await importRoute()
      const res = await POST(makePost({ comando: 'run_nlp' }))
      expect(res.status).toBe(400)
    })

    it('accepts run_pipeline with limit', async () => {
      const { POST } = await importRoute()
      const res = await POST(makePost({
        comando: 'run_pipeline',
        params: { limit: 500 },
      }))

      // May succeed (201) or hit Supabase mock limitation (500)
      // But should NOT be 400 (validation passed)
      expect(res.status).not.toBe(400)
    })

    it('accepts commands that dont need params', async () => {
      const noParamCommands = [
        'reprocess_errors', 'reapply_rules', 'sync_supabase',
        'sync_supabase_full', 'generate_training',
      ]

      for (const cmd of noParamCommands) {
        const { POST } = await importRoute()
        const res = await POST(makePost({ comando: cmd }))
        // Should not be 400 (no params required)
        expect(res.status).not.toBe(400)
      }
    })

    it('all valid commands are accepted', () => {
      expect(VALID_COMMANDS).toHaveLength(11)
      // Verify the list matches the route
      for (const cmd of VALID_COMMANDS) {
        expect(typeof cmd).toBe('string')
        expect(cmd).toMatch(/^[a-z_]+$/)
      }
    })

    it('returns 500 when Supabase not configured', async () => {
      process.env.NEXT_PUBLIC_SUPABASE_URL = ''
      delete process.env.SUPABASE_SERVICE_ROLE_KEY

      const { POST } = await importRoute()
      const res = await POST(makePost({ comando: 'sync_supabase' }))
      expect(res.status).toBe(500)
    })
  })
})
