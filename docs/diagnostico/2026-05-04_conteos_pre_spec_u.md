# Conteos pre-SPEC U

**Fecha ejecución:** 2026-05-04
**Pipeline activo durante el diagnóstico:** no
**Modo:** read-only estricto (SQLite `?mode=ro`, sin INSERT/UPDATE/DELETE, sin tocar configs)
**BD:** `database/bumeran_scraping.db` (60.237 ofertas, 56.433 con matching, 1.116.011 filas en `ofertas_esco_skills_detalle`)
**Queries no completadas:** ninguna
**Queries con bug primer intento, re-ejecutadas:** E2 (función `avg_skills` mal escrita), E3/E4 (parche posterior)

> **Nota de método:** este reporte solo cuantifica. La interpretación, las propuestas de fix y el orden de ejecución quedan para una decisión posterior. Donde un conteo contradice una afirmación del SPEC U, lo declaro como **discrepancia** sin proponer cambio al SPEC.

---

## A — Reglas sin URI

### A1. Total reglas en `config/matching_rules_business.json`

| Métrica | Valor |
|---|---|
| Estructura raíz | dict con clave `reglas_forzar_isco` (dict de 358 entries) |
| Entries con campo `accion` (=reglas reales) | **357** |
| Reglas activas (`activa: true` o ausente) | 354 |
| Reglas inactivas (`activa: false`) | 3 |

**Nota:** las reglas no tienen un campo `esco_uri` directo. Tienen `accion.esco_code` (ej `3118.3`) que el pipeline debería resolver a URI. La pregunta del prompt original asumía un campo `esco_uri`; lo reformulé en función de `esco_code` que sí existe.

### A2. Reglas sin `esco_code` (vacío/null/ausente)

| Cantidad | Listado | Motivo |
|---|---|---|
| **7** total | | |
| | R4_nivel_gerencial (activa, isco=null, label=null) | campo `esco_code` ausente |
| | R6_sector_gastronomia (activa, isco=null, label=null) | campo `esco_code` ausente |
| | R7_sector_educacion (activa, isco=null, label=null) | campo `esco_code` ausente |
| | R9_tareas_logisticas (activa, isco=null, label=null) | campo `esco_code` ausente |
| | R10_electricista_industrial (inactiva) | campo `esco_code` ausente |
| | R11_titulo_compuesto (inactiva) | campo `esco_code` ausente |
| | R314_advisor_software (inactiva, isco=2519, label='analista de pruebas') | campo `esco_code` ausente |

Reglas sin `esco_label`: 6 (overlap parcial con las 7 anteriores).

### A3. Mapeo a URI candidato — reglas SIN `esco_code`

| Mapeo | Cantidad | Detalle |
|---|---|---|
| Unívoco (1 URI) | 0 | — |
| Ambiguo (2+) | 0 | — |
| Sin mapeo (0) | **7** | 6 reglas no traen ni isco ni label (no son reglas de mapeo a ocupación, son reglas auxiliares); 1 (R314) trae isco+label pero no encuentra match en catálogo |

### A3b. Reglas CON `esco_code`: ¿se resuelven en el catálogo ESCO?

| Métrica | Valor |
|---|---|
| Total reglas con `esco_code` | 350 |
| Resolvable a URI ESCO oficial | **350 (100%)** |
| No resolvable (esco_code inexistente en catálogo) | 0 |

**Implicación:** el catálogo de reglas no tiene URIs huérfanas; el `esco_code` siempre cae en una ocupación válida del catálogo `esco_occupations_full.json`.

### A4. Concentración de las 3.762 ofertas con URI vacío

| Estado | n | % |
|---|---|---|
| Total ofertas en `ofertas_esco_matching` | 56.433 | 100% |
| Con URI vacío/null | **3.762** | 6.7% |
| De las 3.762: con `regla_aplicada` no nula | **3** | 0.1% |
| De las 3.762: sin `regla_aplicada` | **3.759** | 99.9% |

Top reglas que producen URI vacío:

