-- Migration 039: Tabla pipeline_runs_history
-- M-01: Historial completo de runs del pipeline
-- Permite análisis de tendencias, correlación de cambios con impacto

CREATE TABLE IF NOT EXISTS pipeline_runs_history (
    id                    BIGSERIAL PRIMARY KEY,
    run_id                TEXT NOT NULL UNIQUE,
    timestamp             TIMESTAMPTZ NOT NULL,

    -- Versiones
    git_branch            TEXT,
    git_commit            TEXT,
    nlp_version           TEXT,
    matching_version      TEXT,

    -- Métricas del run
    ofertas_count         INT,
    skills_count          INT,
    failures_count        INT,
    failures_pct          REAL,
    errores_detectados    INT,
    errores_corregidos    INT,
    errores_escalados     INT,
    precision             REAL,

    -- Delta vs run anterior
    run_anterior_id       TEXT,
    delta_precision       REAL,
    delta_mejoras         INT,
    delta_regresiones     INT,
    reglas_nuevas         INT,
    sinonimos_count       INT,

    -- Top failures (JSON)
    top_failures          JSONB,

    -- Metadata
    created_at            TIMESTAMPTZ DEFAULT NOW()
);

-- Índices para queries de historial
CREATE INDEX IF NOT EXISTS idx_runs_history_timestamp ON pipeline_runs_history(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_runs_history_branch    ON pipeline_runs_history(git_branch);

-- RLS: SELECT solo platform_admin, INSERT bloqueado (solo via RPC)
ALTER TABLE pipeline_runs_history ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "admin_read_only" ON pipeline_runs_history;
CREATE POLICY "admin_read_only" ON pipeline_runs_history
    FOR SELECT TO authenticated
    USING (auth.jwt() ->> 'role' = 'platform_admin');
