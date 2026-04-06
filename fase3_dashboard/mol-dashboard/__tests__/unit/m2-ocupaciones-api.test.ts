import { describe, it, expect, vi, beforeEach } from 'vitest'

const mockFrom = vi.fn()
const mockRpc = vi.fn()

vi.mock('@supabase/supabase-js', () => ({
  createClient: () => ({
    from: mockFrom,
    rpc: mockRpc,
  }),
}))

import { GET as getOcupaciones } from '@/app/api/perfiles/[id]/ocupaciones/route'
import { GET as getGap } from '@/app/api/perfiles/[id]/gap/route'
import { NextRequest } from 'next/server'

beforeEach(() => {
  vi.stubEnv('NEXT_PUBLIC_SUPABASE_URL', 'https://test.supabase.co')
  vi.stubEnv('SUPABASE_SERVICE_ROLE_KEY', 'test-key')
  vi.clearAllMocks()
})

function makeReq(id: string, path: string, query = '') {
  const url = `http://localhost:3000/api/perfiles/${id}/${path}${query}`
  return { request: new NextRequest(url), params: Promise.resolve({ id }) }
}

describe('GET /api/perfiles/[id]/ocupaciones', () => {
  it('retorna sin_skills si perfil no tiene skills', async () => {
    mockFrom.mockReturnValue({
      select: () => ({
        eq: () => ({
          neq: () => Promise.resolve({ data: [], error: null }),
        }),
      }),
    })

    const { request, params } = makeReq('p1', 'ocupaciones')
    const res = await getOcupaciones(request, { params })
    const data = await res.json()
    expect(data.mensaje).toBe('sin_skills')
    expect(data.ocupaciones).toEqual([])
  })

  it('llama RPC y retorna ocupaciones mapeadas', async () => {
    mockFrom.mockReturnValue({
      select: () => ({
        eq: () => ({
          neq: () => Promise.resolve({
            data: [{ skill_uri: 'uri1' }, { skill_uri: 'uri2' }],
            error: null,
          }),
        }),
      }),
    })

    mockRpc.mockResolvedValue({
      data: [
        { occupation_uri: 'occ1', occupation_label: 'Albañil', isco_code: '7112', best_similarity: 0.87, skills_matched: 5 },
        { occupation_uri: 'occ2', occupation_label: 'Pintor', isco_code: '7131', best_similarity: 0.62, skills_matched: 3 },
      ],
      error: null,
    })

    const { request, params } = makeReq('p1', 'ocupaciones')
    const res = await getOcupaciones(request, { params })
    const data = await res.json()

    expect(data.ocupaciones).toHaveLength(2)
    expect(data.ocupaciones[0].label).toBe('Albañil')
    expect(data.ocupaciones[0].afinidad).toBe(87)
    expect(data.total_skills_perfil).toBe(2)
    expect(mockRpc).toHaveBeenCalledWith('match_occupations_by_skills', {
      skill_uris: ['uri1', 'uri2'],
      similarity_threshold: 0.55,
      max_results: 20,
    })
  })
})

describe('GET /api/perfiles/[id]/gap', () => {
  it('retorna 400 sin occupation_uri', async () => {
    const { request, params } = makeReq('p1', 'gap')
    const res = await getGap(request, { params })
    expect(res.status).toBe(400)
  })

  it('retorna sin_skills si perfil vacío', async () => {
    mockFrom.mockReturnValue({
      select: () => ({
        eq: () => ({
          neq: () => Promise.resolve({ data: [], error: null }),
        }),
      }),
    })

    const { request, params } = makeReq('p1', 'gap', '?occupation_uri=http://example.com/occ1')
    const res = await getGap(request, { params })
    const data = await res.json()
    expect(data.mensaje).toBe('sin_skills')
  })

  it('expande skills en paralelo y retorna cubiertas', async () => {
    mockFrom.mockReturnValue({
      select: () => ({
        eq: () => ({
          neq: () => Promise.resolve({
            data: [{ skill_uri: 'uri1' }, { skill_uri: 'uri2' }],
            error: null,
          }),
        }),
      }),
    })

    // Mock expand_skills_semantic per skill
    mockRpc
      .mockResolvedValueOnce({
        data: [
          { expanded_uri: 'exp-a', similarity: 0.8, is_exact: false },
          { expanded_uri: 'exp-b', similarity: 0.7, is_exact: true },
        ],
        error: null,
      })
      .mockResolvedValueOnce({
        data: [
          { expanded_uri: 'exp-c', similarity: 0.9, is_exact: false },
          { expanded_uri: 'exp-a', similarity: 0.85, is_exact: false }, // duplicate, higher sim
        ],
        error: null,
      })

    const { request, params } = makeReq('p1', 'gap', '?occupation_uri=http://example.com/occ1')
    const res = await getGap(request, { params })
    const data = await res.json()

    expect(data.total_skills_perfil).toBe(2)
    expect(data.total_expanded).toBe(3) // exp-a, exp-b, exp-c
    expect(data.skills_cubiertas_uris).toContain('exp-a')
    expect(data.skills_cubiertas_uris).toContain('exp-b')
    expect(data.skills_cubiertas_uris).toContain('exp-c')
    // exp-a should have the higher similarity (0.85 from second call)
    expect(data.skills_cubiertas_detail['exp-a'].similarity).toBe(0.85)
  })
})
