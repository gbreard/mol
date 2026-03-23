'use client'

import { useState } from 'react'
import { Tag, Trash2, Link2 } from 'lucide-react'

export type UnclassifiedType = 'skills' | 'ocupaciones'

export interface UnclassifiedItem {
  id: string
  label: string
  frecuencia: number   // apariciones en ofertas
  ejemplos: string[]   // ejemplos de contexto
}

interface Props {
  items: UnclassifiedItem[]
  tipo: UnclassifiedType
  minFreq?: number
  onCatalogar?: (item: UnclassifiedItem) => void
  onSinonimo?: (item: UnclassifiedItem) => void
  onDescartar?: (item: UnclassifiedItem) => void
}

export default function UnclassifiedPanel({
  items,
  tipo,
  minFreq = 0,
  onCatalogar,
  onSinonimo,
  onDescartar,
}: Props) {
  const [activeTab, setActiveTab] = useState<UnclassifiedType>(tipo)
  const [freqFilter, setFreqFilter] = useState(minFreq)
  const [descartados, setDescartados] = useState<Set<string>>(new Set())

  const filtered = items
    .filter((i) => i.frecuencia >= freqFilter && !descartados.has(i.id))

  const handleDescartar = (item: UnclassifiedItem) => {
    setDescartados((prev) => new Set(prev).add(item.id))
    onDescartar?.(item)
  }

  const tabs: { key: UnclassifiedType; label: string }[] = [
    { key: 'skills', label: 'Skills' },
    { key: 'ocupaciones', label: 'Ocupaciones' },
  ]

  return (
    <div className="space-y-4">
      {/* Tabs */}
      <div className="flex gap-1 rounded-lg border border-gray-200 bg-gray-50 p-1 w-fit">
        {tabs.map((t) => (
          <button
            key={t.key}
            onClick={() => setActiveTab(t.key)}
            aria-pressed={activeTab === t.key}
            className={`rounded-md px-4 py-1.5 text-sm font-medium transition-colors ${
              activeTab === t.key
                ? 'bg-white text-gray-900 shadow-sm'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Filtro frecuencia */}
      <div className="flex items-center gap-3">
        <label className="text-sm text-gray-600" htmlFor="freq-filter">
          Mínimo de apariciones:
        </label>
        <input
          id="freq-filter"
          type="number"
          min={0}
          value={freqFilter}
          onChange={(e) => setFreqFilter(Number(e.target.value))}
          aria-label="Filtrar por frecuencia mínima"
          className="w-20 rounded-lg border border-gray-300 px-2 py-1 text-sm focus:border-blue-500 focus:outline-none"
        />
        <span className="text-xs text-gray-400">{filtered.length} items</span>
      </div>

      {/* Lista */}
      {filtered.length === 0 ? (
        <p className="text-sm text-gray-400">No hay {activeTab} sin clasificar con esa frecuencia.</p>
      ) : (
        <ul className="space-y-2">
          {filtered.map((item) => (
            <li
              key={item.id}
              className="rounded-xl border border-gray-200 bg-white p-4"
            >
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <p className="font-medium text-gray-900">{item.label}</p>
                    <span className="rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-500">
                      {item.frecuencia} ofertas
                    </span>
                  </div>
                  {item.ejemplos.length > 0 && (
                    <p className="mt-1 text-xs text-gray-400 truncate">
                      Ej: {item.ejemplos.slice(0, 2).join(' · ')}
                    </p>
                  )}
                </div>

                <div className="flex shrink-0 gap-2">
                  <button
                    onClick={() => onCatalogar?.(item)}
                    aria-label={`Catalogar ${item.label}`}
                    className="flex min-h-[44px] items-center gap-1.5 rounded-lg bg-blue-600 px-3 py-2 text-xs font-medium text-white hover:bg-blue-700"
                  >
                    <Tag className="h-3.5 w-3.5" />
                    Catalogar
                  </button>
                  <button
                    onClick={() => onSinonimo?.(item)}
                    aria-label={`Marcar ${item.label} como sinónimo`}
                    className="flex min-h-[44px] items-center gap-1.5 rounded-lg border border-gray-300 px-3 py-2 text-xs text-gray-600 hover:bg-gray-50"
                  >
                    <Link2 className="h-3.5 w-3.5" />
                    Sinónimo
                  </button>
                  <button
                    onClick={() => handleDescartar(item)}
                    aria-label={`Descartar ${item.label}`}
                    className="flex min-h-[44px] items-center rounded-lg border border-gray-200 px-2 py-2 text-gray-400 hover:text-red-500"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                </div>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
