import { NextRequest, NextResponse } from 'next/server'
import { getGroq, GROQ_MODEL_LARGE } from '@/lib/groq'
import { parseTrayectoria } from '@/lib/recomendacion-ia'
import { formatFecha } from '@/lib/ofertas-estado'
import { provinciaDisplay } from '@/lib/cursos'

const SYSTEM_PROMPT = `Sos un orientador laboral de la Oficina de Empleo conversando con la persona en una entrevista. Hablale de vos, por su nombre de pila al empezar el diagnóstico, con calidez y sin vueltas. Sé honesto con las dificultades: si un camino es difícil, decilo y explicá por qué. No uses lenguaje de informe ni frases genéricas que le servirían a cualquiera.

Recibís las ocupaciones más compatibles con su perfil, con lo que ya sabe hacer, lo que le falta, los avisos publicados y los cursos disponibles cerca o a distancia.

REGLAS:
- Cifras: podés usar SOLO los números que te paso (competencias cubiertas sobre el total, cantidad de avisos) y la provincia. No agregues ningún otro número, porcentaje, duración ni plazo.
- Si cubre todas las competencias esenciales, decí "todas"; no lo presentes como si le faltara algo.
- Cursos: nombrá solo cursos de la lista que te paso, con su nombre exacto. No inventes cursos, instituciones ni lugares.
- Los datos de mercado son avisos publicados hasta la fecha indicada. No hables de "vacantes disponibles".
- Para la demanda usá solo el indicador que te paso ("Demanda en alza", "estable", "en baja" o "sin datos de tendencia"). No hables de estabilidad ni volatilidad.
- Nombrá competencias concretas de la lista (lo que ya sabe y lo que le falta), no categorías vagas.
- Voseo rioplatense en TODOS los verbos: tenés, manejás, cubrís, sabés, podés, vas a encontrar. Nunca tienes, manejas, cubres, sabes, puedes ni futuros como encontrarás.
- Los pasos tienen que ser concretos y empezar con un verbo en imperativo con voseo (Anotate, Armá, Practicá, Reforzá): una competencia para reforzar, un curso de la lista o una de estas acciones de la Oficina de Empleo, sin inventar otras: armar el CV con el orientador, anotarse en la bolsa de empleo de la Oficina, pedir una entrevista de orientación, preparar entrevistas laborales con el orientador. Nunca "postulá" a secas.
- Cuando digas qué cubre un curso, usá solo las competencias que te paso para ese curso.
- Los avisos son de todo el país, no de la provincia de la persona.
- No prometas resultados (empleo seguro, continuidad, que va a conseguir trabajo pronto).

Respondé SOLO un objeto JSON con esta forma:
{
  "ocupacion": "la ocupación que le recomendás, tal como figura en la lista",
  "diagnostico": "párrafo de 3 a 4 oraciones: empezá con su nombre de pila; dónde está hoy, qué lo hace fuerte (nombrá 1 o 2 competencias concretas) y qué le falta",
  "recomendacion": "párrafo de 2 a 3 oraciones: por qué este camino tiene sentido para esta persona",
  "alternativas": [{ "ocupacion": "tal como figura en la lista", "comentario": "1 o 2 oraciones honestas, también si no conviene" }],
  "pasos": [{ "accion": "1 oración concreta, en imperativo con voseo", "por_que": "1 oración" }],
  "cierre": "1 oración de aliento, sin exagerar"
}
Máximo 2 alternativas y 3 pasos.`

interface CursoInput { titulo: string; institucion?: string; modalidad?: string; provincia?: string; municipio?: string | null; cubre?: string[] }
interface OcupacionInput {
  label: string
  cubiertas: number
  esenciales_total: number
  avisos: number
  demanda: string
  fortalezas?: string[]
  gap_skills?: { label: string }[]
  cursos?: CursoInput[]
}

/** "Cubre 19 de 28" (con la calibración 100% = "todas"). */
function cobertura(cubiertas: number, total: number): string {
  if (total > 0 && cubiertas >= total) return `Cubre todas las competencias esenciales (${total} de ${total})`
  return `Cubre ${cubiertas} de ${total} competencias esenciales`
}

