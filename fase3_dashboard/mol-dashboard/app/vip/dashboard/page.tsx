'use client'

import { useState, useEffect } from 'react'
import { BarChart3, Loader2, FlaskConical, Zap, PieChart, GraduationCap, Cpu, Share2, Timer, Wifi, ArrowRight } from 'lucide-react'
import Link from 'next/link'
import { createBrowserClient } from '@supabase/ssr'

let _supabase: ReturnType<typeof createBrowserClient> | null = null
function getSupabase() {
  if (!_supabase) _supabase = createBrowserClient(process.env.NEXT_PUBLIC_SUPABASE_URL!, process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!)
  return _supabase
}

const PROVINCIAS = [
  '', 'Buenos Aires', 'CABA', 'Catamarca', 'Chaco', 'Chubut', 'Córdoba',
  'Corrientes', 'Entre Ríos', 'Formosa', 'Jujuy', 'La Pampa', 'La Rioja',
  'Mendoza', 'Misiones', 'Neuquén', 'Río Negro', 'Salta', 'San Juan',
  'San Luis', 'Santa Cruz', 'Santa Fe', 'Santiago del Estero', 'Tierra del Fuego', 'Tucumán',
]

const PERIODOS = [
  { id: '7d', label: 'Última semana', days: 7 },
  { id: '30d', label: 'Último mes', days: 30 },
  { id: '90d', label: 'Últimos 3 meses', days: 90 },
  { id: '365d', label: 'Último año', days: 365 },
]

const LAB_INDICATORS = [
  { slug: 'tension-demanda', title: 'Tensión de Demanda', description: 'Persistencia x Insistencia por ocupación', href: '/vip/laboratorio/tension-demanda', icon: Zap },
  { slug: 'concentracion-ocupacional', title: 'Concentración Ocupacional', description: 'Índice HHI de concentración de ofertas', href: '/vip/laboratorio/concentracion-ocupacional', icon: PieChart },
  { slug: 'brecha-calificacion', title: 'Brecha de Calificación', description: 'Skills demandadas vs promedio del mercado', href: '/vip/laboratorio/brecha-calificacion', icon: GraduationCap },
  { slug: 'digitalizacion-sector', title: 'Digitalización por Sector', description: '% de skills digitales por sector CLAE', href: '/vip/laboratorio/digitalizacion-sector', icon: Cpu },
  { slug: 'transicion-skills', title: 'Transición Skills-Ocupación', description: 'Similitud entre ocupaciones por skills compartidas', href: '/vip/laboratorio/transicion-skills', icon: Share2 },
  { slug: 'velocidad-cobertura', title: 'Velocidad de Cobertura', description: 'Mediana de días para cubrir una posición', href: '/vip/laboratorio/velocidad-cobertura', icon: Timer },
  { slug: 'indice-remoto', title: 'Índice de Trabajo Remoto', description: 'Evolución de modalidades presencial/híbrido/remoto', href: '/vip/laboratorio/indice-remoto', icon: Wifi },
]

function getDateRange(periodoId: string) {
  const p = PERIODOS.find(x => x.id === periodoId)
  if (!p) return { desde: null, hasta: null }
  const hasta = new Date()
  const desde = new Date(hasta.getTime() - p.days * 86400000)
  return { desde: desde.toISOString().split('T')[0], hasta: hasta.toISOString().split('T')[0] }
}

