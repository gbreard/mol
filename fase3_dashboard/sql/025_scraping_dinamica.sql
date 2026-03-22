-- ============================================================
-- Tabla scraping_dinamica: métricas de dinámica del mercado por día
-- Persiste: nuevas, bajas, republicaciones, activas, vida media
-- Se alimenta desde sync_scraping_daily.py después del post-import
-- ============================================================

CREATE TABLE IF NOT EXISTS scraping_dinamica (
  fecha DATE NOT NULL PRIMARY KEY,
  ofertas_nuevas INT NOT NULL DEFAULT 0,
  ofertas_bajas INT NOT NULL DEFAULT 0,
  ofertas_republicadas INT NOT NULL DEFAULT 0,
  ofertas_activas INT NOT NULL DEFAULT 0,
  grupos_republicados INT NOT NULL DEFAULT 0,
  vida_media_dias REAL,              -- mediana de días activa
  tasa_rotacion REAL,                -- bajas / activas
  tasa_republicacion REAL,           -- republicadas / total
  flujo_neto INT NOT NULL DEFAULT 0, -- nuevas - bajas
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- RLS
ALTER TABLE scraping_dinamica ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Lectura publica scraping_dinamica" ON scraping_dinamica
  FOR SELECT USING (true);

CREATE POLICY "Solo service_role modifica scraping_dinamica" ON scraping_dinamica
  FOR ALL USING (auth.role() = 'service_role');

-- RPC para leer dinámica del mercado
CREATE OR REPLACE FUNCTION get_scraping_dinamica(p_days int DEFAULT 30)
RETURNS json
LANGUAGE plpgsql
STABLE
SECURITY DEFINER
SET statement_timeout = '5s'
AS $$
DECLARE
  v_result json;
  v_dias json;
  v_kpis json;
BEGIN
  -- Serie temporal
  SELECT COALESCE(json_agg(row_to_json(d) ORDER BY d.fecha), '[]'::json)
  INTO v_dias
  FROM (
    SELECT
      fecha,
      ofertas_nuevas,
      ofertas_bajas,
      ofertas_republicadas,
      ofertas_activas,
      flujo_neto,
      vida_media_dias,
      tasa_rotacion,
      tasa_republicacion
    FROM scraping_dinamica
    WHERE fecha >= CURRENT_DATE - (p_days || ' days')::interval
  ) d;

  -- KPIs del período (excluir días masivos >10K de los promedios)
  SELECT json_build_object(
    'total_nuevas', COALESCE(SUM(ofertas_nuevas), 0),
    'total_bajas', COALESCE(SUM(ofertas_bajas), 0),
    'total_republicadas', COALESCE(SUM(ofertas_republicadas), 0),
    'flujo_neto_periodo', COALESCE(SUM(flujo_neto), 0),
    'activas_actual', (SELECT ofertas_activas FROM scraping_dinamica ORDER BY fecha DESC LIMIT 1),
    'tasa_rotacion_promedio', ROUND(COALESCE(
      (SELECT AVG(tasa_rotacion) FROM scraping_dinamica
       WHERE fecha >= CURRENT_DATE - (p_days || ' days')::interval
         AND tasa_rotacion IS NOT NULL
         AND ofertas_nuevas <= 10000 AND ofertas_bajas <= 10000)
    , 0)::numeric, 4),
    'tasa_republicacion_promedio', ROUND(COALESCE(
      (SELECT AVG(tasa_republicacion) FROM scraping_dinamica
       WHERE fecha >= CURRENT_DATE - (p_days || ' days')::interval
         AND tasa_republicacion IS NOT NULL
         AND ofertas_nuevas <= 10000)
    , 0)::numeric, 4),
    'vida_media_promedio', ROUND(COALESCE(
      (SELECT AVG(vida_media_dias) FROM scraping_dinamica
       WHERE fecha >= CURRENT_DATE - (p_days || ' days')::interval
         AND vida_media_dias IS NOT NULL
         AND vida_media_dias < 365)
    , 0)::numeric, 1),
    'dias_con_datos', COUNT(*),
    'dias_masivos', (SELECT COUNT(*) FROM scraping_dinamica
      WHERE fecha >= CURRENT_DATE - (p_days || ' days')::interval
        AND (ofertas_nuevas > 10000 OR ofertas_bajas > 10000))
  )
  INTO v_kpis
  FROM scraping_dinamica
  WHERE fecha >= CURRENT_DATE - (p_days || ' days')::interval;

  v_result := json_build_object(
    'dias', v_dias,
    'kpis', v_kpis,
    'periodo', json_build_object(
      'desde', CURRENT_DATE - (p_days || ' days')::interval,
      'hasta', CURRENT_DATE,
      'dias', p_days
    )
  );

  RETURN v_result;
END;
$$;
