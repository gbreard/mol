import { NextRequest, NextResponse } from 'next/server'
import { getGroq, GROQ_MODEL_LARGE } from '@/lib/groq'
import { parseAnalisis } from '@/lib/recomendacion-ia'
import { formatFecha } from '@/lib/ofertas-estado'

const SYSTEM_PROMPT = `Sos un analista de política laboral del Observatorio de Empleo y Dinámica Empresarial (OEDE) de Argentina.
Analizás una ocupación y sus opciones de reconversión ante un escenario de crisis (cierre de empresa, caída de demanda sectorial, apertura de importaciones, automatización).

REGLAS ESTRICTAS:
- Usá SOLO los datos que te paso. No inventes ocupaciones, cifras, duraciones, lugares, instituciones ni cursos.
- No menciones porcentajes ni cantidades y no escribas números: las cifras las muestra la pantalla.
- Cursos: mencioná solo cursos de la lista que te paso, con el nombre exacto. Si no hay cursos, "formacion" va vacío.
- Los datos de mercado son avisos publicados hasta la fecha indicada. No uses la palabra "vacante": hablá de avisos publicados.
- Para la demanda usá solo el indicador que te paso ("Demanda en alza", "estable", "en baja" o "sin datos de tendencia"). No hables de estabilidad ni volatilidad.
- Priorizá destinos con más competencias compartidas, demanda en alza o estable y cursos disponibles.
- Escribí para un técnico de política laboral: claro, técnico, sin muletillas.

Respondé SOLO un objeto JSON con esta forma:
{
  "resumen": "diagnóstico de la ocupación, máximo 2 oraciones",
  "destinos": [{ "ocupacion": "nombre tal como figura en la lista", "motivo": "1 oración" }],
  "recomendaciones": ["1 oración", "1 oración", "1 oración"],
  "formacion": [{ "curso": "nombre exacto del curso", "motivo": "1 oración" }]
}
Máximo 3 destinos, 3 recomendaciones y 2 cursos.`

interface CursoInput { titulo: string }
interface SimilarInput { label: string; afinidad: string; demanda: string; cursos?: CursoInput[] }

function buildPrompt(data: any): string {
  const { ocupacion, similares, cursos_ocupacion, fecha_max } = data
  let prompt = fecha_max ? `Datos de mercado: avisos publicados hasta el ${formatFecha(fecha_max)}.\n\n` : ''
  prompt += `OCUPACIÓN ANALIZADA: ${ocupacion.label}. ${ocupacion.demanda}.\n`
  if (ocupacion.skills_esenciales?.length) prompt += `Competencias esenciales: ${ocupacion.skills_esenciales.join(', ')}\n`
  if (cursos_ocupacion?.length) {
    prompt += 'Cursos para esta ocupación:\n'
    for (const c of cursos_ocupacion as CursoInput[]) prompt += `- "${c.titulo}"\n`
  }
  if (similares?.length) {
    prompt += '\nOCUPACIONES DESTINO DE RECONVERSIÓN (por competencias compartidas):\n'
    for (const s of similares as SimilarInput[]) {
      prompt += `• ${s.label}: afinidad ${s.afinidad}. ${s.demanda}.\n`
      if (s.cursos?.length) for (const c of s.cursos) prompt += `  Curso: "${c.titulo}"\n`
      else prompt += '  Sin cursos de formación disponibles.\n'
    }
  }
  return prompt
}

export async function POST(request: NextRequest) {
  const groq = getGroq()
  if (!groq) {
    return NextResponse.json({ recomendacion: null, disponible: false })
  }

  try {
    const data = await request.json()
    if (!data.ocupacion?.label) {
      return NextResponse.json({ error: 'Falta la ocupación' }, { status: 400 })
    }

    const completion = await groq.chat.completions.create({
      model: GROQ_MODEL_LARGE,
      max_completion_tokens: 2048,
      temperature: 0.3,
      reasoning_effort: 'low',
      response_format: { type: 'json_object' },
      messages: [
        { role: 'system', content: SYSTEM_PROMPT },
        { role: 'user', content: buildPrompt(data) },
      ],
    })

    // Solo content; los cursos se validan contra la lista enviada
    const raw = completion.choices[0]?.message?.content?.trim() || ''
    const cursosPermitidos = [
      ...(data.cursos_ocupacion || []),
      ...((data.similares || []) as SimilarInput[]).flatMap(s => s.cursos || []),
    ]
    const recomendacion = parseAnalisis(raw, cursosPermitidos)
    if (!recomendacion) console.error('analisis-ocupacional: JSON inválido', raw.slice(0, 200))

    return NextResponse.json({
      recomendacion,
      disponible: !!recomendacion,
      model: GROQ_MODEL_LARGE,
      tokens_used: completion.usage?.total_tokens || 0,
    })
  } catch (error: any) {
    console.error('Error en analisis-ocupacional:', error?.message || error)
    return NextResponse.json({ recomendacion: null, disponible: false })
  }
}
