# SPEC W — Fase 0: Resultado

**Fecha de ejecución:** 2026-05-19
**Branch:** `spec/w-validacion-estructurada` (desde `main`)
**Modo:** read-only sobre BD local y Supabase
**Tiempo activo:** ~3 horas

---

## Veredicto global

**OK CON AJUSTES.**

No hay bloqueos críticos para arrancar Etapa 1. Todas las precondiciones técnicas (credenciales, RPCs, schema base, capacidad DDL) están dadas. Hay 5 decisiones de diseño pendientes que requieren input de Gerardo antes de Sprint 1 de Etapa 1, y 3 bugs prerequisito operativos que deben registrarse como issues y resolverse antes de que Etapa 1 sea operable.

---

## Bloque A — Tipos de datos

**Estado:** OK con observaciones.

### A.1 `ofertas_dashboard` (56 columnas)

9 de 10 columnas requeridas presentes:

| Columna | Estado |
|---------|--------|
| `id_oferta` | OK |
| `validacion_humana` | OK (valores: ok/error/revisar/basura) |
| `validacion_humana_at` | OK |
| `validacion_humana_por` | OK |
| `esco_occupation_uri` | OK |
| `esco_occupation_label` | OK |
| `isco_code` | OK |
| `run_id` | OK |
| `matching_version` | OK |
| `observaciones` | **NO EXISTE — viven en `validacion_correcciones.nota` (JSONB)** |

**Hallazgo crítico:** El SPEC asume columna `observaciones` independiente. En realidad las notas libres de Cyn viven en `validacion_correcciones` (JSONB) bajo la clave `nota`. Etapa 2 puede leer esto sin cambios, pero el diseño debe documentar `validacion_correcciones->>'nota'` como source.

### A.2 `gold_set`

- **112 casos activos** (confirma estado post-Paso D).
- Schema: 11 columnas (`id`, `id_oferta`, `esco_ok`, `isco_esperado`, `esco_esperado`, `tipo_error`, `comentario`, `agregado_por`, `agregado_at`, `version_reglas`, `activo`).
- Distribución: 49 migracion_inicial, 38 cinvazquez4@gmail.com, 14 claude_*, 7 otros.

### A.3 `ofertas_skills` (skills ESCO mapeadas)

- Tiene `id` propio por skill → ID estable para marcar individualmente (cumple F2 del SPEC).
- Columnas: `skill_uri`, `preferred_label`, `l1/l2`, `es_digital`, `es_esencial`, `es_opcional`, `origen`, `score`.
- **No tiene** columna `categoria` con valores "Correcta / Implícita fuerte / Implícita pertinente / Incorrecta". Esa categorización vive en lógica de UI (no en BD). Las marcas que Cyn agregue irán a `audit_actions` con `target_type='skill'` y `target_id = ofertas_skills.id`.

### A.4 Tareas extraídas

**Bloqueo de diseño:** `ofertas_dashboard.tareas_explicitas` es **TEXT** con tareas separadas por `;`. No hay tabla relacional ni IDs por tarea.

Esto rompe el supuesto del SPEC: "marcar tarea individual como incorrecta" requiere identificación estable. Dos caminos:

- **Opción 1 (mínima):** `audit_actions.target_value` guarda el texto exacto de la tarea. Si la tarea cambia (re-NLP), la marca pierde referencia. Aceptable para empezar.
- **Opción 2 (estructural):** Crear `ofertas_tareas` (id, id_oferta, texto, orden, fuente) y migrar. Más invasivo pero más robusto. Requiere migration adicional.

**Recomendación:** Opción 1 para Etapa 1. Si los re-NLP rompen >20% de las marcas, escalar a Opción 2.

### A.5 BD local SQLite (`database/bumeran_scraping.db`, 3.5 GB)

- 54 tablas. Las relevantes para SPEC W:
  - `ofertas_nlp` (69.794 filas, 171 columnas) — `tareas_explicitas` TEXT también.
  - `ofertas_esco_matching` (68.241 filas, 49 columnas).
  - `ofertas_esco_skills_detalle` (1.569.227 filas) — granular por skill, tiene `texto_original`, `match_method`, `source_classification`.
  - `validation_errors` (278.565 filas) — historial completo de errores.
  - `validacion_humana` local: **0 filas** (Cyn nunca valida en local; todo es Supabase).

