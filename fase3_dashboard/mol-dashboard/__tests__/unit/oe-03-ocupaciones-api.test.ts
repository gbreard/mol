import { describe, it, expect, vi, beforeEach } from 'vitest'

// Mock Supabase client
const mockSelect = vi.fn()
const mockEq = vi.fn()
const mockNeq = vi.fn()
const mockMaybeSingle = vi.fn()
const mockRpc = vi.fn()
const mockExecute = vi.fn()
const mockFrom = vi.fn()

vi.mock('@supabase/supabase-js', () => ({
  createClient: () => ({
    from: mockFrom,
    rpc: mockRpc,
  }),
}))

// Import after mocking
import { GET } from '@/app/api/casos/[id]/ocupaciones/route'
import { NextRequest } from 'next/server'

function makeRequest(id: string) {
  const url = `http://localhost:3000/api/casos/${id}/ocupaciones`
  const req = new NextRequest(url)
  return { request: req, params: Promise.resolve({ id }) }
}

// Setup Supabase env
beforeEach(() => {
  vi.stubEnv('NEXT_PUBLIC_SUPABASE_URL', 'https://test.supabase.co')
  vi.stubEnv('SUPABASE_SERVICE_ROLE_KEY', 'test-key')
  vi.clearAllMocks()
})

describe('OE-03 — GET /api/casos/[id]/ocupaciones', () => {

  it('retorna 404 si el caso no existe', async () => {
    mockFrom.mockReturnValue({
      select: () => ({
        eq: () => ({
          maybeSingle: () => Promise.resolve({ data: null, error: null }),
        }),
      }),
    })

    const { request, params } = makeRequest('nonexistent-id')
    const res = await GET(request, { params })
    const body = await res.json()

    expect(res.status).toBe(404)
    expect(body.error).toBe('Caso no encontrado')
  })

  it('retorna sin_skills si la persona no tiene skills', async () => {
    // Mock caso exists
    mockFrom.mockImplementation((table: string) => {
      if (table === 'casos') {
        return {
          select: () => ({
            eq: () => ({
              maybeSingle: () => Promise.resolve({
                data: { id: 'caso-1', persona_id: 'persona-1' },
                error: null,
              }),
            }),
          }),
        }
      }
      if (table === 'perfil_skills') {
        return {
          select: () => ({
            eq: () => ({
              neq: () => Promise.resolve({ data: [], error: null }),
            }),
          }),
        }
      }
      return { select: () => ({ eq: () => ({ maybeSingle: () => Promise.resolve({ data: null, error: null }) }) }) }
    })

    const { request, params } = makeRequest('caso-1')
    const res = await GET(request, { params })
    const body = await res.json()

    expect(res.status).toBe(200)
    expect(body.mensaje).toBe('sin_skills')
    expect(body.ocupaciones).toEqual([])
    expect(body.total_skills_perfil).toBe(0)
  })

  it('retorna ocupaciones cuando la persona tiene skills', async () => {
    const mockSkills = [
      { skill_uri: 'http://esco/skill/abc', perfiles: { persona_id: 'p1' } },
      { skill_uri: 'http://esco/skill/def', perfiles: { persona_id: 'p1' } },
    ]

    const mockOcupaciones = [
      { occupation_uri: 'http://esco/occ/1', occupation_label: 'Contable', isco_code: '2411', best_similarity: 0.88, skills_matched: 2 },
      { occupation_uri: 'http://esco/occ/2', occupation_label: 'Auditor', isco_code: '4312', best_similarity: 0.75, skills_matched: 1 },
      { occupation_uri: 'http://esco/occ/3', occupation_label: 'Analista', isco_code: '2413', best_similarity: 0.72, skills_matched: 1 },
    ]

    mockFrom.mockImplementation((table: string) => {
      if (table === 'casos') {
        return {
          select: () => ({
            eq: () => ({
              maybeSingle: () => Promise.resolve({
                data: { id: 'caso-1', persona_id: 'persona-1' },
                error: null,
              }),
            }),
          }),
        }
      }
      if (table === 'perfil_skills') {
        return {
          select: () => ({
            eq: () => ({
              neq: () => Promise.resolve({ data: mockSkills, error: null }),
            }),
          }),
        }
      }
      return { select: () => ({ eq: () => ({ maybeSingle: () => Promise.resolve({ data: null, error: null }) }) }) }
    })

    mockRpc.mockResolvedValue({ data: mockOcupaciones, error: null })

    const { request, params } = makeRequest('caso-1')
    const res = await GET(request, { params })
    const body = await res.json()

    expect(res.status).toBe(200)
    expect(body.total_skills_perfil).toBe(2)
    expect(body.ocupaciones).toHaveLength(3)
    expect(body.ocupaciones[0]).toEqual({
      uri: 'http://esco/occ/1',
      label: 'Contable',
      isco_code: '2411',
      afinidad: 88,
      skills_matched: 2,
    })
    // Verify RPC was called with correct params
    expect(mockRpc).toHaveBeenCalledWith('match_occupations_by_skills', {
      skill_uris: ['http://esco/skill/abc', 'http://esco/skill/def'],
      similarity_threshold: 0.55,
      max_results: 10,
    })
  })

  it('retorna 500 si la RPC falla', async () => {
    mockFrom.mockImplementation((table: string) => {
      if (table === 'casos') {
        return {
          select: () => ({
            eq: () => ({
              maybeSingle: () => Promise.resolve({
                data: { id: 'caso-1', persona_id: 'persona-1' },
                error: null,
              }),
            }),
          }),
        }
      }
      if (table === 'perfil_skills') {
        return {
          select: () => ({
            eq: () => ({
              neq: () => Promise.resolve({
                data: [{ skill_uri: 'http://esco/skill/abc', perfiles: {} }],
                error: null,
              }),
            }),
          }),
        }
      }
      return { select: () => ({ eq: () => ({ maybeSingle: () => Promise.resolve({ data: null, error: null }) }) }) }
    })

    mockRpc.mockResolvedValue({ data: null, error: { message: 'timeout' } })

    const { request, params } = makeRequest('caso-1')
    const res = await GET(request, { params })
    const body = await res.json()

    expect(res.status).toBe(500)
    expect(body.error).toContain('timeout')
  })
})
