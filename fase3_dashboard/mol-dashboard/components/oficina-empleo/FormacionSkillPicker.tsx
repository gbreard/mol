'use client'

import { useState } from 'react'
import { Search, Loader2, GraduationCap, ArrowLeft, Check } from 'lucide-react'
import type { SelectedSkill } from './useSkillCapture'

interface Props {
  skillUris: Set<string>
  onAddSkills: (skills: SelectedSkill[]) => void
}

interface CursoResult {
  curso_id: number
  denominacion: string
  grupo: string
  carga_horaria_modal: number | null
  skills_count: number
}

interface CursoSkill {
  skill_uri: string
  skill_label: string
}

export function FormacionSkillPicker({ skillUris, onAddSkills }: Props) {
  const [query, setQuery] = useState('')
  const [cursos, setCursos] = useState<CursoResult[]>([])
  const [loading, setLoading] = useState(false)
  const [selectedCurso, setSelectedCurso] = useState<CursoResult | null>(null)
  const [cursoSkills, setCursoSkills] = useState<CursoSkill[]>([])
  const [loadingSkills, setLoadingSkills] = useState(false)
  const [checkedUris, setCheckedUris] = useState<Set<string>>(new Set())

  async function handleSearch() {
    if (!query.trim() || query.trim().length < 2) return
    setLoading(true)
    setCursos([])
    setSelectedCurso(null)
    try {
      const res = await fetch(`/api/cursos-formacion/search?q=${encodeURIComponent(query)}`)
      if (res.ok) {
        const data = await res.json()
        setCursos(data.cursos || [])
      }
    } catch {} finally {
      setLoading(false)
    }
  }

  async function selectCurso(curso: CursoResult) {
    setSelectedCurso(curso)
    setLoadingSkills(true)
    setCursoSkills([])
    try {
      const res = await fetch(`/api/cursos-formacion/${curso.curso_id}/skills`)
      if (res.ok) {
        const data = await res.json()
        const skills = data.skills || []
        setCursoSkills(skills)
        // Pre-check skills not already in profile
        const preChecked = new Set<string>(
          skills.filter((s: CursoSkill) => !skillUris.has(s.skill_uri)).map((s: CursoSkill) => s.skill_uri)
        )
        setCheckedUris(preChecked)
      }
    } catch {} finally {
      setLoadingSkills(false)
    }
  }

  function toggleCheck(uri: string) {
    setCheckedUris(prev => {
      const next = new Set(prev)
      if (next.has(uri)) next.delete(uri)
      else next.add(uri)
      return next
    })
  }

  function addToProfile() {
    const toAdd: SelectedSkill[] = cursoSkills
      .filter(s => checkedUris.has(s.skill_uri))
      .map(s => ({
        uri: s.skill_uri,
        label: s.skill_label,
        type: 'skill' as const,
        source: 'estructurado' as const,
        nivel: 'intermedio' as 'basico' | 'intermedio' | 'avanzado' | 'experto',
        certificado: true,
      }))
    onAddSkills(toAdd)
    setSelectedCurso(null)
    setCursoSkills([])
    setCheckedUris(new Set())
    setQuery('')
    setCursos([])
  }

  return (
    <div className="space-y-3">
      <p className="text-sm text-gray-500">
        Cursos del sistema de formación continua del STEySS
      </p>

      {/* Course skills view */}
      {selectedCurso ? (
        <div className="border rounded-lg overflow-hidden">
          <div className="bg-teal-50 px-4 py-2.5 flex items-center gap-2">
            <button onClick={() => { setSelectedCurso(null); setCursoSkills([]) }} className="text-teal-600 hover:text-teal-800">
              <ArrowLeft className="w-4 h-4" />
            </button>
            <div>
              <span className="text-sm font-medium text-teal-800">{selectedCurso.denominacion}</span>
              <span className="text-xs text-teal-600 ml-2">
                {selectedCurso.grupo}{selectedCurso.carga_horaria_modal ? ` · ${selectedCurso.carga_horaria_modal}hs` : ''}
              </span>
            </div>
          </div>

          {loadingSkills ? (
            <div className="py-6 flex items-center justify-center gap-2 text-gray-400">
              <Loader2 className="w-4 h-4 animate-spin" />
              <span className="text-sm">Cargando competencias...</span>
            </div>
          ) : cursoSkills.length === 0 ? (
            <div className="py-6 text-center text-gray-400 text-sm">
              Este curso no tiene competencias asociadas
            </div>
          ) : (
            <>
              <div className="px-4 py-2 text-xs text-gray-500 border-b">
                Competencias que cubre este curso:
              </div>
              <div className="max-h-56 overflow-y-auto divide-y">
                {cursoSkills.map((s, i) => {
                  const alreadyInProfile = skillUris.has(s.skill_uri)
                  const checked = checkedUris.has(s.skill_uri)
                  return (
                    <label key={i} className={`flex items-center gap-2 px-4 py-2 cursor-pointer hover:bg-gray-50 ${alreadyInProfile ? 'opacity-40' : ''}`}>
                      <input
                        type="checkbox"
                        checked={alreadyInProfile || checked}
                        disabled={alreadyInProfile}
                        onChange={() => toggleCheck(s.skill_uri)}
                        className="rounded text-teal-600"
                      />
                      <span className="text-sm text-gray-900 flex-1">{s.skill_label}</span>
                      {alreadyInProfile && <span className="text-[10px] text-gray-400">ya en el perfil</span>}
                    </label>
                  )
                })}
              </div>
              <div className="px-4 py-2.5 bg-gray-50 border-t flex items-center justify-between">
                <span className="text-xs text-gray-500">{checkedUris.size} seleccionadas</span>
                <button
                  onClick={addToProfile}
                  disabled={checkedUris.size === 0}
                  className="bg-teal-600 text-white text-sm px-3 py-1.5 rounded-lg hover:bg-teal-700 disabled:opacity-50"
                >
                  Agregar competencias seleccionadas
                </button>
              </div>
            </>
          )}
        </div>
      ) : (
        <>
          {/* Search */}
          <div className="flex gap-2">
            <input
              value={query}
              onChange={e => setQuery(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleSearch()}
              placeholder="electricidad, soldadura, gastronomía..."
              className="flex-1 border rounded-lg px-3 py-2 text-sm"
            />
            <button
              onClick={handleSearch}
              disabled={loading || !query.trim()}
              className="bg-teal-600 text-white px-3 py-2 rounded-lg text-sm hover:bg-teal-700 disabled:opacity-50 flex items-center gap-1"
            >
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
            </button>
          </div>

          {/* Results */}
          {cursos.length > 0 && (
            <div className="border rounded-lg divide-y max-h-56 overflow-y-auto">
              {cursos.map(c => (
                <button
                  key={c.curso_id}
                  onClick={() => selectCurso(c)}
                  className="w-full flex items-start gap-3 px-4 py-3 text-left hover:bg-teal-50 transition-colors"
                >
                  <GraduationCap className="w-4 h-4 text-teal-500 shrink-0 mt-0.5" />
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-medium text-gray-900">{c.denominacion}</div>
                    <div className="text-xs text-gray-400">
                      {c.grupo}{c.carga_horaria_modal ? ` · ${c.carga_horaria_modal}hs` : ' · Duración no especificada'} · {c.skills_count} competencias
                    </div>
                  </div>
                </button>
              ))}
            </div>
          )}

          {query.trim().length >= 2 && !loading && cursos.length === 0 && (
            <p className="text-xs text-gray-400 text-center py-2">No se encontraron cursos. Probá con otras palabras.</p>
          )}
        </>
      )}
    </div>
  )
}
