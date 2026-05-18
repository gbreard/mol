-- Migration 023: agregar columnas source + description e índices a pipeline_runs_history
-- Aplicar desde Supabase Studio → SQL Editor (Management API estuvo bloqueada por Cloudflare 1010
-- al momento de generar esta migration, 2026-05-18).
--
-- Después de aplicar, ejecutar el backfill:
--   python scripts/backfill_pipeline_runs_source.py

ALTER TABLE pipeline_runs_history
    ADD COLUMN IF NOT EXISTS source TEXT,
    ADD COLUMN IF NOT EXISTS description TEXT;

CREATE INDEX IF NOT EXISTS idx_pipeline_runs_history_timestamp
    ON pipeline_runs_history(timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_pipeline_runs_history_source
    ON pipeline_runs_history(source);
