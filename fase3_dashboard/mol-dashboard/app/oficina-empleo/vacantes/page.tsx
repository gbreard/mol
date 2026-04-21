'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { Search, Plus, ChevronRight, Loader2, Briefcase } from 'lucide-react'

interface Vacante {
  id: string
  titulo: string
  empresa: string
  modalidad: string
  vacantes: number
  candidatos: number
  estado: string
  isco: string
  match_promedio: number
  fecha: string
}

export default function VacantesOEPage() {
  const [vacantes, setVacantes] = useState<Vacante[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)
  const [busqueda, setBusqueda] = useState('')
  const [filtro, setFiltro] = useState<'todas' | 'activa' | 'cerrada'>('activa')

  useEffect(() => {
    setLoading(true)
    setError(false)
    fetch('/api/vacantes-oe')
      .then(r => r.ok ? r.json() : Promise.reject())
      .then(data => setVacantes(Array.isArray(data) ? data : []))
      .catch(() => setError(true))
      .finally(() => setLoading(false))
  }, [])

  const filtered = vacantes.filter((v) => {
    const matchB = !busqueda.trim() || v.titulo.toLowerCase().includes(busqueda.toLowerCase()) || v.empresa.toLowerCase().includes(busqueda.toLowerCase())
    const matchF = filtro === 'todas' || v.estado === filtro
    return matchB && matchF
  })

  const activas = vacantes.filter(v => v.estado === 'activa').length
  const totalCandidatos = vacantes.reduce((s, v) => s + (v.candidatos || 0), 0)

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto px-4 py-8">

        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-xl font-bold text-gray-900">Vacantes OE</h1>
            {!loading && !error && vacantes.length > 0 && (
              <p className="text-sm text-gray-500 mt-0.5">
                {activas} activas · {totalCandidatos} candidatos derivados
              </p>
            )}
          </div>
          <Link
            href="/oficina-empleo/vacantes/nueva"
            className="inline-flex items-center gap-2 bg-teal-600 text-white text-sm font-semibold px-4 py-2.5 rounded-xl hover:bg-teal-700 transition-colors"
          >
            <Plus className="w-4 h-4" />
            Nueva vacante
          </Link>
        </div>

        {/* Busqueda + filtro */}
        <div className="flex gap-2 mb-4">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              value={busqueda}
              onChange={(e) => setBusqueda(e.target.value)}
              placeholder="Buscar por titulo o empresa..."
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
          {loading ? (
            <div className="py-12 flex items-center justify-center gap-2 text-gray-400">
              <Loader2 className="w-4 h-4 animate-spin" />
              <span className="text-sm">Cargando vacantes...</span>
            </div>
          ) : error ? (
            <div className="py-12 text-center text-gray-400 text-sm">
              Error al cargar vacantes. Intentá de nuevo.
            </div>
          ) : vacantes.length === 0 ? (
            <div className="py-12 text-center">
              <Briefcase className="w-8 h-8 mx-auto mb-2 text-gray-300" />
              <p className="text-sm text-gray-400">No hay vacantes cargadas todavia.</p>
            </div>
          ) : filtered.length === 0 ? (
            <div className="py-12 text-center text-gray-400 text-sm">No hay vacantes con ese filtro.</div>
          ) : (
            <div className="divide-y divide-gray-50">
              {filtered.map((v) => (
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
