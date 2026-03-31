'use client'

import { useState, useEffect, useCallback } from 'react'
import { useRouter, useParams } from 'next/navigation'
import {
  ArrowLeft, User, Briefcase, BookOpen, ClipboardList,
  TrendingUp, Plus, ChevronRight, CheckCircle, Clock,
  Building2, MapPin, AlertTriangle, Edit3, Send, Loader2,
} from 'lucide-react'

// ─── Types ───────────────────────────────────────────────────────────────────

interface Persona {
  id: string
  nombre: string
  dni: string
  edad: number
  nivel_educativo: string
  ubicacion: string
  telefono: string
  email: string
}

interface Caso {
  id: string
  persona_id: string
  estado: string
  objetivo: string
  prioridad: string
  nota_tecnico: string
  created_at: string
}

interface Skill {
  id: string
  skill_uri: string
  skill_label: string
  via_captura: string
  estado: string
  confianza: number
}

interface MatchedOffer {
  id_oferta: string
  titulo: string
  empresa: string
  provincia: string
  isco_code: string
  match_score: number
  skills_cubiertas: number
  skills_oferta_total: number
  skills_detalle: Array<{
    skill: string
    similarity: number
    matched_by: string
    exact: boolean
  }>
}

// ─── State machine ───────────────────────────────────────────────────────────

const ESTADO_CONFIG: Record<string, { label: string; color: string; next?: string[] }> = {
  nuevo: { label: 'Nuevo', color: 'bg-gray-100 text-gray-600', next: ['en_diagnostico'] },
  en_diagnostico: { label: 'En diagnóstico', color: 'bg-blue-100 text-blue-700', next: ['perfil_completo'] },
  perfil_completo: { label: 'Perfil completo', color: 'bg-purple-100 text-purple-700', next: ['derivado_vacante', 'derivado_curso', 'en_seguimiento'] },
  derivado_vacante: { label: 'Derivado vacante', color: 'bg-green-100 text-green-700', next: ['en_seguimiento', 'insertado'] },
  derivado_curso: { label: 'Derivado curso', color: 'bg-orange-100 text-orange-700', next: ['en_seguimiento'] },
  en_seguimiento: { label: 'En seguimiento', color: 'bg-yellow-100 text-yellow-700', next: ['insertado', 'cerrado'] },
  insertado: { label: 'Insertado', color: 'bg-emerald-100 text-emerald-700', next: ['cerrado'] },
  cerrado: { label: 'Cerrado', color: 'bg-gray-100 text-gray-500', next: [] },
}

const TABS = [
  { id: 'perfil', label: 'Perfil', icon: User },
  { id: 'vacantes', label: 'Vacantes', icon: Briefcase },
  { id: 'notas', label: 'Notas', icon: ClipboardList },
]

function MatchBar({ pct }: { pct: number }) {
  const color = pct >= 50 ? 'bg-green-500' : pct >= 30 ? 'bg-blue-500' : 'bg-yellow-400'
  const text = pct >= 50 ? 'text-green-600' : pct >= 30 ? 'text-blue-600' : 'text-yellow-600'
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 bg-gray-100 rounded-full overflow-hidden">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${Math.min(pct, 100)}%` }} />
      </div>
      <span className={`text-xs font-bold tabular-nums ${text}`}>{pct}%</span>
    </div>
  )
}

function ViaCapturaBadge({ via }: { via: string }) {
  const config: Record<string, { label: string; color: string }> = {
    ocupacion: { label: 'Ocupación', color: 'bg-blue-50 text-blue-600' },
    tarea: { label: 'Tarea', color: 'bg-purple-50 text-purple-600' },
    texto: { label: 'Texto', color: 'bg-orange-50 text-orange-600' },
    formacion: { label: 'Formación', color: 'bg-green-50 text-green-600' },
  }
  const c = config[via] || { label: via, color: 'bg-gray-50 text-gray-600' }
  return <span className={`text-[10px] px-1.5 py-0.5 rounded ${c.color}`}>{c.label}</span>
}

