-- ============================================
-- MOL Dashboard - Catalogos ESCO
-- Version: 1.0
-- Fecha: 2026-02-03
-- ============================================
-- Catalogos de referencia ESCO para skills y ocupaciones
-- Se sincronizan desde SQLite local
-- ============================================

-- 1. TABLA SKILLS (Catalogo ESCO)
-- ============================================
CREATE TABLE IF NOT EXISTS skills (
    skill_uri TEXT PRIMARY KEY,           -- URI ESCO del skill

    -- Datos basicos
    preferred_label_es TEXT,              -- Nombre en espanol
    preferred_label_en TEXT,              -- Nombre en ingles (original ESCO)
    description_es TEXT,                  -- Descripcion en espanol
    alt_labels TEXT[],                    -- Etiquetas alternativas

    -- Categorizacion ESCO
    L1 TEXT,                              -- S1-S8, K1-K7, T1-T6, A1-A8
    L1_nombre TEXT,                       -- Nombre categoria L1
    L2 TEXT,                              -- Subcategoria
    L2_nombre TEXT,                       -- Nombre subcategoria
    skill_type TEXT CHECK(skill_type IN ('skill', 'knowledge', 'transversal', 'attitude')),

    -- Digital Skills
    es_digital BOOLEAN DEFAULT false,     -- Pertenece a Digital Skills taxonomy
    digital_level TEXT,                   -- foundation/intermediate/advanced

    -- Relaciones
    broader_skill_uri TEXT,               -- Skill padre en jerarquia
    reuse_level TEXT,                     -- cross-sector/sector-specific/occupation-specific

    -- Metadata
    esco_version TEXT,                    -- Version ESCO (1.1.1, 1.2.0)
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE skills IS 'Catalogo ESCO de skills - sincronizado desde SQLite local';
COMMENT ON COLUMN skills.skill_type IS 'skill=competencia, knowledge=conocimiento, transversal=transversal, attitude=actitud';
COMMENT ON COLUMN skills.reuse_level IS 'Nivel de reutilizacion del skill entre ocupaciones';

-- 2. TABLA OCUPACIONES_ESCO
-- ============================================
CREATE TABLE IF NOT EXISTS ocupaciones_esco (
    esco_uri TEXT PRIMARY KEY,            -- URI ESCO de la ocupacion

    -- ISCO
    isco_code TEXT NOT NULL,              -- Codigo ISCO-08 (4 digitos)
    isco_label TEXT,                      -- Nombre ISCO-08

    -- Datos basicos
    preferred_label_es TEXT NOT NULL,     -- Nombre en espanol
    preferred_label_en TEXT,              -- Nombre en ingles
    description_es TEXT,                  -- Descripcion en espanol
    alt_labels TEXT[],                    -- Etiquetas alternativas

    -- Jerarquia
    broader_uri TEXT,                     -- Ocupacion padre
    hierarchy_level INTEGER,              -- 1=grupo mayor, 2=subgrupo, 3=menor, 4=unitario

    -- Metadata
    esco_version TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE ocupaciones_esco IS 'Catalogo ESCO de ocupaciones con mapeo a ISCO-08';
COMMENT ON COLUMN ocupaciones_esco.isco_code IS 'Codigo ISCO-08 de 4 digitos (ej: 2512)';
COMMENT ON COLUMN ocupaciones_esco.hierarchy_level IS '1-4, donde 4 es la ocupacion mas especifica';

-- 3. TABLA SKILL_OCCUPATION (Relacion N:M)
-- ============================================
-- Indica que skills son requeridos por cada ocupacion segun ESCO
CREATE TABLE IF NOT EXISTS skill_occupation (
    id SERIAL PRIMARY KEY,
    esco_occupation_uri TEXT REFERENCES ocupaciones_esco(esco_uri) ON DELETE CASCADE,
    skill_uri TEXT REFERENCES skills(skill_uri) ON DELETE CASCADE,

    -- Tipo de relacion
    relation_type TEXT CHECK(relation_type IN ('essential', 'optional')),

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(esco_occupation_uri, skill_uri)
);

COMMENT ON TABLE skill_occupation IS 'Relacion ESCO oficial entre ocupaciones y skills';
COMMENT ON COLUMN skill_occupation.relation_type IS 'essential=obligatorio, optional=deseable';

-- 4. TABLA EMPRESAS (Normalizada)
-- ============================================
CREATE TABLE IF NOT EXISTS empresas (
    id SERIAL PRIMARY KEY,
    nombre TEXT NOT NULL,                 -- Nombre de la empresa
    nombre_normalizado TEXT,              -- Nombre limpio (sin SA, SRL, etc)

    -- Clasificacion
    sector TEXT,                          -- Sector economico
    clae_code TEXT,                       -- Codigo CLAE (AFIP)
    clae_grupo TEXT,                      -- Grupo CLAE

    -- Datos
    tamano TEXT CHECK(tamano IN ('micro', 'pequena', 'mediana', 'grande')),
    provincia_sede TEXT,                  -- Provincia de la sede principal

    -- Metricas
    ofertas_activas INTEGER DEFAULT 0,    -- Contador de ofertas activas
    ofertas_historicas INTEGER DEFAULT 0, -- Total ofertas publicadas

    -- Metadata
    primera_oferta TIMESTAMPTZ,
    ultima_oferta TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(nombre_normalizado)
);

COMMENT ON TABLE empresas IS 'Catalogo de empresas normalizado';
COMMENT ON COLUMN empresas.clae_code IS 'Codigo CLAE del sector (clasificacion AFIP)';

-- 5. INDICES
-- ============================================

-- Skills
CREATE INDEX IF NOT EXISTS idx_skills_l1 ON skills(L1);
CREATE INDEX IF NOT EXISTS idx_skills_l2 ON skills(L2);
CREATE INDEX IF NOT EXISTS idx_skills_digital ON skills(es_digital) WHERE es_digital = true;
CREATE INDEX IF NOT EXISTS idx_skills_type ON skills(skill_type);
CREATE INDEX IF NOT EXISTS idx_skills_label ON skills(preferred_label_es);

-- Ocupaciones
CREATE INDEX IF NOT EXISTS idx_ocupaciones_isco ON ocupaciones_esco(isco_code);
CREATE INDEX IF NOT EXISTS idx_ocupaciones_label ON ocupaciones_esco(preferred_label_es);
CREATE INDEX IF NOT EXISTS idx_ocupaciones_level ON ocupaciones_esco(hierarchy_level);

-- Skill-Occupation
CREATE INDEX IF NOT EXISTS idx_skill_occ_skill ON skill_occupation(skill_uri);
CREATE INDEX IF NOT EXISTS idx_skill_occ_occ ON skill_occupation(esco_occupation_uri);
CREATE INDEX IF NOT EXISTS idx_skill_occ_type ON skill_occupation(relation_type);

-- Empresas
CREATE INDEX IF NOT EXISTS idx_empresas_nombre ON empresas(nombre_normalizado);
CREATE INDEX IF NOT EXISTS idx_empresas_sector ON empresas(sector);
CREATE INDEX IF NOT EXISTS idx_empresas_clae ON empresas(clae_code);

-- 6. VISTAS
-- ============================================

-- Vista: Ocupaciones con cantidad de skills requeridos
CREATE OR REPLACE VIEW v_ocupaciones_con_skills AS
SELECT
    o.isco_code,
    o.preferred_label_es as ocupacion,
    COUNT(CASE WHEN so.relation_type = 'essential' THEN 1 END) as skills_esenciales,
    COUNT(CASE WHEN so.relation_type = 'optional' THEN 1 END) as skills_opcionales,
    COUNT(*) as skills_total
FROM ocupaciones_esco o
LEFT JOIN skill_occupation so ON o.esco_uri = so.esco_occupation_uri
GROUP BY o.isco_code, o.preferred_label_es
ORDER BY skills_total DESC;

-- Vista: Skills mas comunes entre ocupaciones
CREATE OR REPLACE VIEW v_skills_transversales AS
SELECT
    s.skill_uri,
    s.preferred_label_es as skill,
    s.L1,
    COUNT(DISTINCT so.esco_occupation_uri) as ocupaciones_count,
    ROUND(COUNT(DISTINCT so.esco_occupation_uri) * 100.0 /
          NULLIF((SELECT COUNT(*) FROM ocupaciones_esco), 0), 1) as porcentaje_ocupaciones
FROM skills s
JOIN skill_occupation so ON s.skill_uri = so.skill_uri
GROUP BY s.skill_uri, s.preferred_label_es, s.L1
HAVING COUNT(DISTINCT so.esco_occupation_uri) > 10
ORDER BY ocupaciones_count DESC
LIMIT 50;

-- Vista: Jerarquia ISCO
CREATE OR REPLACE VIEW v_jerarquia_isco AS
SELECT
    SUBSTRING(isco_code, 1, 1) as grupo_mayor,
    SUBSTRING(isco_code, 1, 2) as subgrupo_mayor,
    SUBSTRING(isco_code, 1, 3) as grupo_menor,
    isco_code as grupo_unitario,
    preferred_label_es as ocupacion,
    hierarchy_level
FROM ocupaciones_esco
ORDER BY isco_code;

-- Vista: Empresas activas
CREATE OR REPLACE VIEW v_empresas_activas AS
SELECT
    e.id,
    e.nombre,
    e.sector,
    e.tamano,
    e.provincia_sede,
    e.ofertas_activas,
    COUNT(o.id_oferta) as ofertas_actuales
FROM empresas e
LEFT JOIN ofertas_dashboard o ON e.nombre_normalizado = LOWER(TRIM(o.empresa))
WHERE o.estado = 'activa'
GROUP BY e.id
HAVING e.ofertas_activas > 0 OR COUNT(o.id_oferta) > 0
ORDER BY ofertas_actuales DESC;

-- 7. ROW LEVEL SECURITY
-- ============================================

-- Catalogos son de lectura publica
ALTER TABLE skills ENABLE ROW LEVEL SECURITY;
ALTER TABLE ocupaciones_esco ENABLE ROW LEVEL SECURITY;
ALTER TABLE skill_occupation ENABLE ROW LEVEL SECURITY;
ALTER TABLE empresas ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Skills catalogo publico" ON skills
    FOR SELECT USING (true);

CREATE POLICY "Ocupaciones catalogo publico" ON ocupaciones_esco
    FOR SELECT USING (true);

CREATE POLICY "Skill-Occupation catalogo publico" ON skill_occupation
    FOR SELECT USING (true);

CREATE POLICY "Empresas catalogo publico" ON empresas
    FOR SELECT USING (true);

-- Solo service_role puede modificar catalogos
CREATE POLICY "Solo service_role modifica skills" ON skills
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Solo service_role modifica ocupaciones" ON ocupaciones_esco
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Solo service_role modifica skill_occupation" ON skill_occupation
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Solo service_role modifica empresas" ON empresas
    FOR ALL USING (auth.role() = 'service_role');

-- 8. FUNCIONES AUXILIARES
-- ============================================

-- Funcion: Buscar skill por nombre
CREATE OR REPLACE FUNCTION buscar_skill(nombre TEXT)
RETURNS TABLE (
    skill_uri TEXT,
    preferred_label TEXT,
    L1 TEXT,
    skill_type TEXT,
    es_digital BOOLEAN
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        s.skill_uri,
        s.preferred_label_es,
        s.L1,
        s.skill_type,
        s.es_digital
    FROM skills s
    WHERE s.preferred_label_es ILIKE '%' || nombre || '%'
       OR nombre = ANY(s.alt_labels)
    ORDER BY s.preferred_label_es
    LIMIT 20;
END;
$$ LANGUAGE plpgsql STABLE;

-- Funcion: Skills de una ocupacion (segun ESCO oficial)
CREATE OR REPLACE FUNCTION get_skills_ocupacion(isco TEXT)
RETURNS TABLE (
    skill_uri TEXT,
    skill_label TEXT,
    relation_type TEXT,
    es_digital BOOLEAN
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        s.skill_uri,
        s.preferred_label_es,
        so.relation_type,
        s.es_digital
    FROM skill_occupation so
    JOIN skills s ON so.skill_uri = s.skill_uri
    JOIN ocupaciones_esco o ON so.esco_occupation_uri = o.esco_uri
    WHERE o.isco_code = isco
    ORDER BY so.relation_type, s.preferred_label_es;
END;
$$ LANGUAGE plpgsql STABLE;

-- Funcion: Actualizar updated_at
CREATE OR REPLACE FUNCTION update_catalog_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_skills_updated
    BEFORE UPDATE ON skills
    FOR EACH ROW EXECUTE FUNCTION update_catalog_timestamp();

CREATE TRIGGER trigger_ocupaciones_updated
    BEFORE UPDATE ON ocupaciones_esco
    FOR EACH ROW EXECUTE FUNCTION update_catalog_timestamp();

CREATE TRIGGER trigger_empresas_updated
    BEFORE UPDATE ON empresas
    FOR EACH ROW EXECUTE FUNCTION update_catalog_timestamp();

-- ============================================
-- FIN DEL SCRIPT v1.0
-- ============================================
