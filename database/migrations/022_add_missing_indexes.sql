-- Migración 022: Índices faltantes para optimización de queries
-- Fecha: 2026-02-03
-- Basado en análisis de queries frecuentes del pipeline

-- ============================================
-- TABLA: ofertas
-- ============================================

-- Búsqueda por estado (activa/baja/expirada)
CREATE INDEX IF NOT EXISTS idx_ofertas_estado_oferta
    ON ofertas(estado_oferta);

-- Búsqueda por fecha de baja (ofertas cerradas)
CREATE INDEX IF NOT EXISTS idx_ofertas_fecha_baja
    ON ofertas(fecha_baja) WHERE fecha_baja IS NOT NULL;

-- Búsqueda por categoría de permanencia
CREATE INDEX IF NOT EXISTS idx_ofertas_categoria_permanencia
    ON ofertas(categoria_permanencia);

-- Compuesto: estado + fecha (para queries de ofertas activas recientes)
CREATE INDEX IF NOT EXISTS idx_ofertas_estado_fecha
    ON ofertas(estado_oferta, fecha_publicacion_iso);

-- ============================================
-- TABLA: ofertas_nlp
-- ============================================

-- Búsqueda por provincia (agregaciones geográficas)
CREATE INDEX IF NOT EXISTS idx_ofertas_nlp_provincia
    ON ofertas_nlp(provincia);

-- Búsqueda por localidad
CREATE INDEX IF NOT EXISTS idx_ofertas_nlp_localidad
    ON ofertas_nlp(localidad);

-- Búsqueda por modalidad (presencial/remoto/híbrido)
CREATE INDEX IF NOT EXISTS idx_ofertas_nlp_modalidad
    ON ofertas_nlp(modalidad);

-- Búsqueda por sector empresa
CREATE INDEX IF NOT EXISTS idx_ofertas_nlp_sector
    ON ofertas_nlp(sector_empresa);

-- Búsqueda por tipo de contrato
CREATE INDEX IF NOT EXISTS idx_ofertas_nlp_contrato
    ON ofertas_nlp(tipo_contrato);

-- Rango salarial (queries de ofertas con salario > X)
CREATE INDEX IF NOT EXISTS idx_ofertas_nlp_salario_min
    ON ofertas_nlp(salario_min) WHERE salario_min IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_ofertas_nlp_salario_max
    ON ofertas_nlp(salario_max) WHERE salario_max IS NOT NULL;

-- Compuesto: provincia + modalidad (query muy común)
CREATE INDEX IF NOT EXISTS idx_ofertas_nlp_provincia_modalidad
    ON ofertas_nlp(provincia, modalidad);

-- Compuesto: área + seniority (para perfiles)
CREATE INDEX IF NOT EXISTS idx_ofertas_nlp_area_seniority
    ON ofertas_nlp(area_funcional, nivel_seniority);

-- CLAE (clasificación AFIP)
CREATE INDEX IF NOT EXISTS idx_ofertas_nlp_clae
    ON ofertas_nlp(clae_code) WHERE clae_code IS NOT NULL;

-- ============================================
-- TABLA: ofertas_esco_matching
-- ============================================

-- Búsqueda por ISCO (agregaciones por ocupación)
CREATE INDEX IF NOT EXISTS idx_matching_isco
    ON ofertas_esco_matching(isco_code);

-- Búsqueda por método de decisión
CREATE INDEX IF NOT EXISTS idx_matching_decision
    ON ofertas_esco_matching(decision_metodo);

-- Score de matching (para filtrar por confianza)
CREATE INDEX IF NOT EXISTS idx_matching_score
    ON ofertas_esco_matching(occupation_match_score);

-- Compuesto: estado + validado (ofertas validadas)
CREATE INDEX IF NOT EXISTS idx_matching_estado_validado
    ON ofertas_esco_matching(estado_validacion, validado_timestamp);

-- Dual: ofertas donde regla y semántico difieren
CREATE INDEX IF NOT EXISTS idx_matching_dual_difieren
    ON ofertas_esco_matching(dual_coinciden) WHERE dual_coinciden = 0;

