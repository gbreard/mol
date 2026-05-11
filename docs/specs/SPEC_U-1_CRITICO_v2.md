# SPEC U-1 — Crítico: datos producto-visibles (v2)

**Versión:** 2.0
**Fecha:** 2026-05-05
**Autor:** Gerardo + Claude
**Estado:** Borrador para revisión final
**Predecesor inmediato:** SPEC U-1 v1.0 (2026-05-04)
**Diagnóstico base:** SPEC U original (`2026-04-29_U_diagnostico_codificaciones_mol.md`)
**Reportes que sustentan este SPEC:**
- R1: `2026-05-04_conteos_pre_spec_u.md`
- R2: `2026-05-04_conteos_2_diccionario_argentino.md`
- R3: `2026-05-04_conteos_3_label_drift_y_zombies.md`
- R4: `2026-05-04_conteos_4_consolidado.md`
- R5: `2026-05-04_conteos_5_bge_scraping.md`
- R6: `2026-05-04_conteos_6_supabase_nlp_uris.md`
- R7: `2026-05-04_conteos_7_bug_semantico_uri_vacia.md` (corrige causa raíz de C2)
- R8: `2026-05-04_conteos_8_fallback_isco_familia.md` (define estrategia híbrida de C2)

---

## Cambios respecto a v1.0

1. **Causa raíz de C2 corregida** (R7): la falla está en `match_ofertas_v3.py:587-594` (rama `if dict_match:` no setea `semantic_uri`), confirmado para 3.758 ofertas (100% diccionario). Universo: 3.758, no 3.762.
2. **Estrategia híbrida en C2** (R8): tres entradas se eliminan (analista/operario/tecnico, cobertura ≥99% por reglas), dos se conservan con URI por contexto (gerente/operador, cobertura ≤70%). Las 17 entradas con `isco_primario` reciben URI hardcoded.
3. **Resolución de URIs vía lookup automático**: Claude Code genera el JSON enriquecido consultando `esco_occupations` (no hay decisiones manuales).
4. **C3 ya no es prerequisito de C2** (R7): pueden ejecutarse en paralelo.
5. **Verificación previa obligatoria** antes de eliminar 3 entradas: muestra de 50 ofertas por entrada para validar que las reglas no over-matchean (sospecha en R348, R238, R87 según R8).
6. **Estimación total revisada**: 26-42h trabajo activo + cómputo + 3 días calendario.

---

## 1. Propósito y alcance

**Propósito:** corregir los bugs que producen datos visibles incorrectos al usuario del MOL (analistas OEDE, dashboard Skill Intelligence, validadores de Cynthia) y que bloquean la implementación de cualquier fix posterior.

**Alcance:** F0 + C1 + C2 + C3 + C4 + C5 + F-meta. Todo lo demás queda fuera de este SPEC.

**Fuera de alcance:**
- Anti-alucinación NLP, sesgos del LLM (`semisenior=49%`), regresiones de scrapers (ZonaJobs, ComputRabajo) → SPEC U-2
- Tablas zombies, schema mismatch, performance (`id_oferta` TEXT vs INTEGER) → SPEC U-3
- LoRA fine-tuning → diferido hasta sistema limpio
- VPS embed-server → issue separado fuera de los SPECs
- Errores de clasificación preexistentes (Arquitecto Director → TIC, etc.) → fase 2 post-SPEC con datos
- Re-validación humana de las 8.210 ofertas desvalidadas → coordinación operativa con Cynthia, no técnica

---

## 2. Contexto y evidencia consolidada

Los 8 reportes confirmaron 5 problemas que producen datos incorrectos visibles al usuario y se refuerzan entre sí:

**1. Bug del cruce URI×label** (R3 §E1, R4 §A2). Commit `94f0d73c` (2026-04-25 16:46) en `rematch_isco_spec_h.py` introdujo un UPDATE incompleto: escribía 9 columnas dejando `esco_occupation_uri`, `regla_aplicada`, `isco_label` y otras 5 con valores stale. Ventana del bug: 24h hasta el fix `7aeb16a3` (2026-04-26 17:39). Resultado: 4.203 ofertas con cruce, 1.237 URIs con drift, hasta 41 labels distintos para una sola URI.

**2. Bug del diccionario argentino** (R7 confirmó causa raíz). En `match_ofertas_v3.py:587-594`, cuando el diccionario matchea, la rama `if dict_match:` no asigna `semantic_uri`. Variable persiste con su default `""`. Resultado: **3.758 ofertas con `esco_occupation_uri = ''`**, 100% del diccionario argentino. No es regresión — es feature que nunca se construyó. Bug estructural desde v3.5.x (febrero 2026), no relacionado con SPEC H.

