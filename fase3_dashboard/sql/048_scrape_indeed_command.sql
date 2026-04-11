-- Migration 048: Agregar scrape_indeed al CHECK constraint de pipeline_commands
-- Indeed corre local (IP del VPS bloqueada por Cloudflare).
-- El cron del VPS encola el comando via queue_indeed_local.py → Supabase.
-- El poller local (pipeline_command_poller.py) lo ejecuta.

ALTER TABLE pipeline_commands DROP CONSTRAINT IF EXISTS pipeline_commands_comando_check;

ALTER TABLE pipeline_commands ADD CONSTRAINT pipeline_commands_comando_check
CHECK (comando IN (
    'run_pipeline', 'run_nlp', 'run_matching',
    'reprocess_errors', 'revalidate_nlp', 'revalidate_matching',
    'reapply_rules', 'export_excel', 'sync_supabase',
    'sync_supabase_full', 'generate_training',
    'recluster_preview', 'recluster_apply',
    'scrape_indeed'
));