### A.6 Datos históricos de Cyn

| Métrica | Valor |
|---------|-------|
| Total ofertas validadas por Cyn | **224** |
| Por categoría | 216 revisar, 5 ok, 3 error |
| Por mes | 2026-03: 73, 2026-04: 98, 2026-05: 53 |
| Con `validacion_correcciones.nota >10 chars` | **216** (96%) |
| Otros validadores | Diego Schlese: 7, Gerardo: 1 |

**216 ofertas tienen notas explotables** para Etapa 2 (detección de patrones). Esto cumple holgadamente la dependencia "4-6 semanas de datos" mencionada en SPEC W.

---

## Bloque B — Endpoints y RPCs

**Estado:** OK con gaps identificados.

### B.1 RPCs Supabase (73 total)

| Requerida por SPEC | Estado | Notas |
|--------------------|--------|-------|
| `get_ofertas_validacion` | **NO existe** | Se usa SELECT directo en PostgREST via `lib/supabase.ts:getOfertasValidacion()` (filtros en JS, no en RPC) |
| `get_runs_disponibles` | OK | |
| `get_gold_set_metrics` | **NO existe** | El endpoint Next.js `/api/gold-set-metrics` se creó en otro branch (`feature/spec-e-embeddings-enriquecidos`), no en `main` |
| `insertar_pipeline_run` | OK | |
| `guardar_validacion_humana(p_id_oferta, p_resultado, p_correcciones)` | OK | Es la RPC que Cyn usa hoy |
| `agregar_a_gold_set` (8 params) | OK | |
| `get_gold_set_stats` | OK | |
| `log_accion` y `log_action` | OK (duplicadas) | Deuda menor de naming |
| `reconciliar_sistemas` | OK | Usada por `/admin/metricas` |

### B.2 Endpoints Next.js (~80 paths)

| Endpoint | Estado |
|----------|--------|
| `/api/gold-set` | OK (GET stats + POST agregar + DELETE) |
| `/api/gold-set/candidates` | OK |
| `/api/processing-metrics` | OK |
| `/api/pipeline-status` | OK |
| `/api/issues/[id]/propagation` | OK (sistema SPEC T) |
| `/api/gold-set-metrics` | **NO en main** (sí en feature/spec-e) |
| `/api/pipeline-runs` | **NO existe** |

### B.3 Endpoints nuevos requeridos por SPEC W

Para Etapa 1:
- `POST /api/audit-actions` (registrar acción granular)
- `DELETE /api/audit-actions/:id` (deshacer)
- `GET /api/oferta/:id/audit-history` (historial)
- Extensión a `lib/supabase.ts:getOfertasValidacion()` con params `solo_datos_incompletos`, `solo_correccion_manual`, `estado_revision`.

Para Etapa 2:
- `GET /api/correction-patterns`
- `POST /api/correction-patterns/:id/review`
- `POST /api/correction-patterns/run-detection`

Para Etapa 3:
- `GET /api/correction-impact/:validador`
- `GET /api/similar-validated/:id_oferta`
- `POST /api/correction-feedback/:impact_id`
- `GET /api/recent-applied-corrections/:validador`

### B.4 UI actual de validación

| Componente | Líneas | Rol |
|---|---|---|
| `app/admin/validacion/page.tsx` | 365 | Orquestador (3-panel split) |
| `components/validacion/ValidationFilters.tsx` | 315 | 11 filtros (NO incluye filtro por run_id en main) |
| `components/validacion/OfertaList.tsx` | 100 | Panel 1 (20%) |
| `components/validacion/PuestoPanel.tsx` | 124 | Panel 2 (40%, NLP+tareas+skills text) |
| `components/validacion/ClasificacionPanel.tsx` | 154 | Panel 3 (40%, ISCO+skills ESCO) |
| `components/validacion/OfertaDetailSkills.tsx` | 108 | Sub-componente skills |
| `components/validacion/ValidationActions.tsx` | 457 | Sticky bottom bar (OK/Error/Revisar/Basura + crear issue) |
| `components/validacion/GoldSetModal.tsx` | 201 | Modal Gold Set (Alt+6) |

**Puntos de inyección para Etapa 1:**