**3. Embeddings de ocupaciones borrados** (R4 §A3). Commit `25828fbf` (2026-04-24 22:45) destrackeó los archivos **1 minuto después** de promoverlos a producción. Quedaron en `database/embeddings/enriched/` pero el matcher los busca en raíz. Resultado: `_semantic_match_title()` retorna `[]` siempre, `code_to_occupation = {}` siempre. SPEC J nominalmente activo pero efectivamente apagado. 12.231 ofertas (20% del matching actual) procesadas post-destrackeo.

**4. Regresión de flags ESCO (DIAG A)** (R1 §B1). Al refactorizar a v3.5.4, se eliminó la lógica que poblaba `is_essential_for_occupation` e `is_optional_for_occupation`. Resultado: 1.116.011 filas con flags en cero (100% de la tabla). Imposible filtrar skills esenciales vs opcionales en el dashboard, métricas de cobertura ESCO devuelven 0/0/0.

**5. Sin sync automático a Supabase + zombies** (R6 §B1, R6 §B2). No existe cron de `sync_to_supabase.py`. Última corrida manual: 2026-04-28. Drift: −8.420 ofertas (esperable) y **+28.395 skills zombies en Supabase** (re-sync hace `delete + insert` solo de las ofertas del sync actual; skills de ofertas borradas localmente quedan zombies). Vercel lee directo de Supabase sin caché → drift se refleja al usuario en tiempo real.

**Estos 5 problemas son producto-visibles**, lo que significa: dashboards muestran labels cruzados, conteos inflados, ofertas con URI vacía; filtros por skill esencial/opcional no funcionan; datos del dashboard tienen 6 días de retraso; mejoras downstream (M-08b, OE matching persona→oferta) heredan estos problemas.

---

## 3. Fix F0 — Snapshot BD + canarios SQL

**Esfuerzo estimado:** 1–2 horas
**Bloquea:** todos los fixes posteriores
**Tipo:** precondición operativa

### 3.1 Problema

Los reportes 1-8 demostraron un patrón recurrente: refactors silenciosos introducen regresiones que solo se detectan meses después por reporte humano (Diego). Sin snapshots ni canarios, cualquier fix de este SPEC puede introducir nueva regresión sin detección automática.

### 3.2 Acción

Antes de ejecutar cualquier otro fix:
- Snapshot completo de SQLite local: dump SQL gzip a `data/snapshots/pre_spec_u1_v2_YYYYMMDD_HHMMSS.sql.gz` (~700 MB-1 GB esperados según R8 G).
- Snapshot de tablas críticas en Supabase: export JSON de `ofertas_dashboard`, `ofertas_skills`, `issues`, `rule_candidates`, `validacion_humana`.
- Crear archivo `scripts/canarios/canarios_spec_u1.sql` con 5 queries:
  - C-Q1: Cantidad de ofertas con `esco_occupation_uri = ''` (baseline esperado: 3.758)
  - C-Q2: Cantidad de filas en `ofertas_esco_skills_detalle` con `is_essential_for_occupation = 0 AND is_optional_for_occupation = 0` (baseline: 1.116.011)
  - C-Q3: Cantidad de URIs con drift de labels (>1 label distinto por URI) (baseline: 1.237)
  - C-Q4: Cantidad de skills zombies en Supabase (baseline: 28.395)
  - C-Q5: Diff Local↔Supabase de `ofertas_dashboard` (baseline: −8.420)
- Configurar cron horario que corre los canarios y escribe a `logs/canarios_YYYYMMDD.log`.
- Umbrales de alarma:
  - C-Q1: drift > +5% del baseline → alarmar
  - C-Q2: drift > +1% → alarmar (debe bajar drásticamente con C4, no subir)
  - C-Q3: drift > +5% → alarmar
  - C-Q4: drift > +10% → alarmar
  - C-Q5: drift > ±20% → alarmar

### 3.3 Criterios de éxito

- Snapshot SQL existe, comprimido, restaurable (test: restore a BD temporal y comparar count de filas).
- Canarios corriendo cada hora con valores baseline registrados en `docs/diagnostico/baseline_canarios_post_F0.md`.
- Los 5 valores baseline coinciden con los conteos esperados.

### 3.4 Riesgos y rollback

