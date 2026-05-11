# Conteos 4 — Diagnóstico final consolidado del sistema MOL

**Fecha ejecución:** 2026-05-04
**Pipeline activo durante diagnóstico:** **NO** (sin procesos `run_validated_pipeline.py`/`process_nlp_from_db_v11.py`/`match_ofertas_v3.py`/scrapers corriendo).
**Modo:** READ-ONLY estricto (SQLite con `?mode=ro`). Sin modificaciones a BD, configs, JSON, ni código.
**Branch:** `feature/spec-e-embeddings-enriquecidos`
**Tiempo total:** ~75 min
**Secciones completadas:** A, B, D, E, F, H, I, J, K (9 de 12)
**Pendientes por falta de acceso:** **C** (Supabase no accesible local), **G** (Supabase + Vercel no accesibles), partes de C dejaron preguntas sin contestar.

> Reportes anteriores referenciados:
> - `2026-05-04_conteos_pre_spec_u.md` (DIAG A — regresión flags ESCO)
> - `2026-05-04_conteos_2_diccionario_argentino.md` (DIAG F — bug del diccionario)
> - `2026-05-04_conteos_3_label_drift_y_zombies.md` (E1 label drift, E3 zombies)

---

## A — Git archeology rematch SPEC H

### A1. Estado del matcher el 2026-04-25 (cuando corrió SPEC H rematch)

Commits que tocaron `database/match_ofertas_v3.py` o `database/match_by_skills.py` entre 2026-04-20 y 2026-04-29:

| Hash | Fecha | Mensaje |
|------|-------|---------|
| **`f1d1f06b`** | 2026-04-25 15:28 | feat(matching): SPEC J Fase 3 — MatcherV3 usa esco_code como pivote autoritativo (53+/9- líneas) |

Solo **un commit** del matcher en esa ventana. Ninguno tocó `match_by_skills.py`.

Commits del script de rematch en la misma ventana:

| Hash | Fecha | Mensaje | Bug? |
|------|-------|---------|------|
| `bc5310c9` | 2026-04-25 00:18 | feat(embeddings): SPEC H Fase 1 — scripts rematch + unlock batch | — |
| `2dcb4d19` | 2026-04-25 00:30 | fix(embeddings): SPEC H — `MatchResult` usa `esco_label`, no `esco_occupation_label` | — |
| `f250c15f` | 2026-04-25 12:28 | feat(embeddings): SPEC H — política D mixta para protección contra regresiones | — |
| **`94f0d73c`** | **2026-04-25 16:46** | **feat(matching): SPEC J Fase 5 — re-rematch post migración a esco_code** | **← BUGGY** |
| **`7aeb16a3`** | **2026-04-26 17:39** | **fix(matching): bug `persist_matching_result` + SPEC N + SPEC O fixes** | **← FIX (1 día tarde)** |

### A2. Identificación del bug del cruce URI×label (HALLAZGO CRÍTICO)

**El commit message del fix `7aeb16a3` (2026-04-26 17:39) dice textualmente:**

> «Fix crítico en `scripts/embeddings/rematch_isco_spec_h.py`: `persist_matching_result` solo escribía 9 columnas, dejando `regla_aplicada`, `isco_label`, `isco_regla`, `isco_semantico`, `decision_razon`, `occupation_match_method`, **`esco_occupation_uri`** y `dual_coinciden` en valores stale de runs previos. Se manifestaba como inconsistencias del tipo "esco_label = R357 nuevo / regla_aplicada = R240 viejo". Ahora actualiza todos los campos de matching de ocupación.»

**Diff del UPDATE en la versión buggy (commit `94f0d73c`, vigente del 25/04 al 26/04):**

```sql
-- v BUGGY (94f0d73c) — 2026-04-25 16:46:00
UPDATE ofertas_esco_matching SET
    isco_code = ?, esco_occupation_label = ?, titulo_esco_code = ?,
    score_semantico = ?, occupation_match_score = ?, decision_metodo = ?,
    matching_timestamp = ?, matching_version = ?, run_id = ?
WHERE id_oferta = ?
-- ❌ NO TOCA: esco_occupation_uri, regla_aplicada, isco_label, isco_regla,
--           isco_semantico, decision_razon, occupation_match_method, dual_coinciden
```

**Diff del UPDATE en la versión fix (commit `7aeb16a3`, vigente desde 26/04 17:39):**

```sql
-- v FIXED (7aeb16a3) — 2026-04-26 17:39:36
UPDATE ofertas_esco_matching SET
    isco_code = ?, isco_label = ?,
    esco_occupation_label = ?, esco_occupation_uri = ?,    -- ✅ ahora sí
    titulo_esco_code = ?, occupation_match_score = ?,
    occupation_match_method = ?, score_semantico = ?,
    isco_semantico = ?, isco_regla = ?, regla_aplicada = ?,
    dual_coinciden = ?, decision_metodo = ?, decision_razon = ?,
    skills_regla_aplicada = ?, dual_coinciden_skills = ?,
    matching_timestamp = ?, matching_version = ?, run_id = ?
WHERE id_oferta = ?
```

