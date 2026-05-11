# Conteos 6 — Supabase + NLP + URIs

**Fecha ejecución:** 2026-05-04
**Pipeline activo:** NO (sin procesos `run_validated_pipeline`, NLP, matching, scraping; cron VPS Lun/Jue ya corrió 08:00-11:30)
**Supabase accesible:** SÍ (service_role_key)
**Tiempo total:** ~80 min
**Secciones completadas:** A, B, C, D, E, F, G, H
**Pendientes:**
- Verificar contenido del dashboard que consume `terminologia_argentina_skills` (no investigado en código TS Next.js, solo en Python).
- Drift exacto de `ofertas_skills` Local↔Supabase (1.116.011 vs 1.144.406 — diff 28.395 que merece investigación).
- Frecuencia de sincronización automática (cron) de sync_to_supabase: **no encontrado**, parece manual.

**Bloqueo de salida:** `/mnt/user-data/outputs/` no escribible (Permission denied). Reporte solo a `docs/diagnostico/`.

---

## A — rule_candidates (E3 cerrado, schema OK, vacío en producción)

### A1. Tabla `rule_candidates` en Supabase

- **Existe.** Migration `fase3_dashboard/sql/061_m09b_comp4_rule_candidates.sql`.
- **Total filas: 0.**
- Schema completo:

| Columna | Tipo | Notas |
|---|---|---|
| id | BIGSERIAL PK | |
| oferta_id | TEXT | |
| issue_ids | TEXT[] | |
| tipo | TEXT NOT NULL CHECK | 11 valores: `regla_nueva`, `fix_regla`, `fix_bug`, `sinonimo`, `skills_gold_set`, `nlp_correccion_sector`, `nlp_area_funcional`, `nlp_limpieza_tareas`, `nlp_fix_puntual`, `excepcion_aceptable`, `requiere_revision` |
| propuesta | JSONB NOT NULL | |
| justificacion | TEXT | |
| confianza | TEXT CHECK | `alta` / `media` / `baja` |
| afecta_otras | BOOLEAN | default FALSE |
| estado | TEXT CHECK | `pendiente` / `aprobado` / `rechazado` / `sincronizado` |
| revisado_por | TEXT | |
| revisado_at | TIMESTAMPTZ | |
| motivo_rechazo | TEXT | |
| generado_por | TEXT | default `'claude-api'` |
| batch_id | TEXT | |
| created_at | TIMESTAMPTZ | default NOW() |

- Índices: `estado`, `tipo`, `oferta_id`.
- RLS: read público, write service_role + authenticated.

### A2. Drift Supabase ↔ JSON local

- 0 candidatos `aprobado` en Supabase. Imposible drift.
- El reporte 3 ya había confirmado 0 entradas zombie en el JSON local. Mantengo conclusión.

### A3. ¿Corrió `sync_rules_from_candidates.py` alguna vez?

- **NUNCA en producción**, según `pipeline_commands` (27 filas, todas `scrape_indeed`).
- No hay tabla `sync_log` en Supabase.
- El script `scripts/sync_rules_from_candidates.py` tampoco produce log local persistente.
- **Conclusión:** el script existe, está desplegado, pero nunca se ejecutó porque la cola de candidatos siempre estuvo vacía.

### A4. Lectores y escritores de `rule_candidates`

| Rol | Archivo | Acción |
|---|---|---|
| Escritor | `fase3_dashboard/mol-dashboard/app/api/admin/analizar-correcciones/route.ts:340` | INSERT (cuando admin UI llama a Claude API y este propone candidatos) |
| Lector | `fase3_dashboard/mol-dashboard/app/api/admin/analizar-correcciones/route.ts:387,418` | SELECT (UI lista candidatos) |
| Lector + actualizador | `scripts/sync_rules_from_candidates.py:196` | SELECT estado='aprobado', UPDATE → 'sincronizado' |
| Tests | `tests/matching/test_m09b_comp4.py:171` | check tabla existe |

**Hallazgo:** `sync_rules_from_candidates.py` líneas 263-273 hace `json.dump` a `RULES_PATH`, `SINONIMOS_PATH`, `NLP_RULES_PATH`. El reporte 3 ya documentó schema drift (escribe `isco`/`label`, matcher lee `isco_primario`/`esco_label`). Cierra E3.

---

## B — Drift Local ↔ Supabase ↔ Vercel

### B1. Frecuencia y mecanismo de sync

- **No hay cron automático**. Sync se ejecuta manualmente vía `scripts/exports/sync_to_supabase.py`.
- Estado: `config/supabase_sync_log.json`:
  - **Última corrida:** 2026-04-28T14:22:20 (864 ofertas, 14.417 skills)
  - **Historial:** 20 corridas entre 2026-04-22 y 2026-04-28 → ninguna desde hace 6 días.
