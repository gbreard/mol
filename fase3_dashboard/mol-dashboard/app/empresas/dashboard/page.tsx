'use client'

import Link from 'next/link'
import {
  Briefcase, Users, TrendingUp, Star,
  Plus, ChevronRight, Eye, AlertCircle,
  Building2, BarChart3,
} from 'lucide-react'

// ─── Mock data ────────────────────────────────────────────────────────────────
const EMPRESA = {
  nombre: 'TechCorp Argentina S.A.',
  sector: 'Tecnología',
  plan: 'Profesional',
}

const METRICAS = [
  { label: 'Puestos activos', valor: 7, delta: '+2 esta semana', color: 'indigo', icon: Briefcase },
  { label: 'Candidatos en evaluación', valor: 43, delta: '18 nuevos hoy', color: 'blue', icon: Users },
  { label: 'Match promedio', valor: '74%', delta: '↑ 3pp vs mes ant.', color: 'green', icon: TrendingUp },
  { label: 'Top match', valor: '96%', delta: 'Desarrollador React', color: 'purple', icon: Star },
]

const PUESTOS = [
  { id: 'p1', titulo: 'Desarrollador React', candidatos: 18, matchTop: 96, estado: 'activo', dias: 5 },
  { id: 'p2', titulo: 'Analista de Datos Senior', candidatos: 7, matchTop: 88, estado: 'activo', dias: 12 },
  { id: 'p3', titulo: 'DevOps Engineer', candidatos: 4, matchTop: 79, estado: 'activo', dias: 8 },
  { id: 'p4', titulo: 'QA Automation', candidatos: 9, matchTop: 71, estado: 'activo', dias: 3 },
  { id: 'p5', titulo: 'Product Manager', candidatos: 5, matchTop: 83, estado: 'activo', dias: 15 },
]

const CANDIDATOS_RECIENTES = [
  { id: 'c1', nombre: 'Lucía Fernández', puesto: 'Desarrollador React', match: 96, estado: 'nuevo' },
  { id: 'c2', nombre: 'Martín Soria', puesto: 'Analista de Datos Senior', match: 88, estado: 'revisado' },
  { id: 'c3', nombre: 'Valentina Cruz', puesto: 'Desarrollador React', match: 85, estado: 'nuevo' },
  { id: 'c4', nombre: 'Diego Méndez', puesto: 'DevOps Engineer', match: 79, estado: 'contactado' },
]

const QUICK_LINKS = [
  { href: '/empresas/puestos', label: 'Mis puestos', icon: Briefcase },
  { href: '/empresas/candidatos', label: 'Candidatos', icon: Users },
  { href: '/empresas/benchmark', label: 'Benchmark', icon: BarChart3 },
  { href: '/empresas/pool', label: 'Buscar en pool', icon: Eye },
]

function MatchBar({ pct }: { pct: number }) {
  const color = pct >= 85 ? 'bg-green-500' : pct >= 70 ? 'bg-blue-500' : 'bg-yellow-500'
  return (
    <div className="flex items-center gap-2">
      <div className="w-16 h-1.5 bg-gray-100 rounded-full overflow-hidden">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className={`text-xs font-bold tabular-nums ${pct >= 85 ? 'text-green-600' : pct >= 70 ? 'text-blue-600' : 'text-yellow-600'}`}>
        {pct}%
      </span>
    </div>
  )
}

