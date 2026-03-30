-- Migration 041: Actualizar get_pipeline_status() para incluir campos ultimo_run_*
-- M-01: Los campos de sistema_estado ya existen (migration 038) pero el RPC no los retornaba

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
    SELECT 1 as prioridad,
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
    SELECT 2,
      CASE WHEN v_estado.fase2_sin_nlp > 500 THEN 'error' WHEN v_estado.fase2_sin_nlp > 0 THEN 'warning' ELSE NULL END,
      v_estado.fase2_sin_nlp || ' ofertas sin procesar NLP', 'procesar_nlp',
      'Procesadas: ' || v_estado.fase2_con_nlp || '/' || v_estado.fase1_ofertas_totales
    WHERE v_estado.fase2_sin_nlp > 0

    UNION ALL
    SELECT 3,
      CASE WHEN v_estado.fase2_pendientes_matching > 500 THEN 'error' WHEN v_estado.fase2_pendientes_matching > 0 THEN 'warning' ELSE NULL END,
      v_estado.fase2_pendientes_matching || ' ofertas sin matching', 'procesar_matching',
      'Con matching: ' || v_estado.fase2_con_matching
    WHERE v_estado.fase2_pendientes_matching > 0

    UNION ALL
    SELECT 4,
      CASE WHEN v_estado.fase3_pendientes_sync > 1000 THEN 'error' WHEN v_estado.fase3_pendientes_sync > 0 THEN 'warning' ELSE NULL END,
      v_estado.fase3_pendientes_sync || ' ofertas pendientes de sync a Supabase', 'sync_supabase',
      'En Supabase: ' || v_estado.fase3_ofertas_supabase
    WHERE v_estado.fase3_pendientes_sync > 0

    UNION ALL
    SELECT 5, 'warning'::text,
      v_estado.fase2_errores_sin_resolver || ' errores de validación sin resolver', 'ver_errores', NULL::text
    WHERE v_estado.fase2_errores_sin_resolver > 0

    UNION ALL
    SELECT 6, 'info'::text,
      v_issues_humanos || ' issues de usuarios pendientes', 'ver_issues', NULL::text
    WHERE v_issues_humanos > 0

    UNION ALL
    SELECT 99, 'ok'::text, 'Pipeline operativo — sin alertas', NULL, NULL::text
    WHERE v_estado.fase1_dias_desde_scraping <= 3
      AND v_estado.fase2_sin_nlp = 0
      AND v_estado.fase2_pendientes_matching = 0
      AND v_estado.fase3_pendientes_sync = 0
      AND v_estado.fase2_errores_sin_resolver = 0
      AND v_issues_humanos = 0
  ) a
  WHERE a.nivel IS NOT NULL;

  -- Resultado final (incluye campos M-01 ultimo_run_*)
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
    'ultimo_update', v_estado.timestamp,
    -- M-01: Campos del último run del pipeline
    'ultimo_run_id', v_estado.ultimo_run_id,
    'ultimo_run_timestamp', v_estado.ultimo_run_timestamp,
    'ultimo_run_branch', v_estado.ultimo_run_branch,
    'ultimo_run_nlp_version', v_estado.ultimo_run_nlp_version,
    'ultimo_run_matching_version', v_estado.ultimo_run_matching_version,
    'ultimo_run_ofertas', v_estado.ultimo_run_ofertas,
    'ultimo_run_skills', v_estado.ultimo_run_skills,
    'ultimo_run_failures', v_estado.ultimo_run_failures,
    'ultimo_run_failures_pct', v_estado.ultimo_run_failures_pct,
    'ultimo_run_errores', v_estado.ultimo_run_errores,
    'ultimo_run_corregidos', v_estado.ultimo_run_corregidos,
    'ultimo_run_escalados', v_estado.ultimo_run_escalados,
    'ultimo_run_precision', v_estado.ultimo_run_precision,
    'ultimo_run_delta_precision', v_estado.ultimo_run_delta_precision,
    'ultimo_run_delta_regresiones', v_estado.ultimo_run_delta_regresiones,
    'ultimo_run_delta_mejoras', v_estado.ultimo_run_delta_mejoras,
    'ultimo_run_reglas_nuevas', v_estado.ultimo_run_reglas_nuevas,
    'ultimo_run_top_failures', v_estado.ultimo_run_top_failures
  );

  RETURN v_result;
END;
$$;
