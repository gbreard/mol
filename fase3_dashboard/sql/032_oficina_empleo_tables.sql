-- Migration 032: Tablas para Oficina de Empleo
-- worker_profiles: perfiles de trabajadores con skills capturadas
-- perfiles_puesto: perfiles de puesto con skills requeridas/deseables

-- ============================================================
-- worker_profiles: perfil del trabajador
-- ============================================================

CREATE TABLE IF NOT EXISTS worker_profiles (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  nombre TEXT NOT NULL,
  dni TEXT,
  edad TEXT,
  nivel_educativo TEXT,
  skills JSONB DEFAULT '[]'::jsonb,               -- [{uri, label, type, source}]
  ocupaciones_compatibles JSONB DEFAULT '[]'::jsonb, -- [{isco_code, label, match_score}]
  organizacion_id UUID,                            -- FK a organizaciones (OE que lo registró)
  creado_por TEXT,                                  -- Email del técnico
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Índices
CREATE INDEX IF NOT EXISTS idx_worker_profiles_dni ON worker_profiles(dni) WHERE dni IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_worker_profiles_created ON worker_profiles(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_worker_profiles_org ON worker_profiles(organizacion_id) WHERE organizacion_id IS NOT NULL;

-- RLS
ALTER TABLE worker_profiles ENABLE ROW LEVEL SECURITY;

CREATE POLICY "worker_profiles_read" ON worker_profiles
  FOR SELECT USING (true);

CREATE POLICY "worker_profiles_write" ON worker_profiles
  FOR ALL USING (auth.role() = 'service_role')
  WITH CHECK (auth.role() = 'service_role');

-- Trigger updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS worker_profiles_updated_at ON worker_profiles;
CREATE TRIGGER worker_profiles_updated_at
  BEFORE UPDATE ON worker_profiles
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================
-- perfiles_puesto: perfil de puesto/vacante
-- ============================================================

CREATE TABLE IF NOT EXISTS perfiles_puesto (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  titulo TEXT NOT NULL,
  isco_code TEXT,                                   -- Código ISCO asociado
  skills JSONB DEFAULT '[]'::jsonb,                -- [{uri, label, type, source, required: bool}]
  organizacion_id UUID,                            -- FK a organizaciones
  creado_por TEXT,                                  -- Email del técnico
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Índices
CREATE INDEX IF NOT EXISTS idx_perfiles_puesto_created ON perfiles_puesto(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_perfiles_puesto_isco ON perfiles_puesto(isco_code) WHERE isco_code IS NOT NULL;

-- RLS
ALTER TABLE perfiles_puesto ENABLE ROW LEVEL SECURITY;

CREATE POLICY "perfiles_puesto_read" ON perfiles_puesto
  FOR SELECT USING (true);

CREATE POLICY "perfiles_puesto_write" ON perfiles_puesto
  FOR ALL USING (auth.role() = 'service_role')
  WITH CHECK (auth.role() = 'service_role');

DROP TRIGGER IF EXISTS perfiles_puesto_updated_at ON perfiles_puesto;
CREATE TRIGGER perfiles_puesto_updated_at
  BEFORE UPDATE ON perfiles_puesto
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
