import { describe, it, expect, vi, beforeEach } from 'vitest'

const mockFrom = vi.fn()
const mockRpc = vi.fn()

vi.mock('@supabase/supabase-js', () => ({
  createClient: () => ({
    from: mockFrom,
    rpc: mockRpc,
  }),
}))

import { GET } from '@/app/api/laboratorio/brecha-formacion/route'
import { NextRequest } from 'next/server'

beforeEach(() => {
  vi.stubEnv('NEXT_PUBLIC_SUPABASE_URL', 'https://test.supabase.co')
  vi.stubEnv('SUPABASE_SERVICE_ROLE_KEY', 'test-key')
  vi.clearAllMocks()
})

function makeReq(params: Record<string, string> = {}) {
  const url = new URL('http://localhost:3000/api/laboratorio/brecha-formacion')
  for (const [k, v] of Object.entries(params)) url.searchParams.set(k, v)
  return new NextRequest(url)
}

describe('GET /api/laboratorio/brecha-formacion', () => {
  it('retorna resumen con total, brechas, cubiertas', async () => {
    mockRpc.mockResolvedValue({
      data: [
        { skill_uri: 'u1', skill_label: 'skill1', ofertas_count: 100, cursos_count: 0, estado: 'brecha', pct_mercado: 2.5 },
      ],
      error: null,
    })
    mockFrom.mockReturnValue({
      select: () => ({
        eq: () => ({ data: null }),
        limit: () => ({ data: [{ calculado_en: '2026-04-06' }] }),
        data: [{ estado: 'brecha' }, { estado: 'brecha' }, { estado: 'cubierta' }],
      }),
    })

    const res = await GET(makeReq())
    expect(res.status).toBe(200)
    const data = await res.json()
    expect(data.skills).toHaveLength(1)
    expect(data.skills[0].estado).toBe('brecha')
  })

  it('filtra por estado=brecha', async () => {
    mockRpc.mockResolvedValue({
      data: [{ skill_uri: 'u1', skill_label: 's', ofertas_count: 50, cursos_count: 0, estado: 'brecha', pct_mercado: 1 }],
      error: null,
    })
    mockFrom.mockReturnValue({
      select: () => ({
        eq: () => ({ data: null }),
        limit: () => ({ data: [] }),
        data: [{ estado: 'brecha' }],
      }),
    })

    await GET(makeReq({ estado: 'brecha' }))
    expect(mockRpc).toHaveBeenCalledWith('get_brecha_formacion', {
      p_estado: 'brecha',
      p_limit: 20,
      p_offset: 0,
    })
  })

  it('usa RPC provincial cuando hay provincia', async () => {
    mockRpc.mockResolvedValue({
      data: [{ skill_uri: 'u1', skill_label: 's', ofertas_count: 30, cursos_count: 0, estado: 'brecha' }],
      error: null,
    })
    mockFrom.mockReturnValue({
      select: () => ({
        eq: () => ({
          data: [{ estado: 'brecha' }],
        }),
        limit: () => ({ data: [] }),
      }),
    })

    await GET(makeReq({ provincia: 'Buenos Aires', estado: 'brecha' }))
    expect(mockRpc).toHaveBeenCalledWith('get_brecha_formacion_provincia', {
      p_provincia: 'Buenos Aires',
      p_estado: 'brecha',
      p_limit: 20,
    })
  })

  it('paginación con limit y offset', async () => {
    mockRpc.mockResolvedValue({ data: [], error: null })
    mockFrom.mockReturnValue({
      select: () => ({
        limit: () => ({ data: [] }),
        data: [],
      }),
    })

    await GET(makeReq({ limit: '5', offset: '10' }))
    expect(mockRpc).toHaveBeenCalledWith('get_brecha_formacion', {
      p_estado: null,
      p_limit: 5,
      p_offset: 10,
    })
  })
})