| Funcionalidad SPEC | Componente a tocar |
|---|---|
| F1 ✕ por tarea | `PuestoPanel.tsx` (sección "Tareas") |
| F2 ✕/➕ por skill | `OfertaDetailSkills.tsx` (skills ESCO) + `PuestoPanel.tsx` (skills NLP) |
| F3 agregar sugerida | Modal nuevo, disparado desde PuestoPanel/ClasificacionPanel |
| F4 marcar Revisada | `ValidationActions.tsx` (nueva acción junto a OK/Error) o toolbar separada |
| F5 mal extraída total | `ValidationActions.tsx` |
| F6 toast feedback | Componente nuevo `FeedbackToast` global |
| F7 filtro datos incompletos | `ValidationFilters.tsx` |
| F8 filtro corrección manual | `ValidationFilters.tsx` |
| F9 denominación AR/ES | `PuestoPanel.tsx` |
| F10 source en audit_actions | Backend/RPC, no visible en UI |

---

## Bloque C — Permisos y credenciales

**Estado:** OK.

### C.1 Credenciales Supabase

| Credencial | Estado |
|---|---|
| `anon_key` | OK (lectura RLS-public) |
| `service_role_key` | OK (UPDATE/DELETE confirmado con test PATCH) |
| `management_api_token` | OK (funciona — endpoint `/database/query` responde 201) |
| `project_ref` | OK (`uywzoyhjjofsvvsrrnek`) |

**Pendiente crítico de seguridad:** S-01 (rotación service_role_key) sigue abierto según CLAUDE.md. No bloquea Fase 0 pero debe resolverse antes de cualquier deploy de Etapa 1.

### C.2 VPS

- SSH `root@187.124.150.28` configurado con id_ed25519, accesible. Necesario para refresh de prioridades y eventuales scripts batch.

### C.3 Capacidad de migrations

- **Management API permite DDL completo.** Test pasó: `CREATE TABLE spec_w_fase0_test (id INT); DROP TABLE spec_w_fase0_test;` → status 201.
- RPC `exec_sql` NO está expuesta via PostgREST (intencional). DDL solo via Management API o Supabase Studio web.
- RLS de `ofertas_dashboard`: lectura pública, modificación solo service_role.
- Implicación: Claude puede ejecutar las migrations 023/024/025 de forma automatizada vía Management API, sin requerir que Gerardo entre a Studio.

---

## Bloque D — Plan de tests por etapa

**Estado:** Definido. Cobertura objetivo: ≥80% sobre código nuevo.

### Infraestructura existente

- **Frontend:** vitest v4 + Testing Library + MSW + happy-dom. 933+ tests vivos.
- **Tests por categoría:**
  - `__tests__/component/` (60 archivos) — componentes React
  - `__tests__/unit/` (37 archivos) — utilidades + endpoints
  - `__tests__/integration/` (3 archivos)
  - `__tests__/security/` (7 archivos, S01-S25)
- **Mocks:** `__tests__/mocks/handlers.ts` (722 líneas) intercepta Supabase RPCs y PostgREST.
- **Backend:** pytest 157 tests Python.

### D.1 Tests Etapa 1 (Visualizador)

**Component tests obligatorios (carpeta `__tests__/component/`):**

| Test | Cubre |
|---|---|
| `audit-actions-bar.test.tsx` | F4 marcar revisada / F5 mal extraída total / toast F6 |
| `clasificacion-panel-skills-actions.test.tsx` | F2 ✕/➕ skills |
| `puesto-panel-tasks-actions.test.tsx` | F1 ✕ tareas + F9 denominación AR/ES |
| `validation-filters-new.test.tsx` | F7 + F8 nuevos filtros |
| `suggest-task-modal.test.tsx` | F3 modal agregar tarea sugerida |
| `feedback-toast.test.tsx` | F6 timing < 500ms |

**Unit tests (carpeta `__tests__/unit/`):**

| Test | Cubre |
|---|---|
| `audit-actions-api.test.ts` | POST/DELETE/GET history endpoints |
| `get-ofertas-validacion-filters.test.ts` | Filtros nuevos en `lib/supabase.ts` |
| `build-audit-rpc-filters.test.ts` | Helpers de query |

**Tests de regresión (deben seguir verdes):**

- `validacion-filters.test.ts` (filtros previos)
- `learning-dashboard.test.tsx`
- Stats de validación (categorías ok/error/revisar/basura)