- **Riesgo:** snapshot grande (~700 MB-1 GB). Mitigación: gzip, descartar tablas zombie identificadas en R6 G1.
- **Rollback:** N/A. F0 no modifica nada.

---

## 4. Fix C1 — Bug del cruce URI×label

**Esfuerzo estimado:** 4–6 horas + 2-7 horas de cómputo no atendido para re-rematch
**Depende de:** F0
**Tipo:** corrección de datos

### 4.1 Problema

1.237 URIs en `ofertas_esco_matching` aparecen con más de un label distinto. Ejemplo: la URI `7235d075-...` (canónicamente "mozo de almacén/moza de almacén") aparece en BD con 24 labels distintos: "soldador/soldadora", "operario de prensado de fruta", "mecánico de maquinaria industrial", etc.

### 4.2 Root cause

Commit `94f0d73c` introdujo un UPDATE incompleto en `scripts/embeddings/rematch_isco_spec_h.py:persist_matching_result()`. Versión buggy escribía 9 columnas; fix `7aeb16a3` escribe 19. Las 8 columnas omitidas: `esco_occupation_uri`, `regla_aplicada`, `isco_label`, `isco_regla`, `isco_semantico`, `decision_razon`, `occupation_match_method`, `dual_coinciden`.

Cuando el rematch del 25/04 calculó nuevo match (URI = `U_new`, label = `L_new`), escribió `esco_occupation_label = L_new` pero dejó `esco_occupation_uri = U_old`. Resultado: 4.203 ofertas con cruce.

Evidencia: distribución por `matching_version` muestra ratio 2,62 labels/URI en `spec_h_rematch` vs 1,01 en v3.5.2 (sano).

### 4.3 Acción

- Identificar conjunto exacto: ofertas con `matching_version = 'spec_h_rematch'` (8.221 filas).
- **Decisión cerrada (R3, decisión 04/05):** re-rematch global con matcher arreglado, asumiendo desvalidación de las 8.210 ofertas afectadas.
- Antes del re-rematch: confirmar que el código del matcher (commit actual o posterior a `7aeb16a3`) escribe las 19 columnas correctamente.
- Ejecutar re-rematch dirigido a las 8.221 ofertas. Estimación: 1-3 segundos por oferta = 2-7 horas de cómputo.
- **No** tocar las 4.203 ofertas con drift que ya fueron sobreescritas por el path correcto post-fix; el re-rematch las cubre.

### 4.4 Criterios de éxito

- Después del re-rematch: query `SELECT COUNT(DISTINCT esco_occupation_label) FROM ofertas_esco_matching WHERE esco_occupation_uri = ?` para muestra de 50 URIs aleatorias debe devolver 1 por URI.
- C-Q3 (URIs con drift) baja de 1.237 a < 50.
- Las 63 URIs con drift donde el label canónico no está en BD (R4 §D3) reciben el label canónico.

### 4.5 Riesgos y rollback

- **Riesgo 1:** desvalida 8.210 ofertas en estado `validado_claude` o `validado`. Mitigación: aceptado por decisión 04/05. Comunicación a Cynthia/Diego (§13).
- **Riesgo 2:** si C3 no se ejecuta antes, el re-rematch usa matcher con rama título-semántico apagada. Mitigación: ejecutar **C3 antes de C1** (ver §10).
- **Rollback:** restaurar desde snapshot F0. Las 8.210 ofertas vuelven a estado pre-rematch.

---

## 5. Fix C2 — Bug del diccionario argentino (estrategia híbrida)

**Esfuerzo estimado:** 10–14 horas (incluye verificación previa, generación JSON, fix código, reprocesamiento)
**Depende de:** F0
**Independiente de:** C3 (R7 confirmó: el path del diccionario nunca pasa por `_semantic_match_title()`)
**Tipo:** corrección de código + datos

### 5.1 Problema

3.758 ofertas con `esco_occupation_uri = ''`. **100% vienen del path "diccionario argentino"** (R7 §A1). 14 variantes de `match_method = 'diccionario_argentino_*'`, ninguna escribe URI. Distribución:
- 17 entradas con `isco_primario`: ~2.694 ofertas
- 5 entradas con `isco_familia` (+ contextos): 1.064 ofertas
  - analista 357, gerente 302, operario 156, operador 145, tecnico 104

### 5.2 Root cause

**Línea exacta del bug** (R7 §B): `match_ofertas_v3.py:587-594`. La rama `if dict_match:` setea `semantic_isco`, `semantic_label`, `semantic_score`, `semantic_metodo` desde el dict del diccionario, pero NO setea `semantic_uri`. La variable persiste con su default `""` (línea 583).

