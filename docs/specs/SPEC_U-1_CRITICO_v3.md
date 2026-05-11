# SPEC U-1 — Crítico: datos producto-visibles (v3)

**Versión:** 3.0 (final, listo para implementación)
**Fecha:** 2026-05-05
**Autor:** Gerardo + Claude
**Estado:** Borrador final
**Predecesores:** v1.0 (2026-05-04), v2.0 (2026-05-04)
**Diagnóstico base:** SPEC U original + 9 reportes de diagnóstico R1-R9.

**Reportes que sustentan este SPEC:**
- R1-R6: diagnóstico inicial del sistema (`2026-05-04_conteos_*.md`)
- R7: causa raíz de C2 (bug del setter en `match_ofertas_v3.py:587-594`)
- R8: estrategia híbrida de C2 (3 entradas a quitar + 2 a conservar)
- R9: resolución de los 4 bloqueantes (heurística URI, SQL ejecutable, label drift, criterio zombie)

---

## Cambios respecto a v2

| Cambio | Origen | Impacto |
|---|---|---|
| Sub-fase B de C2: 7 selecciones automáticas + 4 decisiones humanas (no "lookup automático" puro) | R9 §A | Estimación realista 3-4h, no 2h |
| SQL de C4 ejecutable validado con `EXPLAIN QUERY PLAN` | R9 §B1 | UPDATE listo para correr |
| Estimación C4 revisada a 8-35 min (no 30-90) | R9 §B2 | Ventana más corta |
| Índice compuesto previo a C4 | tu decisión 05/05 | Acelera C4 3-5x |
| 3 entradas con label drift: decisiones específicas por entrada | R9 §C3 | 1 cambio de ISCO + 2 sustituciones de label |
| **Hallazgo crítico:** "jefe de mantenimiento" tiene ISCO mal declarado (1321 → 1219) | R9 §C2 | 149 ofertas mal clasificadas históricamente |
| **Decisión #11 cerrada:** quitar contexto `operador.maquinas/CNC` del JSON | tu decisión 05/05 | ISCO 8211 mal declarado, sin match ESCO |
| **Decisión #6 cerrada:** gerente.marketing → frecuencia histórica ("responsable marketing digital") | tu decisión 05/05 | URI definida |
| **Decisión #7 cerrada:** gerente.logistica → match de keyword ("director cadena suministro") | tu decisión 05/05 | URI definida |
| **Decisión #10 cerrada:** operador.produccion → Claude Code decide en sub-fase B | tu decisión 05/05 | Aceptado criterio Claude Code |
| C5 con orden corregido: SYNC → RECONTAR → DELETE (no DELETE primero) | R9 §D3 | Evita pérdida de datos válidos |
| Estimación C5 revisada a 6-10h (no 4-6) | R9 §E3 | Sync masivo de 40K ofertas + 880K skills |
| Conteos correctos: 19 entradas isco_primario (no 17), 7 contextos gerente, 4 contextos operador | R9 §C4 | Datos verificados |
| **Total estimación realista: 30-46h** trabajo activo + 5-15h cómputo + 4 días calendario | R9 | +25% sobre v2 |

---

## 1. Propósito y alcance

**Propósito:** corregir bugs que producen datos visibles incorrectos al usuario (analistas OEDE, dashboard Skill Intelligence, validadores) y bloquean cualquier fix posterior.

**Alcance:** F0 + C1 + C2 + C3 + C4 + C5 + F-meta.

**Fuera de alcance:**
- Anti-alucinación NLP, sesgos LLM, regresiones scrapers → SPEC U-2
- Tablas zombies locales, schema mismatch, performance → SPEC U-3
- LoRA fine-tuning → diferido
- VPS embed-server → issue separado
- Errores de clasificación preexistentes (Arquitecto Director→TIC, etc.) → fase 2 con datos
- Re-validación humana de las 8.210 ofertas desvalidadas → coordinación con Cynthia

---

## 2. Contexto y evidencia consolidada

Los 9 reportes confirmaron 5 problemas que producen datos visibles incorrectos y se refuerzan entre sí.

**1. Bug del cruce URI×label** (R3 §E1, R4 §A2). Commit `94f0d73c` (2026-04-25 16:46) introdujo UPDATE incompleto: 9 columnas escritas, 8 dejadas con valores stale. Ventana 24h hasta fix `7aeb16a3`. Resultado: 4.203 ofertas con cruce, 1.237 URIs con drift, hasta 41 labels distintos para una URI.

