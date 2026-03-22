'use client'

import { useState, useEffect } from 'react'
import { useSearchParams } from 'next/navigation'
import TrainingImpact, { type TrainingImpactData } from '@/components/TrainingImpact'

// Mock hasta que Gerardo implemente GET /api/training-impact
const MOCK_DATA: TrainingImpactData = {
  profile_id: 'demo',
  current_match: 62,
  max_potential_match: 89,
  gap_groups: [
    {
      skill_label: 'Programación en Python',
      courses: [
        {
          id: 1,
          name: 'Python para análisis de datos',
          certificacion: 'Certificado CABA',
          duracion: '3 meses',
          modalidad: 'Online',
          covers_skills: ['Python', 'Pandas', 'NumPy'],
          url: 'https://capacitacion.buenosaires.gob.ar',
          delta_match: 15,
        },
        {
          id: 2,
          name: 'Introducción a Python',
          certificacion: '',
          duracion: '6 semanas',
          modalidad: 'Presencial',
          covers_skills: ['Python'],
          delta_match: 8,
        },
      ],
    },
    {
      skill_label: 'Gestión de bases de datos SQL',
      courses: [
        {
          id: 3,
          name: 'SQL para principiantes',
          certificacion: 'Certificado MTEySS',
          duracion: '4 semanas',
          modalidad: 'Online',
          covers_skills: ['SQL', 'PostgreSQL'],
          url: 'https://cursos.trabajo.gob.ar',
          delta_match: 12,
        },
      ],
    },
  ],
}

export default function FormacionPage() {
  const searchParams = useSearchParams()
  const profileId = searchParams.get('profile_id') ?? 'demo'
  const [data, setData] = useState<TrainingImpactData | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const load = async () => {
      setLoading(true)
      try {
        const res = await fetch(`/api/training-impact?profile_id=${profileId}`)
        if (res.ok) {
          setData(await res.json())
        } else {
          setData(MOCK_DATA)
        }
      } catch {
        setData(MOCK_DATA)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [profileId])

  return (
    <div className="mx-auto max-w-3xl px-4 py-8">
      <h1 className="mb-1 text-2xl font-bold text-gray-900">Formación con impacto</h1>
      <p className="mb-6 text-sm text-gray-500">
        Cursos que mejoran la compatibilidad del perfil con las ocupaciones del mercado.
      </p>

      {loading ? (
        <div className="space-y-4">
          {[1, 2].map((i) => (
            <div key={i} className="h-24 animate-pulse rounded-lg bg-gray-100" />
          ))}
        </div>
      ) : data ? (
        <TrainingImpact
          data={data}
          onDerivar={(id, name) => console.log('Derivado:', id, name)}
        />
      ) : (
        <p className="text-sm text-gray-400">No se pudo cargar la información de formación.</p>
      )}
    </div>
  )
}
