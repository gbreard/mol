-- Migration 074: frecuencia de cada skill en los avisos de un ISCO
-- (DEMO-MIERCOLES, "pedida en X% de ofertas" de M3). Reemplaza dos selects sin
-- paginar (ids de la ocupación + skills de 500 ids) que se cortaban en 1.000 filas.
-- Solo lectura; no modifica datos.

CREATE OR REPLACE FUNCTION get_skill_freq_by_isco(p_isco TEXT)
RETURNS TABLE(skill_uri TEXT, ofertas BIGINT, total_ofertas BIGINT)
LANGUAGE sql STABLE
SECURITY DEFINER
SET search_path = public
AS $$
  WITH ofertas_isco AS (
    SELECT id_oferta FROM ofertas_dashboard WHERE isco_code = p_isco
  )
  SELECT os.skill_uri,
         COUNT(*) AS ofertas,  -- UNIQUE (id_oferta, skill_uri)
         (SELECT COUNT(*) FROM ofertas_isco) AS total_ofertas
  FROM ofertas_skills os
  JOIN ofertas_isco oi ON oi.id_oferta = os.id_oferta
  WHERE os.skill_uri IS NOT NULL
  GROUP BY os.skill_uri;
$$;

GRANT EXECUTE ON FUNCTION get_skill_freq_by_isco(TEXT) TO anon, authenticated;
