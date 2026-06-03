# Decisiones Pre-Sprint 1 — SPEC W

**Fecha:** 2026-05-19
**Aprobadas por:** Gerardo
**Base:** [FASE_0_RESULTADO.md](FASE_0_RESULTADO.md) sección "Decisiones pendientes"

---

## D1 — Schema para marcas granulares de tareas

**Decisión:** Opción 1.

`audit_actions.target_value` guarda el texto exacto de la tarea. No se crea
tabla relacional `ofertas_tareas`.

**Riesgo conocido:** Si re-NLP cambia el texto de la tarea, la marca
pierde referencia. Se acepta. Si pérdida supera 20% en métricas, escalar
a Opción 2 (tabla relacional).

---

## D2 — Backfill retroactivo de notas históricas

**Decisión:** No para Etapa 1.

Las 216 notas de Cyn en `validacion_correcciones.nota` (JSONB) quedan
como historial separado. Etapa 2 puede leerlas como fuente secundaria
si los detectores necesitan más data.

---

## D3 — Granularidad de "mal extraída total"

**Decisión:** Flag simple + nota libre opcional.

Se agrega columna `estado_revision = 'mal_extraida_total'` en
`ofertas_dashboard` (ya prevista en SPEC). Sin desglose por bloque
(NLP/tareas/skills/ocupación). Si Cyn quiere explicar matices, lo hace
en nota libre.

---

## D4 — Diferenciar "tarea sugerida nueva" de "edición de tarea"

**Decisión:** Action separada (`add_suggested_task`).

Ya resuelto en SPEC W Etapa 1, sección 3.1.1 (enum de action_type).

---

## D5 — Crear audit_actions o reusar audit_log

**Decisión:** Crear `audit_actions` separada.

`audit_log` (existente, vacía, multi-tenant) NO se reusa. Semántica
distinta. Documentar `audit_log` como deuda menor en backlog.

---

## D6 — Algoritmo de similitud para Etapa 3

**Decisión:** Heurística B (ISCO + sector + ≥1 keyword común en título).

Sin pgvector. Sin embeddings. Suficiente para arrancar.

**Escalación posterior:** Si M4 (-30% tiempo) no se cumple en 8 semanas,
considerar Opción A (embeddings sobre descripción) o Opción C (híbrido).

---

## D7 — Merge de feature/spec-e antes de Sprint 1

**Decisión:** Resuelto.

`feature/spec-e-embeddings-enriquecidos` fue mergeado a main
(2026-05-19, commit `dec5525e`). Los pre-requisitos están presentes:
- Filtro por `run_id` disponible
- Endpoint `/api/gold-set-metrics` disponible
- Migrations 022/023/065 aplicadas

Adicionalmente, bugs prerequisito B1 y B2 reportados por Cyn fueron
fixeados y mergeados a main (2026-05-19, commit `4d365179`):
- B1: guardia de input/textarea/dialog en listener global de flechas
- B2: feedback visual cuando búsqueda + filtros activos retorna vacío

---

## D8 — Cobertura parcial del filtro F7 "datos incompletos"

**Decisión:** Generated column con cobertura 67%.

**Contexto:** El filtro F7 originalmente debía detectar ofertas con
ESCO/skills/tareas/score bajo. La verificación "sin skills" requiere
JOIN con `ofertas_skills` que en 68K filas tarda 1.8-9s.

**Solución aplicada:** Generated column `datos_incompletos` cubre
4 condiciones rápidas (sin ESCO, sin tareas explícitas, tareas vacías,
score < 0.5). Excluye el chequeo "sin skills puro" (~1.4K ofertas =
33% del concepto original cuando se considera el universo de matching
del filtro F7).

**Riesgo:** Cyn puede notar que algunas ofertas sin skills no aparecen
en el filtro. Si lo reporta, se agrega columna `tiene_skills` con
trigger en Sprint 2 (o equivalente).

**Decisión de iterar:** Validar uso real primero. Si Cyn no nota
limitación o no lo reporta, dejar así. Si lo reporta, escalar.

**Aplicado en:** `migrations/024_1_spec_w_performance_filtros.sql`.

**Métricas pre/post migration:**

| Query | Antes | Después |
|---|---|---|
| `solo_datos_incompletos` count | 1815 ms | 21.7 ms |
| `estado_revision IS NULL` LIMIT 50 | 4902 ms | 16.7 ms |
| `datos_incompletos = true` LIMIT 50 | n/a | 2.4 ms |
| `estado_revision IS NULL` count exact | 4902 ms | 2845 ms (mitigar con `count: 'planned'` en frontend) |

---

## Próximos pasos

1. **Etapa 1 Sprint 1 (semana 1):** Schema + backend
   - Migration 024: tabla `audit_actions` + columnas en `ofertas_dashboard`
   - Endpoints `POST /api/audit-actions`, `DELETE`, `GET history`
   - Tests unitarios sobre RPCs y endpoints

2. **Etapa 1 Sprint 2 (semana 2):** UI básica
   - `AuditActionToolbar` con botones Revisada / Mal extraída total
   - `FeedbackToast` con feedback visual al guardar (F6)
   - Modificación de `ClasificacionPanel` con botones ✕ y ➕ por tarea/skill
   - Tests E2E del flujo básico

3. **Etapa 1 Sprint 3 (semana 3):** Filtros + refinamientos
   - Filtros nuevos (F7, F8) en `ValidationFilters`
   - Denominación Argentina/España en `PuestoPanel` (F9)
   - Polish de UX

4. **Etapa 1 Sprint 4 (semana 4):** Validación con Cyn
   - Cyn opera el flujo nuevo en producción
   - Ajustes según feedback
   - Documentación operativa
   - Cierre de Etapa 1

---

## Anexo — Riesgos identificados de las decisiones

| Decisión | Riesgo | Mitigación |
|----------|--------|------------|
| D1 | Re-NLP rompe referencias por texto | Monitorear pérdida, escalar a tabla relacional si supera 20% |
| D2 | Etapa 2 no tiene data suficiente | Plan B: parseo parcial de notas como ingest a `audit_actions` |
| D3 | Cyn pide desglose después | Aditivo: agregar columnas detalle sin romper schema actual |
| D6 | Similitud heurística genera falsos positivos | Mostrar score visible para que Cyn juzgue |
| D8 | Cyn pide cobertura completa (incluir sin skills) | Aditivo: agregar columna `tiene_skills` + trigger en Sprint 2 sin romper schema |
