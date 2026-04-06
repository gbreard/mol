'use client'

import { useState, useEffect, useCallback, useMemo } from 'react'
import { useSearchParams, useRouter } from 'next/navigation'
import { Loader2, Map, Check, X as XIcon, ArrowRight, ExternalLink } from 'lucide-react'
import { createBrowserClient } from '@supabase/ssr'
import { OEBreadcrumb } from '@/components/oficina-empleo/OEBreadcrumb'

let _supabase: ReturnType<typeof createBrowserClient> | null = null
function getSupabase() {
  if (!_supabase) _supabase = createBrowserClient(process.env.NEXT_PUBLIC_SUPABASE_URL!, process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!)
  return _supabase
}
import { PersonaSelector, type PerfilResumen } from '@/components/oficina-empleo/PersonaSelector'
import { OcupacionObjetivoSelector } from '@/components/oficina-empleo/OcupacionObjetivoSelector'
import { OfertasModal } from '@/components/oficina-empleo/OfertasModal'
import type { OccupationMatch } from '@/app/oficina-empleo/perfiles/matching/page'

interface PerfilSkill {
  skill_uri: string
  skill_label: string
  type?: string
}

interface OccSkill {
  id: string
  label: string
  L1?: string
  L2?: string
}

interface OccDetail {
  uri: string
  label: string
  isco_code: string
  essentialCount: number
  optionalCount: number
}

interface MOLSkillFreq {
  skill_uri: string
  frequency: number
  ofertas_count: number
}

function barColor(pct: number) {
  if (pct >= 70) return 'bg-green-500'
  if (pct >= 40) return 'bg-yellow-500'
  return 'bg-red-400'
}

function demandLabel(freq: number) {
  if (freq > 100) return { bars: '███', label: 'Alta demanda' }
  if (freq > 30) return { bars: '██', label: 'Media demanda' }
  return { bars: '█', label: 'Baja demanda' }
}

