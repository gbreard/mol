# POL-CURSOS-OCUPACIONES — Cursos en Ocupaciones y Comparar (Políticas Laborales)

## Contexto

Diego pide agregar cursos de formación en dos lugares de Políticas Laborales:

**Spec 12 — OccupationDetail:** mostrar cursos disponibles para la ocupación
seleccionada, debajo de las ocupaciones similares.

**Spec 13 — OccupationCompare:** mostrar cursos que cubren las skills del gap
(lo que le falta a la ocupación A para llegar a la B).

**Fuente de datos:** RPC `get_cursos_for_gap` ya existe en Supabase.
Para OccupationDetail: se pasan las URIs de skills esenciales de la ocupación.
Para OccupationCompare: se pasan las URIs de skills del gap (gapToCover).

**Estos componentes son puramente informativos** — no tienen contexto de
persona ni perfil. Los cursos son generales para la ocupación/gap, no
personalizados.

---

## Pre-condición (verificar antes de arrancar)

```sql
-- get_cursos_for_gap debe responder con skills de una ocupación
SELECT * FROM get_cursos_for_gap(
  ARRAY[
    'http://data.europa.eu/esco/skill/URI_REAL_1',
    'http://data.europa.eu/esco/skill/URI_REAL_2'
  ],
  NULL,
  5
);
-- Debe retornar cursos con titulo, institucion, provincia, modalidad
```

---

## Parte 1 — Cambios en OccupationDetail (Spec 12)

### Nuevo bloque debajo de Ocupaciones Similares

En el panel izquierdo (2/3), debajo de Conocimientos, agregar:

```
┌─────────────────────────────────────────────────────────────┐
│  📚 Cursos del sistema de formación continua del STEySS     │
│  Formación disponible para esta ocupación                   │
├─────────────────────────────────────────────────────────────┤
│  Instalaciones eléctricas domiciliarias                     │
│  CFL Comunidad Organizada · Berisso, Buenos Aires           │
│  Presencial · 163hs                                         │
│                                                             │
│  Electricidad industrial                                    │
│  INET · Córdoba Capital, Córdoba                            │
│  Presencial · 120hs                                         │
│                                                             │
│  [Ver más cursos]  ← si hay más de 3                       │
└─────────────────────────────────────────────────────────────┘
```

### Lógica de carga

```typescript
// Al cambiar la ocupación seleccionada:
const skillUris = (occDetail.skills?.essential ?? [])
  .map(s => `http://data.europa.eu/esco/skill/${s.id}`)

// Si hay skills esenciales, buscar cursos
if (skillUris.length > 0) {
  const res = await fetch('/api/perfiles/cursos-gap', {
    method: 'POST',
    body: JSON.stringify({ gap_skill_uris: skillUris })
  })
  const data = await res.json()
  setCursos(data.cursos.slice(0, 3))  // mostrar 3 por defecto
}
```

**Estado loading/empty:**
- Loading: spinner pequeño "Buscando cursos..."
- Sin resultados: "No hay cursos registrados para esta ocupación"
- Con resultados: lista de cursos

**"Ver más":** expande a todos los cursos del fetch (máx 20) sin
nuevo request.

### Rediseño del layout según Diego

Diego propone este orden:
1. Parte superior: competencias y conocimientos (ya está)
2. Ocupaciones similares (ya está, columna derecha)
3. **Cursos de formación (NUEVO)** — debajo, span completo

El layout actual es grid 2/3 + 1/3. Los cursos van en el panel
izquierdo debajo de Conocimientos — mantener el grid existente,
no rediseñar el layout completo.

---

## Parte 2 — Cambios en OccupationCompare (Spec 13)

### Nuevo bloque debajo del gap

OccupationCompare muestra el gap entre dos ocupaciones. Debajo de
la lista de skills que le faltan a A para llegar a B, agregar:

```
┌─────────────────────────────────────────────────────────────┐
│  📚 Cursos para cubrir el gap                               │
│  Formación que cubre las competencias faltantes             │
├─────────────────────────────────────────────────────────────┤
│  Instalaciones eléctricas domiciliarias                     │
│  CFL Comunidad Organizada · Berisso, Buenos Aires           │
│  Presencial · 163hs · Cubre 5 de 8 faltantes               │
│                                                             │
│  [Ver más cursos]                                           │
└─────────────────────────────────────────────────────────────┘
```

### Lógica de carga

```typescript
// gapToCover ya existe en OccupationCompare
// Son las skills de B que A no tiene
const gapUris = gapAnalysis.gapToCover
  .map(s => `http://data.europa.eu/esco/skill/${s.id}`)