Causa secundaria: `_match_by_argentino_dict()` líneas 308-314 retorna un dict que **no incluye `esco_uri`**. Aunque la rama `if` quisiera leerla, no estaría disponible.

Es bug estructural desde v3.5.x (febrero 2026), no regresión.

### 5.3 Estrategia: híbrida por entrada (R8)

**Las 17 entradas con `isco_primario`** → URI por entrada raíz (Opción 3). Lookup automático en `esco_occupations` para resolver URI desde `esco_label` o `isco_primario` con default `.1`.

**Las 5 entradas con `isco_familia` se dividen según cobertura por reglas** (R8 §E):

| Entrada | Cobertura reglas | Decisión |
|---|---:|---|
| analista | 100% | **Quitar del JSON** (Opción 1) |
| operario | 100% | **Quitar del JSON** (Opción 1) |
| tecnico | 99% | **Quitar del JSON** (Opción 1) |
| gerente | 70% | **URI por contexto** (Opción 3) |
| operador | 11% | **URI por contexto** (Opción 3) |

### 5.4 Acción

**Sub-fase A — Verificación previa de over-match (3-4 horas):**

R8 detectó sospecha de over-match en R348 (operario_plastico_soplado), R238 (analista_it), R87 (jefe_delegacion). Antes de quitar 3 entradas, validar empíricamente:

- Ejecutar matcher en muestra de 50 ofertas por entrada (analista, operario, tecnico) sin la entrada del diccionario.
- Verificar que la regla matcheada por cada oferta corresponde al título real (no es sobre-captura).
- Si over-match > 10% en alguna entrada: revisar/restringir la regla antes de quitar la entrada.
- Si over-match ≤ 10%: proceder a quitar.

Reporte de salida: `docs/diagnostico/2026-05-XX_verificacion_overmatch_C2.md` con muestra anotada y decisión por entrada.

**Sub-fase B — Generación JSON enriquecido (2 horas):**

Script Claude Code que:
- Lee `config/sinonimos_argentinos_esco.json` actual.
- Para las 17 entradas con `isco_primario`: lookup en `esco_occupations` por `(isco_code, esco_label)` → asigna `esco_uri`.
- Para `gerente` y `operador`: para cada `contexto` declarado, lookup en `esco_occupations` por `(isco_code_del_contexto, esco_label_del_contexto)` → asigna `esco_uri` al contexto.
- Para `analista`, `operario`, `tecnico`: marcar las entradas como `_deprecated: true` o eliminarlas del JSON.
- Spot-check humano: revisar 5 entradas aleatorias del JSON resultante antes de aprobar.
- Versionado: nuevo archivo `config/sinonimos_argentinos_esco_v2.json`. El v1 queda como referencia histórica.

**Sub-fase C — Fix del código (2 horas):**

En `match_ofertas_v3.py:_match_by_argentino_dict()` líneas 308-314: agregar `esco_uri` al dict retornado, leído desde la entrada del JSON v2.

En `match_ofertas_v3.py:587-594`, dentro de `if dict_match:`, agregar:
```python
semantic_uri = dict_match.get("esco_uri", "")
```

Test unitario: `_match_by_argentino_dict()` con entrada nueva escribe URI no vacía. Falla si retorna URI vacía cuando la entrada tiene URI declarada.

**Sub-fase D — Reprocesamiento (3-5 horas cómputo):**

- Las 3.758 ofertas con `esco_occupation_uri = ''` se re-procesan con matcher arreglado.
- Para las que cubrían `analista`/`operario`/`tecnico`: caen al path de reglas o semántico.
- Para las que cubrían `gerente`/`operador`: el diccionario las matchea correctamente con URI poblada.
- Para las 17 entradas `isco_primario`: el diccionario las matchea correctamente con URI poblada.

### 5.5 Criterios de éxito

- C-Q1 (ofertas con URI vacía) baja de 3.758 a < 50.
- Test unit: `_match_by_argentino_dict()` con entrada nueva escribe URI no vacía.
- Las 1.064 ofertas que matcheaban por `isco_familia` mantienen ISCO razonable post-reprocesamiento (al menos 90% conservan o mejoran su clasificación, validar contra muestra de 100).
- 17 entradas `isco_primario` con `esco_uri` poblada en el JSON v2.
- 11 contextos de `gerente` + 4 contextos de `operador` con `esco_uri` poblada.
- 3 entradas eliminadas del JSON: `analista`, `operario`, `tecnico` (si verificación previa lo aprueba).