| regla_aplicada | n_ofertas | esco_code en config | resoluble a URI |
|---|---|---|---|
| R81_monitoreo_alarmas | 1 | sí | sí |
| R48_secretaria_admin | 1 | sí | sí |
| R191_vendedor_autos | 1 | (regla NO está en config) | n/a |

> **Discrepancia con la hipótesis del SPEC U §F:** el diagnóstico atribuía DIAG F a "reglas que mapean a ISCO/label sin URI". Los conteos refutan esa hipótesis: solo 3 ofertas (0.1%) con URI vacío vienen del path de reglas, y 2 de esas reglas tienen `esco_code` resoluble. **El root cause real** está en el path semántico (ver Sección G — Hallazgos colaterales).

---

## B — Backfill flags `is_essential` / `is_optional`

### B1. Filas afectadas en `ofertas_esco_skills_detalle`

| Métrica | Valor |
|---|---|
| Total filas | **1.116.011** |
| `is_essential = 0 AND is_optional = 0` | 1.116.011 (100.00%) |
| Con al menos un flag = 1 | 0 (0.00%) |
| Algún flag NULL | 0 |

**La regresión es total**: ninguna fila tiene flags poblados.

### B2. Cobertura del backfill posible

| Caso | n |
|---|---|
| Skills con flags=0 y oferta padre tiene URI no vacía → **backfilleable** | **1.023.911** |
| Skills con flags=0 y oferta padre con URI vacía → bloqueado por F11+F10 | 92.100 |
| Skills con flags=0 sin oferta padre (huérfanas) | 0 |

### B3. Drift entre fuentes ESCO

| Comparación | Valor |
|---|---|
| Skills en `esco_skills_metadata_full.json` | 14.257 |
| Skills en `esco_occupation_skills.json` | 13.492 |
| En `occupation_skills` y NO en `metadata` | **0** |
| En `metadata` y NO en `occupation_skills` | 765 (skills no asociadas a ninguna ocupación, no es drift) |

**No hay drift entre los dos JSONs ESCO.**

### B4. Tabla `esco_associations` en BD

| Métrica | Valor |
|---|---|
| Existe | **sí** |
| Filas | **129.004** |
| relation_type='essential' | 67.622 |
| relation_type='optional' | 61.382 |
| Ocupaciones distintas | 3.039 (de 3.046 del catálogo) |
| Skills distintas | 13.492 |
| Total pairs en `esco_occupation_skills.json` | 129.004 |
| **Diff BD vs JSON** | **0** (cobertura completa) |

**La tabla `esco_associations` está completamente sincronizada con el JSON canónico.** Sirve directamente como fuente de verdad para el backfill F1.

---

## C — Tests / `save_skills_detalle` / call sites

### C1. Tests que mencionan la función o tabla

| Archivo | save_skills_detalle | ofertas_esco_skills_detalle | is_essential_for_occupation |
|---|---|---|---|
| `tests/test_m01_sync_learnings.py` | 0 | 5 | 0 |
| `tests/test_m06_integration.py` | 0 | 1 | 0 |
| `tests/test_m08b_candidates.py` | 0 | 8 | 0 |
| `tests/test_m08b_texto_original.py` | **4** | 6 | 0 |
| `tests/matching/test_gold_set_manual.py` | 0 | 1 | 0 |

**Solo 1 archivo invoca `save_skills_detalle` directamente** (test_m08b_texto_original) y **0 tests en todo el repo verifican `is_essential_for_occupation`**.

### C2. Diferencia de columnas INSERT (vieja vs actual)

**INSERT viejo** (`archive_old_versions/pipelines_old/populate_skills_detalle_v83.py`), 12 columnas:
```
id_oferta, skill_mencionado, skill_tipo_fuente,
esco_skill_uri, esco_skill_label, esco_skill_type,
esco_skill_reusability, is_essential_for_occupation,
is_optional_for_occupation, source_classification,
match_method, match_score
```

