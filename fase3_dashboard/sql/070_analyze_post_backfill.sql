-- ============================================================
-- 070 — Mantenimiento post-backfill B.4 (Fase 5)
-- ============================================================
-- NO es una migración de schema. Es una operación de mantenimiento
-- one-time: el backfill B.4 hizo UPDATE masivo sobre ~97K filas de
-- ofertas_dashboard (6 columnas de ciclo de vida) → tuplas muertas +
-- estadísticas de planner desactualizadas. Eso empuja a las RPCs
-- borderline (get_pipeline_status 5s, reconciliar_sistemas 8s) sobre
-- su statement_timeout → 57014.
--
-- Objetivo: refrescar stats del planner (y compactar, si el Editor lo
-- permite). Las stats son la parte que probablemente explica el salto.
--
-- EJECUTAR EN: Supabase SQL Editor (https://supabase.com/dashboard)
-- ============================================================

-- Opción A (preferida): VACUUM + ANALYZE. Compacta tuplas muertas y
-- refresca stats. VACUUM NO corre dentro de una transacción; el SQL
-- Editor de Supabase a veces envuelve todo en una → si tira
--   "VACUUM cannot run inside a transaction block"
-- usar la Opción B de abajo (comentar A, descomentar B).
VACUUM (ANALYZE) ofertas_dashboard;
VACUUM (ANALYZE) ofertas_skills;

-- Opción B (fallback si A es rechazada por el Editor):
-- ANALYZE solo — refresca stats sin compactar. Corre dentro de txn.
-- ANALYZE ofertas_dashboard;
-- ANALYZE ofertas_skills;
