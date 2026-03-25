'use client'

import { Suspense, useState, useEffect } from 'react'
import { useSearchParams } from 'next/navigation'
import Link from 'next/link'
import { ArrowLeft } from 'lucide-react'
import TrainingImpact, { type TrainingImpactData } from '@/components/TrainingImpact'
import { OEBreadcrumb } from '@/components/oficina-empleo/OEBreadcrumb'

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
    <div className="text-center py-12 text-gray-400">
      <p className="text-sm mb-4">Selecciona un perfil para ver su formacion con impacto.</p>
      <Link href="/oficina-empleo/perfil" className="text-teal-600 text-sm font-medium inline-flex items-center gap-1">
        <ArrowLeft className="w-4 h-4" /> Ir a Perfil Trabajador
      </Link>
    </div>
  )
  if (loading) return (
    <div className="space-y-4">
      {[1, 2].map((i) => <div key={i} className="h-24 animate-pulse rounded-lg bg-gray-100" />)}
    </div>
  )
  if (error) return (
    <p className="text-sm text-red-500">No se pudo cargar la informacion de formacion.</p>
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
      <OEBreadcrumb items={[
        { label: "Perfil", href: "/oficina-empleo/perfil" },
        { label: "Formacion con impacto" },
      ]} />
      <h1 className="mb-1 text-2xl font-bold text-gray-900">Formacion con impacto</h1>
      <p className="mb-6 text-sm text-gray-500">
        Cursos que mejoran la compatibilidad del perfil con las ocupaciones del mercado.
      </p>
      <Suspense fallback={<div className="h-24 animate-pulse rounded-lg bg-gray-100" />}>
        <FormacionContent />
      </Suspense>
    </div>
  )
}
