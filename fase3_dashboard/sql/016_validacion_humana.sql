-- ============================================================
-- 016_validacion_humana.sql
-- Columnas y RPC para validación humana en ofertas_dashboard
-- ============================================================

-- 1. Columnas nuevas en ofertas_dashboard
ALTER TABLE ofertas_dashboard
  ADD COLUMN IF NOT EXISTS validacion_humana text,
  ADD COLUMN IF NOT EXISTS validacion_humana_at timestamptz,
  ADD COLUMN IF NOT EXISTS validacion_humana_por text,
  ADD COLUMN IF NOT EXISTS validacion_correcciones jsonb;

-- Valores válidos
ALTER TABLE ofertas_dashboard
  DROP CONSTRAINT IF EXISTS chk_validacion_humana_valor;
ALTER TABLE ofertas_dashboard
  ADD CONSTRAINT chk_validacion_humana_valor
  CHECK (validacion_humana IS NULL OR validacion_humana IN ('ok', 'error', 'revisar', 'basura'));

-- 2. Índice para filtrar por estado de validación
CREATE INDEX IF NOT EXISTS idx_ofertas_validacion_humana
  ON ofertas_dashboard(validacion_humana);

-- 3. RPC: guardar_validacion_humana
--    SECURITY DEFINER para bypasear RLS (mismo patrón que crear_issue en 005)
CREATE OR REPLACE FUNCTION guardar_validacion_humana(
  p_id_oferta TEXT,
  p_resultado TEXT,
  p_correcciones JSONB DEFAULT NULL
)
RETURNS BOOLEAN AS $$
DECLARE
  v_email TEXT;
BEGIN
  -- Solo admins pueden validar
  IF NOT is_platform_admin() THEN
    RAISE EXCEPTION 'Solo platform_admin puede validar ofertas';
  END IF;

  -- Validar resultado
  IF p_resultado NOT IN ('ok', 'error', 'revisar', 'basura') THEN
    RAISE EXCEPTION 'Resultado inválido: %. Valores: ok, error, revisar, basura', p_resultado;
  END IF;

  -- Obtener email del validador
  v_email := coalesce(
    (auth.jwt() -> 'email')::text,
    (SELECT email FROM usuarios WHERE id = auth.uid())
  );
  -- Limpiar comillas del JWT
  v_email := trim(both '"' from v_email);

  UPDATE ofertas_dashboard
  SET
    validacion_humana = p_resultado,
    validacion_humana_at = NOW(),
    validacion_humana_por = v_email,
    validacion_correcciones = p_correcciones
  WHERE id_oferta = p_id_oferta;

  RETURN FOUND;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
