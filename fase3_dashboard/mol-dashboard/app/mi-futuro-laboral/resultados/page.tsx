'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { Briefcase, Target, GraduationCap, ArrowRight, TrendingUp, MapPin, Building2, Clock } from 'lucide-react'
import { useS1Store } from '@/lib/use-s1-store'

// Mock data — se reemplaza con /api/matching-offers y /api/matching-occupations cuando Gerardo entregue las APIs
const MOCK_OCUPACIONES = [
  { uri: 'esco_3511', label: 'Técnico en sistemas informáticos', isco: '3511', match: 87, gap: 2, ofertas: 124 },
  { uri: 'esco_2512', label: 'Desarrollador de software', isco: '2512', match: 73, gap: 4, ofertas: 312 },
  { uri: 'esco_3512', label: 'Técnico de soporte TI', isco: '3512', match: 69, gap: 3, ofertas: 88 },
  { uri: 'esco_2511', label: 'Analista de sistemas', isco: '2511', match: 61, gap: 5, ofertas: 97 },
]

const MOCK_OFERTAS = [
  {
    id: 1, titulo: 'Técnico IT Junior', empresa: 'TechSolutions SA',
    provincia: 'CABA', modalidad: 'Híbrido', match: 84,
    skills_ok: ['Python', 'SQL', 'Linux'], skills_gap: ['Docker'],
    publicada: 'hace 2 días', url: '#',
  },
  {
    id: 2, titulo: 'Soporte Técnico N1', empresa: 'BancoCentral',
    provincia: 'GBA Norte', modalidad: 'Presencial', match: 78,
    skills_ok: ['Windows', 'Redes', 'Hardware'], skills_gap: ['Active Directory'],
    publicada: 'hace 3 días', url: '#',
  },
  {
    id: 3, titulo: 'Analista de Datos Jr.', empresa: 'Startup ABC',
    provincia: 'CABA', modalidad: 'Remoto', match: 71,
    skills_ok: ['Excel', 'SQL'], skills_gap: ['Python', 'Tableau'],
    publicada: 'hace 1 semana', url: '#',
  },
]

const MOCK_CURSOS = [
  {
    skill: 'Docker', impacto: '+9%', nombre: 'Administración de contenedores con Docker',
    institucion: 'CGPC CABA', duracion: '3 semanas', modalidad: 'Presencial', gratuito: true,
  },
  {
    skill: 'Python', impacto: '+12%', nombre: 'Python para análisis de datos',
    institucion: 'Argentina Programa', duracion: '8 semanas', modalidad: 'Online', gratuito: true,
  },
  {
    skill: 'Active Directory', impacto: '+6%', nombre: 'Administración de Windows Server',
    institucion: 'Teclab', duracion: '4 semanas', modalidad: 'Híbrido', gratuito: false,
  },
]

const TABS = [
  { id: 'ocupaciones', label: 'Ocupaciones', icon: Target },
  { id: 'ofertas', label: 'Ofertas reales', icon: Briefcase },
  { id: 'formacion', label: 'Formación', icon: GraduationCap },
]

function MatchBar({ pct }: { pct: number }) {
  const color = pct >= 80 ? 'bg-green-500' : pct >= 60 ? 'bg-blue-500' : 'bg-yellow-400'
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 bg-gray-100 rounded-full overflow-hidden">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className={`text-xs font-bold tabular-nums ${pct >= 80 ? 'text-green-600' : pct >= 60 ? 'text-blue-600' : 'text-yellow-600'}`}>
        {pct}%
      </span>
    </div>
  )
}

