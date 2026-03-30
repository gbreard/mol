# M-01 — Reporte Consolidado Post-Run (v2)

> **Estado:** ⬜ No iniciado
> **Prioridad:** CRÍTICO
> **Fase:** -1, Nivel 1
> **Prerequisito de:** M-02, M-03, M-04, M-05
> **Supersede:** SPEC_M01_REPORTE_POSTRUN.md (v1, corregida por ajustes en PASO 8 y RLS)

---

## Problema que resuelve

El pipeline termina y nadie sabe qué pasó. Los datos existen —
`pipeline_runs`, `validation_errors`, `skills_extraction_failures` —
pero ninguno llega al dashboard automáticamente. El operador tiene que
abrir múltiples lugares para reconstruir el estado del último run.

Los validadores humanos no saben cuándo hay un lote nuevo listo en
`/admin/validacion` sin entrar a verlo.

**Caso concreto que falló:** El modelo BGE-M3 se cayó. El matching
degradó al fallback sin skills. El pipeline procesó igual y nadie se
enteró porque las alertas solo son visibles si alguien entra al
dashboard manualmente.

---

## Correcciones respecto a v1

La v1 tenía 2 problemas identificados al verificar contra el código real:

1. **PASO 9 innecesario:** La v1 proponía un PASO 9 nuevo en `run_validated_pipeline.py` que escribe directamente a Supabase. Pero ese script no importa supabase — quien lo hace es `sync_learnings.py` en PASO 8. Crear un segundo punto de escritura duplica responsabilidades. La v2 extiende el PASO 8 existente.

2. **RLS bloquea anon_key:** La v1 proponía `pipeline_runs_history` con RLS `platform_admin only`, pero `sync_learnings.py` usa `anon_key` (no `service_role_key`, que está comprometida — S-01 pendiente). La v2 usa un RPC `SECURITY DEFINER` para el INSERT, manteniendo la seguridad sin cambiar keys.

---

## Decisiones de diseño

### Dónde vive el reporte

**Decisión: sección nueva en `/admin/metricas`**

`/admin/metricas` es el Centro de Control — el lugar conceptualmente
correcto para el reporte post-run. No se crea una página nueva para
evitar fragmentar más el admin.

### Cómo llegan los datos al dashboard

**Decisión: dos destinos distintos para dos propósitos distintos**

```
sistema_estado (ya existe)        → último run, acceso inmediato
pipeline_runs_history (nueva)     → historial completo de todos los runs
```

`sistema_estado` sobreescribe en cada sync — sirve para mostrar el
estado actual en el dashboard sin latencia. `pipeline_runs_history` es
una tabla nueva en Supabase donde se inserta una fila por run — sirve
para análisis histórico, correlación de cambios con impacto, y
tendencias en el tiempo.

Ambos se escriben durante el PASO 8 (sync_learnings.py), que ya tiene
conexión a Supabase y ya escribe en `sistema_estado`.

### Por qué no crear un PASO 9

`run_validated_pipeline.py` no importa supabase. `sync_learnings.py`
sí — ya tiene el client, el try/except, y escribe en `sistema_estado`.
Agregar los campos de último run al dict `data` existente (línea 1036
de sync_learnings.py) es una extensión natural. Un PASO 9 separado
duplicaría la conexión a Supabase y complicaría el manejo de errores.

### RLS y seguridad

**Decisión: Opción C — RPC SECURITY DEFINER para INSERT**

`sync_learnings.py` usa `anon_key` porque `service_role_key` está
comprometida (S-01 pendiente). Cambiar a `service_role_key` antes de
rotar es riesgoso. En cambio:

- `pipeline_runs_history` tiene RLS restrictivo (solo platform_admin lee)
- INSERT se hace via RPC `insertar_pipeline_run()` con `SECURITY DEFINER`
- La `anon_key` puede llamar al RPC pero no puede leer/escribir la tabla directamente
- SELECT se hace via RPC `get_pipeline_runs_history()` con `SECURITY DEFINER`

Cuando S-01 se resuelva, se puede simplificar eliminando los RPCs y
usando `service_role_key` directamente. Pero el código no necesitará
cambios — los RPCs siguen funcionando.

