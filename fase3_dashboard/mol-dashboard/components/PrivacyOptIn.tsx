'use client'

import { useState } from 'react'
import { Shield, Eye, EyeOff, Check } from 'lucide-react'

const PROVINCIAS = [
  'Buenos Aires',
  'CABA',
  'Catamarca',
  'Chaco',
  'Chubut',
  'Córdoba',
  'Corrientes',
  'Entre Ríos',
  'Formosa',
  'Jujuy',
  'La Pampa',
  'La Rioja',
  'Mendoza',
  'Misiones',
  'Neuquén',
  'Río Negro',
  'Salta',
  'San Juan',
  'San Luis',
  'Santa Cruz',
  'Santa Fe',
  'Santiago del Estero',
  'Tierra del Fuego',
  'Tucumán',
]

export type AlcanceOpt = 'privado' | 'provincial' | 'nacional'

export interface PrivacyOptInValue {
  alcance: AlcanceOpt
  provincia: string | null
}

interface Props {
  initial?: PrivacyOptInValue
  onSave?: (value: PrivacyOptInValue) => Promise<void>
}

export default function PrivacyOptIn({ initial, onSave }: Props) {
  const [visible, setVisible] = useState<boolean>(
    initial ? initial.alcance !== 'privado' : false
  )
  const [alcance, setAlcance] = useState<'provincial' | 'nacional'>(
    initial?.alcance === 'provincial' ? 'provincial' : 'nacional'
  )
  const [provincia, setProvincia] = useState<string>(
    initial?.provincia ?? 'Buenos Aires'
  )
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)

  const handleSave = async () => {
    setSaving(true)
    setSaved(false)
    const value: PrivacyOptInValue = {
      alcance: visible ? alcance : 'privado',
      provincia: visible && alcance === 'provincial' ? provincia : null,
    }
    try {
      await onSave?.(value)
    } finally {
      setSaving(false)
      setSaved(true)
      setTimeout(() => setSaved(false), 3000)
    }
  }

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-6">
      <div className="mb-4 flex items-center gap-2">
        <Shield className="h-5 w-5 text-blue-500" />
        <h2 className="text-base font-semibold text-gray-800">
          Visibilidad en búsquedas
        </h2>
      </div>

      <p className="mb-4 text-sm text-gray-600">
        ¿Querés que oficinas de empleo y empresas puedan encontrar tu perfil?
      </p>

      {/* Toggle */}
      <button
        role="switch"
        aria-checked={visible}
        aria-label="Activar visibilidad del perfil"
        onClick={() => setVisible(!visible)}
        className={`mb-4 flex min-h-[44px] w-full items-center gap-3 rounded-lg border px-4 py-3 text-left transition-colors ${
          visible
            ? 'border-blue-200 bg-blue-50'
            : 'border-gray-200 bg-gray-50'
        }`}
      >
        <span
          className={`flex h-6 w-11 shrink-0 items-center rounded-full transition-colors ${
            visible ? 'bg-blue-600' : 'bg-gray-300'
          }`}
        >
          <span
            className={`h-5 w-5 rounded-full bg-white shadow transition-transform ${
              visible ? 'translate-x-5' : 'translate-x-0.5'
            }`}
          />
        </span>
        <span className="flex items-center gap-2 text-sm font-medium text-gray-700">
          {visible ? (
            <>
              <Eye className="h-4 w-4 text-blue-500" />
              Perfil visible (anonimizado)
            </>
          ) : (
            <>
              <EyeOff className="h-4 w-4 text-gray-400" />
              No, mantener privado
            </>
          )}
        </span>
      </button>

      {/* Explanation — always shown */}
      <div className="mb-4 rounded-lg bg-gray-50 px-4 py-3 text-xs text-gray-500">
        Al activar, tu perfil aparece <strong>anonimizado</strong>: solo ven tus
        skills y compatibilidad. Tu nombre y datos se revelan únicamente si vos
        aceptás el contacto.
      </div>

      {/* Alcance — visible only when visible=true */}
      {visible && (
        <fieldset className="mb-4 space-y-2">
          <legend className="mb-2 text-sm font-medium text-gray-700">
            ¿Dónde querés aparecer?
          </legend>

          <label className="flex min-h-[44px] cursor-pointer items-center gap-3 rounded-lg border border-gray-200 px-4 py-2 hover:bg-gray-50">
            <input
              type="radio"
              name="alcance"
              value="provincial"
              checked={alcance === 'provincial'}
              onChange={() => setAlcance('provincial')}
              className="h-4 w-4 text-blue-600"
            />
            <span className="text-sm text-gray-700">Solo en mi provincia</span>
          </label>

          {alcance === 'provincial' && (
            <div className="ml-7">
              <select
                value={provincia}
                onChange={(e) => setProvincia(e.target.value)}
                aria-label="Seleccionar provincia"
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
              >
                {PROVINCIAS.map((p) => (
                  <option key={p} value={p}>
                    {p}
                  </option>
                ))}
              </select>
            </div>
          )}

          <label className="flex min-h-[44px] cursor-pointer items-center gap-3 rounded-lg border border-gray-200 px-4 py-2 hover:bg-gray-50">
            <input
              type="radio"
              name="alcance"
              value="nacional"
              checked={alcance === 'nacional'}
              onChange={() => setAlcance('nacional')}
              className="h-4 w-4 text-blue-600"
            />
            <span className="text-sm text-gray-700">En todo el país</span>
          </label>
        </fieldset>
      )}

      <button
        onClick={handleSave}
        disabled={saving}
        className="flex min-h-[44px] w-full items-center justify-center gap-2 rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
      >
        {saved ? (
          <>
            <Check className="h-4 w-4" />
            Preferencia guardada
          </>
        ) : saving ? (
          'Guardando...'
        ) : (
          'Guardar preferencia'
        )}
      </button>
    </div>
  )
}
