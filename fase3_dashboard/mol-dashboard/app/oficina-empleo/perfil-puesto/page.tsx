'use client'

import JobProfileForm, { type JobProfile } from '@/components/JobProfileForm'

export default function PerfilPuestoPage() {
  const handleSave = async (profile: JobProfile) => {
    // TODO: POST /api/perfil-puesto
    console.log('Guardar perfil de puesto:', profile)
  }

  return (
    <div className="mx-auto max-w-2xl px-4 py-8">
      <h1 className="mb-1 text-2xl font-bold text-gray-900">Perfil de puesto</h1>
      <p className="mb-6 text-sm text-gray-500">
        Definí las skills requeridas para una vacante. El sistema las usa para calcular compatibilidad con candidatos.
      </p>
      <JobProfileForm onSave={handleSave} />
    </div>
  )
}