### Historial completo — caso de uso

```
Caso 1 — Detectar degradación gradual
    "La tasa de failures era 24% hace 3 semanas y hoy es 31%"

Caso 2 — Correlacionar cambio con impacto
    "Agregué 15 reglas nuevas el martes ¿mejoró la precisión?"

Caso 3 — Debugging de un run específico
    "El run del jueves pasado tuvo muchos escalados ¿qué pasó?"

Caso 4 — Reportar evolución al OEDE
    "El sistema mejoró X% en los últimos 3 meses"
```

### Auto-refresh

**Decisión: agregar auto-refresh de 30s a `/admin/metricas`**

Otras páginas admin ya lo tienen (`/admin/arquitectura`). El Centro de
Control es la página que más lo necesita y la única que no lo tiene.
Se copia el patrón existente — `setInterval` + cleanup en `useEffect`.

### Badge de validadores

**Decisión: mostrar conteo de pendientes en el sidebar/header del admin**

`getValidacionStats()` ya devuelve `pendientes` (ofertas con
`validacion_humana IS NULL`). El dato existe, la query existe. Solo
falta mostrarlo en la navegación global (`GlobalNav`) sin necesidad de
entrar a `/admin/validacion`.

---

## Componente 1 — PASO 8 extendido en sync_learnings.py

**Archivo:** `scripts/sync_learnings.py`

**Dónde:** Dentro de `sync_to_supabase()`, en el dict `data` (línea 1036).

**Qué hace:** Agregar campos de último run al snapshot de `sistema_estado`
que ya se escribe en cada sync. Además, insertar una fila en
`pipeline_runs_history` via RPC.

### Campos nuevos en el dict `data` de `sync_to_supabase()`

```
# Último run (se leen de pipeline_runs en SQLite)
"ultimo_run_id":                run_id,
"ultimo_run_timestamp":         timestamp,
"ultimo_run_branch":            git_branch,
"ultimo_run_nlp_version":       nlp_version,
"ultimo_run_matching_version":  matching_version,
"ultimo_run_ofertas":           ofertas_count,
"ultimo_run_skills":            skills_count,        # de ofertas_esco_skills_detalle
"ultimo_run_failures":          failures_count,      # de skills_extraction_failures
"ultimo_run_failures_pct":      failures_pct,        # failures / tareas_totales
"ultimo_run_errores":           errores_detectados,
"ultimo_run_corregidos":        errores_corregidos,
"ultimo_run_escalados":         errores_escalados,
"ultimo_run_precision":         metricas_precision,
"ultimo_run_delta_precision":   delta vs run anterior (o NULL),
"ultimo_run_delta_regresiones": diff_regresiones (o NULL),
"ultimo_run_delta_mejoras":     diff_mejoras (o NULL),
"ultimo_run_reglas_nuevas":     delta_reglas,
"ultimo_run_top_failures":      JSON de 3 tareas más cercanas al umbral,
```

### Lectura de datos locales

Los campos se leen de dos fuentes locales:

1. **`pipeline_runs`** (SQLite) — último run por timestamp DESC.
   Ya se consulta en `sync_learnings.py` para `fase2_ultimo_run`.

2. **`skills_extraction_failures`** (SQLite, M-06) — COUNT y TOP 3
   del run_id correspondiente. Si la tabla no existe o está vacía,
   failures = 0.

### Escritura en Supabase

Dos operaciones, ambas con fallo silencioso:

1. **`sistema_estado`** — los campos se agregan al INSERT existente
   (línea 1071). No hay cambio en la lógica, solo más keys en el dict.

2. **`pipeline_runs_history`** — INSERT via RPC `insertar_pipeline_run()`.
   Se llama después del INSERT de `sistema_estado`, dentro del mismo
   try/except.

```python
# Después de insertar sistema_estado (línea 1071):
try:
    client.rpc('insertar_pipeline_run', { ... }).execute()
except Exception as e:
    if verbose:
        print(f"[SUPABASE] Warning: no se pudo insertar pipeline_run: {e}")
```

