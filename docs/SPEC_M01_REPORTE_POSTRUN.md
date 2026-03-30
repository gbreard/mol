# M-01 — Reporte Consolidado Post-Run

> **Estado:** ⬜ No iniciado  
> **Prioridad:** CRÍTICO  
> **Fase:** -1, Nivel 1  
> **Prerequisito de:** M-02, M-03, M-04, M-05

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

`sistema_estado` sobreescribe en cada run — sirve para mostrar el
estado actual en el dashboard sin latencia. `pipeline_runs_history` es
una tabla nueva en Supabase donde se inserta una fila por run — sirve
para análisis histórico, correlación de cambios con impacto, y
tendencias en el tiempo.

Ambas se escriben en el PASO 9, al terminar el pipeline. No dependen
del sync manual de ofertas — cada run queda registrado inmediatamente.

**Por qué no syncear desde sync_to_supabase.py:**
El historial de runs no es datos de ofertas. Es metadata del sistema.
Depender del sync manual significa que si el operador no syncea, el
historial se pierde. El PASO 9 garantiza que cada run queda registrado
sin intervención adicional.

### Historial completo — caso de uso

El sistema se mueve constantemente: nuevas reglas, nuevos perfiles
consolidados, cambios en el extractor. El historial permite:

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
Se copia el patrón existente — 5 líneas de código.

### Badge de validadores

**Decisión: mostrar conteo de pendientes en el sidebar/header del admin**

`getValidacionStats()` ya devuelve `pendientes` (ofertas con
`validacion_humana IS NULL`). El dato existe, la query existe. Solo
falta mostrarlo en la navegación global sin necesidad de entrar a
`/admin/validacion`.

---

## Componente 1 — PASO 9 en el pipeline

**Archivo:** `scripts/run_validated_pipeline.py`

**Dónde:** Entre PASO 8 (Sync learnings) y `return resultados` (línea 570)

**Qué hace:** Al terminar el pipeline, escribir el resumen del run en
`sistema_estado` para que el dashboard lo pueda mostrar.

### Campos nuevos en `sistema_estado`

```
ultimo_run_id              TEXT    "run_20260329_0830"
ultimo_run_timestamp       TEXT    "2026-03-29T08:30:00"
ultimo_run_branch          TEXT    "feature/m06-skills-failures"
ultimo_run_nlp_version     TEXT    "11.3.0"
ultimo_run_matching_version TEXT   "3.5.2"

ultimo_run_ofertas         INT     500
ultimo_run_skills          INT     355349
ultimo_run_failures        INT     312
ultimo_run_failures_pct    REAL    0.243
ultimo_run_errores         INT     12
ultimo_run_corregidos      INT     10
ultimo_run_escalados       INT     2
ultimo_run_precision       REAL    0.976

ultimo_run_delta_precision  REAL   0.002   (vs run anterior, positivo=mejora)
ultimo_run_delta_regresiones INT   0
ultimo_run_delta_mejoras    INT    15
ultimo_run_reglas_nuevas    INT    38

ultimo_run_top_failures     TEXT   JSON array con las 3 tareas más cercanas al umbral
```

### Estructura de `ultimo_run_top_failures`

```json
[
  {
    "tarea": "Controlar políticas de mermas, decomisos y vencimientos",
    "oferta": "Gerente de sucursal",
    "score": 0.3945,
    "gap": 0.0055,
    "mejor_skill": "administrar políticas comerciales"
  },
  ...
]
```

### Comportamiento

- Si `compare_runs.py --latest` falla, escribir los campos de delta
  como NULL — no interrumpir el pipeline
- Si `skills_extraction_failures` no tiene registros del run (M-06 no
  activo), escribir failures = 0
- El write a `sistema_estado` es el último paso — si falla, loggear
  warning pero no propagar excepción

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
automáticamente en la respuesta existente. No hay RPC nuevo.

---

## Componente 3 — Auto-refresh en `/admin/metricas`

**Archivo:** `fase3_dashboard/mol-dashboard/app/admin/metricas/page.tsx`

