'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import {
  ArrowLeft, User, Briefcase, BookOpen, ClipboardList,
  TrendingUp, Plus, ChevronRight, CheckCircle, Clock,
  Building2, MapPin, AlertTriangle, Edit3, Send,
} from 'lucide-react'

// ─── Mock data ────────────────────────────────────────────────────────────────
const MOCK_CASO = {
  id: 'c001',
  nombre: 'María González',
  dni: '28.450.123',
  telefono: '+54 11 4523-9876',
  email: 'mgonzalez@email.com',
  provincia: 'CABA',
  barrio: 'Flores',
  edad: 34,
  estado: 'en_diagnostico',
  ocupacion: 'Administrativa',
  match_score: 72,
  ultima_actividad: '2026-03-22',
  tecnico: 'Andrea P.',
  skills_confirmadas: [
    { uri: 's1', label: 'Microsoft Office', confidence: 'confirmed' },
    { uri: 's2', label: 'Atención al cliente', confidence: 'confirmed' },
    { uri: 's3', label: 'Gestión documental', confidence: 'confirmed' },
    { uri: 's4', label: 'Facturación', confidence: 'inferred' },
  ],
}

const MOCK_OCUPACIONES = [
  { uri: 'esco_4120', label: 'Secretaria administrativa', isco: '4120', match: 87, gap: 2, ofertas: 89 },
  { uri: 'esco_4110', label: 'Empleada de oficina en general', isco: '4110', match: 72, gap: 3, ofertas: 134 },
  { uri: 'esco_4322', label: 'Asistente de recursos humanos', isco: '4322', match: 64, gap: 4, ofertas: 47 },
]

const MOCK_VACANTES = [
  {
    id: 1, titulo: 'Recepcionista administrativa', empresa: 'Clinica Santa Rosa',
    provincia: 'CABA', modalidad: 'Presencial', match: 84,
    skills_ok: ['Microsoft Office', 'Atención al cliente'], skills_gap: ['SAP'],
    publicada: 'hace 2 días',
  },
  {
    id: 2, titulo: 'Asistente contable Jr.', empresa: 'Estudio Jiménez',
    provincia: 'CABA', modalidad: 'Híbrido', match: 71,
    skills_ok: ['Excel', 'Facturación'], skills_gap: ['Tango Gestión', 'Liquidación sueldos'],
    publicada: 'hace 5 días',
  },
]

const MOCK_CURSOS = [
  { skill: 'SAP', nombre: 'SAP MM para usuarios', institucion: 'Teclab', duracion: '6 semanas', modalidad: 'Online', gratuito: false, impacto: '+8%' },
  { skill: 'Tango', nombre: 'Gestión contable con Tango', institucion: 'CGPC CABA', duracion: '4 semanas', modalidad: 'Presencial', gratuito: true, impacto: '+6%' },
]

const MOCK_NOTAS = [
  { id: 'n1', fecha: '2026-03-22', tecnico: 'Andrea P.', texto: 'Primera entrevista de diagnóstico. La persona tiene 8 años de experiencia administrativa pero nunca usó software especializado. Buena predisposición para formación.' },
  { id: 'n2', fecha: '2026-03-20', tecnico: 'Andrea P.', texto: 'Derivada al curso de SAP del CGPC Flores. Interesada también en vacante de clínica.' },
]

const ESTADO_CONFIG: Record<string, { label: string; color: string; next?: string[] }> = {
  nuevo: { label: 'Nuevo', color: 'bg-gray-100 text-gray-600', next: ['en_diagnostico'] },
  en_diagnostico: { label: 'En diagnóstico', color: 'bg-blue-100 text-blue-700', next: ['perfil_completo'] },
  perfil_completo: { label: 'Perfil completo', color: 'bg-purple-100 text-purple-700', next: ['derivado_vacante', 'derivado_curso', 'en_seguimiento'] },
  derivado_vacante: { label: 'Derivado vacante', color: 'bg-green-100 text-green-700', next: ['en_seguimiento', 'insertado'] },
  derivado_curso: { label: 'Derivado curso', color: 'bg-orange-100 text-orange-700', next: ['en_seguimiento'] },
  en_seguimiento: { label: 'En seguimiento', color: 'bg-yellow-100 text-yellow-700', next: ['insertado', 'cerrado'] },
  insertado: { label: 'Insertado', color: 'bg-emerald-100 text-emerald-700', next: ['cerrado'] },
  cerrado: { label: 'Cerrado', color: 'bg-gray-100 text-gray-500', next: [] },
}