**INSERT actual** (`database/match_ofertas_v3.py:1566-1590`), 10 columnas:
```
id_oferta, skill_mencionado, skill_tipo_fuente,
esco_skill_uri, esco_skill_label, match_score, match_method,
esco_skill_type, source_classification, texto_original
```

| Cambio | Columnas |
|---|---|
| **Eliminadas en regresión** | `esco_skill_reusability`, `is_essential_for_occupation`, `is_optional_for_occupation` |
| Agregadas | `texto_original` |

### C3. Call sites de `save_skills_detalle`

| Archivo | Línea | Línea de código |
|---|---|---|
| `database/match_ofertas_v3.py` | **1788** | `self.save_skills_detalle(id_oferta, skills_to_save)` |
| `tests/test_m08b_texto_original.py` | 56, 80, 102, 125 | `matcher.save_skills_detalle("OF_xxx", skills)` |

**Único call site en pipeline:** línea 1788 de `match_ofertas_v3.py`. La línea 1785 inmediatamente anterior llama a `save_matching_result(id_oferta, result, run_id=run_id)`. **El `result` contiene la URI de la ocupación**, pero no se está pasando a `save_skills_detalle`. Para el fix se necesita modificar la firma a `save_skills_detalle(self, id_oferta, skills, occupation_uri=None)` y pasar `result.get('esco_occupation_uri')`.

---

## D — Validaciones humanas históricas

### D1. Distribución por estado de validación

| estado_validacion | n | % |
|---|---|---|
| validado_claude | 49.071 | 87.0% |
| **validado** | **7.326** | 13.0% |
| pendiente | 36 | 0.1% |
| **Total** | 56.433 | 100% |

**Otras tablas de validación:**
| Tabla | Filas |
|---|---|
| `validacion_humana` | **0** (no se está usando) |
| `validacion_historial` | 9.745 (cambios de estado) |
| `validacion_v7` | 121 (NLP v7, antiguo) |
| `validacion_pipeline` | 3 |
| `validacion_incremental` | 2 |
| `validacion_campos` | 0 |

### D2. Distribución temporal y de origen de las "validaciones humanas"

**Por mes** (estado=validado):
| Mes | n |
|---|---|
| 2026-02 | 7.326 (todas) |

**Por validador** (estado=validado):
| validado_por | n | % |
|---|---|---|
| `claude_bulk` | 6.847 | 93.5% |
| `claude_bulk_fix1` | 475 | 6.5% |
| `manual` | **4** | 0.05% |

**Por matching_version** (estado=validado):
| matching_version | n |
|---|---|
| 3.5.2 | 7.179 |
| spec_h_rematch | 147 |

**Cambios de estado en `validacion_historial`:**

| Transición | n |
|---|---|
| pendiente → validado | 8.251 |
| pendiente → validado_claude | 1.388 |
| NULL → en_revision | 100 |
| validado → en_revision | 6 |

**Por usuario en `validacion_historial`:**
| usuario | n |
|---|---|
| claude_bulk | 7.728 |
| claude_auto_batch | 1.000 |
| claude_bulk_fix1 | 478 |
| claude | 394 |
| sistema | 100 |
| **gerardo** | **37** |
| manual | 8 |

> **Discrepancia con la asunción del SPEC U §9.4 ("no romper validaciones humanas históricas"):** los 7.326 estados=`validado` son **etiquetas que puso Claude en bulk**, no validaciones humanas reales. Las validaciones realmente humanas suman **~50** (37 `gerardo` + 8 `manual` + 4 `manual` + algunos cruzados). Esto cambia drásticamente el peso de "preservar lo humano" en cualquier decisión de re-procesamiento.

### D3. ¿Qué validaron exactamente?

La tabla `ofertas_esco_matching` **no tiene un campo `validated_field`**. "Validación humana" en el código operativo significa que `estado_validacion = 'validado'` (vs `'validado_claude'`).

Heurística sobre los 7.326 `validado`:
| Característica | n |
|---|---|
| Con `regla_aplicada` no nula | 3.962 |
| Sin `regla_aplicada` | 3.364 |
| Con `notas_revision` no nula | **0** |

