'use client'

import { useState, useEffect, useCallback } from 'react'
import { Loader2, FlaskConical } from 'lucide-react'
import { OEBreadcrumb } from '@/components/oficina-empleo/OEBreadcrumb'

const PROVINCIAS_MOL = [
  '', 'Buenos Aires', 'CABA', 'Catamarca', 'Chaco', 'Chubut', 'Corrientes',
  'Córdoba', 'Entre Ríos', 'Formosa', 'Jujuy', 'La Pampa', 'La Rioja',
  'Mendoza', 'Misiones', 'Neuquén', 'Río Negro', 'Salta', 'San Juan',
  'San Luis', 'Santa Cruz', 'Santa Fe', 'Santiago del Estero',
  'Tierra del Fuego', 'Tucumán',
]

type Tab = 'brecha' | 'cubierta' | 'todo'

interface SkillBrecha {
  skill_uri: string
  skill_label: string
  ofertas_count: number
  cursos_count: number
  estado: string
  pct_mercado?: number
}

interface Resumen {
  total_skills: number
  brechas: number
  cubiertas: number
  pct_brecha: number
}

export default function BrechaFormacionPage() {
  const [tab, setTab] = useState<Tab>('brecha')
  const [provincia, setProvincia] = useState('')
  const [skills, setSkills] = useState<SkillBrecha[]>([])
  const [resumen, setResumen] = useState<Resumen | null>(null)
  const [loading, setLoading] = useState(true)
  const [offset, setOffset] = useState(0)
  const [hasMore, setHasMore] = useState(true)
  const [calculadoEn, setCalculadoEn] = useState<string | null>(null)

  const fetchData = useCallback(async (estado: Tab, prov: string, off: number, append: boolean) => {
    setLoading(true)
    const params = new URLSearchParams()
    if (estado !== 'todo') params.set('estado', estado)
    if (prov) params.set('provincia', prov)
    params.set('limit', '20')
    params.set('offset', String(off))

    try {
      const res = await fetch(`/api/laboratorio/brecha-formacion?${params}`)
      if (!res.ok) throw new Error()
      const data = await res.json()
      setSkills(prev => append ? [...prev, ...data.skills] : data.skills)
      setResumen(data.resumen)
      setCalculadoEn(data.calculado_en)
      setHasMore(data.skills.length === 20)
    } catch {} finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    setOffset(0)
    setSkills([])
    fetchData(tab, provincia, 0, false)
  }, [tab, provincia, fetchData])

  function loadMore() {
    const next = offset + 20
    setOffset(next)
    fetchData(tab, provincia, next, true)
  }

  const maxOfertas = skills.length > 0 ? Math.max(...skills.map(s => s.ofertas_count)) : 1

  return (
    <div className="p-8 max-w-6xl mx-auto space-y-6">
      <OEBreadcrumb items={[
        { label: 'Indicadores', href: '/oficina-empleo' },
        { label: 'Brecha de Formación' },
      ]} />

      {/* Header */}
      <div className="flex items-center gap-3 mb-2">
        <div className="bg-gradient-to-br from-purple-500 to-purple-600 rounded-lg p-2.5 shadow-md">
          <FlaskConical className="w-5 h-5 text-white" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold text-gray-900">Brecha de Formación</h1>
            <span className="text-[10px] bg-amber-100 text-amber-700 px-2 py-0.5 rounded-full font-medium border border-amber-200">EXPERIMENTAL</span>
          </div>
          <p className="text-sm text-gray-500">Skills demandadas por el mercado vs oferta educativa en REGICE</p>
        </div>
      </div>

      {/* Filtro provincia */}
      <div>
        <label className="text-xs text-gray-500 mb-1 block">Provincia</label>
        <select
          value={provincia}
          onChange={e => setProvincia(e.target.value)}
          className="border rounded-lg px-3 py-2 text-sm min-w-[200px]"
        >
          <option value="">Todo el país</option>
          {PROVINCIAS_MOL.filter(Boolean).map(p => (
            <option key={p} value={p}>{p}</option>
          ))}
        </select>
      </div>

      {/* KPIs */}
      {resumen && (
        <div className="grid grid-cols-3 gap-4">
          <div className="bg-white rounded-xl border border-gray-200 p-4">
            <p className="text-2xl font-bold text-gray-900">{resumen.total_skills.toLocaleString('es-AR')}</p>
            <p className="text-xs text-gray-500">Skills totales</p>
          </div>
          <div className="bg-white rounded-xl border border-red-100 p-4">
            <p className="text-2xl font-bold text-red-600">{resumen.brechas.toLocaleString('es-AR')}</p>
            <p className="text-xs text-gray-500">Brecha · {resumen.pct_brecha}%</p>
          </div>
          <div className="bg-white rounded-xl border border-green-100 p-4">
            <p className="text-2xl font-bold text-green-600">{resumen.cubiertas.toLocaleString('es-AR')}</p>
            <p className="text-xs text-gray-500">Cubiertas · {100 - resumen.pct_brecha}%</p>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="flex items-center gap-1 bg-gray-100 rounded-lg p-1 w-fit">
        {([['brecha', 'Brecha'], ['cubierta', 'Cobertura'], ['todo', 'Todo']] as [Tab, string][]).map(([id, label]) => (
          <button
            key={id}
            onClick={() => setTab(id)}
            className={`px-4 py-1.5 rounded-md text-sm font-medium transition-colors ${
              tab === id ? 'bg-white text-purple-700 shadow-sm' : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      {/* Skills list */}
      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        {loading && skills.length === 0 ? (
          <div className="p-8 flex items-center justify-center gap-2 text-gray-400">
            <Loader2 className="w-4 h-4 animate-spin" />
            <span className="text-sm">Cargando...</span>
          </div>
        ) : skills.length === 0 ? (
          <div className="p-8 text-center text-sm text-gray-400">Sin datos</div>
        ) : (
          <>
            <div className="divide-y">
              {skills.map((s, i) => (
                <div key={s.skill_uri} className="px-4 py-3 flex items-center gap-3">
                  <span className="text-xs text-gray-400 w-6 shrink-0">{i + 1}.</span>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-gray-900">{s.skill_label}</p>
                    <p className="text-xs text-gray-400">
                      {s.ofertas_count.toLocaleString('es-AR')} ofertas · {s.cursos_count} curso{s.cursos_count !== 1 ? 's' : ''}
                      {s.pct_mercado != null && ` · ${s.pct_mercado}% del mercado`}
                    </p>
                  </div>
                  <div className="w-24 shrink-0">
                    <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full ${s.estado === 'brecha' ? 'bg-red-400' : 'bg-green-400'}`}
                        style={{ width: `${(s.ofertas_count / maxOfertas) * 100}%` }}
                      />
                    </div>
                  </div>
                  <span className={`text-[10px] px-2 py-0.5 rounded-full font-medium shrink-0 ${
                    s.estado === 'brecha' ? 'bg-red-50 text-red-600' : 'bg-green-50 text-green-600'
                  }`}>
                    {s.estado}
                  </span>
                </div>
              ))}
            </div>
            {hasMore && (
              <div className="p-3 border-t">
                <button
                  onClick={loadMore}
                  disabled={loading}
                  className="w-full text-sm text-purple-600 hover:text-purple-700 font-medium py-1 disabled:opacity-50"
                >
                  {loading ? 'Cargando...' : 'Cargar más'}
                </button>
              </div>
            )}
          </>
        )}
      </div>

      {calculadoEn && (
        <p className="text-[10px] text-gray-400 text-right">
          Último cálculo: {new Date(calculadoEn).toLocaleDateString('es-AR')}
        </p>
      )}
    </div>
  )
}
