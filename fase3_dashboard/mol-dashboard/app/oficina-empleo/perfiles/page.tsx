'use client'

import { useState, useEffect, useCallback, useRef } from 'react'
import Link from 'next/link'
import { Search, Plus, Loader2, User } from 'lucide-react'
import { OEBreadcrumb } from '@/components/oficina-empleo/OEBreadcrumb'

interface PerfilResumen {
  id: string
  nombre: string
  dni: string
  ocupaciones: { label: string }[]
  skill_count: number
  estado: string
  validado_at: string | null
  created_at: string
}

const PAGE_SIZE = 20

export default function PerfilesListPage() {
  const [perfiles, setPerfiles] = useState<PerfilResumen[]>([])
  const [loading, setLoading] = useState(true)
  const [loadingMore, setLoadingMore] = useState(false)
  const [hasMore, setHasMore] = useState(true)
  const [search, setSearch] = useState('')
  const sentinelRef = useRef<HTMLDivElement>(null)

  const mapPerfil = (p: any): PerfilResumen => ({
    id: p.id,
    nombre: p.personas?.nombre || '',
    dni: p.personas?.dni || '',
    ocupaciones: p.ocupaciones || [],
    skill_count: p.completitud || 0,
    estado: p.estado || 'borrador',
    validado_at: p.validado_at,
    created_at: p.updated_at,
  })

  const loadPerfiles = useCallback(async (offset: number, append: boolean) => {
    if (append) setLoadingMore(true)
    else setLoading(true)

    try {
      const res = await fetch(`/api/perfiles?limit=${PAGE_SIZE}&offset=${offset}`)
      const data = await res.json()
      if (Array.isArray(data)) {
        const mapped = data.map(mapPerfil)
        if (append) {
          setPerfiles(prev => [...prev, ...mapped])
        } else {
          setPerfiles(mapped)
        }
        setHasMore(mapped.length >= PAGE_SIZE)
      }
    } catch {}
    finally {
      setLoading(false)
      setLoadingMore(false)
    }
  }, [])

  useEffect(() => { loadPerfiles(0, false) }, [loadPerfiles])

  // Infinite scroll via IntersectionObserver
  useEffect(() => {
    if (!sentinelRef.current) return
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && hasMore && !loadingMore && !loading) {
          loadPerfiles(perfiles.length, true)
        }
      },
      { rootMargin: '200px' }
    )
    observer.observe(sentinelRef.current)
    return () => observer.disconnect()
  }, [hasMore, loadingMore, loading, perfiles.length, loadPerfiles])

  const filtered = search.trim()
    ? perfiles.filter(p =>
        p.nombre.toLowerCase().includes(search.toLowerCase()) ||
        (p.dni || '').includes(search)
      )
    : perfiles

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto px-4 py-6">
        <OEBreadcrumb items={[{ label: 'Perfil de Competencias' }]} />

        {/* Header */}
        <div className="flex items-center justify-between mb-5">
          <h1 className="text-xl font-bold text-gray-900">Perfiles de Competencias</h1>
          <Link
            href="/oficina-empleo/perfiles/nuevo"
            className="inline-flex items-center gap-1.5 bg-teal-600 text-white text-sm font-semibold px-4 py-2 rounded-lg hover:bg-teal-700 transition-colors"
          >
            <Plus className="w-4 h-4" /> Nuevo perfil
          </Link>
        </div>

        {/* Search */}
        <div className="relative mb-4">
          <Search className="w-4 h-4 absolute left-3 top-2.5 text-gray-400" />
          <input
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="Buscar por nombre o DNI..."
            className="w-full border rounded-lg pl-9 pr-3 py-2 text-sm"
          />
        </div>

        {/* Table */}
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          {loading ? (
            <div className="py-12 flex items-center justify-center gap-2 text-gray-400">
              <Loader2 className="w-4 h-4 animate-spin" />
              <span className="text-sm">Cargando...</span>
            </div>
          ) : filtered.length === 0 ? (
            <div className="py-12 text-center text-gray-400">
              <User className="w-8 h-8 mx-auto mb-2 opacity-30" />
              <p className="text-sm">{search ? 'Sin resultados' : 'No hay perfiles. Crea el primero.'}</p>
            </div>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-xs text-gray-500 uppercase tracking-wide border-b">
                  <th className="px-4 py-3 font-medium">Nombre</th>
                  <th className="px-4 py-3 font-medium">DNI</th>
                  <th className="px-4 py-3 font-medium text-center">Competencias</th>
                  <th className="px-4 py-3 font-medium">Estado</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {filtered.map(p => (
                  <tr key={p.id} className="hover:bg-gray-50 transition-colors">
                    <td className="px-4 py-3">
                      <Link href={`/oficina-empleo/perfiles/${p.id}`} className="text-teal-700 font-medium hover:underline">
                        {p.nombre}
                      </Link>
                      {p.ocupaciones?.length > 0 && (
                        <p className="text-xs text-gray-400 mt-0.5">
                          {p.ocupaciones.map(o => o.label).join(', ')}
                        </p>
                      )}
                    </td>
                    <td className="px-4 py-3 text-gray-600">{p.dni}</td>
                    <td className="px-4 py-3 text-center text-gray-700 font-medium">{p.skill_count}</td>
                    <td className="px-4 py-3">
                      {p.estado === 'validado' ? (
                        <span className="inline-flex items-center gap-1 text-xs font-medium text-green-700 bg-green-50 px-2 py-0.5 rounded-full">
                          <span className="w-1.5 h-1.5 rounded-full bg-green-500" />
                          Validado
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 text-xs font-medium text-gray-500 bg-gray-100 px-2 py-0.5 rounded-full">
                          <span className="w-1.5 h-1.5 rounded-full bg-gray-400" />
                          Borrador
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}

          {/* Infinite scroll sentinel */}
          {!search.trim() && hasMore && !loading && (
            <div ref={sentinelRef} className="py-4 flex items-center justify-center">
              {loadingMore && (
                <div className="flex items-center gap-2 text-gray-400">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span className="text-xs">Cargando mas...</span>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
