'use client'

import { useState, useEffect, useRef } from 'react'
import { Search, User, X, Loader2 } from 'lucide-react'

export interface PerfilResumen {
  id: string
  persona_id: string
  nombre: string
  dni: string
  ocupaciones: { label: string }[]
  completitud: number
  estado: string
  validado_at: string | null
}

interface Props {
  selectedId: string | null
  onSelect: (perfil: PerfilResumen) => void
  onClear: () => void
}

export function PersonaSelector({ selectedId, onSelect, onClear }: Props) {
  const [perfiles, setPerfiles] = useState<PerfilResumen[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [open, setOpen] = useState(false)
  const [selected, setSelected] = useState<PerfilResumen | null>(null)
  const ref = useRef<HTMLDivElement>(null)

  const onSelectRef = useRef(onSelect)
  onSelectRef.current = onSelect

  // Load all perfiles on mount
  useEffect(() => {
    fetch('/api/perfiles')
      .then(r => r.json())
      .then(data => {
        if (Array.isArray(data)) {
          const mapped = data.map((p: any) => ({
            id: p.id,
            persona_id: p.persona_id,
            nombre: p.personas?.nombre || '',
            dni: p.personas?.dni || '',
            ocupaciones: p.ocupaciones || [],
            completitud: p.completitud || 0,
            estado: p.estado || 'borrador',
            validado_at: p.validado_at,
          }))
          setPerfiles(mapped)
          // Auto-select if perfil_id provided
          if (selectedId) {
            const found = mapped.find((p: PerfilResumen) => p.id === selectedId)
            if (found) {
              setSelected(found)
              onSelectRef.current(found)
            }
          }
        }
      })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [selectedId])

  // Close dropdown on click outside
  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [])

  const filtered = search.trim()
    ? perfiles.filter(p =>
        p.nombre.toLowerCase().includes(search.toLowerCase()) ||
        p.dni.includes(search)
      )
    : perfiles

  function handleSelect(p: PerfilResumen) {
    setSelected(p)
    setOpen(false)
    setSearch('')
    onSelect(p)
  }

  function handleClear() {
    setSelected(null)
    setSearch('')
    onClear()
  }

  // Selected state — ficha
  if (selected) {
    const occLabels = selected.ocupaciones.map(o => o.label).join(', ')
    return (
      <div className="bg-white border border-teal-200 rounded-xl px-4 py-3 flex items-center gap-3">
        <div className="w-9 h-9 rounded-full bg-teal-100 text-teal-700 flex items-center justify-center shrink-0">
          <User className="w-4 h-4" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="text-sm font-semibold text-gray-900">{selected.nombre}</span>
            <span className="text-xs text-gray-400">DNI {selected.dni}</span>
          </div>
          <div className="flex items-center gap-2 text-xs text-gray-500">
            <span>{selected.completitud} competencias</span>
            {occLabels && <span>· {occLabels}</span>}
            {selected.estado === 'validado' ? (
              <span className="text-green-600 font-medium">● Validado</span>
            ) : (
              <span className="text-gray-400">○ Borrador</span>
            )}
          </div>
        </div>
        <button onClick={handleClear} className="text-gray-400 hover:text-gray-600 shrink-0">
          <X className="w-4 h-4" />
        </button>
      </div>
    )
  }

  // Search state
  return (
    <div ref={ref} className="relative">
      <div className="relative">
        <Search className="w-4 h-4 absolute left-3 top-2.5 text-gray-400" />
        <input
          value={search}
          onChange={e => { setSearch(e.target.value); setOpen(true) }}
          onFocus={() => setOpen(true)}
          placeholder="Buscar por nombre o DNI..."
          className="w-full border rounded-xl pl-9 pr-3 py-2 text-sm"
        />
        {loading && <Loader2 className="w-4 h-4 animate-spin absolute right-3 top-2.5 text-gray-400" />}
      </div>

      {open && !loading && (
        <div className="absolute z-20 top-full left-0 right-0 mt-1 bg-white border border-gray-200 rounded-xl shadow-lg max-h-64 overflow-y-auto">
          {filtered.length === 0 ? (
            <div className="px-4 py-3 text-sm text-gray-400 text-center">
              {search ? 'Sin resultados' : 'No hay perfiles'}
            </div>
          ) : (
            <>
              <div className="px-4 py-1.5 text-xs text-gray-400 border-b">
                {filtered.length} perfil{filtered.length !== 1 ? 'es' : ''} encontrado{filtered.length !== 1 ? 's' : ''}
              </div>
              {filtered.map(p => {
                const occLabels = p.ocupaciones.map(o => o.label).join(', ')
                return (
                  <button
                    key={p.id}
                    onClick={() => handleSelect(p)}
                    className="w-full flex items-center gap-3 px-4 py-2.5 text-left hover:bg-teal-50 transition-colors"
                  >
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium text-gray-900">{p.nombre}</span>
                        <span className="text-xs text-gray-400">DNI {p.dni}</span>
                      </div>
                      <div className="flex items-center gap-2 text-xs text-gray-500">
                        <span>{p.completitud} competencias</span>
                        {occLabels && <span>· {occLabels}</span>}
                        {p.estado === 'validado' ? (
                          <span className="text-green-600">● Validado</span>
                        ) : (
                          <span className="text-gray-400">○ Borrador</span>
                        )}
                      </div>
                    </div>
                  </button>
                )
              })}
            </>
          )}
        </div>
      )}
    </div>
  )
}
