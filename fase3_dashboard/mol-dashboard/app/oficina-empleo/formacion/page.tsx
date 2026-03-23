'use client'

import { Suspense, useState, useEffect } from 'react'
import { useSearchParams } from 'next/navigation'
import TrainingImpact, { type TrainingImpactData } from '@/components/TrainingImpact'

function FormacionContent() {
  const searchParams = useSearchParams()
  const profileId = searchParams.get('profile_id')
  const [data, setData] = useState<TrainingImpactData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)

  useEffect(() => {
    if (!profileId) { setLoading(false); return }
    const load = async () => {
      setLoading(true)
      setError(false)
      try {
        const res = await fetch(`/api/training-impact?profile_id=${profileId}`)
        if (res.ok) setData(await res.json())
        else setError(true)
      } catch {
        setError(true)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [profileId])

  if (!profileId) return (
    <p className="text-sm text-gray-400">Seleccioná un perfil para ver su formación con impacto.</p>
  )
  if (loading) return (
    <div className="space-y-4">
      {[1, 2].map((i) => <div key={i} className="h-24 animate-pulse rounded-lg bg-gray-100" />)}
    </div>
  )
  if (error) return (
    <p className="text-sm text-red-500">No se pudo cargar la información de formación.</p>
  )
  if (!data) return null

  return (
    <TrainingImpact
      data={data}
      onDerivar={(id, name) => console.log('Derivado:', id, name)}
    />
  )
}

export default function FormacionPage() {
  return (
    <div className="mx-auto max-w-3xl px-4 py-8">
      <h1 className="mb-1 text-2xl font-bold text-gray-900">Formación con impacto</h1>
      <p className="mb-6 text-sm text-gray-500">
        Cursos que mejoran la compatibilidad del perfil con las ocupaciones del mercado.
      </p>
      <Suspense fallback={<div className="h-24 animate-pulse rounded-lg bg-gray-100" />}>
        <FormacionContent />
      </Suspense>
    </div>
  )
}
