-- Migración: Agregar columnas faltantes a ofertas_dashboard
-- Fecha: 2026-02-05
-- Problema: getDistribucionRequerimientos consulta campos que no existen

-- Agregar columnas de requerimientos (NLP)
ALTER TABLE ofertas_dashboard ADD COLUMN IF NOT EXISTS titulo_limpio TEXT;
ALTER TABLE ofertas_dashboard ADD COLUMN IF NOT EXISTS nivel_educativo TEXT;
ALTER TABLE ofertas_dashboard ADD COLUMN IF NOT EXISTS experiencia_min_anios INTEGER;
ALTER TABLE ofertas_dashboard ADD COLUMN IF NOT EXISTS tiene_gente_cargo BOOLEAN DEFAULT FALSE;
ALTER TABLE ofertas_dashboard ADD COLUMN IF NOT EXISTS jornada_laboral TEXT;

-- Agregar columnas ESCO completas (para Skills Intelligence)
ALTER TABLE ofertas_dashboard ADD COLUMN IF NOT EXISTS esco_occupation_uri TEXT;
ALTER TABLE ofertas_dashboard ADD COLUMN IF NOT EXISTS esco_occupation_label TEXT;

-- Índices para las nuevas columnas
CREATE INDEX IF NOT EXISTS idx_ofertas_nivel_educativo ON ofertas_dashboard(nivel_educativo);
CREATE INDEX IF NOT EXISTS idx_ofertas_jornada ON ofertas_dashboard(jornada_laboral);
CREATE INDEX IF NOT EXISTS idx_ofertas_esco_uri ON ofertas_dashboard(esco_occupation_uri);

-- Vista actualizada para distribución de requerimientos
CREATE OR REPLACE VIEW v_distribucion_requerimientos AS
SELECT
    COALESCE(nivel_educativo, 'Sin especificar') as nivel_educativo,
    COUNT(*) as cantidad,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 1) as porcentaje
FROM ofertas_dashboard
GROUP BY nivel_educativo
ORDER BY cantidad DESC;

-- Vista para distribución por experiencia
CREATE OR REPLACE VIEW v_ofertas_por_experiencia AS
SELECT
    CASE
        WHEN experiencia_min_anios IS NULL THEN 'Sin especificar'
        WHEN experiencia_min_anios = 0 THEN 'Sin experiencia'
        WHEN experiencia_min_anios <= 2 THEN '1-2 años'
        WHEN experiencia_min_anios <= 4 THEN '3-4 años'
        ELSE '5+ años'
    END as rango_experiencia,
    COUNT(*) as cantidad
FROM ofertas_dashboard
GROUP BY 1
ORDER BY cantidad DESC;

-- Vista para distribución por jornada
CREATE OR REPLACE VIEW v_ofertas_por_jornada AS
SELECT
    COALESCE(jornada_laboral, 'Sin especificar') as jornada,
    COUNT(*) as cantidad
FROM ofertas_dashboard
GROUP BY jornada_laboral
ORDER BY cantidad DESC;

-- Comentario de columnas para documentación
COMMENT ON COLUMN ofertas_dashboard.nivel_educativo IS 'Nivel educativo requerido (universitario, terciario, secundario, primario)';
COMMENT ON COLUMN ofertas_dashboard.experiencia_min_anios IS 'Años mínimos de experiencia requerida';
COMMENT ON COLUMN ofertas_dashboard.tiene_gente_cargo IS 'Si el puesto requiere tener personal a cargo';
COMMENT ON COLUMN ofertas_dashboard.jornada_laboral IS 'Tipo de jornada (full-time, part-time, freelance)';
COMMENT ON COLUMN ofertas_dashboard.esco_occupation_uri IS 'URI completa de la ocupación ESCO';
COMMENT ON COLUMN ofertas_dashboard.esco_occupation_label IS 'Label de la ocupación ESCO en español';
