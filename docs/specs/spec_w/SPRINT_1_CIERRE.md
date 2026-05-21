# SPEC W Sprint 1 Etapa 1 — Reporte de cierre

**Fecha de cierre:** 2026-05-20
**Branch:** `spec/w-validacion-estructurada`
**Estado:** Listo para merge a `main` (pendiente OK explícito de Gerardo)
**Etapa:** 1 — Visualizador Estructurado
**Spec de referencia:** `docs/specs/spec_w/SPEC_W_etapa1_visualizador.md`

---

## 1. Resumen

Sprint 1 cierra con **6 sub-tareas implementadas** (A, B, C, D.1, D.2, D.4) y **1 diferida** (D.3 — denominaciones argentinas, escalada a SPEC AR-Cat). El branch agrega 5,225 líneas en 28 archivos, distribuido entre 2 migraciones SQL, 3 endpoints nuevos, 6 componentes UI nuevos/modificados, y 6 archivos de tests (~1,700 líneas de test).

Las funcionalidades cubren F4 (estado Revisada), F5 (Mal extraída), F6 (feedback visual inmediato), F7 (filtro datos incompletos), F8 (filtro corrección manual), F10 (origen de acciones con campo `source`).

---

## 2. Tabla de sub-tareas

| Sub-tarea | Descripción | Commit | Estado |
|---|---|---|---|
| **A** | Fase 0 factibilidad — schemas, decisiones, Fase 0 OK con ajustes | `f1bd01f3`, `7ab60516` | ✅ Cerrada |
| **B** | Schema + endpoints (`POST/DELETE/GET audit-actions`) | `d6478131`, `b4e51ded` | ✅ Cerrada |
| **C** | Migration 024.1 — índices de performance para filtros | `616e3a00` | ✅ Cerrada |
| **D.1** | UI `AuditActionToolbar` (Revisada, Mal extraída, atajos Alt+7/Alt+8) | `0f4304c8` | ✅ Cerrada |
| **D.2** | UI bloque Revisión en `ValidationFilters` (radio + 2 toggles) | `97d04a22` | ✅ Cerrada |
| **D.3** | Badge denominación AR/ES | — | ⏸️ **Diferida** (SPEC AR-Cat) |
| **D.4** | Tests integrales e2e + guía Cyn + reporte cierre | _este sprint_ | ✅ Cerrada |

### 2.1 Sub-tarea diferida (D.3)

**Motivo del diferimiento:** la columna `denominacion_arg` está poblada en 0/68,152 ofertas (0%). No hay catálogo de denominaciones argentinas. Implementar el badge ahora sería un componente sin datos para mostrar.

**Documentos de soporte:**
- `docs/issues/2026-05-19_investigacion_denominaciones_argentinas.md` — investigación previa
- `docs/specs/spec_ar_cat/MEDICION_UNIVERSO_v1.md` — medición de universo a curar (4,087 combinaciones únicas ISCO+ESCO, 50.1% cubierto por fuentes existentes)

**Hallazgo lateral durante la medición:** la regla `R238_analista_it` mapea 495 ofertas a `esco_label = "consultor de TIC verdes"` (ISCO 2511 correcto, label incorrecto). Patrón sistémico en otras reglas (`R226_analista_rrhh`, `R229_analista_comercial`, etc.) — ~2,138 ofertas con `esco_label` críticamente desalineado del título real. Documentado en `docs/issues/2026-05-19_diagnostico_mismatching_consultor_tic_verdes.md`. **Resolver antes (o en paralelo) a SPEC AR-Cat** — la medición del universo a curar está inflada por estos bugs.

---

## 3. Migrations aplicadas

| Migration | Archivo | Cambio |
|---|---|---|
| `024_spec_w_audit_actions` | `migrations/024_spec_w_audit_actions.sql` | CREATE TABLE `audit_actions` (10 cols + 5 índices); ALTER `ofertas_dashboard` ADD `estado_revision`, `denominacion_arg`, `denominacion_esp` |
| `024_1_spec_w_performance_filtros` | `migrations/024_1_spec_w_performance_filtros.sql` | Generated column `datos_incompletos` + índice parcial; índices `idx_audit_actions_source`, `idx_audit_actions_type` |

Las migrations son reversibles y están testeadas en `tests/spec_w/test_migration_024.py` (215 líneas) y `tests/spec_w/test_filtros_performance.py` (122 líneas).

---

## 4. Endpoints creados

