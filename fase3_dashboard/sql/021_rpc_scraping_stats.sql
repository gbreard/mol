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
      MAX(fecha_publicacion) as ultima_publicacion,
      MAX(created_at::date) as ultimo_scraping,
      (CURRENT_DATE - MAX(fecha_publicacion))::int as dias_sin_publicacion,
      (CURRENT_DATE - MAX(created_at::date))::int as dias_sin_scraping,
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
    -- Portal sin scraping hace más de 3 días
    SELECT
      CASE WHEN dias_sin_scrape > 7 THEN 'error' ELSE 'warning' END as nivel,
      portal,
      portal || ' sin scraping hace ' || dias_sin_scrape || ' dias' as mensaje,
      'Ultimo scraping: ' || ultimo_scrape || ' | Ultima publicacion: ' || ultima_pub as detalle
    FROM (
      SELECT
        portal,
        MAX(created_at::date) as ultimo_scrape,
        MAX(fecha_publicacion) as ultima_pub,
        (CURRENT_DATE - MAX(created_at::date))::int as dias_sin_scrape
      FROM ofertas_dashboard
      WHERE portal IS NOT NULL
      GROUP BY portal
      HAVING (CURRENT_DATE - MAX(created_at::date))::int > 3
    ) inactivos

    UNION ALL

    -- Portal con caída >50% vs semana anterior (solo si tiene datos recientes,
    -- si no ya lo cubre la alerta de "sin datos hace X días")
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
        (CURRENT_DATE - MAX(fecha_publicacion))::int as dias_inactivo,
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
    WHERE pct_caida > 50 AND pct_caida < 100 AND sem_anterior > 10 AND dias_inactivo <= 3

    UNION ALL

    -- Portal scrapeado recientemente pero sin ofertas nuevas
    -- (scraping funciona pero no trae datos — posible bloqueo o scraper roto)
    SELECT
      'warning',
      portal,
      portal || ': scrapeado pero sin ofertas nuevas (ultima publicacion hace ' || dias_pub || ' dias)',
      'Ultimo scraping: ' || ultimo_scrape || ' | Ultima publicacion: ' || ultima_pub
    FROM (
      SELECT
        portal,
        MAX(created_at::date) as ultimo_scrape,
        MAX(fecha_publicacion) as ultima_pub,
        (CURRENT_DATE - MAX(created_at::date))::int as dias_scrape,
        (CURRENT_DATE - MAX(fecha_publicacion))::int as dias_pub
      FROM ofertas_dashboard
      WHERE portal IS NOT NULL
      GROUP BY portal
    ) brecha
    -- Scrapeado en los últimos 3 días pero sin publicaciones en los últimos 7
    WHERE dias_scrape <= 3 AND dias_pub > 7
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
-- p_fecha_tipo: 'publicacion' (default) o 'scraping'
CREATE OR REPLACE FUNCTION get_scraping_history(
  p_days int DEFAULT 14,
  p_fecha_tipo text DEFAULT 'publicacion'
)
RETURNS json
LANGUAGE plpgsql
STABLE
SECURITY DEFINER
SET statement_timeout = '8s'
AS $$
DECLARE
  v_result json;
BEGIN
  IF p_fecha_tipo = 'scraping' THEN
    -- Agrupar por fecha de scraping (created_at)
    SELECT json_build_object(
      'dias', COALESCE(json_agg(row_to_json(d) ORDER BY d.fecha), '[]'::json),
      'periodo', json_build_object(
        'desde', CURRENT_DATE - (p_days || ' days')::interval,
        'hasta', CURRENT_DATE,
        'dias', p_days
      ),
      'tipo_fecha', 'scraping'
    )
    INTO v_result
    FROM (
      SELECT
        fecha,
        SUM(cnt)::int as total,
        json_object_agg(portal, cnt) as por_portal
      FROM (
        SELECT
          created_at::date as fecha,
          COALESCE(portal, 'otro') as portal,
          COUNT(*)::int as cnt
        FROM ofertas_dashboard
        WHERE created_at >= CURRENT_DATE - (p_days || ' days')::interval
          AND created_at IS NOT NULL
        GROUP BY created_at::date, portal
      ) detalle
      GROUP BY fecha
    ) d;
  ELSE
    -- Agrupar por fecha de publicación (default)
    SELECT json_build_object(
      'dias', COALESCE(json_agg(row_to_json(d) ORDER BY d.fecha), '[]'::json),
      'periodo', json_build_object(
        'desde', CURRENT_DATE - (p_days || ' days')::interval,
        'hasta', CURRENT_DATE,
        'dias', p_days
      ),
      'tipo_fecha', 'publicacion'
    )
    INTO v_result
    FROM (
      SELECT
        fecha,
        SUM(cnt)::int as total,
        json_object_agg(portal, cnt) as por_portal
      FROM (
        SELECT
          fecha_publicacion as fecha,
          COALESCE(portal, 'otro') as portal,
          COUNT(*)::int as cnt
        FROM ofertas_dashboard
        WHERE fecha_publicacion >= CURRENT_DATE - (p_days || ' days')::interval
          AND fecha_publicacion IS NOT NULL
        GROUP BY fecha_publicacion, portal
      ) detalle
      GROUP BY fecha
    ) d;
  END IF;

  RETURN v_result;
END;
$$;
