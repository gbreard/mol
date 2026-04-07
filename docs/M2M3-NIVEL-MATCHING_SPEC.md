# M2M3-NIVEL-MATCHING — Peso por nivel de maestría en matching

## Contexto

El matchScore hoy es binario: tiene la skill (1) o no la tiene (0).
Este spec agrega peso por nivel de maestría al cálculo, y de paso
extrae la lógica duplicada de M2 y M3 a una función compartida.

---

## Decisión de diseño — pesos por nivel

| Nivel | Peso |
|-------|------|
| básico | 0.40 |
| intermedio | 0.65 |
| avanzado | 0.85 |
| experto | 1.00 |
| sin nivel (null) | 0.65 (mismo que intermedio) |

**Razonamiento:**
- básico (0.40): tiene la skill pero no suficiente para desempeñarse
  solo — necesita supervisión
- intermedio (0.65): puede trabajar autónomamente en la mayoría 
  de situaciones
- avanzado (0.85): domina la skill, puede enseñar a otros
- experto (1.00): nivel máximo, no hay gap adicional

**El matchScore resultante sigue siendo 0-100%** — es la suma de
pesos de skills cubiertas dividido el total de skills esenciales.
Una persona con todas las skills esenciales en nivel experto = 100%.
Una persona con todas las skills en nivel básico ≈ 40%.

---

## Parte 1 — Función utilitaria compartida

**Nuevo archivo:** `lib/matching.ts`

```typescript
export type NivelMaestria = 'basico' | 'intermedio' | 'avanzado' | 'experto'

export const NIVEL_WEIGHTS: Record<NivelMaestria | 'default', number> = {
  basico:     0.40,
  intermedio: 0.65,
  avanzado:   0.85,
  experto:    1.00,
  default:    0.65,  // fallback si nivel es null/undefined
}

export interface ProfileSkill {
  skill_uri:  string
  nivel?:     NivelMaestria | null
}

export interface OccupationSkill {
  id:    string   // UUID corto (sin prefijo URI)
  label: string
}

const ESCO_PREFIX = 'http://data.europa.eu/esco/skill/'

/**
 * Calcula el matchScore ponderado por nivel de maestría.
 * 
 * @param profileSkills  Skills del perfil de la persona con nivel
 * @param essentialSkills Skills esenciales de la ocupación (id corto)
 * @param optionalSkills  Skills opcionales de la ocupación (id corto)
 * @returns {
 *   matchScore:        0-100 ponderado por nivel
 *   essentialCovered:  skills esenciales cubiertas (con peso)
 *   essentialTotal:    total skills esenciales
 *   sharedEssential:   skills esenciales que tiene (para gap)
 *   sharedOptional:    skills opcionales que tiene
 *   gapEssential:      skills esenciales que le faltan
 *   gapOptional:       skills opcionales que le faltan
 *   transferable:      skills del perfil no requeridas por la ocupación
 * }
 */
export function calculateOccupationMatch(
  profileSkills:  ProfileSkill[],
  essentialSkills: OccupationSkill[],
  optionalSkills:  OccupationSkill[] = []
) {
  // Construir Map<uri_completa, nivel> del perfil
  const profileMap = new Map<string, NivelMaestria | null>()
  for (const s of profileSkills) {
    profileMap.set(s.skill_uri, s.nivel ?? null)
  }

  const allOccSkills = [...essentialSkills, ...optionalSkills]
  const essentialUris = new Set(essentialSkills.map(s => ESCO_PREFIX + s.id))
  const allOccUris    = new Set(allOccSkills.map(s => ESCO_PREFIX + s.id))

  // Skills esenciales cubiertas con peso ponderado
  let weightedCovered = 0
  const sharedEssential: OccupationSkill[] = []
  const gapEssential:    OccupationSkill[] = []

  for (const skill of essentialSkills) {
    const uri   = ESCO_PREFIX + skill.id
    const nivel = profileMap.get(uri)
    if (profileMap.has(uri)) {
      const weight = NIVEL_WEIGHTS[nivel ?? 'default'] ?? NIVEL_WEIGHTS.default
      weightedCovered += weight
      sharedEssential.push(skill)
    } else {
      gapEssential.push(skill)
    }
  }

  // Skills opcionales cubiertas (sin peso — son bonus)
  const sharedOptional: OccupationSkill[] = []
  const gapOptional:    OccupationSkill[] = []

  for (const skill of optionalSkills) {
    const uri = ESCO_PREFIX + skill.id
    if (profileMap.has(uri)) {
      sharedOptional.push(skill)
    } else {
      gapOptional.push(skill)
    }
  }

  // Skills transferibles (tiene pero la ocupación no pide)
  const transferable: ProfileSkill[] = profileSkills.filter(
    s => !allOccUris.has(s.skill_uri)
  )

  // matchScore: suma de pesos / total esenciales × 100
  const matchScore = essentialSkills.length > 0
    ? Math.round((weightedCovered / essentialSkills.length) * 100)
    : 0

  return {
    matchScore,
    essentialCovered: weightedCovered,  // suma de pesos (no conteo)
    essentialTotal:   essentialSkills.length,
    sharedEssential,
    sharedOptional,
    gapEssential,
    gapOptional,
    transferable,
  }
}
```

