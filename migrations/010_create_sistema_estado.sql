-- Migration 010: Crear tabla sistema_estado para colaboración
-- Ejecutar en Supabase SQL Editor
-- Fecha: 2026-01-17

-- Tabla para estado del sistema (métricas de las 3 fases)
CREATE TABLE IF NOT EXISTS sistema_estado (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ DEFAULT NOW(),

    -- Fase 1: Adquisición
    fase1_ofertas_totales INTEGER,
    fase1_ofertas_activas INTEGER,
    fase1_ofertas_cerradas INTEGER,
    fase1_ultimo_scraping DATE,
    fase1_dias_desde_scraping INTEGER,
    fase1_fuentes JSONB,

    -- Fase 2: Procesamiento
    fase2_con_nlp INTEGER,
    fase2_sin_nlp INTEGER,
    fase2_con_matching INTEGER,
    fase2_pendientes_matching INTEGER,
    fase2_validadas INTEGER,
    fase2_pendientes_validacion INTEGER,
    fase2_errores_sin_resolver INTEGER,
    fase2_reglas_negocio INTEGER,
    fase2_tasa_convergencia TEXT,
    fase2_ultimo_run TEXT,

    -- Fase 3: Presentación
    fase3_ofertas_supabase INTEGER,
    fase3_pendientes_sync INTEGER,

    -- Sugerencia
    fase_sugerida INTEGER,
    fase_sugerida_nombre TEXT,
    fase_sugerida_razon TEXT,

    -- Metadata
    sync_source TEXT DEFAULT 'sync_learnings.py',
    sync_version TEXT DEFAULT '2.0'
);

-- Índice para consultas por fecha
CREATE INDEX IF NOT EXISTS idx_sistema_estado_timestamp ON sistema_estado(timestamp DESC);

-- Vista para el último estado
CREATE OR REPLACE VIEW v_sistema_estado_actual AS
SELECT * FROM sistema_estado
ORDER BY timestamp DESC
LIMIT 1;

-- Comentarios
COMMENT ON TABLE sistema_estado IS 'Estado de las 3 fases del sistema MOL para colaboración';
COMMENT ON COLUMN sistema_estado.fase_sugerida IS 'Número de fase que necesita atención (1, 2, 3, o 0 si todo OK)';

-- Política RLS (permite lectura y escritura pública - tabla de métricas internas)
ALTER TABLE sistema_estado ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Lectura pública sistema_estado" ON sistema_estado
    FOR SELECT USING (true);

CREATE POLICY "Escritura pública sistema_estado" ON sistema_estado
    FOR INSERT WITH CHECK (true);
