'use client'

import { Suspense, useState, useEffect } from 'react'
import { useSearchParams } from 'next/navigation'
import { Download, TrendingUp, Users, AlertTriangle, BookOpen } from 'lucide-react'
import MarketBenchmark, { type MarketBenchmarkData } from '@/components/MarketBenchmark'

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

const MOCK_DATA: InteligenciaLocalData = {
  jurisdiccion: 'CABA',
  total_ofertas: 5240,
  total_perfiles: 1830,
  top_demandadas: [
    { label: 'Atención al cliente', pct: 71 },
    { label: 'Excel avanzado', pct: 62 },
    { label: 'Trabajo en equipo', pct: 58 },
    { label: 'Python', pct: 45 },
    { label: 'SQL', pct: 38 },
  ],
  top_disponibles: [
    { label: 'Atención al cliente', pct: 68 },
    { label: 'Excel avanzado', pct: 54 },
    { label: 'Trabajo en equipo', pct: 52 },
    { label: 'Ventas', pct: 41 },
    { label: 'Cobros y pagos', pct: 38 },
  ],
  benchmark: {
    jurisdiccion: 'CABA',
    total_ofertas: 5240,
    total_perfiles: 1830,
    skills: [
      { uri: 'e1', label: 'Python',              demanda_pct: 45, disponibilidad_pct: 18, brecha: 27, dificultad: 'alta',  tendencia: 'subiendo' },
      { uri: 'e2', label: 'SQL',                 demanda_pct: 38, disponibilidad_pct: 22, brecha: 16, dificultad: 'alta',  tendencia: 'subiendo' },
      { uri: 'e5', label: 'Manejo de CRM',       demanda_pct: 29, disponibilidad_pct: 11, brecha: 18, dificultad: 'alta',  tendencia: 'subiendo' },
      { uri: 'e3', label: 'Excel avanzado',      demanda_pct: 62, disponibilidad_pct: 54, brecha: 8,  dificultad: 'media', tendencia: 'estable'  },
      { uri: 'e4', label: 'Atención al cliente', demanda_pct: 71, disponibilidad_pct: 68, brecha: 3,  dificultad: 'baja',  tendencia: 'bajando'  },
      { uri: 'e6', label: 'Soldadura MIG',       demanda_pct: 15, disponibilidad_pct: 12, brecha: 3,  dificultad: 'baja',  tendencia: 'estable'  },
    ],
  },
  cursos_faltantes: [
    { skill_label: 'Python', brecha: 27, curso_nombre: 'Python para análisis de datos', duracion: '3 meses', modalidad: 'Online', curso_url: 'https://capacitacion.buenosaires.gob.ar' },
    { skill_label: 'SQL',    brecha: 16, curso_nombre: 'SQL básico para no programadores', duracion: '4 semanas', modalidad: 'Online' },
    { skill_label: 'Manejo de CRM', brecha: 18, curso_nombre: 'CRM: Salesforce y Zoho', duracion: '6 semanas', modalidad: 'Presencial' },
  ],
}

function InteligenciaContent() {
  const searchParams = useSearchParams()
  const jurisdiccion = searchParams.get('jurisdiccion') ?? 'CABA'
  const [data, setData] = useState<InteligenciaLocalData | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const load = async () => {
      setLoading(true)
      try {
        const res = await fetch(`/api/inteligencia-local?jurisdiccion=${jurisdiccion}`)
        if (res.ok) setData(await res.json())
        else setData({ ...MOCK_DATA, jurisdiccion })
      } catch {
        setData({ ...MOCK_DATA, jurisdiccion })
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [jurisdiccion])

  const handleExportPDF = () => {
    // TODO: implementar export PDF con jspdf
    window.print()
  }

  if (loading) return (
    <div className="space-y-4">
      {[1, 2, 3, 4].map((i) => <div key={i} className="h-32 animate-pulse rounded-xl bg-gray-100" />)}
    </div>
  )

  if (!data) return null

  return (
    <div className="space-y-8">
      {/* Header con botón exportar */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3 text-sm text-gray-500">
          <span>{data.total_ofertas.toLocaleString()} ofertas analizadas</span>
          <span>·</span>
          <span>{data.total_perfiles.toLocaleString()} perfiles en la zona</span>
        </div>
        <button
          onClick={handleExportPDF}
          aria-label="Exportar PDF"
          className="flex min-h-[44px] items-center gap-2 rounded-lg border border-gray-300 px-4 py-2 text-sm text-gray-600 hover:bg-gray-50"
        >
          <Download className="h-4 w-4" />
          Exportar PDF
        </button>
      </div>

      {/* Sección 1 y 2: Demandadas vs Disponibles */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        {/* Top demandadas */}
        <div className="rounded-xl border border-gray-200 bg-white p-4">
          <div className="mb-3 flex items-center gap-2">
            <TrendingUp className="h-4 w-4 text-blue-600" />
            <h2 className="text-sm font-semibold text-gray-800">Top skills demandadas</h2>
          </div>
          <ul className="space-y-2">
            {data.top_demandadas.map((s) => (
              <li key={s.label} className="flex items-center gap-3">
                <div className="flex-1">
                  <div className="flex justify-between text-xs text-gray-700 mb-0.5">
                    <span>{s.label}</span>
                    <span className="font-medium">{s.pct}%</span>
                  </div>
                  <div className="h-1.5 rounded-full bg-gray-100">
                    <div className="h-1.5 rounded-full bg-blue-500" style={{ width: `${s.pct}%` }} />
                  </div>
                </div>
              </li>
            ))}
          </ul>
        </div>

        {/* Top disponibles */}
        <div className="rounded-xl border border-gray-200 bg-white p-4">
          <div className="mb-3 flex items-center gap-2">
            <Users className="h-4 w-4 text-green-600" />
            <h2 className="text-sm font-semibold text-gray-800">Top skills disponibles</h2>
          </div>
          <ul className="space-y-2">
            {data.top_disponibles.map((s) => (
              <li key={s.label} className="flex items-center gap-3">
                <div className="flex-1">
                  <div className="flex justify-between text-xs text-gray-700 mb-0.5">
                    <span>{s.label}</span>
                    <span className="font-medium">{s.pct}%</span>
                  </div>
                  <div className="h-1.5 rounded-full bg-gray-100">
                    <div className="h-1.5 rounded-full bg-green-500" style={{ width: `${s.pct}%` }} />
                  </div>
                </div>
              </li>
            ))}
          </ul>
        </div>
      </div>

      {/* Sección 3: Tabla brecha */}
      <div>
        <div className="mb-3 flex items-center gap-2">
          <AlertTriangle className="h-4 w-4 text-amber-500" />
          <h2 className="text-sm font-semibold text-gray-800">Brecha de skills</h2>
        </div>
        <MarketBenchmark data={data.benchmark} />
      </div>

      {/* Sección 4: Cursos faltantes */}
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
