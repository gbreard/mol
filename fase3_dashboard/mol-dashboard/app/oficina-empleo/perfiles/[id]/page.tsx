'use client'

import { useState, useEffect, useMemo } from 'react'
import { useParams, useRouter } from 'next/navigation'
import Link from 'next/link'
import { Loader2, Printer, Pencil, ArrowRight, Shield, ShieldOff, Briefcase } from 'lucide-react'
import { OEBreadcrumb } from '@/components/oficina-empleo/OEBreadcrumb'

interface PerfilSkill {
  id: string
  uri: string
  label: string
  via_captura: string
  estado: string
  confianza: number
}

interface PerfilData {
  id: string
  persona_id: string
  nombre: string
  dni: string
  ocupaciones: { id: string; label: string; isco_code: string }[]
  estado: string
  validado_at: string | null
  skills: PerfilSkill[]
}

interface Section {
  key: string
  label: string
  skills: PerfilSkill[]
}

function classifyByVia(skills: PerfilSkill[]): Section[] {
  const map: Record<string, { label: string; skills: PerfilSkill[] }> = {
    ocupacion: { label: 'Skills de ocupación', skills: [] },
    tarea: { label: 'Skills por tarea', skills: [] },
    texto: { label: 'Skills por relato', skills: [] },
    estructurado: { label: 'Herramientas e idiomas', skills: [] },
    formacion: { label: 'Skills por formación', skills: [] },
  }
  for (const s of skills) {
    const via = s.via_captura || 'tarea'
    if (map[via]) map[via].skills.push(s)
    else map.tarea.skills.push(s)
  }
  return Object.entries(map)
    .filter(([, v]) => v.skills.length > 0)
    .map(([key, v]) => ({ key, label: v.label, skills: v.skills }))
}

