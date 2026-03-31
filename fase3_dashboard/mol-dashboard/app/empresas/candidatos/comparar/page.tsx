'use client'

import { useSearchParams } from 'next/navigation'
import { Suspense } from 'react'
import Link from 'next/link'
import { CheckCircle2, XCircle, Minus, ArrowLeft } from 'lucide-react'

// ─── Mock data ─────────────────────────────────────────────────────────────────
const MOCK_CANDIDATOS: Record<string, {
  nombre: string
  ocupacion: string
  ubicacion: string
  experiencia: string
  match: number
  disponibilidad: string
  skills: { nombre: string; nivel: 'alto' | 'medio' | 'bajo' }[]
  formacion: string[]
  idiomas: string[]
}> = {
  c1: {
    nombre: 'Lucía Fernández',
    ocupacion: 'Desarrolladora Frontend',
    ubicacion: 'Buenos Aires',
    experiencia: '5 años',
    match: 96,
    disponibilidad: 'Inmediata',
    skills: [
      { nombre: 'React', nivel: 'alto' },
      { nombre: 'TypeScript', nivel: 'alto' },
      { nombre: 'Next.js', nivel: 'alto' },
      { nombre: 'REST APIs', nivel: 'alto' },
      { nombre: 'Testing', nivel: 'medio' },
      { nombre: 'Docker', nivel: 'bajo' },
    ],
    formacion: ['Lic. Sistemas (UBA)', 'React Avanzado (Udemy)'],
    idiomas: ['Español (nativo)', 'Inglés (B2)'],
  },
  c2: {
    nombre: 'Martín Soria',
    ocupacion: 'Analista de Datos',
    ubicacion: 'Córdoba',
    experiencia: '3 años',
    match: 88,
    disponibilidad: 'En 7 días',
    skills: [
      { nombre: 'React', nivel: 'medio' },
      { nombre: 'TypeScript', nivel: 'medio' },
      { nombre: 'Next.js', nivel: 'bajo' },
      { nombre: 'REST APIs', nivel: 'alto' },
      { nombre: 'Testing', nivel: 'alto' },
      { nombre: 'Docker', nivel: 'medio' },
    ],
    formacion: ['Ing. Informática (UTN)', 'JavaScript Full Stack (Coderhouse)'],
    idiomas: ['Español (nativo)', 'Inglés (B1)'],
  },
  c3: {
    nombre: 'Valentina Cruz',
    ocupacion: 'Desarrolladora React',
    ubicacion: 'Buenos Aires',
    experiencia: '4 años',
    match: 85,
    disponibilidad: 'En 14 días',
    skills: [
      { nombre: 'React', nivel: 'alto' },
      { nombre: 'TypeScript', nivel: 'medio' },
      { nombre: 'Next.js', nivel: 'medio' },
      { nombre: 'REST APIs', nivel: 'medio' },
      { nombre: 'Testing', nivel: 'bajo' },
      { nombre: 'Docker', nivel: 'bajo' },
    ],
    formacion: ['Analista Programador (UADE)'],
    idiomas: ['Español (nativo)', 'Inglés (C1)'],
  },
}

const NIVEL_COLOR = {
  alto: 'bg-green-500',
  medio: 'bg-blue-400',
  bajo: 'bg-gray-300',
}

const NIVEL_LABEL = {
  alto: 'Alto',
  medio: 'Medio',
  bajo: 'Básico',
}

