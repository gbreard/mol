'use client'

import { useState, useRef, useCallback, useEffect, useMemo } from 'react'
import { Search, Loader2, X, Zap, BarChart3, ArrowUpDown } from 'lucide-react'
import { createBrowserClient } from '@supabase/ssr'
import type { OccupationMatch } from '@/app/oficina-empleo/perfiles/matching/page'

let _sb: ReturnType<typeof createBrowserClient> | null = null
function getSb() {
  if (!_sb) _sb = createBrowserClient(process.env.NEXT_PUBLIC_SUPABASE_URL!, process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!)
  return _sb
}

interface OccDetail {
  uri: string
  label: string
  isco_code: string
  essentialCount: number
  optionalCount: number
}

interface Props {
  disabled: boolean
  matches: OccupationMatch[]
  selected: OccDetail | null
  onSelect: (occ: OccDetail) => void
  onClear: () => void
}

interface TrendRow {
  isco_code: string
  label: string
  uri: string
  matchScore: number
  essentialTotal: number
  optionalCovered: number
  ofertas: number
  trend: 'up' | 'stable' | 'down'
  trendPct: number
  volatility: 'alta' | 'media' | 'baja'
  monthlyCounts: number[]
}

type MapSort = 'ofertas' | 'match' | 'trend'

function barColor(pct: number) {
  if (pct >= 70) return 'bg-green-500'
  if (pct >= 40) return 'bg-yellow-500'
  return 'bg-red-400'
}

