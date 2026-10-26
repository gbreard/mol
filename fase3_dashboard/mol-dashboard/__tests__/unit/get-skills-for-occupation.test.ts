import { describe, it, expect, vi } from 'vitest'
import { getSkillsForOccupation } from '@/components/oficina-empleo/getSkillsForOccupation'

const OCC_JSON = {
  'cajero-test': {
    label: 'cajero/cajera',
    skills: {
      essential: [{ id: 'esco-1', label: 'cobrar a los clientes' }, { id: 'abc-123', label: 'gestionar la caja' }],
      optional: [{ id: 'esco-opt', label: 'vender productos' }],
    },
  },
}

const AR = {
  skills_consolidadas: [
    { source: 'mol_approved', esco_uri: 'http://data.europa.eu/esco/skill/abc-123', label_normalized: 'gestionar la caja', L1: 'S4', percentage: 83.3 },
    { source: 'mol_approved', esco_uri: 'http://data.europa.eu/esco/skill/ar-1', label_normalized: 'manejar efectivo', L1: 'S4' },
    { source: 'mol_approved', label_normalized: 'sin uri' },
  ],
}

describe('getSkillsForOccupation', () => {
  it('ofrece las esenciales ESCO pre-tildadas + las aprobadas para Argentina, sin repetir', async () => {
    vi.stubGlobal('fetch', vi.fn(async (url: string) => ({
      ok: true,
      json: async () => (url.includes('occupation_full_detail') ? OCC_JSON : AR),
    })))

    const { skills, source } = await getSkillsForOccupation('http://data.europa.eu/esco/occupation/cajero-test')

    expect(source).toBe('argentino')
    expect(skills.map(s => s.id)).toEqual(['esco-1', 'abc-123', 'esco-opt', 'ar-1'])
    expect(skills.find(s => s.id === 'esco-1')).toMatchObject({ essential: true, source: 'esco' })
    expect(skills.find(s => s.id === 'esco-opt')).toMatchObject({ essential: false })
    // normaliza esco_uri / label_normalized del perfil argentino y lo pre-tilda
    expect(skills.find(s => s.id === 'ar-1')).toMatchObject({ label: 'manejar efectivo', essential: true })
    vi.unstubAllGlobals()
  })
})