export default function EmpresasDashboardPage() {
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-5xl mx-auto px-4 py-8">

        {/* Header */}
        <div className="flex items-start justify-between mb-6">
          <div>
            <div className="flex items-center gap-2 mb-0.5">
              <Building2 className="w-5 h-5 text-indigo-500" />
              <h1 className="text-xl font-bold text-gray-900">{EMPRESA.nombre}</h1>
            </div>
            <p className="text-sm text-gray-500">
              {EMPRESA.sector} · Plan {EMPRESA.plan}
            </p>
          </div>
          <Link
            href="/empresas/puestos/nuevo"
            className="inline-flex items-center gap-2 bg-indigo-600 text-white text-sm font-semibold px-4 py-2.5 rounded-xl hover:bg-indigo-700 transition-colors"
          >
            <Plus className="w-4 h-4" />
            Nuevo puesto
          </Link>
        </div>

        {/* Métricas */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-6">
          {METRICAS.map((m) => {
            const colorMap: Record<string, string> = {
              indigo: 'bg-indigo-50 text-indigo-600',
              blue: 'bg-blue-50 text-blue-600',
              green: 'bg-green-50 text-green-600',
              purple: 'bg-purple-50 text-purple-600',
            }
            return (
              <div key={m.label} className="bg-white rounded-xl border border-gray-200 p-4">
                <div className={`w-8 h-8 rounded-lg ${colorMap[m.color]} flex items-center justify-center mb-3`}>
                  <m.icon className="w-4 h-4" />
                </div>
                <p className="text-2xl font-bold text-gray-900">{m.valor}</p>
                <p className="text-xs text-gray-500 mt-0.5">{m.label}</p>
                <p className="text-[10px] mt-1 font-medium text-gray-400">{m.delta}</p>
              </div>
            )
          })}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">

          {/* Puestos activos */}
          <div className="lg:col-span-2 bg-white rounded-xl border border-gray-200 overflow-hidden">
            <div className="flex items-center justify-between px-4 py-3 border-b border-gray-100">
              <h2 className="text-sm font-semibold text-gray-800">Puestos activos</h2>
              <Link href="/empresas/puestos" className="text-xs text-indigo-600 hover:underline">
                Ver todos →
              </Link>
            </div>
            <div className="divide-y divide-gray-50">
              {PUESTOS.map((p) => (
                <Link
                  key={p.id}
                  href={`/empresas/puestos/${p.id}`}
                  className="flex items-center gap-3 px-4 py-3 hover:bg-gray-50 transition-colors"
                >
                  <div className="w-8 h-8 rounded-lg bg-indigo-100 text-indigo-700 flex items-center justify-center shrink-0">
                    <Briefcase className="w-4 h-4" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 truncate">{p.titulo}</p>
                    <p className="text-xs text-gray-400">
                      {p.candidatos} candidatos · publicado hace {p.dias}d
                    </p>
                  </div>
                  <div className="flex items-center gap-3 shrink-0">
                    <MatchBar pct={p.matchTop} />
                    <ChevronRight className="w-4 h-4 text-gray-300" />
                  </div>
                </Link>
              ))}
            </div>
          </div>

          {/* Candidatos recientes */}
          <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
            <div className="flex items-center justify-between px-4 py-3 border-b border-gray-100">
              <h2 className="text-sm font-semibold text-gray-800">Candidatos recientes</h2>
              <Link href="/empresas/candidatos" className="text-xs text-indigo-600 hover:underline">
                Ver todos →
              </Link>
            </div>
            <div className="divide-y divide-gray-50">
              {CANDIDATOS_RECIENTES.map((c) => {
                const estadoColor: Record<string, string> = {
                  nuevo: 'bg-blue-100 text-blue-700',
                  revisado: 'bg-gray-100 text-gray-600',
                  contactado: 'bg-green-100 text-green-700',
                }
                return (
                  <Link
                    key={c.id}
                    href={`/empresas/candidatos/${c.id}`}
                    className="flex items-center gap-3 px-4 py-3 hover:bg-gray-50 transition-colors"
                  >
                    <div className="w-8 h-8 rounded-full bg-indigo-100 text-indigo-700 text-xs font-bold flex items-center justify-center shrink-0">
                      {c.nombre.split(' ').map((n) => n[0]).join('').slice(0, 2)}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900 truncate">{c.nombre}</p>
                      <p className="text-xs text-gray-400 truncate">{c.puesto}</p>
                    </div>
                    <div className="flex flex-col items-end gap-1 shrink-0">
                      <span className={`text-xs font-bold ${c.match >= 85 ? 'text-green-600' : 'text-blue-600'}`}>
                        {c.match}%
                      </span>
                      <span className={`text-[10px] px-1.5 py-0.5 rounded-full font-medium ${estadoColor[c.estado]}`}>
                        {c.estado}
                      </span>
                    </div>
                  </Link>
                )
              })}
            </div>
          </div>
        </div>

        {/* Quick links */}
        <div className="mt-5 grid grid-cols-2 sm:grid-cols-4 gap-3">
          {QUICK_LINKS.map((l) => (
            <Link
              key={l.href}
              href={l.href}
              className="flex items-center gap-3 bg-white rounded-xl border border-gray-200 p-4 hover:border-indigo-300 hover:bg-indigo-50 transition-all group"
            >
              <l.icon className="w-5 h-5 text-gray-400 group-hover:text-indigo-600 shrink-0" />
              <span className="text-sm font-medium text-gray-700 group-hover:text-indigo-700 truncate">{l.label}</span>
              <ChevronRight className="w-4 h-4 text-gray-300 ml-auto shrink-0" />
            </Link>
          ))}
        </div>

        {/* Alerta plan */}
        <div className="mt-4 flex items-start gap-3 bg-amber-50 border border-amber-200 rounded-xl p-4">
          <AlertCircle className="w-4 h-4 text-amber-500 shrink-0 mt-0.5" />
          <div className="flex-1 min-w-0">
            <p className="text-xs font-semibold text-amber-800">Tu prueba vence en 7 días</p>
            <p className="text-xs text-amber-700 mt-0.5">Activá el plan Profesional para mantener acceso al pool completo y al benchmark.</p>
          </div>
          <Link href="/empresas" className="text-xs font-semibold text-amber-700 hover:underline shrink-0">
            Ver planes
          </Link>
        </div>

      </div>
    </div>
  )
}