// ─── Component ───────────────────────────────────────────────────────────────

export default function DetalleCasoPage() {
  const router = useRouter()
  const params = useParams()
  const casoId = params.id as string

  const [tab, setTab] = useState('perfil')
  const [nota, setNota] = useState('')
  const [loading, setLoading] = useState(true)
  const [matchLoading, setMatchLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Data
  const [persona, setPersona] = useState<Persona | null>(null)
  const [caso, setCaso] = useState<Caso | null>(null)
  const [skills, setSkills] = useState<Skill[]>([])
  const [offers, setOffers] = useState<MatchedOffer[]>([])
  const [matchStats, setMatchStats] = useState<{ expanded: number; total: number } | null>(null)

  // Fetch case data
  useEffect(() => {
    async function loadCaso() {
      setLoading(true)
      setError(null)
      try {
        const res = await fetch(`/api/casos/${casoId}`)
        if (!res.ok) throw new Error(`Error ${res.status}`)
        const data = await res.json()

        setCaso(data.caso)
        setPersona(data.persona)

        // Skills come from the perfil included in the caso response
        if (data.perfil?.skills) {
          setSkills(data.perfil.skills)
        }
      } catch (e) {
        setError((e as Error).message)
      } finally {
        setLoading(false)
      }
    }
    if (casoId) loadCaso()
  }, [casoId])

  // Fetch semantic matches when switching to vacantes tab
  const loadMatches = useCallback(async () => {
    if (skills.length === 0) return
    setMatchLoading(true)
    try {
      const skillUris = skills.map(s => s.skill_uri).join(',')
      const res = await fetch(
        `/api/matching-offers-semantic?skill_uris=${encodeURIComponent(skillUris)}&limit=20&threshold=0.60`
      )
      if (!res.ok) throw new Error(`Error ${res.status}`)
      const data = await res.json()
      setOffers(data.offers || [])
      setMatchStats({ expanded: data.expanded_skills || 0, total: data.total || 0 })
    } catch (e) {
      console.error('Error loading matches:', e)
    } finally {
      setMatchLoading(false)
    }
  }, [skills])

  useEffect(() => {
    if (tab === 'vacantes' && offers.length === 0 && skills.length > 0) {
      loadMatches()
    }
  }, [tab, offers.length, skills.length, loadMatches])

  // Change state
  const handleCambiarEstado = async (nuevoEstado: string) => {
    if (!caso) return
    setCaso({ ...caso, estado: nuevoEstado })
    try {
      await fetch(`/api/casos/${casoId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ estado: nuevoEstado }),
      })
    } catch (e) {
      console.error('Error updating estado:', e)
    }
  }

  // Save note
  const handleGuardarNota = async () => {
    if (!nota.trim() || !caso) return
    try {
      await fetch(`/api/casos/${casoId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ nota_tecnico: nota }),
      })
      setNota('')
    } catch (e) {
      console.error('Error saving note:', e)
    }
  }

  // Loading state
  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="flex items-center gap-3 text-gray-500">
          <Loader2 className="w-5 h-5 animate-spin" />
          <span className="text-sm">Cargando caso...</span>
        </div>
      </div>
    )
  }

  if (error || !persona || !caso) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <AlertTriangle className="w-8 h-8 text-red-400 mx-auto mb-2" />
          <p className="text-sm text-gray-600">{error || 'Caso no encontrado'}</p>
          <button onClick={() => router.back()} className="mt-3 text-sm text-teal-600 hover:underline">
            Volver
          </button>
        </div>
      </div>
    )
  }

  const est = ESTADO_CONFIG[caso.estado] || ESTADO_CONFIG.nuevo
  const confirmedSkills = skills.filter(s => s.estado === 'confirmada')
  const suggestedSkills = skills.filter(s => s.estado === 'sugerida')

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-5xl mx-auto px-4 py-6">

        {/* Back */}
        <button
          onClick={() => router.back()}
          className="flex items-center gap-1.5 text-sm text-gray-500 hover:text-gray-700 mb-4 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" /> Cartera de casos
        </button>

        {/* Header */}
        <div className="bg-white rounded-xl border border-gray-200 p-4 mb-4">
          <div className="flex items-start justify-between gap-3">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-full bg-teal-100 text-teal-700 text-sm font-bold flex items-center justify-center shrink-0">
                {persona.nombre.split(' ').map(n => n[0]).join('').slice(0, 2)}
              </div>
              <div>
                <h1 className="text-lg font-bold text-gray-900">{persona.nombre}</h1>
                <div className="flex flex-wrap items-center gap-2 mt-0.5">
                  {persona.dni && <span className="text-xs text-gray-400">DNI {persona.dni}</span>}
                  {persona.edad && (
                    <>
                      <span className="text-gray-200">·</span>
                      <span className="text-xs text-gray-400">{persona.edad} años</span>
                    </>
                  )}
                  {persona.ubicacion && (
                    <>
                      <span className="text-gray-200">·</span>
                      <span className="text-xs text-gray-400">{persona.ubicacion}</span>
                    </>
                  )}
                </div>
              </div>
            </div>
            <div className="flex items-center gap-2 shrink-0">
              <span className={`text-xs px-2.5 py-1 rounded-full font-medium ${est.color}`}>
                {est.label}
              </span>
              <span className="text-xs text-gray-400">{skills.length} skills</span>
            </div>
          </div>

          {/* State transitions */}
          {(est.next ?? []).length > 0 && (
            <div className="mt-3 pt-3 border-t border-gray-100 flex flex-wrap gap-2">
              <span className="text-xs text-gray-500 self-center">Pasar a:</span>
              {(est.next ?? []).map(s => (
                <button
                  key={s}
                  onClick={() => handleCambiarEstado(s)}
                  className="text-xs border border-gray-200 text-gray-600 px-3 py-1 rounded-full hover:border-teal-400 hover:text-teal-700 transition-colors"
                >
                  {ESTADO_CONFIG[s]?.label}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Tabs */}
        <div className="flex gap-1 bg-white border border-gray-200 rounded-xl p-1 mb-4">
          {TABS.map(t => (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className={`flex-1 flex items-center justify-center gap-1.5 py-2 rounded-lg text-xs font-medium transition-all ${
                tab === t.id
                  ? 'bg-teal-600 text-white shadow-sm'
                  : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'
              }`}
            >
              <t.icon className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">{t.label}</span>
            </button>
          ))}
        </div>

        {/* Tab: Perfil */}
        {tab === 'perfil' && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <div className="bg-white rounded-xl border border-gray-200 p-4">
              <h3 className="text-sm font-semibold text-gray-700 mb-3">Datos de contacto</h3>
              <div className="space-y-2">
                {persona.telefono && (
                  <div className="flex items-center gap-2 text-sm text-gray-600">
                    <User className="w-4 h-4 text-gray-400" />
                    {persona.telefono}
                  </div>
                )}
                {persona.email && (
                  <div className="flex items-center gap-2 text-sm text-gray-600">
                    <Send className="w-4 h-4 text-gray-400" />
                    {persona.email}
                  </div>
                )}
                {persona.ubicacion && (
                  <div className="flex items-center gap-2 text-sm text-gray-600">
                    <MapPin className="w-4 h-4 text-gray-400" />
                    {persona.ubicacion}
                  </div>
                )}
                {persona.nivel_educativo && (
                  <div className="flex items-center gap-2 text-sm text-gray-600">
                    <BookOpen className="w-4 h-4 text-gray-400" />
                    {persona.nivel_educativo}
                  </div>
                )}
              </div>
            </div>

            <div className="bg-white rounded-xl border border-gray-200 p-4">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm font-semibold text-gray-700">
                  Competencias ({skills.length})
                </h3>
                <button
                  onClick={() => router.push(`/mi-futuro-laboral/perfil?caso_id=${casoId}&persona_id=${persona.id}`)}
                  className="text-xs text-teal-600 hover:underline flex items-center gap-1"
                >
                  <Plus className="w-3 h-3" /> Agregar
                </button>
              </div>
              {skills.length === 0 ? (
                <p className="text-sm text-gray-400 italic">Sin competencias registradas</p>
              ) : (
                <div className="space-y-2 max-h-64 overflow-y-auto">
                  {confirmedSkills.map(s => (
                    <div key={s.id} className="flex items-center gap-2">
                      <CheckCircle className="w-3.5 h-3.5 shrink-0 text-green-500" />
                      <span className="text-sm text-gray-700 flex-1">{s.skill_label}</span>
                      <ViaCapturaBadge via={s.via_captura} />
                    </div>
                  ))}
                  {suggestedSkills.map(s => (
                    <div key={s.id} className="flex items-center gap-2">
                      <CheckCircle className="w-3.5 h-3.5 shrink-0 text-yellow-400" />
                      <span className="text-sm text-gray-700 flex-1">{s.skill_label}</span>
                      <ViaCapturaBadge via={s.via_captura} />
                      <span className="text-[10px] text-yellow-600 bg-yellow-50 px-1.5 py-0.5 rounded">sugerida</span>
                    </div>
                  ))}
                </div>
              )}
              <button
                onClick={() => router.push(`/mi-futuro-laboral/perfil?caso_id=${casoId}&persona_id=${persona.id}`)}
                className="mt-3 w-full text-xs text-teal-600 bg-teal-50 hover:bg-teal-100 rounded-lg py-2 transition-colors font-medium"
              >
                Completar perfil con la persona →
              </button>
            </div>
          </div>
        )}

        {/* Tab: Vacantes (semantic matching) */}
        {tab === 'vacantes' && (
          <div className="space-y-3">
            {matchLoading && (
              <div className="bg-white rounded-xl border border-gray-200 p-8 flex items-center justify-center gap-3">
                <Loader2 className="w-5 h-5 animate-spin text-teal-600" />
                <span className="text-sm text-gray-500">Buscando ofertas compatibles (matching semántico)...</span>
              </div>
            )}

            {!matchLoading && skills.length === 0 && (
              <div className="bg-white rounded-xl border border-gray-200 p-8 text-center">
                <AlertTriangle className="w-6 h-6 text-yellow-400 mx-auto mb-2" />
                <p className="text-sm text-gray-600">Esta persona no tiene competencias registradas.</p>
                <button
                  onClick={() => router.push(`/mi-futuro-laboral/perfil?caso_id=${casoId}&persona_id=${persona.id}`)}
                  className="mt-3 text-sm text-teal-600 hover:underline"
                >
                  Completar perfil primero →
                </button>
              </div>
            )}

            {!matchLoading && matchStats && (
              <div className="bg-teal-50 rounded-xl border border-teal-100 px-4 py-2 flex items-center justify-between">
                <span className="text-xs text-teal-700">
                  Matching semántico: {skills.length} skills → {matchStats.expanded} expandidas → {matchStats.total} ofertas encontradas
                </span>
                <button
                  onClick={loadMatches}
                  className="text-xs text-teal-600 hover:underline"
                >
                  Recalcular
                </button>
              </div>
            )}

            {!matchLoading && offers.map(v => (
              <div key={v.id_oferta} className="bg-white rounded-xl border border-gray-200 p-4">
                <div className="flex items-start justify-between gap-3 mb-2">
                  <div>
                    <h3 className="font-semibold text-gray-900 text-sm">{v.titulo}</h3>
                    <div className="flex flex-wrap items-center gap-2 mt-1">
                      {v.empresa && (
                        <span className="flex items-center gap-1 text-xs text-gray-500">
                          <Building2 className="w-3 h-3" />{v.empresa}
                        </span>
                      )}
                      {v.provincia && (
                        <span className="flex items-center gap-1 text-xs text-gray-500">
                          <MapPin className="w-3 h-3" />{v.provincia}
                        </span>
                      )}
                      <span className="text-xs text-gray-400 font-mono">{v.isco_code}</span>
                    </div>
                  </div>
                </div>
                <MatchBar pct={v.match_score} />
                <div className="mt-2">
                  <span className="text-[10px] text-gray-400 mb-1 block">
                    {v.skills_cubiertas}/{v.skills_oferta_total} competencias cubiertas
                  </span>
                  <div className="flex flex-wrap gap-1">
                    {v.skills_detalle.slice(0, 6).map((d, i) => (
                      <span
                        key={i}
                        className={`text-[10px] px-2 py-0.5 rounded-full ${
                          d.exact
                            ? 'bg-green-50 text-green-700'
                            : d.similarity >= 0.80
                              ? 'bg-blue-50 text-blue-700'
                              : 'bg-yellow-50 text-yellow-700'
                        }`}
                        title={d.exact ? 'Match exacto' : `Similar a "${d.matched_by}" (${(d.similarity * 100).toFixed(0)}%)`}
                      >
                        {d.exact ? '✓' : '~'} {d.skill}
                      </span>
                    ))}
                    {v.skills_detalle.length > 6 && (
                      <span className="text-[10px] text-gray-400">+{v.skills_detalle.length - 6} más</span>
                    )}
                  </div>
                </div>
                <div className="mt-3 flex gap-2">
                  <button
                    onClick={() => handleCambiarEstado('derivado_vacante')}
                    className="flex-1 text-xs text-teal-600 font-medium bg-teal-50 hover:bg-teal-100 rounded-lg py-2 transition-colors"
                  >
                    Derivar a esta vacante →
                  </button>
                </div>
              </div>
            ))}

            {!matchLoading && offers.length === 0 && skills.length > 0 && matchStats && (
              <div className="bg-white rounded-xl border border-gray-200 p-8 text-center">
                <p className="text-sm text-gray-500">No se encontraron ofertas compatibles con este perfil.</p>
              </div>
            )}
          </div>
        )}

        {/* Tab: Notas */}
        {tab === 'notas' && (
          <div className="space-y-4">
            <div className="bg-white rounded-xl border border-gray-200 p-4">
              <p className="text-xs font-semibold text-gray-700 mb-2">Nueva nota técnica</p>
              <textarea
                value={nota}
                onChange={e => setNota(e.target.value)}
                placeholder="Ej: Realizamos entrevista de diagnóstico. La persona muestra interés en..."
                rows={3}
                className="w-full rounded-lg border border-gray-200 px-3 py-2.5 text-sm text-gray-900 placeholder-gray-400 focus:border-teal-400 focus:outline-none focus:ring-2 focus:ring-teal-100 resize-none"
              />
              <button
                onClick={handleGuardarNota}
                disabled={!nota.trim()}
                className="mt-2 inline-flex items-center gap-2 bg-teal-600 text-white text-xs font-medium px-4 py-2 rounded-lg hover:bg-teal-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
              >
                <Plus className="w-3.5 h-3.5" />
                Guardar nota
              </button>
            </div>

            {caso.nota_tecnico && (
              <div className="bg-white rounded-xl border border-gray-200 p-4">
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-xs font-medium text-gray-700">Nota del técnico</span>
                  <span className="text-xs text-gray-400">· {new Date(caso.created_at).toLocaleDateString('es-AR')}</span>
                </div>
                <p className="text-sm text-gray-700 leading-relaxed">{caso.nota_tecnico}</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
