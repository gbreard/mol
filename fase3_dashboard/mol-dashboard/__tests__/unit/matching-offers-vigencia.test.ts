/**
 * Fase 5 / Etapa C — /api/matching-offers filtra por vigencia real.
 *
 * POR QUE EXISTE ESTE TEST
 * El endpoint filtraba por `estado_oferta`, columna que NO existe en
 * ofertas_dashboard (el nombre local viaja al dashboard como `estado`).
 * PostgREST respondia 42703 y la ruta fallaba en TODA llamada. Sobrevivio a 933
 * tests porque el mock MSW de ofertas_dashboard descarta en silencio las
 * columnas que no reconoce (`if (col in row)`), o sea es mas permisivo que
 * Postgres: nunca podia reproducir el error.
 *
 * Por eso este test NO mira la respuesta: mira la CONSULTA que se emite.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'

// La ruta crea el cliente a nivel de MODULO, asi que createClient corre al
// importarla: el mock tiene que existir antes. vi.hoisted lo eleva sobre el
// vi.mock (sin esto: "Cannot access 'mockFrom' before initialization").
const { mockFrom } = vi.hoisted(() => ({ mockFrom: vi.fn() }))

vi.mock('@supabase/supabase-js', () => ({
  createClient: () => ({ from: mockFrom }),
}))

vi.mock('@/lib/api-auth', () => ({
  requireRateLimit: () => null,
}))

import { GET } from '@/app/api/matching-offers/route'
import { NextRequest } from 'next/server'

/** Cadena PostgREST que registra lo que le piden. */
function espiaQuery(filas: Record<string, unknown>[] = []) {
  const eqs: Array<[string, unknown]> = []
  let columnas = ''

  const chain: Record<string, unknown> = {}
  const self = () => chain
  Object.assign(chain, {
    select: (cols: string) => { columnas = cols; return chain },
    in: self,
    eq: (col: string, val: unknown) => { eqs.push([col, val]); return chain },
    ilike: self,
    order: self,
    range: () => Promise.resolve({ data: filas, error: null, count: filas.length }),
  })

  mockFrom.mockReturnValue(chain)
  return { eqs: () => eqs, columnas: () => columnas }
}

beforeEach(() => {
  vi.stubEnv('NEXT_PUBLIC_SUPABASE_URL', 'https://test.supabase.co')
  vi.stubEnv('NEXT_PUBLIC_SUPABASE_ANON_KEY', 'test-anon-key-not-real')
  vi.clearAllMocks()
})

const pedido = (qs: string) =>
  GET(new NextRequest(`http://localhost:3000/api/matching-offers?${qs}`))

describe('/api/matching-offers — filtro de vigencia', () => {
  it('filtra por estado_ciclo, no por la columna inexistente estado_oferta', async () => {
    const espia = espiaQuery()
    await pedido('isco_codes=2512')

    expect(espia.eqs()).toContainEqual(['estado_ciclo', 'activa'])
    expect(espia.eqs().map(([c]) => c)).not.toContain('estado_oferta')
  })

  it('no pide estado_oferta en el select (PostgREST responde 42703)', async () => {
    const espia = espiaQuery()
    await pedido('isco_codes=2512')

    expect(espia.columnas()).toContain('estado_ciclo')
    expect(espia.columnas()).not.toContain('estado_oferta')
  })

  it('no usa el `estado` legacy: marcaba de baja a las ~7.100 ofertas vivas', async () => {
    const espia = espiaQuery()
    await pedido('isco_codes=2512')

    expect(espia.eqs().map(([c]) => c)).not.toContain('estado')
  })

  it('sigue devolviendo ofertas y calculando el gap de skills', async () => {
    espiaQuery([
      {
        id_oferta: 1, titulo: 'Dev', empresa: 'ACME', provincia: 'CABA',
        localidad: 'CABA', modalidad: 'remoto', fecha_publicacion_iso: '2026-09-01',
        url_oferta: 'http://x', isco_code: '2512',
        esco_occupation_label: 'Programador', skills_tecnicas_list: ['python', 'sql'],
        estado_ciclo: 'activa',
      },
    ])

    const res = await pedido('isco_codes=2512&skills=python')
    expect(res.status).toBe(200)

    const { offers } = await res.json()
    expect(offers).toHaveLength(1)
    expect(offers[0].skills_cubiertas).toEqual(['python'])
    expect(offers[0].skills_gap).toEqual(['sql'])
  })
})
