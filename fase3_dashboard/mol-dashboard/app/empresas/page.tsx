import Link from 'next/link'
import {
  Building2, Users, TrendingUp, BarChart3, ChevronRight,
  Zap, ShieldCheck, BookOpen, Search, ArrowRight,
} from 'lucide-react'

const FEATURES = [
  {
    icon: Zap,
    title: 'Matching inteligente',
    desc: 'Cruzamos tu perfil de puesto con miles de candidatos. Te mostramos quién tiene las skills exactas que necesitás.',
  },
  {
    icon: ShieldCheck,
    title: 'Competencias verificadas',
    desc: 'Cada skill está validada por el motor ESCO. Sin CVs inventados, sin palabras vacías.',
  },
  {
    icon: TrendingUp,
    title: 'Benchmark de mercado',
    desc: 'Sabé qué skills están en demanda, cuáles escasean y cómo se mueve el mercado en tu sector.',
  },
  {
    icon: BookOpen,
    title: 'Reskilling de plantilla',
    desc: 'Detectá brechas en tu equipo actual y conectalos con formación específica. Retención con impacto.',
  },
]

const STATS = [
  { valor: '120K+', label: 'Perfiles activos' },
  { valor: '4.500+', label: 'Empresas usuarias' },
  { valor: '92%', label: 'Match preciso' },
  { valor: '3.2x', label: 'Más rápido que bolsa tradicional' },
]

const PLANES = [
  {
    nombre: 'Explorar',
    precio: 'Gratis',
    desc: 'Para conocer el sistema.',
    features: ['1 perfil de puesto', '10 candidatos visibles', 'Reporte QR básico'],
    cta: 'Empezar gratis',
    href: '/empresas/dashboard',
    highlight: false,
  },
  {
    nombre: 'Profesional',
    precio: '$12.900/mes',
    desc: 'Para equipos de RRHH activos.',
    features: ['Puestos ilimitados', 'Pool completo de candidatos', 'Benchmark sectorial', 'Comparar candidatos', 'Exportar a ATS'],
    cta: 'Comenzar prueba 14 días',
    href: '/empresas/dashboard',
    highlight: true,
  },
  {
    nombre: 'Enterprise',
    precio: 'A medida',
    desc: 'Para grandes organizaciones.',
    features: ['Todo Profesional', 'Reskilling de plantilla', 'API + integraciones', 'Soporte dedicado', 'SLA garantizado'],
    cta: 'Hablar con ventas',
    href: '/empresas/dashboard',
    highlight: false,
  },
]

