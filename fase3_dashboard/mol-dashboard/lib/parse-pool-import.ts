/**
 * Parser y sanitizador para importación de pools OE via CSV.
 *
 * Sanitiza contra:
 * - Fórmulas Excel (=, +, -, @)
 * - HTML tags
 * - Caracteres de control
 * - SQL injection patterns
 *
 * Valida:
 * - Columnas requeridas presentes
 * - Tipos de dato
 * - Longitudes máximas
 * - Límite de filas
 */

export const MAX_ROWS = 10000
export const MAX_CELL_LENGTH = 500

export interface PoolPersona {
  nombre: string
  dni?: string
  email?: string
  telefono?: string
  ocupacion_actual?: string
  skills_declaradas?: string
  notas?: string
}

export interface PoolVacante {
  titulo: string
  empresa: string
  descripcion?: string
  requisitos?: string
  ubicacion?: string
  modalidad?: string
  contacto?: string
}

export interface PoolCurso {
  nombre: string
  descripcion?: string
  duracion?: string
  modalidad?: string
  certificacion?: string
  institucion?: string
}

export interface ParseResult<T> {
  data: T[]
  errors: string[]
  warnings: string[]
  total_rows: number
  valid_rows: number
  skipped_rows: number
}

/**
 * Sanitiza una celda contra inyección de fórmulas Excel, HTML y SQL.
 */
