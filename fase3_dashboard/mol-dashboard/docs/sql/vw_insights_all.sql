-- ============================================
-- Vistas e Función para Insights (E-16)
-- ============================================
-- Ejecutar en Supabase SQL Editor
-- Referencia: docs/plan/12_INSIGHTS_SISTEMA.md
-- ============================================

-- 1. Vista: KPIs generales
DROP VIEW IF EXISTS vw_insights_kpis;
CREATE VIEW vw_insights_kpis AS
SELECT
  COUNT(*) as total_ofertas,
  COUNT(DISTINCT isco_code) as ocupaciones_distintas,
  COUNT(DISTINCT empresa) as empresas_activas,
  COUNT(DISTINCT provincia) as provincias
FROM ofertas_dashboard;

-- Verificar
SELECT * FROM vw_insights_kpis;

-- ============================================

-- 2. Vista: Distribución por grupo ISCO (primer dígito)
DROP VIEW IF EXISTS vw_insights_isco_grupos;
CREATE VIEW vw_insights_isco_grupos AS
SELECT
  LEFT(isco_code, 1) as grupo,
  COUNT(*) as total,
  ROUND(COUNT(*) * 100.0 / NULLIF(SUM(COUNT(*)) OVER (), 0), 1) as porcentaje
FROM ofertas_dashboard
WHERE isco_code IS NOT NULL AND isco_code != ''
GROUP BY LEFT(isco_code, 1)
ORDER BY total DESC;

-- Verificar
SELECT * FROM vw_insights_isco_grupos;

-- ============================================

-- 3. Vista: Tendencia mensual (últimos 12 meses)
DROP VIEW IF EXISTS vw_insights_tendencia;
CREATE VIEW vw_insights_tendencia AS
SELECT
  DATE_TRUNC('month', fecha_publicacion::date) as mes,
  COUNT(*) as ofertas,
  COUNT(DISTINCT empresa) as empresas,
  COUNT(DISTINCT isco_code) as ocupaciones
FROM ofertas_dashboard
WHERE fecha_publicacion IS NOT NULL
GROUP BY DATE_TRUNC('month', fecha_publicacion::date)
ORDER BY mes DESC
LIMIT 12;

-- Verificar
SELECT * FROM vw_insights_tendencia;

-- ============================================

-- 4. Vista: Top empresas
DROP VIEW IF EXISTS vw_insights_empresas;
CREATE VIEW vw_insights_empresas AS
SELECT
  empresa,
  COUNT(*) as ofertas,
  COUNT(DISTINCT isco_code) as ocupaciones_distintas
FROM ofertas_dashboard
WHERE empresa IS NOT NULL AND empresa != ''
GROUP BY empresa
ORDER BY ofertas DESC
LIMIT 20;

-- Verificar
SELECT * FROM vw_insights_empresas LIMIT 5;

-- ============================================

-- 5. Vista: Distribución por provincia
DROP VIEW IF EXISTS vw_insights_provincias;
CREATE VIEW vw_insights_provincias AS
SELECT
  COALESCE(provincia, 'No especificado') as provincia,
  COUNT(*) as total,
  ROUND(COUNT(*) * 100.0 / NULLIF(SUM(COUNT(*)) OVER (), 0), 1) as porcentaje
FROM ofertas_dashboard
GROUP BY provincia
ORDER BY total DESC;

-- Verificar
SELECT * FROM vw_insights_provincias LIMIT 5;

-- ============================================

-- 6. Función RPC: get_insights (acepta filtros)
CREATE OR REPLACE FUNCTION get_insights(
  p_provincia text DEFAULT NULL,
  p_fecha_desde date DEFAULT NULL,
  p_fecha_hasta date DEFAULT NULL
)
RETURNS json
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
  result json;
