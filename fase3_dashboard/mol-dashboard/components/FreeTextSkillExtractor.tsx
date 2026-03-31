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
      if (!res.ok) throw new Error(`API error ${res.status}`)
      const data = await res.json()

      // La API devuelve data.results (array de skills)
      const rawSkills = data.results || data.skills || []
      const skills: SkillItem[] = rawSkills.map(
        (s: any) => ({
          uri: s.uri || s.id || '',
          label: s.label || '',
          type: s.type || 'skill',
          description: s.description || '',
          source: s.source || 'esco',
          confidence: 'confirmed' as SkillConfidence,
          via: 'texto_libre' as const,
        })
      )

      if (skills.length === 0) {
        setError('No se encontraron competencias para ese texto. Probá con más detalle.')
      } else {
        setExtracted(skills)
      }
    } catch (e) {
      console.error('Error extracting skills:', e)
      setError('Error al procesar el texto. Intentá de nuevo.')
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
            <div key={skill.uri} className="space-y-1">
              <SkillWithDefinition
                skill={skill}
                onConfidenceChange={handleConfidenceChange}
                onRemove={handleRemove}
              />
              <div className="flex justify-end">
                <button
                  onClick={() => handleAddOne(skill)}
                  aria-label={`Agregar ${skill.label} al perfil`}
                  className="min-h-[44px] rounded px-3 py-1 text-sm text-blue-600 hover:bg-blue-50"
                >
                  + Agregar al perfil
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