### Estructura de `ultimo_run_top_failures`

```json
[
  {
    "tarea": "Controlar políticas de mermas, decomisos y vencimientos",
    "oferta": "Gerente de sucursal",
    "score": 0.3945,
    "gap": 0.0055,
    "mejor_skill": "administrar"
  }
]
```

Se genera con una query a `skills_extraction_failures` JOIN `ofertas_nlp`
ordenada por `gap_al_umbral ASC LIMIT 3`.

### Comportamiento en edge cases

- Si `pipeline_runs` está vacía → todos los campos `ultimo_run_*` = NULL
- Si `skills_extraction_failures` no existe (M-06 no implementado) → failures = 0, top_failures = []
- Si Supabase no responde → loggear warning, no propagar excepción (patrón ya existente en la función)
- Si el RPC `insertar_pipeline_run` falla → loggear warning, `sistema_estado` ya se escribió

---

## Componente 2 — Sección "Último Run" en `/admin/metricas`

**Archivo:** `fase3_dashboard/mol-dashboard/app/admin/metricas/page.tsx`

**Posición:** Entre sección 5 (Reconciliación) y sección 6 (Acceso rápido)

### Layout de la sección

```
┌─────────────────────────────────────────────────────────────┐
│ ÚLTIMO RUN                          run_20260329_0830  [▼] │
│ hace 2 horas · branch: feature/m06 · NLP 11.3 · Match 3.5  │
├────────────┬────────────┬────────────┬────────────┬─────────┤
│  Ofertas   │  Skills    │  Fallidas  │  Errores   │Escalados│
│    500     │  355.349   │  312 ⚠️   │     12     │    2    │
│            │            │   24.3%    │            │         │
├────────────┴────────────┴────────────┴────────────┴─────────┤
│ vs run anterior                                             │
│ Precisión: 97.6% → 97.6% (sin cambio)                      │
│ Mejoras: +15  Regresiones: 0  Reglas nuevas: 38 ✓          │
├─────────────────────────────────────────────────────────────┤
│ Tareas más cercanas al umbral                               │
│ • "Controlar políticas de mermas..."  score 0.39  gap 0.005│
│ • "Elaborar plan maestro de producción..."  score 0.38      │
│ • "Especialista confiabilidad metalúrgico"  score 0.33      │
└─────────────────────────────────────────────────────────────┘
```

### Semáforos de la sección

```
failures_pct >= 30%   → rojo    (degradación seria)
failures_pct 20-30%   → amarillo (normal pero a monitorear)
failures_pct < 20%    → verde

escalados > 0         → amarillo siempre
delta_regresiones > 0 → rojo
```

### Fuente de datos

Lee de `get_pipeline_status()` — el mismo RPC que ya usa la página.
Los campos nuevos de `ultimo_run_*` en `sistema_estado` llegan
automáticamente en la respuesta existente. No hay RPC nuevo para esta
sección.

---

## Componente 3 — Auto-refresh en `/admin/metricas`

**Archivo:** `fase3_dashboard/mol-dashboard/app/admin/metricas/page.tsx`

Copiar el patrón de `/admin/arquitectura`:

```
useEffect + setInterval(loadData, 30000) + cleanup clearInterval
```

Sin condicional de tab — `/admin/metricas` no tiene tabs, siempre
refresca. `loadData()` ya existe (línea 137 de la página actual).

---

## Componente 4 — Badge de pendientes en navegación admin

**Archivo:** `components/navigation/GlobalNav.tsx`
(referenciado desde `app/admin/layout.tsx` línea 29)

**Qué hace:** Mostrar el conteo de ofertas pendientes de validación
junto al link de "Validación" en la navegación.

```
Validación  [487]
```

**Fuente de datos:** `getValidacionStats()` — ya existe, ya devuelve
`pendientes`. Llamarlo desde GlobalNav al montar + refresh cada 5 minutos.

**Comportamiento:**
- Badge solo visible si `pendientes > 0`
- Si `pendientes > 999` → mostrar "999+"
- Color: azul (informativo, no alarmante)

---

