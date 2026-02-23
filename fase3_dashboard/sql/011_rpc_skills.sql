-- ============================================================
-- RPC: get_skills_resumen(p_filters jsonb)
-- Reemplaza: getSkillsPorCategoriaL1, getSkillsDigitales,
--            getTopSkillsConCategoria, getTopSkillsTecnicas
-- Usa tabla ofertas_skills (join con ofertas_dashboard para filtros)
-- ============================================================

CREATE OR REPLACE FUNCTION get_skills_resumen(p_filters jsonb DEFAULT '{}')
RETURNS json
LANGUAGE plpgsql
STABLE
SECURITY DEFINER
AS $$
DECLARE
  v_result json;
  v_has_global_filter boolean;
BEGIN
  -- Determinar si hay filtros globales que requieren join con ofertas_dashboard
  v_has_global_filter := (
    p_filters->>'provincia' IS NOT NULL
    OR p_filters->>'fecha_desde' IS NOT NULL
    OR p_filters->>'fecha_hasta' IS NOT NULL
    OR p_filters->'localidad' IS NOT NULL
    OR p_filters->'seniority' IS NOT NULL
    OR p_filters->'modalidad' IS NOT NULL
    OR p_filters->'sector' IS NOT NULL
    OR p_filters->'ocupaciones' IS NOT NULL
    OR p_filters->'permanencia' IS NOT NULL
    OR p_filters->'nivel_educativo' IS NOT NULL
    OR p_filters->>'experiencia' IS NOT NULL
    OR p_filters->>'jornada' IS NOT NULL
  );

  WITH filtered_ofertas AS (
    -- Solo hacer join si hay filtros globales
    SELECT id_oferta
    FROM ofertas_dashboard
    WHERE
      v_has_global_filter = TRUE
      AND (p_filters->>'provincia' IS NULL OR provincia = p_filters->>'provincia')
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
  filtered_skills AS (
    SELECT s.*
    FROM ofertas_skills s
    WHERE
      CASE
        WHEN v_has_global_filter THEN s.id_oferta IN (SELECT id_oferta FROM filtered_ofertas)
        ELSE TRUE
      END
  ),
  total_skills AS (
    SELECT COUNT(*) AS total FROM filtered_skills
  )
  SELECT json_build_object(
    'por_l1', (
      SELECT COALESCE(json_agg(row_to_json(t)), '[]'::json)
      FROM (
        SELECT
          l1 as code,
          COALESCE(l1_nombre, l1) as name,
          COUNT(*) as value,
          ROUND(COUNT(*)::numeric / GREATEST((SELECT total FROM total_skills), 1) * 100) as porcentaje
        FROM filtered_skills
        WHERE l1 IS NOT NULL
        GROUP BY l1, l1_nombre
        ORDER BY value DESC
      ) t
    ),
    'digitales', (
      SELECT json_build_object(
        'digitales', COUNT(*) FILTER (WHERE es_digital = TRUE),
        'no_digitales', COUNT(*) FILTER (WHERE es_digital = FALSE),
        'total', COUNT(*)
      )
      FROM filtered_skills
    ),
    'top_skills', (
      SELECT COALESCE(json_agg(row_to_json(t)), '[]'::json)
      FROM (
        SELECT
          preferred_label as name,
          COUNT(*) as value,
          l1 as categoria,
          COALESCE(l1_nombre, l1) as "categoriaNombre",
          BOOL_OR(es_digital) as es_digital
        FROM filtered_skills
        WHERE preferred_label IS NOT NULL AND l1 IS NOT NULL
        GROUP BY preferred_label, l1, l1_nombre
        ORDER BY value DESC
        LIMIT 100
      ) t
    )
  ) INTO v_result;

  RETURN v_result;
END;
$$;
