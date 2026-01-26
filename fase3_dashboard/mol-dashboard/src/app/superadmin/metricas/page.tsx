'use client'

import { useState, useEffect } from 'react'
import { createClient } from '@/lib/supabase/browser'

interface MetricasSistema {
  ofertas_totales: number
  usuarios_totales: number
  organizaciones_totales: number
  busquedas_mes: number
  exports_mes: number
  usuarios_activos_semana: number
}

interface PipelineStatus {
  fase: string
  estado: 'ok' | 'warning' | 'error'
  ultimo_run: string | null
  errores: number
}

export default function SuperAdminMetricasPage() {
  const [metricas, setMetricas] = useState<MetricasSistema | null>(null)
  const [pipelineStatus, setPipelineStatus] = useState<PipelineStatus[]>([])
  const [loading, setLoading] = useState(true)

  const supabase = createClient()

  useEffect(() => {
    cargarDatos()
  }, [])

  const cargarDatos = async () => {
    setLoading(true)

    // Cargar metricas desde la vista
    const { data: metricasData } = await supabase
      .from('v_metricas_sistema')
      .select('*')
      .single()

    if (metricasData) {
      setMetricas(metricasData as MetricasSistema)
    }

    // Simular estado del pipeline (en produccion vendria de BD)
    setPipelineStatus([
      { fase: 'Scraping', estado: 'ok', ultimo_run: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(), errores: 0 },
      { fase: 'NLP', estado: 'ok', ultimo_run: new Date(Date.now() - 1 * 60 * 60 * 1000).toISOString(), errores: 3 },
      { fase: 'Matching', estado: 'ok', ultimo_run: new Date(Date.now() - 1 * 60 * 60 * 1000).toISOString(), errores: 0 },
      { fase: 'Validacion', estado: 'warning', ultimo_run: new Date(Date.now() - 30 * 60 * 1000).toISOString(), errores: 12 },
    ])

    setLoading(false)
  }

  const formatRelativeTime = (dateStr: string | null) => {
    if (!dateStr) return 'Nunca'
    const date = new Date(dateStr)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffMinutes = Math.floor(diffMs / (1000 * 60))
    const diffHours = Math.floor(diffMinutes / 60)

    if (diffMinutes < 60) return `Hace ${diffMinutes} min`
    if (diffHours < 24) return `Hace ${diffHours}h`
    return new Date(dateStr).toLocaleDateString('es-AR')
  }

  const statusIcon = (estado: string) => {
    switch (estado) {
      case 'ok':
        return <span className="text-green-500">✓</span>
      case 'warning':
        return <span className="text-yellow-500">⚠</span>
      case 'error':
        return <span className="text-red-500">✕</span>
      default:
        return null
    }
  }

  if (loading) {
    return (
      <div className="animate-pulse">
        <div className="h-8 w-64 bg-gray-200 rounded mb-6"></div>
        <div className="grid grid-cols-3 gap-4 mb-6">
          {[1,2,3].map(i => (
            <div key={i} className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <div className="h-4 w-24 bg-gray-200 rounded mb-2"></div>
              <div className="h-10 w-16 bg-gray-200 rounded"></div>
            </div>
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-5xl">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Metricas del Sistema</h1>

      {/* KPIs principales */}
      {metricas && (
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-6">
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <p className="text-sm font-medium text-gray-500">Ofertas Totales</p>
            <p className="text-3xl font-semibold text-gray-900 mt-1">
              {metricas.ofertas_totales?.toLocaleString() || 0}
            </p>
          </div>
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <p className="text-sm font-medium text-gray-500">Usuarios Totales</p>
            <p className="text-3xl font-semibold text-gray-900 mt-1">
              {metricas.usuarios_totales || 0}
            </p>
            <p className="text-xs text-green-600 mt-1">
              {metricas.usuarios_activos_semana || 0} activos esta semana
            </p>
          </div>
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <p className="text-sm font-medium text-gray-500">Organizaciones</p>
            <p className="text-3xl font-semibold text-gray-900 mt-1">
              {metricas.organizaciones_totales || 0}
            </p>
          </div>
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <p className="text-sm font-medium text-gray-500">Busquedas (mes)</p>
            <p className="text-3xl font-semibold text-blue-600 mt-1">
              {metricas.busquedas_mes?.toLocaleString() || 0}
            </p>
          </div>
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <p className="text-sm font-medium text-gray-500">Exports (mes)</p>
            <p className="text-3xl font-semibold text-blue-600 mt-1">
              {metricas.exports_mes?.toLocaleString() || 0}
            </p>
          </div>
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <p className="text-sm font-medium text-gray-500">Estado Pipeline</p>
            <p className="text-3xl font-semibold text-green-600 mt-1">OK</p>
          </div>
        </div>
      )}

      {/* Estado del Pipeline */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Estado del Pipeline</h2>

        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="bg-gray-50">
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Fase
                </th>
                <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Estado
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Ultimo Run
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Errores
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {pipelineStatus.map((fase) => (
                <tr key={fase.fase} className="hover:bg-gray-50">
                  <td className="px-4 py-3 text-sm font-medium text-gray-900">
                    {fase.fase}
                  </td>
                  <td className="px-4 py-3 text-center text-lg">
                    {statusIcon(fase.estado)}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-500">
                    {formatRelativeTime(fase.ultimo_run)}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <span className={`text-sm font-medium ${
                      fase.errores > 0 ? 'text-red-600' : 'text-gray-500'
                    }`}>
                      {fase.errores}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Informacion del sistema */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Informacion del Sistema</h2>

        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <p className="text-gray-500">Version</p>
            <p className="font-medium text-gray-900">MOL v3.4.3</p>
          </div>
          <div>
            <p className="text-gray-500">Base de datos</p>
            <p className="font-medium text-gray-900">Supabase PostgreSQL</p>
          </div>
          <div>
            <p className="text-gray-500">Dashboard</p>
            <p className="font-medium text-gray-900">Next.js 16.1.3</p>
          </div>
          <div>
            <p className="text-gray-500">Ultima actualizacion</p>
            <p className="font-medium text-gray-900">{new Date().toLocaleDateString('es-AR')}</p>
          </div>
        </div>
      </div>
    </div>
  )
}