## Componente 5 — Sección "Historial de Runs" en `/admin/metricas`

**Posición:** Debajo de la sección "Último Run"

### Layout de la sección

```
┌─────────────────────────────────────────────────────────────────┐
│ HISTORIAL DE RUNS                              Últimos 30 runs  │
├──────────────────┬────────┬────────┬─────────┬────────┬────────┤
│ Run              │Ofertas │Failures│Precisión│ Delta  │ Branch │
├──────────────────┼────────┼────────┼─────────┼────────┼────────┤
│ hace 2h          │  500   │ 24.3%  │  97.6%  │  +0.2% │ feat/  │
│ run_20260329_... │        │   ⚠️   │         │        │ m06    │
├──────────────────┼────────┼────────┼─────────┼────────┼────────┤
│ hace 3 días      │  487   │ 23.1%  │  97.4%  │  +1.1% │ main   │
│ run_20260326_... │        │        │         │   ✓    │        │
├──────────────────┼────────┼────────┼─────────┼────────┼────────┤
│ hace 1 semana    │  512   │ 31.2%  │  96.3%  │  -0.5% │ main   │
│ run_20260322_... │        │   🔴   │         │   ⚠️   │        │
└──────────────────┴────────┴────────┴─────────┴────────┴────────┘
```

**Semáforos por fila:**
```
failures_pct >= 30%      → 🔴
failures_pct 20-29%      → ⚠️
delta_precision negativo → ⚠️
delta_regresiones > 0    → 🔴
```

**Fuente de datos:** RPC `get_pipeline_runs_history(limit_n=30)`

---

## Cambios por archivo

```
scripts/sync_learnings.py
    → extender sync_to_supabase():
      - leer último run de pipeline_runs (SQLite)
      - leer failures de skills_extraction_failures (SQLite)
      - agregar ~18 campos ultimo_run_* al dict data
      - llamar RPC insertar_pipeline_run() después del INSERT
      - fallo silencioso en ambos casos

sistema_estado (tabla Supabase)
    → agregar ~18 columnas (migration SQL #1)

pipeline_runs_history (tabla nueva Supabase)
    → crear tabla + índices + RLS (migration SQL #2)

RPCs nuevos (Supabase)
    → insertar_pipeline_run() — SECURITY DEFINER INSERT (migration SQL #3)
    → get_pipeline_runs_history() — SECURITY DEFINER SELECT (migration SQL #3)

app/admin/metricas/page.tsx
    → agregar sección "Último Run" (lee sistema_estado via get_pipeline_status())
    → agregar sección "Historial de Runs" (lee via get_pipeline_runs_history())
    → agregar auto-refresh cada 30s

components/navigation/GlobalNav.tsx
    → agregar badge de pendientes junto a link Validación
```

---

## Migration SQL

### 1. Campos nuevos en `sistema_estado` (último run)

```sql
ALTER TABLE sistema_estado ADD COLUMN IF NOT EXISTS ultimo_run_id TEXT;
ALTER TABLE sistema_estado ADD COLUMN IF NOT EXISTS ultimo_run_timestamp TEXT;
ALTER TABLE sistema_estado ADD COLUMN IF NOT EXISTS ultimo_run_branch TEXT;
ALTER TABLE sistema_estado ADD COLUMN IF NOT EXISTS ultimo_run_nlp_version TEXT;
ALTER TABLE sistema_estado ADD COLUMN IF NOT EXISTS ultimo_run_matching_version TEXT;
ALTER TABLE sistema_estado ADD COLUMN IF NOT EXISTS ultimo_run_ofertas INT;
ALTER TABLE sistema_estado ADD COLUMN IF NOT EXISTS ultimo_run_skills INT;
ALTER TABLE sistema_estado ADD COLUMN IF NOT EXISTS ultimo_run_failures INT;
ALTER TABLE sistema_estado ADD COLUMN IF NOT EXISTS ultimo_run_failures_pct REAL;
ALTER TABLE sistema_estado ADD COLUMN IF NOT EXISTS ultimo_run_errores INT;
ALTER TABLE sistema_estado ADD COLUMN IF NOT EXISTS ultimo_run_corregidos INT;
ALTER TABLE sistema_estado ADD COLUMN IF NOT EXISTS ultimo_run_escalados INT;
ALTER TABLE sistema_estado ADD COLUMN IF NOT EXISTS ultimo_run_precision REAL;
ALTER TABLE sistema_estado ADD COLUMN IF NOT EXISTS ultimo_run_delta_precision REAL;
ALTER TABLE sistema_estado ADD COLUMN IF NOT EXISTS ultimo_run_delta_regresiones INT;
ALTER TABLE sistema_estado ADD COLUMN IF NOT EXISTS ultimo_run_delta_mejoras INT;
ALTER TABLE sistema_estado ADD COLUMN IF NOT EXISTS ultimo_run_reglas_nuevas INT;
ALTER TABLE sistema_estado ADD COLUMN IF NOT EXISTS ultimo_run_top_failures TEXT;
```

