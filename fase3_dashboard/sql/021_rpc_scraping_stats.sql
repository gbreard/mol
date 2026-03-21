-- ============================================================
-- RPC: get_scraping_stats()
-- Bloque H1a — estadísticas de scraping por portal
--
-- Lee ofertas_dashboard para obtener:
--   - Conteo por portal
--   - Última fecha de publicación por portal
--   - Ofertas de los últimos 7 días por portal
--   - Detección de anomalías (portal sin datos >3 días o caída >50%)
--
-- RPC: get_scraping_history(p_days int)
-- Bloque H1b — serie temporal de ofertas por día y portal
-- ============================================================

-- H1a: Stats por portal
CREATE OR REPLACE FUNCTION get_scraping_stats()
RETURNS json
LANGUAGE plpgsql
STABLE
SECURITY DEFINER
SET statement_timeout = '8s'
AS $$
DECLARE
  v_result json;
  v_portales json;
  v_alertas json;
  v_totales json;
BEGIN
  -- Stats por portal
  SELECT COALESCE(json_agg(row_to_json(p) ORDER BY p.total DESC), '[]'::json)
  INTO v_portales
  FROM (
    SELECT
      portal,
      COUNT(*) as total,
      COUNT(*) FILTER (WHERE fecha_publicacion >= CURRENT_DATE - INTERVAL '7 days') as ultimos_7d,
      COUNT(*) FILTER (WHERE fecha_publicacion >= CURRENT_DATE - INTERVAL '1 day') as hoy,
      MAX(fecha_publicacion) as ultima_fecha,
      (CURRENT_DATE - MAX(fecha_publicacion))::int as dias_sin_datos,
      ROUND(COUNT(*)::numeric / GREATEST(NULLIF((SELECT COUNT(*) FROM ofertas_dashboard), 0), 1) * 100, 1) as porcentaje
    FROM ofertas_dashboard
    WHERE portal IS NOT NULL
    GROUP BY portal
  ) p;

  -- Totales generales
  SELECT json_build_object(
    'total_ofertas', COUNT(*),
    'total_activas', COUNT(*) FILTER (WHERE estado = 'activa' OR estado IS NULL),
    'portales_activos', COUNT(DISTINCT portal),
    'ultima_fecha_global', MAX(fecha_publicacion),
    'dias_sin_datos_global', (CURRENT_DATE - MAX(fecha_publicacion))::int,
    'ofertas_7d', COUNT(*) FILTER (WHERE fecha_publicacion >= CURRENT_DATE - INTERVAL '7 days'),
    'ofertas_30d', COUNT(*) FILTER (WHERE fecha_publicacion >= CURRENT_DATE - INTERVAL '30 days')
  )
  INTO v_totales
  FROM ofertas_dashboard;

  -- H1c: Detección de anomalías por portal
  SELECT COALESCE(json_agg(
    json_build_object(
      'nivel', a.nivel,
      'portal', a.portal,
      'mensaje', a.mensaje,
      'detalle', a.detalle
    ) ORDER BY CASE a.nivel WHEN 'error' THEN 1 WHEN 'warning' THEN 2 ELSE 3 END
  ), '[]'::json)
  INTO v_alertas
  FROM (
    -- Portal sin datos hace más de 3 días
    SELECT
      CASE WHEN dias_inactivo > 7 THEN 'error' ELSE 'warning' END as nivel,
      portal,
      portal || ' sin ofertas hace ' || dias_inactivo || ' dias' as mensaje,
      'Ultima oferta: ' || ultima_fecha as detalle
    FROM (
      SELECT
        portal,
        MAX(fecha_publicacion) as ultima_fecha,
        (CURRENT_DATE - MAX(fecha_publicacion))::int as dias_inactivo
      FROM ofertas_dashboard
      WHERE portal IS NOT NULL
      GROUP BY portal
      HAVING (CURRENT_DATE - MAX(fecha_publicacion))::int > 3
    ) inactivos

    UNION ALL

    -- Portal con caída >50% vs semana anterior
    SELECT
      'warning',
      portal,
      portal || ': caida del ' || pct_caida || '% vs semana anterior',
      'Sem actual: ' || sem_actual || ', Sem anterior: ' || sem_anterior
    FROM (
      SELECT
        portal,
        COUNT(*) FILTER (WHERE fecha_publicacion >= CURRENT_DATE - INTERVAL '7 days') as sem_actual,
        COUNT(*) FILTER (WHERE fecha_publicacion >= CURRENT_DATE - INTERVAL '14 days'
                         AND fecha_publicacion < CURRENT_DATE - INTERVAL '7 days') as sem_anterior,
        CASE
          WHEN COUNT(*) FILTER (WHERE fecha_publicacion >= CURRENT_DATE - INTERVAL '14 days'
                                AND fecha_publicacion < CURRENT_DATE - INTERVAL '7 days') > 0
          THEN ROUND(
            (1 - COUNT(*) FILTER (WHERE fecha_publicacion >= CURRENT_DATE - INTERVAL '7 days')::numeric /
             COUNT(*) FILTER (WHERE fecha_publicacion >= CURRENT_DATE - INTERVAL '14 days'
                              AND fecha_publicacion < CURRENT_DATE - INTERVAL '7 days')
            ) * 100
          )
          ELSE 0
        END as pct_caida
      FROM ofertas_dashboard
      WHERE portal IS NOT NULL
      GROUP BY portal
    ) cambios
    WHERE pct_caida > 50 AND sem_anterior > 10
  ) a;

  -- Resultado
  v_result := json_build_object(
    'portales', v_portales,
    'totales', v_totales,
    'alertas', v_alertas,
    'timestamp', NOW()
  );

  RETURN v_result;
END;
$$;

-- H1b: Historia diaria por portal
CREATE OR REPLACE FUNCTION get_scraping_history(p_days int DEFAULT 14)
RETURNS json
LANGUAGE plpgsql
STABLE
SECURITY DEFINER
SET statement_timeout = '8s'
AS $$
DECLARE
  v_result json;
BEGIN
  SELECT json_build_object(
    'dias', COALESCE(json_agg(row_to_json(d) ORDER BY d.fecha), '[]'::json),
    'periodo', json_build_object(
      'desde', CURRENT_DATE - (p_days || ' days')::interval,
      'hasta', CURRENT_DATE,
      'dias', p_days
    )
  )
  INTO v_result
  FROM (
    SELECT
      fecha_publicacion as fecha,
      COUNT(*) as total,
      json_object_agg(COALESCE(portal, 'otro'), cnt) as por_portal
    FROM (
      SELECT
        fecha_publicacion,
        portal,
        COUNT(*) as cnt
      FROM ofertas_dashboard
      WHERE fecha_publicacion >= CURRENT_DATE - (p_days || ' days')::interval
        AND fecha_publicacion IS NOT NULL
      GROUP BY fecha_publicacion, portal
    ) detalle
    GROUP BY fecha_publicacion
  ) d;

  RETURN v_result;
END;
$$;