**Cero notas en los 7.326.** No hay rastro de qué se evaluó en cada caso. `validacion_v7` tiene 121 filas (NLP v7 — irrelevante para matching v3.5.4) con 1 aprobado, 1 corregido, 119 pendientes.

---

## E — Cola larga del extractor (DIAG E)

### E1. Distribución skills por oferta

| Métrica | Valor |
|---|---|
| Ofertas con ≥1 skill | 54.557 |
| Total skills extraídas | 1.116.011 |
| Promedio | 20.5 |
| Mediana | 20 |
| P25 | 14 |
| P75 | 26 |
| P90 | 33 |
| P95 | 38 |
| P99 | 52 |
| Máximo | 117 (id_oferta=8563055837) |

### E2. Longitud descripción vs skills/oferta

| Bucket descripción | n ofertas | mean skills | median skills | max |
|---|---|---|---|---|
| Short (<500 chars) | 7.568 | 8.1 | 5 | 59 |
| Medio (500–2000) | 36.311 | 18.4 | 18 | 83 |
| Largo (>2000) | 16.358 | 23.5 | 23 | 117 |

**Correlación Pearson** longitud_descripcion vs skills_extraídas: **r = 0.265** (débil-moderada).

### E3. Skills con frecuencia ≥ 1.000

| Métrica | Valor |
|---|---|
| Skills con n ≥ 1.000 | **155** |

**Top 10 (por n_apariciones):**
| skill_label | n | n_ocupaciones distintas | L1 |
|---|---|---|---|
| ocuparse de la orientación al cliente | 5.776 | 541 | (NULL) |
| gestionar el inventario | 5.655 | 527 | (NULL) |
| trabajar en equipo | 5.616 | 844 | (NULL) |
| controlar existencias | 5.568 | 527 | (NULL) |
| analizar problemas para buscar soluciones | 5.015 | 707 | (NULL) |
| animar a los equipos de trabajo | 4.861 | 711 | (NULL) |
| identificar acciones de mejora | 4.661 | 597 | (NULL) |
| hacer recomendaciones de reparaciones | 4.038 | 608 | (NULL) |
| crear un espíritu de equipo | 3.267 | 614 | (NULL) |
| mantener sistemas de control de las existencias | 3.223 | 360 | T3 |

Distribución L1 entre las 155 frecuentes:
| L1 valor exacto | n |
|---|---|
| (NULL) | 154 |
| K | 1 |
| Otros (T1/T2/T3/T4/T5/T6/S1/S2/S3/S4/S5/S6/S7/S8) | 0 |

> **Hallazgo colateral:** el campo `L1` viene en formato compuesto en el catálogo (ej `T4`, `S1`, `K`). De las 14.257 skills del catálogo, solo 327 tienen L1=NULL. Pero **154 de las 155 skills más frecuentes en MOL tienen L1=NULL** — es una sobre-representación brutal de skills sin clasificación L1. Ver Sección G.

### E4. Skills con frecuencia = 1

| Métrica | Valor |
|---|---|
| Total skills con n=1 | **963** |
| URIs válidas (en `esco_skills_metadata_full.json`) | **963 (100%)** |
| URIs no en catálogo | 0 |

**Cero URIs inventadas en la cola larga.** Todas son ESCO válidas, solo apariciones únicas.

### E4b. Filas con URI presente pero sin label

| Métrica | Valor | SPEC U estimaba |
|---|---|---|
| Filas sin URI | 0 | — |
| Filas sin label | 8.452 | — |
| Filas con URI pero sin label | **8.452** | 7.254 (DIAG D) |
| Filas sin URI ni label | 0 | — |

> **Discrepancia con SPEC U §D:** el conteo real es **8.452, no 7.254**. Sample muestra que las URIs vacías-de-label son válidas en el catálogo pero el `label` está vacío también en `esco_skills_metadata_full.json`. Es problema upstream en la extracción del RDF, no en el pipeline MOL.