### 5.6 Riesgos y rollback

- **Riesgo 1:** verificación previa detecta over-match alto en una entrada. Mitigación: ese caso pasa a Opción 3 (URI por contexto) en vez de quitarse.
- **Riesgo 2:** lookup automático asigna URI subóptima en casos edge. Mitigación: spot-check humano de 5 entradas del JSON resultante.
- **Riesgo 3:** las 1.064 ofertas re-procesadas pueden cambiar de ISCO. Mitigación: muestra de 100 validada; aceptado como riesgo conocido (R8 G5).
- **Riesgo 4:** errores de clasificación preexistentes (Arquitecto Director → TIC, etc.) NO se corrigen acá. Mitigación: declarado fuera de alcance, fase 2 con datos.
- **Rollback:** restaurar `sinonimos_argentinos_esco.json` desde snapshot F0. Revert del cambio de código. Las 3.758 ofertas vuelven a `esco_occupation_uri = ''`.

---

## 6. Fix C3 — Embeddings de ocupaciones borrados

**Esfuerzo estimado:** 1–2 horas
**Depende de:** F0
**Independiente de:** C2 (R7 confirmó)
**Tipo:** corrección de configuración

### 6.1 Problema

`database/embeddings/esco_occupations_embeddings.npy` y `database/embeddings/esco_occupations_metadata.json` no existen en disco. Están en `database/embeddings/enriched/` pero el matcher los busca en raíz. Resultado: `_semantic_match_title()` retorna `[]` siempre, `code_to_occupation = {}` siempre. SPEC J nominalmente activo, efectivamente apagado.

### 6.2 Root cause

Commit `25828fbf` (2026-04-24 22:45) destrackeó los archivos **1 minuto después** de promoverlos a producción (`66f922fa` 22:44). Razonamiento del commit válido (binarios autogenerados no van a git) pero el push los borró del filesystem productivo y nadie regeneró en raíz.

### 6.3 Decisión

**Opción A — Restaurar la rama** (recomendada): symlinks `database/embeddings/esco_occupations_embeddings.npy → enriched/esco_occupations_embeddings.npy` y mismo para metadata. Alternativa: cambiar el path en `match_ofertas_v3.py:147-163` para apuntar a `enriched/`.

Razones:
- Es trivial (1 línea o 2 symlinks).
- Cierra una regresión silenciosa, no la oficializa.
- C1 funciona mejor con `code_to_occupation` poblado.
- Si más adelante se decide deprecar la rama, se hace con datos.

### 6.4 Acción

- Verificar que `_load_occupation_embeddings()` y `_semantic_match_title()` existen en el código actual y son compatibles con el schema enriched (R8 detectó que el matcher usa `skills_first_v3` por defecto, no `_semantic_match_title`).
- Si compatibles: crear symlinks `database/embeddings/esco_occupations_embeddings.npy` y `esco_occupations_metadata.json` apuntando a `enriched/`.
- Verificar carga al iniciar el matcher: `code_to_occupation` poblado con 3.046 ocupaciones, `_semantic_match_title("título de ejemplo")` retorna lista no vacía.

### 6.5 Criterios de éxito

- `_load_occupation_embeddings()` carga correctamente.
- `code_to_occupation` poblado con 3.046 ocupaciones.
- `_semantic_match_title()` sobre muestra de 10 títulos retorna lista no vacía.
- Test sobre 100 ofertas con `decision_metodo = 'semantico_unico'`: el path título-semántico contribuye con score no nulo en al menos el 30% de los casos.

### 6.6 Riesgos y rollback

- **Riesgo 1:** schema-mismatch entre archivos `enriched/` (SPEC E) y código del matcher (versión antigua). Mitigación: validación previa antes de habilitar, descrita en §6.4.
- **Riesgo 2:** activar `code_to_occupation` puede cambiar comportamiento del matcher para casos donde antes caía al fallback. Mitigación: comparación A/B sobre 100 ofertas antes/después.
- **Rollback:** eliminar symlinks. El sistema vuelve al estado actual (rama título-semántico apagada).

---

## 7. Fix C4 — Regresión de flags ESCO (DIAG A)

**Esfuerzo estimado:** 30–90 minutos para el UPDATE + 1–2 horas de verificación
**Depende de:** F0, C2 (las 92.100 filas con URI vacía no son backfilleables hasta que C2 las arregle)
**Tipo:** corrección de datos

