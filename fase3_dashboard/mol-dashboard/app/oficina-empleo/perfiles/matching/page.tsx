'use client'

import { useState, useEffect, useCallback, useRef, useMemo } from 'react'
import { useSearchParams, useRouter } from 'next/navigation'
import { Loader2, Target, ArrowUpDown } from 'lucide-react'
import { OEBreadcrumb } from '@/components/oficina-empleo/OEBreadcrumb'
import { PersonaSelector, type PerfilResumen } from '@/components/oficina-empleo/PersonaSelector'
import { OccupationMatchCard } from '@/components/oficina-empleo/OccupationMatchCard'
import { type OccSkillDetail } from '@/components/oficina-empleo/getSkillsForOccupation'
import { createBrowserClient } from '@supabase/ssr'

let _supabase: ReturnType<typeof createBrowserClient> | null = null
function getSupabase() {
  if (!_supabase) _supabase = createBrowserClient(process.env.NEXT_PUBLIC_SUPABASE_URL!, process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!)
  return _supabase
}
import { OfertasModal } from '@/components/oficina-empleo/OfertasModal'

export interface OccupationMatch {
  uri: string
  label: string
  isco_code: string
  matchScore: number
  essentialTotal: number
  essentialCovered: number
  optionalCovered: number
  gapCount: number
}

type SortBy = 'match' | 'gap' | 'ofertas' | 'alpha'

const SORT_OPTIONS: { id: SortBy; label: string }[] = [
  { id: 'match', label: 'Mejor match' },
  { id: 'gap', label: 'Menor gap' },
  { id: 'ofertas', label: 'Más ofertas' },
  { id: 'alpha', label: 'Alfabético' },
]

