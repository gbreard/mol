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

const SYSTEM_PROMPT = `Sos un analista de política laboral del Observatorio de Empleo y Dinámica Empresarial (OEDE) de Argentina.
Tu rol es analizar una ocupación y sus posibilidades de reconversión ante escenarios de crisis laboral (cierre de empresa, caída de demanda sectorial, apertura de importaciones, automatización).

REGLAS:
- Usá SOLO los datos proporcionados. No inventes ocupaciones, cursos ni porcentajes.
- Analizá las ocupaciones similares como destinos de reconversión: cuáles tienen demanda activa, qué skills son transferibles, qué formación existe.
- Priorizá destinos con: muchas ofertas activas + alta similaridad de skills + cursos disponibles.
- Si hay ocupaciones similares sin ofertas, mencionalo como limitación.
- Mencioná explícitamente qué skills son transferibles (las que comparten) y cuáles requieren formación adicional.
- Si hay cursos del sistema de formación continua, nombralos como recurso concreto.
- Escribí para un técnico de política laboral que necesita fundamentar decisiones con datos.
- Usá lenguaje técnico pero claro. Podés usar porcentajes y cifras.
- Máximo 400 palabras.
- Formato: 3-4 párrafos. Sin bullets, sin markdown, sin títulos, sin emojis. Texto técnico fluido.
- Empezá directo con el análisis, no con "Ante un escenario..." genérico.`

function buildPrompt(data: any): string {
  const { ocupacion, similares, cursos } = data

  let prompt = `OCUPACIÓN ANALIZADA: ${ocupacion.label} (ISCO ${ocupacion.isco_code})\n`
  prompt += `Ofertas activas: ${ocupacion.ofertas_total}\n`
  prompt += `Skills esenciales (${ocupacion.skills_esenciales.length}): ${ocupacion.skills_esenciales.join(', ')}\n`
  if (ocupacion.skills_opcionales_count > 0) {
    prompt += `Skills opcionales: ${ocupacion.skills_opcionales_count}\n`
  }
  if (ocupacion.knowledge_esenciales?.length > 0) {
    prompt += `Conocimientos clave: ${ocupacion.knowledge_esenciales.join(', ')}\n`
  }
  prompt += '\n'

  if (similares && similares.length > 0) {
    prompt += `OCUPACIONES SIMILARES (por skills compartidas):\n`
    for (const s of similares) {
      prompt += `- ${s.label} (ISCO ${s.isco_code}): ${Math.round(s.similarity * 100)}% similaridad, ${s.ofertas} ofertas activas\n`
    }
    prompt += '\n'
  }

  if (cursos && cursos.length > 0) {
    prompt += `CURSOS DE FORMACIÓN DISPONIBLES:\n`
    for (const c of cursos) {
      prompt += `- "${c.titulo}" en ${c.institucion} (${c.provincia}): cubre ${c.skills_cubiertas} skills\n`
    }
    prompt += '\n'
  } else {
    prompt += `CURSOS: No se encontraron cursos de formación vinculados a esta ocupación.\n\n`
  }

  prompt += `Analizá las opciones de reconversión para trabajadores de "${ocupacion.label}" en un escenario de crisis. Identificá las mejores trayectorias considerando transferibilidad de skills, demanda de mercado y formación disponible.`
  return prompt
}

export async function POST(request: NextRequest) {
  const groq = getGroq()
  if (!groq) {
    return NextResponse.json({ error: 'Servicio de IA no configurado' }, { status: 500 })
  }

  try {
    const data = await request.json()
    if (!data.ocupacion?.label) {
      return NextResponse.json({ error: 'Falta la ocupación' }, { status: 400 })
    }

    const userPrompt = buildPrompt(data)

    const completion = await groq.chat.completions.create({
      model: 'llama-3.3-70b-versatile',
      max_tokens: 800,
      temperature: 0.3,
      messages: [
        { role: 'system', content: SYSTEM_PROMPT },
        { role: 'user', content: userPrompt },
      ],
    })

    const text = completion.choices[0]?.message?.content?.trim() || ''
    return NextResponse.json({
      recomendacion: text,
      model: 'llama-3.3-70b-versatile',
      tokens_used: completion.usage?.total_tokens || 0,
    })
  } catch (error: any) {
    console.error('Error en analisis-ocupacional:', error?.message || error)
    return NextResponse.json({ error: 'Error generando análisis' }, { status: 500 })
  }
}
