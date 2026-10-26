import { describe, it, expect, vi } from 'vitest'
import { getSkillsForOccupation } from '@/components/oficina-empleo/getSkillsForOccupation'

describe('getSkillsForOccupation — perfil argentino', () => {
  it('normaliza esco_uri → id y label_normalized → label, y pre-tilda las aprobadas', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        skills_consolidadas: [
          { source: 'mol_approved', esco_uri: 'http://data.europa.eu/esco/skill/abc-123', label_normalized: 'gestionar la caja', L1: 'S4', percentage: 83.3 },
          { source: 'esco_common', esco_uri: 'http://data.europa.eu/esco/skill/def-456', label_original: 'atender clientes', L1: 'S3' },
          { source: 'mol_approved', label_normalized: 'sin uri' },
        ],
      }),
    }))

    const { skills, source } = await getSkillsForOccupation('http://data.europa.eu/esco/occupation/cajero-test')

    expect(source).toBe('argentino')
    expect(skills).toHaveLength(2) // la que no tiene URI se descarta
    expect(skills[0]).toMatchObject({ id: 'abc-123', label: 'gestionar la caja', essential: true, total: 83.3 })
    expect(skills[1]).toMatchObject({ id: 'def-456', label: 'atender clientes', essential: true })
    vi.unstubAllGlobals()
  })
})
