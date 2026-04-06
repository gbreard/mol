'use client'

import { useState } from 'react'
import { Search, Loader2, X, Zap } from 'lucide-react'
import type { OccupationMatch } from '@/app/oficina-empleo/perfiles/matching/page'

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

function barColor(pct: number) {
  if (pct >= 70) return 'bg-green-500'
  if (pct >= 40) return 'bg-yellow-500'
  return 'bg-red-400'
}

export function OcupacionObjetivoSelector({ disabled, matches, selected, onSelect, onClear }: Props) {
  const [mode, setMode] = useState<'matches' | 'otro'>('matches')
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState<any[]>([])
  const [searching, setSearching] = useState(false)

  async function handleSearch(q: string) {
    setSearchQuery(q)
    if (q.trim().length < 2) { setSearchResults([]); return }
    setSearching(true)
    try {
      // Uses search_occupations_by_text RPC (pg_trgm) for fuzzy matching
      const res = await fetch(`/api/occupations/search-semantic?q=${encodeURIComponent(q)}`)
      if (res.ok) {
        const data = await res.json()
        setSearchResults(data.results || [])
      }
    } catch {} finally {
      setSearching(false)
    }
  }

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
        <button
          onClick={() => { setMode('matches'); setSearchResults([]) }}
          className={`flex-1 px-3 py-2 text-xs font-medium transition-colors ${mode === 'matches' ? 'bg-white text-purple-700 border-b-2 border-purple-600' : 'text-gray-500 hover:text-gray-700'}`}
        >
          Mis matches
        </button>
        <button
          onClick={() => setMode('otro')}
          className={`flex-1 px-3 py-2 text-xs font-medium transition-colors ${mode === 'otro' ? 'bg-white text-purple-700 border-b-2 border-purple-600' : 'text-gray-500 hover:text-gray-700'}`}
        >
          Otro rumbo
        </button>
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