**2. Bug del diccionario argentino** (R7). En `match_ofertas_v3.py:587-594`, la rama `if dict_match:` no asigna `semantic_uri`. Variable persiste con default `""`. Resultado: 3.758 ofertas con `esco_occupation_uri = ''`, 100% del diccionario. Bug estructural desde febrero 2026, no regresión.

**3. Embeddings de ocupaciones borrados** (R4 §A3). Commit `25828fbf` destrackeó archivos 1 minuto después de promoverlos. Resultado: `_semantic_match_title()` retorna `[]` siempre, SPEC J apagado de facto. 12.231 ofertas (20% del matching) procesadas post-destrackeo.

**4. Regresión flags ESCO (DIAG A)** (R1 §B1). Refactor v3.5.4 eliminó la lógica que poblaba flags. Resultado: 1.116.011 filas con `is_essential = is_optional = 0`. Imposible filtrar por skill esencial/opcional.

**5. Sin sync automático + drift Local↔Supabase** (R6 §B1, R9 §D). No existe cron de sync. Local: 56.397 ofertas validadas. Supabase: ~16K. **Drift real ≈40K ofertas + 880K skills no sincronizadas.** El "+28.395 skills zombies" identificado en R6 es **mayoritariamente artefacto de backlog de sync**, no zombies reales (R9 §D1).

**Estos 5 problemas son producto-visibles**: dashboards muestran labels cruzados, conteos inflados, ofertas con URI vacía, filtros por skill esencial no funcionan, datos del dashboard tienen 6 días de retraso.

---

## 3. Fix F0 — Snapshot BD + canarios SQL

**Esfuerzo:** 1-2h
**Bloquea:** todos los fixes posteriores
**Tipo:** precondición operativa

### 3.1 Acción

- Snapshot SQLite local: dump SQL gzip a `data/snapshots/pre_spec_u1_v3_YYYYMMDD_HHMMSS.sql.gz` (~700 MB-1 GB).
- Snapshot Supabase: export JSON de `ofertas_dashboard`, `ofertas_skills`, `issues`, `rule_candidates`, `validacion_humana`.
- Crear `scripts/canarios/canarios_spec_u1.sql` con 5 queries:
  - C-Q1: ofertas con `esco_occupation_uri = ''` (baseline 3.762, de las cuales 3.758 son del diccionario)
  - C-Q2: filas en `ofertas_esco_skills_detalle` con flags=0 (baseline 1.116.011)
  - C-Q3: URIs con drift de labels (baseline 1.237)
  - C-Q4: skills "candidatas a zombie" en Supabase (baseline 28.395 — ojo, mayoría es backlog)
  - C-Q5: diff Local↔Supabase de `ofertas_dashboard` (baseline ~40K, no 8.420)
- Cron horario corre los canarios → `logs/canarios_YYYYMMDD.log`.
- Umbrales de alarma:
  - C-Q1: > +5% baseline
  - C-Q2: > +1% baseline (debe BAJAR drásticamente con C4)
  - C-Q3: > +5% baseline
  - C-Q4: > +10% baseline
  - C-Q5: > ±20% baseline

### 3.2 Criterios de éxito

- Snapshots SQL y JSON existen, comprimidos, restaurables (test: restore a BD temporal y comparar count).
- Canarios corriendo cada hora con baselines registrados en `docs/diagnostico/baseline_canarios_post_F0.md`.

### 3.3 Riesgos y rollback

- **Riesgo:** snapshot grande. Mitigación: gzip + descartar tablas zombie identificadas en R6 G1.
- **Rollback:** N/A.

---

## 4. Fix C1 — Bug del cruce URI×label

**Esfuerzo:** 4-6h trabajo + 2-10h cómputo (re-rematch 8.221 ofertas)
**Depende de:** F0, C3 (matcher debe tener `code_to_occupation` poblado), C2 (el matcher debe tener el fix del setter)
**Tipo:** corrección de datos

### 4.1 Acción

- Confirmar que el matcher actual (post-C2) escribe las 19 columnas correctamente.
- Identificar conjunto: `matching_version = 'spec_h_rematch'` (8.221 filas).
- **Decisión cerrada:** re-rematch global, asume desvalidación de 8.210 ofertas.
- Antes del re-rematch real: benchmark sobre 50 ofertas para confirmar throughput (1-3 seg/oferta declarado en SPEC v2 — validar antes de comprometer ETA).
- Ejecutar re-rematch dirigido. Estimación: 2-10h cómputo según benchmark.

