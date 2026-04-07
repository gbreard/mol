# LAB-BRECHA-FORMATIVA — Indicador: Brecha de Formación

## Contexto

Nuevo indicador experimental que cruza la demanda real del mercado laboral
(ofertas MOL) con la oferta de formación disponible (REGICE) para identificar:
- **Brechas:** skills muy demandadas sin cursos que las cubran
- **Cobertura:** skills demandadas con cursos disponibles

Aparece en dos lugares:
1. `/oficina-empleo/laboratorio/brecha-formacion` — vista detallada
2. `/oficina-empleo/dashboard-ejecutivo` (M4) — bloque resumido

**Fuente de datos:**
- Demanda: `ofertas_skills` + `ofertas_dashboard` (ya en Supabase)
- Oferta formativa: `regice_cursos_skills` + `regice_sedes` (ya en Supabase desde M3)

---

## Pre-condición — Gerardo ejecuta antes de arrancar

### Migration: tabla pre-calculada + RPC

El cruce `ofertas_skills` × `regice_cursos_skills` sobre 350K+ rows es
pesado para ejecutar en tiempo real. Se pre-calcula como tabla y se
actualiza con cada sync del pipeline.

**Tabla pre-calculada `brecha_formacion_skills`:**

```sql
CREATE TABLE IF NOT EXISTS brecha_formacion_skills (
  skill_uri          TEXT NOT NULL,
  skill_label        TEXT NOT NULL,
  ofertas_count      INTEGER NOT NULL,  -- cuántas ofertas MOL la piden
  cursos_count       INTEGER NOT NULL,  -- cuántos cursos REGICE la cubren
  estado             TEXT NOT NULL      -- 'brecha' | 'cubierta'
    CHECK (estado IN ('brecha', 'cubierta')),
  calculado_en       TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_bfs_estado 
  ON brecha_formacion_skills(estado);
CREATE INDEX IF NOT EXISTS idx_bfs_ofertas 
  ON brecha_formacion_skills(ofertas_count DESC);
```

**Poblar la tabla (ejecutar después de crear):**

```sql
INSERT INTO brecha_formacion_skills 
  (skill_uri, skill_label, ofertas_count, cursos_count, estado)
SELECT 
  os.skill_uri,
  os.skill_label,
  COUNT(DISTINCT os.id_oferta)    AS ofertas_count,
  COUNT(DISTINCT rcs.curso_id)    AS cursos_count,
  CASE 
    WHEN COUNT(DISTINCT rcs.curso_id) = 0 THEN 'brecha'
    ELSE 'cubierta'
  END AS estado
FROM ofertas_skills os
LEFT JOIN regice_cursos_skills rcs 
  ON os.skill_uri = rcs.skill_uri
GROUP BY os.skill_uri, os.skill_label
ORDER BY ofertas_count DESC
ON CONFLICT DO NOTHING;
```

**RPC para el indicador (filtros por estado y límite):**

```sql
CREATE OR REPLACE FUNCTION get_brecha_formacion(
  p_estado   TEXT    DEFAULT NULL,  -- 'brecha' | 'cubierta' | NULL (ambos)
  p_limit    INT     DEFAULT 20,
  p_offset   INT     DEFAULT 0
)
RETURNS TABLE (
  skill_uri      TEXT,
  skill_label    TEXT,
  ofertas_count  INT,
  cursos_count   INT,
  estado         TEXT,
  pct_mercado    FLOAT  -- % del total de ofertas que piden esta skill
)
LANGUAGE sql STABLE
AS $$
  SELECT
    skill_uri,
    skill_label,
    ofertas_count,
    cursos_count,
    estado,
    ROUND(
      (ofertas_count::FLOAT / NULLIF(
        (SELECT SUM(ofertas_count) FROM brecha_formacion_skills), 0
      ) * 100)::NUMERIC, 2
    )::FLOAT AS pct_mercado
  FROM brecha_formacion_skills
  WHERE (p_estado IS NULL OR estado = p_estado)
  ORDER BY ofertas_count DESC
  LIMIT p_limit
  OFFSET p_offset;
$$;
```

**RPC para dimensión provincial (cruce en tiempo real, acotado):**