export default function VipDashboardPage() {
  const [provincia, setProvincia] = useState('')
  const [periodo, setPeriodo] = useState('90d')
  const [panorama, setPanorama] = useState<any>(null)
  const [loadingKpis, setLoadingKpis] = useState(true)
  const [brechaData, setBrechaData] = useState<any>(null)
  const [loadingBrecha, setLoadingBrecha] = useState(true)

  useEffect(() => {
    const supabase = getSupabase()
    const { desde, hasta } = getDateRange(periodo)
    const filters: Record<string, any> = {}
    if (provincia) filters.provincia = provincia
    if (desde) { filters.fecha_desde = desde; filters.fecha_hasta = hasta }

    setLoadingKpis(true)
    supabase.rpc('get_panorama', { p_filters: filters }).then(({ data }) => {
      if (data) setPanorama(data)
      setLoadingKpis(false)
    })

    setLoadingBrecha(true)
    const brechaParams = new URLSearchParams({ estado: 'brecha', limit: '5' })
    if (provincia) brechaParams.set('provincia', provincia)
    fetch(`/api/laboratorio/brecha-formacion?${brechaParams}`)
      .then(r => r.ok ? r.json() : null)
      .then(data => { if (data) setBrechaData(data) })
      .catch(() => {})
      .finally(() => setLoadingBrecha(false))
  }, [provincia, periodo])

  const kpis = panorama?.kpis || {}

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-5xl mx-auto px-4 py-6">
        <div className="mb-5">
          <div className="flex items-center gap-2 mb-1">
            <BarChart3 className="w-5 h-5 text-amber-600" />
            <h1 className="text-xl font-bold text-gray-900">Panorama del Mercado Laboral</h1>
          </div>
          <p className="text-sm text-gray-500">Demanda de empleo en Argentina · datos MOL</p>
        </div>

        {/* Filters */}
        <div className="flex items-center gap-4 mb-6">
          <div>
            <label className="text-xs text-gray-500 mb-1 block">Territorio</label>
            <select value={provincia} onChange={e => setProvincia(e.target.value)} className="border rounded-lg px-3 py-2 text-sm min-w-[180px]">
              <option value="">Todo el país</option>
              {PROVINCIAS.filter(Boolean).map(p => <option key={p} value={p}>{p}</option>)}
            </select>
          </div>
          <div>
            <label className="text-xs text-gray-500 mb-1 block">Período</label>
            <select value={periodo} onChange={e => setPeriodo(e.target.value)} className="border rounded-lg px-3 py-2 text-sm">
              {PERIODOS.map(p => <option key={p.id} value={p.id}>{p.label}</option>)}
            </select>
          </div>
        </div>

        {/* KPIs */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-5">
          {loadingKpis ? (
            Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="bg-white rounded-xl border p-4 animate-pulse"><div className="h-6 bg-gray-100 rounded w-12" /></div>
            ))
          ) : (
            <>
              <KpiCard label="Ofertas activas" value={kpis.total_ofertas?.toLocaleString('es-AR') || '0'} />
              <KpiCard label="Ocupaciones distintas" value={kpis.ocupaciones_distintas?.toLocaleString('es-AR') || '0'} />
              <KpiCard label="Empresas" value={kpis.empresas_activas?.toLocaleString('es-AR') || '0'} />
              <KpiCard label="Provincias" value={kpis.provincias?.toString() || '0'} />
            </>
          )}
        </div>

        {/* Brecha de Formación */}
        <div className="bg-white rounded-xl border border-gray-200 p-5 mb-5">
          <div className="flex items-center gap-2 mb-1">
            <FlaskConical className="w-4 h-4 text-purple-600" />
            <h2 className="text-sm font-semibold text-gray-800">Brecha de Formación</h2>
            <span className="text-[10px] bg-amber-100 text-amber-700 px-1.5 py-0.5 rounded-full font-medium">Experimental</span>
          </div>
          <p className="text-xs text-gray-400 mb-3">Skills demandadas sin oferta educativa disponible</p>
          {loadingBrecha ? (
            <div className="animate-pulse space-y-2">{Array.from({length:3}).map((_,i) => <div key={i} className="h-4 bg-gray-100 rounded w-3/4" />)}</div>
          ) : brechaData ? (
            <div>
              <p className="text-sm text-gray-700 mb-3">
                <span className="font-semibold text-red-600">{brechaData.resumen?.pct_brecha || 0}%</span> de skills demandadas no tienen cursos en REGICE
              </p>
              {brechaData.skills?.slice(0, 5).map((s: any, i: number) => (
                <div key={s.skill_uri} className="flex items-center gap-2 py-0.5">
                  <span className="text-xs text-gray-400 w-4">{i + 1}.</span>
                  <span className="text-xs text-gray-700 flex-1 truncate">{s.skill_label}</span>
                  <span className="text-xs text-gray-500">{s.ofertas_count?.toLocaleString('es-AR')} ofertas</span>
                </div>
              ))}
              <Link href="/vip/laboratorio/brecha-calificacion" className="inline-flex items-center gap-1 text-xs text-purple-600 hover:text-purple-700 font-medium mt-3">
                Ver análisis completo <ArrowRight className="w-3 h-3" />
              </Link>
            </div>
          ) : <p className="text-xs text-gray-400">Sin datos</p>}
        </div>

        {/* Laboratorio */}
        <div className="mt-5">
          <div className="flex items-center gap-2 mb-3">
            <FlaskConical className="w-4 h-4 text-purple-600" />
            <h2 className="text-sm font-semibold text-gray-800">Indicadores experimentales</h2>
            <span className="text-[10px] bg-amber-100 text-amber-700 px-1.5 py-0.5 rounded-full font-medium">Experimental</span>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {LAB_INDICATORS.map(ind => (
              <Link key={ind.slug} href={ind.href} className="bg-white rounded-xl border border-gray-200 p-4 hover:border-purple-200 hover:shadow-sm transition-all group">
                <div className="flex items-start gap-3">
                  <div className="bg-gray-100 rounded-lg p-2 shrink-0"><ind.icon className="w-4 h-4 text-gray-600" /></div>
                  <div className="flex-1 min-w-0">
                    <h3 className="text-sm font-medium text-gray-900 mb-0.5">{ind.title}</h3>
                    <p className="text-xs text-gray-500 line-clamp-2">{ind.description}</p>
                  </div>
                  <ArrowRight className="w-4 h-4 text-gray-300 group-hover:text-purple-500 shrink-0 mt-0.5 transition-colors" />
                </div>
              </Link>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

function KpiCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-4">
      <p className="text-2xl font-bold text-gray-900">{value}</p>
      <p className="text-xs text-gray-500 mt-0.5">{label}</p>
    </div>
  )
}
