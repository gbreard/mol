# 12. Sistema de Insights

> Última actualización: 2026-02-11
> Estado: ✅ FASE 1-2 IMPLEMENTADAS - Performance corregido + Tensión de Demanda diseñada

## Referencias

| Documento | Relación |
|-----------|----------|
| [07_ESCALABILIDAD](./07_ESCALABILIDAD.md) | E-XX Performance crítico |
| [04_MODELO_DATOS](./04_MODELO_DATOS.md) | Vistas/funciones SQL |
| [02_ARQUITECTURA_PANTALLAS](./02_ARQUITECTURA_PANTALLAS.md) | Pantallas afectadas |

---

## Problema Actual: Performance

### Código Problemático

**Archivo:** `lib/supabase.ts`

```typescript
// ANTI-PATRÓN: Traer TODOS los datos al cliente para procesarlos en JS
const ofertas = await fetchAllPaginated<{...}>(...)

// Después iterar N veces sobre TODAS las ofertas:
data.forEach(o => { ... })  // Agrupar por ISCO
data.forEach(o => { ... })  // Contar por provincia
data.forEach(o => { ... })  // Contar por empresa
```

### Impacto por Escala

| Ofertas | Tiempo estimado | Experiencia |
|---------|-----------------|-------------|
| 1,000 | ~50ms | OK |
| 10,000 | ~500ms | Se nota lag |
| 100,000 | ~5s+ | Browser congela |

### Funciones Afectadas

| Función | Línea aprox | Problema |
|---------|-------------|----------|
| `getKPIs()` | 160-180 | 3 Set() sobre todos los datos |
| `getOfertasPorProvincia()` | 200-220 | forEach + counts manual |
| `getTopOcupaciones()` | 228-250 | forEach + counts manual |
| `getDistribucionModalidad()` | 259-280 | forEach + counts manual |
| `getTopSkills()` | 348-400 | forEach + counts manual |

---

## Solución Propuesta

### Fase 1: Vistas SQL (Corto plazo)

Crear vistas en Supabase que pre-calculen los agregados:

```sql
-- Vista: Distribución por ISCO (primer dígito)
CREATE OR REPLACE VIEW vw_insights_isco_grupos AS
SELECT
  LEFT(isco_code, 1) as grupo,
  COUNT(*) as total,
  ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) as porcentaje
FROM ofertas_dashboard
WHERE isco_code IS NOT NULL
GROUP BY LEFT(isco_code, 1)
ORDER BY total DESC;

-- Vista: Top empresas
CREATE OR REPLACE VIEW vw_insights_empresas AS
SELECT
  empresa,
  COUNT(*) as ofertas,
  COUNT(DISTINCT isco_code) as ocupaciones_distintas
FROM ofertas_dashboard
WHERE empresa IS NOT NULL
GROUP BY empresa
ORDER BY ofertas DESC
LIMIT 20;

-- Vista: Tendencia mensual
CREATE OR REPLACE VIEW vw_insights_tendencia AS
SELECT
  DATE_TRUNC('month', fecha_publicacion::date) as mes,
  COUNT(*) as ofertas,
  COUNT(DISTINCT empresa) as empresas,
  COUNT(DISTINCT isco_code) as ocupaciones
FROM ofertas_dashboard
GROUP BY DATE_TRUNC('month', fecha_publicacion::date)
ORDER BY mes DESC
LIMIT 12;

-- Vista: KPIs generales
CREATE OR REPLACE VIEW vw_insights_kpis AS
SELECT
  COUNT(*) as total_ofertas,
  COUNT(DISTINCT isco_code) as ocupaciones_distintas,
  COUNT(DISTINCT empresa) as empresas_activas,
  COUNT(DISTINCT provincia) as provincias
FROM ofertas_dashboard;
```

### Fase 2: Función RPC (Mediano plazo)

Función que acepta filtros y devuelve insights pre-calculados:

```sql
CREATE OR REPLACE FUNCTION get_insights(
  p_provincia text DEFAULT NULL,
  p_fecha_desde date DEFAULT NULL,
  p_fecha_hasta date DEFAULT NULL
)
RETURNS json AS $$
  SELECT json_build_object(
    'kpis', (SELECT row_to_json(k) FROM vw_insights_kpis k),
    'top_ocupaciones', (SELECT json_agg(o) FROM (SELECT * FROM vw_insights_isco_grupos LIMIT 5) o),
    'tendencia', (SELECT json_agg(t) FROM vw_insights_tendencia t),
    'concentracion_top3', (
      SELECT ROUND(SUM(porcentaje), 1)
      FROM (SELECT porcentaje FROM vw_insights_isco_grupos LIMIT 3) sub
    )
  )
$$ LANGUAGE sql STABLE;
```

### Fase 3: Cache + Triggers (Largo plazo)