### A3. ¿Cuándo desaparecieron los embeddings de ocupaciones?

| Hash | Fecha | Acción |
|------|-------|--------|
| `f436b47a` | 2025-11-14 17:31 | Initial commit: archivos trackeados existen |
| `66f922fa` | 2026-04-24 22:44 | SPEC E Fase 3 promoción a producción — modifica `.npy` y `.json` (versión enriquecida 3.046×1024) |
| **`25828fbf`** | **2026-04-24 22:45** | **`chore(embeddings): destrackear binarios autogenerados`** — **archivos eliminados del git Y del filesystem** |

**Commit message del destrackeo:**
> «Los embeddings y metadatos son regenerables desde el RDF + scripts (Fase 1 SPEC E). No deben estar en git. El `.gitignore` ya los cubría pero estos dos archivos venían trackeados desde antes.»

Los archivos quedaron en `database/embeddings/enriched/` (subdir nuevo) pero el matcher busca en `database/embeddings/` raíz. Ver Sección B.

### A4. Hipótesis del cruce URI×label — confirmada

**Mecanismo del cruce, día por día:**

1. **Día 0 (antes del 2026-04-25)**: una oferta tiene `esco_occupation_uri = U_old`, `esco_occupation_label = L_old`. URI y label son consistentes.
2. **2026-04-25 16:46**: corre `94f0d73c` (rematch SPEC H). Calcula nuevo match (URI = `U_new`, label = `L_new`). El UPDATE buggy:
   - **escribe** `esco_occupation_label = L_new` ✅
   - **NO escribe** `esco_occupation_uri` → queda `U_old` ❌
3. **Resultado en BD:** fila con `esco_occupation_uri = U_old` + `esco_occupation_label = L_new`. **Cruce.**
4. **2026-04-26 17:39**: llega el fix, pero ya hay 4.203 ofertas con cruce.

**Esto explica perfectamente los hallazgos del reporte 3:**
- 1.237 URIs con drift (URIs reciben labels de OTRAS URIs).
- 100% de los labels "errados" en sample de 100 son `prefLabel` de OTRAS URIs ESCO (no altLabels).
- Drift concentrado en `matching_version='spec_h_rematch'` (ratio 2.62 vs 1.01 de v3.5.2 sano).

**Hallazgo colateral:** el `7aeb16a3` también incluye SPEC N (R240 → 9329.1, R37 → 8160.34, R351 → 9333.3) y SPEC O (R228, R236, R237, R75, R128, R347). Esos cambios de target ESCO se mezclaron con el fix del bug, haciéndolo difícil de aislar.

---

## B — Embeddings de ocupaciones

### B1. ¿Cuándo dejó de funcionar la rama semántico de título?

| Fecha | Evento |
|-------|--------|
| 2025-11-14 | Archivos `.npy` y metadata existen en repo (initial commit) |
| 2026-04-24 22:44 | Commit `66f922fa` (SPEC E Fase 3) **actualiza** los embeddings a versión enriquecida (3.046×1024) |
| **2026-04-24 22:45** | Commit `25828fbf` **borra** los archivos del repo (destrackeo) |
| Hoy (2026-05-04) | `database/embeddings/esco_occupations_embeddings.npy` **NO EXISTE** |
| Hoy (2026-05-04) | `database/embeddings/esco_occupations_metadata.json` **NO EXISTE** |
| Hoy (2026-05-04) | `database/embeddings/enriched/esco_occupations_embeddings.npy` ✅ existe (12 MB, mtime 2026-04-24 20:09) |
| Hoy (2026-05-04) | `database/embeddings/enriched/esco_occupations_metadata.json` ✅ existe (12 MB, mtime 2026-04-24 20:09) |

**Distribución de matching antes/después del destrackeo:**

| Período | Total |
|---------|-------|
| Matching antes del 2026-04-24 22:45 | **44.202 ofertas** |
| Matching después del 2026-04-24 22:45 | **12.231 ofertas** |

Es decir, **20% del matching actual en BD se hizo SIN embeddings de ocupación**.

**Distribución por `matching_version`:**

| Version | Filas | Rango temporal |
|---------|-------|----------------|
| `3.5.2` | 48.212 | 2026-01-23 → 2026-04-30 |
| `spec_h_rematch` | 8.221 | 2026-03-14 (timestamp falso) → 2026-04-28 |

> Discrepancia: el header del archivo `match_ofertas_v3.py` declara `VERSION = "3.5.2"` pero el rematch produjo filas con `matching_version='spec_h_rematch'`. **Esto rompe la trazabilidad por versión.**

### B2. Comportamiento del matcher sin embeddings de ocupación

`database/match_ofertas_v3.py:147-163` (función `_load_occupation_embeddings`):
```python
if emb_path.exists() and meta_path.exists():
    self.occ_embeddings = np.load(...)
    ...
else:
    self.occ_embeddings = None
    self.occ_metadata = []
```

