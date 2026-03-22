-- ============================================================
-- Tabla scraping_schedule: configuración del calendario de scraping
-- El poller del VPS lee esta tabla para saber cuándo ejecutar
-- ============================================================

CREATE TABLE IF NOT EXISTS scraping_schedule (
  id SERIAL PRIMARY KEY,
  portal TEXT NOT NULL,              -- 'bumeran', 'todos', etc.
  dias_semana INT[] NOT NULL,        -- {1,4} = lunes y jueves (1=lun, 7=dom)
  hora_utc TIME NOT NULL DEFAULT '11:00', -- 08:00 Argentina = 11:00 UTC
  activo BOOLEAN NOT NULL DEFAULT true,
  updated_by TEXT,
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Insertar configuración actual (Lun/Jue 08:00 ARG = 11:00 UTC)
INSERT INTO scraping_schedule (portal, dias_semana, hora_utc, activo, updated_by) VALUES
  ('todos', '{1,4}', '11:00', true, 'sistema')
ON CONFLICT DO NOTHING;

-- RLS
ALTER TABLE scraping_schedule ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Lectura publica scraping_schedule" ON scraping_schedule
  FOR SELECT USING (true);

CREATE POLICY "Solo admin modifica scraping_schedule" ON scraping_schedule
  FOR ALL USING (auth.role() = 'service_role');

-- RPC para leer y actualizar schedule
CREATE OR REPLACE FUNCTION get_scraping_schedule()
RETURNS json
LANGUAGE plpgsql
STABLE
SECURITY DEFINER
AS $$
DECLARE
  v_result json;
BEGIN
  SELECT COALESCE(json_agg(row_to_json(s) ORDER BY s.portal), '[]'::json)
  INTO v_result
  FROM (
    SELECT
      id, portal, dias_semana, hora_utc::text as hora_utc, activo,
      updated_by, updated_at
    FROM scraping_schedule
  ) s;

  RETURN v_result;
END;
$$;
