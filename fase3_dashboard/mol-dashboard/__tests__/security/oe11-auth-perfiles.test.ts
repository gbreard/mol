import { describe, it, expect, vi } from 'vitest'
import { NextRequest } from 'next/server'

// Fase 3 (OE-11 parcial): perfiles, perfiles/[id], perfiles/[id]/skills y personas
// exigen sesión; sin sesión responden 401 y no tocan Supabase.
const { createClient } = vi.hoisted(() => ({ createClient: vi.fn() }))
vi.mock('@supabase/supabase-js', () => ({ createClient }))
vi.mock('@/lib/api-auth', async () => {
  const { NextResponse } = await import('next/server')
  return {
    requireAuth: vi.fn(async () => NextResponse.json({ error: 'No autorizado' }, { status: 401 })),
    isAuthError: (r: unknown) => r instanceof Response,
  }
})

import * as perfiles from '@/app/api/perfiles/route'
import * as perfilId from '@/app/api/perfiles/[id]/route'
import * as perfilSkills from '@/app/api/perfiles/[id]/skills/route'
import * as personas from '@/app/api/personas/route'

const req = (method: string, path: string) => new NextRequest(`http://localhost:3000${path}`, {
  method,
  ...(method === 'GET' ? {} : { body: JSON.stringify({}), headers: { 'Content-Type': 'application/json' } }),
})
const ctx = { params: Promise.resolve({ id: 'p1' }) }

describe('OE-11: rutas de perfiles y personas sin sesión → 401', () => {
  it.each([
    ['GET /api/perfiles', () => perfiles.GET(req('GET', '/api/perfiles'))],
    ['POST /api/perfiles', () => perfiles.POST(req('POST', '/api/perfiles'))],
    ['PATCH /api/perfiles/[id]', () => perfilId.PATCH(req('PATCH', '/api/perfiles/p1'), ctx)],
    ['PUT /api/perfiles/[id]', () => perfilId.PUT(req('PUT', '/api/perfiles/p1'), ctx)],
    ['DELETE /api/perfiles/[id]', () => perfilId.DELETE(req('DELETE', '/api/perfiles/p1'), ctx)],
    ['POST /api/perfiles/[id]/skills', () => perfilSkills.POST(req('POST', '/api/perfiles/p1/skills'), ctx)],
    ['PATCH /api/perfiles/[id]/skills', () => perfilSkills.PATCH(req('PATCH', '/api/perfiles/p1/skills'), ctx)],
    ['GET /api/personas', () => personas.GET(req('GET', '/api/personas'))],
    ['POST /api/personas', () => personas.POST(req('POST', '/api/personas'))],
  ])('%s', async (_nombre, llamar) => {
    const res = await llamar()
    expect(res.status).toBe(401)
    expect(createClient).not.toHaveBeenCalled()
  })
})
