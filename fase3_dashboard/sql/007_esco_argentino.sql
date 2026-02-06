-- ============================================================
-- TABLA: esco_argentino
-- Propósito: Taxonomía ESCO adaptada al mercado laboral argentino
-- Este es el PRODUCTO FINAL que otros módulos consumirán
-- ============================================================

-- Eliminar tabla anterior si existe (migraremos datos después)
-- DROP TABLE IF EXISTS esco_argentino;

CREATE TABLE IF NOT EXISTS esco_argentino (
  -- Identificadores
  esco_occupation_uri TEXT PRIMARY KEY,
  esco_occupation_label TEXT NOT NULL,
  isco_code TEXT,

  -- Skills consolidadas (ESCO común + aprobadas por humano)
  -- Cada skill tiene: label, uri, source (esco_common|argentina_approved), L1, L2, freq_cuando_aprobada
  skills_consolidadas JSONB NOT NULL DEFAULT '[]',

  -- Métricas del perfil
  total_skills INT DEFAULT 0,
  skills_from_esco INT DEFAULT 0,        -- Cuántas vienen de ESCO en común
  skills_from_argentina INT DEFAULT 0,    -- Cuántas aprobó el humano

  -- Métricas de cobertura (snapshot al momento de consolidar)
  cobertura_esco_essential DECIMAL(5,2) DEFAULT 0,  -- % de skills ESCO esenciales cubiertas
  cobertura_esco_total DECIMAL(5,2) DEFAULT 0,      -- % de skills ESCO totales cubiertas
  ofertas_count_snapshot INT DEFAULT 0,              -- Ofertas al momento de consolidar

  -- Metadata de consolidación
  version INT DEFAULT 1,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  updated_by TEXT,  -- Email del usuario que consolidó

  -- Notas del analista
  notas TEXT
);

-- Índices
CREATE INDEX IF NOT EXISTS idx_esco_argentino_isco ON esco_argentino(isco_code);
CREATE INDEX IF NOT EXISTS idx_esco_argentino_updated ON esco_argentino(updated_at DESC);

-- Comentarios
COMMENT ON TABLE esco_argentino IS 'Taxonomía ESCO adaptada al mercado laboral argentino. Producto final para otros módulos.';
COMMENT ON COLUMN esco_argentino.skills_consolidadas IS 'Array JSON de skills. Cada una: {label, uri, source, L1, L2, percentage_when_approved}';
COMMENT ON COLUMN esco_argentino.skills_from_esco IS 'Skills que están en ESCO Y se detectaron en ofertas argentinas';
COMMENT ON COLUMN esco_argentino.skills_from_argentina IS 'Skills emergentes de Argentina aprobadas por humano';

-- ============================================================
-- VISTA: v_esco_argentino_stats
-- Estadísticas generales del ESCO Argentino
-- ============================================================

CREATE OR REPLACE VIEW v_esco_argentino_stats AS
SELECT
  COUNT(*) AS ocupaciones_consolidadas,
  SUM(total_skills) AS total_skills,
  SUM(skills_from_esco) AS total_from_esco,
  SUM(skills_from_argentina) AS total_from_argentina,
  AVG(cobertura_esco_essential) AS avg_cobertura_essential,
  AVG(cobertura_esco_total) AS avg_cobertura_total,
  SUM(ofertas_count_snapshot) AS ofertas_procesadas,
  MAX(updated_at) AS ultima_actualizacion
FROM esco_argentino;

-- ============================================================
-- MIGRACIÓN: consolidated_profiles → esco_argentino
-- (solo si hay datos en la tabla anterior)
-- ============================================================

DO $$
BEGIN
  -- Verificar si existe la tabla consolidated_profiles con datos
  IF EXISTS (
    SELECT 1 FROM information_schema.tables
    WHERE table_name = 'consolidated_profiles'
  ) THEN
    -- Migrar datos existentes
    INSERT INTO esco_argentino (
      esco_occupation_uri,
      esco_occupation_label,
      skills_consolidadas,
      total_skills,
      skills_from_argentina,
      updated_at,
      version
    )
    SELECT
      'http://data.europa.eu/esco/occupation/' || esco_uuid,
      esco_label,
      consolidated_skills,
      COALESCE((stats->>'total_consolidated')::int, 0),
      COALESCE((stats->>'from_mol_approved')::int, 0),
      last_updated::timestamptz,
      1
    FROM consolidated_profiles
    ON CONFLICT (esco_occupation_uri) DO UPDATE SET
      skills_consolidadas = EXCLUDED.skills_consolidadas,
      total_skills = EXCLUDED.total_skills,
      skills_from_argentina = EXCLUDED.skills_from_argentina,
      updated_at = EXCLUDED.updated_at;

    RAISE NOTICE 'Migrados % registros de consolidated_profiles a esco_argentino',
      (SELECT COUNT(*) FROM consolidated_profiles);
  END IF;
END $$;

-- ============================================================
-- RLS (Row Level Security) - Por si hay multi-tenant
-- ============================================================

-- Habilitar RLS
ALTER TABLE esco_argentino ENABLE ROW LEVEL SECURITY;

-- Política: todos pueden leer (es un catálogo público)
CREATE POLICY "esco_argentino_read_all" ON esco_argentino
  FOR SELECT USING (true);

-- Política: solo usuarios autenticados pueden modificar
CREATE POLICY "esco_argentino_write_authenticated" ON esco_argentino
  FOR ALL USING (auth.role() = 'authenticated');