### 4.2 Criterios de éxito

- Query `SELECT COUNT(DISTINCT esco_occupation_label) FROM ofertas_esco_matching WHERE esco_occupation_uri = ?` para muestra de 50 URIs aleatorias devuelve 1 por URI.
- C-Q3 baja de 1.237 a < 50.
- Las 63 URIs con drift donde el label canónico no estaba en BD (R4 §D3) reciben label canónico.

### 4.3 Riesgos y rollback

- **Riesgo 1:** desvalida 8.210 ofertas validadas. Aceptado, comunicación a Cynthia/Diego (§13).
- **Riesgo 2:** benchmark inicial puede revelar throughput < 0.5 ofertas/seg. Mitigación: si pasa, evaluar si lockear y correr en background.
- **Rollback:** restaurar desde snapshot F0.

---

## 5. Fix C2 — Bug del diccionario argentino (estrategia híbrida)

**Esfuerzo:** 11-15h trabajo + 3-5h cómputo
**Depende de:** F0
**Independiente de:** C3 (R7 confirmó)
**Tipo:** corrección de código + datos

### 5.1 Problema

3.758 ofertas con `esco_occupation_uri = ''`. 100% del diccionario argentino. Distribución:
- 19 entradas con `isco_primario`: ~2.694 ofertas
- 5 entradas con `isco_familia` + 30 contextos: 1.064 ofertas

### 5.2 Root cause

`match_ofertas_v3.py:587-594` (rama `if dict_match:` no asigna `semantic_uri`) y `_match_by_argentino_dict()` líneas 308-314 (dict retornado sin `esco_uri`).

### 5.3 Estrategia híbrida por entrada

**19 entradas `isco_primario`:** URI por entrada raíz.

**5 entradas `isco_familia`:**