**Tests de schema (Python pytest):**

| Test | Cubre |
|---|---|
| `test_audit_actions_migration.py` | Migration 023 reversible (DROP + recreate) |
| `test_backfill_columnas_nuevas.py` | No pierde datos existentes |
| `test_audit_actions_inmutable.py` | UPDATE/DELETE bloqueado en audit_actions |

### D.2 Tests Etapa 2 (Patrones)

| Test | Cubre |
|---|---|
| `test_detector_isco_reassignment.py` | Detector A con dataset semilla (las 30 correcciones de Cyn sobre ISCO 0110) |
| `test_detector_keywords.py` | Detector B keywords ambiguos |
| `test_detector_tasks_systematic.py` | Detector C tareas |
| `test_detector_skills_systematic.py` | Detector D skills |
| `test_confidence_threshold.py` | Candidatos <0.7 no se muestran como activos |
| `test_no_false_positives.py` | Cero candidatos espurios sobre dataset aleatorio |
| `test_etapa2_no_modifica_etapa1.py` | Análisis de patrones no toca `audit_actions` |

### D.3 Tests Etapa 3 (Loop feedback)

| Test | Cubre |
|---|---|
| `correction-impact-panel.test.tsx` | F1 vista de impactos |
| `similar-validated-badge.test.tsx` | F2 badge en panel detalle |
| `test_similarity_heuristic.py` | Opción B (ISCO + sector + keywords) devuelve resultados <1s |
| `test_correction_feedback_persiste.py` | Feedback retroactivo se guarda |

### D.4 Tests transversales

**Performance:**

- Page load `/admin/validacion` < 2s con ~70K ofertas (medir en producción).
- POST `/api/audit-actions` responde < 500ms (test e2e con `expect.objectContaining({status: 200})`).
- Query "similares" responde < 1s.

**Seguridad (extender `__tests__/security/`):**

- `s26-audit-actions-inmutable.test.ts` — DELETE solo crea inversa, no borra.
- `s27-audit-actions-rls.test.ts` — anon no puede insertar/leer `audit_actions` de otros.
- `s28-source-field-no-manipulable.test.ts` — campo `source` no permite valores fuera del CHECK.

---

## Bloque E — Dependencias externas

**Estado:** Bugs operativos NO resueltos. Bloqueo parcial para arrancar Etapa 1.

### E.1 Bugs prerequisito (de cuestionario Cyn)

| Bug | Estado | Acción |
|---|---|---|
| B1 "Oferta cambia automáticamente entre secciones" | NO registrado como issue en BD ni en `docs/issues/` | **Crear issue + reproducir + fixear antes de Sprint 1 de Etapa 1** |
| B2 "Buscador por ID inconsistente" | NO registrado como issue | **Crear issue + fixear antes de Sprint 1** |
| B3 R3 V27 (454 falsos positivos) | Diagnosticado en `docs/issues/2026-05-19_diagnostico_escalados_regimen.md` — PAUSADO esperando cuestionario | Opcional, no bloquea SPEC W |

**Recomendación:** Antes de Sprint 1 de Etapa 1, abrir 2 issues (B1, B2) y resolver. Sin esto, los ajustes de UI nuevos se construyen sobre una base inestable.

### E.2 Capacitación Alt+6 a Cyn

- **No verificable desde código.** Según SPEC W (sección 4.1) y el origen del cuestionario, Cyn nunca usó Alt+6 sistemáticamente. Las 36 ofertas que aporta al gold set vinieron por ingesta de Excel histórico, no marcado en vivo.
- **Acción:** 15 min de demo + 1 página de instrucciones, antes de validación con usuaria (Sprint 4 de Etapa 1).
- No bloqueante para Sprints 1-3, sí para medir M4 (≥5 ofertas Gold Set por semana de Cyn).

### E.3 Dependencias de datos para Etapa 2

- 216 ofertas con notas de Cyn ya disponibles para entrenar/probar detectores. Cumple holgadamente "4-6 semanas de datos".
- Las correcciones de Cyn históricas (216 con `validacion_correcciones.nota`) requieren ser ingestadas a `audit_actions` retroactivamente — Decisión D2 pendiente.

---

## Bloque F — Riesgos técnicos