```sql
CREATE OR REPLACE FUNCTION get_brecha_formacion_provincia(
  p_provincia  TEXT,
  p_estado     TEXT DEFAULT NULL,
  p_limit      INT  DEFAULT 20
)
RETURNS TABLE (
  skill_uri      TEXT,
  skill_label    TEXT,
  ofertas_count  INT,
  cursos_count   INT,
  estado         TEXT
)
LANGUAGE sql STABLE
AS $$
  -- Normalización MOL → REGICE para provincias
  WITH provincia_regice AS (
    SELECT CASE 
      WHEN lower(p_provincia) IN ('caba', 'ciudad de buenos aires', 
           'ciudad autónoma de buenos aires') THEN 'Capital federal'
      WHEN lower(unaccent(p_provincia)) = 'buenos aires' THEN 'Buenos aires'
      WHEN lower(unaccent(p_provincia)) = 'cordoba' THEN 'Cordoba'
      WHEN lower(unaccent(p_provincia)) = 'tucuman' THEN 'Tucuman'
      ELSE p_provincia
    END AS prov_regice
  ),
  demanda_prov AS (
    SELECT os.skill_uri, os.skill_label,
           COUNT(DISTINCT os.id_oferta) AS ofertas_count
    FROM ofertas_skills os
    JOIN ofertas_dashboard od ON os.id_oferta = od.id_oferta
    WHERE od.provincia = p_provincia
    GROUP BY os.skill_uri, os.skill_label
  ),
  oferta_prov AS (
    SELECT rcs.skill_uri, COUNT(DISTINCT rcs.curso_id) AS cursos_count
    FROM regice_cursos_skills rcs
    JOIN regice_cursos_sedes rcse ON rcs.curso_id = rcse.curso_id
    JOIN regice_sedes rs ON rcse.sede_code = rs.sede_code
    WHERE rs.provincia = (SELECT prov_regice FROM provincia_regice)
    GROUP BY rcs.skill_uri
  )
  SELECT 
    d.skill_uri,
    d.skill_label,
    d.ofertas_count,
    COALESCE(o.cursos_count, 0)::INT AS cursos_count,
    CASE WHEN COALESCE(o.cursos_count, 0) = 0 
         THEN 'brecha' ELSE 'cubierta' END AS estado
  FROM demanda_prov d
  LEFT JOIN oferta_prov o ON d.skill_uri = o.skill_uri
  WHERE (p_estado IS NULL OR 
         CASE WHEN COALESCE(o.cursos_count, 0) = 0 
              THEN 'brecha' ELSE 'cubierta' END = p_estado)
  ORDER BY d.ofertas_count DESC
  LIMIT p_limit;
$$;
```

**Verificar antes de continuar:**
```sql
SELECT COUNT(*) FROM brecha_formacion_skills;  -- esperado: 2,000-5,000 skills
SELECT estado, COUNT(*) FROM brecha_formacion_skills GROUP BY estado;
SELECT * FROM get_brecha_formacion('brecha', 5, 0);
SELECT * FROM get_brecha_formacion_provincia('Buenos Aires', 'brecha', 5);
```

---

## Parte 1 — API

**`GET /api/laboratorio/brecha-formacion`**

```
Params:
  estado:    'brecha' | 'cubierta' | null (default: null = ambos)
  provincia: string | null (default: null = nacional)
  limit:     number (default: 20)
  offset:    number (default: 0)

Lógica:
  Si provincia → llamar get_brecha_formacion_provincia
  Si no → llamar get_brecha_formacion

Retorna:
{
  skills: [{
    skill_uri, skill_label,
    ofertas_count, cursos_count,
    estado,           // 'brecha' | 'cubierta'
    pct_mercado       // % del total (solo en nacional)
  }],
  resumen: {
    total_skills:    number,
    brechas:         number,
    cubiertas:       number,
    pct_brecha:      number   // brechas / total × 100
  },
  provincia: string | null,
  calculado_en: string       // timestamp del último cálculo
}
```

**Auth:** comentar requireAuth. Agregar `// TODO OE-11`.

---

## Parte 2 — Página en Laboratorio

**Ruta:** `/oficina-empleo/laboratorio/brecha-formacion`

```
┌─────────────────────────────────────────────────────────────┐
│  🔬 Brecha de Formación         [EXPERIMENTAL]              │
│  Skills demandadas por el mercado vs oferta educativa       │
│  disponible en REGICE                                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Provincia: [Todo el país ▾]                                │
│                                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                  │
│  │  4,821   │  │  3,102   │  │  1,719   │                  │
│  │  Skills  │  │  Brecha  │  │  Cubiert.│                  │
│  │  totales │  │  64%     │  │  36%     │                  │
│  └──────────┘  └──────────┘  └──────────┘                  │
│                                                             │
│  [Brecha ●] [Cobertura] [Todo]    Ordenar: [Más demandadas] │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│  SKILLS CON BRECHA (sin cursos disponibles)                 │
├─────────────────────────────────────────────────────────────┤
│  1. atención al cliente                                     │
│     1,840 ofertas · 0 cursos · 4.2% del mercado            │
│     ████████████████████████████░░  brecha                  │
│                                                             │
│  2. gestión de inventario                                   │
│     940 ofertas · 0 cursos · 2.1% del mercado              │
│     █████████████████░░░░░░░░░░░░░  brecha                  │
│                                                             │
│  [Cargar más]                                               │
├─────────────────────────────────────────────────────────────┤
│  SKILLS CON COBERTURA (tienen cursos)                       │
├─────────────────────────────────────────────────────────────┤
│  1. soldadura MIG/MAG                                       │
│     820 ofertas · 12 cursos · 1.9% del mercado             │
│     ████████████████░░░░░░░░░░░░░░  cubierta                │
└─────────────────────────────────────────────────────────────┘
```

