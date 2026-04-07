'use client'

import { useState, useEffect } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { Briefcase, Search, Wrench, Loader2 } from 'lucide-react'
import { OEBreadcrumb } from '@/components/oficina-empleo/OEBreadcrumb'
import { useSkillCapture, type SelectedSkill } from '@/components/oficina-empleo/useSkillCapture'
import { OccupationSkillPicker } from '@/components/oficina-empleo/OccupationSkillPicker'
import { TaskSkillSearch } from '@/components/oficina-empleo/TaskSkillSearch'
import { StructuredSkills } from '@/components/oficina-empleo/StructuredSkills'
import { SkillProfilePanel } from '@/components/oficina-empleo/SkillProfilePanel'

type Via = 'ocupacion' | 'tarea' | 'estructurado'

const VIA_TABS: { id: Via; label: string; icon: typeof Briefcase }[] = [
  { id: 'ocupacion', label: 'Ocupación', icon: Briefcase },
  { id: 'tarea', label: 'Tareas', icon: Search },
  { id: 'estructurado', label: 'Herramientas', icon: Wrench },
]

function parseUbicacion(ubicacion: string | null | undefined): { localidad: string; provincia: string } {
  if (!ubicacion) return { localidad: '', provincia: '' }
  const parts = ubicacion.split(',').map(s => s.trim())
  if (parts.length >= 2) return { localidad: parts[0], provincia: parts[parts.length - 1] }
  return { localidad: '', provincia: ubicacion }
}

