-- Migration 073: conteo de ofertas por ISCO con filtro de provincia y fecha
-- (DEMO-MIERCOLES 1.1/1.1c). Reemplaza el select('isco_code') sin paginar de M2,
-- que PostgREST cortaba en 1.000 filas. Solo lectura; no modifica datos.

CREATE OR REPLACE FUNCTION get_ofertas_count_by_isco_filtrado(
  p_provincia TEXT DEFAULT NULL,
  p_since     DATE DEFAULT NULL
)
RETURNS TABLE(isco_code TEXT, total BIGINT, activas BIGINT)
LANGUAGE sql STABLE
SECURITY DEFINER
SET search_path = public
AS $$
  SELECT od.isco_code,
         COUNT(*) AS total,
         COUNT(*) FILTER (WHERE od.estado_ciclo = 'activa') AS activas
  FROM ofertas_dashboard od
  WHERE od.isco_code IS NOT NULL
    AND (p_provincia IS NULL OR od.provincia = p_provincia)
    AND (p_since IS NULL OR od.fecha_publicacion >= p_since)
  GROUP BY od.isco_code;
$$;

GRANT EXECUTE ON FUNCTION get_ofertas_count_by_isco_filtrado(TEXT, DATE) TO anon, authenticated;