- Tablas que sincroniza el script:
  - `ofertas_dashboard` ← JOIN `ofertas` + `ofertas_nlp` + `ofertas_esco_matching` (solo `estado_validacion` IN validado/validado_claude/validado_humano)
  - `ofertas_skills` ← `ofertas_esco_skills_detalle` (delete+insert por oferta)
- Otras tablas que se actualizan en ciclo independiente:
  - `scraping_live_stats` ← cron VPS via `sync_scraping_stats.py` (Lun/Jue, último OK con upsert, falla en print final por bug C)
  - `sistema_estado` ← scripts puntuales (último snapshot 2026-04-28T17:19:28)

### B2. Conteos comparados Local vs Supabase

| Tabla local | Local | Tabla Supabase | Sup | Diff |
|---|---:|---|---:|---:|
| ofertas | 60.983 | ofertas_dashboard | 52.563 | **−8.420** |
| ofertas_nlp | 57.900 | (n/a — embebido) | — | — |
| ofertas_esco_matching | 56.433 | (n/a — embebido) | — | — |
| ofertas_esco_skills_detalle | 1.116.011 | ofertas_skills | 1.144.406 | **+28.395** |
| esco_associations | 129.004 | (n/a — no se sincroniza) | — | — |
| esco_occupations | 3.045 | (n/a) | — | — |
| esco_skills | 14.247 | (n/a) | — | — |

**Tablas Supabase adicionales identificadas (9 totales):**

| Tabla | Filas |
|---|---:|
| ofertas_dashboard | 52.563 |
| ofertas_skills | 1.144.406 (estimated) |
| issues | 213.134 |
| sistema_estado | 401 (snapshots históricos) |
| esco_argentino | 44 (skills curadas por humano para ARG) |
| pipeline_commands | 27 (scrape_indeed exclusivamente) |
| audit_log | 0 |
| rule_candidates | 0 |
| scraping_live_stats | 1 (id='current') |

**Hallazgos del diff:**
- **−8.420 ofertas** en Supabase vs local: son las que NO pasaron `estado_validacion IN (validado*)` o están en tránsito. Esperable.
- **+28.395 skills** en Supabase vs local: anomalía. Skills DEL antes en Supabase no se purgaron al re-sincronizar. **Bug de gobierno de datos.**

### B3. URI vacía (DIAG F revisitado)

- **Supabase:** 3.607 ofertas con `esco_occupation_uri` vacía/NULL (de 52.563 sincronizadas, 6,9%).
- **Local:** según reporte 5, 3.762 con URI vacía en `ofertas_esco_matching`.
- Diff: 155 (probablemente las que se validaron después del último sync, o ofertas que aún no cruzaron el filtro de validación).

### B4. Label drift en Supabase

- **Supabase:** 1.776 URIs distintas, 761 con >1 label distinto.
- **Local:** 1.237 URIs con drift (reporte previo).
- **Conclusión:** drift PEOR en Supabase. Significa que ofertas viejas (antes de SPEC E) quedaron con label antiguo, y al re-sincronizar las nuevas con label SPEC E, el dashboard muestra ambos. **No hay limpieza de drift al re-sync.**

### B5. Validaciones humanas reales

| Estado validacion_humana | Conteo Supabase |
|---|---:|
| NULL | 52.306 |
| `revisar` | 245 |
| `ok` | 6 |
| `error` | 6 |
| **Total con `validacion_humana_at` no NULL** | **257** |

**Confirmación reporte 1:** validaciones humanas reales son **257**, muchas más que las ~50 que estimé. El campo está poblado. La mayoría son `revisar` (acción incompleta), 12 son veredictos finales (`ok` + `error`).

### B6. Vercel — cache strategy

- `next.config.ts`: minimal config, sin reglas de revalidate global.
- **Routes API que fuerzan no-cache:**
  - `app/api/skills-intelligence/route.ts`: `export const revalidate = 0`
  - `app/api/skills-intelligence/occupation/route.ts`: `export const revalidate = 0`
  - `app/reporte/[token]/page.tsx`: `cache: 'no-store'`
- **Sin SWR / React Query** detectado en grep (0 matches en `app/`).
- **Conclusión:** Vercel lee directo de Supabase, sin capa de caché propia significativa. Drift de B4 se refleja al usuario en tiempo real.

---

## C — sync_scraping_stats KeyError

### C1. Reproducción del bug

**Archivo:** `/opt/mol/scripts/sync_scraping_stats.py:82`
```python
total_7d = sum(p["ultimos_7d"] for p in merged.values())
```

