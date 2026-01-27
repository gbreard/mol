import { createClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!

export const supabase = createClient(supabaseUrl, supabaseAnonKey)

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

// Funciones para obtener datos del dashboard
export async function getKPIs() {
  const { data, error } = await supabase
    .from('ofertas_dashboard')
    .select('id_oferta, isco_code, empresa, provincia')

  if (error) throw error

  const ofertas = data || []
  return {
    totalOfertas: ofertas.length,
    ocupacionesDistintas: new Set(ofertas.map(o => o.isco_code).filter(Boolean)).size,
    empresasActivas: new Set(ofertas.map(o => o.empresa).filter(Boolean)).size,
    provincias: new Set(ofertas.map(o => o.provincia).filter(Boolean)).size
  }
}

export async function getOfertasPorProvincia() {
  const { data, error } = await supabase
    .from('ofertas_dashboard')
    .select('provincia')

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

export async function getTopOcupaciones(limit = 10) {
  const { data, error } = await supabase
    .from('ofertas_dashboard')
    .select('isco_code, isco_label')

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

export async function getOfertasPorModalidad() {
  const { data, error } = await supabase
    .from('ofertas_dashboard')
    .select('modalidad')

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

export async function getOfertas(limit = 50, offset = 0) {
  const { data, error, count } = await supabase
    .from('ofertas_dashboard')
    .select('*', { count: 'exact' })
    .order('fecha_publicacion', { ascending: false })
    .range(offset, offset + limit - 1)

  if (error) throw error

  return { ofertas: data || [], total: count || 0 }
}
