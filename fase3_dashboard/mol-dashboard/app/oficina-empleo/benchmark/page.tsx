'use client'

import { Suspense, useState, useEffect } from 'react'
import { useSearchParams } from 'next/navigation'
import { Download, TrendingUp, Users, AlertTriangle, BookOpen } from 'lucide-react'
import MarketBenchmark, { type MarketBenchmarkData } from '@/components/MarketBenchmark'
import { OEBreadcrumb } from '@/components/oficina-empleo/OEBreadcrumb'

interface CursoFaltante {
  skill_label: string
  brecha: number
  curso_nombre: string
  curso_url?: string
  duracion: string
  modalidad: string
}

interface InteligenciaLocalData {
  jurisdiccion: string
  total_ofertas: number
  total_perfiles: number
  top_demandadas: { label: string; pct: number }[]
  top_disponibles: { label: string; pct: number }[]
  benchmark: MarketBenchmarkData
  cursos_faltantes: CursoFaltante[]
}

function InteligenciaContent() {
  const searchParams = useSearchParams()
  const jurisdiccion = searchParams.get('jurisdiccion') ?? 'CABA'
  const [data, setData] = useState<InteligenciaLocalData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)

  useEffect(() => {
    const load = async () => {
      setLoading(true)
      setError(false)
      try {
        const res = await fetch(`/api/inteligencia-local?jurisdiccion=${jurisdiccion}`)
        if (res.ok) setData(await res.json())
        else setError(true)
      } catch {
        setError(true)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [jurisdiccion])

  if (loading) return (
    <div className="space-y-4">
      {[1, 2, 3, 4].map((i) => <div key={i} className="h-32 animate-pulse rounded-xl bg-gray-100" />)}
    </div>
  )

  if (error || !data) return (
    <p className="text-sm text-red-500">No se pudo cargar la información de inteligencia local.</p>
  )

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3 text-sm text-gray-500">
          <span>{data.total_ofertas.toLocaleString()} ofertas analizadas</span>
          <span>·</span>
          <span>{data.total_perfiles.toLocaleString()} perfiles en la zona</span>
        </div>
        <button
          onClick={() => window.print()}
          aria-label="Exportar PDF"
          className="flex min-h-[44px] items-center gap-2 rounded-lg border border-gray-300 px-4 py-2 text-sm text-gray-600 hover:bg-gray-50"
        >
          <Download className="h-4 w-4" />
          Exportar PDF
        </button>
      </div>

      {/* Demandadas vs Disponibles */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div className="rounded-xl border border-gray-200 bg-white p-4">
          <div className="mb-3 flex items-center gap-2">
            <TrendingUp className="h-4 w-4 text-blue-600" />
            <h2 className="text-sm font-semibold text-gray-800">Top skills demandadas</h2>
          </div>
          <ul className="space-y-2">
            {data.top_demandadas.map((s) => (
              <li key={s.label}>
                <div className="flex justify-between text-xs text-gray-700 mb-0.5">
                  <span>{s.label}</span>
                  <span className="font-medium">{s.pct}%</span>
                </div>
                <div className="h-1.5 rounded-full bg-gray-100">
                  <div className="h-1.5 rounded-full bg-blue-500" style={{ width: `${s.pct}%` }} />
                </div>
              </li>
            ))}
          </ul>
        </div>

        <div className="rounded-xl border border-gray-200 bg-white p-4">
          <div className="mb-3 flex items-center gap-2">
            <Users className="h-4 w-4 text-green-600" />
            <h2 className="text-sm font-semibold text-gray-800">Top skills disponibles</h2>
          </div>
          <ul className="space-y-2">
            {data.top_disponibles.map((s) => (
              <li key={s.label}>
                <div className="flex justify-between text-xs text-gray-700 mb-0.5">
                  <span>{s.label}</span>
                  <span className="font-medium">{s.pct}%</span>
                </div>
                <div className="h-1.5 rounded-full bg-gray-100">
                  <div className="h-1.5 rounded-full bg-green-500" style={{ width: `${s.pct}%` }} />
                </div>
              </li>
            ))}
          </ul>
        </div>
      </div>

      {/* Tabla brecha */}
      <div>
        <div className="mb-3 flex items-center gap-2">
          <AlertTriangle className="h-4 w-4 text-amber-500" />
          <h2 className="text-sm font-semibold text-gray-800">Brecha de skills</h2>
        </div>
        <MarketBenchmark data={data.benchmark} />
      </div>

      {/* Cursos faltantes */}
      <div>
        <div className="mb-3 flex items-center gap-2">
          <BookOpen className="h-4 w-4 text-violet-600" />
          <h2 className="text-sm font-semibold text-gray-800">Cursos para cerrar brechas</h2>
        </div>
        <ul className="space-y-2">
          {data.cursos_faltantes.map((c) => (
            <li key={c.skill_label} className="rounded-xl border border-gray-200 bg-white p-4">
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-2 mb-1">
                    <span className="rounded bg-red-100 px-2 py-0.5 text-xs font-medium text-red-700">
                      Brecha {c.brecha}%
                    </span>
                    <span className="text-xs text-gray-500">{c.skill_label}</span>
                  </div>
                  <p className="font-medium text-gray-900 text-sm">{c.curso_nombre}</p>
                  <p className="text-xs text-gray-500 mt-0.5">{c.duracion} · {c.modalidad}</p>
                </div>
                {c.curso_url && (
                  <a
                    href={c.curso_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    aria-label={`Ver curso: ${c.curso_nombre}`}
                    className="flex min-h-[44px] shrink-0 items-center rounded-lg border border-gray-200 px-3 py-2 text-xs text-gray-600 hover:bg-gray-50"
                  >
                    Ver curso
                  </a>
                )}
              </div>
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
}

export default function InteligenciaLocalPage() {
  return (
    <div className="mx-auto max-w-4xl px-4 py-8">
      <OEBreadcrumb items={[{ label: "Benchmark Mercado" }]} />
      <h1 className="mb-1 text-2xl font-bold text-gray-900">Inteligencia local</h1>
      <p className="mb-6 text-sm text-gray-500">
        Análisis de demanda y disponibilidad de skills en el mercado laboral de la jurisdicción.
      </p>
      <Suspense fallback={<div className="h-24 animate-pulse rounded-xl bg-gray-100" />}>
        <InteligenciaContent />
      </Suspense>
    </div>
  )
}
