import { createClient } from '@supabase/supabase-js'
import { DashboardFilters } from './types'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!

export const supabase = createClient(supabaseUrl, supabaseAnonKey)

// Nombre de la tabla principal con datos
const TABLA_OFERTAS = 'ofertas'

// Tipos para las tablas
export interface OfertaDashboard {
  id_oferta: string
  titulo: string
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

  // Filtro por fecha desde (usa fecha_publicacion_iso)
  if (filters.fechaDesde) {
    const fechaDesde = filters.fechaDesde.toISOString().split('T')[0]
    query = query.gte('fecha_publicacion_iso', fechaDesde)
  }

  // Filtro por fecha hasta
  if (filters.fechaHasta) {
    const fechaHasta = filters.fechaHasta.toISOString().split('T')[0]
    query = query.lte('fecha_publicacion_iso', fechaHasta)
  }

  // Filtro por ocupaciones seleccionadas
  if (filters.ocupacionesSeleccionadas && filters.ocupacionesSeleccionadas.length > 0) {
    query = query.in('isco_code', filters.ocupacionesSeleccionadas)
  }

  return query
}

// Funciones para obtener datos del dashboard
export async function getKPIs(filters?: DashboardFilters) {
  let query = supabase
    .from(TABLA_OFERTAS)
    .select('id_oferta, isco_code, empresa, provincia')

  query = applyFilters(query, filters)

  const { data, error } = await query

  if (error) throw error

  const ofertas = data || []
  return {
    totalOfertas: ofertas.length,
    ocupacionesDistintas: new Set(ofertas.map(o => o.isco_code).filter(Boolean)).size,
    empresasActivas: new Set(ofertas.map(o => o.empresa).filter(Boolean)).size,
    provincias: new Set(ofertas.map(o => o.provincia).filter(Boolean)).size
  }
}

export async function getOfertasPorProvincia(filters?: DashboardFilters) {
  let query = supabase
    .from(TABLA_OFERTAS)
    .select('provincia')

  // Para este caso, no filtramos por provincia para mostrar la distribución
  if (filters?.fechaDesde) {
    const fechaDesde = filters.fechaDesde.toISOString().split('T')[0]
    query = query.gte('fecha_publicacion_iso', fechaDesde)
  }
  if (filters?.fechaHasta) {
    const fechaHasta = filters.fechaHasta.toISOString().split('T')[0]
    query = query.lte('fecha_publicacion_iso', fechaHasta)
  }

  const { data, error } = await query

  if (error) throw error

  const counts: Record<string, number> = {}
  data?.forEach(o => {
    const prov = o.provincia || 'No especificado'
    counts[prov] = (counts[prov] || 0) + 1
  })

  const total = data?.length || 1
  return Object.entries(counts)
    .map(([jurisdiccion, cantidad]) => ({
      jurisdiccion,
      cantidad,
      porcentaje: Math.round(cantidad * 1000 / total) / 10
    }))
    .sort((a, b) => b.cantidad - a.cantidad)
}

