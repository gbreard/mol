-- Migration 051: RPC para contar ofertas por ISCO (reemplaza descarga de 37K filas al browser)
CREATE OR REPLACE FUNCTION get_ofertas_count_by_isco()
RETURNS TABLE(isco_code text, count bigint)
LANGUAGE sql STABLE
SECURITY DEFINER
AS $$
  SELECT isco_code, count(*) as count
  FROM ofertas_dashboard
  WHERE isco_code IS NOT NULL
  GROUP BY isco_code;
$$;
