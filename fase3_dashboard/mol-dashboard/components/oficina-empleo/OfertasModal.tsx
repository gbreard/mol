'use client'

import { useState, useEffect, useCallback } from 'react'
import { X, Briefcase, ExternalLink, Loader2, RefreshCw } from 'lucide-react'
import { getOfertasByIsco } from '@/lib/supabase'

interface Props {
  isOpen: boolean
  onClose: () => void
  iscoCode: string
  label: string
  provincia?: string | null
}

export function OfertasModal({ isOpen, onClose, iscoCode, label, provincia }: Props) {
  const [ofertas, setOfertas] = useState<any[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(false)

  const loadOfertas = useCallback(() => {
    if (!iscoCode) return
    setLoading(true)
    setError(false)
    getOfertasByIsco(iscoCode, 100, 0, provincia)
      .then(({ ofertas: data, total: count }) => {
        setOfertas(data)
        setTotal(count)
      })
      .catch(() => setError(true))
      .finally(() => setLoading(false))
  }, [iscoCode, provincia])

  useEffect(() => {
    if (isOpen && iscoCode) loadOfertas()
  }, [isOpen, iscoCode, provincia, loadOfertas])

  const activasCount = ofertas.filter((o: any) => o.estado === 'activa').length

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/50" onClick={onClose} />

      <div className="relative bg-white rounded-xl shadow-2xl w-full max-w-3xl max-h-[85vh] m-4 flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b">
          <div>
            <h2 className="text-lg font-bold text-gray-900">Ofertas disponibles</h2>
            <p className="text-sm text-gray-500">{label} · ISCO {iscoCode}</p>
          </div>
          <button onClick={onClose} className="p-1.5 hover:bg-gray-100 rounded-lg">
            <X className="w-5 h-5 text-gray-500" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-5">
          {loading ? (
            <div className="flex items-center justify-center py-12 gap-2">
              <Loader2 className="w-5 h-5 animate-spin text-teal-600" />
              <span className="text-sm text-gray-500">Cargando ofertas...</span>
            </div>
          ) : error ? (
            <div className="text-center py-12">
              <p className="text-sm text-gray-500 mb-3">No se pudieron cargar las ofertas. Intentá de nuevo.</p>
              <button
                onClick={loadOfertas}
                className="inline-flex items-center gap-1.5 text-sm text-teal-600 hover:text-teal-700 font-medium"
              >
                <RefreshCw className="w-4 h-4" /> Reintentar
              </button>
            </div>
          ) : ofertas.length === 0 ? (
            <div className="text-center py-12">
              <Briefcase className="w-10 h-10 mx-auto text-gray-300 mb-2" />
              <p className="text-sm text-gray-500">No hay ofertas activas para esta ocupación</p>
            </div>
          ) : (
            <>
              <p className="text-xs text-gray-400 mb-3">
                {total} oferta{total !== 1 ? 's' : ''}
                {activasCount > 0 && ` · ${activasCount} activa${activasCount !== 1 ? 's' : ''}`}
              </p>
              <div className="space-y-2">
                {ofertas.map((o: any, i: number) => (
                  <div key={o.id_oferta || i} className="bg-gray-50 rounded-lg p-3 hover:bg-gray-100 transition-colors">
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <p className="text-sm font-medium text-gray-900 truncate">{o.titulo_limpio || o.titulo}</p>
                          <span className={`text-[9px] px-1.5 py-0.5 rounded font-medium shrink-0 ${o.estado === 'activa' ? 'bg-green-50 text-green-600' : 'bg-gray-100 text-gray-400'}`}>
                            {o.estado === 'activa' ? 'Activa' : 'Cerrada'}
                          </span>
                        </div>
                        <div className="flex items-center gap-3 mt-0.5 text-xs text-gray-500">
                          {o.empresa && <span>{o.empresa}</span>}
                          {o.fecha_publicacion && <span>{new Date(o.fecha_publicacion).toLocaleDateString('es-AR')}</span>}
                        </div>
                      </div>
                      {o.url && (
                        <a href={o.url} target="_blank" rel="noopener noreferrer" className="text-teal-600 hover:text-teal-700 shrink-0">
                          <ExternalLink className="w-4 h-4" />
                        </a>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </>
          )}
        </div>

        <div className="border-t px-5 py-3 text-xs text-gray-400">
          Fuente: MOL, en base a portales de intermediación laboral
        </div>
      </div>
    </div>
  )
}
