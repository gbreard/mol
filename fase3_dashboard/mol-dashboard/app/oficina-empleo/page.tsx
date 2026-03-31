'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import {
  Users, Briefcase, TrendingUp, AlertTriangle,
  Plus, ChevronRight, CheckCircle, Clock, BookOpen,
  Sparkles, BarChart3, FileText, Loader2,
} from 'lucide-react'

interface CasoResumen {
  id: string
  nombre: string
  estado: string
  ocupacion: string
}

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

const QUICK_LINKS = [
  { href: '/oficina-empleo/casos', label: 'Cartera de casos', icon: Users },
  { href: '/oficina-empleo/vacantes', label: 'Vacantes OE', icon: Briefcase },
  { href: '/oficina-empleo/formacion', label: 'Formación', icon: BookOpen },
  { href: '/oficina-empleo/perfil-puesto', label: 'Perfil de puesto', icon: FileText },
  { href: '/oficina-empleo/benchmark', label: 'Benchmark mercado', icon: BarChart3 },
  { href: '/oficina-empleo/onboarding', label: 'Importar planilla', icon: Sparkles },
]

export default function OficinaEmpleoPage() {
  const [casos, setCasos] = useState<CasoResumen[]>([])
  const [cargando, setCargando] = useState(true)

  useEffect(() => {
    async function cargar() {
      try {
        const res = await fetch('/api/casos?limit=20')
        if (res.ok) {
          const data = await res.json()
          if (Array.isArray(data)) {
            setCasos(data.map((c: any) => ({
              id: c.id,
              nombre: c.persona_nombre || 'Sin nombre',
              estado: c.estado,
              ocupacion: c.objetivo || 'empleo',
            })))
          }
        }
      } catch (e) {
        console.error('Error cargando casos:', e)
      } finally {
        setCargando(false)
      }
    }
    cargar()
  }, [])

  const activos = casos.filter(c => !['cerrado', 'insertado'].includes(c.estado))
  const insertados = casos.filter(c => c.estado === 'insertado')
  const enFormacion = casos.filter(c => c.estado === 'derivado_curso')
  const recientes = casos.slice(0, 4)

  const metricas = [
    { label: 'Casos activos', valor: activos.length, color: 'blue', icon: Users },
    { label: 'Insertados', valor: insertados.length, color: 'green', icon: CheckCircle },
    { label: 'En formación', valor: enFormacion.length, color: 'orange', icon: BookOpen },
    { label: 'Total personas', valor: casos.length, color: 'red', icon: TrendingUp },
  ]

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-5xl mx-auto px-4 py-8">

        {/* Header */}
        <div className="flex items-start justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Panel del técnico</h1>
            <p className="text-gray-500 text-sm mt-1">Oficina de Empleo</p>
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
          {metricas.map((m) => {
            const colors: Record<string, string> = {
              blue: 'bg-blue-50 text-blue-600',
              green: 'bg-green-50 text-green-600',
              orange: 'bg-orange-50 text-orange-600',
              red: 'bg-red-50 text-red-600',
            }
            return (
              <div key={m.label} className="bg-white rounded-xl border border-gray-200 p-4">
                <div className={`w-8 h-8 rounded-lg ${colors[m.color]} flex items-center justify-center mb-3`}>
                  <m.icon className="w-4 h-4" />
                </div>
                <p className="text-2xl font-bold text-gray-900">{cargando ? '—' : m.valor}</p>
                <p className="text-xs text-gray-500 mt-0.5">{m.label}</p>
              </div>
            )
          })}
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
            {cargando ? (
              <div className="py-8 flex items-center justify-center gap-2 text-gray-400">
                <Loader2 className="w-4 h-4 animate-spin" />
                <span className="text-sm">Cargando...</span>
              </div>
            ) : recientes.length === 0 ? (
              <div className="py-8 text-center text-gray-400 text-sm">No hay casos registrados.</div>
            ) : (
              <div className="divide-y divide-gray-50">
                {recientes.map((c) => {
                  const est = ESTADO_CONFIG[c.estado] || ESTADO_CONFIG.nuevo
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
                        <span className={`text-[10px] px-2 py-0.5 rounded-full font-medium ${est.color}`}>
                          {est.label}
                        </span>
                        <ChevronRight className="w-4 h-4 text-gray-300" />
                      </div>
                    </Link>
                  )
                })}
              </div>
            )}
          </div>

          {/* Info panel */}
          <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
            <div className="px-4 py-3 border-b border-gray-100">
              <h2 className="text-sm font-semibold text-gray-800">Accesos rápidos</h2>
            </div>
            <div className="p-3 space-y-2">
              {QUICK_LINKS.slice(0, 4).map((l) => (
                <Link
                  key={l.href}
                  href={l.href}
                  className="flex items-center gap-2 rounded-lg p-2 hover:bg-gray-50 transition-colors group"
                >
                  <l.icon className="w-4 h-4 text-gray-400 group-hover:text-teal-600" />
                  <span className="text-xs font-medium text-gray-600 group-hover:text-teal-700">{l.label}</span>
                  <ChevronRight className="w-3 h-3 text-gray-300 ml-auto" />
                </Link>
              ))}
            </div>
          </div>
        </div>

        {/* Quick links grid */}
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
