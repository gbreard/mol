/**
 * DEMO-MIERCOLES 2.2 — verificación de solo lectura de los perfiles DEMO.
 *
 * Usa el mismo código que la UI (lib/matching.ts, normalizeProvinciaToRegice) y las
 * mismas fuentes (occupation_full_detail.json, RPC de conteos, /api/perfiles/cursos-gap)
 * para reportar, por perfil DEMO:
 *   - M2: top 10 ocupaciones (matchScore, esenciales cubiertas/total, avisos y activas)
 *   - M3: gap de la ocupación esperada principal + 3 primeros cursos ("cubre N de M")
 * y, aparte, qué devuelve el texto libre para 4 frases de prueba.
 * No escribe nada.
 *
 * Uso (desde fase3_dashboard/mol-dashboard):
 *   npx esbuild scripts/demo/verificar_perfiles_demo.ts --bundle --platform=node --outfile=/tmp/verif.js
 *   node /tmp/verif.js --base https://mol-nextjs.vercel.app --config ../../config/supabase_config.json --out salida.json
 */
import { readFileSync, writeFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { calculateOccupationMatch, isEligibleMatch, compareMatches, capPerIsco, cursosQueCubrenVarias, type ProfileSkill } from '../../lib/matching'
import { normalizeProvinciaToRegice } from '../../components/oficina-empleo/normalizeProvinciaToRegice'
import { periodoDesde, provinciaOfertas } from '../../lib/ofertas-estado'

const args = Object.fromEntries(
  process.argv.slice(2).reduce<[string, string][]>((acc, a, i, arr) => (a.startsWith('--') ? [...acc, [a.slice(2), arr[i + 1]]] : acc), [])
)
const BASE = (args.base || 'https://mol-nextjs.vercel.app').replace(/\/$/, '')
const CONFIG = JSON.parse(readFileSync(resolve(args.config || '../../config/supabase_config.json'), 'utf8'))
const OCC_JSON = JSON.parse(readFileSync(resolve(args.occ || 'public/data/occupation_full_detail.json'), 'utf8'))
// Cuando /api/perfiles exija sesión (Fase 3): --cookie con la cookie de sesión del navegador
const COOKIE: string | undefined = args.cookie

const ESPERADAS: Record<string, { principal: string; esperadas: string[] }> = {
  'DEMO-001': { principal: 'soldador/soldadora', esperadas: ['soldador', 'metal', 'calderer'] },
  'DEMO-002': { principal: 'reponedor/reponedora', esperadas: ['reponedor', 'cajero', 'vendedor', 'dependiente'] },
  'DEMO-003': { principal: 'albañil', esperadas: ['albañil', 'solador', 'pisos', 'peón', 'construcción'] },
  'DEMO-004': { principal: 'empleado administrativo/empleada administrativa', esperadas: ['administrativ', 'recepcionista', 'contab'] },
  'DEMO-005': { principal: 'desarrollador de software/desarrolladora de software', esperadas: ['desarrollador', 'programador', 'analista'] },
}

const FRASES: Record<string, string> = {
  enfermera: 'trabajé de enfermera en un hospital, pongo inyecciones, tomo la presión y cuido pacientes',
  albañil: 'trabajé 5 años de albañil, levanto paredes y hago revoques',
  programador: 'soy programador, hago páginas web con JavaScript y Python y manejo bases de datos',
  cajera: 'fui cajera en un supermercado, cobraba, hacía el cierre de caja y atendía clientes',
  'albañil (paso 6 de la demo)': 'trabajé de albañil, levanto paredes y hago revoques',
}

async function api(path: string, init?: RequestInit) {
  const res = await fetch(BASE + path, {
    ...init,
    headers: { 'Content-Type': 'application/json', ...(COOKIE ? { Cookie: COOKIE } : {}), ...(init?.headers || {}) },
  })
  if (!res.ok) throw new Error(`${path} → HTTP ${res.status}`)
  return res.json()
}

async function rpc(fn: string, body: Record<string, unknown>, intento = 1): Promise<any> {
  const res = await fetch(`${CONFIG.url}/rest/v1/rpc/${fn}`, {
    method: 'POST',
    headers: { apikey: CONFIG.anon_key, Authorization: `Bearer ${CONFIG.anon_key}`, 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) {
    if (intento < 3) return rpc(fn, body, intento + 1)
    throw new Error(`rpc ${fn} → HTTP ${res.status}`)
  }
  return res.json()
}

async function fechaMaxOfertas(): Promise<string | null> {
  const res = await fetch(`${CONFIG.url}/rest/v1/ofertas_dashboard?select=fecha_publicacion&fecha_publicacion=not.is.null&order=fecha_publicacion.desc&limit=1`, {
    headers: { apikey: CONFIG.anon_key, Authorization: `Bearer ${CONFIG.anon_key}` },
  })
  return (await res.json())?.[0]?.fecha_publicacion ?? null
}

type Conteo = { total: number; activas: number }
async function conteos(provincia: string | null, since: string | null): Promise<Record<string, Conteo>> {
  const rows: { isco_code: string; total: number; activas: number }[] = await rpc('get_ofertas_count_by_isco_filtrado', { p_provincia: provincia, p_since: since })
  return Object.fromEntries(rows.map(r => [r.isco_code, { total: Number(r.total), activas: Number(r.activas) }]))
}

function esEsperada(label: string, esperadas: string[]) {
  const l = label.toLowerCase()
  return esperadas.some(e => l.includes(e))
}

async function main() {
  const fechaMax = await fechaMaxOfertas()
  const since = periodoDesde(30, fechaMax) // M2 arranca en "Último mes", anclado a la última fecha con datos
  const pais = await conteos(null, since)

  const lista: any[] = await api('/api/perfiles?limit=100')
  const demos = lista.filter(p => p.personas?.dni?.startsWith('DEMO-')).sort((a, b) => a.personas.dni.localeCompare(b.personas.dni))

  const perfiles = []
  for (const p of demos) {
    const dni: string = p.personas.dni
    const det = await api(`/api/perfiles?id=${p.id}`)
    const skills: ProfileSkill[] = (det.skills || []).map((s: any) => ({ skill_uri: s.skill_uri, nivel: s.nivel ?? null }))
    const ubicacion: string | null = det.personas?.ubicacion ?? null
    const provincia = provinciaOfertas(ubicacion)
    const prov = provincia ? await conteos(provincia, since) : pais
    const esp = ESPERADAS[dni]

    // === M2: mismo cálculo, barandas y orden que perfiles/matching (sort 'match') ===
    const activasPais = Object.fromEntries(Object.entries(pais).map(([k, v]) => [k, v.activas]))
    const matches = Object.entries(OCC_JSON as Record<string, any>).flatMap(([id, occ]) => {
      const r = calculateOccupationMatch(skills, occ.skills?.essential ?? [], occ.skills?.optional ?? [])
      if (r.sharedEssential.length === 0) return []
      const isco_code = String(occ.isco || '').replace(/^C/, '')
      const m = { id, label: occ.label as string, isco_code, isco: isco_code, matchScore: r.matchScore, weightedScore: r.weightedScore,
        essentialTotal: r.essentialTotal, essentialCovered: r.sharedEssential.length, cubiertas: r.sharedEssential.length, total: r.essentialTotal }
      return isEligibleMatch(m) ? [m] : []
    }).sort((a, b) => compareMatches(a, b, activasPais))
    // Lista principal de M2: ≥ 3 avisos en el país y ≥ 20% de cobertura
    const esPrincipal = (m: { isco: string; matchScore: number }) => (pais[m.isco]?.total || 0) >= 3 && m.matchScore >= 20
    const conAvisos = capPerIsco(matches.filter(esPrincipal))
    const otras = matches.filter(m => !esPrincipal(m))
    const top10 = conAvisos.slice(0, 10).map((m, i) => ({
      rank: i + 1, ...m,
      avisos_prov: prov[m.isco]?.total || 0, activas_prov: prov[m.isco]?.activas || 0,
      avisos_pais: pais[m.isco]?.total || 0, activas_pais: pais[m.isco]?.activas || 0,
      esperada: esEsperada(m.label, esp.esperadas),
    }))
    const rankPrincipal = conAvisos.findIndex(m => m.label === esp.principal) + 1

    // === M3: gap de la ocupación esperada principal + cursos (igual que perfiles/futuro) ===
    const [occId, occ] = Object.entries(OCC_JSON as Record<string, any>).find(([, o]) => o.label === esp.principal)!
    const gap = calculateOccupationMatch(skills, occ.skills.essential || [], occ.skills.optional || [])
    const gapUris = gap.gapEssential.map(s => `http://data.europa.eu/esco/skill/${s.id}`)
    const provRegice = normalizeProvinciaToRegice(ubicacion)
    let cursos: any[] = []
    let cursosAlcance = 'provincia'
    if (gapUris.length > 0) {
      // Igual que M3: solo cursos que cubren ≥ 2 del gap (o el único); provincia → país
      const utiles = (c: any[]) => cursosQueCubrenVarias(c || [], gapUris.length)
      cursos = utiles((await api('/api/perfiles/cursos-gap', { method: 'POST', body: JSON.stringify({ gap_skill_uris: gapUris, provincia: provRegice || null }) })).cursos)
      if (cursos.length === 0 && provRegice) {
        cursos = utiles((await api('/api/perfiles/cursos-gap', { method: 'POST', body: JSON.stringify({ gap_skill_uris: gapUris }) })).cursos)
        cursosAlcance = 'país'
      }
    }

    perfiles.push({
      dni, nombre: det.personas?.nombre, ubicacion, provincia, skills: skills.length,
      m2: { since, fecha_max: fechaMax, compatibles: matches.length, con_avisos: conAvisos.length, otras_sin_avisos: otras.length, rank_principal: rankPrincipal || null, top10 },
      m3: {
        ocupacion: esp.principal, occ_id: occId, compatibilidad: gap.matchScore, ponderado: gap.weightedScore,
        cubiertas: gap.sharedEssential.length, total: gap.essentialTotal,
        faltantes: gap.gapEssential.map(s => s.label),
        cursos_alcance: cursosAlcance,
        cursos: cursos.slice(0, 3).map(c => ({
          titulo: c.titulo, institucion: c.institucion, provincia: c.provincia,
          cubre: c.skills_cubiertas, de: c.total_gap_skills ?? gapUris.length,
        })),
      },
    })
  }

  // === Texto libre ===
  const textoLibre = []
  for (const [frase, text] of Object.entries(FRASES)) {
    const t0 = Date.now()
    const d = await api('/api/skills-extract-from-text', { method: 'POST', body: JSON.stringify({ text }) })
    textoLibre.push({ frase, method: d.method, segundos: (Date.now() - t0) / 1000, competencias: (d.results || []).map((r: any) => r.label) })
  }

  const salida = { generado: new Date().toISOString(), base: BASE, perfiles, textoLibre }
  if (args.out) writeFileSync(args.out, JSON.stringify(salida, null, 1))
  console.log(JSON.stringify(salida, null, 1))
}

main().catch(e => { console.error(e); process.exit(1) })
