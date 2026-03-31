'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { ArrowRight } from 'lucide-react'
import { useS1Store, type S1Proposito } from '@/lib/use-s1-store'

const PROPOSITOS: { value: S1Proposito; label: string; emoji: string }[] = [
  { value: 'busco_trabajo', label: 'Busco trabajo', emoji: '💼' },
  { value: 'cambiar_rubro', label: 'Quiero cambiar de rubro', emoji: '🔄' },
  { value: 'saber_que_vale', label: 'Quiero saber qué vale lo que sé', emoji: '🎯' },
  { value: 'desde_oe', label: 'Me mandaron desde la Oficina de Empleo', emoji: '🏛️' },
]

export default function OnboardingPage() {
  const router = useRouter()
  const { setStore, reset } = useS1Store()
  const [nombre, setNombre] = useState('')
  const [proposito, setProposito] = useState<S1Proposito | null>(null)

  useEffect(() => { reset() }, [reset])
  const [error, setError] = useState('')

  const handleContinuar = () => {
    if (!nombre.trim()) { setError('Ingresá tu nombre para continuar.'); return }
    if (!proposito) { setError('Elegí una opción para continuar.'); return }
    setStore({ nombre: nombre.trim(), proposito })
    router.push('/mi-futuro-laboral/perfil')
  }

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4 py-12">
      <div className="w-full max-w-md">

        {/* Header */}
        <div className="text-center mb-8">
          <span className="inline-block bg-blue-100 text-blue-700 text-[10px] font-bold px-2.5 py-0.5 rounded-full uppercase tracking-wider mb-3">
            Paso 1 de 3
          </span>
          <h1 className="text-2xl font-bold text-gray-900 mb-2">¿Cómo te llamás?</h1>
          <p className="text-gray-500 text-sm">
            Lo usamos para el reporte. Nada más.
          </p>
        </div>

        <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-6 space-y-6">

          {/* Nombre */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">
              Tu nombre
            </label>
            <input
              type="text"
              value={nombre}
              onChange={(e) => { setNombre(e.target.value); setError('') }}
              onKeyDown={(e) => e.key === 'Enter' && handleContinuar()}
              placeholder="Ej: María García"
              className="w-full rounded-lg border border-gray-200 px-3 py-2.5 text-sm text-gray-900 placeholder-gray-400 focus:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-100"
              autoFocus
            />
          </div>

          {/* Propósito */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              ¿Para qué lo usás hoy?
            </label>
            <div className="space-y-2">
              {PROPOSITOS.map((p) => (
                <button
                  key={p.value}
                  onClick={() => { setProposito(p.value); setError('') }}
                  className={`w-full flex items-center gap-3 rounded-lg border px-4 py-3 text-sm transition-all text-left ${
                    proposito === p.value
                      ? 'border-blue-500 bg-blue-50 text-blue-800 font-medium'
                      : 'border-gray-200 bg-white text-gray-700 hover:border-gray-300 hover:bg-gray-50'
                  }`}
                >
                  <span className="text-lg">{p.emoji}</span>
                  {p.label}
                </button>
              ))}
            </div>
          </div>

          {proposito === 'desde_oe' && (
            <p className="text-xs text-blue-600 bg-blue-50 rounded-lg px-3 py-2">
              Tu técnico de la Oficina de Empleo puede ver tu perfil cuando lo construyas.
            </p>
          )}

          {error && (
            <p className="text-xs text-red-600">{error}</p>
          )}

          <button
            onClick={handleContinuar}
            className="w-full inline-flex items-center justify-center gap-2 bg-blue-600 text-white text-sm font-semibold px-4 py-3 rounded-xl hover:bg-blue-700 transition-colors"
          >
            Continuar
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>

        <p className="text-center text-xs text-gray-400 mt-4">
          No necesitás crear una cuenta. Podés guardar tu perfil al final.
        </p>
      </div>
    </div>
  )
}
