-- Migration 058: reconciliar el CHECK de pipeline_commands + comando aplicar_candidata
-- ============================================================================
-- Contexto: SPEC S1C-PUENTE (mesa de Cyn, P4). El poller (COMMAND_MAP) maneja
-- comandos que el CHECK de pipeline_commands no permite -> drift.
--
-- Estado antes de esta migracion:
--   CHECK (047) tiene 13 comandos.
--   Poller (COMMAND_MAP) maneja 14.
--   Drift = 'scrape_indeed' (el poller lo ejecuta, la tabla lo RECHAZA en INSERT).
--
-- Esta migracion:
--   1. Reconcilia: agrega 'scrape_indeed' (drift preexistente).
--   2. Agrega 'aplicar_candidata' (nuevo, escritura git-first del puente).
-- ============================================================================

ALTER TABLE pipeline_commands DROP CONSTRAINT IF EXISTS pipeline_commands_comando_check;

ALTER TABLE pipeline_commands ADD CONSTRAINT pipeline_commands_comando_check
CHECK (comando IN (
  'run_pipeline',
  'run_nlp',
  'run_matching',
  'reprocess_errors',
  'revalidate_nlp',
  'revalidate_matching',
  'reapply_rules',
  'export_excel',
  'sync_supabase',
  'sync_supabase_full',
  'generate_training',
  'recluster_preview',
  'recluster_apply',
  'scrape_indeed',        -- reconciliacion drift: el poller ya lo manejaba
  'aplicar_candidata'     -- NUEVO: escritura git-first del puente (mesa de Cyn)
));

-- Nota: el CHECK ahora tiene 15 comandos, alineado con el COMMAND_MAP del poller
-- (14 previos + aplicar_candidata). Cualquier comando nuevo en el poller exige
-- una migracion que lo agregue aca (git-first: la tabla no acepta lo que el poller
-- no declara, y viceversa).