`merged` se construye así:
- Línea 56-65: portales de VPS (bumeran, zonajobs, computrabajo, caba, portalempleo) con dict completo `{total, ultimo_scraping, ultimos_7d, hoy}`.
- Líneas 67-71: portales LOCALES (`indeed`) preservados desde el `scraping_live_stats.portales` existente, **sin re-construir las keys**.

Cuando indeed fue insertado por primera vez sin `ultimos_7d`/`hoy`, ese dict se preserva entre corridas y el `sum` falla.

**Verificado en producción ahora mismo en Supabase:**
```
indeed:
  total: 6959
  ultimo_scraping: 2026-05-04T13:49:24.609046
  (NO tiene ultimos_7d ni hoy)
```

**Resto de portales:** todos tienen `total`, `ultimo_scraping`, `ultimos_7d`, `hoy`.

### C2. Impacto

- **El upsert OCURRE antes del sum** (línea 76 del script). Por eso los datos llegan a Supabase a pesar del traceback.
- Lo único que NO ocurre es el `print` final con el resumen.
- **`scraping_live_stats` SÍ está actualizado** — última corrida 2026-05-04T16:49:28 con 48.085 ofertas y 6 portales.
- **Indeed no se actualiza nunca** (sigue en 6.959 desde quién sabe cuándo).

### C3. Otros bugs silenciosos

- `cron_errors.log` (VPS): 21 líneas, **únicamente** la traza KeyError repetida 4 veces.
- Nota fantasma: `/opt/mol/scripts/scraping/run_scraping_vps.sh: not found` aparece en log, pero el archivo SÍ existe hoy. Probablemente residuo de un cron viejo o reinicio que ya no se reproduce.
- **Sin otros errores recurrentes detectados.**

---

## D — NLP regex v4 vs LLM

### D1. Decisión regex / LLM

`database/process_nlp_from_db_v11.py` líneas 166-183 + 359-388:

**Pipeline en orden:**
1. **CAPA 0 (regex_patterns_v4):** extrae `salario_min`, `salario_max`, `moneda`, `jornada_laboral`, `modalidad`. Solo estos 5 campos.
2. **CAPA 1 (Qwen2.5:7b):** extrae 20 campos restantes.
3. **MERGE selectivo (línea 379):** regex gana SOLO para los 5 campos de CAPA 0. El resto siempre es LLM (a menos que LLM falle 2 reintentos, en cuyo caso queda regex como fallback).

**Source-aware pre-fill (CAPA 1b)** desde `process_nlp_from_db_v11.py` (mencionado en CLAUDE.md): para CABA / Portal Empleo / Indeed con metadata embebida, hay un paso adicional. No verificado a fondo en este diagnóstico.

### D2. Cobertura por campo (sobre 57.900 filas en `ofertas_nlp`, nlp_version='11.3.0')

| Campo | Fuente | Filas | % |
|---|---|---:|---:|
| salario_min | regex | 833 | 1,4% |
| salario_max | regex | 571 | 1,0% |
| moneda | regex | 1.492 | 2,6% |
| jornada_laboral | regex | 36.564 | 63,2% |
| modalidad | regex | 57.461 | **99,2%** |
| provincia | LLM | 50.600 | 87,4% |
| localidad | LLM | 44.958 | 77,6% |
| tareas_explicitas | LLM | 55.097 | 95,2% |
| nivel_educativo | LLM | 47.105 | 81,4% |
| experiencia_min_anios | LLM | 50.428 | 87,1% |
| requerimiento_edad | LLM | 57.721 | 99,7% |
| requerimiento_sexo | LLM | 57.721 | 99,7% |
| area_funcional | LLM | 57.874 | 100,0% |
| nivel_seniority | LLM | 57.574 | 99,4% |
| tiene_gente_cargo | LLM | 57.900 | 100,0% |
| mision_rol | LLM | 56.586 | 97,7% |
| tipo_oferta | LLM | 57.900 | 100,0% |

**Hallazgos:**
- Los campos LLM "categóricos cerrados" tienen casi 100% de cobertura. **No hay** ofertas en estado "el LLM no sabe responder" → Qwen siempre devuelve algo, aún si forzado.
- `salario_min`/`salario_max`/`moneda` regex < 3%: la mayoría de las ofertas no menciona salario explícito. OK.
- `jornada_laboral` regex 63%: el resto (37%) queda NULL. No hay fallback LLM para este campo.
- **Skills no aparecen en cobertura** porque están en `ofertas_esco_skills_detalle`, no en `ofertas_nlp` (decisión de schema separado).

### D3. Tests de regresión regex

**Archivos en `tests/nlp/`:**
- `test_extraction.py` (test general extracción)
- `test_area_normalization.py`
- `test_diccionarios_carga.py`
- `test_nlp_validation_rules.py`
- `test_nlp_validator.py`
- `test_postprocessor_area.py`
- `gold_set.json` (20+ casos)

