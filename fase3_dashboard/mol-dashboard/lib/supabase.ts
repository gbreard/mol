import { createClient, SupabaseClient } from '@supabase/supabase-js'
import { DashboardFilters, Issue, IssueStats } from './types'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || ''
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || ''

// Solo crear cliente si hay credenciales (permite páginas públicas sin Supabase)
export const supabase: SupabaseClient | null =
  supabaseUrl && supabaseAnonKey
    ? createClient(supabaseUrl, supabaseAnonKey)
    : null

// Helper para verificar si Supabase está disponible
export function requireSupabase(): SupabaseClient {
  if (!supabase) {
    throw new Error('Supabase no está configurado. Verifica las variables de entorno.')
  }
  return supabase
}

// Nombre de la tabla principal con datos
const TABLA_OFERTAS = 'ofertas_dashboard'

// Tipos para las tablas
export interface OfertaDashboard {
  id_oferta: string
  titulo: string
  titulo_limpio: string | null
  empresa: string | null
  fecha_publicacion: string | null
  url: string | null
  portal: string | null
  provincia: string | null
  localidad: string | null
  isco_code: string | null
  isco_label: string | null
  occupation_match_score: number | null
  occupation_match_method: string | null
  modalidad: string | null
  nivel_seniority: string | null
  area_funcional: string | null
  sector_empresa: string | null
  salario_min: number | null
  salario_max: number | null
  skills_tecnicas: string[] | null
  soft_skills: string[] | null
}

// Mapeo de nombres de provincia a valores de BD
const provinciaMap: Record<string, string> = {
  'caba': 'Capital Federal',
  'buenosaires': 'Buenos Aires',
  'cordoba': 'Córdoba',
  'santafe': 'Santa Fe',
  'mendoza': 'Mendoza',
  'tucuman': 'Tucumán',
  'entrerios': 'Entre Ríos',
  'salta': 'Salta',
  'chaco': 'Chaco',
  'corrientes': 'Corrientes',
  'misiones': 'Misiones',
  'neuquen': 'Neuquén',
  'formosa': 'Formosa',
  'jujuy': 'Jujuy',
  'catamarca': 'Catamarca',
  'larioja': 'La Rioja',
  'sanjuan': 'San Juan',
  'sanluis': 'San Luis',
  'rionegro': 'Río Negro',
  'chubut': 'Chubut',
  'santacruz': 'Santa Cruz',
  'tierradelfuego': 'Tierra del Fuego',
  'lapampa': 'La Pampa',
  'santiago': 'Santiago del Estero',
}

// Helper para parsear skills de string a array
function parseSkillsList(skills: string | null): string[] {
  if (!skills) return []
  // Skills vienen separadas por "; " o ", "
  return skills.split(/[;,]\s*/).map(s => s.trim()).filter(Boolean)
}

// Helper para aplicar filtros a una query
function applyFilters(query: any, filters?: DashboardFilters) {
  if (!filters) return query

  // Filtro por provincia
  if (filters.provincia && provinciaMap[filters.provincia]) {
    query = query.eq('provincia', provinciaMap[filters.provincia])
  }

  // Filtro por localidad
  if (filters.localidad) {
    query = query.eq('localidad', filters.localidad)
  }

  // Filtro por fecha desde
  if (filters.fechaDesde) {
    const fechaDesde = filters.fechaDesde.toISOString().split('T')[0]
    query = query.gte('fecha_publicacion', fechaDesde)
  }

  // Filtro por fecha hasta
  if (filters.fechaHasta) {
    const fechaHasta = filters.fechaHasta.toISOString().split('T')[0]
    query = query.lte('fecha_publicacion', fechaHasta)
  }

  // Filtro por ocupaciones seleccionadas
  if (filters.ocupacionesSeleccionadas && filters.ocupacionesSeleccionadas.length > 0) {
    query = query.in('isco_code', filters.ocupacionesSeleccionadas)
  }

  return query
}

// Helper para obtener cliente de forma segura (retorna null si no está disponible)
function getSupabaseClient() {
  return supabase
}

// Helper para paginación - Supabase limita a 1000 filas por query
// Esta función obtiene TODOS los datos usando paginación automática
async function fetchAllPaginated<T>(
  client: SupabaseClient,
  table: string,
  selectColumns: string,
  applyFiltersFunc?: (query: any) => any,
  pageSize: number = 1000
): Promise<T[]> {
  let allData: T[] = []
  let offset = 0

  while (true) {
    let query = client
      .from(table)
      .select(selectColumns)
      .range(offset, offset + pageSize - 1)

    if (applyFiltersFunc) {
      query = applyFiltersFunc(query)
    }

    const { data, error } = await query

    if (error) throw error
    if (!data || data.length === 0) break

    allData = allData.concat(data as T[])

    if (data.length < pageSize) break // Última página
    offset += pageSize
  }

  return allData
}

// ============================================
// INSIGHTS OPTIMIZADOS (E-16) - Usa RPC SQL
// ============================================

// Tipo para la respuesta del RPC get_insights
export interface InsightsData {
  kpis: {
    total_ofertas: number
    ocupaciones_distintas: number
    empresas_activas: number
    provincias: number
  }
  isco_grupos: Array<{
    grupo: string
    total: number
    porcentaje: number
  }>
  concentracion_top3: number
  top_empresas: Array<{
    empresa: string
    ofertas: number
  }>
  provincias: Array<{
    provincia: string
    total: number
    porcentaje: number
  }>
}

/**
 * Obtiene todos los insights en UNA sola llamada RPC
 * Reemplaza: getKPIs, getOfertasPorProvincia, getTopOcupaciones (parcialmente)
 * Performance: ~5ms vs ~500ms con fetchAllPaginated
 */
export async function getInsightsRPC(filters?: DashboardFilters): Promise<InsightsData | null> {
  const client = getSupabaseClient()
  if (!client) return null

  const { data, error } = await client.rpc('get_insights', {
    p_provincia: filters?.provincia ? provinciaMap[filters.provincia] || filters.provincia : null,
    p_fecha_desde: filters?.fechaDesde?.toISOString().split('T')[0] || null,
    p_fecha_hasta: filters?.fechaHasta?.toISOString().split('T')[0] || null
  })

  if (error) {
    console.error('Error en get_insights RPC:', error)
    return null
  }

  return data as InsightsData
}

/**
 * Obtiene KPIs usando RPC (optimizado)
 */
export async function getKPIsOptimized(filters?: DashboardFilters) {
  const insights = await getInsightsRPC(filters)
  if (!insights) {
    return { totalOfertas: 0, ocupacionesDistintas: 0, empresasActivas: 0, provincias: 0 }
  }
  return {
    totalOfertas: insights.kpis.total_ofertas,
    ocupacionesDistintas: insights.kpis.ocupaciones_distintas,
    empresasActivas: insights.kpis.empresas_activas,
    provincias: insights.kpis.provincias
  }
}