export default function EmpresasLandingPage() {
  return (
    <div className="min-h-screen bg-white">

      {/* Hero */}
      <section className="bg-gradient-to-br from-indigo-900 via-indigo-800 to-purple-900 text-white">
        <div className="max-w-5xl mx-auto px-4 py-16 sm:py-24">
          <div className="max-w-2xl">
            <span className="inline-block bg-indigo-600/40 border border-indigo-400/30 text-indigo-200 text-xs font-semibold px-3 py-1 rounded-full mb-4">
              Para empresas · S3
            </span>
            <h1 className="text-3xl sm:text-4xl font-bold leading-tight mb-4">
              Encontrá talento por lo que saben hacer,<br />
              <span className="text-indigo-300">no por lo que dicen en el CV</span>
            </h1>
            <p className="text-indigo-200 text-lg mb-8">
              MOL cruza tus perfiles de puesto con candidatos reales usando skills verificadas.
              Sin filtros de palabra clave. Sin ruido.
            </p>
            <div className="flex flex-col sm:flex-row gap-3">
              <Link
                href="/empresas/dashboard"
                className="inline-flex items-center justify-center gap-2 bg-white text-indigo-900 text-sm font-bold px-6 py-3 rounded-xl hover:bg-indigo-50 transition-colors"
              >
                Ver demo
                <ArrowRight className="w-4 h-4" />
              </Link>
              <Link
                href="/empresas/pool"
                className="inline-flex items-center justify-center gap-2 border border-indigo-400/50 text-white text-sm font-semibold px-6 py-3 rounded-xl hover:bg-indigo-700/50 transition-colors"
              >
                <Search className="w-4 h-4" />
                Explorar candidatos
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Stats */}
      <section className="bg-indigo-950 text-white py-10">
        <div className="max-w-5xl mx-auto px-4">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-6 text-center">
            {STATS.map((s) => (
              <div key={s.label}>
                <p className="text-2xl sm:text-3xl font-bold text-indigo-300">{s.valor}</p>
                <p className="text-xs text-indigo-400 mt-1">{s.label}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="py-16 bg-gray-50">
        <div className="max-w-5xl mx-auto px-4">
          <h2 className="text-2xl font-bold text-gray-900 mb-2 text-center">
            Todo lo que necesitás para contratar mejor
          </h2>
          <p className="text-gray-500 text-sm text-center mb-10">
            Un sistema diseñado para el mercado laboral argentino.
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
            {FEATURES.map((f) => (
              <div key={f.title} className="bg-white rounded-xl border border-gray-200 p-6">
                <div className="w-10 h-10 rounded-lg bg-indigo-50 flex items-center justify-center mb-4">
                  <f.icon className="w-5 h-5 text-indigo-600" />
                </div>
                <h3 className="text-sm font-semibold text-gray-900 mb-1">{f.title}</h3>
                <p className="text-xs text-gray-500 leading-relaxed">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Planes */}
      <section className="py-16">
        <div className="max-w-5xl mx-auto px-4">
          <h2 className="text-2xl font-bold text-gray-900 mb-2 text-center">Planes</h2>
          <p className="text-gray-500 text-sm text-center mb-10">Sin contratos de permanencia. Cancelá cuando quieras.</p>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-5">
            {PLANES.map((p) => (
              <div
                key={p.nombre}
                className={`rounded-xl border p-6 flex flex-col ${
                  p.highlight
                    ? 'border-indigo-500 bg-indigo-50 shadow-md shadow-indigo-100'
                    : 'border-gray-200 bg-white'
                }`}
              >
                {p.highlight && (
                  <span className="inline-block bg-indigo-600 text-white text-[10px] font-bold px-2.5 py-0.5 rounded-full uppercase tracking-wider mb-3 self-start">
                    Más popular
                  </span>
                )}
                <h3 className="text-base font-bold text-gray-900">{p.nombre}</h3>
                <p className="text-2xl font-bold text-indigo-700 mt-1 mb-0.5">{p.precio}</p>
                <p className="text-xs text-gray-400 mb-4">{p.desc}</p>
                <ul className="space-y-2 mb-6 flex-1">
                  {p.features.map((feat) => (
                    <li key={feat} className="flex items-start gap-2 text-xs text-gray-600">
                      <span className="text-green-500 mt-0.5">✓</span>
                      {feat}
                    </li>
                  ))}
                </ul>
                <Link
                  href={p.href}
                  className={`inline-flex items-center justify-center gap-1.5 text-sm font-semibold px-4 py-2.5 rounded-xl transition-colors ${
                    p.highlight
                      ? 'bg-indigo-600 text-white hover:bg-indigo-700'
                      : 'border border-gray-300 text-gray-700 hover:border-indigo-300 hover:text-indigo-700'
                  }`}
                >
                  {p.cta}
                  <ChevronRight className="w-4 h-4" />
                </Link>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA final */}
      <section className="bg-indigo-900 text-white py-14">
        <div className="max-w-2xl mx-auto px-4 text-center">
          <Building2 className="w-10 h-10 text-indigo-400 mx-auto mb-4" />
          <h2 className="text-2xl font-bold mb-2">¿Ya tenés una cuenta?</h2>
          <p className="text-indigo-300 text-sm mb-6">
            Accedé al dashboard para ver tus puestos y candidatos.
          </p>
          <Link
            href="/empresas/dashboard"
            className="inline-flex items-center gap-2 bg-white text-indigo-900 text-sm font-bold px-8 py-3 rounded-xl hover:bg-indigo-50 transition-colors"
          >
            Ir al dashboard
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </section>
    </div>
  )
}
