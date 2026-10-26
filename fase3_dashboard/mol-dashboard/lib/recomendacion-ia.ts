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

/** trayectoria-laboral (persona): voz de orientador, en párrafos */
export interface RecomendacionTrayectoria {
  ocupacion: string
  diagnostico: string
  recomendacion: string
  alternativas: { ocupacion: string; comentario: string }[]
  pasos: { accion: string; por_que: string }[]
  cierre: string
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

// Controles deterministas sobre lo que devuelve el modelo (el prompt solo no alcanza)

const TU_A_VOS: [RegExp, string][] = [
  [/\bcubres\b/gi, 'cubrís'], [/\btienes\b/gi, 'tenés'], [/\bpuedes\b/gi, 'podés'], [/\bsabes\b/gi, 'sabés'],
  [/\bmanejas\b/gi, 'manejás'], [/\bnecesitas\b/gi, 'necesitás'], [/\brequieres\b/gi, 'requerís'],
  [/\bdebes\b/gi, 'debés'], [/\bquieres\b/gi, 'querés'], [/\bdominas\b/gi, 'dominás'], [/\bestás trabajando\b/gi, 'trabajás'],
]
const PROMESAS_DE_VELOCIDAD = /,?\s+(rápidamente|en poco tiempo|pronto|enseguida)\b/gi

/** Voseo y sin promesas de velocidad. Respeta la mayúscula inicial del reemplazo. */
export function pulirTexto(t: string): string {
  let out = t.replace(PROMESAS_DE_VELOCIDAD, '')
  for (const [re, vos] of TU_A_VOS) {
    out = out.replace(re, m => (m[0] === m[0].toUpperCase() ? vos.charAt(0).toUpperCase() + vos.slice(1) : vos))
  }
  return out.replace(/\s+([.,;])/g, '$1').trim()
}

const PASO_GENERICO = /\b(CV|curr[ií]culum|bolsa de empleo|entrevista de orientaci[oó]n|entrevistas laborales)\b/i

/** Como máximo un paso genérico de la Oficina; los específicos de la persona van primero. */
export function limitarPasosGenericos<T extends { accion: string }>(pasos: T[]): T[] {
  const especificos = pasos.filter(p => !PASO_GENERICO.test(p.accion))
  const genericos = pasos.filter(p => PASO_GENERICO.test(p.accion))
  return [...especificos, ...genericos.slice(0, 1)]
}

/** null si el JSON no parsea o no trae lo mínimo (ocupación, diagnóstico y recomendación). */
export function parseTrayectoria(raw: string): RecomendacionTrayectoria | null {
  const d = parseJson(raw)
  if (!d || typeof d !== 'object') return null
  const ocupacion = texto(d.ocupacion)
  const diagnostico = texto(d.diagnostico)
  const recomendacion = texto(d.recomendacion)
  if (!ocupacion || !diagnostico || !recomendacion) return null
  const pasos: { accion: string; por_que: string }[] = (Array.isArray(d.pasos) ? d.pasos : [])
    .map((p: any) => (typeof p === 'string' ? { accion: texto(p), por_que: '' } : { accion: texto(p?.accion), por_que: texto(p?.por_que) }))
    .filter((p: { accion: string }) => p.accion)
  return {
    ocupacion,
    diagnostico: pulirTexto(diagnostico),
    recomendacion: pulirTexto(recomendacion),
    alternativas: (Array.isArray(d.alternativas) ? d.alternativas : [])
      .map((a: any) => ({ ocupacion: texto(a?.ocupacion), comentario: pulirTexto(texto(a?.comentario)) }))
      .filter((a: { ocupacion: string; comentario: string }) => a.ocupacion && a.comentario)
      .slice(0, 2),
    pasos: limitarPasosGenericos(pasos)
      .slice(0, 3)
      .map(p => ({ accion: pulirTexto(p.accion), por_que: pulirTexto(p.por_que) })),
    cierre: pulirTexto(texto(d.cierre)),
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

/** "soldador/soldadora" → "Soldador": la forma antes de "/", con mayúscula inicial. */
export function etiquetaOcupacion(label: string): string {
  const corta = (label || '').split('/')[0].trim()
  return corta.charAt(0).toUpperCase() + corta.slice(1)
}
