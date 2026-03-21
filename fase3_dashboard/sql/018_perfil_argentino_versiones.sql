-- ============================================================
-- TABLA: perfil_argentino_versiones
-- Propósito: Snapshots versionados del Perfil Consolidado Argentino
-- Solo UNA versión activa a la vez. Todo el sistema (matching,
-- búsqueda, reportes) apunta a la versión activa.
-- ============================================================

CREATE TABLE IF NOT EXISTS perfil_argentino_versiones (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  version VARCHAR(20) NOT NULL UNIQUE,          -- 'v1.0', 'v2.1', etc.

  -- Snapshot completo del perfil al momento del corte
  -- Estructura: { "ocupaciones": { "<uri>": { "label": "...", "isco": "...", "skills_consolidadas": [...] } } }
  snapshot JSONB NOT NULL,

  -- Métricas del corte
  total_skills INTEGER NOT NULL DEFAULT 0,
  total_emergentes_aprobadas INTEGER NOT NULL DEFAULT 0,
  total_ocupaciones INTEGER NOT NULL DEFAULT 0,

  -- Metadata
  nota TEXT,                                     -- Nota del analista al crear el corte
  creado_por UUID REFERENCES auth.users(id),
  activa BOOLEAN DEFAULT FALSE,                  -- Solo UNA puede ser TRUE

  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Constraint: solo una versión activa a la vez
CREATE UNIQUE INDEX IF NOT EXISTS idx_perfil_version_activa
  ON perfil_argentino_versiones(activa) WHERE activa = TRUE;

-- Índices
CREATE INDEX IF NOT EXISTS idx_perfil_version_nombre
  ON perfil_argentino_versiones(version);
CREATE INDEX IF NOT EXISTS idx_perfil_version_fecha
  ON perfil_argentino_versiones(created_at DESC);

-- Comentarios
COMMENT ON TABLE perfil_argentino_versiones IS 'Snapshots versionados del Perfil Consolidado Argentino. La versión activa es la fuente de verdad para matching y reportes.';
COMMENT ON COLUMN perfil_argentino_versiones.snapshot IS 'JSONB con el estado completo de esco_argentino al momento del corte';
COMMENT ON COLUMN perfil_argentino_versiones.activa IS 'Solo una versión puede ser activa (constraint unique parcial)';

-- ============================================================
-- RLS
-- ============================================================

ALTER TABLE perfil_argentino_versiones ENABLE ROW LEVEL SECURITY;

-- Todos pueden leer (es referencia pública)
CREATE POLICY "perfil_versiones_read_all" ON perfil_argentino_versiones
  FOR SELECT USING (true);

-- Solo autenticados pueden crear/modificar (admin en la práctica)
CREATE POLICY "perfil_versiones_write_authenticated" ON perfil_argentino_versiones
  FOR ALL USING (auth.role() = 'authenticated');

-- ============================================================
-- FUNCIÓN: crear_version_perfil_argentino
-- Congela un snapshot de esco_argentino y lo marca como activa
-- ============================================================

CREATE OR REPLACE FUNCTION crear_version_perfil_argentino(
  p_version VARCHAR(20),
  p_nota TEXT DEFAULT NULL,
  p_user_id UUID DEFAULT NULL
) RETURNS UUID AS $$
DECLARE
  v_snapshot JSONB;
  v_total_skills INTEGER;
  v_total_emergentes INTEGER;
  v_total_ocupaciones INTEGER;
  v_new_id UUID;
BEGIN
  -- Construir snapshot desde esco_argentino actual
  SELECT jsonb_object_agg(
    esco_occupation_uri,
    jsonb_build_object(
      'label', esco_occupation_label,
      'isco', isco_code,
      'skills_consolidadas', skills_consolidadas,
      'total_skills', total_skills,
      'skills_from_esco', skills_from_esco,
      'skills_from_argentina', skills_from_argentina,
      'cobertura_esco_essential', cobertura_esco_essential
    )
  ) INTO v_snapshot
  FROM esco_argentino;

  -- Calcular métricas
  SELECT
    COALESCE(SUM(total_skills), 0),
    COALESCE(SUM(skills_from_argentina), 0),
    COUNT(*)
  INTO v_total_skills, v_total_emergentes, v_total_ocupaciones
  FROM esco_argentino;

  -- Desactivar versión anterior
  UPDATE perfil_argentino_versiones SET activa = FALSE WHERE activa = TRUE;

  -- Crear nueva versión activa
  INSERT INTO perfil_argentino_versiones (
    version, snapshot, total_skills, total_emergentes_aprobadas,
    total_ocupaciones, nota, creado_por, activa
  ) VALUES (
    p_version, COALESCE(v_snapshot, '{}'::jsonb), v_total_skills,
    v_total_emergentes, v_total_ocupaciones, p_nota, p_user_id, TRUE
  ) RETURNING id INTO v_new_id;

  RETURN v_new_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================================
-- FUNCIÓN: activar_version_perfil (rollback)
-- ============================================================

CREATE OR REPLACE FUNCTION activar_version_perfil(
  p_version_id UUID
) RETURNS VOID AS $$
BEGIN
  -- Verificar que existe
  IF NOT EXISTS (SELECT 1 FROM perfil_argentino_versiones WHERE id = p_version_id) THEN
    RAISE EXCEPTION 'Versión no encontrada';
  END IF;

  -- Desactivar actual
  UPDATE perfil_argentino_versiones SET activa = FALSE WHERE activa = TRUE;

  -- Activar la solicitada
  UPDATE perfil_argentino_versiones SET activa = TRUE WHERE id = p_version_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================================
-- FUNCIÓN: get_perfil_activo
-- Retorna el snapshot de la versión activa (para matching)
-- ============================================================

CREATE OR REPLACE FUNCTION get_perfil_activo()
RETURNS TABLE (
  version VARCHAR(20),
  snapshot JSONB,
  total_skills INTEGER,
  total_emergentes INTEGER,
  created_at TIMESTAMPTZ
) AS $$
  SELECT version, snapshot, total_skills, total_emergentes_aprobadas, created_at
  FROM perfil_argentino_versiones
  WHERE activa = TRUE
  LIMIT 1;
$$ LANGUAGE sql STABLE;
