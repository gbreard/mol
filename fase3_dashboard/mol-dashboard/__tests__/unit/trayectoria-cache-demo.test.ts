import { describe, it, expect, vi, beforeEach } from 'vitest'
import { NextRequest } from 'next/server'

const { mockCreate } = vi.hoisted(() => ({ mockCreate: vi.fn() }))
vi.mock('@/lib/groq', () => ({
  GROQ_MODEL_LARGE: 'test-large',
  getGroq: () => ({ chat: { completions: { create: mockCreate } } }),
}))
vi.mock('@/lib/demo/recomendaciones-demo.json', () => ({
  default: {
    'perfil-jorge|': { ocupacion: 'Soldador', diagnostico: 'Jorge, fijado.', recomendacion: 'r', alternativas: [], pasos: [], cierre: '' },
  },
}))

import { POST } from '@/app/api/trayectoria-laboral/route'

const req = (body: unknown) => new NextRequest('http://localhost:3000/api/trayectoria-laboral', {
  method: 'POST', body: JSON.stringify(body), headers: { 'Content-Type': 'application/json' },
})
const top = [{ label: 'Soldador', cubiertas: 19, esenciales_total: 28, avisos: 208, demanda: 'Demanda estable' }]

beforeEach(() => vi.clearAllMocks())

describe('trayectoria-laboral — recomendaciones fijadas DEMO', () => {
  it('perfil DEMO con recomendación fijada: la sirve sin llamar al modelo (con o sin ocupación elegida)', async () => {
    for (const ocupacion_uri of [null, 'http://data.europa.eu/esco/occupation/x']) {
      const data = await (await POST(req({ perfil_id: 'perfil-jorge', ocupacion_uri, top_ocupaciones: top }))).json()
      expect(data.cacheado).toBe(true)
      expect(data.recomendacion.diagnostico).toBe('Jorge, fijado.')
    }
    expect(mockCreate).not.toHaveBeenCalled()
  })

  it('otro perfil: genera con el modelo y valida', async () => {
    mockCreate.mockResolvedValue({ choices: [{ message: { content: JSON.stringify({ ocupacion: 'Soldador', diagnostico: 'd', recomendacion: 'r' }) } }] })
    const data = await (await POST(req({ perfil_id: 'otro', top_ocupaciones: top }))).json()
    expect(mockCreate).toHaveBeenCalledTimes(1)
    expect(data.cacheado).toBeUndefined()
    expect(data.recomendacion.ocupacion).toBe('Soldador')
  })
})
