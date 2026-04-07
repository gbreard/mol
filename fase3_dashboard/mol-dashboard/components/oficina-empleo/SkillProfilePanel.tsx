'use client'

import { useMemo } from 'react'
import { X, Briefcase, Award } from 'lucide-react'
import type { SelectedSkill, SelectedOccupation, NivelMaestria } from './useSkillCapture'

const PROVINCIAS_AR = [
  'Buenos Aires', 'CABA', 'Catamarca', 'Chaco', 'Chubut', 'Córdoba',
  'Corrientes', 'Entre Ríos', 'Formosa', 'Jujuy', 'La Pampa', 'La Rioja',
  'Mendoza', 'Misiones', 'Neuquén', 'Río Negro', 'Salta', 'San Juan',
  'San Luis', 'Santa Cruz', 'Santa Fe', 'Santiago del Estero',
  'Tierra del Fuego', 'Tucumán',
]

interface Props {
  ocupaciones: SelectedOccupation[]
  skills: SelectedSkill[]
  onRemoveSkill: (uri: string) => void
  onRemoveOccupation: (id: string) => void
  onUpdateNivel?: (uri: string, nivel: NivelMaestria) => void
  onToggleCertificado?: (uri: string) => void
  nombre: string
  dni: string
  localidad: string
  provincia: string
  onSetNombre: (v: string) => void
  onSetDni: (v: string) => void
  onSetLocalidad: (v: string) => void
  onSetProvincia: (v: string) => void
  onSave: () => void
  saving?: boolean
  editMode?: boolean
}

interface Section {
  key: string
  label: string
  skills: SelectedSkill[]
}

function classifySkills(skills: SelectedSkill[]): Section[] {
  const sections: Section[] = [
    { key: 'essential', label: 'Skills esenciales', skills: [] },
    { key: 'technical', label: 'Skills técnicas', skills: [] },
    { key: 'digital', label: 'Habilidades digitales', skills: [] },
    { key: 'transversal', label: 'Transversales', skills: [] },
    { key: 'knowledge', label: 'Conocimientos', skills: [] },
    { key: 'idiomas', label: 'Idiomas', skills: [] },
    { key: 'otras', label: 'Otras', skills: [] },
  ]

  for (const s of skills) {
    if (s.source === 'estructurado' && s.category === 'idioma') {
      sections[5].skills.push(s)
    } else if (s.essential_for_occupation) {
      sections[0].skills.push(s)
    } else if (s.L1 === 'S5' || s.source === 'estructurado') {
      sections[2].skills.push(s)
    } else if (s.type === 'knowledge') {
      sections[4].skills.push(s)
    } else if (s.L1 && ['T1', 'T2', 'T3', 'T4', 'T5', 'T6'].includes(s.L1)) {
      sections[3].skills.push(s)
    } else if (s.L1 && ['S1', 'S2', 'S3', 'S4', 'S6', 'S7', 'S8'].includes(s.L1)) {
      sections[1].skills.push(s)
    } else if (s.L1) {
      sections[1].skills.push(s)
    } else {
      sections[6].skills.push(s)
    }
  }

  return sections.filter(sec => sec.skills.length > 0)
}

function DemandBar({ frequency }: { frequency?: number }) {
  if (!frequency) return null
  const level = frequency > 100 ? 3 : frequency > 30 ? 2 : 1
  return (
    <span className="text-[10px] text-gray-400 ml-1" title={`Demanda: ${frequency} ofertas`}>
      {'█'.repeat(level)}{'░'.repeat(3 - level)}
    </span>
  )
}