### 7.1 Problema

1.116.011 filas en `ofertas_esco_skills_detalle` tienen `is_essential_for_occupation = 0` y `is_optional_for_occupation = 0`. El cross-check ESCO no se está ejecutando. Imposible filtrar en dashboard, métricas ESCO devuelven 0/0/0.

### 7.2 Root cause

Al refactorizar el matcher a v3.5.4, se eliminó la lógica que poblaba estos flags. La función actual `match_ofertas_v3.py:save_skills_detalle()` no recibe `occupation_uri` como parámetro.

### 7.3 Acción

**Backfill UPDATE masivo** (R2 §B confirmó viabilidad):

```sql
-- Pseudo-SQL ilustrativo. Validar JOIN antes de ejecutar.
UPDATE ofertas_esco_skills_detalle
SET is_essential_for_occupation = (
  SELECT 1 FROM esco_associations ea
  WHERE ea.occupation_uri = ofertas_esco_matching.esco_occupation_uri
    AND ea.skill_uri = ofertas_esco_skills_detalle.esco_skill_uri
    AND ea.relation_type = 'essential'
),
is_optional_for_occupation = (
  SELECT 1 FROM esco_associations ea
  WHERE ea.occupation_uri = ofertas_esco_matching.esco_occupation_uri
    AND ea.skill_uri = ofertas_esco_skills_detalle.esco_skill_uri
    AND ea.relation_type = 'optional'
)
WHERE id_oferta IN (
  SELECT id_oferta FROM ofertas_esco_matching
  WHERE esco_occupation_uri != ''
);
```

- 1.023.911 filas backfilleables (post-C2: el 92.100 que era no-backfilleable ya tendrá URI).
- Estimación: 30-90 minutos con WAL activado e índices presentes.

**No incluir** en este SPEC el fix del código del matcher (re-incorporar el cross-check en el INSERT). Eso es F2 del SPEC U original y va a SPEC U-2.

### 7.4 Criterios de éxito

- Después del backfill: 1.023.911 filas con al menos un flag poblado.
- Distribución esperada (R2 §B2): 32,4% `is_essential = 1` o `is_optional = 1`, 67,6% ambos en cero (skill no en catálogo de su ocupación, legítimo).
- C-Q2 (filas con flags=0) baja de 1.116.011 a ~755.000 (67,6% del nuevo total post-C2).

**F-meta — métrica de validación nueva** (criterio de éxito del SPEC U-1 entero):

```sql
-- F-meta: cobertura ESCO por oferta
WITH oferta_cobertura AS (
  SELECT 
    om.id_oferta,
    om.esco_occupation_uri,
    SUM(CASE WHEN sd.is_essential_for_occupation = 1 
             OR sd.is_optional_for_occupation = 1
             THEN 1 ELSE 0 END) AS skills_en_catalogo
  FROM ofertas_esco_matching om
  JOIN ofertas_esco_skills_detalle sd ON om.id_oferta = sd.id_oferta
  WHERE om.esco_occupation_uri != ''
  GROUP BY om.id_oferta
)
SELECT 
  AVG(CASE WHEN skills_en_catalogo >= 1 THEN 1.0 ELSE 0.0 END) * 100 AS cobertura_K1,
  AVG(CASE WHEN skills_en_catalogo >= 3 THEN 1.0 ELSE 0.0 END) * 100 AS cobertura_K3,
  AVG(CASE WHEN skills_en_catalogo >= 5 THEN 1.0 ELSE 0.0 END) * 100 AS cobertura_K5
FROM oferta_cobertura;
```

Hoy esa query devuelve 0/0/0. **El primer valor que dé después del backfill es el baseline.** No fijar objetivo a priori. Registrar en `docs/diagnostico/baseline_cobertura_esco_K_post_C4.md`.

### 7.5 Riesgos y rollback

- **Riesgo 1:** UPDATE concurrente con pipeline activo puede generar locks. Mitigación: ejecutar con pipeline parado (ventana de mantenimiento).
- **Riesgo 2:** flags se pueblan según `esco_associations` actual. Si catálogo ESCO se actualiza después, flags quedan stale. No es problema para C4 hoy.
- **Rollback:** UPDATE inverso desde snapshot F0.

---

## 8. Fix C5 — Sync automático Supabase + limpieza zombies

**Esfuerzo estimado:** 4–6 horas
**Depende de:** F0, C1, C2, C4 (lo que se sincroniza debe estar correcto)
**Tipo:** corrección de infraestructura + datos

