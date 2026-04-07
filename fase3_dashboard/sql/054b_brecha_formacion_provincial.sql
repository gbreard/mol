-- Migration 054b: Brecha formación provincial — tabla pre-calculada
-- La RPC en tiempo real da timeout, pre-calculamos por provincia

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

-- Poblar: para cada provincia de MOL, cruzar demanda vs oferta REGICE
-- Normalización MOL→REGICE inline en el CASE
INSERT INTO brecha_formacion_provincial
  (provincia, skill_uri, skill_label, ofertas_count, cursos_count, estado)
SELECT
  od.provincia,
  os.skill_uri,
  MAX(os.preferred_label) AS skill_label,
  COUNT(DISTINCT os.id_oferta) AS ofertas_count,
  COUNT(DISTINCT rcs.curso_id) AS cursos_count,
  CASE WHEN COUNT(DISTINCT rcs.curso_id) = 0 THEN 'brecha' ELSE 'cubierta' END AS estado
FROM ofertas_skills os
JOIN ofertas_dashboard od ON os.id_oferta = od.id_oferta
LEFT JOIN regice_cursos_skills rcs ON os.skill_uri = rcs.skill_uri
  AND rcs.curso_id IN (
    SELECT rcse.curso_id
    FROM regice_cursos_sedes rcse
    JOIN regice_sedes rs ON rcse.sede_code = rs.sede_code
    WHERE rs.provincia = CASE lower(od.provincia)
      WHEN 'buenos aires' THEN 'Buenos aires'
      WHEN 'caba' THEN 'Capital federal'
      WHEN 'córdoba' THEN 'Cordoba'
      WHEN 'entre ríos' THEN 'Entre rios'
      WHEN 'neuquén' THEN 'Neuquen'
      WHEN 'río negro' THEN 'Rio negro'
      WHEN 'santa fe' THEN 'Santa fe'
      WHEN 'tucumán' THEN 'Tucuman'
      ELSE od.provincia
    END
  )
WHERE os.skill_uri IS NOT NULL
  AND od.provincia IS NOT NULL
GROUP BY od.provincia, os.skill_uri;

-- Reemplazar RPC provincial por lectura de tabla
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
