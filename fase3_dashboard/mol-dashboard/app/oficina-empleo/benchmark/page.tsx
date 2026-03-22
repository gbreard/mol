'use client'

import { Suspense, useState, useEffect } from 'react'
import { useSearchParams } from 'next/navigation'
import MarketBenchmark, { type MarketBenchmarkData } from '@/components/MarketBenchmark'

const MOCK_DATA: MarketBenchmarkData = {
  jurisdiccion: 'CABA',
  total_ofertas: 5240,
  total_perfiles: 1830,
  skills: [
    { uri: 'e1', label: 'Python',             demanda_pct: 45, disponibilidad_pct: 18, brecha: 27, dificultad: 'alta',  tendencia: 'subiendo' },
    { uri: 'e2', label: 'SQL',                demanda_pct: 38, disponibilidad_pct: 22, brecha: 16, dificultad: 'alta',  tendencia: 'subiendo' },
    { uri: 'e3', label: 'Excel avanzado',     demanda_pct: 62, disponibilidad_pct: 54, brecha: 8,  dificultad: 'media', tendencia: 'estable' },
    { uri: 'e4', label: 'Atención al cliente',demanda_pct: 71, disponibilidad_pct: 68, brecha: 3,  dificultad: 'baja',  tendencia: 'bajando' },
    { uri: 'e5', label: 'Manejo de CRM',      demanda_pct: 29, disponibilidad_pct: 11, brecha: 18, dificultad: 'alta',  tendencia: 'subiendo' },
    { uri: 'e6', label: 'Soldadura MIG',      demanda_pct: 15, disponibilidad_pct: 12, brecha: 3,  dificultad: 'baja',  tendencia: 'estable' },
  ],
}

function BenchmarkContent() {
  const searchParams = useSearchParams()
  const jurisdiccion = searchParams.get('jurisdiccion') ?? 'CABA'
  const [data, setData] = useState<MarketBenchmarkData | null>(null)
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

  return loading ? (
    <div className="space-y-4">
      {[1, 2].map((i) => <div key={i} className="h-24 animate-pulse rounded-xl bg-gray-100" />)}
    </div>
  ) : data ? <MarketBenchmark data={data} /> : null
}

export default function BenchmarkPage() {
  return (
    <div className="mx-auto max-w-4xl px-4 py-8">
      <h1 className="mb-1 text-2xl font-bold text-gray-900">Inteligencia local</h1>
      <p className="mb-6 text-sm text-gray-500">
        Disponibilidad y demanda de skills en el mercado laboral de la jurisdicción.
      </p>
      <Suspense fallback={<div className="h-24 animate-pulse rounded-xl bg-gray-100" />}>
        <BenchmarkContent />
      </Suspense>
    </div>
  )
}
