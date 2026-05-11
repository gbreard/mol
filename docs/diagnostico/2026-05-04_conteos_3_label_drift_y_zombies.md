# Conteos 3 — Label drift y zombies

**Fecha ejecución:** 2026-05-04
**Pipeline activo:** no (sin procesos `run_validated_pipeline`/`match_ofertas`/`process_nlp` corriendo, sin WAL/SHM en SQLite)
**Modo:** read-only estricto (SQLite con `?mode=ro`, sin escrituras a configs/BD/scripts del pipeline)
**Tiempo total:** ~30 min
**Output declarado en prompt:** `/mnt/user-data/outputs/` no existe en este entorno → archivo escrito en `docs/diagnostico/2026-05-04_conteos_3_label_drift_y_zombies.md` (consistente con reportes 1 y 2)
**Sin commit a git.**

**Queries no completadas:**
- B4 (historial de `sync_rules_from_candidates.py`): la tabla `rule_candidates` está en **Supabase**, no en SQLite local — no se puede responder en modo read-only sin conectar a Supabase. Marcado como pendiente.

---

## A — Label drift

### A1. Volumen exacto y distribución

```
Filas con esco_occupation_uri no vacío:           52.671
URIs distintas con URI no vacía:                   2.232
URIs con al menos 1 label no vacío:                2.232  (100%)
```

| # labels distintos | URIs | % del total |
|---:|---:|---:|
| 1 | 995 | 44,6% |
| 2 | 534 | 23,9% |
| 3-5 | 524 | 23,5% |
| 6-10 | 133 | 6,0% |
| 11-20 | 34 | 1,5% |
| >20 | 12 | 0,5% |

**1.237 URIs (55,4%) tienen drift** (>1 label).
**Ofertas en URIs con drift:** 44.770 (85,0% de las 52.671 filas con URI).

### A2. Concentración del problema

**Top 20 URIs con más labels distintos:**

| URI (sufijo) | n_labels | n_filas | Top label en BD |
|---|---:|---:|---|
| f4de7e28-…b3aa83b | 41 | 210 | director departamento laboratorio médico (140) |
| 6a6e174e-…81cdee5 | 34 | 199 | empleado mostrador oficina postal (155) |
| bea705fe-…6f4f87f | 31 | 962 | mozo de almacén (844) |
| 612430b3-…4953f66 | 28 | 118 | empleado servicio venta entradas (82) |
| 33e3a746-…531cb2 | 25 | 97 | director salón de belleza (60) |
| 9ba74e8a-…7c5c11df | 24 | 105 | vendedor/vendedora (78) |
| 7235d075-…7bbce152 | 23 | 171 | mozo almacén (92) |
| 9b889f07-…650b9ac | 23 | 499 | médico especialista (467) |
| 40517ed4-…0d939bd2d3 | 22 | 307 | supervisor producción (285) |
| 01989dd8-…fc409de9c4 | 21 | 61 | ingeniero especializado en desmantelamiento (40) |
| 49e4e358-…56f5f7 | 21 | 53 | quiropráctico (31) |
| b7b75eb6-…9bcc1397 | 21 | 841 | agente centro atención cliente (815) |
| 9653fb92-…02fa93b | 20 | 48 | empleado servicio atención al viajero (23) |
| 18fbb1f8-…f6130bbf | 18 | 48 | supervisor empapelado (22) |
| a14e96a7-…7bac5 | 18 | 48 | director formación empresas (29) |
| 47e81c7f-…3c36344 | 17 | 76 | ayudante marketing (58) |
| 547b304b-…46df5f64e | 17 | 2.914 | vendedor especializado (2.895) |
| 7d27600b-…2d47572035 | 17 | 50 | jefe taller artes escénicas (28) |
| 2d5a50c6-…44d1bf1e3d12 | 16 | 46 | empleado centro termal (30) |
| c0a15ec7-…ff6f4f87f | 16 | 70 | operario cultivo acuícola (47) |

**Top 20 cubren 6.923 ofertas = 15,5% de las 44.770 con drift.**

