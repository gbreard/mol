-- Migration 035: Modelo de datos S1/S2/S3 — Personas, Perfiles, Casos, Derivaciones
-- Basado en PLAN_INTEGRACION_GERARDO.md de Sergio
-- Reemplaza worker_profiles (deprecada, 0 rows)

-- ============================================================
-- 1. PERSONAS
-- ============================================================

CREATE TABLE IF NOT EXISTS personas (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  nombre          TEXT NOT NULL,
  dni             TEXT,
  edad            INTEGER,
  nivel_educativo TEXT,
  ubicacion       TEXT,
  telefono        TEXT,
  email           TEXT,
  opt_in          BOOLEAN DEFAULT FALSE,
  origen          TEXT CHECK (origen IN ('S1','S2')),
  created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_personas_dni ON personas(dni) WHERE dni IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_personas_nombre ON personas USING gin(to_tsvector('spanish', nombre));

-- ============================================================
-- 2. PERFILES
-- ============================================================

CREATE TABLE IF NOT EXISTS perfiles (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  persona_id      UUID REFERENCES personas(id) ON DELETE CASCADE,
  origen          TEXT CHECK (origen IN ('S1','S2')),
  completitud     INTEGER DEFAULT 0,
  nivel_confianza DECIMAL DEFAULT 0,
  updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_perfiles_persona ON perfiles(persona_id);

-- ============================================================
-- 3. PERFIL_SKILLS
-- ============================================================

CREATE TABLE IF NOT EXISTS perfil_skills (
  id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  perfil_id            UUID REFERENCES perfiles(id) ON DELETE CASCADE,
  skill_uri            TEXT NOT NULL,
  skill_label          TEXT NOT NULL,
  via_captura          TEXT CHECK (via_captura IN ('ocupacion','tarea','texto','formacion')),
  estado               TEXT CHECK (estado IN ('confirmada','sugerida','descartada')) DEFAULT 'sugerida',
  confianza            DECIMAL DEFAULT 0.5,
  validado_por_tecnico BOOLEAN DEFAULT FALSE,
  created_at           TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_perfil_skills_perfil ON perfil_skills(perfil_id, estado);

-- ============================================================
-- 4. CASOS
-- ============================================================

CREATE TABLE IF NOT EXISTS casos (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  persona_id      UUID REFERENCES personas(id),
  organizacion_id UUID REFERENCES organizaciones(id),
  estado          TEXT CHECK (estado IN (
                    'nuevo','en_diagnostico','perfil_completo',
                    'derivado_vacante','derivado_curso',
                    'en_seguimiento','insertado','cerrado'
                  )) DEFAULT 'nuevo',
  objetivo        TEXT CHECK (objetivo IN ('empleo','formacion')),
  prioridad       TEXT CHECK (prioridad IN ('normal','urgente')) DEFAULT 'normal',
  nota_tecnico    TEXT,
  checkboxes_tecnico JSONB DEFAULT '{}',
  created_at      TIMESTAMPTZ DEFAULT NOW(),
  updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_casos_org_estado ON casos(organizacion_id, estado);
CREATE INDEX IF NOT EXISTS idx_casos_persona ON casos(persona_id);

-- ============================================================
-- 5. DERIVACIONES
-- ============================================================

CREATE TABLE IF NOT EXISTS derivaciones (
  id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  caso_id          UUID REFERENCES casos(id) ON DELETE CASCADE,
  tipo             TEXT CHECK (tipo IN ('vacante','curso')),
  destino_id       UUID,
  estado           TEXT CHECK (estado IN (
                     'derivado','entrevistado','no_se_presento','rechazado','aceptado'
                   )) DEFAULT 'derivado',
  motivo           TEXT,
  fecha_derivacion TIMESTAMPTZ DEFAULT NOW(),
  fecha_resultado  TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_derivaciones_caso ON derivaciones(caso_id);

-- ============================================================
-- 6. EVENTOS_CASO (auditoría)
-- ============================================================

CREATE TABLE IF NOT EXISTS eventos_caso (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  entidad     TEXT CHECK (entidad IN ('caso','perfil','vacante','derivacion')),
  entidad_id  UUID NOT NULL,
  tipo        TEXT NOT NULL,
  usuario_id  UUID,
  payload     JSONB DEFAULT '{}',
  timestamp   TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_eventos_entidad ON eventos_caso(entidad_id);

-- ============================================================
-- 7. VACANTES_OE (pool propio de la OE)
-- ============================================================

CREATE TABLE IF NOT EXISTS vacantes_oe (
  id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  organizacion_id  UUID NOT NULL,
  titulo           TEXT NOT NULL,
  empresa          TEXT,
  descripcion      TEXT,
  skills_requeridas JSONB DEFAULT '[]',
  ubicacion        TEXT,
  estado           TEXT CHECK (estado IN ('activa','en_proceso','cubierta','cerrada')) DEFAULT 'activa',
  created_at       TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_vacantes_oe_org ON vacantes_oe(organizacion_id, estado);

-- ============================================================
-- RLS — Todas las tablas
-- ============================================================

ALTER TABLE personas ENABLE ROW LEVEL SECURITY;
ALTER TABLE perfiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE perfil_skills ENABLE ROW LEVEL SECURITY;
ALTER TABLE casos ENABLE ROW LEVEL SECURITY;
ALTER TABLE derivaciones ENABLE ROW LEVEL SECURITY;
ALTER TABLE eventos_caso ENABLE ROW LEVEL SECURITY;
ALTER TABLE vacantes_oe ENABLE ROW LEVEL SECURITY;

-- Lectura: autenticados pueden leer
CREATE POLICY "personas_read" ON personas FOR SELECT USING (true);
CREATE POLICY "perfiles_read" ON perfiles FOR SELECT USING (true);
CREATE POLICY "perfil_skills_read" ON perfil_skills FOR SELECT USING (true);
CREATE POLICY "casos_read" ON casos FOR SELECT USING (true);
CREATE POLICY "derivaciones_read" ON derivaciones FOR SELECT USING (true);
CREATE POLICY "eventos_caso_read" ON eventos_caso FOR SELECT USING (true);
CREATE POLICY "vacantes_oe_read" ON vacantes_oe FOR SELECT USING (true);

-- Escritura: solo service_role (las APIs usan service key)
CREATE POLICY "personas_write" ON personas FOR ALL
  USING (auth.role() = 'service_role') WITH CHECK (auth.role() = 'service_role');
CREATE POLICY "perfiles_write" ON perfiles FOR ALL
  USING (auth.role() = 'service_role') WITH CHECK (auth.role() = 'service_role');
CREATE POLICY "perfil_skills_write" ON perfil_skills FOR ALL
  USING (auth.role() = 'service_role') WITH CHECK (auth.role() = 'service_role');
CREATE POLICY "casos_write" ON casos FOR ALL
  USING (auth.role() = 'service_role') WITH CHECK (auth.role() = 'service_role');
CREATE POLICY "derivaciones_write" ON derivaciones FOR ALL
  USING (auth.role() = 'service_role') WITH CHECK (auth.role() = 'service_role');
CREATE POLICY "eventos_caso_write" ON eventos_caso FOR ALL
  USING (auth.role() = 'service_role') WITH CHECK (auth.role() = 'service_role');
CREATE POLICY "vacantes_oe_write" ON vacantes_oe FOR ALL
  USING (auth.role() = 'service_role') WITH CHECK (auth.role() = 'service_role');

-- Triggers updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN NEW.updated_at = NOW(); RETURN NEW; END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS casos_updated_at ON casos;
CREATE TRIGGER casos_updated_at BEFORE UPDATE ON casos
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS perfiles_updated_at ON perfiles;
CREATE TRIGGER perfiles_updated_at BEFORE UPDATE ON perfiles
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
