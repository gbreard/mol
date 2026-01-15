-- =====================================================
-- MIGRACIÓN 006: Sistema de Validación Completo
-- Fecha: 2026-01-13
-- Propósito: Centralizar tracking de runs y validación en BD
-- =====================================================

-- =====================================================
-- 1. CREAR TABLA: pipeline_runs
-- Registra cada ejecución del pipeline con sus configs y métricas
-- =====================================================

CREATE TABLE IF NOT EXISTS pipeline_runs (
    -- Identificación
    run_id TEXT PRIMARY KEY,              -- "run_20260113_1550"
    timestamp TEXT NOT NULL,              -- ISO format "2026-01-13T15:50:00"
    source TEXT,                          -- "gold_set_100", "produccion", "test"
    description TEXT,                     -- Descripción del cambio/experimento

    -- Versiones de código
    git_branch TEXT,                      -- "feature/optimization-nlp"
    git_commit TEXT,                      -- "abc1234" (short hash)
    nlp_version TEXT,                     -- "11.3.0"
    matching_version TEXT,                -- "3.2.4"

    -- Configs usadas (snapshots JSON)
    config_snapshot TEXT,                 -- {"matching_config": "2.1.0", "rules": "1.2", ...}
    config_files TEXT,                    -- Contenido completo de cada JSON (para reproducibilidad)

    -- Ofertas procesadas
    ofertas_count INTEGER,                -- 100
    ofertas_ids TEXT,                     -- JSON array: ["2171813", "2171866", ...]

    -- Métricas resultantes (se llenan al finalizar el run)
    metricas_total INTEGER,               -- Total ofertas evaluadas
    metricas_correctos INTEGER,           -- Matches correctos
    metricas_parciales INTEGER,           -- Matches parcialmente correctos
    metricas_errores INTEGER,             -- Matches incorrectos
    metricas_precision REAL,              -- Precisión (0.0 - 1.0)
    metricas_detalle TEXT,                -- JSON: {"cross_sector": 5, "seniority_mismatch": 3}

    -- Comparación con run anterior (opcional)
    run_anterior TEXT,                    -- "run_20260113_1200"
    diff_mejoras INTEGER,                 -- Ofertas que mejoraron vs run anterior
    diff_regresiones INTEGER,             -- Ofertas que empeoraron
    diff_sin_cambio INTEGER               -- Ofertas sin cambio
);

-- Índices para búsqueda rápida
CREATE INDEX IF NOT EXISTS idx_runs_timestamp ON pipeline_runs(timestamp);
CREATE INDEX IF NOT EXISTS idx_runs_source ON pipeline_runs(source);
CREATE INDEX IF NOT EXISTS idx_runs_matching_version ON pipeline_runs(matching_version);

-- =====================================================
-- 2. MODIFICAR TABLA: ofertas_esco_matching
-- Agregar columnas de validación
-- =====================================================

-- Estado de validación
-- Valores: 'pendiente', 'en_revision', 'validado', 'rechazado', 'descartado'
ALTER TABLE ofertas_esco_matching ADD COLUMN estado_validacion TEXT DEFAULT 'pendiente';

-- Timestamp de validación
ALTER TABLE ofertas_esco_matching ADD COLUMN validado_timestamp TEXT;

-- Quién validó (usuario o "sistema")
ALTER TABLE ofertas_esco_matching ADD COLUMN validado_por TEXT;

-- Notas de revisión (errores detectados, comentarios)
ALTER TABLE ofertas_esco_matching ADD COLUMN notas_revision TEXT;

-- Índice para filtrar por estado
CREATE INDEX IF NOT EXISTS idx_matching_estado ON ofertas_esco_matching(estado_validacion);

-- =====================================================
-- 3. CREAR TABLA: validacion_historial
-- Auditoría de cambios de estado
-- =====================================================

CREATE TABLE IF NOT EXISTS validacion_historial (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Qué oferta
    id_oferta TEXT NOT NULL,

    -- En qué run estaba cuando cambió
    run_id TEXT,

    -- Cambio de estado
    estado_anterior TEXT,                 -- NULL si es primer estado
    estado_nuevo TEXT NOT NULL,

    -- Cuándo y por qué
    timestamp TEXT NOT NULL,
    motivo TEXT,                          -- "Revisión manual OK", "Error ISCO corregido"
    usuario TEXT,                         -- "gerardo", "sistema"

    -- Foreign keys (sin CONSTRAINT para compatibilidad SQLite)
    FOREIGN KEY (id_oferta) REFERENCES ofertas_esco_matching(id_oferta),
    FOREIGN KEY (run_id) REFERENCES pipeline_runs(run_id)
);

CREATE INDEX IF NOT EXISTS idx_historial_oferta ON validacion_historial(id_oferta);
CREATE INDEX IF NOT EXISTS idx_historial_timestamp ON validacion_historial(timestamp);
CREATE INDEX IF NOT EXISTS idx_historial_run ON validacion_historial(run_id);

-- =====================================================
-- 4. MIGRAR DATOS EXISTENTES
-- Los 100 IDs actuales pasan a estado 'en_revision'
-- =====================================================

-- Crear run baseline retroactivo para los datos existentes
INSERT OR IGNORE INTO pipeline_runs (
    run_id,
    timestamp,
    source,
    description,
    matching_version,
    ofertas_count,
    metricas_precision
) VALUES (
    'run_baseline_20260113',
    '2026-01-13T15:00:00',
    'gold_set_100',
    'Baseline inicial - FASE 1/2/3 aplicadas - Pre-sistema de tracking',
    '3.2.3',
    100,
    0.64
);

-- Asignar run_id a ofertas existentes que no tienen
UPDATE ofertas_esco_matching
SET run_id = 'run_baseline_20260113',
    estado_validacion = 'en_revision'
WHERE run_id IS NULL;

-- Registrar en historial la migración
INSERT INTO validacion_historial (id_oferta, run_id, estado_anterior, estado_nuevo, timestamp, motivo, usuario)
SELECT
    id_oferta,
    'run_baseline_20260113',
    NULL,
    'en_revision',
    datetime('now'),
    'Migración inicial - Sistema de validación activado',
    'sistema'
FROM ofertas_esco_matching
WHERE run_id = 'run_baseline_20260113';

-- =====================================================
-- 5. VERIFICACIÓN (comentado - ejecutar manualmente)
-- =====================================================
-- SELECT COUNT(*) as ofertas_migradas FROM ofertas_esco_matching WHERE run_id = 'run_baseline_20260113';
-- SELECT COUNT(*) as historial_entries FROM validacion_historial WHERE run_id = 'run_baseline_20260113';
-- SELECT estado_validacion, COUNT(*) FROM ofertas_esco_matching GROUP BY estado_validacion;
