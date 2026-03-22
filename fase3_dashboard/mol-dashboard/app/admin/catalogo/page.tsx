'use client'

import { useState } from 'react'
import UnclassifiedPanel, { type UnclassifiedItem } from '@/components/UnclassifiedPanel'
import MolFichaEditor from '@/components/MolFichaEditor'

const MOCK_ITEMS: UnclassifiedItem[] = [
  { id: 'u1', label: 'Manejo de CRM', frecuencia: 342, ejemplos: ['usa CRM Salesforce', 'gestión CRM Zoho'] },
  { id: 'u2', label: 'Facturación AFIP', frecuencia: 287, ejemplos: ['factura electrónica AFIP', 'comprobantes AFIP'] },
  { id: 'u3', label: 'Punto de venta Tango', frecuencia: 198, ejemplos: ['sistema Tango POS'] },
  { id: 'u4', label: 'Atención en caja', frecuencia: 156, ejemplos: ['cajera supermercado', 'cobros y pagos'] },
  { id: 'u5', label: 'Logística last mile', frecuencia: 89, ejemplos: ['última milla', 'entrega domicilio'] },
]

export default function CatalogoPage() {
  const [showEditor, setShowEditor] = useState(false)
  const [selectedItem, setSelectedItem] = useState<UnclassifiedItem | null>(null)

  const handleCatalogar = (item: UnclassifiedItem) => {
    setSelectedItem(item)
    setShowEditor(true)
  }

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-900 mb-1">Catálogo MOL</h1>
      <p className="text-sm text-gray-500 mb-6">
        Skills y ocupaciones detectadas en ofertas que no tienen match ESCO. Catalogalas, marcalas como sinónimos o descartarlas.
      </p>

      <UnclassifiedPanel
        items={MOCK_ITEMS}
        tipo="skills"
        onCatalogar={handleCatalogar}
        onSinonimo={(item) => console.log('Sinónimo:', item.label)}
        onDescartar={(item) => console.log('Descartado:', item.label)}
      />

      {showEditor && (
        <MolFichaEditor
          initial={{ label: selectedItem?.label ?? '' }}
          onSave={async (ficha) => {
            console.log('Guardando ficha:', ficha)
            setShowEditor(false)
          }}
          onClose={() => setShowEditor(false)}
        />
      )}
    </div>
  )
}