export async function getTopOcupaciones(limit = 10, filters?: DashboardFilters) {
  let query = supabase
    .from(TABLA_OFERTAS)
    .select('isco_code, isco_label')

  query = applyFilters(query, filters)

  const { data, error } = await query

  if (error) throw error

  const counts: Record<string, { label: string, count: number }> = {}
  data?.forEach(o => {
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
  let query = supabase
    .from(TABLA_OFERTAS)
    .select('modalidad')

  query = applyFilters(query, filters)

  const { data, error } = await query

  if (error) throw error

  const counts: Record<string, number> = {}
  data?.forEach(o => {
    const mod = o.modalidad || 'No especificado'
    counts[mod] = (counts[mod] || 0) + 1
  })

  return Object.entries(counts)
    .map(([modalidad, cantidad]) => ({ modalidad, cantidad }))
    .sort((a, b) => b.cantidad - a.cantidad)
}

export async function getOfertas(limit = 50, offset = 0, filters?: DashboardFilters) {
  let query = supabase
    .from(TABLA_OFERTAS)
    .select(`
      id_oferta,
      titulo,
      empresa,
      fecha_publicacion_iso,
      url_oferta,
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
      skills_tecnicas_list,
      soft_skills_list
    `, { count: 'exact' })

  query = applyFilters(query, filters)

  const { data, error, count } = await query
    .order('fecha_publicacion_iso', { ascending: false })
    .range(offset, offset + limit - 1)

  if (error) throw error

  // Transformar los datos al formato esperado por el dashboard
  const ofertas = (data || []).map(o => ({
    id_oferta: o.id_oferta,
    titulo: o.titulo,
    empresa: o.empresa,
    fecha_publicacion: o.fecha_publicacion_iso,
    url: o.url_oferta,
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
    salario_min: null,
    salario_max: null,
    skills_tecnicas: parseSkillsList(o.skills_tecnicas_list),
    soft_skills: parseSkillsList(o.soft_skills_list),
  }))

  return { ofertas, total: count || 0 }
}

// Funciones para obtener skills (para Requerimientos)
export async function getTopSkillsTecnicas(limit = 20, filters?: DashboardFilters) {
  let query = supabase
    .from(TABLA_OFERTAS)
    .select('skills_tecnicas_list')

  query = applyFilters(query, filters)

  const { data, error } = await query

  if (error) throw error

  const counts: Record<string, number> = {}
  data?.forEach(o => {
    const skills = parseSkillsList(o.skills_tecnicas_list)
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
  let query = supabase
    .from(TABLA_OFERTAS)
    .select('soft_skills_list')

  query = applyFilters(query, filters)

  const { data, error } = await query

  if (error) throw error

  const counts: Record<string, number> = {}
  data?.forEach(o => {
    const skills = parseSkillsList(o.soft_skills_list)
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
  let query = supabase
    .from(TABLA_OFERTAS)
    .select('id_oferta', { count: 'exact', head: true })

  query = applyFilters(query, filters)

  const { count, error } = await query
  if (error) throw error
  return count || 0
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
  let query = supabase
    .from(TABLA_OFERTAS)
    .select('isco_code, isco_label')

  query = applyFilters(query, filters)

  const { data, error } = await query
  if (error) throw error

  // Agrupar por código ISCO de 4 dígitos
  const detailCounts: Record<string, { label: string; count: number }> = {}
  data?.forEach(o => {
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
  let query = supabase
    .from(TABLA_OFERTAS)
    .select('nivel_educativo, experiencia_min_anios, nivel_seniority, modalidad, tiene_gente_cargo, jornada_laboral')

  query = applyFilters(query, filters)

  // Aplicar filtros locales
  if (localFilters?.educacion && localFilters.educacion !== 'Todos') {
    query = query.eq('nivel_educativo', localFilters.educacion)
  }
  if (localFilters?.modalidad && localFilters.modalidad !== 'Todos') {
    query = query.eq('modalidad', localFilters.modalidad)
  }

  const { data, error } = await query

  if (error) throw error

  const ofertas = data || []
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
  if (!filters) return null

  const hasGlobalFilter = filters.provincia || filters.fechaDesde || filters.fechaHasta ||
    (filters.ocupacionesSeleccionadas && filters.ocupacionesSeleccionadas.length > 0)

  if (!hasGlobalFilter) return null

  let query = supabase
    .from(TABLA_OFERTAS)
    .select('id_oferta')

  query = applyFilters(query, filters)

  const { data, error } = await query
  if (error) throw error

  return (data || []).map(o => o.id_oferta)
}

// Helper: aplicar filtro de IDs a una query de ofertas_skills
function applyOfertaIdsFilter(query: any, ofertaIds: string[] | null) {
  if (ofertaIds === null) return query
  if (ofertaIds.length === 0) return query.in('id_oferta', ['__none__']) // No match
  return query.in('id_oferta', ofertaIds)
}

// Distribución por categoría L1
export async function getSkillsPorCategoriaL1(skillsFilters?: SkillsFilters, globalFilters?: DashboardFilters) {
  const ofertaIds = await getFilteredOfertaIds(globalFilters)

  let query = supabase
    .from('ofertas_skills')
    .select('l1, l1_nombre, es_digital')
    .not('l1', 'is', null)

  query = applyOfertaIdsFilter(query, ofertaIds)

  // Filtro por digital
  if (skillsFilters?.esDigital !== undefined && skillsFilters.esDigital !== null) {
    query = query.eq('es_digital', skillsFilters.esDigital)
  }

  const { data, error } = await query

  if (error) throw error

  const counts: Record<string, { nombre: string, count: number }> = {}
  data?.forEach(s => {
    if (!counts[s.l1]) {
      counts[s.l1] = { nombre: s.l1_nombre || s.l1, count: 0 }
    }
    counts[s.l1].count++
  })

  const total = data?.length || 1
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
  const ofertaIds = await getFilteredOfertaIds(globalFilters)

  let query = supabase
    .from('ofertas_skills')
    .select('es_digital, l1, l1_nombre')

  query = applyOfertaIdsFilter(query, ofertaIds)

  // Filtro por categoría
  if (skillsFilters?.categoria && skillsFilters.categoria !== 'Todos') {
    query = query.eq('l1_nombre', skillsFilters.categoria)
  }

  const { data, error } = await query

  if (error) throw error

  let digitales = 0
  let noDigitales = 0
  data?.forEach(s => {
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
  const ofertaIds = await getFilteredOfertaIds(globalFilters)

  let query = supabase
    .from('ofertas_skills')
    .select('l1, l1_nombre, esco_skill_label, es_digital')
    .not('l1', 'is', null)
    .not('esco_skill_label', 'is', null)

  query = applyOfertaIdsFilter(query, ofertaIds)

  // Filtro por digital
  if (skillsFilters?.esDigital !== undefined && skillsFilters.esDigital !== null) {
    query = query.eq('es_digital', skillsFilters.esDigital)
  }

  const { data, error } = await query

  if (error) throw error

  // Agrupar por categoría y contar skills
  const porCategoria: Record<string, Record<string, number>> = {}
  const nombreCategoria: Record<string, string> = {}

  data?.forEach(s => {
    if (!porCategoria[s.l1]) {
      porCategoria[s.l1] = {}
      nombreCategoria[s.l1] = s.l1_nombre || s.l1
    }
    const skill = s.esco_skill_label
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
  const ofertaIds = await getFilteredOfertaIds(globalFilters)

  let query = supabase
    .from('ofertas_skills')
    .select('l1, l1_nombre, esco_skill_label, es_digital')
    .not('l1', 'is', null)
    .not('esco_skill_label', 'is', null)

  query = applyOfertaIdsFilter(query, ofertaIds)

  // Filtro por categoría
  if (skillsFilters?.categoria && skillsFilters.categoria !== 'Todos') {
    query = query.eq('l1_nombre', skillsFilters.categoria)
  }

  // Filtro por digital
  if (skillsFilters?.esDigital !== undefined && skillsFilters.esDigital !== null) {
    query = query.eq('es_digital', skillsFilters.esDigital)
  }

  const { data, error } = await query

  if (error) throw error

  // Contar skills y guardar su categoría
  const skillCounts: Record<string, { count: number, l1: string, l1_nombre: string }> = {}

  data?.forEach(s => {
    const skill = s.esco_skill_label
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
  const ofertaIds = await getFilteredOfertaIds(globalFilters)

  let query = supabase
    .from('ofertas_skills')
    .select(`
      l1,
      l1_nombre,
      id_oferta
    `)
    .not('l1', 'is', null)

  query = applyOfertaIdsFilter(query, ofertaIds)

  // Obtener skills con su ocupación asociada
  const { data, error } = await query

  if (error) throw error

  // Obtener ocupaciones de las ofertas
  const skillOfertaIds = [...new Set(data?.map(s => s.id_oferta) || [])]

  const { data: ofertas, error: err2 } = await supabase
    .from('ofertas')
    .select('id_oferta, isco_label')
    .in('id_oferta', skillOfertaIds.slice(0, 100)) // Limitar para performance
    .not('isco_label', 'is', null)

  if (err2) throw err2

  // Crear mapa de oferta -> ocupación
  const ofertaOcupacion: Record<string, string> = {}
  ofertas?.forEach(o => {
    ofertaOcupacion[o.id_oferta] = o.isco_label
  })

  // Contar categorías por ocupación
  const heatmap: Record<string, Record<string, number>> = {}
  const categoriasNombres: Record<string, string> = {}

  data?.forEach(s => {
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
