-- Tabla principal para el dashboard de ofertas
-- Contiene los datos necesarios para visualización

CREATE TABLE IF NOT EXISTS ofertas_dashboard (
    id_oferta TEXT PRIMARY KEY,
    -- Datos básicos
    titulo TEXT NOT NULL,
    empresa TEXT,
    fecha_publicacion DATE,
    url TEXT,
    portal TEXT,
    -- Ubicación
    provincia TEXT,
    localidad TEXT,
    -- Clasificación ESCO
    isco_code TEXT,
    isco_label TEXT,
    occupation_match_score REAL,
    occupation_match_method TEXT,
    -- Atributos NLP
    modalidad TEXT,
    nivel_seniority TEXT,
    area_funcional TEXT,
    sector_empresa TEXT,
    -- Salario
    salario_min INTEGER,
    salario_max INTEGER,
    moneda TEXT DEFAULT 'ARS',
    -- Skills (JSON arrays)
    skills_tecnicas JSONB,
    soft_skills JSONB,
    -- Metadata
    estado TEXT DEFAULT 'activa',
    fecha_sync TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Índices para consultas frecuentes
CREATE INDEX IF NOT EXISTS idx_ofertas_provincia ON ofertas_dashboard(provincia);
CREATE INDEX IF NOT EXISTS idx_ofertas_isco ON ofertas_dashboard(isco_code);
CREATE INDEX IF NOT EXISTS idx_ofertas_fecha ON ofertas_dashboard(fecha_publicacion);
CREATE INDEX IF NOT EXISTS idx_ofertas_modalidad ON ofertas_dashboard(modalidad);
CREATE INDEX IF NOT EXISTS idx_ofertas_seniority ON ofertas_dashboard(nivel_seniority);

-- Vista para KPIs
CREATE OR REPLACE VIEW v_kpis_dashboard AS
SELECT
    COUNT(*) as total_ofertas,
    COUNT(DISTINCT isco_code) as ocupaciones_distintas,
    COUNT(DISTINCT provincia) as provincias,
    COUNT(DISTINCT empresa) as empresas_activas
FROM ofertas_dashboard;

-- Vista para distribución geográfica
CREATE OR REPLACE VIEW v_ofertas_por_provincia AS
SELECT
    provincia,
    COUNT(*) as cantidad,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 1) as porcentaje
FROM ofertas_dashboard
WHERE provincia IS NOT NULL
GROUP BY provincia
ORDER BY cantidad DESC;

-- Vista para top ocupaciones
CREATE OR REPLACE VIEW v_top_ocupaciones AS
SELECT
    isco_code,
    isco_label as ocupacion,
    COUNT(*) as cantidad
FROM ofertas_dashboard
WHERE isco_label IS NOT NULL
GROUP BY isco_code, isco_label
ORDER BY cantidad DESC
LIMIT 10;

-- Vista para distribución por modalidad
CREATE OR REPLACE VIEW v_ofertas_por_modalidad AS
SELECT
    COALESCE(modalidad, 'No especificado') as modalidad,
    COUNT(*) as cantidad
FROM ofertas_dashboard
GROUP BY modalidad
ORDER BY cantidad DESC;

-- Vista para distribución por seniority
CREATE OR REPLACE VIEW v_ofertas_por_seniority AS
SELECT
    COALESCE(nivel_seniority, 'No especificado') as seniority,
    COUNT(*) as cantidad
FROM ofertas_dashboard
GROUP BY nivel_seniority
ORDER BY cantidad DESC;

-- RLS: Lectura pública (datos agregados del mercado laboral)
ALTER TABLE ofertas_dashboard ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Ofertas visibles para todos" ON ofertas_dashboard
    FOR SELECT USING (true);

-- Solo service_role puede insertar/actualizar
CREATE POLICY "Solo service_role puede modificar" ON ofertas_dashboard
    FOR ALL USING (auth.role() = 'service_role');

-- Función para actualizar updated_at
CREATE OR REPLACE FUNCTION update_ofertas_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_ofertas_updated_at
    BEFORE UPDATE ON ofertas_dashboard
    FOR EACH ROW
    EXECUTE FUNCTION update_ofertas_updated_at();
