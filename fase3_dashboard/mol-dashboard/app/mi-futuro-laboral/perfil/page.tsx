'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { Briefcase, Search, FileText, GraduationCap, ArrowRight, X, CheckCircle } from 'lucide-react'
import SkillSearchByTask from '@/components/SkillSearchByTask'
import FreeTextSkillExtractor from '@/components/FreeTextSkillExtractor'
import FormacionSearch from '@/components/FormacionSearch'
import SkillWithDefinition, { type SkillItem, type SkillConfidence } from '@/components/SkillWithDefinition'
import { useS1Store } from '@/lib/use-s1-store'
import OcupacionSkillsVia from '@/components/s1/OcupacionSkillsVia'

type Via = 'ocupacion' | 'tarea' | 'texto' | 'formacion'

const VIAS: { id: Via; label: string; labelCorto: string; icon: typeof Briefcase; desc: string }[] = [
  {
    id: 'ocupacion',
    label: 'Por ocupación',
    labelCorto: 'Ocupación',
    icon: Briefcase,
    desc: 'Decinos en qué trabajás y el sistema extrae las competencias del rol.',
  },
  {
    id: 'tarea',
    label: 'Por tarea o skill',
    labelCorto: 'Tarea',
    icon: Search,
    desc: 'Buscá competencias por nombre: "atención al cliente", "Excel", etc.',
  },
  {
    id: 'texto',
    label: 'Contalo con tus palabras',
    labelCorto: 'Texto libre',
    icon: FileText,
    desc: 'Escribí tu experiencia como quieras y el sistema identifica las competencias.',
  },
  {
    id: 'formacion',
    label: 'Por título o curso',
    labelCorto: 'Formación',
    icon: GraduationCap,
    desc: 'Cargá un título o certificación y el sistema mapea las competencias que implica.',
  },
]

export default function PerfilPage() {
  const router = useRouter()
  const { store, addSkills, updateSkill, removeSkill, confirmed } = useS1Store()
  const [viaActiva, setViaActiva] = useState<Via>('ocupacion')

  const existingUris = new Set(store.skills.map((s) => s.uri))

  const handleSkillsFromVia = (skills: SkillItem[]) => {
    addSkills(skills)
  }

  const handleFormacion = (result: { skills_derivadas: string[] }) => {
    const nuevas: SkillItem[] = result.skills_derivadas.map((label, i) => ({
      uri: `formacion_${Date.now()}_${i}`,
      label,
      type: 'skill' as const,
      description: `Competencia derivada de tu formación.`,
      source: 'esco' as const,
      confidence: 'confirmed' as SkillConfidence,
      via: 'formacion' as const,
    }))
    addSkills(nuevas)
  }

  const pct = Math.min(100, Math.round((confirmed.length / 5) * 100))
  const listo = confirmed.length >= 3

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-5xl mx-auto px-4 py-8">

        {/* Header */}
        <div className="mb-6">
          <span className="inline-block bg-blue-100 text-blue-700 text-[10px] font-bold px-2.5 py-0.5 rounded-full uppercase tracking-wider mb-2">
            Paso 2 de 3
          </span>
          <h1 className="text-2xl font-bold text-gray-900">
            {store.nombre ? `Hola ${store.nombre.split(' ')[0]}, ` : ''}agregá tus competencias
          </h1>
          <p className="text-gray-500 text-sm mt-1">
            Usá la forma que te resulte más fácil. Podés combinar varias.
          </p>
        </div>

        <div className="flex flex-col lg:flex-row gap-6">

          {/* Panel izquierdo — vías de captura */}
          <div className="flex-1 min-w-0">

            {/* Tabs de vías */}
            <div className="flex gap-1 bg-white border border-gray-200 rounded-xl p-1 mb-4 overflow-x-auto">
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
            <p className="text-xs text-gray-400 mb-4">
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
            </div>
          </div>

          {/* Panel derecho — acumulador de skills */}
          <div className="w-full lg:w-80 shrink-0">
            <div className="bg-white rounded-xl border border-gray-200 p-4 sticky top-4">

              {/* Completitud */}
              <div className="mb-4">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs font-medium text-gray-700">
                    Competencias confirmadas
                  </span>
                  <span className={`text-xs font-bold ${listo ? 'text-green-600' : 'text-blue-600'}`}>
                    {confirmed.length} {listo ? '✓' : `/ 3 mínimo`}
                  </span>
                </div>
                <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all ${listo ? 'bg-green-500' : 'bg-blue-500'}`}
                    style={{ width: `${pct}%` }}
                  />
                </div>
              </div>

              {/* Lista de skills */}
              {store.skills.length === 0 ? (
                <div className="py-8 text-center">
                  <p className="text-xs text-gray-400">
                    Usá las vías de la izquierda para agregar competencias.
                  </p>
                </div>
              ) : (
                <div className="space-y-2 max-h-96 overflow-y-auto pr-1">
                  {store.skills.map((skill) => (
                    <SkillWithDefinition
                      key={skill.uri}
                      skill={skill}
                      onConfidenceChange={(uri, confidence) => updateSkill(uri, { confidence })}
                      onRemove={removeSkill}
                    />
                  ))}
                </div>
              )}

              {/* CTA */}
              <div className="mt-4 pt-4 border-t border-gray-100">
                {listo ? (
                  <button
                    onClick={() => router.push('/mi-futuro-laboral/resultados')}
                    className="w-full inline-flex items-center justify-center gap-2 bg-green-600 text-white text-sm font-semibold px-4 py-2.5 rounded-xl hover:bg-green-700 transition-colors"
                  >
                    <CheckCircle className="w-4 h-4" />
                    Ver mis resultados
                    <ArrowRight className="w-4 h-4" />
                  </button>
                ) : (
                  <p className="text-center text-xs text-gray-400">
                    Confirmá al menos {3 - confirmed.length} competencia
                    {3 - confirmed.length !== 1 ? 's' : ''} más para ver resultados.
                  </p>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
