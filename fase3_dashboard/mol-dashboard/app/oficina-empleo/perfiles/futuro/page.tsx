'use client'

import { useState, useEffect, useCallback, useMemo } from 'react'
import { useSearchParams, useRouter } from 'next/navigation'
import { Loader2, Map, Check, X as XIcon, ArrowRight, ExternalLink, ChevronDown, ChevronUp, BookOpen, MessageSquare } from 'lucide-react'
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

  // Demand trend indicators + projection
  const [demandTrend, setDemandTrend] = useState<{
    trend: 'up' | 'stable' | 'down'
    trendPct: number
    volatility: 'alta' | 'media' | 'baja'
    cv: number
    monthlyCounts: number[]
    months: string[]
    slope: number
    r2: number
    suficiente: boolean
  } | null>(null)

  // AI recommendation
  const [recomendacion, setRecomendacion] = useState<string | null>(null)
  const [loadingReco, setLoadingReco] = useState(false)
  const [recoError, setRecoError] = useState(false)

  // Loading & errors
  const [loadingPerfil, setLoadingPerfil] = useState(false)
  const [loadingMol, setLoadingMol] = useState(false)
  const [dataError, setDataError] = useState<string | null>(null)
  const [cursosError, setCursosError] = useState(false)

  // Load static data on mount
  useEffect(() => {
    fetch('/data/occupation_full_detail.json')
      .then(r => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json() })
      .then(d => setOccupationsData(d))
      .catch(() => setDataError('No se pudieron cargar las ocupaciones. Recargá la página.'))

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
      .catch(() => {}) // Not critical — demand indicators just won't show

    // Ofertas count via RPC (not critical — defaults to 0)
    getSupabase().rpc('get_ofertas_count_by_isco').then(({ data, error }) => {
      if (!error && data) {
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

    return {
      compatibility: result.matchScore,
      essentialTotal: result.essentialTotal,
      sharedEssential: result.sharedEssential,
      sharedOptional: result.sharedOptional,
      gapEssential: result.gapEssential,
      gapOptional: result.gapOptional,
      gapCount: result.gapCount,
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
    setDemandTrend(null)
    setMolOfertasCount(ofertasCountMap[iscoCode] || 0)
    try {
      // 1. Read pre-calculated trend from isco_demand_trend (single source of truth)
      const { data: trendRow } = await getSupabase()
        .from('isco_demand_trend')
        .select('*')
        .eq('isco_code', iscoCode)
        .maybeSingle()

      if (trendRow) {
        setMolOfertasCount(trendRow.ofertas_total || 0)
        const mc: number[] = (typeof trendRow.monthly_counts === 'string'
          ? JSON.parse(trendRow.monthly_counts) : trendRow.monthly_counts) || []
        const ml: string[] = (typeof trendRow.monthly_labels === 'string'
          ? JSON.parse(trendRow.monthly_labels) : trendRow.monthly_labels) || []

        if (trendRow.suficiente) {
          const trend: 'up' | 'stable' | 'down' =
            trendRow.trend_label === 'creciendo' ? 'up' : trendRow.trend_label === 'cayendo' ? 'down' : 'stable'
          const volatility: 'alta' | 'media' | 'baja' =
            trendRow.volatility_label === 'volatil' ? 'alta' : trendRow.volatility_label === 'variable' ? 'media' : 'baja'
          const recent = mc.length >= 6 ? (mc[mc.length-3] + mc[mc.length-2] + mc[mc.length-1]) / 3 : 0
          const previous = mc.length >= 6 ? (mc[mc.length-6] + mc[mc.length-5] + mc[mc.length-4]) / 3 : 0
          const trendPct = previous > 0 ? Math.round(((recent - previous) / previous) * 100) : 0
          setDemandTrend({
            trend, trendPct, volatility, cv: trendRow.volatility_cv || 0,
            monthlyCounts: mc, months: ml,
            slope: trendRow.trend_slope || 0, r2: trendRow.trend_r2 || 0, suficiente: true,
          })
        }
      }

      // 2. Load skill frequencies (for "pedida en X% de ofertas")
      const { data: ofertas } = await getSupabase()
        .from('ofertas_dashboard')
        .select('id_oferta')
        .eq('isco_code', iscoCode)
      if (ofertas && ofertas.length > 0) {
        if (!trendRow) setMolOfertasCount(ofertas.length)
        const ids = ofertas.map((o: any) => o.id_oferta)
        const { data: skills } = await getSupabase()
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
    setCursosError(false)
    try {
      const gapUris = gapEssential.map((s: any) => `http://data.europa.eu/esco/skill/${s.id}`)
      // First try with provincia filter
      let res = await fetch('/api/perfiles/cursos-gap', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ gap_skill_uris: gapUris, provincia: prov || null }),
      })
      if (res.ok) {
        const data = await res.json()
        if (data.cursos && data.cursos.length > 0) {
          setCursosGap(data.cursos)
        } else if (prov) {
          // No results with provincia — retry without filter (national)
          res = await fetch('/api/perfiles/cursos-gap', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ gap_skill_uris: gapUris }),
          })
          if (res.ok) {
            const data2 = await res.json()
            setCursosGap(data2.cursos || [])
          } else {
            setCursosError(true)
          }
        } else {
          setCursosGap([])
        }
      } else {
        setCursosError(true)
      }
    } catch {
      setCursosError(true)
    } finally {
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
    setRecomendacion(null)
    setRecoError(false)
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
    setRecomendacion(null)
    setRecoError(false)
    loadMolProfile(occ.uri, occ.isco_code)
  }

  async function handlePedirRecomendacion() {
    if (!perfil || !selectedOcc || !gapAnalysis) return
    setLoadingReco(true)
    setRecoError(false)
    setRecomendacion(null)
    try {
      const res = await fetch('/api/trayectoria-laboral', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          perfil: {
            nombre: perfil.nombre,
            skills_count: perfilSkills.length,
            ubicacion: perfilProvincia,
          },
          ocupacion: {
            label: selectedOcc.label,
            isco_code: selectedOcc.isco_code,
            compatibilidad: gapAnalysis.compatibility,
            esenciales_total: gapAnalysis.essentialTotal,
            cubiertas: gapAnalysis.sharedEssential.length,
          },
          tendencia: demandTrend ? {
            trend_label: demandTrend.trend === 'up' ? 'creciendo' : demandTrend.trend === 'down' ? 'cayendo' : 'estable',
            ofertas_total: molOfertasCount,
            volatilidad: demandTrend.volatility === 'alta' ? 'volatil' : demandTrend.volatility === 'media' ? 'variable' : 'estable',
          } : { trend_label: 'insuficiente', ofertas_total: molOfertasCount, volatilidad: 'desconocida' },
          gap_skills: gapAnalysis.gapEssential.map((s: any) => ({
            label: s.label,
            frecuencia_mercado: molFreqs[`http://data.europa.eu/esco/skill/${s.id}`] || null,
          })),
          skills_tiene: gapAnalysis.sharedEssential.slice(0, 5).map((s: any) => ({ label: s.label })),
          cursos: cursosGap.slice(0, 5).map((c: any) => ({
            titulo: c.titulo,
            institucion: c.institucion,
            skills_cubiertas: c.skills_cubiertas,
            provincia: c.provincia,
          })),
          alternativas: alternatives.slice(0, 3).map((a: any) => ({
            label: a.label,
            match: a.matchScore,
            ofertas: a.ofertasCount,
            tendencia: 'sin datos',
          })),
        }),
      })
      if (res.ok) {
        const data = await res.json()
        setRecomendacion(data.recomendacion || null)
      } else {
        setRecoError(true)
      }
    } catch {
      setRecoError(true)
    } finally {
      setLoadingReco(false)
    }
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

        {/* Data error */}
        {dataError && (
          <div className="bg-red-50 border border-red-200 rounded-xl p-4 text-center mb-4">
            <p className="text-sm text-red-700">{dataError}</p>
          </div>
        )}

        {/* Empty state */}
        {(!perfil || !selectedOcc) && !loadingPerfil && !dataError && (
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
                    {ofertasBadge(molOfertasCount)} {molOfertasCount} oferta{molOfertasCount !== 1 ? 's' : ''} activa{molOfertasCount !== 1 ? 's' : ''}
                  </p>
                  {molOfertasCount > 0 && (
                    <button onClick={() => setModalOpen(true)} className="text-xs text-teal-600 hover:text-teal-700 font-medium mt-1">
                      Ver {molOfertasCount === 1 ? 'la oferta' : `las ${molOfertasCount} ofertas`} →
                    </button>
                  )}
                </div>
              </div>

              {/* Demand trend + projection */}
              {demandTrend && (
                <DemandTrendPanel trend={demandTrend} />
              )}
              {loadingMol && !demandTrend && (
                <div className="mt-3 pt-3 border-t border-gray-100">
                  <div className="flex items-center gap-2 text-gray-400">
                    <Loader2 className="w-3 h-3 animate-spin" />
                    <span className="text-[10px]">Calculando tendencia...</span>
                  </div>
                </div>
              )}
              {!loadingMol && !demandTrend && (
                <div className="mt-3 pt-3 border-t border-gray-100">
                  <p className="text-[10px] text-gray-400">
                    Datos insuficientes para estimar la tendencia de demanda de esta ocupación. Se necesitan al menos 4 meses con ofertas publicadas en portales estables.
                  </p>
                </div>
              )}
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

            {/* Panel 2a — Recomendación IA */}
            {gapAnalysis && (
              <div className="bg-white rounded-xl border border-gray-200 p-4">
                <div className="flex items-center gap-2 mb-2">
                  <MessageSquare className="w-4 h-4 text-purple-600" />
                  <h3 className="text-sm font-semibold text-purple-700">Recomendación personalizada</h3>
                </div>

                {!recomendacion && !loadingReco && !recoError && (
                  <div className="text-center py-3">
                    <p className="text-xs text-gray-400 mb-3">
                      Analizamos el perfil, el gap de competencias, los cursos disponibles y la demanda del mercado para darte una recomendación concreta.
                    </p>
                    <button
                      onClick={handlePedirRecomendacion}
                      className="inline-flex items-center gap-1.5 bg-purple-600 text-white text-sm font-medium px-4 py-2 rounded-lg hover:bg-purple-700 transition-colors"
                    >
                      <MessageSquare className="w-3.5 h-3.5" />
                      Pedir recomendación
                    </button>
                  </div>
                )}

                {loadingReco && (
                  <div className="flex items-center justify-center gap-2 py-6 text-purple-400">
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span className="text-xs">Analizando perfil y mercado...</span>
                  </div>
                )}

                {recoError && (
                  <div className="text-center py-3">
                    <p className="text-xs text-red-500 mb-2">No se pudo generar la recomendación.</p>
                    <button
                      onClick={handlePedirRecomendacion}
                      className="text-xs text-purple-600 hover:text-purple-700 font-medium"
                    >
                      Reintentar
                    </button>
                  </div>
                )}

                {recomendacion && (
                  <div>
                    <p className="text-sm text-gray-700 leading-relaxed whitespace-pre-line">{recomendacion}</p>
                    <p className="text-[9px] text-gray-300 mt-3 leading-snug">
                      Generado con IA a partir de {molOfertasCount > 0 ? `${molOfertasCount} ofertas y ` : ''}datos del mercado laboral argentino.
                      Esta recomendación es orientativa y no constituye asesoramiento profesional.
                    </p>
                  </div>
                )}
              </div>
            )}

            {/* Panel 2b — Dónde aprender lo que falta */}
            {gapAnalysis.gapEssential.length > 0 && (
              <CursosGapPanel
                cursos={cursosGap}
                loading={loadingCursos}
                error={cursosError}
                showAll={showAllCursos}
                onShowAll={() => setShowAllCursos(true)}
                sharedCount={gapAnalysis.sharedEssential.length}
                essentialTotal={gapAnalysis.essentialTotal}
              />
            )}

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

function DemandTrendPanel({ trend }: { trend: {
  trend: 'up' | 'stable' | 'down'; trendPct: number
  volatility: 'alta' | 'media' | 'baja'; cv: number
  monthlyCounts: number[]; months: string[]
  slope: number; r2: number; suficiente: boolean
}}) {
  // Project 6 months ahead using slope from regression
  const mc = trend.monthlyCounts
  const n = mc.length
  const canProject = trend.suficiente && trend.r2 >= 0.3 && n >= 4

  // Build regression line for existing data
  const mean = mc.reduce((a, b) => a + b, 0) / (n || 1)
  // Simple linear fit on raw counts for display
  let fitSlope = 0, fitIntercept = mean
  if (n >= 2) {
    const xMean = (n - 1) / 2
    let ssxy = 0, ssxx = 0
    for (let i = 0; i < n; i++) { ssxy += (i - xMean) * (mc[i] - mean); ssxx += (i - xMean) ** 2 }
    fitSlope = ssxx > 0 ? ssxy / ssxx : 0
    fitIntercept = mean - fitSlope * xMean
  }

  // Generate projection months labels
  const projMonths = 6
  const projLabels: string[] = []
  if (trend.months.length > 0) {
    const last = trend.months[trend.months.length - 1]
    const [y, m] = last.split('-').map(Number)
    for (let i = 1; i <= projMonths; i++) {
      const d = new Date(y, m - 1 + i, 1)
      projLabels.push(`${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`)
    }
  }

  // Projected values
  const projValues = canProject
    ? Array.from({ length: projMonths }, (_, i) => Math.max(0, Math.round(fitIntercept + fitSlope * (n + i))))
    : []

  // All values for scale
  const allValues = [...mc, ...projValues]
  const maxVal = Math.max(...allValues, 1)
  const barH = 40

  // Month labels for display (short)
  const shortMonth = (label: string) => {
    const [, m] = label.split('-')
    const names = ['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic']
    return names[parseInt(m) - 1] || m
  }

  return (
    <div className="mt-3 pt-3 border-t border-gray-100">
      {/* Indicators row */}
      <div className="flex items-center gap-4 mb-3">
        <div className="flex items-center gap-1">
          <span className={`text-sm font-bold ${trend.trend === 'up' ? 'text-green-600' : trend.trend === 'down' ? 'text-red-500' : 'text-gray-600'}`}>
            {trend.trend === 'up' ? '↑' : trend.trend === 'down' ? '↓' : '→'}
          </span>
          <span className={`text-xs font-medium ${trend.trend === 'up' ? 'text-green-600' : trend.trend === 'down' ? 'text-red-500' : 'text-gray-500'}`}>
            {trend.trend === 'up' ? 'Creciendo' : trend.trend === 'down' ? 'Cayendo' : 'Estable'}
            {trend.trendPct !== 0 && ` ${trend.trendPct > 0 ? '+' : ''}${trend.trendPct}%`}
          </span>
        </div>
        <span className={`text-[10px] font-medium px-1.5 py-0.5 rounded ${
          trend.volatility === 'baja' ? 'bg-green-50 text-green-700' :
          trend.volatility === 'media' ? 'bg-yellow-50 text-yellow-700' :
          'bg-red-50 text-red-600'
        }`}>
          {trend.volatility === 'baja' ? 'Estable' : trend.volatility === 'media' ? 'Variable' : 'Volátil'}
        </span>
        {canProject && (
          <span className="text-[10px] text-gray-400 ml-auto">
            R² {(trend.r2 * 100).toFixed(0)}% — confianza {trend.r2 >= 0.6 ? 'alta' : 'moderada'}
          </span>
        )}
      </div>

      {/* Chart: historical bars + projection */}
      <div className="flex items-end gap-[3px]" style={{ height: `${barH + 16}px` }}>
        {/* Historical */}
        {mc.map((c, i) => {
          const h = Math.max(2, Math.round((c / maxVal) * barH))
          return (
            <div key={`h-${i}`} className="flex flex-col items-center gap-0.5" style={{ width: '24px' }}>
              <div
                className="w-full rounded-t-sm bg-teal-500"
                style={{ height: `${h}px` }}
                title={`${trend.months[i]}: ${c} ofertas (real)`}
              />
              <span className="text-[8px] text-gray-400 leading-none">{shortMonth(trend.months[i])}</span>
            </div>
          )
        })}

        {/* Separator */}
        {canProject && (
          <div className="flex flex-col items-center justify-end" style={{ width: '8px', height: `${barH}px` }}>
            <div className="w-px h-full border-l border-dashed border-gray-300" />
          </div>
        )}

        {/* Projection */}
        {projValues.map((c, i) => {
          const h = Math.max(2, Math.round((c / maxVal) * barH))
          return (
            <div key={`p-${i}`} className="flex flex-col items-center gap-0.5" style={{ width: '24px' }}>
              <div
                className="w-full rounded-t-sm bg-teal-200 border border-dashed border-teal-400"
                style={{ height: `${h}px` }}
                title={`${projLabels[i]}: ~${c} ofertas (proyección)`}
              />
              <span className="text-[8px] text-gray-300 leading-none">{shortMonth(projLabels[i])}</span>
            </div>
          )
        })}
      </div>

      {/* Legend */}
      <div className="flex items-center gap-3 mt-1.5">
        <div className="flex items-center gap-1">
          <div className="w-2 h-2 rounded-sm bg-teal-500" />
          <span className="text-[9px] text-gray-400">Datos reales</span>
        </div>
        {canProject && (
          <div className="flex items-center gap-1">
            <div className="w-2 h-2 rounded-sm bg-teal-200 border border-dashed border-teal-400" />
            <span className="text-[9px] text-gray-400">Proyección 6 meses</span>
          </div>
        )}
        {!canProject && (
          <span className="text-[9px] text-gray-300">Datos insuficientes para proyectar</span>
        )}
      </div>
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

function CursosGapPanel({ cursos, loading, error, showAll, onShowAll, sharedCount, essentialTotal }: {
  cursos: any[]
  loading: boolean
  error?: boolean
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

      {!loading && error && (
        <p className="text-xs text-red-500 text-center py-3">
          Error al buscar cursos. Intentá de nuevo.
        </p>
      )}

      {!loading && !error && sorted.length === 0 && (
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
