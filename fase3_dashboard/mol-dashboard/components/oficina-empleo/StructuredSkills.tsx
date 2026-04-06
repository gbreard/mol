'use client'

import { useState } from 'react'
import { Plus, X } from 'lucide-react'
import type { SelectedSkill } from './useSkillCapture'

interface Props {
  skillUris: Set<string>
  onAddSkill: (skill: SelectedSkill) => void
}

const IDIOMAS = ['Inglés', 'Portugués', 'Francés', 'Italiano', 'Alemán']
const OFIMATICA = ['Excel', 'Word', 'PowerPoint']
const SOFTWARE = ['Python', 'JavaScript', 'SAP', 'AutoCAD', 'Photoshop']

const NIVELES_IDIOMA = ['Básico', 'Intermedio', 'Avanzado', 'Nativo']
const NIVELES = ['Básico', 'Intermedio', 'Avanzado']

type Category = 'idioma' | 'herramienta' | 'software'

interface Entry {
  label: string
  nivel: string
  category: Category
}

export function StructuredSkills({ skillUris, onAddSkill }: Props) {
  const [category, setCategory] = useState<Category>('idioma')
  const [selected, setSelected] = useState('')
  const [customText, setCustomText] = useState('')
  const [nivel, setNivel] = useState('')

  const options = category === 'idioma' ? IDIOMAS : category === 'herramienta' ? OFIMATICA : SOFTWARE
  const niveles = category === 'idioma' ? NIVELES_IDIOMA : NIVELES
  const showCustom = selected === '__otro__'
  const actualLabel = showCustom ? customText.trim() : selected

  function addEntry() {
    if (!actualLabel || !nivel) return
    const fullLabel = `${actualLabel} — ${nivel}`
    const uri = `structured:${category}:${actualLabel.toLowerCase()}`

    if (skillUris.has(uri)) return

    const skill: SelectedSkill = {
      uri,
      label: fullLabel,
      type: category === 'idioma' ? 'knowledge' : 'skill',
      source: 'estructurado',
      category,
    }
    onAddSkill(skill)
    setSelected('')
    setCustomText('')
    setNivel('')
  }

  const TABS: { id: Category; label: string }[] = [
    { id: 'idioma', label: 'Idiomas' },
    { id: 'herramienta', label: 'Ofimática' },
    { id: 'software', label: 'Software' },
  ]

  return (
    <div className="space-y-3">
      <p className="text-sm text-gray-500">
        ¿Manejás algún idioma, programa o herramienta específica?
      </p>

      {/* Category tabs */}
      <div className="flex gap-1 bg-gray-100 rounded-lg p-1">
        {TABS.map(t => (
          <button
            key={t.id}
            onClick={() => { setCategory(t.id); setSelected(''); setCustomText(''); setNivel('') }}
            className={`flex-1 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${category === t.id ? 'bg-white text-teal-700 shadow-sm' : 'text-gray-500 hover:text-gray-700'}`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Selection row */}
      <div className="flex gap-2 items-end flex-wrap">
        <div className="flex-1 min-w-[140px]">
          <label className="text-xs text-gray-500 mb-1 block">
            {category === 'idioma' ? 'Idioma' : category === 'herramienta' ? 'Herramienta' : 'Software'}
          </label>
          <select
            value={selected}
            onChange={e => { setSelected(e.target.value); setCustomText('') }}
            className="w-full border rounded-lg px-3 py-2 text-sm"
          >
            <option value="">Seleccionar...</option>
            {options.map(o => (
              <option key={o} value={o}>{o}</option>
            ))}
            <option value="__otro__">Otro...</option>
          </select>
        </div>

        {showCustom && (
          <div className="flex-1 min-w-[120px]">
            <label className="text-xs text-gray-500 mb-1 block">Especificar</label>
            <input
              value={customText}
              onChange={e => setCustomText(e.target.value)}
              placeholder="Nombre..."
              className="w-full border rounded-lg px-3 py-2 text-sm"
            />
          </div>
        )}

        <div className="min-w-[120px]">
          <label className="text-xs text-gray-500 mb-1 block">Nivel</label>
          <select
            value={nivel}
            onChange={e => setNivel(e.target.value)}
            className="w-full border rounded-lg px-3 py-2 text-sm"
          >
            <option value="">Nivel...</option>
            {niveles.map(n => (
              <option key={n} value={n}>{n}</option>
            ))}
          </select>
        </div>

        <button
          onClick={addEntry}
          disabled={!actualLabel || !nivel}
          className="bg-teal-600 text-white p-2 rounded-lg hover:bg-teal-700 disabled:opacity-50 shrink-0"
        >
          <Plus className="w-4 h-4" />
        </button>
      </div>
    </div>
  )
}
