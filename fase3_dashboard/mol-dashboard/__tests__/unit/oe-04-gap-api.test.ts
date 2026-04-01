import { describe, it, expect, vi, beforeEach } from 'vitest'

const mockFrom = vi.fn()
const mockRpc = vi.fn()

vi.mock('@supabase/supabase-js', () => ({
  createClient: () => ({
    from: mockFrom,
    rpc: mockRpc,
  }),
}))

import { POST } from '@/app/api/casos/[id]/gap/route'
import { NextRequest } from 'next/server'

function makeRequest(id: string, body: any) {
  const req = new NextRequest(`http://localhost:3000/api/casos/${id}/gap`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  return { request: req, params: Promise.resolve({ id }) }
}

beforeEach(() => {
  vi.stubEnv('NEXT_PUBLIC_SUPABASE_URL', 'https://test.supabase.co')
  vi.stubEnv('SUPABASE_SERVICE_ROLE_KEY', 'test-key')
  vi.clearAllMocks()
})

describe('OE-04 — POST /api/casos/[id]/gap', () => {

  it('retorna 400 si falta occupation_uri', async () => {
    const { request, params } = makeRequest('caso-1', {})
    const res = await POST(request, { params })
    expect(res.status).toBe(400)
    const body = await res.json()
    expect(body.error).toContain('occupation_uri')
  })

  it('retorna 404 si el caso no existe', async () => {
    mockFrom.mockReturnValue({
      select: () => ({
        eq: () => ({
          maybeSingle: () => Promise.resolve({ data: null, error: null }),
        }),
      }),
    })

    const { request, params } = makeRequest('nonexistent', {
      occupation_uri: 'http://data.europa.eu/esco/occupation/xxx',
    })
    const res = await POST(request, { params })
    expect(res.status).toBe(404)
  })

  it('retorna sin_skills si la persona no tiene skills', async () => {
    mockFrom.mockImplementation((table: string) => {
      if (table === 'casos') {
        return {
          select: () => ({
            eq: () => ({
              maybeSingle: () => Promise.resolve({
                data: { id: 'c1', persona_id: 'p1' },
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

    const { request, params } = makeRequest('c1', {
      occupation_uri: 'http://data.europa.eu/esco/occupation/xxx',
    })
    const res = await POST(request, { params })
    const body = await res.json()
    expect(res.status).toBe(200)
    expect(body.mensaje).toBe('sin_skills')
    expect(body.gap).toBeNull()
  })

  it('retorna skills_cubiertas_uris y detail para perfil con skills', async () => {
    mockFrom.mockImplementation((table: string) => {
      if (table === 'casos') {
        return {
          select: () => ({
            eq: () => ({
              maybeSingle: () => Promise.resolve({
                data: { id: 'c1', persona_id: 'p1' },
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
                data: [
                  { skill_uri: 'http://esco/skill/a', perfiles: {} },
                  { skill_uri: 'http://esco/skill/b', perfiles: {} },
                ],
                error: null,
              }),
            }),
          }),
        }
      }
      return { select: () => ({ eq: () => ({ maybeSingle: () => Promise.resolve({ data: null, error: null }) }) }) }
    })

    // Mock expand_skills_semantic — called once per skill (parallel)
    mockRpc.mockImplementation((_name: string, params: any) => {
      const uri = params.skill_uris[0]
      return Promise.resolve({
        data: [
          { expanded_uri: uri, expanded_label: 'exact', similarity: 1.0, is_exact: true, original_uri: uri, original_label: 'orig' },
          { expanded_uri: uri + '_similar', expanded_label: 'similar', similarity: 0.82, is_exact: false, original_uri: uri, original_label: 'orig' },
        ],
        error: null,
      })
    })

    const { request, params } = makeRequest('c1', {
      occupation_uri: 'http://data.europa.eu/esco/occupation/xxx',
    })
    const res = await POST(request, { params })
    const body = await res.json()

    expect(res.status).toBe(200)
    expect(body.total_skills_perfil).toBe(2)
    expect(Array.isArray(body.skills_cubiertas_uris)).toBe(true)
    expect(body.skills_cubiertas_uris.length).toBeGreaterThan(0)
    expect(typeof body.skills_cubiertas_detail).toBe('object')
    expect(body.total_expanded).toBeGreaterThan(0)

    // Verify parallel calls: should be called once per skill
    expect(mockRpc).toHaveBeenCalledTimes(2)
  })

  it('retorna 500 si la RPC falla', async () => {
    mockFrom.mockImplementation((table: string) => {
      if (table === 'casos') {
        return {
          select: () => ({
            eq: () => ({
              maybeSingle: () => Promise.resolve({
                data: { id: 'c1', persona_id: 'p1' },
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
                data: [{ skill_uri: 'http://esco/skill/a', perfiles: {} }],
                error: null,
              }),
            }),
          }),
        }
      }
      return { select: () => ({ eq: () => ({ maybeSingle: () => Promise.resolve({ data: null, error: null }) }) }) }
    })

    mockRpc.mockResolvedValue({ data: null, error: { message: 'RPC timeout' } })

    const { request, params } = makeRequest('c1', {
      occupation_uri: 'http://data.europa.eu/esco/occupation/xxx',
    })
    const res = await POST(request, { params })
    expect(res.status).toBe(500)
  })
})