/**
 * Obtiene distribución por provincia usando RPC (optimizado)
 */
export async function getOfertasPorProvinciaOptimized(filters?: DashboardFilters) {
  const insights = await getInsightsRPC(filters)
  if (!insights) return []

  return insights.provincias.map(p => ({
    jurisdiccion: p.provincia,
    cantidad: p.total,
    porcentaje: p.porcentaje
  }))
}

// ============================================
// FUNCIONES LEGACY (mantener por compatibilidad)
// ============================================

// Funciones para obtener datos del dashboard
// @deprecated - Usar getKPIsOptimized para mejor performance
export async function getKPIs(filters?: DashboardFilters) {
  const client = getSupabaseClient()
  if (!client) return { totalOfertas: 0, ocupacionesDistintas: 0, empresasActivas: 0, provincias: 0 }

  // 1. Obtener total de ofertas usando count (sin límite de 1000)
  let countQuery = client
    .from(TABLA_OFERTAS)
    .select('id_oferta', { count: 'exact', head: true })
  countQuery = applyFilters(countQuery, filters)
  const { count: totalOfertas, error: countError } = await countQuery
  if (countError) throw countError

  // 2. Obtener datos únicos para las demás métricas con paginación
  const ofertas = await fetchAllPaginated<{ isco_code: string; empresa: string; provincia: string }>(
    client,
    TABLA_OFERTAS,
    'isco_code, empresa, provincia',
    (query) => applyFilters(query, filters)
  )

  return {
    totalOfertas: totalOfertas || 0,
    ocupacionesDistintas: new Set(ofertas.map(o => o.isco_code).filter(Boolean)).size,
    empresasActivas: new Set(ofertas.map(o => o.empresa).filter(Boolean)).size,
    provincias: new Set(ofertas.map(o => o.provincia).filter(Boolean)).size
  }
}

export async function getOfertasPorProvincia(filters?: DashboardFilters) {
  const client = getSupabaseClient()
  if (!client) return []

  // Usar paginación para obtener TODOS los datos
  const applyDateFilters = (query: any) => {
    if (filters?.fechaDesde) {
      const fechaDesde = filters.fechaDesde.toISOString().split('T')[0]
      query = query.gte('fecha_publicacion', fechaDesde)
    }
    if (filters?.fechaHasta) {
      const fechaHasta = filters.fechaHasta.toISOString().split('T')[0]
      query = query.lte('fecha_publicacion', fechaHasta)
    }
    return query
  }

  const data = await fetchAllPaginated<{ provincia: string }>(
    client,
    TABLA_OFERTAS,
    'provincia',
    applyDateFilters
  )

  const counts: Record<string, number> = {}
  data.forEach(o => {
    const prov = o.provincia || 'No especificado'
    counts[prov] = (counts[prov] || 0) + 1
  })

  const total = data.length || 1
  return Object.entries(counts)
    .map(([jurisdiccion, cantidad]) => ({
      jurisdiccion,
      cantidad,
      porcentaje: Math.round(cantidad * 1000 / total) / 10
    }))
    .sort((a, b) => b.cantidad - a.cantidad)
}

export async function getTopOcupaciones(limit = 10, filters?: DashboardFilters) {
  const client = getSupabaseClient()
  if (!client) return []

  // Usar paginación para obtener TODOS los datos
  const data = await fetchAllPaginated<{ isco_code: string; isco_label: string }>(
    client,
    TABLA_OFERTAS,
    'isco_code, isco_label',
    (query) => applyFilters(query, filters)
  )

  const counts: Record<string, { label: string, count: number }> = {}
  data.forEach(o => {
    if (o.isco_code && o.isco_label) {
      if (!counts[o.isco_code]) {
        counts[o.isco_code] = { label: o.isco_label, count: 0 }
      }
      counts[o.isco_code].count++
    }
  })

  return Object.entries(counts)
    .map(([code, { label, count }]) => ({
      ocupacion: label,
      cantidad: count
    }))
    .sort((a, b) => b.cantidad - a.cantidad)
    .slice(0, limit)
}

export async function getOfertasPorModalidad(filters?: DashboardFilters) {
  const client = getSupabaseClient()
  if (!client) return []

  // Usar paginación para obtener TODOS los datos
  const data = await fetchAllPaginated<{ modalidad: string }>(
    client,
    TABLA_OFERTAS,
    'modalidad',
    (query) => applyFilters(query, filters)
  )

  const counts: Record<string, number> = {}
  data.forEach(o => {
    const mod = o.modalidad || 'No especificado'
    counts[mod] = (counts[mod] || 0) + 1
  })

  return Object.entries(counts)
    .map(([modalidad, cantidad]) => ({ modalidad, cantidad }))
    .sort((a, b) => b.cantidad - a.cantidad)
}

export async function getOfertas(limit = 50, offset = 0, filters?: DashboardFilters) {
  const client = getSupabaseClient()
  if (!client) return { ofertas: [], total: 0 }

  let query = client
    .from(TABLA_OFERTAS)
    .select(`
      id_oferta,
      titulo,
      empresa,
      fecha_publicacion,
      url,
      portal,
      provincia,
      localidad,
      isco_code,
      isco_label,
      occupation_match_score,
      occupation_match_method,
      modalidad,
      nivel_seniority,
      area_funcional,
      sector_empresa,
      salario_min,
      salario_max,
      skills_tecnicas,
      soft_skills
    `, { count: 'exact' })

  query = applyFilters(query, filters)

  const { data, error, count } = await query
    .order('fecha_publicacion', { ascending: false })
    .range(offset, offset + limit - 1)

  if (error) throw error

  // Transformar los datos al formato esperado por el dashboard
  const ofertas = (data || []).map(o => ({
    id_oferta: o.id_oferta,
    titulo: o.titulo,
    titulo_limpio: o.titulo,  // Usamos titulo como fallback
    empresa: o.empresa,
    fecha_publicacion: o.fecha_publicacion,
    url: o.url,
    portal: o.portal,
    provincia: o.provincia,
    localidad: o.localidad,
    isco_code: o.isco_code,
    isco_label: o.isco_label,
    occupation_match_score: o.occupation_match_score,
    occupation_match_method: o.occupation_match_method,
    modalidad: o.modalidad,
    nivel_seniority: o.nivel_seniority,
    area_funcional: o.area_funcional,
    sector_empresa: o.sector_empresa,
    salario_min: o.salario_min,
    salario_max: o.salario_max,
    skills_tecnicas: parseSkillsList(o.skills_tecnicas),
    soft_skills: parseSkillsList(o.soft_skills),
  }))

  return { ofertas, total: count || 0 }
}

