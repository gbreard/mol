-- Migración 007: Agregar columnas CLAE para clasificación de sector
-- Fecha: 2026-01-15
-- Descripción: Agrega columnas para código CLAE (Clasificador de Actividades Económicas Argentina)
--              Convive con sector_empresa (texto libre) para debugging
--
-- Estructura CLAE:
--   - clae_code: 6 dígitos (actividad específica, ej: 620100)
--   - clae_grupo: 3 dígitos (grupo, ej: 620)
--   - clae_seccion: 1 letra (sección, ej: J)
--
-- Las columnas empiezan NULL y se llenan por el postprocessor

-- Agregar columnas a ofertas_nlp
ALTER TABLE ofertas_nlp ADD COLUMN IF NOT EXISTS clae_code TEXT;
ALTER TABLE ofertas_nlp ADD COLUMN IF NOT EXISTS clae_grupo TEXT;
ALTER TABLE ofertas_nlp ADD COLUMN IF NOT EXISTS clae_seccion TEXT;

-- Índices para queries por sector
CREATE INDEX IF NOT EXISTS idx_ofertas_nlp_clae_code ON ofertas_nlp(clae_code);
CREATE INDEX IF NOT EXISTS idx_ofertas_nlp_clae_grupo ON ofertas_nlp(clae_grupo);
CREATE INDEX IF NOT EXISTS idx_ofertas_nlp_clae_seccion ON ofertas_nlp(clae_seccion);

-- Comentarios (SQLite no soporta COMMENT, esto es documentación)
-- clae_code: Código de 6 dígitos de la actividad económica AFIP
-- clae_grupo: Código de 3 dígitos del grupo (para matching)
-- clae_seccion: Letra de sección A-Z (para dashboard)
