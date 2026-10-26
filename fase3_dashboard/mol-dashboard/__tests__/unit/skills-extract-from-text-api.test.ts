import { describe, it, expect, vi, beforeEach } from 'vitest'

const { mockRpc, mockGroqCreate, groqState } = vi.hoisted(() => ({
  mockRpc: vi.fn(),
  mockGroqCreate: vi.fn(),
  groqState: { available: true },
}))

vi.mock('@supabase/supabase-js', () => ({
  createClient: () => ({ rpc: mockRpc }),
}))

vi.mock('@/lib/groq', () => ({
  GROQ_MODEL_FAST: 'test-fast',
  GROQ_MODEL_LARGE: 'test-large',
  getGroq: () => (groqState.available ? { chat: { completions: { create: mockGroqCreate } } } : null),
}))

import { POST } from '@/app/api/skills-extract-from-text/route'
import { NextRequest } from 'next/server'

const fetchMock = vi.fn()

function makeReq(text: string, query = '') {
  return new NextRequest(`http://localhost:3000/api/skills-extract-from-text${query}`, {
    method: 'POST',
    body: JSON.stringify({ text }),
    headers: { 'content-type': 'application/json', 'x-forwarded-for': `10.0.0.${Math.floor(Math.random() * 250)}` },
  })
}

function embedOk(n: number) {
  return { ok: true, json: async () => ({ embeddings: Array.from({ length: n }, () => [0.1, 0.2]) }) }
}

beforeEach(() => {
  vi.clearAllMocks()
  groqState.available = true
  vi.stubGlobal('fetch', fetchMock)
  mockRpc.mockResolvedValue({
    data: [{ skill_uri: 'esco:albanileria', skill_label: 'construir muros de mampostería', similarity: 0.72 }],
    error: null,
  })
})

