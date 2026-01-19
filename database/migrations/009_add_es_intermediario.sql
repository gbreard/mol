-- Migration 009: Add es_intermediario field
-- Date: 2026-01-15
-- Purpose: Flag offers from staffing agencies (consultoras)
-- When es_intermediario=1, sector_empresa doesn't represent the real employer

-- Agregar columna es_intermediario (boolean: 0=false, 1=true)
ALTER TABLE ofertas_nlp ADD COLUMN es_intermediario INTEGER DEFAULT 0;

-- Crear indice para filtrar ofertas de consultoras
CREATE INDEX IF NOT EXISTS idx_ofertas_nlp_es_intermediario ON ofertas_nlp(es_intermediario);

-- Comentario sobre uso:
-- es_intermediario = 1: La empresa que publica es una consultora (Manpower, Randstad, etc.)
--                       El sector_empresa NO representa al empleador real
--                       Útil para: filtrar en análisis de demanda por sector
-- es_intermediario = 0: La empresa que publica es el empleador real
--                       El sector_empresa es confiable
