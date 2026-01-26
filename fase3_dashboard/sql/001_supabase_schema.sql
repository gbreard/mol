-- MOL Dashboard - Schema de Datos
-- Ejecutar ANTES de 003_sistema_admin.sql

-- TABLA: ofertas (principal, desnormalizada)

CREATE TABLE IF NOT EXISTS ofertas (
    id_oferta TEXT PRIMARY KEY,
    titulo TEXT,
    empresa TEXT,
    descripcion TEXT,
    localizacion TEXT,
    modalidad_trabajo TEXT,
    url_oferta TEXT,
    portal TEXT,
    fecha_publicacion_iso DATE,
    scrapeado_en TIMESTAMPTZ,
    provincia_normalizada TEXT,
    localidad_normalizada TEXT,
    estado_oferta TEXT,
    fecha_ultimo_visto DATE,
    dias_publicada INTEGER,
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
    esco_occupation_uri TEXT,
    esco_occupation_label TEXT,
    isco_code TEXT,
    isco_label TEXT,
    occupation_match_score REAL,
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
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ofertas_provincia ON ofertas(provincia);
CREATE INDEX IF NOT EXISTS idx_ofertas_isco ON ofertas(isco_code);
CREATE INDEX IF NOT EXISTS idx_ofertas_area ON ofertas(area_funcional);
CREATE INDEX IF NOT EXISTS idx_ofertas_seniority ON ofertas(nivel_seniority);
CREATE INDEX IF NOT EXISTS idx_ofertas_modalidad ON ofertas(modalidad);
CREATE INDEX IF NOT EXISTS idx_ofertas_fecha ON ofertas(fecha_publicacion_iso);
CREATE INDEX IF NOT EXISTS idx_ofertas_portal ON ofertas(portal);
CREATE INDEX IF NOT EXISTS idx_ofertas_sector ON ofertas(sector_empresa);

-- TABLA: ofertas_skills

CREATE TABLE IF NOT EXISTS ofertas_skills (
    id SERIAL PRIMARY KEY,
    id_oferta TEXT REFERENCES ofertas(id_oferta) ON DELETE CASCADE,
    skill_mencionado TEXT,
    skill_tipo_fuente TEXT,
    esco_skill_uri TEXT,
    esco_skill_label TEXT,
    match_score REAL,
    skill_type TEXT,
    l1 TEXT,
    l1_nombre TEXT,
    l2 TEXT,
    l2_nombre TEXT,
    es_digital BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_skills_oferta ON ofertas_skills(id_oferta);
CREATE INDEX IF NOT EXISTS idx_skills_l1 ON ofertas_skills(l1);
CREATE INDEX IF NOT EXISTS idx_skills_l2 ON ofertas_skills(l2);
CREATE INDEX IF NOT EXISTS idx_skills_digital ON ofertas_skills(es_digital);
CREATE INDEX IF NOT EXISTS idx_skills_esco_uri ON ofertas_skills(esco_skill_uri);

-- TABLA: esco_occupations

CREATE TABLE IF NOT EXISTS esco_occupations (
    uri TEXT PRIMARY KEY,
    label TEXT NOT NULL,
    isco_code TEXT,
    isco_label TEXT,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_esco_occ_isco ON esco_occupations(isco_code);

-- TABLA: esco_skills

CREATE TABLE IF NOT EXISTS esco_skills (
    uri TEXT PRIMARY KEY,
    label TEXT NOT NULL,
    skill_type TEXT,
    l1 TEXT,
    l1_nombre TEXT,
    l2 TEXT,
    l2_nombre TEXT,
    es_digital BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_esco_skills_l1 ON esco_skills(l1);
CREATE INDEX IF NOT EXISTS idx_esco_skills_type ON esco_skills(skill_type);

-- VISTAS PARA EL DASHBOARD (drop primero por si cambiaron columnas)

DROP VIEW IF EXISTS vw_dashboard_kpis;
DROP VIEW IF EXISTS vw_distribucion_ocupaciones;
DROP VIEW IF EXISTS vw_distribucion_geografica;
DROP VIEW IF EXISTS vw_distribucion_area;
DROP VIEW IF EXISTS vw_distribucion_seniority;
DROP VIEW IF EXISTS vw_top_skills;
DROP VIEW IF EXISTS vw_evolucion_mensual;

CREATE OR REPLACE VIEW vw_dashboard_kpis AS
SELECT
    COUNT(*) as total_ofertas,
    COUNT(DISTINCT isco_code) as ocupaciones_distintas,
    COUNT(DISTINCT provincia) as provincias_con_ofertas,
    COUNT(DISTINCT empresa) as empresas_distintas,
    ROUND(AVG(skills_demandados_total)::numeric, 1) as skills_promedio,
    COUNT(*) FILTER (WHERE modalidad = 'remoto') as ofertas_remotas,
    COUNT(*) FILTER (WHERE modalidad = 'hibrido') as ofertas_hibridas,
    COUNT(*) FILTER (WHERE modalidad = 'presencial') as ofertas_presenciales
FROM ofertas;

CREATE OR REPLACE VIEW vw_distribucion_ocupaciones AS
SELECT
    isco_code,
    isco_label,
    COUNT(*) as cantidad,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 1) as porcentaje
FROM ofertas
WHERE isco_code IS NOT NULL
GROUP BY isco_code, isco_label
ORDER BY cantidad DESC
LIMIT 20;

CREATE OR REPLACE VIEW vw_distribucion_geografica AS
SELECT
    provincia,
    COUNT(*) as cantidad,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 1) as porcentaje
FROM ofertas
WHERE provincia IS NOT NULL
GROUP BY provincia
ORDER BY cantidad DESC;

CREATE OR REPLACE VIEW vw_distribucion_area AS
SELECT
    area_funcional,
    COUNT(*) as cantidad,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 1) as porcentaje
FROM ofertas
WHERE area_funcional IS NOT NULL
GROUP BY area_funcional
ORDER BY cantidad DESC;

CREATE OR REPLACE VIEW vw_distribucion_seniority AS
SELECT
    nivel_seniority,
    COUNT(*) as cantidad,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 1) as porcentaje
