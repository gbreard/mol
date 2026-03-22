-- ============================================================
-- Tabla scraping_daily: conteos diarios de ofertas crudas por portal
-- Se alimenta desde sync_learnings.py con datos de SQLite local
-- Es la fuente de verdad para el gráfico de scraping (no ofertas_dashboard)
-- ============================================================

CREATE TABLE IF NOT EXISTS scraping_daily (
  fecha DATE NOT NULL,
  portal TEXT NOT NULL,
  ofertas_nuevas INT NOT NULL DEFAULT 0,
  ofertas_acumuladas INT NOT NULL DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  PRIMARY KEY (fecha, portal)
);

-- RLS
ALTER TABLE scraping_daily ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Lectura publica scraping_daily" ON scraping_daily
  FOR SELECT USING (true);

CREATE POLICY "Solo service_role modifica scraping_daily" ON scraping_daily
  FOR ALL USING (auth.role() = 'service_role');

-- RPC para leer historial de scraping crudo
CREATE OR REPLACE FUNCTION get_scraping_daily(
  p_days int DEFAULT 14,
  p_portal text DEFAULT NULL
)
RETURNS json
LANGUAGE plpgsql
STABLE
SECURITY DEFINER
SET statement_timeout = '5s'
AS $$
DECLARE
  v_result json;
BEGIN
  SELECT json_build_object(
    'dias', COALESCE(json_agg(row_to_json(d) ORDER BY d.fecha), '[]'::json),
    'periodo', json_build_object(
      'desde', CURRENT_DATE - (p_days || ' days')::interval,
      'hasta', CURRENT_DATE,
      'dias', p_days
    ),
    'fuente', 'scraping_daily (datos crudos BD local)'
  )
  INTO v_result
  FROM (
    SELECT
      fecha,
      SUM(ofertas_nuevas)::int as total,
      json_object_agg(portal, ofertas_nuevas) as por_portal
    FROM scraping_daily
    WHERE fecha >= CURRENT_DATE - (p_days || ' days')::interval
      AND (p_portal IS NULL OR portal = p_portal)
    GROUP BY fecha
  ) d;

  RETURN v_result;
END;
$$;
