/**
 * Cursos REGICE asociados a la localidad de una persona (M3 y trayectoria-laboral).
 * Regla: presenciales solo de la provincia de la persona; a distancia de cualquiera.
 */

export interface CursoPersona {
  grupo: 'presencial' | 'virtual'
  curso_id: number
  titulo: string
  institucion: string
  provincia: string
  municipio: string | null
  modalidad: string
  carga_horaria: number | null
  skills_cubiertas: number
  total_gap_skills: number
  skills_detalle: { uri: string; label: string }[]
}

export interface CursosPersonaResult {
  cursos: CursoPersona[]
  /** La persona no tiene provincia reconocible: solo se buscaron virtuales */
  sinProvincia: boolean
}

export async function fetchCursosParaPersona(gapSkillUris: string[], provinciaRegice: string | null): Promise<CursosPersonaResult> {
  const res = await fetch('/api/perfiles/cursos-persona', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ gap_skill_uris: gapSkillUris, provincia: provinciaRegice }),
  })
  if (!res.ok) throw new Error(`cursos-persona → HTTP ${res.status}`)
  const data = await res.json()
  return { cursos: data.cursos || [], sinProvincia: !!data.sin_provincia }
}

/** 'Cordoba' / 'Capital federal' (formato REGICE) → 'Córdoba' / 'CABA'. */
const PROVINCIAS = [
  'Buenos Aires', 'Catamarca', 'Chaco', 'Chubut', 'Córdoba', 'Corrientes', 'Entre Ríos', 'Formosa',
  'Jujuy', 'La Pampa', 'La Rioja', 'Mendoza', 'Misiones', 'Neuquén', 'Río Negro', 'Salta', 'San Juan',
  'San Luis', 'Santa Cruz', 'Santa Fe', 'Santiago del Estero', 'Tierra del Fuego', 'Tucumán',
]
const sinTildes = (s: string) => s.toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '').trim()

export function provinciaDisplay(regice: string | null | undefined): string {
  if (!regice) return ''
  if (sinTildes(regice) === 'capital federal') return 'CABA'
  return PROVINCIAS.find(p => sinTildes(p) === sinTildes(regice)) || regice
}

export function esVirtual(c: Pick<CursoPersona, 'modalidad'>): boolean {
  return (c.modalidad || '').toUpperCase() !== 'PRESENCIAL'
}

/**
 * Línea de ubicación del curso:
 * presencial → "institución · localidad, provincia · Presencial"
 * virtual    → "institución · Virtual · se puede cursar desde <provincia de la persona>"
 */
export function lineaUbicacionCurso(c: Pick<CursoPersona, 'institucion' | 'municipio' | 'provincia' | 'modalidad'>, provinciaPersona: string | null): string {
  if (esVirtual(c)) {
    return `${c.institucion} · Virtual · se puede cursar desde ${provinciaPersona || 'cualquier provincia'}`
  }
  const lugar = [c.municipio, provinciaDisplay(c.provincia)].filter(Boolean).join(', ')
  return `${c.institucion} · ${lugar} · Presencial`
}

const MINUSCULAS = new Set(['de', 'del', 'la', 'las', 'el', 'los', 'y', 'e', 'en', 'a', 'al', 'para', 'por', 'con', 'o', 'u'])

/**
 * Formato título para textos de REGICE que vienen en mayúsculas o minúsculas:
 * "ESCUELA MUNICIPAL DE OFIC" → "Escuela Municipal de Ofic", "albanileria" → "Albanileria".
 * Solo cambia mayúsculas: no completa truncados ni agrega tildes. Siglas cortas (SRL, SA) quedan.
 */
export function formatoTitulo(texto: string | null | undefined): string {
  if (!texto) return ''
  return texto
    .split(/(\s+)/)
    .map((p, i) => {
      if (/^\s+$/.test(p)) return p
      const limpio = p.replace(/[.,]/g, '')
      if (/^(S\.?R\.?L|S\.?A|SA|SRL|SAS|UTN|INTA|INET|UOCRA|CGT)\.?$/i.test(limpio)) return p.toUpperCase()
      const minus = p.toLowerCase()
      if (i > 0 && MINUSCULAS.has(minus)) return minus
      return minus.charAt(0).toUpperCase() + minus.slice(1)
    })
    .join('')
}

/** Normaliza para mostrar (y para el prompt) los campos de texto de un curso. */
export function formatearCurso<T extends { titulo?: string; institucion?: string; municipio?: string | null }>(c: T): T {
  return {
    ...c,
    titulo: formatoTitulo(c.titulo),
    institucion: formatoTitulo(c.institucion),
    municipio: c.municipio ? formatoTitulo(c.municipio) : c.municipio,
  }
}
