-- ============================================================
-- Bloque I2a: Config overrides
-- Los JSONs del repo son el fallback. Los cambios desde la UI
-- se guardan acá. El pipeline lee primero el override.
-- ============================================================

CREATE TABLE IF NOT EXISTS config_overrides (
  config_key TEXT NOT NULL PRIMARY KEY,    -- 'matching_rules_business', 'nlp_inference_rules', etc.
  json_value JSONB NOT NULL,               -- el contenido completo del config
  version INT NOT NULL DEFAULT 1,
  updated_by TEXT,
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  changelog JSONB DEFAULT '[]'             -- [{timestamp, user, action, diff_summary}]
);

-- RLS
ALTER TABLE config_overrides ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Lectura publica config_overrides" ON config_overrides FOR SELECT USING (true);
CREATE POLICY "Service role modifica config_overrides" ON config_overrides FOR ALL USING (auth.role() = 'service_role');

-- RPC para leer config con metadata
CREATE OR REPLACE FUNCTION get_config(p_key text)
RETURNS json
LANGUAGE plpgsql
STABLE
SECURITY DEFINER
AS $$
DECLARE
  v_result json;
  v_override record;
BEGIN
  SELECT * INTO v_override FROM config_overrides WHERE config_key = p_key;

  IF v_override IS NULL THEN
    RETURN json_build_object(
      'config_key', p_key,
      'source', 'none',
      'data', NULL,
      'version', 0,
      'updated_by', NULL,
      'updated_at', NULL
    );
  END IF;

  RETURN json_build_object(
    'config_key', p_key,
    'source', 'override',
    'data', v_override.json_value,
    'version', v_override.version,
    'updated_by', v_override.updated_by,
    'updated_at', v_override.updated_at,
    'changelog', v_override.changelog
  );
END;
$$;