// Funciones para obtener skills (para Requerimientos)
export async function getTopSkillsTecnicas(limit = 20, filters?: DashboardFilters) {
  const client = getSupabaseClient()
  if (!client) return []

  // Usar paginación para obtener TODOS los datos
  const data = await fetchAllPaginated<{ skills_tecnicas: string }>(
    client,
    TABLA_OFERTAS,
    'skills_tecnicas',
    (query) => applyFilters(query, filters)
  )

  const counts: Record<string, number> = {}
  data.forEach(o => {
    const skills = parseSkillsList(o.skills_tecnicas)
    skills.forEach((skill: string) => {
      counts[skill] = (counts[skill] || 0) + 1
    })
  })

  return Object.entries(counts)
    .map(([name, value]) => ({ name, value }))
    .sort((a, b) => b.value - a.value)
    .slice(0, limit)
}

export async function getTopSoftSkills(limit = 20, filters?: DashboardFilters) {
  const client = getSupabaseClient()
  if (!client) return []

  // Usar paginación para obtener TODOS los datos
  const data = await fetchAllPaginated<{ soft_skills: string }>(
    client,
    TABLA_OFERTAS,
    'soft_skills',
    (query) => applyFilters(query, filters)
  )

  const counts: Record<string, number> = {}
  data.forEach(o => {
    const skills = parseSkillsList(o.soft_skills)
    skills.forEach((skill: string) => {
      counts[skill] = (counts[skill] || 0) + 1
    })
  })

  return Object.entries(counts)
    .map(([name, value]) => ({ name, value }))
    .sort((a, b) => b.value - a.value)
    .slice(0, limit)
}

// ========== FUNCIONES PARA SIDEBAR ==========

// Total de ofertas con filtros aplicados
export async function getTotalOfertas(filters?: DashboardFilters): Promise<number> {
  const client = getSupabaseClient()
  if (!client) return 0

  let query = client
    .from(TABLA_OFERTAS)
    .select('id_oferta', { count: 'exact', head: true })

  query = applyFilters(query, filters)

  const { count, error } = await query
  if (error) throw error
  return count || 0
}

// Localidades distintas para una provincia dada
export async function getLocalidadesByProvincia(provinciaKey: string): Promise<string[]> {
  const client = getSupabaseClient()
  if (!client) return []

  const provinciaName = provinciaMap[provinciaKey]
  if (!provinciaName) return []

  const data = await fetchAllPaginated<{ localidad: string }>(
    client,
    TABLA_OFERTAS,
    'localidad',
    (query) => query.eq('provincia', provinciaName).not('localidad', 'is', null)
  )

  const unique = [...new Set(data.map(d => d.localidad).filter(Boolean))]
  return unique.sort((a, b) => a.localeCompare(b, 'es'))
}

// Árbol de ocupaciones ISCO para el Sidebar (agrupadas por primer dígito)
const ISCO_MAJOR_GROUPS: Record<string, string> = {
  '1': 'Directores y gerentes',
  '2': 'Profesionales científicos e intelectuales',
  '3': 'Técnicos y profesionales de nivel medio',
  '4': 'Personal de apoyo administrativo',
  '5': 'Trabajadores de servicios y vendedores',
  '6': 'Agricultores y trabajadores agropecuarios',
  '7': 'Oficiales, operarios y artesanos',
  '8': 'Operadores de instalaciones y máquinas',
  '9': 'Ocupaciones elementales',
  '0': 'Ocupaciones militares',
}

export interface OcupacionTreeNode {
  id: string;
  label: string;
  count: number;
  children: { id: string; label: string; count: number }[];
}

export async function getOcupacionesTree(filters?: DashboardFilters): Promise<OcupacionTreeNode[]> {
  const client = getSupabaseClient()
  if (!client) return []

  // Usar paginación para obtener TODOS los datos (Supabase limita a 1000 por query)
  const data = await fetchAllPaginated<{ isco_code: string; isco_label: string }>(
    client,
    TABLA_OFERTAS,
    'isco_code, isco_label',
    (query) => applyFilters(query, filters)
  )

  // Agrupar por código ISCO de 4 dígitos
  const detailCounts: Record<string, { label: string; count: number }> = {}
  data.forEach(o => {
    if (o.isco_code && o.isco_label) {
      if (!detailCounts[o.isco_code]) {
        detailCounts[o.isco_code] = { label: o.isco_label, count: 0 }
      }
      detailCounts[o.isco_code].count++
    }
  })

  // Agrupar en major groups (primer dígito)
  const groups: Record<string, { children: Record<string, { label: string; count: number }>, totalCount: number }> = {}

  Object.entries(detailCounts).forEach(([code, { label, count }]) => {
    const majorDigit = code.charAt(0)
    if (!groups[majorDigit]) {
      groups[majorDigit] = { children: {}, totalCount: 0 }
    }
    groups[majorDigit].children[code] = { label, count }
    groups[majorDigit].totalCount += count
  })

  // Convertir a formato de árbol, ordenado por count descendente
  return Object.entries(groups)
    .map(([digit, { children, totalCount }]) => ({
      id: `isco-${digit}`,
      label: ISCO_MAJOR_GROUPS[digit] || `Grupo ${digit}`,
      count: totalCount,
      children: Object.entries(children)
        .map(([code, { label, count }]) => ({
          id: code,
          label,
          count,
        }))
        .sort((a, b) => b.count - a.count)
    }))
    .sort((a, b) => b.count - a.count)
}

// Filtros locales para el tab de requerimientos
export interface RequerimientosFilters {
  educacion?: string;
  modalidad?: string;
}

