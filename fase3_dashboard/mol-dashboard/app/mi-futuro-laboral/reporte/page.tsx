'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import {
  ArrowLeft, Download, Share2, QrCode, CheckCircle,
  Briefcase, User, TrendingUp, BookOpen, Loader2, Copy, RotateCcw,
} from 'lucide-react'
import { useS1Store } from '@/lib/use-s1-store'

// ─── Tipos locales ────────────────────────────────────────────────────────────
type TipoReporte = 'generico' | 'vacante'

interface MockVacante {
  id: number
  titulo: string
  empresa: string
  match: number
}

const MOCK_VACANTES: MockVacante[] = [
  { id: 1, titulo: 'Técnico IT Junior', empresa: 'TechSolutions SA', match: 84 },
  { id: 2, titulo: 'Soporte Técnico N1', empresa: 'BancoCentral', match: 78 },
  { id: 3, titulo: 'Analista de Datos Jr.', empresa: 'Startup ABC', match: 71 },
]

// ─── Sub-componente: selección de tipo de reporte ────────────────────────────
function TipoCard({
  active, onClick, icon: Icon, title, desc,
}: {
  active: boolean
  onClick: () => void
  icon: React.ElementType
  title: string
  desc: string
}) {
  return (
    <button
      onClick={onClick}
      className={`w-full flex items-start gap-3 rounded-xl border p-4 text-left transition-all ${
        active
          ? 'border-blue-500 bg-blue-50 ring-1 ring-blue-200'
          : 'border-gray-200 bg-white hover:border-gray-300 hover:bg-gray-50'
      }`}
    >
      <div className={`mt-0.5 shrink-0 rounded-lg p-2 ${active ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-500'}`}>
        <Icon className="w-4 h-4" />
      </div>
      <div>
        <p className={`text-sm font-semibold ${active ? 'text-blue-800' : 'text-gray-800'}`}>{title}</p>
        <p className={`text-xs mt-0.5 ${active ? 'text-blue-600' : 'text-gray-500'}`}>{desc}</p>
      </div>
      {active && <CheckCircle className="w-4 h-4 text-blue-600 shrink-0 ml-auto mt-0.5" />}
    </button>
  )
}

