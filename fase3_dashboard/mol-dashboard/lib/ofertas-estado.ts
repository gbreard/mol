/**
 * Estado y antigüedad de avisos para la Oficina de Empleo.
 *
 * El estado vigente es `estado_ciclo` (5 valores). La columna vieja `estado`
 * quedó casi toda en 'baja' y no debe usarse para badges.
 */

const ESTADO_RANK: Record<string, number> = { activa: 0, presunta_baja: 1 }

export interface EstadoBadge {
  label: string
  className: string
}

export function estadoOfertaBadge(estadoCiclo: string | null | undefined): EstadoBadge {
  if (estadoCiclo === 'activa') return { label: 'Activa', className: 'bg-green-50 text-green-600' }
  if (estadoCiclo === 'presunta_baja') return { label: 'Sin confirmar', className: 'bg-amber-50 text-amber-600' }
  return { label: 'Cerrada', className: 'bg-gray-100 text-gray-400' }
}

/** Orden por fecha DESC; dentro de la misma fecha, activa → presunta_baja → resto. Estable. */
export function sortOfertasRecientes<T extends { fecha_publicacion: string | null; estado_ciclo?: string | null }>(ofertas: T[]): T[] {
  return ofertas
    .map((o, i) => ({ o, i }))
    .sort((a, b) => {
      const fa = a.o.fecha_publicacion || ''
      const fb = b.o.fecha_publicacion || ''
      if (fa !== fb) return fa < fb ? 1 : -1
      const ra = ESTADO_RANK[a.o.estado_ciclo ?? ''] ?? 2
      const rb = ESTADO_RANK[b.o.estado_ciclo ?? ''] ?? 2
      return ra !== rb ? ra - rb : a.i - b.i
    })
    .map(x => x.o)
}

/** 'YYYY-MM-DD' → 'DD/MM/YYYY' sin pasar por zonas horarias. */
export function formatFecha(fecha: string | null | undefined): string {
  if (!fecha) return ''
  const [y, m, d] = fecha.slice(0, 10).split('-')
  return y && m && d ? `${d}/${m}/${y}` : fecha
}

/** "Publicado hace 3 meses" / "Publicado hace 5 días" / "Publicado hoy". */
export function antiguedadOferta(fecha: string | null | undefined, hoy: Date = new Date()): string {
  if (!fecha) return ''
  const [y, m, d] = fecha.slice(0, 10).split('-').map(Number)
  if (!y || !m || !d) return ''
  const pub = Date.UTC(y, m - 1, d)
  const ref = Date.UTC(hoy.getFullYear(), hoy.getMonth(), hoy.getDate())
  const dias = Math.max(0, Math.round((ref - pub) / 86_400_000))
  if (dias === 0) return 'Publicado hoy'
  if (dias === 1) return 'Publicado ayer'
  if (dias < 30) return `Publicado hace ${dias} días`
  const meses = Math.floor(dias / 30)
  if (meses < 12) return `Publicado hace ${meses} ${meses === 1 ? 'mes' : 'meses'}`
  const anios = Math.floor(meses / 12)
  return `Publicado hace ${anios} ${anios === 1 ? 'año' : 'años'}`
}

/**
 * Inicio de un período contado hacia atrás desde la última fecha con datos
 * (no desde hoy). `dias = null` → sin filtro.
 */
export function periodoDesde(dias: number | null, fechaMax: string | null): string | null {
  if (dias === null) return null
  const base = fechaMax ? new Date(`${fechaMax.slice(0, 10)}T00:00:00Z`) : new Date()
  base.setUTCDate(base.getUTCDate() - dias)
  return base.toISOString().slice(0, 10)
}

/** Provincias tal como figuran en ofertas_dashboard.provincia. */
const PROVINCIAS_MOL = [
  'Buenos Aires', 'CABA', 'Catamarca', 'Chaco', 'Chubut', 'Córdoba', 'Corrientes',
  'Entre Ríos', 'Formosa', 'Jujuy', 'La Pampa', 'La Rioja', 'Mendoza', 'Misiones',
  'Neuquén', 'Río Negro', 'Salta', 'San Juan', 'San Luis', 'Santa Cruz', 'Santa Fe',
  'Santiago del Estero', 'Tierra del Fuego', 'Tucumán',
]

const sinTildes = (s: string) => s.toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '').trim()

const ALIAS_CABA = new Set([
  'caba', 'capital federal', 'cap. fed.', 'cap fed', 'ciudad de buenos aires',
  'ciudad autonoma de buenos aires', 'c.a.b.a.',
])

/**
 * Ubicación de la persona ("La Matanza, Buenos Aires", "CABA", "Cordoba") →
 * provincia en el formato de ofertas_dashboard. null si no se reconoce.
 */
export function provinciaOfertas(ubicacion: string | null | undefined): string | null {
  if (!ubicacion) return null
  const partes = ubicacion.split(',').map(p => p.trim()).filter(Boolean)
  for (const parte of [...partes].reverse()) {
    const n = sinTildes(parte)
    if (ALIAS_CABA.has(n)) return 'CABA'
    if (n === 'gba') return 'Buenos Aires'
    const match = PROVINCIAS_MOL.find(p => sinTildes(p) === n)
    if (match) return match
  }
  return null
}
