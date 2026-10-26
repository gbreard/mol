/**
 * Recomendaciones IA en secciones (trayectoria-laboral y analisis-ocupacional).
 * El modelo devuelve JSON con textos; las cifras (chips) las arma la UI con sus datos
 * y la institución/modalidad de cada curso salen de la lista filtrada, no del modelo.
 */

export interface OpcionIA {
  ocupacion: string
  motivo: string
}

export interface FormacionIA {
  curso: string
  motivo: string
}

/** trayectoria-laboral (persona) */
export interface RecomendacionTrayectoria {
  ocupacion: string
  por_que: string
  alternativas: OpcionIA[]
  pasos: string[]
  formacion: FormacionIA[]
}

/** analisis-ocupacional (VIP, sin persona) */
export interface AnalisisOcupacional {
  resumen: string
  destinos: OpcionIA[]
  recomendaciones: string[]
  formacion: FormacionIA[]
}

export const normalizarTexto = (s: string) =>
  s.toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/["“”«»]/g, '').replace(/\s+/g, ' ').trim()

const texto = (v: unknown): string => (typeof v === 'string' ? v.trim() : '')

function opciones(v: unknown, max: number, campo: 'ocupacion' | 'curso'): { nombre: string; motivo: string }[] {
  if (!Array.isArray(v)) return []
  return v
    .map(x => ({ nombre: texto((x as any)?.[campo]), motivo: texto((x as any)?.motivo) }))
    .filter(x => x.nombre && x.motivo)
    .slice(0, max)
}

function parseJson(raw: string): any | null {
  try {
    return JSON.parse(raw.replace(/```json|```/g, '').trim())
  } catch {
    return null
  }
}

/**
 * Busca un curso por nombre en la lista filtrada. Exacto (normalizado) o, si el modelo
 * agregó algo, por inclusión. null si el curso no está en la lista (inventado).
 */
export function buscarCurso<T extends { titulo: string }>(nombre: string, cursos: T[]): T | null {
  const n = normalizarTexto(nombre)
  return cursos.find(c => normalizarTexto(c.titulo) === n)
    ?? cursos.find(c => n.includes(normalizarTexto(c.titulo)) || normalizarTexto(c.titulo).includes(n))
    ?? null
}

/** Formación: solo cursos de la lista permitida, con el título tal como figura en la lista. */
function formacionPermitida(v: unknown, cursosPermitidos: { titulo: string }[]): FormacionIA[] {
  return opciones(v, 2, 'curso')
    .map(f => ({ curso: buscarCurso(f.nombre, cursosPermitidos)?.titulo || '', motivo: f.motivo }))
    .filter(f => f.curso)
}

/** null si el JSON no parsea o no trae lo mínimo (ocupación + por qué). */
export function parseTrayectoria(raw: string, cursosPermitidos: { titulo: string }[]): RecomendacionTrayectoria | null {
  const d = parseJson(raw)
  if (!d || typeof d !== 'object') return null
  const ocupacion = texto(d.ocupacion)
  const por_que = texto(d.por_que)
  if (!ocupacion || !por_que) return null
  return {
    ocupacion,
    por_que,
    alternativas: opciones(d.alternativas, 3, 'ocupacion').map(o => ({ ocupacion: o.nombre, motivo: o.motivo })),
    pasos: (Array.isArray(d.pasos) ? d.pasos : []).map(texto).filter(Boolean).slice(0, 3),
    formacion: formacionPermitida(d.formacion, cursosPermitidos),
  }
}

/** null si el JSON no parsea o no trae el resumen. */
export function parseAnalisis(raw: string, cursosPermitidos: { titulo: string }[]): AnalisisOcupacional | null {
  const d = parseJson(raw)
  if (!d || typeof d !== 'object') return null
  const resumen = texto(d.resumen)
  if (!resumen) return null
  return {
    resumen,
    destinos: opciones(d.destinos, 3, 'ocupacion').map(o => ({ ocupacion: o.nombre, motivo: o.motivo })),
    recomendaciones: (Array.isArray(d.recomendaciones) ? d.recomendaciones : []).map(texto).filter(Boolean).slice(0, 3),
    formacion: formacionPermitida(d.formacion, cursosPermitidos),
  }
}

/**
 * Indicador único de demanda (el que muestra la UI y el que recibe el modelo), a partir
 * del trend_label de isco_demand_trend. No se combina con la volatilidad.
 */
export function demandaLabel(trendLabel: string | null | undefined): string {
  switch (trendLabel) {
    case 'creciendo': return 'Demanda en alza'
    case 'estable': return 'Demanda estable'
    case 'cayendo': return 'Demanda en baja'
    default: return 'Sin datos de tendencia'
  }
}