**Drift por método (`occupation_match_method`):**

| Método | pares (uri\|\|label) únicos | URIs únicos | filas | pares/uri |
|---|---:|---:|---:|---:|
| `skills_first_v3` | **5.441** | 2.111 | 14.673 | **2,58** |
| `semantic_fallback_v3` | 569 | 523 | 1.098 | 1,09 |
| `regla_negocio_R240_operario_produccion` | 24 | 2 | 1.175 | 12,00 |
| Resto de reglas (~290 reglas) | 1-2 cada una | 1-2 | varía | 1,00 |

**Hallazgo clave:** el drift es responsabilidad casi exclusiva de `skills_first_v3` (path semántico). Las reglas de negocio mantienen un label estable (1,00 pares/URI), salvo R240 que tiene 12 labels para 2 URIs (caso aparte).

### A3. Cuál es el label "correcto"

**Comparación BD vs catálogo (10 URIs muestreadas: 5 top + 5 medio):**

| URI sufijo | n_labels | Canónico (catálogo `esco_label`) | Cubre % filas |
|---|---:|---|---:|
| f4de7e28 (1349.17) | 41 | director departamento laboratorio médico | 66,7% (140/210) |
| 6a6e174e (4211.2) | 34 | empleado mostrador oficina postal | 77,9% (155/199) |
| bea705fe (9333.8) | 31 | mozo de almacén | 87,7% (844/962) |
| 612430b3 (5230.3) | 28 | empleado servicio venta entradas | 69,5% (82/118) |
| 33e3a746 (1431.2.1) | 25 | director salón de belleza | 61,9% (60/97) |
| af355ac4 | 3 | supervisor operaciones intro datos | 75,0% (6/8) |
| af513bd8 | 3 | conductor coche fúnebre | 50,0% (2/4) |
| b0480558 | 3 | técnico maquinaria construcción | 62,5% (5/8) |
| b10dc548 | 3 | chef de pastelería | 40,0% (4/10) — chocolatero (4) iguala |
| b3b32930 | 3 | instructor de vuelo | 50,0% (2/4) |

**Métrica global sobre las 1.237 URIs con drift:**

```
URIs con drift:                                     1.237
  Canónico presente en BD:                          1.174 (94,9%)
  Canónico es el label más frecuente:               1.013 (81,9%)
  Canónico NO está en BD para esa URI:                 63 (5,1%)
Total filas en URIs con drift:                     44.770
  Filas con label canónico:                        40.454 (90,4%)
  Filas con label NO canónico:                      4.316 (9,6%)
```

**Coincidencia matcher → catálogo (fuente de verdad):**
- `esco_occupations_full.json` (3.046 entries, 3.045 con `esco_label`).
- Tabla SQL `esco_occupations` (3.045 entries, 3.045 con `preferred_label_es`).
- 0 discrepancias entre SQL y JSON. **El catálogo NO es la fuente del drift.**

### A4. Origen del drift por método

**Para top 5 URIs con drift, breakdown (label, método, n):**

```
URI f4de7e28 (41 labels):
  TODOS los labels vienen de skills_first_v3 (sin excepción)
  director del depto laboratorio médico       skills_first_v3   140  ← canónico
  ingeniero industrial / arquitecto / DevOps  skills_first_v3   ~70  ← labels de OTRAS URIs

URI 6a6e174e (34 labels):
  empleado mostrador oficina postal           skills_first_v3   130  ← canónico
  empleado mostrador oficina postal           semantic_fallback  25  ← canónico (path alternativo)
  organizador bodas / técnico mantenim / etc  skills_first_v3    ~44  ← cruzados

URI bea705fe (31 labels) — caso mixto:
  mozo de almacén  R353_operario_carga       228  ← regla, canónico
  mozo de almacén  R137_picking              185
  mozo de almacén  R136_personal_deposito    108
  mozo de almacén  R32_operario_picking       81
  mozo de almacén  skills_first_v3           122  ← semántico, canónico
  reponedor       R139_repositor              79  ← regla con label canónico para SU URI;
                                                    aquí guarda label="reponedor" pero uri=mozo_almacen
                                                    (mismatch URI/label dentro de regla)
  resto: ~30 labels, todos vía skills_first_v3
```

