'use client'

import { useState, useRef, useCallback, useEffect } from 'react'
import Link from 'next/link'
import { Search, SlidersHorizontal, X, Users, ChevronRight, Loader2 } from 'lucide-react'

const MOCK_POOL = [
  {
    id: 'p1',
    nombre: 'Lucía Fernández',
    ocupacion: 'Desarrolladora Frontend',
    skills: ['React', 'TypeScript', 'Next.js', 'REST APIs'],
    ubicacion: 'Buenos Aires',
    match: 96,
    disponibilidad: 'Inmediata',
  },
  {
    id: 'p2',
    nombre: 'Martín Soria',
    ocupacion: 'Analista de Datos',
    skills: ['Python', 'SQL', 'Power BI', 'Machine Learning'],
    ubicacion: 'Córdoba',
    match: 88,
    disponibilidad: 'En 7 días',
  },
  {
    id: 'p3',
    nombre: 'Valentina Cruz',
    ocupacion: 'Desarrolladora React',
    skills: ['React', 'JavaScript', 'CSS', 'Testing'],
    ubicacion: 'Buenos Aires',
    match: 85,
    disponibilidad: 'En 14 días',
  },
  {
    id: 'p4',
    nombre: 'Diego Méndez',
    ocupacion: 'Ingeniero DevOps',
    skills: ['Docker', 'Kubernetes', 'AWS', 'CI/CD'],
    ubicacion: 'Rosario',
    match: 79,
    disponibilidad: 'En 30 días',
  },
  {
    id: 'p5',
    nombre: 'Sofía Ramos',
    ocupacion: 'QA Engineer',
    skills: ['Selenium', 'Jest', 'Python', 'Bug tracking'],
    ubicacion: 'Buenos Aires',
    match: 71,
    disponibilidad: 'Inmediata',
  },
  {
    id: 'p6',
    nombre: 'Alejandro Torres',
    ocupacion: 'Product Manager',
    skills: ['Agile', 'Scrum', 'Roadmap', 'KPIs'],
    ubicacion: 'Mendoza',
    match: 68,
    disponibilidad: 'Inmediata',
  },
  {
    id: 'p7',
    nombre: 'Carolina López',
    ocupacion: 'UX Designer',
    skills: ['Figma', 'User Research', 'Prototipado', 'CSS'],
    ubicacion: 'Buenos Aires',
    match: 64,
    disponibilidad: 'En 7 días',
  },
  {
    id: 'p8',
    nombre: 'Roberto García',
    ocupacion: 'Backend Developer',
    skills: ['Node.js', 'PostgreSQL', 'Docker', 'REST APIs'],
    ubicacion: 'La Plata',
    match: 77,
    disponibilidad: 'En 14 días',
  },
]

const PROVINCIAS = ['Todas', 'Buenos Aires', 'Córdoba', 'Rosario', 'Mendoza', 'La Plata']
const DISPONIBILIDAD_OPTS = ['Cualquiera', 'Inmediata', 'En 7 días', 'En 14 días', 'En 30 días']

