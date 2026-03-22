'use client'

import { Users, Briefcase, GraduationCap, Download, Upload, ChevronRight } from 'lucide-react'

interface CardData {
  step: number
  title: string
  badge: string
  description: string
  icon: React.ReactNode
  required: boolean
  templateHref: string
  onUpload: () => void
}

interface Props {
  nombreOE?: string
  nombreUsuario?: string
  onUploadPersonas: (file: File) => void
  onUploadVacantes?: (file: File) => void
  onUploadCursos?: (file: File) => void
  onAtenderManual?: () => void
}

function UploadCard({ card }: { card: CardData }) {
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) card.onUpload()
  }

  return (
    <div className={`flex flex-col rounded-xl border-2 p-5 ${card.required ? 'border-blue-200 bg-blue-50' : 'border-gray-200 bg-white'}`}>
      <div className="mb-3 flex items-center gap-2">
        <div className={`flex h-8 w-8 items-center justify-center rounded-full text-sm font-bold ${card.required ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-600'}`}>
          {card.step}
        </div>
        <div className="min-w-0">
          <h3 className="text-sm font-semibold text-gray-900">{card.title}</h3>
          <span className={`text-[10px] font-bold uppercase tracking-wider ${card.required ? 'text-blue-600' : 'text-gray-400'}`}>
            {card.badge}
          </span>
        </div>
        <div className="ml-auto">{card.icon}</div>
      </div>
      <p className="mb-4 flex-1 text-xs text-gray-500">{card.description}</p>
      <div className="space-y-2">
        <a
          href={card.templateHref}
          download
          aria-label={`Descargar template ${card.title}`}
          className="flex min-h-[44px] w-full items-center justify-center gap-2 rounded-lg border border-gray-300 px-3 py-2 text-sm text-gray-600 hover:bg-gray-50"
        >
          <Download className="h-4 w-4" />
          Descargar template
        </a>
        <label
          aria-label={`Subir Excel ${card.title}`}
          className={`flex min-h-[44px] w-full cursor-pointer items-center justify-center gap-2 rounded-lg px-3 py-2 text-sm font-medium ${
            card.required
              ? 'bg-blue-600 text-white hover:bg-blue-700'
              : 'border border-blue-300 text-blue-600 hover:bg-blue-50'
          }`}
        >
          <Upload className="h-4 w-4" />
          Subir Excel
          <input
            type="file"
            accept=".xlsx,.xls,.csv"
            className="sr-only"
            onChange={handleFileChange}
            aria-label={`Archivo Excel ${card.title}`}
          />
        </label>
      </div>
    </div>
  )
}

export default function OEOnboarding({
  nombreOE = 'tu Oficina de Empleo',
  nombreUsuario = '',
  onUploadPersonas,
  onUploadVacantes,
  onUploadCursos,
  onAtenderManual,
}: Props) {
  const cards: CardData[] = [
    {
      step: 1,
      title: 'Personas',
      badge: 'mínimo para arrancar',
      description: 'Tu planilla de personas registradas en la OE. Es el punto de partida para el sistema.',
      icon: <Users className="h-5 w-5 text-blue-500" />,
      required: true,
      templateHref: '/templates/template-personas.xlsx',
      onUpload: () => onUploadPersonas(new File([], 'personas.xlsx')),
    },
    {
      step: 2,
      title: 'Vacantes',
      badge: 'opcional',
      description: 'Vacantes que empresas locales traen a la OE. Permite cruzar con perfiles de personas.',
      icon: <Briefcase className="h-5 w-5 text-gray-400" />,
      required: false,
      templateHref: '/templates/template-vacantes.xlsx',
      onUpload: () => onUploadVacantes?.(new File([], 'vacantes.xlsx')),
    },
    {
      step: 3,
      title: 'Cursos',
      badge: 'opcional',
      description: 'Cursos que ofrece tu municipio. Se usan para sugerir capacitación a las personas.',
      icon: <GraduationCap className="h-5 w-5 text-gray-400" />,
      required: false,
      templateHref: '/templates/template-cursos.xlsx',
      onUpload: () => onUploadCursos?.(new File([], 'cursos.xlsx')),
    },
  ]

  return (
    <div className="mx-auto max-w-3xl space-y-6 px-4 py-8">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">
          {nombreUsuario ? `Bienvenida/o, ${nombreUsuario}!` : '¡Bienvenida/o!'}
        </h1>
        <p className="mt-1 text-sm text-gray-500">{nombreOE}</p>
      </div>

      <p className="text-sm text-gray-600">
        Para empezar a usar el sistema, cargá tu planilla de personas.
        Después podés agregar vacantes y cursos.
      </p>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        {cards.map((card) => (
          <UploadCard key={card.step} card={card} />
        ))}
      </div>

      <div className="border-t border-gray-100 pt-4 text-center">
        <p className="mb-3 text-sm text-gray-500">
          O si preferís, podés empezar cargando casos uno por uno:
        </p>
        <button
          onClick={onAtenderManual}
          aria-label="Atender primer caso manualmente"
          className="inline-flex min-h-[44px] items-center gap-2 rounded-lg border border-gray-300 px-5 py-2.5 text-sm text-gray-600 hover:bg-gray-50"
        >
          Atender primer caso manualmente
          <ChevronRight className="h-4 w-4" />
        </button>
      </div>
    </div>
  )
}