if (gapUris.length > 0) {
  const res = await fetch('/api/perfiles/cursos-gap', {
    method: 'POST',
    body: JSON.stringify({ gap_skill_uris: gapUris })
  })
  const data = await res.json()
  setCursosGap(data.cursos.slice(0, 3))
}
```

**Cuándo mostrar:** solo cuando hay gap > 0. Si las dos ocupaciones
son idénticas (gap = 0), no mostrar el bloque.

**"Cubre N de M faltantes":** usar `skills_cubiertas` y
`total_gap_skills` del response — ya los retorna `get_cursos_for_gap`.

---

## Estado React a agregar

### En OccupationDetail:
```typescript
const [cursos, setCursos]             = useState<CursoGap[]>([])
const [loadingCursos, setLoadingCursos] = useState(false)
const [showAllCursos, setShowAllCursos] = useState(false)
```

### En OccupationCompare:
```typescript
const [cursosGap, setCursosGap]           = useState<CursoGap[]>([])
const [loadingCursosGap, setLoadingCursosGap] = useState(false)
const [showAllCursosGap, setShowAllCursosGap] = useState(false)
```

---

## Criterios de aceptación

**OccupationDetail:**
- [ ] Al seleccionar una ocupación, se cargan cursos debajo de Conocimientos
- [ ] Muestra 3 cursos por defecto con titulo, institución, provincia, modalidad, horas
- [ ] "Ver más" expande sin nuevo fetch
- [ ] Si 0 cursos: mensaje "No hay cursos registrados"
- [ ] Al cambiar de ocupación, los cursos se actualizan
- [ ] El texto "REGICE" nunca aparece en la UI
- [ ] Título: "Cursos del sistema de formación continua del STEySS"

**OccupationCompare:**
- [ ] Bloque de cursos aparece solo cuando hay gap > 0
- [ ] Cursos ordenados por skills_cubiertas DESC
- [ ] Cada curso muestra "Cubre N de M faltantes"
- [ ] "Ver más" expande sin nuevo fetch
- [ ] Si gap = 0: bloque no se muestra

---

## Tests

`tests/pol-cursos-ocupaciones.test.ts`
- OccupationDetail: seleccionar ocupación → fetch a cursos-gap con
  URIs de skills esenciales
- OccupationDetail: sin skills esenciales → no hace fetch
- OccupationCompare: gap > 0 → muestra cursos
- OccupationCompare: gap = 0 → no muestra cursos
- "Ver más" → expande lista sin fetch adicional

---

## Notas

- Reutilizar el tipo `CursoGap` que ya existe del spec M3-CURSOS.
  No crear un tipo nuevo.

- La API `/api/perfiles/cursos-gap` ya existe. No crear API nueva.
  Solo llamarla desde los componentes.

- En OccupationDetail, la carga de cursos es lazy — se dispara
  cuando cambia `selectedId` (la ocupación seleccionada). Con
  `useEffect([selectedId])`.

- En OccupationCompare, la carga se dispara cuando cambia
  `gapAnalysis` — con `useEffect([gapAnalysis])`.

- Ambos componentes son usados en /vip/politicas y en /admin/skills.
  Los cambios aplican a ambos lugares automáticamente.

- No modificar `/api/perfiles/cursos-gap` — funciona igual para
  skills de gap de persona y para skills esenciales de ocupación.
  La distinción es solo conceptual, no técnica.
