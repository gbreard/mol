'use client'

import { useState } from 'react'
import { X, Save } from 'lucide-react'

export type FichaTipo = 'skill' | 'knowledge' | 'ocupacion'
export type FichaCategoria = 'digital' | 'tecnica' | 'transversal' | 'oficio' | 'gestion'

export interface MolFicha {
  label: string
  definicion: string
  tipo: FichaTipo
  categoria: FichaCategoria
  esco_parent?: string   // URI ESCO relacionado
  relaciones: string[]   // labels de skills relacionadas
}

interface Props {
  initial?: Partial<MolFicha>
  onSave?: (ficha: MolFicha) => Promise<void>
  onClose?: () => void
}

const CATEGORIAS: { value: FichaCategoria; label: string }[] = [
  { value: 'digital', label: 'Digital' },
  { value: 'tecnica', label: 'Técnica' },
  { value: 'transversal', label: 'Transversal' },
  { value: 'oficio', label: 'Oficio' },
  { value: 'gestion', label: 'Gestión' },
]

export default function MolFichaEditor({ initial, onSave, onClose }: Props) {
  const [label, setLabel] = useState(initial?.label ?? '')
  const [definicion, setDefinicion] = useState(initial?.definicion ?? '')
  const [tipo, setTipo] = useState<FichaTipo>(initial?.tipo ?? 'skill')
  const [categoria, setCategoria] = useState<FichaCategoria>(initial?.categoria ?? 'tecnica')
  const [escoParent, setEscoParent] = useState(initial?.esco_parent ?? '')
  const [relacionInput, setRelacionInput] = useState('')
  const [relaciones, setRelaciones] = useState<string[]>(initial?.relaciones ?? [])
  const [saving, setSaving] = useState(false)

  const isValid = label.trim().length > 0 && definicion.trim().length > 0

  const addRelacion = () => {
    const val = relacionInput.trim()
    if (val && !relaciones.includes(val)) {
      setRelaciones((prev) => [...prev, val])
    }
    setRelacionInput('')
  }

  const removeRelacion = (rel: string) => {
    setRelaciones((prev) => prev.filter((r) => r !== rel))
  }

  const handleSave = async () => {
    if (!isValid) return
    setSaving(true)
    try {
      await onSave?.({ label, definicion, tipo, categoria, esco_parent: escoParent || undefined, relaciones })
    } finally {
      setSaving(false)
    }
  }

  return (
    <div
      role="dialog"
      aria-label="Editor de ficha MOL"
      aria-modal="true"
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
    >
      <div className="w-full max-w-lg rounded-2xl bg-white p-6 shadow-xl">
        {/* Header */}
        <div className="mb-5 flex items-center justify-between">
          <h2 className="text-lg font-bold text-gray-900">Nueva ficha MOL</h2>
          <button
            onClick={onClose}
            aria-label="Cerrar editor"
            className="rounded-lg p-1 text-gray-400 hover:text-gray-600"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="space-y-4">
          {/* Label */}
          <div>
            <label className="mb-1 block text-sm font-medium text-gray-700" htmlFor="ficha-label">
              Nombre
            </label>
            <input
              id="ficha-label"
              type="text"
              value={label}
              onChange={(e) => setLabel(e.target.value)}
              placeholder="Ej: Facturación electrónica AFIP"
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
            />
          </div>

          {/* Definición */}
          <div>
            <label className="mb-1 block text-sm font-medium text-gray-700" htmlFor="ficha-definicion">
              Definición
            </label>
            <textarea
              id="ficha-definicion"
              value={definicion}
              onChange={(e) => setDefinicion(e.target.value)}
              rows={3}
              placeholder="Descripción de la skill u ocupación..."
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
            />
          </div>

          {/* Tipo */}
          <div>
            <p className="mb-2 text-sm font-medium text-gray-700">Tipo</p>
            <div className="flex gap-3">
              {(['skill', 'knowledge', 'ocupacion'] as FichaTipo[]).map((t) => (
                <label
                  key={t}
                  className="flex min-h-[44px] cursor-pointer items-center gap-2 rounded-lg border border-gray-200 px-3 py-2 text-sm has-[:checked]:border-blue-500 has-[:checked]:bg-blue-50"
                >
                  <input
                    type="radio"
                    name="tipo"
                    value={t}
                    checked={tipo === t}
                    onChange={() => setTipo(t)}
                    aria-label={`Tipo: ${t}`}
                    className="accent-blue-600"
                  />
                  <span className="capitalize text-gray-700">{t}</span>
                </label>
              ))}
            </div>
          </div>

          {/* Categoría */}
          <div>
            <label className="mb-1 block text-sm font-medium text-gray-700" htmlFor="ficha-categoria">
              Categoría
            </label>
            <select
              id="ficha-categoria"
              value={categoria}
              onChange={(e) => setCategoria(e.target.value as FichaCategoria)}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
            >
              {CATEGORIAS.map((c) => (
                <option key={c.value} value={c.value}>{c.label}</option>
              ))}
            </select>
          </div>

          {/* ESCO parent */}
          <div>
            <label className="mb-1 block text-sm font-medium text-gray-700" htmlFor="ficha-esco">
              ESCO relacionado (opcional)
            </label>
            <input
              id="ficha-esco"
              type="text"
              value={escoParent}
              onChange={(e) => setEscoParent(e.target.value)}
              placeholder="URI o label ESCO..."
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
            />
          </div>

          {/* Relaciones */}
          <div>
            <p className="mb-1 text-sm font-medium text-gray-700">Skills relacionadas</p>
            <div className="flex gap-2">
              <input
                type="text"
                value={relacionInput}
                onChange={(e) => setRelacionInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && addRelacion()}
                placeholder="Agregar skill relacionada..."
                aria-label="Agregar relación"
                className="flex-1 rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
              />
              <button
                type="button"
                onClick={addRelacion}
                aria-label="Confirmar relación"
                className="min-h-[44px] rounded-lg border border-gray-300 px-3 text-sm text-gray-600 hover:bg-gray-50"
              >
                +
              </button>
            </div>
            {relaciones.length > 0 && (
              <div className="mt-2 flex flex-wrap gap-1">
                {relaciones.map((rel) => (
                  <span key={rel} className="flex items-center gap-1 rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-700">
                    {rel}
                    <button
                      onClick={() => removeRelacion(rel)}
                      aria-label={`Quitar relación ${rel}`}
                      className="text-gray-400 hover:text-red-500"
                    >
                      <X className="h-3 w-3" />
                    </button>
                  </span>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Acciones */}
        <div className="mt-6 flex gap-3">
          <button
            onClick={onClose}
            aria-label="Cancelar edición"
            className="flex min-h-[44px] flex-1 items-center justify-center rounded-lg border border-gray-300 px-4 py-2 text-sm text-gray-600 hover:bg-gray-50"
          >
            Cancelar
          </button>
          <button
            onClick={handleSave}
            disabled={!isValid || saving}
            aria-label="Guardar ficha MOL"
            className="flex min-h-[44px] flex-1 items-center justify-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
          >
            <Save className="h-4 w-4" />
            {saving ? 'Guardando...' : 'Guardar ficha'}
          </button>
        </div>
      </div>
    </div>
  )
}