### 2. Tabla nueva `pipeline_runs_history`

```sql
CREATE TABLE pipeline_runs_history (
    id                    BIGSERIAL PRIMARY KEY,
    run_id                TEXT NOT NULL UNIQUE,
    timestamp             TIMESTAMPTZ NOT NULL,

    -- Versiones
    git_branch            TEXT,
    git_commit            TEXT,
    nlp_version           TEXT,
    matching_version      TEXT,

    -- Métricas del run
    ofertas_count         INT,
    skills_count          INT,
    failures_count        INT,
    failures_pct          REAL,
    errores_detectados    INT,
    errores_corregidos    INT,
    errores_escalados     INT,
    precision             REAL,

    -- Delta vs run anterior
    run_anterior_id       TEXT,
    delta_precision       REAL,
    delta_mejoras         INT,
    delta_regresiones     INT,
    reglas_nuevas         INT,
    sinonimos_count       INT,

    -- Top failures (JSON)
    top_failures          JSONB,

    -- Metadata
    created_at            TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_runs_history_timestamp ON pipeline_runs_history(timestamp DESC);
CREATE INDEX idx_runs_history_branch    ON pipeline_runs_history(git_branch);

ALTER TABLE pipeline_runs_history ENABLE ROW LEVEL SECURITY;
CREATE POLICY "admin_read_only" ON pipeline_runs_history
    FOR SELECT TO authenticated
    USING (auth.jwt() ->> 'role' = 'platform_admin');
-- INSERT bloqueado por RLS — solo via RPC SECURITY DEFINER
```

### 3. RPCs nuevos

```sql
-- INSERT: usado por sync_learnings.py con anon_key
CREATE OR REPLACE FUNCTION insertar_pipeline_run(
    p_run_id TEXT,
    p_timestamp TIMESTAMPTZ,
    p_git_branch TEXT DEFAULT NULL,
    p_git_commit TEXT DEFAULT NULL,
    p_nlp_version TEXT DEFAULT NULL,
    p_matching_version TEXT DEFAULT NULL,
    p_ofertas_count INT DEFAULT NULL,
    p_skills_count INT DEFAULT NULL,
    p_failures_count INT DEFAULT NULL,
    p_failures_pct REAL DEFAULT NULL,
    p_errores_detectados INT DEFAULT NULL,
    p_errores_corregidos INT DEFAULT NULL,
    p_errores_escalados INT DEFAULT NULL,
    p_precision REAL DEFAULT NULL,
    p_run_anterior_id TEXT DEFAULT NULL,
    p_delta_precision REAL DEFAULT NULL,
    p_delta_mejoras INT DEFAULT NULL,
    p_delta_regresiones INT DEFAULT NULL,
    p_reglas_nuevas INT DEFAULT NULL,
    p_sinonimos_count INT DEFAULT NULL,
    p_top_failures JSONB DEFAULT NULL
)
RETURNS VOID
LANGUAGE plpgsql SECURITY DEFINER
AS $$
BEGIN
    INSERT INTO pipeline_runs_history (
        run_id, timestamp, git_branch, git_commit,
        nlp_version, matching_version,
        ofertas_count, skills_count, failures_count, failures_pct,
        errores_detectados, errores_corregidos, errores_escalados, precision,
        run_anterior_id, delta_precision, delta_mejoras, delta_regresiones,
        reglas_nuevas, sinonimos_count, top_failures
    ) VALUES (
        p_run_id, p_timestamp, p_git_branch, p_git_commit,
        p_nlp_version, p_matching_version,
        p_ofertas_count, p_skills_count, p_failures_count, p_failures_pct,
        p_errores_detectados, p_errores_corregidos, p_errores_escalados, p_precision,
        p_run_anterior_id, p_delta_precision, p_delta_mejoras, p_delta_regresiones,
        p_reglas_nuevas, p_sinonimos_count, p_top_failures
    )
    ON CONFLICT (run_id) DO NOTHING;
END;
$$;

-- SELECT: usado por dashboard con auth
CREATE OR REPLACE FUNCTION get_pipeline_runs_history(limit_n INT DEFAULT 30)
RETURNS SETOF pipeline_runs_history
LANGUAGE sql SECURITY DEFINER
AS $$
    SELECT * FROM pipeline_runs_history
    ORDER BY timestamp DESC
    LIMIT limit_n;
$$;
```

