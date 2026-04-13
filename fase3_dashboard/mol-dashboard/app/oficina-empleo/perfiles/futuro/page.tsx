'use client'

import { useState, useEffect, useCallback, useMemo } from 'react'
import { useSearchParams, useRouter } from 'next/navigation'
import { Loader2, Map, Check, X as XIcon, ArrowRight, ExternalLink, ChevronDown, ChevronUp, BookOpen } from 'lucide-react'
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
import { normalizeProvinciaToRegice } from '@/components/oficina-empleo/normalizeProvinciaToRegice'

import type { OccupationMatch } from '@/app/oficina-empleo/perfiles/matching/page'
import { calculateOccupationMatch, type ProfileSkill } from '@/lib/matching'

interface PerfilSkill {
  skill_uri: string
  skill_label: string
  type?: string
  nivel?: string | null
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

  // Provincia (MOL format, for filtering ofertas)
  const [perfilProvincia, setPerfilProvincia] = useState<string | null>(null)

  // Modal
  const [modalOpen, setModalOpen] = useState(false)

  // Cursos gap
  const [cursosGap, setCursosGap] = useState<any[]>([])
  const [loadingCursos, setLoadingCursos] = useState(false)
  const [provinciaCursos, setProvinciaCursos] = useState('')
  const [showAllCursos, setShowAllCursos] = useState(false)

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

  // Client-side matching with nivel weighting — for "Mis matches" in occupation selector
  const matchingOccupations = useMemo((): OccupationMatch[] => {
    if (perfilSkills.length === 0 || !occupationsData) return []
    const results: OccupationMatch[] = []
    for (const [id, occ] of Object.entries(occupationsData) as [string, any][]) {
      const result = calculateOccupationMatch(
        perfilSkills,
        occ.skills?.essential ?? [],
        occ.skills?.optional ?? []
      )
      if (result.sharedEssential.length === 0) continue
      results.push({
        uri: `http://data.europa.eu/esco/occupation/${id}`,
        label: occ.label || id,
        isco_code: (occ.isco || '').replace(/^C/, ''),
        matchScore: result.matchScore,
        essentialTotal: result.essentialTotal,
        essentialCovered: result.sharedEssential.length,
        optionalCovered: result.sharedOptional.length,
        gapCount: result.gapCount,
      })
    }
    results.sort((a, b) => b.matchScore - a.matchScore || a.gapCount - b.gapCount)
    return results
  }, [perfilSkills, occupationsData])

  // Gap analysis — uses calculateOccupationMatch + separate knowledge calc
  const gapAnalysis = useMemo(() => {
    if (!selectedOcc || !occupationsData) return null
    const occId = selectedOcc.uri.split('/').pop() || ''
    const occ = occupationsData[occId]
    if (!occ?.skills) return null

    const result = calculateOccupationMatch(
      perfilSkills,
      occ.skills.essential || [],
      occ.skills.optional || []
    )

    // Knowledge (separate — not handled by calculateOccupationMatch)
    const knowledgeRaw = occ.knowledge || {}
    const knowledgeB = [...(knowledgeRaw.essential || []), ...(knowledgeRaw.optional || [])]
    const profileUriSet = new Set(perfilSkills.map(s => s.skill_uri))
    const sharedKnowledge = knowledgeB.filter((k: any) => profileUriSet.has(`http://data.europa.eu/esco/skill/${k.id}`))
    const gapKnowledge = knowledgeB.filter((k: any) => !profileUriSet.has(`http://data.europa.eu/esco/skill/${k.id}`))

    return {
      compatibility: result.matchScore,
      essentialTotal: result.essentialTotal,
      sharedEssential: result.sharedEssential,
      sharedOptional: result.sharedOptional,
      gapEssential: result.gapEssential,
      gapOptional: result.gapOptional,
      gapCount: result.gapCount,
      sharedKnowledge,
      gapKnowledge,
      transferable: result.transferable,
    }
  }, [selectedOcc, occupationsData, perfilSkills])

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
        const result = calculateOccupationMatch(perfilSkills, altOcc.skills.essential, [])
        if (result.sharedEssential.length === 0) return null
        const isco = (altOcc.isco || '').replace(/^C/, '')
        return {
          uri: `http://data.europa.eu/esco/occupation/${s.id}`,
          id: s.id,
          label: altOcc.label || s.label,
          isco_code: isco,
          matchScore: result.matchScore,
          gapCount: result.gapCount,
          ofertasCount: ofertasCountMap[isco] || 0,
        }
      })
      .filter(Boolean)
      .sort((a: any, b: any) => a.gapCount - b.gapCount || b.matchScore - a.matchScore)
      .slice(0, 5)
  }, [selectedOcc, occupationsData, perfilSkills, gapAnalysis, ofertasCountMap])

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
        nivel: s.nivel ?? null,
      })))
      // Pre-select provincia for cursos panel + ofertas filter
      const ubi = data.personas?.ubicacion
      if (ubi) {
        const parts = ubi.split(',')
        setPerfilProvincia(parts.length > 1 ? parts[parts.length - 1].trim() : ubi.trim())
      }
      const prov = normalizeProvinciaToRegice(ubi)
      if (prov) setProvinciaCursos(prov)
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

  // Fetch cursos when gap changes
  const fetchCursosGap = useCallback(async (gapEssential: any[], prov: string) => {
    if (gapEssential.length === 0) { setCursosGap([]); return }
    setLoadingCursos(true)
    setShowAllCursos(false)
    try {
      const gapUris = gapEssential.map((s: any) => `http://data.europa.eu/esco/skill/${s.id}`)
      const res = await fetch('/api/perfiles/cursos-gap', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ gap_skill_uris: gapUris, provincia: prov || null }),
      })
      if (res.ok) {
        const data = await res.json()
        setCursosGap(data.cursos || [])
      }
    } catch {} finally {
      setLoadingCursos(false)
    }
  }, [])

  useEffect(() => {
    if (gapAnalysis && gapAnalysis.gapEssential.length > 0) {
      fetchCursosGap(gapAnalysis.gapEssential, provinciaCursos)
    } else {
      setCursosGap([])
    }
  }, [gapAnalysis, provinciaCursos, fetchCursosGap])

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
    setProvinciaCursos('')
    setCursosGap([])
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

            {/* Panel 2b — Dónde aprender lo que falta */}
            {gapAnalysis.gapEssential.length > 0 && (
              <CursosGapPanel
                cursos={cursosGap}
                loading={loadingCursos}
                showAll={showAllCursos}
                onShowAll={() => setShowAllCursos(true)}
                sharedCount={gapAnalysis.sharedEssential.length}
                essentialTotal={gapAnalysis.essentialTotal}
              />
            )}

            {/* Panel 3 — Conocimientos (fusionado con competencias — no se muestra separado) */}

            {/* Panel 4 — Skills transferibles */}
            {gapAnalysis.transferable.length > 0 && (
              <TransferableSkillsPanel skills={gapAnalysis.transferable} />
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
        provincia={perfilProvincia}
      />
    </div>
  )
}

