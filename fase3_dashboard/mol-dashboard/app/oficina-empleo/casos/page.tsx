'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { Search, Plus, ChevronRight, Filter, Loader2 } from 'lucide-react'

interface Caso {
  id: string
  nombre: string
  dni: string
  ocupacion: string
  estado: string
  match: number | null
  ultima_actividad: string
}

const ESTADO_CONFIG: Record<string, { label: string; color: string }> = {
  nuevo: { label: 'Nuevo', color: 'bg-gray-100 text-gray-600' },
  en_diagnostico: { label: 'En diagnóstico', color: 'bg-blue-100 text-blue-700' },
  perfil_completo: { label: 'Perfil completo', color: 'bg-purple-100 text-purple-700' },
  derivado_vacante: { label: 'Derivado vacante', color: 'bg-green-100 text-green-700' },
  derivado_curso: { label: 'Derivado curso', color: 'bg-orange-100 text-orange-700' },
  en_seguimiento: { label: 'En seguimiento', color: 'bg-yellow-100 text-yellow-700' },
  insertado: { label: 'Insertado', color: 'bg-emerald-100 text-emerald-700' },
  cerrado: { label: 'Cerrado', color: 'bg-gray-100 text-gray-400' },
}

const FILTROS_ESTADO = ['todos', 'nuevo', 'en_diagnostico', 'perfil_completo', 'derivado_vacante', 'derivado_curso', 'en_seguimiento', 'insertado', 'cerrado']

function diasDesde(fecha: string) {
  const diff = Math.floor((Date.now() - new Date(fecha).getTime()) / 86400000)
  if (diff === 0) return 'hoy'
  if (diff === 1) return 'ayer'
  return `hace ${diff} días`
}

