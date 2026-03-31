'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { Loader2, Sparkles, ChevronRight, Plus, X } from 'lucide-react'

interface EscoSugerencia {
  isco: string
  label: string
  confianza: number
  skills: string[]
}

const MOCK_SUGERENCIAS: EscoSugerencia[] = [
  {
    isco: '2512',
    label: 'Desarrollador de software',
    confianza: 94,
    skills: ['Programación', 'React', 'TypeScript', 'APIs REST', 'Testing'],
  },
  {
    isco: '2513',
    label: 'Desarrollador web',
    confianza: 72,
    skills: ['HTML/CSS', 'JavaScript', 'UX', 'SEO', 'CMS'],
  },
]

export default function NuevoPuestoPage() {
  const router = useRouter()
  const [paso, setPaso] = useState<'descripcion' | 'clasificacion' | 'detalles'>('descripcion')
  const [descripcion, setDescripcion] = useState('')
  const [loading, setLoading] = useState(false)
  const [sugerencias, setSugerencias] = useState<EscoSugerencia[]>([])
  const [seleccionado, setSeleccionado] = useState<EscoSugerencia | null>(null)
  const [titulo, setTitulo] = useState('')
  const [skillsExtra, setSkillsExtra] = useState<string[]>([])
  const [skillInput, setSkillInput] = useState('')

  const handleClasificar = async () => {
    if (!descripcion.trim()) return
    setLoading(true)
    await new Promise((r) => setTimeout(r, 1200))
    setSugerencias(MOCK_SUGERENCIAS)
    setLoading(false)
    setPaso('clasificacion')
  }

  const handleSeleccionar = (s: EscoSugerencia) => {
    setSeleccionado(s)
    setTitulo(s.label)
    setPaso('detalles')
  }

  const addSkill = () => {
    const s = skillInput.trim()
    if (s && !skillsExtra.includes(s)) {
      setSkillsExtra([...skillsExtra, s])
    }
    setSkillInput('')
  }

  const handlePublicar = async () => {
    setLoading(true)
    await new Promise((r) => setTimeout(r, 800))
    router.push('/empresas/puestos')
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-2xl mx-auto px-4 py-8">

        {/* Header */}
        <div className="mb-6">
          <div className="flex items-center gap-2 text-xs text-gray-400 mb-3">
            <button onClick={() => router.push('/empresas/puestos')} className="hover:text-gray-600">Mis puestos</button>
            <ChevronRight className="w-3 h-3" />
            <span className="text-gray-600">Nuevo puesto</span>
          </div>
          <h1 className="text-xl font-bold text-gray-900">Nuevo perfil de puesto</h1>
          <p className="text-sm text-gray-500 mt-1">
            Describí el puesto y el sistema identifica las competencias ESCO automáticamente.
          </p>
        </div>

        {/* Steps indicator */}
        <div className="flex items-center gap-2 mb-6">
          {(['descripcion', 'clasificacion', 'detalles'] as const).map((s, i) => (
            <div key={s} className="flex items-center gap-2">
              <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${
                paso === s ? 'bg-indigo-600 text-white' :
                (['descripcion', 'clasificacion', 'detalles'].indexOf(paso) > i)
                  ? 'bg-green-500 text-white' : 'bg-gray-200 text-gray-500'
              }`}>
                {i + 1}
              </div>
              <span className={`text-xs ${paso === s ? 'text-indigo-600 font-medium' : 'text-gray-400'}`}>
                {s === 'descripcion' ? 'Descripción' : s === 'clasificacion' ? 'Clasificación' : 'Detalles'}
              </span>
              {i < 2 && <div className="w-6 h-px bg-gray-200" />}
            </div>
          ))}
        </div>

        {/* Paso 1: Descripción */}
        {paso === 'descripcion' && (
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Describí el puesto con tus palabras
            </label>
            <textarea
              value={descripcion}
              onChange={(e) => setDescripcion(e.target.value)}
              placeholder="Ej: Necesitamos un desarrollador con experiencia en React y TypeScript para el equipo de frontend. Debe saber trabajar con APIs REST, manejar estado con Redux y hacer code reviews..."
              className="w-full rounded-lg border border-gray-200 p-3 text-sm text-gray-900 placeholder-gray-400 focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-100 resize-none"
              rows={6}
              autoFocus
            />
            <p className="text-xs text-gray-400 mt-1">{descripcion.length} caracteres</p>

            <div className="mt-4 flex items-center gap-2 bg-indigo-50 border border-indigo-100 rounded-lg px-3 py-2">
              <Sparkles className="w-4 h-4 text-indigo-500 shrink-0" />
              <p className="text-xs text-indigo-700">
                El sistema detecta automáticamente las competencias ESCO del puesto.
              </p>
            </div>

            <button
              onClick={handleClasificar}
              disabled={descripcion.trim().length < 30 || loading}
              className="mt-4 w-full inline-flex items-center justify-center gap-2 bg-indigo-600 text-white text-sm font-semibold px-4 py-2.5 rounded-xl hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {loading ? (
                <><Loader2 className="w-4 h-4 animate-spin" />Clasificando...</>
              ) : (
                <>Clasificar con ESCO <Sparkles className="w-4 h-4" /></>
              )}
            </button>
          </div>
        )}

        {/* Paso 2: Clasificación */}
        {paso === 'clasificacion' && (
          <div className="space-y-3">
            <div className="bg-indigo-50 border border-indigo-100 rounded-xl px-4 py-3 mb-2">
              <p className="text-xs text-indigo-700 font-medium">
                Encontramos {sugerencias.length} categorías ESCO para tu puesto. Seleccioná la que mejor encaje.
              </p>
            </div>
            {sugerencias.map((s) => (
              <button
                key={s.isco}
                onClick={() => handleSeleccionar(s)}
                className="w-full text-left bg-white rounded-xl border border-gray-200 p-4 hover:border-indigo-400 hover:shadow-sm transition-all"
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-sm font-semibold text-gray-900">{s.label}</span>
                      <span className="text-[10px] font-mono text-gray-400 bg-gray-100 px-1.5 py-0.5 rounded">
                        ISCO {s.isco}
                      </span>
                    </div>
                    <div className="flex flex-wrap gap-1.5 mt-2">
                      {s.skills.map((sk) => (
                        <span key={sk} className="text-[10px] bg-indigo-50 text-indigo-700 px-2 py-0.5 rounded font-medium">
                          {sk}
                        </span>
                      ))}
                    </div>
                  </div>
                  <div className="text-right shrink-0">
                    <span className={`text-lg font-bold ${s.confianza >= 85 ? 'text-green-600' : 'text-blue-600'}`}>
                      {s.confianza}%
                    </span>
                    <p className="text-[10px] text-gray-400">confianza</p>
                  </div>
                </div>
              </button>
            ))}
            <button
              onClick={() => setPaso('descripcion')}
              className="text-xs text-gray-400 hover:text-gray-600 mt-1"
            >
              ← Volver y editar descripción
            </button>
          </div>
        )}

        {/* Paso 3: Detalles */}
        {paso === 'detalles' && seleccionado && (
          <div className="bg-white rounded-xl border border-gray-200 p-6 space-y-4">
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">Título del puesto</label>
              <input
                type="text"
                value={titulo}
                onChange={(e) => setTitulo(e.target.value)}
                className="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm text-gray-900 focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-100"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-gray-700 mb-2">
                Competencias detectadas
              </label>
              <div className="flex flex-wrap gap-1.5 mb-3">
                {seleccionado.skills.map((sk) => (
                  <span key={sk} className="text-xs bg-indigo-100 text-indigo-700 px-2.5 py-1 rounded-full font-medium">
                    {sk}
                  </span>
                ))}
                {skillsExtra.map((sk) => (
                  <span key={sk} className="flex items-center gap-1 text-xs bg-green-100 text-green-700 px-2.5 py-1 rounded-full font-medium">
                    {sk}
                    <button onClick={() => setSkillsExtra(skillsExtra.filter((s) => s !== sk))}>
                      <X className="w-3 h-3" />
                    </button>
                  </span>
                ))}
              </div>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={skillInput}
                  onChange={(e) => setSkillInput(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && addSkill()}
                  placeholder="Agregar competencia adicional..."
                  className="flex-1 rounded-lg border border-gray-200 px-3 py-1.5 text-xs focus:border-indigo-400 focus:outline-none"
                />
                <button
                  onClick={addSkill}
                  className="inline-flex items-center gap-1 bg-indigo-50 text-indigo-700 text-xs font-medium px-3 py-1.5 rounded-lg hover:bg-indigo-100 transition-colors"
                >
                  <Plus className="w-3.5 h-3.5" />
                  Agregar
                </button>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">Modalidad</label>
                <select className="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm text-gray-900 focus:border-indigo-400 focus:outline-none">
                  <option>Presencial</option>
                  <option>Híbrido</option>
                  <option>Remoto</option>
                </select>
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">Seniority</label>
                <select className="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm text-gray-900 focus:border-indigo-400 focus:outline-none">
                  <option>Junior</option>
                  <option>Semi-senior</option>
                  <option>Senior</option>
                </select>
              </div>
            </div>

            <button
              onClick={handlePublicar}
              disabled={!titulo.trim() || loading}
              className="w-full inline-flex items-center justify-center gap-2 bg-indigo-600 text-white text-sm font-semibold px-4 py-2.5 rounded-xl hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {loading ? (
                <><Loader2 className="w-4 h-4 animate-spin" />Publicando...</>
              ) : (
                'Publicar puesto'
              )}
            </button>

            <button
              onClick={() => setPaso('clasificacion')}
              className="w-full text-xs text-gray-400 hover:text-gray-600 py-1"
            >
              ← Cambiar clasificación ESCO
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
