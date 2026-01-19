-- Migration 008: Add sector_confianza field
-- Date: 2026-01-15
-- Purpose: Track confidence level of sector_empresa classification
-- Values: 'alta' | 'media' | 'baja' | NULL (sin clasificar)

-- Agregar columna sector_confianza
ALTER TABLE ofertas_nlp ADD COLUMN sector_confianza TEXT;

-- Agregar columna sector_fuente para debugging
ALTER TABLE ofertas_nlp ADD COLUMN sector_fuente TEXT;

-- Crear indice para filtrar por confianza
CREATE INDEX IF NOT EXISTS idx_ofertas_nlp_sector_confianza ON ofertas_nlp(sector_confianza);

-- Comentario sobre valores de sector_confianza:
-- 'alta': Empresa identificable conocida O frase explícita "somos empresa de..."
-- 'media': Keyword encontrado después de patrón de descripción de empresa
-- 'baja': Keyword encontrado en descripción general (puede ser del puesto, no de empresa)
-- NULL: Sin clasificar o sin información suficiente

-- Comentario sobre valores de sector_fuente:
-- 'empresa_conocida': Nombre de empresa matcheó con catálogo
-- 'frase_explicita': Encontró "somos una empresa de [sector]"
-- 'keyword_contexto': Keyword después de patrón empresa
-- 'keyword_general': Keyword en descripción (baja confianza)
-- 'llm': LLM extrajo directamente