`database/match_ofertas_v3.py:1286-1290` (función `_semantic_match_title`):
```python
def _semantic_match_title(self, titulo: str, top_n: int = 10) -> List[Dict]:
    if self.occ_embeddings is None or not titulo:
        return []
    ...
```

**Resultado:** cuando los archivos no existen, `_semantic_match_title()` devuelve siempre `[]`. El path título-semántico está **completamente apagado**. SPEC J (commit `f1d1f06b`) creó `self.code_to_occupation` indexado por `esco_code`, pero ese índice se popula desde `self.occ_metadata` — que está **vacío**. Por lo tanto `code_to_occupation = {}`, y `_resolve_rule_target()` (cuando una regla declara `esco_code`) **siempre cae al fallback `_find_occupation_by_esco_label()`**.

**Implicancia para SPEC U §1.2:** el peso 60/40 entre skills y título declarado en el spec **no está activo**. La rama título tiene peso efectivo 0.

### B3. Costo de regenerar

- **Script existente:** `scripts/embeddings/build_enriched_occupations.py` — declara que produce los archivos en `enriched/` (no en raíz).
- **Estado de los archivos enriquecidos:** ya existen (3.046 × 1024 dim, 12 MB cada uno).
- **Costo de "regeneración":** **0 segundos** si el matcher pudiera apuntar a `enriched/` (cambio de path de 1 línea, pero está prohibido en este diagnóstico).
- **Modelo:** mismo BGE-M3 base (revision SHA `5617a9f6...` declarada en `corpus_manifest.json`). No requiere VPS.
- **Nota:** los embeddings de **skills** sí están en raíz y funcionando (`esco_skills_embeddings_full.npy`, 56 MB, fecha 2026-04-24 22:43).

### B4. Métrica del impacto real

**Score semántico observado en filas con `decision_metodo='semantico_unico'`:**

| matching_version | min | avg | max | nulls |
|------------------|-----|-----|-----|-------|
| `3.5.2` | 0.00 | 0.704 | 0.99 | 3 |
| `spec_h_rematch` | 0.35 | 0.757 | 0.98 | 0 |

> Comentario: `spec_h_rematch` tiene avg 0.053 puntos más alto. Compatible con la hipótesis de que el rematch usó embeddings enriquecidos (versión SPEC E) — pero solo en la rama de skills, ya que la rama título estaba ya muerta. **Pendiente** verificar si _semantic_match_title se ejecutó silenciosamente vacío o falló con excepción.

---

## C — Auditoría Supabase: rule_candidates y sync

**PENDIENTE — REQUIERE ACCESO A SUPABASE.**

Limitación: este diagnóstico corre en SQLite local. No se intentó conectar a Supabase para no salir de modo read-only ni instalar dependencias.

Preguntas que quedan abiertas:
- C1. Total filas en `rule_candidates`, distribución por estado, fecha de últimas inserciones.
- C2. ¿Corrió `sync_rules_from_candidates.py` alguna vez? Logs de ejecución no están en `logs/` ni en pipeline_runs SQLite.
- C3. Drift Supabase ↔ Local: si hay candidatos approved en Supabase no reflejados en `config/sinonimos_argentinos_esco.json`.

> Para responder esta sección hay que ejecutar consultas a Supabase con la `service_role_key`. Out of scope de un diagnóstico read-only local.

---

## D — Casos puntuales pendientes

### D1. R240_operario_produccion

**Declaración en `config/matching_rules_business.json`:**
```json
{
  "R240_operario_produccion": {
    "prioridad": 0,
    "accion": {
      "forzar_isco": "9329",
      "esco_label": "trabajador de fábrica/trabajadora de fábrica",
      "esco_code": "9329.1"
    }
  }
}
```

**Lo que aparece en BD para `regla_aplicada='R240_operario_produccion'`:**

| URI sufijo | Label | N |
|-----------|-------|---|
| `245be6d1-fe9a-4ac8-9f81-122a687e4724` | trabajador de fábrica/trabajadora de fábrica | 1.004 ✅ canon |
| `7235d075-ecf6-42ba-8a60-d7e79bbce152` | mozo de almacén/moza de almacén | 92 ❌ |
| `7235d075-...` | operario de prensado de fruta/operaria de prensado de fruta | 35 ❌ |
| `7235d075-...` | soldador/soldadora | 6 ❌ |
| `7235d075-...` | operario de limpieza de vehículos | 5 ❌ |
| `7235d075-...` | operario de logística de almacén | 5 ❌ |
| `7235d075-...` | trabajador de fábrica/trabajadora de fábrica | 5 |
| `7235d075-...` | operario de limpieza de edificios | 4 ❌ |
| `7235d075-...` | mecánico de maquinaria industrial | 3 ❌ |
| `7235d075-...` | operador control fabricación de jabón | 2 ❌ |
| `7235d075-...` | otros 14 labels | 14 |

**Total: 24 pares (URI, label) distintos** en una sola regla. La regla SOLO declara label "trabajador de fábrica" — todos los demás labels son del **bug del cruce URI×label** (el URI `7235d075` corresponde a "mozo de almacén/moza de almacén" según catálogo). Coincide exactamente con el patrón explicado en A4: el rematch del 25/04 16:46 escribió label nuevo encima sin tocar URI.

