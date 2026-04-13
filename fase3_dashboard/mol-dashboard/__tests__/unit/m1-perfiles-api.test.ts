import { describe, it, expect, vi, beforeEach } from 'vitest'

// Mock Supabase
const mockFrom = vi.fn()

vi.mock('@supabase/supabase-js', () => ({
  createClient: () => ({
    from: mockFrom,
  }),
}))

import { GET, POST } from '@/app/api/perfiles/route'
import { NextRequest } from 'next/server'

beforeEach(() => {
  vi.stubEnv('NEXT_PUBLIC_SUPABASE_URL', 'https://test.supabase.co')
  vi.stubEnv('SUPABASE_SERVICE_ROLE_KEY', 'test-key')
  vi.clearAllMocks()
})

describe('GET /api/perfiles (list all — M1 perfiles list)', () => {
  it('retorna todos los perfiles con join a personas cuando no hay params', async () => {
    const mockPerfiles = [
      { id: 'p1', persona_id: 'per1', estado: 'borrador', validado_at: null, ocupaciones: [{ label: 'Albañil' }], updated_at: '2026-04-01', completitud: 5, personas: { nombre: 'María', dni: '28450123' } },
    ]

    mockFrom.mockReturnValue({
      select: () => ({
        order: () => ({
          range: () => Promise.resolve({ data: mockPerfiles, error: null }),
        }),
      }),
    })

    const req = new NextRequest('http://localhost:3000/api/perfiles')
    const res = await GET(req)
    expect(res.status).toBe(200)
    const data = await res.json()
    expect(data).toHaveLength(1)
    expect(data[0].personas.nombre).toBe('María')
    expect(data[0].ocupaciones[0].label).toBe('Albañil')
  })

  it('filtra por search en nombre', async () => {
    const mockPerfiles = [
      { id: 'p1', personas: { nombre: 'María González', dni: '111' }, estado: 'borrador' },
      { id: 'p2', personas: { nombre: 'Jorge Pérez', dni: '222' }, estado: 'validado' },
    ]

    mockFrom.mockReturnValue({
      select: () => ({
        order: () => ({
          range: () => Promise.resolve({ data: mockPerfiles, error: null }),
        }),
      }),
    })

    const req = new NextRequest('http://localhost:3000/api/perfiles?search=gonzález')
    const res = await GET(req)
    const data = await res.json()
    expect(data).toHaveLength(1)
    expect(data[0].id).toBe('p1')
  })

  it('retorna perfil con skills y join a personas cuando ?id=X', async () => {
    const perfil = { id: 'p1', persona_id: 'per1', ocupaciones: [], estado: 'borrador', personas: { id: 'per1', nombre: 'Test', dni: '123' } }
    const skills = [{ id: 's1', perfil_id: 'p1', skill_uri: 'u1', skill_label: 'Soldadura', via_captura: 'ocupacion', estado: 'confirmada', confianza: 0.9 }]

    mockFrom.mockImplementation((table: string) => {
      if (table === 'perfiles') {
        return { select: () => ({ eq: () => ({ maybeSingle: () => Promise.resolve({ data: perfil, error: null }) }) }) }
      }
      if (table === 'perfil_skills') {
        return { select: () => ({ eq: () => ({ neq: () => ({ order: () => Promise.resolve({ data: skills, error: null }) }) }) }) }
      }
      return {}
    })

    const req = new NextRequest('http://localhost:3000/api/perfiles?id=p1')
    const res = await GET(req)
    const data = await res.json()
    expect(data.personas.nombre).toBe('Test')
    expect(data.skills).toHaveLength(1)
    expect(data.skills[0].skill_label).toBe('Soldadura')
  })
})

describe('POST /api/perfiles (M1 create)', () => {
  it('retorna 400 sin persona_id', async () => {
    const req = new NextRequest('http://localhost:3000/api/perfiles', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({}),
    })
    const res = await POST(req)
    expect(res.status).toBe(400)
  })

  it('crea perfil con ocupaciones y estado borrador', async () => {
    mockFrom.mockReturnValue({
      insert: () => ({
        select: () => ({
          single: () => Promise.resolve({
            data: { id: 'new-perfil', persona_id: 'per1', estado: 'borrador', ocupaciones: [{ label: 'Albañil' }] },
            error: null,
          }),
        }),
      }),
    })

    const req = new NextRequest('http://localhost:3000/api/perfiles', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        persona_id: 'per1',
        ocupaciones: [{ id: 'occ1', label: 'Albañil', isco_code: '7112' }],
      }),
    })
    const res = await POST(req)
    expect(res.status).toBe(201)
    const data = await res.json()
    expect(data.estado).toBe('borrador')
    expect(data.ocupaciones[0].label).toBe('Albañil')
  })
})
