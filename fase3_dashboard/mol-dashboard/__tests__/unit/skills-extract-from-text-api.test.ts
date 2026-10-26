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
    expect(data.keywords).toEqual(['albañilería', 'aplicar revoque'])
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
})
