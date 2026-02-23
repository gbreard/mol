-- ============================================================
-- RPC: get_sidebar_counts(p_filters jsonb)
-- Reemplaza: getSectores, getOcupacionesTree
-- Nota: getLocalidadesGroupedByDepartamento sigue como query directa
--       (solo se llama cuando cambia la provincia)
-- ============================================================

CREATE OR REPLACE FUNCTION get_sidebar_counts(p_filters jsonb DEFAULT '{}')
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
  )
  SELECT json_build_object(
    'total_ofertas', (SELECT COUNT(*) FROM filtered),
    'sectores', (
      SELECT COALESCE(json_agg(row_to_json(t)), '[]'::json)
      FROM (
        SELECT
          clae_descripcion_seccion as sector,
          COUNT(*) as count
        FROM filtered
        WHERE clae_descripcion_seccion IS NOT NULL
        GROUP BY clae_descripcion_seccion
        ORDER BY count DESC
      ) t
    ),
    'ocupaciones_tree', (
      SELECT COALESCE(json_agg(row_to_json(g) ORDER BY g.count DESC), '[]'::json)
      FROM (
        SELECT
          mg.major_group,
          mg.count,
          (
            SELECT COALESCE(json_agg(row_to_json(c) ORDER BY c.count DESC), '[]'::json)
            FROM (
              SELECT
                f2.isco_code as id,
                f2.isco_label as label,
                COUNT(*) as count
              FROM filtered f2
              WHERE f2.isco_code IS NOT NULL
                AND SUBSTRING(f2.isco_code FROM 1 FOR 1) = mg.major_group
              GROUP BY f2.isco_code, f2.isco_label
            ) c
          ) as children
        FROM (
          SELECT
            SUBSTRING(isco_code FROM 1 FOR 1) as major_group,
            COUNT(*) as count
          FROM filtered
          WHERE isco_code IS NOT NULL
          GROUP BY SUBSTRING(isco_code FROM 1 FOR 1)
        ) mg
      ) g
    )
  ) INTO v_result;

  RETURN v_result;
END;
$$;
