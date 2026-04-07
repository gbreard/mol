# OE-M3-CURSOS — Panel de Formación en M3 (Futuro Laboral)

## Contexto

M3 muestra el gap entre el perfil de una persona y una ocupación objetivo.
Este spec agrega un panel de formación que muestra cursos reales de REGICE
que cubren **específicamente las skills del gap** — no cursos genéricos
para la ocupación, sino cursos que cierran las brechas concretas de esa persona.

**Fuente de datos:** REGICE — 1,999 cursos con skills ESCO asociadas
(URIs completas, compatibles con perfil_skills.skill_uri).

**Cadena de conexión:**
```
Gap de la persona (skill_uri que le faltan)
    ↓
regice_cursos_skills WHERE skill_uri IN (gap_uris)
    ↓
cursos que cubren esas skills específicas
    ↓
JOIN sedes → provincia, institución, modalidad
    ↓
"Este curso cubre N de tus M skills faltantes"
```

---

## Pre-condición — Gerardo ejecuta antes de arrancar

### 1. Subir tablas a Supabase (orden por dependencias)

```
1. regice_sedes        (~1,400 rows)
2. regice_cursos       (~2,500 rows)
3. regice_cursos_esco  (~2,500 rows)
4. regice_cursos_sedes (~19,000 rows)
5. regice_cursos_skills (~14,977 rows)  ← CRÍTICA para el cruce
```

### 2. Verificar antes de continuar

```sql
SELECT COUNT(*) FROM regice_sedes;          -- ~1,400
SELECT COUNT(*) FROM regice_cursos;         -- ~2,500
SELECT COUNT(*) FROM regice_cursos_skills;  -- ~14,977

-- Test del cruce gap → cursos
-- Reemplazar con URIs reales del gap de una persona sintética
SELECT 
  rc.denominacion,
  COUNT(DISTINCT rcs_k.skill_uri) AS skills_cubiertas,
  rs.provincia
FROM regice_cursos_skills rcs_k
JOIN regice_cursos rc ON rcs_k.curso_id = rc.id
JOIN regice_cursos_sedes rcs ON rc.id = rcs.curso_id
JOIN regice_sedes rs ON rcs.sede_code = rs.sede_code
WHERE rcs_k.skill_uri IN (
  'http://data.europa.eu/esco/skill/URI_1',
  'http://data.europa.eu/esco/skill/URI_2'
)
GROUP BY rc.id, rc.denominacion, rs.provincia
ORDER BY skills_cubiertas DESC
LIMIT 5;
```

Si el test no retorna resultados, detener y avisar.

---

## Parte 1 — RPC en Supabase

**Crear RPC `get_cursos_for_gap`:**

```sql
CREATE OR REPLACE FUNCTION get_cursos_for_gap(
  p_gap_skill_uris  TEXT[],          -- URIs de skills que le faltan a la persona
  p_provincia       TEXT DEFAULT NULL, -- NULL = todas las provincias
  p_max_results     INT  DEFAULT 20
)
RETURNS TABLE (
  curso_id           INT,
  titulo             TEXT,
  institucion        TEXT,
  provincia          TEXT,
  municipio          TEXT,
  modalidad          TEXT,
  carga_horaria      INT,
  skills_cubiertas   INT,    -- cuántas skills del gap cubre este curso
  total_gap_skills   INT,    -- total de skills del gap (para calcular %)
  skills_detalle     JSONB   -- [{uri, label}] de las skills que cubre
)
LANGUAGE sql STABLE
AS $$
  SELECT
    rc.id                             AS curso_id,
    rc.denominacion                   AS titulo,
    rs.descripcion                    AS institucion,
    rs.provincia                      AS provincia,
    rs.municipio                      AS municipio,
    rcs.modalidad                     AS modalidad,
    rcs.carga_horaria                 AS carga_horaria,
    COUNT(DISTINCT rcs_k.skill_uri)::INT AS skills_cubiertas,
    array_length(p_gap_skill_uris, 1) AS total_gap_skills,
    jsonb_agg(DISTINCT jsonb_build_object(
      'uri', rcs_k.skill_uri,
      'label', rcs_k.skill_label
    )) AS skills_detalle
  FROM regice_cursos_skills rcs_k
  JOIN regice_cursos rc         ON rcs_k.curso_id = rc.id
  JOIN regice_cursos_sedes rcs  ON rc.id = rcs.curso_id
  JOIN regice_sedes rs          ON rcs.sede_code = rs.sede_code
  WHERE rcs_k.skill_uri = ANY(p_gap_skill_uris)
    AND (p_provincia IS NULL OR rs.provincia = p_provincia)
  GROUP BY rc.id, rc.denominacion, rs.descripcion, 
           rs.provincia, rs.municipio, rcs.modalidad, rcs.carga_horaria
  ORDER BY skills_cubiertas DESC, rcs.carga_horaria ASC
  LIMIT p_max_results;
$$;
```

