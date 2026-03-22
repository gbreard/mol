'use client'

import { useState } from 'react'
import { ExternalLink, TrendingUp, ArrowRight } from 'lucide-react'
import type { Course } from './TrainingByGap'

export interface ImpactCourse extends Course {
  delta_match: number  // puntos porcentuales que sube el match
}

export interface ImpactGapGroup {
  skill_label: string
  courses: ImpactCourse[]
}

export interface TrainingImpactData {
  profile_id: string
  current_match: number
  max_potential_match: number
  gap_groups: ImpactGapGroup[]
}

interface Props {
  data: TrainingImpactData
  onDerivar?: (courseId: number, courseName: string) => void
}

export default function TrainingImpact({ data, onDerivar }: Props) {
  const [derivados, setDerivados] = useState<Set<number>>(new Set())

  const handleDerivar = (course: ImpactCourse) => {
    setDerivados((prev) => new Set(prev).add(course.id))
    onDerivar?.(course.id, course.name)
  }

  const gain = data.max_potential_match - data.current_match

  return (
    <div className="space-y-6">
      {/* Caja impacto */}
      <div className="rounded-xl border border-blue-200 bg-blue-50 p-4">
        <div className="flex items-center gap-2 mb-3">
          <TrendingUp className="h-4 w-4 text-blue-600" />
          <p className="text-sm font-semibold text-blue-900">Impacto potencial de la formación</p>
        </div>
        <div className="flex items-center gap-3">
          <div className="text-center">
            <p className="text-2xl font-bold text-gray-700">{data.current_match}%</p>
            <p className="text-xs text-gray-500">compatibilidad actual</p>
          </div>
          <ArrowRight className="h-5 w-5 text-blue-400 shrink-0" />
          <div className="text-center">
            <p className="text-2xl font-bold text-blue-700">{data.max_potential_match}%</p>
            <p className="text-xs text-gray-500">con toda la formación</p>
          </div>
          {gain > 0 && (
            <span className="ml-auto rounded-full bg-blue-100 px-3 py-1 text-sm font-bold text-blue-700">
              +{gain}% mejora
            </span>
          )}
        </div>
      </div>

      {/* Grupos por brecha */}
      {data.gap_groups.length === 0 ? (
        <p className="text-sm text-gray-400">No hay brechas con cursos disponibles.</p>
      ) : (
        data.gap_groups.map((group) => (
          <div key={group.skill_label}>
            <div className="mb-2 flex items-center gap-2">
              <span className="rounded bg-red-100 px-2 py-0.5 text-xs font-medium text-red-700">
                Brecha
              </span>
              <h3 className="text-sm font-semibold text-gray-800">{group.skill_label}</h3>
            </div>

            <div className="space-y-2">
              {group.courses.map((course) => {
                const yaDerivado = derivados.has(course.id)
                return (
                  <div
                    key={course.id}
                    className="rounded-lg border border-gray-200 bg-white p-4"
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div className="min-w-0 flex-1">
                        <div className="flex flex-wrap items-center gap-2">
                          <p className="font-medium text-gray-900">{course.name}</p>
                          <span
                            aria-label={`Impacto: +${course.delta_match}% compatibilidad`}
                            className="rounded-full bg-green-100 px-2 py-0.5 text-xs font-bold text-green-700"
                          >
                            +{course.delta_match}%
                          </span>
                        </div>
                        <div className="mt-1 flex flex-wrap gap-2 text-xs text-gray-500">
                          {course.certificacion && (
                            <span className="rounded bg-blue-50 px-1.5 py-0.5 text-blue-700">
                              {course.certificacion}
                            </span>
                          )}
                          <span>{course.duracion}</span>
                          <span>{course.modalidad}</span>
                        </div>
                        {course.covers_skills.length > 0 && (
                          <p className="mt-1.5 text-xs text-green-700">
                            Cubre: {course.covers_skills.join(', ')}
                          </p>
                        )}
                      </div>

                      <div className="flex shrink-0 flex-col items-end gap-2">
                        {course.url && (
                          <a
                            href={course.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            aria-label={`Ver curso: ${course.name}`}
                            className="rounded-lg border border-gray-200 p-1.5 text-gray-500 hover:bg-gray-50"
                          >
                            <ExternalLink className="h-3.5 w-3.5" />
                          </a>
                        )}
                        <button
                          onClick={() => handleDerivar(course)}
                          disabled={yaDerivado}
                          aria-label={`Derivar a ${course.name}`}
                          className="min-h-[44px] rounded-lg bg-blue-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-blue-700 disabled:bg-green-600"
                        >
                          {yaDerivado ? '✓ Derivado' : 'Derivar'}
                        </button>
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        ))
      )}
    </div>
  )
}