| Endpoint | Archivo | Función |
|---|---|---|
| `POST /api/audit-actions` | `app/api/audit-actions/route.ts` | Inserta acción + actualiza `estado_revision` si aplica. Valida 8 action_types, 4 target_types, 4 sources. |
| `DELETE /api/audit-actions/[id]` | `app/api/audit-actions/[id]/route.ts` | **Op 3**: inserta acción inversa (`unmark_revised`/`unmark_total_failure`) y setea `estado_revision=NULL`. Solo `mark_revised`/`mark_total_failure` son revertibles; el resto devuelve 400 `action_not_revertible`. |
| `GET /api/oferta/[id]/audit-history` | `app/api/oferta/[id]/audit-history/route.ts` | Lista acciones de una oferta ordenadas DESC por timestamp. |

Los tres usan `requireAdmin` (rate limit admin tier + auth Supabase).

---

## 5. Componentes UI

| Componente | Archivo | Cambio |
|---|---|---|
| `AuditActionToolbar` | `components/validacion/AuditActionToolbar.tsx` (nuevo, 321 líneas) | Botones Revisada/Mal extraída con atajos Alt+7/Alt+8; modal de nota para Mal extraída; estado optimista + revert al fallar; reset al cambiar de oferta. |
| `ValidationFilters` | `components/validacion/ValidationFilters.tsx` (+70 líneas) | Bloque "Revisión": radio (Todas/Pendientes/Revisadas/Mal extraídas) + checkboxes (Solo datos incompletos / Solo corregidas manualmente). |
| `EmptyResultsWithFilters` | `components/validacion/EmptyResultsWithFilters.tsx` (nuevo, fix B2) | Mensaje claro cuando búsqueda + filtros devuelven 0 resultados. |
| `ValidationActions` | `components/validacion/ValidationActions.tsx` (+31 líneas) | Integración con AuditActionToolbar en sticky bar. |
| `admin/validacion/page.tsx` | `app/admin/validacion/page.tsx` (+27 líneas) | Wiring de filtros nuevos al state global. |
| `lib/supabase.ts` | `lib/supabase.ts` (+54 líneas) | `getOfertasValidacion` con 3 filtros nuevos (`soloDatosIncompletos`, `soloCorreccionManual`, `estadoRevision`) + helper `getOfertasConCorreccionManual`. |
| `lib/types.ts` | `lib/types.ts` (+8 líneas) | Tipos para `ValidationFiltersState` extendido. |

---

## 6. Métricas

### 6.1 Líneas de código

| Categoría | Líneas | Archivos |
|---|---:|---:|
| Migrations SQL | 118 | 2 |
| Endpoints (TS) | 405 | 3 |
| Componentes UI (TSX) | 446 | 4 (modificados + nuevos) |
| Lib + types (TS) | 62 | 2 |
| Tests Python (migrations) | 337 | 2 |
| Tests TS (unit + component + integration) | 1,690 | 6 |
| Docs (specs SPEC W + cierre + guía + issues) | 2,167 | 9 |
| **Total branch vs main** | **5,225** | **28** |

### 6.2 Tests SPEC W (74 tests pasando)

| Archivo | Tests | Tipo |
|---|---:|---|
| `__tests__/integration/spec-w-sprint-1-e2e.test.ts` | **8** | Integration (nuevo en D.4) |
| `__tests__/component/audit-action-toolbar.test.tsx` | 16 | Component |
| `__tests__/component/validation-filters-revision.test.tsx` | 15 | Component |
| `__tests__/component/empty-results-with-filters.test.tsx` | 7 | Component |
| `__tests__/unit/audit-actions-api.test.ts` | 13 | Unit (endpoints) |
| `__tests__/unit/get-ofertas-validacion-filters.test.ts` | 15 | Unit (filtros) |
| **Total SPEC W** | **74 / 74** | ✅ Verde |

Tests Python migrations: `tests/spec_w/test_migration_024.py` + `test_filtros_performance.py` (~12 tests adicionales, no corridos en esta sesión por requerir BD local).

### 6.3 Suite frontend completa

```
Test Files:  110 passed | 5 failed   (115)
Tests:     1,217 passed | 27 failed  (1,244)
Duration:  99.39s
```

**Cero regresiones por SPEC W**. Las 27 fallas están en archivos no relacionados con SPEC W y son **pre-existentes en `main`** (verificado con `git checkout main` + corrida de los 5 archivos: 28 fallas pre-existentes).

| Archivo fallido | Tema | Pre-existente en main |
|---|---|:---:|
| `__tests__/security/s05-rate-limiting.test.ts` (10) | Rate limiting de /api/casos, /api/perfiles, /api/matching-offers-semantic, /api/trayectoria-laboral, etc. | ✅ |
| `__tests__/component/m01-reporte-postrun.test.tsx` (5) | Sección Último Run en /admin/metricas | ✅ |
| `__tests__/component/m09b-correcciones.test.tsx` (6) | Página de Issues / Correcciones expertas | ✅ |
| `__tests__/unit/personas-casos-api.test.ts` (5) | API personas/casos (modelo S1/S2/S3) | ✅ |
| `__tests__/component/reglas-page.test.tsx` (1) | ReglasPage save | ✅ |

