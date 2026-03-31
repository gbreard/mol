import Link from 'next/link'
import {
  Users, Briefcase, TrendingUp, AlertTriangle,
  Plus, ChevronRight, CheckCircle, Clock, BookOpen,
  Sparkles, BarChart3, FileText,
} from 'lucide-react'

// ─── Mock data ────────────────────────────────────────────────────────────────
const METRICAS = [
  { label: 'Casos activos', valor: 34, delta: '+3 esta semana', color: 'blue', icon: Users },
  { label: 'Inserción mes', valor: 12, delta: '↑ 4 vs mes ant.', color: 'green', icon: CheckCircle },
  { label: 'En formación', valor: 8, delta: '3 finalizan pronto', color: 'orange', icon: BookOpen },
  { label: 'Sin actividad 7d', valor: 5, delta: 'Requieren atención', color: 'red', icon: AlertTriangle },
]

const CASOS_RECIENTES = [
  { id: 'c001', nombre: 'María González', estado: 'en_diagnostico', ocupacion: 'Administrativa', match: 72 },
  { id: 'c002', nombre: 'Carlos Ruiz', estado: 'derivado_vacante', ocupacion: 'Técnico IT', match: 85 },
  { id: 'c003', nombre: 'Laura Méndez', estado: 'perfil_completo', ocupacion: 'Comercial', match: 63 },
  { id: 'c004', nombre: 'Roberto Sosa', estado: 'nuevo', ocupacion: 'Sin definir', match: null },
]

const ALERTAS = [
  { id: 'a1', texto: 'Ana Torres sin actividad hace 9 días', nivel: 'alto', casoId: 'c005' },
  { id: 'a2', texto: 'Curso de Python de Juan Pérez vence en 3 días', nivel: 'medio', casoId: 'c006' },
  { id: 'a3', texto: 'Nueva vacante con 91% match para Laura Méndez', nivel: 'oportunidad', casoId: 'c003' },
]

const ESTADO_CONFIG: Record<string, { label: string; color: string }> = {
  nuevo: { label: 'Nuevo', color: 'bg-gray-100 text-gray-600' },
  en_diagnostico: { label: 'En diagnóstico', color: 'bg-blue-100 text-blue-700' },
  perfil_completo: { label: 'Perfil completo', color: 'bg-purple-100 text-purple-700' },
  derivado_vacante: { label: 'Derivado vacante', color: 'bg-green-100 text-green-700' },
  derivado_curso: { label: 'Derivado curso', color: 'bg-orange-100 text-orange-700' },
  en_seguimiento: { label: 'En seguimiento', color: 'bg-yellow-100 text-yellow-700' },
  insertado: { label: 'Insertado', color: 'bg-emerald-100 text-emerald-700' },
  cerrado: { label: 'Cerrado', color: 'bg-gray-100 text-gray-500' },
}

const ALERTA_CONFIG: Record<string, { color: string; icon: typeof AlertTriangle }> = {
  alto: { color: 'border-red-200 bg-red-50 text-red-700', icon: AlertTriangle },
  medio: { color: 'border-yellow-200 bg-yellow-50 text-yellow-700', icon: Clock },
  oportunidad: { color: 'border-green-200 bg-green-50 text-green-700', icon: TrendingUp },
}

const QUICK_LINKS = [
  { href: '/oficina-empleo/casos', label: 'Cartera de casos', icon: Users },
  { href: '/oficina-empleo/vacantes', label: 'Vacantes OE', icon: Briefcase },
  { href: '/oficina-empleo/formacion', label: 'Formación', icon: BookOpen },
  { href: '/oficina-empleo/perfil-puesto', label: 'Perfil de puesto', icon: FileText },
  { href: '/oficina-empleo/benchmark', label: 'Benchmark mercado', icon: BarChart3 },
  { href: '/oficina-empleo/onboarding', label: 'Importar planilla', icon: Sparkles },
]

function MetricaCard({ m }: { m: typeof METRICAS[0] }) {
  const colors: Record<string, string> = {
    blue: 'bg-blue-50 text-blue-600',
    green: 'bg-green-50 text-green-600',
    orange: 'bg-orange-50 text-orange-600',
    red: 'bg-red-50 text-red-600',
  }
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-4">
      <div className={`w-8 h-8 rounded-lg ${colors[m.color]} flex items-center justify-center mb-3`}>
        <m.icon className="w-4 h-4" />
      </div>
      <p className="text-2xl font-bold text-gray-900">{m.valor}</p>
      <p className="text-xs text-gray-500 mt-0.5">{m.label}</p>
      <p className={`text-[10px] mt-1 font-medium ${m.color === 'red' ? 'text-red-500' : m.color === 'green' ? 'text-green-600' : 'text-gray-400'}`}>
        {m.delta}
      </p>
    </div>
  )
}