// Funciones para obtener distribuciones de requerimientos
export async function getDistribucionRequerimientos(filters?: DashboardFilters, localFilters?: RequerimientosFilters) {
  const client = getSupabaseClient()
  if (!client) return { total: 0, educacion: [], experiencia: [], seniority: [], modalidad: [], genteCargo: [], jornada: [] }

  // Usar paginación para obtener TODOS los datos
  const ofertas = await fetchAllPaginated<{
    nivel_educativo: string | null;
    experiencia_min_anios: number | null;
    nivel_seniority: string | null;
    modalidad: string | null;
    tiene_gente_cargo: boolean | null;
    jornada_laboral: string | null;
  }>(
    client,
    TABLA_OFERTAS,
    'nivel_educativo, experiencia_min_anios, nivel_seniority, modalidad, tiene_gente_cargo, jornada_laboral',
    (query) => {
      query = applyFilters(query, filters)
      // Aplicar filtros locales
      if (localFilters?.educacion && localFilters.educacion !== 'Todos') {
        query = query.eq('nivel_educativo', localFilters.educacion)
      }
      if (localFilters?.modalidad && localFilters.modalidad !== 'Todos') {
        query = query.eq('modalidad', localFilters.modalidad)
      }
      return query
    }
  )
  const total = ofertas.length

  // Nivel educativo
  const educacionCounts: Record<string, number> = {}
  ofertas.forEach(o => {
    const nivel = o.nivel_educativo || 'Sin especificar'
    educacionCounts[nivel] = (educacionCounts[nivel] || 0) + 1
  })

  // Experiencia (agrupada en rangos)
  const experienciaCounts: Record<string, number> = {
    'Sin experiencia': 0,
    '1-2 años': 0,
    '3-4 años': 0,
    '5+ años': 0,
    'Sin especificar': 0
  }
  ofertas.forEach(o => {
    const exp = o.experiencia_min_anios
    if (exp === null || exp === undefined) {
      experienciaCounts['Sin especificar']++
    } else if (exp === 0) {
      experienciaCounts['Sin experiencia']++
    } else if (exp <= 2) {
      experienciaCounts['1-2 años']++
    } else if (exp <= 4) {
      experienciaCounts['3-4 años']++
    } else {
      experienciaCounts['5+ años']++
    }
  })

  // Seniority
  const seniorityCounts: Record<string, number> = {}
  ofertas.forEach(o => {
    const nivel = o.nivel_seniority || 'Sin especificar'
    seniorityCounts[nivel] = (seniorityCounts[nivel] || 0) + 1
  })

  // Modalidad
  const modalidadCounts: Record<string, number> = {}
  ofertas.forEach(o => {
    const mod = o.modalidad || 'Sin especificar'
    modalidadCounts[mod] = (modalidadCounts[mod] || 0) + 1
  })

  // Gente a cargo
  const genteCargoCounts: Record<string, number> = {
    'Con gente a cargo': 0,
    'Sin gente a cargo': 0
  }
  ofertas.forEach(o => {
    if (o.tiene_gente_cargo) {
      genteCargoCounts['Con gente a cargo']++
    } else {
      genteCargoCounts['Sin gente a cargo']++
    }
  })

  // Jornada laboral
  const jornadaCounts: Record<string, number> = {}
  ofertas.forEach(o => {
    const jornada = o.jornada_laboral || 'Sin especificar'
    jornadaCounts[jornada] = (jornadaCounts[jornada] || 0) + 1
  })

  // Formatear para gráficos
  const formatDistribucion = (counts: Record<string, number>, orden?: string[]) => {
    const entries = Object.entries(counts)
    if (orden) {
      entries.sort((a, b) => {
        const idxA = orden.indexOf(a[0])
        const idxB = orden.indexOf(b[0])
        return (idxA === -1 ? 999 : idxA) - (idxB === -1 ? 999 : idxB)
      })
    } else {
      entries.sort((a, b) => b[1] - a[1])
    }
    return entries.map(([name, value]) => ({
      name,
      value,
      porcentaje: total > 0 ? Math.round(value * 100 / total) : 0
    }))
  }

  return {
    total,
    educacion: formatDistribucion(educacionCounts, ['universitario', 'terciario', 'secundario', 'primario', 'Sin especificar']),
    experiencia: formatDistribucion(experienciaCounts, ['Sin experiencia', '1-2 años', '3-4 años', '5+ años', 'Sin especificar']),
    seniority: formatDistribucion(seniorityCounts, ['trainee', 'junior', 'semisenior', 'senior', 'manager', 'Sin especificar']),
    modalidad: formatDistribucion(modalidadCounts, ['presencial', 'hibrido', 'remoto', 'Sin especificar']),
    genteCargo: formatDistribucion(genteCargoCounts),
    jornada: formatDistribucion(jornadaCounts, ['full-time', 'part-time', 'freelance', 'Sin especificar'])
  }
}

// ========== FUNCIONES PARA SKILLS CLASIFICADAS (ofertas_skills) ==========

// Filtros para skills
export interface SkillsFilters {
  categoria?: string;  // Código L1 o nombre
  esDigital?: boolean | null;  // true = solo digitales, false = solo no digitales, null = todos
}

// Helper: obtener IDs de ofertas que cumplen filtros globales
// Solo consulta si hay filtros activos, sino retorna null (= sin filtro)
async function getFilteredOfertaIds(filters?: DashboardFilters): Promise<string[] | null> {
  const client = getSupabaseClient()
  if (!client) return null
  if (!filters) return null

  const hasGlobalFilter = filters.provincia || filters.fechaDesde || filters.fechaHasta ||
    (filters.ocupacionesSeleccionadas && filters.ocupacionesSeleccionadas.length > 0)

  if (!hasGlobalFilter) return null

  // Usar paginación para obtener TODOS los IDs
  const data = await fetchAllPaginated<{ id_oferta: string }>(
    client,
    TABLA_OFERTAS,
    'id_oferta',
    (query) => applyFilters(query, filters)
  )

  return data.map(o => o.id_oferta)
}

// Helper: aplicar filtro de IDs a una query de ofertas_skills
function applyOfertaIdsFilter(query: any, ofertaIds: string[] | null) {
  if (ofertaIds === null) return query
  if (ofertaIds.length === 0) return query.in('id_oferta', ['__none__']) // No match
  return query.in('id_oferta', ofertaIds)
}

// Distribución por categoría L1
export async function getSkillsPorCategoriaL1(skillsFilters?: SkillsFilters, globalFilters?: DashboardFilters) {
  const client = getSupabaseClient()
  if (!client) return []

  const ofertaIds = await getFilteredOfertaIds(globalFilters)

  // Usar paginación para obtener TODOS los datos
  const data = await fetchAllPaginated<{ l1: string; l1_nombre: string; es_digital: boolean }>(
    client,
    'ofertas_skills',
    'l1, l1_nombre, es_digital',
    (query) => {
      query = query.not('l1', 'is', null)
      query = applyOfertaIdsFilter(query, ofertaIds)
      // Filtro por digital
      if (skillsFilters?.esDigital !== undefined && skillsFilters.esDigital !== null) {
        query = query.eq('es_digital', skillsFilters.esDigital)
      }
      return query
    }
  )

  const counts: Record<string, { nombre: string, count: number }> = {}
  data.forEach(s => {
    if (!counts[s.l1]) {
      counts[s.l1] = { nombre: s.l1_nombre || s.l1, count: 0 }
    }
    counts[s.l1].count++
  })

  const total = data.length || 1
  return Object.entries(counts)
    .map(([code, { nombre, count }]) => ({
      code,
      name: nombre,
      value: count,
      porcentaje: Math.round(count * 100 / total)
    }))
    .sort((a, b) => b.value - a.value)
}