export default function PerfilDetailPage() {
  const params = useParams()
  const router = useRouter()
  const id = params.id as string
  const [perfil, setPerfil] = useState<PerfilData | null>(null)
  const [loading, setLoading] = useState(true)
  const [toggling, setToggling] = useState(false)
  const [qrUrl, setQrUrl] = useState('')

  useEffect(() => {
    fetch(`/api/perfiles?id=${id}`)
      .then(r => r.ok ? r.json() : Promise.reject())
      .then(data => {
        setPerfil({
          id: data.id,
          persona_id: data.persona_id,
          nombre: data.personas?.nombre || '',
          dni: data.personas?.dni || '',
          ocupaciones: data.ocupaciones || [],
          estado: data.estado || 'borrador',
          validado_at: data.validado_at,
          skills: (data.skills || []).map((s: any) => ({
            id: s.id,
            uri: s.skill_uri,
            label: s.skill_label,
            via_captura: s.via_captura,
            estado: s.estado,
            confianza: s.confianza,
          })),
        })
      })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [id])

  // Lazy load QR code
  useEffect(() => {
    if (typeof window !== 'undefined') {
      setQrUrl(`${window.location.origin}/oficina-empleo/perfiles/${id}`)
    }
  }, [id])

  const sections = useMemo(() => perfil ? classifyByVia(perfil.skills) : [], [perfil])

  async function toggleEstado() {
    if (!perfil) return
    setToggling(true)
    const newEstado = perfil.estado === 'validado' ? 'borrador' : 'validado'
    try {
      const res = await fetch(`/api/perfiles/${id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ estado: newEstado }),
      })
      if (res.ok) {
        const data = await res.json()
        setPerfil(prev => prev ? { ...prev, estado: data.estado, validado_at: data.validado_at } : prev)
      }
    } catch {} finally {
      setToggling(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
      </div>
    )
  }

  if (!perfil) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <p className="text-gray-500">Perfil no encontrado</p>
      </div>
    )
  }

  const validadoDate = perfil.validado_at ? new Date(perfil.validado_at).toLocaleDateString('es-AR') : null
  const createdDate = new Date().toLocaleDateString('es-AR')

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-3xl mx-auto px-4 py-6">
        <div className="print:hidden">
          <OEBreadcrumb items={[
            { label: 'Perfil de Competencias', href: '/oficina-empleo/perfiles' },
            { label: perfil.nombre },
          ]} />
        </div>

        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden print:border-none print:shadow-none">
          {/* Header */}
          <div className="px-6 py-5 border-b flex items-start justify-between">
            <div>
              <h1 className="text-xl font-bold text-gray-900">{perfil.nombre}</h1>
              <p className="text-sm text-gray-500 mt-0.5">DNI {perfil.dni}</p>
              <p className="text-sm text-gray-500">
                {perfil.skills.length} competencias
                {perfil.ocupaciones.length > 0 && ` · ${perfil.ocupaciones.length} ocupaciones`}
              </p>
              <div className="mt-2">
                {perfil.estado === 'validado' ? (
                  <span className="inline-flex items-center gap-1 text-xs font-medium text-green-700 bg-green-50 px-2.5 py-1 rounded-full">
                    <span className="w-1.5 h-1.5 rounded-full bg-green-500" />
                    Validado {validadoDate && `· ${validadoDate}`}
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1 text-xs font-medium text-gray-500 bg-gray-100 px-2.5 py-1 rounded-full">
                    <span className="w-1.5 h-1.5 rounded-full bg-gray-400" />
                    Borrador
                  </span>
                )}
              </div>
            </div>

            {/* QR placeholder */}
            <div className="w-20 h-20 bg-gray-100 rounded-lg flex items-center justify-center text-xs text-gray-400 shrink-0 print:bg-white">
              QR
            </div>
          </div>

          {/* Occupations */}
          {perfil.ocupaciones.length > 0 && (
            <div className="px-6 py-4 border-b">
              <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Ocupaciones</h2>
              <div className="flex flex-wrap gap-2">
                {perfil.ocupaciones.map((occ, i) => (
                  <span key={i} className="inline-flex items-center gap-1.5 bg-teal-50 text-teal-700 text-sm font-medium px-3 py-1 rounded-lg">
                    <Briefcase className="w-3.5 h-3.5" />
                    {occ.label}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Skills by section */}
          {sections.map(sec => (
            <div key={sec.key} className="px-6 py-4 border-b last:border-b-0">
              <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
                {sec.label} <span className="text-gray-400 font-normal">({sec.skills.length})</span>
              </h2>
              <div className="space-y-1">
                {sec.skills.map(s => (
                  <div key={s.id} className="flex items-center gap-2">
                    <span className="text-sm text-gray-800">● {s.label}</span>
                  </div>
                ))}
              </div>
            </div>
          ))}

          {/* Footer */}
          <div className="px-6 py-3 bg-gray-50 text-xs text-gray-400 text-center print:bg-white">
            Generado por MOL · {createdDate}
          </div>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-3 mt-4 print:hidden">
          <Link
            href={`/oficina-empleo/perfiles/nuevo?edit=${id}`}
            className="inline-flex items-center gap-1.5 bg-white border border-gray-200 text-gray-700 text-sm font-medium px-4 py-2 rounded-lg hover:bg-gray-50 transition-colors"
          >
            <Pencil className="w-4 h-4" /> Editar perfil
          </Link>

          <button
            onClick={toggleEstado}
            disabled={toggling}
            className="inline-flex items-center gap-1.5 bg-white border border-gray-200 text-gray-700 text-sm font-medium px-4 py-2 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50"
          >
            {perfil.estado === 'validado' ? (
              <><ShieldOff className="w-4 h-4" /> Quitar validación</>
            ) : (
              <><Shield className="w-4 h-4" /> Validar perfil</>
            )}
          </button>

          <button
            onClick={() => window.print()}
            className="inline-flex items-center gap-1.5 bg-white border border-gray-200 text-gray-700 text-sm font-medium px-4 py-2 rounded-lg hover:bg-gray-50 transition-colors"
          >
            <Printer className="w-4 h-4" /> Imprimir
          </button>

          <Link
            href={`/oficina-empleo/perfiles/matching?perfil_id=${id}`}
            className="inline-flex items-center gap-1.5 bg-teal-600 text-white text-sm font-semibold px-4 py-2 rounded-lg hover:bg-teal-700 transition-colors ml-auto"
          >
            Oportunidades <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </div>
    </div>
  )
}