export default function NuevoPerfilPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const editId = searchParams.get('edit')

  const capture = useSkillCapture()
  const [activeVia, setActiveVia] = useState<Via>('ocupacion')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [loadingEdit, setLoadingEdit] = useState(!!editId)

  // Edit mode: load existing perfil
  useEffect(() => {
    if (!editId) return
    setLoadingEdit(true)
    fetch(`/api/perfiles?id=${editId}`)
      .then(r => r.ok ? r.json() : Promise.reject())
      .then(data => {
        // Pre-fill persona data
        capture.setNombre(data.personas?.nombre || '')
        capture.setDni(data.personas?.dni || '')
        const { localidad, provincia } = parseUbicacion(data.personas?.ubicacion)
        capture.setLocalidad(localidad)
        capture.setProvincia(provincia)

        // Pre-fill ocupaciones
        capture.setOcupaciones(data.ocupaciones || [])

        // Pre-fill skills from perfil_skills
        const skills: SelectedSkill[] = (data.skills || []).map((s: any) => ({
          uri: s.skill_uri,
          label: s.skill_label,
          type: 'skill' as const,
          source: (s.via_captura === 'ocupacion' ? 'ocupacion'
            : s.via_captura === 'tarea' ? 'busqueda'
            : s.via_captura === 'texto' ? 'texto'
            : s.via_captura === 'estructurado' ? 'estructurado'
            : 'busqueda') as any,
        }))
        capture.setSkills(skills)
      })
      .catch(() => setError('Error cargando perfil'))
      .finally(() => setLoadingEdit(false))
  }, [editId]) // eslint-disable-line react-hooks/exhaustive-deps

  async function handleSave() {
    setError('')
    setSaving(true)

    // Build ubicacion from localidad + provincia
    const ubicacion = capture.localidad && capture.provincia
      ? `${capture.localidad}, ${capture.provincia}`
      : capture.provincia || capture.localidad || undefined

    try {
      if (editId) {
        // === EDIT MODE: PUT existing perfil ===
        const res = await fetch(`/api/perfiles/${editId}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            nombre: capture.nombre,
            dni: capture.dni,
            ubicacion,
            ocupaciones: capture.ocupaciones,
            skills: capture.skills.map(s => ({
              uri: s.uri,
              label: s.label,
              source: s.source,
            })),
          }),
        })
        if (!res.ok) {
          const d = await res.json()
          setError(d.error || 'Error actualizando perfil')
          return
        }
        router.push(`/oficina-empleo/perfiles/${editId}`)
      } else {
        // === CREATE MODE: POST new persona + perfil + skills ===
        // 1. Create or find persona
        const personaRes = await fetch('/api/personas', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            nombre: capture.nombre,
            dni: capture.dni,
            ubicacion,
          }),
        })
        if (!personaRes.ok) {
          const d = await personaRes.json()
          setError(d.error || 'Error creando persona')
          return
        }
        const persona = await personaRes.json()

        // 2. Create perfil
        const perfilRes = await fetch('/api/perfiles', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            persona_id: persona.id,
            ocupaciones: capture.ocupaciones,
          }),
        })
        if (!perfilRes.ok) {
          const d = await perfilRes.json()
          setError(d.error || 'Error creando perfil')
          return
        }
        const perfil = await perfilRes.json()

        // 3. Add skills
        const skillRows = capture.skills.map(s => ({
          skill_uri: s.uri,
          skill_label: s.label,
          via_captura: s.source === 'ocupacion' ? 'ocupacion'
            : s.source === 'busqueda' ? 'tarea'
            : s.source === 'texto' ? 'texto'
            : s.source === 'estructurado' ? 'estructurado'
            : 'tarea',
          estado: 'confirmada',
          confianza: 0.8,
        }))
        const skillsRes = await fetch(`/api/perfiles/${perfil.id}/skills`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ skills: skillRows }),
        })
        if (!skillsRes.ok) {
          const d = await skillsRes.json()
          setError(d.error || 'Error guardando skills')
          return
        }

        router.push(`/oficina-empleo/perfiles/${perfil.id}`)
      }
    } catch {
      setError('Error de conexión')
    } finally {
      setSaving(false)
    }
  }

  if (loadingEdit) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <Loader2 className="w-6 h-6 animate-spin text-teal-600" />
        <span className="ml-2 text-sm text-gray-500">Cargando perfil...</span>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-6xl mx-auto px-4 py-6">
        <OEBreadcrumb items={[
          { label: 'Perfil de Competencias', href: '/oficina-empleo/perfiles' },
          { label: editId ? 'Editar' : 'Nuevo' },
        ]} />

        {error && (
          <div className="mb-4 bg-red-50 border border-red-200 text-red-700 text-sm px-4 py-2 rounded-lg">
            {error}
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5 items-start">
          {/* Left panel — capture */}
          <div className="bg-white rounded-xl border border-gray-200 p-5 space-y-4">
            <h2 className="text-lg font-semibold text-gray-900">
              {editId ? 'Editar skills' : 'Captura de skills'}
            </h2>

            {/* Via tabs */}
            <div className="flex gap-1 bg-gray-100 rounded-lg p-1">
              {VIA_TABS.map(v => (
                <button
                  key={v.id}
                  onClick={() => setActiveVia(v.id)}
                  className={`flex items-center gap-1.5 px-3 py-2 rounded-md text-sm font-medium transition-colors flex-1 justify-center ${
                    activeVia === v.id ? 'bg-white text-teal-700 shadow-sm' : 'text-gray-500 hover:text-gray-700'
                  }`}
                >
                  <v.icon className="w-4 h-4" />
                  {v.label}
                </button>
              ))}
            </div>

            {activeVia === 'ocupacion' && (
              <OccupationSkillPicker
                ocupaciones={capture.ocupaciones}
                skillUris={capture.skillUris}
                onAddOccupation={capture.addOccupation}
                onRemoveOccupation={capture.removeOccupation}
                onAddSkills={capture.addSkills}
              />
            )}
            {activeVia === 'tarea' && (
              <TaskSkillSearch
                skillUris={capture.skillUris}
                onAddSkill={capture.addSkill}
                onAddSkills={capture.addSkills}
              />
            )}
            {activeVia === 'estructurado' && (
              <StructuredSkills
                skillUris={capture.skillUris}
                onAddSkill={capture.addSkill}
              />
            )}
          </div>

          {/* Right panel — accumulated profile */}
          <div className="bg-white rounded-xl border border-gray-200 p-5 lg:sticky lg:top-6" style={{ maxHeight: 'calc(100vh - 120px)' }}>
            <h2 className="text-lg font-semibold text-gray-900 mb-3">
              {editId ? 'Perfil' : 'Perfil acumulado'}
            </h2>
            <SkillProfilePanel
              ocupaciones={capture.ocupaciones}
              skills={capture.skills}
              onRemoveSkill={capture.removeSkill}
              onRemoveOccupation={capture.removeOccupation}
              nombre={capture.nombre}
              dni={capture.dni}
              localidad={capture.localidad}
              provincia={capture.provincia}
              onSetNombre={capture.setNombre}
              onSetDni={capture.setDni}
              onSetLocalidad={capture.setLocalidad}
              onSetProvincia={capture.setProvincia}
              onSave={handleSave}
              saving={saving}
              editMode={!!editId}
            />
          </div>
        </div>
      </div>
    </div>
  )
}