### 8.1 Problema

- No hay cron automático de `scripts/exports/sync_to_supabase.py`. Última corrida manual: 2026-04-28.
- Drift Local↔Supabase: −8.420 ofertas (esperable) y +28.395 skills zombies en Supabase.
- Vercel lee directo de Supabase sin caché → drift se refleja en tiempo real.
- 257 validaciones humanas reales viven solo en Supabase (riesgo si Supabase cae).

### 8.2 Root cause

- Sync diseñado como manual, nunca se cronizó.
- Re-sync hace `delete + insert` solo de las ofertas del sync actual. Skills de ofertas borradas localmente quedan zombies.

### 8.3 Acción

**Cron de sync:**
- Configurar cron diario de `sync_to_supabase.py` (03:00 AR para no chocar con scraping).
- Logs estructurados a `logs/sync_supabase_YYYYMMDD.log`.
- Notificación por email/Slack si falla.

**Limpieza de zombies en Supabase:**

Antes de la primera corrida del cron post-fixes:

```sql
-- Verificación previa: contar zombies (esperado ~28.395)
SELECT COUNT(*) FROM ofertas_skills 
WHERE id_oferta NOT IN (SELECT id_oferta FROM ofertas_dashboard);

-- Si difiere mucho de 28.395: ABORTAR y revisar.
-- Si coincide: ejecutar DELETE.

DELETE FROM ofertas_skills 
WHERE id_oferta NOT IN (SELECT id_oferta FROM ofertas_dashboard);
```

**Atención:** la decisión sobre **qué se considera zombie** requiere claridad. Si en Supabase hay ofertas que existen ahí pero no en local porque están en optimización, sus skills también se borrarían. Antes del DELETE, validar que `ofertas_dashboard` Supabase coincide con el universo de ofertas válidas (no solo las locales).

**Fix del re-sync para que purgue al sincronizar:**
- Modificar `sync_to_supabase.py` para que el delete cubra todas las skills cuyas ofertas no están en el sync actual.
- Test de regresión: si una oferta se borra localmente, sus skills se borran en Supabase en la siguiente corrida del cron.

### 8.4 Criterios de éxito

- Cron corriendo diariamente, logs sin errores.
- C-Q4 (skills zombies) baja de 28.395 a 0.
- C-Q5 (diff Local↔Supabase) coincide con el filtro de validación esperado.
- Las 257 validaciones humanas siguen disponibles en Supabase.
- F-meta calculado desde Supabase coincide con F-meta local (ratio drift ≤ 1%).

### 8.5 Riesgos y rollback

- **Riesgo 1:** query de purga puede borrar skills válidas si el filtro es incorrecto. Mitigación: SELECT COUNT antes del DELETE, comparar con baseline 28.395, abortar si difiere.
- **Riesgo 2:** cambio en lógica de re-sync puede borrar más de la cuenta. Mitigación: test en BD de staging antes de producción.
- **Riesgo 3:** las 257 validaciones humanas pueden perderse si cron falla durante primera corrida y limpieza ya se ejecutó. Mitigación: snapshot Supabase pre-purga (extensión de F0).
- **Rollback:** restaurar Supabase desde snapshot F0. Cron se desactiva.

---

## 9. Métrica F-meta (criterio de éxito del SPEC entero)

Ya descrita en §7.4. Resumen:

- `cobertura_esco_K1`, `cobertura_esco_K3`, `cobertura_esco_K5`.
- Antes de F0: 0/0/0.
- Después de C4: baseline real (registrar).
- Después de C5: mismo baseline si sync funcionó.
- Aplicar como canario permanente → hereda al SPEC U-3 (D7).

**Cuándo F-meta valida cada fix:**
- C4 exitoso: K1, K3, K5 > 0.
- C5 exitoso: F-meta desde Supabase ≈ F-meta local.

**Lo que F-meta no valida:**
- Calidad del matching de ocupaciones (Gold Set ampliado, fuera de alcance).
- Calidad de extracción de skills (SPEC U-2).
- Anti-alucinación NLP (SPEC U-2).

---

## 10. Orden de ejecución