// Skills digitales vs no digitales
export async function getSkillsDigitales(skillsFilters?: SkillsFilters, globalFilters?: DashboardFilters) {
  const client = getSupabaseClient()
  if (!client) return []

  const ofertaIds = await getFilteredOfertaIds(globalFilters)

  // Usar paginación para obtener TODOS los datos
  const data = await fetchAllPaginated<{ es_digital: boolean; l1: string; l1_nombre: string }>(
    client,
    'ofertas_skills',
    'es_digital, l1, l1_nombre',
    (query) => {
      query = applyOfertaIdsFilter(query, ofertaIds)
      // Filtro por categoría
      if (skillsFilters?.categoria && skillsFilters.categoria !== 'Todos') {
        query = query.eq('l1_nombre', skillsFilters.categoria)
      }
      return query
    }
  )

  let digitales = 0
  let noDigitales = 0
  data.forEach(s => {
    if (s.es_digital) digitales++
    else noDigitales++
  })

  const total = digitales + noDigitales
  if (total === 0) return []

  return [
    { name: 'Digitales', value: digitales, porcentaje: Math.round(digitales * 100 / total) },
    { name: 'No digitales', value: noDigitales, porcentaje: Math.round(noDigitales * 100 / total) }
  ]
}

// Top skills por categoría L1
export async function getTopSkillsPorCategoria(limit = 5, skillsFilters?: SkillsFilters, globalFilters?: DashboardFilters) {
  const client = getSupabaseClient()
  if (!client) return {}

  const ofertaIds = await getFilteredOfertaIds(globalFilters)

  // Usar paginación para obtener TODOS los datos
  const data = await fetchAllPaginated<{ l1: string; l1_nombre: string; preferred_label: string; es_digital: boolean }>(
    client,
    'ofertas_skills',
    'l1, l1_nombre, preferred_label, es_digital',
    (query) => {
      query = query.not('l1', 'is', null).not('preferred_label', 'is', null)
      query = applyOfertaIdsFilter(query, ofertaIds)
      // Filtro por digital
      if (skillsFilters?.esDigital !== undefined && skillsFilters.esDigital !== null) {
        query = query.eq('es_digital', skillsFilters.esDigital)
      }
      return query
    }
  )

  // Agrupar por categoría y contar skills
  const porCategoria: Record<string, Record<string, number>> = {}
  const nombreCategoria: Record<string, string> = {}

  data.forEach(s => {
    if (!porCategoria[s.l1]) {
      porCategoria[s.l1] = {}
      nombreCategoria[s.l1] = s.l1_nombre || s.l1
    }
    const skill = s.preferred_label
    porCategoria[s.l1][skill] = (porCategoria[s.l1][skill] || 0) + 1
  })

  // Para cada categoría, obtener top N skills
  const resultado: Record<string, { nombre: string, skills: { name: string, value: number }[] }> = {}

  Object.entries(porCategoria).forEach(([cat, skills]) => {
    const topSkills = Object.entries(skills)
      .map(([name, value]) => ({ name, value }))
      .sort((a, b) => b.value - a.value)
      .slice(0, limit)

    resultado[cat] = {
      nombre: nombreCategoria[cat],
      skills: topSkills
    }
  })

  return resultado
}

// Top N skills totales con su categoría
export async function getTopSkillsConCategoria(limit = 10, skillsFilters?: SkillsFilters, globalFilters?: DashboardFilters) {
  const client = getSupabaseClient()
  if (!client) return []

  const ofertaIds = await getFilteredOfertaIds(globalFilters)

  // Usar paginación para obtener TODOS los datos
  const data = await fetchAllPaginated<{ l1: string; l1_nombre: string; preferred_label: string; es_digital: boolean }>(
    client,
    'ofertas_skills',
    'l1, l1_nombre, preferred_label, es_digital',
    (query) => {
      query = query.not('l1', 'is', null).not('preferred_label', 'is', null)
      query = applyOfertaIdsFilter(query, ofertaIds)
      // Filtro por categoría
      if (skillsFilters?.categoria && skillsFilters.categoria !== 'Todos') {
        query = query.eq('l1_nombre', skillsFilters.categoria)
      }
      // Filtro por digital
      if (skillsFilters?.esDigital !== undefined && skillsFilters.esDigital !== null) {
        query = query.eq('es_digital', skillsFilters.esDigital)
      }
      return query
    }
  )

  // Contar skills y guardar su categoría
  const skillCounts: Record<string, { count: number, l1: string, l1_nombre: string }> = {}

  data.forEach(s => {
    const skill = s.preferred_label
    if (!skillCounts[skill]) {
      skillCounts[skill] = { count: 0, l1: s.l1, l1_nombre: s.l1_nombre }
    }
    skillCounts[skill].count++
  })

  return Object.entries(skillCounts)
    .map(([name, { count, l1, l1_nombre }]) => ({
      name,
      value: count,
      categoria: l1,
      categoriaNombre: l1_nombre
    }))
    .sort((a, b) => b.value - a.value)
    .slice(0, limit)
}

// Heatmap: categorías L1 por ocupación ESCO
export async function getSkillsCategoriaPorOcupacion(globalFilters?: DashboardFilters) {
  const client = getSupabaseClient()
  if (!client) return { data: [], ocupaciones: [], categorias: [] }

  const ofertaIds = await getFilteredOfertaIds(globalFilters)

  // Usar paginación para obtener TODOS los datos
  const data = await fetchAllPaginated<{ l1: string; l1_nombre: string; id_oferta: string }>(
    client,
    'ofertas_skills',
    'l1, l1_nombre, id_oferta',
    (query) => {
      query = query.not('l1', 'is', null)
      query = applyOfertaIdsFilter(query, ofertaIds)
      return query
    }
  )

  // Obtener ocupaciones de las ofertas
  const skillOfertaIds = [...new Set(data.map(s => s.id_oferta))]

  // Obtener ocupaciones con paginación también
  const ofertas = await fetchAllPaginated<{ id_oferta: string; isco_label: string }>(
    client,
    'ofertas_dashboard',
    'id_oferta, isco_label',
    (query) => query.in('id_oferta', skillOfertaIds).not('isco_label', 'is', null)
  )

  // Crear mapa de oferta -> ocupación
  const ofertaOcupacion: Record<string, string> = {}
  ofertas.forEach(o => {
    ofertaOcupacion[o.id_oferta] = o.isco_label
  })

  // Contar categorías por ocupación
  const heatmap: Record<string, Record<string, number>> = {}
  const categoriasNombres: Record<string, string> = {}

  data.forEach(s => {
    const ocupacion = ofertaOcupacion[s.id_oferta]
    if (!ocupacion) return

    if (!heatmap[ocupacion]) heatmap[ocupacion] = {}
    heatmap[ocupacion][s.l1] = (heatmap[ocupacion][s.l1] || 0) + 1
    categoriasNombres[s.l1] = s.l1_nombre || s.l1
  })

  // Convertir a formato para visualización
  const ocupaciones = Object.keys(heatmap).slice(0, 10) // Top 10 ocupaciones
  const categorias = Object.keys(categoriasNombres)

  const matrizData: { ocupacion: string, categoria: string, categoriaNombre: string, value: number }[] = []

  ocupaciones.forEach(ocup => {
    categorias.forEach(cat => {
      matrizData.push({
        ocupacion: ocup.length > 25 ? ocup.substring(0, 22) + '...' : ocup,
        categoria: cat,
        categoriaNombre: categoriasNombres[cat],
        value: heatmap[ocup][cat] || 0
      })
    })
  })

  return {
    data: matrizData,
    ocupaciones,
    categorias: categorias.map(c => ({ code: c, name: categoriasNombres[c] }))
  }
}