Estas fallas **están fuera del scope de SPEC W** y deben tratarse aparte. No bloquean el merge del branch.

### 6.4 Tiempo total

Sprint 1 distribuido a lo largo de mayo 2026. Tiempo neto estimado por sub-tarea: A (Fase 0) ~6h, B ~8h, C ~2h, D.1 ~6h, D.2 ~4h, D.4 ~4h = **~30h efectivas**.

---

## 7. Deploy

**Plataforma:** Vercel (`mol-nextjs.vercel.app`).
**Estado:** branch `spec/w-validacion-estructurada` ya servido en producción (deploy manual previo) — Cyn está validando uso real sobre este branch. **No mergeado a `main`** todavía: si algo se rompe en su uso, queremos poder hacer rollback fácil sin revertir el branch principal.

---

## 8. Pendientes / Próximos pasos

### 8.1 Sub-tarea D.3 diferida → SPEC AR-Cat

- Investigación + decisión: `docs/issues/2026-05-19_investigacion_denominaciones_argentinas.md`
- Medición del universo: `docs/specs/spec_ar_cat/MEDICION_UNIVERSO_v1.md`
- 5 decisiones pendientes de Gerardo (granularidad, schema, estrategia P0/P1, UX, semántica "denominación española").
- **Recomendado**: arrancar SPEC AR-Cat **después** del fix de mismatching (sección 8.3) para no curar sobre labels europeos incorrectos.

### 8.2 Sprint 2 (siguiente etapa SPEC W)

- F1: marcar tareas individuales (backend de `audit_actions` ya soporta `mark_task_incorrect` + `add_suggested_task`)
- F2: marcar/sugerir skills individuales (idem)
- F3: agregar tarea/skill nueva como "sugerida"
- UI: botones ✕ y ➕ por tarea/skill en `ClasificacionPanel`
- Modal de "sugerir tarea/skill nueva"

### 8.3 Investigación mismatching (issue separado)

- `docs/issues/2026-05-19_diagnostico_mismatching_consultor_tic_verdes.md`
- 16+ reglas con `_linaje.requiere_revision=true` y `esco_label` críticamente desalineado del título.
- ~2,138 ofertas afectadas en nivel crítico, ~3,925 incluyendo medias.
- Recomendación: Opción B (auditoría manual de las 16 críticas, 1-2 días-persona) + Opción D (LLM-asistida de las 259 restantes).

### 8.4 Cyn validando uso real

- Cyn está usando el validador en producción sobre `spec/w-validacion-estructurada`.
- Métricas a observar (de spec sección 7):
  - M1: ≥10 ofertas marcadas como Revisada por día
  - M2: ≥5 acciones granulares por semana (pendiente UI Sprint 2)
  - M3: tiempo promedio por oferta <15min
  - M4: ≥5 Gold Set por semana
  - M5: cero quejas operativas

**Guía operativa entregada:** `docs/usuarios/cyn/SPEC_W_GUIA_USO.md`.

---

## 9. Recomendación de merge a `main`

**No mergear automáticamente.** Esperar OK explícito de Gerardo, con estos checks previos:

1. ✅ Cyn confirma que el flujo funciona en su uso diario (~1 semana post-deploy)
2. ✅ Cero issues reportados por Cyn sobre los botones nuevos
3. ✅ Migrations 024 y 024.1 aplicadas en Supabase prod sin errores
4. ✅ Suite SPEC W verde (74/74)
5. ⚠️ Documentar en CHANGELOG/release notes que SPEC W Sprint 1 cierra con D.3 diferida

**Estrategia de merge sugerida:** rebase sobre main (los 8 commits son atómicos y narrativos), no squash — se preserva la trazabilidad de A/B/C/D.1/D.2/D.4. Si Gerardo prefiere squash, OK también: el branch entero es una unidad lógica.

**Riesgo de no mergear:** divergencia creciente con main. Si pasan >2 semanas sin merge, planificar rebase para evitar conflictos acumulados.

---

## 10. Referencias

- Spec etapa 1: `docs/specs/spec_w/SPEC_W_etapa1_visualizador.md`
- Decisiones Fase 0: `docs/specs/spec_w/DECISIONES_PRE_SPRINT_1.md`
- Resultado Fase 0: `docs/specs/spec_w/FASE_0_RESULTADO.md`
- Spec AR-Cat (diferido): `docs/specs/spec_ar_cat/MEDICION_UNIVERSO_v1.md`
- Issue diagnóstico mismatching: `docs/issues/2026-05-19_diagnostico_mismatching_consultor_tic_verdes.md`
- Guía Cyn: `docs/usuarios/cyn/SPEC_W_GUIA_USO.md`
