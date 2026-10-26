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

async function loadOccDetailJson(): Promise<Record<string, any> | null> {
  if (!occDetailJson) {
    try {
      const res = await fetch('/data/occupation_full_detail.json')
      if (res.ok) occDetailJson = await res.json()
    } catch {}
  }
  return occDetailJson
}

/** Esenciales (pre-tildadas) y opcionales de ESCO para la ocupación. */
async function escoSkills(uri: string): Promise<OccSkillDetail[]> {
  const json = await loadOccDetailJson()
  const occ = json?.[uri.split('/').pop() || '']
  if (!occ?.skills) return []
  const essential = (occ.skills.essential || []).map((s: any) => ({ ...s, type: 'skill', essential: true, total: 0, source: 'esco' }))
  const optional = (occ.skills.optional || []).map((s: any) => ({ ...s, type: 'skill', essential: false, total: 0, source: 'esco' }))
  return [...essential, ...optional]
}

export async function getSkillsForOccupation(uri: string): Promise<OccSkillResult> {
  if (cache[uri]) return { skills: cache[uri], source: 'argentino' }

  // DEUDA: unificar fuente de requisitos (perfil argentino vs ESCO). El matching de M2/M3
  // mide contra las esenciales ESCO y el perfil argentino no comparte ninguna con ellas
  // (cajero 0/9, desarrollador de software 0/15): por eso se ofrecen las dos fuentes.
  const esco = await escoSkills(uri)

  // Perfil argentino: se suman sus skills aprobadas que no estén ya en ESCO
  try {
    const res = await fetch(`/api/esco-argentino?occupation=${encodeURIComponent(uri)}`)
    if (res.ok) {
      const data = await res.json()
      if (data.skills_consolidadas?.length > 0) {
        // La API devuelve esco_uri / label_normalized (no uri / label): sin normalizar,
        // el picker mostraba filas sin nombre y guardaba URIs '…/skill/undefined'.
        const argentinas: OccSkillDetail[] = data.skills_consolidadas
          .map((s: any) => {
            const skillUri: string | undefined = s.uri || s.esco_uri
            const label: string | undefined = s.label || s.label_normalized || s.label_original
            return {
              id: skillUri?.split('/').pop() || '',
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
        const escoIds = new Set(esco.map(s => s.id))
        const skills = [...esco, ...argentinas.filter(s => !escoIds.has(s.id))]
        cache[uri] = skills
        return { skills, source: 'argentino' }
      }
    }
  } catch {}

  cache[uri] = esco
  return { skills: esco, source: 'esco' }
}
