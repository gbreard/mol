-- ============================================================
-- RPC: get_requerimientos(p_filters jsonb)
-- Reemplaza: getDistribucionRequerimientos (6 forEach loops client-side)
-- Performance: 1 RPC (~5ms) vs fetchAllPaginated + 6 JS loops (~300ms)
-- ============================================================

CREATE OR REPLACE FUNCTION get_requerimientos(p_filters jsonb DEFAULT '{}')
RETURNS json
LANGUAGE plpgsql
STABLE
SECURITY DEFINER
AS $$
DECLARE
  v_result json;
BEGIN
  WITH filtered AS (
    SELECT
      nivel_educativo,
      experiencia_min_anios,
      nivel_seniority,
      modalidad,
      tiene_gente_cargo,
      jornada_laboral
    FROM ofertas_dashboard
    WHERE
      (p_filters->>'provincia' IS NULL OR provincia = p_filters->>'provincia')
      AND (p_filters->>'fecha_desde' IS NULL OR fecha_publicacion >= (p_filters->>'fecha_desde')::date)
      AND (p_filters->>'fecha_hasta' IS NULL OR fecha_publicacion <= (p_filters->>'fecha_hasta')::date)
      AND (p_filters->'localidad' IS NULL OR localidad = ANY(ARRAY(SELECT jsonb_array_elements_text(p_filters->'localidad'))))
      AND (p_filters->'seniority' IS NULL OR nivel_seniority = ANY(ARRAY(SELECT jsonb_array_elements_text(p_filters->'seniority'))))
      AND (p_filters->'modalidad' IS NULL OR modalidad = ANY(ARRAY(SELECT jsonb_array_elements_text(p_filters->'modalidad'))))
      AND (p_filters->'sector' IS NULL OR clae_descripcion_seccion = ANY(ARRAY(SELECT jsonb_array_elements_text(p_filters->'sector'))))
      AND (p_filters->'ocupaciones' IS NULL OR isco_code = ANY(ARRAY(SELECT jsonb_array_elements_text(p_filters->'ocupaciones'))))
      AND (p_filters->'permanencia' IS NULL OR categoria_permanencia = ANY(ARRAY(SELECT jsonb_array_elements_text(p_filters->'permanencia'))))
      AND (p_filters->'nivel_educativo' IS NULL OR nivel_educativo = ANY(ARRAY(SELECT jsonb_array_elements_text(p_filters->'nivel_educativo'))))
      AND (
        p_filters->>'experiencia' IS NULL
        OR (p_filters->>'experiencia' = 'sin_experiencia' AND experiencia_min_anios = 0)
        OR (p_filters->>'experiencia' = '1_2_anios' AND experiencia_min_anios BETWEEN 1 AND 2)
        OR (p_filters->>'experiencia' = '3_5_anios' AND experiencia_min_anios BETWEEN 3 AND 5)
        OR (p_filters->>'experiencia' = '5_mas' AND experiencia_min_anios > 5)
      )
      AND (
        p_filters->>'jornada' IS NULL
        OR jornada_laboral = CASE p_filters->>'jornada'
          WHEN 'full_time' THEN 'full-time'
          WHEN 'part_time' THEN 'part-time'
          WHEN 'por_horas' THEN 'por horas'
          ELSE p_filters->>'jornada'
        END
      )
  ),
  total_count AS (
    SELECT COUNT(*) AS total FROM filtered
  )
  SELECT json_build_object(
    'total', (SELECT total FROM total_count),
    'educacion', (
      SELECT COALESCE(json_agg(row_to_json(t) ORDER BY t.sort_order), '[]'::json)
      FROM (
        SELECT
          COALESCE(nivel_educativo, 'Sin especificar') as name,
          COUNT(*) as value,
          ROUND(COUNT(*)::numeric / GREATEST((SELECT total FROM total_count), 1) * 100) as porcentaje,
          CASE nivel_educativo
            WHEN 'universitario' THEN 1
            WHEN 'terciario' THEN 2
            WHEN 'secundario' THEN 3
            WHEN 'primario' THEN 4
            ELSE 5
          END as sort_order
        FROM filtered
        GROUP BY nivel_educativo
      ) t
    ),
    'experiencia', (
      SELECT COALESCE(json_agg(row_to_json(t) ORDER BY t.sort_order), '[]'::json)
      FROM (
        SELECT
          CASE
            WHEN experiencia_min_anios IS NULL THEN 'Sin especificar'
            WHEN experiencia_min_anios = 0 THEN 'Sin experiencia'
            WHEN experiencia_min_anios <= 2 THEN '1-2 anos'
            WHEN experiencia_min_anios <= 4 THEN '3-4 anos'
            ELSE '5+ anos'
          END as name,
          COUNT(*) as value,
          ROUND(COUNT(*)::numeric / GREATEST((SELECT total FROM total_count), 1) * 100) as porcentaje,
          CASE
            WHEN experiencia_min_anios IS NULL THEN 5
            WHEN experiencia_min_anios = 0 THEN 1
            WHEN experiencia_min_anios <= 2 THEN 2
            WHEN experiencia_min_anios <= 4 THEN 3
            ELSE 4
          END as sort_order
        FROM filtered
        GROUP BY 1, 4
      ) t
    ),
    'seniority', (
      SELECT COALESCE(json_agg(row_to_json(t) ORDER BY t.sort_order), '[]'::json)
      FROM (
        SELECT
          COALESCE(nivel_seniority, 'Sin especificar') as name,
          COUNT(*) as value,
          ROUND(COUNT(*)::numeric / GREATEST((SELECT total FROM total_count), 1) * 100) as porcentaje,
          CASE nivel_seniority
            WHEN 'trainee' THEN 1
            WHEN 'junior' THEN 2
            WHEN 'semisenior' THEN 3
            WHEN 'senior' THEN 4
            WHEN 'manager' THEN 5
            ELSE 6
          END as sort_order
        FROM filtered
        GROUP BY nivel_seniority
      ) t
    ),
    'modalidad', (
      SELECT COALESCE(json_agg(row_to_json(t) ORDER BY t.sort_order), '[]'::json)
      FROM (
        SELECT
          COALESCE(modalidad, 'Sin especificar') as name,
          COUNT(*) as value,
          ROUND(COUNT(*)::numeric / GREATEST((SELECT total FROM total_count), 1) * 100) as porcentaje,
          CASE modalidad
            WHEN 'presencial' THEN 1
            WHEN 'hibrido' THEN 2
            WHEN 'remoto' THEN 3
            ELSE 4
          END as sort_order
        FROM filtered
        GROUP BY modalidad
      ) t
    ),
    'jornada', (
      SELECT COALESCE(json_agg(row_to_json(t) ORDER BY t.sort_order), '[]'::json)
      FROM (
        SELECT
          COALESCE(jornada_laboral, 'Sin especificar') as name,
          COUNT(*) as value,
          ROUND(COUNT(*)::numeric / GREATEST((SELECT total FROM total_count), 1) * 100) as porcentaje,
          CASE jornada_laboral
            WHEN 'full-time' THEN 1
            WHEN 'part-time' THEN 2
            WHEN 'freelance' THEN 3
            ELSE 4
          END as sort_order
        FROM filtered
        GROUP BY jornada_laboral
      ) t
    ),
    'gente_cargo', (
      SELECT COALESCE(json_agg(row_to_json(t)), '[]'::json)
      FROM (
        SELECT
          CASE WHEN tiene_gente_cargo THEN 'Con gente a cargo' ELSE 'Sin gente a cargo' END as name,
          COUNT(*) as value,
          ROUND(COUNT(*)::numeric / GREATEST((SELECT total FROM total_count), 1) * 100) as porcentaje
        FROM filtered
        GROUP BY tiene_gente_cargo
        ORDER BY value DESC
      ) t
    )
  ) INTO v_result;

  RETURN v_result;
END;
$$;