```sql
-- Tabla de cache
CREATE TABLE insights_cache (
  cache_key text PRIMARY KEY,
  data jsonb NOT NULL,
  expires_at timestamptz NOT NULL,
  created_at timestamptz DEFAULT now()
);

-- Trigger para invalidar cache cuando cambian ofertas
CREATE OR REPLACE FUNCTION invalidate_insights_cache()
RETURNS trigger AS $$
BEGIN
  DELETE FROM insights_cache WHERE cache_key LIKE 'insights_%';
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_invalidate_insights
AFTER INSERT OR UPDATE OR DELETE ON ofertas_dashboard
FOR EACH STATEMENT EXECUTE FUNCTION invalidate_insights_cache();
```

---

## Ubicación de Insights por Pantalla

### Actual (solo P-09)

| Pantalla | Insights actuales |
|----------|-------------------|
| P-09 Dashboard (tab Panorama) | Evolución, Top ocupaciones, Distribución geográfica |

### Propuesto (expandir a 6 pantallas)

| Pantalla | ID | Insights propuestos | Prioridad |
|----------|----|--------------------|-----------|
| **P-09 Dashboard** | Tab Panorama | KPIs, evolución, concentración | ✅ Existe |
| **P-09 Dashboard** | Tab Requerimientos | Top 5 skills demandadas, skills emergentes (+50% vs mes anterior) | Alta |
| **P-09 Dashboard** | Tab Ofertas | "Esta ocupación paga X% más/menos que promedio" (al seleccionar) | Media |
| **P-10 Skills Intelligence** | Detalle ocupación | "Esta ocupación tiene X% menos ofertas que hace 6 meses" | Alta |
| **Sidebar filtros** | Todos | Counts en filtros: "Buenos Aires (234)", "CABA (189)" | Media |
| **Header global** | Banner/ticker | "🔥 +23% ofertas IT esta semana" | Baja |

---

## Insights Específicos a Implementar

### Grupo 1: Concentración y Distribución

| Insight | Cálculo | Uso |
|---------|---------|-----|
| Concentración Top 3 ISCO | SUM(%) de los 3 primeros grupos | "3 grupos concentran X% de ofertas" |
| Índice Herfindahl | SUM(share²) por ISCO | Medir concentración del mercado |
| Cobertura geográfica | COUNT DISTINCT provincia | "Ofertas en X provincias" |

### Grupo 2: Tendencias Temporales

| Insight | Cálculo | Uso |
|---------|---------|-----|
| Crecimiento mensual | (mes_actual - mes_anterior) / mes_anterior | "+X% vs mes anterior" |
| Estacionalidad | Comparar vs mismo mes año anterior | "Similar a hace 1 año" |
| Velocidad de cierre | AVG días entre publicación y cierre | "Ofertas duran X días promedio" |

### Grupo 3: Skills y Competencias

| Insight | Cálculo | Uso |
|---------|---------|-----|
| Skills emergentes | Skills con +50% frecuencia vs 3 meses atrás | "Skills en alza" |
| Skills saturadas | Skills muy comunes (>30% ofertas) | "Skills básicas esperadas" |
| Gap de skills | Skills en ocupación ESCO sin ofertas locales | "Skills faltantes en mercado" |

### Grupo 4: Empresas y Mercado

| Insight | Cálculo | Uso |
|---------|---------|-----|
| Empresa líder | MAX ofertas por empresa | "X lidera con N ofertas" |
| Concentración empleadores | Top 10 empresas / total | "10 empresas = X% mercado" |
| Empresas nuevas | Empresas sin ofertas en últimos 6 meses | "X empresas nuevas contratando" |

### Grupo 5: Tensión de Demanda

