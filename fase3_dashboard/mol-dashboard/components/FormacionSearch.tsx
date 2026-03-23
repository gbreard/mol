'use client'

import { useState } from 'react'
import { Search, CheckCircle, Plus } from 'lucide-react'

export interface FormacionResult {
  id: string
  titulo: string
  institucion: string
  nivel: string           // "Tecnicatura" | "Curso" | "Diplomatura" etc
  resolucion?: string     // número resolución oficial
  verificado: boolean     // tiene resolución oficial
  skills_derivadas: string[]
}

interface Props {
  onAgregar?: (result: FormacionResult) => void
}

export default function FormacionSearch({ onAgregar }: Props) {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<FormacionResult[]>([])
  const [loading, setLoading] = useState(false)
  const [searched, setSearched] = useState(false)
  const [agregados, setAgregados] = useState<Set<string>>(new Set())

  const handleSearch = async () => {
    if (!query.trim()) return
    setLoading(true)
    setSearched(true)
    try {
      const res = await fetch(`/api/formacion-search?q=${encodeURIComponent(query)}`)
      if (res.ok) {
        const data = await res.json()
        setResults(data.results ?? [])
      } else {
        setResults([])
      }
    } catch {
      setResults([])
    } finally {
      setLoading(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') handleSearch()
  }

  const handleAgregar = (result: FormacionResult) => {
    setAgregados((prev) => new Set(prev).add(result.id))
    onAgregar?.(result)
  }

  return (
    <div className="space-y-4">
      {/* Buscador */}
      <div className="flex gap-2">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Buscar título formativo... ej: Tecnicatura en Redes"
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

      {/* Resultados */}
      {searched && !loading && results.length === 0 && (
        <p className="text-sm text-gray-400">No se encontraron títulos formativos para "{query}".</p>
      )}

      {results.length > 0 && (
        <ul className="space-y-3">
          {results.map((r) => (
            <li
              key={r.id}
              className="rounded-xl border border-gray-200 bg-white p-4"
            >
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <p className="font-medium text-gray-900">{r.titulo}</p>
                    {r.verificado && (
                      <span
                        aria-label="Título verificado con resolución oficial"
                        className="flex items-center gap-1 rounded-full bg-green-100 px-2 py-0.5 text-xs font-medium text-green-700"
                      >
                        <CheckCircle className="h-3 w-3" />
                        Verificado
                      </span>
                    )}
                  </div>

                  <div className="mt-1 flex flex-wrap gap-2 text-xs text-gray-500">
                    <span>{r.institucion}</span>
                    <span className="rounded bg-gray-100 px-1.5 py-0.5 text-gray-600">{r.nivel}</span>
                    {r.resolucion && (
                      <span className="text-gray-400">Res. {r.resolucion}</span>
                    )}
                  </div>

                  {r.skills_derivadas.length > 0 && (
                    <div className="mt-2 flex flex-wrap gap-1">
                      {r.skills_derivadas.map((skill) => (
                        <span
                          key={skill}
                          className="rounded bg-blue-50 px-2 py-0.5 text-xs text-blue-700"
                        >
                          {skill}
                        </span>
                      ))}
                    </div>
                  )}
                </div>

                <button
                  onClick={() => handleAgregar(r)}
                  disabled={agregados.has(r.id)}
                  aria-label={`Agregar ${r.titulo} al perfil`}
                  className="flex min-h-[44px] shrink-0 items-center gap-1.5 rounded-lg border border-blue-300 px-3 py-2 text-sm font-medium text-blue-600 hover:bg-blue-50 disabled:border-green-300 disabled:text-green-600"
                >
                  {agregados.has(r.id) ? (
                    <>
                      <CheckCircle className="h-4 w-4" />
                      Agregado
                    </>
                  ) : (
                    <>
                      <Plus className="h-4 w-4" />
                      Agregar
                    </>
                  )}
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
