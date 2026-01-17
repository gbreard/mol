-- Migration 011: Learning Evolution Metrics
-- Agrega columnas para trackear la evolucion del aprendizaje del sistema
-- Fecha: 2026-01-16

-- Agregar columnas de conteo de reglas a pipeline_runs
ALTER TABLE pipeline_runs ADD COLUMN reglas_negocio_count INTEGER DEFAULT 0;
ALTER TABLE pipeline_runs ADD COLUMN reglas_validacion_count INTEGER DEFAULT 0;
ALTER TABLE pipeline_runs ADD COLUMN sinonimos_count INTEGER DEFAULT 0;
ALTER TABLE pipeline_runs ADD COLUMN empresas_catalogo_count INTEGER DEFAULT 0;

-- Agregar columnas de errores detectados/corregidos
ALTER TABLE pipeline_runs ADD COLUMN errores_detectados INTEGER DEFAULT 0;
ALTER TABLE pipeline_runs ADD COLUMN errores_corregidos INTEGER DEFAULT 0;
ALTER TABLE pipeline_runs ADD COLUMN errores_escalados INTEGER DEFAULT 0;

-- Agregar columna de delta de reglas respecto al run anterior
ALTER TABLE pipeline_runs ADD COLUMN delta_reglas INTEGER DEFAULT 0;

-- Crear tabla de historial de aprendizaje (timeline)
CREATE TABLE IF NOT EXISTS learning_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL DEFAULT (datetime('now')),
    run_id TEXT,
    evento_tipo TEXT NOT NULL,  -- 'regla_agregada', 'error_corregido', 'sinonimo_agregado', etc
    config_modificado TEXT,     -- 'matching_rules_business.json', 'sinonimos_argentinos_esco.json', etc
    descripcion TEXT,
    conteo_antes INTEGER,
    conteo_despues INTEGER,
    delta INTEGER,
    detalles TEXT,  -- JSON con info adicional
    FOREIGN KEY (run_id) REFERENCES pipeline_runs(run_id)
);

-- Crear indice para busquedas por fecha
CREATE INDEX IF NOT EXISTS idx_learning_history_timestamp ON learning_history(timestamp);
CREATE INDEX IF NOT EXISTS idx_learning_history_evento ON learning_history(evento_tipo);

-- Crear vista de evolucion del aprendizaje
CREATE VIEW IF NOT EXISTS v_learning_evolution AS
SELECT
    pr.run_id,
    date(pr.timestamp) as fecha,
    time(pr.timestamp) as hora,
    pr.matching_version,
    pr.source,
    pr.ofertas_count,
    pr.reglas_negocio_count,
    pr.reglas_validacion_count,
    pr.sinonimos_count,
    pr.delta_reglas,
    pr.errores_detectados,
    pr.errores_corregidos,
    pr.metricas_precision,
    pr.run_anterior,
    -- Calcular mejora respecto al anterior
    CASE
        WHEN pr.run_anterior IS NOT NULL THEN
            pr.reglas_negocio_count - COALESCE(
                (SELECT reglas_negocio_count FROM pipeline_runs WHERE run_id = pr.run_anterior), 0
            )
        ELSE 0
    END as reglas_desde_anterior
FROM pipeline_runs pr
ORDER BY pr.timestamp DESC;

-- Crear vista de resumen diario
CREATE VIEW IF NOT EXISTS v_learning_daily_summary AS
SELECT
    date(timestamp) as fecha,
    COUNT(*) as runs_count,
    SUM(ofertas_count) as ofertas_procesadas,
    MAX(reglas_negocio_count) as reglas_al_final,
    SUM(errores_corregidos) as errores_corregidos_total,
    MAX(metricas_precision) as mejor_precision
FROM pipeline_runs
GROUP BY date(timestamp)
ORDER BY fecha DESC;
