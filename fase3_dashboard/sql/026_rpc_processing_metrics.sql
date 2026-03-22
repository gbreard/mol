-- ============================================================
-- Tabla processing_metrics: métricas de procesamiento por corrida
-- Se alimenta desde sync_processing_metrics.py
--
-- RPC get_processing_metrics: agrega todo para el dashboard
-- ============================================================

CREATE TABLE IF NOT EXISTS processing_metrics (
  id SERIAL PRIMARY KEY,
  fecha DATE NOT NULL,
  -- NLP
  nlp_procesadas INT DEFAULT 0,
  nlp_pendientes INT DEFAULT 0,
  nlp_version TEXT,
  -- Matching
  matching_total INT DEFAULT 0,
  matching_por_regla INT DEFAULT 0,
  matching_por_semantico INT DEFAULT 0,
  matching_dual_coinciden INT DEFAULT 0,
  matching_dual_difieren INT DEFAULT 0,
  matching_score_promedio REAL,
  -- Validación
  validacion_ok INT DEFAULT 0,
  validacion_warnings INT DEFAULT 0,
  validacion_errores INT DEFAULT 0,
  errores_resueltos INT DEFAULT 0,
  errores_pendientes INT DEFAULT 0,
  -- Pipeline run
  run_id TEXT,
  ofertas_en_run INT DEFAULT 0,
  precision_run REAL,
  -- Reglas
  reglas_negocio_count INT DEFAULT 0,
  reglas_nuevas INT DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_processing_metrics_fecha ON processing_metrics(fecha DESC);

-- Tabla errores por tipo (resumen)
CREATE TABLE IF NOT EXISTS processing_errors_by_type (
  error_tipo TEXT NOT NULL,
  total INT NOT NULL DEFAULT 0,
  resueltos INT NOT NULL DEFAULT 0,
  pendientes INT NOT NULL DEFAULT 0,
  severidad_predominante TEXT,
  ultimo_detectado DATE,
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  PRIMARY KEY (error_tipo)
);

-- RLS
ALTER TABLE processing_metrics ENABLE ROW LEVEL SECURITY;
ALTER TABLE processing_errors_by_type ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Lectura publica processing_metrics" ON processing_metrics FOR SELECT USING (true);
CREATE POLICY "Service role modifica processing_metrics" ON processing_metrics FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "Lectura publica processing_errors" ON processing_errors_by_type FOR SELECT USING (true);
CREATE POLICY "Service role modifica processing_errors" ON processing_errors_by_type FOR ALL USING (auth.role() = 'service_role');

-- RPC: métricas de procesamiento para el dashboard
CREATE OR REPLACE FUNCTION get_processing_metrics(p_days int DEFAULT 30)
RETURNS json
LANGUAGE plpgsql
STABLE
SECURITY DEFINER
SET statement_timeout = '5s'
AS $$
DECLARE
  v_result json;
  v_timeline json;
  v_errores json;
  v_kpis json;
  v_estado record;
BEGIN
  -- Estado actual del sistema
  SELECT * INTO v_estado
  FROM sistema_estado ORDER BY timestamp DESC LIMIT 1;

  -- Timeline de procesamiento
  SELECT COALESCE(json_agg(row_to_json(d) ORDER BY d.fecha), '[]'::json)
  INTO v_timeline
  FROM (
    SELECT fecha, nlp_procesadas, nlp_pendientes,
           matching_total, matching_por_regla, matching_por_semantico,
           matching_dual_coinciden, matching_dual_difieren,
           matching_score_promedio,
           validacion_ok, validacion_warnings, validacion_errores,
           errores_resueltos, errores_pendientes,
           run_id, ofertas_en_run, precision_run,
           reglas_negocio_count, reglas_nuevas
    FROM processing_metrics
    WHERE fecha >= CURRENT_DATE - (p_days || ' days')::interval
  ) d;

  -- Errores por tipo
  SELECT COALESCE(json_agg(row_to_json(e) ORDER BY e.pendientes DESC), '[]'::json)
  INTO v_errores
  FROM (
    SELECT error_tipo, total, resueltos, pendientes,
           severidad_predominante, ultimo_detectado
    FROM processing_errors_by_type
    WHERE total > 0
  ) e;

  -- KPIs actuales (desde sistema_estado)
  v_kpis := json_build_object(
    'nlp', json_build_object(
      'procesadas', COALESCE(v_estado.fase2_con_nlp, 0),
      'pendientes', COALESCE(v_estado.fase2_sin_nlp, 0),
      'total', COALESCE(v_estado.fase1_ofertas_totales, 0),
      'porcentaje', CASE WHEN v_estado.fase1_ofertas_totales > 0
        THEN ROUND(v_estado.fase2_con_nlp::numeric / v_estado.fase1_ofertas_totales * 100, 1)
        ELSE 0 END
    ),
    'matching', json_build_object(
      'con_matching', COALESCE(v_estado.fase2_con_matching, 0),
      'pendientes', COALESCE(v_estado.fase2_pendientes_matching, 0),
      'validadas', COALESCE(v_estado.fase2_validadas, 0)
    ),
    'sync', json_build_object(
      'en_supabase', COALESCE(v_estado.fase3_ofertas_supabase, 0),
      'pendientes', COALESCE(v_estado.fase3_pendientes_sync, 0)
    ),
    'ultimo_run', v_estado.fase2_ultimo_run
  );

  v_result := json_build_object(
    'timeline', v_timeline,
    'errores_por_tipo', v_errores,
    'kpis', v_kpis,
    'periodo', json_build_object(
      'desde', CURRENT_DATE - (p_days || ' days')::interval,
      'hasta', CURRENT_DATE
    )
  );

  RETURN v_result;
END;
$$;
