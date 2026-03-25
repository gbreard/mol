'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import {
  ArrowLeft, ArrowRight, CheckCircle, Lock,
  Wrench, BookOpen, Globe, Sparkles,
} from 'lucide-react'
import SkillWithDefinition, { type SkillConfidence } from '@/components/SkillWithDefinition'
import { useS1Store } from '@/lib/use-s1-store'

const NIVELES_IDIOMA: Record<string, string> = {
  basico: 'Básico',
  intermedio: 'Intermedio',
  avanzado: 'Avanzado',
  nativo: 'Nativo / Bilingüe',
}

export default function PerfilReviewPage() {
  const router = useRouter()
  const { store, updateSkill, removeSkill, removeIdioma, confirmed } = useS1Store()
  const [showGate, setShowGate] = useState(false)
  const [email, setEmail] = useState('')
  const [gateLoading, setGateLoading] = useState(false)

  const competencias = store.skills.filter((s) => s.type === 'skill')
  const conocimientos = store.skills.filter((s) => s.type === 'knowledge')
  const totalItems = store.skills.length + store.idiomas.length

  const handleVerResultados = () => {
    // Por ahora simula el gate: en producción verificaría si hay sesión
    setShowGate(true)
  }

  const handleRegistro = async () => {
    if (!email.trim()) return
    setGateLoading(true)
    // Simula registro / login
    await new Promise((r) => setTimeout(r, 800))
    router.push('/mi-futuro-laboral/resultados')
  }

  const handleSaltarRegistro = () => {
    // Permite continuar sin registro en el MVP
    router.push('/mi-futuro-laboral/resultados')
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-2xl mx-auto px-4 py-8">

        {/* Header */}
        <button
          onClick={() => router.back()}
          className="inline-flex items-center gap-1.5 text-xs text-gray-400 hover:text-gray-600 mb-4"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          Volver a captura
        </button>

        <div className="mb-6">
          <span className="inline-block bg-blue-100 text-blue-700 text-[10px] font-bold px-2.5 py-0.5 rounded-full uppercase tracking-wider mb-2">
            Paso 2 de 3 — Revisión
          </span>
          <h1 className="text-xl font-bold text-gray-900">Revisá tu perfil de competencias</h1>
          <p className="text-gray-500 text-sm mt-1">
            {totalItems} elemento{totalItems !== 1 ? 's' : ''} cargado{totalItems !== 1 ? 's' : ''} ·{' '}
            {confirmed.length} confirmado{confirmed.length !== 1 ? 's' : ''}.
            Podés ajustar antes de ver tus resultados.
          </p>
        </div>

        {totalItems === 0 ? (
          <div className="bg-white rounded-xl border border-gray-200 p-8 text-center">
            <p className="text-gray-400 text-sm mb-4">No cargaste competencias todavía.</p>
            <button
              onClick={() => router.back()}
              className="inline-flex items-center gap-2 bg-blue-600 text-white text-sm font-semibold px-4 py-2.5 rounded-xl hover:bg-blue-700 transition-colors"
            >
              <ArrowLeft className="w-4 h-4" />
              Volver a cargar competencias
            </button>
          </div>
        ) : (
          <div className="space-y-5">

            {/* Competencias */}
            {competencias.length > 0 && (
              <div className="bg-white rounded-xl border border-gray-200 p-4">
                <div className="flex items-center gap-2 mb-3">
                  <Wrench className="w-4 h-4 text-blue-500" />
                  <h2 className="text-sm font-semibold text-gray-800">
                    Competencias <span className="text-gray-400 font-normal">({competencias.length})</span>
                  </h2>
                </div>
                <div className="space-y-2">
                  {competencias.map((skill) => (
                    <SkillWithDefinition
                      key={skill.uri}
                      skill={skill}
                      onConfidenceChange={(uri, confidence: SkillConfidence) => updateSkill(uri, { confidence })}
                      onRemove={removeSkill}
                    />
                  ))}
                </div>
              </div>
            )}

            {/* Conocimientos */}
            {conocimientos.length > 0 && (
              <div className="bg-white rounded-xl border border-gray-200 p-4">
                <div className="flex items-center gap-2 mb-3">
                  <BookOpen className="w-4 h-4 text-purple-500" />
                  <h2 className="text-sm font-semibold text-gray-800">
                    Conocimientos <span className="text-gray-400 font-normal">({conocimientos.length})</span>
                  </h2>
                </div>
                <div className="space-y-2">
                  {conocimientos.map((skill) => (
                    <SkillWithDefinition
                      key={skill.uri}
                      skill={skill}
                      onConfidenceChange={(uri, confidence: SkillConfidence) => updateSkill(uri, { confidence })}
                      onRemove={removeSkill}
                    />
                  ))}
                </div>
              </div>
            )}

            {/* Idiomas */}
            {store.idiomas.length > 0 && (
              <div className="bg-white rounded-xl border border-gray-200 p-4">
                <div className="flex items-center gap-2 mb-3">
                  <Globe className="w-4 h-4 text-green-500" />
                  <h2 className="text-sm font-semibold text-gray-800">
                    Idiomas <span className="text-gray-400 font-normal">({store.idiomas.length})</span>
                  </h2>
                </div>
                <div className="space-y-2">
                  {store.idiomas.map((i) => (
                    <div key={i.label} className="flex items-center justify-between rounded-lg border border-gray-100 bg-gray-50 px-3 py-2.5">
                      <div className="flex items-center gap-2">
                        <CheckCircle className="w-4 h-4 text-green-400" />
                        <span className="text-sm font-medium text-gray-900">{i.label}</span>
                        <span className="text-xs text-gray-400">{NIVELES_IDIOMA[i.nivel]}</span>
                      </div>
                      <button
                        onClick={() => removeIdioma(i.label)}
                        className="text-xs text-gray-400 hover:text-red-500 transition-colors"
                      >
                        quitar
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Agregar más */}
            <button
              onClick={() => router.back()}
              className="w-full text-sm text-blue-600 font-medium bg-white border border-gray-200 hover:bg-blue-50 rounded-xl py-3 transition-colors"
            >
              + Agregar más competencias
            </button>

            {/* CTA ver resultados */}
            {!showGate ? (
              <div className="bg-blue-600 rounded-xl p-5 text-white">
                <div className="flex items-center gap-2 mb-2">
                  <Sparkles className="w-5 h-5 text-blue-200" />
                  <h2 className="font-bold text-base">Ver mis resultados</h2>
                </div>
                <p className="text-blue-100 text-xs mb-4">
                  Con {confirmed.length} competencias confirmadas podemos mostrarte
                  qué ocupaciones te quedan cerca, qué ofertas encajan y cómo cerrar las brechas.
                </p>
                <button
                  onClick={handleVerResultados}
                  className="w-full inline-flex items-center justify-center gap-2 bg-white text-blue-700 text-sm font-semibold px-4 py-2.5 rounded-xl hover:bg-blue-50 transition-colors"
                >
                  Ver mis resultados
                  <ArrowRight className="w-4 h-4" />
                </button>
              </div>
            ) : (
              /* Freemium gate */
              <div className="bg-white rounded-xl border-2 border-blue-200 p-5">
                <div className="flex items-center gap-2 mb-3">
                  <Lock className="w-5 h-5 text-blue-500" />
                  <h2 className="font-bold text-gray-900">Registrate para ver tus resultados</h2>
                </div>
                <p className="text-gray-500 text-xs mb-4">
                  Es gratis. Te guardamos el perfil para que no pierdas lo que cargaste
                  y podés actualizar tus competencias cuando quieras.
                </p>
                <div className="space-y-2 mb-3">
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleRegistro()}
                    placeholder="tu@email.com"
                    className="w-full rounded-lg border border-gray-200 px-3 py-2.5 text-sm focus:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-100"
                    autoFocus
                  />
                  <button
                    onClick={handleRegistro}
                    disabled={!email.trim() || gateLoading}
                    className="w-full inline-flex items-center justify-center gap-2 bg-blue-600 text-white text-sm font-semibold px-4 py-2.5 rounded-xl hover:bg-blue-700 disabled:opacity-50 transition-colors"
                  >
                    {gateLoading ? 'Creando cuenta...' : 'Crear cuenta gratis y ver resultados'}
                    <ArrowRight className="w-4 h-4" />
                  </button>
                </div>
                <button
                  onClick={handleSaltarRegistro}
                  className="w-full text-xs text-gray-400 hover:text-gray-600 py-1 transition-colors"
                >
                  Continuar sin registrarme (no podré guardar mi perfil)
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
