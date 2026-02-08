-- ============================================
-- Vista vw_distribucion_isco para /admin/metricas
-- ============================================

-- Descripcion: Distribucion de ofertas por codigo ISCO
-- Usada por: /admin/metricas (Top 10 Ocupaciones ESCO)

CREATE OR REPLACE VIEW vw_distribucion_isco AS
SELECT
  isco_code,
  isco_label,
  COUNT(*) as total
FROM ofertas_dashboard
WHERE isco_code IS NOT NULL
GROUP BY isco_code, isco_label
ORDER BY total DESC;

-- Verificar
SELECT * FROM vw_distribucion_isco LIMIT 10;
