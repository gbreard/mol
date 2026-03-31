'use client'

export type SkillConfidence = 'confirmed' | 'unsure' | 'discarded'
export type SkillVia = 'ocupacion' | 'busqueda' | 'texto_libre' | 'tarea' | 'texto' | 'formacion'

export interface SkillItem {
  uri: string
  label: string
  type: 'skill' | 'knowledge'
  description: string
  source: 'esco' | 'argentina_approved'
  frequency?: number
  confidence: SkillConfidence
  via: SkillVia
}

interface Props {
  skill: SkillItem
  onConfidenceChange: (uri: string, confidence: SkillConfidence) => void
  onRemove: (uri: string) => void
}

const VIA_LABELS: Record<SkillVia, string> = {
  ocupacion: 'vía ocupación',
  busqueda: 'vía búsqueda',
  texto_libre: 'vía texto libre',
  tarea: 'vía tarea',
  texto: 'vía texto libre',
  formacion: 'vía formación',
}

const TYPE_LABELS: Record<string, string> = {
  skill: 'competencia',
  knowledge: 'conocimiento',
}

const SOURCE_LABELS: Record<string, string> = {
  esco: 'ESCO',
  argentina_approved: 'emergente',
}

export default function SkillWithDefinition({ skill, onConfidenceChange, onRemove }: Props) {
  const [expanded, setExpanded] = useState(false)
  const isLong = skill.description.length > 120

  return (
    <div
      className={`rounded-lg border p-3 transition-colors ${
        skill.confidence === 'discarded'
          ? 'border-red-200 bg-red-50 opacity-60'
          : 'border-gray-200 bg-white'
      }`}
    >
      <div className="flex items-start gap-2">
        {/* Confidence buttons */}
        <div className="flex flex-col gap-1 pt-0.5">
          <button
            onClick={() => onConfidenceChange(skill.uri, 'confirmed')}
            aria-label="Confirmar"
            className={`h-6 w-6 rounded text-xs font-bold transition-colors ${
              skill.confidence === 'confirmed'
                ? 'bg-green-500 text-white'
                : 'bg-gray-100 text-gray-400 hover:bg-green-100 hover:text-green-600'
            }`}
          >
            ✓
          </button>
          <button
            onClick={() => onConfidenceChange(skill.uri, 'unsure')}
            aria-label="No estoy seguro"
            className={`h-6 w-6 rounded text-xs font-bold transition-colors ${
              skill.confidence === 'unsure'
                ? 'bg-yellow-400 text-white'
                : 'bg-gray-100 text-gray-400 hover:bg-yellow-100 hover:text-yellow-600'
            }`}
          >
            ?
          </button>
          <button
            onClick={() => onConfidenceChange(skill.uri, 'discarded')}
            aria-label="Descartar"
            className={`h-6 w-6 rounded text-xs font-bold transition-colors ${
              skill.confidence === 'discarded'
                ? 'bg-red-400 text-white'
                : 'bg-gray-100 text-gray-400 hover:bg-red-100 hover:text-red-600'
            }`}
          >
            ✗
          </button>
        </div>

        {/* Content */}
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-1.5">
            <span className="font-medium text-gray-900">{skill.label}</span>
            <span className="rounded bg-blue-100 px-1.5 py-0.5 text-xs text-blue-700">
              {TYPE_LABELS[skill.type]}
            </span>
            <span
              className={`rounded px-1.5 py-0.5 text-xs ${
                skill.source === 'argentina_approved'
                  ? 'bg-orange-100 text-orange-700'
                  : 'bg-gray-100 text-gray-600'
              }`}
            >
              {SOURCE_LABELS[skill.source]}
            </span>
            <span className="rounded bg-purple-50 px-1.5 py-0.5 text-xs text-purple-600">
              {VIA_LABELS[skill.via]}
            </span>
            {skill.frequency !== undefined && (
              <span className="text-xs text-gray-400">{skill.frequency}% ofertas</span>
            )}
          </div>

          {/* Description */}
          <p className="mt-1 text-sm text-gray-500">
            {isLong && !expanded
              ? `${skill.description.slice(0, 120)}…`
              : skill.description}
            {isLong && (
              <button
                onClick={() => setExpanded(!expanded)}
                className="ml-1 text-xs text-blue-500 hover:underline"
              >
                {expanded ? 'ver menos' : 'ver más'}
              </button>
            )}
          </p>
        </div>

        {/* Remove button */}
        <button
          onClick={() => onRemove(skill.uri)}
          aria-label="Quitar skill"
          className="ml-1 rounded p-1 text-gray-300 hover:bg-red-50 hover:text-red-400"
        >
          ✕
        </button>
      </div>
    </div>
  )
}

// useState import
import { useState } from 'react'
