import { describe, it, expect, vi, beforeEach } from 'vitest'

const mockRpc = vi.fn()

vi.mock('@supabase/supabase-js', () => ({
  createClient: () => ({ rpc: mockRpc }),
}))

import { GET as searchCursos } from '@/app/api/cursos-formacion/search/route'
import { GET as getSkills } from '@/app/api/cursos-formacion/[id]/skills/route'
import { NextRequest } from 'next/server'

beforeEach(() => {
  vi.stubEnv('NEXT_PUBLIC_SUPABASE_URL', 'https://test.supabase.co')
  vi.stubEnv('SUPABASE_SERVICE_ROLE_KEY', 'test-key')
  vi.clearAllMocks()
})

describe('GET /api/cursos-formacion/search', () => {
  it('retorna cursos para búsqueda válida', async () => {
    mockRpc.mockResolvedValue({
      data: [
        { curso_id: 1, denominacion: 'electricidad basica', grupo: 'Construcción', carga_horaria_modal: 48, skills_count: 8 },
      ],
      error: null,
    })

    const req = new NextRequest('http://localhost:3000/api/cursos-formacion/search?q=electricidad')
    const res = await searchCursos(req)
    const data = await res.json()
    expect(data.cursos).toHaveLength(1)
    expect(data.cursos[0].denominacion).toBe('electricidad basica')
  })

  it('retorna vacío para búsqueda corta', async () => {
    const req = new NextRequest('http://localhost:3000/api/cursos-formacion/search?q=e')
    const res = await searchCursos(req)
    const data = await res.json()
    expect(data.cursos).toEqual([])
  })

  it('retorna vacío sin query', async () => {
    const req = new NextRequest('http://localhost:3000/api/cursos-formacion/search')
    const res = await searchCursos(req)
    const data = await res.json()
    expect(data.cursos).toEqual([])
  })
})

describe('GET /api/cursos-formacion/[id]/skills', () => {
  it('retorna skills de un curso', async () => {
    mockRpc.mockResolvedValue({
      data: [
        { skill_uri: 'http://data.europa.eu/esco/skill/aaa', skill_label: 'instalar enchufes' },
        { skill_uri: 'http://data.europa.eu/esco/skill/bbb', skill_label: 'leer planos' },
      ],
      error: null,
    })

    const req = new NextRequest('http://localhost:3000/api/cursos-formacion/42/skills')
    const res = await getSkills(req, { params: Promise.resolve({ id: '42' }) })
    const data = await res.json()
    expect(data.skills).toHaveLength(2)
    expect(data.skills[0].skill_label).toBe('instalar enchufes')
  })

  it('retorna vacío para ID no numérico', async () => {
    const req = new NextRequest('http://localhost:3000/api/cursos-formacion/abc/skills')
    const res = await getSkills(req, { params: Promise.resolve({ id: 'abc' }) })
    const data = await res.json()
    expect(data.skills).toEqual([])
  })
})