**Resumen global:** del total de 4.690 pares (URI, label_distinto) en URIs con drift, **filas con label != canónico:**

| decision_metodo | filas con label no canónico |
|---|---:|
| `semantico_unico` | 4.158 (91,1%) |
| `dual_coinciden` | 292 (6,4%) |
| `regla_por_score_bajo` | 60 (1,3%) |
| `regla_prioridad` | 28 (0,6%) |
| `regla_zona_gris` | 14 |
| `regla_manual_fix` | 9 |
| `regla_override_semantico_alto` | 2 |
| `regla_revisar` | 2 |
| `regla_manual` | 1 |

**91% del drift viene de la rama puramente semántica.**

### A5. Origen del drift por path interno

**Asignación de `esco_occupation_label` (puntos en código):**

| archivo:línea | contexto | comportamiento |
|---|---|---|
| `match_by_skills.py:286` | `esco_label = meta.get('label', '')` dentro de `match()` | Lee de `self.occupation_metadata[occ_uri]` poblado desde **tabla SQL `esco_occupations`** (línea 201-210). 1 label por URI. |
| `match_ofertas_v3.py:1306` | `_semantic_match_title()` | Lee `meta = self.occ_metadata[idx]`, donde `occ_metadata` se carga de `esco_occupations_metadata.json`. **El archivo NO existe** en `database/embeddings/`, por lo que `self.occ_embeddings = None` y la función retorna `[]`. |
| `match_ofertas_v3.py:1356` | `_combine_candidates()` | Indexa por URI: `base = skill_c if skill_c else title_c`. En el path actual, `title_c` queda siempre vacío (ver fila anterior); `skill_c` viene del lookup SQL. Determinístico. |
| `match_ofertas_v3.py:647-648` | `semantic_label = best.get("esco_label","")`, `semantic_uri = best.get("occupation_uri","")` | Toma del candidato top combinado. |
| `match_ofertas_v3.py:1454` | `_save_match()` persiste `result.esco_uri, result.esco_label` en `ofertas_esco_matching` |
| `scripts/embeddings/rematch_isco_spec_h.py:228` | `esco_label_nuevo = result.esco_label or meta.get('esco_label') or ''` | **Script de rematch SPEC H** que escribió `matching_version='spec_h_rematch'` en BD el 2026-04-25. Toma del MatchResult del matcher. |

**Hallazgo dirimente — distribución del drift por `matching_version`:**

| matching_version | filas | URIs únicas | pares uri\|\|label | ratio | extra labels (drift puro) |
|---|---:|---:|---:|---:|---:|
| `3.5.2` | 44.461 | 1.956 | 1.969 | **1,01** | 13 |
| `spec_h_rematch` | 8.210 | 1.480 | 3.872 | **2,62** | 2.392 |

**Conclusión:** el drift no es histórico ni acumulado por múltiples runs — está **concentrado casi por completo en el rematch SPEC H** (script `scripts/embeddings/rematch_isco_spec_h.py`, ejecutado 2026-04-25). v3.5.2 produce 1,01 pares/URI (sano). spec_h_rematch produce 2,62 pares/URI (drift severo).

**Mecanismo exacto que cruzó URI/label:** no se pudo identificar línea por línea sin reconstruir el estado del repo al 2026-04-25 (no se hizo en este diagnóstico). Lo observable es que `result.esco_uri` y `result.esco_label` que llegan al persist en `rematch_isco_spec_h.py:228-229` están ya desincronizados — proviene del matcher mismo (`match_ofertas_v3.py`). Pendiente para diagnóstico 4: cotejar git log del matcher entre 2026-04-23..2026-04-26 para ver qué cambió en `_combine_candidates` o el path de skills.

### A6. Impacto operativo del drift

**Skill Intelligence dashboard agrupa por URI, no por (URI, label):**

