-- Migration 058: M-10 — Gold Set dinámico en Supabase
--
-- Tabla para almacenar casos de referencia (ground truth) para
-- medir precisión del pipeline de matching ESCO.
-- Reemplaza el archivo estático gold_set_manual_v2.json.

-- ============================================================
-- 1. TABLA gold_set
-- ============================================================

CREATE TABLE IF NOT EXISTS gold_set (
  id              BIGSERIAL PRIMARY KEY,
  id_oferta       TEXT NOT NULL,
  esco_ok         BOOLEAN NOT NULL,
  isco_esperado   TEXT,
  esco_esperado   TEXT,
  tipo_error      TEXT CHECK (tipo_error IS NULL OR tipo_error IN (
    'dominio_incorrecto', 'nivel_incorrecto', 'nivel_jerarquico',
    'homonimia', 'rol_incorrecto', 'rol_primario'
  )),
  comentario      TEXT,
  agregado_por    TEXT NOT NULL,
  agregado_at     TIMESTAMPTZ DEFAULT NOW(),
  version_reglas  TEXT,
  activo          BOOLEAN DEFAULT TRUE,
  UNIQUE(id_oferta)
);

COMMENT ON TABLE gold_set IS 'M-10: Casos de referencia (ground truth) para medir precisión del matching ESCO';

-- ============================================================
-- 2. RLS
-- ============================================================

ALTER TABLE gold_set ENABLE ROW LEVEL SECURITY;

CREATE POLICY "gold_set_read" ON gold_set
  FOR SELECT USING (true);

CREATE POLICY "gold_set_write" ON gold_set
  FOR ALL USING (auth.role() = 'authenticated' OR auth.role() = 'service_role')
  WITH CHECK (auth.role() = 'authenticated' OR auth.role() = 'service_role');

-- ============================================================
-- 3. RPC agregar_a_gold_set (UPSERT)
-- ============================================================

CREATE OR REPLACE FUNCTION agregar_a_gold_set(
  p_id_oferta     TEXT,
  p_esco_ok       BOOLEAN,
  p_isco_esperado TEXT DEFAULT NULL,
  p_esco_esperado TEXT DEFAULT NULL,
  p_tipo_error    TEXT DEFAULT NULL,
  p_comentario    TEXT DEFAULT NULL,
  p_agregado_por  TEXT DEFAULT 'admin',
  p_version_reglas TEXT DEFAULT NULL
)
RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
  v_result RECORD;
  v_is_update BOOLEAN;
BEGIN
  -- Check if already exists
  v_is_update := EXISTS (SELECT 1 FROM gold_set WHERE id_oferta = p_id_oferta);

  INSERT INTO gold_set (
    id_oferta, esco_ok, isco_esperado, esco_esperado,
    tipo_error, comentario, agregado_por, version_reglas
  ) VALUES (
    p_id_oferta, p_esco_ok, p_isco_esperado, p_esco_esperado,
    p_tipo_error, p_comentario, p_agregado_por, p_version_reglas
  )
  ON CONFLICT (id_oferta) DO UPDATE SET
    esco_ok = EXCLUDED.esco_ok,
    isco_esperado = EXCLUDED.isco_esperado,
    esco_esperado = EXCLUDED.esco_esperado,
    tipo_error = EXCLUDED.tipo_error,
    comentario = EXCLUDED.comentario,
    agregado_por = EXCLUDED.agregado_por,
    agregado_at = NOW(),
    version_reglas = EXCLUDED.version_reglas,
    activo = TRUE
  RETURNING * INTO v_result;

  RETURN jsonb_build_object(
    'id', v_result.id,
    'id_oferta', v_result.id_oferta,
    'is_update', v_is_update,
    'total', (SELECT COUNT(*) FROM gold_set WHERE activo = TRUE)
  );
END;
$$;

COMMENT ON FUNCTION agregar_a_gold_set IS 'M-10: UPSERT caso en Gold Set. Retorna id + total actual.';

-- ============================================================
-- 4. RPC get_gold_set_stats
-- ============================================================

CREATE OR REPLACE FUNCTION get_gold_set_stats()
RETURNS JSONB
LANGUAGE sql
STABLE
SECURITY DEFINER
AS $$
  SELECT jsonb_build_object(
    'total', COUNT(*) FILTER (WHERE activo = TRUE),
    'correctos', COUNT(*) FILTER (WHERE activo = TRUE AND esco_ok = TRUE),
    'errores', COUNT(*) FILTER (WHERE activo = TRUE AND esco_ok = FALSE),
    'por_tipo_error', COALESCE(
      (SELECT jsonb_object_agg(tipo_error, cnt)
       FROM (
         SELECT tipo_error, COUNT(*) as cnt
         FROM gold_set
         WHERE activo = TRUE AND esco_ok = FALSE AND tipo_error IS NOT NULL
         GROUP BY tipo_error
       ) t),
      '{}'::JSONB
    ),
    'agregados_este_mes', COUNT(*) FILTER (
      WHERE activo = TRUE
      AND agregado_at >= date_trunc('month', CURRENT_DATE)
    )
  )
  FROM gold_set;
$$;

COMMENT ON FUNCTION get_gold_set_stats IS 'M-10: Estadísticas del Gold Set para KPI dashboard.';
