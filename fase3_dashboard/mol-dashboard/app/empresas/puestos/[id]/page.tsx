'use client'

import { useParams, useRouter } from 'next/navigation'
import Link from 'next/link'
import { ArrowLeft, Users, ChevronRight, Mail, CheckCircle2, Clock } from 'lucide-react'

const MOCK_PUESTOS: Record<string, {
  id: string
  titulo: string
  isco: string
  descripcion: string
  estado: string
  dias: number
  modalidad: string
  seniority: string
  skills: { nombre: string; esencial: boolean }[]
  candidatos: {
    id: string
    nombre: string
    match: number
    ocupacion: string
    ubicacion: string
    disponibilidad: string
    estado: 'nuevo' | 'revisado' | 'contactado' | 'descartado'
  }[]
}> = {
  p1: {
    id: 'p1',
    titulo: 'Desarrollador React',
    isco: '2512',
    descripcion: 'Desarrollo frontend con React 18, TypeScript y Next.js para nuestra plataforma principal.',
    estado: 'activo',
    dias: 5,
    modalidad: 'Híbrido',
    seniority: 'Semi-senior',
    skills: [
      { nombre: 'React', esencial: true },
      { nombre: 'TypeScript', esencial: true },
      { nombre: 'Next.js', esencial: true },
      { nombre: 'REST APIs', esencial: true },
      { nombre: 'Git', esencial: false },
      { nombre: 'Testing', esencial: false },
    ],
    candidatos: [
      { id: 'c1', nombre: 'Lucía Fernández', match: 96, ocupacion: 'Desarrolladora Frontend', ubicacion: 'Buenos Aires', disponibilidad: 'Inmediata', estado: 'nuevo' },
      { id: 'c3', nombre: 'Valentina Cruz', match: 85, ocupacion: 'Desarrolladora React', ubicacion: 'Buenos Aires', disponibilidad: 'En 14 días', estado: 'nuevo' },
      { id: 'c8', nombre: 'Jorge Ibáñez', match: 79, ocupacion: 'Frontend Developer', ubicacion: 'Rosario', disponibilidad: 'En 7 días', estado: 'revisado' },
      { id: 'c9', nombre: 'Marina Suárez', match: 74, ocupacion: 'Desarrollador Web', ubicacion: 'Buenos Aires', disponibilidad: 'Inmediata', estado: 'contactado' },
      { id: 'c10', nombre: 'Pablo Ríos', match: 68, ocupacion: 'JavaScript Developer', ubicacion: 'Córdoba', disponibilidad: 'En 30 días', estado: 'nuevo' },
    ],
  },
  p2: {
    id: 'p2',
    titulo: 'Analista de Datos Senior',
    isco: '2521',
    descripcion: 'Análisis y visualización de datos del negocio con Python, SQL y Power BI.',
    estado: 'activo',
    dias: 12,
    modalidad: 'Remoto',
    seniority: 'Senior',
    skills: [
      { nombre: 'Python', esencial: true },
      { nombre: 'SQL', esencial: true },
      { nombre: 'Power BI', esencial: true },
      { nombre: 'Machine Learning', esencial: false },
      { nombre: 'Pandas', esencial: false },
    ],
    candidatos: [
      { id: 'c2', nombre: 'Martín Soria', match: 88, ocupacion: 'Analista de Datos', ubicacion: 'Córdoba', disponibilidad: 'En 7 días', estado: 'revisado' },
      { id: 'c11', nombre: 'Clara Medina', match: 76, ocupacion: 'Data Analyst', ubicacion: 'Buenos Aires', disponibilidad: 'Inmediata', estado: 'nuevo' },
    ],
  },
}

const ESTADO_CONFIG: Record<string, { label: string; color: string }> = {
  nuevo: { label: 'Nuevo', color: 'bg-blue-100 text-blue-700' },
  revisado: { label: 'Revisado', color: 'bg-gray-100 text-gray-600' },
  contactado: { label: 'Contactado', color: 'bg-green-100 text-green-700' },
  descartado: { label: 'Descartado', color: 'bg-red-100 text-red-500' },
}

