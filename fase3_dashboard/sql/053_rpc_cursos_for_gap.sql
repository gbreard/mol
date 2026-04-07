-- Migration 053: RPC get_cursos_for_gap
-- Dado un array de skill URIs del gap, retorna cursos REGICE que cubren esas skills

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