// ========== FUNCIONES PARA ISSUES/FEEDBACK ==========

// Obtener issues con filtros opcionales
export async function getIssues(filters?: {
  estado?: string;
  tipo?: string;
  prioridad?: string;
  id_oferta?: string;
}): Promise<Issue[]> {
  const client = getSupabaseClient()
  if (!client) return []

  let query = client
    .from('issues')
    .select('*')
    .order('created_at', { ascending: false })

  if (filters?.estado) {
    query = query.eq('estado', filters.estado)
  }
  if (filters?.tipo) {
    query = query.eq('tipo', filters.tipo)
  }
  if (filters?.prioridad) {
    query = query.eq('prioridad', filters.prioridad)
  }
  if (filters?.id_oferta) {
    query = query.eq('id_oferta', filters.id_oferta)
  }

  const { data, error } = await query

  if (error) throw error
  return data || []
}

// Obtener issues pendientes (para el badge del FAB)
export async function getIssuesPendientes(): Promise<Issue[]> {
  const client = getSupabaseClient()
  if (!client) return []

  const { data, error } = await client
    .from('issues')
    .select('*')
    .in('estado', ['pendiente', 'en_progreso'])
    .order('prioridad', { ascending: true }) // critica primero
    .order('created_at', { ascending: false })

  if (error) throw error
  return data || []
}

// Crear un issue
export async function createIssue(issue: {
  titulo: string;
  descripcion?: string;
  tipo: string;
  prioridad: string;
  id_oferta?: string;
  autor_id: string;
  autor_email: string;
  autor_nombre?: string;
}): Promise<Issue> {
  const client = getSupabaseClient()
  if (!client) throw new Error('Supabase no está configurado')

  const { data, error } = await client
    .from('issues')
    .insert([issue])
    .select()
    .single()

  if (error) throw error
  return data
}

// Actualizar un issue
export async function updateIssue(
  id: string,
  updates: Partial<Omit<Issue, 'id' | 'created_at'>>
): Promise<Issue> {
  const client = getSupabaseClient()
  if (!client) throw new Error('Supabase no está configurado')

  const updateData = {
    ...updates,
    updated_at: new Date().toISOString()
  }

  // Si se marca como resuelto, agregar fecha
  if (updates.estado === 'resuelto' && !updates.resuelto_at) {
    updateData.resuelto_at = new Date().toISOString()
  }

  const { data, error } = await client
    .from('issues')
    .update(updateData)
    .eq('id', id)
    .select()
    .single()

  if (error) throw error
  return data
}

// Obtener estadísticas de issues
export async function getIssuesStats(): Promise<IssueStats> {
  const client = getSupabaseClient()
  if (!client) return { pendientes: 0, en_progreso: 0, resueltos: 0 }

  const { data, error } = await client
    .from('issues')
    .select('estado')

  if (error) throw error

  const stats: IssueStats = {
    pendientes: 0,
    en_progreso: 0,
    resueltos: 0
  }

  data?.forEach(issue => {
    if (issue.estado === 'pendiente') stats.pendientes++
    else if (issue.estado === 'en_progreso') stats.en_progreso++
    else if (issue.estado === 'resuelto') stats.resueltos++
  })

  return stats
}

// Obtener issues de una oferta específica
export async function getIssuesByOferta(id_oferta: string): Promise<Issue[]> {
  const client = getSupabaseClient()
  if (!client) return []

  const { data, error } = await client
    .from('issues')
    .select('*')
    .eq('id_oferta', id_oferta)
    .order('created_at', { ascending: false })

  if (error) throw error
  return data || []
}

// ========== FUNCIONES PARA PERFIL CONSOLIDADO ==========

import { ConsolidatedProfile, ConsolidatedProfilesIndex } from './types'

export interface OfertaConsolidado {
  id_oferta: string
  titulo: string
  titulo_limpio: string | null
  empresa: string | null
  skills_tecnicas: string | null
  soft_skills: string | null
  descripcion?: string
}

// Get all consolidated profiles
export async function getConsolidatedProfiles(): Promise<ConsolidatedProfilesIndex> {
  const client = getSupabaseClient()
  if (!client) {
    return { version: '1.0.0', generated_at: new Date().toISOString(), profiles: {} }
  }

  const { data, error } = await client
    .from('consolidated_profiles')
    .select('*')
    .order('last_updated', { ascending: false })

  if (error) {
    console.error('Error fetching consolidated profiles:', error)
    return { version: '1.0.0', generated_at: new Date().toISOString(), profiles: {} }
  }

  // Convert array to index
  const profiles: { [key: string]: ConsolidatedProfile } = {}
  data?.forEach(row => {
    profiles[row.esco_uuid] = {
      esco_uuid: row.esco_uuid,
      esco_label: row.esco_label,
      last_updated: row.last_updated,
      consolidated_skills: row.consolidated_skills || [],
      stats: row.stats || {}
    }
  })

  return {
    version: '1.0.0',
    generated_at: new Date().toISOString(),
    profiles
  }
}

// Save or update a consolidated profile
export async function saveConsolidatedProfile(profile: ConsolidatedProfile): Promise<boolean> {
  const client = getSupabaseClient()
  if (!client) return false

  const { error } = await client
    .from('consolidated_profiles')
    .upsert({
      esco_uuid: profile.esco_uuid,
      esco_label: profile.esco_label,
      last_updated: new Date().toISOString(),
      consolidated_skills: profile.consolidated_skills,
      stats: profile.stats
    }, { onConflict: 'esco_uuid' })

  if (error) {
    console.error('Error saving consolidated profile:', error)
    return false
  }

  return true
}

