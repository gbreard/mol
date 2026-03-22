'use client'

import { useState } from 'react'
import SkillsMapEditable, { type ReportSkillItem } from './SkillsMapEditable'
import AffinityMatrix from './AffinityMatrix'

export interface ReportData {
  candidato_nombre: string
  ocupacion_label: string
  ocupacion_isco: string
  match_score: number
  perfil_consolidado_version: string
  skills_candidato: ReportSkillItem[]
  skills_requeridas: ReportSkillItem[]
  skills_cubiertas: ReportSkillItem[]
  skills_gap: ReportSkillItem[]
  estado: 'activo' | 'expirado' | 'revocado'
  created_at: string
  expira_at: string
}

interface Props {
  data: ReportData
}

function calcScore(required: ReportSkillItem[], covered: ReportSkillItem[]): number {
  if (required.length === 0) return 0
  const coveredUris = new Set(covered.map((s) => s.uri))
  const matched = required.filter((s) => coveredUris.has(s.uri)).length
  return Math.round((matched / required.length) * 100)
}

export default function CompatibilityReport({ data }: Props) {
  const [required, setRequired] = useState<ReportSkillItem[]>(data.skills_requeridas)
  const [covered, setCovered] = useState<ReportSkillItem[]>(data.skills_cubiertas)
  const isEdited =
    required.length !== data.skills_requeridas.length ||
    required.some((s, i) => s.uri !== data.skills_requeridas[i]?.uri)

  const score = calcScore(required, covered)
  const coveredCount = required.filter((s) =>
    covered.some((c) => c.uri === s.uri)
  ).length
  const gaps = required.filter((s) => !covered.some((c) => c.uri === s.uri))

  const handleChange = (newRequired: ReportSkillItem[], newCovered: ReportSkillItem[]) => {
    setRequired(newRequired)
    setCovered(newCovered)
  }

  const handleRestore = () => {
    setRequired(data.skills_requeridas)
    setCovered(data.skills_cubiertas)
  }

  const scoreColor =
    score >= 80 ? 'bg-green-500' : score >= 50 ? 'bg-yellow-400' : 'bg-red-400'

  return (
    <div className="mx-auto max-w-3xl space-y-6 px-4 py-8">
      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="text-2xl font-bold text-blue-700">MOL</div>
        <h1 className="text-lg font-semibold text-gray-700">Reporte de Compatibilidad Laboral</h1>
      </div>

      {/* Profile data */}
      <div className="rounded-lg border border-gray-200 bg-white p-6">
        <h2 className="mb-3 text-base font-semibold text-gray-800">Datos del Perfil</h2>
        <dl className="grid grid-cols-1 gap-2 text-sm sm:grid-cols-2">
          <div>
            <dt className="text-gray-500">Candidato</dt>
            <dd className="font-medium text-gray-900">{data.candidato_nombre}</dd>
          </div>
          <div>
            <dt className="text-gray-500">Vacante analizada</dt>
            <dd className="font-medium text-gray-900">{data.ocupacion_label}</dd>
          </div>
          <div>
            <dt className="text-gray-500">Código ISCO</dt>
            <dd className="font-medium text-gray-900">{data.ocupacion_isco}</dd>
          </div>
          <div>
            <dt className="text-gray-500">Perfil Consolidado</dt>
            <dd className="font-medium text-gray-900">{data.perfil_consolidado_version}</dd>
          </div>
          <div>
            <dt className="text-gray-500">Fecha del reporte</dt>
            <dd className="font-medium text-gray-900">
              {new Date(data.created_at).toLocaleDateString('es-AR')}
            </dd>
          </div>
        </dl>

        {/* Score bar */}
        <div className="mt-4">
          <div className="mb-1 flex items-center justify-between text-sm">
            <span className="font-medium text-gray-700">Compatibilidad general</span>
            <span className="font-bold text-gray-900">
              {score}%
              {isEdited && (
                <span className="ml-1 text-xs text-blue-500">(recalculada)</span>
              )}
            </span>
          </div>
          <div className="h-3 overflow-hidden rounded-full bg-gray-100">
            <div
              className={`h-full rounded-full transition-all duration-300 ${scoreColor}`}
              style={{ width: `${score}%` }}
            />
          </div>
          <p className="mt-1 text-xs text-gray-400">
            {coveredCount} de {required.length} competencias esenciales
          </p>
          {isEdited && (
            <button
              onClick={handleRestore}
              className="mt-2 text-xs text-blue-500 hover:underline"
            >
              Restaurar original
            </button>
          )}
        </div>
      </div>

      {/* Skills map */}
      <SkillsMapEditable
        required={required}
        covered={covered}
        onChange={handleChange}
      />

      {/* Affinity matrix */}
      <AffinityMatrix
        detected={covered.filter((s) => required.some((r) => r.uri === s.uri))}
        gaps={gaps}
      />

      {/* About MOL */}
      <div className="rounded-lg border border-gray-200 bg-gray-50 p-6 text-sm text-gray-600">
        <h2 className="mb-2 font-semibold text-gray-800">Sobre el MOL</h2>
        <p>
          El Monitor de Ofertas Laborales (MOL) es una herramienta del Observatorio de Empleo y
          Dinámica Empresarial (OEDE) que analiza la demanda laboral utilizando la taxonomía ESCO
          para estandarizar competencias.
        </p>
        <a
          href="https://mol-nextjs.vercel.app"
          target="_blank"
          rel="noopener noreferrer"
          className="mt-2 inline-block text-blue-600 hover:underline"
        >
          Conocer más sobre el MOL →
        </a>
        <p className="mt-2 text-gray-400">Consultas: contacto@oede.gob.ar</p>
      </div>
    </div>
  )
}
