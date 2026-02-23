-- ============================================================
-- RPC: get_skills_resumen(p_filters jsonb)
-- v3: IF/ELSE branches — no CASE WHEN, no IN subquery
-- Unfiltered: direct scan of ofertas_skills (~296K rows)
-- Filtered: JOIN ofertas_skills with ofertas_dashboard
-- ============================================================

CREATE OR REPLACE FUNCTION get_skills_resumen(p_filters jsonb DEFAULT '{}')
RETURNS json
LANGUAGE plpgsql
VOLATILE
SECURITY DEFINER
SET statement_timeout = '15s'
AS $$
DECLARE
  v_result json;
  v_has_filter boolean;
  v_total bigint;
BEGIN
  v_has_filter := (
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

  IF v_has_filter THEN
    -----------------------------------------------------------
    -- PATH A: Con filtros — JOIN ofertas_dashboard
    -----------------------------------------------------------
    CREATE TEMP TABLE _skill_agg ON COMMIT DROP AS
    SELECT
      s.preferred_label,
      s.l1,
      s.l1_nombre,
      s.es_digital,
      COUNT(*) AS cnt
    FROM ofertas_skills s
    JOIN ofertas_dashboard d ON d.id_oferta = s.id_oferta
    WHERE
      (p_filters->>'provincia' IS NULL OR d.provincia = p_filters->>'provincia')
      AND (p_filters->>'fecha_desde' IS NULL OR d.fecha_publicacion >= (p_filters->>'fecha_desde')::date)
      AND (p_filters->>'fecha_hasta' IS NULL OR d.fecha_publicacion <= (p_filters->>'fecha_hasta')::date)
      AND (p_filters->'localidad' IS NULL OR d.localidad = ANY(ARRAY(SELECT jsonb_array_elements_text(p_filters->'localidad'))))
      AND (p_filters->'seniority' IS NULL OR d.nivel_seniority = ANY(ARRAY(SELECT jsonb_array_elements_text(p_filters->'seniority'))))
      AND (p_filters->'modalidad' IS NULL OR d.modalidad = ANY(ARRAY(SELECT jsonb_array_elements_text(p_filters->'modalidad'))))
      AND (p_filters->'sector' IS NULL OR d.clae_descripcion_seccion = ANY(ARRAY(SELECT jsonb_array_elements_text(p_filters->'sector'))))
      AND (p_filters->'ocupaciones' IS NULL OR d.isco_code = ANY(ARRAY(SELECT jsonb_array_elements_text(p_filters->'ocupaciones'))))
      AND (p_filters->'permanencia' IS NULL OR d.categoria_permanencia = ANY(ARRAY(SELECT jsonb_array_elements_text(p_filters->'permanencia'))))
      AND (p_filters->'nivel_educativo' IS NULL OR d.nivel_educativo = ANY(ARRAY(SELECT jsonb_array_elements_text(p_filters->'nivel_educativo'))))
      AND (
        p_filters->>'experiencia' IS NULL
        OR (p_filters->>'experiencia' = 'sin_experiencia' AND d.experiencia_min_anios = 0)
        OR (p_filters->>'experiencia' = '1_2_anios' AND d.experiencia_min_anios BETWEEN 1 AND 2)
        OR (p_filters->>'experiencia' = '3_5_anios' AND d.experiencia_min_anios BETWEEN 3 AND 5)
        OR (p_filters->>'experiencia' = '5_mas' AND d.experiencia_min_anios > 5)
      )
      AND (
        p_filters->>'jornada' IS NULL
        OR d.jornada_laboral = CASE p_filters->>'jornada'
          WHEN 'full_time' THEN 'full-time'
          WHEN 'part_time' THEN 'part-time'
          WHEN 'por_horas' THEN 'por horas'
          ELSE p_filters->>'jornada'
        END
      )
    GROUP BY s.preferred_label, s.l1, s.l1_nombre, s.es_digital;

  ELSE
    -----------------------------------------------------------
    -- PATH B: Sin filtros — scan directo de ofertas_skills
    -----------------------------------------------------------
    CREATE TEMP TABLE _skill_agg ON COMMIT DROP AS
    SELECT
      preferred_label,
      l1,
      l1_nombre,
      es_digital,
      COUNT(*) AS cnt
    FROM ofertas_skills
    GROUP BY preferred_label, l1, l1_nombre, es_digital;

  END IF;

  -- Total (de la tabla pre-agregada, ~5K filas)
  SELECT COALESCE(SUM(cnt), 0) INTO v_total FROM _skill_agg;

  -- Construir JSON de la tabla chica
  SELECT json_build_object(
    'por_l1', (
      SELECT COALESCE(json_agg(row_to_json(t) ORDER BY t.value DESC), '[]'::json)
      FROM (
        SELECT
          l1 AS code,
          COALESCE(l1_nombre, l1) AS name,
          SUM(cnt)::bigint AS value,
          ROUND(SUM(cnt)::numeric / GREATEST(v_total, 1) * 100) AS porcentaje
        FROM _skill_agg
        WHERE l1 IS NOT NULL
        GROUP BY l1, l1_nombre
      ) t
    ),
    'digitales', json_build_object(
      'digitales', COALESCE((SELECT SUM(cnt) FROM _skill_agg WHERE es_digital = TRUE), 0),
      'no_digitales', COALESCE((SELECT SUM(cnt) FROM _skill_agg WHERE es_digital = FALSE), 0),
      'total', v_total
    ),
    'top_skills', (
      SELECT COALESCE(json_agg(row_to_json(t) ORDER BY t.value DESC), '[]'::json)
      FROM (
        SELECT
          preferred_label AS name,
          SUM(cnt)::bigint AS value,
          l1 AS categoria,
          COALESCE(l1_nombre, l1) AS "categoriaNombre",
          BOOL_OR(es_digital) AS es_digital
        FROM _skill_agg
        WHERE preferred_label IS NOT NULL AND l1 IS NOT NULL
        GROUP BY preferred_label, l1, l1_nombre
        ORDER BY SUM(cnt) DESC
        LIMIT 100
      ) t
    )
  ) INTO v_result;

  RETURN v_result;
END;
$$;