// ─── Página principal ────────────────────────────────────────────────────────
export default function ReportePage() {
  const router = useRouter()
  const { store, confirmed } = useS1Store()

  const [tipo, setTipo] = useState<TipoReporte>('generico')
  const [vacanteSeleccionada, setVacanteSeleccionada] = useState<MockVacante | null>(null)
  const [generando, setGenerando] = useState(false)
  const [token, setToken] = useState<string | null>(null)
  const [copiado, setCopiado] = useState(false)

  const nombre = store.nombre || 'Candidato'
  const matchScore = vacanteSeleccionada?.match ?? 73
  const qrUrl = token ? `https://mol.gob.ar/reporte/${token}` : null

  const handleGenerar = async () => {
    setGenerando(true)
    try {
      // Llamar a la API real si existe; si no, usar mock
      const res = await fetch('/api/compatibility-report', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          candidato_nombre: nombre,
          ocupacion_uri: 'esco_3511',
          ocupacion_label: 'Técnico en sistemas informáticos',
          ocupacion_isco: '3511',
          oferta_id: vacanteSeleccionada?.id ?? null,
          oferta_titulo: vacanteSeleccionada?.titulo ?? null,
          origen: 'trabajador',
          match_score: matchScore,
          skills_candidato: confirmed.map((s) => ({
            uri: s.uri,
            label: s.label,
            type: s.type,
            source: s.source,
          })),
          skills_requeridas: [],
          skills_cubiertas: confirmed.slice(0, Math.floor(confirmed.length * 0.8)),
          skills_gap: [],
        }),
      })

      if (res.ok) {
        const data = await res.json()
        setToken(data.token ?? data.report?.token ?? 'MOCK_TOKEN_001')
      } else {
        // Mock fallback
        setToken('MOCK_TOKEN_001')
      }
    } catch {
      // Mock fallback cuando no hay backend
      setToken('MOCK_TOKEN_001')
    } finally {
      setGenerando(false)
    }
  }

  const handleCopiarLink = async () => {
    if (!qrUrl) return
    try {
      await navigator.clipboard.writeText(qrUrl)
    } catch {
      // fallback silencioso
    }
    setCopiado(true)
    setTimeout(() => setCopiado(false), 2000)
  }

  const handleDescargarPDF = () => {
    if (!token) return
    // En producción: redirige al endpoint de generación de PDF
    window.open(`/api/compatibility-report/pdf?token=${token}`, '_blank')
  }

  // ── Vista: reporte generado ──────────────────────────────────────────────
  if (token) {
    return (
      <div className="min-h-screen bg-gray-50">
        <div className="max-w-md mx-auto px-4 py-8">
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-green-100 rounded-full mb-4">
              <CheckCircle className="w-8 h-8 text-green-600" />
            </div>
            <h1 className="text-xl font-bold text-gray-900 mb-1">¡Reporte generado!</h1>
            <p className="text-gray-500 text-sm">
              Podés compartirlo con empleadores o descargarlo como PDF.
            </p>
          </div>

          {/* Preview tarjeta */}
          <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-5 mb-4">
            <div className="flex items-start justify-between mb-4">
              <div>
                <p className="text-xs text-gray-400 uppercase tracking-wider mb-1">Reporte de competencias</p>
                <h2 className="text-base font-bold text-gray-900">{nombre}</h2>
                <p className="text-sm text-gray-500 mt-0.5">
                  {vacanteSeleccionada ? vacanteSeleccionada.titulo : 'Técnico en sistemas informáticos'}
                </p>
              </div>
              <div className="text-right">
                <p className="text-xs text-gray-400">Match</p>
                <p className="text-2xl font-bold text-blue-600">{matchScore}%</p>
              </div>
            </div>

            {/* Skills chips */}
            <div className="flex flex-wrap gap-1 mb-4">
              {confirmed.slice(0, 6).map((s) => (
                <span key={s.uri} className="text-[10px] bg-blue-50 text-blue-700 px-2 py-0.5 rounded-full font-medium">
                  {s.label}
                </span>
              ))}
              {confirmed.length > 6 && (
                <span className="text-[10px] bg-gray-100 text-gray-500 px-2 py-0.5 rounded-full">
                  +{confirmed.length - 6} más
                </span>
              )}
            </div>

            {/* QR placeholder */}
            <div className="flex items-center justify-center gap-3 border border-dashed border-gray-200 rounded-xl p-4">
              <div className="bg-gray-100 rounded-lg p-3">
                <QrCode className="w-10 h-10 text-gray-400" />
              </div>
              <div className="text-left">
                <p className="text-xs font-medium text-gray-700">Código QR incluido en el PDF</p>
                <p className="text-xs text-gray-400 mt-0.5 break-all">{qrUrl}</p>
              </div>
            </div>

            <p className="text-[10px] text-gray-400 text-center mt-3">
              Válido por 30 días · Token: {token}
            </p>
          </div>

          {/* Acciones */}
          <div className="space-y-2">
            <button
              onClick={handleDescargarPDF}
              className="w-full inline-flex items-center justify-center gap-2 bg-blue-600 text-white text-sm font-semibold px-4 py-3 rounded-xl hover:bg-blue-700 transition-colors"
            >
              <Download className="w-4 h-4" />
              Descargar PDF
            </button>

            <button
              onClick={handleCopiarLink}
              className="w-full inline-flex items-center justify-center gap-2 bg-white text-gray-700 text-sm font-medium px-4 py-3 rounded-xl border border-gray-200 hover:bg-gray-50 transition-colors"
            >
              {copiado ? (
                <>
                  <CheckCircle className="w-4 h-4 text-green-500" />
                  <span className="text-green-600">¡Link copiado!</span>
                </>
              ) : (
                <>
                  <Copy className="w-4 h-4" />
                  Copiar link QR
                </>
              )}
            </button>

            <button
              onClick={() => router.push('/mi-futuro-laboral/resultados')}
              className="w-full inline-flex items-center justify-center gap-2 text-gray-500 text-sm px-4 py-2.5 hover:text-gray-700 transition-colors"
            >
              <ArrowLeft className="w-4 h-4" />
              Volver a resultados
            </button>
          </div>

          {/* Info guardado */}
          <div className="mt-6 bg-blue-50 rounded-xl p-4 text-center">
            <Share2 className="w-5 h-5 text-blue-500 mx-auto mb-2" />
            <p className="text-xs text-blue-700 font-medium">¿Trabajás con una Oficina de Empleo?</p>
            <p className="text-xs text-blue-600 mt-1">
              Tu técnico puede ver este reporte directamente desde el sistema.
              Compartile el link QR o el código <strong>{token}</strong>.
            </p>
          </div>

          <button
            onClick={() => setToken(null)}
            className="mt-4 w-full flex items-center justify-center gap-1 text-xs text-gray-400 hover:text-gray-600 transition-colors"
          >
            <RotateCcw className="w-3 h-3" />
            Generar otro reporte
          </button>
        </div>
      </div>
    )
  }

  // ── Vista: configurar reporte ────────────────────────────────────────────
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-md mx-auto px-4 py-8">

        {/* Back */}
        <button
          onClick={() => router.back()}
          className="flex items-center gap-1.5 text-sm text-gray-500 hover:text-gray-700 mb-6 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" /> Volver
        </button>

        {/* Header */}
        <div className="mb-6">
          <h1 className="text-xl font-bold text-gray-900 mb-1">Generar reporte PDF + QR</h1>
          <p className="text-gray-500 text-sm">
            Tu reporte incluye un código QR que podés mostrarle a cualquier empleador.
          </p>
        </div>

        {/* Resumen perfil */}
        <div className="bg-white rounded-xl border border-gray-200 p-4 mb-5 flex items-center gap-3">
          <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center shrink-0">
            <User className="w-5 h-5 text-blue-600" />
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-semibold text-gray-900">{nombre}</p>
            <p className="text-xs text-gray-500 truncate">
              {confirmed.length} competencia{confirmed.length !== 1 ? 's' : ''} confirmada{confirmed.length !== 1 ? 's' : ''}
            </p>
          </div>
          <div className="text-right shrink-0">
            <p className="text-lg font-bold text-blue-600">73%</p>
            <p className="text-[10px] text-gray-400">match base</p>
          </div>
        </div>

        {/* Tipo de reporte */}
        <p className="text-xs font-semibold text-gray-600 uppercase tracking-wider mb-3">
          Tipo de reporte
        </p>
        <div className="space-y-2 mb-6">
          <TipoCard
            active={tipo === 'generico'}
            onClick={() => { setTipo('generico'); setVacanteSeleccionada(null) }}
            icon={TrendingUp}
            title="Reporte genérico"
            desc="Muestra tus competencias y tu perfil profesional. Sirve para cualquier oferta."
          />
          <TipoCard
            active={tipo === 'vacante'}
            onClick={() => setTipo('vacante')}
            icon={Briefcase}
            title="Vinculado a una vacante"
            desc="Muestra exactamente qué % de la vacante cubrís y qué te falta."
          />
        </div>

        {/* Selector de vacante */}
        {tipo === 'vacante' && (
          <div className="mb-6">
            <p className="text-xs font-medium text-gray-600 mb-2">Elegí la vacante:</p>
            <div className="space-y-2">
              {MOCK_VACANTES.map((v) => (
                <button
                  key={v.id}
                  onClick={() => setVacanteSeleccionada(v)}
                  className={`w-full flex items-center justify-between gap-3 rounded-xl border px-4 py-3 text-left transition-all ${
                    vacanteSeleccionada?.id === v.id
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 bg-white hover:border-gray-300'
                  }`}
                >
                  <div>
                    <p className="text-sm font-medium text-gray-800">{v.titulo}</p>
                    <p className="text-xs text-gray-400">{v.empresa}</p>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    <span className={`text-xs font-bold ${v.match >= 80 ? 'text-green-600' : 'text-blue-600'}`}>
                      {v.match}%
                    </span>
                    {vacanteSeleccionada?.id === v.id && (
                      <CheckCircle className="w-4 h-4 text-blue-500" />
                    )}
                  </div>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Qué incluye */}
        <div className="bg-gray-50 rounded-xl border border-gray-200 p-4 mb-6">
          <p className="text-xs font-semibold text-gray-700 mb-2 flex items-center gap-1.5">
            <BookOpen className="w-3.5 h-3.5 text-gray-500" />
            El reporte incluye:
          </p>
          <ul className="space-y-1.5">
            {[
              'Tu nombre y perfil profesional',
              `${confirmed.length} competencias con clasificación ESCO`,
              tipo === 'vacante' && vacanteSeleccionada
                ? `Match con "${vacanteSeleccionada.titulo}" (${vacanteSeleccionada.match}%)`
                : 'Match % con el mercado laboral',
              'Código QR único y verificable',
              'Cursos recomendados para cerrar brechas',
            ].filter(Boolean).map((item, i) => (
              <li key={i} className="flex items-start gap-2 text-xs text-gray-600">
                <CheckCircle className="w-3.5 h-3.5 text-green-500 shrink-0 mt-0.5" />
                {item as string}
              </li>
            ))}
          </ul>
        </div>

        {/* CTA */}
        <button
          onClick={handleGenerar}
          disabled={generando || (tipo === 'vacante' && !vacanteSeleccionada)}
          className="w-full inline-flex items-center justify-center gap-2 bg-blue-600 text-white text-sm font-semibold px-4 py-3.5 rounded-xl hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {generando ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              Generando reporte...
            </>
          ) : (
            <>
              <QrCode className="w-4 h-4" />
              Generar PDF + QR
            </>
          )}
        </button>

        {tipo === 'vacante' && !vacanteSeleccionada && (
          <p className="text-center text-xs text-gray-400 mt-2">
            Seleccioná una vacante para continuar.
          </p>
        )}

        <p className="text-center text-xs text-gray-400 mt-4">
          Gratuito · Sin registro · Válido 30 días
        </p>
      </div>
    </div>
  )
}