export default function CarteraCasosPage() {
  const [busqueda, setBusqueda] = useState('')
  const [estadoFiltro, setEstadoFiltro] = useState('todos')
  const [casos, setCasos] = useState<Caso[]>([])
  const [cargando, setCargando] = useState(true)

  useEffect(() => {
    async function cargar() {
      setCargando(true)
      try {
        const params = new URLSearchParams()
        if (estadoFiltro !== 'todos') params.set('estado', estadoFiltro)
        if (busqueda.trim()) params.set('q', busqueda.trim())
        const res = await fetch(`/api/casos?${params}`)
        if (res.ok) {
          const data = await res.json()
          if (Array.isArray(data)) {
            setCasos(data.map((c: any) => ({
              id: c.id,
              nombre: c.persona_nombre || 'Sin nombre',
              dni: c.persona_dni || '',
              ocupacion: c.objetivo || 'empleo',
              estado: c.estado,
              match: null,
              ultima_actividad: c.ultima_atencion || c.created_at,
            })))
          }
        }
      } catch (e) {
        console.error('Error cargando casos:', e)
      } finally {
        setCargando(false)
      }
    }
    const t = setTimeout(cargar, 300)
    return () => clearTimeout(t)
  }, [busqueda, estadoFiltro])

  const casosFiltrados = casos.filter((c) => {
    const matchBusq = !busqueda.trim() ||
      c.nombre.toLowerCase().includes(busqueda.toLowerCase()) ||
      c.dni.includes(busqueda)
    const matchEstado = estadoFiltro === 'todos' || c.estado === estadoFiltro
    return matchBusq && matchEstado
  })

  const activos = casos.filter(c => c.estado !== 'cerrado' && c.estado !== 'insertado').length

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto px-4 py-8">

        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-xl font-bold text-gray-900">Cartera de casos</h1>
            <p className="text-sm text-gray-500 mt-0.5">{casos.length} personas · {activos} activas</p>
          </div>
          <Link
            href="/oficina-empleo/casos/nuevo"
            className="inline-flex items-center gap-2 bg-teal-600 text-white text-sm font-semibold px-4 py-2.5 rounded-xl hover:bg-teal-700 transition-colors"
          >
            <Plus className="w-4 h-4" />
            Nuevo caso
          </Link>
        </div>

        {/* Búsqueda */}
        <div className="relative mb-4">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            value={busqueda}
            onChange={(e) => setBusqueda(e.target.value)}
            placeholder="Buscar por nombre o DNI..."
            className="w-full rounded-xl border border-gray-200 bg-white pl-9 pr-3 py-2.5 text-sm text-gray-900 placeholder-gray-400 focus:border-teal-400 focus:outline-none focus:ring-2 focus:ring-teal-100"
          />
        </div>

        {/* Filtros de estado */}
        <div className="flex gap-1.5 overflow-x-auto pb-1 mb-4">
          <Filter className="w-4 h-4 text-gray-400 shrink-0 my-auto" />
          {FILTROS_ESTADO.map((f) => {
            const count = casos.filter(c => c.estado === f).length
            return (
              <button
                key={f}
                onClick={() => setEstadoFiltro(f)}
                className={`shrink-0 text-xs font-medium px-3 py-1.5 rounded-full transition-all ${
                  estadoFiltro === f
                    ? 'bg-teal-600 text-white'
                    : 'bg-white border border-gray-200 text-gray-500 hover:border-gray-300'
                }`}
              >
                {f === 'todos' ? 'Todos' : (ESTADO_CONFIG[f]?.label ?? f)}
                {f !== 'todos' && count > 0 && (
                  <span className="ml-1 opacity-60">({count})</span>
                )}
              </button>
            )
          })}
        </div>

        {/* Lista */}
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          {cargando ? (
            <div className="py-12 flex items-center justify-center gap-2 text-gray-400">
              <Loader2 className="w-4 h-4 animate-spin" />
              <span className="text-sm">Cargando casos...</span>
            </div>
          ) : casosFiltrados.length === 0 ? (
            <div className="py-12 text-center text-gray-400 text-sm">
              {casos.length === 0 ? 'No hay casos registrados.' : 'No se encontraron casos con ese filtro.'}
            </div>
          ) : (
            <div className="divide-y divide-gray-50">
              {casosFiltrados.map((c) => {
                const est = ESTADO_CONFIG[c.estado] || ESTADO_CONFIG.nuevo
                const diasSinActividad = Math.floor((Date.now() - new Date(c.ultima_actividad).getTime()) / 86400000)
                return (
                  <Link
                    key={c.id}
                    href={`/oficina-empleo/casos/${c.id}`}
                    className="flex items-center gap-3 px-4 py-3.5 hover:bg-gray-50 transition-colors"
                  >
                    <div className="w-9 h-9 rounded-full bg-teal-100 text-teal-700 text-xs font-bold flex items-center justify-center shrink-0">
                      {c.nombre.split(' ').map((n) => n[0]).join('').slice(0, 2)}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <p className="text-sm font-semibold text-gray-900 truncate">{c.nombre}</p>
                        {diasSinActividad >= 7 && c.estado !== 'insertado' && c.estado !== 'cerrado' && (
                          <span className="text-[10px] bg-red-50 text-red-500 px-1.5 py-0.5 rounded font-medium shrink-0">
                            {diasSinActividad}d sin actividad
                          </span>
                        )}
                      </div>
                      <div className="flex items-center gap-2 mt-0.5">
                        <span className="text-xs text-gray-400">{c.dni}</span>
                        <span className="text-gray-200">·</span>
                        <span className="text-xs text-gray-400">{diasDesde(c.ultima_actividad)}</span>
                      </div>
                    </div>
                    <div className="flex items-center gap-2 shrink-0">
                      <span className={`hidden sm:inline text-[10px] px-2 py-0.5 rounded-full font-medium ${est.color}`}>
                        {est.label}
                      </span>
                      <ChevronRight className="w-4 h-4 text-gray-300" />
                    </div>
                  </Link>
                )
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
