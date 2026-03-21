-- ============================================================
-- TABLAS: organizaciones + user_organizaciones
-- Propósito: Multi-tenancy para Oficinas de Empleo y Empresas
-- Cada OE ve solo sus datos. Cada empresa ve solo los suyos.
-- ============================================================

CREATE TABLE IF NOT EXISTS organizaciones (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  nombre VARCHAR(200) NOT NULL,
  tipo VARCHAR(30) NOT NULL,                -- 'oficina_empleo', 'empresa'
  jurisdiccion VARCHAR(100),                -- provincia/municipio (para OE)
  sector VARCHAR(100),                      -- sector económico (para empresa)
  activa BOOLEAN DEFAULT TRUE,
  metadata JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_org_tipo ON organizaciones(tipo);
CREATE INDEX IF NOT EXISTS idx_org_jurisdiccion ON organizaciones(jurisdiccion) WHERE tipo = 'oficina_empleo';

COMMENT ON TABLE organizaciones IS 'Oficinas de Empleo y Empresas. Cada una es un tenant con datos aislados.';

-- Relación usuario-organización
CREATE TABLE IF NOT EXISTS user_organizaciones (
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  organizacion_id UUID REFERENCES organizaciones(id) ON DELETE CASCADE,
  rol_en_org VARCHAR(30) NOT NULL,          -- 'tecnico', 'coordinador', 'rrhh', 'gerente'
  activo BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  PRIMARY KEY (user_id, organizacion_id)
);

CREATE INDEX IF NOT EXISTS idx_user_org_user ON user_organizaciones(user_id);
CREATE INDEX IF NOT EXISTS idx_user_org_org ON user_organizaciones(organizacion_id);

-- ============================================================
-- Agregar organizacion_id a perfiles_trabajadores (si existe)
-- ============================================================

DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'perfiles_trabajadores') THEN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'perfiles_trabajadores' AND column_name = 'organizacion_id') THEN
      ALTER TABLE perfiles_trabajadores ADD COLUMN organizacion_id UUID REFERENCES organizaciones(id);
      CREATE INDEX idx_perfiles_org ON perfiles_trabajadores(organizacion_id);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'perfiles_trabajadores' AND column_name = 'nota_tecnico') THEN
      ALTER TABLE perfiles_trabajadores ADD COLUMN nota_tecnico JSONB;
    END IF;
  END IF;
END $$;

-- ============================================================
-- RLS organizaciones
-- ============================================================

ALTER TABLE organizaciones ENABLE ROW LEVEL SECURITY;

-- Todos pueden leer organizaciones (para listar en UI)
CREATE POLICY "org_read_all" ON organizaciones
  FOR SELECT USING (true);

-- Solo autenticados pueden crear/modificar
CREATE POLICY "org_write_authenticated" ON organizaciones
  FOR ALL USING (auth.role() = 'authenticated');

-- ============================================================
-- RLS user_organizaciones
-- ============================================================

ALTER TABLE user_organizaciones ENABLE ROW LEVEL SECURITY;

-- Usuario ve solo sus propias relaciones
CREATE POLICY "user_org_read_own" ON user_organizaciones
  FOR SELECT USING (auth.uid() = user_id);

-- Admin ve todas
CREATE POLICY "user_org_read_admin" ON user_organizaciones
  FOR SELECT USING (
    EXISTS (
      SELECT 1 FROM auth.users
      WHERE id = auth.uid()
      AND raw_user_meta_data->>'role' = 'admin'
    )
  );

-- Solo autenticados pueden insertar/modificar
CREATE POLICY "user_org_write_authenticated" ON user_organizaciones
  FOR ALL USING (auth.role() = 'authenticated');

-- ============================================================
-- FUNCIÓN: get_user_org
-- Retorna la organización del usuario actual
-- ============================================================

CREATE OR REPLACE FUNCTION get_user_org()
RETURNS TABLE (
  organizacion_id UUID,
  nombre VARCHAR(200),
  tipo VARCHAR(30),
  jurisdiccion VARCHAR(100),
  rol_en_org VARCHAR(30)
) AS $$
  SELECT
    o.id,
    o.nombre,
    o.tipo,
    o.jurisdiccion,
    uo.rol_en_org
  FROM user_organizaciones uo
  JOIN organizaciones o ON o.id = uo.organizacion_id
  WHERE uo.user_id = auth.uid()
    AND uo.activo = TRUE
    AND o.activa = TRUE
  LIMIT 1;
$$ LANGUAGE sql STABLE SECURITY DEFINER;

-- ============================================================
-- FUNCIÓN: get_perfiles_by_org
-- Retorna perfiles de trabajadores de la organización del usuario
-- ============================================================

CREATE OR REPLACE FUNCTION get_perfiles_by_org()
RETURNS SETOF perfiles_trabajadores AS $$
DECLARE
  v_org_id UUID;
BEGIN
  SELECT organizacion_id INTO v_org_id
  FROM user_organizaciones
  WHERE user_id = auth.uid() AND activo = TRUE
  LIMIT 1;

  IF v_org_id IS NULL THEN
    RETURN;
  END IF;

  RETURN QUERY
  SELECT * FROM perfiles_trabajadores
  WHERE organizacion_id = v_org_id
  ORDER BY updated_at DESC;
END;
$$ LANGUAGE plpgsql STABLE SECURITY DEFINER;