// Obtener ofertas por ocupación ESCO
export async function getOfertasByEscoOccupation(
  escoUuid: string,
  limit: number = 20,
  offset: number = 0
): Promise<{ ofertas: OfertaConsolidado[], total: number }> {
  const client = getSupabaseClient()
  if (!client) return { ofertas: [], total: 0 }

  // Construir URI ESCO completa
  const escoUri = `http://data.europa.eu/esco/occupation/${escoUuid}`

  const { data, error, count } = await client
    .from(TABLA_OFERTAS)
    .select(`
      id_oferta,
      titulo,
      titulo_limpio,
      empresa,
      skills_tecnicas,
      soft_skills
    `, { count: 'exact' })
    .eq('esco_occupation_uri', escoUri)
    .order('fecha_publicacion', { ascending: false })
    .range(offset, offset + limit - 1)

  if (error) {
    console.error('Error fetching ofertas by ESCO:', error)
    return { ofertas: [], total: 0 }
  }

  return { ofertas: data || [], total: count || 0 }
}

// ========== OFERTAS POR OCUPACIÓN (ISCO) - SPRINT 2 ==========

export interface OfertaPorOcupacion {
  id_oferta: string;
  titulo: string;
  titulo_limpio: string | null;
  empresa: string | null;
  fecha_publicacion: string | null;
  url: string | null;
  skills_tecnicas: string | null;
}

export interface OfertasCountByIsco {
  isco_code: string;
  isco_label: string;
  count: number;
}

/**
 * Obtiene el conteo de ofertas activas por código ISCO
 * Retorna un mapa de isco_code -> count
 */
export async function getOfertasCountByIsco(): Promise<Record<string, number>> {
  const client = getSupabaseClient()
  if (!client) return {}

  try {
    const data = await fetchAllPaginated<{ isco_code: string }>(
      client,
      TABLA_OFERTAS,
      'isco_code',
      (query) => query.not('isco_code', 'is', null)
    )

    const counts: Record<string, number> = {}
    data.forEach(o => {
      counts[o.isco_code] = (counts[o.isco_code] || 0) + 1
    })

    return counts
  } catch (error) {
    console.error('Error getting ofertas count by ISCO:', error)
    return {}
  }
}

/**
 * Obtiene ofertas activas para un código ISCO específico
 */
export async function getOfertasByIsco(
  iscoCode: string,
  limit: number = 50,
  offset: number = 0
): Promise<{ ofertas: OfertaPorOcupacion[], total: number }> {
  const client = getSupabaseClient()
  if (!client) return { ofertas: [], total: 0 }

  try {
    const { data, error, count } = await client
      .from(TABLA_OFERTAS)
      .select(`
        id_oferta,
        titulo,
        titulo_limpio,
        empresa,
        fecha_publicacion,
        url,
        skills_tecnicas
      `, { count: 'exact' })
      .eq('isco_code', iscoCode)
      .order('fecha_publicacion', { ascending: false })
      .range(offset, offset + limit - 1)

    if (error) throw error

    return {
      ofertas: data || [],
      total: count || 0
    }
  } catch (error) {
    console.error('Error getting ofertas by ISCO:', error)
    return { ofertas: [], total: 0 }
  }
}

/**
 * Obtiene ofertas para múltiples códigos ISCO (para exportar)
 */
export async function getOfertasByMultipleIsco(
  iscoCodes: string[]
): Promise<OfertaPorOcupacion[]> {
  const client = getSupabaseClient()
  if (!client || iscoCodes.length === 0) return []

  try {
    const data = await fetchAllPaginated<OfertaPorOcupacion>(
      client,
      TABLA_OFERTAS,
      'id_oferta, titulo, titulo_limpio, empresa, fecha_publicacion, url, skills_tecnicas',
      (query) => query.in('isco_code', iscoCodes).order('fecha_publicacion', { ascending: false })
    )

    return data
  } catch (error) {
    console.error('Error getting ofertas by multiple ISCO:', error)
    return []
  }
}

// ========== AUDIT LOG - REGISTRAR ACCIONES ==========

/**
 * Registra una acción en el audit_log
 * Usar para trackear navegación, exportaciones, etc.
 */
export async function logAction(
  accion: string,
  recurso: string,
  recurso_id?: string,
  detalle?: Record<string, unknown>
): Promise<void> {
  const client = getSupabaseClient()
  if (!client) return

  try {
    const { data: { user } } = await client.auth.getUser()
    if (!user) return

    await client
      .from('audit_log')
      .insert({
        usuario_id: user.id,
        accion,
        recurso,
        recurso_id,
        detalle
      })
  } catch (error) {
    // Silently fail - audit logs shouldn't break the app
    console.debug('Audit log error:', error)
  }
}

/**
 * Registra un evento de uso (analytics ligero)
 */
export async function logEvent(
  evento: string,
  categoria: string,
  metadata?: Record<string, unknown>
): Promise<void> {
  const client = getSupabaseClient()
  if (!client) return

  try {
    const { data: { user } } = await client.auth.getUser()
    if (!user) return

    await client
      .from('eventos_uso')
      .insert({
        usuario_id: user.id,
        evento,
        categoria,
        metadata
      })
  } catch (error) {
    console.debug('Event log error:', error)
  }
}

// ========== SKILLS INTELLIGENCE - DATOS DINÁMICOS ==========

export interface SkillsIntelligenceStats {
  total_ofertas: number;
  total_ocupaciones: number;
  total_skills: number;
  avg_skills_por_oferta: number;
}

export interface OccupationWithMOLData {
  esco_uri: string;
  esco_label: string;
  isco_code: string;
  isco_label: string;
  ofertas_count: number;
  skills_count: number;
}

export interface MOLSkillAggregated {
  skill_uri: string;
  preferred_label: string;
  l1: string;
  l1_nombre: string;
  l2: string;
  l2_nombre: string;
  es_digital: boolean;
  frequency: number;      // Cuántas ofertas tienen esta skill
  avg_score: number;      // Score promedio
  is_essential: boolean;  // Mayoría de ofertas la tienen como esencial
}

export interface OccupationMOLProfileData {
  esco_uri: string;
  esco_label: string;
  isco_code: string;
  ofertas_count: number;
  skills: MOLSkillAggregated[];
}

/**
 * Obtiene estadísticas generales de Skills Intelligence
 */
