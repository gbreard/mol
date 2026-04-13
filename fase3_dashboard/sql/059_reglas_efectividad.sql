-- Migration 059: M-12 — Vista y RPC para efectividad de reglas de negocio
--
-- Calcula: usos por regla, coincidencia con semántico, reglas sin uso reciente.

-- ============================================================
-- 1. RPC get_reglas_efectividad
-- ============================================================
-- Retorna estadísticas de uso y coincidencia para cada regla aplicada.

CREATE OR REPLACE FUNCTION get_reglas_efectividad(p_dias INTEGER DEFAULT 30)
RETURNS JSONB
LANGUAGE sql STABLE
SECURITY DEFINER
SET statement_timeout = '10s'
AS $$
  WITH regla_stats AS (
    SELECT
      regla_aplicada,
      COUNT(*) AS usos_total,
      COUNT(*) FILTER (WHERE fecha_publicacion >= CURRENT_DATE - p_dias * INTERVAL '1 day') AS usos_periodo,
      ROUND(AVG(CASE WHEN decision_metodo = 'dual_coinciden' THEN 1.0
                     WHEN decision_metodo = 'regla_prioridad' THEN 0.0
                     ELSE NULL END)::NUMERIC * 100, 1) AS pct_coincidencia
    FROM ofertas_dashboard
    WHERE regla_aplicada IS NOT NULL
    GROUP BY regla_aplicada
  )
  SELECT jsonb_build_object(
    'total_reglas_usadas', (SELECT COUNT(*) FROM regla_stats),
    'top_10', (
      SELECT COALESCE(jsonb_agg(
        jsonb_build_object(
          'regla', regla_aplicada,
          'usos_total', usos_total,
          'usos_periodo', usos_periodo,
          'pct_coincidencia', pct_coincidencia
        ) ORDER BY usos_total DESC
      ), '[]'::JSONB)
      FROM (SELECT * FROM regla_stats ORDER BY usos_total DESC LIMIT 10) t
    ),
    'sin_uso_reciente', (
      SELECT COALESCE(jsonb_agg(regla_aplicada ORDER BY regla_aplicada), '[]'::JSONB)
      FROM regla_stats
      WHERE usos_periodo = 0
    ),
    'sin_uso_reciente_count', (
      SELECT COUNT(*) FROM regla_stats WHERE usos_periodo = 0
    ),
    'baja_coincidencia', (
      SELECT COALESCE(jsonb_agg(
        jsonb_build_object('regla', regla_aplicada, 'pct', pct_coincidencia)
        ORDER BY pct_coincidencia
      ), '[]'::JSONB)
      FROM regla_stats
      WHERE pct_coincidencia IS NOT NULL AND pct_coincidencia < 30
    ),
    'baja_coincidencia_count', (
      SELECT COUNT(*) FROM regla_stats
      WHERE pct_coincidencia IS NOT NULL AND pct_coincidencia < 30
    ),
    'periodo_dias', p_dias
  );
$$;

COMMENT ON FUNCTION get_reglas_efectividad IS 'M-12: Estadísticas de efectividad de reglas de negocio (uso + coincidencia semántica)';