const titulo = (s: string) => s.toLowerCase().replace(/(^|\s)\S/g, m => m.toUpperCase())

function lugarCurso(c: CursoInput): string {
  if ((c.modalidad || '').toUpperCase() !== 'PRESENCIAL') return 'a distancia'
  return `presencial en ${[c.municipio && titulo(c.municipio), provinciaDisplay(c.provincia)].filter(Boolean).join(', ')}`
}

function buildUserPrompt(data: {
  perfil?: { nombre_pila?: string; provincia?: string | null }
  fecha_max?: string
  ocupacion_elegida?: { label: string } | null
  top_ocupaciones: OcupacionInput[]
}): string {
  let prompt = `PERSONA: ${data.perfil?.nombre_pila || 'la persona'}`
  prompt += data.perfil?.provincia ? `, vive en ${data.perfil.provincia}.\n` : '.\n'
  if (data.fecha_max) prompt += `Datos de mercado: avisos publicados hasta el ${formatFecha(data.fecha_max)}.\n`
  if (data.ocupacion_elegida) prompt += `Está mirando la ocupación: ${data.ocupacion_elegida.label}.\n`
  prompt += '\nOCUPACIONES COMPATIBLES (de mayor a menor cobertura):\n\n'
  data.top_ocupaciones.forEach((occ, i) => {
    prompt += `${i + 1}. ${occ.label}\n`
    prompt += `   ${cobertura(occ.cubiertas, occ.esenciales_total)}. ${occ.avisos} avisos publicados en todo el país. ${occ.demanda}.\n`
    if (occ.fortalezas?.length) prompt += `   Ya sabe: ${occ.fortalezas.slice(0, 4).join(', ')}\n`
    if (occ.gap_skills?.length) prompt += `   Le falta: ${occ.gap_skills.slice(0, 5).map(s => s.label).join(', ')}\n`
    if (occ.cursos?.length) {
      for (const c of occ.cursos) {
        prompt += `   Curso: "${c.titulo}" (${c.institucion ? `${c.institucion}, ` : ''}${lugarCurso(c)})`
        prompt += c.cubre?.length ? `. Cubre: ${c.cubre.slice(0, 4).join(', ')}\n` : '\n'
      }
    } else if (occ.gap_skills?.length) {
      prompt += '   No hay cursos en su provincia ni a distancia para lo que le falta.\n'
    }
    prompt += '\n'
  })
  return prompt
}

export async function POST(request: NextRequest) {
  const groq = getGroq()
  if (!groq) {
    return NextResponse.json({ recomendacion: null, disponible: false })
  }

  try {
    const data = await request.json()

    if (!Array.isArray(data.top_ocupaciones) || data.top_ocupaciones.length === 0) {
      return NextResponse.json({ error: 'Faltan ocupaciones' }, { status: 400 })
    }

    const completion = await groq.chat.completions.create({
      model: GROQ_MODEL_LARGE,
      max_completion_tokens: 3000,
      temperature: 0.5,
      reasoning_effort: 'low',
      response_format: { type: 'json_object' },
      messages: [
        { role: 'system', content: SYSTEM_PROMPT },
        { role: 'user', content: buildUserPrompt(data) },
      ],
    })

    // Solo content: el reasoning del modelo no se lee
    const raw = completion.choices[0]?.message?.content?.trim() || ''
    const recomendacion = parseTrayectoria(raw)
    if (!recomendacion) console.error('trayectoria-laboral: JSON inválido', raw.slice(0, 200))

    return NextResponse.json({
      recomendacion,
      disponible: !!recomendacion,
      model: GROQ_MODEL_LARGE,
      tokens_used: completion.usage?.total_tokens || 0,
    })
  } catch (error: any) {
    console.error('Error en trayectoria-laboral:', error?.message || error)
    return NextResponse.json({ recomendacion: null, disponible: false })
  }
}
