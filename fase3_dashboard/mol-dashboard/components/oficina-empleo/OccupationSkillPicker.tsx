'use client'

import { useState } from 'react'
import { Search, Briefcase, Loader2, Plus, Check, X } from 'lucide-react'
import type { SelectedSkill, SelectedOccupation } from './useSkillCapture'
import { getSkillsForOccupation } from './getSkillsForOccupation'

interface Props {
  ocupaciones: SelectedOccupation[]
  skillUris: Set<string>
  onAddOccupation: (occ: SelectedOccupation) => void
  onRemoveOccupation: (id: string) => void
  onAddSkills: (skills: SelectedSkill[]) => void
}

export function OccupationSkillPicker({ ocupaciones, skillUris, onAddOccupation, onRemoveOccupation, onAddSkills }: Props) {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [selectedOcc, setSelectedOcc] = useState<any | null>(null)
  const [occSkills, setOccSkills] = useState<any[]>([])
  const [loadingSkills, setLoadingSkills] = useState(false)
  const [checkedUris, setCheckedUris] = useState<Set<string>>(new Set())

  async function handleSearch() {
    if (!query.trim() || query.trim().length < 2) return
    setLoading(true)
    setResults([])
    setSelectedOcc(null)
    try {
      const res = await fetch(`/api/occupations/search?q=${encodeURIComponent(query)}&limit=10`)
      if (res.ok) {
        const data = await res.json()
        setResults(data.results || [])
      }
    } catch {} finally {
      setLoading(false)
    }
  }

  async function selectOccupation(occ: any) {
    setSelectedOcc(occ)
    setResults([])
    setLoadingSkills(true)
    try {
      const { skills } = await getSkillsForOccupation(occ.uri)
      setOccSkills(skills)
      // Pre-check essentials that aren't already in profile
      // Skills from getSkillsForOccupation have .id (UUID), build URI for matching
      const preChecked = new Set<string>(
        skills
          .filter((s: any) => s.essential && !skillUris.has(`http://data.europa.eu/esco/skill/${s.id}`))
          .map((s: any) => s.id)
      )
      setCheckedUris(preChecked)
    } catch {} finally {
      setLoadingSkills(false)
    }
  }

  function toggleCheck(id: string) {
    setCheckedUris(prev => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  function selectAll() {
    const skillUriSet = new Set(
      occSkills
        .filter((s: any) => !skillUris.has(`http://data.europa.eu/esco/skill/${s.id}`))
        .map((s: any) => s.id)
    )
    setCheckedUris(skillUriSet)
  }

  function addToProfile() {
    if (!selectedOcc) return
    // Add occupation
    onAddOccupation({
      id: selectedOcc.id || selectedOcc.uri.split('/').pop(),
      label: selectedOcc.label,
      isco_code: selectedOcc.isco_code,
    })
    // Add checked skills — build full ESCO URI from skill.id
    const toAdd: SelectedSkill[] = occSkills
      .filter((s: any) => checkedUris.has(s.id))
      .map((s: any) => ({
        uri: `http://data.europa.eu/esco/skill/${s.id}`,
        label: s.label,
        type: (s.type === 'knowledge' ? 'knowledge' : 'skill') as 'skill' | 'knowledge',
        L1: s.L1,
        L2: s.L2,
        source: 'ocupacion' as const,
        essential_for_occupation: s.essential,
        market_frequency: s.total || 0,
      }))
    onAddSkills(toAdd)
    // Reset
    setSelectedOcc(null)
    setOccSkills([])
    setCheckedUris(new Set())
    setQuery('')
  }

  const addedOccIds = new Set(ocupaciones.map(o => o.id))

  return (
    <div className="space-y-3">
      <p className="text-sm text-gray-500">
        ¿En qué trabajaste? ¿Cuál era tu ocupación?
      </p>

      {/* Occupation chips */}
      {ocupaciones.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {ocupaciones.map(occ => (
            <span key={occ.id} className="inline-flex items-center gap-1 bg-teal-50 text-teal-700 text-xs font-medium px-2 py-1 rounded-full">
              {occ.label}
              <button onClick={() => onRemoveOccupation(occ.id)} className="hover:text-teal-900">
                <X className="w-3 h-3" />
              </button>
            </span>
          ))}
        </div>
      )}

      {/* Search */}
      {!selectedOcc && (
        <>
          <div className="flex gap-2">
            <input
              value={query}
              onChange={e => setQuery(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleSearch()}
              placeholder="albañil, electricista, vendedor..."
              className="flex-1 border rounded-lg px-3 py-2 text-sm"
            />
            <button
              onClick={handleSearch}
              disabled={loading || !query.trim()}
              className="bg-teal-600 text-white px-3 py-2 rounded-lg text-sm hover:bg-teal-700 disabled:opacity-50 flex items-center gap-1"
            >
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
            </button>
          </div>

          {results.length > 0 && (
            <div className="border rounded-lg divide-y max-h-48 overflow-y-auto">
              {results.map((occ: any, i: number) => {
                const occId = occ.id || occ.uri?.split('/').pop()
                const already = addedOccIds.has(occId)
                return (
                  <button
                    key={i}
                    onClick={() => !already && selectOccupation(occ)}
                    disabled={already}
                    className={`w-full flex items-center gap-3 px-4 py-2.5 text-left transition-colors ${already ? 'opacity-40' : 'hover:bg-teal-50'}`}
                  >
                    <Briefcase className="w-4 h-4 text-teal-500 shrink-0" />
                    <div className="flex-1 min-w-0">
                      <div className="text-sm font-medium text-gray-900">{occ.label}</div>
                      <div className="text-xs text-gray-400">ISCO {occ.isco_code}</div>
                    </div>
                    {already ? <Check className="w-4 h-4 text-green-400" /> : <Plus className="w-4 h-4 text-teal-500" />}
                  </button>
                )
              })}
            </div>
          )}
        </>
      )}

      {/* Skills of selected occupation */}
      {selectedOcc && (
        <div className="border rounded-lg overflow-hidden">
          <div className="bg-teal-50 px-4 py-2.5 flex items-center justify-between">
            <div>
              <span className="text-sm font-medium text-teal-800">{selectedOcc.label}</span>
              <span className="text-xs text-teal-600 ml-2">ISCO {selectedOcc.isco_code}</span>
            </div>
            <button onClick={() => { setSelectedOcc(null); setOccSkills([]) }} className="text-teal-600 hover:text-teal-800">
              <X className="w-4 h-4" />
            </button>
          </div>

          {loadingSkills ? (
            <div className="py-6 flex items-center justify-center gap-2 text-gray-400">
              <Loader2 className="w-4 h-4 animate-spin" />
              <span className="text-sm">Cargando skills...</span>
            </div>
          ) : occSkills.length === 0 ? (
            <div className="py-6 text-center text-gray-400 text-sm">
              No se encontraron skills para esta ocupación
            </div>
          ) : (
            <>
              <div className="max-h-56 overflow-y-auto divide-y">
                {occSkills.map((s: any, i: number) => {
                  const fullUri = `http://data.europa.eu/esco/skill/${s.id}`
                  const alreadyInProfile = skillUris.has(fullUri)
                  const checked = checkedUris.has(s.id)
                  return (
                    <label key={i} className={`flex items-center gap-2 px-4 py-2 cursor-pointer hover:bg-gray-50 ${alreadyInProfile ? 'opacity-40' : ''}`}>
                      <input
                        type="checkbox"
                        checked={alreadyInProfile || checked}
                        disabled={alreadyInProfile}
                        onChange={() => toggleCheck(s.id)}
                        className="rounded text-teal-600"
                      />
                      <span className="text-sm text-gray-900 flex-1">{s.label}</span>
                      {s.essential && <span className="text-[10px] bg-teal-100 text-teal-700 px-1.5 py-0.5 rounded">esencial</span>}
                      {alreadyInProfile && <Check className="w-3 h-3 text-green-400" />}
                    </label>
                  )
                })}
              </div>
              <div className="px-4 py-2.5 bg-gray-50 border-t flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <span className="text-xs text-gray-500">{checkedUris.size} seleccionadas</span>
                  <button onClick={selectAll} className="text-xs text-teal-600 hover:text-teal-700 font-medium">
                    Seleccionar todas
                  </button>
                </div>
                <button
                  onClick={addToProfile}
                  disabled={checkedUris.size === 0}
                  className="bg-teal-600 text-white text-sm px-3 py-1.5 rounded-lg hover:bg-teal-700 disabled:opacity-50"
                >
                  Agregar al perfil
                </button>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  )
}
