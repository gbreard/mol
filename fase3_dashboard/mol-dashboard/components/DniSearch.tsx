'use client'

import { useState } from 'react'
import { Search, UserCheck, UserX, Link2, X } from 'lucide-react'

export interface WorkerProfileFound {
  id: string
  nombre: string
  dni: string
  creado_at: string
  skills_count: number
  ocupaciones_count: number
  reportes_count: number
  organizacion_id?: string | null
}

type SearchState = 'idle' | 'loading' | 'found' | 'not_found'

interface Props {
  organizacionNombre?: string
  onVincular?: (profile: WorkerProfileFound) => Promise<void>
  onCrearNuevo?: () => void
}

function formatDni(raw: string): string {
  const digits = raw.replace(/\D/g, '').slice(0, 8)
  return digits.replace(/\B(?=(\d{3})+(?!\d))/g, '.')
}

export default function DniSearch({ organizacionNombre = 'tu oficina', onVincular, onCrearNuevo }: Props) {
  const [dniInput, setDniInput] = useState('')
  const [state, setState] = useState<SearchState>('idle')
  const [profile, setProfile] = useState<WorkerProfileFound | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [vinculando, setVinculando] = useState(false)
  const [vinculado, setVinculado] = useState(false)

  const dniDigits = dniInput.replace(/\D/g, '')
  const isValidDni = dniDigits.length >= 7 && dniDigits.length <= 8

  const handleSearch = async () => {
    if (!isValidDni) return
    setState('loading')
    setProfile(null)
    setError(null)
    setVinculado(false)

    try {
      const res = await fetch(`/api/worker-profiles?dni=${dniDigits}`)
      if (res.status === 404) {
        setState('not_found')
        return
      }
      if (!res.ok) throw new Error('Error al buscar el perfil')
      const data = await res.json()
      setProfile(data)
      setState('found')
    } catch {
      setError('No se pudo conectar. Intentá de nuevo.')
      setState('idle')
    }
  }

  const handleVincular = async () => {
    if (!profile) return
    setVinculando(true)
    try {
      await onVincular?.(profile)
      setVinculado(true)
    } finally {
      setVinculando(false)
    }
  }

  const handleReset = () => {
    setState('idle')
    setProfile(null)
    setDniInput('')
    setError(null)
    setVinculado(false)
  }

  return (
    <div className="space-y-4">
      {/* DNI input */}
      <div>
        <label htmlFor="dni-input" className="mb-1.5 block text-sm font-medium text-gray-700">
          DNI del trabajador/a
        </label>
        <div className="flex gap-2">
          <input
            id="dni-input"
            type="text"
            inputMode="numeric"
            value={dniInput}
            onChange={(e) => {
              setDniInput(e.target.value.replace(/\D/g, ''))
              setState('idle')
              setProfile(null)
              setError(null)
              setVinculado(false)
            }}
            onKeyDown={(e) => e.key === 'Enter' && isValidDni && handleSearch()}
            placeholder="30123456"
            maxLength={8}
            className="flex-1 rounded-lg border border-gray-300 px-3 py-2.5 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          />
          <button
            onClick={handleSearch}
            disabled={!isValidDni || state === 'loading'}
            aria-label="Buscar perfil por DNI"
            className="flex min-h-[44px] items-center gap-2 rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
          >
            <Search className="h-4 w-4" />
            {state === 'loading' ? 'Buscando...' : 'Buscar'}
          </button>
        </div>
        {error && <p className="mt-1 text-xs text-red-500">{error}</p>}
      </div>

      {/* Found */}
      {state === 'found' && profile && (
        <div className="rounded-lg border border-green-200 bg-green-50 p-4">
          <div className="mb-3 flex items-start justify-between">
            <div className="flex items-center gap-2">
              <UserCheck className="h-5 w-5 text-green-600" />
              <span className="text-sm font-semibold text-green-800">Perfil encontrado</span>
            </div>
            <button
              onClick={handleReset}
              aria-label="Cerrar resultado"
              className="text-gray-400 hover:text-gray-600"
            >
              <X className="h-4 w-4" />
            </button>
          </div>

          <dl className="mb-4 space-y-1 text-sm">
            <div className="flex gap-2">
              <dt className="w-28 shrink-0 text-gray-500">Nombre</dt>
              <dd className="font-medium text-gray-900">{profile.nombre}</dd>
            </div>
            <div className="flex gap-2">
              <dt className="w-28 shrink-0 text-gray-500">DNI</dt>
              <dd className="font-medium text-gray-900">{formatDni(profile.dni)}</dd>
            </div>
            <div className="flex gap-2">
              <dt className="w-28 shrink-0 text-gray-500">Creado</dt>
              <dd className="text-gray-700">
                {new Date(profile.creado_at).toLocaleDateString('es-AR')}
                <span className="ml-1 text-gray-400">(por el trabajador)</span>
              </dd>
            </div>
            <div className="flex gap-2">
              <dt className="w-28 shrink-0 text-gray-500">Skills</dt>
              <dd className="text-gray-700">
                {profile.skills_count} · {profile.ocupaciones_count} ocupaciones evaluadas · {profile.reportes_count} reportes
              </dd>
            </div>
          </dl>

          {vinculado ? (
            <div className="flex items-center gap-2 rounded-lg bg-green-100 px-4 py-3 text-sm font-medium text-green-800">
              <UserCheck className="h-4 w-4" />
              Perfil vinculado a {organizacionNombre}
            </div>
          ) : (
            <div className="space-y-2">
              <p className="text-xs text-gray-500">
                ¿Querés vincular este perfil a {organizacionNombre}?
                El trabajador debe aceptar verbalmente.
              </p>
              <div className="flex gap-2">
                <button
                  onClick={handleReset}
                  className="min-h-[44px] flex-1 rounded-lg border border-gray-300 px-4 py-2 text-sm text-gray-600 hover:bg-gray-50"
                >
                  Cancelar
                </button>
                <button
                  onClick={handleVincular}
                  disabled={vinculando}
                  aria-label={`Vincular a ${organizacionNombre}`}
                  className="flex min-h-[44px] flex-1 items-center justify-center gap-2 rounded-lg bg-green-600 px-4 py-2 text-sm font-medium text-white hover:bg-green-700 disabled:opacity-50"
                >
                  <Link2 className="h-4 w-4" />
                  {vinculando ? 'Vinculando...' : `Vincular a ${organizacionNombre}`}
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Not found */}
      {state === 'not_found' && (
        <div className="rounded-lg border border-gray-200 bg-gray-50 p-4">
          <div className="mb-3 flex items-center gap-2">
            <UserX className="h-5 w-5 text-gray-400" />
            <span className="text-sm font-semibold text-gray-700">
              No se encontró perfil con DNI {formatDni(dniDigits)}
            </span>
          </div>
          <button
            onClick={onCrearNuevo}
            aria-label="Crear nuevo perfil"
            className="min-h-[44px] w-full rounded-lg border border-blue-300 px-4 py-2 text-sm font-medium text-blue-600 hover:bg-blue-50"
          >
            + Crear nuevo perfil
          </button>
        </div>
      )}
    </div>
  )
}
