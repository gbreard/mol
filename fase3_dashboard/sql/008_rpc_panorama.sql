-- ============================================================
-- RPC: get_panorama(p_filters jsonb)
-- Reemplaza: getKPIs, getTopOcupaciones, getOfertasPorProvincia, getOfertasPorModalidad
-- Performance: 1 RPC (~5ms) vs 4 fetchAllPaginated (~500ms)
-- ============================================================

CREATE OR REPLACE FUNCTION get_panorama(p_filters jsonb DEFAULT '{}')
RETURNS json
LANGUAGE plpgsql
STABLE
SECURITY DEFINER
AS $$
DECLARE
  v_result json;
BEGIN
  WITH filtered AS (
    SELECT *
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
    'kpis', (
      SELECT json_build_object(
        'total_ofertas', (SELECT total FROM total_count),
        'ocupaciones_distintas', COUNT(DISTINCT isco_code),
        'empresas_activas', COUNT(DISTINCT empresa),
        'provincias', COUNT(DISTINCT provincia)
      )
      FROM filtered
    ),
    'top_ocupaciones', (
      SELECT COALESCE(json_agg(row_to_json(t)), '[]'::json)
      FROM (
        SELECT isco_code, isco_label as ocupacion, COUNT(*) as cantidad
        FROM filtered
        WHERE isco_code IS NOT NULL AND isco_label IS NOT NULL
        GROUP BY isco_code, isco_label
        ORDER BY cantidad DESC
        LIMIT 100
      ) t
    ),
    'provincias', (
      SELECT COALESCE(json_agg(row_to_json(t)), '[]'::json)
      FROM (
        SELECT
          COALESCE(provincia, 'No especificado') as jurisdiccion,
          COUNT(*) as cantidad,
          ROUND(COUNT(*)::numeric / GREATEST((SELECT total FROM total_count), 1) * 100, 1) as porcentaje
        FROM filtered
        GROUP BY provincia
        ORDER BY cantidad DESC
      ) t
    ),
    'modalidad', (
      SELECT COALESCE(json_agg(row_to_json(t)), '[]'::json)
      FROM (
        SELECT
          COALESCE(modalidad, 'No especificado') as modalidad,
          COUNT(*) as cantidad
        FROM filtered
        GROUP BY modalidad
        ORDER BY cantidad DESC
      ) t
    )
  ) INTO v_result;

  RETURN v_result;
END;
$$;