-- Por regla aplicada (para medir efectividad)
CREATE INDEX IF NOT EXISTS idx_matching_regla
    ON ofertas_esco_matching(regla_aplicada) WHERE regla_aplicada IS NOT NULL;

-- Skills dual: donde difieren
CREATE INDEX IF NOT EXISTS idx_matching_skills_dual_difieren
    ON ofertas_esco_matching(dual_coinciden_skills) WHERE dual_coinciden_skills = 0;

-- ============================================
-- TABLA: ofertas_esco_skills_detalle
-- ============================================

-- Búsqueda por skill_uri (queries "ofertas con X skill")
CREATE INDEX IF NOT EXISTS idx_skills_detalle_uri
    ON ofertas_esco_skills_detalle(esco_skill_uri);

-- Búsqueda por L1
CREATE INDEX IF NOT EXISTS idx_skills_detalle_l1
    ON ofertas_esco_skills_detalle(L1);

-- Búsqueda por L2
CREATE INDEX IF NOT EXISTS idx_skills_detalle_l2
    ON ofertas_esco_skills_detalle(L2);

-- Skills digitales
CREATE INDEX IF NOT EXISTS idx_skills_detalle_digital
    ON ofertas_esco_skills_detalle(es_digital) WHERE es_digital = 1;

-- ============================================
-- TABLA: pipeline_runs
-- ============================================

-- Búsqueda por fecha (runs recientes)
CREATE INDEX IF NOT EXISTS idx_runs_timestamp
    ON pipeline_runs(timestamp);

-- Búsqueda por source (gold_set/produccion)
CREATE INDEX IF NOT EXISTS idx_runs_source
    ON pipeline_runs(source);

-- Búsqueda por versión matching
CREATE INDEX IF NOT EXISTS idx_runs_matching_version
    ON pipeline_runs(matching_version);

-- ============================================
-- TABLA: validation_errors
-- ============================================

-- Errores por severidad (para priorizar)
CREATE INDEX IF NOT EXISTS idx_errors_severidad
    ON validation_errors(severidad);

-- Errores no resueltos por fecha (orden de trabajo)
CREATE INDEX IF NOT EXISTS idx_errors_pendientes_fecha
    ON validation_errors(detectado_timestamp)
    WHERE resuelto = 0;

-- ============================================
-- TABLA: learning_history
-- ============================================

-- Por tipo de evento
CREATE INDEX IF NOT EXISTS idx_learning_evento
    ON learning_history(evento_tipo);

-- Por config modificado
CREATE INDEX IF NOT EXISTS idx_learning_config
    ON learning_history(config_modificado);

-- ============================================
-- TABLA: ofertas_prioridad (si existe)
-- ============================================

-- Compuesto: estado + score (para cola de procesamiento)
CREATE INDEX IF NOT EXISTS idx_prioridad_estado_score
    ON ofertas_prioridad(estado, score_total DESC);

-- Por lote asignado
CREATE INDEX IF NOT EXISTS idx_prioridad_lote
    ON ofertas_prioridad(lote_asignado);

-- ============================================
-- TABLA: esco_occupations
-- ============================================

-- Por ISCO (JOIN con matching)
CREATE INDEX IF NOT EXISTS idx_esco_occ_isco
    ON esco_occupations(isco_code);

-- Por label (búsqueda por nombre)
CREATE INDEX IF NOT EXISTS idx_esco_occ_label
    ON esco_occupations(preferred_label_es);

-- ============================================
-- TABLA: esco_skills
-- ============================================

-- Por label (búsqueda por nombre)
CREATE INDEX IF NOT EXISTS idx_esco_skills_label
    ON esco_skills(preferred_label_es);

-- Por tipo de skill
CREATE INDEX IF NOT EXISTS idx_esco_skills_type
    ON esco_skills(skill_type);

-- ============================================
-- NOTA: Verificar índices existentes
-- ============================================
-- Para ver índices actuales:
--   SELECT name, tbl_name FROM sqlite_master WHERE type='index';
--
-- Para analizar queries lentas:
--   EXPLAIN QUERY PLAN SELECT ...;
