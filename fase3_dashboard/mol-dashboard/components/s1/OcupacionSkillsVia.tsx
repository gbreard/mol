'use client'

import { useState, useRef, useCallback } from 'react'
import { Search, Loader2, Plus, ChevronRight } from 'lucide-react'
import type { SkillItem, SkillConfidence } from '@/components/SkillWithDefinition'

interface OccupationResult {
  id: string
  label: string
  isco: string
}

interface OccupationSkill {
  uri: string
  label: string
  type: 'skill' | 'knowledge'
  description: string
  source: 'esco' | 'argentina_approved'
  essential: boolean
}

interface Props {
  onSkillsFound: (skills: SkillItem[]) => void
}

export default function OcupacionSkillsVia({ onSkillsFound }: Props) {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<OccupationResult[]>([])
  const [loadingSearch, setLoadingSearch] = useState(false)
  const [selected, setSelected] = useState<OccupationResult | null>(null)
  const [skills, setSkills] = useState<OccupationSkill[]>([])
  const [loadingSkills, setLoadingSkills] = useState(false)
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  const search = useCallback(async (q: string) => {
    if (!q.trim()) { setResults([]); return }
    setLoadingSearch(true)
    try {
      const res = await fetch(`/api/occupations/search?q=${encodeURIComponent(q)}&limit=8`)
      if (res.ok) {
        const data = await res.json()
        setResults(data.results ?? data)
      }
    } finally {
      setLoadingSearch(false)
    }
  }, [])

  const handleQueryChange = (q: string) => {
    setQuery(q)
    setSelected(null)
    setSkills([])
    if (debounceRef.current) clearTimeout(debounceRef.current)
    debounceRef.current = setTimeout(() => search(q), 350)
  }

  const handleSelectOccupation = async (occ: OccupationResult) => {
    setSelected(occ)
    setResults([])
    setQuery(occ.label)
    setLoadingSkills(true)
    try {
      const res = await fetch(`/api/occupations/skills?occupation_id=${occ.id}&limit=20`)
      if (res.ok) {
        const data = await res.json()
        setSkills(data.skills ?? data)
      }
    } finally {
      setLoadingSkills(false)
    }
  }

  const handleAgregar = () => {
    const items: SkillItem[] = skills.map((s) => ({
      uri: s.uri,
      label: s.label,
      type: s.type,
      description: s.description,
      source: s.source,
      confidence: 'confirmed' as SkillConfidence,
      via: 'ocupacion' as const,
    }))
    onSkillsFound(items)
    setSelected(null)
    setQuery('')
    setSkills([])
  }

  return (
    <div className="space-y-4">
      {/* Search input */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
        <input
          type="text"
          value={query}
          onChange={(e) => handleQueryChange(e.target.value)}
          placeholder="Ej: cajero, enfermero, desarrollador..."
          className="w-full rounded-lg border border-gray-200 pl-9 pr-3 py-2.5 text-sm text-gray-900 placeholder-gray-400 focus:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-100"
          autoFocus
        />
        {loadingSearch && (
          <Loader2 className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 animate-spin" />
        )}
      </div>

      {/* Resultados búsqueda */}
      {results.length > 0 && !selected && (
        <div className="border border-gray-200 rounded-lg divide-y divide-gray-100 overflow-hidden">
          {results.map((r) => (
            <button
              key={r.id}
              onClick={() => handleSelectOccupation(r)}
              className="w-full flex items-center justify-between px-4 py-2.5 hover:bg-blue-50 text-left transition-colors"
            >
              <span className="text-sm text-gray-800">{r.label}</span>
              <div className="flex items-center gap-2 shrink-0">
                <span className="text-xs text-gray-400 font-mono">{r.isco}</span>
                <ChevronRight className="w-3.5 h-3.5 text-gray-300" />
              </div>
            </button>
          ))}
        </div>
      )}

      {/* Skills de la ocupación seleccionada */}
      {loadingSkills && (
        <div className="flex items-center justify-center py-8 text-gray-400">
          <Loader2 className="w-5 h-5 animate-spin mr-2" />
          <span className="text-sm">Cargando competencias...</span>
        </div>
      )}

      {selected && skills.length > 0 && (
        <div>
          <div className="flex items-center justify-between mb-2">
            <p className="text-xs font-medium text-gray-600">
              Competencias para <span className="text-blue-700">{selected.label}</span>
            </p>
            <span className="text-xs text-gray-400">{skills.length} competencias</span>
          </div>
          <div className="border border-gray-200 rounded-lg divide-y divide-gray-100 overflow-hidden max-h-64 overflow-y-auto mb-3">
            {skills.map((s) => (
              <div key={s.uri} className="flex items-center gap-2 px-3 py-2">
                <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${s.essential ? 'bg-blue-500' : 'bg-gray-300'}`} />
                <span className="text-sm text-gray-800 flex-1">{s.label}</span>
                {s.essential && (
                  <span className="text-[10px] bg-blue-50 text-blue-600 px-1.5 py-0.5 rounded font-medium">
                    esencial
                  </span>
                )}
              </div>
            ))}
          </div>
          <button
            onClick={handleAgregar}
            className="w-full inline-flex items-center justify-center gap-2 bg-blue-600 text-white text-sm font-medium px-4 py-2.5 rounded-lg hover:bg-blue-700 transition-colors"
          >
            <Plus className="w-4 h-4" />
            Agregar estas {skills.length} competencias a mi perfil
          </button>
        </div>
      )}

      {selected && !loadingSkills && skills.length === 0 && (
        <p className="text-sm text-gray-400 text-center py-4">
          No encontramos competencias para esta ocupación.
        </p>
      )}
    </div>
  )
}
