-- ============================================================
-- Bloque H2a: Cola de comandos para scraping remoto
--
-- El admin crea comandos desde la UI.
-- Un poller en el VPS los lee cada 1 min y ejecuta.
-- ============================================================

CREATE TABLE IF NOT EXISTS scraping_commands (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  comando TEXT NOT NULL,           -- lanzar_portal, lanzar_todos, sync_vps_local, sync_local_supabase
  params JSONB DEFAULT '{}',       -- {portal: "bumeran"}, etc.
  estado TEXT NOT NULL DEFAULT 'pendiente',  -- pendiente, ejecutando, completado, error, cancelado
  creado_por TEXT,                  -- email del admin
  log TEXT,                        -- output progresivo del comando
  resultado JSONB,                 -- {ofertas: 391, errores: 0, duracion_seg: 120}
  error_mensaje TEXT,              -- si falló, por qué
  created_at TIMESTAMPTZ DEFAULT NOW(),
  started_at TIMESTAMPTZ,          -- cuando el poller lo tomó
  completed_at TIMESTAMPTZ,        -- cuando terminó (ok o error)
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Índice para el poller (busca pendientes)
CREATE INDEX IF NOT EXISTS idx_scraping_commands_estado
  ON scraping_commands(estado) WHERE estado = 'pendiente';

-- Índice para listar recientes
CREATE INDEX IF NOT EXISTS idx_scraping_commands_created
  ON scraping_commands(created_at DESC);

-- RLS: admin puede crear y leer, service_role puede todo
ALTER TABLE scraping_commands ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Admin puede leer comandos" ON scraping_commands
  FOR SELECT USING (true);

CREATE POLICY "Admin puede crear comandos" ON scraping_commands
  FOR INSERT WITH CHECK (true);

CREATE POLICY "Service role puede actualizar" ON scraping_commands
  FOR UPDATE USING (auth.role() = 'service_role');

-- Trigger updated_at
CREATE OR REPLACE FUNCTION update_scraping_commands_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_scraping_commands_updated_at
  BEFORE UPDATE ON scraping_commands
  FOR EACH ROW
  EXECUTE FUNCTION update_scraping_commands_updated_at();

-- RPC para listar comandos recientes con formato limpio
CREATE OR REPLACE FUNCTION get_scraping_commands(p_limit int DEFAULT 20)
RETURNS json
LANGUAGE plpgsql
STABLE
SECURITY DEFINER
SET statement_timeout = '5s'
AS $$
DECLARE
  v_result json;
BEGIN
  SELECT COALESCE(json_agg(row_to_json(c)), '[]'::json)
  INTO v_result
  FROM (
    SELECT
      id, comando, params, estado, creado_por,
      LEFT(log, 500) as log_preview,
      resultado, error_mensaje,
      created_at, started_at, completed_at,
      CASE
        WHEN completed_at IS NOT NULL AND started_at IS NOT NULL
        THEN EXTRACT(EPOCH FROM (completed_at - started_at))::int
        WHEN started_at IS NOT NULL
        THEN EXTRACT(EPOCH FROM (NOW() - started_at))::int
        ELSE NULL
      END as duracion_seg
    FROM scraping_commands
    ORDER BY created_at DESC
    LIMIT p_limit
  ) c;

  RETURN v_result;
END;
$$;
