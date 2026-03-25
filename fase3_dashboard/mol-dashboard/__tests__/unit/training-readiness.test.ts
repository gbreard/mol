/**
 * Unit tests for /api/training-readiness (I3)
 * Tests: auth, response structure, readiness assessment logic
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { NextRequest } from 'next/server'

const mockRequireAdmin = vi.fn()
const mockIsAuthError = vi.fn()

vi.mock('@/lib/api-auth', () => ({
  requireAdmin: (...args: any[]) => mockRequireAdmin(...args),
  isAuthError: (...args: any[]) => mockIsAuthError(...args),
}))

async function importRoute() {
  vi.resetModules()
  return import('../../app/api/training-readiness/route')
}

function makeGetRequest(): NextRequest {
  return new NextRequest('http://localhost:3000/api/training-readiness', { method: 'GET' })
}

describe('/api/training-readiness', () => {
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

  it('returns 401 when not authenticated', async () => {
    const errorResponse = new Response(JSON.stringify({ error: 'No autorizado' }), { status: 401 })
    mockRequireAdmin.mockResolvedValue(errorResponse)
    mockIsAuthError.mockReturnValue(true)

    const { GET } = await importRoute()
    const res = await GET(makeGetRequest())
    expect(res.status).toBe(401)
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

  it('returns readiness data with expected structure', async () => {
    const { GET } = await importRoute()
    const res = await GET(makeGetRequest())
    const data = await res.json()

    expect(res.status).toBe(200)
    expect(data).toHaveProperty('total_pairs')
    expect(data).toHaveProperty('distinct_isco')
    expect(data).toHaveProperty('groups_covered')
    expect(data).toHaveProperty('readiness')
    expect(data).toHaveProperty('suggestions')
    expect(data).toHaveProperty('distribution')
    expect(data).toHaveProperty('autores')
  })

  it('readiness has checks array with ok/label/detail', async () => {
    const { GET } = await importRoute()
    const res = await GET(makeGetRequest())
    const data = await res.json()

    expect(data.readiness).toHaveProperty('ready')
    expect(data.readiness).toHaveProperty('level')
    expect(data.readiness).toHaveProperty('checks')
    expect(Array.isArray(data.readiness.checks)).toBe(true)

    if (data.readiness.checks.length > 0) {
      const check = data.readiness.checks[0]
      expect(check).toHaveProperty('label')
      expect(check).toHaveProperty('ok')
      expect(check).toHaveProperty('detail')
    }
  })

  it('distribution has by_group and top_isco arrays', async () => {
    const { GET } = await importRoute()
    const res = await GET(makeGetRequest())
    const data = await res.json()

    expect(Array.isArray(data.distribution.by_group)).toBe(true)
    expect(Array.isArray(data.distribution.top_isco)).toBe(true)
    expect(Array.isArray(data.distribution.gaps)).toBe(true)
  })

  it('suggestions is an array of strings', async () => {
    const { GET } = await importRoute()
    const res = await GET(makeGetRequest())
    const data = await res.json()

    expect(Array.isArray(data.suggestions)).toBe(true)
    for (const s of data.suggestions) {
      expect(typeof s).toBe('string')
    }
  })
})
