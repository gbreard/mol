-- Migration 030: Catálogo MOL — Taxonomía propia (skills + ocupaciones)
-- Bloque G del roadmap
--
-- El mercado laboral argentino genera skills y ocupaciones que ESCO no tiene.
-- El Catálogo MOL les da estructura: definición, categoría, relaciones, versionado.

-- ============================================================
-- G1: Tabla catalogo_mol_skills
-- ============================================================

CREATE TABLE IF NOT EXISTS catalogo_mol_skills (
  id TEXT PRIMARY KEY,                          -- mol-skill-docker-config
  label TEXT NOT NULL,                          -- "Configurar Docker"
  label_normalized TEXT NOT NULL,               -- "configurar docker"
  definicion TEXT,                              -- Descripción completa
  tipo TEXT NOT NULL DEFAULT 'skill'            -- skill | knowledge | transversal
    CHECK (tipo IN ('skill', 'knowledge', 'transversal')),
  categoria_l1 TEXT,                            -- Categoría nivel 1 (alineada ESCO si existe)
  categoria_l2 TEXT,                            -- Categoría nivel 2
  source TEXT NOT NULL DEFAULT 'mol_catalogo'   -- mol_catalogo | esco | emergente
    CHECK (source IN ('mol_catalogo', 'esco', 'emergente')),
  esco_parent_uri TEXT,                         -- Skill ESCO más cercana (si existe)
  esco_parent_label TEXT,                       -- Label de la skill ESCO parent
  relaciones JSONB DEFAULT '[]'::jsonb,         -- [{skill, tipo: related|prerequisite|broader|narrower}]
  frecuencia_mercado NUMERIC(5,2) DEFAULT 0,   -- % de ofertas que la mencionan
  primera_deteccion DATE,                       -- Cuándo se detectó por primera vez
  estado TEXT NOT NULL DEFAULT 'detectada'      -- detectada | en_revision | catalogada | descartada
    CHECK (estado IN ('detectada', 'en_revision', 'catalogada', 'descartada')),
  aprobada_por TEXT,                            -- Email del admin que aprobó
  aprobada_at TIMESTAMPTZ,                      -- Cuándo se aprobó
  version_catalogo TEXT,                        -- En qué versión del catálogo entró
  notas TEXT,                                   -- Notas del revisor
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Índices
CREATE INDEX IF NOT EXISTS idx_catalogo_skills_estado ON catalogo_mol_skills(estado);
CREATE INDEX IF NOT EXISTS idx_catalogo_skills_tipo ON catalogo_mol_skills(tipo);
CREATE INDEX IF NOT EXISTS idx_catalogo_skills_source ON catalogo_mol_skills(source);
CREATE INDEX IF NOT EXISTS idx_catalogo_skills_label_norm ON catalogo_mol_skills(label_normalized);
CREATE INDEX IF NOT EXISTS idx_catalogo_skills_frecuencia ON catalogo_mol_skills(frecuencia_mercado DESC);

-- ============================================================
-- G2: Tabla catalogo_mol_ocupaciones
-- ============================================================

CREATE TABLE IF NOT EXISTS catalogo_mol_ocupaciones (
  id TEXT PRIMARY KEY,                          -- mol-occ-community-manager
  label TEXT NOT NULL,                          -- "Community Manager"
  label_normalized TEXT NOT NULL,               -- "community manager"
  definicion TEXT,                              -- Descripción completa
  isco_parent TEXT,                             -- Código ISCO 4 dígitos más cercano
  isco_parent_label TEXT,                       -- Label del ISCO parent
  esco_parent_uri TEXT,                         -- Ocupación ESCO más cercana
  esco_parent_label TEXT,                       -- Label ESCO parent
  source TEXT NOT NULL DEFAULT 'mol_catalogo'
    CHECK (source IN ('mol_catalogo', 'esco', 'emergente')),
  skills_esenciales JSONB DEFAULT '[]'::jsonb,  -- ["marketing digital", "redes sociales"]
  skills_opcionales JSONB DEFAULT '[]'::jsonb,  -- ["diseño gráfico", "analítica web"]
  sector TEXT,                                  -- Sector predominante
  frecuencia_mercado NUMERIC(5,2) DEFAULT 0,   -- % de ofertas con este título
  primera_deteccion DATE,
  estado TEXT NOT NULL DEFAULT 'detectada'
    CHECK (estado IN ('detectada', 'en_revision', 'catalogada', 'descartada')),
  aprobada_por TEXT,
  aprobada_at TIMESTAMPTZ,
  version_catalogo TEXT,
  notas TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Índices
CREATE INDEX IF NOT EXISTS idx_catalogo_ocup_estado ON catalogo_mol_ocupaciones(estado);
CREATE INDEX IF NOT EXISTS idx_catalogo_ocup_isco ON catalogo_mol_ocupaciones(isco_parent);
CREATE INDEX IF NOT EXISTS idx_catalogo_ocup_label_norm ON catalogo_mol_ocupaciones(label_normalized);
CREATE INDEX IF NOT EXISTS idx_catalogo_ocup_frecuencia ON catalogo_mol_ocupaciones(frecuencia_mercado DESC);

-- ============================================================
-- G1/G2: Tabla de versiones del catálogo
-- ============================================================

CREATE TABLE IF NOT EXISTS catalogo_mol_versiones (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  version TEXT NOT NULL UNIQUE,                 -- "v1.0", "v1.1"
  fecha_corte TIMESTAMPTZ DEFAULT NOW(),
  total_skills INTEGER DEFAULT 0,
  total_ocupaciones INTEGER DEFAULT 0,
  skills_nuevas INTEGER DEFAULT 0,              -- Agregadas en esta versión
  ocupaciones_nuevas INTEGER DEFAULT 0,
  skills_descartadas INTEGER DEFAULT 0,
  nota TEXT,                                    -- Descripción del corte
  creado_por TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- G3: RPC detección de no clasificados
-- ============================================================

-- Detecta skills que aparecen en ofertas pero no están en ESCO ni en el catálogo MOL
CREATE OR REPLACE FUNCTION get_unclassified_items(p_min_frecuencia INTEGER DEFAULT 3)
RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
SET statement_timeout = '15s'
AS $$
DECLARE
  v_result JSONB;
  v_total_ofertas INTEGER;
  v_unclassified_skills JSONB;
  v_unclassified_titles JSONB;
BEGIN
  -- Total ofertas para calcular frecuencia
  SELECT COUNT(*) INTO v_total_ofertas FROM ofertas_dashboard;
  IF v_total_ofertas = 0 THEN v_total_ofertas := 1; END IF;

  -- Skills no clasificadas: aparecen en ofertas_skills pero no están en el catálogo
  -- (preferred_label que no matchean con catalogo_mol_skills)
  WITH skill_counts AS (
    SELECT
      os.preferred_label AS label,
      COUNT(DISTINCT os.id_oferta) AS frecuencia,
      ROUND(COUNT(DISTINCT os.id_oferta)::numeric / v_total_ofertas * 100, 2) AS pct
    FROM ofertas_skills os
    WHERE os.preferred_label IS NOT NULL
      AND os.preferred_label != ''
    GROUP BY os.preferred_label
    HAVING COUNT(DISTINCT os.id_oferta) >= p_min_frecuencia
  ),
  already_cataloged AS (
    SELECT label_normalized FROM catalogo_mol_skills
    WHERE estado != 'descartada'
  )
  SELECT COALESCE(jsonb_agg(
    jsonb_build_object(
      'label', sc.label,
      'frecuencia', sc.frecuencia,
      'pct', sc.pct
    ) ORDER BY sc.frecuencia DESC
  ), '[]'::jsonb)
  INTO v_unclassified_skills
  FROM skill_counts sc
  WHERE LOWER(sc.label) NOT IN (SELECT label_normalized FROM already_cataloged)
  LIMIT 100;

  -- Títulos no clasificados: títulos frecuentes sin ocupación ESCO clara
  -- (occupation_match_score bajo o sin matching)
  WITH title_counts AS (
    SELECT
      od.titulo_limpio AS label,
      COUNT(*) AS frecuencia,
      ROUND(COUNT(*)::numeric / v_total_ofertas * 100, 2) AS pct,
      AVG(od.occupation_match_score) AS avg_score,
      MODE() WITHIN GROUP (ORDER BY od.isco_code) AS isco_mode
    FROM ofertas_dashboard od
    WHERE od.titulo_limpio IS NOT NULL
      AND od.titulo_limpio != ''
    GROUP BY od.titulo_limpio
    HAVING COUNT(*) >= p_min_frecuencia
  ),
  already_cataloged_occ AS (
    SELECT label_normalized FROM catalogo_mol_ocupaciones
    WHERE estado != 'descartada'
  )
  SELECT COALESCE(jsonb_agg(
    jsonb_build_object(
      'label', tc.label,
      'frecuencia', tc.frecuencia,
      'pct', tc.pct,
      'avg_score', ROUND(tc.avg_score::numeric, 2),
      'isco_mode', tc.isco_mode
    ) ORDER BY tc.frecuencia DESC
  ), '[]'::jsonb)
  INTO v_unclassified_titles
  FROM title_counts tc
  WHERE (tc.avg_score IS NULL OR tc.avg_score < 0.6)
    AND LOWER(tc.label) NOT IN (SELECT label_normalized FROM already_cataloged_occ)
  LIMIT 100;

  v_result := jsonb_build_object(
    'total_ofertas', v_total_ofertas,
    'unclassified_skills', v_unclassified_skills,
    'unclassified_skills_count', jsonb_array_length(v_unclassified_skills),
    'unclassified_titles', v_unclassified_titles,
    'unclassified_titles_count', jsonb_array_length(v_unclassified_titles),
    'min_frecuencia', p_min_frecuencia
  );

  RETURN v_result;
END;
$$;

-- ============================================================
-- G3: RPC stats del catálogo
-- ============================================================

CREATE OR REPLACE FUNCTION get_catalogo_stats()
RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
SET statement_timeout = '10s'
AS $$
DECLARE
  v_result JSONB;
BEGIN
  SELECT jsonb_build_object(
    'skills', jsonb_build_object(
      'total', (SELECT COUNT(*) FROM catalogo_mol_skills),
      'catalogadas', (SELECT COUNT(*) FROM catalogo_mol_skills WHERE estado = 'catalogada'),
      'en_revision', (SELECT COUNT(*) FROM catalogo_mol_skills WHERE estado = 'en_revision'),
      'detectadas', (SELECT COUNT(*) FROM catalogo_mol_skills WHERE estado = 'detectada'),
      'descartadas', (SELECT COUNT(*) FROM catalogo_mol_skills WHERE estado = 'descartada'),
      'por_tipo', (
        SELECT COALESCE(jsonb_object_agg(tipo, cnt), '{}'::jsonb)
        FROM (SELECT tipo, COUNT(*) AS cnt FROM catalogo_mol_skills WHERE estado != 'descartada' GROUP BY tipo) t
      )
    ),
    'ocupaciones', jsonb_build_object(
      'total', (SELECT COUNT(*) FROM catalogo_mol_ocupaciones),
      'catalogadas', (SELECT COUNT(*) FROM catalogo_mol_ocupaciones WHERE estado = 'catalogada'),
      'en_revision', (SELECT COUNT(*) FROM catalogo_mol_ocupaciones WHERE estado = 'en_revision'),
      'detectadas', (SELECT COUNT(*) FROM catalogo_mol_ocupaciones WHERE estado = 'detectada'),
      'descartadas', (SELECT COUNT(*) FROM catalogo_mol_ocupaciones WHERE estado = 'descartada')
    ),
    'versiones', (
      SELECT COALESCE(jsonb_agg(
        jsonb_build_object('version', v.version, 'fecha', v.fecha_corte, 'skills', v.total_skills, 'ocupaciones', v.total_ocupaciones)
        ORDER BY v.created_at DESC
      ), '[]'::jsonb)
      FROM catalogo_mol_versiones v
    ),
    'ultima_version', (SELECT version FROM catalogo_mol_versiones ORDER BY created_at DESC LIMIT 1)
  ) INTO v_result;

  RETURN v_result;
END;
$$;

-- ============================================================
-- RLS Policies
-- ============================================================

ALTER TABLE catalogo_mol_skills ENABLE ROW LEVEL SECURITY;
ALTER TABLE catalogo_mol_ocupaciones ENABLE ROW LEVEL SECURITY;
ALTER TABLE catalogo_mol_versiones ENABLE ROW LEVEL SECURITY;

-- Lectura pública (anon puede ver catalogadas)
CREATE POLICY "catalogo_skills_read" ON catalogo_mol_skills
  FOR SELECT USING (true);

CREATE POLICY "catalogo_ocupaciones_read" ON catalogo_mol_ocupaciones
  FOR SELECT USING (true);

CREATE POLICY "catalogo_versiones_read" ON catalogo_mol_versiones
  FOR SELECT USING (true);

-- Escritura solo service_role (admin via API)
CREATE POLICY "catalogo_skills_write" ON catalogo_mol_skills
  FOR ALL USING (auth.role() = 'service_role')
  WITH CHECK (auth.role() = 'service_role');

CREATE POLICY "catalogo_ocupaciones_write" ON catalogo_mol_ocupaciones
  FOR ALL USING (auth.role() = 'service_role')
  WITH CHECK (auth.role() = 'service_role');

CREATE POLICY "catalogo_versiones_write" ON catalogo_mol_versiones
  FOR ALL USING (auth.role() = 'service_role')
  WITH CHECK (auth.role() = 'service_role');

-- ============================================================
-- Trigger updated_at
-- ============================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS catalogo_skills_updated_at ON catalogo_mol_skills;
CREATE TRIGGER catalogo_skills_updated_at
  BEFORE UPDATE ON catalogo_mol_skills
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS catalogo_ocupaciones_updated_at ON catalogo_mol_ocupaciones;
CREATE TRIGGER catalogo_ocupaciones_updated_at
  BEFORE UPDATE ON catalogo_mol_ocupaciones
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
