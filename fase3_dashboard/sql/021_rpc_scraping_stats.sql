-- ============================================================
-- RPC: get_scraping_stats()
-- Bloque H1a — estadísticas de scraping por portal
--
-- FUENTE DE VERDAD: sistema_estado (reflejo de BD local con TODAS las ofertas)
-- ofertas_dashboard solo tiene las procesadas, NO es la fuente para scraping.
--
-- RPC: get_scraping_history(p_days, p_fecha_tipo)
-- Bloque H1b — serie temporal (usa ofertas_dashboard porque es lo que hay en Supabase)
-- ============================================================

-- H1a: Stats por portal (desde sistema_estado, no ofertas_dashboard)
CREATE OR REPLACE FUNCTION get_scraping_stats()
RETURNS json
LANGUAGE plpgsql
STABLE
SECURITY DEFINER
SET statement_timeout = '8s'
AS $$
DECLARE
  v_result json;
  v_estado record;
  v_portales json;
  v_alertas json;
  v_totales json;
  v_portal_key text;
  v_portal_count int;
BEGIN
  -- Leer último estado del sistema (viene de BD local, tiene TODAS las ofertas)
  SELECT * INTO v_estado
  FROM sistema_estado
  ORDER BY timestamp DESC
  LIMIT 1;

  IF v_estado IS NULL THEN
    RETURN json_build_object('error', 'No hay datos de estado del sistema');
  END IF;

  -- Portales desde fase1_fuentes (BD local, todas las ofertas scrapeadas)
  SELECT COALESCE(json_agg(
    json_build_object(
      'portal', p.key,
      'total', p.value::int,
      'porcentaje', ROUND((p.value::numeric / GREATEST(v_estado.fase1_ofertas_totales, 1)) * 100, 1)
    ) ORDER BY p.value::int DESC
  ), '[]'::json)
  INTO v_portales
  FROM jsonb_each_text(v_estado.fase1_fuentes::jsonb) p;

  -- Enriquecer portales con datos de ofertas_dashboard (fechas de publicación y scraping)
  -- para los portales que SÍ tienen ofertas procesadas
  SELECT COALESCE(json_agg(row_to_json(enriched) ORDER BY enriched.total DESC), '[]'::json)
  INTO v_portales
  FROM (
    SELECT
      p.key as portal,
      p.value::int as total,
      ROUND((p.value::numeric / GREATEST(v_estado.fase1_ofertas_totales, 1)) * 100, 1) as porcentaje,
      COALESCE(od.ultima_publicacion, v_estado.fase1_ultimo_scraping) as ultima_publicacion,
      COALESCE(od.ultimo_scraping, v_estado.fase1_ultimo_scraping) as ultimo_scraping,
      COALESCE((CURRENT_DATE - od.ultima_publicacion)::int, v_estado.fase1_dias_desde_scraping) as dias_sin_publicacion,
      COALESCE((CURRENT_DATE - od.ultimo_scraping)::int, v_estado.fase1_dias_desde_scraping) as dias_sin_scraping,
      COALESCE(od.ultimos_7d, 0) as ultimos_7d,
      COALESCE(od.hoy, 0) as hoy,
      COALESCE(od.en_dashboard, 0) as en_dashboard
    FROM jsonb_each_text(v_estado.fase1_fuentes::jsonb) p
    LEFT JOIN (
      SELECT
        portal,
        MAX(fecha_publicacion) as ultima_publicacion,
        MAX(created_at::date) as ultimo_scraping,
        COUNT(*) FILTER (WHERE fecha_publicacion >= CURRENT_DATE - INTERVAL '7 days') as ultimos_7d,
        COUNT(*) FILTER (WHERE fecha_publicacion >= CURRENT_DATE - INTERVAL '1 day') as hoy,
        COUNT(*) as en_dashboard
      FROM ofertas_dashboard
      WHERE portal IS NOT NULL
      GROUP BY portal
    ) od ON od.portal = p.key
  ) enriched;

  -- Totales (desde sistema_estado, no ofertas_dashboard)
  v_totales := json_build_object(
    'total_ofertas', v_estado.fase1_ofertas_totales,
    'total_activas', v_estado.fase1_ofertas_activas,
    'portales_activos', (SELECT COUNT(*) FROM jsonb_each_text(v_estado.fase1_fuentes::jsonb)),
    'ultimo_scraping', v_estado.fase1_ultimo_scraping,
    'dias_desde_scraping', v_estado.fase1_dias_desde_scraping,
    'en_dashboard', (SELECT COUNT(*) FROM ofertas_dashboard),
    'sin_procesar', v_estado.fase2_sin_nlp
  );

  -- Alertas
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
    -- Scraping global atrasado
    SELECT
      CASE WHEN v_estado.fase1_dias_desde_scraping > 7 THEN 'error' ELSE 'warning' END as nivel,
      'global' as portal,
      'Scraping general sin ejecutar hace ' || v_estado.fase1_dias_desde_scraping || ' dias' as mensaje,
      'Ultimo: ' || v_estado.fase1_ultimo_scraping as detalle
    WHERE v_estado.fase1_dias_desde_scraping > 3

    UNION ALL

    -- Ofertas sin procesar
    SELECT
      CASE WHEN v_estado.fase2_sin_nlp > 1000 THEN 'error' ELSE 'warning' END,
      'pipeline',
      v_estado.fase2_sin_nlp || ' ofertas scrapeadas sin procesar (NLP pendiente)',
      'En dashboard: ' || (SELECT COUNT(*) FROM ofertas_dashboard) || ' / ' || v_estado.fase1_ofertas_totales || ' total'
    WHERE v_estado.fase2_sin_nlp > 0

    UNION ALL

    -- Portal scrapeado recientemente pero sin ofertas nuevas
    -- Usa scraping_daily (datos crudos) para detectar portales que no traen datos
    SELECT
      'warning',
      sd.portal,
      sd.portal || ': scrapeado el ' || sd.ultimo_dia || ' pero trajo solo ' || sd.ofertas_ultimo_dia || ' ofertas',
      'Promedio diario: ' || sd.promedio_diario || ' | Ultimo dia: ' || sd.ofertas_ultimo_dia
    FROM (
      SELECT
        portal,
        MAX(fecha) as ultimo_dia,
        (SELECT ofertas_nuevas FROM scraping_daily s2
         WHERE s2.portal = scraping_daily.portal
         ORDER BY fecha DESC LIMIT 1) as ofertas_ultimo_dia,
        ROUND(AVG(ofertas_nuevas)) as promedio_diario
      FROM scraping_daily
      WHERE fecha >= CURRENT_DATE - INTERVAL '30 days'
      GROUP BY portal
      HAVING MAX(fecha) >= CURRENT_DATE - INTERVAL '3 days'
    ) sd
    WHERE sd.ofertas_ultimo_dia = 0
      OR (sd.promedio_diario > 100 AND sd.ofertas_ultimo_dia < sd.promedio_diario * 0.2)
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
-- NOTA: usa ofertas_dashboard (solo procesadas) porque es lo disponible en Supabase
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
    SELECT json_build_object(
      'dias', COALESCE(json_agg(row_to_json(d) ORDER BY d.fecha), '[]'::json),
      'periodo', json_build_object(
        'desde', CURRENT_DATE - (p_days || ' days')::interval,
        'hasta', CURRENT_DATE,
        'dias', p_days
      ),
      'tipo_fecha', 'scraping',
      'nota', 'Solo ofertas procesadas (en Supabase). Ofertas sin NLP no aparecen.'
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
    SELECT json_build_object(
      'dias', COALESCE(json_agg(row_to_json(d) ORDER BY d.fecha), '[]'::json),
      'periodo', json_build_object(
        'desde', CURRENT_DATE - (p_days || ' days')::interval,
        'hasta', CURRENT_DATE,
        'dias', p_days
      ),
      'tipo_fecha', 'publicacion',
      'nota', 'Solo ofertas procesadas (en Supabase). Ofertas sin NLP no aparecen.'
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