export default function EmpresasPoolPage() {
  const [query, setQuery] = useState('')
  const [searching, setSearching] = useState(false)
  const [results, setResults] = useState(MOCK_POOL)
  const [showFiltros, setShowFiltros] = useState(false)
  const [provincia, setProvincia] = useState('Todas')
  const [disponibilidad, setDisponibilidad] = useState('Cualquiera')
  const [matchMin, setMatchMin] = useState(50)
  const [skillsFiltro, setSkillsFiltro] = useState<string[]>([])
  const [skillInput, setSkillInput] = useState('')
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  const runSearch = useCallback(() => {
    setSearching(true)
    setTimeout(() => {
      let filtered = MOCK_POOL
      if (query.trim()) {
        filtered = filtered.filter((p) =>
          p.nombre.toLowerCase().includes(query.toLowerCase()) ||
          p.ocupacion.toLowerCase().includes(query.toLowerCase()) ||
          p.skills.some((s) => s.toLowerCase().includes(query.toLowerCase()))
        )
      }
      if (provincia !== 'Todas') filtered = filtered.filter((p) => p.ubicacion === provincia)
      if (disponibilidad !== 'Cualquiera') filtered = filtered.filter((p) => p.disponibilidad === disponibilidad)
      filtered = filtered.filter((p) => p.match >= matchMin)
      if (skillsFiltro.length > 0) {
        filtered = filtered.filter((p) =>
          skillsFiltro.every((sf) => p.skills.some((s) => s.toLowerCase().includes(sf.toLowerCase())))
        )
      }
      setResults(filtered)
      setSearching(false)
    }, 300)
  }, [query, provincia, disponibilidad, matchMin, skillsFiltro])

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current)
    debounceRef.current = setTimeout(runSearch, 200)
    return () => { if (debounceRef.current) clearTimeout(debounceRef.current) }
  }, [runSearch])

  const addSkillFiltro = () => {
    const s = skillInput.trim()
    if (s && !skillsFiltro.includes(s)) setSkillsFiltro([...skillsFiltro, s])
    setSkillInput('')
  }

  const activeFilters = [
    provincia !== 'Todas' ? `📍 ${provincia}` : null,
    disponibilidad !== 'Cualquiera' ? `⏱ ${disponibilidad}` : null,
    matchMin > 50 ? `≥${matchMin}% match` : null,
    ...skillsFiltro.map((s) => `skill: ${s}`),
  ].filter(Boolean) as string[]

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto px-4 py-8">

        {/* Header */}
        <div className="mb-6">
          <div className="flex items-center gap-2 mb-1">
            <Users className="w-5 h-5 text-indigo-500" />
            <h1 className="text-xl font-bold text-gray-900">Buscar en el pool</h1>
          </div>
          <p className="text-sm text-gray-500">
            Explorá perfiles verificados por competencias ESCO.
          </p>
        </div>

        {/* Search + filtros toggle */}
        <div className="flex gap-2 mb-3">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            {searching && <Loader2 className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 animate-spin" />}
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Buscar por nombre, ocupación o skill..."
              className="w-full rounded-xl border border-gray-200 bg-white pl-9 pr-3 py-2.5 text-sm text-gray-900 placeholder-gray-400 focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-100"
              autoFocus
            />
          </div>
          <button
            onClick={() => setShowFiltros(!showFiltros)}
            className={`inline-flex items-center gap-2 border text-sm font-medium px-4 py-2.5 rounded-xl transition-colors ${
              activeFilters.length > 0 || showFiltros
                ? 'border-indigo-400 bg-indigo-50 text-indigo-700'
                : 'border-gray-200 bg-white text-gray-600 hover:border-gray-300'
            }`}
          >
            <SlidersHorizontal className="w-4 h-4" />
            Filtros
            {activeFilters.length > 0 && (
              <span className="bg-indigo-600 text-white text-[10px] font-bold w-4 h-4 rounded-full flex items-center justify-center">
                {activeFilters.length}
              </span>
            )}
          </button>
        </div>

        {/* Panel de filtros */}
        {showFiltros && (
          <div className="bg-white rounded-xl border border-gray-200 p-4 mb-4 space-y-4">
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Provincia</label>
                <select
                  value={provincia}
                  onChange={(e) => setProvincia(e.target.value)}
                  className="w-full rounded-lg border border-gray-200 px-2.5 py-2 text-xs text-gray-900 focus:border-indigo-400 focus:outline-none"
                >
                  {PROVINCIAS.map((p) => <option key={p}>{p}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Disponibilidad</label>
                <select
                  value={disponibilidad}
                  onChange={(e) => setDisponibilidad(e.target.value)}
                  className="w-full rounded-lg border border-gray-200 px-2.5 py-2 text-xs text-gray-900 focus:border-indigo-400 focus:outline-none"
                >
                  {DISPONIBILIDAD_OPTS.map((d) => <option key={d}>{d}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">
                  Match mínimo: <span className="text-indigo-600 font-bold">{matchMin}%</span>
                </label>
                <input
                  type="range"
                  min={0}
                  max={90}
                  step={10}
                  value={matchMin}
                  onChange={(e) => setMatchMin(Number(e.target.value))}
                  className="w-full accent-indigo-600"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Filtrar por skills específicas</label>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={skillInput}
                  onChange={(e) => setSkillInput(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && addSkillFiltro()}
                  placeholder="Ej: React, SQL..."
                  className="flex-1 rounded-lg border border-gray-200 px-2.5 py-1.5 text-xs focus:border-indigo-400 focus:outline-none"
                />
                <button
                  onClick={addSkillFiltro}
                  className="text-xs font-medium bg-indigo-50 text-indigo-700 px-3 py-1.5 rounded-lg hover:bg-indigo-100 transition-colors"
                >
                  Agregar
                </button>
              </div>
              {skillsFiltro.length > 0 && (
                <div className="flex flex-wrap gap-1.5 mt-2">
                  {skillsFiltro.map((s) => (
                    <span key={s} className="flex items-center gap-1 text-xs bg-indigo-100 text-indigo-700 px-2 py-0.5 rounded-full">
                      {s}
                      <button onClick={() => setSkillsFiltro(skillsFiltro.filter((sk) => sk !== s))}>
                        <X className="w-3 h-3" />
                      </button>
                    </span>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Active filters chips */}
        {activeFilters.length > 0 && !showFiltros && (
          <div className="flex flex-wrap gap-1.5 mb-3">
            {activeFilters.map((f) => (
              <span key={f} className="text-xs bg-indigo-50 text-indigo-700 border border-indigo-100 px-2.5 py-1 rounded-full">
                {f}
              </span>
            ))}
          </div>
        )}

        {/* Results */}
        <div className="flex items-center justify-between mb-2">
          <p className="text-xs text-gray-500">
            {results.length} perfil{results.length !== 1 ? 'es' : ''} encontrado{results.length !== 1 ? 's' : ''}
          </p>
          <p className="text-xs text-gray-400">Ordenados por match %</p>
        </div>

        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          {results.length === 0 ? (
            <div className="py-12 text-center text-gray-400 text-sm">
              No se encontraron perfiles con esos filtros.
            </div>
          ) : (
            <div className="divide-y divide-gray-50">
              {results
                .sort((a, b) => b.match - a.match)
                .map((p) => (
                  <Link
                    key={p.id}
                    href={`/empresas/candidatos/${p.id}`}
                    className="flex items-center gap-3 px-4 py-3.5 hover:bg-gray-50 transition-colors"
                  >
                    {/* Avatar */}
                    <div className="w-9 h-9 rounded-full bg-indigo-100 text-indigo-700 text-xs font-bold flex items-center justify-center shrink-0">
                      {p.nombre.split(' ').map((n) => n[0]).join('').slice(0, 2)}
                    </div>

                    {/* Info */}
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-semibold text-gray-900">{p.nombre}</p>
                      <p className="text-xs text-gray-500">
                        {p.ocupacion} · {p.ubicacion} · {p.disponibilidad}
                      </p>
                      <div className="flex flex-wrap gap-1 mt-1">
                        {p.skills.slice(0, 3).map((s) => (
                          <span
                            key={s}
                            className={`text-[10px] px-1.5 py-0.5 rounded ${
                              skillsFiltro.some((sf) => s.toLowerCase().includes(sf.toLowerCase()))
                                ? 'bg-indigo-200 text-indigo-800 font-semibold'
                                : 'bg-indigo-50 text-indigo-600'
                            }`}
                          >
                            {s}
                          </span>
                        ))}
                        {p.skills.length > 3 && (
                          <span className="text-[10px] text-gray-400">+{p.skills.length - 3}</span>
                        )}
                      </div>
                    </div>

                    {/* Match */}
                    <div className="flex items-center gap-2 shrink-0">
                      <span className={`text-sm font-bold tabular-nums ${
                        p.match >= 85 ? 'text-green-600' : p.match >= 70 ? 'text-blue-600' : 'text-yellow-600'
                      }`}>
                        {p.match}%
                      </span>
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