**Estado:** Verificados. 2 con mitigación clara, 2 requieren decisión de diseño.

### F.1 Schema soporta marcar tareas individuales

**Riesgo:** Las tareas viven como TEXT en `ofertas_dashboard.tareas_explicitas` sin IDs estables.

**Mitigación recomendada:** Opción 1 (target_value = texto exacto) para Etapa 1. Documentar limitación: si re-NLP cambia el texto, la marca queda huérfana. Escalar a tabla `ofertas_tareas` relacional solo si pérdida >20% en métricas.

### F.2 Schema soporta múltiples categorías por skill

**Estado:** No hay restricción de exclusividad en `ofertas_skills`. Una skill puede tener varios flags (`es_esencial`, `es_opcional`, `es_digital`). Las marcas humanas via `audit_actions` son aditivas (cada acción es un registro nuevo).

**Sin riesgo.**

### F.3 Race conditions en validación

**Estado:** Verificado.
- Existe trigger `trigger_ofertas_updated_at` BEFORE UPDATE que mantiene `updated_at`.
- `audit_actions` es append-only por diseño (sin UPDATE/DELETE excepto via inversa) → no hay race condition posible.
- `ofertas_dashboard.updated_at` puede usarse como ETag opcional si se quiere optimistic locking.
- Sync VPS → local NO escribe en `ofertas_dashboard` (solo lee). Sin conflicto.

**Mitigación:** En endpoint `POST /api/audit-actions`, NO modificar `ofertas_dashboard` directamente. Las columnas `estado_revision`, `audit_state` se derivan via trigger ON INSERT en `audit_actions` o vista materializada (preferible).

### F.4 Búsqueda de "ofertas similares" para Etapa 3

**Estado:**
- pgvector **instalado** en Supabase (extensión `vector`).
- `occupations_embeddings` y `skills_embeddings` existen.
- **`ofertas_embeddings` NO existe.**
- BGE-M3 model disponible localmente.

**Opciones:**

- **B (heurística):** ISCO + sector + ≥1 keyword común en título. Sin pgvector. Suficiente para arrancar Etapa 3.
- **A (embeddings):** Generar embeddings de descripción de ofertas (~70K), guardar en `ofertas_embeddings`. Cosine similarity. Más preciso. Costo: ~10h de generación + storage Supabase. **Trabajo iniciado en branch paralelo `feature/spec-e-embeddings-enriquecidos`** — verificar estado de ese trabajo antes de duplicar.
- **C (híbrido):** A para ranking + B para corte. Mejor calidad. Costo: A + tuning.

**Recomendación:** Empezar Etapa 3 con B. Si M1 (Cyn entra al panel ≥1/semana) se cumple pero M4 (-30% tiempo) no, considerar migrar a A.

### F.5 Tabla `audit_log` ya existente

**Hallazgo no anticipado por SPEC:** Existe tabla `audit_log` en Supabase (creada para multi-tenancy: `usuario_id`, `organizacion_id`, `accion`, `recurso`, `detalle JSONB`), **vacía** (0 filas).

**Decisión:** No reusar `audit_log` para audit_actions. La semántica difiere (audit_log es genérica admin, audit_actions es específica de validación de ofertas con campos enum). Crear `audit_actions` separada. Documentar `audit_log` como deuda menor.

### F.6 Filtro por `run_id` en main

**Hallazgo no anticipado:** El SPEC menciona "Filtro Run/Corrida implementado en Sprint 18" como funcionalidad existente que NO se toca. **Ese filtro NO está en `main`** — vive en `feature/spec-e-embeddings-enriquecidos`. Hay que coordinar el merge antes de Sprint 1 de Etapa 1, o sus tests pueden fallar.

---

## Decisiones pendientes (requieren input de Gerardo)

