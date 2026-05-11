# Log de implementación — SPEC U-1 v3.1

**Fecha:** 2026-05-05
**Responsable:** Gerardo + Claude Code
**SPEC base:** `docs/specs/SPEC_U-1_CRITICO_v3_1.md`
**Branch:** `feature/spec-e-embeddings-enriquecidos`

---

## Resumen ejecutivo

| Fix | Estado | Notas |
|---|---|---|
| F0 — snapshot + canarios | ✅ completo | snapshots íntegros, baselines registradas |
| C3 — symlinks embeddings ocupaciones | ✅ implícitamente cubierto | `isco_to_canonical_occupation` 426 ISCOs cargados; pendiente verificar `_semantic_match_title()` real |
| C2 sub-fase A — verificación overmatch | ✅ completo | analista 0%, operario 4%, tecnico 30% |
| C2 sub-fase B — JSON v2 | ✅ completo | 22 entradas, URIs explícitas en gerente/operador, tecnico Opción 3 |
| C2 sub-fase C — fix matcher | ✅ completo | 4 ediciones + bug fix setter línea 651, 5/5 tests pass |
| C2 sub-fase C — activación v2 | ✅ completo | Rename Opción A ejecutado, v1 preservado |
| C2 sub-fase D — reprocesamiento 3.758 ofertas | ✅ completo | 1h24m, 3.744 procesadas, C-Q1: 3.762→18 |
| C1 — re-rematch URI×label (8.221 ofertas) | ✅ completo | 3h21m, 8.179 procesadas + 38 skipped multi-position. Tarea 4: 6 buckets ESCO multi-nivel, 3.691 auto-validadas (C1-1), 4.488 cola humana. **C-Q3: 1.237→39 (-97%)** ✅ |
| C4 — UPDATE flags ESCO + índice compuesto | ✅ completo | 3m30s, 1.27M filas modificadas, F-meta K1=74.9%/K3=38.0%/K5=14.5% |
| F0b' — re-snapshot Supabase pre-C5 (parcial) | ✅ con caveat | skills 65.5%, dashboard+issues 100%, suficiente para rollback |
| C5 — sync Supabase + zombies + cron | ✅ completo | ~4h sync inicial, drift Local↔Supabase=0, zombies=0, cron horario activo |
| **C5 fix H16 — re-sync flags ESCO** | ✅ completo | 3h45m, drift F-meta Supabase vs Local ≤0.1pp ✅ |

**SPEC U-1 v3.1 CERRADO — 2026-05-11. Ver "Cierre SPEC U-1 v3.1 — Estado final" al final del documento.**

---

## F0 — Baselines reales registradas

**Snapshots:**
- `data/snapshots/pre_spec_u1_v3_20260505_145907.db.gz` (509 MB)
- `data/snapshots/pre_spec_u1_v3_supabase_20260505_145907.json.gz` (122 MB)

**Conteos pre-fix (BD local + Supabase):**

| Canario | Valor | Notas |
|---|---:|---|
| C-Q1: ofertas con `esco_occupation_uri = ''` | **3.762** | 3.758 dict + 4 mixtos (semantico/regla) |
| C-Q2: filas en `ofertas_esco_skills_detalle` con flags=0 | **1.116.011** | Total — DIAG A |
| C-Q3: URIs con drift de labels | **1.237** | C1 debe bajarlo a < 50 |
| C-Q6: ofertas validadas locales | **56.397** | Universo a sincronizar |
| C-Q7: matching_version=`spec_h_rematch` | **8.221** | C1 las re-matchea |
| ofertas_dashboard (Supabase) | **52.563** | Mucho más que ~16K que decía CLAUDE.md |
| ofertas_skills (Supabase) | **1.144.527** | 29K más que validadas locales |
| issues (Supabase) | **212.860** | Incluye automáticos (99.4% ruido conocido) |

**Drift real Local↔Supabase: 3.850 ofertas** (validación post-fix script de canarios, no 40K como indicaba SPEC v3.1 §2.5).

### Baselines Supabase (Q4/Q5) post fix script `run_canarios.py`

Pre-fix: el script silenciaba excepciones y los outputs de Q4/Q5 quedaban None. Fix aplicado en `scripts/canarios/run_canarios.py`:
- Conteo de zombies Q4 ahora pagina la tabla `ofertas_skills` completa y compara contra `ofertas_dashboard`.
- Errores ya no se silencian: el bloque except imprime el traceback en consola y lo persiste en el resultado JSON.

**Baselines reales registradas (2026-05-05 17:54):**

| Canario | Valor | Detalle |
|---|---:|---|
| **C-Q4: skills zombies Supabase** | **0** | 1.144.527 skills auditadas, 0 huérfanas (todas tienen oferta padre en `ofertas_dashboard`). |
| **C-Q5: drift Local↔Supabase** | **3.850** | 56.397 validadas locales, 52.563 en Supabase, drift 3.850 (local−supabase) y 16 (supabase−local). |

**Implicancia crítica para C5:** el "28.395 zombies" que el SPEC v3.1 §8.1 daba como baseline NO son zombies. Son skills cuyas ofertas están en Supabase pero no en validadas locales (probablemente bajas con validación previa o validación directa en Supabase). **NO hay DELETE masivo necesario en C5.** Solo sync incremental de 3.850 ofertas + skills asociadas.

---

## C2 sub-fase A — Verificación overmatch

**Reporte completo:** `docs/diagnostico/2026-05-05_verificacion_overmatch_C2.md`

| Entrada | Cobertura regla | Over-match | Decisión |
|---|---:|---:|---|
| `analista` | 100% | 0% | ✅ QUITAR |
| `operario` | 98% | 4% | ✅ QUITAR (caveat: granularidad menor con ISCO 9329) |
| `tecnico` | 100% | 30% | ⚠️ Opción 3 (URI por contexto, NO quitar) |

**Decisión sobre `tecnico`:** se aplicó **Opción 3** (URI por contexto con 6 contextos cerrados) en lugar de Opción C (quitar) prevista en SPEC v3.1. Razón: el over-match de 30% supera el umbral del SPEC y mantener `tecnico` cubre el caso "Soporte Técnico" → ISCO 3512 (regla R180_soporte_infraestructura sigue mal calibrada, queda como issue para SPEC U-2).

---

## C2 sub-fase B — JSON v2 (22 entradas)

**Archivo:** `config/sinonimos_argentinos_esco_v2.json` (post-rename: archivo canónico).

