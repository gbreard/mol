'use client'

import { useState } from 'react'
import Link from 'next/link'
import {
  Search, Filter, Users, ChevronRight,
  Mail, Phone, CheckSquare,
} from 'lucide-react'

const CANDIDATOS = [
  {
    id: 'c1',
    nombre: 'Lucía Fernández',
    ocupacion: 'Desarrolladora Frontend',
    puesto: 'Desarrollador React',
    match: 96,
    skills: ['React', 'TypeScript', 'Next.js', 'REST APIs'],
    estado: 'nuevo',
    diasDisponible: 0,
    ubicacion: 'Buenos Aires',
  },
  {
    id: 'c2',
    nombre: 'Martín Soria',
    ocupacion: 'Analista de Datos',
    puesto: 'Analista de Datos Senior',
    match: 88,
    skills: ['Python', 'SQL', 'Power BI', 'Machine Learning'],
    estado: 'revisado',
    diasDisponible: 7,
    ubicacion: 'Córdoba',
  },
  {
    id: 'c3',
    nombre: 'Valentina Cruz',
    ocupacion: 'Desarrolladora React',
    puesto: 'Desarrollador React',
    match: 85,
    skills: ['React', 'JavaScript', 'CSS', 'Testing'],
    estado: 'nuevo',
    diasDisponible: 14,
    ubicacion: 'Buenos Aires',
  },
  {
    id: 'c4',
    nombre: 'Diego Méndez',
    ocupacion: 'Ingeniero DevOps',
    puesto: 'DevOps Engineer',
    match: 79,
    skills: ['Docker', 'Kubernetes', 'AWS', 'CI/CD'],
    estado: 'contactado',
    diasDisponible: 30,
    ubicacion: 'Rosario',
  },
  {
    id: 'c5',
    nombre: 'Sofía Ramos',
    ocupacion: 'QA Engineer',
    puesto: 'QA Automation',
    match: 71,
    skills: ['Selenium', 'Jest', 'Python', 'Bug tracking'],
    estado: 'nuevo',
    diasDisponible: 0,
    ubicacion: 'Buenos Aires',
  },
  {
    id: 'c6',
    nombre: 'Alejandro Torres',
    ocupacion: 'Product Manager',
    puesto: 'Product Manager',
    match: 83,
    skills: ['Agile', 'Scrum', 'Roadmap', 'KPIs'],
    estado: 'descartado',
    diasDisponible: 0,
    ubicacion: 'Mendoza',
  },
]

const ESTADO_CONFIG: Record<string, { label: string; color: string }> = {
  nuevo: { label: 'Nuevo', color: 'bg-blue-100 text-blue-700' },
  revisado: { label: 'Revisado', color: 'bg-gray-100 text-gray-600' },
  contactado: { label: 'Contactado', color: 'bg-green-100 text-green-700' },
  descartado: { label: 'Descartado', color: 'bg-red-100 text-red-500' },
}

const PUESTOS_FILTRO = ['Todos los puestos', 'Desarrollador React', 'Analista de Datos Senior', 'DevOps Engineer', 'QA Automation', 'Product Manager']

