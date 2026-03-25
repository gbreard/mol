'use client'

import { useState } from 'react'
import Link from 'next/link'
import {
  Briefcase, Plus, ChevronRight, Search,
  Users, Clock, CheckCircle2, XCircle,
} from 'lucide-react'

const PUESTOS = [
  {
    id: 'p1',
    titulo: 'Desarrollador React',
    isco: '2512',
    descripcion: 'Desarrollo frontend con React 18, TypeScript y Next.js.',
    candidatos: 18,
    matchTop: 96,
    matchProm: 74,
    estado: 'activo',
    dias: 5,
    skills: ['React', 'TypeScript', 'Next.js', 'REST APIs', 'Git'],
  },
  {
    id: 'p2',
    titulo: 'Analista de Datos Senior',
    isco: '2521',
    descripcion: 'Análisis de datos con Python, SQL y visualización con Power BI.',
    candidatos: 7,
    matchTop: 88,
    matchProm: 65,
    estado: 'activo',
    dias: 12,
    skills: ['Python', 'SQL', 'Power BI', 'Machine Learning', 'Pandas'],
  },
  {
    id: 'p3',
    titulo: 'DevOps Engineer',
    isco: '2519',
    descripcion: 'CI/CD con GitHub Actions, Docker, Kubernetes y AWS.',
    candidatos: 4,
    matchTop: 79,
    matchProm: 58,
    estado: 'activo',
    dias: 8,
    skills: ['Docker', 'Kubernetes', 'AWS', 'CI/CD', 'Linux'],
  },
  {
    id: 'p4',
    titulo: 'QA Automation',
    isco: '2519',
    descripcion: 'Testing automatizado con Selenium, Cypress y Jest.',
    candidatos: 9,
    matchTop: 71,
    matchProm: 61,
    estado: 'activo',
    dias: 3,
    skills: ['Selenium', 'Cypress', 'Jest', 'Python', 'Testing'],
  },
  {
    id: 'p5',
    titulo: 'Product Manager',
    isco: '1221',
    descripcion: 'Gestión de producto digital con metodologías ágiles.',
    candidatos: 5,
    matchTop: 83,
    matchProm: 70,
    estado: 'activo',
    dias: 15,
    skills: ['Agile', 'Scrum', 'Roadmap', 'UX', 'KPIs'],
  },
  {
    id: 'p6',
    titulo: 'UX Designer',
    isco: '2166',
    descripcion: 'Diseño de experiencia de usuario con Figma.',
    candidatos: 3,
    matchTop: 77,
    matchProm: 63,
    estado: 'cerrado',
    dias: 45,
    skills: ['Figma', 'Diseño UX', 'Prototipado', 'User Research'],
  },
]

const FILTROS = ['todos', 'activo', 'cerrado']