| # | Decisión | Opciones | Recomendación Claude | Cuándo |
|---|----------|----------|----------------------|--------|
| D1 | Schema para marcas granulares de tareas (sin ID estable) | Op 1: target_value = texto / Op 2: tabla `ofertas_tareas` relacional | **Op 1** (más simple, escalar después si pérdida >20%) | Antes Sprint 1 |
| D2 | Backfill retroactivo de las 216 notas de Cyn a `audit_actions` | Sí parcial (parsing manual del texto libre, lossy) / Sí completo / No (queda como historial separado en `validacion_correcciones`) | **No** para Etapa 1, **Sí parcial** opcionalmente en Etapa 2 si los detectores piden más data | Antes Sprint 1 |
| D3 | Granularidad de "mal extraída total" | Flag simple / Detalle por bloque (NLP/tareas/skills/ocupación) | **Flag simple** + nota libre opcional | Antes Sprint 1 |
| D4 | Diferenciar "tarea sugerida nueva" de "edición de tarea existente" | Action separada / misma acción con flag | **Action separada** (`add_suggested_task` ya está en el enum del SPEC) | Resuelto en SPEC |
| D5 | ¿Crear tabla `audit_actions` o reusar `audit_log`? | Crear / Reusar | **Crear** (semántica diferente, `audit_log` está vacía pero es multi-tenant genérica) | Antes Sprint 1 |
| D6 | Algoritmo de similitud Etapa 3 | Heurística B / Embeddings A / Híbrido C | **B** para empezar, escalar a A si M4 no se cumple | Sprint 1 Etapa 3 |
| D7 | Modo de Etapa 1 con respecto a `feature/spec-e-embeddings-enriquecidos` | Merge ese branch a main antes / Trabajar en paralelo y resolver conflictos al final | **Merge antes** (su filtro por run_id es prerequisito de F8) | Antes Sprint 1 |

---

## Estimación final

Basada en evidencia (líneas de código existentes, número de tests a escribir, complejidad de cada bloque).

| Etapa | Backend (h) | Frontend (h) | Tests (h) | Total (h) | Semanas calendar |
|---|---|---|---|---|---|
| Etapa 1 | 25 | 35 | 25 | **85** | 3-4 |
| Etapa 2 | 35 | 15 | 20 | **70** | 3 |
| Etapa 3 | 20 | 25 | 15 | **60** | 2-3 |
| **Total** | **80** | **75** | **60** | **215** | **8-10** |

**Asunciones:**
- 1 desarrollador part-time (~20h/semana efectivas)
- No incluye tiempo de Cyn en validaciones con usuaria
- No incluye fix de bugs prerequisito B1 y B2 (estimar +8h)
- No incluye eventuales rollbacks o re-trabajos por feedback de Cyn

**Margen de error:** ±30%. Lecciones aprendidas en sesiones previas indican multiplicar por 1.3-1.5x estimaciones iniciales (memoria `feedback_estimaciones_tiempo`).

---

## Próximo paso recomendado

**Avanzar a Etapa 1 con condiciones:**

1. Gerardo decide D1, D2, D3, D5, D7 (las que están sin "Resuelto en SPEC").
2. Crear 2 issues en Supabase: B1 (cambia entre secciones) + B2 (buscador por ID). Fixear en paralelo a Sprint 1 de Etapa 1.
3. Decidir si merge de `feature/spec-e-embeddings-enriquecidos` a `main` ocurre antes o después de Sprint 1.
4. Coordinar capacitación Alt+6 con Cyn (15 min) — agendar para Sprint 4.

**No avanzar si:**
- Las decisiones D1, D2, D3, D5, D7 no se cierran antes de Sprint 1 — derivaría en re-trabajo de schema.
- Bugs B1 y B2 no tienen plan de resolución claro.

---

## Apéndice — Comandos ejecutados durante Fase 0

Read-only sobre BD local SQLite + Supabase via service_role_key + Management API. Cero modificaciones a schemas, datos o código.

| Tipo | Detalle |
|---|---|
| Supabase REST (PostgREST) | `select`, `count` sobre `ofertas_dashboard`, `gold_set`, `ofertas_skills`, `issues` |
| Supabase Management API | `SELECT` queries sobre `pg_tables`, `pg_policies`, `information_schema.columns`, `pg_extension`, `pg_trgm`, `vector` |
| SQLite local | `PRAGMA table_info`, `SELECT COUNT(*)` sobre 54 tablas |
| Filesystem | Read sobre `fase3_dashboard/mol-dashboard/{app,components,lib}/` (no modificaciones) |
| Test DDL ephemeral | `CREATE TABLE spec_w_fase0_test (id INT); DROP TABLE spec_w_fase0_test;` (auto-rollback) |

Branch `spec/w-validacion-estructurada` queda con un único cambio: este reporte y archivos de soporte si se crean.
