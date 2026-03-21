-- ============================================================
-- RPC: get_pipeline_status()
-- Centro de Control J1a — estado del pipeline en una sola llamada
--
-- Lee sistema_estado (último registro) y calcula alertas.
-- No recibe filtros — siempre devuelve el estado actual.
--
-- Retorna:
-- {
--   fases: { scraping, nlp, matching, sync },
--   alertas: [ { nivel, mensaje, accion, detalle } ],
--   resumen: { total_ofertas, en_supabase, issues_pendientes },
--   ultimo_update: timestamp
-- }
-- ============================================================

CREATE OR REPLACE FUNCTION get_pipeline_status()
RETURNS json
LANGUAGE plpgsql
STABLE
SECURITY DEFINER
SET statement_timeout = '5s'
AS $$
DECLARE
  v_result json;
  v_estado record;
  v_issues_humanos bigint;
  v_issues_auto_pendientes bigint;
  v_alertas json;
BEGIN
  -- Último estado del sistema
  SELECT * INTO v_estado
  FROM sistema_estado
  ORDER BY timestamp DESC
  LIMIT 1;

  IF v_estado IS NULL THEN
    RETURN json_build_object('error', 'No hay datos de estado del sistema');
  END IF;

  -- Issues pendientes (humanos vs auto)
  SELECT COUNT(*) INTO v_issues_humanos
  FROM issues
  WHERE estado = 'pendiente'
    AND autor_email != 'auto-validator@mol.gob.ar';

  SELECT COUNT(*) INTO v_issues_auto_pendientes
  FROM issues
  WHERE estado = 'pendiente'
    AND autor_email = 'auto-validator@mol.gob.ar';

  -- Construir alertas basadas en el estado
  SELECT COALESCE(json_agg(
    json_build_object(
      'nivel', a.nivel,
      'mensaje', a.mensaje,
      'accion', a.accion,
      'detalle', a.detalle
    ) ORDER BY a.prioridad
  ), '[]'::json)
  INTO v_alertas
  FROM (
    -- Alerta: scraping atrasado
    SELECT
      1 as prioridad,
      CASE
        WHEN v_estado.fase1_dias_desde_scraping > 7 THEN 'error'
        WHEN v_estado.fase1_dias_desde_scraping > 3 THEN 'warning'
        ELSE NULL
      END as nivel,
      'Scraping sin ejecutar hace ' || v_estado.fase1_dias_desde_scraping || ' días' as mensaje,
      'lanzar_scraping' as accion,
      'Último scraping: ' || v_estado.fase1_ultimo_scraping as detalle
    WHERE v_estado.fase1_dias_desde_scraping > 3

    UNION ALL

    -- Alerta: ofertas sin NLP
    SELECT
      2,
      CASE
        WHEN v_estado.fase2_sin_nlp > 500 THEN 'error'
        WHEN v_estado.fase2_sin_nlp > 0 THEN 'warning'
        ELSE NULL
      END,
      v_estado.fase2_sin_nlp || ' ofertas sin procesar NLP',
      'procesar_nlp',
      'Procesadas: ' || v_estado.fase2_con_nlp || '/' || v_estado.fase1_ofertas_totales
    WHERE v_estado.fase2_sin_nlp > 0

    UNION ALL

    -- Alerta: pendientes matching
    SELECT
      3,
      CASE
        WHEN v_estado.fase2_pendientes_matching > 500 THEN 'error'
        WHEN v_estado.fase2_pendientes_matching > 0 THEN 'warning'
        ELSE NULL
      END,
      v_estado.fase2_pendientes_matching || ' ofertas sin matching',
      'procesar_matching',
      'Con matching: ' || v_estado.fase2_con_matching
    WHERE v_estado.fase2_pendientes_matching > 0

    UNION ALL

    -- Alerta: pendientes sync
    SELECT
      4,
      CASE
        WHEN v_estado.fase3_pendientes_sync > 1000 THEN 'error'
        WHEN v_estado.fase3_pendientes_sync > 0 THEN 'warning'
        ELSE NULL
      END,
      v_estado.fase3_pendientes_sync || ' ofertas pendientes de sync a Supabase',
      'sync_supabase',
      'En Supabase: ' || v_estado.fase3_ofertas_supabase
    WHERE v_estado.fase3_pendientes_sync > 0

    UNION ALL

    -- Alerta: errores sin resolver
    SELECT
      5,
      'warning'::text,
      v_estado.fase2_errores_sin_resolver || ' errores de validación sin resolver',
      'ver_errores',
      NULL::text
    WHERE v_estado.fase2_errores_sin_resolver > 0

    UNION ALL

    -- Alerta: issues humanos pendientes
    SELECT
      6,
      'info'::text,
      v_issues_humanos || ' issues de usuarios pendientes',
      'ver_issues',
      NULL::text
    WHERE v_issues_humanos > 0

    UNION ALL

    -- Todo OK
    SELECT
      99,
      'ok'::text,
      'Pipeline operativo — sin alertas',
      NULL,
      NULL::text
    WHERE v_estado.fase1_dias_desde_scraping <= 3
      AND v_estado.fase2_sin_nlp = 0
      AND v_estado.fase2_pendientes_matching = 0
      AND v_estado.fase3_pendientes_sync = 0
      AND v_estado.fase2_errores_sin_resolver = 0
      AND v_issues_humanos = 0
  ) a
  WHERE a.nivel IS NOT NULL;

  -- Resultado final
  v_result := json_build_object(
    'fases', json_build_object(
      'scraping', json_build_object(
        'estado', CASE
          WHEN v_estado.fase1_dias_desde_scraping > 7 THEN 'error'
          WHEN v_estado.fase1_dias_desde_scraping > 3 THEN 'warning'
          ELSE 'ok'
        END,
        'ultimo_scraping', v_estado.fase1_ultimo_scraping,
        'dias_desde_scraping', v_estado.fase1_dias_desde_scraping,
        'ofertas_totales', v_estado.fase1_ofertas_totales,
        'ofertas_activas', v_estado.fase1_ofertas_activas,
        'fuentes', v_estado.fase1_fuentes
      ),
      'nlp', json_build_object(
        'estado', CASE
          WHEN v_estado.fase2_sin_nlp > 500 THEN 'error'
          WHEN v_estado.fase2_sin_nlp > 0 THEN 'warning'
          ELSE 'ok'
        END,
        'procesadas', v_estado.fase2_con_nlp,
        'pendientes', v_estado.fase2_sin_nlp,
        'ultimo_run', v_estado.fase2_ultimo_run
      ),
      'matching', json_build_object(
        'estado', CASE
          WHEN v_estado.fase2_pendientes_matching > 500 THEN 'error'
          WHEN v_estado.fase2_pendientes_matching > 0 THEN 'warning'
          ELSE 'ok'
        END,
        'con_matching', v_estado.fase2_con_matching,
        'pendientes', v_estado.fase2_pendientes_matching,
        'validadas', v_estado.fase2_validadas,
        'errores_sin_resolver', v_estado.fase2_errores_sin_resolver,
        'reglas_negocio', v_estado.fase2_reglas_negocio
      ),
      'sync', json_build_object(
        'estado', CASE
          WHEN v_estado.fase3_pendientes_sync > 1000 THEN 'error'
          WHEN v_estado.fase3_pendientes_sync > 0 THEN 'warning'
          ELSE 'ok'
        END,
        'en_supabase', v_estado.fase3_ofertas_supabase,
        'pendientes', v_estado.fase3_pendientes_sync
      )
    ),
    'alertas', v_alertas,
    'resumen', json_build_object(
      'total_ofertas', v_estado.fase1_ofertas_totales,
      'en_supabase', v_estado.fase3_ofertas_supabase,
      'issues_humanos_pendientes', v_issues_humanos,
      'issues_auto_pendientes', v_issues_auto_pendientes,
      'fase_sugerida', v_estado.fase_sugerida_nombre,
      'fase_sugerida_razon', v_estado.fase_sugerida_razon
    ),
    'ultimo_update', v_estado.timestamp
  );

  RETURN v_result;
END;
$$;
