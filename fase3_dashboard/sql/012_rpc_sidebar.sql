-- ============================================================
-- RPC: get_sidebar_counts(p_filters jsonb)
-- Reemplaza: getSectores, getOcupacionesTree
-- v2: optimizado para evitar timeout en free tier con 37K+ rows
-- ============================================================

CREATE OR REPLACE FUNCTION get_sidebar_counts(p_filters jsonb DEFAULT '{}')
RETURNS json
LANGUAGE plpgsql
STABLE
SECURITY DEFINER
SET statement_timeout = '8s'
AS $$
DECLARE
  v_result json;
  v_total bigint;
  v_sectores json;
  v_tree json;
  -- Pre-extract filters
  v_provincia text := p_filters->>'provincia';
  v_fecha_desde date := (p_filters->>'fecha_desde')::date;
  v_fecha_hasta date := (p_filters->>'fecha_hasta')::date;
  v_experiencia text := p_filters->>'experiencia';
  v_jornada text := p_filters->>'jornada';
  v_has_localidad boolean := p_filters->'localidad' IS NOT NULL;
  v_has_seniority boolean := p_filters->'seniority' IS NOT NULL;
  v_has_modalidad boolean := p_filters->'modalidad' IS NOT NULL;
  v_has_sector boolean := p_filters->'sector' IS NOT NULL;
  v_has_ocupaciones boolean := p_filters->'ocupaciones' IS NOT NULL;
  v_has_permanencia boolean := p_filters->'permanencia' IS NOT NULL;
  v_has_nivel_edu boolean := p_filters->'nivel_educativo' IS NOT NULL;
