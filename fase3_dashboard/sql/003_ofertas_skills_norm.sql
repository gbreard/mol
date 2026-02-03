-- ============================================
-- MOL Dashboard - Skills Normalizados
-- Version: 1.0
-- Fecha: 2026-02-03
-- ============================================
-- Este schema normaliza skills de ofertas para
-- queries eficientes (vs JSONB arrays)
-- ============================================

-- 1. TABLA OFERTAS_SKILLS (N:M normalizada)
-- ============================================
CREATE TABLE IF NOT EXISTS ofertas_skills (
    id SERIAL PRIMARY KEY,

    -- Relacion con oferta
    id_oferta TEXT NOT NULL REFERENCES ofertas_dashboard(id_oferta) ON DELETE CASCADE,

    -- Identificacion del skill
    skill_uri TEXT NOT NULL,              -- URI ESCO del skill
    preferred_label TEXT,                  -- Nombre en espanol

    -- Categorizacion ESCO
    L1 TEXT,                              -- Codigo L1 (ej: "S1", "S2")
    L1_nombre TEXT,                       -- Nombre L1
    L2 TEXT,                              -- Codigo L2
    L2_nombre TEXT,                       -- Nombre L2
    es_digital BOOLEAN DEFAULT false,     -- Si es skill digital

    -- Origen y confianza
    origen TEXT CHECK(origen IN ('regla', 'semantico', 'llm', 'merged', 'manual')),
    score DECIMAL(4,3),                   -- Confianza 0.000-1.000
    es_esencial BOOLEAN DEFAULT false,    -- Si es esencial para la ocupacion

    -- Metadata sync
    run_id TEXT,                          -- ID del run de procesamiento
    created_at TIMESTAMPTZ DEFAULT NOW(),

    -- Constraint: un skill por oferta
    UNIQUE(id_oferta, skill_uri)
);

COMMENT ON TABLE ofertas_skills IS 'Skills de ofertas normalizados - permite queries directas por skill';
COMMENT ON COLUMN ofertas_skills.skill_uri IS 'URI ESCO completa del skill';
COMMENT ON COLUMN ofertas_skills.L1 IS 'Categoria nivel 1 ESCO: S=Skills, K=Knowledge, T=Transversal';
COMMENT ON COLUMN ofertas_skills.es_digital IS 'true si el skill pertenece a Digital Skills taxonomy';

-- 2. INDICES
-- ============================================

-- Busqueda por oferta (JOIN con ofertas)
CREATE INDEX IF NOT EXISTS idx_ofertas_skills_oferta
    ON ofertas_skills(id_oferta);

-- Busqueda por skill (queries "ofertas con Python")
CREATE INDEX IF NOT EXISTS idx_ofertas_skills_skill
    ON ofertas_skills(skill_uri);

-- Busqueda por categoria L1 (agregaciones por categoria)
CREATE INDEX IF NOT EXISTS idx_ofertas_skills_l1
    ON ofertas_skills(L1);

-- Busqueda por categoria L2
CREATE INDEX IF NOT EXISTS idx_ofertas_skills_l2
    ON ofertas_skills(L2);

-- Skills digitales
CREATE INDEX IF NOT EXISTS idx_ofertas_skills_digital
    ON ofertas_skills(es_digital) WHERE es_digital = true;

-- Por origen (para metricas de reglas vs semantico)
CREATE INDEX IF NOT EXISTS idx_ofertas_skills_origen
    ON ofertas_skills(origen);

-- Por label (busqueda por nombre)
CREATE INDEX IF NOT EXISTS idx_ofertas_skills_label
    ON ofertas_skills(preferred_label);

-- 3. VISTAS
-- ============================================

-- Vista: Skills mas demandados
CREATE OR REPLACE VIEW v_skills_demanda AS
SELECT
    skill_uri,
    preferred_label,
    L1,
    L1_nombre,
    es_digital,
    COUNT(*) as ofertas_count,
    ROUND(COUNT(*) * 100.0 / NULLIF((SELECT COUNT(DISTINCT id_oferta) FROM ofertas_skills), 0), 2) as porcentaje
FROM ofertas_skills
WHERE preferred_label IS NOT NULL
GROUP BY skill_uri, preferred_label, L1, L1_nombre, es_digital
ORDER BY ofertas_count DESC;

