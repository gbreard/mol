-- Migration 052: Fix timeout en get_evolucion
-- El default de anon role es 3s, la query tarda ~3.7s con 37K rows
-- Agregar SET statement_timeout = '8s' como las otras RPCs

CREATE OR REPLACE FUNCTION get_evolucion(
  p_filters jsonb DEFAULT '{}',
  p_periodos int DEFAULT 13
)
RETURNS json
LANGUAGE plpgsql
STABLE
SECURITY DEFINER
SET statement_timeout = '8s'
AS $$
DECLARE
  v_result json;
  v_fecha_desde date;
  v_fecha_hasta date;
  v_duracion_dias int;
BEGIN
  v_fecha_desde := (p_filters->>'fecha_desde')::date;
  v_fecha_hasta := (p_filters->>'fecha_hasta')::date;

  -- Modo 1: CON filtro de fechas -> periodos comparativos
  IF v_fecha_desde IS NOT NULL THEN
    IF v_fecha_hasta IS NULL THEN
      v_fecha_hasta := CURRENT_DATE;
    END IF;

    v_duracion_dias := GREATEST(1, v_fecha_hasta - v_fecha_desde);

    WITH periodos AS (
      SELECT
        v_fecha_hasta - (i * v_duracion_dias) - v_duracion_dias + 1 AS periodo_desde,
        v_fecha_hasta - (i * v_duracion_dias) AS periodo_hasta,
        (i = 0) AS es_actual
      FROM generate_series(0, LEAST(p_periodos, 52) - 1) AS i
    ),
    filtered_base AS (
      SELECT fecha_publicacion
      FROM ofertas_dashboard
      WHERE
        fecha_publicacion IS NOT NULL
        AND (p_filters->>'provincia' IS NULL OR provincia = p_filters->>'provincia')
        AND (p_filters->'localidad' IS NULL OR localidad = ANY(ARRAY(SELECT jsonb_array_elements_text(p_filters->'localidad'))))
        AND (p_filters->'seniority' IS NULL OR nivel_seniority = ANY(ARRAY(SELECT jsonb_array_elements_text(p_filters->'seniority'))))
        AND (p_filters->'modalidad' IS NULL OR modalidad = ANY(ARRAY(SELECT jsonb_array_elements_text(p_filters->'modalidad'))))
        AND (p_filters->'sector' IS NULL OR clae_descripcion_seccion = ANY(ARRAY(SELECT jsonb_array_elements_text(p_filters->'sector'))))
        AND (p_filters->'ocupaciones' IS NULL OR isco_code = ANY(ARRAY(SELECT jsonb_array_elements_text(p_filters->'ocupaciones'))))
        AND (p_filters->'permanencia' IS NULL OR categoria_permanencia = ANY(ARRAY(SELECT jsonb_array_elements_text(p_filters->'permanencia'))))
    ),
    conteos AS (
      SELECT
        p.periodo_desde,
        p.periodo_hasta,
        p.es_actual,
        COUNT(f.fecha_publicacion) AS ofertas
      FROM periodos p
      LEFT JOIN filtered_base f
        ON f.fecha_publicacion BETWEEN p.periodo_desde AND p.periodo_hasta
      GROUP BY p.periodo_desde, p.periodo_hasta, p.es_actual
    )
    SELECT json_build_object(
      'periodos', COALESCE(json_agg(
        json_build_object(
          'fecha_desde', c.periodo_desde,
          'fecha_hasta', c.periodo_hasta,
          'ofertas', c.ofertas,
          'es_periodo_actual', c.es_actual,
          'label', CASE
            WHEN v_duracion_dias <= 7 THEN
              'Sem ' || TO_CHAR(c.periodo_desde, 'DD/MM')
            WHEN v_duracion_dias <= 31
              AND EXTRACT(MONTH FROM c.periodo_desde) = EXTRACT(MONTH FROM c.periodo_hasta) THEN
              TO_CHAR(c.periodo_desde, 'Mon YYYY')
            ELSE
              TO_CHAR(c.periodo_desde, 'DD/MM') || ' - ' || TO_CHAR(c.periodo_hasta, 'DD/MM')
          END
        )
        ORDER BY c.periodo_desde
      ), '[]'::json),
      'modo', 'comparativo'
    ) INTO v_result
    FROM conteos c;

    RETURN v_result;
  END IF;

  -- Modo 2: SIN filtro de fechas -> agrupar por semana
  WITH filtered_base AS (
    SELECT fecha_publicacion
    FROM ofertas_dashboard
    WHERE
      fecha_publicacion IS NOT NULL
      AND (p_filters->>'provincia' IS NULL OR provincia = p_filters->>'provincia')
      AND (p_filters->'localidad' IS NULL OR localidad = ANY(ARRAY(SELECT jsonb_array_elements_text(p_filters->'localidad'))))
      AND (p_filters->'seniority' IS NULL OR nivel_seniority = ANY(ARRAY(SELECT jsonb_array_elements_text(p_filters->'seniority'))))
      AND (p_filters->'modalidad' IS NULL OR modalidad = ANY(ARRAY(SELECT jsonb_array_elements_text(p_filters->'modalidad'))))
      AND (p_filters->'sector' IS NULL OR clae_descripcion_seccion = ANY(ARRAY(SELECT jsonb_array_elements_text(p_filters->'sector'))))
      AND (p_filters->'ocupaciones' IS NULL OR isco_code = ANY(ARRAY(SELECT jsonb_array_elements_text(p_filters->'ocupaciones'))))
      AND (p_filters->'permanencia' IS NULL OR categoria_permanencia = ANY(ARRAY(SELECT jsonb_array_elements_text(p_filters->'permanencia'))))
  ),
  semanas AS (
    SELECT
      DATE_TRUNC('week', fecha_publicacion)::date AS lunes,
      (DATE_TRUNC('week', fecha_publicacion) + INTERVAL '6 days')::date AS domingo,
      COUNT(*) AS ofertas
    FROM filtered_base
    GROUP BY DATE_TRUNC('week', fecha_publicacion)
    ORDER BY lunes
  ),
  limited AS (
    SELECT * FROM semanas
    ORDER BY lunes DESC
    LIMIT CASE WHEN p_periodos > 0 THEN p_periodos ELSE 999 END
  )
  SELECT json_build_object(
    'periodos', COALESCE(json_agg(
      json_build_object(
        'fecha_desde', s.lunes,
        'fecha_hasta', s.domingo,
        'ofertas', s.ofertas,
        'es_periodo_actual', (s.lunes = (SELECT MAX(lunes) FROM limited)),
        'label', TO_CHAR(s.lunes, 'DD/MM') || ' - ' || TO_CHAR(s.domingo, 'DD/MM')
      )
      ORDER BY s.lunes
    ), '[]'::json),
    'modo', 'semanal'
  ) INTO v_result
  FROM limited s;

  RETURN v_result;
END;
$$;