BEGIN
  SELECT json_build_object(
    'kpis', (
      SELECT json_build_object(
        'total_ofertas', COUNT(*),
        'ocupaciones_distintas', COUNT(DISTINCT isco_code),
        'empresas_activas', COUNT(DISTINCT empresa),
        'provincias', COUNT(DISTINCT provincia)
      )
      FROM ofertas_dashboard
      WHERE (p_provincia IS NULL OR provincia = p_provincia)
        AND (p_fecha_desde IS NULL OR fecha_publicacion::date >= p_fecha_desde)
        AND (p_fecha_hasta IS NULL OR fecha_publicacion::date <= p_fecha_hasta)
    ),
    'isco_grupos', (
      SELECT COALESCE(json_agg(row_to_json(t)), '[]'::json)
      FROM (
        SELECT
          LEFT(isco_code, 1) as grupo,
          COUNT(*) as total,
          ROUND(COUNT(*) * 100.0 / NULLIF(SUM(COUNT(*)) OVER (), 0), 1) as porcentaje
        FROM ofertas_dashboard
        WHERE isco_code IS NOT NULL AND isco_code != ''
          AND (p_provincia IS NULL OR provincia = p_provincia)
          AND (p_fecha_desde IS NULL OR fecha_publicacion::date >= p_fecha_desde)
          AND (p_fecha_hasta IS NULL OR fecha_publicacion::date <= p_fecha_hasta)
        GROUP BY LEFT(isco_code, 1)
        ORDER BY total DESC
        LIMIT 10
      ) t
    ),
    'concentracion_top3', (
      SELECT COALESCE(ROUND(SUM(porcentaje), 1), 0)
      FROM (
        SELECT ROUND(COUNT(*) * 100.0 / NULLIF(SUM(COUNT(*)) OVER (), 0), 1) as porcentaje
        FROM ofertas_dashboard
        WHERE isco_code IS NOT NULL AND isco_code != ''
          AND (p_provincia IS NULL OR provincia = p_provincia)
          AND (p_fecha_desde IS NULL OR fecha_publicacion::date >= p_fecha_desde)
          AND (p_fecha_hasta IS NULL OR fecha_publicacion::date <= p_fecha_hasta)
        GROUP BY LEFT(isco_code, 1)
        ORDER BY COUNT(*) DESC
        LIMIT 3
      ) sub
    ),
    'top_empresas', (
      SELECT COALESCE(json_agg(row_to_json(t)), '[]'::json)
      FROM (
        SELECT empresa, COUNT(*) as ofertas
        FROM ofertas_dashboard
        WHERE empresa IS NOT NULL AND empresa != ''
          AND (p_provincia IS NULL OR provincia = p_provincia)
          AND (p_fecha_desde IS NULL OR fecha_publicacion::date >= p_fecha_desde)
          AND (p_fecha_hasta IS NULL OR fecha_publicacion::date <= p_fecha_hasta)
        GROUP BY empresa
        ORDER BY ofertas DESC
        LIMIT 5
      ) t
    ),
    'provincias', (
      SELECT COALESCE(json_agg(row_to_json(t)), '[]'::json)
      FROM (
        SELECT
          COALESCE(provincia, 'No especificado') as provincia,
          COUNT(*) as total,
          ROUND(COUNT(*) * 100.0 / NULLIF(SUM(COUNT(*)) OVER (), 0), 1) as porcentaje
        FROM ofertas_dashboard
        WHERE (p_provincia IS NULL OR provincia = p_provincia)
          AND (p_fecha_desde IS NULL OR fecha_publicacion::date >= p_fecha_desde)
          AND (p_fecha_hasta IS NULL OR fecha_publicacion::date <= p_fecha_hasta)
        GROUP BY provincia
        ORDER BY total DESC
        LIMIT 10
      ) t
    )
  ) INTO result;

  RETURN result;
END;
$$;

-- ============================================
-- Verificar función RPC
-- ============================================

-- Sin filtros (todos los datos)
SELECT get_insights();

-- Con filtro de provincia
SELECT get_insights('Buenos Aires');

-- Con filtro de fechas
SELECT get_insights(NULL, '2026-01-01', '2026-02-28');

-- ============================================
-- LISTO - Ahora refactorizar lib/supabase.ts
-- ============================================