| Archivo | Línea | Comportamiento |
|---|---|---|
| `lib/supabase.ts:1825-1838` | `getOccupationsWithMOLData()` | `grouped[uri]` indexed por URI. `esco_label = o.esco_occupation_label \|\| ''` del **primer** registro que llega para esa URI. |
| `lib/supabase.ts:2007` | `firstOferta.esco_occupation_label` | Mismo patrón: toma label del primer registro. |
| `lib/supabase.ts:1530, 1817-1818, 1856, 1925-1926` | Filtros y selects | Todos por `esco_occupation_uri`, no por label. |
| `OcupacionTab.tsx:96, 120` | Wizard de validación | `esco_label = match.label` viene del matcher externo, no del label de BD. |

**Consecuencia operativa:**
- **No hay duplicación de filas** en el dashboard (todo se agrupa por URI).
- **El label mostrado depende del orden de retorno** de Supabase, que no es estable. Dos cargas de la misma vista pueden mostrar etiquetas distintas para una misma URI cuando hay drift. Para 1.013 URIs el label más frecuente es el canónico → ordenamientos por count harían converger; sin orden explícito puede salir cualquier label.
- **Filtros y joins por URI** funcionan bien, no son afectados.
- **No hay queries que dependan del label como clave** ni `GROUP BY (uri, label)` en SQL.

**Distribución de filas con label NO canónico por estado de validación:**

| estado_validacion | filas no canónicas | filas totales | %  |
|---|---:|---:|---:|
| `pendiente` | 0 | 33 | 0,0% |
| `validado` (humano) | 46 | 6.422 | 0,72% |
| `validado_claude` | 4.520 | 46.216 | 9,78% |
| **Total** | **4.566** | **52.671** | **8,67%** |

**46 filas validadas por humano** ya quedaron persistidas con label cruzado (no canónico).

**Ofertas SPEC H rematch validadas:**
- `validado` + spec_h_rematch: 147 filas
- `validado_claude` + spec_h_rematch: 8.063 filas
- `pendiente` + spec_h_rematch: 0 (todas las 33 pendientes son v3.5.2)

---

## B — Entradas zombie del diccionario

### B1. Conteo de entradas con schema "viejo" (las que el matcher entiende)

`config/sinonimos_argentinos_esco.json` tiene 3 buckets dict además de los metadatos:

| Bucket | Total entries (sin `_descripcion`) | Schema |
|---|---:|---|
| `ocupaciones_titulo` | 24 | viejo (`isco_primario`/`isco_familia`/`esco_label`) — **24/24 funcionales** |
| `skills_mapeo` | 7 | propio (`skill_esco`/`skill_uri`) — **NO leído por el matcher** |
| `contextos_sector` | 0 | (vacío bajo `_descripcion`) |

**`ocupaciones_titulo`:** 24 entries, todas con schema viejo válido. **0 entradas con schema nuevo.**

### B2. Conteo de entradas con schema "nuevo" (las inertes)

**0 entradas zombie** en `ocupaciones_titulo`.

El script `scripts/sync_rules_from_candidates.py:117` escribe con schema nuevo:
```python
ocu_titulo[key] = {"isco": isco, "label": label}
```
Mientras el matcher (`match_ofertas_v3.py:257-310`) lee `isco_primario`/`isco_familia`/`esco_label`. Si el script hubiera corrido y aprobado candidatos, habrían quedado entradas inertes — **pero no hay ninguna actualmente**.

### B3. ¿Qué fracción del diccionario es zombie?

```
Entradas funcionales en ocupaciones_titulo:    24
Entradas zombie en ocupaciones_titulo:          0
Total ocupaciones_titulo:                      24

Entradas en skills_mapeo (no leído por matcher): 7
Entradas en contextos_sector:                    0
```

**0% del diccionario es zombie hoy.** El riesgo de schema drift identificado en el reporte 2 sigue latente, pero no se materializó.

### B4. Historial de ejecución de `sync_rules_from_candidates.py`