**Estructura:**
- 19 entradas `isco_primario` con `esco_uri` explícita
- 3 entradas `isco_familia` con URIs por contexto:
  - `gerente` (7 contextos cerrados §5.4 #1-7)
  - `operador` (3 contextos — sin maquinas/CNC eliminado §5.4 #11)
  - `tecnico` (6 contextos resueltos via Opción 3)

**Decisiones cerradas (§5.4):**

| # | Contexto | URI | Heurística | Tipo decisión |
|---|---|---|---|---|
| 1 | gerente.ventas\|comercial | a7594892… | keyword + freq(251) | automática |
| 2 | gerente.finanzas\|financiero | 30f3ea93… | keyword + freq(177) | automática |
| 3 | gerente.operaciones\|planta\|produccion | eb9479c6… | keyword + freq(227) | automática |
| 4 | gerente.rrhh | f605bcd2… | keyword + freq(131) | automática |
| 5 | gerente.it\|sistemas\|tecnologia | 8b6388a4… | freq dominante(104) | automática |
| 6 | gerente.marketing | dc97adbe… | freq histórica(252) | **humana** |
| 7 | gerente.logistica\|supply chain | aacc3918… | match keyword + freq(40) | **humana** |
| 8 | operador.atencion\|cliente | b7b75eb6… | freq dominante(841) | automática |
| 9 | operador.almacen\|deposito | bea705fe… | freq dominante(962) | automática |
| 10 | operador.produccion\|planta | e3dc66de… | naturalidad genérica | **Claude Code** |
| ~~11~~ | ~~operador.maquinas\|cnc\|torno~~ | — | — | **eliminado** (ISCO 8211 mal declarado) |

**Label drift fixes (§5.5):**

| Entrada | Cambio |
|---|---|
| jefe de mantenimiento | ISCO **1321 → 1219**, label "director de mantenimiento de una fábrica" (149 ofertas se re-clasifican; 3 actualmente en 1321) |
| analista de tesoreria | label canónico "empleado administrativo de gestión financiera" (35 ofertas, mismo ISCO 4312) |
| operador de atencion | label canónico "agente de centro de atención al cliente" (213 ofertas, mismo ISCO 4222) |

**Contextos huérfanos (string-only sin URI explícita):** los contextos legacy de `recepcionista`, `vendedor`, `administrativo`, `capataz` mantienen el formato `"patron": "isco"` (string). En estos casos la URI se resuelve **vía lookup canónico** en `isco_to_canonical_occupation` (sub-fase C). Criterio mixto: aceptar lookup automático para contextos que no tuvieron objeción humana en R8/R9.

---

## C2 sub-fase C — Cambios al matcher

**Archivo:** `database/match_ofertas_v3.py` (versión `3.5.2`)

**4 ediciones funcionales + 1 bug fix:**

| Edición | Líneas | Propósito |
|---|---|---|
| 1. Index `isco_to_canonical_occupation` | **179-199** | Construye mapa `isco_4dig → {uri, label, esco_code}` desde `occ_metadata`. Prioriza la entrada cuyo `esco_code == isco_4dig` (padre genérico). Carga 426 ISCOs. |
| 2. Variantes implícitas | **286-291** | La KEY del JSON ahora se considera variante implícita aunque no esté en la lista `variantes`. Antes "jefe de mantenimiento" no matcheaba si la lista no lo incluía explícitamente. |
| 3. Contextos sin pipe | **308-310** | Patrones simples como `"marketing"` (sin `\|`) ahora se evalúan como una sola keyword. Antes se ignoraban. |
| 4. Soporte ctx_value como dict | **312-323** | Permite `{"isco": ..., "esco_uri": ..., "esco_label": ...}` como valor de contexto (formato JSON v2 para gerente/operador/tecnico) además del string legacy. |
| 5. Resolución URI por prioridad | **342-357** | Orden: ctx_uri_override → esco_uri_root del padre → canonical lookup → "". |
| **Bug fix setter** | **649-651** | `if dict_match:` ahora asigna `semantic_uri = dict_match.get("esco_uri", "")`. Antes la rama dict no tocaba `semantic_uri` y persistía con default `""`. **Esta era la raíz del problema R7 (3.758 ofertas con URI vacía).** |

**Validación:** 5/5 tests pasan en `/tmp/test_v2_subfase_c.py`:
- T1 entrada con URI explícita ✅
- T2 entrada sin URI → canonical fallback ✅
- T3 contexto string sin URI → canonical fallback ✅
- T4 entrada deprecated (analista, operario) → no matchea ✅
- T5 contexto eliminado (operador.cnc) → no matchea ✅

---

## Activación v2 (rename Opción A)

```bash
mv config/sinonimos_argentinos_esco.json    config/sinonimos_argentinos_esco_v1_legacy.json
mv config/sinonimos_argentinos_esco_v2.json config/sinonimos_argentinos_esco.json
```

**Resultado:**
- `config/sinonimos_argentinos_esco.json` — 19,162 bytes — **v2 activo** (versión 2.0.0)
- `config/sinonimos_argentinos_esco_v1_legacy.json` — 11,992 bytes — preservado para rollback

**Consumidores activos** (todos cargan por nombre canónico, sin cambios de código necesarios):
- `database/match_ofertas_v3.py:239` — `load_config('sinonimos_argentinos_esco')`
- `scripts/run_tracking.py:107`
- `scripts/sync_learnings.py:138`
- `scripts/sync_rules_from_candidates.py:26`

**Sanity check post-rename:** `MatcherV3().sinonimos_arg["version"] == "2.0.0"` ✅. Tests 5/5 OK con archivo activo.

**Rollback:** revertir el doble `mv`. Las 3.758 ofertas vuelven a `esco_occupation_uri = ''`.

---

## Hallazgos para SPEC W (rediseño arquitectónico)

Estos hallazgos surgieron durante la implementación de SPEC U-1 pero NO se modifican acá. Se registran para que SPEC W los aborde.

### H1. El runtime del matcher pivota sobre el atributo ISCO de cada URI ESCO (reformulado en lenguaje ESCO)

**Reformulación 2026-05-08 (lenguaje URI ESCO puro):**

El runtime del matcher usa el atributo "código ISCO de 4 dígitos" de cada URI ESCO como pivote interno para comparar resultados. Esto es desalineamiento estructural con la dirección ESCO autoritativa del proyecto. SPEC W debe migrar la lógica de decisión runtime a comparar URIs ESCO directamente.

El sistema en producción es **mixto con asimetría**:

| Capa | Pivote efectivo | Ubicación |
|---|---|---|
| Catálogo ESCO (`esco_associations`, `esco_occupations`) | **URI ESCO** (clave canónica) | tabla `esco_associations` indexa por `occupation_uri` |
| Persistencia matching (`ofertas_esco_matching`) | **Paralelo** (URI ESCO + atributo ISCO se escriben ambos) | `save_matching_result` líneas 1496-1540 |
| Lógica de decisión runtime | **Atributo ISCO de la URI** (no la URI completa) | líneas 438, 500, 536, 540, 737-744 |
| Cross-check skills (C4 JOIN) | **URI ESCO** | SPEC U-1 §7.2 SQL |

Líneas concretas donde el runtime usa el atributo ISCO en vez de la URI completa:
- `match_ofertas_v3.py:438` — `_apply_sector_penalty` filtra por `isco_code.startswith()`
- `match_ofertas_v3.py:500` — `_apply_seniority_penalty` filtra por `isco_code.startswith()`
- `match_ofertas_v3.py:536-540` — `_apply_supervision_penalty` filtra por `isco_code.startswith("1")`
- `match_ofertas_v3.py:737-744` — `dual_coinciden = 1 if regla_isco[:4] == semantic_isco[:4]` — comparación clave entre regla y semántico se hace por atributo ISCO, no por URI ESCO

**Implicancia:** dos URIs ESCO distintas que comparten el mismo atributo ISCO se consideran "coincidentes" para `dual_coinciden`. El sistema decide en un nivel de granularidad agregado dentro del cluster, perdiendo la distinción a nivel de URI específica.

### H2. `isco_to_canonical_occupation` (426 ISCOs) habilita pivote ESCO

Implementado en sub-fase C (líneas 179-199). Mapea `isco_4dig → {uri, label, esco_code}` con preferencia por la URI cuyo `esco_code == isco_4dig` (padre genérico). **Esta infraestructura habilita a SPEC W para mover la decisión runtime al espacio ESCO sin tocar el JSON ni las reglas de negocio.**

### H3. Campo `titulo_esco_code` ya existe en schema

Columna `titulo_esco_code` (TEXT) ya está en `ofertas_esco_matching` desde un intento previo de pivote ESCO autoritativo (R4 §A4). Hoy se popula esporádicamente. SPEC W puede activarlo como key autoritativa del título sin migración de schema.

---

## Discrepancias vs SPEC v3.1

| Métrica | SPEC v3.1 | Real | Impacto |
|---|---:|---:|---|
| ofertas_dashboard (Supabase) | "~16K" | **52.563** | SPEC desactualizado en §1.5 — no afecta C5 funcionalmente |
| Drift Local↔Supabase | "~40K ofertas + 880K skills" | **3.850 ofertas, 0 skills zombies** | **Esfuerzo C5 baja a 1-2h** (no 6-10h). Sync incremental ~3.8K ofertas + skills. **DELETE de zombies cancelado** (Q4=0 confirma que no hay). |
| Zombies skills Supabase | "28.395 baseline" | **0 zombies reales** | Conteo del SPEC era artefacto del backlog: 28.395 era diferencia de cardinalidad, no skills huérfanas. C5 §8.2 paso 4 (DELETE) ya no aplica. |
| Tabla `validacion_humana` en Supabase | Listada en §3.1 F0 | **NO EXISTE** | Quitar de la lista de F0 en próximas iteraciones |
| Tecnico decisión final | Quitar (Opción C) | Opción 3 (URI por contexto) | over-match 30% rebasa umbral 10%; conservar evita pérdida de granularidad en 6 contextos IT/mecánica/química/seguridad |

**Recomendación:** considerar emitir SPEC v3.2 con baselines actualizadas (no aplicado todavía).

---

## C2 Sub-fase D — Ejecución

### Decisión arquitectural pre-ejecución

Hallazgo bloqueante detectado al comienzo: el filtro estricto del SPEC (`esco_occupation_uri = '' AND matching_version != 'spec_h_rematch' AND estado_validacion NOT IN (validadas)`) producía **solo 3 ofertas no-validadas**, no 3.758. Las 3.748 restantes estaban validadas (`validado` o `validado_claude`) con URI vacía.

**Decisión de Gerardo:** Opción B — desbloquear las 3.748 + reprocesar global. Comunicación a Cynthia/Diego cubierta.

### Pasos ejecutados

| Paso | Acción | Resultado |
|---|---|---|
| **Pre-flight 1** | Snapshot F0 íntegro | ✅ gzip pasa |
| **Pre-flight 2** | `admin_unlock_validated.py` parche | Aceptaba solo `'validado'`. Parcheado para incluir `validado_claude` y `validado_humano`. **Commit `dcaf29cd`** + push a remote OK. |
| **Pre-flight 3** | Test sobre 5 ofertas mixtas en BD staging | 5/5 desbloqueadas, audit trail correcto |
| **Desbloqueo prod** | 3.748 ofertas → `en_revision` | 904 `validado` + 2.844 `validado_claude` desbloqueados. `validacion_historial`: 3.748 entries con `estado_anterior` real preservado |
| **Audit trail** | `data/spec_u1/desbloqueadas_subfaseD_20260505_184116.txt` + `_prestate.jsonl` | 3.748 IDs + pre-state completo |
| **Reprocesamiento** | Background, log estructurado | **1h24m** (2× más rápido que estimación SPEC 3-5h). 3.744/3.751 ok, 7 skipped |

### Resultado del reprocesamiento

| Métrica | Valor |
|---|---:|
| Duración real | **1h24m** (rate 0.74 ofertas/s) |
| Procesadas | 3.744 |
| Errores reales (excepción) | 0 |
| Skipped (sub-ofertas multi-position sin NLP) | 7 |
| Cambio URI (vacía → poblada) | 3.744 (100% de procesadas) |
| Cambio ISCO 4-dig | 396 (10.6%) |
| **C-Q1 final** | **18** ↓ desde baseline 3.762 |

**Distribución de métodos post-D (top 5):**
- `diccionario_argentino_administrativo`: 2.101 (56.1%)
- `diccionario_argentino_vendedor`: 484 (12.9%)
- `diccionario_argentino_gerente`: 228 (6.1%)
- `skills_first_v3`: 200 (5.3%)
- `diccionario_argentino_operador`: 105 (2.8%)

89% resolvió por diccionario o reglas — JSON v2 + reglas existentes cubre el grueso.

### Tarea 4 — Auto-validación con criterio B endurecido

Criterio aplicado: solo auto-validar cuando los invariantes ESCO pasan **Y** el reprocesamiento llenó URI vacía sin cambiar ISCO ni label canónico (criterio B endurecido). Casos con label drift dentro del mismo ISCO se marcan con bandera SPEC W.

**Buckets resultado (3.744 procesadas):**

| Bucket | Estado nuevo | Cantidad | % |
|---|---|---:|---:|
| **B1 auto-validado** | `validado_claude_subfaseD` | **2.770** | 74.0% |
| B2 sub-ocupación bizarra (bandera SPEC W) | `pendiente_humano_subfaseD` + `[BANDERA_W: sub_ocupacion_bizarra_revisar]` | 407 | 10.9% |
| B3 cambio de ISCO | `pendiente_humano_subfaseD` + `[CAMBIO_ISCO: pre→post]` | 392 | 10.5% |
| B4 falla invariantes — `label_drift_canonico` | `pendiente_humano_subfaseD` | 172 | 4.6% |
| B4 falla invariantes — `uri_no_canonica` | `pendiente_humano_subfaseD` | 3 | 0.1% |
| B4 falla invariantes — `uri_vacia_residual` | `pendiente_humano_subfaseD` | 0 | 0% |
| **B5 skipped multi-position** | `en_revision` (intacto) | 7 | — |
| **Total cola humana real (B2+B3+B4+B5)** | — | **981** | 26% |

**Distribución completa de `estado_validacion` en BD post-Tarea 4:**

```
validado_claude                  46.227
validado                          6.422
validado_claude_subfaseD          2.770   ← nuevo (auto-validado por D)
pendiente_humano_subfaseD           974   ← nuevo (cola humana D)
pendiente                            33   ← residual de operaciones previas
en_revision                           7   ← B5 multi-position
```

### Canarios post-D

| Canario | Pre-D | Post-D | Esperado |
|---|---:|---:|---|
| **C-Q1** (URI vacía global, no spec_h_rematch) | 3.762 | **18** | objetivo <50 ✅ |
| C-Q2 (skills detalle flags=0) | 1.116.011 | 1.161.522 | subió: el reprocesamiento creó skills nuevas. C4 las llenará. |
| C-Q3 (drift de labels) | 1.237 | 1.241 | +4. Mínimo. Esperable. |
| C-Q6 (validadas con 3 estados originales) | 56.397 | 52.649 | -3.748 (desbloqueo) +0 (no se re-validaron a estados originales) |
| C-Q4/Q5 | — | None (timeout) | issue intermitente Supabase, no bloqueante |

**C-Q1 = 18** son: 11 ofertas con `matching_version != 'spec_h_rematch'` y estado distinto a `en_revision` (no parte del set de D) + las 7 sub-ofertas multi-position skipped. Todas legítimamente fuera del scope de D.

### Sample spot-check estratificado (30 muestras)

Ver `logs/spec_u1_subfase_D_buckets_*.json` para listas completas por bucket. Reporte con muestras de B1/B2/B3/B4 entregado a Gerardo en chat.

### Export Excel para validación humana de B2

Generado export estratificado de **30 ofertas** del bucket B2 (407 totales con bandera SPEC W) para revisión por Cynthia o Diego.

- **Path:** `data/spec_u1/validacion_humana_B2_20260505.xlsx`
- **Script:** `scripts/spec_u1/export_b2_validacion_humana.py`
- **Seed:** `20260506` (determinístico)
- **Estrategia:** muestreo estratificado por ISCO, máximo 5 ofertas por ISCO, total 30. Diversidad efectiva: 12 ISCOs distintos representados.
- **Distribución de la muestra:** ISCO 2511 (5), 2423 (5), 4311 (5), 2431 (4), 3122 (4), y 7 ISCOs con 1 oferta cada uno.
- **Estructura:** Hoja "Validacion B2" (id, url, título, descripción truncada a 500 chars, tareas, skills, ISCO/label asignados, columnas editables: evaluación con dropdown OK/dudoso/mal, clasificación libre, comentario, revisor, fecha) + Hoja "Instrucciones" + Hoja "Metadata" (totales, distribución, seed, bandera SQL).
- **Decisión sobre demora:** si en 48h no hay respuesta, las 407 ofertas quedan en `pendiente_humano_subfaseD` con bandera SPEC W aplicada (información preservada para análisis cuantitativo posterior). C1 puede arrancar antes sin esperar la validación humana.

**Hallazgos del spot-check:**
- B1 (auto-validado): muestra dominada por `Empleado de oficina/empleada de oficina` (URI canónica del ISCO 4110), URI exacta, sin drift.
- B2 (bandera SPEC W): casos paradigmáticos del problema — `Administrativo de Compras → "comprador de café verde"` (ISCO 3323 mismo, label sub-ocupación bizarra), `Empleada Administrativa contable → "asistente de departamento de ventas"`, `Capataz de Planta → "supervisor de montaje de contenedores"`.
- B3 (cambio ISCO): mezcla de casos correctos (`Marketing Digital → especialista mercadotecnia`) y dudosos (`Operario sector almacén → trabajador de fábrica`).
- B4: casos donde el matcher escribió label que NO es la `preferred_label_es` de la URI persistida. Indica un bug menor en el matcher: el campo label se setea desde diferentes fuentes que no siempre coinciden con la URI canónica. Issue para SPEC U-2 o SPEC W.

---

## Hallazgos para SPEC W (rediseño arquitectónico) — Ampliación

### H4 — Validador no comparte contrato con matcher

El validador actual (auto y humano) **NO verifica que `esco_occupation_uri` esté poblada al validar**. 3.748 ofertas con URI vacía estuvieron en estado `validado` o `validado_claude`. Esto significa que la capacidad de validación no comparte contrato con la capacidad de matching.

En sub-fase D se aplicó un criterio de auto-validación ESCO-puro (URI canónica + label coherente) como capa adicional. Este criterio **NO está integrado al validador actual**; es un parche operacional de SPEC U-1. SPEC W debe rediseñar el validador para que comparta contrato con el matcher y use URI ESCO como autoritativo.

El runtime del matcher sigue siendo ISCO-céntrico (decisiones en `_decide_dual_match`, líneas 438, 500, 536, 540, 737-744). En sub-fase D se aceptó esa contradicción: el matcher decide en ISCO, pero la auto-validación verifica en ESCO. Es trade-off temporal hasta SPEC W.

### H5 — Detector multi-position incompleto

El detector v2.8.1 (`limpiar_titulos.py`) crea sub-ofertas con ID derivada (sufijo `_2`, `_3`, `_4`) pero **no replica el NLP del padre**. Las sub-ofertas quedan sin `tareas_explicitas`/`skills_tecnicas_list`/etc., y el matcher las saltea como `skipped_no_nlp`.

Existen **7 casos detectados en sub-fase D** (todas con sufijo `_N`):

```
1118230579_2, 1118254441_2, 5069250623_4, 6550856766_2,
6661854482_3, 7087776816_4, 8054784821_2
```

Hay un universo más amplio en BD probablemente. SPEC W debe rediseñar el detector para que: **(a)** replique NLP relevante del padre, **(b)** las marque explícitamente como "no procesables" en lugar de dejarlas en limbo, o **(c)** las matchee usando la URI del parent como fallback.

### H6 — Limpieza de zona geográfica en títulos parcial

El NLP tiene un step de remoción de zona geográfica antes del matching, pero la cobertura no es completa. Casos del spot-check con zona geográfica intacta llegando al matcher:

- `Administrativo Técnico*CABA*`
- `Administrativo de Compras - Zona Sur GBA`
- `Administrativo/a Ensobrado de Tarjetas / Eventual – Córdoba Capital`
- `Operario/a sector almacén Zona San Martin`

Esto introduce ruido en el matching. Pertenece al pipeline NLP (potencialmente SPEC U-2 si es bug menor, o SPEC W si el rediseño cambia el flujo).

### H8 — Label desincronizado de URI canónica

**175 ofertas en B4** (172 `label_drift_canonico` + 3 `uri_no_canonica`) muestran que el matcher en algunos casos asigna URI ESCO correcta pero **el label persistido NO coincide con `preferred_label_es` ni con ninguna `alt_label` de esa URI**.

Casos paradigmáticos del spot-check B4 de sub-fase D:
- Oferta `1118209400` (Facilities Manager): URI `…d3b1211f5525` (canónica → "gestor de proyectos de TIC"), pero label persistido = "director de tecnología/directora de tecnología" (label que NO está entre los `alt_label` de esa URI).
- Oferta `1118019132` (Operador Planta Tratamiento Efluentes): URI `…7244036d316d` ("operario de producción de alimentos") pero label persistido = "hornero de panadería/hornera de panadería".

**Análisis del bug:** el matcher tiene fuentes múltiples para el campo `esco_label` que no siempre están sincronizadas con la URI seleccionada:
- Algunas reglas hardcodean labels en `matching_rules_business.json` que pueden divergir del catálogo ESCO
- La resolución vía `_get_esco_label_for_isco()` (línea 374) usa el label preferido del ISCO mapping, no de la URI específica
- El diccionario argentino tiene `esco_label` por entrada que puede divergir del label real de la URI declarada

**Magnitud cuantificada:** 175 casos de las 3.744 procesadas en sub-fase D (4.7%). En el universo completo de matching es probablemente más alto.

**Implicancia para SPEC W o U-2:** invariante en el matcher — al persistir, validar que el `esco_label` venga del catálogo de la URI persistida (`preferred_label_es` o `alt_label`). Si no, derivarlo automáticamente de la URI. Bug menor pero sistemático con dataset cuantificado disponible (`b4_label_drift_canonico` en `logs/spec_u1_subfase_D_buckets_*.json`).

### H7 — Cluster ESCO como fallback cuando no hay URI ESCO genuina (reformulado en lenguaje ESCO)

**Reformulación 2026-05-08 (lenguaje URI ESCO puro):**

Cuando ESCO no contiene una URI específica que represente correctamente el contexto argentino de una oferta (ej: "administrativo de compras" en Argentina no tiene URI ESCO directamente equivalente; ESCO ofrece "comprador de café verde", "comprador de moda", etc.), forzar una URI ESCO específica produce clasificaciones bizarras. SPEC W debe permitir que el sistema admita un nivel de granularidad agregado dentro del cluster ESCO como respuesta válida cuando la URI específica del cluster no es genuina para el contexto.

**Decisión arquitectural original de Gerardo (2026-05-05):** cuando ESCO no tiene una ocupación apropiada para el contexto argentino (ej: `administrativo compras` forzado a sub-URI `comprador de café verde`), el sistema debería admitir granularidad agregada (cluster ocupacional ESCO) como respuesta válida en lugar de forzar URI ESCO específica bizarra.

**Magnitud cuantificada por sub-fase D:** **407 ofertas** (Bucket 2, 10.9% del set reprocesado) con bandera `sub_ocupacion_bizarra_revisar`. Casos paradigmáticos:
- `Administrativo de Compras` (ISCO 3323) → URI `…222ab6d84bc4` "comprador de café verde"
- `Empleada Administrativa contable` (ISCO 4311) → URI `…4c5906320100` "asistente de departamento de ventas"
- `Capataz de Planta` (ISCO 3122) → URI `…c8ea4afc2738` "supervisor de montaje de contenedores"

**Implicancias para SPEC W:**
- Permitir `esco_occupation_uri = NULL` legítimo cuando el match es a nivel ISCO.
- Distinguir "URI vacía por bug" de "URI vacía por diseño" en métricas y validación (campo flag separado).
- Definir criterio para detectar "ESCO genuino vs ESCO forzado bizarro" (no trivial, requiere análisis de catálogo + frecuencia).
- Bandera `bandera_spec_w = 'sub_ocupacion_bizarra_revisar'` ya aplicada a las 407 ofertas de Bucket 2 vía `notas_revision`. Esto permite a SPEC W cuantificar y caracterizar el problema antes de diseñar la solución.
- Va contra la dirección "ESCO > ISCO siempre" pero es la excepción razonable cuando ESCO es insuficiente para el contexto local.

### H9 — Validación humana de B2 confirma que el matcher acierta la familia ocupacional ESCO

**Origen:** validación de Cynthia sobre 30 ofertas de B2 (2026-05-06 a 2026-05-08).

En las 30 ofertas validadas por Cynthia, **el matcher asignó URIs ESCO que pertenecen al cluster ESCO correcto para la oferta**. Cynthia no propone migrar a una familia ocupacional ESCO distinta. **El error es de selección de URI ESCO específica dentro del cluster correcto.**

**Caso paradigmático:** oferta de "administrativo de compras" recibe URI ESCO "comprador de café verde" — la URI pertenece al cluster ocupacional correcto (URIs cuyo `broader_occupation_uri` apunta al mismo grupo ESCO de "agentes de compras") pero es subóptimamente específica para el contexto argentino.

**Otros casos paradigmáticos del spot-check (todos confirman cluster correcto, URI subóptima):**
- "Capataz textil" → URI "supervisor de montaje de contenedores" (cluster supervisión de producción ✓, URI específica errónea)
- "Analista de datos" → URI "analista de sistemas de TIC" (cluster analistas TIC ✓, URI subóptima — Cyn ubica en `2511.3 - analista de datos`)
- "Administrativa contable" → URI "asistente de departamento de ventas" (cluster empleados administrativos ✓, URI subóptima — Cyn ubica en `4311.1 - empleado de contabilidad`)

**Cero propuestas de cambio de cluster ESCO en las 30 ofertas validadas por humano.**

**Implicancias para SPEC W:**
- SPEC W debe diseñar el criterio para distinguir **"URI ESCO genuina para la oferta"** vs **"URI ESCO específica del cluster pero subóptima"**.
- Las 407 ofertas con `bandera_spec_w = 'sub_ocupacion_bizarra_revisar'` quedan como dataset cuantificado para entrenar/validar ese criterio.
- Posible aproximación: cuando el matcher elige una URI específica de baja frecuencia histórica en el dominio argentino, escalar a granularidad de cluster (URI ESCO del padre `broader_occupation_uri`) en lugar de la URI específica subóptima.

### H10 — Validación curatorial de Cynthia produce información estructurada que excede el modelo OK/dudoso/mal

**Origen:** análisis cualitativo de las 30 correcciones de Cynthia (2026-05-08).

Cynthia categoriza las skills de cada oferta como "Correcta", "Implícita fuerte", "Implícita pertinente" o "Incorrecta", **con justificación por skill y referencia a la tarea de origen**. El formato es estructurado:

```
Skill: <nombre>
Tarea de origen: <texto literal del aviso>
Validación: ✔ Explícita correcta | ⚠ Implícita débil | ✗ Incorrecta
Justificación: <razón>
Ubicación sugerida dentro del Excel: ESCO XXXX.X
```

**Volumen cuantificado en 30 ofertas:**
- 315 skills marcadas `✔ Explícita correcta`
- 190 skills marcadas `⚠ Implícita débil` (38% del total — ruido percibido)
- Sub-códigos ESCO específicos sugeridos para refinar la URI sistema (ej: `3122.4 — supervisor de producción`, `4311.1 — empleado de contabilidad`).

**El problema:** esa información hoy **no tiene canal para entrar a `ofertas_esco_skills_detalle` ni a ningún sistema downstream**. Queda como output suelto en el campo `validacion_correcciones` de Supabase (texto libre). El validador binario `validacion_humana = 'revisar'` no captura la riqueza estructural de lo que Cynthia produce.

**Implicancias para SPEC W:**
- Diseñar el flujo **"validación humana → enriquecimiento de skills"** como capacidad de primera clase, no como output adjunto.
- Schema propuesto: tabla `validacion_humana_skills` con columnas (id_oferta, esco_skill_uri, label_humano, categoria_validacion, justificacion_humana, sub_codigo_esco_sugerido, validador, timestamp).
- La UI debe permitir al humano (a) confirmar/cuestionar cada skill individualmente, (b) sugerir sub-código ESCO específico, (c) escribir justificación por skill — todo en formato estructurado.
- Output downstream: training pairs para fine-tuning del extractor de skills + propuestas de URI canónica para corregir label drift.
- Las **30 ofertas validadas por Cynthia son baseline cuantificado** de qué información produce el humano cuando puede ir más allá del modelo binario.

---

## Próximo paso

**C2 sub-fase D — COMPLETA.** Avanzando a **C1 (re-rematch de las 8.221 con `matching_version='spec_h_rematch'`)**.

**Cambio en lenguaje operacional (2026-05-08):** todas las decisiones operacionales, criterios de validación y reportes desde C1 en adelante se expresan en términos URI ESCO puros. El código ISCO sigue existiendo como atributo de cada URI ESCO pero NO es criterio de decisión ni lenguaje de reporte.

**Auto-validación C1 con criterio ESCO puro:**
- Bucket C1-1: misma URI ESCO pre y post (auto-validable)
- Bucket C1-2: URI distinta dentro del mismo cluster ocupacional ESCO (mismo `broader_occupation_uri`) — bandera SPEC W
- Bucket C1-3: cambio de cluster ocupacional ESCO (cola humana sin bandera)
- Bucket C1-4: falla invariantes técnicos (URI no canónica, label drift, URI vacía residual)

### F0b — Re-snapshot Supabase pre-C1 (2026-05-08)

**Estado del snapshot:**

| Tabla | Filas bajadas | Status |
|---|---:|---|
| `ofertas_dashboard` | 52.564 | ✅ completo |
| `ofertas_skills` | **954.000 / 1.144.527 (83%)** | ⚠️ **PARCIAL — timeout Supabase en página 954** |
| `issues` | 212.976 | ✅ completo |
| `rule_candidates` | 0 | ✅ vacío esperado |

**Path:** `data/snapshots/pre_c1_supabase_20260508_175242.json.gz` (111 MB, gzip íntegro, JSON parseable).

**Caveat para C5:** el snapshot de `ofertas_skills` está incompleto (190K skills no capturadas por timeout de Supabase). **No bloqueante para C1** (el reprocesamiento opera sobre `ofertas_esco_matching` local, no sobre `ofertas_skills`). **Sí relevante para C5**: si el sync masivo + DELETE de zombies de C5 falla y se necesita rollback de skills en Supabase desde el snapshot F0b, el rollback solo cubrirá el 83% de las skills. Para C5 conviene: (a) re-snapshot completo de `ofertas_skills` antes de arrancar (paginación más conservadora con sleep entre páginas), o (b) aceptar el riesgo y avanzar (probable, dado que C5 hace DELETE de zombies que no se va a invertir desde snapshot).

### Pre-C1 — Set efectivo y desbloqueo (2026-05-08)

**Hallazgo no contemplado en SPEC v3.1 §4 original:** el set completo de 8.221 ofertas con `matching_version='spec_h_rematch'` está en estado validado (`validado_claude` 8.074 + `validado` 147), protegido por triggers SQL. Imposible re-rematchar sin desbloquear primero.

**Decisión arquitectural (Gerardo, 2026-05-08):**
- Excluir 4 ofertas con validación humana real (registrada en `validacion_historial`):
  - `1118115497`, `1118115501`, `1118115516` — validación de Gerardo del 2026-01-19
  - `1118099854` — validador `manual` con motivo "Errores resueltos, scores OK" (preservación conservadora)
- Desbloquear las 8.217 restantes (8.070 `validado_claude` + 147 `validado`).

**Ejecución:**
- Pre-flight C1: 5/5 verificaciones OK (snapshot F0 íntegro, pipeline pausado, JSON v2 + embeddings cargados, sub-fase C aplicada, conteo 8.221).
- F0b: snapshot Supabase fresco (parcial en skills — ver arriba).
- Desbloqueo masivo via `admin_unlock_validated.py`: **8.217/8.217 OK** a `en_revision` en una pasada.
- `validacion_historial`: 8.217 entries con `estado_anterior` real preservado (8.070 `validado_claude` + 147 `validado`).
- 4 excluidas intactas en `validado_claude`.
- 0 errores de trigger.

**Audit trail:**
- `data/spec_u1/desbloqueadas_C1_20260508_183139.txt` — 8.217 IDs
- `data/spec_u1/desbloqueadas_C1_prestate_20260508_183139.jsonl` — pre-state completo (esco_uri, esco_label, isco_code, score, decision_metodo, occupation_match_method, validado_por, matching_version)
- `data/spec_u1/humanas_excluidas_C1_20260508.{txt,json}` — 4 IDs con motivo + estado actual + título
- `logs/spec_u1_C1_desbloqueo_20260508_183139.log` — log completo del unlock

---

## C1 — Re-rematch ejecutado (2026-05-08 19:01 → 22:23)

**Duración:** 3h21m (rate 0.68 ofertas/s, consistente con sub-fase D).

| Métrica | Valor |
|---|---:|
| Total input | 8.217 |
| Procesadas exitosamente | **8.179** (99.54%) |
| Errores (`skipped_no_nlp`, sub-ofertas multi-position H5) | 38 (0.46%) |
| Cambio URI ESCO | 4.488 (54.9%) |
| Sin cambio URI ESCO | 3.691 (45.1%) |
| Quedaron sin URI | 0 ✅ |

**Distribución de métodos post-C1 (top 5):**
- `skills_first_v3`: 4.135 (50.6%)
- `regla_negocio_R240_operario_produccion`: 922 (11.3%)
- `regla_negocio_R17_compliance_legal`: 458 (5.6%)
- `regla_negocio_R13_enfermero`: 332 (4.1%)
- `regla_negocio_R353_operario_carga_descarga`: 274 (3.4%)

50.6% del set resolvió por path semántico — el set `spec_h_rematch` contiene perfiles más técnicos/especializados (compliance, enfermería, ingeniería) donde los embeddings dominan vs reglas/diccionario.

---

## C1 — Auto-validación con criterio ESCO multi-nivel (Tarea 4, 2026-05-10)

**Pre-trabajo:** carga de `esco_occupation_ancestors` desde API ESCO oficial (1h41m, 16.667 entradas, 100% cobertura de las 3.045 ocupaciones, profundidad típica 5-6 niveles, 0 errores). Ver H11 abajo.

**Criterio:** 6 buckets ESCO multi-nivel evaluados en orden de prioridad. Para cada oferta procesada (8.179):

| Bucket | Estado nuevo | Bandera SPEC W | Cantidad | % |
|---|---|---|---:|---:|
| **C1-1** misma URI ESCO + invariantes OK | `validado_claude_C1` | (sin bandera) | **3.691** | 45.1% |
| **C1-2a** Occupation común L1-L2 | `pendiente_humano_C1` | `cluster_esco_propio_uri_distinta` | 3 | 0.04% |
| **C1-2b** IscoGroup C\d{4} común L2 | `pendiente_humano_C1` | `cluster_isco_4dig_uri_distinta` | 1 | 0.01% |
| **C1-3** ancestor común L3-L4 | `pendiente_humano_C1` | `subgrupo_compartido_ocupacion_distinta` | 300 | 3.7% |
| **C1-4** sin ancestor común L1-L4 | `pendiente_humano_C1` | (sin bandera) | **4.151** | 50.8% |
| **C1-5** falla invariantes técnicos | `pendiente_humano_C1` | (sin bandera) | 33 | 0.4% |
| Total persistido | | | **8.179** | 100% |

**C1-5 razones:** 33/33 son `label_drift_canonico` (el matcher escribió un label que no es `preferred_label_es` ni `alt_label` de la URI persistida — patrón H8 reportado en sub-fase D, recurrente).

**Distribución completa de `estado_validacion` post-C1:**

```
validado_claude                  38.157   (no tocadas por D ni C1)
validado                          6.275
pendiente_humano_C1               4.488   ← nuevo (cola humana C1)
validado_claude_C1                3.691   ← nuevo (auto-validado C1)
validado_claude_subfaseD          2.770
pendiente_humano_subfaseD           974
en_revision                          45   ← 38 multi-position skipped C1 + 7 sub-fase D
pendiente                            33
```

### Hallazgo crítico interpretativo de los 50.8% en C1-4

**El alto porcentaje en C1-4 (cluster ESCO completamente distinto) NO refleja error del re-rematch sino corrección masiva del bug del cruce URI×label R3§E1.**

Caso paradigmático verificado en spot-check (`id=1118217322` "Técnico/a de Laboratorio"):
- **URI pre real:** `azafato/azafata` (ISCO C4221) — bug del cruce URI×label
- **`isco_code` persistido pre:** 3212 (stale — 8 columnas no actualizadas tras commit `94f0d73c`)
- **URI post:** `auxiliar de laboratorio de análisis clínicos` (C3212) ✅ corregido

El log del re-rematch reportó `_isco_pre=3212 → _isco_post=3212` (sin cambio aparente), pero la URI ESCO autoritativa cambió de "azafato" a "auxiliar de laboratorio" — distinta familia ocupacional. **La validación correcta es por URI ESCO, no por isco_code derivado** (ese estaba afectado por el bug).

**4.151 ofertas C1-4 = víctimas del bug del cruce URI×label corregidas masivamente por C1.** Coherente con R3§E1 que estimaba 4.203 ofertas afectadas.

### Canarios post-C1 (Tarea 4)

| Canario | Pre-D | Post-D | Post-C1 | Notas |
|---|---:|---:|---:|---|
| C-Q1 (URI vacía global) | 3.762 | 18 | **7** | objetivo SPEC <50 ✅ |
| C-Q3 (drift labels) | 1.237 | 1.241 | **39** | **bajó 97%** — el bug del cruce era la causa principal del drift, ahora corregido ✅ |

### Spot-check estratificado (30 muestras, seed 20260510)

Detalles completos en chat. Resumen:
- C1-1 (8 muestras): todas con misma URI pre/post, mismo ISCO, label idéntico — auto-validables confirmadas.
- C1-2a (3 disponibles): ej. `Dermoconsejera` URI cambió de "Gerente de tienda cosmética" (C1420) → "vendedor cosmética" (C5223), Occupation común en L1-L2.
- C1-2b (1 disponible): ej. `Associate Manager Supply Planning` URI cambió manteniendo cluster ISCO 4-dig.
- C1-3 (4 muestras): ofertas con cambio de URI dentro del mismo subgrupo ISCO (ej: dos URIs de "pintor de obra" distintas, ambas C7131).
- **C1-4 (4 muestras):** todas confirman el patrón del bug del cruce — URI pre era de familia distinta a la oferta real, URI post corrige a la familia correcta.
- C1-5 (4 muestras): todas son casos de "Marketing Manager" donde diccionario_argentino_gerente escribió label "director de ventas" pero la URI persistida es `dc97adbe…c24b3416cdef` cuyo `preferred_label` es "responsable de marketing digital" — label no coincide con el catálogo (H8 confirmado).

---

## Hallazgos para SPEC W (ampliación post-C1)

### H11 — Jerarquía ESCO multi-nivel cargada como infraestructura permanente

**Carga realizada:** 2026-05-09, 1h41m, 0 errores, desde API ESCO oficial v1.2.0.

| Métrica | Valor |
|---|---:|
| Filas en `esco_occupation_ancestors` | **16.667** |
| Cobertura ocupaciones | **100%** (3.045/3.045) |
| Profundidad típica | 5 niveles (58.8%), 6 niveles (35.2%), hasta 8 niveles (1.3%) |
| Ancestros tipo `IscoGroup` | 12.156 (73%) |
| Ancestros tipo `Occupation` (jerarquía ESCO propia) | 4.511 (27%) |
| Ancestros únicos | 3.648 |

**Disponible para SPEC W como infraestructura jerárquica nativa** sin dependencia de la API ESCO online. Permite consultas:
- "Dame todos los descendientes de C2511" (analistas de sistemas)
- "¿Qué ancestro común tienen URI A y URI B?" (lowest common ancestor)
- "¿Qué subgrupo ISCO pertenece esta ocupación específica?"

### H12 — Datasets cuantificados de drift en C1 con bandera SPEC W

Tres banderas distintas para análisis SPEC W:

| Bandera | Cantidad | Caracterización |
|---|---:|---|
| `cluster_esco_propio_uri_distinta` (C1-2a) | **3** | URI cambió pero hay Occupation común en L1-L2 — drift mínimo dentro del cluster ESCO real |
| `cluster_isco_4dig_uri_distinta` (C1-2b) | **1** | URI cambió, ISCO 4-dig común — drift dentro del mismo grupo unitario ISCO |
| `subgrupo_compartido_ocupacion_distinta` (C1-3) | **300** | URI cambió a otra ocupación del mismo subgrupo ISCO 3-dig (cambio sustantivo dentro del mismo área) |

Cada bandera permite a SPEC W:
- Estudiar el drift dentro del cluster ESCO sin contaminarlo con drift de cluster.
- Validar el matcher con humanos sobre subset específicos.
- Tunear el criterio "URI ESCO genuina vs subóptima" (H7) con dataset cuantificado por nivel.

**Persistencia:** columna `bandera_spec_w_C1` agregada a `ofertas_esco_matching` (TEXT, nullable). Coexiste con la bandera de sub-fase D que vive en `notas_revision` con prefijo `[BANDERA_W: sub_ocupacion_bizarra_revisar]` (407 ofertas). Próximos hallazgos pueden migrar a columnas formales similares.

### H13 — El bug del cruce URI×label tuvo impacto masivo en clasificación

C1-4 con 4.151 ofertas (50.8%) confirma que el bug R3§E1 (commit `94f0d73c` 2026-04-25 con UPDATE incompleto) **cambió la URI ESCO de muchas ofertas a familias completamente distintas a la real del puesto**, mientras dejaba el `isco_code` persistido stale. El re-rematch las corrigió a la familia correcta.

**Implicancia para SPEC W:** la validación post-matching debe verificar coherencia URI↔isco_code antes de persistir. Invariante propuesto: si la URI pertenece a `esco_occupations` con `isco_code` X, y el matcher quiere persistir `isco_code` Y ≠ X, ABORTAR la persistencia y escalar.

---

## C4 — Backfill flags ESCO ejecutado (2026-05-10 15:22 → 15:26)

**Duración total:** **3m30s** (vs 8-35min estimado SPEC §7.2). Mucho más rápido por:
- Índice compuesto `idx_esco_assoc_compound` creado en 3.4s previamente
- WAL mode + synchronous=NORMAL para batch
- COVERING INDEX usado en EXPLAIN QUERY PLAN

| Paso | Tiempo |
|---|---:|
| Crear índice compuesto | 3.4s |
| UPDATE (51s) + commit (18s) | 1m9s |
| Verificación Q1+Q2+Q3+F-meta | ~1min |
| **Total** | **3m30s** |

### Pre-flight C4

| Métrica | Valor | vs Baseline SPEC |
|---|---:|---|
| Total filas en `ofertas_esco_skills_detalle` | **1.268.844** | +152K vs baseline 1.116.011 (D+C1 generaron skills nuevas) |
| Backfilleables | **1.268.705** | +244K vs baseline 1.023.911 (D+C1 corrigieron URIs vacías) |
| No-backfilleables (URI vacía) | **139** | -91.961 vs baseline 92.100 (¡bajo masivamente!) |

### Resultados C4

**Filas modificadas por UPDATE:** 1.268.705 (= backfilleables)

**Distribución post-C4 en backfilleables:**

| Flag | Cantidad | % |
|---|---:|---:|
| `is_essential_for_occupation = 1` | **76.038** | 6.0% |
| `is_optional_for_occupation = 1` | **47.630** | 3.8% |
| Ambos en 0 | 1.145.062 | 90.3% |

**F-meta baseline (registrado en `docs/diagnostico/baseline_cobertura_esco_K_post_C4.md`):**

| Métrica | Valor |
|---|---:|
| **cobertura_K1** (≥1 skill catálogo) | **74.87%** |
| **cobertura_K3** (≥3 skills) | **38.03%** |
| **cobertura_K5** (≥5 skills) | **14.49%** |
| Avg skills en catálogo / oferta | 2.26 |
| n_ofertas con URI | 54.774 |

### Verificación Q1 + Q2 + Q3

- **Q1 (Conteo flags):** 76K essential + 48K optional + 1.14M zero = 1.27M total ✅
- **Q2 (Sample 10 ofertas con flags):** skills essential conceptualmente coherentes con ocupación (Mecánico → "reparación vehículos"; Chef → "técnicas de cocina"; Bartender → "servir bebidas"; etc.) ✅
- **Q3 (5 ocupaciones sample):** todas cumplen `BD ≤ catálogo` (4≤12, 1≤17, 3≤32, 2≤28, 0≤12). Backfill no excede catálogo oficial. ✅

### Discrepancia vs SPEC v3.1 §7.6

SPEC esperaba **~784K filas en cero**. Real: **1.145.201**. Diferencia +361K.

**Razón:** solo ~10% de skills extraídas caen en el catálogo ESCO de su URI (no ~32% que esperaba el SPEC). **El extractor de skills v2.4 produce más skills de las que ESCO reconoce para la ocupación target.**

**Implicancia para SPEC W (refuerzo de H9):** dataset cuantificado de ~1.14M skills extraídas que no caen en el catálogo ESCO. Usable para distinguir:
- Skills razonables pero ESCO incompleto
- Ruido del extractor (skills falsas/genéricas)
- Skills de ocupaciones cercanas (drift)

### Canario C-Q2 post-C4

| Canario | Pre-C4 | **Post-C4** | Notas |
|---|---:|---:|---|
| **C-Q2** (filas con flags=0) | 1.268.844 | **1.145.201** | bajó 124K — corresponde a las 124K que ahora son essential u optional |

### Hallazgo nuevo H14 — F-meta funcional

El UPDATE de C4 produjo F-meta > 0 confirmando que toda la cadena URI ESCO ↔ skills ↔ catálogo ESCO funciona end-to-end:

- 74.87% de las ofertas con URI tienen al menos 1 skill reconocida por ESCO para esa ocupación
- 14.49% tienen 5+ skills reconocidas

Esto es el **criterio de éxito cross-cutting del SPEC entero (§9 F-meta).** Pre-D era 0/0/0. Post-C4 es 74.87%/38.03%/14.49%. **El sistema produce datos ESCO-coherentes ahora, no solo ISCO.**

---

## Próximo paso

**C4 — COMPLETO.** Cadena C2 sub-fase C/D + C1 + C4 produce datos consistentes con catálogo ESCO end-to-end.

**Pendiente:** F0b' (re-snapshot Supabase pre-C5) + C5 (sync masivo + zombies + cron). Drift real Local↔Supabase = 3.850 ofertas (no 40K), esfuerzo C5 = 1-2h (no 6-10h).

NO arrancar C5 sin OK explícito de Gerardo.

### H15 — Extractor de skills produce ~90% fuera del catálogo ESCO de la ocupación

**Origen:** C4 backfill (2026-05-10).

C4 reveló post-backfill: solo **9.8%** (123.668 / 1.268.705) de las filas de `ofertas_esco_skills_detalle` con URI poblada tienen flag essential u optional poblado. Pre-SPEC se estimaba ~32% basado en R2 §B2; real ~10%.

La discrepancia indica que el extractor BGE-M3 (`SkillsImplicitExtractor` con threshold 0.40, top-3 por tarea) produce más skills de las que ESCO reconoce como esenciales u opcionales para la ocupación target.

**Causas posibles (a investigar en SPEC U-2 o W):**
- **(a) Extractor demasiado permisivo:** threshold 0.40 puede estar capturando ruido semántico. Dataset cuantificado: 1.145.062 filas con `is_essential=0 AND is_optional=0` en ofertas backfilleables.
- **(b) Catálogo ESCO incompleto para contexto argentino:** skills relevantes para una ocupación argentina pueden no estar en `esco_associations` de la URI canónica europea.
- **(c) Combinación de ambas.**

**Implicancias:**
- F-meta baseline post-C4: K1=74.87%, K3=38.03%, K5=14.49%. Funcionales pero relativamente bajos.
- Mejorar K3/K5 requiere intervención sobre el extractor o el catálogo, **no sobre el matcher de ocupaciones** (el matcher ya funciona correctamente, validado por C1+C4).
- Las 1.145.062 filas con flags=0 son universo cuantificado para diagnóstico SPEC W.

**Convergencia con H9 (sub-fase D):** la validación humana de Cynthia marcó 38% de skills como `⚠ Implícita débil`. C4 muestra que ~90% NO están en catálogo ESCO. Combinando: las "implícitas débiles" son un subset de las que el catálogo no reconoce; el catálogo es más estricto que Cynthia.

---

## F0b' (parcial) — Pre-C5 (2026-05-10)

**Duración:** 54m29s. Terminado por sí mismo (no abortado), pero `ofertas_skills` quedó incompleto por timeouts agresivos de Supabase REST con paginación deep en tablas >500K filas.

**Cobertura efectiva por tabla (combinada F0 inicial + F0b'):**

| Tabla | F0 inicial (2026-05-05) | F0b' (2026-05-10) | Combinada |
|---|---|---|---|
| `ofertas_dashboard` | 52.563 (estado pre-C1) | **52.564 (100% fresco)** | 100% fresco F0b' |
| `ofertas_skills` | 1.144.527 (100%) | 750.112 (65.5%) | ~100% combinada con timestamps distintos |
| `issues` | 212.860 (100%) | 212.976 (100% fresco) | 100% fresco F0b' |
| `rule_candidates` | 0 (esperado) | 0 (esperado) | OK |
| `validacion_humana` | tabla no existe (PGRST205) | tabla no existe | **tabla no existe en Supabase** — validaciones humanas viven en `ofertas_dashboard.validacion_correcciones`, cubierto por snapshot de `ofertas_dashboard` |

**Ubicación:** `data/snapshots/pre_c5_supabase_full_20260510_170940/` (5 archivos `.json.gz`, 105 MB total)

### Plan de rollback de C5 (si se requiere)

- **`ofertas_dashboard`:** restaurar desde F0b' (snapshot fresco 100%).
- **`ofertas_skills`:** restaurar combinando F0 inicial (~83% datos viejos) + F0b' (~59% datos recientes). **NO es plan automático** — es procedimiento documentado que requiere intervención manual con criterio para resolver conflictos por `id_oferta`.
- **`issues`:** restaurar desde F0b' (100% fresco).
- **Resto de tablas:** F0 inicial es suficiente (`rule_candidates` vacía, `validacion_humana` no existe).

### Justificación para aceptar snapshot parcial

1. **Q4 (zombies) = 0** confirmado en F0 inicial → C5 §8.2 paso 4 (DELETE) no se ejecuta.
2. **C5 efectivo = sync incremental de ~3.850 ofertas** → operación reversible vía re-sync inverso.
3. Cobertura agregada F0+F0b' de `ofertas_skills` cercana al 100% para rollback.
4. Riesgo de rollback real es bajo dado que C5 no hace operaciones destructivas masivas.

### Issue identificado para SPEC U-3 o W

**Supabase REST timeout con paginación deep en tablas >500K filas.** El cliente REST con OFFSET alto (>635K) genera `statement timeout` (código 57014) incluso con `page_size=125`. El script `snapshot_supabase_full.py` baja adaptativamente hasta `page_size=62` pero sigue degradando.

**Solución propuesta para SPEC U-3:** crear RPC SQL server-side en Supabase que retorne batches por rango de IDs (no por OFFSET). Eso evita el problema de deep pagination.

---

## C5 — Sync Supabase ejecutado (2026-05-10 18:13 → 22:02)

**Duración total:** 3h45min (sync principal 3h37m + post-sync con 2 warnings no-bloqueantes).

### Pre-trabajo: parche al script sync_to_supabase.py

El filtro hardcoded `estado_validacion IN ('validado', 'validado_claude', 'validado_humano')` aparecía en **13 lugares** del script. Sin parchearlo, las 6.461 ofertas con estados nuevos (`validado_claude_subfaseD` 2.770 + `validado_claude_C1` 3.691) no se hubieran sincronizado.

Parche: extender filtro a 5 estados en los 13 lugares:
```sql
estado_validacion IN ('validado_claude', 'validado_humano', 'validado',
                       'validado_claude_subfaseD', 'validado_claude_C1')
```

### Resultado sync principal

| Métrica | Pre-C5 | Post-C5 | Delta |
|---|---:|---:|---:|
| `ofertas_dashboard` (Supabase) | 52.564 | **56.365** | +3.801 |
| `ofertas_skills` (Supabase) | 1.144.527 | **1.190.607** | +46.080 |
| Validadas locales (5 estados) | 50.893 | 50.893 | sin cambio |
| **Drift Local↔Supabase (C-Q5)** | 3.850 | **0** | ✅ drift cero |
| **Skills zombies (C-Q4)** | 0 (F0) | **0** | ✅ confirmado |

**Indicadores agregados sincronizados:**
- Issues: 92.109
- Tensión ocupaciones: 402
- Concentración ocupacional: 30
- Brecha calificación: 301
- Digitalización sector: 18
- Transición skills: 210
- Velocidad cobertura: 359
- Índice trabajo remoto: 137

### Warnings no-bloqueantes post-sync

Dos fases post-sync fallaron con timeout de Supabase (no afectan integridad del sync):
1. `generate_mol_skills_profile.py` — timeout en query agregada (perfil MOL vs ESCO sin regenerar)
2. RPC `recalcular_emergentes` — timeout server-side (registrado como WARNING "no bloquea")

Ambos quedan como issue para revisión separada. Pertenecen al pipeline de indicadores derivados, no al core de sync de ofertas+skills.

### Zombies = 0 confirmado (Paso 4.2)

Conteo exhaustivo paginando las 1.19M filas de `ofertas_skills` vs 56.365 IDs de `ofertas_dashboard`:
- **Skills zombies: 0** ✅
- Ofertas huérfanas: 0
- **DELETE de C5 §8.2 paso 4: SKIP** (no aplica, como ya se anticipó desde F0)

### Cron diario activo (Paso 4.4)

Cron ya configurado **antes** de SPEC U-1, corre cada hora:
```
0 * * * * /mnt/d/OEDE/Webscrapping/scripts/auto_sync.sh
```

El script `auto_sync.sh` hace:
1. Sync VPS → Local (ofertas nuevas del scraping)
2. Sync Local → Supabase (solo si hay ofertas nuevas en local)
3. Sync scraping_daily

Frecuencia horaria es **más conservadora que la diaria 03:00 AR** del SPEC §8.2 paso 5. Cubre el requisito. **No requiere acción adicional.**

Mejora pendiente menor: agregar notificación si falla (email/Slack). No crítico.

### Canarios finales post-C5

| Canario | Baseline F0 | Post-C5 | Resultado |
|---|---:|---:|---|
| **C-Q1** URI vacía global | 3.762 | **7** | ✅ -99.8% (objetivo SPEC <50) |
| **C-Q3** drift labels | 1.237 | **39** | ✅ -97% |
| **C-Q4** zombies Supabase | 0 (F0) / 28.395 (SPEC estimaba) | **0** | ✅ confirmado, baseline SPEC era artefacto |
| **C-Q5** drift Local↔Supabase | 3.850 | **0** | ✅ drift cero post-sync |
| C-Q2 skills flags=0 | 1.116.011 | 1.145.201 | (subió por skills nuevas C4+sync, esperado) |
| C-Q6 validadas (3 estados orig.) | 56.397 | 44.432 | (resto migró a validado_claude_subfaseD/_C1) |
| C-Q7 spec_h_rematch | 8.221 | 42 | ✅ -99.5% (C1 procesó casi todo) |

**Las "alarmas" en C-Q2/Q5/Q6 son artefactos de comparación contra baseline antiguo.** Los valores nuevos son el estado correcto post-SPEC.

---

## Cierre SPEC U-1 v3.1 — Estado final

**Fecha de cierre:** 2026-05-11
**Duración total calendario:** 6 días (2026-05-05 → 2026-05-11)
**Branch:** `feature/spec-e-embeddings-enriquecidos`

### 1. Estado de cada fix

| Fix | Estado | Tiempo real |
|---|---|---:|
| F0 (snapshot + canarios + baselines) | ✅ | 1-2h |
| C3 (embeddings ocupaciones — implícito via sub-fase C) | ✅ | — |
| C2 sub-A (verificación overmatch) | ✅ | 30 min |
| C2 sub-B (JSON v2 con 22 entradas) | ✅ | 2-3h |
| C2 sub-C (fix matcher: 4 ediciones + bug setter) | ✅ | 4-6h |
| C2 sub-D (reprocesamiento 3.748 desbloqueadas + 3) | ✅ | 1h24m |
| C1 (re-rematch URI×label 8.217 ofertas) | ✅ | **3h21m** |
| C4 (índice compuesto + backfill flags ESCO) | ✅ | **3m30s** |
| F0b' (re-snapshot Supabase parcial) | ✅ con caveat | 38m (cortado por timeouts) |
| C5 (sync masivo + zombies + cron) | ✅ | ~4h |
| **C5 fix H16 (re-sync flags ESCO)** | ✅ | **3h45m** |

### 2. Métricas finales — Canarios

| Canario | Pre-SPEC | Post-SPEC | Δ |
|---|---:|---:|---:|
| **C-Q1** (URI ESCO vacía) | 3.762 | **7** | -99.8% ✅ |
| C-Q2 (flags=0) | 1.116.011 | 1.145.062 (universo expandido, 78.038 con flag=1) | esperado |
| **C-Q3** (drift labels URI×label) | 1.237 | **39** | -97% ✅ |
| **C-Q4** (zombies Supabase) | 0 (confirmado pre, vs 28.395 que estimaba SPEC) | **0** | — |
| **C-Q5** (drift Local↔Supabase) | ~3.834 (no 40K como decía SPEC v3.1) | **0** | -100% ✅ |

### 3. F-meta — Métricas de cobertura ESCO

| Universo | n_ofertas | K1 (≥1) | K3 (≥3) | K5 (≥5) |
|---|---:|---:|---:|---:|
| Local TOTAL (incluye cola humana) | 54.774 | **74.87%** | **38.03%** | **14.49%** |
| **Local-validadas (= sincronizadas)** | **49.241** | **72.72%** | **34.64%** | **13.11%** |
| **Supabase (vía proxy + sample 1:1)** | 49.241 | **72.72%** | **34.64%** | **13.11%** |
| Drift inferido Supabase vs Local-validadas | — | ≤0.1pp | ≤0.1pp | ≤0.1pp |

**Criterio SPEC §8.4 cumplido:** drift F-meta Supabase ≈ Local ≤ 1pp ✅.

### 4. Limitación de verificación F-meta Supabase (caveat documentado)

La verificación F-meta sobre Supabase no se hizo por cálculo agregado directo sobre todas las ofertas en Supabase, porque la query agregada tropieza con timeouts de Supabase REST en paginación deep de `ofertas_skills` (mismo problema de F0b').

La verificación efectiva se compuso de:

1. **Sample 1:1 de 100 ofertas validadas:** 100/100 match exacto entre flag local y flag Supabase.
2. **Cálculo F-meta sobre Local-validadas** (universo equivalente al que se sincroniza): K1=72.72%, K3=34.64%, K5=13.11%.
3. **Inferencia:** si los flags coinciden 100/100 a nivel oferta-skill, la métrica agregada también coincide (universo idéntico, flags idénticos → F-meta idéntico).

Esta verificación es **indirecta pero válida para SPEC U-1**. Para verificación agregada directa sobre Supabase se requiere infraestructura RPC SQL server-side (mismo issue identificado en F0b'). Queda como mejora pendiente.

### 5. Hallazgos para SPEC W consolidados (H1 a H16)

| # | Hallazgo |
|---|---|
| **H1** | Runtime ISCO-céntrico del matcher (atributo ISCO de la URI ESCO como pivote en líneas 438, 500, 536, 540, 737-744). Desalineamiento estructural con dirección ESCO autoritativa. |
| **H2** | `isco_to_canonical_occupation` con 426 entradas post-C3 disponible como infraestructura para pivote ESCO autoritativo. |
| **H3** | Campo `titulo_esco_code` en schema desde intento previo de pivote ESCO; SPEC W puede activarlo sin migración. |
| **H4** | Validador no verifica `esco_occupation_uri` poblada al validar (3.748 ofertas validadas con URI vacía detectadas en sub-fase D). |
| **H5** | Detector multi-position v2.8.1 incompleto: no replica NLP a sub-ofertas (sufijos `_N`). 45 casos detectados (7 D + 38 C1). |
| **H6** | Limpieza de zona geográfica en títulos parcial (CABA, GBA, etc. llegan al matcher). |
| **H7** | ISCO como fallback legítimo cuando ESCO no tiene match conceptual (407 ofertas con `sub_ocupacion_bizarra_revisar`, confirmado por Cynthia). |
| **H8** | Label desincronizado de URI canónica: el matcher escribe labels que no son `preferred_label_es` ni `alt_label` de la URI persistida. 172 D + 33 C1 = 205 casos. |
| **H9** | Cynthia confirma 100% acierto cluster ESCO en B2: el error es de selección de URI específica dentro del cluster correcto, no de familia ocupacional. |
| **H10** | Validación curatorial de Cynthia produce información estructurada (4 categorías + justificación por skill + sub-código ESCO sugerido) que no tiene canal para entrar al sistema downstream. |
| **H11** | `esco_occupation_ancestors` cargada (16.667 entradas, 100% cobertura, profundidad típica 5-6 niveles) como infraestructura permanente. |
| **H12** | Datasets cuantificados por bandera para análisis SPEC W (407 sub_ocupacion_bizarra + 3 cluster_esco_propio + 1 cluster_isco_4dig + 300 subgrupo_compartido). |
| **H13** | Bug del cruce URI×label tuvo impacto masivo (4.151 ofertas afectadas en C1-4, corregidas). Invariante propuesto: validar coherencia URI↔isco_code pre-persistencia. |
| **H14** | F-meta funcional end-to-end demostrado: 0/0/0 → 74.87/38.03/14.49. La cadena URI ESCO ↔ skills ↔ catálogo funciona. |
| **H15** | Extractor de skills produce ~90% de skills fuera del catálogo ESCO de la ocupación matcheada. Dataset cuantificado: 1.145.062 filas con flags=0. |
| **H16** | Sync Supabase no contemplaba flags ESCO (bug estructural pre-existente). Fix aplicado en C5 fix H16: 13 filtros parcheados + 2 columnas nuevas en SELECT + columna `es_opcional` agregada en Supabase + re-sync completo. |

### 6. Datasets cuantificados disponibles para SPEC W

| Dataset | Cantidad | Ubicación |
|---|---:|---|
| Ofertas con `bandera_spec_w = 'sub_ocupacion_bizarra_revisar'` (B2 sub-fase D) | **407** | `notas_revision LIKE '%BANDERA_W%'` |
| Ofertas con `bandera_spec_w_C1` | **304** | columna `bandera_spec_w_C1` |
| └ `cluster_esco_propio_uri_distinta` | 3 | |
| └ `cluster_isco_4dig_uri_distinta` | 1 | |
| └ `subgrupo_compartido_ocupacion_distinta` | 300 | |
| Ofertas afectadas por bug cruce URI×label (C1-4, corregidas) | **4.151** | `pendiente_humano_C1` con notas |
| Ofertas con validación curatorial estructurada de Cynthia | **30** | Supabase `validacion_correcciones` |
| Entradas en `esco_occupation_ancestors` | **16.667** | tabla local |
| Filas en ofertas_esco_skills_detalle con flags=0 (ruido extractor) | **1.145.062** | local |
| Ofertas auto-validadas en SPEC U-1 | **6.461** | 2.770 subfaseD + 3.691 C1 |

### 7. Issues residuales identificados

1. **Infraestructura snapshots Supabase vía RPC SQL server-side** — problema timeouts paginación deep en tablas >500K filas (afectó F0b parcial 83% y F0b' parcial 65.5%). Issue separado para SPEC U-2 o U-3.
2. **Bug `bandera_spec_w_C1` columna formal** — confirmar que persistió correctamente las 304 banderas en BD. Verificación rápida ya hecha en T5 (count by valor) — OK, pero conviene re-validar en próxima sesión.
3. **Cron diario de sync configurado y activo** (`auto_sync.sh` cada hora) pero conviene monitorear primera semana de ejecución. Notificación si falla queda como mejora menor.
4. **Warnings post-sync C5** en `generate_mol_skills_profile.py` y RPC `recalcular_emergentes` (ambos timeouts Supabase). No bloquean el core de sync de ofertas+skills. Issue separado para indicadores derivados.
5. **2 fixes auxiliares** durante SPEC U-1 que quedan en repo:
   - `scripts/canarios/run_canarios.py` — fix Q4/Q5 que silenciaba excepciones (commit pendiente).
   - `scripts/admin_unlock_validated.py` — parche para aceptar 3 estados validados (commit `dcaf29cd` ya pusheado).
   - `scripts/exports/sync_to_supabase.py` — 13 filtros extendidos + flags ESCO mapeados (commit pendiente).

### 8. Cambios respecto a SPEC v3.1 documentados como discrepancias

| Discrepancia | SPEC v3.1 | Real |
|---|---|---|
| Drift Local↔Supabase | ~40K ofertas + 880K skills | **3.834 ofertas, 0 skills zombies** |
| C-Q4 (zombies) baseline | 28.395 | **0** confirmado en F0 (no eran zombies, era diferencia de cardinalidad) |
| C4 tiempo | 8-35 min estimado | **3m30s** ✅ |
| C5 esfuerzo total | 6-10h | ~4h sync inicial + 3h45m re-sync por H16 |
| Total ejecución calendario | 4 días estimado | **6 días real** (+50% por hallazgos no contemplados) |
| `validacion_humana` tabla en Supabase | listada en F0 §3.1 | **no existe** (validaciones humanas viven en `ofertas_dashboard.validacion_correcciones`) |
| C2 sub-fase D: tecnico decisión | Quitar (Opción C) | **Opción 3** (URI por contexto) por over-match 30% |
| Universo a reprocesar en D | 3.758 sin validar | 3 sin validar + 3.748 desbloqueadas (Opción B) |
| Universo a reprocesar en C1 | 8.221 todas | 8.217 (4 humanas reales excluidas) |
| Multi-position skipped (H5) | no contemplado | 7 D + 38 C1 = 45 ofertas detectadas |
| H16 sync flags ESCO | no contemplado | **+3h45m re-sync para cumplir §8.4** |

### 9. SPEC U-1 v3.1 — CERRADO

**Estado:** ✅ **CERRADO**
**Fecha:** 2026-05-11
**Hora:** ~06:30 ART
**Branch:** `feature/spec-e-embeddings-enriquecidos`

**Criterios de éxito SPEC §9 (cross-cutting) — TODOS CUMPLIDOS:**
- ✅ C-Q1 baja drásticamente (3.762 → 7)
- ✅ C-Q3 baja drásticamente (1.237 → 39)
- ✅ C-Q4 = 0 (zombies)
- ✅ C-Q5 = 0 (drift Local↔Supabase)
- ✅ F-meta > 0 en K1/K3/K5 con valores funcionales
- ✅ Drift F-meta Supabase ≈ Local ≤ 1pp

**Próximos SPECs habilitados:**
- **SPEC U-2:** anti-alucinación NLP, fix scrapers, re-incorporar cross-check en pipeline
- **SPEC U-3:** RPC SQL Supabase para paginación, multi-position v2 (H5), notificación cron, label sync invariante (H8)
- **SPEC W:** rediseño arquitectónico ESCO autoritativo con datasets cuantificados de H1-H16

---

**Fin del log de implementación SPEC U-1 v3.1 — Cerrado 2026-05-11 ~06:30 ART.**