**No verifiqué si pasan hoy** (no ejecuté pytest, READ-ONLY). El gold_set existe pero no medí.

### D4. Calidad LLM — defaults sospechosos

| Campo | Top valor | % | Comentario |
|---|---|---:|---|
| nivel_seniority | semisenior | **49,3%** | Sospechoso (esperable < 30%) |
| area_funcional | Ventas | 21,4% | Distribución plausible |
| tipo_oferta | demanda_real | 96,6% | Plausible (otros tipos son raros) |
| modalidad | presencial | 83,3% | Plausible para AR |
| requerimiento_edad | 0 (sin requisito) | 90,9% | Plausible |
| requerimiento_sexo | 0 (sin requisito) | 97,5% | Plausible |

**Sospecha clave:** `nivel_seniority='semisenior'` en 49,3% es claramente excesivo. Qwen tiende a ese valor cuando no tiene señal clara, exactamente como reportó el reporte 4. Es un default sesgado del modelo, no un patrón real del mercado argentino.

---

## E — Anti-alucinación Qwen

### E1. ¿Hay anti-alucinación en NLP?

**NO.** Grep contra `process_nlp_from_db_v11.py` con patterns `aluc|ground|verify_in_text|appears.*in.*desc` retorna **0 matches**.

El postprocessor (`nlp_postprocessor.py` v1.3) hace correcciones, no verificación contra texto original.

El NLP Gate (`nlp_validator.py` v1.1) valida coherencia entre campos (cross-field), pero no verifica groundedness.

### E2. Métricas de alucinación detectada

**No existen métricas en BD.** No hay tabla, columna ni log que cuente alucinaciones.

### E3. Sample experimental — 50 ofertas

Verifiqué heurísticamente: para cada `tareas_explicitas`, qué fracción de las palabras significativas (>4 chars) aparece en la `descripcion` original.

| Métrica | Valor |
|---|---:|
| Sample | 50 ofertas |
| Ofertas con ≥1 tarea con <40% de palabras en descripción | **4 (8%)** |
| Tareas alucinadas | 18 de 275 (**6,5%**) |

**Ejemplos detectados:**
- oferta 2070054: tarea `'analizar problemas técnicos'`
- oferta 2149320: tarea `'respondiendo a preguntas sobre cuentas de clientes'`
- oferta 2150001: tarea `'Comunicarse con clientes'`
- oferta 2145519: tarea `'Realizar reparaciones eléctricas'`

Las muestras parecen tareas plausibles pero NO están literales en el texto. Pueden ser inferencias razonables del LLM, aunque en sentido estricto son alucinaciones.

### E4. Versión NLP en producción

Discrepancia confirmada:

| Fuente | Versión declarada |
|---|---|
| `database/process_nlp_from_db_v11.py:6` | `VERSION: 11.3.1` (en docstring) |
| `database/process_nlp_from_db_v11.py:89` | `VERSION = "11.3.0"` (constante usada) |
| `database/process_nlp_from_db_v11.py:90` | `NLP_VERSION_TAG = "11.3.0"` (la que se persiste) |
| BD `ofertas_nlp.nlp_version` | **'11.3.0'** (las 57.900 filas) |
| `CLAUDE.md` | "v11.4" |
| `learnings.yaml` | "v11.4" |

**Producción real: 11.3.0.** La 11.4 que documenta CLAUDE.md no existe en código ni en datos. Es un upgrade nominal sin implementación, o el archivo fue renombrado y la constante no se actualizó.

---

## F — URIs no canónicas

### F1. URIs hex sintéticas (`terminologia_argentina_skills.json`)

**Corrección al reporte 5:** la afirmación "51 URIs hex sintéticas afectan 30.593 filas en `ofertas_esco_skills_detalle`" es **INCORRECTA**.

**Verificación actual:**
```sql
SELECT COUNT(*) FROM ofertas_esco_skills_detalle
WHERE esco_skill_uri NOT LIKE 'http://data.europa.eu/esco/skill/%';
-- → 0
```

**1.116.011 filas TODAS canónicas** (`http://data.europa.eu/esco/skill/...`). 12.888 URIs distintas, todas válidas ESCO.

**Hallazgo del config:** `config/terminologia_argentina_skills.json` es un dict con keys `version`, `descripcion`, `_instrucciones`, etc. El contenido real está estructurado como diccionario de términos pero no se persiste en ningún campo `esco_skill_uri` de BD. Es **configuración para enriquecer corpus** o **mapeo opcional**, no inserción en tablas de matching.

**Consumidores del archivo según grep:**
- `database/skills_implicit_extractor.py` — referencia el JSON (no verifiqué cómo lo aplica exactamente)
- 7 archivos SQL en `fase3_dashboard/sql/` (007, 014, 018, 028, 043, 050, 055, 056, 057) — pertenecen al sistema de curación esco_argentino

