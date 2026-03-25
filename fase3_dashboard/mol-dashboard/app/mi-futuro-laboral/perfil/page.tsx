'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import {
  Briefcase, Search, FileText, GraduationCap,
  Languages, ArrowRight, X, CheckCircle, ChevronRight,
} from 'lucide-react'
import SkillSearchByTask from '@/components/SkillSearchByTask'
import FreeTextSkillExtractor from '@/components/FreeTextSkillExtractor'
import FormacionSearch from '@/components/FormacionSearch'
import SkillWithDefinition, { type SkillItem, type SkillConfidence } from '@/components/SkillWithDefinition'
import { useS1Store, type S1Idioma } from '@/lib/use-s1-store'
import OcupacionSkillsVia from '@/components/s1/OcupacionSkillsVia'

type Via = 'ocupacion' | 'tarea' | 'texto' | 'formacion' | 'idiomas'

const VIAS: { id: Via; label: string; labelCorto: string; icon: typeof Briefcase; desc: string }[] = [
  {
    id: 'ocupacion',
    label: 'Por ocupación',
    labelCorto: 'Ocupación',
    icon: Briefcase,
    desc: 'Buscá en qué trabajás y el sistema carga las competencias del rol automáticamente.',
  },
  {
    id: 'tarea',
    label: 'Por skill o tarea',
    labelCorto: 'Skill',
    icon: Search,
    desc: 'Buscá competencias por nombre: "soldadura", "Excel", "atención al cliente", etc.',
  },
  {
    id: 'texto',
    label: 'Con tus palabras',
    labelCorto: 'Texto',
    icon: FileText,
    desc: 'Contá tu experiencia laboral como quieras y el sistema identifica las competencias.',
  },
  {
    id: 'formacion',
    label: 'Por título o curso',
    labelCorto: 'Formación',
    icon: GraduationCap,
    desc: 'Cargá un título, tecnicatura o certificación y el sistema mapea las competencias.',
  },
  {
    id: 'idiomas',
    label: 'Idiomas',
    labelCorto: 'Idiomas',
    icon: Languages,
    desc: 'Agregá los idiomas que hablás con tu nivel.',
  },
]

const NIVELES_IDIOMA: { value: S1Idioma['nivel']; label: string }[] = [
  { value: 'basico', label: 'Básico' },
  { value: 'intermedio', label: 'Intermedio' },
  { value: 'avanzado', label: 'Avanzado' },
  { value: 'nativo', label: 'Nativo / Bilingüe' },
]

const IDIOMAS_COMUNES = ['Inglés', 'Portugués', 'Francés', 'Italiano', 'Alemán', 'Chino (Mandarín)', 'Árabe']

