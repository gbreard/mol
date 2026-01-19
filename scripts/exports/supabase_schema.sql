-- ============================================================
-- Schema Supabase para MOL - Monitor de Ofertas Laborales
-- ============================================================
-- Ejecutar en Supabase Dashboard > SQL Editor
-- ============================================================

-- Tabla principal: ofertas validadas (desnormalizada)
CREATE TABLE IF NOT EXISTS ofertas (
    -- PK
    id_oferta TEXT PRIMARY KEY,

    -- Scraping (15 campos)
    titulo TEXT,
    empresa TEXT,
    descripcion TEXT,
    localizacion TEXT,
    modalidad_trabajo TEXT,
    url_oferta TEXT,
    portal TEXT,
    fecha_publicacion_iso TEXT,
    scrapeado_en TIMESTAMPTZ,
    provincia_normalizada TEXT,
    localidad_normalizada TEXT,
    estado_oferta TEXT,
    fecha_ultimo_visto TIMESTAMPTZ,
    dias_publicada INTEGER,

    -- NLP (26 campos con datos)
    titulo_limpio TEXT,
    tareas_explicitas TEXT,
    mision_rol TEXT,
    area_funcional TEXT,
    nivel_seniority TEXT,
    sector_empresa TEXT,
    tipo_oferta TEXT,
    tipo_contrato TEXT,
    provincia TEXT,
    localidad TEXT,
    modalidad TEXT,
    jornada_laboral TEXT,
    nivel_educativo TEXT,
    titulo_requerido TEXT,
    experiencia_min_anios INTEGER,
    tiene_gente_cargo BOOLEAN,
    requiere_movilidad_propia BOOLEAN,
    skills_tecnicas_list JSONB,
    soft_skills_list JSONB,
    tecnologias_list JSONB,
    herramientas_list JSONB,
    nlp_extraction_timestamp TIMESTAMPTZ,
    nlp_version TEXT,

    -- Matching (17 campos)
    esco_occupation_uri TEXT,
    esco_occupation_label TEXT,
    isco_code TEXT,
    isco_label TEXT,
    occupation_match_score NUMERIC,
    occupation_match_method TEXT,
    skills_oferta_json JSONB,
    skills_matched_essential JSONB,
    skills_demandados_total INTEGER,
    skills_matcheados_esco INTEGER,
    matching_timestamp TIMESTAMPTZ,
    matching_version TEXT,
    run_id TEXT,
    estado_validacion TEXT,
    validado_timestamp TIMESTAMPTZ,
    validado_por TEXT,

    -- Metadata Supabase
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Skills por oferta (relación 1:N)
CREATE TABLE IF NOT EXISTS ofertas_skills (
    id SERIAL PRIMARY KEY,
    id_oferta TEXT REFERENCES ofertas(id_oferta) ON DELETE CASCADE,
    skill_mencionado TEXT,
    skill_tipo_fuente TEXT,
    esco_skill_uri TEXT,
    esco_skill_label TEXT,
    match_score NUMERIC,
    skill_type TEXT,
    L1 TEXT,
    L1_nombre TEXT,
    L2 TEXT,
    L2_nombre TEXT,
    es_digital BOOLEAN,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Catálogo ESCO ocupaciones (subset usado)
CREATE TABLE IF NOT EXISTS esco_occupations (
    uri TEXT PRIMARY KEY,
    label TEXT,
    isco_code TEXT,
    isco_label TEXT,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Catálogo ESCO skills (subset usado)
CREATE TABLE IF NOT EXISTS esco_skills (
    uri TEXT PRIMARY KEY,
    label TEXT,
    skill_type TEXT,
    L1 TEXT,
    L1_nombre TEXT,
    L2 TEXT,
    L2_nombre TEXT,
    es_digital BOOLEAN,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- Índices para queries comunes del dashboard
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_ofertas_isco ON ofertas(isco_code);
CREATE INDEX IF NOT EXISTS idx_ofertas_provincia ON ofertas(provincia);
CREATE INDEX IF NOT EXISTS idx_ofertas_area ON ofertas(area_funcional);
CREATE INDEX IF NOT EXISTS idx_ofertas_seniority ON ofertas(nivel_seniority);
CREATE INDEX IF NOT EXISTS idx_ofertas_modalidad ON ofertas(modalidad);
CREATE INDEX IF NOT EXISTS idx_ofertas_validado ON ofertas(validado_timestamp);
CREATE INDEX IF NOT EXISTS idx_skills_oferta ON ofertas_skills(id_oferta);
CREATE INDEX IF NOT EXISTS idx_skills_esco ON ofertas_skills(esco_skill_uri);

-- ============================================================
-- Row Level Security (RLS) - Lectura pública
-- ============================================================

ALTER TABLE ofertas ENABLE ROW LEVEL SECURITY;
ALTER TABLE ofertas_skills ENABLE ROW LEVEL SECURITY;
ALTER TABLE esco_occupations ENABLE ROW LEVEL SECURITY;
ALTER TABLE esco_skills ENABLE ROW LEVEL SECURITY;

-- Políticas de lectura pública (para dashboard)
DROP POLICY IF EXISTS "Public read ofertas" ON ofertas;
CREATE POLICY "Public read ofertas" ON ofertas FOR SELECT USING (true);

DROP POLICY IF EXISTS "Public read ofertas_skills" ON ofertas_skills;
CREATE POLICY "Public read ofertas_skills" ON ofertas_skills FOR SELECT USING (true);

DROP POLICY IF EXISTS "Public read esco_occupations" ON esco_occupations;
CREATE POLICY "Public read esco_occupations" ON esco_occupations FOR SELECT USING (true);

DROP POLICY IF EXISTS "Public read esco_skills" ON esco_skills;
CREATE POLICY "Public read esco_skills" ON esco_skills FOR SELECT USING (true);

-- ============================================================
-- Función para actualizar updated_at automáticamente
-- ============================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS update_ofertas_updated_at ON ofertas;
CREATE TRIGGER update_ofertas_updated_at
    BEFORE UPDATE ON ofertas
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================
-- Vista para métricas del dashboard
-- ============================================================

CREATE OR REPLACE VIEW vw_dashboard_metrics AS
SELECT
    COUNT(*) as total_ofertas,
    COUNT(DISTINCT isco_code) as ocupaciones_unicas,
    COUNT(DISTINCT provincia) as provincias,
    COUNT(DISTINCT area_funcional) as areas_funcionales,
    MIN(validado_timestamp) as primera_validacion,
    MAX(validado_timestamp) as ultima_validacion
FROM ofertas;

-- Vista para distribución por ISCO
CREATE OR REPLACE VIEW vw_distribucion_isco AS
SELECT
    isco_code,
    isco_label,
    COUNT(*) as total,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as porcentaje
FROM ofertas
GROUP BY isco_code, isco_label
ORDER BY total DESC;

-- Vista para distribución geográfica
CREATE OR REPLACE VIEW vw_distribucion_geografica AS
SELECT
    provincia,
    COUNT(*) as total,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as porcentaje
FROM ofertas
WHERE provincia IS NOT NULL
GROUP BY provincia
ORDER BY total DESC;

-- ============================================================
-- Comentarios
-- ============================================================

COMMENT ON TABLE ofertas IS 'Ofertas laborales validadas del pipeline MOL';
COMMENT ON TABLE ofertas_skills IS 'Skills extraídas por oferta con clasificación ESCO';
COMMENT ON TABLE esco_occupations IS 'Catálogo ESCO ocupaciones (subset usado)';
COMMENT ON TABLE esco_skills IS 'Catálogo ESCO skills (subset usado)';