BEGIN
  -- Total count
  SELECT COUNT(*) INTO v_total
  FROM ofertas_dashboard
  WHERE
    (v_provincia IS NULL OR provincia = v_provincia)
    AND (v_fecha_desde IS NULL OR fecha_publicacion >= v_fecha_desde)
    AND (v_fecha_hasta IS NULL OR fecha_publicacion <= v_fecha_hasta)
    AND (NOT v_has_localidad OR localidad = ANY(ARRAY(SELECT jsonb_array_elements_text(p_filters->'localidad'))))
    AND (NOT v_has_seniority OR nivel_seniority = ANY(ARRAY(SELECT jsonb_array_elements_text(p_filters->'seniority'))))
    AND (NOT v_has_modalidad OR modalidad = ANY(ARRAY(SELECT jsonb_array_elements_text(p_filters->'modalidad'))))
    AND (NOT v_has_sector OR clae_descripcion_seccion = ANY(ARRAY(SELECT jsonb_array_elements_text(p_filters->'sector'))))
    AND (NOT v_has_ocupaciones OR isco_code = ANY(ARRAY(SELECT jsonb_array_elements_text(p_filters->'ocupaciones'))))
    AND (NOT v_has_permanencia OR categoria_permanencia = ANY(ARRAY(SELECT jsonb_array_elements_text(p_filters->'permanencia'))))
    AND (NOT v_has_nivel_edu OR nivel_educativo = ANY(ARRAY(SELECT jsonb_array_elements_text(p_filters->'nivel_educativo'))))
    AND (
      v_experiencia IS NULL
      OR (v_experiencia = 'sin_experiencia' AND experiencia_min_anios = 0)
      OR (v_experiencia = '1_2_anios' AND experiencia_min_anios BETWEEN 1 AND 2)
      OR (v_experiencia = '3_5_anios' AND experiencia_min_anios BETWEEN 3 AND 5)
      OR (v_experiencia = '5_mas' AND experiencia_min_anios > 5)
    )
    AND (
      v_jornada IS NULL
      OR jornada_laboral = CASE v_jornada
        WHEN 'full_time' THEN 'full-time'
        WHEN 'part_time' THEN 'part-time'
        WHEN 'por_horas' THEN 'por horas'
        ELSE v_jornada
      END
    );

  -- Sectores
  SELECT COALESCE(json_agg(row_to_json(t)), '[]'::json)
  INTO v_sectores
  FROM (
    SELECT clae_descripcion_seccion as sector, COUNT(*) as count
    FROM ofertas_dashboard
    WHERE
      clae_descripcion_seccion IS NOT NULL
      AND (v_provincia IS NULL OR provincia = v_provincia)
      AND (v_fecha_desde IS NULL OR fecha_publicacion >= v_fecha_desde)
      AND (v_fecha_hasta IS NULL OR fecha_publicacion <= v_fecha_hasta)
      AND (NOT v_has_localidad OR localidad = ANY(ARRAY(SELECT jsonb_array_elements_text(p_filters->'localidad'))))
      AND (NOT v_has_seniority OR nivel_seniority = ANY(ARRAY(SELECT jsonb_array_elements_text(p_filters->'seniority'))))
      AND (NOT v_has_modalidad OR modalidad = ANY(ARRAY(SELECT jsonb_array_elements_text(p_filters->'modalidad'))))
      AND (NOT v_has_sector OR clae_descripcion_seccion = ANY(ARRAY(SELECT jsonb_array_elements_text(p_filters->'sector'))))
      AND (NOT v_has_ocupaciones OR isco_code = ANY(ARRAY(SELECT jsonb_array_elements_text(p_filters->'ocupaciones'))))
      AND (NOT v_has_permanencia OR categoria_permanencia = ANY(ARRAY(SELECT jsonb_array_elements_text(p_filters->'permanencia'))))
      AND (NOT v_has_nivel_edu OR nivel_educativo = ANY(ARRAY(SELECT jsonb_array_elements_text(p_filters->'nivel_educativo'))))
      AND (
        v_experiencia IS NULL
        OR (v_experiencia = 'sin_experiencia' AND experiencia_min_anios = 0)
        OR (v_experiencia = '1_2_anios' AND experiencia_min_anios BETWEEN 1 AND 2)
        OR (v_experiencia = '3_5_anios' AND experiencia_min_anios BETWEEN 3 AND 5)
        OR (v_experiencia = '5_mas' AND experiencia_min_anios > 5)
      )
      AND (
        v_jornada IS NULL
        OR jornada_laboral = CASE v_jornada
          WHEN 'full_time' THEN 'full-time'
          WHEN 'part_time' THEN 'part-time'
          WHEN 'por_horas' THEN 'por horas'
          ELSE v_jornada
        END
      )
    GROUP BY clae_descripcion_seccion
    ORDER BY count DESC
  ) t;

  -- Ocupaciones tree: single GROUP BY then aggregate in-memory
  SELECT COALESCE(json_agg(row_to_json(g) ORDER BY g.count DESC), '[]'::json)
  INTO v_tree
  FROM (
    SELECT
      major_group,
      SUM(count)::bigint as count,
      json_agg(json_build_object('id', isco_code, 'label', isco_label, 'count', count) ORDER BY count DESC) as children
    FROM (
      SELECT
        SUBSTRING(isco_code FROM 1 FOR 1) as major_group,
        isco_code,
        isco_label,
        COUNT(*) as count
      FROM ofertas_dashboard
      WHERE
        isco_code IS NOT NULL
        AND (v_provincia IS NULL OR provincia = v_provincia)
        AND (v_fecha_desde IS NULL OR fecha_publicacion >= v_fecha_desde)
        AND (v_fecha_hasta IS NULL OR fecha_publicacion <= v_fecha_hasta)
        AND (NOT v_has_localidad OR localidad = ANY(ARRAY(SELECT jsonb_array_elements_text(p_filters->'localidad'))))
        AND (NOT v_has_seniority OR nivel_seniority = ANY(ARRAY(SELECT jsonb_array_elements_text(p_filters->'seniority'))))
        AND (NOT v_has_modalidad OR modalidad = ANY(ARRAY(SELECT jsonb_array_elements_text(p_filters->'modalidad'))))
        AND (NOT v_has_sector OR clae_descripcion_seccion = ANY(ARRAY(SELECT jsonb_array_elements_text(p_filters->'sector'))))
        AND (NOT v_has_ocupaciones OR isco_code = ANY(ARRAY(SELECT jsonb_array_elements_text(p_filters->'ocupaciones'))))
        AND (NOT v_has_permanencia OR categoria_permanencia = ANY(ARRAY(SELECT jsonb_array_elements_text(p_filters->'permanencia'))))
        AND (NOT v_has_nivel_edu OR nivel_educativo = ANY(ARRAY(SELECT jsonb_array_elements_text(p_filters->'nivel_educativo'))))
        AND (
          v_experiencia IS NULL
          OR (v_experiencia = 'sin_experiencia' AND experiencia_min_anios = 0)
          OR (v_experiencia = '1_2_anios' AND experiencia_min_anios BETWEEN 1 AND 2)
          OR (v_experiencia = '3_5_anios' AND experiencia_min_anios BETWEEN 3 AND 5)
          OR (v_experiencia = '5_mas' AND experiencia_min_anios > 5)
        )
        AND (
          v_jornada IS NULL
          OR jornada_laboral = CASE v_jornada
            WHEN 'full_time' THEN 'full-time'
            WHEN 'part_time' THEN 'part-time'
            WHEN 'por_horas' THEN 'por horas'
            ELSE v_jornada
          END
        )
      GROUP BY isco_code, isco_label
    ) detail
    GROUP BY major_group
  ) g;

  -- Build result
  v_result := json_build_object(
    'total_ofertas', v_total,
    'sectores', v_sectores,
    'ocupaciones_tree', v_tree
  );

  RETURN v_result;
END;
$$;
