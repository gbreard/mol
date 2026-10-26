import { describe, it, expect, vi, beforeEach } from 'vitest'
import { NextRequest } from 'next/server'

const { mockRpc, auth } = vi.hoisted(() => ({ mockRpc: vi.fn(), auth: { logueado: true } }))
vi.mock('@supabase/supabase-js', () => ({ createClient: () => ({ rpc: mockRpc }) }))
vi.mock('@/lib/api-auth', async () => {
  const { NextResponse } = await import('next/server')
  return {
    requireAuth: vi.fn(async () => auth.logueado ? { user: { id: 'u1' }, role: 'oficina_empleo' } : NextResponse.json({}, { status: 401 })),
    isAuthError: (r: unknown) => r instanceof Response,
  }
})

import { POST } from '@/app/api/perfiles/cursos-persona/route'

const req = (body: unknown) => new NextRequest('http://localhost:3000/api/perfiles/cursos-persona', {
  method: 'POST', body: JSON.stringify(body), headers: { 'Content-Type': 'application/json' },
})

beforeEach(() => {
  vi.clearAllMocks()
  auth.logueado = true
  process.env.NEXT_PUBLIC_SUPABASE_URL = 'https://test.supabase.co'
  process.env.SUPABASE_SERVICE_ROLE_KEY = 'k'
  mockRpc.mockResolvedValue({ data: [{ grupo: 'presencial', titulo: 'albanileria' }], error: null })
})

describe('POST /api/perfiles/cursos-persona', () => {
  it('pasa la provincia y exige ≥ 2 competencias cubiertas si el gap tiene más de 1', async () => {
    const res = await POST(req({ gap_skill_uris: ['a', 'b', 'c'], provincia: 'Cordoba' }))
    const data = await res.json()
    expect(mockRpc).toHaveBeenCalledWith('get_cursos_para_persona', expect.objectContaining({ p_provincia: 'Cordoba', p_min_cubiertas: 2 }))
    expect(data.sin_provincia).toBe(false)
  })

  it('gap de 1: alcanza con cubrir esa', async () => {
    await POST(req({ gap_skill_uris: ['a'], provincia: 'Cordoba' }))
    expect(mockRpc.mock.calls[0][1].p_min_cubiertas).toBe(1)
  })

  it('sin provincia: una sola búsqueda (solo virtuales en el RPC), sin reintento nacional', async () => {
    const data = await (await POST(req({ gap_skill_uris: ['a', 'b'] }))).json()
    expect(mockRpc).toHaveBeenCalledTimes(1)
    expect(mockRpc.mock.calls[0][1].p_provincia).toBeNull()
    expect(data.sin_provincia).toBe(true)
  })

  it('exige sesión', async () => {
    auth.logueado = false
    expect((await POST(req({ gap_skill_uris: ['a'] }))).status).toBe(401)
    expect(mockRpc).not.toHaveBeenCalled()
  })
})
