-- Migration 019: Sistema Dual de Skills
-- Fecha: 2026-01-21
-- Descripcion: Agrega columnas para tracking de skills extraidos por reglas vs semantico
--              Similar al sistema dual de ISCO (isco_regla vs isco_semantico)

-- ============================================
-- PARTE 1: Columnas en ofertas_esco_matching
-- ============================================

-- Skills extraidos por reglas (si alguna regla aplica)
ALTER TABLE ofertas_esco_matching ADD COLUMN skills_regla_json TEXT;

-- Skills extraidos por metodo semantico (BGE-M3)
ALTER TABLE ofertas_esco_matching ADD COLUMN skills_semantico_json TEXT;

-- Identificador de la regla que se aplico (ej: RS1_python_developer)
ALTER TABLE ofertas_esco_matching ADD COLUMN skills_regla_aplicada TEXT;

-- 1 si skills_regla y skills_semantico coinciden, 0 si no, NULL si no hay regla
ALTER TABLE ofertas_esco_matching ADD COLUMN dual_coinciden_skills INTEGER;

-- Ratio de coherencia entre skills extraidos y skills esperados para el ISCO
-- Ejemplo: Si ISCO 2514 requiere 10 skills y matcheamos 6 -> 0.6
ALTER TABLE ofertas_esco_matching ADD COLUMN skills_coherence_ratio REAL;

-- Cantidad de skills esenciales del ISCO que fueron matcheados
ALTER TABLE ofertas_esco_matching ADD COLUMN essential_skills_matched INTEGER;

-- ============================================
-- PARTE 2: Columna en ofertas_esco_skills_detalle
-- ============================================

-- Origen del skill: 'regla', 'semantico', 'merged'
ALTER TABLE ofertas_esco_skills_detalle ADD COLUMN origen_tipo TEXT DEFAULT 'semantico';

-- ============================================
-- PARTE 3: Indices para consultas eficientes
-- ============================================

CREATE INDEX IF NOT EXISTS idx_dual_coinciden_skills ON ofertas_esco_matching(dual_coinciden_skills);
CREATE INDEX IF NOT EXISTS idx_skills_coherence ON ofertas_esco_matching(skills_coherence_ratio);
CREATE INDEX IF NOT EXISTS idx_skills_regla_aplicada ON ofertas_esco_matching(skills_regla_aplicada);
CREATE INDEX IF NOT EXISTS idx_skills_detalle_origen ON ofertas_esco_skills_detalle(origen_tipo);

-- ============================================
-- PARTE 4: Vista para analisis de skills duales
-- ============================================

CREATE VIEW IF NOT EXISTS v_skills_dual_analysis AS
SELECT
    m.id_oferta,
    o.titulo,
    m.isco_code,
    m.isco_label,
    m.skills_regla_aplicada,
    m.dual_coinciden_skills,
    m.skills_coherence_ratio,
    m.essential_skills_matched,
    CASE
        WHEN m.skills_regla_json IS NOT NULL THEN 'regla'
        ELSE 'semantico'
    END as metodo_skills_primario,
    m.skills_regla_json,
    m.skills_semantico_json,
    m.skills_oferta_json as skills_final_json
FROM ofertas_esco_matching m
JOIN ofertas o ON m.id_oferta = o.id_oferta
WHERE m.isco_code IS NOT NULL;

-- ============================================
-- PARTE 5: Vista para ofertas con divergencia skills dual
-- ============================================

CREATE VIEW IF NOT EXISTS v_skills_dual_divergencia AS
SELECT
    m.id_oferta,
    o.titulo,
    m.isco_code,
    m.isco_label,
    m.skills_regla_aplicada,
    m.skills_regla_json,
    m.skills_semantico_json,
    m.skills_coherence_ratio
FROM ofertas_esco_matching m
JOIN ofertas o ON m.id_oferta = o.id_oferta
WHERE m.dual_coinciden_skills = 0
  AND m.skills_regla_json IS NOT NULL;

-- ============================================
-- PARTE 6: Registro de migracion
-- ============================================

INSERT OR IGNORE INTO schema_migrations (migration_id, description, applied_at)
VALUES ('019_skills_dual', 'Sistema dual de skills (regla vs semantico)', datetime('now'));