**Verificar RPC:**
```sql
SELECT * FROM get_cursos_for_gap(
  ARRAY[
    'http://data.europa.eu/esco/skill/URI_REAL_1',
    'http://data.europa.eu/esco/skill/URI_REAL_2'
  ],
  NULL,
  5
);
-- Debe retornar cursos con skills_cubiertas > 0
```

---

## Parte 2 — API

**Nuevo endpoint:** `POST /api/perfiles/cursos-gap`

```typescript
// Body:
{
  gap_skill_uris: string[],   // URIs de skills del gap (gapAnalysis.gapEssential)
  provincia?: string          // opcional
}

// Llama RPC get_cursos_for_gap

// Retorna:
{
  cursos: [{
    curso_id: number,
    titulo: string,
    institucion: string,
    provincia: string,
    municipio: string,
    modalidad: string,
    carga_horaria: number,
    skills_cubiertas: number,
    total_gap_skills: number,
    pct_gap_cubierto: number,  // skills_cubiertas / total_gap_skills × 100
    skills_detalle: { uri: string, label: string }[]
  }],
  total: number,
  provincia_filtro: string | null
}
```

**Nota:** POST porque el body puede tener muchas URIs.
**Auth:** comentar requireAuth. Agregar `// TODO OE-11`.

**Manejo de errores:**
- `gap_skill_uris` vacío o ausente → retornar `{ cursos: [], total: 0 }`
  (no error — si no hay gap, no hay cursos que recomendar)
- RPC falla → 500 con mensaje descriptivo

---

## Parte 3 — UI en M3

**Ubicación:** panel nuevo después de "Lo que necesita aprender" (Panel 2),
antes de "Conocimientos" (Panel 3). Tiene sentido acá porque el Panel 2
muestra las skills faltantes y este panel inmediatamente dice dónde aprenderlas.

Solo aparece cuando:
- Hay ocupación objetivo seleccionada
- `gapAnalysis.gapEssential.length > 0` (hay skills faltantes)

### Estado de carga

```
📚 Dónde aprender lo que falta
[spinner]
```

### Sin resultados

```
📚 Dónde aprender lo que falta
No encontramos cursos registrados para las 
skills que le faltan.
```

### Con resultados

```
┌──────────────────────────────────────────────────────────────┐
│  📚 Dónde aprender lo que falta                              │
│  Cursos que cubren las skills ausentes del perfil            │
│                                                              │
│  Provincia: [Buenos Aires ▾]  ← pre-seleccionada si          │
│             el perfil tiene provincia                        │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  Instalaciones domiciliarias de electricidad                 │
│  CFL Comunidad Organizada · Berisso, Buenos Aires            │
│  Presencial · 163hs                                          │
│  ✓ Cubre 5 de 8 skills faltantes                            │
│  instalar interruptores · planos cableado · +3 más          │
│                                                              │
│  Instalador electricista domiciliario                        │
│  UNIDAD PENAL NRO 31 · Florencio Varela, Buenos Aires        │
│  Presencial · 160hs                                          │
│  ✓ Cubre 4 de 8 skills faltantes                            │
│  instalar enchufes · resolver averías · +2 más              │
│                                                              │
│  [+ Ver más cursos]                                          │
└──────────────────────────────────────────────────────────────┘
```

**Reglas de display:**
- Ordenados por `skills_cubiertas DESC` — los más completos primero
- Mostrar 3 por defecto, "Ver más" expande a 20 sin nuevo fetch
- Skills detalle: mostrar primeras 2 + "y N más"
- Badge de modalidad: PRESENCIAL gris / SEMIPRESENCIAL azul / VIRTUAL verde
- El indicador "Cubre N de M skills faltantes" es el dato más importante
  — destacarlo visualmente

**Dropdown de provincia:**
- Default: provincia del perfil de la persona (si existe en `perfil.persona.ubicacion`)
- Si no hay provincia en el perfil: "Todas las provincias"
- Dropdown muestra solo las provincias que tienen cursos relevantes
  — no las 24 siempre