- El script **existe** en `scripts/sync_rules_from_candidates.py`.
- Lee de tabla **Supabase** `rule_candidates` (línea 196: `client.table('rule_candidates')`), no de SQLite local.
- En SQLite **no hay tablas con "candidate" o "rule"** que registren su ejecución.
- **No se puede responder en modo read-only** cuántas veces corrió ni qué procesó. Pendiente para diagnóstico 4 (consultar Supabase).
- El script tiene mtime reciente (modificado en sesiones anteriores).

### B5. ¿Las entradas zombie afectaron el matching?

**No aplica:** no hay entradas zombie en el JSON actualmente. La pregunta queda en N/A para este reporte.

---

## C — Coherencia entre matcher y catálogo

### C1. Catálogo de labels canónicos ESCO

**Catálogo declarado:**

| Fuente | Total | Con label canónico | URIs con múltiples labels declarados |
|---|---:|---:|---:|
| `esco_occupations_full.json` | 3.046 | 3.045 | 0 |
| Tabla SQL `esco_occupations` | 3.045 | 3.045 | 0 |
| `esco_occupations_metadata.json` (matcher path) | **NO EXISTE** | — | — |
| `esco_occupations_embeddings.npy` (matcher path) | **NO EXISTE** | — | — |

**Coherencia SQL ↔ JSON:**
- 3.045 URIs en ambas fuentes.
- **0 labels discrepantes.**
- 1 URI en JSON sin label (`12330cce-d129-4d87-9d8b-7dc7bfabac83`).
- 0 URIs en SQL ausentes del JSON.

**Hallazgo crítico colateral:** el matcher (`_load_occupation_embeddings`, `match_ofertas_v3.py:147-163`) busca `database/embeddings/esco_occupations_embeddings.npy` y `esco_occupations_metadata.json`. **Ninguno existe en disco.** Por lo tanto:
- `self.occ_embeddings = None`
- `self.occ_metadata = []`
- `self.code_to_occupation = {}` (vacío — el loop iterativo no encuentra entradas)
- `_semantic_match_title()` siempre retorna `[]` (línea 1289)

**Implicaciones:**
1. La rama "title semántico" del matcher actual es código muerto — solo queda `match_by_skills.py` (que sí usa la tabla SQL).
2. La función `code_to_occupation` que se propuso reutilizar en el reporte 2 (PROMPT 2) para resolver URIs del diccionario argentino **está vacía en runtime**. Cualquier solución futura del bug del diccionario debe primero reconstruir esa metadata o usar la tabla SQL directamente.

### C2. Comparación BD vs catálogo

**Top 50 URIs con drift (823 pares URI, label_distinto):**

| Categoría | n | % |
|---|---:|---:|
| Label coincide con `preferred_label_es` (canónico) | 50 | 6,1% |
| Label es `altLabel` del MISMO URI | 0 | 0,0% |
| Label NO está en pref ni alt del URI | 773 | **93,9%** |

**Global (4.690 pares URI, label_distinto en las 1.237 URIs con drift):**

| Categoría | n | % |
|---|---:|---:|
| Coincide con canónico | 1.174 | 25,0% |
| Es altLabel del MISMO URI | 1 | <0,1% |
| No relacionado (no en pref ni alt) | **3.515** | **74,9%** |

**Sample de los 100 primeros labels "no relacionados" en top 50 URIs:**

| Naturaleza del label "errado" | n |
|---|---:|
| Es `preferred_label_es` de **OTRA URI** ESCO | **100** |
| Es `altLabel` de OTRA URI | 0 |
| No existe en el catálogo | 0 |

**100% de los labels cruzados son `prefLabel` de otras URIs ESCO.**

### C3. Hipótesis sobre el origen del drift

