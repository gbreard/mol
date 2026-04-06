'use client'

import { useState, useEffect, useCallback } from 'react'
import { BarChart3, Loader2 } from 'lucide-react'
import { createBrowserClient } from '@supabase/ssr'
import { OEBreadcrumb } from '@/components/oficina-empleo/OEBreadcrumb'

const PROVINCIAS = [
  '', 'Buenos Aires', 'CABA', 'Catamarca', 'Chaco', 'Chubut', 'Córdoba',
  'Corrientes', 'Entre Ríos', 'Formosa', 'Jujuy', 'La Pampa', 'La Rioja',
  'Mendoza', 'Misiones', 'Neuquén', 'Río Negro', 'Salta', 'San Juan',
  'San Luis', 'Santa Cruz', 'Santa Fe', 'Santiago del Estero',
  'Tierra del Fuego', 'Tucumán',
]

const PERIODOS: { id: string; label: string; days: number }[] = [
  { id: '7d', label: 'Última semana', days: 7 },
  { id: '30d', label: 'Último mes', days: 30 },
  { id: '90d', label: 'Últimos 3 meses', days: 90 },
  { id: '365d', label: 'Último año', days: 365 },
]

function getDateRange(periodoId: string): { desde: string | null; hasta: string | null } {
  const p = PERIODOS.find(x => x.id === periodoId)
  if (!p) return { desde: null, hasta: null }
  const hasta = new Date()
  const desde = new Date(hasta.getTime() - p.days * 24 * 60 * 60 * 1000)
  return { desde: desde.toISOString().split('T')[0], hasta: hasta.toISOString().split('T')[0] }
}

function barWidth(value: number, max: number) {
  return max > 0 ? `${Math.round((value / max) * 100)}%` : '0%'
}

