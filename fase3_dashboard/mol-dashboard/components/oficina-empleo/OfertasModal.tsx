'use client'

import { useState, useEffect, useCallback } from 'react'
import { X, Briefcase, ExternalLink, Loader2, RefreshCw } from 'lucide-react'
import { getOfertasByIsco, getFechaMaxOfertas, type OfertaPorOcupacion } from '@/lib/supabase'
import { estadoOfertaBadge, antiguedadOferta, formatFecha } from '@/lib/ofertas-estado'

interface Props {
  isOpen: boolean
  onClose: () => void
  iscoCode: string
  label: string
  provincia?: string | null
  since?: string | null
}

export function OfertasModal({ isOpen, onClose, iscoCode, label, provincia, since }: Props) {
  const [ofertas, setOfertas] = useState<OfertaPorOcupacion[]>([])
  const [total, setTotal] = useState(0)
  const [activasCount, setActivasCount] = useState(0)
  const [alcancePais, setAlcancePais] = useState(false)
  const [sinFiltroFecha, setSinFiltroFecha] = useState(false)
  const [fechaMax, setFechaMax] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(false)

  const loadOfertas = useCallback(() => {
    if (!iscoCode) return
    setLoading(true)
    setError(false)
    getOfertasByIsco(iscoCode, 100, 0, provincia, since)
      .then(res => {
        setOfertas(res.ofertas)
        setTotal(res.total)
        setActivasCount(res.activas)
        setAlcancePais(!!provincia && res.alcance === 'pais')
        setSinFiltroFecha(res.sinFiltroFecha)
      })
      .catch(() => setError(true))
      .finally(() => setLoading(false))
  }, [iscoCode, provincia, since])

  useEffect(() => {
    if (isOpen && iscoCode) loadOfertas()
  }, [isOpen, iscoCode, provincia, since, loadOfertas])

  useEffect(() => {
    if (isOpen) getFechaMaxOfertas().then(setFechaMax)
  }, [isOpen])

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/50" onClick={onClose} />

      <div className="relative bg-white rounded-xl shadow-2xl w-full max-w-3xl max-h-[85vh] m-4 flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b">
          <div>
            <h2 className="text-lg font-bold text-gray-900">Últimos avisos publicados</h2>
            <p className="text-sm text-gray-500">
              {label} · ISCO {iscoCode}{fechaMax ? ` · datos al ${formatFecha(fechaMax)}` : ''}
            </p>
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
              <p className="text-sm text-gray-500">Todavía no hay avisos publicados para esta ocupación</p>
            </div>
          ) : (
            <>
              {alcancePais && (
                <p className="text-xs text-amber-700 bg-amber-50 rounded px-2 py-1 mb-2">
                  Sin avisos en {provincia}. Mostrando los más recientes del país.
                </p>
              )}
              {sinFiltroFecha && (
                <p className="text-xs text-amber-700 bg-amber-50 rounded px-2 py-1 mb-2">
                  Sin avisos en el período elegido. Mostrando los más recientes.
                </p>
              )}
              <p className="text-xs text-gray-400 mb-3">
                {total} oferta{total !== 1 ? 's' : ''} · {activasCount} activa{activasCount !== 1 ? 's' : ''}
              </p>
              <div className="space-y-2">
                {ofertas.map((o, i) => {
                  const estado = estadoOfertaBadge(o.estado_ciclo)
                  return (
                  <div key={o.id_oferta || i} className="bg-gray-50 rounded-lg p-3 hover:bg-gray-100 transition-colors">
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <p className="text-sm font-medium text-gray-900 truncate">{o.titulo_limpio || o.titulo}</p>
                          <span className={`text-[9px] px-1.5 py-0.5 rounded font-medium shrink-0 ${estado.className}`}>
                            {estado.label}
                          </span>
                        </div>
                        <div className="flex items-center gap-3 mt-0.5 text-xs text-gray-500">
                          {o.empresa && <span>{o.empresa}</span>}
                          <span>{o.fecha_publicacion ? `${antiguedadOferta(o.fecha_publicacion)} (${formatFecha(o.fecha_publicacion)})` : 'Sin fecha'}</span>
                        </div>
                      </div>
                      {o.url && (
                        <a href={o.url} target="_blank" rel="noopener noreferrer" className="text-teal-600 hover:text-teal-700 shrink-0">
                          <ExternalLink className="w-4 h-4" />
                        </a>
                      )}
                    </div>
                  </div>
                  )
                })}
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
