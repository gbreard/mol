import Link from 'next/link'
import { BarChart3, Briefcase, Scale, FileText, ChevronRight } from 'lucide-react'

const MODULES = [
  {
    href: '/vip/dashboard',
    icon: BarChart3,
    title: 'Tablero de seguimiento',
    description: 'Ofertas laborales, requerimientos y competencias',
    color: 'amber',
  },
  {
    href: '/oficina-empleo',
    icon: Briefcase,
    title: 'Oficina de Empleo',
    description: 'Orientación a trabajadores y trabajadoras para acceder a vacantes disponibles y reconversión laboral',
    color: 'teal',
  },
  {
    href: '/vip/politicas',
    icon: Scale,
    title: 'Análisis ocupacional',
    description: 'Indicadores analíticos, perfiles de competencias y reconversión laboral',
    color: 'blue',
  },
  {
    href: '/informes',
    icon: FileText,
    title: 'Informes',
    description: 'Reportes y análisis del mercado laboral argentino',
    color: 'purple',
  },
]

const COLORS: Record<string, { iconBg: string; iconText: string; hover: string }> = {
  amber:  { iconBg: 'bg-amber-50',  iconText: 'text-amber-600',  hover: 'hover:border-amber-300' },
  teal:   { iconBg: 'bg-teal-50',   iconText: 'text-teal-600',   hover: 'hover:border-teal-300' },
  blue:   { iconBg: 'bg-blue-50',   iconText: 'text-blue-600',   hover: 'hover:border-blue-300' },
  purple: { iconBg: 'bg-purple-50', iconText: 'text-purple-600', hover: 'hover:border-purple-300' },
}

export default function VipPage() {
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-5xl mx-auto px-4 py-12">
        <div className="mb-10 text-center">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Inteligencia del Mercado Laboral Argentino
          </h1>
          <p className="text-gray-500 text-lg">
            Herramientas diseñadas para transformar datos dispersos en inteligencia accionable
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {MODULES.map(m => {
            const c = COLORS[m.color]
            return (
              <Link
                key={m.href}
                href={m.href}
                className={`bg-white rounded-xl border border-gray-200 ${c.hover} p-6 flex flex-col gap-3 transition-all group`}
              >
                <div className={`w-11 h-11 rounded-lg ${c.iconBg} ${c.iconText} flex items-center justify-center`}>
                  <m.icon className="w-5 h-5" />
                </div>
                <div className="flex-1">
                  <h2 className="text-lg font-semibold text-gray-900 mb-1">{m.title}</h2>
                  <p className="text-sm text-gray-500 leading-relaxed">{m.description}</p>
                </div>
                <div className="flex items-center gap-1 text-sm font-medium text-gray-400 group-hover:text-gray-600 transition-colors">
                  Abrir <ChevronRight className="w-4 h-4" />
                </div>
              </Link>
            )
          })}
        </div>
      </div>
    </div>
  )
}
