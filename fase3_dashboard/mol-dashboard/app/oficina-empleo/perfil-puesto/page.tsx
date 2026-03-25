'use client'

import { useState } from 'react'
import JobProfileForm, { type JobProfile } from '@/components/JobProfileForm'
import { OEBreadcrumb } from '@/components/oficina-empleo/OEBreadcrumb'
import { CheckCircle2 } from 'lucide-react'

export default function PerfilPuestoPage() {
  const [saved, setSaved] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSave = async (profile: JobProfile) => {
    setSaved(false)
    setError(null)
    try {
      const res = await fetch('/api/perfil-puesto', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          titulo: profile.titulo,
          isco: profile.isco,
          skills: profile.skills,
        }),
      })
      if (!res.ok) {
        const data = await res.json()
        throw new Error(data.error || 'Error al guardar')
      }
      setSaved(true)
    } catch (e: any) {
      setError(e.message)
    }
  }

  return (
    <div className="mx-auto max-w-2xl px-4 py-8">
      <OEBreadcrumb items={[{ label: "Perfil de Puesto" }]} />
      <h1 className="mb-1 text-2xl font-bold text-gray-900">Perfil de puesto</h1>
      <p className="mb-6 text-sm text-gray-500">
        Defini las skills requeridas para una vacante. El sistema las usa para calcular compatibilidad con candidatos.
      </p>

      {saved && (
        <div className="flex items-center gap-2 mb-4 px-4 py-3 rounded-lg bg-green-50 border border-green-200 text-green-800 text-sm">
          <CheckCircle2 className="w-4 h-4" /> Perfil de puesto guardado
        </div>
      )}
      {error && (
        <div className="mb-4 px-4 py-3 rounded-lg bg-red-50 border border-red-200 text-red-800 text-sm">
          {error}
        </div>
      )}

      <JobProfileForm onSave={handleSave} />
    </div>
  )
}
