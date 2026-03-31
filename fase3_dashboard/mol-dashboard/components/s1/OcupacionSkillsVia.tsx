'use client'

import { useState, useRef, useCallback, useEffect } from 'react'
import { Search, Loader2, Plus, ChevronRight, CheckCircle } from 'lucide-react'
import type { SkillItem, SkillConfidence } from '@/components/SkillWithDefinition'

interface OccupationResult {
  id: string
  label: string
  isco: string
}

interface OccupationSkill {
  uri: string
  label: string
  type: 'skill' | 'knowledge'
  description: string
  source: 'esco' | 'argentina_approved'
  essential: boolean
}

interface Props {
  onSkillsFound: (skills: SkillItem[]) => void
  existingUris?: Set<string>
}

export default function OcupacionSkillsVia({ onSkillsFound, existingUris }: Props) {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<OccupationResult[]>([])
  const [loadingSearch, setLoadingSearch] = useState(false)
  const [selected, setSelected] = useState<OccupationResult | null>(null)
  const [skills, setSkills] = useState<OccupationSkill[]>([])
  const [loadingSkills, setLoadingSkills] = useState(false)
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  const MOCK_OCUPACIONES: OccupationResult[] = [
    { id: 'esco_5223', label: 'Cajero/a', isco: '5223' },
    { id: 'esco_5221', label: 'Vendedor/a en comercios', isco: '5221' },
    { id: 'esco_4110', label: 'Empleado/a administrativo/a', isco: '4110' },
    { id: 'esco_2512', label: 'Desarrollador/a de software', isco: '2512' },
    { id: 'esco_3511', label: 'Técnico/a en sistemas informáticos', isco: '3511' },
    { id: 'esco_2221', label: 'Enfermero/a', isco: '2221' },
    { id: 'esco_5141', label: 'Peluquero/a', isco: '5141' },
    { id: 'esco_7411', label: 'Electricista', isco: '7411' },
    { id: 'esco_7422', label: 'Plomero/a', isco: '7422' },
    { id: 'esco_3412', label: 'Agente inmobiliario', isco: '3412' },
    { id: 'esco_2431', label: 'Publicista / Gestor de publicidad', isco: '2431' },
    { id: 'esco_1221', label: 'Gerente de ventas', isco: '1221' },
    { id: 'esco_5311', label: 'Cuidador/a de niños', isco: '5311' },
    { id: 'esco_8332', label: 'Conductor/a de camiones', isco: '8332' },
    { id: 'esco_6111', label: 'Agricultor/a', isco: '6111' },
    { id: 'esco_3433', label: 'Contador/a', isco: '3433' },
    { id: 'esco_5120', label: 'Cocinero/a', isco: '5120' },
    { id: 'esco_2330', label: 'Docente de nivel secundario', isco: '2330' },
  ]

  const MOCK_SKILLS: Record<string, OccupationSkill[]> = {
    'esco_5223': [
      { uri: 'esco_sk_caja', label: 'Manejo de caja registradora', type: 'skill', description: 'Operar sistemas de cobro y manejo de efectivo.', source: 'esco', essential: true },
      { uri: 'esco_sk_atencion', label: 'Atención al cliente', type: 'skill', description: 'Atender y resolver consultas de clientes de forma efectiva.', source: 'esco', essential: true },
      { uri: 'esco_sk_stock', label: 'Control de stock', type: 'skill', description: 'Gestionar inventario y reposición de mercadería.', source: 'esco', essential: true },
      { uri: 'esco_sk_calcul', label: 'Cálculo numérico básico', type: 'knowledge', description: 'Realizar operaciones aritméticas con rapidez y precisión.', source: 'esco', essential: false },
      { uri: 'esco_sk_venta', label: 'Técnicas de venta', type: 'skill', description: 'Aplicar estrategias para incrementar las ventas.', source: 'esco', essential: false },
    ],
    'esco_2512': [
      { uri: 'esco_sk_prog', label: 'Programación orientada a objetos', type: 'skill', description: 'Diseñar y desarrollar software usando paradigmas OOP.', source: 'esco', essential: true },
      { uri: 'esco_sk_db', label: 'Bases de datos', type: 'knowledge', description: 'Diseñar y consultar bases de datos relacionales.', source: 'esco', essential: true },
      { uri: 'esco_sk_api', label: 'Desarrollo de APIs REST', type: 'skill', description: 'Construir y consumir APIs web siguiendo estándares REST.', source: 'esco', essential: true },
      { uri: 'esco_sk_git', label: 'Control de versiones (Git)', type: 'skill', description: 'Gestionar código fuente con herramientas de versionado.', source: 'esco', essential: false },
      { uri: 'esco_sk_test', label: 'Testing de software', type: 'skill', description: 'Escribir y ejecutar pruebas para garantizar calidad del código.', source: 'esco', essential: false },
    ],
    'esco_4110': [
      { uri: 'esco_sk_ofim', label: 'Ofimática (Office)', type: 'skill', description: 'Manejo de Word, Excel y herramientas de oficina.', source: 'esco', essential: true },
      { uri: 'esco_sk_archivo', label: 'Gestión documental', type: 'skill', description: 'Organizar, clasificar y archivar documentación.', source: 'esco', essential: true },
      { uri: 'esco_sk_comunic', label: 'Comunicación escrita', type: 'skill', description: 'Redactar comunicaciones formales con claridad.', source: 'esco', essential: true },
      { uri: 'esco_sk_agenda', label: 'Gestión de agenda', type: 'skill', description: 'Coordinar reuniones, turnos y compromisos.', source: 'esco', essential: false },
    ],
    'default': [
      { uri: 'esco_sk_resol', label: 'Resolución de problemas', type: 'skill', description: 'Identificar y solucionar problemas de manera sistemática.', source: 'esco', essential: true },
      { uri: 'esco_sk_comu2', label: 'Comunicación efectiva', type: 'skill', description: 'Transmitir información de forma clara y concisa.', source: 'esco', essential: true },
      { uri: 'esco_sk_org', label: 'Organización y planificación', type: 'skill', description: 'Planificar tareas y gestionar el tiempo de forma eficiente.', source: 'esco', essential: false },
      { uri: 'esco_sk_eq', label: 'Trabajo en equipo', type: 'skill', description: 'Colaborar con otros para alcanzar objetivos comunes.', source: 'esco', essential: false },
    ],
  }

  const search = useCallback(async (q: string) => {
    if (!q.trim()) { setResults([]); return }
    setLoadingSearch(true)
    try {
      const res = await fetch(`/api/occupations/search?q=${encodeURIComponent(q)}&limit=8`)
      if (res.ok) {
        const data = await res.json()
        const results = data.results ?? data
        if (Array.isArray(results) && results.length > 0) {
          setResults(results)
          setLoadingSearch(false)
          return
        }
      }
    } catch { /* fallback */ }
    // Mock fallback
    const filtered = MOCK_OCUPACIONES.filter((o) =>
      o.label.toLowerCase().includes(q.toLowerCase()) ||
      o.isco.startsWith(q)
    )
    setResults(filtered.length > 0 ? filtered : [])
    setLoadingSearch(false)
  }, [])

  const handleQueryChange = (q: string) => {
    setQuery(q)
    setSelected(null)
    setSkills([])
    if (debounceRef.current) clearTimeout(debounceRef.current)
    debounceRef.current = setTimeout(() => search(q), 350)
  }

  const handleSelectOccupation = async (occ: OccupationResult) => {
    setSelected(occ)
    setResults([])
    setQuery(occ.label)
    setLoadingSkills(true)
    try {
      const res = await fetch(`/api/occupations/skills?occupation_id=${occ.id}&limit=20`)
      if (res.ok) {
        const data = await res.json()
        const skills = data.skills ?? data
        if (Array.isArray(skills) && skills.length > 0) {
          setSkills(skills)
          setLoadingSkills(false)
          return
        }
      }
    } catch { /* fallback */ }
    // Mock fallback
    await new Promise((r) => setTimeout(r, 400))
    setSkills(MOCK_SKILLS[occ.id] ?? MOCK_SKILLS['default'])
    setLoadingSkills(false)
  }

  const handleAgregar = () => {
    const items: SkillItem[] = skills.map((s) => ({
      uri: s.uri,
      label: s.label,
      type: s.type,
      description: s.description,
      source: s.source,
      confidence: 'confirmed' as SkillConfidence,
      via: 'ocupacion' as const,
    }))
    onSkillsFound(items)
    setSelected(null)
    setQuery('')
    setSkills([])
    // Refocus para que el usuario pueda buscar otra ocupación inmediatamente
    setTimeout(() => inputRef.current?.focus(), 50)
  }

  const nuevasCount = skills.filter((s) => !existingUris?.has(s.uri)).length

  return (
    <div className="space-y-4">
      {/* Search input */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
        <input
          ref={inputRef}
          type="text"
          value={query}
          onChange={(e) => handleQueryChange(e.target.value)}
          placeholder="Ej: cajero, enfermero, desarrollador..."
          className="w-full rounded-lg border border-gray-200 pl-9 pr-3 py-2.5 text-sm text-gray-900 placeholder-gray-400 focus:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-100"
          autoFocus
        />
        {loadingSearch && (
          <Loader2 className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 animate-spin" />
        )}
      </div>

      {/* Resultados búsqueda */}
      {results.length > 0 && !selected && (
        <div className="border border-gray-200 rounded-lg divide-y divide-gray-100 overflow-hidden">
          {results.map((r) => (
            <button
              key={r.id}
              onClick={() => handleSelectOccupation(r)}
              className="w-full flex items-center justify-between px-4 py-2.5 hover:bg-blue-50 text-left transition-colors"
            >
              <span className="text-sm text-gray-800">{r.label}</span>
              <div className="flex items-center gap-2 shrink-0">
                <span className="text-xs text-gray-400 font-mono">{r.isco}</span>
                <ChevronRight className="w-3.5 h-3.5 text-gray-300" />
              </div>
            </button>
          ))}
        </div>
      )}

      {/* Skills de la ocupación seleccionada */}
      {loadingSkills && (
        <div className="flex items-center justify-center py-8 text-gray-400">
          <Loader2 className="w-5 h-5 animate-spin mr-2" />
          <span className="text-sm">Cargando competencias...</span>
        </div>
      )}

      {selected && skills.length > 0 && (
        <div>
          <div className="flex items-center justify-between mb-2">
            <p className="text-xs font-medium text-gray-600">
              Competencias para <span className="text-blue-700">{selected.label}</span>
            </p>
            <span className="text-xs text-gray-400">
              {nuevasCount} nuevas · {skills.length - nuevasCount} ya en tu perfil
            </span>
          </div>
          <div className="border border-gray-200 rounded-lg divide-y divide-gray-100 overflow-hidden max-h-64 overflow-y-auto mb-3">
            {skills.map((s) => {
              const yaEnPerfil = existingUris?.has(s.uri)
              return (
                <div key={s.uri} className={`flex items-center gap-2 px-3 py-2 ${yaEnPerfil ? 'opacity-50' : ''}`}>
                  <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${s.essential ? 'bg-blue-500' : 'bg-gray-300'}`} />
                  <span className="text-sm text-gray-800 flex-1">{s.label}</span>
                  {yaEnPerfil ? (
                    <CheckCircle className="w-3.5 h-3.5 text-green-400 shrink-0" />
                  ) : s.essential ? (
                    <span className="text-[10px] bg-blue-50 text-blue-600 px-1.5 py-0.5 rounded font-medium">
                      esencial
                    </span>
                  ) : null}
                </div>
              )
            })}
          </div>
          <button
            onClick={handleAgregar}
            disabled={nuevasCount === 0}
            className="w-full inline-flex items-center justify-center gap-2 bg-blue-600 text-white text-sm font-medium px-4 py-2.5 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <Plus className="w-4 h-4" />
            {nuevasCount > 0
              ? `Agregar ${nuevasCount} competencia${nuevasCount !== 1 ? 's' : ''} nueva${nuevasCount !== 1 ? 's' : ''}`
              : 'Todas ya están en tu perfil'}
          </button>
          {nuevasCount === 0 && (
            <p className="text-center text-xs text-gray-400 mt-2">
              Probá buscar otra ocupación para sumar más.
            </p>
          )}
        </div>
      )}

      {selected && !loadingSkills && skills.length === 0 && (
        <p className="text-sm text-gray-400 text-center py-4">
          No encontramos competencias para esta ocupación.
        </p>
      )}
    </div>
  )
}
