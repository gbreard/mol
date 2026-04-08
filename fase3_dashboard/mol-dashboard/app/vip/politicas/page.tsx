'use client'

import { useState, useEffect } from 'react'
import { Scale, BarChart3, Target, Loader2, FlaskConical, Zap, PieChart, GraduationCap, Cpu, Share2, Timer, Wifi, ArrowRight, ArrowUpDown } from 'lucide-react'
import Link from 'next/link'
import { createBrowserClient } from '@supabase/ssr'
import dynamic from 'next/dynamic'

const OccupationDetail = dynamic(() => import('@/components/OccupationDetail'), { loading: () => <LoadingPlaceholder /> })
const OccupationCompare = dynamic(() => import('@/components/OccupationCompare'), { loading: () => <LoadingPlaceholder /> })

function LoadingPlaceholder() {
  return (
    <div className="flex items-center justify-center py-12 gap-2 text-gray-400">
      <Loader2 className="w-5 h-5 animate-spin" />
      <span className="text-sm">Cargando...</span>
    </div>
  )
}

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
  { slug: 'tension-demanda', title: 'Tensión de Demanda', href: '/vip/laboratorio/tension-demanda', icon: Zap },
  { slug: 'concentracion-ocupacional', title: 'Concentración Ocupacional', href: '/vip/laboratorio/concentracion-ocupacional', icon: PieChart },
  { slug: 'brecha-calificacion', title: 'Brecha de Calificación', href: '/vip/laboratorio/brecha-calificacion', icon: GraduationCap },
  { slug: 'digitalizacion-sector', title: 'Digitalización por Sector', href: '/vip/laboratorio/digitalizacion-sector', icon: Cpu },
  { slug: 'transicion-skills', title: 'Transición Skills-Ocupación', href: '/vip/laboratorio/transicion-skills', icon: Share2 },
  { slug: 'velocidad-cobertura', title: 'Velocidad de Cobertura', href: '/vip/laboratorio/velocidad-cobertura', icon: Timer },
  { slug: 'indice-remoto', title: 'Índice de Trabajo Remoto', href: '/vip/laboratorio/indice-remoto', icon: Wifi },
]

type Section = 'mercado' | 'skills'
type SkillsTab = 'ocupaciones' | 'comparar'

function getDateRange(periodoId: string) {
  const p = PERIODOS.find(x => x.id === periodoId)
  if (!p) return { desde: null, hasta: null }
  const hasta = new Date()
  const desde = new Date(hasta.getTime() - p.days * 86400000)
  return { desde: desde.toISOString().split('T')[0], hasta: hasta.toISOString().split('T')[0] }
}

function barWidth(value: number, max: number) { return max > 0 ? `${Math.round((value / max) * 100)}%` : '0%' }

export default function VipPoliticasPage() {
  const [section, setSection] = useState<Section>('mercado')

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-6xl mx-auto px-4 py-6">
        <div className="mb-5">
          <div className="flex items-center gap-2 mb-1">
            <Scale className="w-5 h-5 text-blue-600" />
            <h1 className="text-xl font-bold text-gray-900">Políticas Laborales</h1>
          </div>
          <p className="text-sm text-gray-500">Inteligencia de mercado y análisis de ocupaciones para fundamentar políticas basadas en datos</p>
        </div>

        {/* Section tabs */}
        <div className="flex gap-1 bg-gray-100 rounded-lg p-1 w-fit mb-6">
          <button onClick={() => setSection('mercado')} className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${section === 'mercado' ? 'bg-white text-blue-700 shadow-sm' : 'text-gray-500 hover:text-gray-700'}`}>
            <BarChart3 className="w-4 h-4 inline mr-1.5" />Inteligencia de Mercado
          </button>
          <button onClick={() => setSection('skills')} className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${section === 'skills' ? 'bg-white text-blue-700 shadow-sm' : 'text-gray-500 hover:text-gray-700'}`}>
            <Target className="w-4 h-4 inline mr-1.5" />Skills Intelligence
          </button>
        </div>

        {section === 'mercado' && <InteligenciaMercadoSection />}
        {section === 'skills' && <SkillsIntelligenceSection />}
      </div>
    </div>
  )
}

// ============================================================
// Section 1: Inteligencia de Mercado (M4 completo)
// ============================================================

