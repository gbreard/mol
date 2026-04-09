# M1-VIA-FORMACION — Nueva vía de captura: Nivel educativo / Formación profesional

## Contexto

M1 tiene 3 vías de captura: Ocupación, Tareas, Herramientas.
Este spec agrega una cuarta vía: **Nivel educativo / Formación profesional**.

El técnico busca un curso o título del sistema de formación continua del
STEySS (datos REGICE en Supabase). El sistema muestra las competencias
derivadas de ese curso. El técnico confirma cuáles aplican y se agregan
al perfil.

**Fuente de datos:** `regice_cursos` + `regice_cursos_skills` — ya en Supabase.
**Nombre en UI:** "Cursos del sistema de formación continua del STEySS"
— nunca mencionar "REGICE" en la interfaz.

---

## Pre-condición (verificar antes de arrancar)

```sql
SELECT COUNT(*) FROM regice_cursos;        -- ~2,500
SELECT COUNT(*) FROM regice_cursos_skills; -- 14,977

-- Test de búsqueda full-text
SELECT id, denominacion, grupo, carga_horaria_modal
FROM regice_cursos
WHERE denominacion ILIKE '%electricidad%'
LIMIT 5;
```

---

## Parte 1 — RPC de búsqueda de cursos

**Crear RPC `search_cursos_formacion`:**

```sql
CREATE OR REPLACE FUNCTION search_cursos_formacion(
  query_text  TEXT,
  max_results INT DEFAULT 10
)
RETURNS TABLE (
  curso_id            INT,
  denominacion        TEXT,
  grupo               TEXT,
  carga_horaria_modal INT,
  skills_count        INT
)
LANGUAGE sql STABLE
AS $$
  SELECT
    rc.id                                    AS curso_id,
    rc.denominacion                          AS denominacion,
    rc.grupo                                 AS grupo,
    rc.carga_horaria_modal                   AS carga_horaria_modal,
    COUNT(rcs.id)::INT                       AS skills_count
  FROM regice_cursos rc
  LEFT JOIN regice_cursos_skills rcs ON rc.id = rcs.curso_id
  WHERE rc.denominacion ILIKE '%' || query_text || '%'
     OR rc.grupo        ILIKE '%' || query_text || '%'
  GROUP BY rc.id, rc.denominacion, rc.grupo, rc.carga_horaria_modal
  ORDER BY skills_count DESC, rc.denominacion ASC
  LIMIT max_results;
$$;
```

**RPC para obtener skills de un curso:**

```sql
CREATE OR REPLACE FUNCTION get_skills_by_curso(
  p_curso_id INT
)
RETURNS TABLE (
  skill_uri   TEXT,
  skill_label TEXT
)
LANGUAGE sql STABLE
AS $$
  SELECT skill_uri, skill_label
  FROM regice_cursos_skills
  WHERE curso_id = p_curso_id;
$$;
```

**Verificar:**
```sql
SELECT * FROM search_cursos_formacion('electricidad', 5);
SELECT * FROM get_skills_by_curso(1);  -- reemplazar con ID real
```

---

## Parte 2 — API

**Nuevo endpoint:** `GET /api/cursos-formacion/search?q=texto`

```typescript
// Llama search_cursos_formacion
// Retorna:
{
  cursos: [{
    curso_id: number,
    denominacion: string,
    grupo: string,
    carga_horaria_modal: number,
    skills_count: number
  }]
}
```

**Nuevo endpoint:** `GET /api/cursos-formacion/[id]/skills`

```typescript
// Llama get_skills_by_curso
// Retorna:
{
  skills: [{
    skill_uri: string,
    skill_label: string
  }]
}
```

**Auth:** comentar requireAuth. Agregar `// TODO OE-11`.

---

## Parte 3 — Componente FormacionSkillPicker

**Nuevo archivo:** `components/oficina-empleo/FormacionSkillPicker.tsx`

**Props (mismo patrón que las otras vías):**
```typescript
interface FormacionSkillPickerProps {
  onAddSkills:  (skills: SkillItem[]) => void
  skillUris:    Set<string>  // para dedup
}
```

### UI del componente

```
┌─────────────────────────────────────────────────────────────┐
│  Cursos del sistema de formación continua del STEySS        │
│                                                             │
│  [🔍 Buscar curso o área de formación...]                   │
│                                                             │
│  — resultados de búsqueda —                                 │
│  Instalaciones eléctricas domiciliarias                     │
│  Construcción · 163hs · 8 competencias                      │
│  [Ver competencias →]                                       │
│                                                             │
│  Electricidad industrial                                    │
│  Industria · 120hs · 6 competencias                         │
│  [Ver competencias →]                                       │
└─────────────────────────────────────────────────────────────┘
```

