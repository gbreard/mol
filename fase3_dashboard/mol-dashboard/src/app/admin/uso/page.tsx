'use client'

import { useState, useEffect } from 'react'
import { createClient } from '@/lib/supabase/browser'

interface ActividadUsuario {
  id: string
  nombre: string
  email: string
  rol: string
  total_busquedas: number
  total_exports: number
  ultima_busqueda: string | null
  ultimo_export: string | null
  last_sign_in_at: string | null
}

interface KPIs {
  usuarios_totales: number
  usuarios_activos: number
  busquedas_mes: number
  exports_mes: number
}

export default function AdminUsoPage() {
  const [actividad, setActividad] = useState<ActividadUsuario[]>([])
  const [kpis, setKpis] = useState<KPIs | null>(null)
  const [loading, setLoading] = useState(true)

  const supabase = createClient()

  useEffect(() => {
    cargarDatos()
  }, [])

  const cargarDatos = async () => {
    setLoading(true)

    const { data: { user } } = await supabase.auth.getUser()
    if (!user) return

    const { data: currentUser } = await supabase
      .from('usuarios')
      .select('organizacion_id')
      .eq('auth_id', user.id)
      .single()

    if (!currentUser) return

    // Cargar vista de actividad
    const { data: actividadData } = await supabase
      .from('v_actividad_usuarios')
      .select('*')
      .eq('organizacion_id', currentUser.organizacion_id)
      .order('total_busquedas', { ascending: false })

    setActividad(actividadData || [])

    // Calcular KPIs
    const usuarios = actividadData || []
    const ahora = new Date()
    const hace7dias = new Date(ahora.getTime() - 7 * 24 * 60 * 60 * 1000)

    setKpis({
      usuarios_totales: usuarios.length,
      usuarios_activos: usuarios.filter(u =>
        u.last_sign_in_at && new Date(u.last_sign_in_at) > hace7dias
      ).length,
      busquedas_mes: usuarios.reduce((sum, u) => sum + (u.total_busquedas || 0), 0),
      exports_mes: usuarios.reduce((sum, u) => sum + (u.total_exports || 0), 0),
    })

    setLoading(false)
  }

  const formatRelativeTime = (dateStr: string | null) => {
    if (!dateStr) return 'Nunca'
    const date = new Date(dateStr)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60))
    const diffDays = Math.floor(diffHours / 24)

    if (diffHours < 1) return 'Hace menos de 1 hora'
    if (diffHours < 24) return `Hace ${diffHours} horas`
    if (diffDays < 7) return `Hace ${diffDays} dias`
    return new Date(dateStr).toLocaleDateString('es-AR')
  }

  if (loading) {
    return (
      <div className="animate-pulse">
        <div className="h-8 w-48 bg-gray-200 rounded mb-6"></div>
        <div className="grid grid-cols-4 gap-4 mb-6">
          {[1,2,3,4].map(i => (
            <div key={i} className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <div className="h-4 w-20 bg-gray-200 rounded mb-2"></div>
              <div className="h-8 w-12 bg-gray-200 rounded"></div>
            </div>
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-5xl">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Dashboard de Uso</h1>

      {/* KPIs */}
      {kpis && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <p className="text-sm font-medium text-gray-500">Usuarios Totales</p>
            <p className="text-3xl font-semibold text-gray-900 mt-1">{kpis.usuarios_totales}</p>
          </div>
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <p className="text-sm font-medium text-gray-500">Activos (7 dias)</p>
            <p className="text-3xl font-semibold text-blue-600 mt-1">{kpis.usuarios_activos}</p>
          </div>
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <p className="text-sm font-medium text-gray-500">Busquedas (mes)</p>
            <p className="text-3xl font-semibold text-gray-900 mt-1">{kpis.busquedas_mes}</p>
          </div>
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <p className="text-sm font-medium text-gray-500">Exports (mes)</p>
            <p className="text-3xl font-semibold text-gray-900 mt-1">{kpis.exports_mes}</p>
          </div>
        </div>
      )}

      {/* Tabla de actividad */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Actividad por Usuario</h2>

        {actividad.length === 0 ? (
          <p className="text-gray-500 text-sm">No hay datos de actividad</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="bg-gray-50">
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Usuario
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Rol
                  </th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Busquedas
                  </th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Exports
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Ultimo acceso
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {actividad.map((u) => (
                  <tr key={u.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3">
                      <div>
                        <p className="text-sm font-medium text-gray-900">{u.nombre}</p>
                        <p className="text-xs text-gray-500">{u.email}</p>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                        u.rol === 'admin' ? 'bg-blue-100 text-blue-800' :
                        u.rol === 'analista' ? 'bg-green-100 text-green-800' :
                        'bg-gray-100 text-gray-800'
                      }`}>
                        {u.rol}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right">
                      <span className="text-sm font-medium text-gray-900">
                        {u.total_busquedas || 0}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right">
                      <span className="text-sm font-medium text-gray-900">
                        {u.total_exports || 0}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-500">
                      {formatRelativeTime(u.last_sign_in_at)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