```
F0 (snapshot + canarios)
 │
 ├──► C3 (embeddings ocupaciones — restaurar via symlinks)
 │
 └──► C2 (fix diccionario — estrategia híbrida)
       ├─► Sub-fase A: verificación previa de over-match
       │   (matcher en muestra de 50 ofertas/entrada)
       ├─► Sub-fase B: generación JSON v2 (lookup automático)
       ├─► Sub-fase C: fix código setter
       └─► Sub-fase D: reprocesamiento 3.758 ofertas
 │
 ▼
C1 (re-rematch URI×label — desvalida 8.210 ofertas)
 │
 ▼
C4 (backfill flags ESCO + medir F-meta baseline)
 │
 ▼
C5 (cron sync + limpieza zombies + medir F-meta Supabase)
 │
 ▼
SPEC U-1 cerrado.
```

**C2 y C3 pueden ejecutarse en paralelo** (R7 confirmó independencia).

**Ventana de ejecución sugerida:**
- Día 1: F0 + C3 + Sub-fase A de C2 (verificación over-match).
- Día 2: Sub-fases B/C/D de C2 + C1 (incluye 2-7 horas cómputo de re-rematch).
- Día 3: C4 + C5 + verificación F-meta + buffer.

Pipeline pausado durante C2 sub-fase D, C1, y C4. Scraping cron del VPS Lun/Jue 08:00 puede seguir corriendo.

---

## 11. Lo que NO está en este SPEC

- Anti-alucinación NLP (`semisenior` 49%, tareas alucinadas 6,5%) → SPEC U-2.
- ZonaJobs paginación rota, ComputRabajo regresión descripción → SPEC U-2.
- Tablas zombies locales (12), `issues` con 99,4% ruido, `id_oferta` TEXT vs INTEGER → SPEC U-3.
- Versionado del matcher (5 lugares), canarios estructurales permanentes, LoRA → SPEC U-3.
- Re-incorporar cross-check ESCO en pipeline futuro (F2 del SPEC U original) → SPEC U-2.
- Gold Set expandido → fuera de los 3 SPECs.
- VPS embed-server → issue separado.
- **Errores de clasificación preexistentes** (Arquitecto Director → TIC, etc., R8 G5) → fase 2 con datos.

---

## 12. Dependencias hacia adelante

Una vez cerrado SPEC U-1:
- **SPEC U-2** puede empezar inmediatamente: anti-alucinación, fix scrapers, re-incorporar cross-check en pipeline.
- **SPEC U-3** puede empezar en paralelo: limpieza zombies locales, normalización schema, observabilidad.
- **OE matching persona→oferta** puede arrancar diseño porque depende de URIs correctas y flags poblados.

---

## 13. Decisiones que requieren cierre antes de implementar

1. **Confirmar Opción A en C3** (restaurar via symlinks) o decidir Opción B (deprecar formalmente). Recomendación: A.
2. **Aprobar el plan de verificación previa C2 sub-fase A**: muestra de 50 ofertas por entrada (analista, operario, tecnico) para validar over-match.
3. **Aprobar el JSON v2** generado por Claude Code (spot-check de 5 entradas aleatorias).
4. **Confirmar ventana de mantenimiento** de 3 días.
5. **Comunicar a Cynthia y Diego** (texto sugerido):

> "Vamos a ejecutar fixes críticos del MOL del 2026-05-XX al 2026-05-XX (3 días). En ese período:
> - El dashboard puede mostrar conteos cambiantes mientras corren los sync.
> - 8.210 ofertas que estaban validadas vuelven temporalmente a `pendiente_validacion` y se re-procesan. Cuando termine, te pido que revalides la muestra que estabas trabajando.
> - 1.064 ofertas que matcheaban por `gerente`/`analista`/`operario`/`operador`/`tecnico` van a tener URI ESCO completa (hoy aparecen sin URI en el dashboard).
> - Filtros por skill esencial/opcional (que hoy devuelven 0) van a empezar a funcionar — esperá ver más resultados que antes.
> - Si ves algo raro, anotá ID de oferta y screenshot, lo revisamos al cierre del SPEC."

---

## 14. Resumen de estimaciones

| Fix | Trabajo activo | Cómputo | Total |
|---|---:|---:|---:|
| F0 | 1-2 h | — | 1-2 h |
| C3 | 1-2 h | — | 1-2 h |
| C2 (todas las sub-fases) | 7-9 h | 3-5 h | 10-14 h |
| C1 | 4-6 h | 2-7 h | 6-13 h |
| C4 | 1-2 h | 30-90 min | 1.5-3.5 h |
| C5 | 4-6 h | — | 4-6 h |
| **Total** | **18-27 h** | **6-13 h** | **24-40 h** |

Calendario: 3 días con dedicación full-time.

---

**Fin del SPEC U-1 v2.**
