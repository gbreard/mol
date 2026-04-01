'use client'

import { useState, useEffect, useRef, useCallback } from 'react'
import { useRouter, useParams } from 'next/navigation'
import {
  ArrowLeft, ArrowRight, Search, X, Loader2, Check, ChevronDown, ChevronUp,
} from 'lucide-react'
import FreeTextSkillExtractor from '@/components/FreeTextSkillExtractor'
import type { SkillItem } from '@/components/SkillWithDefinition'

// ─── Types ───────────────────────────────────────────────────────────────────

interface Occupation {
  uri: string
  label: string
  isco_code: string
}

interface OccSkill {
  id: string
  label: string
  description: string
  essential: boolean
  // Interview state
  selected: boolean
  nivel: 'basico' | 'intermedio' | 'avanzado'
  certificado: boolean
}

interface OccupationWithSkills extends Occupation {
  skills: OccSkill[]
}

interface EscoArgentinoEntry {
  esco_occupation_uri: string
  skills_consolidadas: Array<{
    esco_uri: string
    label_original: string
    description?: string
    L1?: string
  }>
}

// ─── getSkillsForOccupation ─────────────────────────────────────────────────

function getSkillsForOccupation(
  occupationUri: string,
  escoArgentino: Map<string, EscoArgentinoEntry>,
  occFullDetail: Record<string, any> | null,
): { essential: OccSkill[]; optional: OccSkill[] } {
  // Try esco_argentino first (curated for Argentina)
  const arg = escoArgentino.get(occupationUri)
  if (arg && arg.skills_consolidadas.length > 0) {
    const skills = arg.skills_consolidadas.map(s => ({
      id: s.esco_uri.split('/').pop() || s.esco_uri,
      label: s.label_original,
      description: s.description || '',
      essential: true,
      selected: true,
      nivel: 'intermedio' as const,
      certificado: false,
    }))
    return { essential: skills, optional: [] }
  }

  // Fallback to occupation_full_detail.json
  if (occFullDetail) {
    const occId = occupationUri.split('/').pop() || ''
    const occ = occFullDetail[occId]
    if (occ) {
      const mapSkill = (s: any, essential: boolean): OccSkill => ({
        id: s.id,
        label: s.label,
        description: s.description || '',
        essential,
        selected: true,
        nivel: 'intermedio',
        certificado: false,
      })
      return {
        essential: (occ.skills?.essential || []).map((s: any) => mapSkill(s, true)),
        optional: (occ.skills?.optional || []).map((s: any) => mapSkill(s, false)),
      }
    }
  }

  return { essential: [], optional: [] }
}

// ─── NivelSelector ──────────────────────────────────────────────────────────

function NivelSelector({ nivel, onChange }: { nivel: string; onChange: (n: 'basico' | 'intermedio' | 'avanzado') => void }) {
  const opts: Array<{ value: 'basico' | 'intermedio' | 'avanzado'; label: string }> = [
    { value: 'basico', label: 'Básico' },
    { value: 'intermedio', label: 'Intermedio' },
    { value: 'avanzado', label: 'Avanzado' },
  ]
  return (
    <div className="flex gap-1">
      {opts.map(o => (
        <button
          key={o.value}
          onClick={() => onChange(o.value)}
          className={`text-[10px] px-2 py-0.5 rounded-full transition-colors ${
            nivel === o.value
              ? 'bg-teal-600 text-white'
              : 'bg-gray-100 text-gray-500 hover:bg-gray-200'
          }`}
        >
          {o.label}
        </button>
      ))}
    </div>
  )
}

// ─── Page ────────────────────────────────────────────────────────────────────

