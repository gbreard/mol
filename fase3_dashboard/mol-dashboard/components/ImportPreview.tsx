'use client'

import { X, Check } from 'lucide-react'

export interface ImportRow {
  nombre: string | null
  dni: string | null
  ocupacion: string | null
  skills: string | null
}

export interface ImportSummary {
  total: number
  con_ocupacion: number
  con_skills: number
  sin_datos: number
  sin_nombre: number
}

interface Props {
  rows: ImportRow[]
  summary: ImportSummary
  onConfirm: () => void
  onCancel: () => void
  loading?: boolean
}

export default function ImportPreview({ rows, summary, onConfirm, onCancel, loading }: Props) {
  const validCount = summary.total - summary.sin_nombre

  return (
    <div className="space-y-4">
      <p className="text-sm text-gray-600">
        Se encontraron <strong>{summary.total}</strong> personas.
        {summary.sin_nombre > 0 && (
          <span className="ml-1 text-amber-600">
            {summary.sin_nombre} sin nombre (se saltan).
          </span>
        )}
      </p>

      {/* Tabla preview */}
      <div className="overflow-x-auto rounded-lg border border-gray-200">
        <table className="w-full text-sm">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-2 text-left font-medium text-gray-600">Nombre</th>
              <th className="px-4 py-2 text-left font-medium text-gray-600">DNI</th>
              <th className="px-4 py-2 text-left font-medium text-gray-600">Ocupación</th>
              <th className="px-4 py-2 text-left font-medium text-gray-600">Skills</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {rows.map((row, i) => (
              <tr key={i} className={!row.nombre ? 'opacity-40' : ''}>
                <td className="px-4 py-2 text-gray-900">{row.nombre ?? <span className="text-red-400 italic">sin nombre</span>}</td>
                <td className="px-4 py-2 text-gray-500">{row.dni ?? '—'}</td>
                <td className="px-4 py-2 text-gray-700">{row.ocupacion ?? '—'}</td>
                <td className="px-4 py-2 text-gray-500">{row.skills ?? '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <p className="border-t border-gray-100 px-4 py-2 text-xs text-gray-400">
          Mostrando {rows.length} de {summary.total}
        </p>
      </div>

      {/* Resumen */}
      <div className="rounded-lg bg-gray-50 p-4 text-sm">
        <p className="mb-2 font-medium text-gray-700">Resumen:</p>
        <ul className="space-y-1 text-gray-600">
          <li>· Con ocupación declarada: <strong>{summary.con_ocupacion}</strong> (se derivan skills automáticamente)</li>
          <li>· Con skills explícitas: <strong>{summary.con_skills}</strong></li>
          <li>· Sin datos de ocupación ni skills: <strong>{summary.sin_datos}</strong></li>
          {summary.sin_nombre > 0 && (
            <li className="text-amber-600">· Sin nombre (se saltan): <strong>{summary.sin_nombre}</strong></li>
          )}
        </ul>
      </div>

      {/* Acciones */}
      <div className="flex gap-3">
        <button
          onClick={onCancel}
          aria-label="Cancelar importación"
          className="flex min-h-[44px] flex-1 items-center justify-center gap-2 rounded-lg border border-gray-300 px-4 py-2 text-sm text-gray-600 hover:bg-gray-50"
        >
          <X className="h-4 w-4" />
          Cancelar
        </button>
        <button
          onClick={onConfirm}
          disabled={loading || validCount === 0}
          aria-label={`Confirmar importación de ${validCount}`}
          className="flex min-h-[44px] flex-1 items-center justify-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
        >
          <Check className="h-4 w-4" />
          {loading ? 'Importando...' : `Confirmar importación de ${validCount}`}
        </button>
      </div>
    </div>
  )
}
