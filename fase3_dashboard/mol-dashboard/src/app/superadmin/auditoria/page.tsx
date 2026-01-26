'use client'

import { useState, useEffect } from 'react'
import { createClient } from '@/lib/supabase/browser'

interface AuditLog {
  id: string
  usuario: {
    nombre: string
    email: string
  } | null
  organizacion: {
    nombre: string
  } | null
  accion: string
  recurso: string | null
  detalle: Record<string, unknown> | null
  ip_address: string | null
  created_at: string
}

const accionesDisponibles = [
  'LOGIN',
  'LOGOUT',
  'EXPORT',
  'SEARCH',
  'INVITAR',
  'CREATE_USER',
  'UPDATE_USER',
  'DELETE_USER',
  'SYNC',
]

export default function SuperAdminAuditoriaPage() {
  const [logs, setLogs] = useState<AuditLog[]>([])
  const [loading, setLoading] = useState(true)
  const [filtroAccion, setFiltroAccion] = useState<string>('todas')
  const [filtroOrg, setFiltroOrg] = useState<string>('todas')
  const [organizaciones, setOrganizaciones] = useState<{ id: string; nombre: string }[]>([])

  const supabase = createClient()

  useEffect(() => {
    cargarDatos()
  }, [])

  const cargarDatos = async () => {
    setLoading(true)

    // Cargar organizaciones para filtro
    const { data: orgs } = await supabase
      .from('organizaciones')
      .select('id, nombre')
      .order('nombre')

    setOrganizaciones(orgs || [])

    // Cargar logs
    const { data } = await supabase
      .from('audit_log')
      .select(`
        id,
        accion,
        recurso,
        detalle,
        ip_address,
        created_at,
        usuario:usuarios(nombre, email),
        organizacion:organizaciones(nombre)
      `)
      .order('created_at', { ascending: false })
      .limit(200)

    setLogs(data as unknown as AuditLog[] || [])
    setLoading(false)
  }

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('es-AR', {
      day: '2-digit',
      month: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const accionColor = (accion: string) => {
    switch (accion) {
      case 'LOGIN':
      case 'LOGOUT':
        return 'bg-blue-100 text-blue-800'
      case 'EXPORT':
        return 'bg-green-100 text-green-800'
      case 'SEARCH':
        return 'bg-gray-100 text-gray-800'
      case 'INVITAR':
      case 'CREATE_USER':
        return 'bg-purple-100 text-purple-800'
      case 'UPDATE_USER':
      case 'DELETE_USER':
        return 'bg-yellow-100 text-yellow-800'
      case 'SYNC':
        return 'bg-cyan-100 text-cyan-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  const logsFiltrados = logs.filter(log => {
    if (filtroAccion !== 'todas' && log.accion !== filtroAccion) return false
    if (filtroOrg !== 'todas' && log.organizacion?.nombre !== filtroOrg) return false
    return true
  })

  if (loading) {
    return (
      <div className="animate-pulse">
        <div className="h-8 w-48 bg-gray-200 rounded mb-6"></div>
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="space-y-3">
            {[1,2,3,4,5].map(i => (
              <div key={i} className="h-12 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-6xl">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Log de Auditoria</h1>

      {/* Filtros */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 mb-6">
        <div className="flex flex-wrap gap-4">
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">Accion</label>
            <select
              value={filtroAccion}
              onChange={(e) => setFiltroAccion(e.target.value)}
              className="px-3 py-1.5 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-purple-500"
            >
              <option value="todas">Todas las acciones</option>
              {accionesDisponibles.map(a => (
                <option key={a} value={a}>{a}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">Organizacion</label>
            <select
              value={filtroOrg}
              onChange={(e) => setFiltroOrg(e.target.value)}
              className="px-3 py-1.5 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-purple-500"
            >
              <option value="todas">Todas</option>
              {organizaciones.map(o => (
                <option key={o.id} value={o.nombre}>{o.nombre}</option>
              ))}
            </select>
          </div>
          <div className="flex items-end">
            <button
              onClick={() => {
                setFiltroAccion('todas')
                setFiltroOrg('todas')
              }}
              className="px-3 py-1.5 text-sm text-gray-600 hover:text-gray-900"
            >
              Limpiar filtros
            </button>
          </div>
        </div>
      </div>

      {/* Tabla de logs */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">
            Registros ({logsFiltrados.length})
          </h2>
          <button
            onClick={cargarDatos}
            className="text-sm text-purple-600 hover:text-purple-700 font-medium"
          >
            Actualizar
          </button>
        </div>

        {logsFiltrados.length === 0 ? (
          <div className="text-center py-8">
            <svg className="w-12 h-12 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
            </svg>
            <p className="text-gray-500">No hay registros de auditoria</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="bg-gray-50">
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Fecha
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Usuario
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Organizacion
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Accion
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Detalle
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {logsFiltrados.map((log) => (
                  <tr key={log.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 text-sm text-gray-500 whitespace-nowrap">
                      {formatDate(log.created_at)}
                    </td>
                    <td className="px-4 py-3">
                      {log.usuario ? (
                        <div>
                          <p className="text-sm font-medium text-gray-900">
                            {log.usuario.nombre}
                          </p>
                          <p className="text-xs text-gray-500">{log.usuario.email}</p>
                        </div>
                      ) : (
                        <span className="text-sm text-gray-500">Sistema</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-500">
                      {log.organizacion?.nombre || '-'}
                    </td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-1 text-xs font-medium rounded-full ${accionColor(log.accion)}`}>
                        {log.accion}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-500 max-w-xs truncate">
                      {log.recurso || (log.detalle ? JSON.stringify(log.detalle) : '-')}
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