export default function EntrevistaPage() {
  const router = useRouter()
  const params = useParams()
  const casoId = params.id as string

  const [paso, setPaso] = useState(1)
  const [personaNombre, setPersonaNombre] = useState('')
  const [perfilId, setPerfilId] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Paso 1: ocupaciones
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState<Occupation[]>([])
  const [searching, setSearching] = useState(false)
  const [selectedOccupations, setSelectedOccupations] = useState<Occupation[]>([])
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  // Paso 2: skills por ocupación
  const [occWithSkills, setOccWithSkills] = useState<OccupationWithSkills[]>([])
  const [currentOccIdx, setCurrentOccIdx] = useState(0)
  const [occJsonLoading, setOccJsonLoading] = useState(false)
  const [occFullDetail, setOccFullDetail] = useState<Record<string, any> | null>(null)
  const [escoArgentino, setEscoArgentino] = useState<Map<string, EscoArgentinoEntry>>(new Map())
  const [showOptional, setShowOptional] = useState(false)

  // Paso 3: skills adicionales
  const [extraSkills, setExtraSkills] = useState<OccSkill[]>([])

  // Load caso info
  useEffect(() => {
    async function load() {
      try {
        const res = await fetch(`/api/casos/${casoId}`)
        if (!res.ok) throw new Error('Caso no encontrado')
        const data = await res.json()
        setPersonaNombre(data.persona?.nombre || 'la persona')
        setPerfilId(data.perfil?.id || null)
      } catch (e) {
        setError((e as Error).message)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [casoId])

  // Load esco_argentino on mount
  useEffect(() => {
    async function loadArg() {
      try {
        const res = await fetch('/api/esco-argentino')
        if (res.ok) {
          const data = await res.json()
          const items = data.profiles || data.data || data
          if (Array.isArray(items)) {
            const map = new Map<string, EscoArgentinoEntry>()
            for (const item of items) {
              map.set(item.esco_occupation_uri, item)
            }
            setEscoArgentino(map)
          }
        }
      } catch { /* optional, fallback to JSON */ }
    }
    loadArg()
  }, [])

  // Search occupations (Paso 1)
  const searchOccupations = useCallback(async (q: string) => {
    if (q.length < 2) { setSearchResults([]); return }
    setSearching(true)
    try {
      const res = await fetch(`/api/occupations/search-semantic?q=${encodeURIComponent(q)}`)
      if (res.ok) {
        const data = await res.json()
        setSearchResults((data.results || []).filter(
          (o: Occupation) => !selectedOccupations.some(s => s.uri === o.uri)
        ))
      }
    } catch { /* ignore */ }
    finally { setSearching(false) }
  }, [selectedOccupations])

  const handleSearchChange = (q: string) => {
    setSearchQuery(q)
    if (debounceRef.current) clearTimeout(debounceRef.current)
    debounceRef.current = setTimeout(() => searchOccupations(q), 350)
  }

  const addOccupation = (occ: Occupation) => {
    setSelectedOccupations(prev => [...prev, occ])
    setSearchResults([])
    setSearchQuery('')
  }

  const removeOccupation = (uri: string) => {
    setSelectedOccupations(prev => prev.filter(o => o.uri !== uri))
  }

  // Enter Paso 2: lazy load JSON + build skills
  const enterPaso2 = async () => {
    setPaso(2)
    setOccJsonLoading(true)
    setCurrentOccIdx(0)
    setShowOptional(false)

    try {
      // Load occupation_full_detail.json (lazy, only when entering paso 2)
      let detail = occFullDetail
      if (!detail) {
        const res = await fetch('/data/occupation_full_detail.json')
        if (res.ok) {
          detail = await res.json()
          setOccFullDetail(detail)
        }
      }

      // Build skills for each occupation
      const withSkills: OccupationWithSkills[] = selectedOccupations.map(occ => {
        const { essential, optional } = getSkillsForOccupation(occ.uri, escoArgentino, detail)
        return { ...occ, skills: [...essential, ...optional] }
      })
      setOccWithSkills(withSkills)
    } catch (e) {
      console.error('Error loading occupation skills:', e)
    } finally {
      setOccJsonLoading(false)
    }
  }

  // Toggle skill in Paso 2
  const toggleSkill = (occIdx: number, skillId: string) => {
    setOccWithSkills(prev => prev.map((occ, i) => {
      if (i !== occIdx) return occ
      return {
        ...occ,
        skills: occ.skills.map(s =>
          s.id === skillId ? { ...s, selected: !s.selected, nivel: s.selected ? 'intermedio' : s.nivel } : s
        ),
      }
    }))
  }

  const updateSkillNivel = (occIdx: number, skillId: string, nivel: 'basico' | 'intermedio' | 'avanzado') => {
    setOccWithSkills(prev => prev.map((occ, i) => {
      if (i !== occIdx) return occ
      return { ...occ, skills: occ.skills.map(s => s.id === skillId ? { ...s, nivel } : s) }
    }))
  }

  const toggleCertificado = (occIdx: number, skillId: string) => {
    setOccWithSkills(prev => prev.map((occ, i) => {
      if (i !== occIdx) return occ
      return { ...occ, skills: occ.skills.map(s => s.id === skillId ? { ...s, certificado: !s.certificado } : s) }
    }))
  }

  // Paso 3: skills from FreeTextSkillExtractor
  const handleExtraSkills = (skills: SkillItem[]) => {
    const nuevas: OccSkill[] = skills.map(s => ({
      id: s.uri,
      label: s.label,
      description: s.description || '',
      essential: false,
      selected: true,
      nivel: 'intermedio',
      certificado: false,
    }))
    setExtraSkills(prev => {
      const existing = new Set(prev.map(s => s.id))
      return [...prev, ...nuevas.filter(s => !existing.has(s.id))]
    })
  }

  const toggleExtraSkill = (skillId: string) => {
    setExtraSkills(prev => prev.map(s =>
      s.id === skillId ? { ...s, selected: !s.selected } : s
    ))
  }

  const updateExtraNivel = (skillId: string, nivel: 'basico' | 'intermedio' | 'avanzado') => {
    setExtraSkills(prev => prev.map(s => s.id === skillId ? { ...s, nivel } : s))
  }

  const toggleExtraCert = (skillId: string) => {
    setExtraSkills(prev => prev.map(s => s.id === skillId ? { ...s, certificado: !s.certificado } : s))
  }

  // Save
  const handleSave = async () => {
    if (!perfilId) { setError('No hay perfil asociado'); return }
    setSaving(true)
    setError(null)

    const SKILL_PREFIX = 'http://data.europa.eu/esco/skill/'

    // Collect all selected skills
    const allSkills: Array<{
      skill_uri: string; skill_label: string; via_captura: string
      estado: string; confianza: number; nivel: string; certificado: boolean
    }> = []

    // From Paso 2 (occupations)
    for (const occ of occWithSkills) {
      for (const s of occ.skills) {
        if (!s.selected) continue
        const uri = s.id.startsWith('http') ? s.id : SKILL_PREFIX + s.id
        if (allSkills.some(x => x.skill_uri === uri)) continue
        allSkills.push({
          skill_uri: uri,
          skill_label: s.label,
          via_captura: 'ocupacion',
          estado: 'confirmada',
          confianza: 1.0,
          nivel: s.nivel,
          certificado: s.certificado,
        })
      }
    }

    // From Paso 3 (text)
    for (const s of extraSkills) {
      if (!s.selected) continue
      const uri = s.id.startsWith('http') ? s.id : SKILL_PREFIX + s.id
      if (allSkills.some(x => x.skill_uri === uri)) continue
      allSkills.push({
        skill_uri: uri,
        skill_label: s.label,
        via_captura: 'texto',
        estado: 'confirmada',
        confianza: 1.0,
        nivel: s.nivel,
        certificado: s.certificado,
      })
    }

    if (allSkills.length === 0) {
      setError('No hay skills seleccionadas')
      setSaving(false)
      return
    }

    try {
      const res = await fetch(`/api/perfiles/${perfilId}/skills`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ skills: allSkills }),
      })

      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.error || 'Error guardando skills')
      }

      router.push(`/oficina-empleo/casos/${casoId}`)
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setSaving(false)
    }
  }

  // ─── Render ────────────────────────────────────────────────────────────────

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <Loader2 className="w-5 h-5 animate-spin text-teal-600" />
      </div>
    )
  }

  const currentOcc = occWithSkills[currentOccIdx]
  const essentialSkills = currentOcc?.skills.filter(s => s.essential) || []
  const optionalSkills = currentOcc?.skills.filter(s => !s.essential) || []

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-2xl mx-auto px-4 py-6">

        {/* Header */}
        <button
          onClick={() => paso === 1 ? router.push(`/oficina-empleo/casos/${casoId}`) : setPaso(paso - 1)}
          className="flex items-center gap-1.5 text-sm text-gray-500 hover:text-gray-700 mb-4"
        >
          <ArrowLeft className="w-4 h-4" />
          {paso === 1 ? 'Volver al caso' : 'Anterior'}
        </button>

        {/* ─── PASO 1: Trayectoria laboral ──────────────────────────────────── */}
        {paso === 1 && (
          <div>
            <div className="mb-6">
              <span className="text-[10px] font-bold text-teal-600 bg-teal-50 px-2 py-0.5 rounded-full uppercase">
                Paso 1 de 3
              </span>
              <h1 className="text-xl font-bold text-gray-900 mt-2">
                ¿En qué trabajó {personaNombre}?
              </h1>
            </div>

            {/* Search */}
            <div className="relative mb-4">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={e => handleSearchChange(e.target.value)}
                placeholder="Ej: soldador, cajero, enfermero, albañil..."
                className="w-full rounded-xl border border-gray-200 bg-white pl-9 pr-3 py-2.5 text-sm focus:border-teal-400 focus:outline-none focus:ring-2 focus:ring-teal-100"
                autoFocus
              />
              {searching && <Loader2 className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 animate-spin" />}
            </div>

            {/* Search results */}
            {searchResults.length > 0 && (
              <div className="border border-gray-200 rounded-xl overflow-hidden mb-4">
                {searchResults.map(o => (
                  <button
                    key={o.uri}
                    onClick={() => addOccupation(o)}
                    className="w-full flex items-center justify-between px-4 py-2.5 hover:bg-teal-50 text-left border-b border-gray-50 last:border-0"
                  >
                    <span className="text-sm text-gray-800">{o.label}</span>
                    <span className="text-xs text-gray-400 font-mono">{o.isco_code}</span>
                  </button>
                ))}
              </div>
            )}

            {/* Selected occupations */}
            {selectedOccupations.length > 0 && (
              <div className="space-y-2 mb-6">
                <p className="text-xs text-gray-500 font-medium">Ocupaciones agregadas:</p>
                {selectedOccupations.map(o => (
                  <div key={o.uri} className="flex items-center gap-2 bg-teal-50 border border-teal-200 rounded-lg px-3 py-2">
                    <Check className="w-3.5 h-3.5 text-teal-600 shrink-0" />
                    <span className="text-sm text-teal-800 flex-1">{o.label}</span>
                    <button onClick={() => removeOccupation(o.uri)} className="text-teal-400 hover:text-teal-600">
                      <X className="w-3.5 h-3.5" />
                    </button>
                  </div>
                ))}
              </div>
            )}

            <button
              onClick={enterPaso2}
              disabled={selectedOccupations.length === 0}
              className="w-full bg-teal-600 text-white text-sm font-semibold py-2.5 rounded-xl hover:bg-teal-700 disabled:opacity-40 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              Continuar <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        )}

        {/* ─── PASO 2: Skills por ocupación ─────────────────────────────────── */}
        {paso === 2 && (
          <div>
            <div className="mb-6">
              <span className="text-[10px] font-bold text-teal-600 bg-teal-50 px-2 py-0.5 rounded-full uppercase">
                Paso 2 de 3 — {currentOcc?.label} ({currentOccIdx + 1} de {occWithSkills.length})
              </span>
              <h1 className="text-xl font-bold text-gray-900 mt-2">
                ¿Cuáles de estas habilidades aplica?
              </h1>
            </div>

            {occJsonLoading ? (
              <div className="bg-white rounded-xl border border-gray-200 p-12 flex items-center justify-center gap-3">
                <Loader2 className="w-5 h-5 animate-spin text-teal-600" />
                <span className="text-sm text-gray-500">Cargando competencias...</span>
              </div>
            ) : currentOcc ? (
              <div className="space-y-2">
                {/* Essential */}
                {essentialSkills.length > 0 && (
                  <div className="bg-white rounded-xl border border-gray-200 p-4">
                    <p className="text-xs font-semibold text-gray-600 mb-3 uppercase tracking-wider">Esenciales</p>
                    <div className="space-y-3">
                      {essentialSkills.map(s => (
                        <div key={s.id} className={`rounded-lg p-3 transition-colors ${s.selected ? 'bg-teal-50 border border-teal-200' : 'bg-gray-50 border border-gray-100'}`}>
                          <div className="flex items-start gap-2">
                            <button onClick={() => toggleSkill(currentOccIdx, s.id)} className="mt-0.5 shrink-0">
                              <div className={`w-4 h-4 rounded border-2 flex items-center justify-center ${s.selected ? 'bg-teal-600 border-teal-600' : 'border-gray-300'}`}>
                                {s.selected && <Check className="w-3 h-3 text-white" />}
                              </div>
                            </button>
                            <div className="flex-1 min-w-0">
                              <p className={`text-sm font-medium ${s.selected ? 'text-gray-900' : 'text-gray-400'}`}>{s.label}</p>
                              {s.description && <p className="text-xs text-gray-400 mt-0.5 line-clamp-2">{s.description}</p>}
                              {s.selected && (
                                <div className="flex items-center gap-3 mt-2">
                                  <NivelSelector nivel={s.nivel} onChange={n => updateSkillNivel(currentOccIdx, s.id, n)} />
                                  <button
                                    onClick={() => toggleCertificado(currentOccIdx, s.id)}
                                    className={`text-[10px] px-2 py-0.5 rounded-full ${s.certificado ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-400'}`}
                                  >
                                    {s.certificado ? '✓ Cert' : 'Cert'}
                                  </button>
                                </div>
                              )}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Optional (collapsed) */}
                {optionalSkills.length > 0 && (
                  <div className="bg-white rounded-xl border border-gray-200 p-4">
                    <button
                      onClick={() => setShowOptional(!showOptional)}
                      className="flex items-center gap-2 text-xs text-gray-500 hover:text-gray-700 w-full"
                    >
                      {showOptional ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                      <span>{showOptional ? 'Ocultar' : 'Ver'} {optionalSkills.length} habilidades opcionales</span>
                    </button>
                    {showOptional && (
                      <div className="space-y-3 mt-3">
                        {optionalSkills.map(s => (
                          <div key={s.id} className={`rounded-lg p-3 ${s.selected ? 'bg-blue-50 border border-blue-200' : 'bg-gray-50 border border-gray-100'}`}>
                            <div className="flex items-start gap-2">
                              <button onClick={() => toggleSkill(currentOccIdx, s.id)} className="mt-0.5 shrink-0">
                                <div className={`w-4 h-4 rounded border-2 flex items-center justify-center ${s.selected ? 'bg-blue-600 border-blue-600' : 'border-gray-300'}`}>
                                  {s.selected && <Check className="w-3 h-3 text-white" />}
                                </div>
                              </button>
                              <div className="flex-1">
                                <p className={`text-sm ${s.selected ? 'text-gray-800' : 'text-gray-400'}`}>{s.label}</p>
                                {s.selected && (
                                  <div className="flex items-center gap-3 mt-2">
                                    <NivelSelector nivel={s.nivel} onChange={n => updateSkillNivel(currentOccIdx, s.id, n)} />
                                    <button
                                      onClick={() => toggleCertificado(currentOccIdx, s.id)}
                                      className={`text-[10px] px-2 py-0.5 rounded-full ${s.certificado ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-400'}`}
                                    >
                                      {s.certificado ? '✓ Cert' : 'Cert'}
                                    </button>
                                  </div>
                                )}
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {/* Navigation */}
                <div className="flex gap-3 mt-4">
                  {currentOccIdx > 0 && (
                    <button
                      onClick={() => { setCurrentOccIdx(currentOccIdx - 1); setShowOptional(false) }}
                      className="flex-1 border border-gray-200 text-gray-600 text-sm py-2.5 rounded-xl hover:bg-gray-50"
                    >
                      ← Anterior
                    </button>
                  )}
                  {currentOccIdx < occWithSkills.length - 1 ? (
                    <button
                      onClick={() => { setCurrentOccIdx(currentOccIdx + 1); setShowOptional(false) }}
                      className="flex-1 bg-teal-600 text-white text-sm font-semibold py-2.5 rounded-xl hover:bg-teal-700 flex items-center justify-center gap-2"
                    >
                      Siguiente ocupación <ArrowRight className="w-4 h-4" />
                    </button>
                  ) : (
                    <button
                      onClick={() => setPaso(3)}
                      className="flex-1 bg-teal-600 text-white text-sm font-semibold py-2.5 rounded-xl hover:bg-teal-700 flex items-center justify-center gap-2"
                    >
                      Continuar <ArrowRight className="w-4 h-4" />
                    </button>
                  )}
                </div>
              </div>
            ) : (
              <p className="text-sm text-gray-400 text-center py-8">Sin datos de la ocupación.</p>
            )}
          </div>
        )}

        {/* ─── PASO 3: Skills adicionales ───────────────────────────────────── */}
        {paso === 3 && (
          <div>
            <div className="mb-6">
              <span className="text-[10px] font-bold text-teal-600 bg-teal-50 px-2 py-0.5 rounded-full uppercase">
                Paso 3 de 3
              </span>
              <h1 className="text-xl font-bold text-gray-900 mt-2">
                ¿Hay algo más que sepa hacer?
              </h1>
              <p className="text-sm text-gray-500 mt-1">
                El técnico escribe lo que la persona dice con sus propias palabras.
              </p>
            </div>

            <div className="bg-white rounded-xl border border-gray-200 p-4 mb-4">
              <FreeTextSkillExtractor onSkillsAdded={handleExtraSkills} />
            </div>

            {/* Extra skills with nivel/cert */}
            {extraSkills.length > 0 && (
              <div className="bg-white rounded-xl border border-gray-200 p-4 mb-4 space-y-3">
                <p className="text-xs font-semibold text-gray-600">Skills encontradas:</p>
                {extraSkills.map(s => (
                  <div key={s.id} className={`rounded-lg p-3 ${s.selected ? 'bg-teal-50 border border-teal-200' : 'bg-gray-50 border border-gray-100'}`}>
                    <div className="flex items-start gap-2">
                      <button onClick={() => toggleExtraSkill(s.id)} className="mt-0.5 shrink-0">
                        <div className={`w-4 h-4 rounded border-2 flex items-center justify-center ${s.selected ? 'bg-teal-600 border-teal-600' : 'border-gray-300'}`}>
                          {s.selected && <Check className="w-3 h-3 text-white" />}
                        </div>
                      </button>
                      <div className="flex-1">
                        <p className={`text-sm ${s.selected ? 'text-gray-800' : 'text-gray-400'}`}>{s.label}</p>
                        {s.selected && (
                          <div className="flex items-center gap-3 mt-2">
                            <NivelSelector nivel={s.nivel} onChange={n => updateExtraNivel(s.id, n)} />
                            <button
                              onClick={() => toggleExtraCert(s.id)}
                              className={`text-[10px] px-2 py-0.5 rounded-full ${s.certificado ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-400'}`}
                            >
                              {s.certificado ? '✓ Cert' : 'Cert'}
                            </button>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {error && <p className="text-sm text-red-500 mb-3">{error}</p>}

            <button
              onClick={handleSave}
              disabled={saving}
              className="w-full bg-teal-600 text-white text-sm font-semibold py-2.5 rounded-xl hover:bg-teal-700 disabled:opacity-50 flex items-center justify-center gap-2"
            >
              {saving ? (
                <><Loader2 className="w-4 h-4 animate-spin" /> Guardando...</>
              ) : (
                <>Guardar perfil <Check className="w-4 h-4" /></>
              )}
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
