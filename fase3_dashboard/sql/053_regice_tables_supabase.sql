-- Migration 053a: Crear tablas REGICE en Supabase + RPC get_cursos_for_gap
-- Ejecutar ANTES de cargar datos con el script Python

-- 1. SEDES
CREATE TABLE IF NOT EXISTS regice_sedes (
    sede_code   TEXT PRIMARY KEY,
    descripcion TEXT,
    tipo_efector TEXT,
    provincia   TEXT,
    municipio   TEXT,
    lat         DOUBLE PRECISION,
    lon         DOUBLE PRECISION
);

-- 2. CURSOS
CREATE TABLE IF NOT EXISTS regice_cursos (
    id                  SERIAL PRIMARY KEY,
    denominacion        TEXT NOT NULL,
    denominacion_orig   TEXT,
    grupo               TEXT,
    carga_horaria_modal INTEGER
);

-- 3. CURSOS_SEDES
CREATE TABLE IF NOT EXISTS regice_cursos_sedes (
    id              SERIAL PRIMARY KEY,
    clave_curso     TEXT NOT NULL,
    sede_code       TEXT NOT NULL REFERENCES regice_sedes(sede_code),
    curso_id        INTEGER NOT NULL REFERENCES regice_cursos(id),
    modalidad       TEXT,
    anio_inicio     INTEGER,
    mes_inicio      TEXT,
    anio_fin        INTEGER,
    carga_horaria   INTEGER,
    contraparte     TEXT,
    matricula       INTEGER DEFAULT 0,
    mat_femenina    INTEGER DEFAULT 0,
    mat_18_24       INTEGER DEFAULT 0,
    mat_fomentar    INTEGER DEFAULT 0,
    mat_vat         INTEGER DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_regice_cs_sede ON regice_cursos_sedes(sede_code);
CREATE INDEX IF NOT EXISTS idx_regice_cs_curso ON regice_cursos_sedes(curso_id);

-- 4. CURSOS_ESCO
CREATE TABLE IF NOT EXISTS regice_cursos_esco (
    id                    SERIAL PRIMARY KEY,
    curso_id              INTEGER NOT NULL REFERENCES regice_cursos(id),
    occupation_uri        TEXT,
    classification_method TEXT,
    classification_score  REAL,
    role                  TEXT DEFAULT 'primary',
    status                TEXT DEFAULT 'auto',
    notes                 TEXT
);

CREATE INDEX IF NOT EXISTS idx_regice_ce_curso ON regice_cursos_esco(curso_id);
CREATE INDEX IF NOT EXISTS idx_regice_ce_ocup ON regice_cursos_esco(occupation_uri);

-- 5. CURSOS_SKILLS (crítica para el cruce gap → cursos)
CREATE TABLE IF NOT EXISTS regice_cursos_skills (
    id          SERIAL PRIMARY KEY,
    curso_id    INTEGER NOT NULL REFERENCES regice_cursos(id),
    skill_uri   TEXT,
    skill_label TEXT,
    source      TEXT
);

CREATE INDEX IF NOT EXISTS idx_regice_cskills_curso ON regice_cursos_skills(curso_id);
CREATE INDEX IF NOT EXISTS idx_regice_cskills_skill ON regice_cursos_skills(skill_uri);

-- RLS
ALTER TABLE regice_sedes ENABLE ROW LEVEL SECURITY;
ALTER TABLE regice_cursos ENABLE ROW LEVEL SECURITY;
ALTER TABLE regice_cursos_sedes ENABLE ROW LEVEL SECURITY;
ALTER TABLE regice_cursos_esco ENABLE ROW LEVEL SECURITY;
ALTER TABLE regice_cursos_skills ENABLE ROW LEVEL SECURITY;

CREATE POLICY "regice_sedes_read" ON regice_sedes FOR SELECT USING (true);
CREATE POLICY "regice_cursos_read" ON regice_cursos FOR SELECT USING (true);
CREATE POLICY "regice_cursos_sedes_read" ON regice_cursos_sedes FOR SELECT USING (true);
CREATE POLICY "regice_cursos_esco_read" ON regice_cursos_esco FOR SELECT USING (true);
CREATE POLICY "regice_cursos_skills_read" ON regice_cursos_skills FOR SELECT USING (true);

-- RPC get_cursos_for_gap
CREATE OR REPLACE FUNCTION get_cursos_for_gap(
  p_gap_skill_uris  TEXT[],
  p_provincia       TEXT DEFAULT NULL,
  p_max_results     INT  DEFAULT 20
)
RETURNS TABLE (
  curso_id           INT,
  titulo             TEXT,
  institucion        TEXT,
  provincia          TEXT,
  municipio          TEXT,
  modalidad          TEXT,
  carga_horaria      INT,
  skills_cubiertas   INT,
  total_gap_skills   INT,
  skills_detalle     JSONB
)
LANGUAGE sql STABLE
SECURITY DEFINER
SET statement_timeout = '8s'
AS $$
  SELECT
    rc.id                             AS curso_id,
    rc.denominacion                   AS titulo,
    rs.descripcion                    AS institucion,
    rs.provincia                      AS provincia,
    rs.municipio                      AS municipio,
    rcs.modalidad                     AS modalidad,
    rcs.carga_horaria                 AS carga_horaria,
    COUNT(DISTINCT rcs_k.skill_uri)::INT AS skills_cubiertas,
    array_length(p_gap_skill_uris, 1) AS total_gap_skills,
    jsonb_agg(DISTINCT jsonb_build_object(
      'uri', rcs_k.skill_uri,
      'label', rcs_k.skill_label
    )) AS skills_detalle
  FROM regice_cursos_skills rcs_k
  JOIN regice_cursos rc         ON rcs_k.curso_id = rc.id
  JOIN regice_cursos_sedes rcs  ON rc.id = rcs.curso_id
  JOIN regice_sedes rs          ON rcs.sede_code = rs.sede_code
  WHERE rcs_k.skill_uri = ANY(p_gap_skill_uris)
    AND (p_provincia IS NULL OR rs.provincia = p_provincia)
  GROUP BY rc.id, rc.denominacion, rs.descripcion,
           rs.provincia, rs.municipio, rcs.modalidad, rcs.carga_horaria
  ORDER BY skills_cubiertas DESC, rcs.carga_horaria ASC
  LIMIT p_max_results;
$$;