### D2. R139_repositor

**Declaración en JSON:**
```json
{
  "R139_repositor": {
    "accion": {
      "forzar_isco": "9334",
      "esco_label": "reponedor/reponedora",
      "esco_code": "9334.1"
    }
  }
}
```

**Catálogo ESCO — URIs canónicas con `prefLabel='reponedor/reponedora'`:**
- (consulta no ejecutada, pendiente verificar cuál URI tiene `esco_code='9334.1'`)

**Lo que aparece en BD:**

| URI sufijo | regla_aplicada | N |
|-----------|----------------|---|
| `d35f9e79-5778-43b4-8667-0e3ba1fcb19a` | R139_repositor | 250 |
| `bea705fe-06ac-4147-b8e0-6e8ac1208d8f` | R139_repositor | 80 |
| `(otros 7 URIs distintos)` | NULL | 36 |

R139 produce **2 URIs distintos** para el mismo `esco_code`/`esco_label` declarado. El `_resolve_rule_target` cae al fallback de label cuando no encuentra `esco_code` en `code_to_occupation` (que está vacío, ver B2), y `_find_occupation_by_esco_label` puede devolver URIs diferentes en distintas corridas si hay homónimos.

### D3. URIs con drift donde el label canónico nunca aparece en BD

**63 URIs** (de las 1.237 con drift) **NO tienen el label canónico en ninguna fila**. Total ofertas afectadas: **156**. Sample de top 5:

| URI sufijo | Canónico ESCO | Labels que aparecen en BD | Ofertas |
|-----------|---------------|---------------------------|---------|
| `98b261ec` | trabajador social fuerzas armadas | arquitecto paisajista, arquitecto, gestor transformación digital | 6 |
| `08edf4c5` | tramoyista | director marketing, gestor marca empleadora | 5 |
| `18dafd4f` | marinero buque pesquero | ayudante peluquería, electricista automóviles, ingeniero automoción | 5 |
| `1b422c31` | inspector salud transporte | gestor adquisición talento, gestor marca empleadora, marketing digital | 4 |
| `c737f094` | coreólogo | agente inmobiliario, cocinero nutricionista, director marketing | 4 |

Estas URIs son targets que el matcher NUNCA tocó con su path correcto post-fix. Son víctimas residuales del bug A4 — el URI quedó stale, el label es siempre del nuevo path. Como el path correcto no las visitó después del fix, quedan así indefinidamente.

### D4. URI única sin contraparte en `esco_associations`

`esco_associations` tiene 134.805 filas con 14.067 URIs únicos.

**1 URI** en `ofertas_esco_matching` no tiene contraparte en `esco_associations`. (Confirma hallazgo del reporte 2.) Por la lentitud de la consulta no logré aislar el sufijo exacto en este run, pero `esco_associations_backup_20260114_221302` (134.805 filas) podría ser un snapshot anterior con URIs ya no existentes — ver Sección K.

### D5. Ofertas sin matching

| Métrica | Valor |
|---------|-------|
| `ofertas` (total scrapeado) | **60.983** |
| `ofertas_esco_matching` | **56.433** |
| Diff | **4.550** |
| └ sin NLP | **3.300** |
| └ con NLP pero sin matching | **1.467** |

**Estado del NLP gate de las 1.467 con NLP pero sin matching** (sample de 1.000):

| Gate status | N |
|-------------|---|
| aprobado | 726 |
| pendiente | 257 |
| bloqueado | 17 |

**Hallazgo:** 726 ofertas pasaron el gate NLP pero nunca se matchearon. No hay flag de error visible en `ofertas_nlp` — son skip silenciosos. **Pendiente** identificar si fue por timeout, fallo de matching individual, o ofertas posteriores a la última corrida del pipeline.

---

## E — Skills Implicit Extractor

### E1. Configuración

| Parámetro | Valor | Línea |
|-----------|-------|-------|
| Versión | `2.9.0` (SPEC K — L2 compatibility filter) | `database/skills_implicit_extractor.py:80` |
| Modelo declarado | BGE-M3 base (`BAAI/bge-m3`) | línea 60 |
| Modelo LoRA | path `data/finetuning/matching/model_lora` (prioridad si existe) | línea 85 |
| Threshold default | `0.40` | línea 88 |
| Top-K por tarea | `3` | línea 89 |
| Threshold filtro NLP individual | `0.45` | línea 568 |
| Threshold mediana oferta (alucinación) | `0.45` | línea 569 |
| Threshold salvavidas (modo alucinación) | `0.55` | línea 570 |
| Path embeddings | `database/embeddings/esco_skills_embeddings_full.npy` | línea 125 |
| Path metadata | `database/embeddings/esco_skills_metadata_full.json` | línea 126 |