export function OcupacionObjetivoSelector({ disabled, matches, selected, onSelect, onClear }: Props) {
  const [mode, setMode] = useState<'matches' | 'otro' | 'mapa'>('matches')
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState<any[]>([])
  const [searching, setSearching] = useState(false)
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  // Mapa de demanda state
  const [trendData, setTrendData] = useState<TrendRow[]>([])
  const [trendLoading, setTrendLoading] = useState(false)
  const [trendLoaded, setTrendLoaded] = useState(false)
  const [mapSort, setMapSort] = useState<MapSort>('ofertas')

  useEffect(() => {
    return () => { if (debounceRef.current) clearTimeout(debounceRef.current) }
  }, [])

  const doSearch = useCallback(async (q: string) => {
    setSearching(true)
    try {
      const res = await fetch(`/api/occupations/search-semantic?q=${encodeURIComponent(q)}`)
      if (res.ok) {
        const data = await res.json()
        setSearchResults(data.results || [])
      }
    } catch {} finally {
      setSearching(false)
    }
  }, [])

  function handleSearch(q: string) {
    setSearchQuery(q)
    if (q.trim().length < 2) { setSearchResults([]); return }
    if (debounceRef.current) clearTimeout(debounceRef.current)
    debounceRef.current = setTimeout(() => doSearch(q), 300)
  }

  // Load trend data batch (once, when Mapa tab is first opened)
  const loadTrends = useCallback(async () => {
    if (trendLoaded || matches.length === 0) return
    setTrendLoading(true)
    try {
      // Get all ISCOs from matches
      const iscoSet = new Set(matches.map(m => m.isco_code))
      const iscoCodes = [...iscoSet]

      // Batch query: all ofertas for these ISCOs with date + portal
      const { data: ofertas } = await getSb()
        .from('ofertas_dashboard')
        .select('isco_code, fecha_publicacion, portal')
        .in('isco_code', iscoCodes)

      if (!ofertas) { setTrendLoaded(true); setTrendLoading(false); return }

      // Build 6-month window
      const now = new Date()
      const monthLabels: string[] = []
      for (let i = 5; i >= 0; i--) {
        const d = new Date(now.getFullYear(), now.getMonth() - i, 1)
        monthLabels.push(`${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`)
      }

      // Find stable portals (present in first AND last month)
      const portalFirst = new Set<string>()
      const portalLast = new Set<string>()
      for (const o of ofertas) {
        if (!o.fecha_publicacion || !o.portal) continue
        const m = o.fecha_publicacion.substring(0, 7)
        if (m === monthLabels[0]) portalFirst.add(o.portal)
        if (m === monthLabels[5]) portalLast.add(o.portal)
      }
      const stablePortals = new Set([...portalFirst].filter(p => portalLast.has(p)))
      const useAll = stablePortals.size === 0

      // Aggregate by ISCO + month (stable portals only for trend)
      const byIsco: Record<string, { total: number; monthly: number[] }> = {}
      for (const code of iscoCodes) {
        byIsco[code] = { total: 0, monthly: monthLabels.map(() => 0) }
      }
      for (const o of ofertas) {
        const code = o.isco_code
        if (!byIsco[code]) continue
        byIsco[code].total++
        if (!o.fecha_publicacion) continue
        if (!useAll && o.portal && !stablePortals.has(o.portal)) continue
        const m = o.fecha_publicacion.substring(0, 7)
        const idx = monthLabels.indexOf(m)
        if (idx >= 0) byIsco[code].monthly[idx]++
      }

      // Build trend rows — only occupations with >0 offers
      const rows: TrendRow[] = []
      for (const m of matches) {
        const d = byIsco[m.isco_code]
        if (!d || d.total === 0) continue

        const mc = d.monthly
        const recent = (mc[3] + mc[4] + mc[5]) / 3
        const previous = (mc[0] + mc[1] + mc[2]) / 3
        const trendPct = previous > 0 ? Math.round(((recent - previous) / previous) * 100) : (recent > 0 ? 100 : 0)
        const trend: 'up' | 'stable' | 'down' = trendPct > 15 ? 'up' : trendPct < -15 ? 'down' : 'stable'

        const nonZero = mc.filter(c => c > 0)
        const mean = nonZero.length > 0 ? nonZero.reduce((a, b) => a + b, 0) / nonZero.length : 0
        const stddev = mean > 0 ? Math.sqrt(nonZero.reduce((sum, c) => sum + (c - mean) ** 2, 0) / nonZero.length) : 0
        const cv = mean > 0 ? Math.round((stddev / mean) * 100) : 0
        const volatility: 'alta' | 'media' | 'baja' = cv > 60 ? 'alta' : cv > 30 ? 'media' : 'baja'

        rows.push({
          isco_code: m.isco_code,
          label: m.label,
          uri: m.uri,
          matchScore: m.matchScore,
          essentialTotal: m.essentialTotal,
          optionalCovered: m.optionalCovered,
          ofertas: d.total,
          trend, trendPct, volatility, monthlyCounts: mc,
        })
      }

      // Deduplicate by ISCO (keep highest match)
      const seen = new Map<string, TrendRow>()
      for (const r of rows) {
        const existing = seen.get(r.isco_code)
        if (!existing || r.matchScore > existing.matchScore) seen.set(r.isco_code, r)
      }

      setTrendData([...seen.values()])
      setTrendLoaded(true)
    } catch {
      setTrendLoaded(true)
    } finally {
      setTrendLoading(false)
    }
  }, [matches, trendLoaded])

  const sortedTrends = useMemo(() => {
    return [...trendData].sort((a, b) => {
      switch (mapSort) {
        case 'match': return b.matchScore - a.matchScore
        case 'trend': return b.trendPct - a.trendPct || b.ofertas - a.ofertas
        default: return b.ofertas - a.ofertas || b.matchScore - a.matchScore
      }
    })
  }, [trendData, mapSort])

  function selectFromSearch(occ: any) {
    onSelect({
      uri: occ.uri,
      label: occ.label,
      isco_code: (occ.isco_code || '').replace(/^C/, ''),
      essentialCount: 0,
      optionalCount: 0,
    })
    setSearchQuery('')
    setSearchResults([])
  }

  function selectFromMatches(m: OccupationMatch) {
    onSelect({
      uri: m.uri,
      label: m.label,
      isco_code: m.isco_code,
      essentialCount: m.essentialTotal,
      optionalCount: m.optionalCovered,
    })
  }

  function selectFromTrend(r: TrendRow) {
    onSelect({
      uri: r.uri,
      label: r.label,
      isco_code: r.isco_code,
      essentialCount: r.essentialTotal,
      optionalCount: r.optionalCovered,
    })
  }

  // Selected state — ficha
  if (selected) {
    return (
      <div className="bg-white border border-purple-200 rounded-xl px-4 py-3 flex items-center gap-3">
        <Zap className="w-4 h-4 text-purple-600 shrink-0" />
        <div className="flex-1 min-w-0">
          <span className="text-sm font-semibold text-gray-900">{selected.label}</span>
          <span className="text-xs text-gray-400 ml-2">ISCO {selected.isco_code}</span>
          {(selected.essentialCount > 0 || selected.optionalCount > 0) && (
            <span className="text-xs text-gray-400 ml-2">
              · {selected.essentialCount} esenciales · {selected.optionalCount} opcionales
            </span>
          )}
        </div>
        <button onClick={onClear} className="text-gray-400 hover:text-gray-600 shrink-0">
          <X className="w-4 h-4" />
        </button>
      </div>
    )
  }

  if (disabled) {
    return (
      <div className="bg-gray-50 border border-gray-200 rounded-xl px-4 py-3 text-sm text-gray-400">
        Seleccioná una persona primero
      </div>
    )
  }

  return (
    <div className="border border-gray-200 rounded-xl overflow-hidden">
      {/* Mode tabs */}
      <div className="flex bg-gray-50 border-b">
        {([
          { id: 'matches' as const, label: 'Mis matches' },
          { id: 'mapa' as const, label: 'Mapa de demanda' },
          { id: 'otro' as const, label: 'Otro rumbo' },
        ]).map(tab => (
          <button
            key={tab.id}
            onClick={() => {
              setMode(tab.id)
              if (tab.id === 'mapa') loadTrends()
              if (tab.id !== 'otro') setSearchResults([])
            }}
            className={`flex-1 px-3 py-2 text-xs font-medium transition-colors ${mode === tab.id ? 'bg-white text-purple-700 border-b-2 border-purple-600' : 'text-gray-500 hover:text-gray-700'}`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Matches mode */}
      {mode === 'matches' && (
        <div className="max-h-56 overflow-y-auto">
          {matches.length === 0 ? (
            <div className="px-4 py-4 text-xs text-gray-400 text-center">
              Sin ocupaciones compatibles
            </div>
          ) : (
            matches.slice(0, 15).map(m => (
              <button
                key={m.uri}
                onClick={() => selectFromMatches(m)}
                className="w-full flex items-center gap-3 px-4 py-2.5 text-left hover:bg-purple-50 transition-colors border-b border-gray-50 last:border-b-0"
              >
                <div className="flex-1 min-w-0">
                  <span className="text-sm text-gray-900 truncate block">{m.label}</span>
                  <span className="text-xs text-gray-400">ISCO {m.isco_code}</span>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  <div className="w-16 h-1.5 bg-gray-100 rounded-full overflow-hidden">
                    <div className={`h-full rounded-full ${barColor(m.matchScore)}`} style={{ width: `${m.matchScore}%` }} />
                  </div>
                  <span className="text-xs font-medium text-gray-600 w-8">{m.matchScore}%</span>
                </div>
              </button>
            ))
          )}
        </div>
      )}

      {/* Mapa de demanda */}
      {mode === 'mapa' && (
        <div>
          {trendLoading && (
            <div className="flex items-center justify-center gap-2 py-8 text-gray-400">
              <Loader2 className="w-4 h-4 animate-spin" />
              <span className="text-xs">Calculando tendencias de mercado...</span>
            </div>
          )}

          {!trendLoading && sortedTrends.length === 0 && (
            <div className="px-4 py-6 text-xs text-gray-400 text-center">
              <BarChart3 className="w-6 h-6 mx-auto mb-1 opacity-30" />
              No hay ocupaciones compatibles con ofertas activas
            </div>
          )}

          {!trendLoading && sortedTrends.length > 0 && (
            <>
              {/* Sort bar */}
              <div className="flex items-center gap-1 px-3 py-1.5 border-b bg-gray-50">
                <ArrowUpDown className="w-3 h-3 text-gray-400" />
                {([
                  { id: 'ofertas' as MapSort, label: 'Más ofertas' },
                  { id: 'match' as MapSort, label: 'Mejor match' },
                  { id: 'trend' as MapSort, label: 'Creciendo' },
                ]).map(s => (
                  <button
                    key={s.id}
                    onClick={() => setMapSort(s.id)}
                    className={`text-[10px] px-2 py-0.5 rounded-full transition-colors ${mapSort === s.id ? 'bg-purple-100 text-purple-700 font-medium' : 'text-gray-400 hover:text-gray-600'}`}
                  >
                    {s.label}
                  </button>
                ))}
                <span className="text-[10px] text-gray-300 ml-auto">{sortedTrends.length} con ofertas</span>
              </div>

              {/* Rows */}
              <div className="max-h-72 overflow-y-auto">
                {sortedTrends.map(r => {
                  const max = Math.max(...r.monthlyCounts, 1)
                  return (
                    <button
                      key={r.uri}
                      onClick={() => selectFromTrend(r)}
                      className="w-full px-3 py-2 text-left hover:bg-purple-50 transition-colors border-b border-gray-50 last:border-b-0"
                    >
                      {/* Row 1: name + match bar */}
                      <div className="flex items-center gap-2">
                        <span className="text-sm text-gray-900 truncate flex-1">{r.label}</span>
                        <div className="flex items-center gap-1.5 shrink-0">
                          <div className="w-10 h-1.5 bg-gray-100 rounded-full overflow-hidden">
                            <div className={`h-full rounded-full ${barColor(r.matchScore)}`} style={{ width: `${r.matchScore}%` }} />
                          </div>
                          <span className="text-[10px] font-medium text-gray-500 w-7">{r.matchScore}%</span>
                        </div>
                      </div>
                      {/* Row 2: metrics */}
                      <div className="flex items-center gap-3 mt-1">
                        <span className="text-[10px] text-gray-400">ISCO {r.isco_code}</span>
                        <span className="text-[10px] font-medium text-gray-600">{r.ofertas} oferta{r.ofertas !== 1 ? 's' : ''}</span>
                        <span className={`text-[10px] font-medium ${r.trend === 'up' ? 'text-green-600' : r.trend === 'down' ? 'text-red-500' : 'text-gray-500'}`}>
                          {r.trend === 'up' ? '↑' : r.trend === 'down' ? '↓' : '→'}
                          {r.trendPct !== 0 && ` ${r.trendPct > 0 ? '+' : ''}${r.trendPct}%`}
                        </span>
                        <span className={`text-[10px] px-1 py-0 rounded ${
                          r.volatility === 'baja' ? 'bg-green-50 text-green-600' :
                          r.volatility === 'media' ? 'bg-yellow-50 text-yellow-600' :
                          'bg-red-50 text-red-500'
                        }`}>
                          {r.volatility === 'baja' ? 'Estable' : r.volatility === 'media' ? 'Variable' : 'Volátil'}
                        </span>
                        {/* Mini sparkline */}
                        <div className="flex items-end gap-px h-3 ml-auto">
                          {r.monthlyCounts.map((c, i) => (
                            <div
                              key={i}
                              className={`w-1.5 rounded-sm ${i >= 3 ? 'bg-teal-400' : 'bg-gray-300'}`}
                              style={{ height: `${Math.max(1, Math.round((c / max) * 12))}px` }}
                            />
                          ))}
                        </div>
                      </div>
                    </button>
                  )
                })}
              </div>
            </>
          )}
        </div>
      )}

      {/* Search mode */}
      {mode === 'otro' && (
        <div>
          <div className="relative px-3 py-2 border-b">
            <Search className="w-3.5 h-3.5 absolute left-5 top-4 text-gray-400" />
            <input
              value={searchQuery}
              onChange={e => handleSearch(e.target.value)}
              placeholder="Buscar ocupación..."
              className="w-full pl-6 pr-2 py-1 text-sm border-none bg-transparent focus:outline-none"
            />
            {searching && <Loader2 className="w-3.5 h-3.5 animate-spin absolute right-5 top-4 text-gray-400" />}
          </div>
          <div className="max-h-48 overflow-y-auto">
            {searchResults.map((occ, i) => (
              <button
                key={i}
                onClick={() => selectFromSearch(occ)}
                className="w-full flex items-center gap-3 px-4 py-2.5 text-left hover:bg-purple-50 transition-colors border-b border-gray-50 last:border-b-0"
              >
                <span className="text-sm text-gray-900 flex-1 truncate">{occ.label}</span>
                <span className="text-xs text-gray-400 shrink-0">ISCO {(occ.isco_code || '').replace(/^C/, '')}</span>
              </button>
            ))}
            {searchQuery.length >= 2 && !searching && searchResults.length === 0 && (
              <div className="px-4 py-3 text-xs text-gray-400 text-center">Sin resultados</div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
