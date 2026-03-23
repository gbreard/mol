'use client'

import { useState } from 'react'
import { Plus, Edit2, Trash2, Save, X, Search } from 'lucide-react'

export interface DictEntry {
  id: string
  key: string           // término / trigger
  value: string         // valor / mapeo
  activa: boolean
  nota?: string
}

export type DictType =
  | 'sinonimos'
  | 'nlp_inference'
  | 'skills_rules'
  | 'oficios'

interface Props {
  tipo: DictType
  entries: DictEntry[]
  onAdd?: (entry: Omit<DictEntry, 'id'>) => Promise<void>
  onEdit?: (id: string, changes: Partial<DictEntry>) => Promise<void>
  onDelete?: (id: string) => Promise<void>
}

const TIPO_LABELS: Record<DictType, { key: string; value: string; title: string }> = {
  sinonimos:     { key: 'Término',  value: 'Sinónimo ESCO',     title: 'Diccionario de sinónimos' },
  nlp_inference: { key: 'Keyword',  value: 'Valor inferido',    title: 'Reglas de inferencia NLP' },
  skills_rules:  { key: 'Trigger',  value: 'Skills forzadas',   title: 'Reglas de skills' },
  oficios:       { key: 'Oficio',   value: 'ISCO / ESCO',       title: 'Catálogo de oficios' },
}