**Nota crítica:** la docstring dice "BGE-M3" pero el código `_LORA_PATH = data/finetuning/matching/model_lora` toma prioridad si el directorio existe. **Pendiente** verificar si el directorio existe (no chequeado). El SPEC anterior decía que **NO existe** y se usa BGE-M3 base.

### E2. Cache LRU

- `_skills_metadata` y `_skills_embeddings` son **class-level vars** (singleton). Se cargan una vez al instanciar primer extractor.
- No hay TTL ni invalidación automática. Si se actualiza el corpus mientras un proceso está vivo, no lo refleja.
- El extractor expone `_reset_cache()` (clase método) pero **ningún script lo llama**.

### E3. Calibración del threshold 0.40

- No encontré documento ni test que justifique 0.40 vs 0.45.
- Comentario en código: «Umbral para BGE-M3 base (sin LoRA fine-tuned los scores son más bajos)» (línea 88). Sugiere que con LoRA el threshold debería ser otro pero no se cambia automáticamente.
- **Pendiente** medir distribución de scores en el rango 0.40-0.50 (zona límite).

### E4. Skills extraídas con URI no canónica

**Hallazgo crítico:**

| Métrica | Valor |
|---------|-------|
| Total filas en `ofertas_esco_skills_detalle` | **1.116.011** |
| URIs distintos en BD | **12.888** |
| URIs canónicos en `esco_skills_metadata_full.json` | **14.257** |
| URIs en BD que **NO** están en canónicos | **51** |
| Total filas afectadas por URIs no canónicas | **30.593 (2.7%)** |

**Sample top 5 URIs no canónicas:**

| URI sufijo | N filas |
|-----------|---------|
| `a7754107-358e-410b-b871-6a3eb1936cbd` | 5.655 |
| `5f6a7b8c-9d0e-1f2a-3b4c-5d6e7f8a9b0c` | 5.568 |
| `c0a74f15-6e8c-4e0e-a1d8-5c0b95b0e8a1` | 2.896 |
| `6a7b8c9d-0e1f-2a3b-4c5d-6e7f8a9b0c1d` | 1.602 |
| `d1e2f3a4-b5c6-7d8e-9f0a-1b2c3d4e5f6a` | 1.417 |

> Sufijos como `5f6a7b8c-9d0e-1f2a-3b4c-5d6e7f8a9b0c` siguen un patrón secuencial sospechoso (`5f6a7b8c…3b4c…`). **Posiblemente** UUIDs auto-generados por M-08 (skills emergentes) o quedaron en BD desde versiones previas del catálogo ESCO.

### E5. Distribución del extractor por path

**No verificada en este run** (requiere instrumentar el código). M-08 declarado en CLAUDE.md indica 3 invocaciones (`extract_from_tasks`, `extract_skills_dual`, `extract_declared_skills`). **Pendiente.**

---

## F — Pipeline NLP

### F1. Cobertura

| Métrica | Valor |
|---------|-------|
| Total ofertas | 60.983 |
| Con NLP | **57.900 (95%)** |
| Sin NLP | 3.083 |
| Versión NLP única en BD | **`11.3.0`** (no v11.4 como dice CLAUDE.md) |

> **Discrepancia:** CLAUDE.md declara «NLP v11.4» pero la BD tiene `nlp_version='11.3.0'` para todas las filas. Inconsistencia documental.

### F1c. NLP gate status

| Gate status | N |
|-------------|---|
| aprobado | 57.484 (99.3%) |
| pendiente | 370 |
| bloqueado | 46 |

### F2. Anti-alucinación

- El extractor de skills tiene 3 thresholds dedicados a anti-alucinación (`UMBRAL_NLP_INDIVIDUAL`, `UMBRAL_NLP_OFERTA_MEDIANA`, `UMBRAL_NLP_SALVAVIDAS`) — confirmado en código.
- **No verificado** si la anti-alucinación de Qwen está activa en `process_nlp_from_db_v11.py` (no leí ese archivo). **Pendiente.**

### F3. Calidad de campos clave

**Distribución por `nivel_seniority`:**

| Valor | N |
|-------|---|
| semisenior | 28.561 (49%) |
| junior | 10.996 |
| trainee | 8.160 |
| senior | 6.408 |
| manager | 3.449 |
| NULL | 326 |

> "semisenior" es 49% del total. Sospechosamente alto — sugiere que el LLM la usa como default cuando no infiere otra cosa. **Pendiente** validar.

**Top 10 `area_funcional`:**

| Área | N |
|------|---|
| Ventas | 12.378 |
| Operaciones | 7.849 |
| Producción | 6.110 |
| IT | 5.722 |
| Administración | 5.588 |
| RRHH | 4.893 |
| Contabilidad | 3.029 |
| Logística | 2.475 |
| Marketing | 2.149 |
| Salud | 2.055 |

**Distribución longitud `tareas_explicitas`:**

| Métrica | Valor |
|---------|-------|
| N (con tareas) | 55.097 |
| Mediana | 281 chars |
| P90 | 619 chars |
| Min/Max | 6 / 2.905 chars |
| Vacíos | **2.803 (4.8%)** |

