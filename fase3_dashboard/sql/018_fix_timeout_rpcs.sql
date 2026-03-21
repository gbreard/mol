-- ============================================================
-- FIX: Timeout en get_panorama y get_sidebar_counts
-- Problema: con 37K+ rows y filtro de fechas, el CTE materializado
--           causa statement timeout (~3.5s) en Supabase free tier
-- Solución:
--   1. SET statement_timeout = '8s' en cada función
--   2. Eliminar CTE materializado (SELECT *), usar queries directas
--   3. Pre-extraer filtros a variables (evitar reparseo jsonb)
--   4. Sidebar: eliminar nested query en ocupaciones_tree
--
-- EJECUTAR EN: Supabase SQL Editor (https://supabase.com/dashboard)
-- ============================================================

-- También crear índices compuestos para acelerar filtros por fecha
CREATE INDEX IF NOT EXISTS idx_ofertas_fecha_isco_label
  ON ofertas_dashboard(fecha_publicacion, isco_code, isco_label);
CREATE INDEX IF NOT EXISTS idx_ofertas_fecha_provincia
  ON ofertas_dashboard(fecha_publicacion, provincia);
CREATE INDEX IF NOT EXISTS idx_ofertas_fecha_modalidad_idx
  ON ofertas_dashboard(fecha_publicacion, modalidad);
CREATE INDEX IF NOT EXISTS idx_ofertas_fecha_sector
  ON ofertas_dashboard(fecha_publicacion, clae_descripcion_seccion);

-- ============================================================
-- 1. get_panorama v2 (optimizado)
-- ============================================================

CREATE OR REPLACE FUNCTION get_panorama(p_filters jsonb DEFAULT '{}')
RETURNS json
LANGUAGE plpgsql
STABLE
SECURITY DEFINER
SET statement_timeout = '8s'
AS $$
DECLARE
  v_result json;
  v_total bigint;
  v_ocupaciones bigint;
  v_empresas bigint;
  v_provincias bigint;
  v_top_ocup json;
  v_prov json;
  v_modal json;
  -- Pre-extract filters to avoid repeated jsonb parsing
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
  -- KPIs: single scan with COUNT DISTINCT
  SELECT
    COUNT(*),
    COUNT(DISTINCT isco_code),
    COUNT(DISTINCT empresa),
    COUNT(DISTINCT provincia)
  INTO v_total, v_ocupaciones, v_empresas, v_provincias
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

  -- Top ocupaciones
  SELECT COALESCE(json_agg(row_to_json(t)), '[]'::json)
  INTO v_top_ocup
  FROM (
    SELECT isco_code, isco_label as ocupacion, COUNT(*) as cantidad
    FROM ofertas_dashboard
    WHERE
      isco_code IS NOT NULL AND isco_label IS NOT NULL
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
    ORDER BY cantidad DESC
    LIMIT 100
  ) t;

  -- Provincias
  SELECT COALESCE(json_agg(row_to_json(t)), '[]'::json)
  INTO v_prov
  FROM (
    SELECT
      COALESCE(provincia, 'No especificado') as jurisdiccion,
      COUNT(*) as cantidad,
      ROUND(COUNT(*)::numeric / GREATEST(v_total, 1) * 100, 1) as porcentaje
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
      )
    GROUP BY provincia
    ORDER BY cantidad DESC
  ) t;

  -- Modalidad
  SELECT COALESCE(json_agg(row_to_json(t)), '[]'::json)
  INTO v_modal
  FROM (
    SELECT
      COALESCE(modalidad, 'No especificado') as modalidad,
      COUNT(*) as cantidad
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
      )
    GROUP BY modalidad
    ORDER BY cantidad DESC
  ) t;

  -- Build final JSON
  v_result := json_build_object(
    'kpis', json_build_object(
      'total_ofertas', v_total,
      'ocupaciones_distintas', v_ocupaciones,
      'empresas_activas', v_empresas,
      'provincias', v_provincias
    ),
    'top_ocupaciones', v_top_ocup,
    'provincias', v_prov,
    'modalidad', v_modal
  );

  RETURN v_result;
END;
$$;

-- ============================================================
-- 2. get_sidebar_counts v2 (optimizado)
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

  -- Ocupaciones tree: single GROUP BY, aggregate in-memory (no nested query)
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