---

## Estrategia de Tests

### Estructura de archivos

```
tests/
  test_m01_sync_learnings.py          ← unitarios + integración del PASO 8 extendido
  test_m01_dashboard.test.tsx         ← componentes React (vitest/testing-library)
```

### Nota sobre tests de dashboard

Los tests de componentes React usan vitest + @testing-library/react
(ya configurados en el proyecto). Los tests Python cubren la lógica
de sync. Los tests de UI cubren renderizado y comportamiento.

---

### Componente 1 — PASO 8 extendido (sync_learnings.py)

#### Unitarios

```
test_lee_ultimo_run_de_pipeline_runs
    Tipo: unitario
    Qué verifica:
      - Dado pipeline_runs con 3 runs, lee el más reciente (ORDER BY timestamp DESC)
      - Retorna dict con todos los campos esperados
      - Si pipeline_runs está vacía, retorna None sin error
    Datos: SQLite en memoria con pipeline_runs mock (3 filas)

test_lee_failures_del_run
    Tipo: unitario
    Qué verifica:
      - Dado skills_extraction_failures con registros del run actual
      - Cuenta correctamente failures_count
      - Calcula failures_pct = failures / tareas_totales
      - Genera top_failures (3 con menor gap_al_umbral)
    Datos: SQLite en memoria con skills_extraction_failures mock

test_lee_failures_tabla_no_existe
    Tipo: unitario
    Qué verifica:
      - Si skills_extraction_failures no existe (M-06 no implementado)
      - Retorna failures_count=0, failures_pct=0.0, top_failures=[]
      - No lanza excepción
    Datos: SQLite en memoria SIN la tabla

test_construye_dict_data_completo
    Tipo: unitario
    Qué verifica:
      - El dict data tiene los 18 campos ultimo_run_* además de los existentes
      - Los campos de Fase 1/2/3 originales siguen presentes
      - Si no hay run, los campos son NULL (no rompen el INSERT)
    Datos: Mock de las funciones de lectura

test_top_failures_estructura_correcta
    Tipo: unitario
    Qué verifica:
      - top_failures es JSON array de max 3 elementos
      - Cada elemento tiene: tarea, oferta, score, gap, mejor_skill
      - Ordenados por gap ASC (más cercano al umbral primero)
    Datos: SQLite con 10 failures de distintos gaps
```

#### Integración

