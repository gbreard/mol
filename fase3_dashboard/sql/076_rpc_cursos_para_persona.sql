-- Migration 076: cursos para cerrar la brecha de una PERSONA (DEMO-MIERCOLES, cambio A).
-- Regla: presenciales solo de la provincia de la persona; a distancia (virtuales) de
-- cualquier provincia. Nunca presenciales de otra provincia. Sin provincia → solo virtuales.
-- modalidad en regice_cursos_sedes: 'PRESENCIAL' | 'DISTANCIA' (no hay semipresencial).
-- Las pantallas sin persona (VIP) siguen usando get_cursos_for_gap (todo el país).
-- Solo lectura.

CREATE OR REPLACE FUNCTION get_cursos_para_persona(
  p_gap_skill_uris TEXT[],
  p_provincia      TEXT DEFAULT NULL,   -- formato regice_sedes.provincia ('Cordoba', 'Capital federal')
  p_min_cubiertas  INT  DEFAULT 1,
  p_max_por_grupo  INT  DEFAULT 10
)
RETURNS TABLE(
  grupo TEXT, curso_id INT, titulo TEXT, institucion TEXT, provincia TEXT, municipio TEXT,
  modalidad TEXT, carga_horaria INT, skills_cubiertas INT, total_gap_skills INT, skills_detalle JSONB
)
LANGUAGE sql STABLE
SECURITY DEFINER
SET search_path = public
SET statement_timeout TO '8s'
AS $$
  WITH base AS (
    SELECT
      CASE WHEN rcs.modalidad = 'PRESENCIAL' THEN 'presencial' ELSE 'virtual' END AS grupo,
      rc.id AS curso_id, rc.denominacion AS titulo, rs.descripcion AS institucion,
      rs.provincia, rs.municipio, rcs.modalidad, rcs.carga_horaria,
      rcs_k.skill_uri, rcs_k.skill_label
    FROM regice_cursos_skills rcs_k
    JOIN regice_cursos rc        ON rcs_k.curso_id = rc.id
    JOIN regice_cursos_sedes rcs ON rc.id = rcs.curso_id
    JOIN regice_sedes rs         ON rcs.sede_code = rs.sede_code
    WHERE rcs_k.skill_uri = ANY(p_gap_skill_uris)
      AND (
        (rcs.modalidad = 'PRESENCIAL' AND p_provincia IS NOT NULL AND rs.provincia = p_provincia)
        OR rcs.modalidad <> 'PRESENCIAL'
      )
  ),
  agrupado AS (
    -- un curso dictado por la misma institución en varias sedes/años cuenta una vez
    SELECT grupo, MIN(curso_id) AS curso_id, titulo, institucion, provincia, municipio, modalidad,
           MIN(carga_horaria) AS carga_horaria,
           COUNT(DISTINCT skill_uri)::INT AS skills_cubiertas,
           jsonb_agg(DISTINCT jsonb_build_object('uri', skill_uri, 'label', skill_label)) AS skills_detalle
    FROM base
    GROUP BY grupo, titulo, institucion, provincia, municipio, modalidad
    HAVING COUNT(DISTINCT skill_uri) >= p_min_cubiertas
  ),
  rankeado AS (
    SELECT a.*, ROW_NUMBER() OVER (
             PARTITION BY a.grupo,
               -- los virtuales se repiten en cada sede que los ofrece: uno por título,
               -- preferentemente el de una sede de la provincia de la persona
               CASE WHEN a.grupo = 'virtual' THEN a.titulo ELSE a.titulo || '|' || a.institucion || '|' || COALESCE(a.municipio, '') END
             ORDER BY (a.provincia = p_provincia) DESC NULLS LAST, a.skills_cubiertas DESC, a.carga_horaria ASC NULLS LAST) AS dup
    FROM agrupado a
  ),
  dedup AS (
    SELECT r.*, ROW_NUMBER() OVER (PARTITION BY r.grupo ORDER BY r.skills_cubiertas DESC, r.carga_horaria ASC NULLS LAST) AS pos2
    FROM rankeado r WHERE r.grupo = 'presencial' OR r.dup = 1
  )
  SELECT grupo, curso_id, titulo, institucion, provincia, municipio, modalidad, carga_horaria,
         skills_cubiertas, array_length(p_gap_skill_uris, 1) AS total_gap_skills, skills_detalle
  FROM dedup
  WHERE pos2 <= p_max_por_grupo
  ORDER BY CASE WHEN grupo = 'presencial' THEN 0 ELSE 1 END, skills_cubiertas DESC, carga_horaria ASC NULLS LAST;
$$;

GRANT EXECUTE ON FUNCTION get_cursos_para_persona(TEXT[], TEXT, INT, INT) TO anon, authenticated;
