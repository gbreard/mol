'use client'

import { useState, useEffect } from 'react'
import { createClient } from '@/lib/supabase/browser'

interface Exportacion {
  id: string
  usuario: {
    nombre: string
    email: string
  }
  tipo: string
  nombre_archivo: string
  filtros_aplicados: Record<string, unknown>
  filas_exportadas: number
  tamano_bytes: number | null
  created_at: string
}

export default function AdminExportacionesPage() {
  const [exportaciones, setExportaciones] = useState<Exportacion[]>([])
  const [loading, setLoading] = useState(true)
  const [filtroTipo, setFiltroTipo] = useState<string>('todos')

  const supabase = createClient()

  useEffect(() => {
    cargarExportaciones()
  }, [])

  const cargarExportaciones = async () => {
    setLoading(true)

    const { data: { user } } = await supabase.auth.getUser()
    if (!user) return

    const { data: currentUser } = await supabase
      .from('usuarios')
      .select('organizacion_id')
      .eq('auth_id', user.id)
      .single()

    if (!currentUser) return

    const { data } = await supabase
      .from('exportaciones')
      .select(`
        id,
        tipo,
        nombre_archivo,
        filtros_aplicados,
        filas_exportadas,
        tamano_bytes,
        created_at,
        usuario:usuarios(nombre, email)
      `)
      .eq('organizacion_id', currentUser.organizacion_id)
      .order('created_at', { ascending: false })
      .limit(100)

    setExportaciones(data as unknown as Exportacion[] || [])
    setLoading(false)
  }

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('es-AR', {
      day: '2-digit',
      month: '2-digit',
      year: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const formatSize = (bytes: number | null) => {
    if (!bytes) return '-'
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  const tipoIcono = (tipo: string) => {
    switch (tipo) {
      case 'xlsx':
        return (
          <span className="text-green-600">
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
              <path d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" />
            </svg>
          </span>
        )
      case 'csv':
        return (
          <span className="text-blue-600">
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
              <path d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" />
            </svg>
          </span>
        )
      case 'pdf':
        return (
          <span className="text-red-600">
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
              <path d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" />
            </svg>
          </span>
        )
      default:
        return null
    }
  }

  const exportacionesFiltradas = filtroTipo === 'todos'
    ? exportaciones
    : exportaciones.filter(e => e.tipo === filtroTipo)

  // Stats
  const stats = {
    total: exportaciones.length,
    xlsx: exportaciones.filter(e => e.tipo === 'xlsx').length,
    csv: exportaciones.filter(e => e.tipo === 'csv').length,
    pdf: exportaciones.filter(e => e.tipo === 'pdf').length,
  }

  if (loading) {
    return (
      <div className="animate-pulse">
        <div className="h-8 w-48 bg-gray-200 rounded mb-6"></div>
        <div className="grid grid-cols-4 gap-4 mb-6">
          {[1,2,3,4].map(i => (
            <div key={i} className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
              <div className="h-4 w-16 bg-gray-200 rounded mb-2"></div>
              <div className="h-6 w-8 bg-gray-200 rounded"></div>
            </div>
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-5xl">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Historial de Exportaciones</h1>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
          <p className="text-sm text-gray-500">Total</p>
          <p className="text-2xl font-semibold text-gray-900">{stats.total}</p>
        </div>
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
          <p className="text-sm text-gray-500">Excel</p>
          <p className="text-2xl font-semibold text-green-600">{stats.xlsx}</p>
        </div>
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
          <p className="text-sm text-gray-500">CSV</p>
          <p className="text-2xl font-semibold text-blue-600">{stats.csv}</p>
        </div>
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
          <p className="text-sm text-gray-500">PDF</p>
          <p className="text-2xl font-semibold text-red-600">{stats.pdf}</p>
        </div>
      </div>

      {/* Filtro */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">
            Exportaciones ({exportacionesFiltradas.length})
          </h2>
          <select
            value={filtroTipo}
            onChange={(e) => setFiltroTipo(e.target.value)}
            className="px-3 py-1 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500"
          >
            <option value="todos">Todos los tipos</option>
            <option value="xlsx">Excel (.xlsx)</option>
            <option value="csv">CSV</option>
            <option value="pdf">PDF</option>
          </select>
        </div>

        {exportacionesFiltradas.length === 0 ? (
          <div className="text-center py-8">
            <svg className="w-12 h-12 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
            </svg>
            <p className="text-gray-500">No hay exportaciones registradas</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="bg-gray-50">
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Archivo
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Usuario
                  </th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Filas
                  </th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Tamaño
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Fecha
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {exportacionesFiltradas.map((exp) => (
                  <tr key={exp.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        {tipoIcono(exp.tipo)}
                        <div>
                          <p className="text-sm font-medium text-gray-900">
                            {exp.nombre_archivo || `export.${exp.tipo}`}
                          </p>
                          <p className="text-xs text-gray-500 uppercase">{exp.tipo}</p>
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <p className="text-sm text-gray-900">{exp.usuario?.nombre || '-'}</p>
                      <p className="text-xs text-gray-500">{exp.usuario?.email || '-'}</p>
                    </td>
                    <td className="px-4 py-3 text-right">
                      <span className="text-sm font-medium text-gray-900">
                        {exp.filas_exportadas?.toLocaleString() || '-'}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right text-sm text-gray-500">
                      {formatSize(exp.tamano_bytes)}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-500">
                      {formatDate(exp.created_at)}
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