---

## Integración con el estado de M3

```typescript
// Agregar al estado existente de futuro/page.tsx:
const [cursosGap, setCursosGap]             = useState<CursoGap[]>([])
const [loadingCursos, setLoadingCursos]     = useState(false)
const [provinciaCursos, setProvinciaCursos] = useState<string>('')
const [showAllCursos, setShowAllCursos]     = useState(false)

// Trigger: cuando gapAnalysis cambia y hay skills en gapEssential
useEffect(() => {
  if (!gapAnalysis || gapAnalysis.gapEssential.length === 0) {
    setCursosGap([])
    return
  }
  
  const gapUris = gapAnalysis.gapEssential.map(s => s.id)
  // Construir URI completa si el id es solo UUID:
  // 'http://data.europa.eu/esco/skill/' + s.id
  
  fetchCursosGap(gapUris, provinciaCursos || undefined)
}, [gapAnalysis, provinciaCursos])

const fetchCursosGap = async (uris: string[], provincia?: string) => {
  setLoadingCursos(true)
  const res = await fetch('/api/perfiles/cursos-gap', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ 
      gap_skill_uris: uris,
      provincia: provincia || null
    })
  })
  const data = await res.json()
  setCursosGap(data.cursos)
  setLoadingCursos(false)
}
```

**Pre-selección de provincia:**
Al montar el componente, si `perfil.persona.ubicacion` tiene valor,
intentar matchearlo contra las provincias argentinas estándar.
Si hay match → setProvinciaCursos con ese valor → el useEffect
hace el fetch con esa provincia pre-filtrada.

---

## Criterios de aceptación

- [ ] Pre-condiciones pasan (5 tablas en Supabase + RPC responde)
- [ ] Panel no aparece cuando no hay ocupación objetivo
- [ ] Panel no aparece cuando gapEssential está vacío (perfil completo)
- [ ] Panel carga lazy al cambiar ocupación objetivo
- [ ] Cursos ordenados por skills_cubiertas DESC
- [ ] "Cubre N de M skills faltantes" visible en cada card
- [ ] Skills detalle: primeras 2 + "y N más"
- [ ] Si el perfil tiene provincia → pre-seleccionada por defecto
- [ ] Cambiar provincia re-fetcha sin recargar la página
- [ ] Mostrar 3 por defecto, "Ver más" expande sin fetch adicional
- [ ] Badge de modalidad en cada curso
- [ ] Sin resultados: mensaje claro, no error

---

## Tests

`tests/oe-m3-cursos-api.test.ts`
- POST sin gap_skill_uris → `{ cursos: [], total: 0 }` (no 400)
- POST con URIs válidas → cursos con skills_cubiertas > 0
- POST con provincia → solo cursos de esa provincia
- POST con URIs sin cursos → `{ cursos: [], total: 0 }`

`tests/oe-m3-cursos-ui.test.ts`
- Sin ocupación → panel no renderiza
- Con gap vacío (perfil completo) → panel no renderiza
- Con gap → panel carga y muestra cursos ordenados
- "Cubre N de M" visible en cada card
- Cambiar provincia → re-fetch con parámetro correcto
- "Ver más" → expande sin fetch adicional

---

## Notas

- Las URIs en `gapAnalysis.gapEssential` vienen del JSON 
  `occupation_full_detail.json` como IDs cortos (UUID sin prefijo).
  Antes de pasar a la RPC, construir la URI completa:
  `'http://data.europa.eu/esco/skill/' + skill.id`
  Verificar con Claude Code si el formato en el JSON es UUID 
  corto o URI completa antes de implementar.

- No incluir INET en esta primera versión. INET no tiene provincia
  directa — se infiere de la jurisdicción, lo que agrega complejidad.
  Se agrega en iteración futura.

- La RPC filtra por `skill_uri = ANY(p_gap_skill_uris)` — match exacto
  por URI. Si en producción hay pocos resultados, verificar que las URIs
  del gap (del JSON) coincidan con las URIs en regice_cursos_skills
  (de la BD). Son la misma fuente ESCO pero pueden tener diferencias
  de formato.

- `rcs.carga_horaria ASC` como segundo criterio de orden — si dos cursos
  cubren el mismo número de skills, mostrar primero el más corto (menor
  esfuerzo para cerrar el gap).

- El panel de formación complementa Panel 2 ("Lo que necesita aprender"),
  no lo reemplaza. Panel 2 dice QUÉ falta, este panel dice DÓNDE aprenderlo.