---

## Parte 2 — Cambios en M2 (matching/page.tsx)

**Cambiar el Set de URIs a un array de ProfileSkill:**

```typescript
// ANTES:
const uris = new Set<string>(skills.map((s: any) => s.skill_uri))
setProfileSkillUris(uris)

// DESPUÉS:
const profileSkills: ProfileSkill[] = skills.map((s: any) => ({
  skill_uri: s.skill_uri,
  nivel: s.nivel ?? null
}))
setProfileSkills(profileSkills)
```

**Reemplazar el useMemo de matching:**

```typescript
// ANTES: cálculo inline con Set.has()
// DESPUÉS: usar calculateOccupationMatch
const matchingOccupations = useMemo(() => {
  if (!occupationsData || !profileSkills.length) return []
  
  const results = []
  for (const [id, occ] of Object.entries(occupationsData)) {
    const { matchScore, essentialTotal, sharedEssential, gapEssential } = 
      calculateOccupationMatch(
        profileSkills,
        occ.skills?.essential ?? [],
        occ.skills?.optional  ?? []
      )
    
    if (sharedEssential.length === 0) continue  // sin overlap real
    
    results.push({
      id, label: occ.label, isco: occ.isco,
      matchScore,
      essentialTotal,
      essentialCovered: sharedEssential.length,
      gapCount: gapEssential.length,
      gapSkills: gapEssential,
    })
  }
  
  return results.sort((a, b) => b.matchScore - a.matchScore)
}, [occupationsData, profileSkills])
```

---

## Parte 3 — Cambios en M3 (futuro/page.tsx)

**Agregar nivel al mapeo de perfilSkills:**

```typescript
// ANTES:
setPerfilSkills(data.skills.map((s: any) => ({
  skill_uri: s.skill_uri,
  skill_label: s.skill_label,
  type: s.via_captura,
})))

// DESPUÉS:
setPerfilSkills(data.skills.map((s: any) => ({
  skill_uri:  s.skill_uri,
  skill_label: s.skill_label,
  type:       s.via_captura,
  nivel:      s.nivel ?? null,
})))
```

**Reemplazar los tres cálculos duplicados** (líneas 149, 195 y el de 
caminos alternativos) con `calculateOccupationMatch`:

```typescript
const gapAnalysis = useMemo(() => {
  if (!perfil || !occDetail) return null
  
  return calculateOccupationMatch(
    perfilSkills,
    occDetail.skills?.essential ?? [],
    occDetail.skills?.optional  ?? []
  )
}, [perfilSkills, occDetail])

// compatibility = gapAnalysis.matchScore
// sharedEssential = gapAnalysis.sharedEssential
// gapEssential = gapAnalysis.gapEssential
// etc.
```

---

## Criterios de aceptación

- [ ] `lib/matching.ts` exporta `calculateOccupationMatch`
- [ ] M2: skills del perfil incluyen nivel en el matching
- [ ] M2: persona con skills en nivel experto obtiene mayor matchScore
  que la misma persona con las mismas skills en nivel básico
- [ ] M3: gapAnalysis usa calculateOccupationMatch (no cálculo inline)
- [ ] M3: compatibility refleja nivel de maestría
- [ ] Los tres cálculos duplicados de M3 reemplazados por la función
- [ ] Una persona sin nivel en sus skills (null) → peso 0.65 (intermedio)
- [ ] Persona con 0 skills esenciales en común → no aparece en M2

---

## Tests

`tests/lib-matching.test.ts`
- Skills todas en experto → matchScore = 100%
- Skills todas en básico → matchScore = 40%
- Skills mixtas → matchScore ponderado correcto
- Sin skills del perfil → matchScore = 0
- Sin esenciales de ocupación → matchScore = 0
- nivel null → usa peso 0.65

`tests/m2-matching-nivel.test.ts`
- Perfil con nivel avanzado matchea mejor que mismo perfil en básico
- Persona sin overlap → no aparece en resultados

---

## Notas

- El matchScore ponderado puede sorprender al técnico si ve "87% de 
  compatibilidad" pero la persona tiene todas las skills en nivel básico.
  Considerar mostrar en la card de M2 tanto el matchScore ponderado 
  como el conteo raw "N de M esenciales". Ya se muestra el conteo — 
  mantenerlo para dar contexto al %.
  
- Los pesos (0.40 / 0.65 / 0.85 / 1.00) son una propuesta inicial.
  Con datos reales se puede calibrar. Si el sistema subestima o 
  sobreestima compatibilidades, ajustar los pesos antes de tocar 
  la arquitectura.

- No cambiar el cálculo de `get_cursos_for_gap` — ese cruza por URI
  exacta sin nivel. El nivel no afecta qué cursos se recomiendan,
  solo el score de compatibilidad.
