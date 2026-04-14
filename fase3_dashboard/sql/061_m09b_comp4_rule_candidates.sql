-- Migration 061: M-09b Componente 4 — rule_candidates + api_anthropic_usage
--
-- Tabla para candidatos de reglas/sinónimos/NLP propuestos por Claude API.
-- Campo JSONB en sistema_estado para tracking de costos API.

-- ============================================================
-- 1. ADD COLUMN api_anthropic_usage en sistema_estado
-- ============================================================

ALTER TABLE sistema_estado
ADD COLUMN IF NOT EXISTS api_anthropic_usage JSONB DEFAULT '{
  "total_llamadas": 0,
  "total_tokens_input": 0,
  "total_tokens_output": 0,
  "costo_usd_estimado": 0.0,
  "ultimo_uso": null,
  "llamadas_hoy": 0,
  "costo_hoy": 0.0,
  "fecha_reset_hoy": null
}'::jsonb;

-- ============================================================
-- 2. CREATE TABLE rule_candidates
-- ============================================================

CREATE TABLE IF NOT EXISTS rule_candidates (
    id              BIGSERIAL PRIMARY KEY,
    oferta_id       TEXT,
    issue_ids       TEXT[],
    tipo            TEXT NOT NULL CHECK (tipo IN (
        'regla_nueva', 'fix_regla', 'fix_bug',
        'sinonimo', 'skills_gold_set',
        'nlp_correccion_sector', 'nlp_area_funcional',
        'nlp_limpieza_tareas', 'nlp_fix_puntual',
        'excepcion_aceptable', 'requiere_revision'
    )),
    propuesta       JSONB NOT NULL,
    justificacion   TEXT,
    confianza       TEXT CHECK (confianza IN ('alta', 'media', 'baja')),
    afecta_otras    BOOLEAN DEFAULT FALSE,
    estado          TEXT DEFAULT 'pendiente' CHECK (estado IN (
        'pendiente', 'aprobado', 'rechazado', 'sincronizado'
    )),
    revisado_por    TEXT,
    revisado_at     TIMESTAMPTZ,
    motivo_rechazo  TEXT,
    generado_por    TEXT DEFAULT 'claude-api',
    batch_id        TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_candidates_estado ON rule_candidates(estado);
CREATE INDEX IF NOT EXISTS idx_candidates_tipo ON rule_candidates(tipo);
CREATE INDEX IF NOT EXISTS idx_candidates_oferta ON rule_candidates(oferta_id);

COMMENT ON TABLE rule_candidates IS 'M-09b C4: Candidatos de reglas/sinónimos/NLP propuestos por Claude API';

-- ============================================================
-- 3. RLS
-- ============================================================

ALTER TABLE rule_candidates ENABLE ROW LEVEL SECURITY;

CREATE POLICY "rule_candidates_read" ON rule_candidates
  FOR SELECT USING (true);

CREATE POLICY "rule_candidates_write" ON rule_candidates
  FOR ALL USING (auth.role() = 'service_role' OR auth.role() = 'authenticated')
  WITH CHECK (auth.role() = 'service_role' OR auth.role() = 'authenticated');

-- ============================================================
-- 4. RPC para actualizar usage (atómico)
-- ============================================================

CREATE OR REPLACE FUNCTION update_api_anthropic_usage(
  p_tokens_input INTEGER,
  p_tokens_output INTEGER
)
RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
  v_current JSONB;
  v_costo_input NUMERIC;
  v_costo_output NUMERIC;
  v_costo_total NUMERIC;
  v_today TEXT;
BEGIN
  v_today := CURRENT_DATE::TEXT;

  -- Calcular costo (Sonnet 4.6 pricing)
  v_costo_input := (p_tokens_input::NUMERIC / 1000000) * 3.00;
  v_costo_output := (p_tokens_output::NUMERIC / 1000000) * 15.00;
  v_costo_total := v_costo_input + v_costo_output;

  -- Obtener usage actual
  SELECT COALESCE(api_anthropic_usage, '{}'::JSONB) INTO v_current
  FROM sistema_estado
  ORDER BY timestamp DESC LIMIT 1;

  -- Reset diario si cambió el día
  IF COALESCE(v_current->>'fecha_reset_hoy', '') != v_today THEN
    v_current := v_current || jsonb_build_object(
      'llamadas_hoy', 0,
      'costo_hoy', 0.0,
      'fecha_reset_hoy', v_today
    );
  END IF;

  -- Actualizar contadores
  v_current := jsonb_build_object(
    'total_llamadas', COALESCE((v_current->>'total_llamadas')::INTEGER, 0) + 1,
    'total_tokens_input', COALESCE((v_current->>'total_tokens_input')::INTEGER, 0) + p_tokens_input,
    'total_tokens_output', COALESCE((v_current->>'total_tokens_output')::INTEGER, 0) + p_tokens_output,
    'costo_usd_estimado', ROUND(COALESCE((v_current->>'costo_usd_estimado')::NUMERIC, 0) + v_costo_total, 4),
    'ultimo_uso', NOW()::TEXT,
    'llamadas_hoy', COALESCE((v_current->>'llamadas_hoy')::INTEGER, 0) + 1,
    'costo_hoy', ROUND(COALESCE((v_current->>'costo_hoy')::NUMERIC, 0) + v_costo_total, 4),
    'fecha_reset_hoy', v_today
  );

  -- Guardar
  UPDATE sistema_estado
  SET api_anthropic_usage = v_current
  WHERE id = (SELECT id FROM sistema_estado ORDER BY timestamp DESC LIMIT 1);

  RETURN v_current;
END;
$$;

-- ============================================================
-- 5. RPC para check rate limit
-- ============================================================

CREATE OR REPLACE FUNCTION check_api_rate_limit(p_max_daily INTEGER DEFAULT 5)
RETURNS JSONB
LANGUAGE sql STABLE
SECURITY DEFINER
AS $$
  SELECT jsonb_build_object(
    'allowed', COALESCE(
      CASE
        WHEN (api_anthropic_usage->>'fecha_reset_hoy') != CURRENT_DATE::TEXT THEN TRUE
        WHEN COALESCE((api_anthropic_usage->>'llamadas_hoy')::INTEGER, 0) < p_max_daily THEN TRUE
        ELSE FALSE
      END,
      TRUE
    ),
    'llamadas_hoy', CASE
      WHEN (api_anthropic_usage->>'fecha_reset_hoy') != CURRENT_DATE::TEXT THEN 0
      ELSE COALESCE((api_anthropic_usage->>'llamadas_hoy')::INTEGER, 0)
    END,
    'max_daily', p_max_daily,
    'costo_hoy', CASE
      WHEN (api_anthropic_usage->>'fecha_reset_hoy') != CURRENT_DATE::TEXT THEN 0.0
      ELSE COALESCE((api_anthropic_usage->>'costo_hoy')::NUMERIC, 0)
    END
  )
  FROM sistema_estado
  ORDER BY timestamp DESC LIMIT 1;
$$;