function IdiomasVia({
  idiomas,
  onAdd,
  onRemove,
}: {
  idiomas: S1Idioma[]
  onAdd: (i: S1Idioma) => void
  onRemove: (label: string) => void
}) {
  const [idioma, setIdioma] = useState('')
  const [nivel, setNivel] = useState<S1Idioma['nivel']>('intermedio')
  const [custom, setCustom] = useState('')

  const handleAdd = () => {
    const label = idioma === '__custom__' ? custom.trim() : idioma
    if (!label) return
    onAdd({ label, nivel })
    setIdioma('')
    setCustom('')
  }

  return (
    <div className="space-y-4">
      {/* Agregar idioma */}
      <div className="space-y-2">
        <div className="grid grid-cols-2 gap-2">
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Idioma</label>
            <select
              value={idioma}
              onChange={(e) => setIdioma(e.target.value)}
              className="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm text-gray-900 focus:border-blue-400 focus:outline-none"
            >
              <option value="">Seleccioná...</option>
              {IDIOMAS_COMUNES.filter((i) => !idiomas.some((a) => a.label === i)).map((i) => (
                <option key={i} value={i}>{i}</option>
              ))}
              <option value="__custom__">Otro...</option>
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Nivel</label>
            <select
              value={nivel}
              onChange={(e) => setNivel(e.target.value as S1Idioma['nivel'])}
              className="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm text-gray-900 focus:border-blue-400 focus:outline-none"
            >
              {NIVELES_IDIOMA.map((n) => (
                <option key={n.value} value={n.value}>{n.label}</option>
              ))}
            </select>
          </div>
        </div>

        {idioma === '__custom__' && (
          <input
            type="text"
            value={custom}
            onChange={(e) => setCustom(e.target.value)}
            placeholder="Nombre del idioma..."
            className="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm focus:border-blue-400 focus:outline-none"
            autoFocus
          />
        )}

        <button
          onClick={handleAdd}
          disabled={!idioma || (idioma === '__custom__' && !custom.trim())}
          className="w-full inline-flex items-center justify-center gap-2 bg-blue-600 text-white text-sm font-medium px-4 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          + Agregar idioma
        </button>
      </div>

      {/* Idiomas agregados */}
      {idiomas.length > 0 && (
        <div className="space-y-2">
          {idiomas.map((i) => (
            <div key={i.label} className="flex items-center justify-between rounded-lg border border-gray-200 bg-white px-3 py-2">
              <div>
                <span className="text-sm font-medium text-gray-900">{i.label}</span>
                <span className="ml-2 text-xs text-gray-400">
                  {NIVELES_IDIOMA.find((n) => n.value === i.nivel)?.label}
                </span>
              </div>
              <button
                onClick={() => onRemove(i.label)}
                className="text-gray-300 hover:text-red-400 transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          ))}
        </div>
      )}

      {idiomas.length === 0 && (
        <p className="text-xs text-gray-400 text-center py-4">
          Todavía no agregaste idiomas.
        </p>
      )}
    </div>
  )
}

// ─── Panel acumulador ──────────────────────────────────────────────────────────

function SkillGroup({
  titulo,
  emoji,
  skills,
  onConfidenceChange,
  onRemove,
}: {
  titulo: string
  emoji: string
  skills: SkillItem[]
  onConfidenceChange: (uri: string, conf: SkillConfidence) => void
  onRemove: (uri: string) => void
}) {
  if (skills.length === 0) return null
  return (
    <div>
      <p className="text-[10px] font-bold uppercase tracking-widest text-gray-400 mb-1.5">
        {emoji} {titulo} ({skills.length})
      </p>
      <div className="space-y-1.5">
        {skills.map((skill) => (
          <SkillWithDefinition
            key={skill.uri}
            skill={skill}
            onConfidenceChange={onConfidenceChange}
            onRemove={onRemove}
          />
        ))}
      </div>
    </div>
  )
}

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function PerfilPage() {
  const router = useRouter()
  const { store, addSkills, updateSkill, removeSkill, addIdioma, removeIdioma, confirmed } = useS1Store()
  const [viaActiva, setViaActiva] = useState<Via>('ocupacion')

  const existingUris = new Set(store.skills.map((s) => s.uri))

  const handleSkillsFromVia = (skills: SkillItem[]) => addSkills(skills)

  const handleFormacion = (result: { skills_derivadas: string[] }) => {
    const nuevas: SkillItem[] = result.skills_derivadas.map((label, i) => ({
      uri: `formacion_${Date.now()}_${i}`,
      label,
      type: 'knowledge' as const,
      description: `Competencia derivada de tu formación.`,
      source: 'esco' as const,
      confidence: 'confirmed' as SkillConfidence,
      via: 'formacion' as const,
    }))
    addSkills(nuevas)
  }

  const totalItems = store.skills.length + store.idiomas.length
  const confirmedCount = confirmed.length
  const pct = Math.min(100, Math.round((confirmedCount / 5) * 100))
  const listo = confirmedCount >= 3

  // Agrupar skills por type ESCO
  const competencias = store.skills.filter((s) => s.type === 'skill')
  const conocimientos = store.skills.filter((s) => s.type === 'knowledge')

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-5xl mx-auto px-4 py-8">

        {/* Header */}
        <div className="mb-6">
          <span className="inline-block bg-blue-100 text-blue-700 text-[10px] font-bold px-2.5 py-0.5 rounded-full uppercase tracking-wider mb-2">
            Paso 2 de 3
          </span>
          <h1 className="text-2xl font-bold text-gray-900">
            {store.nombre ? `${store.nombre.split(' ')[0]}, ` : ''}agregá tus competencias
          </h1>
          <p className="text-gray-500 text-sm mt-1">
            Usá la forma que te resulte más fácil. Podés combinar varias.
          </p>
        </div>

        <div className="flex flex-col lg:flex-row gap-6">

          {/* Panel izquierdo — vías de captura */}
          <div className="flex-1 min-w-0">

            {/* Tabs de vías */}
            <div className="flex gap-1 bg-white border border-gray-200 rounded-xl p-1 mb-3 overflow-x-auto">
              {VIAS.map((v) => (
                <button
                  key={v.id}
                  onClick={() => setViaActiva(v.id)}
                  className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-medium whitespace-nowrap transition-all ${
                    viaActiva === v.id
                      ? 'bg-blue-600 text-white shadow-sm'
                      : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'
                  }`}
                >
                  <v.icon className="w-3.5 h-3.5 shrink-0" />
                  <span className="hidden sm:inline">{v.label}</span>
                  <span className="sm:hidden">{v.labelCorto}</span>
                </button>
              ))}
            </div>

            {/* Descripción de la vía */}
            <p className="text-xs text-gray-400 mb-3">
              {VIAS.find((v) => v.id === viaActiva)?.desc}
            </p>

            {/* Contenido de cada vía */}
            <div className="bg-white rounded-xl border border-gray-200 p-4">
              {viaActiva === 'ocupacion' && (
                <OcupacionSkillsVia
                  onSkillsFound={handleSkillsFromVia}
                  existingUris={existingUris}
                />
              )}
              {viaActiva === 'tarea' && (
                <SkillSearchByTask
                  onSkillsChange={(skills) => handleSkillsFromVia(
                    skills.map((s) => ({ ...s, via: 'tarea' as const }))
                  )}
                  hideList
                  existingUris={existingUris}
                />
              )}
              {viaActiva === 'texto' && (
                <FreeTextSkillExtractor
                  onSkillsAdded={(skills) => handleSkillsFromVia(
                    skills.map((s) => ({ ...s, via: 'texto' as const }))
                  )}
                />
              )}
              {viaActiva === 'formacion' && (
                <FormacionSearch onAgregar={handleFormacion} />
              )}
              {viaActiva === 'idiomas' && (
                <IdiomasVia
                  idiomas={store.idiomas}
                  onAdd={addIdioma}
                  onRemove={removeIdioma}
                />
              )}
            </div>
          </div>

          {/* Panel derecho — acumulador */}
          <div className="w-full lg:w-80 shrink-0">
            <div className="bg-white rounded-xl border border-gray-200 p-4 sticky top-4">

              {/* Completitud */}
              <div className="mb-4">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs font-medium text-gray-700">Confirmadas</span>
                  <span className={`text-xs font-bold ${listo ? 'text-green-600' : 'text-blue-600'}`}>
                    {confirmedCount} {listo ? '✓ listo' : `/ 3 mínimo`}
                  </span>
                </div>
                <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all ${listo ? 'bg-green-500' : 'bg-blue-500'}`}
                    style={{ width: `${pct}%` }}
                  />
                </div>
              </div>

              {/* Skills agrupadas */}
              {totalItems === 0 ? (
                <div className="py-8 text-center">
                  <p className="text-xs text-gray-400">
                    Usá las vías de la izquierda para agregar competencias.
                  </p>
                </div>
              ) : (
                <div className="space-y-4 max-h-[420px] overflow-y-auto pr-1">
                  <SkillGroup
                    titulo="Competencias"
                    emoji="🛠"
                    skills={competencias}
                    onConfidenceChange={(uri, conf) => updateSkill(uri, { confidence: conf })}
                    onRemove={removeSkill}
                  />
                  <SkillGroup
                    titulo="Conocimientos"
                    emoji="📚"
                    skills={conocimientos}
                    onConfidenceChange={(uri, conf) => updateSkill(uri, { confidence: conf })}
                    onRemove={removeSkill}
                  />

                  {/* Idiomas */}
                  {store.idiomas.length > 0 && (
                    <div>
                      <p className="text-[10px] font-bold uppercase tracking-widest text-gray-400 mb-1.5">
                        🌐 Idiomas ({store.idiomas.length})
                      </p>
                      <div className="space-y-1.5">
                        {store.idiomas.map((i) => (
                          <div key={i.label} className="flex items-center justify-between rounded-lg border border-gray-100 bg-gray-50 px-3 py-2">
                            <div>
                              <span className="text-sm font-medium text-gray-900">{i.label}</span>
                              <span className="ml-2 text-xs text-gray-400">
                                {NIVELES_IDIOMA.find((n) => n.value === i.nivel)?.label}
                              </span>
                            </div>
                            <button onClick={() => removeIdioma(i.label)} className="text-gray-300 hover:text-red-400">
                              <X className="w-3.5 h-3.5" />
                            </button>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* CTA */}
              <div className="mt-4 pt-4 border-t border-gray-100">
                {listo ? (
                  <button
                    onClick={() => router.push('/mi-futuro-laboral/perfil/review')}
                    className="w-full inline-flex items-center justify-center gap-2 bg-green-600 text-white text-sm font-semibold px-4 py-2.5 rounded-xl hover:bg-green-700 transition-colors"
                  >
                    <CheckCircle className="w-4 h-4" />
                    Revisar mi perfil
                    <ArrowRight className="w-4 h-4" />
                  </button>
                ) : (
                  <p className="text-center text-xs text-gray-400">
                    Confirmá al menos {3 - confirmedCount} competencia
                    {3 - confirmedCount !== 1 ? 's' : ''} más para continuar.
                  </p>
                )}
              </div>

              {/* Tip */}
              {totalItems === 0 && (
                <p className="text-center text-[10px] text-gray-300 mt-2">
                  Tip: empezá por "Por ocupación" si sabés en qué trabajás
                </p>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
