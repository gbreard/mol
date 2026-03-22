'use client'

import { useState } from 'react'
import { MessageSquare, Check, MapPin, Briefcase } from 'lucide-react'

export interface AnonProfile {
  id: string
  perfil_numero: number
  jurisdiccion: string
  match_score: number
  skills: string[]
  ocupaciones_previas: number
}

interface Props {
  profile: AnonProfile
  onSolicitarContacto?: (profileId: string) => Promise<void>
}

export default function AnonProfileCard({ profile, onSolicitarContacto }: Props) {
  const [loading, setLoading] = useState(false)
  const [solicitado, setSolicitado] = useState(false)

  const handleSolicitar = async () => {
    setLoading(true)
    try {
      await onSolicitarContacto?.(profile.id)
      setSolicitado(true)
    } finally {
      setLoading(false)
    }
  }

  const scoreColor =
    profile.match_score >= 75
      ? 'text-green-700 bg-green-100'
      : profile.match_score >= 50
        ? 'text-yellow-700 bg-yellow-100'
        : 'text-red-700 bg-red-100'

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-4">
      {/* Header */}
      <div className="mb-3 flex flex-wrap items-center gap-2">
        <span className="text-sm font-semibold text-gray-700">
          Perfil #{profile.perfil_numero}
        </span>
        <span className="flex items-center gap-1 text-xs text-gray-500">
          <MapPin className="h-3 w-3" />
          {profile.jurisdiccion}
        </span>
        <span className={`ml-auto rounded-full px-2.5 py-0.5 text-xs font-bold ${scoreColor}`}>
          Match: {profile.match_score}%
        </span>
      </div>

      {/* Skills */}
      <div className="mb-3 flex flex-wrap gap-1.5">
        {profile.skills.map((skill) => (
          <span
            key={skill}
            className="rounded bg-blue-50 px-2 py-0.5 text-xs text-blue-700"
          >
            {skill}
          </span>
        ))}
      </div>

      {/* Trayectoria */}
      <p className="mb-3 flex items-center gap-1.5 text-xs text-gray-500">
        <Briefcase className="h-3.5 w-3.5" />
        {`Trayectoria: ${profile.ocupaciones_previas} ${profile.ocupaciones_previas !== 1 ? 'ocupaciones previas' : 'ocupación previa'}`}
      </p>

      {/* CTA */}
      {solicitado ? (
        <div className="flex items-center gap-2 rounded-lg bg-green-50 px-4 py-2.5 text-sm text-green-700">
          <Check className="h-4 w-4" />
          Solicitud enviada — el trabajador decidirá si acepta
        </div>
      ) : (
        <button
          onClick={handleSolicitar}
          disabled={loading}
          aria-label={`Solicitar contacto con Perfil #${profile.perfil_numero}`}
          className="flex min-h-[44px] w-full items-center justify-center gap-2 rounded-lg border border-blue-300 px-4 py-2 text-sm font-medium text-blue-600 hover:bg-blue-50 disabled:opacity-50"
        >
          <MessageSquare className="h-4 w-4" />
          {loading ? 'Enviando...' : 'Solicitar contacto'}
        </button>
      )}
    </div>
  )
}
