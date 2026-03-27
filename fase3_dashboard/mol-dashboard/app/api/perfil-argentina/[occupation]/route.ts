import { NextRequest, NextResponse } from 'next/server'
import { requireRateLimit } from '@/lib/api-auth'
import { createClient } from '@supabase/supabase-js'
import fs from 'fs'
import path from 'path'

// Supabase client con service role para API
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || ''
const supabaseServiceKey = process.env.SUPABASE_SERVICE_ROLE_KEY || process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || ''

const supabase = supabaseUrl && supabaseServiceKey
  ? createClient(supabaseUrl, supabaseServiceKey)
  : null

// Cache del JSON de ocupaciones ESCO (se carga una vez)
let escoOccupationsCache: Record<string, any> | null = null

function loadEscoOccupations(): Record<string, any> {
  if (escoOccupationsCache) return escoOccupationsCache

  try {
    const filePath = path.join(process.cwd(), 'public', 'data', 'occupation_full_detail.json')
    const fileContent = fs.readFileSync(filePath, 'utf-8')
    escoOccupationsCache = JSON.parse(fileContent)
    return escoOccupationsCache || {}
  } catch (error) {
    console.error('Error loading ESCO occupations:', error)
    return {}
  }
}

// Normalizar label para comparación
function normalize(label: string): string {
  if (!label) return ''
  return label.trim().toLowerCase()
}

// Extraer UUID de URI ESCO
function extractUuid(uri: string): string {
  if (!uri) return ''
  return uri.split('/').pop() || ''
}

interface SkillMOL {
  label_original: string
  label_normalized: string
  frequency: number
  percentage: number
  is_esco_essential: boolean
  is_esco_optional: boolean
  is_emerging: boolean
  esco_uri?: string
  description?: string
  L1?: string
  L2?: string
}

