# SKILLS-EXTRACT-LLM — Reemplazar extractKeywords con Groq LLM

## Contexto

`/api/skills-extract-from-text` hoy usa `extractKeywords()` que produce
palabras sueltas ("colocar", "pisos") que el trigram matchea literalmente.
Resultado: skills irrelevantes en 6.6 segundos.

Este spec reemplaza `extractKeywords()` con una llamada a Groq (Llama 3.1)
que produce frases de skills normalizadas en contexto laboral argentino.
El resto del pipeline (trigram + pgvector) queda igual.

**Antes:**
```
texto → extractKeywords() → ["colocar", "pisos", "paredes"]
    → 6 RPCs secuenciales (~6.6s)
    → "colocar topes", "colocar atrezzo" (irrelevante)
```

**Después:**
```
texto → Groq (~0.3s) → ["colocación de pisos", "albañilería", "revoque de paredes"]
    → search_skills_by_text en paralelo (~0.5s)
    → "colocación de suelos", "albañilería", "aplicar revoque" (relevante)
```

---

## Pre-condición

```bash
# Verificar que GROQ_API_KEY está en Vercel environment variables
# Y que groq-sdk está instalado:
npm install groq-sdk
```

---

## Cambios requeridos

### 1. Instalar groq-sdk

```bash
npm install groq-sdk
```

### 2. Reemplazar extractKeywords con extractSkillsWithLLM

**En `/api/skills-extract-from-text/route.ts`:**

Reemplazar la función `extractKeywords()` con `extractSkillsWithLLM()`:

```typescript
import Groq from 'groq-sdk'

const groq = new Groq({ apiKey: process.env.GROQ_API_KEY })

async function extractSkillsWithLLM(text: string): Promise<string[]> {
  const completion = await groq.chat.completions.create({
    model: 'llama-3.1-8b-instant',  // rápido y gratuito
    max_tokens: 200,
    temperature: 0.1,  // respuestas consistentes
    messages: [
      {
        role: 'system',
        content: `Sos un experto en el mercado laboral argentino y la taxonomía ESCO de ocupaciones y competencias.
Tu tarea: dado un texto en español que describe experiencia laboral o habilidades, extraer entre 3 y 8 frases cortas que representen competencias laborales concretas.

Reglas:
- Usá frases de 2-4 palabras que matcheen con skills ESCO (ej: "soldadura MIG/MAG", "atención al cliente", "colocación de pisos")
- Priorizá competencias técnicas específicas sobre habilidades genéricas
- Usá vocabulario del mercado laboral argentino cuando corresponda
- Retorná SOLO un JSON array de strings, sin explicación ni texto adicional
- Ejemplo de output: ["albañilería", "colocación de pisos cerámicos", "revoque de paredes", "trabajo en altura"]`
      },
      {
        role: 'user',
        content: text
      }
    ]
  })

  const raw = completion.choices[0]?.message?.content?.trim() ?? '[]'
  
  try {
    // Limpiar posibles backticks o prefijos
    const cleaned = raw.replace(/```json|```/g, '').trim()
    const parsed = JSON.parse(cleaned)
    if (Array.isArray(parsed)) {
      return parsed.filter(s => typeof s === 'string' && s.length > 2).slice(0, 8)
    }
  } catch {
    // Fallback: intentar extraer strings del texto si el JSON falla
    const matches = raw.match(/"([^"]+)"/g)
    if (matches) return matches.map(m => m.replace(/"/g, '')).slice(0, 8)
  }
  
  return []
}
```

### 3. Hacer las RPCs en paralelo

Reemplazar el loop secuencial con Promise.all:

```typescript
// ANTES: loop secuencial (6 llamadas × ~1s = ~6s)
for (const keyword of keywords) {
  const result = await supabase.rpc('search_skills_by_text', ...)
}

// DESPUÉS: paralelo (~0.5s total)
const skillPhrases = await extractSkillsWithLLM(text)

const results = await Promise.all(
  skillPhrases.map(phrase => 
    supabase.rpc('search_skills_by_text', {
      query_text: phrase,
      similarity_min: 0.25,  // más permisivo con frases completas
      max_results: 5
    })
  )
)

// Aplanar y deduplicar por URI
const skillMap = new Map<string, { uri: string, label: string, score: number }>()
for (const result of results) {
  for (const skill of result.data ?? []) {
    if (!skillMap.has(skill.skill_uri) || skill.text_similarity > skillMap.get(skill.skill_uri)!.score) {
      skillMap.set(skill.skill_uri, {
        uri: skill.skill_uri,
        label: skill.skill_label,
        score: skill.text_similarity
      })
    }
  }
}
```

### 4. Fallback si Groq falla

Si la llamada a Groq falla (timeout, error de red, key inválida),
caer al comportamiento anterior con `extractKeywords()`:

```typescript
let skillPhrases: string[]
try {
  skillPhrases = await extractSkillsWithLLM(text)
  if (skillPhrases.length === 0) throw new Error('LLM returned empty')
} catch (err) {
  console.error('Groq fallback:', err)
  skillPhrases = extractKeywords(text)  // fallback al método anterior
}
```

**No eliminar `extractKeywords()`** — es el fallback.

---

## Criterios de aceptación

- [ ] `npm install groq-sdk` ejecutado sin errores
- [ ] `GROQ_API_KEY` configurada en Vercel environment variables
- [ ] Para "trabajé en construcción, sé levantar paredes y hacer revoques":
  - Retorna skills relacionadas con albañilería/construcción (no "colocar atrezzo")
  - Tiempo de respuesta < 2 segundos
- [ ] Para texto en blanco o muy corto → retorna array vacío, no error
- [ ] Si Groq falla → fallback a extractKeywords() sin romper la UI
- [ ] Las RPCs de Supabase se llaman en paralelo (Promise.all)

---

## Tests

`tests/skills-extract-llm.test.ts`
- Texto de construcción → skills de construcción (no skills irrelevantes)
- Texto vacío → array vacío
- Groq timeout → fallback a extractKeywords, no error 500
- Tiempo total < 2s para texto normal

---

## Notas

- Usar `llama-3.1-8b-instant` (no el 70B) — es más rápido (~0.2s vs ~0.8s)
  y suficiente para esta tarea de extracción de keywords.
  
- `temperature: 0.1` para respuestas consistentes — no queremos creatividad,
  queremos el mismo resultado para el mismo input.

- `similarity_min: 0.25` en search_skills_by_text es más permisivo que
  el default (0.2) porque ahora los inputs son frases completas ("colocación 
  de pisos") que matchean mejor con los labels ESCO que palabras sueltas.

- Si en producción el LLM produce frases muy largas o en inglés,
  agregar al prompt: "Respondé siempre en español, frases de máximo 4 palabras".

- El modelo `llama-3.1-8b-instant` tiene límite de 14,400 requests/día
  en el free tier de Groq. Para el volumen actual de la OE es más que suficiente.
  Si se escala, migrar a `llama-3.1-70b-versatile` (mismo límite pero más preciso).
