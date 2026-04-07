import { describe, it, expect, vi, beforeEach } from 'vitest'

const mockRpc = vi.fn()

vi.mock('@supabase/supabase-js', () => ({
  createClient: () => ({
    rpc: mockRpc,
  }),
}))

import { POST } from '@/app/api/perfiles/cursos-gap/route'
import { NextRequest } from 'next/server'

beforeEach(() => {
  vi.stubEnv('NEXT_PUBLIC_SUPABASE_URL', 'https://test.supabase.co')
  vi.stubEnv('SUPABASE_SERVICE_ROLE_KEY', 'test-key')
  vi.clearAllMocks()
})

function makePost(body: any) {
  return new NextRequest('http://localhost:3000/api/perfiles/cursos-gap', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
}

describe('POST /api/perfiles/cursos-gap', () => {
  it('retorna vacío sin gap_skill_uris', async () => {
    const res = await POST(makePost({}))
    const data = await res.json()
    expect(data.cursos).toEqual([])
    expect(data.total).toBe(0)
    expect(res.status).toBe(200) // no error
  })

  it('retorna vacío con array vacío', async () => {
    const res = await POST(makePost({ gap_skill_uris: [] }))
    const data = await res.json()
    expect(data.cursos).toEqual([])
    expect(data.total).toBe(0)
  })

  it('llama RPC con URIs y retorna cursos con pct_gap_cubierto', async () => {
    mockRpc.mockResolvedValue({
      data: [
        {
          curso_id: 1,
          titulo: 'Instalaciones eléctricas',
          institucion: 'CFP 123',
          provincia: 'Buenos Aires',
          municipio: 'Berisso',
          modalidad: 'PRESENCIAL',
          carga_horaria: 163,
          skills_cubiertas: 5,
          total_gap_skills: 8,
          skills_detalle: [
            { uri: 'http://data.europa.eu/esco/skill/aaa', label: 'instalar enchufes' },
            { uri: 'http://data.europa.eu/esco/skill/bbb', label: 'planos cableado' },
          ],
        },
      ],
      error: null,
    })

    const res = await POST(makePost({
      gap_skill_uris: [
        'http://data.europa.eu/esco/skill/aaa',
        'http://data.europa.eu/esco/skill/bbb',
        'http://data.europa.eu/esco/skill/ccc',
      ],
    }))

    const data = await res.json()
    expect(data.total).toBe(1)
    expect(data.cursos[0].titulo).toBe('Instalaciones eléctricas')
    expect(data.cursos[0].skills_cubiertas).toBe(5)
    expect(data.cursos[0].pct_gap_cubierto).toBe(63) // 5/8 * 100

    expect(mockRpc).toHaveBeenCalledWith('get_cursos_for_gap', {
      p_gap_skill_uris: [
        'http://data.europa.eu/esco/skill/aaa',
        'http://data.europa.eu/esco/skill/bbb',
        'http://data.europa.eu/esco/skill/ccc',
      ],
      p_provincia: null,
      p_max_results: 20,
    })
  })

  it('pasa provincia a la RPC', async () => {
    mockRpc.mockResolvedValue({ data: [], error: null })

    await POST(makePost({
      gap_skill_uris: ['http://data.europa.eu/esco/skill/xxx'],
      provincia: 'Córdoba',
    }))

    expect(mockRpc).toHaveBeenCalledWith('get_cursos_for_gap', {
      p_gap_skill_uris: ['http://data.europa.eu/esco/skill/xxx'],
      p_provincia: 'Córdoba',
      p_max_results: 20,
    })
  })

  it('retorna vacío si RPC no encuentra cursos', async () => {
    mockRpc.mockResolvedValue({ data: [], error: null })

    const res = await POST(makePost({
      gap_skill_uris: ['http://data.europa.eu/esco/skill/nonexistent'],
    }))

    const data = await res.json()
    expect(data.cursos).toEqual([])
    expect(data.total).toBe(0)
  })
})