**Comportamiento:**
- Tab default: "Brecha" (lo más accionable)
- Filtro provincia recalcula via `get_brecha_formacion_provincia`
- Barra proporcional al `pct_mercado` o `ofertas_count`
- "Cargar más" → fetch con offset incremental
- Badge EXPERIMENTAL visible siempre

---

## Parte 3 — Bloque en M4

**Ubicación:** nuevo bloque en `/oficina-empleo/dashboard-ejecutivo`
después de "Competencias más demandadas" (Bloque 5).

```
┌─────────────────────────────────────────────────────────────┐
│  🔬 Brecha de Formación           [EXPERIMENTAL]            │
│  Skills demandadas sin oferta educativa disponible          │
├─────────────────────────────────────────────────────────────┤
│  64% de skills demandadas no tienen cursos en REGICE        │
│                                                             │
│  Top 5 brechas en [provincia seleccionada]:                 │
│  1. atención al cliente        1,840 ofertas                │
│  2. gestión de inventario        940 ofertas                │
│  3. ventas                       880 ofertas                │
│  4. liderazgo de equipos         760 ofertas                │
│  5. servicio al cliente          640 ofertas                │
│                                                             │
│         [Ver análisis completo →]                           │
│  (link a /oficina-empleo/laboratorio/brecha-formacion)      │
└─────────────────────────────────────────────────────────────┘
```

**Comportamiento:**
- Se actualiza con el filtro de provincia de M4
- Si provincia seleccionada → usa `get_brecha_formacion_provincia`
- Si todo el país → usa `get_brecha_formacion` (tabla pre-calculada)
- Muestra solo top 5 brechas — sin cobertura en este bloque
- "Ver análisis completo" navega a la página del Laboratorio
  (misma pestaña, no nueva)
- Carga en paralelo con los otros bloques de M4 (Promise.all)

---

## Criterios de aceptación

**Infraestructura:**
- [ ] `brecha_formacion_skills` tiene rows en Supabase
- [ ] `get_brecha_formacion('brecha', 5, 0)` retorna skills con cursos_count = 0
- [ ] `get_brecha_formacion_provincia('Buenos Aires', 'brecha', 5)` retorna resultados

**Laboratorio:**
- [ ] Ruta `/oficina-empleo/laboratorio/brecha-formacion` accesible
- [ ] KPIs muestran total, brechas y cubiertas con %
- [ ] Tab "Brecha" activo por defecto
- [ ] Filtro provincia recalcula la lista
- [ ] "Cargar más" trae siguiente página sin recargar
- [ ] Badge EXPERIMENTAL visible

**M4:**
- [ ] Bloque aparece después de "Competencias más demandadas"
- [ ] Se actualiza al cambiar filtro de provincia en M4
- [ ] "Ver análisis completo" navega sin abrir nueva pestaña
- [ ] Carga en paralelo con otros bloques (no bloquea M4)

---

## Tests

`tests/lab-brecha-formacion-api.test.ts`
- GET sin params → resumen con total, brechas, cubiertas
- GET ?estado=brecha → solo skills con cursos_count = 0
- GET ?estado=cubierta → solo skills con cursos_count > 0
- GET ?provincia=Buenos Aires → filtra por provincia
- GET ?limit=5&offset=5 → paginación correcta

`tests/lab-brecha-formacion-ui.test.ts`
- KPIs renderizan con números > 0
- Tab brecha muestra skills sin cursos
- Tab cobertura muestra skills con cursos
- Cambiar provincia → re-fetch
- M4: bloque renderiza top 5 brechas

---

## Notas

- `brecha_formacion_skills` es una tabla estática que se repobla
  con cada sync del pipeline MOL. Agregar al script `sync_to_supabase.py`
  un paso que trunca y re-inserta después de sincronizar `ofertas_skills`.

- La dimensión provincial usa `get_brecha_formacion_provincia` que
  corre en tiempo real sobre `ofertas_skills` (350K rows). Es más lento
  que la tabla pre-calculada — agregar timeout de 5s en el cliente.

- La normalización de provincias MOL → REGICE está hardcodeada en la
  RPC. Si se agregan nuevas provincias o variantes, actualizar el CASE.

- INET no se incluye en esta versión por el mismo motivo que M3-CURSOS:
  no tiene provincia directa. Se agrega en iteración futura.

- El % de brecha (64% estimado) puede variar significativamente según
  el threshold de matching de REGICE. Mostrar siempre la fecha de
  último cálculo para que el funcionario sepa qué tan reciente es.
