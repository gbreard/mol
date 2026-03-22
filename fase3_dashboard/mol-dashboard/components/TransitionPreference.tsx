'use client'

import { useState } from 'react'
import TrainingByGap, { type GapGroup } from './TrainingByGap'

interface Props {
  profileId: string
}

interface OccupationOption {
  isco: string
  label: string
  match_score: number
  skills_gap: string[]
  by_gap: GapGroup[]
}

export default function TransitionPreference({ profileId }: Props) {
  const [query, setQuery] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<OccupationOption | null>(null)
  const [error, setError] = useState<string | null>(null)

  const handleSearch = async () => {
    if (!query.trim()) return
    setLoading(true)
    setError(null)
    setResult(null)
    try {
      const res = await fetch(
        `/api/training-suggestions?profile_id=${profileId}&transition_to=${encodeURIComponent(query)}`
      )
      if (!res.ok) throw new Error()
      const data = await res.json()
      setResult(data.transition_preference ?? null)
      if (!data.transition_preference) setError('No se encontró esa ocupación.')
    } catch {
      setError('No se pudo buscar la ocupación. Intentá de nuevo.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-4">
      <p className="text-sm text-gray-600">
        Elegí la ocupación a la que querés transicionar y te mostramos qué te falta y cómo capacitarte.
      </p>

      <div className="flex gap-2">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
          placeholder="Ej: técnico en electrónica, cocinero..."
          aria-label="Buscar ocupación destino"
          className="flex-1 rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
        />
        <button
          onClick={handleSearch}
          disabled={!query.trim() || loading}
          className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
        >
          {loading ? 'Buscando...' : 'Buscar'}
        </button>
      </div>

      {error && <p className="text-sm text-red-500">{error}</p>}

      {result && (
        <div className="space-y-4 rounded-lg border border-gray-200 bg-white p-5">
          <div className="flex items-center justify-between">
            <h3 className="font-semibold text-gray-900">{result.label}</h3>
            <span className="text-sm font-bold text-blue-700">{result.match_score}% compatibilidad</span>
          </div>

          {result.skills_gap.length > 0 && (
            <div>
              <p className="mb-1.5 text-xs font-medium text-red-600">Skills que te faltan</p>
              <div className="flex flex-wrap gap-1">
                {result.skills_gap.map((s) => (
                  <span key={s} className="rounded bg-red-50 px-1.5 py-0.5 text-xs text-red-700">
                    {s}
                  </span>
                ))}
              </div>
            </div>
          )}

          <TrainingByGap byGap={result.by_gap} />
        </div>
      )}
    </div>
  )
}