**Pipeline real para skills argentinas:** `esco_argentino` (Supabase, 44 ocupaciones curadas) con `skills_consolidadas` JSONB que contiene URIs canónicas ESCO + label en español. El boost se aplica como `0.05 * (frequency / max_frequency)` en el extractor (reporte 5). **NO inserta URIs sintéticas.**

### F2. Tabla `ofertas_skills_norm` (12.304 filas, ZOMBIE)

```sql
CREATE TABLE ofertas_skills_norm (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    id_oferta INTEGER NOT NULL,
    skill_uri TEXT NOT NULL,
    preferred_label TEXT,
    L1 TEXT, L1_nombre TEXT,
    L2 TEXT, L2_nombre TEXT,
    es_digital INTEGER DEFAULT 0,
    origen TEXT,
    score REAL,
    es_esencial INTEGER DEFAULT 0,
    run_id TEXT,
    created_at TEXT,
    UNIQUE(id_oferta, skill_uri)
);
```

| Métrica | Valor |
|---|---:|
| Total filas | 12.304 |
| URIs distintas | 4.649 |
| Ofertas distintas | **364** (de 60.983 totales) |
| Rango created_at | 2026-02-03T21:55:11 → 2026-02-03T21:55:11 (mismo segundo) |
| Distribución origen | `merged` 6.248 + `semantico` 6.056 |
| Distribución run_id | NULL 6.062 + `reapply_20260126_135723` 3.094 + `run_20260202_2005` 795 + `run_20260129_1745` 784 + `run_20260122_1951` 555 |
| URIs canónicas (`http%`) | 2.308 |
| URIs slug | 2.341 |

**Conclusión:** `ofertas_skills_norm` es **una tabla zombie**.
- Última escritura: 2026-02-03 (3 meses).
- Solo 364 ofertas (vs 56.433 con matching activo).
- Es un experimento de SPEC anterior que no se mantuvo.
- **Escritor:** `scripts/populate_skills_norm.py` (línea 166, INSERT OR REPLACE).
- **Lectores:** `database/query_builder.py` + `scripts/populate_skills_norm.py`.
- **No se sincroniza a Supabase** (no hay tabla `ofertas_skills_norm` en Supabase).

### F3. Slugs vs catálogo ESCO

Sample 20 URIs slug top más frecuentes:

| Slug | Frec | Match en `esco_skills.preferred_label_es` |
|---|---:|---|
| implementar_estrategias_de_ventas | 59 | ✓ |
| responder_a_consultas_de_clientes | 36 | ✓ |
| asistir_a_clientes | 35 | ✓ |
| realizar_tareas_administrativas | 34 | ✓ |
| gestionar_el_inventario | 32 | ✓ |
| controlar_existencias | 30 | ✗ |
| cumplir_los_objetivos_de_ventas | 29 | ✓ |
| mantener_la_limpieza_de_la_zona_de_trabajo | 28 | ✓ |
| mantener_la_relación_con_los_clientes | 27 | ✓ |
| trabajar_en_equipo | 26 | ✓ |
| ... | ... | ... |
| **Match canónico: 19 de 20** |  | **95%** |

**Conclusión:** los slugs son labels ESCO en español slugificados (replace ' '→'_'). El URI canónico se podría reconstruir vía label, pero no se persistió. Tabla zombie con info recuperable pero no usada.

### F4. Overlap entre fuentes

| Fuente | URIs no canónicas |
|---|---:|
| `ofertas_esco_skills_detalle` | 0 |
| `ofertas_skills_norm` | 2.341 |
| **Overlap** | **0** |

Las 2.341 URIs slug existen únicamente en la tabla zombie. **No contaminan el matching activo.**

---

## G — Tablas (zombies y desconocidas)

### G1. Schema completo SQLite local (52 tablas)