```
test_sync_to_supabase_escribe_campos_ultimo_run
    Tipo: integración (mock Supabase)
    Qué verifica:
      - sync_to_supabase() incluye los campos ultimo_run_* en el INSERT
      - El mock de supabase.table("sistema_estado").insert() recibe los campos
    Datos: Mock del Supabase client + pipeline_runs real

test_sync_to_supabase_llama_rpc_insertar_pipeline_run
    Tipo: integración (mock Supabase)
    Qué verifica:
      - Después del INSERT de sistema_estado, se llama client.rpc('insertar_pipeline_run')
      - Los parámetros del RPC coinciden con los datos del último run
      - Si el RPC falla, no propaga excepción (warning logged)
    Datos: Mock del Supabase client

test_sync_fallo_rpc_no_rompe_sistema_estado
    Tipo: integración (mock Supabase)
    Qué verifica:
      - Si insertar_pipeline_run() falla, sistema_estado YA se escribió
      - La función retorna True (sync exitoso de sistema_estado)
      - El warning se loguea
    Datos: Mock con RPC que lanza excepción

test_sync_sin_supabase_fallo_silencioso
    Tipo: integración
    Qué verifica:
      - Si supabase_config.json no existe o no tiene url
      - La función retorna False sin excepción
      - No intenta escribir nada
    Datos: Config vacío o inexistente
```

---

### Componente 2 — Sección "Último Run" (React)

```
test_ultimo_run_renderiza_datos_completos
    Tipo: componente React (vitest + testing-library)
    Qué verifica:
      - Dado pipelineStatus con campos ultimo_run_* poblados
      - Renderiza: run_id, timestamp relativo, branch, versiones
      - Renderiza: 5 cards (ofertas, skills, fallidas, errores, escalados)
      - Renderiza: delta vs anterior (precisión, mejoras, regresiones)
      - Renderiza: top 3 tareas más cercanas al umbral
    Datos: Mock de get_pipeline_status() con ultimo_run_* completos

test_ultimo_run_sin_datos
    Tipo: componente React
    Qué verifica:
      - Si ultimo_run_id es NULL (no hay run registrado)
      - La sección muestra "Sin datos de run" o equivalente
      - No lanza error de renderizado
    Datos: Mock con ultimo_run_id = null

test_semaforos_failures
    Tipo: componente React
    Qué verifica:
      - failures_pct >= 30% → indicador rojo
      - failures_pct 20-29% → indicador amarillo
      - failures_pct < 20% → indicador verde
    Datos: 3 renders con valores distintos de failures_pct

test_semaforos_delta
    Tipo: componente React
    Qué verifica:
      - delta_regresiones > 0 → indicador rojo
      - escalados > 0 → indicador amarillo
      - todo 0 → indicadores verdes
    Datos: Mocks con distintos deltas
```

---

### Componente 3 — Auto-refresh

```
test_auto_refresh_ejecuta_cada_30s
    Tipo: componente React (vitest + fake timers)
    Qué verifica:
      - Al montar, loadData se llama 1 vez
      - Después de 30s (advanceTimersByTime), se llama otra vez
      - Después de 60s, se llamó 3 veces total
    Datos: Mock de loadData + vi.useFakeTimers()

test_auto_refresh_cleanup_al_desmontar
    Tipo: componente React
    Qué verifica:
      - Al desmontar el componente, clearInterval se llama
      - Después de 30s post-desmonte, loadData NO se vuelve a llamar
    Datos: vi.useFakeTimers() + unmount
```

---

### Componente 4 — Badge de pendientes

```
test_badge_visible_con_pendientes
    Tipo: componente React
    Qué verifica:
      - getValidacionStats() retorna pendientes=487
      - El badge muestra "487" junto a "Validación" en GlobalNav
      - El badge tiene color azul
    Datos: Mock de getValidacionStats()

test_badge_oculto_sin_pendientes
    Tipo: componente React
    Qué verifica:
      - getValidacionStats() retorna pendientes=0
      - No se renderiza ningún badge
    Datos: Mock con pendientes=0

test_badge_trunca_999_plus
    Tipo: componente React
    Qué verifica:
      - pendientes=15968 → badge muestra "999+"
    Datos: Mock con pendientes alto

test_badge_refresh_cada_5_min
    Tipo: componente React (fake timers)
    Qué verifica:
      - getValidacionStats() se llama al montar
      - Se vuelve a llamar después de 5 minutos
      - No se llama entre medio
    Datos: vi.useFakeTimers() + mock
```

---

### Componente 5 — Sección "Historial de Runs"