function TransferableSkillsPanel({ skills }: { skills: ProfileSkill[] }) {
  const [showAll, setShowAll] = useState(false)
  const visible = showAll ? skills : skills.slice(0, 10)
  const hiddenCount = skills.length - 10

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-4">
      <h3 className="text-sm font-semibold text-blue-700 mb-1">
        Skills transferibles ({skills.length})
      </h3>
      <p className="text-xs text-gray-400 mb-2">Las tiene pero la ocupacion objetivo no las requiere</p>
      <div className="flex flex-wrap gap-1.5">
        {visible.map((s, i) => (
          <span key={i} className="text-xs bg-blue-50 text-blue-700 px-2 py-0.5 rounded">
            {s.skill_label || s.skill_uri}
          </span>
        ))}
        {!showAll && hiddenCount > 0 && (
          <button
            onClick={() => setShowAll(true)}
            className="text-xs text-blue-600 hover:text-blue-700 font-medium px-2 py-0.5"
          >
            +{hiddenCount} mas — Ver todas
          </button>
        )}
        {showAll && skills.length > 10 && (
          <button
            onClick={() => setShowAll(false)}
            className="text-xs text-gray-400 hover:text-gray-600 font-medium px-2 py-0.5"
          >
            Ver menos
          </button>
        )}
      </div>
    </div>
  )
}

