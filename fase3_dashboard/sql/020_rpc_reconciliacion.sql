-- ============================================================
-- RPC: reconciliar_sistemas()
-- Centro de Control J2a — compara conteos entre sistemas
--
-- Compara:
--   1. sistema_estado (reflejo de local) vs tablas Supabase reales
--   2. ofertas_dashboard vs ofertas_skills (skills faltantes)
--   3. Consistencia interna (ofertas sin ISCO, sin skills, etc.)
--
-- Retorna inconsistencias con severidad y acción sugerida
-- ============================================================

CREATE OR REPLACE FUNCTION reconciliar_sistemas()
RETURNS json
LANGUAGE plpgsql
STABLE
SECURITY DEFINER
SET statement_timeout = '8s'
AS $$
DECLARE
  v_result json;
  v_estado record;
  -- Conteos reales de Supabase
  v_ofertas_supabase bigint;
  v_skills_supabase bigint;
  v_ofertas_con_skills bigint;
  v_ofertas_sin_isco bigint;
  v_ofertas_sin_skills bigint;
  v_inconsistencias json;
BEGIN
  -- Último estado reportado por local
  SELECT * INTO v_estado
  FROM sistema_estado
  ORDER BY timestamp DESC
  LIMIT 1;

  -- Conteos reales en Supabase
  SELECT COUNT(*) INTO v_ofertas_supabase FROM ofertas_dashboard;
  SELECT COUNT(*) INTO v_skills_supabase FROM ofertas_skills;
  SELECT COUNT(DISTINCT id_oferta) INTO v_ofertas_con_skills FROM ofertas_skills;
  SELECT COUNT(*) INTO v_ofertas_sin_isco FROM ofertas_dashboard WHERE isco_code IS NULL;
  SELECT COUNT(*) INTO v_ofertas_sin_skills
    FROM ofertas_dashboard od
    WHERE NOT EXISTS (SELECT 1 FROM ofertas_skills os WHERE os.id_oferta = od.id_oferta);

  -- Construir lista de inconsistencias
  SELECT COALESCE(json_agg(
    json_build_object(
      'tipo', i.tipo,
      'severidad', i.severidad,
      'mensaje', i.mensaje,
      'esperado', i.esperado,
      'actual', i.actual,
      'diferencia', i.diferencia,
      'accion', i.accion
    ) ORDER BY CASE i.severidad WHEN 'error' THEN 1 WHEN 'warning' THEN 2 ELSE 3 END
  ), '[]'::json)
  INTO v_inconsistencias
  FROM (
    -- Local total vs Supabase
    SELECT
      'ofertas_faltantes'::text as tipo,
      CASE
        WHEN v_estado.fase1_ofertas_totales - v_ofertas_supabase > 1000 THEN 'error'
        WHEN v_estado.fase1_ofertas_totales - v_ofertas_supabase > 0 THEN 'warning'
        ELSE NULL
      END as severidad,
      'Ofertas en local sin subir a Supabase' as mensaje,
      v_estado.fase1_ofertas_totales as esperado,
      v_ofertas_supabase as actual,
      v_estado.fase1_ofertas_totales - v_ofertas_supabase as diferencia,
      'sync_supabase' as accion
    WHERE v_estado.fase1_ofertas_totales > v_ofertas_supabase

    UNION ALL

    -- Ofertas en Supabase sin skills
    SELECT
      'sin_skills',
      CASE
        WHEN v_ofertas_sin_skills > 500 THEN 'error'
        WHEN v_ofertas_sin_skills > 0 THEN 'warning'
        ELSE NULL
      END,
      'Ofertas en Supabase sin skills asociadas',
      v_ofertas_supabase,
      v_ofertas_supabase - v_ofertas_sin_skills,
      v_ofertas_sin_skills,
      'backfill_skills'
    WHERE v_ofertas_sin_skills > 0

    UNION ALL

    -- Ofertas sin ISCO code
    SELECT
      'sin_isco',
      CASE
        WHEN v_ofertas_sin_isco > 100 THEN 'warning'
        ELSE NULL
      END,
      'Ofertas sin clasificacion ISCO',
      v_ofertas_supabase,
      v_ofertas_supabase - v_ofertas_sin_isco,
      v_ofertas_sin_isco,
      'reprocesar_matching'
    WHERE v_ofertas_sin_isco > 0

    UNION ALL

    -- NLP procesadas vs Supabase
    SELECT
      'nlp_supabase_diff',
      CASE
        WHEN v_estado.fase2_con_nlp - v_ofertas_supabase > 500 THEN 'warning'
        ELSE NULL
      END,
      'Ofertas con NLP en local pero no en Supabase',
      v_estado.fase2_con_nlp,
      v_ofertas_supabase,
      v_estado.fase2_con_nlp - v_ofertas_supabase,
      'sync_supabase'
    WHERE v_estado.fase2_con_nlp > v_ofertas_supabase

    UNION ALL

    -- Todo OK
    SELECT
      'ok',
      'ok'::text,
      'Sistemas consistentes — sin diferencias',
      v_ofertas_supabase,
      v_ofertas_supabase,
      0::bigint,
      NULL
    WHERE v_estado.fase1_ofertas_totales <= v_ofertas_supabase
      AND v_ofertas_sin_skills = 0
      AND v_ofertas_sin_isco = 0
  ) i
  WHERE i.severidad IS NOT NULL;

  -- Resultado
  v_result := json_build_object(
    'conteos', json_build_object(
      'local_total', v_estado.fase1_ofertas_totales,
      'local_con_nlp', v_estado.fase2_con_nlp,
      'local_validadas', v_estado.fase2_validadas,
      'supabase_ofertas', v_ofertas_supabase,
      'supabase_skills', v_skills_supabase,
      'supabase_ofertas_con_skills', v_ofertas_con_skills,
      'supabase_sin_isco', v_ofertas_sin_isco,
      'supabase_sin_skills', v_ofertas_sin_skills
    ),
    'inconsistencias', v_inconsistencias,
    'estado', CASE
      WHEN v_inconsistencias::text = '[]' THEN 'ok'
      WHEN v_inconsistencias::text LIKE '%"error"%' THEN 'error'
      ELSE 'warning'
    END,
    'timestamp', NOW()
  );

  RETURN v_result;
END;
$$;
