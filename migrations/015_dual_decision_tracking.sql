-- ============================================================================
-- Migración 015: Sistema de Dual Matching con Auto-Decisión
-- Fecha: 2026-01-20
-- Descripción: Permite ejecutar reglas Y semántico, guardando ambos resultados
--              y dejando que el auto_corrector decida automáticamente.
-- ============================================================================

-- PASO 1: Agregar campos para dual matching a ofertas_esco_matching
-- ============================================================================

-- ISCO propuesto por regla de negocio (si aplica)
ALTER TABLE ofertas_esco_matching ADD COLUMN isco_regla TEXT;

-- ISCO propuesto por matching semántico (siempre se ejecuta)
ALTER TABLE ofertas_esco_matching ADD COLUMN isco_semantico TEXT;

-- Score del matching semántico
ALTER TABLE ofertas_esco_matching ADD COLUMN score_semantico REAL;

-- ID de la regla de negocio que aplicó (ej: R123_asesor_tecnico)
ALTER TABLE ofertas_esco_matching ADD COLUMN regla_aplicada TEXT;

-- 1 = coinciden, 0 = difieren, NULL = solo semántico (no hay regla)
ALTER TABLE ofertas_esco_matching ADD COLUMN dual_coinciden INTEGER;

-- Método de decisión final:
--   'coinciden' - regla y semántico dieron el mismo ISCO
--   'semantico_gana_score_alto' - semántico tiene score >= 0.75
--   'regla_gana_casos_validados' - regla tiene >= 5 casos validados
--   'semantico_gana_default' - semántico gana por defecto
--   'solo_semantico' - no había regla aplicable
ALTER TABLE ofertas_esco_matching ADD COLUMN decision_metodo TEXT;


-- PASO 2: Índices para consultas frecuentes
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_dual_coinciden ON ofertas_esco_matching(dual_coinciden);
CREATE INDEX IF NOT EXISTS idx_regla_aplicada ON ofertas_esco_matching(regla_aplicada);
CREATE INDEX IF NOT EXISTS idx_decision_metodo ON ofertas_esco_matching(decision_metodo);


-- PASO 3: Vista para monitorear distribución de decisiones
-- ============================================================================

DROP VIEW IF EXISTS v_dual_decisions;
CREATE VIEW v_dual_decisions AS
SELECT
    decision_metodo,
    COUNT(*) as cantidad,
    ROUND(100.0 * COUNT(*) / (
        SELECT COUNT(*) FROM ofertas_esco_matching
        WHERE decision_metodo IS NOT NULL
    ), 1) as porcentaje
FROM ofertas_esco_matching
WHERE decision_metodo IS NOT NULL
GROUP BY decision_metodo
ORDER BY cantidad DESC;


-- PASO 4: Vista para detectar reglas problemáticas
-- ============================================================================
-- Una regla es "problemática" si difiere del semántico más del 50% de las veces

DROP VIEW IF EXISTS v_reglas_problematicas;
CREATE VIEW v_reglas_problematicas AS
SELECT
    regla_aplicada,
    COUNT(*) as total_aplicaciones,
    SUM(CASE WHEN dual_coinciden = 1 THEN 1 ELSE 0 END) as coinciden_semantico,
    SUM(CASE WHEN dual_coinciden = 0 THEN 1 ELSE 0 END) as difieren_semantico,
    ROUND(100.0 * SUM(CASE WHEN dual_coinciden = 0 THEN 1 ELSE 0 END) / COUNT(*), 1) as pct_difieren
FROM ofertas_esco_matching
WHERE regla_aplicada IS NOT NULL
GROUP BY regla_aplicada
HAVING pct_difieren > 50
ORDER BY pct_difieren DESC;


-- PASO 5: Vista para análisis general de reglas
-- ============================================================================

DROP VIEW IF EXISTS v_reglas_efectividad;
CREATE VIEW v_reglas_efectividad AS
SELECT
    regla_aplicada,
    COUNT(*) as total_aplicaciones,
    SUM(CASE WHEN dual_coinciden = 1 THEN 1 ELSE 0 END) as coinciden,
    SUM(CASE WHEN dual_coinciden = 0 THEN 1 ELSE 0 END) as difieren,
    SUM(CASE WHEN estado_validacion = 'validado' THEN 1 ELSE 0 END) as validados,
    ROUND(100.0 * SUM(dual_coinciden) / NULLIF(COUNT(*), 0), 1) as pct_coincidencia,
    ROUND(AVG(score_semantico), 3) as avg_score_semantico
FROM ofertas_esco_matching
WHERE regla_aplicada IS NOT NULL
GROUP BY regla_aplicada
ORDER BY total_aplicaciones DESC;


-- ============================================================================
-- FIN DE MIGRACIÓN
-- ============================================================================