function InteligenciaMercadoSection() {
  const [provincia, setProvincia] = useState('')
  const [periodo, setPeriodo] = useState('90d')
  const [panorama, setPanorama] = useState<any>(null)
  const [brechaData, setBrechaData] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const supabase = getSupabase()
    const { desde, hasta } = getDateRange(periodo)
    const filters: Record<string, any> = {}
    if (provincia) filters.provincia = provincia
    if (desde) { filters.fecha_desde = desde; filters.fecha_hasta = hasta }

    setLoading(true)
    supabase.rpc('get_panorama', { p_filters: filters }).then(({ data }) => { if (data) setPanorama(data) })

    const brechaParams = new URLSearchParams({ estado: 'brecha', limit: '5' })
    if (provincia) brechaParams.set('provincia', provincia)
    fetch(`/api/laboratorio/brecha-formacion?${brechaParams}`)
      .then(r => r.ok ? r.json() : null)
      .then(data => { if (data) setBrechaData(data) })
      .finally(() => setLoading(false))
  }, [provincia, periodo])

  const kpis = panorama?.kpis || {}

  return (
    <div className="space-y-5">
      {/* Filters */}
      <div className="flex items-center gap-4">
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
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <KpiCard label="Ofertas activas" value={kpis.total_ofertas?.toLocaleString('es-AR') || '—'} />
        <KpiCard label="Ocupaciones distintas" value={kpis.ocupaciones_distintas?.toLocaleString('es-AR') || '—'} />
        <KpiCard label="Empresas" value={kpis.empresas_activas?.toLocaleString('es-AR') || '—'} />
        <KpiCard label="Provincias" value={kpis.provincias?.toString() || '—'} />
      </div>

      {/* Brecha */}
      {brechaData && (
        <div className="bg-white rounded-xl border p-5">
          <div className="flex items-center gap-2 mb-1">
            <FlaskConical className="w-4 h-4 text-purple-600" />
            <h2 className="text-sm font-semibold text-gray-800">Brecha de Formación</h2>
            <span className="text-[10px] bg-amber-100 text-amber-700 px-1.5 py-0.5 rounded-full font-medium">Experimental</span>
          </div>
          <p className="text-sm text-gray-700 my-2"><span className="font-semibold text-red-600">{brechaData.resumen?.pct_brecha || 0}%</span> de skills demandadas no tienen cursos en REGICE</p>
          {brechaData.skills?.slice(0, 5).map((s: any, i: number) => (
            <div key={s.skill_uri} className="flex items-center gap-2 py-0.5">
              <span className="text-xs text-gray-400 w-4">{i + 1}.</span>
              <span className="text-xs text-gray-700 flex-1 truncate">{s.skill_label}</span>
              <span className="text-xs text-gray-500">{s.ofertas_count?.toLocaleString('es-AR')} ofertas</span>
            </div>
          ))}
          <Link href="/vip/laboratorio/brecha-formacion" className="inline-flex items-center gap-1 text-xs text-purple-600 hover:text-purple-700 font-medium mt-3">
            Ver análisis completo <ArrowRight className="w-3 h-3" />
          </Link>
        </div>
      )}

      {/* Laboratorio */}
      <div>
        <div className="flex items-center gap-2 mb-3">
          <FlaskConical className="w-4 h-4 text-purple-600" />
          <h2 className="text-sm font-semibold text-gray-800">Indicadores experimentales</h2>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {LAB_INDICATORS.map(ind => (
            <Link key={ind.slug} href={ind.href} className="bg-white rounded-xl border p-4 hover:border-purple-200 hover:shadow-sm transition-all group">
              <div className="flex items-center gap-3">
                <div className="bg-gray-100 rounded-lg p-2 shrink-0"><ind.icon className="w-4 h-4 text-gray-600" /></div>
                <span className="text-sm font-medium text-gray-900 flex-1">{ind.title}</span>
                <ArrowRight className="w-4 h-4 text-gray-300 group-hover:text-purple-500 shrink-0 transition-colors" />
              </div>
            </Link>
          ))}
        </div>
      </div>
    </div>
  )
}

// ============================================================
// Section 2: Skills Intelligence
// ============================================================

function SkillsIntelligenceSection() {
  const [activeTab, setActiveTab] = useState<'ocupaciones' | 'comparar'>('ocupaciones')
  const [occupationsData, setOccupationsData] = useState<any>(null)
  const [occupationsList, setOccupationsList] = useState<any[]>([])
  const [loadingData, setLoadingData] = useState(false)

  useEffect(() => {
    if (occupationsData) return
    setLoadingData(true)
    Promise.all([
      fetch('/data/occupation_full_detail.json').then(r => r.json()),
      fetch('/data/occupations_index.json').then(r => r.json()),
    ]).then(([fullDetail, indexData]) => {
      setOccupationsData(fullDetail)
      setOccupationsList(
        Object.entries(indexData as Record<string, { label: string; isco: string }>)
          .map(([id, occ]) => ({ id, label: occ.label, isco: occ.isco }))
          .sort((a, b) => a.label.localeCompare(b.label))
      )
    }).catch(() => {}).finally(() => setLoadingData(false))
  }, [occupationsData])

  return (
    <div className="bg-white rounded-xl border overflow-hidden">
      <div className="border-b px-4 py-3">
        <div className="flex gap-1 bg-gray-100 rounded-lg p-1 w-fit">
          <button onClick={() => setActiveTab('ocupaciones')} className={`px-4 py-1.5 rounded-md text-sm font-medium transition-colors ${activeTab === 'ocupaciones' ? 'bg-white text-blue-700 shadow-sm' : 'text-gray-500'}`}>Ocupaciones</button>
          <button onClick={() => setActiveTab('comparar')} className={`px-4 py-1.5 rounded-md text-sm font-medium transition-colors ${activeTab === 'comparar' ? 'bg-white text-blue-700 shadow-sm' : 'text-gray-500'}`}>Comparar</button>
        </div>
      </div>
      <div className="p-4 text-[13px]">
        {loadingData ? <LoadingPlaceholder /> : (
          <>
            {activeTab === 'ocupaciones' && occupationsData && <OccupationDetail occupationsData={occupationsData} occupationsList={occupationsList} />}
            {activeTab === 'comparar' && occupationsData && <OccupationCompare occupationsData={occupationsData} occupationsList={occupationsList} />}
          </>
        )}
      </div>
    </div>
  )
}

function KpiCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-white rounded-xl border p-4">
      <p className="text-2xl font-bold text-gray-900">{value}</p>
      <p className="text-xs text-gray-500 mt-0.5">{label}</p>
    </div>
  )
}
