/**
 * Normaliza el campo ubicacion de personas al formato
 * exacto de regice_sedes.provincia.
 *
 * "La Matanza, Buenos Aires" → "Buenos aires"
 * "CABA" → "Capital federal"
 * "Córdoba Capital, Córdoba" → "Cordoba"
 */

const REGICE_MAP: Record<string, string> = {
  'buenos aires': 'Buenos aires',
  'caba': 'Capital federal',
  'ciudad de buenos aires': 'Capital federal',
  'ciudad autonoma de buenos aires': 'Capital federal',
  'capital federal': 'Capital federal',
  'catamarca': 'Catamarca',
  'chaco': 'Chaco',
  'chubut': 'Chubut',
  'cordoba': 'Cordoba',
  'corrientes': 'Corrientes',
  'entre rios': 'Entre rios',
  'formosa': 'Formosa',
  'jujuy': 'Jujuy',
  'la pampa': 'La pampa',
  'la rioja': 'La rioja',
  'mendoza': 'Mendoza',
  'misiones': 'Misiones',
  'neuquen': 'Neuquen',
  'rio negro': 'Rio negro',
  'salta': 'Salta',
  'san juan': 'San juan',
  'san luis': 'San luis',
  'santa cruz': 'Santa cruz',
  'santa fe': 'Santa fe',
  'santiago del estero': 'Santiago del estero',
  'tierra del fuego': 'Tierra del fuego',
  'tucuman': 'Tucuman',
}

function stripAccents(s: string): string {
  return s.normalize('NFD').replace(/[\u0300-\u036f]/g, '')
}

export function normalizeProvinciaToRegice(ubicacion: string | null | undefined): string | null {
  if (!ubicacion) return null

  // Extract province: part after last comma, or whole string
  const parts = ubicacion.split(',')
  const raw = parts.length > 1 ? parts[parts.length - 1].trim() : ubicacion.trim()

  // Normalize: lowercase, strip accents
  const key = stripAccents(raw.toLowerCase())

  return REGICE_MAP[key] || null
}
