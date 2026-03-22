'use client'

import { useState } from 'react'
import { Search } from 'lucide-react'
import AnonProfileCard, { type AnonProfile } from './AnonProfileCard'

interface Props {
  onSolicitarContacto?: (profileId: string) => Promise<void>
}

export default function PoolSearch({ onSolicitarContacto }: Props) {
  const [isco, setIsco] = useState('')
  const [jurisdiccion, setJurisdiccion] = useState('')
  const [loading, setLoading] = useState(false)
  const [profiles, setProfiles] = useState<AnonProfile[] | null>(null)
  const [error, setError] = useState<string | null>(null)

  const handleSearch = async () => {
    if (!isco.trim()) return
    setLoading(true)
    setError(null)
    setProfiles(null)
    try {
      const params = new URLSearchParams({ isco })
      if (jurisdiccion) params.set('jurisdiccion', jurisdiccion)
      const res = await fetch(`/api/pool-search?${params}`)
      if (!res.ok) throw new Error('Error al buscar')
      const data = await res.json()
      setProfiles(data.profiles ?? [])
    } catch {
      setError('No se pudo realizar la búsqueda. Intentá de nuevo.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-4">
      {/* Filtros */}
      <div className="flex flex-col gap-3 sm:flex-row">
        <div className="flex-1">
          <label htmlFor="pool-isco" className="mb-1 block text-xs font-medium text-gray-600">
            Ocupación (ISCO)
          </label>
          <input
            id="pool-isco"
            type="text"
            value={isco}
            onChange={(e) => setIsco(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
            placeholder="ej: 2512"
            className="w-full rounded-lg border border-gray-300 px-3 py-2.5 text-sm focus:border-blue-500 focus:outline-none"
          />
        </div>
        <div className="flex-1">
          <label htmlFor="pool-jurisdiccion" className="mb-1 block text-xs font-medium text-gray-600">
            Jurisdicción (opcional)
          </label>
          <input
            id="pool-jurisdiccion"
            type="text"
            value={jurisdiccion}
            onChange={(e) => setJurisdiccion(e.target.value)}
            placeholder="ej: CABA"
            className="w-full rounded-lg border border-gray-300 px-3 py-2.5 text-sm focus:border-blue-500 focus:outline-none"
          />
        </div>
        <div className="flex items-end">
          <button
            onClick={handleSearch}
            disabled={!isco.trim() || loading}
            aria-label="Buscar en pool"
            className="flex min-h-[44px] items-center gap-2 rounded-lg bg-teal-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-teal-700 disabled:opacity-50"
          >
            <Search className="h-4 w-4" />
            {loading ? 'Buscando...' : 'Buscar'}
          </button>
        </div>
      </div>

      {error && <p className="text-sm text-red-500">{error}</p>}

      {/* Resultados */}
      {profiles !== null && (
        <div className="space-y-3">
          <p className="text-sm text-gray-600">
            <strong>{profiles.length}</strong> perfil{profiles.length !== 1 ? 'es' : ''} compatible{profiles.length !== 1 ? 's' : ''} encontrado{profiles.length !== 1 ? 's' : ''}
          </p>

          {profiles.length === 0 ? (
            <p className="rounded-lg border border-gray-100 bg-gray-50 px-4 py-6 text-center text-sm text-gray-500">
              No hay perfiles disponibles para esta búsqueda.
            </p>
          ) : (
            <>
              {profiles.map((p) => (
                <AnonProfileCard
                  key={p.id}
                  profile={p}
                  onSolicitarContacto={onSolicitarContacto}
                />
              ))}
              <p className="text-center text-xs text-gray-400">
                Los perfiles son anonimizados. Al solicitar contacto, el trabajador
                recibe una notificación y decide si aceptar.
              </p>
            </>
          )}
        </div>
      )}
    </div>
  )
}