export default function EmpresasPuestosPage() {
  const [busqueda, setBusqueda] = useState('')
  const [filtro, setFiltro] = useState('todos')

  const filtrados = PUESTOS.filter((p) => {
    const matchBusq = !busqueda.trim() ||
      p.titulo.toLowerCase().includes(busqueda.toLowerCase())
    const matchFiltro = filtro === 'todos' || p.estado === filtro
    return matchBusq && matchFiltro
  })

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto px-4 py-8">

        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-xl font-bold text-gray-900">Mis puestos</h1>
            <p className="text-sm text-gray-500 mt-0.5">
              {PUESTOS.filter((p) => p.estado === 'activo').length} activos · {PUESTOS.length} total
            </p>
          </div>
          <Link
            href="/empresas/puestos/nuevo"
            className="inline-flex items-center gap-2 bg-indigo-600 text-white text-sm font-semibold px-4 py-2.5 rounded-xl hover:bg-indigo-700 transition-colors"
          >
            <Plus className="w-4 h-4" />
            Nuevo puesto
          </Link>
        </div>

        {/* Búsqueda */}
        <div className="relative mb-4">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            value={busqueda}
            onChange={(e) => setBusqueda(e.target.value)}
            placeholder="Buscar puesto..."
            className="w-full rounded-xl border border-gray-200 bg-white pl-9 pr-3 py-2.5 text-sm text-gray-900 placeholder-gray-400 focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-100"
          />
        </div>

        {/* Filtros */}
        <div className="flex gap-1.5 mb-4">
          {FILTROS.map((f) => (
            <button
              key={f}
              onClick={() => setFiltro(f)}
              className={`text-xs font-medium px-3 py-1.5 rounded-full transition-all ${
                filtro === f
                  ? 'bg-indigo-600 text-white'
                  : 'bg-white border border-gray-200 text-gray-500 hover:border-gray-300'
              }`}
            >
              {f === 'todos' ? 'Todos' : f.charAt(0).toUpperCase() + f.slice(1)}
              <span className="ml-1 opacity-60">
                ({f === 'todos' ? PUESTOS.length : PUESTOS.filter((p) => p.estado === f).length})
              </span>
            </button>
          ))}
        </div>

        {/* Lista */}
        <div className="space-y-3">
          {filtrados.map((p) => (
            <Link
              key={p.id}
              href={`/empresas/puestos/${p.id}`}
              className="block bg-white rounded-xl border border-gray-200 p-4 hover:border-indigo-200 hover:shadow-sm transition-all"
            >
              <div className="flex items-start gap-3">
                {/* Icon */}
                <div className="w-10 h-10 rounded-lg bg-indigo-100 text-indigo-700 flex items-center justify-center shrink-0 mt-0.5">
                  <Briefcase className="w-5 h-5" />
                </div>

                {/* Info */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <p className="text-sm font-semibold text-gray-900">{p.titulo}</p>
                    <span className="text-[10px] font-mono text-gray-400 bg-gray-100 px-1.5 py-0.5 rounded">
                      ISCO {p.isco}
                    </span>
                    {p.estado === 'activo' ? (
                      <span className="flex items-center gap-1 text-[10px] bg-green-100 text-green-700 px-1.5 py-0.5 rounded-full font-medium">
                        <CheckCircle2 className="w-3 h-3" />
                        Activo
                      </span>
                    ) : (
                      <span className="flex items-center gap-1 text-[10px] bg-gray-100 text-gray-500 px-1.5 py-0.5 rounded-full font-medium">
                        <XCircle className="w-3 h-3" />
                        Cerrado
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-gray-400 mt-0.5 truncate">{p.descripcion}</p>

                  {/* Skills chips */}
                  <div className="flex flex-wrap gap-1.5 mt-2">
                    {p.skills.slice(0, 4).map((s) => (
                      <span key={s} className="text-[10px] bg-indigo-50 text-indigo-700 px-2 py-0.5 rounded font-medium">
                        {s}
                      </span>
                    ))}
                    {p.skills.length > 4 && (
                      <span className="text-[10px] text-gray-400">+{p.skills.length - 4} más</span>
                    )}
                  </div>
                </div>

                {/* Stats */}
                <div className="flex flex-col items-end gap-1.5 shrink-0">
                  <div className="flex items-center gap-1.5 text-xs text-gray-500">
                    <Users className="w-3.5 h-3.5" />
                    <span>{p.candidatos} candidatos</span>
                  </div>
                  <div className="flex items-center gap-1.5 text-xs text-gray-500">
                    <Clock className="w-3.5 h-3.5" />
                    <span>hace {p.dias}d</span>
                  </div>
                  <span className={`text-sm font-bold ${p.matchTop >= 85 ? 'text-green-600' : p.matchTop >= 70 ? 'text-blue-600' : 'text-yellow-600'}`}>
                    Top {p.matchTop}%
                  </span>
                </div>

                <ChevronRight className="w-4 h-4 text-gray-300 shrink-0 self-center" />
              </div>
            </Link>
          ))}

          {filtrados.length === 0 && (
            <div className="py-12 text-center text-gray-400 text-sm">
              No hay puestos con ese filtro.
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
