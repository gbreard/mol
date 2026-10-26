'use client'

import { Sparkles, Info } from 'lucide-react'
import { buscarCurso, normalizarTexto, type FormacionIA, type OpcionIA } from '@/lib/recomendacion-ia'
import { esVirtual, provinciaDisplay } from '@/lib/cursos'
import { formatFecha } from '@/lib/ofertas-estado'

/** Datos que pone la UI (no el modelo): chips y cursos de la lista filtrada. */
export interface OcupacionContexto {
  label: string
  /** null cuando no hay persona (VIP): el chip muestra solo el total de esenciales */
  cubiertas: number | null
  esenciales_total: number
  avisos: number
  demanda: string
  cursos: { titulo: string; institucion?: string; modalidad?: string; provincia?: string; municipio?: string | null }[]
}

export interface SeccionesIA {
  ocupacion: string
  textoPrincipal: string
  tituloPrincipal: string
  opciones: OpcionIA[]
  tituloOpciones: string
  pasos: string[]
  tituloPasos: string
  formacion: FormacionIA[]
}

interface Props {
  titulo: string
  secciones: SeccionesIA
  contexto: OcupacionContexto[]
  fechaMax: string | null
  /** Clases de color (texto/borde/fondo) del módulo: púrpura en M3, azul en VIP */
  tema?: 'purple' | 'blue'
}

function buscarOcupacion(nombre: string, contexto: OcupacionContexto[]) {
  const n = normalizarTexto(nombre)
  return contexto.find(o => normalizarTexto(o.label) === n)
    ?? contexto.find(o => normalizarTexto(o.label).includes(n) || n.includes(normalizarTexto(o.label)))
    ?? null
}

function lineaCurso(c: OcupacionContexto['cursos'][number]): string {
  const modalidad = esVirtual({ modalidad: c.modalidad || '' })
    ? 'Virtual'
    : `Presencial${c.provincia ? ` (${[c.municipio, provinciaDisplay(c.provincia)].filter(Boolean).join(', ')})` : ''}`
  return [c.titulo, c.institucion, modalidad].filter(Boolean).join(' · ')
}

export function RecomendacionCard({ titulo, secciones, contexto, fechaMax, tema = 'purple' }: Props) {
  const color = tema === 'purple'
    ? { titulo: 'text-purple-700', icono: 'text-purple-600', chip: 'bg-purple-100 text-purple-700', seccion: 'text-purple-600' }
    : { titulo: 'text-blue-700', icono: 'text-blue-600', chip: 'bg-blue-100 text-blue-700', seccion: 'text-blue-600' }
  const occ = buscarOcupacion(secciones.ocupacion, contexto)
  const todosLosCursos = contexto.flatMap(o => o.cursos)
  const formacion = secciones.formacion
    .map(f => ({ ...f, datos: buscarCurso(f.curso, todosLosCursos) }))
    .filter(f => f.datos)

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <Sparkles className={`w-4 h-4 ${color.icono}`} />
        <h3 className={`text-sm font-semibold ${color.titulo}`}>{titulo}</h3>
      </div>

      <div>
        <p className="text-base font-semibold text-gray-900">{occ?.label || secciones.ocupacion}</p>
        {occ && (
          <div className="flex flex-wrap gap-1.5 mt-1.5">
            <span className={`text-[11px] px-2 py-0.5 rounded-full font-medium ${color.chip}`}>
              {occ.cubiertas === null ? `${occ.esenciales_total} esenciales` : `${occ.cubiertas}/${occ.esenciales_total} esenciales`}
            </span>
            <span className={`text-[11px] px-2 py-0.5 rounded-full font-medium ${color.chip}`}>
              {occ.avisos.toLocaleString('es-AR')} avisos
            </span>
            <span className={`text-[11px] px-2 py-0.5 rounded-full font-medium ${color.chip}`}>{occ.demanda}</span>
          </div>
        )}
      </div>

      <Seccion titulo={secciones.tituloPrincipal} color={color.seccion}>
        <p className="text-sm text-gray-700 leading-relaxed">{secciones.textoPrincipal}</p>
      </Seccion>

      {secciones.opciones.length > 0 && (
        <Seccion titulo={secciones.tituloOpciones} color={color.seccion}>
          <ul className="space-y-1">
            {secciones.opciones.map((o, i) => (
              <li key={i} className="text-sm text-gray-700">
                • <span className="font-medium">{buscarOcupacion(o.ocupacion, contexto)?.label || o.ocupacion}</span>: {o.motivo}
              </li>
            ))}
          </ul>
        </Seccion>
      )}

      {secciones.pasos.length > 0 && (
        <Seccion titulo={secciones.tituloPasos} color={color.seccion}>
          <ol className="space-y-1">
            {secciones.pasos.map((p, i) => (
              <li key={i} className="text-sm text-gray-700">{i + 1}. {p}</li>
            ))}
          </ol>
        </Seccion>
      )}

      {formacion.length > 0 && (
        <Seccion titulo="Formación sugerida" color={color.seccion}>
          <ul className="space-y-1.5">
            {formacion.map((f, i) => (
              <li key={i} className="text-sm text-gray-700">
                • <span className="font-medium">{lineaCurso(f.datos!)}</span>
                <span className="block text-xs text-gray-500 ml-3">{f.motivo}</span>
              </li>
            ))}
          </ul>
        </Seccion>
      )}

      <p className="flex items-start gap-1.5 text-[10px] text-gray-400 leading-snug pt-1">
        <Info className="w-3 h-3 shrink-0 mt-px" />
        Generado con IA a partir de avisos publicados{fechaMax ? ` hasta el ${formatFecha(fechaMax)}` : ''}. Orientativo.
      </p>
    </div>
  )
}

function Seccion({ titulo, color, children }: { titulo: string; color: string; children: React.ReactNode }) {
  return (
    <div>
      <p className={`text-[11px] font-semibold uppercase tracking-wide mb-1 ${color}`}>{titulo}</p>
      {children}
    </div>
  )
}