function CursosGapPanel({ cursos, loading, showAll, onShowAll, sharedCount, essentialTotal }: {
  cursos: any[]
  loading: boolean
  showAll: boolean
  onShowAll: () => void
  sharedCount: number
  essentialTotal: number
}) {
  const [expandedIdx, setExpandedIdx] = useState<number | null>(null)

  const compatActual = essentialTotal > 0 ? Math.round((sharedCount / essentialTotal) * 100) : 0

  // Sort by mejora DESC (client-side, no refetch)
  const sorted = useMemo(() => {
    return [...cursos].map(c => {
      const proyectada = essentialTotal > 0
        ? Math.round(((sharedCount + c.skills_cubiertas) / essentialTotal) * 100)
        : 0
      return { ...c, compatProyectada: Math.min(proyectada, 100), mejora: Math.min(proyectada, 100) - compatActual }
    }).sort((a, b) => b.mejora - a.mejora)
  }, [cursos, sharedCount, essentialTotal, compatActual])

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-4">
      <div className="flex items-center gap-2 mb-1">
        <BookOpen className="w-4 h-4 text-purple-600" />
        <h3 className="text-sm font-semibold text-purple-700">Dónde aprender lo que falta</h3>
      </div>
      <p className="text-xs text-gray-400 mb-3">Cursos que cubren las skills ausentes del perfil</p>

      {loading && (
        <div className="flex items-center gap-2 py-4 justify-center text-gray-400">
          <Loader2 className="w-4 h-4 animate-spin" />
          <span className="text-xs">Buscando cursos...</span>
        </div>
      )}

      {!loading && sorted.length === 0 && (
        <p className="text-xs text-gray-400 text-center py-3">
          No encontramos cursos registrados para las skills que le faltan.
        </p>
      )}

      {!loading && sorted.length > 0 && (
        <div className="space-y-2">
          {(showAll ? sorted : sorted.slice(0, 3)).map((c: any, i: number) => {
            const isExpanded = expandedIdx === i
            const skills = c.skills_detalle || []
            const skillLabels = skills.map((s: any) => s.label)
            const modalColor = (c.modalidad || '').toLowerCase().includes('virtual') ? 'bg-green-100 text-green-700'
              : (c.modalidad || '').toLowerCase().includes('semi') ? 'bg-blue-100 text-blue-700'
              : 'bg-gray-100 text-gray-600'

            return (
              <div key={`${c.curso_id}-${c.provincia}-${i}`} className="border rounded-lg overflow-hidden">
                {/* Summary — clickable */}
                <button
                  onClick={() => setExpandedIdx(isExpanded ? null : i)}
                  className="w-full p-3 text-left hover:bg-gray-50 transition-colors"
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900">{c.titulo}</p>
                      <p className="text-xs text-gray-500 mt-0.5">
                        {c.institucion} · {c.municipio}, {c.provincia}
                      </p>
                      <div className="flex items-center gap-2 mt-1.5">
                        <span className={`text-[10px] px-1.5 py-0.5 rounded font-medium ${modalColor}`}>
                          {c.modalidad || 'Presencial'}
                        </span>
                        {c.carga_horaria > 0 && (
                          <span className="text-[10px] text-gray-400">{c.carga_horaria}hs</span>
                        )}
                        {c.mejora > 0 && (
                          <span className="text-xs text-green-600 font-semibold ml-auto">+{c.mejora}%</span>
                        )}
                      </div>
                      {!isExpanded && skillLabels.length > 0 && (
                        <p className="text-[10px] text-gray-400 mt-1">
                          {skillLabels.slice(0, 2).join(' · ')}
                          {skillLabels.length > 2 && ` · +${skillLabels.length - 2} más`}
                        </p>
                      )}
                    </div>
                    {isExpanded
                      ? <ChevronUp className="w-4 h-4 text-gray-400 shrink-0 mt-0.5" />
                      : <ChevronDown className="w-4 h-4 text-gray-400 shrink-0 mt-0.5" />
                    }
                  </div>
                </button>

                {/* Expanded detail */}
                {isExpanded && (
                  <div className="border-t px-3 py-3 bg-gray-50 space-y-3">
                    {/* Compatibility projection */}
                    <div>
                      <div className="flex items-center gap-2 mb-1.5">
                        <span className="text-xs text-gray-500 w-36 shrink-0">Compatibilidad actual:</span>
                        <div className="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden">
                          <div className="h-full bg-gray-400 rounded-full" style={{ width: `${compatActual}%` }} />
                        </div>
                        <span className="text-xs text-gray-600 w-8 text-right">{compatActual}%</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-xs text-gray-500 w-36 shrink-0">Si completás este curso:</span>
                        <div className="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden">
                          <div className="h-full bg-green-500 rounded-full" style={{ width: `${c.compatProyectada}%` }} />
                        </div>
                        <span className="text-xs text-gray-800 font-semibold w-8 text-right">{c.compatProyectada}%</span>
                        {c.mejora > 0 && (
                          <span className="text-xs text-green-600 font-semibold shrink-0">(+{c.mejora}%)</span>
                        )}
                      </div>
                    </div>

                    {/* Institution details */}
                    <div>
                      <p className="text-xs font-medium text-gray-600 mb-1">Institución</p>
                      <p className="text-xs text-gray-800">{c.institucion}</p>
                      <p className="text-xs text-gray-500">{c.municipio}, {c.provincia}</p>
                    </div>

                    {/* Course details */}
                    <div className="flex items-center gap-4">
                      <div>
                        <p className="text-xs font-medium text-gray-600">Modalidad</p>
                        <span className={`text-[10px] px-1.5 py-0.5 rounded font-medium ${modalColor}`}>
                          {c.modalidad || 'Presencial'}
                        </span>
                      </div>
                      {c.carga_horaria > 0 && (
                        <div>
                          <p className="text-xs font-medium text-gray-600">Duración</p>
                          <p className="text-xs text-gray-800">{c.carga_horaria} horas</p>
                        </div>
                      )}
                    </div>

                    {/* Skills covered */}
                    <div>
                      <p className="text-xs font-medium text-gray-600 mb-1">
                        Skills que cubre ({skills.length} de {c.total_gap_skills} faltantes)
                      </p>
                      <div className="space-y-0.5">
                        {skills.map((s: any, j: number) => (
                          <div key={j} className="flex items-center gap-1.5">
                            <Check className="w-3 h-3 text-purple-500 shrink-0" />
                            <span className="text-xs text-gray-700">{s.label}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )
          })}
          {!showAll && sorted.length > 3 && (
            <button
              onClick={onShowAll}
              className="text-xs text-purple-600 hover:text-purple-700 font-medium w-full text-center py-1"
            >
              + Ver {sorted.length - 3} cursos más
            </button>
          )}
        </div>
      )}
    </div>
  )
}
