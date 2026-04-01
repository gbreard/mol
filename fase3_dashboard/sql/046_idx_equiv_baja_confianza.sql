-- Migration 046: Índice para alerta de baja confianza
-- Optimiza la query COUNT(*) en get_pipeline_status() que hacía timeout

CREATE INDEX IF NOT EXISTS idx_equiv_auto_similitud
ON skill_equivalences(similitud_minima)
WHERE estado = 'auto' AND similitud_minima IS NOT NULL;