-- Vista: Distribucion por L1
CREATE OR REPLACE VIEW v_skills_por_l1 AS
SELECT
    L1,
    L1_nombre,
    COUNT(DISTINCT skill_uri) as skills_unicos,
    COUNT(*) as menciones_totales,
    COUNT(DISTINCT id_oferta) as ofertas_con_skill
FROM ofertas_skills
WHERE L1 IS NOT NULL
GROUP BY L1, L1_nombre
ORDER BY menciones_totales DESC;

-- Vista: Skills digitales mas demandados
CREATE OR REPLACE VIEW v_skills_digitales_demanda AS
SELECT
    skill_uri,
    preferred_label,
    L2,
    L2_nombre,
    COUNT(*) as ofertas_count
FROM ofertas_skills
WHERE es_digital = true
GROUP BY skill_uri, preferred_label, L2, L2_nombre
ORDER BY ofertas_count DESC
LIMIT 50;

-- Vista: Comparacion origen (regla vs semantico)
CREATE OR REPLACE VIEW v_skills_por_origen AS
SELECT
    origen,
    COUNT(*) as total_skills,
    COUNT(DISTINCT skill_uri) as skills_unicos,
    COUNT(DISTINCT id_oferta) as ofertas_afectadas,
    ROUND(AVG(score)::numeric, 3) as score_promedio
FROM ofertas_skills
GROUP BY origen;

-- Vista: Top skills por ocupacion ISCO
CREATE OR REPLACE VIEW v_skills_por_ocupacion AS
SELECT
    o.isco_code,
    o.isco_label,
    s.skill_uri,
    s.preferred_label as skill,
    COUNT(*) as frecuencia,
    ROUND(COUNT(*) * 100.0 / NULLIF(SUM(COUNT(*)) OVER (PARTITION BY o.isco_code), 0), 1) as porcentaje_en_ocupacion
FROM ofertas_skills s
JOIN ofertas_dashboard o ON s.id_oferta = o.id_oferta
GROUP BY o.isco_code, o.isco_label, s.skill_uri, s.preferred_label
ORDER BY o.isco_code, frecuencia DESC;

-- 4. ROW LEVEL SECURITY
-- ============================================

ALTER TABLE ofertas_skills ENABLE ROW LEVEL SECURITY;

-- Lectura publica (datos agregados del mercado laboral)
CREATE POLICY "Skills visibles para todos" ON ofertas_skills
    FOR SELECT USING (true);

-- Solo service_role puede modificar (sync desde SQLite)
CREATE POLICY "Solo service_role puede modificar skills" ON ofertas_skills
    FOR ALL USING (auth.role() = 'service_role');

-- 5. FUNCION: Buscar ofertas por skill
-- ============================================
CREATE OR REPLACE FUNCTION buscar_ofertas_por_skill(skill_name TEXT)
RETURNS TABLE (
    id_oferta TEXT,
    titulo TEXT,
    empresa TEXT,
    provincia TEXT,
    isco_label TEXT,
    skill_score DECIMAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        o.id_oferta,
        o.titulo,
        o.empresa,
        o.provincia,
        o.isco_label,
        s.score
    FROM ofertas_dashboard o
    JOIN ofertas_skills s ON o.id_oferta = s.id_oferta
    WHERE s.preferred_label ILIKE '%' || skill_name || '%'
       OR s.skill_uri ILIKE '%' || skill_name || '%'
    ORDER BY s.score DESC NULLS LAST;
END;
$$ LANGUAGE plpgsql STABLE;

COMMENT ON FUNCTION buscar_ofertas_por_skill IS 'Busca ofertas que requieren un skill especifico';

-- 6. FUNCION: Skills de una oferta
-- ============================================
CREATE OR REPLACE FUNCTION get_skills_oferta(oferta_id TEXT)
RETURNS TABLE (
    skill_uri TEXT,
    preferred_label TEXT,
    L1 TEXT,
    L2 TEXT,
    es_digital BOOLEAN,
    es_esencial BOOLEAN,
    score DECIMAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        s.skill_uri,
        s.preferred_label,
        s.L1,
        s.L2,
        s.es_digital,
        s.es_esencial,
        s.score
    FROM ofertas_skills s
    WHERE s.id_oferta = oferta_id
    ORDER BY s.es_esencial DESC, s.score DESC NULLS LAST;
END;
$$ LANGUAGE plpgsql STABLE;

COMMENT ON FUNCTION get_skills_oferta IS 'Obtiene todos los skills de una oferta especifica';

-- ============================================
-- FIN DEL SCRIPT v1.0
-- ============================================
