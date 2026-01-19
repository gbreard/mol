-- =====================================================================
-- Migración 004: Campos NLP faltantes detectados por LLM
-- =====================================================================
-- Fecha: 2025-12-10
-- Descripción: Agrega campos que el LLM extrae pero no se guardaban
-- Detectados durante pruebas de NLP v10.0.0
--
-- IMPORTANTE: Ejecutar con backup previo de bumeran_scraping.db
-- =====================================================================

-- =====================================================================
-- CONTRATACIÓN Y CONDICIONES
-- =====================================================================
ALTER TABLE ofertas_nlp ADD COLUMN contratacion_inmediata INTEGER;  -- boolean: urgente/inmediato
ALTER TABLE ofertas_nlp ADD COLUMN indexacion_salarial INTEGER;     -- boolean: ajuste por inflación

-- =====================================================================
-- EMPRESA RELACIONADOS
-- =====================================================================
ALTER TABLE ofertas_nlp ADD COLUMN empresa_contratante TEXT;        -- empresa final (si es consultora)
ALTER TABLE ofertas_nlp ADD COLUMN empresa_publicadora TEXT;        -- consultora/intermediaria

-- =====================================================================
-- BENEFICIOS DE SALUD
-- =====================================================================
ALTER TABLE ofertas_nlp ADD COLUMN obra_social INTEGER;             -- boolean
ALTER TABLE ofertas_nlp ADD COLUMN art INTEGER;                     -- boolean (ART)
ALTER TABLE ofertas_nlp ADD COLUMN prepaga INTEGER;                 -- boolean

-- =====================================================================
-- MOVILIDAD Y VIAJES
-- =====================================================================
ALTER TABLE ofertas_nlp ADD COLUMN disponibilidad_viajes INTEGER;   -- boolean
ALTER TABLE ofertas_nlp ADD COLUMN dias_laborales TEXT;             -- JSON array: ["lunes", "martes", ...]

-- =====================================================================
-- BENEFICIOS DETECTADOS (resumen)
-- =====================================================================
ALTER TABLE ofertas_nlp ADD COLUMN beneficios_detectados TEXT;      -- JSON array de keywords

-- =====================================================================
-- RESUMEN: 10 columnas nuevas
-- Total columnas ofertas_nlp: 143 + 10 = 153
-- =====================================================================