interface PerfilArgentinaResponse {
  esco_uuid: string
  esco_label: string
  isco_code: string
  offer_count: number
  mol_skills: SkillMOL[]
  comparison: {
    coverage_essential: number
    coverage_total: number
    common_count: number
    common_optional_count: number
    emerging_count: number
    missing_count: number
    esco_essential_count: number
    esco_optional_count: number
    mol_unique_count: number
    common_labels: string[]
    common_optional_labels: string[]
    emerging_labels: string[]
    missing_labels: string[]
  }
  generated_at: string
}

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ occupation: string }> }
) {
  const limited = requireRateLimit(request);
  if (limited) return limited;

  const { occupation } = await params

  if (!supabase) {
    return NextResponse.json(
      { error: 'Supabase no configurado' },
      { status: 500 }
    )
  }

  try {
    // El occupation puede ser UUID o URI completa
    const escoUuid = occupation.includes('http')
      ? extractUuid(occupation)
      : occupation

    const escoUri = `http://data.europa.eu/esco/occupation/${escoUuid}`

    // 1. Cargar datos ESCO de esta ocupación
    const escoData = loadEscoOccupations()
    const escoOccupation = escoData[escoUuid]

    if (!escoOccupation) {
      return NextResponse.json(
        { error: `Ocupación ESCO no encontrada: ${escoUuid}` },
        { status: 404 }
      )
    }

    // 2. Obtener ofertas de esta ocupación
    const { data: ofertas, error: ofertasError } = await supabase
      .from('ofertas_dashboard')
      .select('id_oferta, esco_occupation_label, isco_code')
      .eq('esco_occupation_uri', escoUri)
      .limit(5000)

    if (ofertasError) throw ofertasError

    if (!ofertas || ofertas.length === 0) {
      return NextResponse.json({
        esco_uuid: escoUuid,
        esco_label: escoOccupation.label,
        isco_code: escoOccupation.isco || '',
        offer_count: 0,
        mol_skills: [],
        comparison: {
          coverage_essential: 0,
          coverage_total: 0,
          common_count: 0,
          common_optional_count: 0,
          emerging_count: 0,
          missing_count: 0,
          esco_essential_count: 0,
          esco_optional_count: 0,
          mol_unique_count: 0,
          common_labels: [],
          common_optional_labels: [],
          emerging_labels: [],
          missing_labels: []
        },
        generated_at: new Date().toISOString()
      } as PerfilArgentinaResponse)
    }

    const ofertaIds = ofertas.map(o => o.id_oferta)
    const offerCount = ofertas.length

    // 3. Obtener skills de esas ofertas
    const { data: skills, error: skillsError } = await supabase
      .from('ofertas_skills')
      .select(`
        skill_uri,
        preferred_label,
        canonical_label,
        l1,
        l1_nombre,
        l2,
        l2_nombre
      `)
      .in('id_oferta', ofertaIds)

    if (skillsError) throw skillsError

    // 4. Agregar skills por label normalizado (use canonical if available)
    const skillsMap: Record<string, {
      label_original: string
      frequency: number
      uri?: string
      L1?: string
      L2?: string
    }> = {}

    skills?.forEach(s => {
      const label = s.canonical_label || s.preferred_label
      if (!label) return
      const labelNorm = normalize(label)

      if (!skillsMap[labelNorm]) {
        skillsMap[labelNorm] = {
          label_original: s.preferred_label,
          frequency: 0,
          uri: s.skill_uri || undefined,
          L1: s.l1 || undefined,
          L2: s.l2 || undefined
        }
      }
      skillsMap[labelNorm].frequency++
    })

    // 5. Construir sets de ESCO
    const escoEssentialLabels: string[] = []
    const escoOptionalLabels: string[] = []

    // Skills
    escoOccupation.skills?.essential?.forEach((s: any) => {
      escoEssentialLabels.push(normalize(s.label || ''))
    })
    escoOccupation.skills?.optional?.forEach((s: any) => {
      escoOptionalLabels.push(normalize(s.label || ''))
    })

    // Knowledge
    escoOccupation.knowledge?.essential?.forEach((s: any) => {
      escoEssentialLabels.push(normalize(s.label || ''))
    })
    escoOccupation.knowledge?.optional?.forEach((s: any) => {
      escoOptionalLabels.push(normalize(s.label || ''))
    })

    const escoEssentialSet = new Set(escoEssentialLabels.filter(Boolean))
    const escoOptionalSet = new Set(escoOptionalLabels.filter(Boolean))
    const escoAllSet = new Set([...escoEssentialSet, ...escoOptionalSet])
    const molSet = new Set(Object.keys(skillsMap))

    // 6. Calcular comparación
    const common = new Set([...molSet].filter(x => escoEssentialSet.has(x)))
    const commonOptional = new Set([...molSet].filter(x => escoOptionalSet.has(x)))
    const emerging = new Set([...molSet].filter(x => !escoAllSet.has(x)))
    const missing = new Set([...escoEssentialSet].filter(x => !molSet.has(x)))

    const coverageEssential = escoEssentialSet.size > 0
      ? (common.size / escoEssentialSet.size) * 100
      : 0

    const coverageTotal = escoAllSet.size > 0
      ? ((common.size + commonOptional.size) / escoAllSet.size) * 100
      : 0

    // 7. Construir array de skills MOL con métricas
    const molSkills: SkillMOL[] = Object.entries(skillsMap)
      .map(([labelNorm, data]) => ({
        label_original: data.label_original,
        label_normalized: labelNorm,
        frequency: data.frequency,
        percentage: Math.round((data.frequency / offerCount) * 1000) / 10,
        is_esco_essential: escoEssentialSet.has(labelNorm),
        is_esco_optional: escoOptionalSet.has(labelNorm),
        is_emerging: emerging.has(labelNorm),
        esco_uri: data.uri,
        L1: data.L1,
        L2: data.L2
      }))
      .sort((a, b) => b.frequency - a.frequency)

    // 8. Respuesta
    const response: PerfilArgentinaResponse = {
      esco_uuid: escoUuid,
      esco_label: escoOccupation.label || ofertas[0]?.esco_occupation_label || '',
      isco_code: escoOccupation.isco || ofertas[0]?.isco_code || '',
      offer_count: offerCount,
      mol_skills: molSkills,
      comparison: {
        coverage_essential: Math.round(coverageEssential * 10) / 10,
        coverage_total: Math.round(coverageTotal * 10) / 10,
        common_count: common.size,
        common_optional_count: commonOptional.size,
        emerging_count: emerging.size,
        missing_count: missing.size,
        esco_essential_count: escoEssentialSet.size,
        esco_optional_count: escoOptionalSet.size,
        mol_unique_count: molSet.size,
        common_labels: [...common].sort(),
        common_optional_labels: [...commonOptional].sort(),
        emerging_labels: [...emerging].sort(),
        missing_labels: [...missing].sort()
      },
      generated_at: new Date().toISOString()
    }

    return NextResponse.json(response)

  } catch (error) {
    console.error('Error in perfil-argentina API:', error)
    return NextResponse.json(
      { error: 'Error interno del servidor' },
      { status: 500 }
    )
  }
}
