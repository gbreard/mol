'use client'

import { useState, useEffect, useRef, useCallback } from 'react'
import SkillWithDefinition, { type SkillItem, type SkillConfidence } from './SkillWithDefinition'

interface SkillSearchResult {
  uri: string
  label: string
  type: 'skill' | 'knowledge'
  description: string
  source: 'esco' | 'argentina_approved'
  frequency?: number
}

interface Props {
  onSkillsChange?: (skills: SkillItem[]) => void
  hideList?: boolean
  existingUris?: Set<string>
}

export default function SkillSearchByTask({ onSkillsChange, hideList, existingUris }: Props) {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<SkillSearchResult[]>([])
  const [loading, setLoading] = useState(false)
  const [open, setOpen] = useState(false)
  const [addedSkills, setAddedSkills] = useState<SkillItem[]>([])
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  const search = useCallback(async (q: string) => {
    if (!q.trim()) {
      setResults([])
      setOpen(false)
      return
    }
    setLoading(true)
    try {
      const res = await fetch(`/api/skills-search?q=${encodeURIComponent(q)}&limit=10`)
      if (res.ok) {
        const data = await res.json()
        setResults(data.results ?? data)
        setOpen(true)
      }
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current)
    debounceRef.current = setTimeout(() => search(query), 300)
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current)
    }
  }, [query, search])

  const addSkill = (result: SkillSearchResult) => {
    // Ignorar si ya está en el store global o en la lista interna
    if (existingUris?.has(result.uri) || addedSkills.some((s) => s.uri === result.uri)) return
    const newSkill: SkillItem = { ...result, confidence: 'confirmed', via: 'busqueda' }
    const updated = [...addedSkills, newSkill]
    setAddedSkills(updated)
    onSkillsChange?.(updated)
    setQuery('')
    setResults([])
    setOpen(false)
    inputRef.current?.focus()
  }

  const handleConfidenceChange = (uri: string, confidence: SkillConfidence) => {
    const updated = addedSkills.map((s) => (s.uri === uri ? { ...s, confidence } : s))
    setAddedSkills(updated)
    onSkillsChange?.(updated)
  }

  const handleRemove = (uri: string) => {
    const updated = addedSkills.filter((s) => s.uri !== uri)
    setAddedSkills(updated)
    onSkillsChange?.(updated)
  }

  return (
    <div className="space-y-4">
      {/* Search input */}
      <div className="relative">
        <div className="flex items-center gap-2 rounded-lg border border-gray-300 bg-white px-3 py-2 shadow-sm focus-within:border-blue-500 focus-within:ring-1 focus-within:ring-blue-500">
          <svg className="h-4 w-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onFocus={() => results.length > 0 && setOpen(true)}
            onBlur={() => setTimeout(() => setOpen(false), 150)}
            placeholder="Buscar competencia (ej: soldadura, Excel, atención al cliente...)"
            className="flex-1 bg-transparent text-sm outline-none placeholder:text-gray-400"
            aria-label="Buscar skills"
            aria-autocomplete="list"
            aria-expanded={open}
          />
          {loading && (
            <div className="h-4 w-4 animate-spin rounded-full border-2 border-blue-500 border-t-transparent" />
          )}
        </div>

        {/* Dropdown */}
        {open && (
          <ul
            role="listbox"
            className="absolute z-10 mt-1 w-full overflow-hidden rounded-lg border border-gray-200 bg-white shadow-lg"
          >
            {results.length === 0 ? (
              <li className="px-4 py-3 text-sm text-gray-500">Sin resultados para &quot;{query}&quot;</li>
            ) : (
              results.map((r) => (
                <li
                  key={r.uri}
                  role="option"
                  aria-selected={addedSkills.some((s) => s.uri === r.uri) || existingUris?.has(r.uri)}
                  onMouseDown={() => addSkill(r)}
                  className="flex cursor-pointer items-start gap-2 px-4 py-2.5 hover:bg-blue-50"
                >
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-1.5">
                      <span className="text-sm font-medium text-gray-900">{r.label}</span>
                      <span className="rounded bg-blue-100 px-1.5 py-0.5 text-xs text-blue-700">
                        {r.type === 'skill' ? 'competencia' : 'conocimiento'}
                      </span>
                      {r.source === 'argentina_approved' && (
                        <span className="rounded bg-orange-100 px-1.5 py-0.5 text-xs text-orange-700">emergente</span>
                      )}
                    </div>
                    {r.description && (
                      <p className="mt-0.5 truncate text-xs text-gray-400">{r.description}</p>
                    )}
                  </div>
                  {(addedSkills.some((s) => s.uri === r.uri) || existingUris?.has(r.uri)) && (
                    <span className="text-xs text-green-500">✓ agregada</span>
                  )}
                </li>
              ))
            )}
          </ul>
        )}
      </div>

      {/* Added skills list — oculta cuando el padre ya muestra el acumulador */}
      {!hideList && addedSkills.length > 0 && (
        <div className="space-y-2">
          <p className="text-xs font-medium uppercase tracking-wide text-gray-400">
            Competencias agregadas ({addedSkills.length})
          </p>
          {addedSkills.map((skill) => (
            <SkillWithDefinition
              key={skill.uri}
              skill={skill}
              onConfidenceChange={handleConfidenceChange}
              onRemove={handleRemove}
            />
          ))}
        </div>
      )}
    </div>
  )
}