export default function EmpresasCandidatosPage() {
  const [busqueda, setBusqueda] = useState('')
  const [puestoFiltro, setPuestoFiltro] = useState('Todos los puestos')
  const [seleccionados, setSeleccionados] = useState<Set<string>>(new Set())

  const toggleSeleccion = (id: string) => {
    const next = new Set(seleccionados)
    if (next.has(id)) next.delete(id)
    else next.add(id)
    setSeleccionados(next)
  }

  const filtrados = CANDIDATOS.filter((c) => {
    const matchBusq = !busqueda.trim() ||
      c.nombre.toLowerCase().includes(busqueda.toLowerCase()) ||
      c.ocupacion.toLowerCase().includes(busqueda.toLowerCase())
    const matchPuesto = puestoFiltro === 'Todos los puestos' || c.puesto === puestoFiltro
    return matchBusq && matchPuesto
  })

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto px-4 py-8">

        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-xl font-bold text-gray-900">Candidatos</h1>
            <p className="text-sm text-gray-500 mt-0.5">{CANDIDATOS.length} perfiles · {CANDIDATOS.filter(c => c.estado === 'nuevo').length} nuevos</p>
          </div>
          {seleccionados.size >= 2 && (
            <Link
              href={`/empresas/candidatos/comparar?ids=${Array.from(seleccionados).join(',')}`}
              className="inline-flex items-center gap-2 bg-indigo-600 text-white text-sm font-semibold px-4 py-2.5 rounded-xl hover:bg-indigo-700 transition-colors"
            >
              <Users className="w-4 h-4" />
              Comparar {seleccionados.size}
            </Link>
          )}
        </div>

        {/* Búsqueda + filtros */}
        <div className="relative mb-3">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            value={busqueda}
            onChange={(e) => setBusqueda(e.target.value)}
            placeholder="Buscar por nombre u ocupación..."
            className="w-full rounded-xl border border-gray-200 bg-white pl-9 pr-3 py-2.5 text-sm text-gray-900 placeholder-gray-400 focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-100"
          />
        </div>

        <div className="flex items-center gap-2 mb-4 overflow-x-auto pb-1">
          <Filter className="w-4 h-4 text-gray-400 shrink-0" />
          {PUESTOS_FILTRO.map((f) => (
            <button
              key={f}
              onClick={() => setPuestoFiltro(f)}
              className={`shrink-0 text-xs font-medium px-3 py-1.5 rounded-full transition-all ${
                puestoFiltro === f
                  ? 'bg-indigo-600 text-white'
                  : 'bg-white border border-gray-200 text-gray-500 hover:border-gray-300'
              }`}
            >
              {f}
            </button>
          ))}
        </div>

        {/* Hint comparar */}
        {seleccionados.size === 1 && (
          <div className="mb-3 text-xs text-indigo-600 bg-indigo-50 border border-indigo-100 rounded-lg px-3 py-2">
            Seleccioná otro candidato para comparar lado a lado.
          </div>
        )}

        {/* Lista */}
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <div className="divide-y divide-gray-50">
            {filtrados.map((c) => {
              const est = ESTADO_CONFIG[c.estado]
              const isSelected = seleccionados.has(c.id)
              return (
                <div
                  key={c.id}
                  className={`flex items-center gap-3 px-4 py-3.5 transition-colors ${isSelected ? 'bg-indigo-50' : 'hover:bg-gray-50'}`}
                >
                  {/* Checkbox */}
                  <button
                    onClick={() => toggleSeleccion(c.id)}
                    className={`w-5 h-5 rounded border-2 flex items-center justify-center shrink-0 transition-colors ${
                      isSelected ? 'bg-indigo-600 border-indigo-600' : 'border-gray-300 hover:border-indigo-400'
                    }`}
                  >
                    {isSelected && <CheckSquare className="w-3.5 h-3.5 text-white" />}
                  </button>

                  {/* Avatar */}
                  <div className="w-9 h-9 rounded-full bg-indigo-100 text-indigo-700 text-xs font-bold flex items-center justify-center shrink-0">
                    {c.nombre.split(' ').map((n) => n[0]).join('').slice(0, 2)}
                  </div>

                  {/* Info */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <p className="text-sm font-semibold text-gray-900 truncate">{c.nombre}</p>
                      <span className={`hidden sm:inline text-[10px] px-2 py-0.5 rounded-full font-medium ${est.color}`}>
                        {est.label}
                      </span>
                    </div>
                    <p className="text-xs text-gray-500 truncate">{c.ocupacion} · {c.ubicacion}</p>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {c.skills.slice(0, 3).map((s) => (
                        <span key={s} className="text-[10px] bg-indigo-50 text-indigo-600 px-1.5 py-0.5 rounded">
                          {s}
                        </span>
                      ))}
                    </div>
                  </div>

                  {/* Match + acciones */}
                  <div className="flex items-center gap-3 shrink-0">
                    <span className={`text-sm font-bold tabular-nums ${c.match >= 85 ? 'text-green-600' : c.match >= 70 ? 'text-blue-600' : 'text-yellow-600'}`}>
                      {c.match}%
                    </span>
                    <div className="hidden sm:flex items-center gap-1">
                      <button className="p-1.5 rounded-lg hover:bg-gray-100 text-gray-400 hover:text-gray-600 transition-colors">
                        <Mail className="w-3.5 h-3.5" />
                      </button>
                      <button className="p-1.5 rounded-lg hover:bg-gray-100 text-gray-400 hover:text-gray-600 transition-colors">
                        <Phone className="w-3.5 h-3.5" />
                      </button>
                    </div>
                    <Link href={`/empresas/candidatos/${c.id}`}>
                      <ChevronRight className="w-4 h-4 text-gray-300" />
                    </Link>
                  </div>
                </div>
              )
            })}

            {filtrados.length === 0 && (
              <div className="py-12 text-center text-gray-400 text-sm">
                No hay candidatos con ese filtro.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