export default function PuestoDetallePage() {
  const params = useParams()
  const router = useRouter()
  const puesto = MOCK_PUESTOS[params.id as string]

  if (!puesto) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <p className="text-gray-500 text-sm mb-4">Puesto no encontrado.</p>
          <Link href="/empresas/puestos" className="text-indigo-600 text-sm hover:underline">
            ← Volver a puestos
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto px-4 py-8">

        {/* Breadcrumb */}
        <button
          onClick={() => router.push('/empresas/puestos')}
          className="inline-flex items-center gap-1.5 text-xs text-gray-400 hover:text-gray-600 mb-4"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          Mis puestos
        </button>

        {/* Header */}
        <div className="bg-white rounded-xl border border-gray-200 p-5 mb-5">
          <div className="flex items-start justify-between gap-3">
            <div>
              <div className="flex items-center gap-2 flex-wrap mb-1">
                <h1 className="text-lg font-bold text-gray-900">{puesto.titulo}</h1>
                <span className="text-[10px] font-mono text-gray-400 bg-gray-100 px-1.5 py-0.5 rounded">
                  ISCO {puesto.isco}
                </span>
                <span className="text-[10px] bg-green-100 text-green-700 px-2 py-0.5 rounded-full font-medium">
                  {puesto.estado}
                </span>
              </div>
              <p className="text-sm text-gray-500">{puesto.descripcion}</p>
              <div className="flex flex-wrap gap-3 mt-3 text-xs text-gray-500">
                <span>📍 {puesto.modalidad}</span>
                <span>🎯 {puesto.seniority}</span>
                <span>📅 Publicado hace {puesto.dias}d</span>
                <span><Users className="w-3.5 h-3.5 inline mr-0.5" />{puesto.candidatos.length} candidatos</span>
              </div>
            </div>
          </div>

          {/* Skills del puesto */}
          <div className="mt-4 pt-4 border-t border-gray-100">
            <p className="text-xs font-medium text-gray-500 mb-2">Competencias requeridas</p>
            <div className="flex flex-wrap gap-1.5">
              {puesto.skills.map((s) => (
                <span
                  key={s.nombre}
                  className={`text-xs px-2.5 py-0.5 rounded-full font-medium ${
                    s.esencial
                      ? 'bg-indigo-100 text-indigo-700 border border-indigo-200'
                      : 'bg-gray-100 text-gray-600'
                  }`}
                >
                  {s.nombre}
                  {s.esencial && <span className="ml-1 text-[9px] opacity-70">esencial</span>}
                </span>
              ))}
            </div>
          </div>
        </div>

        {/* Ranking de candidatos */}
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <div className="flex items-center justify-between px-4 py-3 border-b border-gray-100">
            <div>
              <h2 className="text-sm font-semibold text-gray-800">
                Candidatos · ranking por match
              </h2>
              <p className="text-xs text-gray-400 mt-0.5">
                {puesto.candidatos.filter(c => c.estado === 'nuevo').length} nuevos sin revisar
              </p>
            </div>
            {puesto.candidatos.length >= 2 && (
              <Link
                href={`/empresas/candidatos/comparar?ids=${puesto.candidatos.slice(0, 3).map(c => c.id).join(',')}`}
                className="text-xs font-medium text-indigo-600 hover:underline"
              >
                Comparar top 3
              </Link>
            )}
          </div>

          <div className="divide-y divide-gray-50">
            {puesto.candidatos
              .sort((a, b) => b.match - a.match)
              .map((c, i) => {
                const est = ESTADO_CONFIG[c.estado]
                return (
                  <Link
                    key={c.id}
                    href={`/empresas/candidatos/${c.id}`}
                    className="flex items-center gap-3 px-4 py-3.5 hover:bg-gray-50 transition-colors"
                  >
                    {/* Rank */}
                    <span className={`w-6 text-center text-xs font-bold tabular-nums ${
                      i === 0 ? 'text-yellow-500' : i === 1 ? 'text-gray-400' : 'text-gray-300'
                    }`}>
                      #{i + 1}
                    </span>

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
                      <p className="text-xs text-gray-400">
                        {c.ocupacion} · {c.ubicacion} · {c.disponibilidad}
                      </p>
                    </div>

                    {/* Match + acciones */}
                    <div className="flex items-center gap-3 shrink-0">
                      <div className="text-right">
                        <span className={`text-base font-bold tabular-nums ${
                          c.match >= 85 ? 'text-green-600' : c.match >= 70 ? 'text-blue-600' : 'text-yellow-600'
                        }`}>
                          {c.match}%
                        </span>
                      </div>
                      <button
                        onClick={(e) => { e.preventDefault(); e.stopPropagation() }}
                        className="p-1.5 rounded-lg hover:bg-gray-100 text-gray-400 hover:text-gray-600 transition-colors"
                      >
                        <Mail className="w-3.5 h-3.5" />
                      </button>
                      <ChevronRight className="w-4 h-4 text-gray-300" />
                    </div>
                  </Link>
                )
              })}
          </div>
        </div>

        {/* Match bar legend */}
        <div className="mt-3 flex items-center gap-4 text-xs text-gray-400 justify-end">
          <span className="flex items-center gap-1"><CheckCircle2 className="w-3 h-3 text-green-500" />≥85% excelente</span>
          <span className="flex items-center gap-1"><Clock className="w-3 h-3 text-blue-400" />70-84% bueno</span>
        </div>
      </div>
    </div>
  )
}