| Entrada | Cobertura reglas | Decisión |
|---|---:|---|
| analista | 100% | Quitar del JSON |
| operario | 100% | Quitar del JSON |
| tecnico | 99% | Quitar del JSON |
| gerente | 70% | URI por contexto (7 contextos) |
| operador | 11% | URI por contexto (3 contextos — ver decisión #11) |

### 5.4 Decisiones de URI cerradas (post R9 + decisiones tuyas)

**11 contextos en gerente (7) + operador (4 - 1 quitado = 3):**

| # | Entrada.Contexto | URI seleccionada | Label | Heurística | Decisión |
|---|---|---|---|---|---|
| 1 | gerente.ventas\|comercial | a7594892-… | director de ventas | keyword + freq | automática |
| 2 | gerente.finanzas\|financiero | 30f3ea93-… | director financiero | keyword + freq | automática |
| 3 | gerente.operaciones\|planta\|produccion | eb9479c6-… | director de producción industrial | keyword + freq | automática |
| 4 | gerente.rrhh\|recursos humanos | f605bcd2-… | director de recursos humanos | keyword + freq | automática |
| 5 | gerente.it\|sistemas\|tecnologia | 8b6388a4-… | gestor de proyectos de TIC | freq dominante | automática |
| 6 | gerente.marketing | dc97adbe-… | responsable de marketing digital | **frecuencia histórica** | **decisión humana cerrada** |
| 7 | gerente.logistica\|supply chain | aacc3918-… | director de la cadena de suministro | **match de keyword** | **decisión humana cerrada** |
| 8 | operador.atencion\|cliente\|call center | b7b75eb6-… | agente de centro de atención al cliente | freq dominante | automática |
| 9 | operador.almacen\|deposito\|logistica | bea705fe-… | mozo de almacén | freq dominante | automática |
| 10 | operador.produccion\|planta\|fabrica | (a decidir) | (a decidir) | **Claude Code decide en sub-fase B** | delegada |
| ~~11~~ | ~~operador.maquinas\|cnc\|torno~~ | — | — | **QUITAR contexto del JSON** (ISCO 8211 mal declarado) | **decisión cerrada** |

### 5.5 Decisiones de label drift cerradas (R9 §C3)

3 de 19 entradas `isco_primario` con drift:

| Entrada | Decisión | Cambio JSON |
|---|---|---|
| jefe de mantenimiento | **(iii) Cambiar ISCO** | `isco_primario: "1321"` → `"1219"` + `esco_label: "director de mantenimiento de una fábrica"` |
| analista de tesoreria | **(i) Aceptar canónico** | `esco_label: "empleado administrativo de gestión financiera"` (mantiene ISCO 4312) |
| operador de atencion | **(i) Aceptar canónico** | `esco_label: "agente de centro de atención al cliente"` (mantiene ISCO 4222) |

**Impacto histórico:**
- jefe de mantenimiento: 149 ofertas re-clasifican C1321 → C1219 (queda cubierto por C1 / sub-fase D)
- analista de tesoreria: 35 ofertas, solo cambia label
- operador de atencion: 213 ofertas, solo cambia label

### 5.6 Acción

**Sub-fase A — Verificación previa de over-match (4-6h):**

R8 detectó sospecha de over-match en R348 (operario_plastico_soplado), R238 (analista_it), R87 (jefe_delegacion). Antes de quitar `analista`/`operario`/`tecnico`:

- Ejecutar matcher en muestra de 50 ofertas por entrada SIN la entrada del diccionario.
- Verificar que la regla matcheada corresponde al título real (no over-captura).
- Si over-match > 10% en alguna entrada: revisar/restringir regla antes de quitar.
- Si over-match ≤ 10%: proceder.
- Si over-match > 30% (caso pesimista): convertir esa entrada a Opción 3 (URI por contexto) en lugar de quitarla.

Reporte: `docs/diagnostico/2026-05-XX_verificacion_overmatch_C2.md`.

**Sub-fase B — Generación JSON v2 (3-5h):**

Script Claude Code que:
- Lee `config/sinonimos_argentinos_esco.json` actual.
- 19 entradas `isco_primario`: lookup automático en `esco_occupations` + corregir las 3 con drift según §5.5.
- `gerente` y `operador` (3 contextos restantes para operador): asignar URIs según §5.4.
  - 9 contextos con decisión cerrada (#1-9): asignación directa.
  - Contexto #10 (operador.produccion): Claude Code decide aplicando criterio mixto frecuencia + naturalidad de label. Documentar la decisión.
  - Contexto #11 (operador.maquinas/CNC): **eliminar del JSON**.
- `analista`, `operario`, `tecnico`: marcar como `_deprecated: true` o eliminar.
- Spot-check humano: revisar 5 entradas aleatorias del JSON resultante antes de aprobar.
- Versionado: `config/sinonimos_argentinos_esco_v2.json`. v1 queda como histórico.

**Sub-fase C — Fix del código (2h):**

En `match_ofertas_v3.py:_match_by_argentino_dict()` líneas 308-314: agregar `esco_uri` al dict retornado, leyendo desde la entrada del JSON v2.

En `match_ofertas_v3.py:587-594`, dentro de `if dict_match:`, agregar:
```python
semantic_uri = dict_match.get("esco_uri", "")
```

Test unit: `_match_by_argentino_dict()` con entrada nueva escribe URI no vacía. Falla si retorna URI vacía cuando la entrada tiene URI declarada.

**Sub-fase D — Reprocesamiento (3-5h cómputo):**

Las 3.758 ofertas con `esco_occupation_uri = ''` se re-procesan con matcher arreglado:
- Las que cubrían `analista`/`operario`/`tecnico` (617 ofertas): caen al path de reglas o semántico.
- Las que cubrían `gerente`/`operador` (1.064 ofertas, menos las del contexto eliminado #11): el diccionario las matchea con URI poblada.
- Las que cubrían las 19 entradas `isco_primario` (~2.694 ofertas): el diccionario las matchea con URI poblada.
- Las 149 ofertas de "jefe de mantenimiento" se re-clasifican a C1219 con label nuevo.

### 5.7 Criterios de éxito

- C-Q1 baja de 3.762 a < 50 (residuos esperables: las 4 con `decision_metodo` no-diccionario + casos edge).
- Test unit: `_match_by_argentino_dict()` con entrada nueva escribe URI no vacía.
- Las 1.064 ofertas que matcheaban por `isco_familia` mantienen ISCO razonable post-reprocesamiento (validar contra muestra de 100; al menos 90% conserva o mejora clasificación).
- 19 entradas `isco_primario` con `esco_uri` poblada en JSON v2.
- 7 contextos de gerente + 3 de operador (no 4) con `esco_uri` poblada.
- 3 entradas eliminadas del JSON: `analista`, `operario`, `tecnico` (si over-match ≤ 10%).
- 1 contexto eliminado: `operador.maquinas/CNC`.

### 5.8 Riesgos y rollback

- **Riesgo 1:** verificación previa detecta over-match alto (>30%). Mitigación: convertir esa entrada a Opción 3 en lugar de quitarla.
- **Riesgo 2:** lookup automático asigna URI subóptima en casos edge. Mitigación: spot-check humano de 5 entradas + sub-fase A valida muestra.
- **Riesgo 3:** las 1.064 ofertas re-procesadas pueden cambiar de ISCO. Mitigación: muestra de 100 validada manualmente.
- **Riesgo 4:** decisión Claude Code en contexto #10 puede no ser óptima. Mitigación: documentar criterio aplicado, spot-check humano post-implementación.
- **Riesgo 5:** errores de clasificación preexistentes (Arquitecto Director → TIC, etc.) NO se corrigen. Declarado fuera de alcance.
- **Rollback:** restaurar JSON desde snapshot F0 + revert código. Las 3.758 vuelven a `esco_occupation_uri = ''`.

---

## 6. Fix C3 — Embeddings de ocupaciones borrados

**Esfuerzo:** 1-2h
**Depende de:** F0
**Independiente de:** C2 (R7 confirmó)
**Tipo:** corrección de configuración

### 6.1 Acción

**Opción A (recomendada):** crear symlinks `database/embeddings/esco_occupations_embeddings.npy → enriched/esco_occupations_embeddings.npy` y mismo para `esco_occupations_metadata.json`.

- Verificar que `_load_occupation_embeddings()` y `_semantic_match_title()` son compatibles con schema enriched (R8 detectó que el matcher usa `skills_first_v3` por defecto, no `_semantic_match_title`).
- Si compatibles: crear symlinks.
- Verificar carga: `code_to_occupation` poblado con 3.046 ocupaciones, `_semantic_match_title("título de ejemplo")` retorna lista no vacía.

### 6.2 Criterios de éxito

- `_load_occupation_embeddings()` carga correctamente.
- `code_to_occupation` poblado (3.046 ocupaciones).
- `_semantic_match_title()` sobre 10 títulos retorna lista no vacía.
- Test sobre 100 ofertas con `decision_metodo = 'semantico_unico'`: el path título-semántico contribuye con score no nulo en al menos 30% de los casos.

### 6.3 Riesgos y rollback

- **Riesgo:** schema-mismatch entre archivos `enriched/` y código. Mitigación: validación previa.
- **Rollback:** eliminar symlinks. Sistema vuelve al estado actual (rama título-semántico apagada).

---

## 7. Fix C4 — Regresión flags ESCO (DIAG A)

**Esfuerzo:** 30 min creación índice + 8-35 min UPDATE + 1-2h verificación
**Depende de:** F0, C2
**Tipo:** corrección de datos

### 7.1 Pre-paso: índice compuesto

Antes del UPDATE, crear índice compuesto sobre `esco_associations` para acelerar el JOIN 3-5x:

```sql
CREATE INDEX IF NOT EXISTS idx_esco_assoc_compound 
ON esco_associations (occupation_uri, skill_uri, relation_type);
```

Tiempo estimado de creación: ~2-5 min sobre 129.004 filas.

### 7.2 SQL de C4 (validado con `EXPLAIN QUERY PLAN`, R9 §B1)

```sql
UPDATE ofertas_esco_skills_detalle AS sd
SET
  is_essential_for_occupation = COALESCE((
    SELECT 1 FROM esco_associations ea
    JOIN ofertas_esco_matching om ON om.id_oferta = sd.id_oferta
    WHERE ea.occupation_uri = om.esco_occupation_uri
      AND ea.skill_uri = sd.esco_skill_uri
      AND ea.relation_type = 'essential'
    LIMIT 1
  ), 0),
  is_optional_for_occupation = COALESCE((
    SELECT 1 FROM esco_associations ea
    JOIN ofertas_esco_matching om ON om.id_oferta = sd.id_oferta
    WHERE ea.occupation_uri = om.esco_occupation_uri
      AND ea.skill_uri = sd.esco_skill_uri
      AND ea.relation_type = 'optional'
    LIMIT 1
  ), 0)
WHERE EXISTS (
  SELECT 1 FROM ofertas_esco_matching om
  WHERE om.id_oferta = sd.id_oferta
    AND om.esco_occupation_uri != ''
);
```

**Estimación con índice compuesto:** 8-15 minutos (R9 §B2: throughput 500-2000 filas/seg con índice).

### 7.3 Pausa de pipeline (R9 §B4)

Pre-C4:
```bash
ps aux | grep -E "(run_validated_pipeline|process_nlp|match_ofertas|sync_to_supabase|auto_validator)" | grep -v grep
```

Si vacío → seguro ejecutar. Si hay procesos → matar/esperar a que terminen.

Scraping VPS Lun/Jue 08:00 puede seguir corriendo (no toca `ofertas_esco_*`). Recomendación: ejecutar C4 fuera de Lun/Jue 08:00 ART.

### 7.4 Verificación post-UPDATE

Las 3 queries de R9 §B3:

**Q1 — Conteo por flag:**
```sql
SELECT
  SUM(CASE WHEN is_essential_for_occupation = 1 THEN 1 ELSE 0 END) AS n_essential,
  SUM(CASE WHEN is_optional_for_occupation = 1 THEN 1 ELSE 0 END) AS n_optional,
  SUM(CASE WHEN is_essential_for_occupation = 0 AND is_optional_for_occupation = 0 THEN 1 ELSE 0 END) AS n_zero,
  COUNT(*) AS total
FROM ofertas_esco_skills_detalle sd
WHERE EXISTS (
  SELECT 1 FROM ofertas_esco_matching om
  WHERE om.id_oferta = sd.id_oferta AND om.esco_occupation_uri != ''
);
```
Esperado: total ≈ 1.023.911. n_essential ≈ 332K (32,4% según R2 §B2).

**Q2 — Sample 50 ofertas:** inspección manual contra catálogo ESCO oficial.

**Q3 — Validación cruzada:** 5 ocupaciones aleatorias, verificar `skills_essential_post_update <= skills_essential_catalogo`.

### 7.5 F-meta (criterio de éxito del SPEC entero)

```sql
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

Hoy: 0/0/0. Después de C4: baseline real. Registrar en `docs/diagnostico/baseline_cobertura_esco_K_post_C4.md`. **No fijar objetivo a priori.**

### 7.6 Criterios de éxito C4

- C-Q2 baja de 1.116.011 a ~755.000 (67,6% del nuevo total post-C2).
- F-meta: K1, K3, K5 > 0 (cualquier valor distinto de cero confirma backfill aplicado).

### 7.7 Riesgos y rollback

- **Riesgo:** UPDATE concurrente con pipeline activo → locks. Mitigación: §7.3.
- **Rollback:** UPDATE inverso desde snapshot F0.

---

## 8. Fix C5 — Sync automático Supabase + zombies (orden corregido)

**Esfuerzo:** 6-10h (incluye sync masivo de 40K ofertas + 880K skills)
**Depende de:** F0, C1, C2, C4
**Tipo:** corrección de infraestructura + datos

### 8.1 Hallazgo crítico de R9 §D

El conteo de "28.395 zombies" del SPEC v2 es **mayoritariamente artefacto de backlog de sync**, no zombies reales. Local tiene 56.397 ofertas validadas; Supabase tiene ~16K. **Drift real ≈40K ofertas y ~880K skills no sincronizadas.**

Si el DELETE corre antes del sync, **borra skills cuyas ofertas locales aún no se subieron** = pérdida de datos.

### 8.2 Plan operacional (R9 §D3, orden corregido)

```
PASO 1 — SYNC FORZADO (no DELETE)
  python scripts/exports/sync_to_supabase.py
  # Sube backlog: ~40K ofertas + ~880K skills
  # Estimación: 60-90 min (rate limit ~15 req/s)

PASO 2 — RE-CONTAR zombies con criterio refinado
  -- En Supabase
  SELECT COUNT(*) AS n_zombies, COUNT(DISTINCT id_oferta) AS n_ofertas_huerfanas
  FROM ofertas_skills os
  WHERE os.id_oferta NOT IN (SELECT id_oferta FROM ofertas_dashboard);

PASO 3 — Decisión por umbral (R9 §D4):
  - Si n_zombies < 500: confianza alta → ejecutar DELETE
  - Si n_zombies entre 500 y 5.000: spot-check sample 20 zombies, si todas
    son ofertas viejas borradas localmente → ejecutar; si alguna es válida
    → reinvestigar
  - Si n_zombies > 5.000: NO ejecutar; el sync no completó

PASO 4 — DELETE zombies remanentes (si paso 3 lo aprueba)
  DELETE FROM ofertas_skills os
  WHERE os.id_oferta NOT IN (SELECT id_oferta FROM ofertas_dashboard);

PASO 5 — Activar cron de sync diario
  Configurar cron 03:00 AR de sync_to_supabase.py
  Logs estructurados a logs/sync_supabase_YYYYMMDD.log
  Notificación si falla
```

### 8.3 Fix del re-sync para purgar al sincronizar

- Modificar `sync_to_supabase.py` para que el delete cubra todas las skills cuyas ofertas no están en el sync actual.
- Test de regresión: si una oferta se borra localmente, sus skills se borran en Supabase en la siguiente corrida del cron.

### 8.4 Criterios de éxito

- Cron corriendo diariamente, logs sin errores.
- C-Q4 (skills zombies post-sync): valor confiable según criterio R9 §D2.
- C-Q5 (diff Local↔Supabase): coincide con filtro de validación esperado.
- 257 validaciones humanas siguen disponibles en Supabase.
- F-meta calculado desde Supabase ≈ F-meta local (drift ≤ 1%).

### 8.5 Riesgos y rollback

- **Riesgo 1:** sync masivo puede tomar >90 min si rate limit Supabase es estricto. Mitigación: monitorear, paginar si necesario.
- **Riesgo 2:** después del sync, número de zombies sigue alto (>5000). Mitigación: PARAR según paso 3, no ejecutar DELETE.
- **Riesgo 3:** las 257 validaciones humanas pueden perderse si cron falla durante primera corrida. Mitigación: snapshot Supabase pre-sync (extensión de F0).
- **Rollback:** restaurar Supabase desde snapshot F0. Cron se desactiva.

---

## 9. Métrica F-meta (criterio cross-cutting)

Definida en §7.5. Resumen:

- `cobertura_esco_K1`, `cobertura_esco_K3`, `cobertura_esco_K5`.
- Antes de F0: 0/0/0.
- Después de C4: baseline real (registrar).
- Después de C5: F-meta desde Supabase ≈ F-meta local.
- Aplicar como canario permanente → hereda al SPEC U-3.

**Cuándo F-meta valida cada fix:**
- C4 exitoso: K1, K3, K5 > 0.
- C5 exitoso: F-meta Supabase ≈ F-meta local.

**Lo que F-meta no valida:**
- Calidad del matching de ocupaciones (Gold Set ampliado, fuera de alcance).
- Calidad de extracción de skills (SPEC U-2).
- Anti-alucinación NLP (SPEC U-2).

---

## 10. Orden de ejecución

```
F0 (snapshot + canarios)
 │
 ├──► C3 (embeddings ocupaciones — symlinks)
 │
 └──► C2 (fix diccionario híbrido)
       ├─► Sub-fase A: verificación over-match (50 ofertas/entrada)
       ├─► Sub-fase B: generación JSON v2 (lookup + decisiones cerradas)
       ├─► Sub-fase C: fix código setter
       └─► Sub-fase D: reprocesamiento 3.758 ofertas
 │
 ▼
C1 (re-rematch URI×label — desvalida 8.210)
 │
 ▼
C4 (índice compuesto + UPDATE flags + medir F-meta)
 │
 ▼
C5 (SYNC → recontar → DELETE zombies → cron + medir F-meta Supabase)
 │
 ▼
SPEC U-1 cerrado.
```

**C2 y C3 pueden ejecutarse en paralelo** (R7 confirmó independencia).

**Ventana de ejecución sugerida:** 4 días con dedicación full-time.
- Día 1: F0 + C3 + C2 sub-fase A
- Día 2: C2 sub-fases B + C
- Día 3: C2 sub-fase D + C1 (incluye 2-10h cómputo)
- Día 4: C4 + C5 + verificación F-meta + buffer

Pipeline pausado durante C2 sub-fase D, C1, C4. Scraping cron VPS puede seguir.

---

## 11. Lo que NO está en este SPEC

- Anti-alucinación NLP, sesgos LLM (`semisenior=49%`), regresiones scrapers (ZonaJobs, ComputRabajo) → SPEC U-2
- Tablas zombies locales (12), `issues` con 99,4% ruido, `id_oferta` TEXT vs INTEGER → SPEC U-3
- Versionado matcher (5 lugares), canarios estructurales permanentes, LoRA → SPEC U-3
- Re-incorporar cross-check ESCO en pipeline (F2 SPEC U original) → SPEC U-2
- Gold Set expandido → fuera de los 3 SPECs
- VPS embed-server → issue separado
- Errores de clasificación preexistentes (Arquitecto Director → TIC, OPERADOR DE MAQUINAS CHILLER → 8211, etc.) → fase 2 con datos
- Bug ISCO 8211 mal declarado en JSON: el contexto `operador.maquinas/CNC` se elimina, pero la decisión de re-introducirlo con ISCO correcto (7223 o 8121) queda diferida

---

## 12. Dependencias hacia adelante

Una vez cerrado SPEC U-1:
- **SPEC U-2** puede empezar inmediatamente: anti-alucinación, fix scrapers, re-incorporar cross-check en pipeline.
- **SPEC U-3** puede empezar en paralelo: limpieza zombies locales, normalización schema, observabilidad.
- **OE matching persona→oferta** puede arrancar diseño (depende de URIs correctas y flags poblados).

---

## 13. Decisiones que requieren cierre antes de implementar

**TODAS las decisiones técnicas están cerradas en v3.** Lo que queda es operativo:

1. **Confirmar ventana de mantenimiento** de 4 días.
2. **Comunicar a Cynthia y Diego** (texto sugerido):

> "Vamos a ejecutar fixes críticos del MOL del 2026-05-XX al 2026-05-XX (4 días). En ese período:
> - Dashboard puede mostrar conteos cambiantes mientras corren los syncs.
> - 8.210 ofertas validadas vuelven temporalmente a `pendiente_validacion` y se re-procesan. Cuando termine, te pido que revalides la muestra que estabas trabajando.
> - 1.064 ofertas que matcheaban por `gerente`/`analista`/`operario`/`operador`/`tecnico` van a tener URI ESCO completa (hoy aparecen sin URI).
> - 149 ofertas de "jefe de mantenimiento" cambian de ISCO 1321 a 1219 (reclasificación correcta).
> - Filtros por skill esencial/opcional (que hoy devuelven 0) van a empezar a funcionar — esperá ver más resultados.
> - El sync a Supabase va a actualizar 40K ofertas en backlog. Vas a ver muchas ofertas nuevas en el dashboard del primer día.
> - Si ves algo raro, anotá ID de oferta y screenshot, lo revisamos al cierre."

---

## 14. Resumen de estimaciones (realista)

| Fix | Trabajo activo | Cómputo | Total |
|---|---:|---:|---:|
| F0 | 1-2 h | — | 1-2 h |
| C3 | 1-2 h | — | 1-2 h |
| C2 sub-fase A (over-match) | 4-6 h | — | 4-6 h |
| C2 sub-fase B (JSON v2) | 3-5 h | — | 3-5 h |
| C2 sub-fase C (código) | 2 h | — | 2 h |
| C2 sub-fase D (reprocesamiento) | 1 h | 3-5 h | 4-6 h |
| C1 (incl. benchmark) | 4-6 h | 2-10 h | 6-16 h |
| C4 (índice + UPDATE + verificación) | 2-5 h | 8-35 min | 2-5 h |
| C5 (sync masivo + zombies + cron) | 5-8 h | — | 5-8 h |
| **Total** | **23-37 h** | **5-15 h** | **28-52 h** |

**Calendario:** 4 días con dedicación full-time, con buffer.

---

## 15. Resumen de cambios v2 → v3 (rastreabilidad)

| Sección v2 | Cambio en v3 | Origen |
|---|---|---|
| §3 F0 baseline C-Q1 | 3.762 (no 3.758) | R9 §A |
| §3 F0 baseline C-Q5 | ~40K (no 8.420) | R9 §D1 |
| §5.4 sub-fase B | 7 automáticas + 4 humanas (no "lookup automático") | R9 §A4 |
| §5.4 11 contextos | Decisiones específicas por contexto | tu decisión 05/05 |
| §5.5 (nuevo) | Decisiones de label drift por entrada | R9 §C3 |
| §5.6 sub-fase A | Plan B explícito si over-match >30% | R8 + tu pedido |
| §5.7 criterios | "7 contextos gerente + 3 operador" (no 11+4) | tu decisión 05/05 |
| §6 C3 | Sin cambios sustanciales | — |
| §7.1 (nuevo) | Pre-paso: índice compuesto | tu decisión 05/05 |
| §7.2 SQL | Versión ejecutable validada | R9 §B1 |
| §7.5 estimación | 8-35 min (no 30-90) | R9 §B2 |
| §8.2 orden C5 | SYNC primero, DELETE después (no al revés) | R9 §D3 |
| §8.5 estimación C5 | 6-10h (no 4-6) | R9 §E3 |

---

**Fin del SPEC U-1 v3.**
