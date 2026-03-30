-- Migration 040: RPCs para pipeline_runs_history
-- M-01: INSERT via SECURITY DEFINER (compatible con anon_key)
-- SELECT via SECURITY DEFINER (solo platform_admin)

-- RPC INSERT: usado por sync_learnings.py con anon_key
-- ON CONFLICT DO NOTHING evita duplicados si se re-ejecuta
CREATE OR REPLACE FUNCTION insertar_pipeline_run(
    p_run_id TEXT,
    p_timestamp TIMESTAMPTZ,
    p_git_branch TEXT DEFAULT NULL,
    p_git_commit TEXT DEFAULT NULL,
    p_nlp_version TEXT DEFAULT NULL,
    p_matching_version TEXT DEFAULT NULL,
    p_ofertas_count INT DEFAULT NULL,
    p_skills_count INT DEFAULT NULL,
    p_failures_count INT DEFAULT NULL,
    p_failures_pct REAL DEFAULT NULL,
    p_errores_detectados INT DEFAULT NULL,
    p_errores_corregidos INT DEFAULT NULL,
    p_errores_escalados INT DEFAULT NULL,
    p_precision REAL DEFAULT NULL,
    p_run_anterior_id TEXT DEFAULT NULL,
    p_delta_precision REAL DEFAULT NULL,
    p_delta_mejoras INT DEFAULT NULL,
    p_delta_regresiones INT DEFAULT NULL,
    p_reglas_nuevas INT DEFAULT NULL,
    p_sinonimos_count INT DEFAULT NULL,
    p_top_failures JSONB DEFAULT NULL
)
RETURNS VOID
LANGUAGE plpgsql SECURITY DEFINER
AS $$
BEGIN
    INSERT INTO pipeline_runs_history (
        run_id, timestamp, git_branch, git_commit,
        nlp_version, matching_version,
        ofertas_count, skills_count, failures_count, failures_pct,
        errores_detectados, errores_corregidos, errores_escalados, precision,
        run_anterior_id, delta_precision, delta_mejoras, delta_regresiones,
        reglas_nuevas, sinonimos_count, top_failures
    ) VALUES (
        p_run_id, p_timestamp, p_git_branch, p_git_commit,
        p_nlp_version, p_matching_version,
        p_ofertas_count, p_skills_count, p_failures_count, p_failures_pct,
        p_errores_detectados, p_errores_corregidos, p_errores_escalados, p_precision,
        p_run_anterior_id, p_delta_precision, p_delta_mejoras, p_delta_regresiones,
        p_reglas_nuevas, p_sinonimos_count, p_top_failures
    )
    ON CONFLICT (run_id) DO NOTHING;
END;
$$;

-- RPC SELECT: usado por dashboard
CREATE OR REPLACE FUNCTION get_pipeline_runs_history(limit_n INT DEFAULT 30)
RETURNS SETOF pipeline_runs_history
LANGUAGE sql SECURITY DEFINER
AS $$
    SELECT * FROM pipeline_runs_history
    ORDER BY timestamp DESC
    LIMIT limit_n;
$$;