export default function DashboardEjecutivoPage() {
  const [provincia, setProvincia] = useState('')
  const [periodo, setPeriodo] = useState('90d')

  // Data per block
  const [panorama, setPanorama] = useState<any>(null)
  const [sectores, setSectores] = useState<any[]>([])
  const [evolucion, setEvolucion] = useState<any[]>([])
  const [requerimientos, setRequerimientos] = useState<any>(null)
  const [topSkills, setTopSkills] = useState<any[]>([])

  // Loading per block
  const [loadingKpis, setLoadingKpis] = useState(true)
  const [loadingSectores, setLoadingSectores] = useState(true)
  const [loadingEvol, setLoadingEvol] = useState(true)
  const [loadingReqs, setLoadingReqs] = useState(true)
  const [loadingSkills, setLoadingSkills] = useState(true)

  const fetchAll = useCallback(async (prov: string, per: string) => {
    const supabase = createBrowserClient(
      process.env.NEXT_PUBLIC_SUPABASE_URL!,
      process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
    )
    const { desde, hasta } = getDateRange(per)
    const p_provincia = prov || null
    const p_fecha_desde = desde
    const p_fecha_hasta = hasta

    setLoadingKpis(true); setLoadingSectores(true); setLoadingEvol(true); setLoadingReqs(true); setLoadingSkills(true)

    // All in parallel
    const [r1, r2, r3, r4, r5] = await Promise.all([
      supabase.rpc('get_panorama', { p_provincia, p_fecha_desde, p_fecha_hasta }),
      supabase.rpc('get_sidebar_counts', { p_provincia, p_fecha_desde, p_fecha_hasta }),
      supabase.rpc('get_evolucion', {
        p_filters: JSON.stringify(prov ? { provincia: prov } : {}),
        p_periodos: per === '7d' ? 7 : per === '30d' ? 4 : per === '365d' ? 12 : 13,
      }),
      supabase.rpc('get_requerimientos', { p_provincia, p_fecha_desde, p_fecha_hasta }),
      supabase.rpc('get_skills_resumen', { p_provincia, p_fecha_desde, p_fecha_hasta, p_limit: 10 }),
    ])

    if (r1.data) setPanorama(r1.data)
    setLoadingKpis(false)

    if (r2.data?.sectores) setSectores(r2.data.sectores)
    setLoadingSectores(false)

    if (r3.data?.periodos) setEvolucion(r3.data.periodos)
    setLoadingEvol(false)

    if (r4.data) setRequerimientos(r4.data)
    setLoadingReqs(false)

    if (r5.data?.top_skills) setTopSkills(r5.data.top_skills)
    else if (r5.data?.por_l1) setTopSkills(r5.data.por_l1)
    setLoadingSkills(false)
  }, [])

  useEffect(() => {
    fetchAll(provincia, periodo)
  }, [provincia, periodo, fetchAll])

  const kpis = panorama?.kpis || {}
  const maxSector = sectores.length > 0 ? Math.max(...sectores.map((s: any) => s.count)) : 1
  const maxEvol = evolucion.length > 0 ? Math.max(...evolucion.map((e: any) => e.ofertas)) : 1
  const maxSkill = topSkills.length > 0 ? Math.max(...topSkills.map((s: any) => s.value || s.count || 0)) : 1

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-5xl mx-auto px-4 py-6">
        <OEBreadcrumb items={[{ label: 'Inteligencia del Mercado' }]} />

        {/* Header + Filters */}
        <div className="mb-5">
          <div className="flex items-center gap-2 mb-1">
            <BarChart3 className="w-5 h-5 text-amber-600" />
            <h1 className="text-xl font-bold text-gray-900">Panorama del Mercado Laboral</h1>
          </div>
          <p className="text-sm text-gray-500">Demanda de empleo en Argentina · datos MOL</p>
        </div>

        <div className="flex items-center gap-4 mb-6">
          <div>
            <label className="text-xs text-gray-500 mb-1 block">Territorio</label>
            <select
              value={provincia}
              onChange={e => setProvincia(e.target.value)}
              className="border rounded-lg px-3 py-2 text-sm min-w-[180px]"
            >
              <option value="">Todo el país</option>
              {PROVINCIAS.filter(Boolean).map(p => (
                <option key={p} value={p}>{p}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="text-xs text-gray-500 mb-1 block">Período</label>
            <select
              value={periodo}
              onChange={e => setPeriodo(e.target.value)}
              className="border rounded-lg px-3 py-2 text-sm"
            >
              {PERIODOS.map(p => (
                <option key={p.id} value={p.id}>{p.label}</option>
              ))}
            </select>
          </div>
        </div>

        {/* Bloque 1 — KPIs */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-5">
          {loadingKpis ? (
            Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="bg-white rounded-xl border border-gray-200 p-4 animate-pulse">
                <div className="h-4 bg-gray-100 rounded w-16 mb-2" />
                <div className="h-6 bg-gray-100 rounded w-12" />
              </div>
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

        {/* Bloque 2 — Sectores */}
        <div className="bg-white rounded-xl border border-gray-200 p-5 mb-5">
          <h2 className="text-sm font-semibold text-gray-800 mb-3">Sectores con mayor demanda</h2>
          {loadingSectores ? (
            <Skeleton lines={6} />
          ) : (
            <div className="space-y-2">
              {sectores.slice(0, 8).map((s: any, i: number) => (
                <div key={i} className="flex items-center gap-3">
                  <span className="text-xs text-gray-600 w-48 truncate shrink-0">{s.sector}</span>
                  <div className="flex-1 h-4 bg-gray-100 rounded overflow-hidden">
                    <div className="h-full bg-amber-500 rounded" style={{ width: barWidth(s.count, maxSector) }} />
                  </div>
                  <span className="text-xs font-medium text-gray-700 w-12 text-right shrink-0">{s.count?.toLocaleString('es-AR')}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Bloque 3 — Evolución */}
        <div className="bg-white rounded-xl border border-gray-200 p-5 mb-5">
          <h2 className="text-sm font-semibold text-gray-800 mb-3">Evolución de ofertas publicadas</h2>
          {loadingEvol ? (
            <Skeleton lines={4} />
          ) : evolucion.length === 0 ? (
            <p className="text-xs text-gray-400">Sin datos de evolución</p>
          ) : (
            <div className="flex items-end gap-1 h-32">
              {evolucion.map((e: any, i: number) => (
                <div key={i} className="flex-1 flex flex-col items-center gap-1">
                  <div className="w-full bg-amber-200 rounded-t" style={{ height: `${Math.max((e.ofertas / maxEvol) * 100, 2)}%` }} />
                  <span className="text-[9px] text-gray-400 leading-tight text-center">{e.label?.split(' ')[0]}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5 mb-5">
          {/* Bloque 4 — Requerimientos */}
          <div className="bg-white rounded-xl border border-gray-200 p-5">
            <h2 className="text-sm font-semibold text-gray-800 mb-3">Perfil de los puestos demandados</h2>
            {loadingReqs ? (
              <Skeleton lines={5} />
            ) : requerimientos ? (
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <p className="text-xs font-medium text-gray-500 mb-2">Nivel educativo</p>
                  {(requerimientos.educacion || []).slice(0, 5).map((r: any, i: number) => (
                    <div key={i} className="flex justify-between text-xs py-0.5">
                      <span className="text-gray-600 capitalize">{r.name}</span>
                      <span className="text-gray-500 font-medium">{r.porcentaje}%</span>
                    </div>
                  ))}
                </div>
                <div>
                  <p className="text-xs font-medium text-gray-500 mb-2">Seniority</p>
                  {(requerimientos.seniority || []).slice(0, 5).map((r: any, i: number) => (
                    <div key={i} className="flex justify-between text-xs py-0.5">
                      <span className="text-gray-600 capitalize">{r.name}</span>
                      <span className="text-gray-500 font-medium">{r.porcentaje}%</span>
                    </div>
                  ))}
                </div>
                <div>
                  <p className="text-xs font-medium text-gray-500 mb-2">Modalidad</p>
                  {(requerimientos.modalidad || []).slice(0, 5).map((r: any, i: number) => (
                    <div key={i} className="flex justify-between text-xs py-0.5">
                      <span className="text-gray-600 capitalize">{r.name}</span>
                      <span className="text-gray-500 font-medium">{r.porcentaje}%</span>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <p className="text-xs text-gray-400">Sin datos</p>
            )}
          </div>

          {/* Bloque 5 — Top skills */}
          <div className="bg-white rounded-xl border border-gray-200 p-5">
            <h2 className="text-sm font-semibold text-gray-800 mb-3">Competencias más demandadas</h2>
            {loadingSkills ? (
              <Skeleton lines={6} />
            ) : (
              <div className="space-y-2">
                {topSkills.slice(0, 10).map((s: any, i: number) => {
                  const value = s.value || s.count || 0
                  return (
                    <div key={i} className="flex items-center gap-2">
                      <span className="text-xs text-gray-400 w-4 shrink-0">{i + 1}.</span>
                      <span className="text-xs text-gray-700 flex-1 truncate">{s.name || s.label}</span>
                      <div className="w-16 h-1.5 bg-gray-100 rounded-full overflow-hidden shrink-0">
                        <div className="h-full bg-amber-500 rounded-full" style={{ width: barWidth(value, maxSkill) }} />
                      </div>
                      <span className="text-xs text-gray-500 w-12 text-right shrink-0">{value.toLocaleString('es-AR')}</span>
                    </div>
                  )
                })}
              </div>
            )}
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

function Skeleton({ lines }: { lines: number }) {
  return (
    <div className="space-y-2 animate-pulse">
      {Array.from({ length: lines }).map((_, i) => (
        <div key={i} className="h-4 bg-gray-100 rounded" style={{ width: `${70 + Math.random() * 30}%` }} />
      ))}
    </div>
  )
}
