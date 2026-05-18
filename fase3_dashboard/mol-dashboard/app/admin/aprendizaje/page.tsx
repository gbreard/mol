'use client'

import { useState, useEffect } from 'react'
import LearningDashboard, { type LearningData } from '@/components/LearningDashboard'
import { PipelineRunsHistory } from '@/components/aprendizaje/PipelineRunsHistory'

export default function AprendizajePage() {
  const [data, setData] = useState<LearningData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)

  useEffect(() => {
    const load = async () => {
      try {
        const res = await fetch('/api/processing-metrics')
        if (res.ok) {
          const json = await res.json()
          setData(json.aprendizaje ?? null)
          if (!json.aprendizaje) setError(true)
        } else {
          setError(true)
        }
      } catch {
        setError(true)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 mb-1">Aprendizaje del sistema</h1>
        <p className="text-sm text-gray-500">
          Evolución de la tasa de error, reglas creadas y resultados del Gold Set de referencia.
        </p>
      </div>

      {loading ? (
        <div className="space-y-4">
          {[1, 2, 3].map((i) => <div key={i} className="h-32 animate-pulse rounded-xl bg-gray-100" />)}
        </div>
      ) : error ? (
        <p className="text-sm text-red-500">No se pudo cargar los datos de aprendizaje del sistema.</p>
      ) : data ? (
        <LearningDashboard data={data} />
      ) : null}

      <PipelineRunsHistory />
    </div>
  )
}
