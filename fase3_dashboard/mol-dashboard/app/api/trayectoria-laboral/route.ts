import { NextRequest, NextResponse } from 'next/server'
import { getGroq, GROQ_MODEL_LARGE } from '@/lib/groq'
import { parseTrayectoria } from '@/lib/recomendacion-ia'
import { formatFecha } from '@/lib/ofertas-estado'

const SYSTEM_PROMPT = `Sos un asesor laboral de una oficina de empleo pública argentina.
Recibís las ocupaciones más compatibles con el perfil de una persona y tenés que recomendarle cuál le conviene más y qué hacer.

REGLAS ESTRICTAS:
- Usá SOLO los datos que te paso. No inventes cifras, duraciones, lugares, instituciones ni cursos.
- No menciones porcentajes ni cantidades: las cifras las muestra la pantalla.
- Cursos: mencioná solo cursos de la lista que te paso, con el nombre exacto. Si ninguna ocupación tiene cursos, "formacion" va vacío.
- Los datos de mercado son avisos publicados hasta la fecha indicada. No digas "vacantes disponibles".
- Para la demanda usá solo el indicador que te paso ("Demanda en alza", "estable", "en baja" o "sin datos de tendencia"). No hables de estabilidad ni volatilidad.
- Priorizá ocupaciones que cubren más competencias esenciales, con demanda en alza o estable, y con cursos para las que faltan.
- Tuteo rioplatense (vos, tenés, podés). No uses el nombre de la persona.
- Lenguaje claro, sin tecnicismos.

Respondé SOLO un objeto JSON con esta forma:
{
  "ocupacion": "nombre de la ocupación recomendada, tal como figura en la lista",
  "por_que": "máximo 2 oraciones",
  "alternativas": [{ "ocupacion": "nombre", "motivo": "1 oración" }],
  "pasos": ["1 oración", "1 oración", "1 oración"],
  "formacion": [{ "curso": "nombre exacto del curso", "motivo": "1 oración" }]
}
Máximo 3 alternativas, 3 pasos y 2 cursos.`

interface CursoInput { titulo: string; institucion?: string; modalidad?: string; provincia?: string; municipio?: string | null }
interface OcupacionInput {
  label: string
  cubiertas: number
  esenciales_total: number
  demanda: string
  gap_skills?: { label: string }[]
  cursos?: CursoInput[]
}

function buildUserPrompt(data: { fecha_max?: string; ocupacion_elegida?: { label: string } | null; top_ocupaciones: OcupacionInput[] }): string {
  let prompt = data.fecha_max ? `Datos de mercado: avisos publicados hasta el ${formatFecha(data.fecha_max)}.\n\n` : ''
  if (data.ocupacion_elegida) {
    prompt += `OCUPACIÓN QUE LA PERSONA ESTÁ MIRANDO: ${data.ocupacion_elegida.label}\n\n`
  }
  prompt += 'OCUPACIONES COMPATIBLES:\n\n'
  data.top_ocupaciones.forEach((occ, i) => {
    prompt += `${i + 1}. ${occ.label}\n`
    prompt += `   Cubre ${occ.cubiertas} de ${occ.esenciales_total} competencias esenciales. ${occ.demanda}.\n`
    if (occ.gap_skills?.length) prompt += `   Le faltan: ${occ.gap_skills.slice(0, 5).map(s => s.label).join(', ')}\n`
    if (occ.cursos?.length) {
      for (const c of occ.cursos) prompt += `   Curso: "${c.titulo}"\n`
    } else {
      prompt += '   Sin cursos para lo que le falta.\n'
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
      max_completion_tokens: 2048,
      temperature: 0.3,
      reasoning_effort: 'low',
      response_format: { type: 'json_object' },
      messages: [
        { role: 'system', content: SYSTEM_PROMPT },
        { role: 'user', content: buildUserPrompt(data) },
      ],
    })

    // Solo content: el reasoning del modelo no se lee. Los cursos se validan contra la lista enviada.
    const raw = completion.choices[0]?.message?.content?.trim() || ''
    const cursosPermitidos = (data.top_ocupaciones as OcupacionInput[]).flatMap(o => o.cursos || [])
    const recomendacion = parseTrayectoria(raw, cursosPermitidos)
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
