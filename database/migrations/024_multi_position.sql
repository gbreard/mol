-- 024_multi_position.sql
-- Soporte para ofertas multi-posición (detector híbrido regex+LLM)
-- Fecha: 2026-02-24

-- Columnas de lineaje para sub-ofertas expandidas
ALTER TABLE ofertas_nlp ADD COLUMN parent_id_oferta TEXT DEFAULT NULL;
ALTER TABLE ofertas_nlp ADD COLUMN es_suboferta INTEGER DEFAULT 0;
ALTER TABLE ofertas_nlp ADD COLUMN numero_suboferta INTEGER DEFAULT NULL;
-- multi_position_status: NULL=no evaluado, 'single'=confirmado único,
--   'multi_detected'=detectado multi, 'expanded'=ya expandido
ALTER TABLE ofertas_nlp ADD COLUMN multi_position_status TEXT DEFAULT NULL;

-- Índice para buscar sub-ofertas de un padre
CREATE INDEX IF NOT EXISTS idx_ofertas_nlp_parent ON ofertas_nlp(parent_id_oferta);
CREATE INDEX IF NOT EXISTS idx_ofertas_nlp_suboferta ON ofertas_nlp(es_suboferta);