### E (extra). Distribución por OCUPACIÓN — el ratio MOL/ESCO real

| Métrica | Valor |
|---|---|
| Ocupaciones MOL con ≥1 oferta | 2.162 |
| Skills únicas/ocupación — promedio | 156 |
| Skills únicas/ocupación — mediana | 55 |
| Skills únicas/ocupación — P75 | 128 |
| Skills únicas/ocupación — P90 | 315 |
| Skills únicas/ocupación — P99 | 1.903 |
| Skills únicas/ocupación — máximo | 4.115 |

**Ratio MOL/ESCO en las 2.161 ocupaciones con catálogo ESCO disponible:**
| Métrica | Valor |
|---|---|
| Promedio | 3.5× |
| **Mediana** | **1.3×** |
| P90 | 7.1× |
| P99 | 42.3× |

**Top 10 ratio (ocupaciones más infladas, todas con muchas ofertas):**
| esco_uri (sufijo) | MOL | ESCO catálogo | Ratio | Ofertas |
|---|---|---|---|---|
| 245be6d1-fe9a-... | 3.274 | 24 | 136.4× | 1.012 |
| bafbc672-0ad9-... | 2.084 | 24 | 86.8× | 967 |
| 22987b58-dbfa-... | 2.255 | 27 | 83.5× | 417 |
| 264b00c9-84d0-... | 2.006 | 29 | 69.2× | 565 |
| 0c408028-c48f-... | 2.306 | 34 | 67.8× | 615 |

> **Discrepancia con SPEC U §E ("10-50× más skills que el catálogo"):** la afirmación se cumple solo para el top decil cuando hay muchas ofertas. La **mediana de la distribución es 1.3×** (cerca del 1× ideal). El "ratio brutal" se da en ~200 ocupaciones con muchas ofertas y label genérico.

---

## F — Gold Sets

### F1. Archivos detectados

12 archivos, 5 con casos válidos y `id_oferta` parseable:

| Archivo | Casos | Schema (campos primer caso) | Activo |
|---|---|---|---|
| `database/gold_set_manual_v2.json` | 49 | id_oferta, esco_ok, comentario, skills_esperadas | sí |
| `tests/matching/gold_set.json` | 49 | id_oferta, esco_ok, comentario | sí (idéntico contenido al anterior) |
| `tests/nlp/gold_set.json` | 49 | id_oferta, titulo_original, nlp_version, expected, verified, notes | sí |
| `exports/matching_v3_gold_set_100.json` | 100 | id, titulo, isco, esco, score | export |
| `archive/database_debris/gold_set_candidates.json` | 31 | id_oferta, esco_label, isco_code, isco_label, score, esco_ok, tipo_error, comentario | archivo |
| `archive/database_debris/gold_set_candidates_validated.json` | 31 | id_oferta, esco_ok, tipo_error, comentario | archivo |
| `archive/database_debris/gold_set_manual_v1.json` | 19 | id_oferta, esco_ok, comentario | archivo |

Otros 5 archivos sin `id_oferta` parseable o sin estructura tabular.

### F2. Solapamiento entre Gold Sets activos

| Cruce | n IDs compartidos |
|---|---|
| `gold_set_manual_v2` ∩ `tests/matching/gold_set` | 49 (idénticos) |
| `gold_set_manual_v2` ∩ `tests/nlp/gold_set` | 49 (idénticos) |
| `gold_set_manual_v2` ∩ `matching_v3_gold_set_100` | 49 (subset completo) |
| `matching_v3_gold_set_100` extra (no en v2) | 51 |

**Núcleo común:** los 49 IDs históricos de `gold_set_manual_v2` están replicados en 4 archivos. El gold set de 100 es una expansión del de 49.

### F3. Cobertura ISCOs Diego en cada Gold Set

| Gold Set | Total | ISCOs únicos | 3322 RC | 5223 Vendedor | 4110 Empleado of. | 2512 Dev SW |
|---|---|---|---|---|---|---|
| `gold_set_manual_v2.json` (49) | 49 | 15 | 2 | 0 | **0** | 1 |
| `matching_v3_gold_set_100.json` (100) | 100 | 55 | 11 | 3 | **0** | 3 |
| `archive/...gold_set_candidates.json` (31) | 31 | 26 | 1 | 2 | **0** | 0 |

