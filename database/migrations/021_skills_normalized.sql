-- Migración 021: Tabla ofertas_skills_norm
-- Skills normalizados para queries eficientes (complementa JSON existente)
-- Fecha: 2026-02-03

-- ============================================
-- TABLA: ofertas_skills_norm
-- Extrae skills de JSON a tabla relacional
-- ============================================

CREATE TABLE IF NOT EXISTS ofertas_skills_norm (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Relación con oferta
    id_oferta INTEGER NOT NULL,

    -- Identificación del skill
    skill_uri TEXT NOT NULL,              -- URI ESCO del skill
    preferred_label TEXT,                  -- Nombre en español

    -- Categorización ESCO
    L1 TEXT,                              -- Código L1 (ej: "S1", "S2")
    L1_nombre TEXT,                       -- Nombre L1 (ej: "Communication skills")
    L2 TEXT,                              -- Código L2
    L2_nombre TEXT,                       -- Nombre L2
    es_digital INTEGER DEFAULT 0,         -- 1 si es skill digital

    -- Origen y confianza
    origen TEXT CHECK(origen IN ('regla', 'semantico', 'llm', 'merged', 'manual')),
    score REAL,                           -- Confianza 0.0-1.0
    es_esencial INTEGER DEFAULT 0,        -- 1 si es esencial para la ocupación

    -- Tracking
    run_id TEXT,                          -- FK a pipeline_runs
    created_at TEXT DEFAULT (datetime('now')),

    -- Foreign keys
    FOREIGN KEY (id_oferta) REFERENCES ofertas(id_oferta) ON DELETE CASCADE,
    FOREIGN KEY (run_id) REFERENCES pipeline_runs(run_id) ON DELETE SET NULL,

    -- Unique constraint: un skill por oferta
    UNIQUE(id_oferta, skill_uri)
);

-- ============================================
-- ÍNDICES
-- ============================================

-- Búsqueda por oferta (JOIN con ofertas)
CREATE INDEX IF NOT EXISTS idx_skills_norm_oferta
    ON ofertas_skills_norm(id_oferta);

-- Búsqueda por skill (queries "ofertas con Python")
CREATE INDEX IF NOT EXISTS idx_skills_norm_skill
    ON ofertas_skills_norm(skill_uri);

-- Búsqueda por categoría L1 (agregaciones por categoría)
CREATE INDEX IF NOT EXISTS idx_skills_norm_l1
    ON ofertas_skills_norm(L1);

-- Búsqueda por categoría L2
CREATE INDEX IF NOT EXISTS idx_skills_norm_l2
    ON ofertas_skills_norm(L2);

-- Skills digitales
CREATE INDEX IF NOT EXISTS idx_skills_norm_digital
    ON ofertas_skills_norm(es_digital) WHERE es_digital = 1;

-- Por origen (para métricas de reglas vs semántico)
CREATE INDEX IF NOT EXISTS idx_skills_norm_origen
    ON ofertas_skills_norm(origen);

-- Por label (búsqueda por nombre)
CREATE INDEX IF NOT EXISTS idx_skills_norm_label
    ON ofertas_skills_norm(preferred_label);

-- ============================================
-- VISTAS
-- ============================================

-- Vista: Skills más demandados
CREATE VIEW IF NOT EXISTS v_skills_demanda AS
SELECT
    skill_uri,
    preferred_label,
    L1,
    L1_nombre,
    es_digital,
    COUNT(*) as ofertas_count,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(DISTINCT id_oferta) FROM ofertas_skills_norm), 2) as porcentaje
FROM ofertas_skills_norm
GROUP BY skill_uri, preferred_label, L1, L1_nombre, es_digital
ORDER BY ofertas_count DESC;

-- Vista: Distribución por L1
CREATE VIEW IF NOT EXISTS v_skills_por_l1_norm AS
SELECT
    L1,
    L1_nombre,
    COUNT(DISTINCT skill_uri) as skills_unicos,
    COUNT(*) as menciones_totales,
    COUNT(DISTINCT id_oferta) as ofertas_con_skill
FROM ofertas_skills_norm
WHERE L1 IS NOT NULL
GROUP BY L1, L1_nombre
ORDER BY menciones_totales DESC;

-- Vista: Skills digitales más demandados
CREATE VIEW IF NOT EXISTS v_skills_digitales_demanda AS
SELECT
    skill_uri,
    preferred_label,
    L2,
    L2_nombre,
    COUNT(*) as ofertas_count
FROM ofertas_skills_norm
WHERE es_digital = 1
GROUP BY skill_uri, preferred_label, L2, L2_nombre
ORDER BY ofertas_count DESC
LIMIT 50;

-- Vista: Comparación origen (regla vs semántico)
CREATE VIEW IF NOT EXISTS v_skills_por_origen AS
SELECT
    origen,
    COUNT(*) as total_skills,
    COUNT(DISTINCT skill_uri) as skills_unicos,
    COUNT(DISTINCT id_oferta) as ofertas_afectadas,
    ROUND(AVG(score), 3) as score_promedio
FROM ofertas_skills_norm
GROUP BY origen;

-- ============================================
-- TRIGGER: Actualizar timestamp
-- ============================================

CREATE TRIGGER IF NOT EXISTS trg_skills_norm_updated
AFTER UPDATE ON ofertas_skills_norm
BEGIN
    UPDATE ofertas_skills_norm
    SET created_at = datetime('now')
    WHERE id = NEW.id;
END;

-- ============================================
-- SCRIPT DE POBLACIÓN INICIAL
-- Se ejecuta por separado: scripts/populate_skills_norm.py
-- ============================================

-- Nota: Esta migración solo crea la estructura.
-- Para poblar la tabla desde los JSON existentes, ejecutar:
--   python scripts/populate_skills_norm.py
--
-- El script extrae skills de:
--   - ofertas_esco_matching.skills_oferta_json
--   - ofertas_esco_skills_detalle (si tiene datos)
--
-- Y los normaliza en esta tabla.