function CompararContent() {
  const params = useSearchParams()
  const ids = (params.get('ids') ?? 'c1,c2').split(',').slice(0, 3)
  const candidatos = ids.map((id) => ({ id, ...MOCK_CANDIDATOS[id] })).filter(Boolean)

  if (candidatos.length < 2) {
    return (
      <div className="text-center py-16 text-gray-400">
        <p className="text-sm">Seleccioná al menos 2 candidatos para comparar.</p>
        <Link href="/empresas/candidatos" className="text-indigo-600 text-sm mt-2 inline-block hover:underline">
          ← Volver a candidatos
        </Link>
      </div>
    )
  }

  // Collect all unique skills
  const allSkills = Array.from(
    new Set(candidatos.flatMap((c) => c.skills.map((s) => s.nombre)))
  )

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-5xl mx-auto px-4 py-8">

        {/* Header */}
        <div className="mb-6">
          <Link
            href="/empresas/candidatos"
            className="inline-flex items-center gap-1.5 text-xs text-gray-400 hover:text-gray-600 mb-3"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            Volver a candidatos
          </Link>
          <h1 className="text-xl font-bold text-gray-900">Comparar candidatos</h1>
          <p className="text-sm text-gray-500 mt-1">Análisis lado a lado de {candidatos.length} perfiles</p>
        </div>

        {/* Tabla comparativa */}
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">

          {/* Cabecera con nombres */}
          <div className="grid border-b border-gray-100" style={{ gridTemplateColumns: `200px repeat(${candidatos.length}, 1fr)` }}>
            <div className="px-4 py-3 bg-gray-50" />
            {candidatos.map((c) => (
              <div key={c.id} className="px-4 py-3 text-center border-l border-gray-100">
                <div className="w-10 h-10 rounded-full bg-indigo-100 text-indigo-700 text-sm font-bold flex items-center justify-center mx-auto mb-2">
                  {c.nombre.split(' ').map((n) => n[0]).join('').slice(0, 2)}
                </div>
                <p className="text-sm font-semibold text-gray-900">{c.nombre}</p>
                <p className="text-xs text-gray-400 mt-0.5">{c.ocupacion}</p>
                <span className={`inline-block mt-1 text-sm font-bold ${c.match >= 85 ? 'text-green-600' : 'text-blue-600'}`}>
                  {c.match}% match
                </span>
              </div>
            ))}
          </div>

          {/* Filas de datos básicos */}
          {[
            { label: 'Ubicación', key: 'ubicacion' as const },
            { label: 'Experiencia', key: 'experiencia' as const },
            { label: 'Disponibilidad', key: 'disponibilidad' as const },
          ].map((row) => (
            <div
              key={row.key}
              className="grid border-b border-gray-50"
              style={{ gridTemplateColumns: `200px repeat(${candidatos.length}, 1fr)` }}
            >
              <div className="px-4 py-3 bg-gray-50 flex items-center">
                <span className="text-xs font-medium text-gray-500">{row.label}</span>
              </div>
              {candidatos.map((c) => (
                <div key={c.id} className="px-4 py-3 text-center border-l border-gray-50">
                  <span className="text-sm text-gray-700">{c[row.key]}</span>
                </div>
              ))}
            </div>
          ))}

          {/* Sección skills */}
          <div className="grid border-b border-gray-100 bg-indigo-50" style={{ gridTemplateColumns: `200px repeat(${candidatos.length}, 1fr)` }}>
            <div className="px-4 py-2 flex items-center">
              <span className="text-xs font-bold text-indigo-700 uppercase tracking-wider">Competencias</span>
            </div>
            {candidatos.map((c) => (
              <div key={c.id} className="border-l border-indigo-100" />
            ))}
          </div>

          {allSkills.map((skillName, i) => (
            <div
              key={skillName}
              className={`grid border-b border-gray-50 ${i % 2 === 0 ? 'bg-white' : 'bg-gray-50/50'}`}
              style={{ gridTemplateColumns: `200px repeat(${candidatos.length}, 1fr)` }}
            >
              <div className="px-4 py-2.5 flex items-center">
                <span className="text-xs text-gray-600">{skillName}</span>
              </div>
              {candidatos.map((c) => {
                const skill = c.skills.find((s) => s.nombre === skillName)
                return (
                  <div key={c.id} className="px-4 py-2.5 border-l border-gray-50 flex items-center justify-center">
                    {skill ? (
                      <div className="flex items-center gap-1.5">
                        <div className={`w-2 h-2 rounded-full ${NIVEL_COLOR[skill.nivel]}`} />
                        <span className="text-xs text-gray-600">{NIVEL_LABEL[skill.nivel]}</span>
                      </div>
                    ) : (
                      <Minus className="w-3.5 h-3.5 text-gray-300" />
                    )}
                  </div>
                )
              })}
            </div>
          ))}

          {/* Formación */}
          <div className="grid border-b border-gray-100 bg-indigo-50" style={{ gridTemplateColumns: `200px repeat(${candidatos.length}, 1fr)` }}>
            <div className="px-4 py-2 flex items-center">
              <span className="text-xs font-bold text-indigo-700 uppercase tracking-wider">Formación</span>
            </div>
            {candidatos.map((c) => (
              <div key={c.id} className="border-l border-indigo-100" />
            ))}
          </div>
          <div
            className="grid border-b border-gray-50"
            style={{ gridTemplateColumns: `200px repeat(${candidatos.length}, 1fr)` }}
          >
            <div className="px-4 py-3 bg-gray-50 flex items-start">
              <span className="text-xs font-medium text-gray-500">Títulos y certificaciones</span>
            </div>
            {candidatos.map((c) => (
              <div key={c.id} className="px-4 py-3 border-l border-gray-50">
                <ul className="space-y-1">
                  {c.formacion.map((f) => (
                    <li key={f} className="flex items-start gap-1.5">
                      <CheckCircle2 className="w-3 h-3 text-green-400 shrink-0 mt-0.5" />
                      <span className="text-xs text-gray-600">{f}</span>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>

          {/* Idiomas */}
          <div
            className="grid border-b border-gray-50"
            style={{ gridTemplateColumns: `200px repeat(${candidatos.length}, 1fr)` }}
          >
            <div className="px-4 py-3 bg-gray-50 flex items-start">
              <span className="text-xs font-medium text-gray-500">Idiomas</span>
            </div>
            {candidatos.map((c) => (
              <div key={c.id} className="px-4 py-3 border-l border-gray-50">
                <ul className="space-y-1">
                  {c.idiomas.map((idioma) => (
                    <li key={idioma} className="text-xs text-gray-600">{idioma}</li>
                  ))}
                </ul>
              </div>
            ))}
          </div>

          {/* CTA */}
          <div className="grid bg-gray-50" style={{ gridTemplateColumns: `200px repeat(${candidatos.length}, 1fr)` }}>
            <div className="px-4 py-4" />
            {candidatos.map((c) => (
              <div key={c.id} className="px-4 py-4 border-l border-gray-100 flex flex-col gap-2">
                <button className="w-full text-xs font-semibold bg-indigo-600 text-white px-3 py-2 rounded-lg hover:bg-indigo-700 transition-colors">
                  Contactar
                </button>
                <button className="w-full text-xs font-medium border border-gray-200 text-gray-600 px-3 py-2 rounded-lg hover:bg-white transition-colors">
                  Ver perfil completo
                </button>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

export default function CompararPage() {
  return (
    <Suspense fallback={<div className="p-8 text-center text-gray-400 text-sm">Cargando comparación...</div>}>
      <CompararContent />
    </Suspense>
  )
}
