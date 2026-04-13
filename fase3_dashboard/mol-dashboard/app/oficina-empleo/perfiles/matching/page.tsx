'use client'

import { useState, useEffect, useCallback, useMemo } from 'react'
import { useSearchParams, useRouter } from 'next/navigation'
import { Loader2, Target, ArrowUpDown, Calendar } from 'lucide-react'
import { OEBreadcrumb } from '@/components/oficina-empleo/OEBreadcrumb'
import { PersonaSelector, type PerfilResumen } from '@/components/oficina-empleo/PersonaSelector'
import { OccupationMatchCard } from '@/components/oficina-empleo/OccupationMatchCard'
import { calculateOccupationMatch, type ProfileSkill } from '@/lib/matching'
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
type TimePeriod = '7d' | '30d' | 'all'

const SORT_OPTIONS: { id: SortBy; label: string }[] = [
  { id: 'match', label: 'Mejor match' },
  { id: 'gap', label: 'Menor gap' },
  { id: 'ofertas', label: 'Más ofertas' },
  { id: 'alpha', label: 'Alfabético' },
]

const TIME_OPTIONS: { id: TimePeriod; label: string }[] = [
  { id: '7d', label: 'Última semana' },
  { id: '30d', label: 'Último mes' },
  { id: 'all', label: 'Histórico' },
]

function getSinceDate(period: TimePeriod): string | null {
  if (period === 'all') return null
  const d = new Date()
  d.setDate(d.getDate() - (period === '7d' ? 7 : 30))
  return d.toISOString().split('T')[0]
}

