'use client'

import { useState, useRef, useCallback } from 'react'
import { Search, MessageSquare, Loader2, Plus, Check, X } from 'lucide-react'
import type { SelectedSkill } from './useSkillCapture'

interface Props {
  skillUris: Set<string>
  onAddSkill: (skill: SelectedSkill) => void
  onAddSkills: (skills: SelectedSkill[]) => void
}

type Mode = 'busqueda' | 'relato'

export function TaskSkillSearch({ skillUris, onAddSkill, onAddSkills }: Props) {
  const [mode, setMode] = useState<Mode>('busqueda')
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [extractedPending, setExtractedPending] = useState<any[]>([])
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  const doSearch = useCallback(async (q: string) => {
    if (q.trim().length < 2) { setResults([]); setLoading(false); return }
    setLoading(true)
    try {
      const res = await fetch(`/api/skills-search?q=${encodeURIComponent(q)}&limit=15`)
      if (res.ok) {
        const data = await res.json()
        setResults(data.results || data || [])
      }
    } catch {} finally {
      setLoading(false)
    }
  }, [])

  function handleQuickSearch(q: string) {
    setQuery(q)
    if (q.trim().length < 2) { setResults([]); return }
    if (debounceRef.current) clearTimeout(debounceRef.current)
    debounceRef.current = setTimeout(() => doSearch(q), 300)
  }

  async function handleExtract() {
    if (!query.trim()) return
    setLoading(true)
    setExtractedPending([])
    try {
      const res = await fetch('/api/skills-extract-from-text', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: query }),
      })
      if (res.ok) {
        const data = await res.json()
        setExtractedPending(data.results || data.skills || [])
      }
    } catch {} finally {
      setLoading(false)
    }
  }

  function addFromResult(r: any) {
    const skill: SelectedSkill = {
      uri: r.uri || r.id || '',
      label: r.label || r.preferred_label,
      type: r.type === 'knowledge' ? 'knowledge' : 'skill',
      L1: r.L1,
      L2: r.L2,
      source: 'busqueda',
      market_frequency: r.total || 0,
    }
    onAddSkill(skill)
    // Remove from results
    setResults(prev => prev.filter(x => (x.uri || x.id) !== (r.uri || r.id)))
  }

  function confirmExtracted(r: any) {
    const skill: SelectedSkill = {
      uri: r.uri || r.id || '',
      label: r.label || r.preferred_label,
      type: r.type === 'knowledge' ? 'knowledge' : 'skill',
      L1: r.L1,
      L2: r.L2,
      source: 'texto',
      market_frequency: r.total || 0,
    }
    onAddSkill(skill)
    setExtractedPending(prev => prev.filter(x => (x.uri || x.id) !== (r.uri || r.id)))
  }

  function discardExtracted(r: any) {
    setExtractedPending(prev => prev.filter(x => (x.uri || x.id) !== (r.uri || r.id)))
  }

  function confirmAll() {
    const toAdd: SelectedSkill[] = extractedPending
      .filter(r => !skillUris.has(r.uri || r.id || ''))
      .map(r => ({
        uri: r.uri || r.id || '',
        label: r.label || r.preferred_label,
        type: (r.type === 'knowledge' ? 'knowledge' : 'skill') as 'skill' | 'knowledge',
        L1: r.L1,
        L2: r.L2,
        source: 'texto' as const,
        market_frequency: r.total || 0,
      }))
    onAddSkills(toAdd)
    setExtractedPending([])
    setQuery('')
  }

  return (
    <div className="space-y-3">
      <p className="text-sm text-gray-500">
        ¿Qué otras tareas o actividades sabés hacer?
      </p>

      {/* Mode toggle */}
      <div className="flex gap-1 bg-gray-100 rounded-lg p-1">
        <button
          onClick={() => { setMode('busqueda'); setResults([]); setExtractedPending([]); setQuery('') }}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium transition-colors flex-1 justify-center ${mode === 'busqueda' ? 'bg-white text-teal-700 shadow-sm' : 'text-gray-500 hover:text-gray-700'}`}
        >
          <Search className="w-3.5 h-3.5" /> Búsqueda rápida
        </button>
        <button
          onClick={() => { setMode('relato'); setResults([]); setExtractedPending([]); setQuery('') }}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium transition-colors flex-1 justify-center ${mode === 'relato' ? 'bg-white text-teal-700 shadow-sm' : 'text-gray-500 hover:text-gray-700'}`}
        >
          <MessageSquare className="w-3.5 h-3.5" /> Relato libre
        </button>
      </div>

      {/* Quick search mode */}
      {mode === 'busqueda' && (
        <>
          <div className="relative">
            <input
              value={query}
              onChange={e => handleQuickSearch(e.target.value)}
              placeholder="soldar, programar, atender clientes..."
              className="w-full border rounded-lg px-3 py-2 text-sm pr-8"
            />
            {loading && <Loader2 className="w-4 h-4 animate-spin absolute right-3 top-2.5 text-gray-400" />}
          </div>

          {results.length > 0 && (
            <div className="border rounded-lg divide-y max-h-56 overflow-y-auto">
              {results.map((r: any, i: number) => {
                const uri = r.uri || r.id || ''
                const already = skillUris.has(uri)
                return (
                  <button
                    key={i}
                    onClick={() => !already && addFromResult(r)}
                    disabled={already}
                    className={`w-full flex items-center gap-2 px-4 py-2 text-left transition-colors ${already ? 'opacity-40' : 'hover:bg-teal-50'}`}
                  >
                    <div className="flex-1 min-w-0">
                      <span className="text-sm text-gray-900">{r.label || r.preferred_label}</span>
                      {r.description && <p className="text-xs text-gray-400 line-clamp-1">{r.description}</p>}
                    </div>
                    {already ? <Check className="w-4 h-4 text-green-400 shrink-0" /> : <Plus className="w-4 h-4 text-teal-500 shrink-0" />}
                  </button>
                )
              })}
            </div>
          )}
          {query.trim().length >= 2 && !loading && results.length === 0 && (
            <p className="text-xs text-gray-400 text-center py-2">No encontramos esa habilidad, probá con otras palabras</p>
          )}
        </>
      )}

      {/* Free text mode */}
      {mode === 'relato' && (
        <>
          <textarea
            value={query}
            onChange={e => setQuery(e.target.value)}
            placeholder="Trabajé 5 años en una fábrica haciendo soldadura y coordinando al equipo..."
            className="w-full border rounded-lg px-3 py-2 text-sm min-h-[80px] resize-y"
          />
          <button
            onClick={handleExtract}
            disabled={loading || !query.trim()}
            className="bg-teal-600 text-white text-sm px-4 py-2 rounded-lg hover:bg-teal-700 disabled:opacity-50 flex items-center gap-1.5"
          >
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
            Extraer habilidades
          </button>

          {extractedPending.length > 0 && (
            <div className="border rounded-lg overflow-hidden">
              <div className="bg-gray-50 px-4 py-2 flex items-center justify-between border-b">
                <span className="text-xs text-gray-500">{extractedPending.length} skills identificadas</span>
                <button onClick={confirmAll} className="text-xs text-teal-600 hover:text-teal-700 font-medium">
                  Confirmar todas
                </button>
              </div>
              <div className="max-h-48 overflow-y-auto divide-y">
                {extractedPending.map((r: any, i: number) => {
                  const uri = r.uri || r.id || ''
                  const already = skillUris.has(uri)
                  const conf = r.confidence || 'medium'
                  const confColor = conf === 'high' ? 'bg-green-100 text-green-700' : conf === 'low' ? 'bg-red-100 text-red-700' : 'bg-yellow-100 text-yellow-700'
                  return (
                    <div key={i} className={`flex items-center gap-2 px-4 py-2 ${already ? 'opacity-40' : ''}`}>
                      <div className="flex-1 min-w-0">
                        <span className="text-sm text-gray-900">{r.label || r.preferred_label}</span>
                        <span className={`ml-2 text-[10px] px-1.5 py-0.5 rounded ${confColor}`}>{conf}</span>
                      </div>
                      {already ? (
                        <Check className="w-4 h-4 text-green-400 shrink-0" />
                      ) : (
                        <div className="flex items-center gap-1 shrink-0">
                          <button onClick={() => confirmExtracted(r)} className="text-teal-500 hover:text-teal-600"><Check className="w-4 h-4" /></button>
                          <button onClick={() => discardExtracted(r)} className="text-gray-300 hover:text-red-400"><X className="w-4 h-4" /></button>
                        </div>
                      )}
                    </div>
                  )
                })}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  )
}
