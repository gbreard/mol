'use client'

import { useState } from 'react'
import SkillWithDefinition, { type SkillItem, type SkillConfidence } from './SkillWithDefinition'

interface Props {
  onSkillsAdded?: (skills: SkillItem[]) => void
}

export default function FreeTextSkillExtractor({ onSkillsAdded }: Props) {
  const [text, setText] = useState('')
  const [loading, setLoading] = useState(false)
  const [extracted, setExtracted] = useState<SkillItem[]>([])
  const [error, setError] = useState<string | null>(null)

  const handleExtract = async () => {
    if (!text.trim()) return
    setLoading(true)
    setError(null)
    setExtracted([])
    try {
      const res = await fetch('/api/skills-extract-from-text', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text }),
      })
      if (!res.ok) throw new Error('Error al procesar el texto')
      const data = await res.json()
      const skills: SkillItem[] = (data.skills ?? []).map(
        (s: Omit<SkillItem, 'confidence' | 'via'>) => ({
          ...s,
          confidence: 'confirmed' as SkillConfidence,
          via: 'texto_libre' as const,
        })
      )
      setExtracted(skills)
    } catch {
      setError('No se pudo procesar el texto. Intentá de nuevo.')
    } finally {
      setLoading(false)
    }
  }

  const handleConfidenceChange = (uri: string, confidence: SkillConfidence) => {
    setExtracted((prev) => prev.map((s) => (s.uri === uri ? { ...s, confidence } : s)))
  }

  const handleRemove = (uri: string) => {
    setExtracted((prev) => prev.filter((s) => s.uri !== uri))
  }

  const handleAddAll = () => {
    const toAdd = extracted.filter((s) => s.confidence !== 'discarded')
    onSkillsAdded?.(toAdd)
    setExtracted([])
    setText('')
  }

  const handleAddOne = (skill: SkillItem) => {
    onSkillsAdded?.([skill])
    setExtracted((prev) => prev.filter((s) => s.uri !== skill.uri))
  }

  return (
    <div className="space-y-4">
      {/* Textarea */}
      <div>
        <label htmlFor="free-text-input" className="mb-1.5 block text-sm font-medium text-gray-700">
          Contá con tus palabras qué sabés hacer
        </label>
        <textarea
          id="free-text-input"
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Ej: Sé soldar con autógena, leer planos y operar tornos CNC. También tengo experiencia con atención al cliente y manejo de Excel."
          rows={4}
          className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm placeholder:text-gray-400 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
        />
      </div>

      <button
        onClick={handleExtract}
        disabled={!text.trim() || loading}
        className="flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
      >
        {loading ? (
          <>
            <div
              role="status"
              aria-label="Procesando"
              className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent"
            />
            Identificando competencias...
          </>
        ) : (
          'Identificar competencias'
        )}
      </button>

      {error && <p className="text-sm text-red-500">{error}</p>}

      {/* Results */}
      {extracted.length > 0 && (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-gray-700">
              {extracted.length} competencia{extracted.length !== 1 ? 's' : ''} identificada{extracted.length !== 1 ? 's' : ''}
            </p>
            <button
              onClick={handleAddAll}
              className="rounded-lg border border-blue-600 px-3 py-1.5 text-sm font-medium text-blue-600 hover:bg-blue-50"
            >
              Agregar todas al perfil
            </button>
          </div>

          {extracted.map((skill) => (
            <div key={skill.uri} className="group relative">
              <SkillWithDefinition
                skill={skill}
                onConfidenceChange={handleConfidenceChange}
                onRemove={handleRemove}
              />
              <button
                onClick={() => handleAddOne(skill)}
                className="absolute right-8 top-2 hidden rounded px-2 py-0.5 text-xs text-blue-600 hover:bg-blue-50 group-hover:block"
              >
                agregar
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
