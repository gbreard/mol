import { NextRequest, NextResponse } from 'next/server'
import Groq from 'groq-sdk'

let _groq: Groq | null = null
function getGroq(): Groq | null {
  if (_groq) return _groq
  const key = process.env.GROQ_API_KEY
  if (!key) return null
  _groq = new Groq({ apiKey: key })
  return _groq
}

const SYSTEM_PROMPT = `Sos un asesor laboral de una oficina de empleo pública argentina.
Tu rol es interpretar datos del mercado laboral y sugerir trayectorias de formación concretas.

REGLAS ESTRICTAS:
- Usá SOLO los datos proporcionados. No inventes cursos, instituciones, porcentajes ni ocupaciones.
- Se te dan las TOP ocupaciones compatibles con el perfil, cada una con su compatibilidad, gap, tendencia de demanda y cursos. Analizá todas y recomendá cuál conviene más, explicando por qué.
- Priorizá ocupaciones con: alto match + demanda creciente o estable + gap cubierto por cursos disponibles.
- Si una ocupación tiene demanda cayendo o volátil, mencionalo como riesgo.
- Si la tendencia es "insuficiente", decí que no hay datos suficientes de mercado para esa ocupación.
- Si hay cursos que cubren el gap, nombralos por nombre e institución exactos. No inventes cursos.
- Si no hay cursos para una ocupación, decilo.
- Usá lenguaje claro, sin tecnicismos. El usuario puede no tener formación universitaria.
- Tuteá al usuario (vos, tu, te). No uses usted.
- Máximo 350 palabras.
- Formato: 3-4 párrafos cortos, texto natural. Sin bullets, sin títulos, sin markdown, sin emojis, como si le hablaras a la persona cara a cara en la oficina de empleo.
- No digas "basado en los datos" ni "según el análisis". Hablá directo.
- Empezá con el nombre de la persona.`

function buildUserPrompt(data: any): string {
  const { perfil, ocupacion_elegida, top_ocupaciones } = data

  let prompt = `PERFIL: ${perfil.nombre}`
  if (perfil.edad) prompt += `, ${perfil.edad} años`
  if (perfil.ubicacion) prompt += `, ${perfil.ubicacion}`
  if (perfil.nivel_educativo) prompt += `, ${perfil.nivel_educativo}`
  prompt += `. Tiene ${perfil.skills_count} competencias confirmadas.\n\n`

  if (ocupacion_elegida) {
    prompt += `OCUPACIÓN ELEGIDA POR EL USUARIO: ${ocupacion_elegida.label} (ISCO ${ocupacion_elegida.isco_code})\n`
    prompt += `Compatibilidad: ${ocupacion_elegida.compatibilidad}% (${ocupacion_elegida.cubiertas} de ${ocupacion_elegida.esenciales_total} esenciales)\n\n`
  }

  if (top_ocupaciones && top_ocupaciones.length > 0) {
    prompt += `TOP ${top_ocupaciones.length} OCUPACIONES COMPATIBLES CON ESTE PERFIL:\n\n`
    for (let i = 0; i < top_ocupaciones.length; i++) {
      const occ = top_ocupaciones[i]
      prompt += `${i + 1}. ${occ.label} (ISCO ${occ.isco_code})\n`
      prompt += `   Match: ${occ.compatibilidad}% (${occ.cubiertas}/${occ.esenciales_total} esenciales)\n`

      // Tendencia
      if (occ.tendencia) {
        if (occ.tendencia.trend_label === 'insuficiente') {
          prompt += `   Mercado: ${occ.tendencia.ofertas_total} ofertas. Sin datos suficientes de tendencia.\n`
        } else {
          prompt += `   Mercado: ${occ.tendencia.ofertas_total} ofertas. Tendencia: ${occ.tendencia.trend_label}. Estabilidad: ${occ.tendencia.volatilidad}.\n`
        }
      }

      // Gap
      if (occ.gap_skills && occ.gap_skills.length > 0) {
        const gapList = occ.gap_skills.slice(0, 5).map((s: any) => {
          let txt = s.label
          if (s.frecuencia_mercado) txt += ` (${s.frecuencia_mercado}% ofertas la piden)`
          return txt
        }).join(', ')
        prompt += `   Le faltan ${occ.gap_skills.length} skills: ${gapList}\n`
      } else {
        prompt += `   No le falta ninguna skill esencial.\n`
      }

      // Cursos
      if (occ.cursos && occ.cursos.length > 0) {
        for (const c of occ.cursos.slice(0, 3)) {
          prompt += `   Curso: "${c.titulo}" en ${c.institucion} (${c.provincia || 'sin sede'}) — cubre ${c.skills_cubiertas} skill${c.skills_cubiertas !== 1 ? 's' : ''} del gap\n`
        }
      } else {
        prompt += `   Sin cursos disponibles para cubrir el gap.\n`
      }
      prompt += '\n'
    }
  }

  const nombre = perfil.nombre.split(' ')[0]
  prompt += `Analizá las opciones y dále a ${nombre} una recomendación concreta: cuál ocupación le conviene más y qué pasos seguir. Si la elegida no es la mejor opción, decíselo con tacto y explicá por qué otra puede ser mejor.`
  return prompt
}

export async function POST(request: NextRequest) {
  const groq = getGroq()
  if (!groq) {
    return NextResponse.json({ error: 'Servicio de IA no configurado' }, { status: 500 })
  }

  try {
    const data = await request.json()

    if (!data.perfil?.nombre) {
      return NextResponse.json({ error: 'Faltan datos del perfil' }, { status: 400 })
    }

    const userPrompt = buildUserPrompt(data)

    const completion = await groq.chat.completions.create({
      model: 'llama-3.3-70b-versatile',
      max_tokens: 700,
      temperature: 0.3,
      messages: [
        { role: 'system', content: SYSTEM_PROMPT },
        { role: 'user', content: userPrompt },
      ],
    })

    const text = completion.choices[0]?.message?.content?.trim() || ''
    const tokens = completion.usage?.total_tokens || 0

    return NextResponse.json({
      recomendacion: text,
      model: 'llama-3.3-70b-versatile',
      tokens_used: tokens,
    })
  } catch (error: any) {
    console.error('Error en trayectoria-laboral:', error?.message || error)
    return NextResponse.json(
      { error: 'Error generando recomendación. Intentá de nuevo.' },
      { status: 500 }
    )
  }
}
