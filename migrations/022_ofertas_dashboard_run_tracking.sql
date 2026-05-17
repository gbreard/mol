-- =============================================================================
-- Migration 022 — run_id + matching_version en ofertas_dashboard (Supabase)
-- Fecha: 2026-05-17
-- Aplicada en: Supabase MOL (uywzoyhjjofsvvsrrnek) via Management API
-- =============================================================================
--
-- CONTEXTO:
-- El SELECT del sync (scripts/exports/sync_to_supabase.py línea 213) ya trae
-- m.run_id y m.matching_version desde ofertas_esco_matching local, pero
-- transform_oferta_for_supabase() no los incluía en el dict de salida.
-- Resultado: 68K rows en ofertas_dashboard sin trazabilidad de qué corrida
-- las produjo.
--
-- SOLUCIÓN:
-- 1. Agregar columnas run_id (TEXT) y matching_version (TEXT) a
--    ofertas_dashboard.
-- 2. Índice en run_id para filtros rápidos en la UI de validación.
-- 3. transform_oferta_for_supabase() ahora incluye ambos campos (cambio
--    paralelo en sync_to_supabase.py).
-- 4. Backfill histórico de las 68K filas con un solo round-trip vía RPC
--    batch (ver scripts/exports/backfill_run_tracking.py).
--
-- HABILITA:
-- - Filtro "Run / Corrida" en /admin/validacion para que Cyn pueda
--   auditar ofertas por corrida específica (ej: régimen 15-17 mayo 2026).
-- - Comparación entre versiones de matcher cuando exista v3.6+.
-- =============================================================================

ALTER TABLE ofertas_dashboard
    ADD COLUMN IF NOT EXISTS run_id TEXT,
    ADD COLUMN IF NOT EXISTS matching_version TEXT;

CREATE INDEX IF NOT EXISTS idx_ofertas_dashboard_run_id
    ON ofertas_dashboard(run_id);
