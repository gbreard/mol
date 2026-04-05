-- Migration 048: RPC para crear pipeline_commands desde la UI
-- Necesario porque RLS bloquea INSERT con anon_key

CREATE OR REPLACE FUNCTION crear_pipeline_command(
    p_comando TEXT,
    p_params JSONB DEFAULT '{}'::jsonb,
    p_creado_por TEXT DEFAULT 'admin@dashboard'
)
RETURNS UUID
LANGUAGE plpgsql SECURITY DEFINER
AS $$
DECLARE
    v_id UUID;
BEGIN
    INSERT INTO pipeline_commands (comando, params, creado_por)
    VALUES (p_comando, p_params, p_creado_por)
    RETURNING id INTO v_id;
    RETURN v_id;
END;
$$;

-- RPC para leer estado de un comando específico
CREATE OR REPLACE FUNCTION get_pipeline_command_status(p_id UUID)
RETURNS TABLE (
    estado TEXT,
    resultado JSONB,
    error_message TEXT,
    log TEXT
)
LANGUAGE sql SECURITY DEFINER
AS $$
    SELECT estado, resultado, error_message, log
    FROM pipeline_commands
    WHERE id = p_id;
$$;