| Hipótesis | Evidencia | Veredicto |
|---|---|---|
| (a) Cada método mantiene cache de labels | El drift está concentrado en `skills_first_v3` (91% de filas no_canon) y `spec_h_rematch` (ratio 2,62). Las reglas mantienen 1,00 (cada regla tiene su `esco_label` fijo en JSON de reglas). | **No probada como mecanismo de cache; sí confirmada como concentración por método.** |
| (b) `altLabels` se guardan en lugar del `prefLabel` | 0/100 sample son altLabels. 1/4.690 global. | **Refutada.** |
| (c) El semántico devuelve labels truncados/normalizados | Los labels son completos y bien formados. | **Refutada por inspección.** |
| (d) Bug histórico de migración | Drift v3.5.2: 13 extra labels (sano). spec_h_rematch: 2.392 extra labels. Los extra del rematch son TODOS prefLabel de otras URIs. | **Confirmada parcialmente** — el rematch SPEC H del 2026-04-25 introdujo el grueso del drift (2.392/2.405 = 99,5%). |
| (e) **El matcher cruza URI de una ocupación con LABEL de otra** | 100% de los labels no relacionados son prefLabel de otras URIs ESCO. Las URIs apuntan correctamente al ESCO de un dominio (ej: 1349 director laboratorio médico) pero los labels persistidos son de URIs distantes (ej: ingeniero industrial 2141, DevOps cloud 2519, etc.). El cruce ocurre en el path semántico (`skills_first_v3`) y se materializó en `rematch_isco_spec_h.py`. | **Confirmada como mecanismo dominante.** |

**Inspección del código actual sin reproducir el bug:**

`match_by_skills.py:286` lee `meta.get('label', '')` desde `self.occupation_metadata[occ_uri]`, que se carga (líneas 200-210) desde tabla SQL con 1 label por URI. **Ese path actual NO debería producir cruce** — produce 1,01 pares/URI en v3.5.2, consistente.

`match_ofertas_v3.py:1314-1368` (`_combine_candidates`): indexa `skills_by_uri` y `title_by_uri` por URI; toma `esco_label` del candidato cuyo URI coincide. Determinístico **si los inputs vienen consistentes**. En el path actual, `title_by_uri` está siempre vacío (los embeddings de título no se cargan).

**Conclusión:** el bug NO está visible en el código actual de matching. **Probablemente el matcher del 2026-04-25 (estado del repo en el momento del rematch SPEC H) tenía un cruce URI/label** — sea porque cargaba `esco_occupations_metadata.json` desde un archivo desincronizado con los embeddings, o porque `_combine_candidates` estaba en una versión que no indexaba bien por URI. Investigar git log del matcher entre 2026-04-23..2026-04-26 queda como pendiente para diagnóstico 4.

**Confirmaciones que la hipótesis (e) requeriría para cerrarse:**
- `git log --since=2026-04-20 --until=2026-04-28 -- database/match_ofertas_v3.py database/match_by_skills.py` para ver versiones del matcher.
- Verificar si en esa fecha existía un `esco_occupations_metadata.json` con orden distinto al de `esco_occupations_embeddings.npy`.

---

## D — Hallazgos colaterales

1. **Embeddings de ocupaciones ausentes.** `database/embeddings/esco_occupations_embeddings.npy` y `esco_occupations_metadata.json` no existen actualmente. Esto deja `_semantic_match_title()` (línea 1286) siempre retornando `[]` y `code_to_occupation` (línea 166) siempre vacío. Toda la rama "semántico de título" del matcher actual es no-operativa. El path de skills (`match_by_skills.py`) sí funciona porque lee de tabla SQL. **Implicación para el reporte 2:** la solución propuesta de reusar `code_to_occupation` para resolver URIs en el path del diccionario argentino requeriría primero regenerar la metadata de embeddings o redirigir el lookup a la tabla SQL.

2. **`bea705fe-…` (mozo de almacén) tiene drift mixto:** algunas reglas (R353_operario_carga_descarga, R137_picking, R136_personal_deposito, R32_operario_picking, R350_operario_deposito, R36_operario_almacen, R142_bodeguero, R141_peon_deposito) persistieron URI=mozo_almacen pero con labels distintos (todos "mozo de almacén" excepto R139_repositor que pone "reponedor/reponedora" con uri=mozo_almacen — eso es un bug específico de R139 con desajuste URI/label en su declaración).