export default function ResultadosPage() {
  const router = useRouter()
  const { store, confirmed } = useS1Store()
  const [tab, setTab] = useState('ocupaciones')

  const nombre = store.nombre || 'tu perfil'

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto px-4 py-8">

        {/* Header */}
        <div className="mb-6">
          <span className="inline-block bg-green-100 text-green-700 text-[10px] font-bold px-2.5 py-0.5 rounded-full uppercase tracking-wider mb-2">
            Paso 3 de 3 — Tus resultados
          </span>
          <h1 className="text-2xl font-bold text-gray-900">
            Resultados para {nombre}
          </h1>
          <p className="text-gray-500 text-sm mt-1">
            Basado en {confirmed.length} competencias confirmadas.
          </p>
        </div>

        {/* Tabs */}
        <div className="flex gap-1 bg-white border border-gray-200 rounded-xl p-1 mb-6">
          {TABS.map((t) => (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className={`flex-1 flex items-center justify-center gap-1.5 py-2 rounded-lg text-xs font-medium transition-all ${
                tab === t.id
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'
              }`}
            >
              <t.icon className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">{t.label}</span>
            </button>
          ))}
        </div>

        {/* Tab: Ocupaciones */}
        {tab === 'ocupaciones' && (
          <div className="space-y-3">
            {MOCK_OCUPACIONES.map((o) => (
              <div key={o.uri} className="bg-white rounded-xl border border-gray-200 p-4">
                <div className="flex items-start justify-between gap-3 mb-3">
                  <div>
                    <h3 className="font-semibold text-gray-900 text-sm">{o.label}</h3>
                    <div className="flex items-center gap-2 mt-0.5">
                      <span className="text-xs text-gray-400 font-mono">{o.isco}</span>
                      <span className="text-xs text-gray-400">·</span>
                      <span className="text-xs text-gray-500">{o.ofertas} ofertas activas</span>
                    </div>
                  </div>
                  <span className="text-xs text-gray-400 shrink-0">
                    falta{o.gap !== 1 ? 'n' : ''} {o.gap} skill{o.gap !== 1 ? 's' : ''}
                  </span>
                </div>
                <MatchBar pct={o.match} />
                <div className="mt-3 flex gap-2">
                  <button
                    onClick={() => router.push(`/mi-futuro-laboral/brecha?uri=${o.uri}&label=${encodeURIComponent(o.label)}`)}
                    className="flex-1 text-xs text-blue-600 font-medium bg-blue-50 hover:bg-blue-100 rounded-lg py-2 transition-colors"
                  >
                    Ver qué me falta →
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Tab: Ofertas reales */}
        {tab === 'ofertas' && (
          <div className="space-y-3">
            {MOCK_OFERTAS.map((o) => (
              <div key={o.id} className="bg-white rounded-xl border border-gray-200 p-4">
                <div className="flex items-start justify-between gap-3 mb-2">
                  <div>
                    <h3 className="font-semibold text-gray-900 text-sm">{o.titulo}</h3>
                    <div className="flex flex-wrap items-center gap-2 mt-1">
                      <span className="flex items-center gap-1 text-xs text-gray-500">
                        <Building2 className="w-3 h-3" />{o.empresa}
                      </span>
                      <span className="flex items-center gap-1 text-xs text-gray-500">
                        <MapPin className="w-3 h-3" />{o.provincia}
                      </span>
                      <span className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full">{o.modalidad}</span>
                      <span className="flex items-center gap-1 text-xs text-gray-400">
                        <Clock className="w-3 h-3" />{o.publicada}
                      </span>
                    </div>
                  </div>
                </div>
                <MatchBar pct={o.match} />
                <div className="mt-3 flex flex-wrap gap-1">
                  {o.skills_ok.map((s) => (
                    <span key={s} className="text-[10px] bg-green-50 text-green-700 px-2 py-0.5 rounded-full">✓ {s}</span>
                  ))}
                  {o.skills_gap.map((s) => (
                    <span key={s} className="text-[10px] bg-red-50 text-red-600 px-2 py-0.5 rounded-full">✗ {s}</span>
                  ))}
                </div>
                <div className="mt-3 flex gap-2">
                  <button
                    onClick={() => router.push(`/mi-futuro-laboral/brecha?oferta=${o.id}&label=${encodeURIComponent(o.titulo)}`)}
                    className="flex-1 text-xs text-blue-600 font-medium bg-blue-50 hover:bg-blue-100 rounded-lg py-2 transition-colors"
                  >
                    Ver brecha exacta →
                  </button>
                  <a
                    href={o.url}
                    className="text-xs text-gray-500 font-medium bg-gray-50 hover:bg-gray-100 rounded-lg py-2 px-3 transition-colors"
                  >
                    Ver oferta
                  </a>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Tab: Formación */}
        {tab === 'formacion' && (
          <div className="space-y-3">
            <p className="text-xs text-gray-400 mb-4">
              Cursos que cierran las brechas más frecuentes de tu perfil, ordenados por impacto en tu empleabilidad.
            </p>
            {MOCK_CURSOS.map((c, i) => (
              <div key={i} className="bg-white rounded-xl border border-gray-200 p-4">
                <div className="flex items-start justify-between gap-3 mb-2">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-xs bg-orange-50 text-orange-600 font-medium px-2 py-0.5 rounded-full">
                        cierra: {c.skill}
                      </span>
                      <span className="text-xs text-green-600 font-bold flex items-center gap-0.5">
                        <TrendingUp className="w-3 h-3" />{c.impacto} match
                      </span>
                    </div>
                    <h3 className="font-semibold text-gray-900 text-sm">{c.nombre}</h3>
                    <div className="flex flex-wrap items-center gap-2 mt-1">
                      <span className="text-xs text-gray-500">{c.institucion}</span>
                      <span className="text-xs text-gray-400">·</span>
                      <span className="text-xs text-gray-500">{c.duracion}</span>
                      <span className="text-xs text-gray-400">·</span>
                      <span className="text-xs text-gray-500">{c.modalidad}</span>
                      {c.gratuito && (
                        <span className="text-[10px] bg-green-50 text-green-700 px-2 py-0.5 rounded-full font-medium">Gratuito</span>
                      )}
                    </div>
                  </div>
                </div>
                <button className="mt-2 w-full text-xs text-blue-600 font-medium bg-blue-50 hover:bg-blue-100 rounded-lg py-2 transition-colors">
                  Ver cómo inscribirme →
                </button>
              </div>
            ))}
          </div>
        )}

        {/* CTA generar reporte */}
        <div className="mt-8 bg-blue-600 rounded-2xl p-5 text-center text-white">
          <h2 className="font-bold text-base mb-1">¿Listo para la entrevista?</h2>
          <p className="text-blue-100 text-xs mb-4">
            Generá tu reporte con código QR para que el empleador vea tu análisis de competencias.
          </p>
          <button
            onClick={() => router.push('/mi-futuro-laboral/reporte')}
            className="inline-flex items-center gap-2 bg-white text-blue-700 text-sm font-semibold px-5 py-2.5 rounded-xl hover:bg-blue-50 transition-colors"
          >
            Generar mi reporte PDF + QR
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  )
}
