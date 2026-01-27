import { createClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!

export const supabase = createClient(supabaseUrl, supabaseAnonKey)

// Tipos para las tablas
export interface Oferta {
  id_oferta: string
  titulo: string
  empresa: string
  provincia: string
  localidad: string
  isco_code: string
  isco_label: string
  esco_occupation_label: string
  occupation_match_score: number
  modalidad: string
  nivel_seniority: string
  area_funcional: string
  sector_empresa: string
  skills_oferta_json: string
  fecha_publicacion: string
}

export interface Organizacion {
  id: string
  nombre: string
  tipo: string
  jurisdiccion: string
}

export interface Usuario {
  id: string
  nombre: string
  apellido: string
  email: string
  rol: 'platform_admin' | 'admin' | 'analista' | 'lector'
  organizacion_id: string
}

// ============================================================
// Funciones de fetch para el Dashboard
// ============================================================

export interface DashboardKPIs {
  total_ofertas: number
  ocupaciones_distintas: number
  provincias_con_ofertas: number
  empresas_distintas: number
  skills_promedio: number
  ofertas_remotas: number
  ofertas_hibridas: number
  ofertas_presenciales: number
}

export interface EvolucionData {
  periodo: string
  ofertas: number
}

export interface GeografiaData {
  jurisdiccion: string
  cantidad: number
  porcentaje: number
}

export interface OcupacionData {
  ocupacion: string
  cantidad: number
}

export interface OfertaTabla {
  id: string
  titulo: string
  empresa: string
  ubicacion: string
  ocupacion: string
  modalidad: string
  seniority: string
  fecha: string
}

export async function getKPIs(): Promise<DashboardKPIs | null> {
  const { data, error } = await supabase
    .from('vw_dashboard_kpis')
    .select('*')
    .single()

  if (error) {
    console.error('Error fetching KPIs:', error)
    return null
  }
  return data
}

export async function getEvolucion(): Promise<EvolucionData[]> {
  const { data, error } = await supabase
    .from('vw_evolucion_mensual')
    .select('*')
    .order('mes', { ascending: true })

  if (error) {
    console.error('Error fetching evolucion:', error)
    return []
  }

  return (data || []).map(d => ({
    periodo: d.mes ? new Date(d.mes).toLocaleDateString('es-AR', { month: 'short' }) : '',
    ofertas: d.ofertas || 0
  }))
}

export async function getDistribucionGeografica(): Promise<GeografiaData[]> {
  const { data, error } = await supabase
    .from('vw_distribucion_geografica')
    .select('*')
    .limit(7)

  if (error) {
    console.error('Error fetching geografia:', error)
    return []
  }

  return (data || []).map(d => ({
    jurisdiccion: d.provincia || 'Sin especificar',
    cantidad: d.cantidad || 0,
    porcentaje: d.porcentaje || 0
  }))
}

export async function getTopOcupaciones(): Promise<OcupacionData[]> {
  const { data, error } = await supabase
    .from('vw_distribucion_ocupaciones')
    .select('*')
    .limit(10)

  if (error) {
    console.error('Error fetching ocupaciones:', error)
    return []
  }

  return (data || []).map(d => ({
    ocupacion: d.isco_label || 'Sin clasificar',
    cantidad: d.cantidad || 0
  }))
}

export async function getOfertas(filtros?: Record<string, string>): Promise<OfertaTabla[]> {
  let query = supabase
    .from('ofertas')
    .select('id_oferta, titulo, empresa, provincia, esco_occupation_label, modalidad, nivel_seniority, fecha_publicacion_iso')
    .order('fecha_publicacion_iso', { ascending: false })
    .limit(100)

  if (filtros?.provincia) query = query.eq('provincia', filtros.provincia)
  if (filtros?.modalidad) query = query.eq('modalidad', filtros.modalidad)
  if (filtros?.seniority) query = query.eq('nivel_seniority', filtros.seniority)

  const { data, error } = await query

  if (error) {
    console.error('Error fetching ofertas:', error)
    return []
  }

  return (data || []).map(d => ({
    id: d.id_oferta,
    titulo: d.titulo || '',
    empresa: d.empresa || '',
    ubicacion: d.provincia || '',
    ocupacion: d.esco_occupation_label || '',
    modalidad: d.modalidad || '',
    seniority: d.nivel_seniority || '',
    fecha: d.fecha_publicacion_iso || ''
  }))
}
