'use client'

import { useState, useEffect, useCallback } from 'react'
import { ExternalLink, FileText } from 'lucide-react'

export interface MatchingOffer {
  id_oferta: number
  titulo: string
  empresa: string
  provincia: string
  localidad: string
  modalidad: string
  fecha_publicacion: string
  url_oferta: string
  match_score: number
  skills_cubiertas: string[]
  skills_gap: string[]
}

interface Filters {
  provincia: string
  ocupacion: string
  modalidad: string
  orden: string
}

interface Props {
  profileId: string
  onGenerateReport?: (offer: MatchingOffer) => void
}

const PROVINCIAS = ['Todas', 'CABA', 'Buenos Aires', 'Córdoba', 'Rosario', 'Mendoza']
const MODALIDADES = ['Todas', 'presencial', 'remoto', 'híbrido']
const ORDENES = ['match_score', 'fecha_publicacion']
const PAGE_SIZE = 10

export default function OffersTab({ profileId, onGenerateReport }: Props) {
  const [offers, setOffers] = useState<MatchingOffer[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(false)
  const [loadingMore, setLoadingMore] = useState(false)
  const [filters, setFilters] = useState<Filters>({
    provincia: '',
    ocupacion: '',
    modalidad: '',
    orden: 'match_score',
  })

  const fetchOffers = useCallback(async (currentPage: number, currentFilters: Filters, replace: boolean) => {
    replace ? setLoading(true) : setLoadingMore(true)
    try {
      const params = new URLSearchParams({
        profile_id: profileId,
        page: String(currentPage),
        ...(currentFilters.provincia && { provincia: currentFilters.provincia }),
        ...(currentFilters.ocupacion && { ocupacion: currentFilters.ocupacion }),
        ...(currentFilters.modalidad && { modalidad: currentFilters.modalidad }),
        orden: currentFilters.orden,
      })
      const res = await fetch(`/api/matching-offers?${params}`)
      if (!res.ok) return
      const data = await res.json()
      setTotal(data.total ?? 0)
      setOffers((prev) => (replace ? data.offers : [...prev, ...data.offers]))
    } finally {
      replace ? setLoading(false) : setLoadingMore(false)
    }
  }, [profileId])

  useEffect(() => {
    setPage(1)
    fetchOffers(1, filters, true)
  }, [filters, fetchOffers])

  const handleLoadMore = () => {
    const next = page + 1
    setPage(next)
    fetchOffers(next, filters, false)
  }

  const setFilter = (key: keyof Filters, value: string) => {
    setFilters((prev) => ({ ...prev, [key]: value === 'Todas' ? '' : value }))
  }

  const scoreColor = (score: number) =>
    score >= 80 ? 'bg-green-500' : score >= 50 ? 'bg-yellow-400' : 'bg-red-400'

  return (
    <div className="space-y-4">
      {/* Filters */}
      <div className="flex flex-wrap gap-3 rounded-lg border border-gray-200 bg-white p-4">
        <div className="flex flex-col gap-1">
          <label className="text-xs font-medium text-gray-500">Provincia</label>
          <select
            aria-label="Filtrar por provincia"
            value={filters.provincia || 'Todas'}
            onChange={(e) => setFilter('provincia', e.target.value)}
            className="rounded-md border border-gray-200 px-2 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-blue-500"
          >
            {PROVINCIAS.map((p) => <option key={p}>{p}</option>)}
          </select>
        </div>

        <div className="flex flex-col gap-1">
          <label className="text-xs font-medium text-gray-500">Modalidad</label>
          <select
            aria-label="Filtrar por modalidad"
            value={filters.modalidad || 'Todas'}
            onChange={(e) => setFilter('modalidad', e.target.value)}
            className="rounded-md border border-gray-200 px-2 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-blue-500"
          >
            {MODALIDADES.map((m) => <option key={m}>{m}</option>)}
          </select>
        </div>

        <div className="flex flex-col gap-1">
          <label className="text-xs font-medium text-gray-500">Ordenar por</label>
          <select
            aria-label="Ordenar ofertas"
            value={filters.orden}
            onChange={(e) => setFilter('orden', e.target.value)}
            className="rounded-md border border-gray-200 px-2 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-blue-500"
          >
            <option value="match_score">Compatibilidad</option>
            <option value="fecha_publicacion">Fecha</option>
          </select>
        </div>

        <div className="flex flex-1 flex-col gap-1">
          <label className="text-xs font-medium text-gray-500">Ocupación</label>
          <input
            type="text"
            aria-label="Filtrar por ocupación"
            value={filters.ocupacion}
            onChange={(e) => setFilter('ocupacion', e.target.value)}
            placeholder="Ej: desarrollador, contador..."
            className="rounded-md border border-gray-200 px-2 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-blue-500"
          />
        </div>
      </div>

      {/* Results count */}
      {!loading && (
        <p className="text-sm text-gray-500">
          {total === 0
            ? 'No se encontraron ofertas'
            : `Mostrando ${offers.length} de ${total} ofertas`}
        </p>
      )}

      {/* Empty state */}
      {!loading && offers.length === 0 && (
        <div className="flex flex-col items-center gap-3 rounded-lg border border-dashed border-gray-200 bg-white py-16 text-center">
          <div className="text-4xl">🔍</div>
          <p className="font-medium text-gray-700">No hay ofertas que coincidan</p>
          <p className="text-sm text-gray-400">
            Probá cambiando los filtros o ampliando tu perfil de competencias.
          </p>
        </div>
      )}

      {/* Loading skeleton */}
      {loading && (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-36 animate-pulse rounded-lg bg-gray-100" />
          ))}
        </div>
      )}

      {/* Offer cards */}
      {!loading && offers.map((offer) => (
        <div
          key={offer.id_oferta}
          className="rounded-lg border border-gray-200 bg-white p-5 shadow-sm"
        >
          <div className="flex items-start justify-between gap-4">
            <div className="min-w-0 flex-1">
              <h3 className="font-semibold text-gray-900">{offer.titulo}</h3>
              <p className="mt-0.5 text-sm text-gray-500">
                {offer.empresa} · {offer.localidad}, {offer.provincia}
              </p>
              <div className="mt-1 flex flex-wrap gap-2">
                <span className="rounded bg-gray-100 px-2 py-0.5 text-xs text-gray-600">
                  {offer.modalidad}
                </span>
                <span className="text-xs text-gray-400">
                  {new Date(offer.fecha_publicacion).toLocaleDateString('es-AR')}
                </span>
              </div>
            </div>

            {/* Score */}
            <div className="shrink-0 text-right">
              <span className="text-2xl font-bold text-gray-900">{offer.match_score}%</span>
              <div className="mt-1 h-2 w-20 overflow-hidden rounded-full bg-gray-100">
                <div
                  className={`h-full rounded-full ${scoreColor(offer.match_score)}`}
                  style={{ width: `${offer.match_score}%` }}
                />
              </div>
            </div>
          </div>

          {/* Skills */}
          <div className="mt-3 grid grid-cols-2 gap-3">
            {offer.skills_cubiertas.length > 0 && (
              <div>
                <p className="mb-1 text-xs font-medium text-green-700">Tenés</p>
                <div className="flex flex-wrap gap-1">
                  {offer.skills_cubiertas.slice(0, 4).map((s) => (
                    <span key={s} className="rounded bg-green-50 px-1.5 py-0.5 text-xs text-green-700">
                      {s}
                    </span>
                  ))}
                  {offer.skills_cubiertas.length > 4 && (
                    <span className="text-xs text-gray-400">+{offer.skills_cubiertas.length - 4}</span>
                  )}
                </div>
              </div>
            )}
            {offer.skills_gap.length > 0 && (
              <div>
                <p className="mb-1 text-xs font-medium text-red-600">Te faltan</p>
                <div className="flex flex-wrap gap-1">
                  {offer.skills_gap.slice(0, 4).map((s) => (
                    <span key={s} className="rounded bg-red-50 px-1.5 py-0.5 text-xs text-red-600">
                      {s}
                    </span>
                  ))}
                  {offer.skills_gap.length > 4 && (
                    <span className="text-xs text-gray-400">+{offer.skills_gap.length - 4}</span>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* Actions */}
          <div className="mt-4 flex gap-2">
            <a
              href={offer.url_oferta}
              target="_blank"
              rel="noopener noreferrer"
              aria-label={`Ver oferta: ${offer.titulo}`}
              className="flex min-h-[44px] items-center gap-1.5 rounded-lg border border-gray-200 px-3 py-2.5 text-sm text-gray-700 hover:bg-gray-50"
            >
              <ExternalLink className="h-3.5 w-3.5" />
              Ver oferta
            </a>
            {onGenerateReport && (
              <button
                onClick={() => onGenerateReport(offer)}
                className="flex min-h-[44px] items-center gap-1.5 rounded-lg bg-blue-50 px-3 py-2.5 text-sm font-medium text-blue-700 hover:bg-blue-100"
              >
                <FileText className="h-3.5 w-3.5" />
                Reporte
              </button>
            )}
          </div>
        </div>
      ))}

      {/* Load more */}
      {!loading && offers.length < total && (
        <button
          onClick={handleLoadMore}
          disabled={loadingMore}
          className="w-full rounded-lg border border-gray-200 py-2.5 text-sm font-medium text-gray-600 hover:bg-gray-50 disabled:opacity-50"
        >
          {loadingMore ? 'Cargando...' : `Cargar más (${total - offers.length} restantes)`}
        </button>
      )}
    </div>
  )
}
