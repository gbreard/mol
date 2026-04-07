-- Migration 054b: Solo schema + RPC (sin INSERT — se puebla desde Python)

CREATE TABLE IF NOT EXISTS brecha_formacion_provincial (
  provincia          TEXT NOT NULL,
  skill_uri          TEXT NOT NULL,
  skill_label        TEXT NOT NULL,
  ofertas_count      INTEGER NOT NULL,
  cursos_count       INTEGER NOT NULL,
  estado             TEXT NOT NULL CHECK (estado IN ('brecha', 'cubierta')),
  calculado_en       TIMESTAMPTZ DEFAULT NOW(),
  PRIMARY KEY (provincia, skill_uri)
);

CREATE INDEX IF NOT EXISTS idx_bfp_prov_estado ON brecha_formacion_provincial(provincia, estado);
CREATE INDEX IF NOT EXISTS idx_bfp_prov_ofertas ON brecha_formacion_provincial(provincia, ofertas_count DESC);

ALTER TABLE brecha_formacion_provincial ENABLE ROW LEVEL SECURITY;
CREATE POLICY "bfp_read" ON brecha_formacion_provincial FOR SELECT USING (true);

-- RPC provincial (lee tabla pre-calculada, instantáneo)
CREATE OR REPLACE FUNCTION get_brecha_formacion_provincia(
  p_provincia  TEXT,
  p_estado     TEXT DEFAULT NULL,
  p_limit      INT  DEFAULT 20
)
RETURNS TABLE (
  skill_uri      TEXT,
  skill_label    TEXT,
  ofertas_count  INT,
  cursos_count   INT,
  estado         TEXT
)
LANGUAGE sql STABLE
SECURITY DEFINER
AS $$
  SELECT skill_uri, skill_label, ofertas_count, cursos_count, estado
  FROM brecha_formacion_provincial
  WHERE provincia = p_provincia
    AND (p_estado IS NULL OR estado = p_estado)
  ORDER BY ofertas_count DESC
  LIMIT p_limit;
$$;
