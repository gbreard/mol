-- Migration 038: Campos ultimo_run_* en sistema_estado
-- M-01: Reporte consolidado post-run
-- Permite que /admin/metricas muestre el estado del último run del pipeline

ALTER TABLE sistema_estado ADD COLUMN IF NOT EXISTS ultimo_run_id TEXT;
ALTER TABLE sistema_estado ADD COLUMN IF NOT EXISTS ultimo_run_timestamp TEXT;
ALTER TABLE sistema_estado ADD COLUMN IF NOT EXISTS ultimo_run_branch TEXT;
ALTER TABLE sistema_estado ADD COLUMN IF NOT EXISTS ultimo_run_nlp_version TEXT;
ALTER TABLE sistema_estado ADD COLUMN IF NOT EXISTS ultimo_run_matching_version TEXT;
ALTER TABLE sistema_estado ADD COLUMN IF NOT EXISTS ultimo_run_ofertas INT;
ALTER TABLE sistema_estado ADD COLUMN IF NOT EXISTS ultimo_run_skills INT;
ALTER TABLE sistema_estado ADD COLUMN IF NOT EXISTS ultimo_run_failures INT;
ALTER TABLE sistema_estado ADD COLUMN IF NOT EXISTS ultimo_run_failures_pct REAL;
ALTER TABLE sistema_estado ADD COLUMN IF NOT EXISTS ultimo_run_errores INT;
ALTER TABLE sistema_estado ADD COLUMN IF NOT EXISTS ultimo_run_corregidos INT;
ALTER TABLE sistema_estado ADD COLUMN IF NOT EXISTS ultimo_run_escalados INT;
ALTER TABLE sistema_estado ADD COLUMN IF NOT EXISTS ultimo_run_precision REAL;
ALTER TABLE sistema_estado ADD COLUMN IF NOT EXISTS ultimo_run_delta_precision REAL;
ALTER TABLE sistema_estado ADD COLUMN IF NOT EXISTS ultimo_run_delta_regresiones INT;
ALTER TABLE sistema_estado ADD COLUMN IF NOT EXISTS ultimo_run_delta_mejoras INT;
ALTER TABLE sistema_estado ADD COLUMN IF NOT EXISTS ultimo_run_reglas_nuevas INT;
ALTER TABLE sistema_estado ADD COLUMN IF NOT EXISTS ultimo_run_top_failures TEXT;