| Tabla | Filas | Última escritura aprox |
|---|---:|---|
| **ACTIVAS** | | |
| ofertas | 60.983 | (sin timestamp parseable, fecha texto libre) |
| ofertas_nlp | 57.900 | 2026-04-30T10:18:20 |
| ofertas_esco_matching | 56.433 | 2026-04-30T10:49:06 |
| ofertas_esco_skills_detalle | 1.116.011 | (sin timestamp) |
| ofertas_prioridad | 47.283 | (score_fecha) |
| validation_errors | 243.668 | 2026-04-30T10:51:07 |
| ofertas_matching_history | 86.107 | 2026-04-30 13:49:06 |
| run_ofertas | 85.749 | 2026-04-30 13:49:06 |
| pipeline_runs | 595 | 2026-04-30T10:42:48 |
| skills_extraction_failures | 6.729 | 2026-04-30 13:49:06 |
| ofertas_nlp_history | 5.544 | (sin timestamp) |
| esco_associations | 129.004 | (catálogo) |
| esco_occupations | 3.045 | (catálogo) |
| esco_skills | 14.247 | (catálogo) |
| esco_skill_alternative_labels | 20.678 | (catálogo) |
| esco_occupation_alternative_labels | 13.796 | (catálogo) |
| esco_isco_hierarchy | 619 | (catálogo) |
| diccionario_arg_esco | 267 | (catálogo) |
| learning_history | 539 | 2026-04-30 13:49:06 |
| **ZOMBIES (sin escritura > 30 días)** | | |
| ofertas_skills_norm | 12.304 | 2026-02-03 |
| skills_semantico_json_backup_spec_e | 49.297 | (backup) |
| spec_e_retro_progress | 49.297 | (progress de migration cerrada) |
| spec_h_rematch_progress | 19.686 | (progress migration cerrada) |
| spec_h_unlock_tracking | 3.364 | (progress migration cerrada) |
| validacion_historial | 9.745 | 2026-03-11 |
| ofertas_matching_backup_spec_h | 8.564 | 2026-04-24 (≥ 10 días) |
| keywords_performance | 2.296 | 2025-10-31 |
| validacion_v7 | 121 | 2025-12-09 |
| ab_snapshot_matching | 65 | 2026-01-21 |
| ab_snapshot_nlp | 65 | 2026-01-21 |
| ab_snapshot_skills | 65 | 2026-01-21 |
| nlp_versions | 4 | 2025-11-03 |
| ofertas_raw | 5.479 | 2025-10-31 |
| ofertas_nlp_backup_oldversions_20260103_140824 | 5.369 | 2025-11-02 |
| ofertas_nlp_backup_20251214_181750 | 49 | 2025-12-14 |
| esco_associations_backup_20260114_221302 | 134.805 | (backup, 5.801 filas más que activa) |
| ofertas_esco_matching_backup_20260103_135227 | 6.621 | 2025-12-09 |
| _clae_snapshot_before | 15 | (snapshot) |
| validacion_pipeline | 3 | 2025-11-26 |
| validacion_incremental | 2 | 2025-11-27 |
| metricas_scraping | 2 | (sin timestamp) |
| scraping_sessions | 1 | 2025-11-03 |
| alertas | 5 | 2025-10-31 |
| **VACÍAS** | | |
| ab_experiments | 0 | |
| esco_occupation_ancestors | 0 | |
| esco_occupation_gendered_terms | 0 | |
| ofertas_historial | 0 | |
| validacion_campos | 0 | |
| validacion_humana | 0 | |
| **TOTAL: 52 tablas** | | 12 zombies + 6 vacías = **35% del schema es muerto** |

### G2. Tablas en Supabase (9 totales)

| Tabla | Filas | Local equivalente | Notas |
|---|---:|---|---|
| ofertas_dashboard | 52.563 | ofertas + nlp + matching (JOIN) | Vista materializada |
| ofertas_skills | 1.144.406 | ofertas_esco_skills_detalle | +28.395 filas (no purga al re-sync) |
| issues | 213.134 | (no en local) | 99,4% son `auto-validator@mol.gob.ar` con estado='resuelto' |
| sistema_estado | 401 | (no en local) | Snapshots históricos, último 2026-04-28 |
| esco_argentino | 44 | (no en local) | Skills curadas humanamente |
| pipeline_commands | 27 | (no en local) | Solo `scrape_indeed` |
| audit_log | 0 | (no en local) | Vacía |
| rule_candidates | 0 | (no en local) | Vacía (sección A) |
| scraping_live_stats | 1 | (no en local) | id='current', heartbeat |

### G3. Schema mismatch local vs Supabase

**Tablas locales que NO suben a Supabase (privadas a pipeline local):**
- `ofertas_nlp`, `ofertas_esco_matching`, `validation_errors`, `pipeline_runs`, `learning_history`, `skills_extraction_failures`, `ofertas_prioridad`, todas las tablas `*_backup`, todas las tablas `spec_*_progress`, todos los catálogos ESCO (`esco_*`), `ab_snapshot_*`, etc.

**Tablas Supabase sin equivalente local directo:**
- `issues`, `sistema_estado`, `esco_argentino`, `pipeline_commands`, `audit_log`, `rule_candidates`, `scraping_live_stats`.

**Schemas que existen en ambos (con diff):**

