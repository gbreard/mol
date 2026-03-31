'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Briefcase, Target, ArrowRight, MapPin, Building2, Loader2, CheckCircle2 } from 'lucide-react'
import { useS1Store } from '@/lib/use-s1-store'

interface MatchedOffer {
  id_oferta: string
  titulo: string
  empresa: string
  provincia: string
  isco_code: string
  match_score: number
  skills_cubiertas: number
  skills_oferta_total: number
  skills_detalle: Array<{
    skill: string
    similarity: number
    matched_by: string
    exact: boolean
  }>
}

const COPY_PROPOSITO: Record<string, { titulo: string; subtitulo: string }> = {
  busco_trabajo: {
    titulo: 'Ofertas que encajan con tu perfil',
    subtitulo: 'Ordenadas por compatibilidad con tus competencias.',
  },
  cambiar_rubro: {
    titulo: 'Ocupaciones más cercanas a tu perfil',
    subtitulo: 'Destinos posibles desde donde estás hoy.',
  },
  saber_que_vale: {
    titulo: 'Así se valorizan tus competencias en el mercado',
    subtitulo: 'Ofertas donde tus skills tienen mayor demanda.',
  },
  desde_oe: {
    titulo: 'Tu análisis de competencias',
    subtitulo: 'Tu técnico de la Oficina de Empleo puede ver estos resultados.',
  },
}

function MatchBar({ pct }: { pct: number }) {
  const color = pct >= 50 ? 'bg-green-500' : pct >= 30 ? 'bg-blue-500' : 'bg-yellow-400'
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 bg-gray-100 rounded-full overflow-hidden">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${Math.min(pct, 100)}%` }} />
      </div>
      <span className={`text-xs font-bold tabular-nums ${pct >= 50 ? 'text-green-600' : pct >= 30 ? 'text-blue-600' : 'text-yellow-600'}`}>
        {pct}%
      </span>
    </div>
  )
}

