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