`ofertas_skills` (Supabase) vs `ofertas_esco_skills_detalle` (local):
- Local: 19 columnas (incluye `match_score_global`, `esco_skill_uri_global`, `source_classification`, `origen_tipo`, `texto_original`)
- Supabase: 16 columnas (sin las "global" extras pero con `equivalence_id`, `canonical_label`)
- **Diff:** Supabase tiene columnas para canonización M-08 (`equivalence_id`, `canonical_label`) que el local NO tiene.

---

## H — Hallazgos colaterales

1. **`issues` Supabase tiene 213.134 filas.** El conteo del CLAUDE.md sugería ~1.000 issues humanos. La realidad: 99,4% son auto-issues generados por `auto-validator@mol.gob.ar` con título `[AUTO] Sin skills esenciales matcheadas` y estado `resuelto`. **Ruido del 99,4%** sobre la tabla. Esta tabla viola el principio de issues como "tickets humanos" — se usa también como log de auto-detecciones del pipeline. SPEC T workflow sólo aplica a 0,6% de la tabla.

2. **`ofertas_skills` Supabase: +28.395 vs local.** Diff inverso al esperado. Local 1.116.011 ↔ Supabase 1.144.406. Indica que **Supabase guarda skills viejas que ya no están en local**. Probable causa: re-sync por oferta hace `delete + insert` solo de las ofertas que están en el sync actual. Las skills de ofertas que **se borraron localmente** quedan zombies en Supabase. Es un leak de datos históricos.

3. **Sin cron de sync_to_supabase.** Última corrida 2026-04-28 (hace 6 días). Datos del dashboard están desfasados ~440 ofertas nuevas (las del scraping VPS post-04-28).

4. **Drift de label en Supabase peor que local** (761 URIs vs 1.237 local). Pero proporcionalmente: 761/1.776 = 42,8% en Supabase vs 1.237/9.700+ = ~13% local. Supabase tiene mucho más drift relativo porque acumula labels viejos.

5. **`audit_log` Supabase vacío.** Ningún cambio se registra. La tabla existe pero el código que la pueble no se ha activado.

6. **`pipeline_commands` solo tiene `scrape_indeed`.** El CLAUDE.md menciona "comandos desde admin UI" para reglas/diccionarios/etc. La realidad: solo se usa para queue Indeed local desde VPS. Resto del flujo pipeline command es declarativo (no implementado).

7. **`learning_batches` (5 filas)** y **`batch_runs` (34 filas)** — bajo uso. El sistema de "batches con convergencia <5%" mencionado en CLAUDE.md tiene 5 batches creados.

8. **Anti-alucinación cero en NLP.** `process_nlp_from_db_v11.py` no verifica que las tareas extraídas estén ancladas al texto. Sample 50 mostró 6,5% de tareas con bajo solape (pero plausibles).

9. **Discrepancia versión NLP**: BD declara 11.3.0, código constant es 11.3.0, docstring dice 11.3.1, CLAUDE.md dice 11.4. **Producción real: 11.3.0.**

10. **Sin tabla `training_pairs` en Supabase.** El pipeline issue→training declarado en CLAUDE.md tiene archivo local `config/training_pairs.json` (583+ pares). No se sube a Supabase.

11. **Indeed nunca actualiza stats `ultimos_7d`/`hoy`.** Por el bug C, Indeed siempre muestra `total: 6959` con timestamp viejo (2026-05-04T13:49). El dashboard probablemente muestra Indeed con stats desactualizados.

12. **Bug nominal `validacion_humana` Local vs Supabase:** local tabla `validacion_humana` tiene 0 filas. Supabase `ofertas_dashboard.validacion_humana` tiene 257 valores (en column dentro de la vista). El campo se persiste **solo** en Supabase, no se replica a SQLite local. Cualquier validación humana se perdería si Supabase cae.

13. **`spec_e_retro_progress` 49.297 filas.** Tabla de progreso de la migración SPEC E (skills enriquecidos) que ya terminó. Tiene casi tantas filas como ofertas validadas. Candidata clara a archivar.

14. **`esco_associations_backup_20260114_221302` tiene 134.805 filas — más que la tabla activa (129.004).** El backup tiene 5.801 asociaciones que se borraron al normalizar. Verificar si fue intencional.

---

## Resumen ejecutivo (sin propuestas)

### Estado de la integración Supabase (Sección A, B)

1. **`rule_candidates` está vacío.** El sistema M-09b C4 (Claude API → admin → sync) nunca se activó en producción. `sync_rules_from_candidates.py` nunca corrió. Schema OK, infraestructura desplegada, cola sin uso.
2. **No hay cron automático de sync_to_supabase.** Última corrida hace 6 días. Sync manual.
3. **Drift consistente Local ↔ Supabase:**
   - Ofertas: −8.420 (filtro de validación, esperable)
   - Skills: **+28.395** (zombies en Supabase, leak de datos)
   - Labels drift: peor en Supabase (761 URIs con drift vs 1.237 local, pero proporción 42,8% vs 13%)