export function sanitizeCell(value: unknown): string {
  if (value === null || value === undefined) return ''

  let str = String(value).trim()

  // Truncar si excede longitud máxima
  if (str.length > MAX_CELL_LENGTH) {
    str = str.substring(0, MAX_CELL_LENGTH)
  }

  // Remover fórmulas Excel (=, +, -, @, tab, carriage return al inicio)
  str = str.replace(/^[=+\-@\t\r]+/, '')

  // Remover HTML tags
  str = str.replace(/<[^>]*>/g, '')

  // Remover caracteres de control (excepto newline)
  str = str.replace(/[\x00-\x09\x0B\x0C\x0E-\x1F\x7F]/g, '')

  // Escapar patrones SQL comunes (no es la defensa principal — RLS y parametrized queries lo son)
  str = str.replace(/[';\\]/g, '')

  return str.trim()
}

/**
 * Parsea CSV text a array de objetos.
 * Primera fila = headers.
 */
export function parseCSV(text: string): Record<string, string>[] {
  const lines = text.split(/\r?\n/).filter(l => l.trim())
  if (lines.length < 2) return [] // necesita header + al menos 1 fila

  const headers = lines[0].split(',').map(h => sanitizeCell(h).toLowerCase().replace(/\s+/g, '_'))
  const rows: Record<string, string>[] = []

  for (let i = 1; i < Math.min(lines.length, MAX_ROWS + 1); i++) {
    const values = lines[i].split(',')
    const row: Record<string, string> = {}
    for (let j = 0; j < headers.length; j++) {
      row[headers[j]] = sanitizeCell(values[j])
    }
    rows.push(row)
  }

  return rows
}

/**
 * Parsea y valida pool de personas.
 */
export function parsePersonas(text: string): ParseResult<PoolPersona> {
  const rows = parseCSV(text)
  const errors: string[] = []
  const warnings: string[] = []
  const data: PoolPersona[] = []

  if (rows.length === 0) {
    errors.push('Archivo vacío o sin datos')
    return { data, errors, warnings, total_rows: 0, valid_rows: 0, skipped_rows: 0 }
  }

  // Verificar columna nombre (requerida)
  const firstRow = rows[0]
  if (!('nombre' in firstRow) && !('nombre_completo' in firstRow) && !('apellido_nombre' in firstRow)) {
    errors.push('Columna "nombre" no encontrada. Columnas disponibles: ' + Object.keys(firstRow).join(', '))
    return { data, errors, warnings, total_rows: rows.length, valid_rows: 0, skipped_rows: rows.length }
  }

  const nameKey = 'nombre' in firstRow ? 'nombre' : ('nombre_completo' in firstRow ? 'nombre_completo' : 'apellido_nombre')

  let skipped = 0
  for (let i = 0; i < rows.length; i++) {
    const row = rows[i]
    const nombre = row[nameKey]

    if (!nombre || nombre.length < 2) {
      warnings.push(`Fila ${i + 2}: nombre vacío o muy corto, saltada`)
      skipped++
      continue
    }

    data.push({
      nombre,
      dni: row.dni || row.documento || undefined,
      email: row.email || row.correo || undefined,
      telefono: row.telefono || row.tel || row.celular || undefined,
      ocupacion_actual: row.ocupacion || row.ocupacion_actual || row.puesto || undefined,
      skills_declaradas: row.skills || row.competencias || row.habilidades || undefined,
      notas: row.notas || row.observaciones || undefined,
    })
  }

  if (rows.length >= MAX_ROWS) {
    warnings.push(`Se procesaron las primeras ${MAX_ROWS} filas. El archivo tiene más.`)
  }

  return {
    data,
    errors,
    warnings,
    total_rows: rows.length,
    valid_rows: data.length,
    skipped_rows: skipped,
  }
}

/**
 * Parsea y valida pool de vacantes.
 */
export function parseVacantes(text: string): ParseResult<PoolVacante> {
  const rows = parseCSV(text)
  const errors: string[] = []
  const warnings: string[] = []
  const data: PoolVacante[] = []

  if (rows.length === 0) {
    errors.push('Archivo vacío o sin datos')
    return { data, errors, warnings, total_rows: 0, valid_rows: 0, skipped_rows: 0 }
  }

  const firstRow = rows[0]
  if (!('titulo' in firstRow) && !('puesto' in firstRow) && !('cargo' in firstRow)) {
    errors.push('Columna "titulo" o "puesto" no encontrada. Columnas: ' + Object.keys(firstRow).join(', '))
    return { data, errors, warnings, total_rows: rows.length, valid_rows: 0, skipped_rows: rows.length }
  }

  const titleKey = 'titulo' in firstRow ? 'titulo' : ('puesto' in firstRow ? 'puesto' : 'cargo')

  let skipped = 0
  for (let i = 0; i < rows.length; i++) {
    const row = rows[i]
    const titulo = row[titleKey]

    if (!titulo || titulo.length < 3) {
      skipped++
      continue
    }

    data.push({
      titulo,
      empresa: row.empresa || row.organizacion || '',
      descripcion: row.descripcion || row.detalle || undefined,
      requisitos: row.requisitos || row.requerimientos || undefined,
      ubicacion: row.ubicacion || row.localidad || row.zona || undefined,
      modalidad: row.modalidad || undefined,
      contacto: row.contacto || row.email_contacto || undefined,
    })
  }

  return { data, errors, warnings, total_rows: rows.length, valid_rows: data.length, skipped_rows: skipped }
}

/**
 * Parsea y valida pool de cursos.
 */
export function parseCursos(text: string): ParseResult<PoolCurso> {
  const rows = parseCSV(text)
  const errors: string[] = []
  const warnings: string[] = []
  const data: PoolCurso[] = []

  if (rows.length === 0) {
    errors.push('Archivo vacío o sin datos')
    return { data, errors, warnings, total_rows: 0, valid_rows: 0, skipped_rows: 0 }
  }

  const firstRow = rows[0]
  if (!('nombre' in firstRow) && !('curso' in firstRow) && !('titulo' in firstRow)) {
    errors.push('Columna "nombre" o "curso" no encontrada. Columnas: ' + Object.keys(firstRow).join(', '))
    return { data, errors, warnings, total_rows: rows.length, valid_rows: 0, skipped_rows: rows.length }
  }

  const nameKey = 'nombre' in firstRow ? 'nombre' : ('curso' in firstRow ? 'curso' : 'titulo')

  let skipped = 0
  for (let i = 0; i < rows.length; i++) {
    const row = rows[i]
    const nombre = row[nameKey]

    if (!nombre || nombre.length < 3) {
      skipped++
      continue
    }

    data.push({
      nombre,
      descripcion: row.descripcion || row.detalle || undefined,
      duracion: row.duracion || undefined,
      modalidad: row.modalidad || undefined,
      certificacion: row.certificacion || row.tipo || undefined,
      institucion: row.institucion || row.centro || undefined,
    })
  }

  return { data, errors, warnings, total_rows: rows.length, valid_rows: data.length, skipped_rows: skipped }
}
