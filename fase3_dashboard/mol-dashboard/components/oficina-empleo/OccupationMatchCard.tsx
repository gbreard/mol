'use client'

import { useState, useEffect, useRef } from 'react'
import { ChevronDown, ChevronUp, Loader2, Briefcase, ExternalLink } from 'lucide-react'
import { getOfertasByIsco } from '@/lib/supabase'

interface OccupationMatch {
  uri: string
  label: string
  isco_code: string
  matchScore: number
  essentialTotal: number
  essentialCovered: number
  optionalCovered: number
  gapCount: number
}

interface OfertaPreview {
  titulo: string
  empresa: string
  fecha_publicacion: string
  url: string
  estado: string
}

interface Props {
  occupation: OccupationMatch
  rank: number
  ofertasCount: number
  provincia?: string | null
  since?: string | null
  onOpenModal: (iscoCode: string, label: string) => void
}

function barColor(pct: number) {
  if (pct >= 80) return 'bg-green-500'
  if (pct >= 50) return 'bg-yellow-500'
  return 'bg-red-400'
}

function ofertasBadge(count: number) {
  if (count >= 5) return { icon: '🟢', text: `${count} ofertas` }
  if (count >= 1) return { icon: '🟡', text: `${count} oferta${count > 1 ? 's' : ''}` }
  return { icon: '⚪', text: 'Sin ofertas' }
}

export function OccupationMatchCard({
  occupation, rank, ofertasCount, provincia, since,
  onOpenModal,
}: Props) {
  const [expanded, setExpanded] = useState(false)
  const [loading, setLoading] = useState(false)
  const [ofertas, setOfertas] = useState<OfertaPreview[]>([])
  const [loaded, setLoaded] = useState(false)
  const prevSinceRef = useRef(since)

  // Invalidate cached ofertas when time period changes
  useEffect(() => {
    if (prevSinceRef.current !== since) {
      prevSinceRef.current = since
      setLoaded(false)
      setOfertas([])
    }
  }, [since])

  async function handleExpand() {
    if (expanded) { setExpanded(false); return }
    setExpanded(true)
    if (loaded) return

    setLoading(true)
    try {
      const ofertasData = await getOfertasByIsco(occupation.isco_code, 3, 0, provincia, since)

      if (ofertasData?.ofertas) {
        setOfertas(ofertasData.ofertas.slice(0, 3).map((o: any) => ({
          titulo: o.titulo_limpio || o.titulo,
          empresa: o.empresa || '',
          fecha_publicacion: o.fecha_publicacion || '',
          url: o.url || '',
          estado: o.estado || 'baja',
        })))
      }

      setLoaded(true)
    } catch (e) {
      console.error('Error loading expanded data:', e)
      setLoaded(true)
    } finally {
      setLoading(false)
    }
  }

  const badge = ofertasBadge(ofertasCount)

  return (
    <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
      {/* Summary row */}
      <button
        onClick={handleExpand}
        className="w-full px-4 py-3.5 flex items-center gap-3 text-left hover:bg-gray-50 transition-colors"
      >
        <span className="text-sm text-gray-400 font-medium w-6 shrink-0">{rank}.</span>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-sm font-semibold text-gray-900 truncate">{occupation.label}</span>
            <span className="text-xs text-gray-400 shrink-0">ISCO {occupation.isco_code}</span>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 flex-1">
              <div className="flex-1 h-2 bg-gray-100 rounded-full overflow-hidden max-w-[180px]">
                <div
                  className={`h-full rounded-full ${barColor(occupation.matchScore)}`}
                  style={{ width: `${Math.min(occupation.matchScore, 100)}%` }}
                />
              </div>
              <span className="text-xs font-semibold text-gray-700 w-10">{occupation.matchScore}%</span>
            </div>
            <span className="text-xs text-gray-500 shrink-0">
              {occupation.essentialCovered}/{occupation.essentialTotal} esenciales
              {occupation.gapCount > 0 && <span className="text-gray-400"> · gap: {occupation.gapCount}</span>}
            </span>
            <span className="text-xs text-gray-500 shrink-0">{badge.icon} {badge.text}</span>
          </div>
        </div>
        {expanded ? <ChevronUp className="w-4 h-4 text-gray-400 shrink-0" /> : <ChevronDown className="w-4 h-4 text-gray-400 shrink-0" />}
      </button>

      {/* Expanded panel */}
      {expanded && (
        <div className="border-t px-4 py-4">
          {loading && (
            <div className="flex items-center justify-center gap-2 py-6 text-gray-400">
              <Loader2 className="w-4 h-4 animate-spin" />
              <span className="text-sm">Analizando compatibilidad...</span>
            </div>
          )}

          {!loading && loaded && (
            <div className="space-y-4">
              {/* Ofertas preview */}
              {(ofertas.length > 0 || ofertasCount > 0) && (
                <div className="border rounded-lg overflow-hidden">
                  <div className="bg-gray-50 px-3 py-2 border-b flex items-center justify-between">
                    <span className="text-xs font-medium text-gray-600">
                      {ofertasCount} oferta{ofertasCount !== 1 ? 's' : ''}
                    </span>
                    {ofertasCount > 0 && (
                      <button
                        onClick={() => onOpenModal(occupation.isco_code, occupation.label)}
                        className="text-xs text-teal-600 hover:text-teal-700 font-medium"
                      >
                        Ver {ofertasCount === 1 ? 'la oferta' : `las ${ofertasCount} ofertas`} →
                      </button>
                    )}
                  </div>
                  {ofertas.length > 0 ? (
                    <div className="divide-y">
                      {ofertas.map((o, i) => (
                        <div key={i} className="px-3 py-2 flex items-center gap-2">
                          <Briefcase className="w-3 h-3 text-gray-300 shrink-0" />
                          <div className="flex-1 min-w-0">
                            <span className="text-xs text-gray-800 truncate block">{o.titulo}</span>
                            <span className="text-[10px] text-gray-400">
                              {o.empresa}{o.fecha_publicacion ? ` · ${new Date(o.fecha_publicacion).toLocaleDateString('es-AR')}` : ''}
                            </span>
                          </div>
                          <span className={`text-[9px] px-1.5 py-0.5 rounded font-medium shrink-0 ${o.estado === 'activa' ? 'bg-green-50 text-green-600' : 'bg-gray-100 text-gray-400'}`}>
                            {o.estado === 'activa' ? 'Activa' : 'Cerrada'}
                          </span>
                          {o.url && (
                            <a href={o.url} target="_blank" rel="noopener noreferrer" className="text-gray-300 hover:text-teal-600 shrink-0">
                              <ExternalLink className="w-3 h-3" />
                            </a>
                          )}
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="px-3 py-3 text-xs text-gray-400 text-center">Sin ofertas activas</div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
