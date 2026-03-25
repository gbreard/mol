'use client'

import { useState } from 'react'
import Link from 'next/link'
import { Search, Plus, ChevronRight, Users, TrendingUp } from 'lucide-react'

const MOCK_VACANTES = [
  {
    id: 'v001', titulo: 'Recepcionista administrativa', empresa: 'Clínica Santa Rosa',
    modalidad: 'Presencial', vacantes: 2, candidatos: 5, estado: 'activa',
    isco: '4120', match_promedio: 76, fecha: '2026-03-20',
  },
  {
    id: 'v002', titulo: 'Asistente contable', empresa: 'Estudio Jiménez',
    modalidad: 'Híbrido', vacantes: 1, candidatos: 3, estado: 'activa',
    isco: '4311', match_promedio: 68, fecha: '2026-03-18',
  },
  {
    id: 'v003', titulo: 'Técnico IT soporte', empresa: 'TechSolutions SA',
    modalidad: 'Presencial', vacantes: 3, candidatos: 8, estado: 'activa',
    isco: '3512', match_promedio: 81, fecha: '2026-03-15',
  },
  {
    id: 'v004', titulo: 'Operario manufactura', empresa: 'Metalúrgica Río',
    modalidad: 'Presencial', vacantes: 5, candidatos: 2, estado: 'cerrada',
    isco: '7212', match_promedio: 55, fecha: '2026-03-01',
  },
]

export default function VacantesOEPage() {
  const [busqueda, setBusqueda] = useState('')
  const [filtro, setFiltro] = useState<'todas' | 'activa' | 'cerrada'>('activa')

  const vacantes = MOCK_VACANTES.filter((v) => {
    const matchB = v.titulo.toLowerCase().includes(busqueda.toLowerCase()) || v.empresa.toLowerCase().includes(busqueda.toLowerCase())
    const matchF = filtro === 'todas' || v.estado === filtro
    return matchB && matchF
  })

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto px-4 py-8">

        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-xl font-bold text-gray-900">Vacantes OE</h1>
            <p className="text-sm text-gray-500 mt-0.5">
              {MOCK_VACANTES.filter((v) => v.estado === 'activa').length} activas · {MOCK_VACANTES.reduce((s, v) => s + v.candidatos, 0)} candidatos derivados
            </p>
          </div>
          <Link
            href="/oficina-empleo/vacantes/nueva"
            className="inline-flex items-center gap-2 bg-teal-600 text-white text-sm font-semibold px-4 py-2.5 rounded-xl hover:bg-teal-700 transition-colors"
          >
            <Plus className="w-4 h-4" />
            Nueva vacante
          </Link>
        </div>

        {/* Búsqueda + filtro */}
        <div className="flex gap-2 mb-4">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              value={busqueda}
              onChange={(e) => setBusqueda(e.target.value)}
              placeholder="Buscar por título o empresa..."
              className="w-full rounded-xl border border-gray-200 bg-white pl-9 pr-3 py-2.5 text-sm focus:border-teal-400 focus:outline-none focus:ring-2 focus:ring-teal-100"
            />
          </div>
          <div className="flex bg-white border border-gray-200 rounded-xl overflow-hidden">
            {(['todas', 'activa', 'cerrada'] as const).map((f) => (
              <button
                key={f}
                onClick={() => setFiltro(f)}
                className={`px-3 py-2 text-xs font-medium transition-colors ${filtro === f ? 'bg-teal-600 text-white' : 'text-gray-500 hover:bg-gray-50'}`}
              >
                {f === 'todas' ? 'Todas' : f === 'activa' ? 'Activas' : 'Cerradas'}
              </button>
            ))}
          </div>
        </div>

        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          {vacantes.length === 0 ? (
            <div className="py-12 text-center text-gray-400 text-sm">No hay vacantes con ese filtro.</div>
          ) : (
            <div className="divide-y divide-gray-50">
              {vacantes.map((v) => (
                <Link
                  key={v.id}
                  href={`/oficina-empleo/vacantes/${v.id}`}
                  className="flex items-center gap-4 px-4 py-4 hover:bg-gray-50 transition-colors"
                >
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <p className="text-sm font-semibold text-gray-900 truncate">{v.titulo}</p>
                      <span className={`text-[10px] px-2 py-0.5 rounded-full font-medium shrink-0 ${v.estado === 'activa' ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}`}>
                        {v.estado}
                      </span>
                    </div>
                    <div className="flex flex-wrap items-center gap-2 mt-0.5">
                      <span className="text-xs text-gray-500">{v.empresa}</span>
                      <span className="text-gray-200">·</span>
                      <span className="text-xs text-gray-400">{v.modalidad}</span>
                      <span className="text-gray-200">·</span>
                      <span className="text-xs text-gray-400 font-mono">{v.isco}</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-4 shrink-0">
                    <div className="text-center hidden sm:block">
                      <p className="text-sm font-bold text-gray-800">{v.vacantes}</p>
                      <p className="text-[10px] text-gray-400">vacantes</p>
                    </div>
                    <div className="text-center hidden sm:block">
                      <p className="text-sm font-bold text-teal-600">{v.candidatos}</p>
                      <p className="text-[10px] text-gray-400">derivados</p>
                    </div>
                    <div className="text-center">
                      <p className={`text-sm font-bold ${v.match_promedio >= 80 ? 'text-green-600' : 'text-blue-600'}`}>{v.match_promedio}%</p>
                      <p className="text-[10px] text-gray-400">match prom.</p>
                    </div>
                    <ChevronRight className="w-4 h-4 text-gray-300" />
                  </div>
                </Link>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
