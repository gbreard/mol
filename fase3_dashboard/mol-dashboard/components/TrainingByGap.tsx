import { ExternalLink } from 'lucide-react'

export interface Course {
  id: number
  name: string
  certificacion: string
  duracion: string
  modalidad: string
  covers_skills: string[]
  url?: string
}

export interface GapGroup {
  skill_label: string
  courses: Course[]
}

interface Props {
  byGap: GapGroup[]
}

export default function TrainingByGap({ byGap }: Props) {
  if (byGap.length === 0) {
    return (
      <p className="text-sm text-gray-400">No hay brechas detectadas. ¡Perfil completo!</p>
    )
  }

  return (
    <div className="space-y-6">
      {byGap.map((group) => (
        <div key={group.skill_label}>
          <div className="mb-2 flex items-center gap-2">
            <span className="rounded bg-red-100 px-2 py-0.5 text-xs font-medium text-red-700">
              Brecha
            </span>
            <h3 className="text-sm font-semibold text-gray-800">{group.skill_label}</h3>
          </div>

          <div className="space-y-2">
            {group.courses.map((course) => (
              <div
                key={course.id}
                className="rounded-lg border border-gray-200 bg-white p-4"
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0 flex-1">
                    <p className="font-medium text-gray-900">{course.name}</p>
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
                  {course.url && (
                    <a
                      href={course.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      aria-label={`Ver curso: ${course.name}`}
                      className="shrink-0 rounded-lg border border-gray-200 p-1.5 text-gray-500 hover:bg-gray-50"
                    >
                      <ExternalLink className="h-3.5 w-3.5" />
                    </a>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  )
}
