-- Migration 012: Batch Learning System
-- Sistema de tracking de aprendizaje por lotes
-- Fecha: 2026-01-16

-- Tabla principal de lotes
CREATE TABLE IF NOT EXISTS learning_batches (
    lote_id TEXT PRIMARY KEY,
    nombre TEXT NOT NULL,
    descripcion TEXT,
    fecha_inicio TEXT NOT NULL,
    fecha_fin TEXT,
    estado TEXT DEFAULT 'en_proceso',  -- en_proceso, completado, archivado

    -- Ofertas
    ofertas_total INTEGER DEFAULT 0,
    ofertas_ids TEXT,  -- JSON array

    -- Métricas de aprendizaje
    reglas_inicio INTEGER DEFAULT 0,
    reglas_fin INTEGER DEFAULT 0,
    reglas_agregadas INTEGER DEFAULT 0,

    -- Métricas de cobertura
    ofertas_cubiertas INTEGER DEFAULT 0,      -- Sin errores (reglas existentes funcionaron)
    ofertas_nuevas_reglas INTEGER DEFAULT 0,  -- Requirieron reglas nuevas

    -- Métricas de convergencia
    tasa_aprendizaje REAL,           -- reglas_agregadas / ofertas_total
    cobertura_estimada REAL,         -- ofertas_cubiertas / ofertas_total

    -- Tracking de errores
    errores_detectados INTEGER DEFAULT 0,
    errores_corregidos INTEGER DEFAULT 0,
    errores_pendientes INTEGER DEFAULT 0,

    -- Metadata
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

-- Relación lote -> runs
CREATE TABLE IF NOT EXISTS batch_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lote_id TEXT NOT NULL,
    run_id TEXT NOT NULL,
    orden INTEGER,  -- Orden del run dentro del lote
    es_final INTEGER DEFAULT 0,  -- 1 si es el run final del lote
    FOREIGN KEY (lote_id) REFERENCES learning_batches(lote_id),
    FOREIGN KEY (run_id) REFERENCES pipeline_runs(run_id),
    UNIQUE(lote_id, run_id)
);

-- Agregar lote_id a ofertas_esco_matching para tracking
-- (Si no existe la columna)
-- ALTER TABLE ofertas_esco_matching ADD COLUMN lote_id TEXT;

-- Índices
CREATE INDEX IF NOT EXISTS idx_batches_estado ON learning_batches(estado);
CREATE INDEX IF NOT EXISTS idx_batches_fecha ON learning_batches(fecha_inicio);
CREATE INDEX IF NOT EXISTS idx_batch_runs_lote ON batch_runs(lote_id);

-- Vista de resumen de lotes
CREATE VIEW IF NOT EXISTS v_batch_summary AS
SELECT
    lb.lote_id,
    lb.nombre,
    lb.estado,
    lb.ofertas_total,
    lb.reglas_inicio,
    lb.reglas_fin,
    lb.reglas_agregadas,
    lb.tasa_aprendizaje,
    lb.cobertura_estimada,
    COUNT(br.run_id) as num_runs,
    lb.fecha_inicio,
    lb.fecha_fin
FROM learning_batches lb
LEFT JOIN batch_runs br ON lb.lote_id = br.lote_id
GROUP BY lb.lote_id
ORDER BY lb.fecha_inicio DESC;

-- Vista de evolución de convergencia
CREATE VIEW IF NOT EXISTS v_convergence_evolution AS
SELECT
    lote_id,
    nombre,
    fecha_inicio,
    reglas_fin as reglas_acumuladas,
    tasa_aprendizaje,
    cobertura_estimada,
    SUM(ofertas_total) OVER (ORDER BY fecha_inicio) as ofertas_acumuladas,
    SUM(reglas_agregadas) OVER (ORDER BY fecha_inicio) as reglas_totales_agregadas
FROM learning_batches
WHERE estado IN ('completado', 'en_proceso')
ORDER BY fecha_inicio;
