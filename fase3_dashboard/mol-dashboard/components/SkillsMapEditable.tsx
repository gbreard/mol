'use client'

import { useState } from 'react'

export interface ReportSkillItem {
  uri: string
  label: string
  type: 'skill' | 'knowledge' | 'transversal'
  source: 'esco' | 'argentina_approved'
  description?: string
}

interface Props {
  required: ReportSkillItem[]
  covered: ReportSkillItem[]
  onChange: (required: ReportSkillItem[], covered: ReportSkillItem[]) => void
}

export default function SkillsMapEditable({ required, covered, onChange }: Props) {
  const [editMode, setEditMode] = useState(false)
  const [addInput, setAddInput] = useState('')

  const coveredUris = new Set(covered.map((s) => s.uri))

  const removeSkill = (uri: string) => {
    const newRequired = required.filter((s) => s.uri !== uri)
    const newCovered = covered.filter((s) => s.uri !== uri)
    onChange(newRequired, newCovered)
  }

  const addSkill = () => {
    const label = addInput.trim()
    if (!label) return
    const newSkill: ReportSkillItem = {
      uri: `custom:${Date.now()}`,
      label,
      type: 'skill',
      source: 'esco',
    }
    onChange([...required, newSkill], covered)
    setAddInput('')
  }

  const essential = required
  const detected = essential.filter((s) => coveredUris.has(s.uri))
  const missing = essential.filter((s) => !coveredUris.has(s.uri))

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-6">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-base font-semibold text-gray-800">
          Mapa de Competencias Requeridas
        </h2>
        <button
          onClick={() => setEditMode(!editMode)}
          className={`rounded-lg px-3 py-1.5 text-sm font-medium transition-colors ${
            editMode
              ? 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              : 'bg-blue-50 text-blue-600 hover:bg-blue-100'
          }`}
        >
          {editMode ? 'Cerrar edición' : 'Editar'}
        </button>
      </div>

      <p className="mb-3 text-xs text-gray-400">
        Competencias esenciales ({essential.length}): {detected.length} detectadas,{' '}
        {missing.length} faltantes
        {editMode && (
          <span className="ml-2 text-blue-500">
            · Los cambios recalculan la compatibilidad automáticamente
          </span>
        )}
      </p>

      <div className="overflow-hidden rounded-lg border border-gray-100">
        <table className="w-full text-sm">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-2 text-left font-medium text-gray-600">Competencia</th>
              <th className="px-4 py-2 text-left font-medium text-gray-600">Origen</th>
              <th className="px-4 py-2 text-left font-medium text-gray-600">Estado</th>
              {editMode && (
                <th className="px-4 py-2 text-right font-medium text-gray-600">Acción</th>
              )}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {essential.map((skill) => {
              const isDetected = coveredUris.has(skill.uri)
              return (
                <tr key={skill.uri} className="hover:bg-gray-50">
                  <td className="px-4 py-2 text-gray-800">{skill.label}</td>
                  <td className="px-4 py-2">
                    <span
                      className={`rounded px-1.5 py-0.5 text-xs ${
                        skill.source === 'argentina_approved'
                          ? 'bg-orange-100 text-orange-700'
                          : 'bg-gray-100 text-gray-600'
                      }`}
                    >
                      {skill.source === 'argentina_approved' ? 'emergente' : 'ESCO'}
                    </span>
                  </td>
                  <td className="px-4 py-2">
                    {isDetected ? (
                      <span className="rounded bg-green-100 px-2 py-0.5 text-xs font-medium text-green-700">
                        Detectada
                      </span>
                    ) : (
                      <span className="rounded bg-red-100 px-2 py-0.5 text-xs font-medium text-red-700">
                        Faltante
                      </span>
                    )}
                  </td>
                  {editMode && (
                    <td className="px-4 py-2 text-right">
                      <button
                        onClick={() => removeSkill(skill.uri)}
                        aria-label={`Quitar ${skill.label}`}
                        className="text-xs text-red-400 hover:text-red-600"
                      >
                        ✕ Quitar
                      </button>
                    </td>
                  )}
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      {editMode && (
        <div className="mt-4 flex gap-2">
          <input
            type="text"
            value={addInput}
            onChange={(e) => setAddInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && addSkill()}
            placeholder="Agregar competencia al mapa..."
            aria-label="Agregar competencia"
            className="flex-1 rounded-lg border border-gray-300 px-3 py-1.5 text-sm focus:border-blue-500 focus:outline-none"
          />
          <button
            onClick={addSkill}
            disabled={!addInput.trim()}
            className="rounded-lg bg-blue-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
          >
            + Agregar
          </button>
        </div>
      )}
    </div>
  )
}
