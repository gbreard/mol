'use client'

import { Suspense, useState, useEffect } from 'react'
import { useSearchParams } from 'next/navigation'
import { Download, TrendingUp, Users, AlertTriangle, Loader2 } from 'lucide-react'
import { OEBreadcrumb } from '@/components/oficina-empleo/OEBreadcrumb'

interface SkillItem {
  name: string
  count: number
  digital: boolean
  l1: string
}

interface OcupacionItem {
  code: string
  label: string
  count: number
}

interface ApiData {
  jurisdiccion: string
  ofertas_total: number
  skills_demandadas: SkillItem[]
  skills_digitales: SkillItem[]
  ocupaciones_top: OcupacionItem[]
  brechas: {
    total_skills_unicas: number
    skills_digitales_pct: number
  }
}

function BenchmarkContent() {
  const searchParams = useSearchParams()
  const jurisdiccion = searchParams.get('jurisdiccion') ?? 'CABA'
  const [data, setData] = useState<ApiData | null>(null)
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
    <div className="py-12 text-center">
      <Loader2 className="w-8 h-8 animate-spin text-teal-600 mx-auto mb-3" />
      <p className="text-gray-500">Analizando mercado laboral de {jurisdiccion}...</p>
    </div>
  )

  if (error || !data) return (
    <p className="text-sm text-red-500">No se pudo cargar la informacion de inteligencia local.</p>
  )

  const maxCount = Math.max(...data.skills_demandadas.map(s => s.count), 1)

  return (
    <div className="space-y-8">
      {/* KPIs */}
      <div className="grid grid-cols-3 gap-4">
        <div className="rounded-xl border border-gray-200 bg-white p-4 text-center">
          <div className="text-2xl font-bold text-gray-900">{data.ofertas_total.toLocaleString("es-AR")}</div>
          <div className="text-xs text-gray-500">ofertas analizadas</div>
        </div>
        <div className="rounded-xl border border-gray-200 bg-white p-4 text-center">
          <div className="text-2xl font-bold text-gray-900">{data.brechas.total_skills_unicas}</div>
          <div className="text-xs text-gray-500">skills distintas</div>
        </div>
        <div className="rounded-xl border border-gray-200 bg-white p-4 text-center">
          <div className="text-2xl font-bold text-blue-600">{data.brechas.skills_digitales_pct}%</div>
          <div className="text-xs text-gray-500">digitales</div>
        </div>
      </div>

      {/* Top skills demandadas */}
      <div className="rounded-xl border border-gray-200 bg-white p-5">
        <div className="mb-4 flex items-center gap-2">
          <TrendingUp className="h-4 w-4 text-blue-600" />
          <h2 className="text-sm font-semibold text-gray-800">Top skills demandadas en {data.jurisdiccion}</h2>
        </div>
        <div className="space-y-2">
          {data.skills_demandadas.slice(0, 20).map((s) => (
            <div key={s.name} className="flex items-center gap-3">
              <span className="text-xs text-gray-700 w-40 truncate">{s.name}</span>
              <div className="flex-1 bg-gray-100 rounded-full h-4 overflow-hidden">
                <div
                  className={`h-full rounded-full ${s.digital ? 'bg-blue-500' : 'bg-gray-400'}`}
                  style={{ width: `${Math.max((s.count / maxCount) * 100, 3)}%` }}
                />
              </div>
              <span className="text-xs text-gray-500 w-10 text-right">{s.count}</span>
              {s.digital && <span className="text-xs bg-blue-50 text-blue-600 px-1.5 py-0.5 rounded">digital</span>}
            </div>
          ))}
        </div>
      </div>

      {/* Top ocupaciones */}
      <div className="rounded-xl border border-gray-200 bg-white p-5">
        <div className="mb-4 flex items-center gap-2">
          <Users className="h-4 w-4 text-green-600" />
          <h2 className="text-sm font-semibold text-gray-800">Top ocupaciones en {data.jurisdiccion}</h2>
        </div>
        <div className="space-y-2">
          {data.ocupaciones_top.slice(0, 15).map((o) => (
            <div key={o.code} className="flex items-center gap-3">
              <span className="text-xs font-mono text-blue-700 w-12">{o.code}</span>
              <span className="text-xs text-gray-700 flex-1 truncate">{o.label}</span>
              <span className="text-xs text-gray-500">{o.count} ofertas</span>
            </div>
          ))}
        </div>
      </div>

      <div className="flex justify-end">
        <button
          onClick={() => window.print()}
          className="flex items-center gap-2 rounded-lg border border-gray-300 px-4 py-2 text-sm text-gray-600 hover:bg-gray-50"
        >
          <Download className="h-4 w-4" />
          Exportar PDF
        </button>
      </div>
    </div>
  )
}

export default function BenchmarkPage() {
  return (
    <div className="mx-auto max-w-4xl px-4 py-8">
      <OEBreadcrumb items={[{ label: "Benchmark Mercado" }]} />
      <h1 className="mb-1 text-2xl font-bold text-gray-900">Inteligencia local</h1>
      <p className="mb-6 text-sm text-gray-500">
        Analisis de demanda y disponibilidad de skills en el mercado laboral por jurisdiccion.
      </p>
      <Suspense fallback={<div className="py-12 text-center"><Loader2 className="w-8 h-8 animate-spin text-teal-600 mx-auto" /></div>}>
        <BenchmarkContent />
      </Suspense>
    </div>
  )
}
