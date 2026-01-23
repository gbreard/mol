-- Migration 018: Tablas para Experimentos A/B
-- Fecha: 2026-01-20
-- Proposito: Tablas SEPARADAS para snapshot y comparacion de experimentos
--
-- IMPORTANTE: Estas tablas NO afectan el pipeline principal.
-- Son 100% independientes de ofertas_nlp, ofertas_esco_matching, etc.

-- ============================================
-- TABLA: ab_snapshot_matching
-- ============================================
-- Snapshot del estado de matching para comparacion A/B

CREATE TABLE IF NOT EXISTS ab_snapshot_matching (
    snapshot_id TEXT NOT NULL,          -- "baseline_v340", "experiment_20260120"
    id_oferta TEXT NOT NULL,

    -- ESCO completo (no solo ISCO)
    esco_occupation_uri TEXT,
    esco_occupation_label TEXT,
    isco_code TEXT,

    -- Scores
    occupation_match_score REAL,
    occupation_match_method TEXT,
    confidence_score REAL,

    -- Dual matching (v3.4.1)
    isco_regla TEXT,                    -- ISCO sugerido por regla de negocio
    isco_semantico TEXT,                -- ISCO sugerido por semantico
    regla_aplicada TEXT,                -- Nombre de la regla (R111, R132, etc)
    dual_coinciden INTEGER,             -- 1=coinciden, 0=difieren
    decision_metodo TEXT,               -- Como se decidio el final

    -- Metadata
    run_id TEXT,                        -- Run que genero estos datos
    snapshot_timestamp TEXT DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (snapshot_id, id_oferta)
);

-- ============================================
-- TABLA: ab_snapshot_nlp
-- ============================================
-- Snapshot de campos NLP relevantes para comparacion

CREATE TABLE IF NOT EXISTS ab_snapshot_nlp (
    snapshot_id TEXT NOT NULL,
    id_oferta TEXT NOT NULL,

    -- Tareas
    tareas_explicitas TEXT,
    tareas_inferidas TEXT,

    -- Clasificacion
    area_funcional TEXT,
    nivel_seniority TEXT,
    sector_empresa TEXT,

    -- Skills extraidas por NLP
    skills_tecnicas_list TEXT,          -- JSON array
    soft_skills_list TEXT,              -- JSON array

    -- Metadata
    snapshot_timestamp TEXT DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (snapshot_id, id_oferta)
);

-- ============================================
-- TABLA: ab_snapshot_skills
-- ============================================
-- Snapshot de skills ESCO matcheadas

CREATE TABLE IF NOT EXISTS ab_snapshot_skills (
    snapshot_id TEXT NOT NULL,
    id_oferta TEXT NOT NULL,

    skills_json TEXT,                   -- JSON array de {label, score, source}
    skills_count INTEGER,               -- Cantidad total de skills

    -- Metadata
    snapshot_timestamp TEXT DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (snapshot_id, id_oferta)
);

-- ============================================
-- TABLA: ab_experiments
-- ============================================
-- Registro de experimentos realizados

CREATE TABLE IF NOT EXISTS ab_experiments (
    experiment_id TEXT PRIMARY KEY,     -- "exp_20260120_1830"
    snapshot_baseline TEXT NOT NULL,    -- ID del snapshot inicial
    snapshot_after TEXT,                -- ID del snapshot despues (opcional)

    -- Configuracion
    offer_count INTEGER,                -- Cuantas ofertas
    offer_ids TEXT,                     -- JSON array de IDs

    -- Resultado
    status TEXT DEFAULT 'created',      -- created | running | completed | reverted
    run_id_experiment TEXT,             -- Run del reproceso

    -- Timestamps
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    completed_at TEXT,

    -- Resumen de resultados
    esco_changed_count INTEGER,
    nlp_changed_count INTEGER,
    skills_changed_count INTEGER,
    summary_json TEXT                   -- JSON con resumen detallado
);

-- ============================================
-- INDICES
-- ============================================

CREATE INDEX IF NOT EXISTS idx_ab_matching_snapshot ON ab_snapshot_matching(snapshot_id);
CREATE INDEX IF NOT EXISTS idx_ab_nlp_snapshot ON ab_snapshot_nlp(snapshot_id);
CREATE INDEX IF NOT EXISTS idx_ab_skills_snapshot ON ab_snapshot_skills(snapshot_id);
CREATE INDEX IF NOT EXISTS idx_ab_experiments_status ON ab_experiments(status);

-- ============================================
-- VERIFICACION
-- ============================================

SELECT 'Tablas de experimentos A/B creadas' as status;

SELECT name FROM sqlite_master
WHERE type = 'table'
AND name LIKE 'ab_%';