describe('POST /api/skills-extract-from-text', () => {
  it('usa LLM + BGE-M3 cuando Groq responde', async () => {
    mockGroqCreate.mockResolvedValue({
      choices: [{ message: { content: '{"terminos": ["albañilería", "aplicar revoque"]}' } }],
    })
    fetchMock.mockResolvedValue(embedOk(2))

    const data = await (await POST(makeReq('levanto paredes y hago revoques'))).json()

    expect(data.method).toBe('llm+bge-m3')
    // consultas = keywords del LLM + frases del relato
    expect(data.keywords).toEqual(['albañilería', 'aplicar revoque', 'levanto paredes', 'hago revoques'])
    expect(data.results[0].label).toBe('construir muros de mampostería')
    expect(mockGroqCreate.mock.calls[0][0]).toMatchObject({
      model: 'test-fast',
      reasoning_effort: 'low',
      response_format: { type: 'json_object' },
    })
    expect(mockGroqCreate.mock.calls[0][0].max_completion_tokens).toBeGreaterThanOrEqual(1024)
  })

  it('si Groq falla, embebe frases del texto con umbral 0.55 y method bge-m3', async () => {
    mockGroqCreate.mockRejectedValue(new Error('404 model_not_found'))
    fetchMock.mockResolvedValue(embedOk(3))

    const data = await (await POST(makeReq('trabajé de albañil, levanto paredes y hago revoques'))).json()

    expect(data.method).toBe('bge-m3')
    expect(data.keywords).toEqual(['trabajé de albañil', 'levanto paredes', 'hago revoques'])
    expect(data.results).toHaveLength(1) // deduplicado por URI
    const rpcArgs = mockRpc.mock.calls[mockRpc.mock.calls.length - 1][1]
    expect(rpcArgs).toMatchObject({ match_threshold: 0.55, match_count: 4 })
  })

  it('?llm=0 fuerza el fallback sin llamar a Groq', async () => {
    fetchMock.mockResolvedValue(embedOk(2))

    const data = await (await POST(makeReq('atiendo la caja y repongo góndolas', '?llm=0'))).json()

    expect(mockGroqCreate).not.toHaveBeenCalled()
    expect(data.method).toBe('bge-m3')
  })

  it('si el VPS también está caído no devuelve resultados basura, sino un mensaje', async () => {
    groqState.available = false
    fetchMock.mockRejectedValue(new Error('ECONNREFUSED'))

    const data = await (await POST(makeReq('trabajé 5 años de albañil, levanto paredes'))).json()

    expect(data.method).toBe('fallback')
    expect(data.results).toEqual([])
    expect(data.message).toMatch(/No pudimos interpretar el texto/)
  })

  it('filtra ruido: exclusiones, idiomas, umbral 0.60 y máximo 8', async () => {
    mockGroqCreate.mockResolvedValue({ choices: [{ message: { content: '{"terminos": ["a", "b"]}' } }] })
    fetchMock.mockResolvedValue(embedOk(2))
    const hits = [
      { skill_uri: 'u-alb', skill_label: 'albanés', similarity: 0.9 },
      { skill_uri: 'u-esc', skill_label: 'escribir en hebreo', similarity: 0.88 },
      { skill_uri: 'u-cab', skill_label: 'criar cabras', similarity: 0.85 },
      ...Array.from({ length: 10 }, (_, i) => ({ skill_uri: `u${i}`, skill_label: `skill ${i}`, similarity: 0.8 - i * 0.01 })),
      { skill_uri: 'u-low', skill_label: 'skill floja', similarity: 0.58 },
    ]
    mockRpc.mockResolvedValue({ data: hits, error: null })

    const data = await (await POST(makeReq('trabajé de albañil y levanto paredes'))).json()
    const labels = data.results.map((r: { label: string }) => r.label)

    expect(labels).toHaveLength(8)
    expect(labels).not.toContain('albanés')
    expect(labels).not.toContain('escribir en hebreo')
    expect(labels).not.toContain('criar cabras')
    expect(labels).not.toContain('skill floja')
  })

  it('conserva idiomas si el texto los menciona', async () => {
    mockGroqCreate.mockResolvedValue({ choices: [{ message: { content: '{"terminos": ["a"]}' } }] })
    fetchMock.mockResolvedValue(embedOk(1))
    mockRpc.mockResolvedValue({ data: [{ skill_uri: 'u-en', skill_label: 'inglés', similarity: 0.9 }], error: null })

    const data = await (await POST(makeReq('atiendo turistas en inglés'))).json()

    expect(data.results.map((r: { label: string }) => r.label)).toContain('inglés')
  })

  it('si quedan menos de 3 sobre el umbral, completa hasta 3 con >= 0.55', async () => {
    mockGroqCreate.mockResolvedValue({ choices: [{ message: { content: '{"terminos": ["a"]}' } }] })
    fetchMock.mockResolvedValue(embedOk(1))
    mockRpc.mockResolvedValue({
      data: [
        { skill_uri: 'a', skill_label: 'a', similarity: 0.7 },
        { skill_uri: 'b', skill_label: 'b', similarity: 0.57 },
        { skill_uri: 'c', skill_label: 'c', similarity: 0.56 },
        { skill_uri: 'd', skill_label: 'd', similarity: 0.555 },
        { skill_uri: 'e', skill_label: 'e', similarity: 0.5 },
      ],
      error: null,
    })

    const data = await (await POST(makeReq('cualquier relato de trabajo'))).json()

    expect(data.results.map((r: { label: string }) => r.label)).toEqual(['a', 'b', 'c'])
  })

  it('warmup llama al /health del VPS y no procesa texto', async () => {
    fetchMock.mockResolvedValue({ ok: true })

    const data = await (await POST(makeReq('', '?warmup=1'))).json()

    expect(data).toEqual({ warmup: true, vps: true })
    expect(fetchMock.mock.calls[0][0]).toMatch(/\/health$/)
    expect(mockGroqCreate).not.toHaveBeenCalled()
  })

  it('Groq se llama con timeout de 4 s y sin reintentos', async () => {
    mockGroqCreate.mockResolvedValue({ choices: [{ message: { content: '{"terminos": ["a"]}' } }] })
    fetchMock.mockResolvedValue(embedOk(1))

    await POST(makeReq('levanto paredes y hago revoques'))

    expect(mockGroqCreate.mock.calls[0][1]).toEqual({ timeout: 4000, maxRetries: 0 })
  })

  it('selección: Groq elige entre los candidatos los que el texto respalda', async () => {
    mockGroqCreate
      .mockResolvedValueOnce({ choices: [{ message: { content: '{"terminos": ["enfermería", "signos vitales"]}' } }] })
      .mockResolvedValueOnce({ choices: [{ message: { content: '{"indices": [2]}' } }] })
    fetchMock.mockResolvedValue(embedOk(2))
    mockRpc.mockResolvedValue({
      data: [
        { skill_uri: 'u1', skill_label: 'presión del agua', similarity: 0.8 },
        { skill_uri: 'u2', skill_label: 'medir la presión sanguínea', similarity: 0.7 },
      ],
      error: null,
    })

    const data = await (await POST(makeReq('tomo la presión y pongo inyecciones'))).json()

    expect(data.method).toBe('llm+bge-m3+seleccion')
    expect(data.results.map((r: { label: string }) => r.label)).toEqual(['medir la presión sanguínea'])
    expect(mockGroqCreate.mock.calls[1][0].messages[1].content).toContain('1. presión del agua')
  })

  it('si la selección falla, devuelve los candidatos con el filtro por umbral', async () => {
    mockGroqCreate
      .mockResolvedValueOnce({ choices: [{ message: { content: '{"terminos": ["albañilería"]}' } }] })
      .mockRejectedValueOnce(new Error('Request timed out.'))
    fetchMock.mockResolvedValue(embedOk(1))
    mockRpc.mockResolvedValue({ data: [{ skill_uri: 'u1', skill_label: 'construir muros', similarity: 0.8 }], error: null })

    const data = await (await POST(makeReq('levanto paredes de ladrillo'))).json()

    expect(data.method).toBe('llm+bge-m3')
    expect(data.results.map((r: { label: string }) => r.label)).toEqual(['construir muros'])
  })

  it('deduplica por label además de por URI', async () => {
    mockGroqCreate.mockResolvedValue({ choices: [{ message: { content: '{"terminos": ["albañilería"]}' } }] })
    fetchMock.mockResolvedValue(embedOk(1))
    mockRpc.mockResolvedValue({
      data: [
        { skill_uri: 'v1', skill_label: 'gestionar el inventario de vehículos', similarity: 0.7 },
        { skill_uri: 'v2', skill_label: 'Gestionar el inventario de vehículos', similarity: 0.75 },
        { skill_uri: 'x', skill_label: 'servicio al cliente', similarity: 0.8 },
        { skill_uri: 'y', skill_label: 'tramitar pagos', similarity: 0.65 },
      ],
      error: null,
    })

    const data = await (await POST(makeReq('trabajé en un supermercado'))).json()
    const labels = data.results.map((r: { label: string }) => r.label.toLowerCase())

    expect(labels.filter((l: string) => l === 'gestionar el inventario de vehículos')).toHaveLength(1)
  })
})
