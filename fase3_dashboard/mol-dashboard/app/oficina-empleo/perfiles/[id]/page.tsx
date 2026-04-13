'use client'

import { useState, useEffect, useMemo, useRef } from 'react'
import QRCode from 'qrcode'
import { useParams, useRouter } from 'next/navigation'
import Link from 'next/link'
import { Loader2, Printer, Pencil, ArrowRight, Shield, ShieldOff, Briefcase, Trash2 } from 'lucide-react'
import { OEBreadcrumb } from '@/components/oficina-empleo/OEBreadcrumb'

interface PerfilSkill {
  id: string
  uri: string
  label: string
  via_captura: string
  estado: string
  confianza: number
  nivel: string
  certificado: boolean
}

const NIVEL_COLORS: Record<string, string> = {
  basico: 'bg-slate-100 text-slate-600',
  intermedio: 'bg-teal-100 text-teal-700',
  avanzado: 'bg-blue-100 text-blue-700',
  experto: 'bg-purple-100 text-purple-700',
}

const NIVEL_LABELS: Record<string, string> = {
  basico: 'Básico',
  intermedio: 'Intermedio',
  avanzado: 'Avanzado',
  experto: 'Experto',
}

interface PerfilData {
  id: string
  persona_id: string
  nombre: string
  dni: string
  ocupaciones: { id: string; label: string; isco_code: string }[]
  estado: string
  validado_at: string | null
  created_at: string | null
  skills: PerfilSkill[]
}

interface Section {
  key: string
  label: string
  skills: PerfilSkill[]
}

function classifyByVia(skills: PerfilSkill[]): Section[] {
  const map: Record<string, { label: string; skills: PerfilSkill[] }> = {
    ocupacion: { label: 'Competencias de ocupación', skills: [] },
    tarea: { label: 'Competencias por tarea', skills: [] },
    texto: { label: 'Competencias por relato', skills: [] },
    estructurado: { label: 'Herramientas e idiomas', skills: [] },
    formacion: { label: 'Competencias por formación', skills: [] },
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
  const [deleting, setDeleting] = useState(false)
  const [confirmDelete, setConfirmDelete] = useState(false)
  const [qrUrl, setQrUrl] = useState('')
  const [qrFailed, setQrFailed] = useState(false)

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
          created_at: data.created_at || data.updated_at || null,
          skills: (data.skills || []).map((s: any) => ({
            id: s.id,
            uri: s.skill_uri,
            label: s.skill_label,
            via_captura: s.via_captura,
            estado: s.estado,
            confianza: s.confianza,
            nivel: s.nivel || 'intermedio',
            certificado: s.certificado || false,
          })),
        })
      })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [id])

  // Generate QR code
  const qrCanvasRef = useRef<HTMLCanvasElement>(null)
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const url = `${window.location.origin}/oficina-empleo/perfiles/${id}`
      setQrUrl(url)
      if (qrCanvasRef.current) {
        QRCode.toCanvas(qrCanvasRef.current, url, {
          width: 80,
          margin: 1,
          color: { dark: '#1f2937', light: '#ffffff' },
        }).catch(() => setQrFailed(true))
      }
    }
  }, [id, perfil])

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

  async function handleDelete() {
    setDeleting(true)
    try {
      const res = await fetch(`/api/perfiles/${id}`, { method: 'DELETE' })
      if (res.ok) {
        router.push('/oficina-empleo/perfiles')
      }
    } catch {} finally {
      setDeleting(false)
      setConfirmDelete(false)
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
  const createdDate = perfil.created_at
    ? new Date(perfil.created_at).toLocaleDateString('es-AR')
    : new Date().toLocaleDateString('es-AR')

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

            {/* QR code */}
            <div className="w-20 h-20 rounded-lg flex items-center justify-center shrink-0 print:bg-white bg-gray-50">
              {qrFailed ? (
                <span className="text-[10px] text-gray-400 text-center">QR no disponible</span>
              ) : (
                <canvas ref={qrCanvasRef} className="rounded" />
              )}
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
              <div className="space-y-1.5">
                {sec.skills.map(s => (
                  <div key={s.id}>
                    <span className="text-sm text-gray-800">● {s.label}</span>
                    <div className="flex items-center gap-1.5 ml-3 mt-0.5">
                      <span className={`text-[10px] px-1.5 py-0.5 rounded font-medium ${NIVEL_COLORS[s.nivel] || NIVEL_COLORS.intermedio}`}>
                        {NIVEL_LABELS[s.nivel] || 'Intermedio'}
                      </span>
                      {s.certificado && (
                        <span className="text-[10px] px-1.5 py-0.5 rounded font-medium bg-green-100 text-green-700">
                          ✓ Cert
                        </span>
                      )}
                    </div>
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

          {!confirmDelete ? (
            <button
              onClick={() => setConfirmDelete(true)}
              className="inline-flex items-center gap-1.5 bg-white border border-gray-200 text-red-500 text-sm font-medium px-4 py-2 rounded-lg hover:bg-red-50 hover:border-red-200 transition-colors"
            >
              <Trash2 className="w-4 h-4" /> Eliminar
            </button>
          ) : (
            <div className="inline-flex items-center gap-2 bg-red-50 border border-red-200 text-sm px-4 py-2 rounded-lg">
              <span className="text-red-700 font-medium">Eliminar perfil?</span>
              <button
                onClick={handleDelete}
                disabled={deleting}
                className="text-red-700 font-semibold hover:text-red-800 disabled:opacity-50"
              >
                {deleting ? 'Eliminando...' : 'Si'}
              </button>
              <button
                onClick={() => setConfirmDelete(false)}
                className="text-gray-500 hover:text-gray-700"
              >
                No
              </button>
            </div>
          )}

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
