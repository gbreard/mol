/**
 * Obtiene skills de una ocupación ESCO.
 * 1. Si tiene perfil en esco_argentino → usa skills_consolidadas
 * 2. Si no → fallback a occupation_full_detail.json
 *
 * Compartida entre M1 (OccupationSkillPicker) y M2 (OccupationMatchCard).
 */

export interface OccSkillDetail {
  id: string
  label: string
  type: string
  L1?: string
  L2?: string
  essential?: boolean
  total?: number
  source?: string
}

export interface OccSkillResult {
  skills: OccSkillDetail[]
  source: 'argentino' | 'esco'
}

// Module-level cache shared across calls
const cache: Record<string, OccSkillDetail[]> = {}
let occDetailJson: Record<string, any> | null = null

export async function getSkillsForOccupation(uri: string): Promise<OccSkillResult> {
  if (cache[uri]) return { skills: cache[uri], source: 'argentino' }

  // 1. Try esco_argentino
  try {
    const res = await fetch(`/api/esco-argentino?occupation=${encodeURIComponent(uri)}`)
    if (res.ok) {
      const data = await res.json()
      if (data.skills_consolidadas?.length > 0) {
        // La API devuelve esco_uri / label_normalized (no uri / label): sin normalizar,
        // el picker mostraba filas sin nombre y guardaba URIs '…/skill/undefined'.
        const skills: OccSkillDetail[] = data.skills_consolidadas
          .map((s: any) => {
            const uri: string | undefined = s.uri || s.esco_uri
            const label: string | undefined = s.label || s.label_normalized || s.label_original
            return {
              id: uri?.split('/').pop() || '',
              label: label || '',
              type: s.L1?.startsWith('K') ? 'knowledge' : 'skill',
              L1: s.L1,
              L2: s.L2,
              total: s.percentage ?? s.percentage_when_approved ?? s.freq_cuando_aprobada ?? 0,
              // Pre-tildadas: las comunes con ESCO y las aprobadas para Argentina
              essential: s.source === 'esco_common' || s.source === 'mol_approved' || s.source === 'argentina_approved',
              source: s.source,
            }
          })
          .filter((s: OccSkillDetail) => s.id && s.label)
        cache[uri] = skills
        return { skills, source: 'argentino' }
      }
    }
  } catch {}

  // 2. Fallback: occupation_full_detail.json
  if (!occDetailJson) {
    try {
      const res = await fetch('/data/occupation_full_detail.json')
      if (res.ok) occDetailJson = await res.json()
    } catch {}
  }

  if (occDetailJson) {
    const occId = uri.split('/').pop() || ''
    const occ = occDetailJson[occId]
    if (occ?.skills) {
      const essential = (occ.skills.essential || []).map((s: any) => ({ ...s, type: 'skill', essential: true, total: 0 }))
      const optional = (occ.skills.optional || []).map((s: any) => ({ ...s, type: 'skill', essential: false, total: 0 }))
      const skills = [...essential, ...optional]
      cache[uri] = skills
      return { skills, source: 'esco' }
    }
  }

  cache[uri] = []
  return { skills: [], source: 'esco' }
}
