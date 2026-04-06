import { describe, it, expect, vi, beforeEach } from 'vitest'

const mockFrom = vi.fn()

vi.mock('@supabase/supabase-js', () => ({
  createClient: () => ({
    from: mockFrom,
  }),
}))

import { PATCH, PUT } from '@/app/api/perfiles/[id]/route'
import { NextRequest } from 'next/server'

beforeEach(() => {
  vi.stubEnv('NEXT_PUBLIC_SUPABASE_URL', 'https://test.supabase.co')
  vi.stubEnv('SUPABASE_SERVICE_ROLE_KEY', 'test-key')
  vi.clearAllMocks()
})

function makeRequest(id: string, method: string, body?: any) {
  const url = `http://localhost:3000/api/perfiles/${id}`
  const init: any = { method }
  if (body) {
    init.headers = { 'Content-Type': 'application/json' }
    init.body = JSON.stringify(body)
  }
  return { request: new NextRequest(url, init), params: Promise.resolve({ id }) }
}

describe('PATCH /api/perfiles/[id]', () => {
  it('retorna 400 con estado inválido', async () => {
    const { request, params } = makeRequest('p1', 'PATCH', { estado: 'invalido' })
    const res = await PATCH(request, { params })
    expect(res.status).toBe(400)
  })

  it('valida perfil — setea validado_at', async () => {
    mockFrom.mockReturnValue({
      update: () => ({
        eq: () => ({
          select: () => ({
            single: () => Promise.resolve({
              data: { id: 'p1', estado: 'validado', validado_at: '2026-04-06T00:00:00Z' },
              error: null,
            }),
          }),
        }),
      }),
    })

    const { request, params } = makeRequest('p1', 'PATCH', { estado: 'validado' })
    const res = await PATCH(request, { params })
    expect(res.status).toBe(200)
    const data = await res.json()
    expect(data.estado).toBe('validado')
    expect(data.validado_at).toBeTruthy()
  })

  it('quita validación — nullea validado_at', async () => {
    mockFrom.mockReturnValue({
      update: () => ({
        eq: () => ({
          select: () => ({
            single: () => Promise.resolve({
              data: { id: 'p1', estado: 'borrador', validado_at: null },
              error: null,
            }),
          }),
        }),
      }),
    })

    const { request, params } = makeRequest('p1', 'PATCH', { estado: 'borrador' })
    const res = await PATCH(request, { params })
    const data = await res.json()
    expect(data.estado).toBe('borrador')
    expect(data.validado_at).toBeNull()
  })
})

describe('PUT /api/perfiles/[id]', () => {
  it('retorna 404 si perfil no existe', async () => {
    mockFrom.mockReturnValue({
      select: () => ({
        eq: () => ({
          maybeSingle: () => Promise.resolve({ data: null, error: null }),
        }),
      }),
    })

    const { request, params } = makeRequest('nope', 'PUT', { nombre: 'X', skills: [{ uri: 'a', label: 'b' }] })
    const res = await PUT(request, { params })
    expect(res.status).toBe(404)
  })

  it('actualiza persona + perfil + reemplaza skills', async () => {
    let insertedSkills: any[] = []

    mockFrom.mockImplementation((table: string) => {
      if (table === 'perfiles') {
        return {
          select: () => ({
            eq: () => ({
              maybeSingle: () => Promise.resolve({ data: { persona_id: 'per1' }, error: null }),
            }),
          }),
          update: () => ({
            eq: () => Promise.resolve({ error: null }),
          }),
        }
      }
      if (table === 'personas') {
        return {
          update: () => ({
            eq: () => Promise.resolve({ error: null }),
          }),
        }
      }
      if (table === 'perfil_skills') {
        return {
          delete: () => ({
            eq: () => Promise.resolve({ error: null }),
          }),
          insert: (rows: any[]) => {
            insertedSkills = rows
            return Promise.resolve({ error: null })
          },
        }
      }
      return {}
    })

    const { request, params } = makeRequest('p1', 'PUT', {
      nombre: 'María Updated',
      dni: '123',
      skills: [
        { uri: 'new1', label: 'Python', source: 'estructurado' },
        { uri: 'new2', label: 'Soldadura', source: 'ocupacion' },
      ],
    })

    const res = await PUT(request, { params })
    expect(res.status).toBe(200)
    const data = await res.json()
    expect(data.estado).toBe('borrador')
    expect(insertedSkills).toHaveLength(2)
    expect(insertedSkills[0].via_captura).toBe('estructurado')
    expect(insertedSkills[1].via_captura).toBe('ocupacion')
  })
})
