-- =============================================================================
-- MIGRACIÓN: Tabla de Auditoría NLP con Versionado
-- Versión: 1.0
-- Fecha: 2025-11-04
-- Descripción: Tabla para rastrear todas las versiones de extracción NLP
-- =============================================================================

-- Crear tabla de historial de versiones NLP
CREATE TABLE IF NOT EXISTS ofertas_nlp_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    id_oferta TEXT NOT NULL,
    nlp_version TEXT NOT NULL,  -- Ej: "3.7.0", "4.0.0", "5.0.0"
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Datos extraídos (JSON completo con todos los campos)
    extracted_data TEXT,  -- JSON con estructura completa

    -- Métricas de calidad
    quality_score REAL,           -- Score 0-7 (número de campos poblados)
    confidence_score REAL,        -- Score 0-1 (confianza del extractor)
    processing_time_ms INTEGER,   -- Tiempo de procesamiento en ms

    -- Control de activación
    is_active BOOLEAN DEFAULT 0,  -- Solo una versión activa por oferta
    replaced_by_version TEXT,      -- Si fue reemplazada, ¿por cuál?

    -- Metadata adicional
    extraction_method TEXT,        -- "regex", "llm", "hybrid"
    error_message TEXT,            -- NULL si OK, mensaje si error

    FOREIGN KEY (id_oferta) REFERENCES ofertas(id_oferta) ON DELETE CASCADE
);

-- Índices para optimizar queries
CREATE INDEX IF NOT EXISTS idx_nlp_history_oferta
    ON ofertas_nlp_history(id_oferta);

CREATE INDEX IF NOT EXISTS idx_nlp_history_version
    ON ofertas_nlp_history(nlp_version);

CREATE INDEX IF NOT EXISTS idx_nlp_history_active
    ON ofertas_nlp_history(is_active);

CREATE INDEX IF NOT EXISTS idx_nlp_history_quality
    ON ofertas_nlp_history(quality_score);

CREATE INDEX IF NOT EXISTS idx_nlp_history_processed_at
    ON ofertas_nlp_history(processed_at);

-- Índice compuesto para queries comunes
CREATE INDEX IF NOT EXISTS idx_nlp_history_oferta_active
    ON ofertas_nlp_history(id_oferta, is_active);