export default function MatchingPage() {
  const searchParams = useSearchParams()
  const router = useRouter()
  const initialPerfilId = searchParams.get('perfil_id')

  const [perfil, setPerfil] = useState<PerfilResumen | null>(null)
  const [perfilProvincia, setPerfilProvincia] = useState<string | null>(null)
  const [profileSkills, setProfileSkills] = useState<ProfileSkill[]>([])
  const [occupationsData, setOccupationsData] = useState<Record<string, any> | null>(null)
  const [loading, setLoading] = useState(false)
  const [mensaje, setMensaje] = useState<string | null>(null)
  const [sortBy, setSortBy] = useState<SortBy>('match')
  const [timePeriod, setTimePeriod] = useState<TimePeriod>('30d')
  const [dataError, setDataError] = useState<string | null>(null)

  // Ofertas count map
  const [ofertasCountMap, setOfertasCountMap] = useState<Record<string, number>>({})
  const [countLoading, setCountLoading] = useState(false)

  // Modal
  const [modalIsco, setModalIsco] = useState('')
  const [modalLabel, setModalLabel] = useState('')
  const [modalOpen, setModalOpen] = useState(false)

  // Load occupation JSON on mount
  useEffect(() => {
    fetch('/data/occupation_full_detail.json')
      .then(r => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`)
        return r.json()
      })
      .then(d => setOccupationsData(d))
      .catch(() => setDataError('No se pudieron cargar las ocupaciones. Recargá la página.'))
  }, [])

  // Load ofertas count (re-runs when time period changes)
  useEffect(() => {
    setCountLoading(true)
    const since = getSinceDate(timePeriod)

    // Try RPC first (fast, pre-aggregated); fallback to direct query with date filter
    if (!since) {
      // Historical: use RPC (no date filter needed)
      getSupabase().rpc('get_ofertas_count_by_isco').then(({ data, error }) => {
        if (!error && data) {
          const map: Record<string, number> = {}
          for (const row of data) map[row.isco_code] = Number(row.count)
          setOfertasCountMap(map)
        }
        setCountLoading(false)
      })
    } else {
      // With date filter: direct query (RPC doesn't support since param)
      let query = getSupabase()
        .from('ofertas_dashboard')
        .select('isco_code')
        .not('isco_code', 'is', null)
        .gte('fecha_publicacion', since)
      query.then(({ data, error }) => {
        if (!error && data) {
          const map: Record<string, number> = {}
          for (const row of data as any[]) {
            if (row.isco_code) map[row.isco_code] = (map[row.isco_code] || 0) + 1
          }
          setOfertasCountMap(map)
        }
        setCountLoading(false)
      })
    }
  }, [timePeriod])

  // Load profile skills when perfil is selected
  const loadPerfilSkills = useCallback(async (perfilId: string) => {
    setLoading(true)
    setMensaje(null)
    setProfileSkills([])
    try {
      const res = await fetch(`/api/perfiles?id=${perfilId}`)
      if (!res.ok) throw new Error(`Error ${res.status}`)
      const data = await res.json()
      const skills = data.skills || []
      if (skills.length === 0) {
        setMensaje('sin_skills')
        return
      }
      setProfileSkills(skills.map((s: any) => ({
        skill_uri: s.skill_uri,
        nivel: s.nivel ?? null,
      })))
      // Extract provincia for filtering ofertas
      const ubi = data.personas?.ubicacion
      if (ubi) {
        // Try "ciudad, provincia" format; fallback to full string
        const parts = ubi.split(',').map((p: string) => p.trim()).filter(Boolean)
        const candidate = parts.length > 1 ? parts[parts.length - 1] : parts[0] || null
        // Normalize common variants
        const NORM: Record<string, string> = {
          'caba': 'Capital Federal', 'ciudad autónoma de buenos aires': 'Capital Federal',
          'ciudad autonoma de buenos aires': 'Capital Federal', 'cap. fed.': 'Capital Federal',
          'capital federal': 'Capital Federal', 'gba': 'Buenos Aires',
        }
        setPerfilProvincia(candidate ? (NORM[candidate.toLowerCase()] || candidate) : null)
      } else {
        setPerfilProvincia(null)
      }
    } catch (e) {
      console.error('Error loading perfil:', e)
      setMensaje('error')
    } finally {
      setLoading(false)
    }
  }, [])

  // Client-side matching with nivel weighting
  const matches = useMemo(() => {
    if (profileSkills.length === 0 || !occupationsData) return []

    const results: OccupationMatch[] = []

    for (const [id, occ] of Object.entries(occupationsData) as [string, any][]) {
      const result = calculateOccupationMatch(
        profileSkills,
        occ.skills?.essential ?? [],
        occ.skills?.optional ?? []
      )

      if (result.sharedEssential.length === 0) continue

      const rawIsco = occ.isco || occ.isco_code || ''
      const iscoCode = rawIsco.replace(/^C/, '')

      results.push({
        uri: `http://data.europa.eu/esco/occupation/${id}`,
        label: occ.label || id,
        isco_code: iscoCode,
        matchScore: result.matchScore,
        essentialTotal: result.essentialTotal,
        essentialCovered: result.sharedEssential.length,
        optionalCovered: result.sharedOptional.length,
        gapCount: result.gapCount,
      })
    }

    return results
  }, [profileSkills, occupationsData])

  function handleSelectPerfil(p: PerfilResumen) {
    setPerfil(p)
    const url = new URL(window.location.href)
    url.searchParams.set('perfil_id', p.id)
    router.replace(url.pathname + url.search, { scroll: false })
    loadPerfilSkills(p.id)
  }

  function handleClear() {
    setPerfil(null)
    setProfileSkills([])
    setPerfilProvincia(null)
    setMensaje(null)
    const url = new URL(window.location.href)
    url.searchParams.delete('perfil_id')
    router.replace(url.pathname, { scroll: false })
  }

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

  const loadingAll = loading || (perfil && profileSkills.length > 0 && !occupationsData)

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

        {/* Error perfil */}
        {!loading && mensaje === 'error' && (
          <div className="bg-red-50 border border-red-200 rounded-xl p-4 text-center">
            <p className="text-sm text-red-700">Error cargando el perfil. Intentá de nuevo.</p>
          </div>
        )}

        {/* Error datos ocupaciones */}
        {dataError && (
          <div className="bg-red-50 border border-red-200 rounded-xl p-4 text-center">
            <p className="text-sm text-red-700">{dataError}</p>
          </div>
        )}

        {/* Results */}
        {!loadingAll && !mensaje && perfil && matches.length > 0 && (
          <div className="space-y-3">
            <div className="flex items-center justify-between flex-wrap gap-2">
              <p className="text-xs text-gray-400">
                {matches.length} ocupaciones compatibles · basado en {profileSkills.length} skills
              </p>
              <div className="flex items-center gap-3">
                {/* Time period filter */}
                <div className="flex items-center gap-1.5">
                  <Calendar className="w-3 h-3 text-gray-400" />
                  <select
                    value={timePeriod}
                    onChange={e => setTimePeriod(e.target.value as TimePeriod)}
                    className="text-xs text-gray-600 bg-transparent border-none cursor-pointer focus:outline-none"
                  >
                    {TIME_OPTIONS.map(o => (
                      <option key={o.id} value={o.id}>{o.label}</option>
                    ))}
                  </select>
                </div>
                {/* Sort */}
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
            </div>

            {sorted.map((o, i) => (
              <OccupationMatchCard
                key={o.uri}
                occupation={o}
                rank={i + 1}
                ofertasCount={ofertasCountMap[o.isco_code] || 0}
                provincia={perfilProvincia}
                since={getSinceDate(timePeriod)}
                onOpenModal={handleOpenModal}
              />
            ))}
          </div>
        )}

        {/* No results */}
        {!loadingAll && !mensaje && perfil && profileSkills.length > 0 && matches.length === 0 && (
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
        provincia={perfilProvincia}
        since={getSinceDate(timePeriod)}
      />
    </div>
  )
}
