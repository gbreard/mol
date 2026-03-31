'use client'

import { useState } from 'react'
import { Search, Plus, CheckCircle } from 'lucide-react'
import type { SkillItem, SkillConfidence } from '@/components/SkillWithDefinition'

interface Props {
  onAgregar?: (result: { id: string; titulo: string; skills_derivadas: SkillItem[] }) => void
}

export default function FormacionSearch({ onAgregar }: Props) {
  const [query, setQuery] = useState('')
  const [skills, setSkills] = useState<SkillItem[]>([])
  const [loading, setLoading] = useState(false)
  const [searched, setSearched] = useState(false)
  const [agregado, setAgregado] = useState(false)

  const handleSearch = async () => {
    if (!query.trim()) return
    setLoading(true)
    setSearched(true)
    setAgregado(false)
    setSkills([])
    try {
      // Usar la misma API de extracción de texto que usa trigrams + pgvector
      const res = await fetch('/api/skills-extract-from-text', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: query }),
      })
      if (!res.ok) throw new Error(`API error ${res.status}`)
      const data = await res.json()
      const rawSkills = data.results || []
      setSkills(rawSkills.map((s: any) => ({
        uri: s.uri || s.id || '',
        label: s.label || '',
        type: s.type || 'skill',
        description: s.description || '',
        source: s.source || 'esco',
        confidence: 'confirmed' as SkillConfidence,
        via: 'formacion' as const,
      })))
    } catch (e) {
      console.error('Error searching formacion:', e)
    } finally {
      setLoading(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') handleSearch()
  }

  const handleAgregar = () => {
    if (skills.length === 0) return
    setAgregado(true)
    onAgregar?.({
      id: `formacion-${Date.now()}`,
      titulo: query,
      skills_derivadas: skills,
    })
  }

  return (
    <div className="space-y-4">
      <div className="flex gap-2">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ej: Tecnicatura en Redes, Curso de Soldadura, Lic. en Enfermería..."
          aria-label="Buscar título formativo"
          className="flex-1 rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
        />
        <button
          onClick={handleSearch}
          disabled={!query.trim() || loading}
          aria-label="Buscar formación"
          className="flex min-h-[44px] items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
        >
          <Search className="h-4 w-4" />
          {loading ? 'Buscando...' : 'Buscar'}
        </button>
      </div>

      {searched && !loading && skills.length === 0 && (
        <p className="text-sm text-gray-400">No se encontraron competencias para &quot;{query}&quot;.</p>
      )}

      {skills.length > 0 && (
        <div className="rounded-xl border border-gray-200 bg-white p-4">
          <div className="flex items-start justify-between gap-3 mb-3">
            <div>
              <p className="font-medium text-gray-900">{query}</p>
              <p className="text-xs text-gray-500 mt-0.5">
                {skills.length} competencias identificadas
              </p>
            </div>
            <button
              onClick={handleAgregar}
              disabled={agregado}
              aria-label="Agregar competencias al perfil"
              className="flex min-h-[44px] shrink-0 items-center gap-1.5 rounded-lg border border-blue-300 px-3 py-2 text-sm font-medium text-blue-600 hover:bg-blue-50 disabled:border-green-300 disabled:text-green-600"
            >
              {agregado ? (
                <>
                  <CheckCircle className="h-4 w-4" />
                  Agregadas
                </>
              ) : (
                <>
                  <Plus className="h-4 w-4" />
                  Agregar todas
                </>
              )}
            </button>
          </div>
          <div className="flex flex-wrap gap-1">
            {skills.map((s) => (
              <span key={s.uri} className="rounded bg-blue-50 px-2 py-0.5 text-xs text-blue-700">
                {s.label}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
