# 57014 en pantalla de KPIs (admin/metricas) — post-switch Fase 5

**Fecha:** 2026-09-24 · **Estado:** en diagnóstico (paso 0 preparado, sin aplicar)

## Síntoma
El dashboard tira `canceling statement due to statement timeout` (57014) en la
pantalla de KPIs, reportado "después del switch de Fase 5".

## Diagnóstico (solo lectura, medido en vivo contra Supabase)
La pantalla es `app/admin/metricas/page.tsx`. Tres RPCs timeoutean, cada una
clavando su ceiling exacto en cada corrida:

| RPC | ceiling | baseline |
|---|---|---|
| `get_pipeline_status` (041) | 5s | 5,37 / 5,34s → 57014 |
| `reconciliar_sistemas` (020) | 8s | 8,30 / 8,24s → 57014 |
| `recalcular_emergentes` (050) | 30s | 30,34 / 30,29s → 57014 |

El panorama del OE (`get_panorama` + 4 más) responde OK ~0,3s.

**No lo causó Fase 5:** ninguna de las 3 RPCs referencia `estado_ciclo` /
`estado_oferta` / tablas de ciclo de vida (grep = 0). Los caminos que sí
filtran `estado_ciclo` son rápidos (matching-offers 0,34s; count activa=4.824;
v_empresas_activas 0,34s) → el índice de 067 `idx_ofertas_dashboard_estado_ciclo`
existe y se usa. `recalcular_emergentes` ya tiraba 57014 el 08-09, pre-Fase-5.
Causa real: agregaciones full-table sobre `ofertas_dashboard` (97.109) y
`ofertas_skills` (~300K) en free tier. Agravante probable: el UPDATE masivo del
backfill B.4 (97K filas, 6 columnas) dejó bloat + stats de planner viejas.

## Resultado paso 0 (ANALYZE, sin VACUUM — el Editor rechazó A)
| RPC | antes | después ANALYZE | veredicto |
|---|---|---|---|
| `reconciliar_sistemas` | 8,27s 57014 | **3,62 / 1,63s OK** | ✅ RESUELTO (eran las stats) |
| `get_pipeline_status` | 5,35s 57014 | 5,10 OK / 5,25 57014 (4/5 fallan) | ⚠️ ver abajo |
| `recalcular_emergentes` | 30,3s 57014 | 30,3 / 31,4s 57014 | ❌ sin cambio |

## Plan de fix (nada aplicado sin OK de Gerardo)
0. ✅ **`sql/070_analyze_post_backfill.sql`** corrido (opción B, ANALYZE). Resolvió
   `reconciliar_sistemas` solo. Las otras dos NO son stats.
1. ~~`reconciliar_sistemas`~~ — **ya no hace falta**, ANALYZE lo bajó a <4s.
2. **`get_pipeline_status`**: NO era lock ni bloat (ni toca `ofertas_dashboard`).
   Causa: 2º COUNT (`v_issues_auto_pendientes`) escanea **1,57M filas auto-validator**
   de `issues` en cada carga. `issues(estado)` ya existe pero es inútil (96% pendientes).
   El de humanos ya usa el parcial `idx_issues_humanos_created_at` (065). Fix candidato:
   (a) índice parcial para el subset auto, o (b) reemplazar el COUNT exacto de auto por
   estimado/acotado (el panel solo necesita "hay N auto pendientes"). **Raíz de fondo:**
   1,64M issues / 1,57M auto-pendientes (vs 397K/396K en mayo, ver 065) — backlog
   auto-validator sin triage, cuadruplicado. Data-hygiene, issue aparte.
3. **`recalcular_emergentes`**: ANALYZE no lo movió. `reconciliar` scanea las MISMAS
   tablas grandes en 1,6-3,6s post-ANALYZE → el costo de recalcular es la complejidad
   del JOIN+GROUP BY+doble NOT EXISTS, **no** bloat de scan. (Chequeo de bloat vía
   pg_stat_user_tables pendiente en Editor, pero evidencia apunta a query, no a tuplas
   muertas.) Fix: desacoplar a job offline (post-sync) que escriba
   `emergentes_pendientes`; la UI ya lee la tabla precomputada.

## Estado de los parches (preparados, NO aplicados)
- **get_pipeline_status** → `sql/071_get_pipeline_status_bounded_auto_count.sql`
  (opción b: COUNT acotado con LIMIT 500; bloat descartado con pg_stat).
- **recalcular_emergentes** → `docs/specs/2026-09-24_desacople_recalcular_emergentes.md`
  (desacople offline; bloat descartado, es costo de query).

## Bloat — descartado con datos (pg_stat_user_tables)
- ofertas_skills 0% dead, autovacuum hoy 12:18
- issues 0,1% dead, autovacuum ayer 18:31
- ofertas_dashboard 15,8% dead pero autovacuum ayer 17:12 → rotación normal del
  sync horario, no acumulación.

## PRIORITARIO — emisor que infla `issues` (diagnóstico, limpieza aparte)
`issues` sigue creciendo en vivo (397K en mayo → 1,64M → **1.693.234**) pese al
`--skip-issues` del 07-09. Causa = dos defectos que se componen:

- **Emisor:** `sync_validation_errors_to_issues` en `scripts/exports/sync_to_supabase.py`
  (transforma `validation_errors` resuelto=0 → `issues` auto-validator).
- **D1 — el gate `--skip-issues` no cubre los caminos automáticos:** corren SIN el
  flag `scripts/auto_sync.sh:65`, `scripts/run_pipeline_loop.sh:64`, y el comando
  `sync_supabase` de `scripts/pipeline_command_poller.py` (`build_args: []`).
- **D2 — dedup rota:** el `SELECT existing` (línea ~1279) no tiene `.limit()`/`.range()`
  → PostgREST corta en 1000 filas → deduplica contra 1000 de 1,69M → re-inserta los
  ~292.754 `validation_errors` pendientes locales como "nuevos" en cada corrida.

**Guarda para la limpieza (validada):** total 1.693.234 · auto-validator 1.692.308
(99,945%) · humanos 926 (374 pendientes) · autor NULL 0. `neq
'auto-validator@mol.gob.ar'` preserva limpio a los 926 humanos.

## Pendientes laterales (anotados, NO son el 57014)
- **`empresas` tiene 0 filas** → `v_empresas_activas` devuelve vacío (rápido) antes y
  después del 069. NO es del join ni del switch. **Pendiente aparte:** ¿existe un
  proceso que debería poblar `empresas` y no está corriendo? Investigar quién/qué la
  puebla.
- **216 filas con `estado_ciclo` NULL en `ofertas_dashboard`** (sincronizadas después
  del B.4). `matching-offers` las excluye en silencio (`.eq(activa)`). El transform del
  sync ya manda la columna → el próximo sync completo debería pisarlas. Verificar si se
  resuelven solas con el sync horario; si no, re-backfill puntual.
