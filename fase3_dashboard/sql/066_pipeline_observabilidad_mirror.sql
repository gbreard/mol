-- Migration 066: Espejo de observabilidad en pipeline_local_status (SPEC S1C-F0.3)
-- El poller sube la última acta de corrida + alertas recientes (fuente de verdad
-- local en SQLite: pipeline_run_actas / pipeline_alertas) para que la Fábrica las muestre.
--
-- ADITIVA: dos columnas JSONB nuevas sobre la fila única id='current'.

ALTER TABLE pipeline_local_status ADD COLUMN IF NOT EXISTS ultima_acta JSONB;
ALTER TABLE pipeline_local_status ADD COLUMN IF NOT EXISTS alertas_recientes JSONB;
