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
Tu rol es interpretar datos del mercado laboral y sugerir trayectorias de formación realistas.

REGLAS ESTRICTAS:
- Usá SOLO los datos proporcionados. No inventes cursos, instituciones, porcentajes ni ocupaciones.
- Si la tendencia es "insuficiente", decí que no hay datos suficientes para evaluar el mercado de esa ocupación.
- Si el gap es chico (1-2 skills), enfocá en el camino corto y concreto.
- Si el gap es grande (>5 skills), sugerí considerar las alternativas con mejor match que se proporcionan.
- Mencioná la volatilidad si es "volatil" como factor de riesgo.
- Si hay cursos disponibles, nombralos por nombre e institución. No inventes cursos que no estén en los datos.
- Usá lenguaje claro, sin tecnicismos. El usuario puede no tener formación universitaria.
- Tuteá al usuario (vos, tu, te). No uses usted.
- Máximo 200 palabras.
- Formato: 2-3 párrafos cortos, texto natural. Sin bullets, sin títulos, sin markdown, como si le hablaras a la persona cara a cara.
- No digas "basado en los datos" ni "según el análisis". Hablá directo.`

function buildUserPrompt(data: any): string {
  const { perfil, ocupacion, tendencia, gap_skills, skills_tiene, cursos, alternativas } = data

  let prompt = `PERFIL: ${perfil.nombre}`
  if (perfil.edad) prompt += `, ${perfil.edad} años`
  if (perfil.ubicacion) prompt += `, ${perfil.ubicacion}`
  if (perfil.nivel_educativo) prompt += `, ${perfil.nivel_educativo}`
  prompt += `. Tiene ${perfil.skills_count} competencias confirmadas.\n\n`

  prompt += `OCUPACIÓN OBJETIVO: ${ocupacion.label} (ISCO ${ocupacion.isco_code})\n`
  prompt += `Compatibilidad: ${ocupacion.compatibilidad}% (${ocupacion.cubiertas} de ${ocupacion.esenciales_total} skills esenciales cubiertas)\n\n`

  if (tendencia) {
    prompt += `MERCADO: `
    if (tendencia.trend_label === 'insuficiente') {
      prompt += `Datos insuficientes para evaluar tendencia.\n`
    } else {
      prompt += `${tendencia.ofertas_total} ofertas. Tendencia: ${tendencia.trend_label}. Estabilidad: ${tendencia.volatilidad}.\n`
    }
    prompt += '\n'
  }

  if (gap_skills && gap_skills.length > 0) {
    prompt += `SKILLS QUE LE FALTAN (${gap_skills.length}):\n`
    for (const s of gap_skills.slice(0, 8)) {
      prompt += `- ${s.label}`
      if (s.frecuencia_mercado) prompt += ` (pedida en ${s.frecuencia_mercado}% de ofertas)`
      prompt += '\n'
    }
    if (gap_skills.length > 8) prompt += `- ... y ${gap_skills.length - 8} más\n`
    prompt += '\n'
  }

  if (skills_tiene && skills_tiene.length > 0) {
    prompt += `SKILLS FUERTES QUE YA TIENE: ${skills_tiene.slice(0, 5).map((s: any) => s.label).join(', ')}\n\n`
  }

  if (cursos && cursos.length > 0) {
    prompt += `CURSOS DISPONIBLES QUE CUBREN EL GAP:\n`
    for (const c of cursos.slice(0, 5)) {
      prompt += `- "${c.titulo}" en ${c.institucion} (${c.provincia || 'sin sede'}): cubre ${c.skills_cubiertas} skill${c.skills_cubiertas !== 1 ? 's' : ''} del gap\n`
    }
    prompt += '\n'
  } else {
    prompt += `CURSOS: No se encontraron cursos que cubran el gap de esta ocupación.\n\n`
  }

  if (alternativas && alternativas.length > 0) {
    prompt += `OCUPACIONES ALTERNATIVAS (mejor match o más ofertas):\n`
    for (const a of alternativas.slice(0, 3)) {
      prompt += `- ${a.label}: ${a.match}% match, ${a.ofertas} ofertas, ${a.tendencia}\n`
    }
    prompt += '\n'
  }

  prompt += `Dále una recomendación personalizada a ${perfil.nombre.split(' ')[0]}.`
  return prompt
}

export async function POST(request: NextRequest) {
  const groq = getGroq()
  if (!groq) {
    return NextResponse.json({ error: 'Servicio de IA no configurado' }, { status: 500 })
  }

  try {
    const data = await request.json()

    if (!data.perfil?.nombre || !data.ocupacion?.label) {
      return NextResponse.json({ error: 'Faltan datos del perfil u ocupación' }, { status: 400 })
    }

    const userPrompt = buildUserPrompt(data)

    const completion = await groq.chat.completions.create({
      model: 'llama-3.3-70b-versatile',
      max_tokens: 400,
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