### Panel de competencias del curso seleccionado

Al hacer click en "Ver competencias":

```
┌─────────────────────────────────────────────────────────────┐
│  ← Instalaciones eléctricas domiciliarias                   │
│  Construcción · 163hs                                       │
│                                                             │
│  Competencias que cubre este curso:                         │
│                                                             │
│  ☑ instalar electrodomésticos                               │
│  ☑ instalar enchufes                                        │
│  ☑ instalar equipos eléctricos                              │
│  ☑ planos del cableado eléctrico                            │
│  ☐ resolver averías de equipos    ← ya en el perfil         │
│                                                             │
│  [Agregar competencias seleccionadas →]                     │
└─────────────────────────────────────────────────────────────┘
```

**Comportamiento:**
- Skills ya en el perfil (en `skillUris`) aparecen deshabilitadas
  con texto "ya en el perfil" — no se pueden seleccionar de nuevo
- Por defecto todas las skills nuevas están marcadas (checked)
- El técnico desmarca las que no aplican
- "Agregar competencias seleccionadas" → llama `onAddSkills(selected)`
  con `via: 'formacion'`
- "← Volver" regresa al listado de cursos

### SkillItem para esta vía

```typescript
// Al agregar skills desde formación:
const skillItem: SkillItem = {
  uri:          skill.skill_uri,
  label:        skill.skill_label,
  via:          'formacion',
  nivel:        'intermedio',    // default
  certificado:  true,            // completó el curso = certificado
  confidence:   'confirmed',
  source:       'esco'
}
```

**Nota:** `certificado: true` porque si la persona hizo el curso,
se asume que tiene el certificado de formación.

---

## Parte 4 — Integración en /perfiles/nuevo

**En la página de captura**, agregar el cuarto tab:

```
[Ocupación]  [Tareas]  [Herramientas]  [Formación]
```

Al activar el tab "Formación", renderizar `FormacionSkillPicker`
con las mismas props que las otras vías:

```typescript
<FormacionSkillPicker
  onAddSkills={handleAddSkills}
  skillUris={new Set(skills.map(s => s.uri))}
/>
```

`handleAddSkills` ya existe en `useSkillCapture` — no modificar.

---

## Criterios de aceptación

- [ ] Pre-condiciones pasan (RPCs responden)
- [ ] Tab "Formación" visible en la captura de M1
- [ ] Búsqueda por texto encuentra cursos relevantes
- [ ] Al seleccionar un curso se muestran sus competencias
- [ ] Skills ya en el perfil aparecen deshabilitadas
- [ ] "Agregar" llama onAddSkills con via: 'formacion' y certificado: true
- [ ] Las skills agregadas aparecen en el panel derecho con badge "Formación"
- [ ] Dedup funciona: no se puede agregar una skill que ya está en el perfil
- [ ] El nombre "REGICE" nunca aparece en la UI
- [ ] Texto visible: "Cursos del sistema de formación continua del STEySS"

---

## Tests

`tests/m1-via-formacion-api.test.ts`
- GET /api/cursos-formacion/search?q=electricidad → cursos relevantes
- GET /api/cursos-formacion/[id]/skills → skills del curso
- Búsqueda vacía → array vacío, no error

`tests/m1-via-formacion-ui.test.ts`
- Tab "Formación" renderiza FormacionSkillPicker
- Buscar "electricidad" → muestra cursos
- Click "Ver competencias" → muestra skills del curso
- Skill ya en perfil → aparece deshabilitada
- Click "Agregar" → onAddSkills llamada con via: 'formacion'

---

## Notas

- La búsqueda usa ILIKE (substring). Si hay pocos resultados con
  el término exacto, el técnico puede probar con palabras más cortas
  (ej: "electric" en lugar de "electricidad").

- `carga_horaria_modal` puede ser NULL en algunos cursos — mostrar
  "Duración no especificada" si es null.

- No mostrar cursos sin skills asociadas (skills_count = 0) — no
  aportarían nada al perfil. La RPC los excluye implícitamente por
  el ORDER BY skills_count DESC, pero agregar WHERE skills_count > 0
  si hace falta.

- El nombre del tab en el código puede ser 'formacion' —
  solo en la UI mostrar "Formación" o el nombre completo del STEySS.
