'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { Search, Plus, ChevronRight, Filter, Loader2 } from 'lucide-react'

// ─── Mock data ────────────────────────────────────────────────────────────────
const MOCK_CASOS = [
  { id: 'c001', nombre: 'María González', dni: '28.450.123', ocupacion: 'Administrativa', estado: 'en_diagnostico', match: 72, ultima_actividad: '2026-03-22', tecnico: 'Andrea P.' },
  { id: 'c002', nombre: 'Carlos Ruiz', dni: '35.122.987', ocupacion: 'Técnico IT', estado: 'derivado_vacante', match: 85, ultima_actividad: '2026-03-24', tecnico: 'Andrea P.' },
  { id: 'c003', nombre: 'Laura Méndez', dni: '31.765.432', ocupacion: 'Comercial', estado: 'perfil_completo', match: 63, ultima_actividad: '2026-03-18', tecnico: 'Andrea P.' },
  { id: 'c004', nombre: 'Roberto Sosa', dni: '40.234.567', ocupacion: 'Sin definir', estado: 'nuevo', match: null, ultima_actividad: '2026-03-25', tecnico: 'Andrea P.' },
  { id: 'c005', nombre: 'Ana Torres', dni: '29.876.543', ocupacion: 'Enfermería', estado: 'en_seguimiento', match: 78, ultima_actividad: '2026-03-16', tecnico: 'Andrea P.' },
  { id: 'c006', nombre: 'Juan Pérez', dni: '33.456.789', ocupacion: 'Programador', estado: 'derivado_curso', match: 56, ultima_actividad: '2026-03-23', tecnico: 'Marcos R.' },
  { id: 'c007', nombre: 'Silvia Romero', dni: '26.987.654', ocupacion: 'Docente', estado: 'insertado', match: 91, ultima_actividad: '2026-03-10', tecnico: 'Marcos R.' },
  { id: 'c008', nombre: 'Pablo Díaz', dni: '38.123.456', ocupacion: 'Logística', estado: 'cerrado', match: 44, ultima_actividad: '2026-02-28', tecnico: 'Andrea P.' },
]

const ESTADO_CONFIG: Record<string, { label: string; color: string }> = {
  nuevo: { label: 'Nuevo', color: 'bg-gray-100 text-gray-600' },
  en_diagnostico: { label: 'En diagnóstico', color: 'bg-blue-100 text-blue-700' },
  perfil_completo: { label: 'Perfil completo', color: 'bg-purple-100 text-purple-700' },
  derivado_vacante: { label: 'Derivado vacante', color: 'bg-green-100 text-green-700' },
  derivado_curso: { label: 'Derivado curso', color: 'bg-orange-100 text-orange-700' },
  en_seguimiento: { label: 'En seguimiento', color: 'bg-yellow-100 text-yellow-700' },
  insertado: { label: 'Insertado ✓', color: 'bg-emerald-100 text-emerald-700' },
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
  const [casos, setCasos] = useState(MOCK_CASOS)
  const [cargando, setCargando] = useState(false)

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
          if (Array.isArray(data) && data.length > 0) {
            setCasos(data.map((c: any) => ({
              id: c.id,
              nombre: c.persona_nombre,
              dni: c.persona_dni || '',
              ocupacion: c.objetivo || 'Sin definir',
              estado: c.estado,
              match: null,
              ultima_actividad: c.ultima_atencion || c.created_at,
              tecnico: '',
            })))
          }
        }
      } catch { /* usa mock */ } finally {
        setCargando(false)
      }
    }
    const t = setTimeout(cargar, 300)
    return () => clearTimeout(t)
  }, [busqueda, estadoFiltro])

  const casosFiltrados = casos.filter((c) => {
    const matchBusq = !busqueda.trim() ||
      c.nombre.toLowerCase().includes(busqueda.toLowerCase()) ||
      c.dni.includes(busqueda) ||
      c.ocupacion.toLowerCase().includes(busqueda.toLowerCase())
    const matchEstado = estadoFiltro === 'todos' || c.estado === estadoFiltro
    return matchBusq && matchEstado
  })

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto px-4 py-8">

        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-xl font-bold text-gray-900">Cartera de casos</h1>
            <p className="text-sm text-gray-500 mt-0.5">{MOCK_CASOS.length} personas · {MOCK_CASOS.filter(c => c.estado !== 'cerrado' && c.estado !== 'insertado').length} activas</p>
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
            placeholder="Buscar por nombre, DNI u ocupación..."
            className="w-full rounded-xl border border-gray-200 bg-white pl-9 pr-3 py-2.5 text-sm text-gray-900 placeholder-gray-400 focus:border-teal-400 focus:outline-none focus:ring-2 focus:ring-teal-100"
          />
        </div>

        {/* Filtros de estado */}
        <div className="flex gap-1.5 overflow-x-auto pb-1 mb-4">
          <Filter className="w-4 h-4 text-gray-400 shrink-0 my-auto" />
          {FILTROS_ESTADO.map((f) => (
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
              {f !== 'todos' && (
                <span className="ml-1 opacity-60">
                  ({MOCK_CASOS.filter(c => c.estado === f).length})
                </span>
              )}
            </button>
          ))}
        </div>

        {/* Lista */}
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          {cargando ? (
            <div className="py-12 flex items-center justify-center gap-2 text-gray-400">
              <Loader2 className="w-4 h-4 animate-spin" />
              <span className="text-sm">Cargando...</span>
            </div>
          ) : casosFiltrados.length === 0 ? (
            <div className="py-12 text-center text-gray-400 text-sm">
              No se encontraron casos con ese filtro.
            </div>
          ) : (
            <div className="divide-y divide-gray-50">
              {casosFiltrados.map((c) => {
                const est = ESTADO_CONFIG[c.estado]
                const diasSinActividad = Math.floor((Date.now() - new Date(c.ultima_actividad).getTime()) / 86400000)
                return (
                  <Link
                    key={c.id}
                    href={`/oficina-empleo/casos/${c.id}`}
                    className="flex items-center gap-3 px-4 py-3.5 hover:bg-gray-50 transition-colors"
                  >
                    {/* Avatar */}
                    <div className="w-9 h-9 rounded-full bg-teal-100 text-teal-700 text-xs font-bold flex items-center justify-center shrink-0">
                      {c.nombre.split(' ').map((n) => n[0]).join('').slice(0, 2)}
                    </div>

                    {/* Info principal */}
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
                        <span className="text-xs text-gray-500 truncate">{c.ocupacion}</span>
                        <span className="text-gray-200">·</span>
                        <span className="text-xs text-gray-400">{diasDesde(c.ultima_actividad)}</span>
                      </div>
                    </div>

                    {/* Match + estado */}
                    <div className="flex items-center gap-2 shrink-0">
                      {c.match !== null && (
                        <span className={`text-xs font-bold tabular-nums ${c.match >= 80 ? 'text-green-600' : c.match >= 60 ? 'text-blue-600' : 'text-yellow-600'}`}>
                          {c.match}%
                        </span>
                      )}
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