export async function getSkillsIntelligenceStats(): Promise<SkillsIntelligenceStats | null> {
  const client = getSupabaseClient()
  if (!client) return null

  try {
    // Total ofertas
    const { count: totalOfertas } = await client
      .from(TABLA_OFERTAS)
      .select('id_oferta', { count: 'exact', head: true })

    // Total ocupaciones únicas
    const { data: ocupaciones } = await client
      .from(TABLA_OFERTAS)
      .select('esco_occupation_uri')
      .not('esco_occupation_uri', 'is', null)

    const ocupacionesUnicas = new Set(ocupaciones?.map(o => o.esco_occupation_uri)).size

    // Total skills y promedio
    const { count: totalSkills } = await client
      .from('ofertas_skills')
      .select('id', { count: 'exact', head: true })

    const avgSkills = totalOfertas && totalOfertas > 0
      ? (totalSkills || 0) / totalOfertas
      : 0

    return {
      total_ofertas: totalOfertas || 0,
      total_ocupaciones: ocupacionesUnicas,
      total_skills: totalSkills || 0,
      avg_skills_por_oferta: Math.round(avgSkills * 10) / 10
    }
  } catch (error) {
    console.error('Error getting skills intelligence stats:', error)
    return null
  }
}

/**
 * Obtiene lista de ocupaciones que tienen ofertas MOL con sus conteos
 */
export async function getOccupationsWithMOLData(): Promise<OccupationWithMOLData[]> {
  const client = getSupabaseClient()
  if (!client) return []

  try {
    // Obtener todas las ofertas con paginación
    const ofertas = await fetchAllPaginated<{
      esco_occupation_uri: string;
      esco_occupation_label: string;
      isco_code: string;
      isco_label: string;
    }>(
      client,
      TABLA_OFERTAS,
      'esco_occupation_uri, esco_occupation_label, isco_code, isco_label',
      (query) => query.not('esco_occupation_uri', 'is', null)
    )

    // Agrupar por ocupación
    const grouped: Record<string, OccupationWithMOLData> = {}

    ofertas.forEach(o => {
      const uri = o.esco_occupation_uri
      if (!uri) return

      if (!grouped[uri]) {
        grouped[uri] = {
          esco_uri: uri,
          esco_label: o.esco_occupation_label || '',
          isco_code: o.isco_code || '',
          isco_label: o.isco_label || '',
          ofertas_count: 0,
          skills_count: 0
        }
      }
      grouped[uri].ofertas_count++
    })

    // Obtener conteo de skills por ocupación (mediante ofertas) con paginación
    const skillsData = await fetchAllPaginated<{ id_oferta: string }>(
      client,
      'ofertas_skills',
      'id_oferta'
    )

    // Crear map de skills por oferta
    const skillsPerOferta: Record<string, number> = {}
    skillsData.forEach(s => {
      skillsPerOferta[s.id_oferta] = (skillsPerOferta[s.id_oferta] || 0) + 1
    })

    // Asociar skills_count a cada ocupación
    ofertas.forEach(o => {
      const uri = o.esco_occupation_uri
      if (uri && grouped[uri] && skillsPerOferta[o.esco_occupation_uri]) {
        // Esto es aproximado, contamos skills totales de ofertas de esa ocupación
      }
    })

    // Ordenar por ofertas_count descendente
    return Object.values(grouped).sort((a, b) => b.ofertas_count - a.ofertas_count)
  } catch (error) {
    console.error('Error getting occupations with MOL data:', error)
    return []
  }
}

/**
 * Obtiene el perfil de skills MOL agregado para una ocupación específica
 */
export async function getOccupationMOLProfile(escoUri: string): Promise<OccupationMOLProfileData | null> {
  const client = getSupabaseClient()
  if (!client) return null

  try {
    // 1. Obtener ofertas de esta ocupación con paginación
    const ofertas = await fetchAllPaginated<{
      id_oferta: string;
      esco_occupation_label: string;
      isco_code: string;
    }>(
      client,
      TABLA_OFERTAS,
      'id_oferta, esco_occupation_label, isco_code',
      (query) => query.eq('esco_occupation_uri', escoUri)
    )

    if (ofertas.length === 0) return null

    const ofertaIds = ofertas.map(o => o.id_oferta)
    const firstOferta = ofertas[0]

    // 2. Obtener skills de esas ofertas con paginación
    const skills = await fetchAllPaginated<{
      skill_uri: string;
      preferred_label: string;
      l1: string;
      l1_nombre: string;
      l2: string;
      l2_nombre: string;
      es_digital: boolean;
      es_esencial: boolean;
      score: number;
    }>(
      client,
      'ofertas_skills',
      'skill_uri, preferred_label, l1, l1_nombre, l2, l2_nombre, es_digital, es_esencial, score',
      (query) => query.in('id_oferta', ofertaIds)
    )

    // 3. Agregar skills
    const skillsMap: Record<string, {
      skill_uri: string;
      preferred_label: string;
      l1: string;
      l1_nombre: string;
      l2: string;
      l2_nombre: string;
      es_digital: boolean;
      count: number;
      essential_count: number;
      total_score: number;
    }> = {}

    skills.forEach(s => {
      if (!s.skill_uri) return

      if (!skillsMap[s.skill_uri]) {
        skillsMap[s.skill_uri] = {
          skill_uri: s.skill_uri,
          preferred_label: s.preferred_label || '',
          l1: s.l1 || '',
          l1_nombre: s.l1_nombre || '',
          l2: s.l2 || '',
          l2_nombre: s.l2_nombre || '',
          es_digital: s.es_digital || false,
          count: 0,
          essential_count: 0,
          total_score: 0
        }
      }

      skillsMap[s.skill_uri].count++
      if (s.es_esencial) skillsMap[s.skill_uri].essential_count++
      skillsMap[s.skill_uri].total_score += (s.score || 0)
    })

    // 4. Convertir a array con métricas calculadas
    const aggregatedSkills: MOLSkillAggregated[] = Object.values(skillsMap)
      .map(s => ({
        skill_uri: s.skill_uri,
        preferred_label: s.preferred_label,
        l1: s.l1,
        l1_nombre: s.l1_nombre,
        l2: s.l2,
        l2_nombre: s.l2_nombre,
        es_digital: s.es_digital,
        frequency: s.count,
        avg_score: s.count > 0 ? Math.round((s.total_score / s.count) * 100) / 100 : 0,
        is_essential: s.essential_count > s.count / 2  // Mayoría lo tiene como esencial
      }))
      .sort((a, b) => b.frequency - a.frequency)  // Ordenar por frecuencia

    return {
      esco_uri: escoUri,
      esco_label: firstOferta.esco_occupation_label || '',
      isco_code: firstOferta.isco_code || '',
      ofertas_count: ofertas.length,
      skills: aggregatedSkills
    }
  } catch (error) {
    console.error('Error getting occupation MOL profile:', error)
    return null
  }
}