export default function FuturoLaboralPage() {
  const searchParams = useSearchParams()
  const router = useRouter()
  const initialPerfilId = searchParams.get('perfil_id')
  const initialOccId = searchParams.get('occ_id')

  // Data sources
  const [occupationsData, setOccupationsData] = useState<Record<string, any> | null>(null)
  const [skillsSearchable, setSkillsSearchable] = useState<Record<string, number>>({}) // uri -> total
  const [ofertasCountMap, setOfertasCountMap] = useState<Record<string, number>>({})

  // Selections
  const [perfil, setPerfil] = useState<PerfilResumen | null>(null)
  const [perfilSkills, setPerfilSkills] = useState<PerfilSkill[]>([])
  const [selectedOcc, setSelectedOcc] = useState<OccDetail | null>(null)

  // MOL data (lazy per occupation)
  const [molFreqs, setMolFreqs] = useState<Record<string, number>>({}) // skill_uri -> freq%
  const [molOfertasCount, setMolOfertasCount] = useState(0)

  // Modal
  const [modalOpen, setModalOpen] = useState(false)

  // Loading
  const [loadingPerfil, setLoadingPerfil] = useState(false)
  const [loadingMol, setLoadingMol] = useState(false)

  // Load static data on mount
  useEffect(() => {
    fetch('/data/occupation_full_detail.json')
      .then(r => r.ok ? r.json() : null)
      .then(d => { if (d) setOccupationsData(d) })
      .catch(() => {})

    // skills_searchable.json — build uri->total map for market_frequency
    fetch('/data/skills_searchable.json')
      .then(r => r.ok ? r.json() : null)
      .then(d => {
        if (d?.skills) {
          const map: Record<string, number> = {}
          for (const s of d.skills) {
            if (s.id) map[`http://data.europa.eu/esco/skill/${s.id}`] = s.total || 0
          }
          setSkillsSearchable(map)
        }
      })
      .catch(() => {})

    // Ofertas count via RPC
    const supabase = getSupabase()
    supabase.rpc('get_ofertas_count_by_isco').then(({ data }) => {
      if (data) {
        const map: Record<string, number> = {}
        for (const row of data) map[row.isco_code] = Number(row.count)
        setOfertasCountMap(map)
      }
    })
  }, [])

  // Profile skill URIs set (for matching)
  const profileSkillUris = useMemo(
    () => new Set(perfilSkills.map(s => s.skill_uri)),
    [perfilSkills]
  )

  // Client-side matching (same as M2) — for "Mis matches" in occupation selector
  const matchingOccupations = useMemo((): OccupationMatch[] => {
    if (profileSkillUris.size === 0 || !occupationsData) return []
    const results: OccupationMatch[] = []
    for (const [id, occ] of Object.entries(occupationsData) as [string, any][]) {
      const essential = occ.skills?.essential ?? []
      const optional = occ.skills?.optional ?? []
      const essentialCovered = essential.filter((s: any) => profileSkillUris.has(`http://data.europa.eu/esco/skill/${s.id}`)).length
      const optionalCovered = optional.filter((s: any) => profileSkillUris.has(`http://data.europa.eu/esco/skill/${s.id}`)).length
      if (essentialCovered === 0) continue
      const essentialTotal = essential.length
      results.push({
        uri: `http://data.europa.eu/esco/occupation/${id}`,
        label: occ.label || id,
        isco_code: (occ.isco || '').replace(/^C/, ''),
        matchScore: essentialTotal > 0 ? Math.round((essentialCovered / essentialTotal) * 100) : 0,
        essentialTotal,
        essentialCovered,
        optionalCovered,
        gapCount: essentialTotal - essentialCovered,
      })
    }
    results.sort((a, b) => b.matchScore - a.matchScore || a.gapCount - b.gapCount)
    return results
  }, [profileSkillUris, occupationsData])

  // Gap analysis (plan lines 1058-1085)
  const gapAnalysis = useMemo(() => {
    if (!selectedOcc || !occupationsData) return null
    const occId = selectedOcc.uri.split('/').pop() || ''
    const occ = occupationsData[occId]
    if (!occ?.skills) return null

    const allSkillsB = [...(occ.skills.essential || []), ...(occ.skills.optional || [])]
    const essentialIdsB = new Set((occ.skills.essential || []).map((s: any) => s.id))

    // Knowledge is {essential: [], optional: []}, flatten to single array
    const knowledgeRaw = occ.knowledge || {}
    const knowledgeB = [...(knowledgeRaw.essential || []), ...(knowledgeRaw.optional || [])]

    // Skills the person has that the occupation requires
    const shared = allSkillsB.filter((s: any) => profileSkillUris.has(`http://data.europa.eu/esco/skill/${s.id}`))
    const sharedEssential = shared.filter((s: any) => essentialIdsB.has(s.id))
    const sharedOptional = shared.filter((s: any) => !essentialIdsB.has(s.id))

    // Skills the occupation requires that the person doesn't have
    const gapToCover = allSkillsB.filter((s: any) => !profileSkillUris.has(`http://data.europa.eu/esco/skill/${s.id}`))
    const gapEssential = gapToCover.filter((s: any) => essentialIdsB.has(s.id))
    const gapOptional = gapToCover.filter((s: any) => !essentialIdsB.has(s.id))

    // Knowledge
    const sharedKnowledge = knowledgeB.filter((k: any) => profileSkillUris.has(`http://data.europa.eu/esco/skill/${k.id}`))
    const gapKnowledge = knowledgeB.filter((k: any) => !profileSkillUris.has(`http://data.europa.eu/esco/skill/${k.id}`))

    // Transferable (person has but occupation doesn't need)
    const bSkillIds = new Set(allSkillsB.map((s: any) => `http://data.europa.eu/esco/skill/${s.id}`))
    const bKnowledgeIds = new Set(knowledgeB.map((k: any) => `http://data.europa.eu/esco/skill/${k.id}`))
    const transferable = perfilSkills.filter(s => !bSkillIds.has(s.skill_uri) && !bKnowledgeIds.has(s.skill_uri))

    // Compatibility
    const essentialTotal = (occ.skills.essential || []).length
    const compatibility = essentialTotal > 0
      ? Math.round((sharedEssential.length / essentialTotal) * 100)
      : 0

    return {
      compatibility,
      essentialTotal,
      sharedEssential, sharedOptional,
      gapEssential, gapOptional,
      gapCount: gapEssential.length + gapOptional.length,
      sharedKnowledge, gapKnowledge,
      transferable,
    }
  }, [selectedOcc, occupationsData, profileSkillUris, perfilSkills])

  // Similar occupations for Panel 5 (caminos alternativos)
  const alternatives = useMemo(() => {
    if (!selectedOcc || !occupationsData || !gapAnalysis || gapAnalysis.gapEssential.length < 3) return []
    const occId = selectedOcc.uri.split('/').pop() || ''
    const occ = occupationsData[occId]
    if (!occ?.similar) return []

    return occ.similar
      .slice(0, 10)
      .map((s: any) => {
        const altOcc = occupationsData[s.id]
        if (!altOcc?.skills?.essential) return null
        const essential = altOcc.skills.essential
        const covered = essential.filter((sk: any) => profileSkillUris.has(`http://data.europa.eu/esco/skill/${sk.id}`)).length
        if (covered === 0) return null
        const total = essential.length
        const isco = (altOcc.isco || '').replace(/^C/, '')
        return {
          uri: `http://data.europa.eu/esco/occupation/${s.id}`,
          id: s.id,
          label: altOcc.label || s.label,
          isco_code: isco,
          matchScore: total > 0 ? Math.round((covered / total) * 100) : 0,
          gapCount: total - covered,
          ofertasCount: ofertasCountMap[isco] || 0,
        }
      })
      .filter(Boolean)
      .sort((a: any, b: any) => a.gapCount - b.gapCount || b.matchScore - a.matchScore)
      .slice(0, 5)
  }, [selectedOcc, occupationsData, profileSkillUris, gapAnalysis, ofertasCountMap])

  // Load perfil skills
  const loadPerfilSkills = useCallback(async (perfilId: string) => {
    setLoadingPerfil(true)
    try {
      const res = await fetch(`/api/perfiles?id=${perfilId}`)
      if (!res.ok) throw new Error()
      const data = await res.json()
      setPerfilSkills((data.skills || []).map((s: any) => ({
        skill_uri: s.skill_uri,
        skill_label: s.skill_label,
        type: s.via_captura,
      })))
    } catch {} finally {
      setLoadingPerfil(false)
    }
  }, [])

  // Load MOL profile for selected occupation (lazy)
  const loadMolProfile = useCallback(async (escoUri: string, iscoCode: string) => {
    setLoadingMol(true)
    setMolFreqs({})
    setMolOfertasCount(ofertasCountMap[iscoCode] || 0)
    try {
      const supabase = createBrowserClient(
        process.env.NEXT_PUBLIC_SUPABASE_URL!,
        process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
      )
      // Get ofertas for this occupation
      const { data: ofertas } = await supabase
        .from('ofertas_dashboard')
        .select('id_oferta')
        .eq('esco_occupation_uri', escoUri)
      if (ofertas && ofertas.length > 0) {
        setMolOfertasCount(ofertas.length)
        const ids = ofertas.map((o: any) => o.id_oferta)
        const { data: skills } = await supabase
          .from('ofertas_skills')
          .select('skill_uri')
          .in('id_oferta', ids.slice(0, 500))
        if (skills) {
          const counts: Record<string, number> = {}
          for (const s of skills) { if (s.skill_uri) counts[s.skill_uri] = (counts[s.skill_uri] || 0) + 1 }
          const freqs: Record<string, number> = {}
          const total = ofertas.length
          for (const [uri, count] of Object.entries(counts)) {
            freqs[uri] = Math.round((count / total) * 100)
          }
          setMolFreqs(freqs)
        }
      }
    } catch {} finally {
      setLoadingMol(false)
    }
  }, [ofertasCountMap])

  function handleSelectPerfil(p: PerfilResumen) {
    setPerfil(p)
    setSelectedOcc(null)
    const url = new URL(window.location.href)
    url.searchParams.set('perfil_id', p.id)
    url.searchParams.delete('occ_id')
    router.replace(url.pathname + url.search, { scroll: false })
    loadPerfilSkills(p.id)
  }

  function handleClearPerfil() {
    setPerfil(null)
    setPerfilSkills([])
    setSelectedOcc(null)
    const url = new URL(window.location.href)
    url.searchParams.delete('perfil_id')
    url.searchParams.delete('occ_id')
    router.replace(url.pathname, { scroll: false })
  }

  function handleSelectOcc(occ: OccDetail) {
    setSelectedOcc(occ)
    loadMolProfile(occ.uri, occ.isco_code)
  }

  function handleSelectAlternative(alt: any) {
    const occ: OccDetail = {
      uri: alt.uri,
      label: alt.label,
      isco_code: alt.isco_code,
      essentialCount: 0,
      optionalCount: 0,
    }
    setSelectedOcc(occ)
    loadMolProfile(occ.uri, occ.isco_code)
  }

  const ofertasBadge = (count: number) => count >= 5 ? '🟢' : count >= 1 ? '🟡' : '⚪'

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto px-4 py-6">
        <OEBreadcrumb items={[{ label: 'Futuro Laboral' }]} />

        <div className="mb-5">
          <div className="flex items-center gap-2 mb-1">
            <Map className="w-5 h-5 text-purple-600" />
            <h1 className="text-xl font-bold text-gray-900">Futuro Laboral</h1>
          </div>
          <p className="text-sm text-gray-500">
            Elegí una persona y una ocupación objetivo para ver el plan de transición laboral
          </p>
        </div>

        {/* Selectors */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-5">
          <div>
            <label className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-1.5 block">Persona</label>
            <PersonaSelector selectedId={initialPerfilId} onSelect={handleSelectPerfil} onClear={handleClearPerfil} />
          </div>
          <div>
            <label className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-1.5 block">Ocupación objetivo</label>
            <OcupacionObjetivoSelector
              disabled={!perfil || loadingPerfil}
              matches={matchingOccupations}
              selected={selectedOcc}
              onSelect={handleSelectOcc}
              onClear={() => setSelectedOcc(null)}
            />
          </div>
        </div>

        {/* Empty state */}
        {(!perfil || !selectedOcc) && !loadingPerfil && (
          <div className="bg-white rounded-xl border border-gray-200 p-12 text-center">
            <Map className="w-10 h-10 text-gray-300 mx-auto mb-3" />
            <p className="text-sm text-gray-500">
              {!perfil ? 'Seleccioná una persona y una ocupación objetivo' : 'Seleccioná una ocupación objetivo'}
            </p>
          </div>
        )}

        {loadingPerfil && (
          <div className="bg-white rounded-xl border border-gray-200 p-12 flex items-center justify-center gap-2">
            <Loader2 className="w-5 h-5 animate-spin text-purple-600" />
            <span className="text-sm text-gray-500">Cargando perfil...</span>
          </div>
        )}

        {/* Analysis */}
        {perfil && selectedOcc && gapAnalysis && (
          <div className="space-y-4">

            {/* Banner */}
            <div className="bg-white rounded-xl border border-gray-200 p-4">
              <p className="text-sm font-semibold text-gray-900 mb-3">
                {perfil.nombre} → {selectedOcc.label}
              </p>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-xs text-gray-500 mb-1">Compatibilidad</p>
                  <div className="flex items-center gap-2">
                    <div className="flex-1 h-2.5 bg-gray-100 rounded-full overflow-hidden">
                      <div className={`h-full rounded-full ${barColor(gapAnalysis.compatibility)}`} style={{ width: `${gapAnalysis.compatibility}%` }} />
                    </div>
                    <span className="text-sm font-bold text-gray-800">{gapAnalysis.compatibility}%</span>
                  </div>
                  <p className="text-xs text-gray-400 mt-1">
                    {gapAnalysis.sharedEssential.length} de {gapAnalysis.essentialTotal} esenciales · {gapAnalysis.gapEssential.length} por cubrir
                  </p>
                </div>
                <div>
                  <p className="text-xs text-gray-500 mb-1">Demanda</p>
                  <p className="text-sm font-bold text-gray-800">
                    {ofertasBadge(molOfertasCount)} {molOfertasCount} ofertas activas
                  </p>
                  {molOfertasCount > 0 && (
                    <button onClick={() => setModalOpen(true)} className="text-xs text-teal-600 hover:text-teal-700 font-medium mt-1">
                      Ver las {molOfertasCount} ofertas →
                    </button>
                  )}
                </div>
              </div>
            </div>

            {/* Panel 1 — Lo que ya tiene */}
            {(gapAnalysis.sharedEssential.length > 0 || gapAnalysis.sharedOptional.length > 0) && (
              <div className="bg-white rounded-xl border border-gray-200 p-4">
                <h3 className="text-sm font-semibold text-green-700 mb-1">
                  Lo que ya tiene ({gapAnalysis.sharedEssential.length + gapAnalysis.sharedOptional.length} skills)
                </h3>
                <p className="text-xs text-gray-400 mb-3">Del perfil del candidato, requeridas por la ocupación</p>

                {gapAnalysis.sharedEssential.length > 0 && (
                  <div className="mb-3">
                    <p className="text-xs font-medium text-gray-500 mb-1">ESENCIALES ({gapAnalysis.sharedEssential.length})</p>
                    <div className="space-y-1">
                      {gapAnalysis.sharedEssential.map((s: any) => {
                        const uri = `http://data.europa.eu/esco/skill/${s.id}`
                        const freq = skillsSearchable[uri] || 0
                        const d = demandLabel(freq)
                        return (
                          <div key={s.id} className="flex items-center gap-2">
                            <Check className="w-3 h-3 text-green-500 shrink-0" />
                            <span className="text-xs text-gray-700 flex-1">{s.label}</span>
                            {freq > 0 && <span className="text-[10px] text-gray-400">{d.bars} {d.label}</span>}
                          </div>
                        )
                      })}
                    </div>
                  </div>
                )}

                {gapAnalysis.sharedOptional.length > 0 && (
                  <div>
                    <p className="text-xs font-medium text-gray-500 mb-1">OPCIONALES ({gapAnalysis.sharedOptional.length})</p>
                    <div className="space-y-1">
                      {gapAnalysis.sharedOptional.map((s: any) => {
                        const uri = `http://data.europa.eu/esco/skill/${s.id}`
                        const freq = skillsSearchable[uri] || 0
                        const d = demandLabel(freq)
                        return (
                          <div key={s.id} className="flex items-center gap-2">
                            <Check className="w-3 h-3 text-green-500 shrink-0" />
                            <span className="text-xs text-gray-700 flex-1">{s.label}</span>
                            {freq > 0 && <span className="text-[10px] text-gray-400">{d.bars} {d.label}</span>}
                          </div>
                        )
                      })}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Panel 2 — Lo que necesita aprender */}
            {(gapAnalysis.gapEssential.length > 0 || gapAnalysis.gapOptional.length > 0) && (
              <div className="bg-white rounded-xl border border-gray-200 p-4">
                <h3 className="text-sm font-semibold text-red-600 mb-1">
                  Lo que necesita aprender ({gapAnalysis.gapEssential.length + gapAnalysis.gapOptional.length} skills)
                </h3>
                <p className="text-xs text-gray-400 mb-3">Requeridas por la ocupación, ausentes en el perfil</p>

                {gapAnalysis.gapEssential.length > 0 && (
                  <div className="mb-3">
                    <p className="text-xs font-medium text-gray-500 mb-1">PRIORIDAD ALTA — Esenciales ({gapAnalysis.gapEssential.length})</p>
                    <div className="space-y-1">
                      {gapAnalysis.gapEssential.map((s: any) => {
                        const uri = `http://data.europa.eu/esco/skill/${s.id}`
                        const pct = molFreqs[uri]
                        return (
                          <div key={s.id} className="flex items-center gap-2">
                            <XIcon className="w-3 h-3 text-red-400 shrink-0" />
                            <span className="text-xs text-gray-600 flex-1">{s.label}</span>
                            {pct !== undefined && (
                              <span className="text-[10px] text-gray-400">pedida en {pct}% de ofertas</span>
                            )}
                          </div>
                        )
                      })}
                    </div>
                  </div>
                )}

                {gapAnalysis.gapOptional.length > 0 && (
                  <div>
                    <p className="text-xs font-medium text-gray-500 mb-1">PRIORIDAD MEDIA — Opcionales ({gapAnalysis.gapOptional.length})</p>
                    <div className="space-y-1">
                      {gapAnalysis.gapOptional.map((s: any) => {
                        const uri = `http://data.europa.eu/esco/skill/${s.id}`
                        const pct = molFreqs[uri]
                        return (
                          <div key={s.id} className="flex items-center gap-2">
                            <XIcon className="w-3 h-3 text-orange-400 shrink-0" />
                            <span className="text-xs text-gray-600 flex-1">{s.label}</span>
                            {pct !== undefined && <span className="text-[10px] text-gray-400">pedida en {pct}% de ofertas</span>}
                          </div>
                        )
                      })}
                    </div>
                  </div>
                )}
                {loadingMol && <p className="text-[10px] text-gray-400 mt-2">Cargando datos de mercado...</p>}
              </div>
            )}

            {/* Panel 3 — Conocimientos */}
            {(gapAnalysis.sharedKnowledge.length > 0 || gapAnalysis.gapKnowledge.length > 0) && (
              <div className="bg-white rounded-xl border border-gray-200 p-4">
                <h3 className="text-sm font-semibold text-gray-700 mb-3">Conocimientos</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-xs font-medium text-green-600 mb-1">Ya tiene ({gapAnalysis.sharedKnowledge.length})</p>
                    <div className="space-y-1">
                      {gapAnalysis.sharedKnowledge.map((k: any) => (
                        <p key={k.id} className="text-xs text-gray-600">○ {k.label}</p>
                      ))}
                    </div>
                  </div>
                  <div>
                    <p className="text-xs font-medium text-red-500 mb-1">Necesita adquirir ({gapAnalysis.gapKnowledge.length})</p>
                    <div className="space-y-1">
                      {gapAnalysis.gapKnowledge.map((k: any) => (
                        <p key={k.id} className="text-xs text-gray-500">○ {k.label}</p>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Panel 4 — Skills transferibles */}
            {gapAnalysis.transferable.length > 0 && (
              <div className="bg-white rounded-xl border border-gray-200 p-4">
                <h3 className="text-sm font-semibold text-blue-700 mb-1">
                  Skills transferibles ({gapAnalysis.transferable.length})
                </h3>
                <p className="text-xs text-gray-400 mb-2">Las tiene pero la ocupación objetivo no las requiere</p>
                <div className="flex flex-wrap gap-1.5">
                  {gapAnalysis.transferable.slice(0, 10).map((s, i) => (
                    <span key={i} className="text-xs bg-blue-50 text-blue-700 px-2 py-0.5 rounded">
                      {s.skill_label}
                    </span>
                  ))}
                  {gapAnalysis.transferable.length > 10 && (
                    <span className="text-xs text-gray-400">+{gapAnalysis.transferable.length - 10} más</span>
                  )}
                </div>
              </div>
            )}

            {/* Panel 5 — Caminos alternativos (solo si gap ≥ 3) */}
            {alternatives.length > 0 && (
              <div className="bg-white rounded-xl border border-gray-200 p-4">
                <h3 className="text-sm font-semibold text-gray-700 mb-1">
                  Caminos alternativos
                </h3>
                <p className="text-xs text-gray-400 mb-3">Ocupaciones similares que puede alcanzar antes</p>
                <div className="space-y-2">
                  {alternatives.map((alt: any) => (
                    <div key={alt.id} className="flex items-center gap-3 py-2 border-b border-gray-50 last:border-b-0">
                      <div className="flex-1 min-w-0">
                        <span className="text-sm text-gray-900">{alt.label}</span>
                        <span className="text-xs text-gray-400 ml-2">ISCO {alt.isco_code}</span>
                      </div>
                      <div className="flex items-center gap-2 shrink-0">
                        <div className="w-12 h-1.5 bg-gray-100 rounded-full overflow-hidden">
                          <div className={`h-full rounded-full ${barColor(alt.matchScore)}`} style={{ width: `${alt.matchScore}%` }} />
                        </div>
                        <span className="text-xs font-medium text-gray-600 w-8">{alt.matchScore}%</span>
                        <span className="text-xs text-gray-400">gap: {alt.gapCount}</span>
                        <span className="text-xs">{ofertasBadge(alt.ofertasCount)} {alt.ofertasCount} ofertas</span>
                      </div>
                      <button
                        onClick={() => handleSelectAlternative(alt)}
                        className="text-xs text-purple-600 hover:text-purple-700 font-medium shrink-0 flex items-center gap-0.5"
                      >
                        Elegir <ArrowRight className="w-3 h-3" />
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      <OfertasModal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        iscoCode={selectedOcc?.isco_code || ''}
        label={selectedOcc?.label || ''}
      />
    </div>
  )
}
