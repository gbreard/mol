-- Migration 031: Pipeline Commands — Gateway local para control de fábrica
-- Mismo patrón que scraping_commands (ya funciona en producción)
--
-- El admin crea comandos desde la UI → Supabase → poller local los ejecuta

CREATE TABLE IF NOT EXISTS pipeline_commands (
  id              UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  comando         TEXT NOT NULL
    CHECK (comando IN (
      'run_pipeline',           -- Procesar N ofertas nuevas (NLP + Matching + Validación)
      'run_nlp',                -- Solo NLP para N ofertas o IDs específicos
      'run_matching',           -- Solo Matching (skip NLP)
      'reprocess_errors',       -- Reprocesar ofertas con errores pendientes
      'revalidate_nlp',         -- Re-ejecutar Gate NLP
      'revalidate_matching',    -- Re-ejecutar Gate Matching
      'reapply_rules',          -- Aplicar reglas nuevas a ofertas ya validadas
      'export_excel',           -- Exportar Excel de validación
      'sync_supabase',          -- Sync incremental a Supabase
      'sync_supabase_full',     -- Sync full a Supabase
      'generate_training'       -- Regenerar training pairs
    )),
  params          JSONB DEFAULT '{}'::jsonb,   -- {limit: 500, ids: [...], skip_nlp: true, ...}
  estado          TEXT NOT NULL DEFAULT 'pendiente'
    CHECK (estado IN ('pendiente', 'ejecutando', 'completado', 'error', 'cancelado')),
  log             TEXT,                         -- Output del proceso (actualizado en tiempo real)
  resultado       JSONB,                        -- Métricas al terminar {procesadas, errores, duracion, ...}
  error_message   TEXT,                         -- Mensaje de error si estado = 'error'
  creado_por      TEXT,                         -- Email del admin que creó el comando
  created_at      TIMESTAMPTZ DEFAULT NOW(),
  started_at      TIMESTAMPTZ,                  -- Cuándo empezó a ejecutar
  completed_at    TIMESTAMPTZ                   -- Cuándo terminó
);

-- Índices
CREATE INDEX IF NOT EXISTS idx_pipeline_commands_estado ON pipeline_commands(estado);
CREATE INDEX IF NOT EXISTS idx_pipeline_commands_created ON pipeline_commands(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_pipeline_commands_pendiente ON pipeline_commands(created_at)
  WHERE estado = 'pendiente';

-- RLS
ALTER TABLE pipeline_commands ENABLE ROW LEVEL SECURITY;

-- Lectura: admins pueden ver todos los comandos
CREATE POLICY "pipeline_commands_read" ON pipeline_commands
  FOR SELECT USING (true);

-- Escritura: solo service_role (admin via API, poller via service key)
CREATE POLICY "pipeline_commands_write" ON pipeline_commands
  FOR ALL USING (auth.role() = 'service_role')
  WITH CHECK (auth.role() = 'service_role');

-- Vista helper: comandos recientes con duración calculada
CREATE OR REPLACE VIEW v_pipeline_commands_recent AS
SELECT
  id,
  comando,
  params,
  estado,
  LEFT(log, 500) AS log_preview,
  resultado,
  error_message,
  creado_por,
  created_at,
  started_at,
  completed_at,
  CASE
    WHEN completed_at IS NOT NULL AND started_at IS NOT NULL
    THEN EXTRACT(EPOCH FROM (completed_at - started_at))::integer
    WHEN started_at IS NOT NULL
    THEN EXTRACT(EPOCH FROM (NOW() - started_at))::integer
    ELSE NULL
  END AS duracion_seg
FROM pipeline_commands
ORDER BY created_at DESC
LIMIT 50;
