# Diccionario de Datos - SQLite Local

Base de datos: `database/bumeran_scraping.db`
Motor: SQLite 3
Total de tablas: 32

---

## Índice de Tablas

| # | Tabla | Registros | Propósito |
|---|-------|-----------|-----------|
| 1 | [ofertas](#ofertas) | 6,521 | Ofertas scrapeadas (raw) |
| 2 | [ofertas_nlp](#ofertas_nlp) | 5,479 | Extracción NLP |
| 3 | [ofertas_nlp_history](#ofertas_nlp_history) | 6,053 | Historial de versiones NLP |
| 4 | [ofertas_esco_matching](#ofertas_esco_matching) | 6,521 | Resultados de matching ESCO |
| 5 | [ofertas_esco_skills_detalle](#ofertas_esco_skills_detalle) | 0 | Skills detallados por oferta |
| 6 | [ofertas_raw](#ofertas_raw) | 5,479 | JSON crudo del scraping |
| 7 | [ofertas_historial](#ofertas_historial) | 0 | Auditoría de cambios |
| 8 | [ofertas_nlp_v2](#ofertas_nlp_v2) | 0 | NLP versionado (propuesto) |
| 9 | [ofertas_skills](#ofertas_skills) | 0 | Skills normalizados (propuesto) |
| 10 | [esco_occupations](#esco_occupations) | 3,045 | Catálogo ocupaciones ESCO |
| 11 | [esco_skills](#esco_skills) | 14,247 | Catálogo skills ESCO |
| 12 | [esco_associations](#esco_associations) | 0 | Relaciones ocupación-skill |
| 13 | [esco_occupation_alternative_labels](#esco_occupation_alternative_labels) | 13,796 | Sinónimos de ocupaciones |
| 14 | [esco_skill_alternative_labels](#esco_skill_alternative_labels) | 20,422 | Sinónimos de skills |
| 15 | [esco_occupation_ancestors](#esco_occupation_ancestors) | 0 | Jerarquía de ocupaciones |
| 16 | [esco_occupation_gendered_terms](#esco_occupation_gendered_terms) | 0 | Términos con género |
| 17 | [esco_isco_hierarchy](#esco_isco_hierarchy) | 619 | Jerarquía ISCO |
| 18 | [metricas_scraping](#metricas_scraping) | 2 | Métricas de ejecución |
| 19 | [alertas](#alertas) | 5 | Alertas de scraping |
| 20 | [circuit_breaker_stats](#circuit_breaker_stats) | 0 | Stats circuit breaker |
| 21 | [rate_limiter_stats](#rate_limiter_stats) | 0 | Stats rate limiter |
| 22 | [scraping_sessions](#scraping_sessions) | 1 | Sesiones de scraping |
| 23 | [nlp_versions](#nlp_versions) | 4 | Catálogo versiones NLP |
| 24 | [skills](#skills) | 0 | Catálogo skills normalizado |
| 25 | [keywords_performance](#keywords_performance) | 2,296 | Performance de keywords |
| 26 | [keywords_performance_v2](#keywords_performance_v2) | 0 | Performance v2 |
| 27 | [cno_ocupaciones](#cno_ocupaciones) | 0 | Catálogo CNO Argentina |
| 28 | [cno_esco_matches](#cno_esco_matches) | 0 | Mapeo CNO-ESCO |
| 29 | [diccionario_arg_esco](#diccionario_arg_esco) | 46 | Términos argentinos |
| 30 | [sinonimos_regionales](#sinonimos_regionales) | 0 | Sinónimos por país |
| 31 | [schema_migrations](#schema_migrations) | 1 | Control de migraciones |
| 32 | [sqlite_sequence](#sqlite_sequence) | 11 | Secuencias SQLite |

---

## Tablas Core (Scraping + NLP + Matching)

### ofertas

**Propósito:** Tabla principal con ofertas scrapeadas de portales de empleo.

| Columna | Tipo | Null | Default | Descripción |
|---------|------|------|---------|-------------|
| `id_oferta` | INTEGER | NO | - | PK. ID original de Bumeran |
| `id_empresa` | INTEGER | SÍ | - | ID de empresa en Bumeran |
| `titulo` | TEXT | NO | - | Título de la oferta |
| `empresa` | TEXT | SÍ | - | Nombre de la empresa |
| `descripcion` | TEXT | SÍ | - | Descripción completa |
| `confidencial` | INTEGER | SÍ | - | 0=público, 1=confidencial |
| `localizacion` | TEXT | SÍ | - | Ubicación textual |
| `modalidad_trabajo` | TEXT | SÍ | - | Presencial/Remoto/Híbrido |
| `tipo_trabajo` | TEXT | SÍ | - | Full-time/Part-time |
| `fecha_publicacion_original` | TEXT | SÍ | - | Fecha DD-MM-YYYY |
| `fecha_publicacion_iso` | TEXT | SÍ | - | Fecha YYYY-MM-DD |
| `fecha_hora_publicacion_iso` | TEXT | SÍ | - | DateTime ISO 8601 |
| `fecha_modificado_iso` | TEXT | SÍ | - | Última modificación |
| `cantidad_vacantes` | INTEGER | SÍ | - | Número de vacantes |
| `apto_discapacitado` | INTEGER | SÍ | - | 0/1 |
| `id_area` | INTEGER | SÍ | - | Área funcional (Bumeran) |
| `id_subarea` | INTEGER | SÍ | - | Subárea funcional |
| `id_pais` | INTEGER | SÍ | - | ID país |
| `logo_url` | TEXT | SÍ | - | URL logo empresa |
| `empresa_validada` | INTEGER | SÍ | - | 0/1 |
| `empresa_pro` | INTEGER | SÍ | - | 0/1 |
| `promedio_empresa` | REAL | SÍ | - | Rating de empresa |
| `portal` | TEXT | SÍ | - | bumeran/indeed/zonajobs |
| `tipo_aviso` | TEXT | SÍ | - | Tipo de publicación |
| `tiene_preguntas` | INTEGER | SÍ | - | 0/1 |
| `salario_obligatorio` | INTEGER | SÍ | - | 0/1 |
| `url_oferta` | TEXT | SÍ | - | URL completa |
| `scrapeado_en` | TEXT | NO | NOW() | Timestamp de scraping |

**Índices:**
- `idx_ofertas_fecha_pub_iso` (fecha_publicacion_iso)
- `idx_ofertas_empresa` (empresa)
- `idx_ofertas_localizacion` (localizacion)
- `idx_ofertas_scrapeado_en` (scrapeado_en)
- `idx_ofertas_id_area` (id_area)

---

### ofertas_nlp

**Propósito:** Campos extraídos por NLP de cada oferta.

| Columna | Tipo | Null | Default | Descripción |
|---------|------|------|---------|-------------|
| `id_oferta` | TEXT | NO | - | PK/FK a ofertas |
| `experiencia_min_anios` | INTEGER | SÍ | - | Años mínimos requeridos |
| `experiencia_max_anios` | INTEGER | SÍ | - | Años máximos |
| `experiencia_area` | TEXT | SÍ | - | Área de experiencia |
| `nivel_educativo` | TEXT | SÍ | - | secundario/terciario/universitario/posgrado |
| `estado_educativo` | TEXT | SÍ | - | completo/en_curso/incompleto |
| `carrera_especifica` | TEXT | SÍ | - | Carrera requerida |
| `titulo_excluyente` | INTEGER | SÍ | - | 0/1 |
| `idioma_principal` | TEXT | SÍ | - | Idioma requerido |
| `nivel_idioma_principal` | TEXT | SÍ | - | basico/intermedio/avanzado/nativo |
| `idioma_secundario` | TEXT | SÍ | - | Segundo idioma |
| `nivel_idioma_secundario` | TEXT | SÍ | - | Nivel segundo idioma |
| `skills_tecnicas_list` | TEXT | SÍ | - | JSON array de skills técnicas |
| `niveles_skills_list` | TEXT | SÍ | - | JSON array de niveles |
| `soft_skills_list` | TEXT | SÍ | - | JSON array de soft skills |
| `certificaciones_list` | TEXT | SÍ | - | JSON array de certificaciones |
| `salario_min` | REAL | SÍ | - | Salario mínimo |
| `salario_max` | REAL | SÍ | - | Salario máximo |
| `moneda` | TEXT | SÍ | - | ARS/USD/EUR |
| `beneficios_list` | TEXT | SÍ | - | JSON array de beneficios |
| `requisitos_excluyentes_list` | TEXT | SÍ | - | JSON array |
| `requisitos_deseables_list` | TEXT | SÍ | - | JSON array |
| `jornada_laboral` | TEXT | SÍ | - | tiempo_completo/medio_tiempo |
| `horario_flexible` | INTEGER | SÍ | - | 0/1 |
| `nlp_extraction_timestamp` | TEXT | SÍ | - | Cuándo se extrajo |
| `nlp_version` | TEXT | SÍ | - | Versión del extractor |
| `nlp_confidence_score` | REAL | SÍ | - | Score 0-1 |

**Nota:** Esta tabla tiene ~150 columnas en producción (ver migraciones 002-009). La versión del schema_bd.sql muestra solo los campos originales.

**Índices:**
- `idx_ofertas_nlp_area_funcional` (area_funcional)
- `idx_ofertas_nlp_nivel_seniority` (nivel_seniority)

---

### ofertas_esco_matching

**Propósito:** Resultados del matching con taxonomía ESCO.

| Columna | Tipo | Null | Default | Descripción |
|---------|------|------|---------|-------------|
| `id_oferta` | TEXT | NO | - | PK/FK a ofertas |
| `esco_occupation_uri` | TEXT | SÍ | - | URI ocupación ESCO |
| `esco_occupation_label` | TEXT | SÍ | - | Label ocupación |
| `occupation_match_score` | REAL | SÍ | - | Score 0-1 |
| `occupation_match_method` | TEXT | SÍ | - | regla/semantico/diccionario |
| `titulo_normalizado` | TEXT | SÍ | - | Título limpio |
| `titulo_esco_code` | TEXT | SÍ | - | Código ESCO del título |
| `esco_skills_esenciales_json` | TEXT | SÍ | - | JSON skills esenciales |
| `esco_skills_opcionales_json` | TEXT | SÍ | - | JSON skills opcionales |
| `skills_demandados_total` | INTEGER | SÍ | - | Total skills pedidos |
| `skills_matcheados_esco` | INTEGER | SÍ | - | Skills con match ESCO |
| `skills_sin_match_json` | TEXT | SÍ | - | JSON skills sin match |
| `matching_timestamp` | TEXT | SÍ | - | Cuándo se matcheó |
| `matching_version` | TEXT | SÍ | - | Versión del matcher |
| `confidence_score` | REAL | SÍ | - | Confianza general |

**Columnas adicionales (migraciones 005-019):**
- `run_id` - FK a pipeline_runs
- `estado_validacion` - pendiente/en_revision/validado/rechazado
- `validado_timestamp` - Cuándo se validó
- `validado_por` - Quién validó
- `isco_regla` - ISCO de regla de negocio
- `isco_semantico` - ISCO de matching semántico
- `score_semantico` - Score del semántico
- `regla_aplicada` - ID de regla (ej: R_GERENTE_VENTAS)
- `dual_coinciden` - 1=coinciden, 0=difieren, NULL=solo semántico
- `decision_metodo` - Cómo se decidió
- `skills_regla_json` - Skills de regla
- `skills_semantico_json` - Skills de semántico
- `skills_oferta_json` - Skills final (merged)

**Índices:**
- `idx_matching_estado` (estado_validacion)
- `idx_ofertas_esco_matching_run_id` (run_id)
- `idx_dual_coinciden` (dual_coinciden)
- `idx_regla_aplicada` (regla_aplicada)

---

### ofertas_nlp_history

**Propósito:** Historial de todas las versiones de extracción NLP por oferta.

| Columna | Tipo | Null | Default | Descripción |
|---------|------|------|---------|-------------|
| `id` | INTEGER | NO | AUTO | PK |
| `id_oferta` | TEXT | NO | - | FK a ofertas |
| `nlp_version` | TEXT | NO | - | Versión (ej: "3.7.0") |
| `processed_at` | TIMESTAMP | SÍ | NOW() | Cuándo se procesó |
| `extracted_data` | TEXT | SÍ | - | JSON completo |
| `quality_score` | REAL | SÍ | - | Score 0-7 |
| `confidence_score` | REAL | SÍ | - | Score 0-1 |
| `processing_time_ms` | INTEGER | SÍ | - | Tiempo en ms |
| `is_active` | BOOLEAN | SÍ | 0 | Solo una activa por oferta |
| `replaced_by_version` | TEXT | SÍ | - | Versión que la reemplazó |
| `extraction_method` | TEXT | SÍ | - | regex/llm/hybrid |
| `error_message` | TEXT | SÍ | - | Error si falló |

**Índices:**
- `idx_nlp_history_oferta` (id_oferta)
- `idx_nlp_history_version` (nlp_version)
- `idx_nlp_history_active` (is_active)

---

## Tablas ESCO (Catálogos de Referencia)

### esco_occupations

**Propósito:** Catálogo de 3,045 ocupaciones de la taxonomía ESCO.

| Columna | Tipo | Null | Default | Descripción |
|---------|------|------|---------|-------------|
| `occupation_uri` | TEXT | NO | - | PK. URI única ESCO |
| `occupation_uuid` | TEXT | NO | - | UUID único |
| `esco_code` | TEXT | SÍ | - | Código ESCO |
| `isco_code` | TEXT | SÍ | - | Código ISCO-08 |
| `preferred_label_es` | TEXT | NO | - | Nombre en español |
| `description_es` | TEXT | SÍ | - | Descripción en español |
| `scope_note_es` | TEXT | SÍ | - | Notas de alcance |
| `is_regulated` | INTEGER | SÍ | 0 | Profesión regulada |
| `broader_occupation_uri` | TEXT | SÍ | - | FK a ocupación padre |
| `hierarchy_level` | INTEGER | SÍ | - | Nivel en jerarquía |
| `status` | TEXT | SÍ | 'released' | Estado |
| `last_modified` | TEXT | SÍ | - | Última modificación |

---

### esco_skills

**Propósito:** Catálogo de 14,247 skills de la taxonomía ESCO.

| Columna | Tipo | Null | Default | Descripción |
|---------|------|------|---------|-------------|
| `skill_uri` | TEXT | NO | - | PK. URI única ESCO |
| `skill_uuid` | TEXT | NO | - | UUID único |
| `skill_code` | TEXT | SÍ | - | Código ESCO |
| `preferred_label_es` | TEXT | NO | - | Nombre en español |
| `description_es` | TEXT | SÍ | - | Descripción |
| `skill_type` | TEXT | SÍ | - | skill/knowledge/attitude |
| `skill_reusability_level` | TEXT | SÍ | - | transversal/sector_specific/occupation_specific |
| `status` | TEXT | SÍ | 'released' | Estado |
| `last_modified` | TEXT | SÍ | - | Última modificación |

---

### esco_associations

**Propósito:** Relaciones entre ocupaciones y skills (N:M).

| Columna | Tipo | Null | Default | Descripción |
|---------|------|------|---------|-------------|
| `association_uri` | TEXT | NO | - | PK |
| `occupation_uri` | TEXT | NO | - | FK a esco_occupations |
| `skill_uri` | TEXT | NO | - | FK a esco_skills |
| `relation_type` | TEXT | NO | - | 'essential' o 'optional' |
| `skill_type_in_relation` | TEXT | SÍ | - | Tipo de skill en la relación |

---

## Tablas de Tracking y Auditoría

### pipeline_runs

**Propósito:** Registro de cada ejecución del pipeline.

| Columna | Tipo | Null | Default | Descripción |
|---------|------|------|---------|-------------|
| `run_id` | TEXT | NO | - | PK. "run_YYYYMMDD_HHMM" |
| `timestamp` | TEXT | SÍ | - | ISO 8601 |
| `source` | TEXT | SÍ | - | gold_set/produccion/test |
| `description` | TEXT | SÍ | - | Descripción del run |
| `git_branch` | TEXT | SÍ | - | Branch actual |
| `git_commit` | TEXT | SÍ | - | Hash del commit |
| `nlp_version` | TEXT | SÍ | - | Versión NLP usada |
| `matching_version` | TEXT | SÍ | - | Versión matching usada |
| `config_snapshot` | TEXT | SÍ | - | JSON con configs |
| `ofertas_count` | INTEGER | SÍ | - | Ofertas procesadas |
| `ofertas_ids` | TEXT | SÍ | - | JSON array de IDs |
| `metricas_precision` | REAL | SÍ | - | Precisión 0-1 |
| `errores_detectados` | INTEGER | SÍ | - | Errores encontrados |
| `errores_corregidos` | INTEGER | SÍ | - | Errores corregidos |
| `delta_reglas` | INTEGER | SÍ | - | Reglas nuevas |

---

### validation_errors

**Propósito:** Errores detectados por auto_validator.

| Columna | Tipo | Null | Default | Descripción |
|---------|------|------|---------|-------------|
| `id` | INTEGER | NO | AUTO | PK |
| `id_oferta` | INTEGER | SÍ | - | FK a ofertas |
| `run_id` | TEXT | SÍ | - | FK a pipeline_runs |
| `error_id` | TEXT | SÍ | - | Código error (ej: V02_isco_nulo) |
| `error_tipo` | TEXT | SÍ | - | error_matching/error_nlp |
| `severidad` | TEXT | SÍ | - | critico/alto/medio/bajo |
| `mensaje` | TEXT | SÍ | - | Descripción del error |
| `campo_afectado` | TEXT | SÍ | - | Campo con problema |
| `valor_actual` | TEXT | SÍ | - | Valor incorrecto |
| `corregido` | INTEGER | SÍ | 0 | 0/1 |
| `corregido_timestamp` | TEXT | SÍ | - | Cuándo se corrigió |
| `escalado_claude` | INTEGER | SÍ | 0 | Si requiere revisión |
| `resuelto` | INTEGER | SÍ | 0 | Si está resuelto |

**Índices:**
- `idx_validation_errors_oferta` (id_oferta)
- `idx_validation_errors_no_resuelto` (resuelto, severidad)
- `idx_validation_errors_escalado` (escalado_claude)

---

### learning_history

**Propósito:** Historial de cambios en configs y reglas.

| Columna | Tipo | Null | Default | Descripción |
|---------|------|------|---------|-------------|
| `id` | INTEGER | NO | AUTO | PK |
| `timestamp` | TEXT | SÍ | - | Cuándo ocurrió |
| `run_id` | TEXT | SÍ | - | FK a pipeline_runs |
| `evento_tipo` | TEXT | SÍ | - | regla_agregada/error_corregido |
| `config_modificado` | TEXT | SÍ | - | Archivo modificado |
| `descripcion` | TEXT | SÍ | - | Qué se cambió |
| `conteo_antes` | INTEGER | SÍ | - | Valor anterior |
| `conteo_despues` | INTEGER | SÍ | - | Valor nuevo |
| `delta` | INTEGER | SÍ | - | Diferencia |
| `detalles` | TEXT | SÍ | - | JSON con detalles |

---

## Tablas de Scraping

### metricas_scraping

**Propósito:** Estadísticas de cada ejecución de scraping.

| Columna | Tipo | Null | Default | Descripción |
|---------|------|------|---------|-------------|
| `id` | INTEGER | NO | AUTO | PK |
| `start_time` | TEXT | NO | - | Inicio (ISO 8601) |
| `end_time` | TEXT | NO | - | Fin |
| `total_time_seconds` | REAL | NO | - | Duración total |
| `pages_scraped` | INTEGER | NO | 0 | Páginas exitosas |
| `pages_failed` | INTEGER | NO | 0 | Páginas fallidas |
| `success_rate` | REAL | SÍ | - | % éxito |
| `offers_total` | INTEGER | NO | 0 | Total ofertas |
| `offers_new` | INTEGER | NO | 0 | Ofertas nuevas |
| `offers_duplicates` | INTEGER | NO | 0 | Duplicadas |
| `errors_count` | INTEGER | NO | 0 | Errores |
| `warnings_count` | INTEGER | NO | 0 | Warnings |
| `query` | TEXT | SÍ | - | Query de búsqueda |

---

### alertas

**Propósito:** Alertas generadas durante scraping.

| Columna | Tipo | Null | Default | Descripción |
|---------|------|------|---------|-------------|
| `id` | INTEGER | NO | AUTO | PK |
| `metrica_id` | INTEGER | SÍ | - | FK a metricas_scraping |
| `timestamp` | TEXT | NO | - | Cuándo ocurrió |
| `level` | TEXT | NO | - | INFO/WARNING/ERROR/CRITICAL |
| `type` | TEXT | NO | - | scraping/validation/circuit_breaker |
| `message` | TEXT | NO | - | Mensaje de alerta |
| `context` | TEXT | SÍ | - | JSON con contexto |

---

## Tablas Auxiliares

### diccionario_arg_esco

**Propósito:** Mapeo de términos argentinos a ESCO.

| Columna | Tipo | Null | Default | Descripción |
|---------|------|------|---------|-------------|
| `id` | INTEGER | NO | AUTO | PK |
| `termino_argentino` | TEXT | NO | - | Término local (ej: "cadete") |
| `esco_terms_json` | TEXT | SÍ | - | JSON de términos ESCO |
| `isco_target` | TEXT | SÍ | - | Código ISCO objetivo |
| `esco_preferred_label` | TEXT | SÍ | - | Label ESCO preferido |
| `notes` | TEXT | SÍ | - | Notas |

---

### schema_migrations

**Propósito:** Control de migraciones aplicadas.

| Columna | Tipo | Null | Default | Descripción |
|---------|------|------|---------|-------------|
| `id` | INTEGER | NO | AUTO | PK |
| `version` | TEXT | NO | - | Versión única (ej: "001") |
| `description` | TEXT | SÍ | - | Descripción |
| `applied_at` | TEXT | NO | NOW() | Cuándo se aplicó |
| `applied_by` | TEXT | SÍ | - | Quién la aplicó |
| `execution_time_seconds` | REAL | SÍ | - | Tiempo de ejecución |

---

## Migraciones Aplicadas

| Versión | Descripción | Tablas Afectadas |
|---------|-------------|------------------|
| 001 | Campos de permanencia | ofertas |
| 002 | NLP Schema v5 columnas | ofertas_nlp |
| 003 | NLP Schema v5 completo | ofertas_nlp |
| 004 | Campos NLP faltantes | ofertas_nlp |
| 005 | run_id en matching | ofertas_esco_matching |
| 006 | Sistema de validación | ofertas_esco_matching |
| 007 | Campos CLAE | ofertas_nlp |
| 008 | Sector confianza | ofertas_nlp |
| 009 | Es intermediario | ofertas_nlp |
| 015 | Dual decision tracking | ofertas_esco_matching |
| 016 | Protección validadas | ofertas_esco_matching (trigger) |
| 017 | Tracking history | ofertas_matching_history |
| 018 | Run ofertas relación | run_ofertas |
| 019 | Skills dual | ofertas_esco_matching |
| 020 | Skills L1/L2 agregación | vistas |

---

## Vistas Principales

| Vista | Propósito |
|-------|-----------|
| `v_errores_pendientes` | Errores sin resolver |
| `v_errores_por_tipo` | Resumen por tipo de error |
| `v_dual_decisions` | Distribución de métodos de decisión |
| `v_reglas_efectividad` | Efectividad de reglas |
| `v_skills_por_l1` | Agregación skills por L1 |
| `v_permanencia_ofertas` | Análisis de permanencia |

---

## Changelog

| Fecha | Cambio |
|-------|--------|
| 2026-02-03 | Versión inicial del diccionario |