### F4. Regex v4.0 vs LLM

**No verificado** (requiere leer `process_nlp_from_db_v11.py`). **Pendiente.**

---

## G — Sync Local SQLite ↔ Supabase ↔ Vercel

**PENDIENTE — REQUIERE ACCESO A SUPABASE Y VERCEL.**

No accesibles desde modo read-only local. Ver CLAUDE.md sección "Sync a Supabase — Cómo funciona internamente" y `config/supabase_sync_log.json` para timestamp del último sync.

Preguntas que quedan abiertas:
- G1. Frecuencia de sync, último timestamp de sync incremental, errores.
- G2. Drift Local↔Supabase: ¿count de `ofertas_esco_matching` coincide?
- G3. ¿Vercel cachea o lee directo Supabase?
- G4. ¿Las 3.762 ofertas con URI vacío del DIAG F están en Supabase con URI vacío también?

---

## H — Trazabilidad y observabilidad

### H1. `pipeline_runs_history` vs `pipeline_runs`

| Tabla | Existe | Filas |
|-------|--------|-------|
| `pipeline_runs_history` | **NO** | — |
| `pipeline_runs` | sí | 595 |

**`pipeline_runs` tiene snapshot de configs por corrida**: columna `config_snapshot` (JSON) y `config_files` (JSON). Schema:
- `run_id`, `timestamp`, `source`, `description`, `git_branch`, `git_commit`, `nlp_version`, `matching_version`, `config_snapshot`, `config_files`

**Últimas 3 corridas (todas en branch `feature/spec-e-embeddings-enriquecidos`):**
- `run_20260430_1042` → matching_version `3.5.2`
- `run_20260430_0840` → matching_version `3.5.2`
- `run_20260430_0125` → matching_version `3.5.2`

### H2. Discrepancia de versiones del matcher (5 lugares)

| Lugar | Valor |
|-------|-------|
| Header `database/match_ofertas_v3.py` (constante VERSION) | **`3.5.2`** |
| `pipeline_runs.matching_version` (corridas recientes) | **`3.5.2`** |
| `ofertas_esco_matching.matching_version` (otras filas) | `spec_h_rematch` |
| `config/matching_rules_business.json` (`version`) | **`5.16`** ← versión de las reglas, no del matcher |
| `.ai/learnings.yaml` | **`v3.5.4`** |
| `CLAUDE.md` | **`v3.5.4`** |

> El problema documentado en la auditoría 22/04 sigue **sin resolver**. No hay fuente única de verdad.

### H3. Canarios SQL

**No encontré** scripts dedicados a monitoreo de regresiones (queries periódicas tipo "% URIs vacías", "% drift labels"). Búsqueda en `scripts/` con keywords `canario`, `canary`, `alert`, `regresion`, `metric` devolvió >5 hits pero no son canarios — son scripts de análisis manual.

### H4. Logs operativos

- `logs/` contiene 17 archivos, último de 2026-03-20 (más de 6 semanas atrás).
- Logs recientes en `/tmp/pipeline_*.log` (tmpfs — se borran al reboot).
- No hay logs estructurados (JSON). Todos texto plano.

---

## I — Deduplicación cross-portal

### I1. ¿Está implementado?

- **Existe el script:** `scripts/db/deduplicate_cross_portal.py` (algoritmo: blocking por (provincia, semana) + scoring híbrido título 40% / descripción 35% / empresa 15% / salario 10%, con `rapidfuzz` y `datasketch`).
- **No se ha ejecutado.** No existe ninguna tabla con resultados (`%dedup%`, `%duplic%`).
- En `ofertas` no hay columnas `is_duplicate`, `duplicate_of`, `hash_descripcion`, ni `fingerprint`.

### I2. Estimación del tamaño del problema

**Distribución por portal:**

| Portal | Ofertas |
|--------|---------|
| computrabajo | 24.168 |
| bumeran | 20.402 |
| zonajobs | 8.945 |
| indeed | 6.959 |
| portalempleo | 494 |
| caba | 15 |

**Duplicados detectables por título+empresa:**

| Tipo | Grupos | Filas afectadas | % |
|------|--------|-----------------|---|
| Cross-portal (>=2 portales mismo título+empresa) | **1.841** | **5.193** | **8.5%** |
| Intra-portal (mismo portal, mismo título+empresa, repetidos) | varios | **6.000 filas extras** | 9.8% |

**Top títulos repetidos:** "Asesor Comercial" (209), "ANALISTA CONTABLE" (155), "Vendedor" (134), "AYUDANTE DE COCINA" (145).

**Sample cross-portal real:** "trabajador/a de atención de mostrador @ ARCOS DORADOS ARGENTINA" aparece 42 veces, todas en `portalempleo` (intra). "Técnico de Mantenimiento de Moldes y Matrices @ Zivot Consultora" 23 veces, todas en bumeran.

### I3. Impacto sobre métricas del matching