FROM ofertas
WHERE nivel_seniority IS NOT NULL
GROUP BY nivel_seniority
ORDER BY cantidad DESC;

CREATE OR REPLACE VIEW vw_top_skills AS
SELECT
    esco_skill_label as skill,
    l1,
    l1_nombre,
    es_digital,
    COUNT(*) as menciones,
    COUNT(DISTINCT id_oferta) as ofertas_con_skill
FROM ofertas_skills
WHERE esco_skill_label IS NOT NULL
GROUP BY esco_skill_label, l1, l1_nombre, es_digital
ORDER BY menciones DESC
LIMIT 50;

CREATE OR REPLACE VIEW vw_evolucion_mensual AS
SELECT
    DATE_TRUNC('month', fecha_publicacion_iso::DATE) as mes,
    COUNT(*) as ofertas,
    COUNT(DISTINCT isco_code) as ocupaciones,
    COUNT(DISTINCT empresa) as empresas
FROM ofertas
WHERE fecha_publicacion_iso IS NOT NULL
GROUP BY DATE_TRUNC('month', fecha_publicacion_iso::DATE)
ORDER BY mes DESC
LIMIT 12;

-- ROW LEVEL SECURITY

ALTER TABLE ofertas ENABLE ROW LEVEL SECURITY;
ALTER TABLE ofertas_skills ENABLE ROW LEVEL SECURITY;
ALTER TABLE esco_occupations ENABLE ROW LEVEL SECURITY;
ALTER TABLE esco_skills ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Lectura publica ofertas" ON ofertas FOR SELECT USING (true);
CREATE POLICY "Lectura publica skills" ON ofertas_skills FOR SELECT USING (true);
CREATE POLICY "Lectura publica ocupaciones" ON esco_occupations FOR SELECT USING (true);
CREATE POLICY "Lectura publica esco_skills" ON esco_skills FOR SELECT USING (true);

CREATE POLICY "Escritura ofertas" ON ofertas FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Escritura skills" ON ofertas_skills FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Escritura ocupaciones" ON esco_occupations FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Escritura esco_skills" ON esco_skills FOR ALL USING (true) WITH CHECK (true);

-- TRIGGER: updated_at automatico

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

-- GRANTS

GRANT SELECT ON ofertas TO anon;
GRANT SELECT ON ofertas_skills TO anon;
GRANT SELECT ON esco_occupations TO anon;
GRANT SELECT ON esco_skills TO anon;
GRANT SELECT ON vw_dashboard_kpis TO anon;
GRANT SELECT ON vw_distribucion_ocupaciones TO anon;
GRANT SELECT ON vw_distribucion_geografica TO anon;
GRANT SELECT ON vw_distribucion_area TO anon;
GRANT SELECT ON vw_distribucion_seniority TO anon;
GRANT SELECT ON vw_top_skills TO anon;
GRANT SELECT ON vw_evolucion_mensual TO anon;

GRANT SELECT ON ofertas TO authenticated;
GRANT SELECT ON ofertas_skills TO authenticated;
GRANT SELECT ON esco_occupations TO authenticated;
GRANT SELECT ON esco_skills TO authenticated;
GRANT SELECT ON vw_dashboard_kpis TO authenticated;
GRANT SELECT ON vw_distribucion_ocupaciones TO authenticated;
GRANT SELECT ON vw_distribucion_geografica TO authenticated;
GRANT SELECT ON vw_distribucion_area TO authenticated;
GRANT SELECT ON vw_distribucion_seniority TO authenticated;
GRANT SELECT ON vw_top_skills TO authenticated;
GRANT SELECT ON vw_evolucion_mensual TO authenticated;

GRANT ALL ON ofertas TO service_role;
GRANT ALL ON ofertas_skills TO service_role;
GRANT ALL ON esco_occupations TO service_role;
GRANT ALL ON esco_skills TO service_role;
GRANT USAGE, SELECT ON SEQUENCE ofertas_skills_id_seq TO service_role;