> **ISCO 4110 (Empleado de oficina) no aparece en NINGÚN Gold Set activo ni archivado.** Las otras 3 ocupaciones de Diego están cubiertas con al menos 1 caso, pero `4110` está completamente fuera del Gold Set de regresión.

---

## G — Hallazgos colaterales (sin propuestas de fix)

### G1. Root cause real de las 3.759 ofertas con URI vacío

Las ofertas se distribuyen así por `decision_metodo` × `occupation_match_method`:

| decision_metodo | match_method | n |
|---|---|---|
| `semantico_unico` | `diccionario_argentino_administrativo` | 2.155 |
| `semantico_unico` | `diccionario_argentino_vendedor` | 492 |
| `semantico_unico` | `diccionario_argentino_analista` | 354 |
| `semantico_unico` | `diccionario_argentino_gerente` | 302 |
| `semantico_unico` | `diccionario_argentino_operario` | 156 |
| `semantico_unico` | `diccionario_argentino_operador` | 144 |
| `semantico_unico` | `diccionario_argentino_tecnico` | 104 |
| `semantico_unico` | otros `diccionario_argentino_*` | 49 |
| `error` | `no_match` | 3 |
| otros (regla_manual_fix, dual_coinciden, etc.) | varios | ~5 |

**El path "diccionario argentino" del matcher v3.5.4** mapea a `isco_code` + `esco_occupation_label` pero **no resuelve `esco_occupation_uri`**. ~99% de las URIs vacías vienen de ahí, no de reglas de negocio.

### G2. Estado de validación de las URIs vacías

| Estado | n |
|---|---|
| pendiente | 3 |
| validado | 904 |
| validado_claude | 2.855 |

Casi todas estas ofertas están "validadas". La validación bulk no detectó la URI vacía como problema.

### G3. Tablas de backup que probablemente no estén siendo usadas

Detectadas durante inspección:
- `esco_associations_backup_20260114_221302`
- `ofertas_esco_matching_backup_20260103_135227`
- `ofertas_matching_backup_spec_h`
- `ofertas_nlp_backup_20251214_181750`
- `ofertas_nlp_backup_oldversions_20260103_140824`
- `skills_semantico_json_backup_spec_e`
- `_clae_snapshot_before`
- `ab_snapshot_matching`, `ab_snapshot_nlp`, `ab_snapshot_skills`

Sin verificar tamaño ni si están desactualizadas. Posible candidato a limpieza pero fuera de alcance de SPEC U.

### G4. Coverage L1 NULL

De las 155 skills más frecuentes (n≥1000) en `ofertas_esco_skills_detalle`, **154 tienen `L1=NULL`** en `esco_skills_metadata_full.json`. En el catálogo total solo 327 de 14.257 (2.3%) tienen L1=NULL. El extractor está sesgado fuertemente hacia skills sin L1 — esto puede explicar parte del DIAG E y por qué el ranking del dashboard ve labels genéricos arriba.

### G5. Ofertas en BD que no están en `ofertas_esco_matching`

| Métrica | Valor |
|---|---|
| Total `ofertas` | 60.237 |
| Total `ofertas_esco_matching` | 56.433 |
| Diferencia | 3.804 ofertas sin matching |

(No se profundizó si son ofertas en estados intermedios, sin NLP, o con error.)

### G6. Ningún test verifica los flags `is_essential_for_occupation` / `is_optional_for_occupation`

`tests/test_m08b_texto_original.py` invoca `save_skills_detalle` 4 veces pero solo verifica `texto_original` y campos básicos. **Si la regresión hubiera ocurrido con un test pasando, el test no habría fallado.** La pérdida de los flags no fue detectada porque no había red de seguridad para esos campos.

---

**Fin del reporte.** Sin commit a repo.
