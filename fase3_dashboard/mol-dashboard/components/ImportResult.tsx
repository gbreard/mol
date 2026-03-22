'use client'

import { CheckCircle, Users, Briefcase, GraduationCap } from 'lucide-react'

export interface ImportStats {
  total_importados: number
  con_skills_derivadas: number
  con_skills_declaradas: number
  sin_skills: number
}

interface Props {
  stats: ImportStats
  onIrPanel?: () => void
  onImportarVacantes?: () => void
  onImportarCursos?: () => void
}

export default function ImportResult({ stats, onIrPanel, onImportarVacantes, onImportarCursos }: Props) {
  return (
    <div className="mx-auto max-w-lg space-y-6 px-4 py-8 text-center">
      <div className="flex flex-col items-center gap-3">
        <CheckCircle className="h-14 w-14 text-green-500" />
        <h1 className="text-2xl font-bold text-gray-900">¡Importación completada!</h1>
      </div>

      {/* Stats */}
      <div className="rounded-xl border border-gray-200 bg-white p-6 text-left">
        <ul className="space-y-2 text-sm text-gray-700">
          <li className="flex justify-between">
            <span>Personas importadas</span>
            <strong className="text-gray-900">{stats.total_importados}</strong>
          </li>
          <li className="flex justify-between">
            <span>Con skills derivadas automáticamente</span>
            <strong className="text-green-700">{stats.con_skills_derivadas}</strong>
          </li>
          <li className="flex justify-between">
            <span>Con skills declaradas</span>
            <strong className="text-blue-700">{stats.con_skills_declaradas}</strong>
          </li>
          <li className="flex justify-between">
            <span className="text-gray-500">Sin skills (completar en atención)</span>
            <strong className="text-gray-400">{stats.sin_skills}</strong>
          </li>
        </ul>
      </div>

      {/* Siguientes pasos */}
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
        <button
          onClick={onIrPanel}
          aria-label="Ir al panel de casos"
          className="flex min-h-[44px] flex-col items-center gap-1.5 rounded-xl border border-gray-200 px-4 py-3 text-sm hover:bg-gray-50"
        >
          <Users className="h-5 w-5 text-blue-600" />
          <span className="font-medium text-gray-800">Panel de casos</span>
          <span className="text-xs text-gray-400">Ver personas importadas</span>
        </button>

        <button
          onClick={onImportarVacantes}
          aria-label="Importar vacantes"
          className="flex min-h-[44px] flex-col items-center gap-1.5 rounded-xl border border-gray-200 px-4 py-3 text-sm hover:bg-gray-50"
        >
          <Briefcase className="h-5 w-5 text-teal-600" />
          <span className="font-medium text-gray-800">Importar vacantes</span>
          <span className="text-xs text-gray-400">Subir Excel de empresas</span>
        </button>

        <button
          onClick={onImportarCursos}
          aria-label="Importar cursos"
          className="flex min-h-[44px] flex-col items-center gap-1.5 rounded-xl border border-gray-200 px-4 py-3 text-sm hover:bg-gray-50"
        >
          <GraduationCap className="h-5 w-5 text-violet-600" />
          <span className="font-medium text-gray-800">Importar cursos</span>
          <span className="text-xs text-gray-400">Subir oferta formativa</span>
        </button>
      </div>
    </div>
  )
}