export default function ResultadosPage() {
  const router = useRouter()
  const { store, confirmed } = useS1Store()

  const [offers, setOffers] = useState<MatchedOffer[]>([])
  const [loading, setLoading] = useState(true)
  const [stats, setStats] = useState<{ expanded: number; total: number } | null>(null)

  const proposito = store.proposito ?? 'busco_trabajo'
  const copy = COPY_PROPOSITO[proposito] ?? COPY_PROPOSITO['busco_trabajo']
  const nombre = store.nombre || 'tu perfil'

  useEffect(() => {
    async function loadResults() {
      const skillUris = store.skills.map(s => s.uri).filter(Boolean)
      if (skillUris.length === 0) {
        setLoading(false)
        return
      }

      try {
        const res = await fetch(
          `/api/matching-offers-semantic?skill_uris=${encodeURIComponent(skillUris.join(','))}&limit=20&threshold=0.55`
        )
        if (!res.ok) throw new Error(`API error ${res.status}`)
        const data = await res.json()
        setOffers(data.offers || [])
        setStats({ expanded: data.expanded_skills || 0, total: data.total || 0 })
      } catch (e) {
        console.error('Error loading results:', e)
      } finally {
        setLoading(false)
      }
    }
    loadResults()
  }, [store.skills])

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto px-4 py-8">

        {/* Header */}
        <div className="mb-6">
          <span className="inline-block bg-green-100 text-green-700 text-[10px] font-bold px-2.5 py-0.5 rounded-full uppercase tracking-wider mb-2">
            Paso 3 de 3 — Tus resultados
          </span>
          <h1 className="text-2xl font-bold text-gray-900">{copy.titulo}</h1>
          <p className="text-gray-500 text-sm mt-1">
            {copy.subtitulo} Basado en {confirmed.length} competencias de {nombre}.
          </p>
        </div>

        {/* Stats */}
        {stats && (
          <div className="mb-4 bg-teal-50 border border-teal-100 rounded-xl px-4 py-2 flex items-center justify-between">
            <span className="text-xs text-teal-700">
              {store.skills.length} skills → {stats.expanded} expandidas semánticamente → {stats.total} ofertas encontradas
            </span>
          </div>
        )}

        {/* Loading */}
        {loading && (
          <div className="bg-white rounded-xl border border-gray-200 p-12 flex items-center justify-center gap-3">
            <Loader2 className="w-5 h-5 animate-spin text-blue-600" />
            <span className="text-sm text-gray-500">Buscando ofertas compatibles (matching semántico)...</span>
          </div>
        )}

        {/* No skills */}
        {!loading && store.skills.length === 0 && (
          <div className="bg-white rounded-xl border border-gray-200 p-8 text-center">
            <p className="text-sm text-gray-600">No tenés competencias cargadas.</p>
            <button
              onClick={() => router.push('/mi-futuro-laboral/perfil')}
              className="mt-3 text-sm text-blue-600 hover:underline"
            >
              Volver a cargar competencias →
            </button>
          </div>
        )}

        {/* Results */}
        {!loading && offers.length > 0 && (
          <div className="space-y-3">
            {offers.map((o) => (
              <div key={o.id_oferta} className="bg-white rounded-xl border border-gray-200 p-4">
                <div className="flex items-start justify-between gap-3 mb-2">
                  <div>
                    <h3 className="font-semibold text-gray-900 text-sm">{o.titulo}</h3>
                    <div className="flex flex-wrap items-center gap-2 mt-1">
                      {o.empresa && (
                        <span className="flex items-center gap-1 text-xs text-gray-500">
                          <Building2 className="w-3 h-3" />{o.empresa}
                        </span>
                      )}
                      {o.provincia && (
                        <span className="flex items-center gap-1 text-xs text-gray-500">
                          <MapPin className="w-3 h-3" />{o.provincia}
                        </span>
                      )}
                      <span className="text-xs text-gray-400 font-mono">{o.isco_code}</span>
                    </div>
                  </div>
                </div>
                <MatchBar pct={o.match_score} />
                <div className="mt-2">
                  <span className="text-[10px] text-gray-400 block mb-1">
                    {o.skills_cubiertas}/{o.skills_oferta_total} competencias cubiertas
                  </span>
                  <div className="flex flex-wrap gap-1">
                    {o.skills_detalle.slice(0, 8).map((d, i) => (
                      <span
                        key={i}
                        className={`text-[10px] px-2 py-0.5 rounded-full ${
                          d.exact
                            ? 'bg-green-50 text-green-700'
                            : d.similarity >= 0.80
                              ? 'bg-blue-50 text-blue-700'
                              : 'bg-yellow-50 text-yellow-700'
                        }`}
                        title={d.exact ? 'Match exacto' : `Similar a "${d.matched_by}" (${(d.similarity * 100).toFixed(0)}%)`}
                      >
                        {d.exact ? '✓' : '~'} {d.skill}
                      </span>
                    ))}
                    {o.skills_detalle.length > 8 && (
                      <span className="text-[10px] text-gray-400">+{o.skills_detalle.length - 8} más</span>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* No results */}
        {!loading && offers.length === 0 && store.skills.length > 0 && (
          <div className="bg-white rounded-xl border border-gray-200 p-8 text-center">
            <p className="text-sm text-gray-500">No se encontraron ofertas compatibles con tu perfil actual.</p>
            <button
              onClick={() => router.push('/mi-futuro-laboral/perfil')}
              className="mt-3 text-sm text-blue-600 hover:underline"
            >
              Agregar más competencias →
            </button>
          </div>
        )}

        {/* CTA generar reporte */}
        {offers.length > 0 && (
          <div className="mt-8 bg-blue-600 rounded-2xl p-5 text-center text-white">
            <h2 className="font-bold text-base mb-1">¿Listo para la entrevista?</h2>
            <p className="text-blue-100 text-xs mb-4">
              Generá tu reporte con código QR para que el empleador vea tu análisis de competencias.
            </p>
            <button
              onClick={() => router.push('/mi-futuro-laboral/reporte')}
              className="inline-flex items-center gap-2 bg-white text-blue-700 text-sm font-semibold px-5 py-2.5 rounded-xl hover:bg-blue-50 transition-colors"
            >
              Generar mi reporte PDF + QR
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