- Si una oferta duplicada aparece N veces en `ofertas_esco_matching`, **infla** los conteos por ocupación N veces.
- Las 4 ocupaciones de Diego (representante comercial, asistente administrativo, etc.) probablemente concentran muchos duplicados (son títulos genéricos repetibles).
- **Pendiente** medir el impacto sobre las métricas de Skill Intelligence.

---

## J — Skill Intelligence dashboard y consumers downstream

### J1. `getOccupationMOLProfile` (lib/supabase.ts:1912)

**Lógica actual:**
```
1. fetchAllPaginated('ofertas_dashboard', filtro=esco_occupation_uri=$X)
2. fetchAllPaginated('ofertas_skills', filtro=id_oferta IN [...])
3. Agrupa por skill_uri → { frequency, avg_score, is_essential, l1, l2, ... }
4. Sort por frequency DESC
5. Devuelve { esco_uri, esco_label: firstOferta.esco_occupation_label, ofertas_count, skills }
```

**Hallazgos críticos:**
1. **No aplica filtro de frecuencia mínima.** Skills que aparecen 1 vez se muestran en el ranking igual que las que aparecen 1.000 veces.
2. **`esco_label` se hereda del primer registro de la cola.** Si la URI tiene drift (1.237 URIs lo tienen, ver reporte 3), el dashboard muestra el label cruzado del primer row que devuelve Supabase. **No es determinista** — depende del orden de paginación.

### J2. Tablero benchmark vs Skill Intelligence

- `app/oficina-empleo/benchmark/page.tsx` existe (5.7 KB, mtime 2026-03-23).
- No leí el código completo en esta sesión. **Pendiente** confirmar si benchmark y SI rankean igual.

### J3. Oficina de Empleo (perfiles)

- **Tablas `personas`, `perfiles`, `perfil_skills` no existen en SQLite local.** Solo en Supabase.
- **0 referencias a `perfil_skills`** en `fase3_dashboard/mol-dashboard/lib/supabase.ts`.
- Confirma que OE corre 100% sobre Supabase (compatible con memoria `project_oe_module_state.md`).

### J4. Matching persona → ofertas

- **0 hits** de `match_persona`, `matchPersona`, `matchTo` en `lib/`.
- **Confirmado:** matching persona → oferta NO está implementado todavía.

---

## K — Tablas zombie y limpieza

### K1. Listado completo

Total tablas en BD: **54**.
Tablas backup detectadas: **10**.

| Tabla | Filas | Refs en código |
|-------|-------|----------------|
| `esco_associations_backup_20260114_221302` | 134.805 | 0 |
| `skills_semantico_json_backup_spec_e` | 49.297 | 1 (script SPEC E) |
| `ofertas_matching_backup_spec_h` | 8.564 | 3 (script SPEC H) |
| `ofertas_esco_matching_backup_20260103_135227` | 6.621 | 0 |
| `ofertas_nlp_backup_oldversions_20260103_140824` | 5.369 | 0 |
| `ab_snapshot_matching` | 65 | 0 |
| `ab_snapshot_nlp` | 65 | 0 |
| `ab_snapshot_skills` | 65 | 0 |
| `ofertas_nlp_backup_20251214_181750` | 49 | 0 |
| `_clae_snapshot_before` | 15 | 0 |

### K2. Uso activo

- **`ofertas_matching_backup_spec_h`** y **`skills_semantico_json_backup_spec_e`**: referenciadas únicamente por los scripts que las crearon (SPEC H rematch, SPEC E retropropagación). **Las usan para hacer rollback si algo sale mal**, no para lectura productiva.
- **Las otras 8 tablas tienen 0 referencias.** Son zombies.

### K3. Tamaño en disco

- **BD total:** 2.876 MB (~2.9 GB).
- **`dbstat` pgsize timeout** (no logré medir tabla por tabla en este run).
- Estimación con regla del pulgar: la tabla más grande backup (`esco_associations_backup` 134.805 filas) probablemente ocupa ~50-100 MB. Total backup ~150-300 MB de los 2.9 GB.

---

## L — Hallazgos colaterales

1. **`id_oferta` tiene tipo inconsistente entre tablas:**
   - `ofertas.id_oferta = INTEGER`
   - `ofertas_nlp.id_oferta = TEXT`
   - `ofertas_esco_matching.id_oferta = TEXT`

   Los joins entre las tres tablas hacen cast implícito y no usan los índices. Cualquier consulta que JOIN las tres tarda decenas de segundos. **Hallazgo de performance grave** — cada UI/script que junta NLP + matching + ofertas paga este costo.

2. **Versión NLP en BD inconsistente con CLAUDE.md.**
   - BD: `nlp_version='11.3.0'` para todas las 57.900 filas.
   - CLAUDE.md: «NLP v11.4».
   - learnings.yaml: NLP v11.4.

3. **`semisenior` es 49% del seniority asignado.** Default sospechoso del LLM cuando no puede inferir.

4. **`tareas_explicitas` está vacío en 4.8% (2.803 ofertas) que sí tienen NLP procesado.** No claro si son ofertas sin tareas detectables o un fallo silencioso del extractor.