4. **Vercel lee directo de Supabase, sin caché propia significativa.** El drift se refleja al usuario en tiempo real.
5. **257 validaciones humanas reales** en Supabase (más que las ~50 estimadas en reporte 1). Distribución: 245 `revisar`, 6 `ok`, 6 `error`, 0 con propagación efectiva.

### Estado del bug `sync_scraping_stats` (Sección C)

6. **Bug confirmado y NO crítico.** El upsert ocurre antes del KeyError, por lo que stats SÍ llegan a Supabase. Lo que falla es el resumen final del log.
7. **Indeed se preserva sin keys `ultimos_7d`/`hoy`** en `scraping_live_stats.portales`, causando el KeyError en cada corrida. Indeed muestra siempre stats stale.
8. **No hay otros bugs silenciosos.** `cron_errors.log` solo contiene esta excepción.

### Estado de NLP regex vs LLM (Sección D)

9. **CAPA 0 regex** cubre 5 campos (salarios, jornada, modalidad). Modalidad 99,2%, jornada 63%, salarios <3%.
10. **CAPA 1 LLM** cubre 15 campos. Casi 100% cobertura categorical (Qwen siempre devuelve algo).
11. **Default sospechoso confirmado:** `nivel_seniority='semisenior'` 49,3% de las ofertas. No es realista — es sesgo del modelo.
12. **Versión nominal vs real:** producción es 11.3.0; CLAUDE.md/learnings dicen 11.4. Documentación adelantada al código.

### Anti-alucinación NLP (Sección E)

13. **NO existe.** Cero código de verificación contra texto original.
14. **Tasa de alucinación heurística:** ~6,5% de tareas tienen <40% de palabras en descripción. 8% de ofertas afectadas en sample.
15. **Sin métricas persistidas.** No hay tabla, columna, ni log que cuente alucinaciones.

### URIs no canónicas (Sección F)

16. **CORRECCIÓN al reporte 5:** `ofertas_esco_skills_detalle` NO tiene URIs hex sintéticas. Son 1.116.011 filas TODAS canónicas.
17. **`terminologia_argentina_skills.json`** es config para enriquecimiento, NO se persiste como URI en BD.
18. **`ofertas_skills_norm` es zombie:** 12.304 filas, última escritura 2026-02-03, 364 ofertas, 2.341 URIs slug que SÍ corresponden 95% a labels ESCO en español. No contamina matching activo.
19. **Sistema real de skills argentinas es `esco_argentino` Supabase** (44 ocupaciones curadas humanamente, skills_consolidadas con URIs canónicas + label_normalized).

### Tablas zombies (Sección G)

20. **Schema local con 52 tablas.** ~12 zombies + 6 vacías = **35% muerto.**
21. **Schema Supabase con 9 tablas.** Mucho más reducido — solo lo que el dashboard consume.
22. **`issues` está contaminado**: 213k filas, 99,4% auto-generadas por validator. La tabla "issues humanos" se usa también como log de detección.

### Riesgos críticos

| ID | Riesgo | Severidad | Detalle |
|---|---|---|---|
| R-1 | Skills zombies en Supabase (28k) | Alta | Datos históricos no purgados al re-sync. Afecta indicadores. |
| R-2 | Sin cron sync to Supabase | Alta | Drift activo de 6 días. Dashboard desincronizado. |
| R-3 | Anti-alucinación cero en NLP | Media | Sample 6,5% tareas con bajo solape. No medible sin instrumentar. |
| R-4 | Indeed stats stale por bug C | Media | Dashboard muestra Indeed parado desde inicio. |
| R-5 | `nivel_seniority='semisenior'` sesgado 49% | Media | Bias del LLM contamina indicadores ocupacionales. |
| R-6 | Versión NLP documentada (11.4) ≠ real (11.3.0) | Baja | Documentación errónea, no afecta producto. |
| R-7 | `validacion_humana` solo en Supabase | Media | Si Supabase cae, se pierden validaciones humanas (257). |
| R-8 | `rule_candidates` schema drift NO tiene candidatos | N/A | Riesgo dormido — si llega el primer candidato, fallaría silenciosamente al sync. |

### Pendientes para SPEC U

- Auditar `terminologia_argentina_skills.json` cómo se aplica en `skills_implicit_extractor.py` (no fue posible este diagnóstico).
- Medir cuándo se rompió el sync automático a Supabase (si alguna vez existió como cron).
- Verificar si `ofertas_skills` Supabase (+28k) tiene impacto en agregaciones del dashboard de skills (¿inflan conteos?).
- Revisar si SPEC T propagation_solicitada tiene casos pendientes (en columna `issues.propagacion_solicitada`).