const TABS = [
  { id: 'perfil', label: 'Perfil', icon: User },
  { id: 'ocupaciones', label: 'Ocupaciones', icon: TrendingUp },
  { id: 'vacantes', label: 'Vacantes', icon: Briefcase },
  { id: 'notas', label: 'Notas', icon: ClipboardList },
]

function MatchBar({ pct }: { pct: number }) {
  const color = pct >= 80 ? 'bg-green-500' : pct >= 60 ? 'bg-blue-500' : 'bg-yellow-400'
  const text = pct >= 80 ? 'text-green-600' : pct >= 60 ? 'text-blue-600' : 'text-yellow-600'
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 bg-gray-100 rounded-full overflow-hidden">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className={`text-xs font-bold tabular-nums ${text}`}>{pct}%</span>
    </div>
  )
}

export default function DetalleCasoPage() {
  const router = useRouter()
  const [tab, setTab] = useState('perfil')
  const [nota, setNota] = useState('')
  const [estado, setEstado] = useState(MOCK_CASO.estado)

  const est = ESTADO_CONFIG[estado]

  const handleCambiarEstado = (nuevoEstado: string) => {
    setEstado(nuevoEstado)
    // En producción: PATCH /api/casos/{id} con { estado: nuevoEstado }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-5xl mx-auto px-4 py-6">

        {/* Back + header */}
        <button
          onClick={() => router.back()}
          className="flex items-center gap-1.5 text-sm text-gray-500 hover:text-gray-700 mb-4 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" /> Cartera de casos
        </button>

        {/* Cabecera del caso */}
        <div className="bg-white rounded-xl border border-gray-200 p-4 mb-4">
          <div className="flex items-start justify-between gap-3">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-full bg-teal-100 text-teal-700 text-sm font-bold flex items-center justify-center shrink-0">
                {MOCK_CASO.nombre.split(' ').map((n) => n[0]).join('').slice(0, 2)}
              </div>
              <div>
                <h1 className="text-lg font-bold text-gray-900">{MOCK_CASO.nombre}</h1>
                <div className="flex flex-wrap items-center gap-2 mt-0.5">
                  <span className="text-xs text-gray-400">DNI {MOCK_CASO.dni}</span>
                  <span className="text-gray-200">·</span>
                  <span className="text-xs text-gray-400">{MOCK_CASO.edad} años</span>
                  <span className="text-gray-200">·</span>
                  <span className="text-xs text-gray-400">{MOCK_CASO.barrio}, {MOCK_CASO.provincia}</span>
                </div>
              </div>
            </div>
            <div className="flex items-center gap-2 shrink-0">
              <span className={`text-xs px-2.5 py-1 rounded-full font-medium ${est.color}`}>
                {est.label}
              </span>
              <span className="text-sm font-bold text-blue-600">{MOCK_CASO.match_score}%</span>
            </div>
          </div>

          {/* Transición de estado */}
          {(est.next ?? []).length > 0 && (
            <div className="mt-3 pt-3 border-t border-gray-100 flex flex-wrap gap-2">
              <span className="text-xs text-gray-500 self-center">Pasar a:</span>
              {(est.next ?? []).map((s) => (
                <button
                  key={s}
                  onClick={() => handleCambiarEstado(s)}
                  className="text-xs border border-gray-200 text-gray-600 px-3 py-1 rounded-full hover:border-teal-400 hover:text-teal-700 transition-colors"
                >
                  {ESTADO_CONFIG[s]?.label}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Tabs */}
        <div className="flex gap-1 bg-white border border-gray-200 rounded-xl p-1 mb-4">
          {TABS.map((t) => (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className={`flex-1 flex items-center justify-center gap-1.5 py-2 rounded-lg text-xs font-medium transition-all ${
                tab === t.id
                  ? 'bg-teal-600 text-white shadow-sm'
                  : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'
              }`}
            >
              <t.icon className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">{t.label}</span>
            </button>
          ))}
        </div>

        {/* Tab: Perfil */}
        {tab === 'perfil' && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {/* Datos personales */}
            <div className="bg-white rounded-xl border border-gray-200 p-4">
              <h3 className="text-sm font-semibold text-gray-700 mb-3">Datos de contacto</h3>
              <div className="space-y-2">
                <div className="flex items-center gap-2 text-sm text-gray-600">
                  <User className="w-4 h-4 text-gray-400" />
                  {MOCK_CASO.telefono}
                </div>
                <div className="flex items-center gap-2 text-sm text-gray-600">
                  <Send className="w-4 h-4 text-gray-400" />
                  {MOCK_CASO.email}
                </div>
                <div className="flex items-center gap-2 text-sm text-gray-600">
                  <MapPin className="w-4 h-4 text-gray-400" />
                  {MOCK_CASO.barrio}, {MOCK_CASO.provincia}
                </div>
              </div>
              <button className="mt-3 text-xs text-teal-600 hover:underline flex items-center gap-1">
                <Edit3 className="w-3 h-3" /> Editar datos
              </button>
            </div>

            {/* Skills */}
            <div className="bg-white rounded-xl border border-gray-200 p-4">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm font-semibold text-gray-700">Competencias</h3>
                <button className="text-xs text-teal-600 hover:underline flex items-center gap-1">
                  <Plus className="w-3 h-3" /> Agregar
                </button>
              </div>
              <div className="space-y-2">
                {MOCK_CASO.skills_confirmadas.map((s) => (
                  <div key={s.uri} className="flex items-center gap-2">
                    <CheckCircle className={`w-3.5 h-3.5 shrink-0 ${s.confidence === 'confirmed' ? 'text-green-500' : 'text-yellow-400'}`} />
                    <span className="text-sm text-gray-700">{s.label}</span>
                    {s.confidence === 'inferred' && (
                      <span className="text-[10px] text-yellow-600 bg-yellow-50 px-1.5 py-0.5 rounded">inferida</span>
                    )}
                  </div>
                ))}
              </div>
              <button
                onClick={() => router.push(`/mi-futuro-laboral/perfil`)}
                className="mt-3 w-full text-xs text-teal-600 bg-teal-50 hover:bg-teal-100 rounded-lg py-2 transition-colors font-medium"
              >
                Completar perfil con la persona →
              </button>
            </div>
          </div>
        )}

        {/* Tab: Ocupaciones */}
        {tab === 'ocupaciones' && (
          <div className="space-y-3">
            {MOCK_OCUPACIONES.map((o) => (
              <div key={o.uri} className="bg-white rounded-xl border border-gray-200 p-4">
                <div className="flex items-start justify-between gap-3 mb-3">
                  <div>
                    <h3 className="font-semibold text-gray-900 text-sm">{o.label}</h3>
                    <div className="flex items-center gap-2 mt-0.5">
                      <span className="text-xs text-gray-400 font-mono">{o.isco}</span>
                      <span className="text-xs text-gray-400">·</span>
                      <span className="text-xs text-gray-500">{o.ofertas} ofertas activas</span>
                    </div>
                  </div>
                  <span className="text-xs text-gray-400 shrink-0">
                    falta{o.gap !== 1 ? 'n' : ''} {o.gap} skill{o.gap !== 1 ? 's' : ''}
                  </span>
                </div>
                <MatchBar pct={o.match} />
                <div className="mt-3 flex gap-2">
                  <button
                    onClick={() => router.push(`/mi-futuro-laboral/brecha?uri=${o.uri}&label=${encodeURIComponent(o.label)}`)}
                    className="flex-1 text-xs text-teal-600 font-medium bg-teal-50 hover:bg-teal-100 rounded-lg py-2 transition-colors"
                  >
                    Ver brecha →
                  </button>
                  <button
                    onClick={() => setTab('vacantes')}
                    className="flex-1 text-xs text-gray-600 font-medium bg-gray-50 hover:bg-gray-100 rounded-lg py-2 transition-colors"
                  >
                    Ver vacantes →
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Tab: Vacantes */}
        {tab === 'vacantes' && (
          <div className="space-y-3">
            {MOCK_VACANTES.map((v) => (
              <div key={v.id} className="bg-white rounded-xl border border-gray-200 p-4">
                <div className="flex items-start justify-between gap-3 mb-2">
                  <div>
                    <h3 className="font-semibold text-gray-900 text-sm">{v.titulo}</h3>
                    <div className="flex flex-wrap items-center gap-2 mt-1">
                      <span className="flex items-center gap-1 text-xs text-gray-500">
                        <Building2 className="w-3 h-3" />{v.empresa}
                      </span>
                      <span className="flex items-center gap-1 text-xs text-gray-500">
                        <MapPin className="w-3 h-3" />{v.provincia}
                      </span>
                      <span className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full">{v.modalidad}</span>
                      <span className="flex items-center gap-1 text-xs text-gray-400">
                        <Clock className="w-3 h-3" />{v.publicada}
                      </span>
                    </div>
                  </div>
                </div>
                <MatchBar pct={v.match} />
                <div className="mt-2 flex flex-wrap gap-1">
                  {v.skills_ok.map((s) => (
                    <span key={s} className="text-[10px] bg-green-50 text-green-700 px-2 py-0.5 rounded-full">✓ {s}</span>
                  ))}
                  {v.skills_gap.map((s) => (
                    <span key={s} className="text-[10px] bg-red-50 text-red-600 px-2 py-0.5 rounded-full">✗ {s}</span>
                  ))}
                </div>
                <div className="mt-3 flex gap-2">
                  <button
                    onClick={() => handleCambiarEstado('derivado_vacante')}
                    className="flex-1 text-xs text-teal-600 font-medium bg-teal-50 hover:bg-teal-100 rounded-lg py-2 transition-colors"
                  >
                    Derivar a esta vacante →
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Tab: Notas */}
        {tab === 'notas' && (
          <div className="space-y-4">
            {/* Nueva nota */}
            <div className="bg-white rounded-xl border border-gray-200 p-4">
              <p className="text-xs font-semibold text-gray-700 mb-2">Nueva nota técnica</p>
              <textarea
                value={nota}
                onChange={(e) => setNota(e.target.value)}
                placeholder="Ej: Realizamos entrevista de diagnóstico. La persona muestra interés en..."
                rows={3}
                className="w-full rounded-lg border border-gray-200 px-3 py-2.5 text-sm text-gray-900 placeholder-gray-400 focus:border-teal-400 focus:outline-none focus:ring-2 focus:ring-teal-100 resize-none"
              />
              <button
                disabled={!nota.trim()}
                className="mt-2 inline-flex items-center gap-2 bg-teal-600 text-white text-xs font-medium px-4 py-2 rounded-lg hover:bg-teal-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
              >
                <Plus className="w-3.5 h-3.5" />
                Guardar nota
              </button>
            </div>

            {/* Historial */}
            {MOCK_NOTAS.map((n) => (
              <div key={n.id} className="bg-white rounded-xl border border-gray-200 p-4">
                <div className="flex items-center gap-2 mb-2">
                  <div className="w-6 h-6 rounded-full bg-teal-100 text-teal-700 text-[10px] font-bold flex items-center justify-center">
                    {n.tecnico.split(' ').map((x) => x[0]).join('')}
                  </div>
                  <span className="text-xs font-medium text-gray-700">{n.tecnico}</span>
                  <span className="text-xs text-gray-400">· {n.fecha}</span>
                </div>
                <p className="text-sm text-gray-700 leading-relaxed">{n.texto}</p>
              </div>
            ))}
          </div>
        )}

        {/* Cursos recomendados (siempre visible abajo) */}
        {(tab === 'vacantes' || tab === 'ocupaciones') && MOCK_CURSOS.length > 0 && (
          <div className="mt-4 bg-white rounded-xl border border-gray-200 p-4">
            <div className="flex items-center gap-2 mb-3">
              <BookOpen className="w-4 h-4 text-orange-500" />
              <h3 className="text-sm font-semibold text-gray-700">Formación recomendada para cerrar brechas</h3>
            </div>
            <div className="space-y-2">
              {MOCK_CURSOS.map((c, i) => (
                <div key={i} className="flex items-start justify-between gap-3 bg-gray-50 rounded-lg p-3">
                  <div>
                    <p className="text-xs font-medium text-gray-800">{c.nombre}</p>
                    <p className="text-[10px] text-gray-400 mt-0.5">
                      {c.institucion} · {c.duracion} · {c.modalidad}
                      {c.gratuito && <span className="ml-1 text-green-600 font-medium">· Gratuito</span>}
                    </p>
                  </div>
                  <span className="text-xs font-bold text-green-600 bg-green-50 px-2 py-1 rounded-lg shrink-0">
                    {c.impacto}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
