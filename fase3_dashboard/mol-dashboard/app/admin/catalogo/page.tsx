'use client'

import { useState, useEffect } from 'react'
import UnclassifiedPanel, { type UnclassifiedItem } from '@/components/UnclassifiedPanel'
import MolFichaEditor, { type MolFicha } from '@/components/MolFichaEditor'

export default function CatalogoPage() {
  const [showEditor, setShowEditor] = useState(false)
  const [selectedItem, setSelectedItem] = useState<UnclassifiedItem | null>(null)
  const [items, setItems] = useState<UnclassifiedItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)

  useEffect(() => {
    const load = async () => {
      try {
        const res = await fetch('/api/unclassified-items')
        if (res.ok) setItems(await res.json())
        else setError(true)
      } catch {
        setError(true)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  const handleCatalogar = (item: UnclassifiedItem) => {
    setSelectedItem(item)
    setShowEditor(true)
  }

  const handleSave = async (ficha: MolFicha) => {
    await fetch('/api/catalog-item', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(ficha) })
    setShowEditor(false)
    setItems(prev => prev.filter(i => i.id !== selectedItem?.id))
  }

  const handleSinonimo = async (item: UnclassifiedItem) => {
    await fetch('/api/catalog-item/sinonimo', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ id: item.id }) })
    setItems(prev => prev.filter(i => i.id !== item.id))
  }

  const handleDescartar = async (item: UnclassifiedItem) => {
    await fetch('/api/catalog-item/descartar', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ id: item.id }) })
    setItems(prev => prev.filter(i => i.id !== item.id))
  }

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-900 mb-1">Catálogo MOL</h1>
      <p className="text-sm text-gray-500 mb-6">
        Skills y ocupaciones detectadas en ofertas que no tienen match ESCO. Catalogalas, marcalas como sinónimos o descartarlas.
      </p>

      {loading ? (
        <div className="space-y-3">
          {[1, 2, 3].map(i => <div key={i} className="h-16 animate-pulse rounded-xl bg-gray-100" />)}
        </div>
      ) : error ? (
        <p className="text-sm text-red-500">No se pudo cargar el catálogo de items sin clasificar.</p>
      ) : (
        <UnclassifiedPanel
          items={items}
          tipo="skills"
          onCatalogar={handleCatalogar}
          onSinonimo={handleSinonimo}
          onDescartar={handleDescartar}
        />
      )}

      {showEditor && (
        <MolFichaEditor
          initial={{ label: selectedItem?.label ?? '' }}
          onSave={handleSave}
          onClose={() => setShowEditor(false)}
        />
      )}
    </div>
  )
}