Copiar el patrón de `/admin/arquitectura`:

```typescript
useEffect(() => {
  const interval = setInterval(() => loadMetrics(), 30000);
  return () => clearInterval(interval); // cleanup al desmontar
}, [loadMetrics]);
```

Sin condicional de tab — `/admin/metricas` no tiene tabs, siempre
refresca.

---

## Componente 4 — Badge de pendientes en navegación admin

**Archivo:** componente de navegación global del admin
(sidebar o header según la implementación actual)

**Qué hace:** Mostrar el conteo de ofertas pendientes de validación
junto al link de "Validación" en la navegación.

```
Validación  [487]
```

**Fuente de datos:** `getValidacionStats()` — ya existe, ya devuelve
`pendientes`. Llamarlo desde el layout del admin una vez al montar con
refresh cada 5 minutos.

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
├──────────────────┼────────┼────────┼────────┼────────┼─────────┤
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
run_validated_pipeline.py
    → agregar PASO 9:
      - escribir ultimo_run_* en sistema_estado (via Supabase client)
      - insertar fila en pipeline_runs_history (via Supabase client)
      - fallo silencioso en ambos casos

sistema_estado (tabla Supabase)
    → agregar ~18 columnas (migration SQL #1)

pipeline_runs_history (tabla nueva Supabase)
    → crear tabla + índices + RLS + RPC (migration SQL #2 y #3)

app/admin/metricas/page.tsx
    → agregar sección "Último Run" (lee sistema_estado via get_pipeline_status())
    → agregar sección "Historial de Runs" (lee via get_pipeline_runs_history())
    → agregar auto-refresh cada 30s

[componente navegación admin]
    → agregar badge de pendientes junto a link Validación
```

---

## Migration SQL

### 1. Campos nuevos en `sistema_estado` (último run)

```sql
ALTER TABLE sistema_estado ADD COLUMN ultimo_run_id TEXT;
ALTER TABLE sistema_estado ADD COLUMN ultimo_run_timestamp TEXT;
ALTER TABLE sistema_estado ADD COLUMN ultimo_run_branch TEXT;
ALTER TABLE sistema_estado ADD COLUMN ultimo_run_nlp_version TEXT;
ALTER TABLE sistema_estado ADD COLUMN ultimo_run_matching_version TEXT;
ALTER TABLE sistema_estado ADD COLUMN ultimo_run_ofertas INT;
ALTER TABLE sistema_estado ADD COLUMN ultimo_run_skills INT;
ALTER TABLE sistema_estado ADD COLUMN ultimo_run_failures INT;
ALTER TABLE sistema_estado ADD COLUMN ultimo_run_failures_pct REAL;
ALTER TABLE sistema_estado ADD COLUMN ultimo_run_errores INT;
ALTER TABLE sistema_estado ADD COLUMN ultimo_run_corregidos INT;
ALTER TABLE sistema_estado ADD COLUMN ultimo_run_escalados INT;
ALTER TABLE sistema_estado ADD COLUMN ultimo_run_precision REAL;
ALTER TABLE sistema_estado ADD COLUMN ultimo_run_delta_precision REAL;
ALTER TABLE sistema_estado ADD COLUMN ultimo_run_delta_regresiones INT;
ALTER TABLE sistema_estado ADD COLUMN ultimo_run_delta_mejoras INT;
ALTER TABLE sistema_estado ADD COLUMN ultimo_run_reglas_nuevas INT;
ALTER TABLE sistema_estado ADD COLUMN ultimo_run_top_failures TEXT;
```

### 2. Tabla nueva `pipeline_runs_history` (historial completo)

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

    -- RLS
    created_at            TIMESTAMPTZ DEFAULT NOW()
);

-- Índices para queries de historial
CREATE INDEX idx_runs_history_timestamp ON pipeline_runs_history(timestamp DESC);
CREATE INDEX idx_runs_history_branch    ON pipeline_runs_history(git_branch);
CREATE INDEX idx_runs_history_precision ON pipeline_runs_history(precision);

-- RLS: solo platform_admin puede leer
ALTER TABLE pipeline_runs_history ENABLE ROW LEVEL SECURITY;
CREATE POLICY "platform_admin_only" ON pipeline_runs_history
    FOR ALL TO authenticated
    USING (auth.jwt() ->> 'role' = 'platform_admin');
```

### 3. RPC nuevo `get_pipeline_runs_history`

```sql
CREATE OR REPLACE FUNCTION get_pipeline_runs_history(limit_n INT DEFAULT 30)
RETURNS TABLE (...) -- todos los campos de pipeline_runs_history
LANGUAGE sql SECURITY DEFINER
AS $$
    SELECT * FROM pipeline_runs_history
    ORDER BY timestamp DESC
    LIMIT limit_n;
$$;
```

---

## Tests requeridos

```
tests/test_m01_reporte_postrun.py

test_paso9_escribe_en_sistema_estado()
    → dado un run_id válido en pipeline_runs
    → PASO 9 escribe los campos ultimo_run_* en sistema_estado
    → verificar que todos los campos tienen valores correctos

test_paso9_inserta_en_pipeline_runs_history()
    → dado un run_id válido
    → PASO 9 inserta una fila en pipeline_runs_history
    → verificar que run_id es único (no duplica si se corre dos veces)

test_paso9_fallo_silencioso()
    → si Supabase no está disponible
    → PASO 9 loggea warning pero no lanza excepción
    → el return resultados del pipeline se ejecuta igual

test_paso9_sin_m06()
    → si skills_extraction_failures no tiene registros del run
    → ultimo_run_failures = 0, failures_pct = 0.0
    → no lanza excepción

test_seccion_ultimo_run_renderiza()
    → dado sistema_estado con campos ultimo_run_* populados
    → la sección "Último Run" renderiza correctamente
    → los semáforos muestran el color correcto según umbrales

test_seccion_historial_renderiza()
    → dado get_pipeline_runs_history() con 5 runs
    → la tabla muestra las 5 filas en orden descendente
    → semáforos por fila correctos

test_badge_pendientes_visible()
    → dado getValidacionStats() con pendientes > 0
    → el badge aparece en la navegación con el número correcto
    → dado pendientes = 0, el badge no aparece

test_auto_refresh_cancela_al_desmontar()
    → montar /admin/metricas
    → desmontar
    → verificar que clearInterval fue llamado
```

---

## Criterio de done

```
□ Migration SQL #1 ejecutada (campos en sistema_estado)
□ Migration SQL #2 ejecutada (tabla pipeline_runs_history)
□ Migration SQL #3 ejecutada (RPC get_pipeline_runs_history)
□ PASO 9 escribe en sistema_estado al terminar el pipeline
□ PASO 9 inserta en pipeline_runs_history al terminar el pipeline
□ Sección "Último Run" visible en /admin/metricas
□ Sección "Historial de Runs" visible con últimos 30 runs
□ Semáforos correctos en ambas secciones según umbrales
□ Top 3 tareas más cercanas al umbral visibles
□ Delta vs run anterior visible
□ Auto-refresh cada 30s funcionando en /admin/metricas
□ Badge de pendientes visible en navegación admin
□ 8 tests pasando
□ Correr pipeline completo → verificar que /admin/metricas
  muestra el run sin recargar manualmente
□ Correr dos runs seguidos → verificar que historial tiene 2 filas
□ No regresión: get_pipeline_status() sigue funcionando igual
□ No regresión: secciones existentes de /admin/metricas intactas
□ RLS verificado: solo platform_admin ve pipeline_runs_history
```

---

## Lo que NO hace este spec

- No reemplaza el sistema de alertas existente en /admin/metricas
- No crea página nueva — todo va en la página existente
- No implementa notificaciones externas (email, Telegram)
- No modifica get_pipeline_status() ni reconciliar_sistemas()
- No toca /admin/arquitectura ni /admin/validacion (excepto badge)
- No migra datos históricos de pipeline_runs local a Supabase —
  el historial empieza desde la implementación de M-01
