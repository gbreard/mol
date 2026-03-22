'use client'

import { useState } from 'react'
import { X, Copy, Save } from 'lucide-react'

export interface SkillRequerida {
  uri: string
  label: string
  type: 'skill' | 'knowledge'
  source: 'esco' | 'argentina_approved'
  required: boolean  // requerida vs deseable
}

export interface JobProfile {
  id?: string
  titulo: string
  isco?: string
  skills: SkillRequerida[]
}

interface Props {
  initial?: JobProfile
  onSave?: (profile: JobProfile) => Promise<void>
  onDuplicate?: (profile: JobProfile) => void
}

export default function JobProfileForm({ initial, onSave, onDuplicate }: Props) {
  const [titulo, setTitulo] = useState(initial?.titulo ?? '')
  const [skills, setSkills] = useState<SkillRequerida[]>(initial?.skills ?? [])
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<SkillRequerida[]>([])
  const [searching, setSearching] = useState(false)
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)

  const handleSearch = async (q: string) => {
    setQuery(q)
    if (q.length < 2) { setResults([]); return }
    setSearching(true)
    try {
      const res = await fetch(`/api/skills-search?q=${encodeURIComponent(q)}&limit=8`)
      if (res.ok) {
        const data = await res.json()
        setResults(data.results ?? [])
      }
    } finally {
      setSearching(false)
    }
  }

  const addSkill = (skill: Omit<SkillRequerida, 'required'>) => {
    if (skills.some((s) => s.uri === skill.uri)) return
    setSkills((prev) => [...prev, { ...skill, required: true }])
    setQuery('')
    setResults([])
  }

  const removeSkill = (uri: string) => {
    setSkills((prev) => prev.filter((s) => s.uri !== uri))
  }

  const toggleRequired = (uri: string) => {
    setSkills((prev) =>
      prev.map((s) => (s.uri === uri ? { ...s, required: !s.required } : s))
    )
  }

  const handleSave = async () => {
    if (!titulo.trim()) return
    setSaving(true)
    try {
      await onSave?.({ titulo, skills, id: initial?.id })
      setSaved(true)
      setTimeout(() => setSaved(false), 2000)
    } finally {
      setSaving(false)
    }
  }

  const handleDuplicate = () => {
    onDuplicate?.({ titulo: `${titulo} (copia)`, skills })
  }

  const sourceBadge = (source: SkillRequerida['source']) =>
    source === 'argentina_approved'
      ? 'bg-amber-100 text-amber-700'
      : 'bg-gray-100 text-gray-600'

  return (
    <div className="space-y-6">
      {/* Título del puesto */}
      <div>
        <label className="mb-1 block text-sm font-medium text-gray-700" htmlFor="titulo-puesto">
          Título del puesto
        </label>
        <input
          id="titulo-puesto"
          type="text"
          value={titulo}
          onChange={(e) => setTitulo(e.target.value)}
          placeholder="Ej: Programador Python Junior"
          className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
        />
      </div>

      {/* Buscador de skills */}
      <div className="relative">
        <label className="mb-1 block text-sm font-medium text-gray-700" htmlFor="buscar-skill">
          Agregar skill requerida
        </label>
        <input
          id="buscar-skill"
          type="text"
          value={query}
          onChange={(e) => handleSearch(e.target.value)}
          placeholder="Buscar skill por nombre..."
          autoComplete="off"
          className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
        />

        {/* Dropdown resultados */}
        {(results.length > 0 || searching) && (
          <ul
            role="listbox"
            aria-label="Resultados de búsqueda de skills"
            className="absolute z-10 mt-1 w-full rounded-lg border border-gray-200 bg-white shadow-lg"
          >
            {searching && (
              <li className="px-4 py-2 text-sm text-gray-400">Buscando...</li>
            )}
            {results.map((r) => (
              <li key={r.uri}>
                <button
                  type="button"
                  onClick={() => addSkill(r)}
                  aria-label={`Agregar skill: ${r.label}`}
                  className="flex w-full items-center gap-2 px-4 py-2 text-left text-sm hover:bg-gray-50"
                >
                  <span className="flex-1 text-gray-800">{r.label}</span>
                  <span className={`rounded px-1.5 py-0.5 text-xs ${sourceBadge(r.source)}`}>
                    {r.source === 'argentina_approved' ? 'ARG' : 'ESCO'}
                  </span>
                  <span className="text-xs text-gray-400">{r.type}</span>
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* Lista de skills agregadas */}
      {skills.length > 0 && (
        <div>
          <p className="mb-2 text-sm font-medium text-gray-700">
            Skills del puesto ({skills.length})
          </p>
          <ul className="space-y-2">
            {skills.map((skill) => (
              <li
                key={skill.uri}
                className="flex items-center gap-2 rounded-lg border border-gray-200 bg-white px-3 py-2"
              >
                <span className="flex-1 text-sm text-gray-800">{skill.label}</span>
                <span className={`rounded px-1.5 py-0.5 text-xs ${sourceBadge(skill.source)}`}>
                  {skill.source === 'argentina_approved' ? 'ARG' : 'ESCO'}
                </span>
                <button
                  type="button"
                  onClick={() => toggleRequired(skill.uri)}
                  aria-label={skill.required ? `Marcar ${skill.label} como deseable` : `Marcar ${skill.label} como requerida`}
                  className={`min-h-[44px] rounded px-2 text-xs font-medium ${
                    skill.required
                      ? 'bg-blue-100 text-blue-700'
                      : 'bg-gray-100 text-gray-500'
                  }`}
                >
                  {skill.required ? 'Requerida' : 'Deseable'}
                </button>
                <button
                  type="button"
                  onClick={() => removeSkill(skill.uri)}
                  aria-label={`Quitar ${skill.label}`}
                  className="min-h-[44px] rounded p-1 text-gray-400 hover:text-red-500"
                >
                  <X className="h-4 w-4" />
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Acciones */}
      <div className="flex gap-3">
        {initial?.id && (
          <button
            type="button"
            onClick={handleDuplicate}
            aria-label="Duplicar perfil de puesto"
            className="flex min-h-[44px] items-center gap-2 rounded-lg border border-gray-300 px-4 py-2 text-sm text-gray-600 hover:bg-gray-50"
          >
            <Copy className="h-4 w-4" />
            Duplicar
          </button>
        )}
        <button
          type="button"
          onClick={handleSave}
          disabled={!titulo.trim() || saving}
          aria-label="Guardar perfil de puesto"
          className="flex min-h-[44px] flex-1 items-center justify-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
        >
          <Save className="h-4 w-4" />
          {saved ? '¡Guardado!' : saving ? 'Guardando...' : 'Guardar perfil'}
        </button>
      </div>
    </div>
  )
}
