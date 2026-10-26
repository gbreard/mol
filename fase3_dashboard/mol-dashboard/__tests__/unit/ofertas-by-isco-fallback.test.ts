import { describe, it, expect, vi, beforeEach } from 'vitest'

type Filtros = Record<string, string>
type Respuesta = { data: unknown[]; count: number }

const { responder, llamadas } = vi.hoisted(() => ({
  responder: { fn: (_f: Record<string, string>, _head: boolean): { data: unknown[]; count: number } => ({ data: [], count: 0 }) },
  llamadas: [] as Record<string, string>[],
}))

// Builder encadenable mínimo: registra filtros y responde según `responder.fn`
vi.mock('@supabase/supabase-js', () => ({
  createClient: () => ({
    from: () => ({
      select: (_cols: string, opts?: { head?: boolean }) => {
        const filtros: Filtros = {}
        const head = !!opts?.head
        const b = {
          eq: (c: string, v: string) => { filtros[`eq:${c}`] = v; return b },
          gte: (c: string, v: string) => { filtros[`gte:${c}`] = v; return b },
          order: () => b,
          range: () => b,
          then: (ok: (r: Respuesta & { error: null }) => unknown) => {
            llamadas.push({ ...filtros, head: String(head) })
            return Promise.resolve({ ...responder.fn(filtros, head), error: null }).then(ok)
          },
        }
        return b
      },
    }),
  }),
}))

import { getOfertasByIsco } from '@/lib/supabase'

beforeEach(() => {
  llamadas.length = 0
})

describe('getOfertasByIsco — nunca vacío', () => {
  it('sin avisos en la provincia → muestra los del país', async () => {
    responder.fn = (f, head) => {
      if (f['eq:provincia']) return { data: [], count: 0 }
      if (head) return { data: [], count: 2 }
      return { data: [{ fecha_publicacion: '2026-08-20', estado_ciclo: 'activa' }], count: 5 }
    }

    const res = await getOfertasByIsco('7112', 3, 0, 'Córdoba', '2026-07-22')

    expect(res.alcance).toBe('pais')
    expect(res.sinFiltroFecha).toBe(false)
    expect(res.total).toBe(5)
    expect(res.activas).toBe(2)
  })

  it('sin avisos en el período → muestra los más recientes sin filtro de fecha', async () => {
    responder.fn = (f, head) => {
      if (f['gte:fecha_publicacion']) return { data: [], count: 0 }
      return head ? { data: [], count: 0 } : { data: [{ fecha_publicacion: '2026-03-01' }], count: 1 }
    }

    const res = await getOfertasByIsco('7112', 3, 0, null, '2026-07-22')

    expect(res.sinFiltroFecha).toBe(true)
    expect(res.total).toBe(1)
  })

  it('cuenta activas por estado_ciclo, no por la columna vieja estado', async () => {
    responder.fn = (f, head) => (head ? { data: [], count: 7 } : { data: [{ fecha_publicacion: '2026-08-21' }], count: 40 })

    const res = await getOfertasByIsco('2512', 10, 0, 'CABA', null)

    expect(res.alcance).toBe('provincia')
    expect(res.activas).toBe(7)
    const head = llamadas.find(l => l.head === 'true')
    expect(head?.['eq:estado_ciclo']).toBe('activa')
  })
})