```
test_historial_renderiza_tabla
    Tipo: componente React
    Qué verifica:
      - Dado get_pipeline_runs_history() con 5 runs
      - Renderiza tabla con 5 filas
      - Columnas: Run, Ofertas, Failures, Precisión, Delta, Branch
      - Orden: más reciente arriba
    Datos: Mock del RPC con 5 filas

test_historial_semaforos_por_fila
    Tipo: componente React
    Qué verifica:
      - Fila con failures_pct >= 30% → indicador rojo
      - Fila con delta_precision negativo → indicador amarillo
      - Fila con todo OK → sin indicadores
    Datos: Mock con filas de distintos valores

test_historial_vacio
    Tipo: componente React
    Qué verifica:
      - Si get_pipeline_runs_history() retorna []
      - Muestra mensaje "Sin historial" o equivalente
      - No lanza error
    Datos: Mock vacío

test_historial_carga_con_error
    Tipo: componente React
    Qué verifica:
      - Si el RPC falla (network error)
      - Muestra mensaje de error, no rompe la página
      - Las otras secciones de /admin/metricas siguen visibles
    Datos: Mock que lanza error
```

---

### Regresión

```
test_regression_secciones_existentes_intactas
    Tipo: componente React
    Qué verifica:
      - Las 6 secciones originales de /admin/metricas siguen visibles
      - Pipeline visual, Alertas, KPIs, Reconciliación, Acceso rápido
      - No desaparecieron ni cambiaron de orden
    Datos: Mock estándar de get_pipeline_status + reconciliar_sistemas

test_regression_get_pipeline_status_sin_campos_nuevos
    Tipo: componente React
    Qué verifica:
      - Si sistema_estado NO tiene los campos ultimo_run_* (migration no ejecutada)
      - La sección "Último Run" muestra "Sin datos" pero no rompe
      - Las secciones existentes funcionan normal
    Datos: Mock de get_pipeline_status() sin los campos nuevos

test_regression_sync_learnings_sin_campos_nuevos
    Tipo: unitario Python
    Qué verifica:
      - Si pipeline_runs está vacía, sync_to_supabase() sigue funcionando
      - Los campos de Fase 1/2/3 se escriben normalmente
      - Los campos ultimo_run_* son NULL pero no rompen el INSERT
    Datos: SQLite con pipeline_runs vacía
```

---

## Criterio de done

```
□ Migration SQL #1 ejecutada (campos en sistema_estado)
□ Migration SQL #2 ejecutada (tabla pipeline_runs_history + RLS)
□ Migration SQL #3 ejecutada (RPCs insertar_pipeline_run + get_pipeline_runs_history)
□ sync_learnings.py extendido: lee último run + failures, escribe campos + llama RPC
□ Sección "Último Run" visible en /admin/metricas
□ Sección "Historial de Runs" visible con últimos 30 runs
□ Semáforos correctos en ambas secciones según umbrales
□ Top 3 tareas más cercanas al umbral visibles
□ Delta vs run anterior visible
□ Auto-refresh cada 30s funcionando en /admin/metricas
□ Badge de pendientes visible en GlobalNav
□ Tests Python pasando (9 tests)
□ Tests React pasando (14 tests)
□ Correr pipeline + sync_learnings → verificar que /admin/metricas muestra el run
□ Correr dos veces → verificar que historial tiene 2 filas
□ No regresión: secciones existentes de /admin/metricas intactas
□ No regresión: sync_learnings funciona sin los campos nuevos en pipeline_runs
□ RLS verificado: anon_key puede INSERT via RPC pero no directo
□ RLS verificado: solo platform_admin puede SELECT via RPC
```

---

## Lo que NO hace este spec

- No reemplaza el sistema de alertas existente en /admin/metricas
- No crea página nueva — todo va en la página existente
- No implementa notificaciones externas (email, Telegram) — eso es M-02
- No modifica get_pipeline_status() ni reconciliar_sistemas()
- No toca /admin/arquitectura ni /admin/validacion (excepto badge)
- No migra datos históricos de pipeline_runs local a Supabase —
  el historial empieza desde la implementación de M-01
- No cambia anon_key por service_role_key — S-01 debe resolverse primero