export default function DictionaryEditor({ tipo, entries, onAdd, onEdit, onDelete }: Props) {
  const labels = TIPO_LABELS[tipo]
  const [query, setQuery] = useState('')
  const [editingId, setEditingId] = useState<string | null>(null)
  const [editValues, setEditValues] = useState<Partial<DictEntry>>({})
  const [adding, setAdding] = useState(false)
  const [newEntry, setNewEntry] = useState<Omit<DictEntry, 'id'>>({ key: '', value: '', activa: true })
  const [saving, setSaving] = useState(false)

  const filtered = entries.filter(
    (e) =>
      e.key.toLowerCase().includes(query.toLowerCase()) ||
      e.value.toLowerCase().includes(query.toLowerCase())
  )

  const startEdit = (entry: DictEntry) => {
    setEditingId(entry.id)
    setEditValues({ key: entry.key, value: entry.value, nota: entry.nota, activa: entry.activa })
  }

  const cancelEdit = () => {
    setEditingId(null)
    setEditValues({})
  }

  const saveEdit = async (id: string) => {
    setSaving(true)
    try {
      await onEdit?.(id, editValues)
      setEditingId(null)
    } finally {
      setSaving(false)
    }
  }

  const saveNew = async () => {
    if (!newEntry.key.trim() || !newEntry.value.trim()) return
    setSaving(true)
    try {
      await onAdd?.(newEntry)
      setNewEntry({ key: '', value: '', activa: true })
      setAdding(false)
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={`Buscar en ${labels.title.toLowerCase()}...`}
            aria-label={`Buscar en ${tipo}`}
            className="w-full rounded-lg border border-gray-300 py-2 pl-9 pr-3 text-sm focus:border-blue-500 focus:outline-none"
          />
        </div>
        <button
          onClick={() => setAdding(true)}
          aria-label="Agregar entrada"
          className="flex min-h-[44px] items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
        >
          <Plus className="h-4 w-4" />
          Agregar
        </button>
      </div>

      {/* Contador */}
      <p className="text-xs text-gray-400">{filtered.length} entradas{query && ` que coinciden con "${query}"`}</p>

      {/* Formulario nuevo */}
      {adding && (
        <div className="rounded-xl border border-blue-200 bg-blue-50 p-4">
          <p className="mb-3 text-sm font-medium text-blue-900">Nueva entrada</p>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="mb-1 block text-xs text-gray-600">{labels.key}</label>
              <input
                type="text"
                value={newEntry.key}
                onChange={(e) => setNewEntry((p) => ({ ...p, key: e.target.value }))}
                aria-label={`Nuevo ${labels.key}`}
                className="w-full rounded border border-gray-300 px-2 py-1.5 text-sm focus:outline-none"
              />
            </div>
            <div>
              <label className="mb-1 block text-xs text-gray-600">{labels.value}</label>
              <input
                type="text"
                value={newEntry.value}
                onChange={(e) => setNewEntry((p) => ({ ...p, value: e.target.value }))}
                aria-label={`Nuevo ${labels.value}`}
                className="w-full rounded border border-gray-300 px-2 py-1.5 text-sm focus:outline-none"
              />
            </div>
          </div>
          <div className="mt-3 flex gap-2">
            <button
              onClick={saveNew}
              disabled={!newEntry.key.trim() || !newEntry.value.trim() || saving}
              aria-label="Confirmar nueva entrada"
              className="flex min-h-[44px] items-center gap-1.5 rounded-lg bg-blue-600 px-3 py-2 text-sm font-medium text-white disabled:opacity-50"
            >
              <Save className="h-3.5 w-3.5" />
              Guardar
            </button>
            <button
              onClick={() => setAdding(false)}
              aria-label="Cancelar nueva entrada"
              className="flex min-h-[44px] items-center gap-1.5 rounded-lg border border-gray-300 px-3 py-2 text-sm text-gray-600"
            >
              <X className="h-3.5 w-3.5" />
              Cancelar
            </button>
          </div>
        </div>
      )}

      {/* Tabla */}
      {filtered.length === 0 ? (
        <p className="text-sm text-gray-400">No hay entradas{query ? ' para esa búsqueda' : ''}.</p>
      ) : (
        <div className="overflow-x-auto rounded-xl border border-gray-200">
          <table className="w-full text-sm">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-2 text-left font-medium text-gray-600">{labels.key}</th>
                <th className="px-4 py-2 text-left font-medium text-gray-600">{labels.value}</th>
                <th className="px-4 py-2 text-center font-medium text-gray-600">Activa</th>
                <th className="px-4 py-2" />
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {filtered.map((entry) =>
                editingId === entry.id ? (
                  <tr key={entry.id} className="bg-blue-50">
                    <td className="px-4 py-2">
                      <input
                        value={editValues.key ?? ''}
                        onChange={(e) => setEditValues((p) => ({ ...p, key: e.target.value }))}
                        aria-label={`Editar ${labels.key} de ${entry.key}`}
                        className="w-full rounded border border-gray-300 px-2 py-1 text-sm"
                      />
                    </td>
                    <td className="px-4 py-2">
                      <input
                        value={editValues.value ?? ''}
                        onChange={(e) => setEditValues((p) => ({ ...p, value: e.target.value }))}
                        aria-label={`Editar ${labels.value} de ${entry.key}`}
                        className="w-full rounded border border-gray-300 px-2 py-1 text-sm"
                      />
                    </td>
                    <td className="px-4 py-2 text-center">
                      <input
                        type="checkbox"
                        checked={editValues.activa ?? true}
                        onChange={(e) => setEditValues((p) => ({ ...p, activa: e.target.checked }))}
                        aria-label="Activa"
                      />
                    </td>
                    <td className="px-4 py-2">
                      <div className="flex gap-1">
                        <button
                          onClick={() => saveEdit(entry.id)}
                          disabled={saving}
                          aria-label={`Guardar cambios de ${entry.key}`}
                          className="min-h-[44px] rounded px-2 text-blue-600 hover:bg-blue-100"
                        >
                          <Save className="h-4 w-4" />
                        </button>
                        <button
                          onClick={cancelEdit}
                          aria-label="Cancelar edición"
                          className="min-h-[44px] rounded px-2 text-gray-400 hover:bg-gray-100"
                        >
                          <X className="h-4 w-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ) : (
                  <tr key={entry.id} className={!entry.activa ? 'opacity-50' : ''}>
                    <td className="px-4 py-2 font-medium text-gray-800">{entry.key}</td>
                    <td className="px-4 py-2 text-gray-600">{entry.value}</td>
                    <td className="px-4 py-2 text-center">
                      <span className={`inline-block h-2 w-2 rounded-full ${entry.activa ? 'bg-green-500' : 'bg-gray-300'}`} />
                    </td>
                    <td className="px-4 py-2">
                      <div className="flex gap-1">
                        <button
                          onClick={() => startEdit(entry)}
                          aria-label={`Editar ${entry.key}`}
                          className="min-h-[44px] rounded px-2 text-gray-400 hover:text-blue-600"
                        >
                          <Edit2 className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => onDelete?.(entry.id)}
                          aria-label={`Eliminar ${entry.key}`}
                          className="min-h-[44px] rounded px-2 text-gray-400 hover:text-red-500"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                )
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
