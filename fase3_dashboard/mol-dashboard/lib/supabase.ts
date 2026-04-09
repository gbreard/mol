import { createClient, SupabaseClient } from '@supabase/supabase-js'
import { DashboardFilters, Issue, IssueStats, ConsolidatedProfile, ConsolidatedProfilesIndex, OfertaValidacion, OfertaSkillValidacion, ValidationFiltersState, ValidationStats, ValidacionHumana } from './types'

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

// ============================================
// FILTER BUILDER — convierte DashboardFilters a JSONB para RPCs
// ============================================

export function buildRPCFilters(filters?: DashboardFilters): Record<string, unknown> {
  if (!filters) return {}
  const f: Record<string, unknown> = {}

  if (filters.provincia && provinciaMap[filters.provincia]) {
    f.provincia = provinciaMap[filters.provincia]
  }
  if (filters.fechaDesde) {
    f.fecha_desde = filters.fechaDesde.toISOString().split('T')[0]
  }
  if (filters.fechaHasta) {
    f.fecha_hasta = filters.fechaHasta.toISOString().split('T')[0]
  }
  if (filters.localidad?.length > 0) {
    f.localidad = filters.localidad
  }
  if (filters.seniority?.length > 0) {
    f.seniority = filters.seniority
  }
  if (filters.modalidad?.length > 0) {
    f.modalidad = filters.modalidad
  }
  if (filters.sector?.length > 0) {
    f.sector = filters.sector
  }
  if (filters.ocupacionesSeleccionadas?.length > 0) {
    f.ocupaciones = filters.ocupacionesSeleccionadas
  }
  if (filters.permanencia?.length > 0) {
    f.permanencia = filters.permanencia
  }
  if (filters.nivelEducativo?.length > 0) {
    f.nivel_educativo = filters.nivelEducativo
  }
  if (filters.experiencia) {
    f.experiencia = filters.experiencia
  }
  if (filters.jornada) {
    f.jornada = filters.jornada
  }

  return f
}

