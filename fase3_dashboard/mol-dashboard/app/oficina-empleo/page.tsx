import Link from 'next/link'
import { ClipboardList, Target, Map, BarChart3, ChevronRight } from 'lucide-react'
import { createServerClient } from '@/lib/supabase/server'

const MODULES = [
  {
    href: '/oficina-empleo/perfiles',
    icon: ClipboardList,
    title: 'Perfil de Competencias',
    description: 'Capturá el perfil de skills de un candidato con la taxonomía ESCO',
    color: 'teal',
  },
  {
    href: '/oficina-empleo/perfiles/matching',
    icon: Target,
    title: 'Oportunidades Laborales',
    description: 'Encontrá las ocupaciones compatibles con el perfil del candidato y la demanda real de MOL',
    color: 'blue',
  },
  {
    href: '/oficina-empleo/perfiles/futuro',
    icon: Map,
    title: 'Futuro Laboral',
    description: 'Analizá la brecha de skills y el plan de transición para un candidato hacia una ocupación objetivo',
    color: 'purple',
  },
]

const M4_MODULE = {
  href: '/oficina-empleo/dashboard-ejecutivo',
  icon: BarChart3,
  title: 'Inteligencia del Mercado Laboral',
  description: 'Panorama territorial de la demanda de empleo — sectores, ocupaciones, skills más pedidas y perfil de requerimientos por provincia y período',
  color: 'amber',
}

const COLORS: Record<string, { bg: string; iconBg: string; iconText: string; hover: string }> = {
  teal:   { bg: 'bg-white', iconBg: 'bg-teal-50',   iconText: 'text-teal-600',   hover: 'hover:border-teal-300' },
  blue:   { bg: 'bg-white', iconBg: 'bg-blue-50',   iconText: 'text-blue-600',   hover: 'hover:border-blue-300' },
  purple: { bg: 'bg-white', iconBg: 'bg-purple-50', iconText: 'text-purple-600', hover: 'hover:border-purple-300' },
  amber:  { bg: 'bg-white', iconBg: 'bg-amber-50',  iconText: 'text-amber-600',  hover: 'hover:border-amber-300' },
}

export default async function OficinaEmpleoPage() {
  // Check if user is VIP — hide M4 for VIP (they have it in /vip/politicas)
  let isVip = false
  try {
    const supabase = await createServerClient()
    const { data: { user } } = await supabase.auth.getUser()
    isVip = user?.user_metadata?.role === 'visit_vip'
  } catch {}

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-5xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-gray-900">Oficina de Empleo</h1>
          <p className="text-gray-500 text-sm mt-1">
            Herramientas para el técnico y el equipo de gestión
          </p>
        </div>

        {/* Top 3 modules */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
          {MODULES.map((m) => {
            const c = COLORS[m.color]
            return (
              <Link
                key={m.href}
                href={m.href}
                className={`${c.bg} rounded-xl border border-gray-200 ${c.hover} p-5 flex flex-col gap-3 transition-all group`}
              >
                <div className={`w-10 h-10 rounded-lg ${c.iconBg} ${c.iconText} flex items-center justify-center`}>
                  <m.icon className="w-5 h-5" />
                </div>
                <div className="flex-1">
                  <h2 className="text-sm font-semibold text-gray-900 mb-1">{m.title}</h2>
                  <p className="text-xs text-gray-500 leading-relaxed">{m.description}</p>
                </div>
                <div className="flex items-center gap-1 text-xs font-medium text-gray-400 group-hover:text-gray-600 transition-colors">
                  Abrir <ChevronRight className="w-3 h-3" />
                </div>
              </Link>
            )
          })}
        </div>

        {/* M4 — only for non-VIP */}
        {!isVip && (
          <Link
            href={M4_MODULE.href}
            className={`${COLORS.amber.bg} rounded-xl border border-gray-200 ${COLORS.amber.hover} p-5 flex items-start gap-4 transition-all group`}
          >
            <div className={`w-10 h-10 rounded-lg ${COLORS.amber.iconBg} ${COLORS.amber.iconText} flex items-center justify-center shrink-0`}>
              <BarChart3 className="w-5 h-5" />
            </div>
            <div className="flex-1">
              <h2 className="text-sm font-semibold text-gray-900 mb-1">{M4_MODULE.title}</h2>
              <p className="text-xs text-gray-500 leading-relaxed">{M4_MODULE.description}</p>
            </div>
            <div className="flex items-center gap-1 text-xs font-medium text-gray-400 group-hover:text-gray-600 transition-colors shrink-0 mt-1">
              Abrir <ChevronRight className="w-3 h-3" />
            </div>
          </Link>
        )}
      </div>
    </div>
  )
}