export default function MatchingPage() {
  const searchParams = useSearchParams()
  const router = useRouter()
  const initialPerfilId = searchParams.get('perfil_id')

  const [perfil, setPerfil] = useState<PerfilResumen | null>(null)
  const [profileSkillUris, setProfileSkillUris] = useState<Set<string>>(new Set())
  const [occupationsData, setOccupationsData] = useState<Record<string, any> | null>(null)
  const [loading, setLoading] = useState(false)
  const [mensaje, setMensaje] = useState<string | null>(null)
  const [sortBy, setSortBy] = useState<SortBy>('match')

  // Ofertas count map (loaded once)
  const [ofertasCountMap, setOfertasCountMap] = useState<Record<string, number>>({})

  // Modal
  const [modalIsco, setModalIsco] = useState('')
  const [modalLabel, setModalLabel] = useState('')
  const [modalOpen, setModalOpen] = useState(false)

  // Cache for expanded card skills
  const occSkillsCache = useRef<Record<string, OccSkillDetail[]>>({})

  // Load occupation JSON + ofertas count on mount
  useEffect(() => {
    fetch('/data/occupation_full_detail.json')
      .then(r => r.ok ? r.json() : null)
      .then(d => { if (d) setOccupationsData(d) })
      .catch(() => {})

    // Ofertas count via RPC (fast — single query, no 37K row download)
    getSupabase().rpc('get_ofertas_count_by_isco').then(({ data, error }) => {
      if (!error && data) {
        const map: Record<string, number> = {}
        for (const row of data) map[row.isco_code] = Number(row.count)
        setOfertasCountMap(map)
      }
    })
  }, [])

  // Load profile skills when perfil is selected
  const loadPerfilSkills = useCallback(async (perfilId: string) => {
    setLoading(true)
    setMensaje(null)
    setProfileSkillUris(new Set())
    try {
      const res = await fetch(`/api/perfiles?id=${perfilId}`)
      if (!res.ok) throw new Error(`Error ${res.status}`)
      const data = await res.json()
      const skills = data.skills || []
      if (skills.length === 0) {
        setMensaje('sin_skills')
        return
      }
      const uris = new Set<string>(skills.map((s: any) => s.skill_uri).filter(Boolean))
      setProfileSkillUris(uris)
    } catch (e) {
      console.error('Error loading perfil:', e)
      setMensaje('error')
    } finally {
      setLoading(false)
    }
  }, [])

  // Client-side matching: plan_OE_MVP.md lines 667-694
  const matches = useMemo(() => {
    if (profileSkillUris.size === 0 || !occupationsData) return []

    const results: OccupationMatch[] = []

    for (const [id, occ] of Object.entries(occupationsData) as [string, any][]) {
      const essential = occ.skills?.essential ?? []
      const optional = occ.skills?.optional ?? []

      const essentialCovered = essential.filter((s: any) => profileSkillUris.has(`http://data.europa.eu/esco/skill/${s.id}`)).length
      const optionalCovered = optional.filter((s: any) => profileSkillUris.has(`http://data.europa.eu/esco/skill/${s.id}`)).length
      const essentialTotal = essential.length

      if (essentialCovered === 0) continue

      const matchScore = essentialTotal > 0
        ? Math.round((essentialCovered / essentialTotal) * 100)
        : 0

      // isco field has "C" prefix (e.g. "C7212"), ofertas_dashboard uses without prefix ("7212")
      const rawIsco = occ.isco || occ.isco_code || ''
      const iscoCode = rawIsco.replace(/^C/, '')

      results.push({
        uri: `http://data.europa.eu/esco/occupation/${id}`,
        label: occ.label || id,
        isco_code: iscoCode,
        matchScore,
        essentialTotal,
        essentialCovered,
        optionalCovered,
        gapCount: essentialTotal - essentialCovered,
      })
    }

    return results
  }, [profileSkillUris, occupationsData])

  function handleSelectPerfil(p: PerfilResumen) {
    setPerfil(p)
    const url = new URL(window.location.href)
    url.searchParams.set('perfil_id', p.id)
    router.replace(url.pathname + url.search, { scroll: false })
    loadPerfilSkills(p.id)
  }

  function handleClear() {
    setPerfil(null)
    setProfileSkillUris(new Set())
    setMensaje(null)
    const url = new URL(window.location.href)
    url.searchParams.delete('perfil_id')
    router.replace(url.pathname, { scroll: false })
  }

  const handleLoadOccSkills = useCallback(async (uri: string): Promise<OccSkillDetail[]> => {
    if (occSkillsCache.current[uri]) return occSkillsCache.current[uri]
    // Use occupation_full_detail.json directly (already loaded)
    const occId = uri.split('/').pop() || ''
    if (occupationsData?.[occId]?.skills) {
      const occ = occupationsData[occId]
      const essential = (occ.skills.essential || []).map((s: any) => ({ ...s, type: 'skill', essential: true, total: 0 }))
      const optional = (occ.skills.optional || []).map((s: any) => ({ ...s, type: 'skill', essential: false, total: 0 }))
      const skills = [...essential, ...optional]
      occSkillsCache.current[uri] = skills
      return skills
    }
    return []
  }, [occupationsData])

  function handleOpenModal(iscoCode: string, label: string) {
    setModalIsco(iscoCode)
    setModalLabel(label)
    setModalOpen(true)
  }

  // Sort
  const sorted = useMemo(() => {
    return [...matches].sort((a, b) => {
      switch (sortBy) {
        case 'gap':
          if (a.gapCount !== b.gapCount) return a.gapCount - b.gapCount
          return b.matchScore - a.matchScore
        case 'ofertas': {
          const ca = ofertasCountMap[a.isco_code] || 0
          const cb = ofertasCountMap[b.isco_code] || 0
          if (cb !== ca) return cb - ca
          return b.matchScore - a.matchScore
        }
        case 'alpha':
          return a.label.localeCompare(b.label)
        default:
          if (b.matchScore !== a.matchScore) return b.matchScore - a.matchScore
          return a.gapCount - b.gapCount
      }
    })
  }, [matches, sortBy, ofertasCountMap])

  const loadingAll = loading || (perfil && profileSkillUris.size > 0 && !occupationsData)

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto px-4 py-6">
        <OEBreadcrumb items={[{ label: 'Oportunidades Laborales' }]} />

        {/* Header */}
        <div className="mb-5">
          <div className="flex items-center gap-2 mb-1">
            <Target className="w-5 h-5 text-blue-600" />
            <h1 className="text-xl font-bold text-gray-900">Oportunidades Laborales</h1>
          </div>
          <p className="text-sm text-gray-500">
            Seleccioná un perfil para ver ocupaciones compatibles con sus competencias
          </p>
        </div>

        {/* Persona selector */}
        <div className="mb-5">
          <label className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-1.5 block">Persona</label>
          <PersonaSelector
            selectedId={initialPerfilId}
            onSelect={handleSelectPerfil}
            onClear={handleClear}
          />
        </div>

        {/* Empty state */}
        {!perfil && !loading && (
          <div className="bg-white rounded-xl border border-gray-200 p-12 text-center">
            <Target className="w-10 h-10 text-gray-300 mx-auto mb-3" />
            <p className="text-sm text-gray-500">Seleccioná una persona para ver sus ocupaciones compatibles</p>
          </div>
        )}

        {/* Loading */}
        {loadingAll && (
          <div className="bg-white rounded-xl border border-gray-200 p-12 flex items-center justify-center gap-3">
            <Loader2 className="w-5 h-5 animate-spin text-blue-600" />
            <span className="text-sm text-gray-500">Buscando ocupaciones compatibles...</span>
          </div>
        )}

        {/* Sin skills */}
        {!loading && mensaje === 'sin_skills' && (
          <div className="bg-white rounded-xl border border-gray-200 p-8 text-center">
            <p className="text-sm text-gray-600">
              El perfil no tiene competencias cargadas. Completá el perfil primero.
            </p>
          </div>
        )}

        {/* Error */}
        {!loading && mensaje === 'error' && (
          <div className="bg-red-50 border border-red-200 rounded-xl p-4 text-center">
            <p className="text-sm text-red-700">Error cargando el perfil. Intentá de nuevo.</p>
          </div>
        )}

        {/* Results */}
        {!loadingAll && !mensaje && perfil && matches.length > 0 && (
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <p className="text-xs text-gray-400">
                {matches.length} ocupaciones compatibles · basado en {profileSkillUris.size} skills
              </p>
              <div className="flex items-center gap-1.5">
                <ArrowUpDown className="w-3 h-3 text-gray-400" />
                <select
                  value={sortBy}
                  onChange={e => setSortBy(e.target.value as SortBy)}
                  className="text-xs text-gray-600 bg-transparent border-none cursor-pointer focus:outline-none"
                >
                  {SORT_OPTIONS.map(o => (
                    <option key={o.id} value={o.id}>{o.label}</option>
                  ))}
                </select>
              </div>
            </div>

            {sorted.map((o, i) => (
              <OccupationMatchCard
                key={o.uri}
                occupation={o}
                rank={i + 1}
                perfilId={perfil!.id}
                ofertasCount={ofertasCountMap[o.isco_code] || 0}
                onLoadOccupationSkills={handleLoadOccSkills}
                onOpenModal={handleOpenModal}
              />
            ))}
          </div>
        )}

        {/* No results */}
        {!loadingAll && !mensaje && perfil && profileSkillUris.size > 0 && matches.length === 0 && (
          <div className="bg-white rounded-xl border border-gray-200 p-8 text-center">
            <p className="text-sm text-gray-600">
              No encontramos ocupaciones con al menos 1 skill en común.
            </p>
            <p className="text-sm text-gray-500 mt-1">
              Completá más el perfil para ver resultados.
            </p>
          </div>
        )}
      </div>

      {/* Modal ofertas */}
      <OfertasModal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        iscoCode={modalIsco}
        label={modalLabel}
      />
    </div>
  )
}
