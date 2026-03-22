'use client'

import { useState, useEffect } from 'react'
import LearningDashboard, { type LearningData } from '@/components/LearningDashboard'

const MOCK_DATA: LearningData = {
  total_reglas_activas: 124,
  total_reglas_creadas: 156,
  tasa_error_actual: 3.2,
  tasa_error_inicial: 18.5,
  timeline_errores: [
    { fecha: 'Ene', tasa_error: 18.5, total_procesadas: 100 },
    { fecha: 'Feb', tasa_error: 12.0, total_procesadas: 400 },
    { fecha: 'Mar', tasa_error: 7.5,  total_procesadas: 800 },
    { fecha: 'Abr', tasa_error: 5.1,  total_procesadas: 1200 },
    { fecha: 'May', tasa_error: 3.2,  total_procesadas: 1800 },
  ],
  timeline_reglas: [
    { fecha: 'Ene 10', regla_id: 'R001', tipo: 'creada',    descripcion: 'Regla para Gerente de Ventas → ISCO 1221' },
    { fecha: 'Ene 15', regla_id: 'R002', tipo: 'creada',    descripcion: 'Regla para Contador Público → ISCO 2411' },
    { fecha: 'Feb 03', regla_id: 'R003', tipo: 'creada',    descripcion: 'Sinónimo: "programador" → desarrollador' },
    { fecha: 'Feb 20', regla_id: 'R001', tipo: 'modificada', descripcion: 'Ajuste Gerente de Ventas: agregar área comercial' },
    { fecha: 'Mar 05', regla_id: 'R045', tipo: 'creada',    descripcion: 'Regla sector construcción: albañil → ISCO 7112' },
  ],
  gold_set: [
    { oferta_id: 1, titulo: 'Programador Python', isco_esperado: '2512', isco_obtenido: '2512', correcto: true, score: 0.95 },
    { oferta_id: 2, titulo: 'Gerente de Ventas', isco_esperado: '1221', isco_obtenido: '1221', correcto: true, score: 0.92 },
    { oferta_id: 3, titulo: 'Contador Público', isco_esperado: '2411', isco_obtenido: '2411', correcto: true, score: 0.98 },
    { oferta_id: 4, titulo: 'Operario de Planta', isco_esperado: '8181', isco_obtenido: '7549', correcto: false, score: 0.61 },
    { oferta_id: 5, titulo: 'Recepcionista', isco_esperado: '4226', isco_obtenido: '4226', correcto: true, score: 0.89 },
  ],
}

export default function AprendizajePage() {
  const [data, setData] = useState<LearningData | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const load = async () => {
      try {
        const res = await fetch('/api/processing-metrics')
        if (res.ok) {
          const json = await res.json()
          setData(json.aprendizaje ?? MOCK_DATA)
        } else {
          setData(MOCK_DATA)
        }
      } catch {
        setData(MOCK_DATA)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-900 mb-1">Aprendizaje del sistema</h1>
      <p className="text-sm text-gray-500 mb-6">
        Evolución de la tasa de error, reglas creadas y resultados del Gold Set de referencia.
      </p>

      {loading ? (
        <div className="space-y-4">
          {[1, 2, 3].map((i) => <div key={i} className="h-32 animate-pulse rounded-xl bg-gray-100" />)}
        </div>
      ) : data ? (
        <LearningDashboard data={data} />
      ) : null}
    </div>
  )
}
