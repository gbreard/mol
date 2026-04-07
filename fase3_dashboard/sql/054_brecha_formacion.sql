-- Migration 054: Brecha de Formación — tabla pre-calculada + 2 RPCs

-- ============================================================
-- 1. Tabla pre-calculada
-- ============================================================

CREATE TABLE IF NOT EXISTS brecha_formacion_skills (
  skill_uri          TEXT NOT NULL,
  skill_label        TEXT NOT NULL,
  ofertas_count      INTEGER NOT NULL,
  cursos_count       INTEGER NOT NULL,
  estado             TEXT NOT NULL
    CHECK (estado IN ('brecha', 'cubierta')),
  calculado_en       TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_bfs_estado ON brecha_formacion_skills(estado);
CREATE INDEX IF NOT EXISTS idx_bfs_ofertas ON brecha_formacion_skills(ofertas_count DESC);

ALTER TABLE brecha_formacion_skills ENABLE ROW LEVEL SECURITY;
CREATE POLICY "bfs_read" ON brecha_formacion_skills FOR SELECT USING (true);

-- ============================================================
-- 2. Poblar tabla
-- ============================================================

INSERT INTO brecha_formacion_skills
  (skill_uri, skill_label, ofertas_count, cursos_count, estado)
SELECT
  os.skill_uri,
  MAX(os.preferred_label)   AS skill_label,
  COUNT(DISTINCT os.id_oferta) AS ofertas_count,
  COUNT(DISTINCT rcs.curso_id) AS cursos_count,
  CASE
    WHEN COUNT(DISTINCT rcs.curso_id) = 0 THEN 'brecha'
    ELSE 'cubierta'
  END AS estado
FROM ofertas_skills os
LEFT JOIN regice_cursos_skills rcs
  ON os.skill_uri = rcs.skill_uri
WHERE os.skill_uri IS NOT NULL
GROUP BY os.skill_uri
ORDER BY ofertas_count DESC;

-- ============================================================
-- 3. RPC nacional (tabla pre-calculada, rápida)
-- ============================================================

CREATE OR REPLACE FUNCTION get_brecha_formacion(
  p_estado   TEXT    DEFAULT NULL,
  p_limit    INT     DEFAULT 20,
  p_offset   INT     DEFAULT 0
)
RETURNS TABLE (
  skill_uri      TEXT,
  skill_label    TEXT,
  ofertas_count  INT,
  cursos_count   INT,
  estado         TEXT,
  pct_mercado    FLOAT
)
LANGUAGE sql STABLE
SECURITY DEFINER
AS $$
  SELECT
    skill_uri,
    skill_label,
    ofertas_count,
    cursos_count,
    estado,
    ROUND(
      (ofertas_count::FLOAT / NULLIF(
        (SELECT SUM(ofertas_count) FROM brecha_formacion_skills), 0
      ) * 100)::NUMERIC, 2
    )::FLOAT AS pct_mercado
  FROM brecha_formacion_skills
  WHERE (p_estado IS NULL OR estado = p_estado)
  ORDER BY ofertas_count DESC
  LIMIT p_limit
  OFFSET p_offset;
$$;

-- ============================================================
-- 4. RPC provincial (tiempo real, con normalización explícita)
-- ============================================================

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
LANGUAGE plpgsql STABLE
SECURITY DEFINER
SET statement_timeout = '8s'
AS $$
DECLARE
  v_prov_regice TEXT;
BEGIN
  -- Normalización MOL → REGICE (CASE explícito, sin unaccent)
  v_prov_regice := CASE lower(p_provincia)
    WHEN 'buenos aires' THEN 'Buenos aires'
    WHEN 'caba' THEN 'Capital federal'
    WHEN 'ciudad de buenos aires' THEN 'Capital federal'
    WHEN 'ciudad autónoma de buenos aires' THEN 'Capital federal'
    WHEN 'capital federal' THEN 'Capital federal'
    WHEN 'catamarca' THEN 'Catamarca'
    WHEN 'chaco' THEN 'Chaco'
    WHEN 'chubut' THEN 'Chubut'
    WHEN 'córdoba' THEN 'Cordoba'
    WHEN 'cordoba' THEN 'Cordoba'
    WHEN 'corrientes' THEN 'Corrientes'
    WHEN 'entre ríos' THEN 'Entre rios'
    WHEN 'entre rios' THEN 'Entre rios'
    WHEN 'formosa' THEN 'Formosa'
    WHEN 'jujuy' THEN 'Jujuy'
    WHEN 'la pampa' THEN 'La pampa'
    WHEN 'la rioja' THEN 'La rioja'
    WHEN 'mendoza' THEN 'Mendoza'
    WHEN 'misiones' THEN 'Misiones'
    WHEN 'neuquén' THEN 'Neuquen'
    WHEN 'neuquen' THEN 'Neuquen'
    WHEN 'río negro' THEN 'Rio negro'
    WHEN 'rio negro' THEN 'Rio negro'
    WHEN 'salta' THEN 'Salta'
    WHEN 'san juan' THEN 'San juan'
    WHEN 'san luis' THEN 'San luis'
    WHEN 'santa cruz' THEN 'Santa cruz'
    WHEN 'santa fe' THEN 'Santa fe'
    WHEN 'santiago del estero' THEN 'Santiago del estero'
    WHEN 'tierra del fuego' THEN 'Tierra del fuego'
    WHEN 'tucumán' THEN 'Tucuman'
    WHEN 'tucuman' THEN 'Tucuman'
    ELSE p_provincia
  END;

  RETURN QUERY
  WITH demanda_prov AS (
    SELECT os.skill_uri, MAX(os.preferred_label) AS skill_label,
           COUNT(DISTINCT os.id_oferta) AS ofertas_count
    FROM ofertas_skills os
    JOIN ofertas_dashboard od ON os.id_oferta = od.id_oferta
    WHERE od.provincia = p_provincia
    GROUP BY os.skill_uri
  ),
  oferta_prov AS (
    SELECT rcs.skill_uri, COUNT(DISTINCT rcs.curso_id) AS cursos_count
    FROM regice_cursos_skills rcs
    JOIN regice_cursos_sedes rcse ON rcs.curso_id = rcse.curso_id
    JOIN regice_sedes rs ON rcse.sede_code = rs.sede_code
    WHERE rs.provincia = v_prov_regice
    GROUP BY rcs.skill_uri
  )
  SELECT
    d.skill_uri,
    d.skill_label,
    d.ofertas_count::INT,
    COALESCE(o.cursos_count, 0)::INT AS cursos_count,
    CASE WHEN COALESCE(o.cursos_count, 0) = 0
         THEN 'brecha' ELSE 'cubierta' END AS estado
  FROM demanda_prov d
  LEFT JOIN oferta_prov o ON d.skill_uri = o.skill_uri
  WHERE (p_estado IS NULL OR
         CASE WHEN COALESCE(o.cursos_count, 0) = 0
              THEN 'brecha' ELSE 'cubierta' END = p_estado)
  ORDER BY d.ofertas_count DESC
  LIMIT p_limit;
END;
$$;