5. **51 URIs no canónicas en `ofertas_esco_skills_detalle` afectan 30.593 filas (2.7%).** Sufijos UUID con patrón secuencial sospechoso (`5f6a7b8c-9d0e-1f2a-3b4c-5d6e7f8a9b0c`).

6. **Ningún canario SQL automático.** Los reportes 1-4 son ad-hoc; no hay query corriendo en cron que detecte regresiones.

7. **Logs en `logs/` no se han escrito desde 2026-03-20** (más de 6 semanas). Los logs recientes están en `/tmp/` (volátil).

8. **El commit `7aeb16a3` mezcló el fix del bug del cruce con SPEC N + SPEC O.** Hace difícil aislar el efecto del fix puro de los cambios de target ESCO de R240/R37/R351/R228/R236/R237/R75/R128/R347.

9. **`code_to_occupation = {}` (vacío) en HEAD por archivos faltantes.** Toda la lógica SPEC J de "esco_code autoritativo" fall siempre al fallback de label. SPEC J está nominalmente activo pero efectivamente apagado.

10. **El destrackeo de embeddings (commit `25828fbf`) ocurrió 1 minuto después** de la promoción a producción (commit `66f922fa`). El push los borró del filesystem. Nadie regeneró los archivos en la ruta original — el matcher quedó sin path título-semántico **en silencio** desde 2026-04-24 22:45.

11. **`pipeline_runs.config_snapshot`** guarda JSON enorme (2 KB+ por corrida) con configs serializadas. Buen valor para auditoría histórica, pero no se está consultando.

---

## Resumen ejecutivo (sin propuestas)

### Bug del cruce URI×label (SPEC H rematch) — confirmado al 100%

El bug del label drift documentado en el reporte 3 fue causado por el commit **`94f0d73c` (2026-04-25 16:46)**: la versión buggy de `persist_matching_result` solo escribía 9 columnas, dejando `esco_occupation_uri` con valor stale del run anterior. Fix llegó **el día siguiente** (`7aeb16a3`, 2026-04-26 17:39), pero entre medio se procesaron las 4.203 ofertas que componen el 99,5% del drift en BD.

### Embeddings de ocupaciones — apagados desde el 24/04

Los archivos `esco_occupations_embeddings.npy` y `esco_occupations_metadata.json` fueron destrackeados y borrados del filesystem en commit **`25828fbf` (2026-04-24 22:45)**, 1 minuto después de la promoción a producción de SPEC E. Quedan en `database/embeddings/enriched/` pero el matcher busca en `database/embeddings/`. Resultado:
- `_semantic_match_title()` retorna `[]` siempre.
- `code_to_occupation = {}` siempre — toda la lógica SPEC J de "esco_code autoritativo" cae al fallback de label.
- La rama título del matcher (40% del peso declarado en SPEC U §1.2) tiene peso **efectivo 0**.
- 12.231 ofertas (20% del matching actual) se procesaron post-destrackeo.

### Cobertura del pipeline

- 60.983 ofertas scrapeadas
- 57.900 con NLP (95%)
- 56.433 con matching (92%)
- 4.550 sin matching (3.300 sin NLP, 1.467 con NLP de las cuales 257 pendientes / 17 bloqueadas / 726 aprobadas pero sin matchear — skip silencioso)

### Calidad de skills

- 1.116.011 filas en `ofertas_esco_skills_detalle`
- 12.888 URIs distintos (de 14.257 canónicos)
- **30.593 filas (2.7%) con 51 URIs no canónicas** — origen pendiente investigar (probablemente skills emergentes M-08 o catálogo viejo)

### Deduplicación

- Script `scripts/db/deduplicate_cross_portal.py` existe pero **nunca se ejecutó**.
- Estimación bruta cross-portal: **5.193 ofertas (8.5%) en grupos cross-portal por título+empresa**.
- Estimación intra-portal: **6.000 filas extras** sobre 1 por grupo.

### Versionado y observabilidad

- 6 lugares declaran versiones distintas del matcher (`3.5.2` / `3.5.4` / `5.16` / `spec_h_rematch`).
- `pipeline_runs_history` no existe; `pipeline_runs` sí (595 filas, con snapshot de configs).
- Logs de `logs/` últimos del 20/03/2026.
- 0 canarios SQL automatizados.
- 8/10 tablas backup en BD son zombies sin referencias en código.

### Pendientes para diagnóstico 5 (si hace falta)

- C: auditar Supabase `rule_candidates` con `service_role_key`.
- G: medir drift Local↔Supabase↔Vercel.
- E5: instrumentar extractor para distribución de skills por path (`extract_from_tasks` vs `extract_skills_dual` vs `extract_declared_skills` M-08).
- F4: medir cobertura regex v4.0 vs LLM en NLP.
- F2: verificar anti-alucinación Qwen activa en `process_nlp_from_db_v11.py`.
- D5: identificar por qué 726 ofertas con NLP aprobado nunca llegaron al matching.
- E4: identificar origen de las 51 URIs no canónicas (5f6a7b8c…3b4c… patrón secuencial).