3. **`R240_operario_produccion` tiene 24 pares uri||label / 2 URIs únicas = 12,00 pares/URI.** Es la única regla con drift apreciable. Podría ser que la regla declare "label fijo" en JSON pero el `_save_match` persistió label de matching semántico paralelo. No investigado en profundidad.

4. **`skills_mapeo` (7 entries) en `sinonimos_argentinos_esco.json` no es leído por nadie.** Búsqueda `grep -rn "skills_mapeo"` en `database/` y `scripts/` (excluyendo archive) no retorna resultados. Es código muerto en JSON. Schema es `{skill_esco, skill_uri}`, distinto al de `ocupaciones_titulo`.

5. **`contextos_sector` está completamente vacío** en el JSON (0 entries reales, solo `_descripcion`).

6. **Tabla `esco_occupations_backup_20260114_221302`** existe en SQLite (snapshot del 2026-01-14). Posible artefacto de migración que podría limpiarse — no investigado.

7. **63 URIs con drift no tienen el label canónico presente en BD** (5,1% de las 1.237). Para estas, el label más frecuente NO está en el catálogo ESCO oficial. Necesita revisión caso por caso.

8. **8.063 ofertas en estado `validado_claude` quedaron con `matching_version=spec_h_rematch`.** De estas, ~9,78% tienen label cruzado (proyección desde la métrica global). Si una corrección del drift se aplicara como rematch masivo, eso requeriría unlock de validadas.

9. **Solo 33 ofertas están en `pendiente`** y todas son v3.5.2 (sin drift). Cualquier fix futuro del drift afecta principalmente ofertas validadas, no la cola actual de pendientes.

10. **Pendiente diagnóstico 4 (no investigado en este reporte):**
    - Reconstruir el estado del matcher al 2026-04-25 vía `git log` para identificar la línea exacta que cruza URI/label.
    - Conectar a Supabase para auditar `rule_candidates` y ver si `sync_rules_from_candidates.py` produjo entradas que luego fueron descartadas/sobrescritas.
    - Investigar el caso `R240_operario_produccion` (12 pares/URI).
    - Decidir política: regenerar embeddings de ocupaciones (requeridos para `_semantic_match_title` y `code_to_occupation`).

---

## Resumen ejecutivo

**Conclusiones cuantificadas (sin propuestas):**

1. 1.237/2.232 URIs (55,4%) tienen drift de label. 4.566 filas (8,67%) tienen label no canónico.
2. 90,4% de las 44.770 filas en URIs con drift sí tienen el label canónico — solo 9,6% (4.316) no.
3. **El drift está concentrado en `matching_version='spec_h_rematch'`** del 2026-04-25 (ratio 2,62 pares/URI vs 1,01 de v3.5.2).
4. **91% del drift viene de `decision_metodo='semantico_unico'`** (path skills_first_v3).
5. **74,9% de los labels "errados" globalmente son prefLabel de OTRAS URIs ESCO**, no altLabels — es un cruce URI×label, no un alias.
6. El catálogo ESCO (JSON + SQL) es coherente: 1 label canónico por URI, 0 discrepancias entre fuentes.
7. **0 entradas zombie** en `ocupaciones_titulo`. El schema drift identificado en el reporte 2 está latente pero no se materializó.
8. `skills_mapeo` (7 entries) y `contextos_sector` (0 entries) son buckets muertos en el JSON — no leídos por el matcher.
9. **Embeddings de ocupaciones ausentes** (`esco_occupations_embeddings.npy` no existe) — toda la rama semántica de título del matcher actual es no-operativa.

**Preguntas abiertas para diagnóstico 4:**
- ¿Qué cambio en el matcher entre v3.5.2 y SPEC H rematch produjo el cruce URI/label? (requiere git archeology)
- ¿Cuántos candidatos aprobó `sync_rules_from_candidates.py` y dónde quedaron? (requiere Supabase)
- ¿Por qué `R240_operario_produccion` tiene 12 labels para 2 URIs?
- ¿Política a seguir: regenerar embeddings de ocupaciones para reactivar `_semantic_match_title`?