export function SkillProfilePanel({
  ocupaciones, skills, onRemoveSkill, onRemoveOccupation,
  nombre, dni, localidad, provincia,
  onSetNombre, onSetDni, onSetLocalidad, onSetProvincia,
  onUpdateNivel, onToggleCertificado,
  onSave, saving, editMode,
}: Props) {
  const sections = useMemo(() => classifySkills(skills), [skills])

  return (
    <div className="flex flex-col h-full">
      {/* Scrollable content */}
      <div className="flex-1 overflow-y-auto space-y-4 pr-1">
        {/* Occupations */}
        {ocupaciones.length > 0 && (
          <div>
            <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Ocupaciones</h3>
            <div className="flex flex-wrap gap-1.5">
              {ocupaciones.map(occ => (
                <span key={occ.id} className="inline-flex items-center gap-1.5 bg-teal-50 text-teal-700 text-xs font-medium px-2.5 py-1 rounded-lg">
                  <Briefcase className="w-3 h-3" />
                  {occ.label}
                  <button onClick={() => onRemoveOccupation(occ.id)} className="hover:text-teal-900"><X className="w-3 h-3" /></button>
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Skills by section */}
        {sections.map(sec => (
          <div key={sec.key}>
            <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1.5">
              {sec.label} <span className="text-gray-400 font-normal">({sec.skills.length})</span>
            </h3>
            <div className="space-y-2">
              {sec.skills.map(s => (
                <SkillRow
                  key={s.uri}
                  skill={s}
                  onRemove={onRemoveSkill}
                  onUpdateNivel={onUpdateNivel}
                  onToggleCertificado={onToggleCertificado}
                />
              ))}
            </div>
          </div>
        ))}

        {/* Empty state */}
        {skills.length === 0 && ocupaciones.length === 0 && (
          <div className="text-center py-8 text-gray-400">
            <p className="text-sm">Usá las vías de captura para agregar competencias</p>
          </div>
        )}
      </div>

      {/* Footer: count + person data + save */}
      <div className="border-t pt-3 mt-3 space-y-3">
        <div className="text-center text-sm text-gray-500">
          {skills.length} competencias
        </div>

        <div className="grid grid-cols-2 gap-2">
          <div>
            <label className="text-xs text-gray-500 mb-0.5 block">Nombre *</label>
            <input
              value={nombre}
              onChange={e => onSetNombre(e.target.value)}
              placeholder="Nombre completo"
              className="w-full border rounded-lg px-3 py-2 text-sm"
            />
          </div>
          <div>
            <label className="text-xs text-gray-500 mb-0.5 block">DNI *</label>
            <input
              value={dni}
              onChange={e => onSetDni(e.target.value)}
              placeholder="12.345.678"
              className="w-full border rounded-lg px-3 py-2 text-sm"
            />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-2">
          <div>
            <label className="text-xs text-gray-500 mb-0.5 block">Provincia</label>
            <select
              value={provincia}
              onChange={e => onSetProvincia(e.target.value)}
              className="w-full border rounded-lg px-3 py-2 text-sm"
            >
              <option value="">Seleccionar...</option>
              {PROVINCIAS_AR.map(p => <option key={p} value={p}>{p}</option>)}
            </select>
          </div>
          <div>
            <label className="text-xs text-gray-500 mb-0.5 block">Localidad</label>
            <input
              value={localidad}
              onChange={e => onSetLocalidad(e.target.value)}
              placeholder="Ciudad o partido"
              className="w-full border rounded-lg px-3 py-2 text-sm"
            />
          </div>
        </div>

        <button
          onClick={onSave}
          disabled={saving || !nombre.trim() || !dni.trim() || skills.length === 0}
          className="w-full bg-teal-600 text-white text-sm font-semibold py-2.5 rounded-lg hover:bg-teal-700 disabled:opacity-50 transition-colors"
        >
          {saving ? 'Guardando...' : editMode ? 'Actualizar perfil' : 'Guardar perfil'}
        </button>
      </div>
    </div>
  )
}

const NIVELES: { id: NivelMaestria; label: string; color: string; activeColor: string }[] = [
  { id: 'basico', label: 'Básico', color: 'text-gray-400', activeColor: 'bg-slate-200 text-slate-700' },
  { id: 'intermedio', label: 'Interm.', color: 'text-gray-400', activeColor: 'bg-teal-100 text-teal-700' },
  { id: 'avanzado', label: 'Avanz.', color: 'text-gray-400', activeColor: 'bg-blue-100 text-blue-700' },
  { id: 'experto', label: 'Experto', color: 'text-gray-400', activeColor: 'bg-purple-100 text-purple-700' },
]

function SkillRow({ skill, onRemove, onUpdateNivel, onToggleCertificado }: {
  skill: SelectedSkill
  onRemove: (uri: string) => void
  onUpdateNivel?: (uri: string, nivel: NivelMaestria) => void
  onToggleCertificado?: (uri: string) => void
}) {
  const nivel = skill.nivel || 'intermedio'

  return (
    <div className="border border-gray-100 rounded-lg px-2 py-1.5">
      {/* Top row: label + badges + remove */}
      <div className="flex items-center gap-1.5">
        <span className="text-sm text-gray-800 flex-1 min-w-0 truncate">{skill.label}</span>
        <DemandBar frequency={skill.market_frequency} />
        {skill.essential_for_occupation && (
          <span className="text-[10px] bg-teal-100 text-teal-700 px-1 py-0.5 rounded shrink-0">esencial</span>
        )}
        <button
          onClick={() => onRemove(skill.uri)}
          className="text-gray-300 hover:text-red-400 shrink-0"
        >
          <X className="w-3.5 h-3.5" />
        </button>
      </div>
      {/* Bottom row: nivel buttons + certificado */}
      <div className="flex items-center gap-1 mt-1">
        {NIVELES.map(n => (
          <button
            key={n.id}
            onClick={() => onUpdateNivel?.(skill.uri, n.id)}
            className={`text-[10px] px-1.5 py-0.5 rounded transition-colors ${
              nivel === n.id ? n.activeColor + ' font-medium' : 'text-gray-400 hover:bg-gray-100'
            }`}
          >
            {n.label}
          </button>
        ))}
        <button
          onClick={() => onToggleCertificado?.(skill.uri)}
          className={`ml-auto flex items-center gap-0.5 text-[10px] px-1.5 py-0.5 rounded transition-colors ${
            skill.certificado ? 'bg-green-100 text-green-700 font-medium' : 'text-gray-400 hover:bg-gray-100'
          }`}
        >
          <Award className="w-3 h-3" />
          Cert
        </button>
      </div>
    </div>
  )
}