// Helper para aplicar filtros a una query
function applyFilters(query: any, filters?: DashboardFilters) {
  if (!filters) return query

  // Filtro por provincia
  if (filters.provincia && provinciaMap[filters.provincia]) {
    query = query.eq('provincia', provinciaMap[filters.provincia])
  }

  // Filtro por localidad (multi-select)
  if (filters.localidad?.length > 0) {
    query = query.in('localidad', filters.localidad)
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

  // Filtro por nivel educativo (multi-select)
  if (filters.nivelEducativo?.length > 0) {
    query = query.in('nivel_educativo', filters.nivelEducativo)
  }

  // Filtro por experiencia (rangos)
  if (filters.experiencia) {
    switch (filters.experiencia) {
      case 'sin_experiencia':
        query = query.eq('experiencia_min_anios', 0)
        break
      case '1_2_anios':
        query = query.gte('experiencia_min_anios', 1).lte('experiencia_min_anios', 2)
        break
      case '3_5_anios':
        query = query.gte('experiencia_min_anios', 3).lte('experiencia_min_anios', 5)
        break
      case '5_mas':
        query = query.gt('experiencia_min_anios', 5)
        break
    }
  }

  // Filtro por seniority (multi-select)
  if (filters.seniority?.length > 0) {
    query = query.in('nivel_seniority', filters.seniority)
  }

  // Filtro por modalidad (multi-select)
  if (filters.modalidad?.length > 0) {
    query = query.in('modalidad', filters.modalidad)
  }

  // Filtro por permanencia
  if (filters.permanencia && filters.permanencia.length > 0) {
    query = query.in('categoria_permanencia', filters.permanencia)
  }

  // Filtro por jornada
  if (filters.jornada) {
    const jornadaMap: Record<string, string> = {
      'full_time': 'full-time',
      'part_time': 'part-time',
      'por_horas': 'por horas'
    }
    query = query.eq('jornada_laboral', jornadaMap[filters.jornada] || filters.jornada)
  }

  // Filtro por sector CLAE (multi-select)
  if (filters.sector?.length > 0) {
    query = query.in('clae_descripcion_seccion', filters.sector)
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

// ============================================
// PANORAMA — single RPC replaces 4 legacy functions
// ============================================

export interface PanoramaData {
  kpis: { total_ofertas: number; ocupaciones_distintas: number; empresas_activas: number; provincias: number }
  top_ocupaciones: { isco_code: string; ocupacion: string; cantidad: number }[]
  provincias: { jurisdiccion: string; cantidad: number; porcentaje: number }[]
  modalidad: { modalidad: string; cantidad: number }[]
}

export async function getPanoramaData(filters?: DashboardFilters): Promise<PanoramaData> {
  const client = getSupabaseClient()
  if (!client) return {
    kpis: { total_ofertas: 0, ocupaciones_distintas: 0, empresas_activas: 0, provincias: 0 },
    top_ocupaciones: [], provincias: [], modalidad: []
  }

  const { data, error } = await client.rpc('get_panorama', { p_filters: buildRPCFilters(filters) })
  if (error) {
    console.error('Error en get_panorama RPC:', error)
    return {
      kpis: { total_ofertas: 0, ocupaciones_distintas: 0, empresas_activas: 0, provincias: 0 },
      top_ocupaciones: [], provincias: [], modalidad: []
    }
  }

  return data as PanoramaData
}

// Backward-compatible wrapper
export async function getKPIs(filters?: DashboardFilters) {
  const panorama = await getPanoramaData(filters)
  return {
    totalOfertas: panorama.kpis.total_ofertas,
    ocupacionesDistintas: panorama.kpis.ocupaciones_distintas,
    empresasActivas: panorama.kpis.empresas_activas,
    provincias: panorama.kpis.provincias,
  }
}

export async function getOfertasPorProvincia(filters?: DashboardFilters) {
  const panorama = await getPanoramaData(filters)
  return panorama.provincias
}

export async function getTopOcupaciones(limit = 10, filters?: DashboardFilters) {
  const panorama = await getPanoramaData(filters)
  return panorama.top_ocupaciones.slice(0, limit)
}

export async function getOfertasPorModalidad(filters?: DashboardFilters) {
  const panorama = await getPanoramaData(filters)
  return panorama.modalidad
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

// Backward-compatible: top skills técnicas (uses skills resumen RPC)
export async function getTopSkillsTecnicas(limit = 20, filters?: DashboardFilters) {
  const resumen = await getSkillsResumen(filters)
  return resumen.top_skills.slice(0, limit).map(s => ({ name: s.name, value: s.value }))
}

// getTopSoftSkills — legacy, kept for backward compat
export async function getTopSoftSkills(limit = 20, _filters?: DashboardFilters) {
  // Soft skills are not in ofertas_skills table, return empty
  // This was always a text-parsing function with limited utility
  return [] as { name: string; value: number }[]
}

// ========== FUNCIONES PARA SIDEBAR ==========

// Total de ofertas — via panorama RPC
export async function getTotalOfertas(filters?: DashboardFilters): Promise<number> {
  const panorama = await getPanoramaData(filters)
  return panorama.kpis.total_ofertas
}

// Evolución semanal de ofertas (últimas N semanas)
export interface EvolucionSemanal {
  label: string;       // "27/01 - 02/02"
  ofertas: number;
  weekStart: string;   // ISO date for sorting
}

// Evolución por períodos comparativos (BarChart)
export interface PeriodoEvolucion {
  label: string            // "27/01 - 02/02" o "Ene 2026"
  ofertas: number
  fechaDesde: string       // ISO date
  fechaHasta: string       // ISO date
  esPeriodoActual: boolean
}

// getEvolucionSemanal — deprecated, use getEvolucionPeriodos instead
export async function getEvolucionSemanal(filters?: DashboardFilters): Promise<EvolucionSemanal[]> {
  const periodos = await getEvolucionPeriodos(filters, 0)
  return periodos.map(p => ({
    label: p.label,
    ofertas: p.ofertas,
    weekStart: p.fechaDesde,
  }))
}

// Helper: aplicar todos los filtros EXCEPTO fechas
function applyFiltersWithoutDates(query: any, filters?: DashboardFilters) {
  if (!filters) return query

  if (filters.provincia && provinciaMap[filters.provincia]) {
    query = query.eq('provincia', provinciaMap[filters.provincia])
  }
  if (filters.localidad?.length > 0) {
    query = query.in('localidad', filters.localidad)
  }
  if (filters.ocupacionesSeleccionadas && filters.ocupacionesSeleccionadas.length > 0) {
    query = query.in('isco_code', filters.ocupacionesSeleccionadas)
  }
  if (filters.nivelEducativo?.length > 0) {
    query = query.in('nivel_educativo', filters.nivelEducativo)
  }
  if (filters.experiencia) {
    switch (filters.experiencia) {
      case 'sin_experiencia':
        query = query.eq('experiencia_min_anios', 0)
        break
      case '1_2_anios':
        query = query.gte('experiencia_min_anios', 1).lte('experiencia_min_anios', 2)
        break
      case '3_5_anios':
        query = query.gte('experiencia_min_anios', 3).lte('experiencia_min_anios', 5)
        break
      case '5_mas':
        query = query.gt('experiencia_min_anios', 5)
        break
    }
  }
  if (filters.seniority?.length > 0) {
    query = query.in('nivel_seniority', filters.seniority)
  }
  if (filters.modalidad?.length > 0) {
    query = query.in('modalidad', filters.modalidad)
  }
  if (filters.permanencia && filters.permanencia.length > 0) {
    query = query.in('categoria_permanencia', filters.permanencia)
  }
  if (filters.jornada) {
    const jornadaMap: Record<string, string> = {
      'full_time': 'full-time',
      'part_time': 'part-time',
      'por_horas': 'por horas'
    }
    query = query.eq('jornada_laboral', jornadaMap[filters.jornada] || filters.jornada)
  }
  if (filters.sector?.length > 0) {
    query = query.in('clae_descripcion_seccion', filters.sector)
  }

  return query
}

/**
 * Evolución por períodos — ahora via RPC get_evolucion
 */
export async function getEvolucionPeriodos(
  filters?: DashboardFilters,
  cantidadPeriodos: number = 13
): Promise<PeriodoEvolucion[]> {
  const client = getSupabaseClient()
  if (!client) return []

  const { data, error } = await client.rpc('get_evolucion', {
    p_filters: buildRPCFilters(filters),
    p_periodos: cantidadPeriodos || 52
  })

  if (error) {
    console.error('Error en get_evolucion RPC:', error)
    return []
  }

  const rpcData = data as { periodos: Array<{
    fecha_desde: string; fecha_hasta: string; ofertas: number;
    es_periodo_actual: boolean; label: string
  }>; modo: string }

  // Map RPC response to PeriodoEvolucion format
  const result = (rpcData?.periodos || []).map(p => ({
    label: p.label,
    ofertas: p.ofertas,
    fechaDesde: p.fecha_desde,
    fechaHasta: p.fecha_hasta,
    esPeriodoActual: p.es_periodo_actual,
  }))

  // If "Todo" (cantidadPeriodos=0), filter out empty leading periods
  if (cantidadPeriodos === 0) {
    const first = result.findIndex(p => p.ofertas > 0)
    return first > 0 ? result.slice(first) : result
  }

  return result
}

// Distribución de ofertas por localidad (para una provincia específica)
export async function getOfertasPorLocalidad(filters?: DashboardFilters) {
  const client = getSupabaseClient()
  if (!client) return []

  const data = await fetchAllPaginated<{ localidad: string }>(
    client,
    TABLA_OFERTAS,
    'localidad',
    (query) => applyFilters(query, filters)
  )

  const counts: Record<string, number> = {}
  data.forEach(o => {
    const loc = o.localidad || 'No especificado'
    counts[loc] = (counts[loc] || 0) + 1
  })

  const total = data.length || 1
  return Object.entries(counts)
    .map(([localidad, cantidad]) => ({
      jurisdiccion: localidad,
      cantidad,
      porcentaje: Math.round(cantidad * 1000 / total) / 10
    }))
    .sort((a, b) => b.cantidad - a.cantidad)
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

// Localidades agrupadas por departamento (para multi-select en Sidebar)
export interface LocalidadConDepartamento {
  localidad: string
  departamento: string | null
  count: number
}

export interface DepartamentoGroup {
  departamento: string
  localidades: { localidad: string; count: number }[]
  totalCount: number
}

export async function getLocalidadesGroupedByDepartamento(provinciaKey: string, filters?: DashboardFilters): Promise<DepartamentoGroup[]> {
  const client = getSupabaseClient()
  if (!client) return []

  const provinciaName = provinciaMap[provinciaKey]
  if (!provinciaName) return []

  const data = await fetchAllPaginated<{ localidad: string; departamento: string | null }>(
    client,
    TABLA_OFERTAS,
    'localidad, departamento',
    (query) => {
      query = query.eq('provincia', provinciaName).not('localidad', 'is', null)
      // Aplicar filtros activos (excepto provincia y localidad) para que los counts
      // sean consistentes con lo que muestra el dashboard
      if (filters) {
        if (filters.fechaDesde) {
          query = query.gte('fecha_publicacion', filters.fechaDesde.toISOString().split('T')[0])
        }
        if (filters.fechaHasta) {
          query = query.lte('fecha_publicacion', filters.fechaHasta.toISOString().split('T')[0])
        }
        if (filters.ocupacionesSeleccionadas?.length > 0) {
          query = query.in('isco_code', filters.ocupacionesSeleccionadas)
        }
        if (filters.permanencia?.length > 0) {
          query = query.in('categoria_permanencia', filters.permanencia)
        }
        if (filters.nivelEducativo?.length > 0) {
          query = query.in('nivel_educativo', filters.nivelEducativo)
        }
        if (filters.seniority?.length > 0) {
          query = query.in('nivel_seniority', filters.seniority)
        }
        if (filters.modalidad?.length > 0) {
          query = query.in('modalidad', filters.modalidad)
        }
      }
      return query
    }
  )

  // Contar por localidad y agrupar por departamento
  const locCounts: Record<string, { departamento: string | null; count: number }> = {}
  data.forEach(d => {
    if (!d.localidad) return
    if (!locCounts[d.localidad]) {
      locCounts[d.localidad] = { departamento: d.departamento, count: 0 }
    }
    locCounts[d.localidad].count++
  })

  // Agrupar por departamento
  const deptGroups: Record<string, { localidades: { localidad: string; count: number }[]; totalCount: number }> = {}

  Object.entries(locCounts).forEach(([localidad, { departamento, count }]) => {
    const dept = departamento || 'Sin clasificar'
    if (!deptGroups[dept]) {
      deptGroups[dept] = { localidades: [], totalCount: 0 }
    }
    deptGroups[dept].localidades.push({ localidad, count })
    deptGroups[dept].totalCount += count
  })

  // Ordenar: departamentos por cantidad desc, localidades dentro por cantidad desc
  return Object.entries(deptGroups)
    .map(([departamento, { localidades, totalCount }]) => ({
      departamento,
      localidades: localidades.sort((a, b) => b.count - a.count),
      totalCount,
    }))
    .sort((a, b) => b.totalCount - a.totalCount)
}

// Sectores CLAE para el Sidebar
export interface SectorCount {
  sector: string
  count: number
}

// ============================================
// SIDEBAR COUNTS — single RPC replaces getSectores + getOcupacionesTree
// ============================================

export interface SidebarCountsData {
  total_ofertas: number
  sectores: SectorCount[]
  ocupaciones_tree: Array<{
    major_group: string; count: number;
    children: Array<{ id: string; label: string; count: number }>
  }>
}

export async function getSidebarCounts(filters?: DashboardFilters): Promise<SidebarCountsData> {
  const client = getSupabaseClient()
  if (!client) return { total_ofertas: 0, sectores: [], ocupaciones_tree: [] }

  const { data, error } = await client.rpc('get_sidebar_counts', { p_filters: buildRPCFilters(filters) })

  if (error) {
    console.error('Error en get_sidebar_counts RPC:', error)
    return { total_ofertas: 0, sectores: [], ocupaciones_tree: [] }
  }

  return data as SidebarCountsData
}

// Backward-compatible wrapper
export async function getSectores(filters?: DashboardFilters): Promise<SectorCount[]> {
  const sidebar = await getSidebarCounts(filters)
  return sidebar.sectores
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
  const sidebar = await getSidebarCounts(filters)

  // Map RPC response to OcupacionTreeNode format
  return (sidebar.ocupaciones_tree || []).map(g => ({
    id: `isco-${g.major_group}`,
    label: ISCO_MAJOR_GROUPS[g.major_group] || `Grupo ${g.major_group}`,
    count: g.count,
    children: (g.children || []).map(c => ({
      id: c.id,
      label: c.label,
      count: c.count,
    }))
  }))
}

// Filtros locales para el tab de requerimientos
export interface RequerimientosFilters {
  educacion?: string;
  modalidad?: string;
}

// Funciones para obtener distribuciones de requerimientos — via RPC
export async function getDistribucionRequerimientos(filters?: DashboardFilters, _localFilters?: RequerimientosFilters) {
  const client = getSupabaseClient()
  if (!client) return { total: 0, educacion: [], experiencia: [], seniority: [], modalidad: [], genteCargo: [], jornada: [] }

  const { data, error } = await client.rpc('get_requerimientos', { p_filters: buildRPCFilters(filters) })

  if (error) {
    console.error('Error en get_requerimientos RPC:', error)
    return { total: 0, educacion: [], experiencia: [], seniority: [], modalidad: [], genteCargo: [], jornada: [] }
  }

  const rpc = data as {
    total: number
    educacion: Array<{ name: string; value: number; porcentaje: number; sort_order: number }>
    experiencia: Array<{ name: string; value: number; porcentaje: number; sort_order: number }>
    seniority: Array<{ name: string; value: number; porcentaje: number; sort_order: number }>
    modalidad: Array<{ name: string; value: number; porcentaje: number; sort_order: number }>
    jornada: Array<{ name: string; value: number; porcentaje: number; sort_order: number }>
    gente_cargo: Array<{ name: string; value: number; porcentaje: number }>
  }

  // Strip sort_order from response (internal to SQL)
  const strip = (arr: Array<{ name: string; value: number; porcentaje: number; sort_order?: number }>) =>
    (arr || []).map(({ name, value, porcentaje }) => ({ name, value, porcentaje }))

  return {
    total: rpc.total,
    educacion: strip(rpc.educacion),
    experiencia: strip(rpc.experiencia),
    seniority: strip(rpc.seniority),
    modalidad: strip(rpc.modalidad),
    genteCargo: strip(rpc.gente_cargo),
    jornada: strip(rpc.jornada),
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
    (filters.ocupacionesSeleccionadas && filters.ocupacionesSeleccionadas.length > 0) ||
    (filters.localidad && filters.localidad.length > 0) ||
    (filters.permanencia && filters.permanencia.length > 0) ||
    (filters.sector && filters.sector.length > 0) ||
    (filters.nivelEducativo && filters.nivelEducativo.length > 0) ||
    (filters.seniority && filters.seniority.length > 0) ||
    (filters.modalidad && filters.modalidad.length > 0) ||
    filters.experiencia || filters.jornada

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

// ============================================
// SKILLS RESUMEN — single RPC replaces 4 legacy functions
// ============================================

export interface SkillsResumenData {
  por_l1: Array<{ code: string; name: string; value: number; porcentaje: number }>
  digitales: { digitales: number; no_digitales: number; total: number }
  top_skills: Array<{ name: string; value: number; categoria: string; categoriaNombre: string; es_digital: boolean }>
}

export async function getSkillsResumen(globalFilters?: DashboardFilters): Promise<SkillsResumenData> {
  const client = getSupabaseClient()
  if (!client) return { por_l1: [], digitales: { digitales: 0, no_digitales: 0, total: 0 }, top_skills: [] }

  const { data, error } = await client.rpc('get_skills_resumen', { p_filters: buildRPCFilters(globalFilters) })

  if (error) {
    console.error('Error en get_skills_resumen RPC:', error)
    return { por_l1: [], digitales: { digitales: 0, no_digitales: 0, total: 0 }, top_skills: [] }
  }

  return data as SkillsResumenData
}

// Backward-compatible: distribución por categoría L1
export async function getSkillsPorCategoriaL1(_skillsFilters?: SkillsFilters, globalFilters?: DashboardFilters) {
  const resumen = await getSkillsResumen(globalFilters)
  return resumen.por_l1
}

// Backward-compatible: skills digitales vs no digitales
export async function getSkillsDigitales(_skillsFilters?: SkillsFilters, globalFilters?: DashboardFilters) {
  const resumen = await getSkillsResumen(globalFilters)
  const { digitales, no_digitales, total } = resumen.digitales
  if (total === 0) return []

  return [
    { name: 'Digitales', value: digitales, porcentaje: Math.round(digitales * 100 / total) },
    { name: 'No digitales', value: no_digitales, porcentaje: Math.round(no_digitales * 100 / total) }
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

// Backward-compatible: top N skills totales con su categoría
export async function getTopSkillsConCategoria(limit = 10, _skillsFilters?: SkillsFilters, globalFilters?: DashboardFilters) {
  const resumen = await getSkillsResumen(globalFilters)
  return resumen.top_skills.slice(0, limit)
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
  autor_email?: string;
  incluir_auto?: boolean;
}): Promise<Issue[]> {
  const client = getSupabaseClient()
  if (!client) return []

  let query = client
    .from('issues')
    .select('*')
    .order('created_at', { ascending: false })
    .limit(500)

  // Por defecto excluir auto-validator (100K+ issues entierran los humanos)
  if (!filters?.incluir_auto) {
    query = query.neq('autor_email', 'auto-validator@mol.gob.ar')
  }

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
  if (filters?.autor_email) {
    query = query.eq('autor_email', filters.autor_email)
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
  // Must use browser client (has user session) for RLS: autor_id = auth.uid()
  const { createBrowserClient } = await import('@/lib/supabase/browser')
  const client = createBrowserClient()

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

// ========== TENSIÓN DE DEMANDA (V-16) ==========

export interface TensionOcupacion {
  isco_code: string
  isco_label: string
  total_posiciones: number
  total_ofertas: number
  persistencia: number
  insistencia: number
  cuadrante: string
}

export async function getTensionOcupaciones(): Promise<TensionOcupacion[]> {
  const client = getSupabaseClient()
  if (!client) return []
  const { data, error } = await client
    .from('tension_ocupaciones')
    .select('*')
    .order('total_posiciones', { ascending: false })
  if (error) {
    console.error('Error fetching tension:', error)
    return []
  }
  return data || []
}

// ========== CONCENTRACIÓN OCUPACIONAL (I-02) ==========

export interface ConcentracionOcupacional {
  tipo: string            // 'global' | 'mensual' | 'ocupacion'
  mes: string | null      // '2026-01' (solo tipo=mensual)
  isco_code: string | null
  isco_label: string | null
  ofertas: number
  share_pct: number       // % del total (solo tipo=ocupacion)
  hhi: number             // HHI value (tipo=global/mensual)
  clasificacion: string | null  // 'diversificado'|'moderado'|'concentrado'
}

export async function getConcentracionOcupacional(): Promise<ConcentracionOcupacional[]> {
  const client = getSupabaseClient()
  if (!client) return []
  const { data, error } = await client
    .from('concentracion_ocupacional')
    .select('*')
    .order('tipo')
    .order('share_pct', { ascending: false })
  if (error) {
    console.error('Error fetching concentracion:', error)
    return []
  }
  return data || []
}

// ========== BRECHA DE CALIFICACIÓN (I-03) ==========

export interface BrechaCalificacion {
  isco_code: string
  isco_label: string
  total_ofertas: number
  skills_promedio: number
  brecha: number          // >1.0 sobreexigente, <1.0 subexigente
  categoria: string       // 'sobreexigente'|'equilibrado'|'subexigente'
}

export async function getBrechaCalificacion(): Promise<BrechaCalificacion[]> {
  const client = getSupabaseClient()
  if (!client) return []
  const { data, error } = await client
    .from('brecha_calificacion')
    .select('*')
    .order('brecha', { ascending: false })
  if (error) {
    console.error('Error fetching brecha:', error)
    return []
  }
  return data || []
}

// ========== DIGITALIZACIÓN POR SECTOR (I-05) ==========

export interface DigitalizacionSector {
  clae_seccion: string
  total_skills: number
  skills_digitales: number
  total_ofertas: number
  idx_digital: number       // % skills digitales sobre total
  nivel_digital: string     // 'alto'|'medio'|'bajo'
}

export async function getDigitalizacionSector(): Promise<DigitalizacionSector[]> {
  const client = getSupabaseClient()
  if (!client) return []
  const { data, error } = await client
    .from('digitalizacion_sector')
    .select('*')
    .order('idx_digital', { ascending: false })
  if (error) {
    console.error('Error fetching digitalizacion:', error)
    return []
  }
  return data || []
}

// ========== TRANSICIÓN SKILLS-OCUPACIÓN (I-04) ==========

export interface TransicionSkillsOcupacion {
  tipo: string              // 'nodo' | 'enlace'
  isco_code: string | null
  isco_label: string | null
  total_ofertas: number | null
  total_skills: number | null
  source_isco: string | null
  target_isco: string | null
  jaccard: number | null
  shared_skills: number | null
  union_skills: number | null
  top_shared_labels: string | null  // JSON array
}

export async function getTransicionSkills(): Promise<TransicionSkillsOcupacion[]> {
  const client = getSupabaseClient()
  if (!client) return []
  const { data, error } = await client
    .from('transicion_skills_ocupacion')
    .select('*')
    .order('tipo')
    .order('total_ofertas', { ascending: false })
  if (error) {
    console.error('Error fetching transicion:', error)
    return []
  }
  return data || []
}

// ========== VELOCIDAD DE COBERTURA (I-06) ==========

export interface VelocidadCobertura {
  isco_code: string
  isco_label: string
  total_ofertas: number
  mediana_dias: number
  q1_dias: number
  q3_dias: number
  min_dias: number
  max_dias: number
  categoria: string    // 'rapida' | 'normal' | 'lenta'
}

export async function getVelocidadCobertura(): Promise<VelocidadCobertura[]> {
  const client = getSupabaseClient()
  if (!client) return []
  const { data, error } = await client
    .from('velocidad_cobertura')
    .select('*')
    .order('mediana_dias', { ascending: false })
  if (error) {
    console.error('Error fetching velocidad:', error)
    return []
  }
  return data || []
}

// ========== ÍNDICE DE TRABAJO REMOTO (I-10) ==========

export interface IndiceTrabajoRemoto {
  mes: string
  clae_seccion: string | null
  total_ofertas: number
  presencial: number
  remoto: number
  hibrido: number
  pct_presencial: number
  pct_remoto: number
  pct_hibrido: number
}

export async function getIndiceRemoto(): Promise<IndiceTrabajoRemoto[]> {
  const client = getSupabaseClient()
  if (!client) return []
  const { data, error } = await client
    .from('indice_trabajo_remoto')
    .select('*')
    .order('mes')
  if (error) {
    console.error('Error fetching indice remoto:', error)
    return []
  }
  return data || []
}

// ========== FUNCIONES PARA PERFIL CONSOLIDADO ==========

// ConsolidatedProfile, ConsolidatedProfilesIndex imported above

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
  offset: number = 0,
  provincia?: string | null
): Promise<{ ofertas: OfertaPorOcupacion[], total: number }> {
  const client = getSupabaseClient()
  if (!client) return { ofertas: [], total: 0 }

  try {
    let query = client
      .from(TABLA_OFERTAS)
      .select(`
        id_oferta,
        titulo,
        titulo_limpio,
        empresa,
        fecha_publicacion,
        url,
        skills_tecnicas,
        estado
      `, { count: 'exact' })
      .eq('isco_code', iscoCode)
    if (provincia) query = query.eq('provincia', provincia)
    const { data, error, count } = await query
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

// ========== LANDING PAGE - DATOS DINÁMICOS ==========

export interface LandingData {
  totalOfertas: number
  rangoSemana: string
  topOcupaciones: { ocupacion: string; cantidad: number }[]
  topSkills: { name: string; value: number }[]
}

/**
 * Obtiene datos para la landing page en una sola llamada paralela.
 * Reutiliza getKPIsOptimized, getTopOcupaciones y getTopSkillsTecnicas.
 */
export async function getLandingData(): Promise<LandingData> {
  const [kpis, topOcupaciones, topSkills] = await Promise.all([
    getKPIsOptimized(),
    getTopOcupaciones(5),
    getTopSkillsTecnicas(5)
  ])

  // Rango: semana anterior completa (lunes a domingo pasados)
  const hoy = new Date()
  const day = hoy.getDay()
  // Domingo pasado: retroceder day días (si hoy es domingo, 0 → 7 para ir al anterior)
  const domingoPasado = new Date(hoy)
  domingoPasado.setDate(hoy.getDate() - (day === 0 ? 7 : day))
  // Lunes de esa semana: domingo - 6
  const lunesPasado = new Date(domingoPasado)
  lunesPasado.setDate(domingoPasado.getDate() - 6)
  const fmt = (d: Date) => `${d.getDate()}/${d.getMonth() + 1}`

  return {
    totalOfertas: kpis.totalOfertas,
    rangoSemana: `${fmt(lunesPasado)} y ${fmt(domingoPasado)}`,
    topOcupaciones,
    topSkills
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

// ========== PANEL DE VALIDACIÓN (admin/validacion) ==========

// OfertaValidacion, OfertaSkillValidacion, ValidationFiltersState imported above

const VALIDACION_SELECT = `
  id_oferta, titulo, titulo_limpio, empresa, fecha_publicacion, url, portal,
  provincia, localidad,
  isco_code, isco_label, esco_occupation_uri, esco_occupation_label,
  occupation_match_score, occupation_match_method, decision_metodo, regla_aplicada,
  descripcion, tareas_explicitas, mision_rol,
  modalidad, nivel_seniority, area_funcional, sector_empresa, clae_descripcion_seccion,
  clae_code, clae_grupo, clae_seccion,
  nivel_educativo, experiencia_min_anios, salario_min, salario_max,
  skills_tecnicas, soft_skills,
  validacion_humana, validacion_humana_at, validacion_humana_por, validacion_correcciones
`

export async function getOfertasValidacion(
  filters: Partial<ValidationFiltersState>,
  limit = 50,
  offset = 0
): Promise<{ ofertas: OfertaValidacion[], total: number }> {
  const client = getSupabaseClient()
  if (!client) return { ofertas: [], total: 0 }

  let query = client
    .from(TABLA_OFERTAS)
    .select(VALIDACION_SELECT, { count: 'exact' })

  // Existing filters
  if (filters.iscoGroup) {
    query = query.like('isco_code', `${filters.iscoGroup}%`)
  }
  if (filters.portal) {
    query = query.eq('portal', filters.portal)
  }
  if (filters.provincia) {
    query = query.eq('provincia', filters.provincia)
  }
  if (filters.metodo) {
    query = query.eq('decision_metodo', filters.metodo)
  }
  if (filters.search) {
    query = query.or(
      `titulo_limpio.ilike.%${filters.search}%,titulo.ilike.%${filters.search}%,id_oferta.eq.${filters.search}`
    )
  }

  // New filters
  if (filters.seniority) {
    query = query.eq('nivel_seniority', filters.seniority)
  }
  if (filters.modalidad) {
    query = query.eq('modalidad', filters.modalidad)
  }
  if (filters.sector) {
    query = query.eq('clae_descripcion_seccion', filters.sector)
  }
  if (filters.nivelEducativo) {
    query = query.eq('nivel_educativo', filters.nivelEducativo)
  }

  // Score range filter
  if (filters.scoreRange) {
    switch (filters.scoreRange) {
      case '<0.3':
        query = query.lt('occupation_match_score', 0.3)
        break
      case '0.3-0.5':
        query = query.gte('occupation_match_score', 0.3).lt('occupation_match_score', 0.5)
        break
      case '0.5-0.7':
        query = query.gte('occupation_match_score', 0.5).lt('occupation_match_score', 0.7)
        break
      case '>0.7':
        query = query.gte('occupation_match_score', 0.7)
        break
    }
  }

  // Estado validación humana
  if (filters.estadoValidacion) {
    if (filters.estadoValidacion === 'pendiente') {
      query = query.is('validacion_humana', null)
    } else {
      query = query.eq('validacion_humana', filters.estadoValidacion)
    }
  }

  const { data, error, count } = await query
    .order('fecha_publicacion', { ascending: false })
    .range(offset, offset + limit - 1)

  if (error) {
    console.error('Error fetching ofertas validacion:', error)
    return { ofertas: [], total: 0 }
  }

  return { ofertas: (data || []) as OfertaValidacion[], total: count || 0 }
}

export async function getOfertaValidacionById(id: string): Promise<OfertaValidacion | null> {
  const client = getSupabaseClient()
  if (!client) return null

  const { data, error } = await client
    .from(TABLA_OFERTAS)
    .select(VALIDACION_SELECT)
    .eq('id_oferta', id)
    .single()

  if (error) {
    console.error('Error fetching oferta validacion:', error)
    return null
  }

  return data as OfertaValidacion
}

export async function getSkillsByOferta(idOferta: string): Promise<OfertaSkillValidacion[]> {
  const client = getSupabaseClient()
  if (!client) return []

  const { data, error } = await client
    .from('ofertas_skills')
    .select('id, id_oferta, preferred_label, canonical_label, equivalence_id, l1, l1_nombre, l2, l2_nombre, es_digital, es_esencial, score, origen')
    .eq('id_oferta', idOferta)
    .order('es_esencial', { ascending: false })
    .order('score', { ascending: false })

  if (error) {
    console.error('Error fetching skills for oferta:', error)
    return []
  }

  return (data || []) as OfertaSkillValidacion[]
}

export interface ValidacionFilterOptions {
  portales: string[]
  provincias: string[]
  metodos: string[]
  iscoGroups: { code: string; label: string }[]
  seniorities: string[]
  modalidades: string[]
  sectores: string[]
  nivelesEducativos: string[]
}

export async function getValidacionFilterOptions(): Promise<ValidacionFilterOptions> {
  const client = getSupabaseClient()
  const empty: ValidacionFilterOptions = {
    portales: [], provincias: [], metodos: [], iscoGroups: [],
    seniorities: [], modalidades: [], sectores: [], nivelesEducativos: [],
  }
  if (!client) return empty

  const [portalesRes, provinciasRes, metodosRes, iscoRes, seniorityRes, modalidadRes, sectorRes, educRes] = await Promise.all([
    client.from(TABLA_OFERTAS).select('portal').not('portal', 'is', null).limit(1000),
    client.from(TABLA_OFERTAS).select('provincia').not('provincia', 'is', null).limit(1000),
    client.from(TABLA_OFERTAS).select('decision_metodo').not('decision_metodo', 'is', null).limit(1000),
    client.from(TABLA_OFERTAS).select('isco_code, isco_label').not('isco_code', 'is', null).limit(5000),
    client.from(TABLA_OFERTAS).select('nivel_seniority').not('nivel_seniority', 'is', null).limit(1000),
    client.from(TABLA_OFERTAS).select('modalidad').not('modalidad', 'is', null).limit(1000),
    client.from(TABLA_OFERTAS).select('clae_descripcion_seccion').not('clae_descripcion_seccion', 'is', null).limit(1000),
    client.from(TABLA_OFERTAS).select('nivel_educativo').not('nivel_educativo', 'is', null).limit(1000),
  ])

  const unique = <T extends string>(data: { [k: string]: T | null }[] | null, key: string): string[] => {
    if (!data) return []
    const set = new Set<string>()
    data.forEach(r => { if (r[key]) set.add(r[key] as string) })
    return [...set].sort()
  }

  const iscoGroupMap: Record<string, string> = {}
  iscoRes.data?.forEach(r => {
    if (r.isco_code) {
      const g = r.isco_code.charAt(0)
      if (!iscoGroupMap[g]) iscoGroupMap[g] = ISCO_MAJOR_GROUPS[g] || `Grupo ${g}`
    }
  })

  return {
    portales: unique(portalesRes.data, 'portal'),
    provincias: unique(provinciasRes.data, 'provincia'),
    metodos: unique(metodosRes.data, 'decision_metodo'),
    iscoGroups: Object.entries(iscoGroupMap)
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([code, label]) => ({ code, label: `${code} - ${label}` })),
    seniorities: unique(seniorityRes.data, 'nivel_seniority'),
    modalidades: unique(modalidadRes.data, 'modalidad'),
    sectores: unique(sectorRes.data, 'clae_descripcion_seccion'),
    nivelesEducativos: unique(educRes.data, 'nivel_educativo'),
  }
}

// ========== VALIDACIÓN HUMANA ==========

export async function saveValidacion(
  idOferta: string,
  resultado: ValidacionHumana,
  correcciones?: Record<string, unknown>
): Promise<boolean> {
  // Must use browser client (has user session/JWT) — not the anon client
  const { createBrowserClient } = await import('@/lib/supabase/browser')
  const client = createBrowserClient()

  const { data, error } = await client.rpc('guardar_validacion_humana', {
    p_id_oferta: idOferta,
    p_resultado: resultado,
    p_correcciones: correcciones || null,
  })

  if (error) throw error
  return data as boolean
}

export async function getValidacionStats(): Promise<ValidationStats> {
  const client = getSupabaseClient()
  if (!client) return { total: 0, ok: 0, error: 0, revisar: 0, basura: 0, pendientes: 0 }

  const { data, error } = await client
    .from(TABLA_OFERTAS)
    .select('validacion_humana')

  if (error) {
    console.error('Error fetching validation stats:', error)
    return { total: 0, ok: 0, error: 0, revisar: 0, basura: 0, pendientes: 0 }
  }

  const stats: ValidationStats = { total: 0, ok: 0, error: 0, revisar: 0, basura: 0, pendientes: 0 }
  data?.forEach(r => {
    stats.total++
    switch (r.validacion_humana) {
      case 'ok': stats.ok++; break
      case 'error': stats.error++; break
      case 'revisar': stats.revisar++; break
      case 'basura': stats.basura++; break
      default: stats.pendientes++
    }
  })
  return stats
}
