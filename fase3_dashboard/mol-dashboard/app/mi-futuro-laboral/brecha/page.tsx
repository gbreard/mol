'use client'

import { Suspense } from 'react'
import { useSearchParams, useRouter } from 'next/navigation'
import { ArrowLeft, TrendingUp, BookOpen, ArrowRight } from 'lucide-react'

const MOCK_GAPS = [
  {
    skill: 'Docker', demanda: 68, cursos: [
      { nombre: 'Administración de contenedores con Docker', institucion: 'CGPC CABA', duracion: '3 semanas', modalidad: 'Presencial', gratuito: true, impacto: '+9%' },
    ],
  },
  {
    skill: 'Python', demanda: 81, cursos: [
      { nombre: 'Python para análisis de datos', institucion: 'Argentina Programa', duracion: '8 semanas', modalidad: 'Online', gratuito: true, impacto: '+12%' },
      { nombre: 'Python desde cero', institucion: 'Coderhouse', duracion: '5 semanas', modalidad: 'Online', gratuito: false, impacto: '+10%' },
    ],
  },
  {
    skill: 'Kubernetes', demanda: 42, cursos: [],
  },
]

function BrechaContent() {
  const router = useRouter()
  const params = useSearchParams()
  const label = params.get('label') ?? 'la ocupación seleccionada'
  const matchActual = 73
  const matchConTodo = 94

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-2xl mx-auto px-4 py-8">

        {/* Back */}
        <button
          onClick={() => router.back()}
          className="flex items-center gap-1.5 text-sm text-gray-500 hover:text-gray-700 mb-6 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" /> Volver a resultados
        </button>

        {/* Header */}
        <div className="mb-6">
          <h1 className="text-xl font-bold text-gray-900 mb-1">
            Brecha hacia <span className="text-blue-600">{label}</span>
          </h1>
          <p className="text-gray-500 text-sm">
            Te faltan {MOCK_GAPS.length} competencias concretas. Si las cerrás todas, tu match sube de{' '}
            <span className="font-bold text-gray-800">{matchActual}%</span> a{' '}
            <span className="font-bold text-green-600">{matchConTodo}%</span>.
          </p>
        </div>

        {/* Barra de progreso */}
        <div className="bg-white rounded-xl border border-gray-200 p-4 mb-6">
          <div className="flex items-center justify-between text-xs mb-2">
            <span className="text-gray-500">Match actual</span>
            <span className="text-gray-500">Con todas las skills</span>
          </div>
          <div className="relative h-3 bg-gray-100 rounded-full overflow-hidden">
            <div className="absolute h-full bg-blue-500 rounded-full" style={{ width: `${matchActual}%` }} />
            <div className="absolute h-full bg-green-200 rounded-full" style={{ width: `${matchConTodo}%` }} />
          </div>
          <div className="flex items-center justify-between text-sm font-bold mt-1">
            <span className="text-blue-600">{matchActual}%</span>
            <span className="text-green-600">{matchConTodo}%</span>
          </div>
        </div>

        {/* Gaps con cursos */}
        <div className="space-y-4">
          {MOCK_GAPS.map((gap) => (
            <div key={gap.skill} className="bg-white rounded-xl border border-gray-200 overflow-hidden">
              {/* Header del gap */}
              <div className="flex items-center justify-between px-4 py-3 border-b border-gray-100">
                <div className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-red-400 shrink-0" />
                  <span className="font-semibold text-gray-900 text-sm">{gap.skill}</span>
                </div>
                <span className="text-xs text-gray-500 flex items-center gap-1">
                  <TrendingUp className="w-3 h-3 text-orange-400" />
                  {gap.demanda}% de las ofertas la requieren
                </span>
              </div>

              {/* Cursos */}
              {gap.cursos.length > 0 ? (
                <div className="divide-y divide-gray-50">
                  {gap.cursos.map((c, i) => (
                    <div key={i} className="px-4 py-3">
                      <div className="flex items-start justify-between gap-3">
                        <div>
                          <div className="flex items-center gap-1.5 mb-1">
                            <BookOpen className="w-3.5 h-3.5 text-blue-500 shrink-0" />
                            <span className="text-sm font-medium text-gray-800">{c.nombre}</span>
                          </div>
                          <div className="flex flex-wrap items-center gap-2">
                            <span className="text-xs text-gray-500">{c.institucion}</span>
                            <span className="text-xs text-gray-400">·</span>
                            <span className="text-xs text-gray-500">{c.duracion}</span>
                            <span className="text-xs text-gray-400">·</span>
                            <span className="text-xs text-gray-500">{c.modalidad}</span>
                            {c.gratuito && (
                              <span className="text-[10px] bg-green-50 text-green-700 px-1.5 py-0.5 rounded font-medium">Gratuito</span>
                            )}
                          </div>
                        </div>
                        <span className="text-xs font-bold text-green-600 shrink-0 bg-green-50 px-2 py-1 rounded-lg">
                          {c.impacto}
                        </span>
                      </div>
                      <button className="mt-2 w-full text-xs text-blue-600 font-medium bg-blue-50 hover:bg-blue-100 rounded-lg py-1.5 transition-colors">
                        Cómo inscribirme →
                      </button>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="px-4 py-3">
                  <p className="text-xs text-gray-400 italic">
                    Sin cursos disponibles en tu zona. Podés buscar en el catálogo nacional.
                  </p>
                  <button className="mt-2 text-xs text-blue-600 hover:underline">
                    Buscar en otra región →
                  </button>
                </div>
              )}
            </div>
          ))}
        </div>

        {/* CTA reporte */}
        <div className="mt-8 flex flex-col sm:flex-row gap-3">
          <button
            onClick={() => router.push('/mi-futuro-laboral/reporte')}
            className="flex-1 inline-flex items-center justify-center gap-2 bg-blue-600 text-white text-sm font-semibold px-4 py-3 rounded-xl hover:bg-blue-700 transition-colors"
          >
            Generar reporte PDF + QR
            <ArrowRight className="w-4 h-4" />
          </button>
          <button
            onClick={() => router.push('/mi-futuro-laboral/resultados')}
            className="flex-1 inline-flex items-center justify-center gap-2 bg-white text-gray-700 text-sm font-medium px-4 py-3 rounded-xl border border-gray-200 hover:bg-gray-50 transition-colors"
          >
            Ver otros destinos
          </button>
        </div>
      </div>
    </div>
  )
}

export default function BrechaPage() {
  return (
    <Suspense>
      <BrechaContent />
    </Suspense>
  )
}
