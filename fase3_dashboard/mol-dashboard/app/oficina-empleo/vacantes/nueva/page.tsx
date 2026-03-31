'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { ArrowLeft, Loader2, Sparkles, ChevronRight } from 'lucide-react'

interface EscoSugerencia {
  uri: string
  label: string
  isco: string
  confianza: number
}

// Mock de respuesta NLP → ESCO
const MOCK_SUGERENCIAS: EscoSugerencia[] = [
  { uri: 'esco_4120', label: 'Secretaria ejecutiva', isco: '4120', confianza: 92 },
  { uri: 'esco_4110', label: 'Empleada de oficina en general', isco: '4110', confianza: 78 },
  { uri: 'esco_4215', label: 'Recepcionista', isco: '4215', confianza: 65 },
]

export default function NuevaVacantePage() {
  const router = useRouter()
  const [paso, setPaso] = useState<'texto' | 'confirmar'>('texto')
  const [textoLibre, setTextoLibre] = useState('')
  const [analizando, setAnalizando] = useState(false)
  const [sugerencias, setSugerencias] = useState<EscoSugerencia[]>([])
  const [escoSeleccionado, setEscoSeleccionado] = useState<EscoSugerencia | null>(null)
  const [vacantes, setVacantes] = useState('1')
  const [empresa, setEmpresa] = useState('')
  const [modalidad, setModalidad] = useState('Presencial')

  const handleAnalizar = async () => {
    if (!textoLibre.trim()) return
    setAnalizando(true)
    try {
      // Llamar /api/vacantes/classify cuando exista
      await new Promise((r) => setTimeout(r, 1200))
      setSugerencias(MOCK_SUGERENCIAS)
      setPaso('confirmar')
    } finally {
      setAnalizando(false)
    }
  }

  const handleGuardar = () => {
    if (!escoSeleccionado) return
    // POST /api/vacantes con { esco_uri, esco_label, isco, descripcion_libre, empresa, vacantes, modalidad }
    router.push('/oficina-empleo/vacantes')
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-lg mx-auto px-4 py-8">

        <button
          onClick={() => paso === 'confirmar' ? setPaso('texto') : router.back()}
          className="flex items-center gap-1.5 text-sm text-gray-500 hover:text-gray-700 mb-6 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          {paso === 'confirmar' ? 'Volver al texto' : 'Vacantes'}
        </button>

        <div className="mb-6">
          <h1 className="text-xl font-bold text-gray-900">Nueva vacante</h1>
          <p className="text-gray-500 text-sm mt-1">
            {paso === 'texto'
              ? 'Describí la vacante con tus palabras. El sistema la clasifica automáticamente en ESCO.'
              : 'Confirmá la clasificación ESCO y completá los datos.'}
          </p>
        </div>

        {paso === 'texto' ? (
          <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-6 space-y-5">
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1.5">
                Descripción de la vacante (texto libre)
              </label>
              <textarea
                value={textoLibre}
                onChange={(e) => setTextoLibre(e.target.value)}
                rows={6}
                placeholder={'Ej: Buscamos secretaria con experiencia en atención telefónica, manejo de agenda y office. Horario de 9 a 17hs. Zona Microcentro CABA.'}
                className="w-full rounded-lg border border-gray-200 px-3 py-2.5 text-sm text-gray-900 placeholder-gray-400 focus:border-teal-400 focus:outline-none focus:ring-2 focus:ring-teal-100 resize-none"
              />
              <p className="text-[10px] text-gray-400 mt-1">
                Incluí título, tareas principales, zona y modalidad si sabés.
              </p>
            </div>

            <button
              onClick={handleAnalizar}
              disabled={analizando || !textoLibre.trim()}
              className="w-full inline-flex items-center justify-center gap-2 bg-teal-600 text-white text-sm font-semibold px-4 py-3 rounded-xl hover:bg-teal-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {analizando ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Clasificando con IA...
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4" />
                  Clasificar automáticamente
                </>
              )}
            </button>
          </div>
        ) : (
          <div className="space-y-4">
            {/* Sugerencias ESCO */}
            <div className="bg-white rounded-xl border border-gray-200 p-4">
              <p className="text-xs font-semibold text-gray-700 mb-3">
                Clasificación ESCO sugerida — elegí la más precisa:
              </p>
              <div className="space-y-2">
                {sugerencias.map((s) => (
                  <button
                    key={s.uri}
                    onClick={() => setEscoSeleccionado(s)}
                    className={`w-full flex items-center justify-between gap-3 rounded-xl border px-4 py-3 text-left transition-all ${
                      escoSeleccionado?.uri === s.uri
                        ? 'border-teal-500 bg-teal-50'
                        : 'border-gray-200 bg-white hover:border-gray-300'
                    }`}
                  >
                    <div>
                      <p className="text-sm font-medium text-gray-800">{s.label}</p>
                      <p className="text-xs text-gray-400 font-mono mt-0.5">{s.isco}</p>
                    </div>
                    <span className={`text-xs font-bold shrink-0 ${s.confianza >= 85 ? 'text-green-600' : s.confianza >= 70 ? 'text-blue-600' : 'text-yellow-600'}`}>
                      {s.confianza}%
                    </span>
                  </button>
                ))}
              </div>
            </div>

            {/* Datos adicionales */}
            <div className="bg-white rounded-xl border border-gray-200 p-4 space-y-4">
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1.5">Empresa</label>
                <input
                  type="text"
                  value={empresa}
                  onChange={(e) => setEmpresa(e.target.value)}
                  placeholder="Nombre de la empresa"
                  className="w-full rounded-lg border border-gray-200 px-3 py-2.5 text-sm focus:border-teal-400 focus:outline-none focus:ring-2 focus:ring-teal-100"
                />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-gray-700 mb-1.5">Vacantes</label>
                  <input
                    type="number"
                    value={vacantes}
                    onChange={(e) => setVacantes(e.target.value)}
                    min={1}
                    className="w-full rounded-lg border border-gray-200 px-3 py-2.5 text-sm focus:border-teal-400 focus:outline-none focus:ring-2 focus:ring-teal-100"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-700 mb-1.5">Modalidad</label>
                  <select
                    value={modalidad}
                    onChange={(e) => setModalidad(e.target.value)}
                    className="w-full rounded-lg border border-gray-200 px-3 py-2.5 text-sm focus:border-teal-400 focus:outline-none focus:ring-2 focus:ring-teal-100"
                  >
                    <option>Presencial</option>
                    <option>Híbrido</option>
                    <option>Remoto</option>
                  </select>
                </div>
              </div>
            </div>

            <button
              onClick={handleGuardar}
              disabled={!escoSeleccionado}
              className="w-full inline-flex items-center justify-center gap-2 bg-teal-600 text-white text-sm font-semibold px-4 py-3 rounded-xl hover:bg-teal-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              Guardar vacante
              <ChevronRight className="w-4 h-4" />
            </button>

            {!escoSeleccionado && (
              <p className="text-center text-xs text-gray-400">
                Seleccioná una clasificación ESCO para continuar.
              </p>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
