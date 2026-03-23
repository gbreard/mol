-- Migration 033: Pipeline local status — snapshot del estado local (SQLite)
-- El poller actualiza esto cada minuto para que la Fábrica lo muestre

CREATE TABLE IF NOT EXISTS pipeline_local_status (
  id TEXT PRIMARY KEY DEFAULT 'current',  -- siempre 1 row, se hace upsert
  timestamp TIMESTAMPTZ DEFAULT NOW(),
  -- Scraping
  total_ofertas INTEGER DEFAULT 0,
  -- NLP
  nlp_procesadas INTEGER DEFAULT 0,
  nlp_pendientes INTEGER DEFAULT 0,
  nlp_aprobados INTEGER DEFAULT 0,
  nlp_bloqueados INTEGER DEFAULT 0,
  nlp_gate_aprobado_pct NUMERIC(5,1) DEFAULT 100,
  -- Matching
  matching_con INTEGER DEFAULT 0,
  matching_sin INTEGER DEFAULT 0,
  -- Validación
  validadas INTEGER DEFAULT 0,
  errores_pendientes INTEGER DEFAULT 0,
  -- Sync
  en_supabase INTEGER DEFAULT 0,
  pendientes_sync INTEGER DEFAULT 0,
  ultimo_sync TEXT
);

-- Insert initial row
INSERT INTO pipeline_local_status (id) VALUES ('current') ON CONFLICT DO NOTHING;

-- RLS
ALTER TABLE pipeline_local_status ENABLE ROW LEVEL SECURITY;

CREATE POLICY "pipeline_local_status_read" ON pipeline_local_status
  FOR SELECT USING (true);

CREATE POLICY "pipeline_local_status_write" ON pipeline_local_status
  FOR ALL USING (auth.role() = 'service_role')
  WITH CHECK (auth.role() = 'service_role');