export default function OficinaEmpleoPage() {
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-5xl mx-auto px-4 py-8">

        {/* Header */}
        <div className="flex items-start justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Panel del técnico</h1>
            <p className="text-gray-500 text-sm mt-1">Oficina de Empleo · CABA</p>
          </div>
          <Link
            href="/oficina-empleo/casos/nuevo"
            className="inline-flex items-center gap-2 bg-teal-600 text-white text-sm font-semibold px-4 py-2.5 rounded-xl hover:bg-teal-700 transition-colors"
          >
            <Plus className="w-4 h-4" />
            Nuevo caso
          </Link>
        </div>

        {/* Métricas */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-6">
          {METRICAS.map((m) => <MetricaCard key={m.label} m={m} />)}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">

          {/* Casos recientes */}
          <div className="lg:col-span-2 bg-white rounded-xl border border-gray-200 overflow-hidden">
            <div className="flex items-center justify-between px-4 py-3 border-b border-gray-100">
              <h2 className="text-sm font-semibold text-gray-800">Casos recientes</h2>
              <Link href="/oficina-empleo/casos" className="text-xs text-teal-600 hover:underline">
                Ver todos →
              </Link>
            </div>
            <div className="divide-y divide-gray-50">
              {CASOS_RECIENTES.map((c) => {
                const est = ESTADO_CONFIG[c.estado]
                return (
                  <Link
                    key={c.id}
                    href={`/oficina-empleo/casos/${c.id}`}
                    className="flex items-center gap-3 px-4 py-3 hover:bg-gray-50 transition-colors"
                  >
                    <div className="w-8 h-8 rounded-full bg-teal-100 text-teal-700 text-xs font-bold flex items-center justify-center shrink-0">
                      {c.nombre.split(' ').map((n) => n[0]).join('').slice(0, 2)}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900 truncate">{c.nombre}</p>
                      <p className="text-xs text-gray-400">{c.ocupacion}</p>
                    </div>
                    <div className="flex items-center gap-2 shrink-0">
                      {c.match !== null && (
                        <span className={`text-xs font-bold ${c.match >= 80 ? 'text-green-600' : 'text-blue-600'}`}>
                          {c.match}%
                        </span>
                      )}
                      <span className={`text-[10px] px-2 py-0.5 rounded-full font-medium ${est.color}`}>
                        {est.label}
                      </span>
                      <ChevronRight className="w-4 h-4 text-gray-300" />
                    </div>
                  </Link>
                )
              })}
            </div>
          </div>

          {/* Alertas */}
          <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
            <div className="px-4 py-3 border-b border-gray-100">
              <h2 className="text-sm font-semibold text-gray-800">Alertas</h2>
            </div>
            <div className="p-3 space-y-2">
              {ALERTAS.map((a) => {
                const cfg = ALERTA_CONFIG[a.nivel]
                const Icon = cfg.icon
                return (
                  <Link
                    key={a.id}
                    href={`/oficina-empleo/casos/${a.casoId}`}
                    className={`flex items-start gap-2 border rounded-lg p-3 hover:opacity-90 transition-opacity ${cfg.color}`}
                  >
                    <Icon className="w-3.5 h-3.5 shrink-0 mt-0.5" />
                    <p className="text-xs leading-relaxed">{a.texto}</p>
                  </Link>
                )
              })}
            </div>
          </div>
        </div>

        {/* Quick links */}
        <div className="mt-5 grid grid-cols-2 sm:grid-cols-3 gap-3">
          {QUICK_LINKS.map((l) => (
            <Link
              key={l.href}
              href={l.href}
              className="flex items-center gap-3 bg-white rounded-xl border border-gray-200 p-4 hover:border-teal-300 hover:bg-teal-50 transition-all group"
            >
              <l.icon className="w-5 h-5 text-gray-400 group-hover:text-teal-600 shrink-0" />
              <span className="text-sm font-medium text-gray-700 group-hover:text-teal-700 truncate">{l.label}</span>
              <ChevronRight className="w-4 h-4 text-gray-300 ml-auto shrink-0" />
            </Link>
          ))}
        </div>
      </div>
    </div>
  )
}