> **Referencia:** [04_MODELO_DATOS](./04_MODELO_DATOS.md#t-tension_ocupaciones-nueva--indicador-tensión-de-demanda) — Definición de tabla y cuadrantes
> **Feature:** [V-16](./08_PROPUESTA_VALOR.md#v-16-indicador-de-tensión-de-demanda)

| Insight | Cálculo | Uso |
|---------|---------|-----|
| Persistencia | % posiciones con `ventana_dias` > 45d por ISCO | "X% de posiciones llevan >45 días publicadas" |
| Insistencia | % posiciones republicadas por ISCO | "X% de posiciones fueron republicadas" |
| Cuadrante | Combinación persistencia + insistencia (umbral 50%) | "Ocupación X es CRÍTICA" |
| Distribución | COUNT por cuadrante sobre total ocupaciones | "30% ocupaciones son críticas" |

**Nota:** Este indicador es GLOBAL (no afectado por filtro de fecha). Se recalcula en cada sincronización a Supabase.

**SQL de cálculo completo:**

```sql
-- Recalcular tabla tension_ocupaciones
TRUNCATE tension_ocupaciones;

INSERT INTO tension_ocupaciones (
  isco_code, isco_label, total_posiciones, total_ofertas,
  persistencia, insistencia, cuadrante
)
SELECT
  isco_code,
  isco_label,
  -- total_posiciones: grupos únicos (misma URL = 1 posición)
  COUNT(DISTINCT grupo_republicacion) AS total_posiciones,
  -- total_ofertas: registros individuales (incluye republicaciones)
  COUNT(*) AS total_ofertas,
  -- persistencia: % posiciones con ventana > 45 días
  ROUND(
    COUNT(DISTINCT grupo_republicacion)
      FILTER (WHERE ventana_dias > 45) * 100.0
    / NULLIF(COUNT(DISTINCT grupo_republicacion), 0),
    2
  ) AS persistencia,
  -- insistencia: % posiciones republicadas (numero_republicacion > 1)
  ROUND(
    COUNT(DISTINCT grupo_republicacion)
      FILTER (WHERE numero_republicacion > 1) * 100.0
    / NULLIF(COUNT(DISTINCT grupo_republicacion), 0),
    2
  ) AS insistencia,
  -- cuadrante: combinación de ambos ejes (umbral 50%)
  CASE
    WHEN persistencia >= 50 AND insistencia >= 50 THEN 'CRITICO'
    WHEN persistencia >= 50 AND insistencia <  50 THEN 'PASIVO'
    WHEN persistencia <  50 AND insistencia >= 50 THEN 'URGENTE'
    ELSE 'FLUIDO'
  END AS cuadrante
FROM ofertas_dashboard
WHERE isco_code IS NOT NULL
GROUP BY isco_code, isco_label;
```

**Cuadrantes:**

| Cuadrante | Persistencia | Insistencia | Interpretación |
|-----------|-------------|-------------|----------------|
| CRÍTICO | >= 50% | >= 50% | Difícil de cubrir, empleadores insisten |
| PASIVO | >= 50% | < 50% | Duran mucho pero sin urgencia percibida |
| URGENTE | < 50% | >= 50% | Se cubren rápido pero alta rotación/insistencia |
| FLUIDO | < 50% | < 50% | Mercado sano, se cubren sin fricción |

---

## Migración del Código

### Antes (JS en cliente)

```typescript
// lib/supabase.ts - ELIMINAR
export async function getKPIs(filters?: DashboardFilters) {
  const ofertas = await fetchAllPaginated<{...}>(...)
  return {
    totalOfertas: ofertas.length,
    ocupacionesDistintas: new Set(ofertas.map(o => o.isco_code)).size,
    // ... procesamiento en JS
  }
}
```

### Después (SQL en Supabase)

```typescript
// lib/supabase.ts - NUEVO
export async function getInsights(filters?: DashboardFilters) {
  const client = getSupabaseClient()
  if (!client) return null

  // Una sola llamada RPC que devuelve todo pre-calculado
  const { data, error } = await client.rpc('get_insights', {
    p_provincia: filters?.provincia,
    p_fecha_desde: filters?.fechaDesde?.toISOString(),
    p_fecha_hasta: filters?.fechaHasta?.toISOString()
  })

  if (error) throw error
  return data
}
```

---

## Plan de Implementación

| Fase | Tarea | Esfuerzo | Estado |
|------|-------|----------|--------|
| 1.1 | Crear vistas SQL en Supabase | 2h | ✅ Completado 2026-02-07 |
| 1.2 | Crear función RPC get_insights() | 2h | ✅ Completado 2026-02-07 |
| 1.3 | Refactorizar lib/supabase.ts | 3h | ✅ Completado 2026-02-07 |
| 1.4 | Actualizar PanoramaGeneral.tsx | 2h | ✅ Completado 2026-02-07 |
| 2.1 | Agregar insights a Tab Requerimientos | 3h | ⏳ Pendiente |
| 2.2 | Agregar insights a Skills Intelligence | 3h | ⏳ Pendiente |
| 2.3 | Counts en sidebar de filtros | 2h | ⏳ Pendiente |
| 3.1 | Tabla insights_cache | 2h | ❌ Descartado (no necesario <50k) |
| 3.2 | Triggers de invalidación | 2h | ❌ Descartado (no necesario <50k) |

**Completado:** 9h (Fases 1.1-1.4)
**Pendiente:** 8h (Fases 2.1-2.3)
**Descartado:** 4h (Fase 3 - overkill para volumen actual)

---

## Métricas de Éxito

| Métrica | Actual | Objetivo |
|---------|--------|----------|
| Tiempo carga insights | ~500ms (2000 ofertas) | <50ms |
| Queries a Supabase | N (uno por métrica) | 1 (RPC única) |
| Datos transferidos | ~200KB | ~2KB |
| Pantallas con insights | 1 | 6 |

---

## Archivos a Modificar

| Archivo | Cambio |
|---------|--------|
| `lib/supabase.ts` | Reemplazar fetchAllPaginated por RPC |
| `components/PanoramaGeneral.tsx` | Usar nuevo getInsights() |
| `components/Requerimientos.tsx` | Agregar InsightCards |
| `app/skills/page.tsx` | Agregar insights de ocupación |
| `components/Sidebar.tsx` | Agregar counts a filtros |

---

## SQL Ejecutado ✅

**Archivo:** `fase3_dashboard/mol-dashboard/docs/sql/vw_insights_all.sql`
**Ejecutado:** 2026-02-07

Contiene:
- 5 vistas (`vw_insights_kpis`, `vw_insights_isco_grupos`, `vw_insights_tendencia`, `vw_insights_empresas`, `vw_insights_provincias`)
- 1 función RPC `get_insights(p_provincia, p_fecha_desde, p_fecha_hasta)`

Ver también: `fase3_dashboard/mol-dashboard/docs/sql/INDEX.md`
