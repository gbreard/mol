import { describe, it, expect, vi, beforeEach } from 'vitest'
import { NextRequest } from 'next/server'

// The search-semantic route creates supabase at module level.
// We mock the module and control rpc via the mock.
const mockRpc = vi.fn()

vi.mock('@supabase/supabase-js', () => {
  return {
    createClient: vi.fn(() => ({ rpc: mockRpc })),
  }
})

beforeEach(() => {
  vi.stubEnv('NEXT_PUBLIC_SUPABASE_URL', 'https://test.supabase.co')
  vi.stubEnv('NEXT_PUBLIC_SUPABASE_ANON_KEY', 'test-key')
  vi.clearAllMocks()
})

describe('OE-C3 — GET /api/occupations/search-semantic', () => {

  it('retorna resultados para "soldador"', async () => {
    mockRpc.mockResolvedValue({
      data: [
        { occupation_uri: 'http://esco/occ/1', occupation_label: 'soldador/soldadora', isco_code: '7212', text_similarity: 0.82 },
      ],
      error: null,
    })

    const { GET } = await import('@/app/api/occupations/search-semantic/route')
    const req = new NextRequest('http://localhost/api/occupations/search-semantic?q=soldador')
    const res = await GET(req)
    const body = await res.json()

    expect(res.status).toBe(200)
    expect(body.results.length).toBeGreaterThan(0)
    expect(body.results[0].label).toBe('soldador/soldadora')
  })

  it('retorna vacío para query corta', async () => {
    const { GET } = await import('@/app/api/occupations/search-semantic/route')
    const req = new NextRequest('http://localhost/api/occupations/search-semantic?q=a')
    const res = await GET(req)
    const body = await res.json()
    expect(body.results).toEqual([])
  })

  it('"contador" incluye "contable"', async () => {
    mockRpc.mockResolvedValue({
      data: [
        { occupation_uri: 'http://esco/occ/10', occupation_label: 'contable', isco_code: '2411', text_similarity: 0.38 },
      ],
      error: null,
    })

    const { GET } = await import('@/app/api/occupations/search-semantic/route')
    const req = new NextRequest('http://localhost/api/occupations/search-semantic?q=contador')
    const res = await GET(req)
    const body = await res.json()
    expect(body.results.map((r: any) => r.label)).toContain('contable')
  })

  it('retorna 500 si RPC falla', async () => {
    mockRpc.mockResolvedValue({ data: null, error: { message: 'timeout' } })

    const { GET } = await import('@/app/api/occupations/search-semantic/route')
    const req = new NextRequest('http://localhost/api/occupations/search-semantic?q=soldador')
    const res = await GET(req)
    expect(res.status).toBe(500)
  })
})
