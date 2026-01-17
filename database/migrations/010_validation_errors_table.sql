-- Migración 010: Tabla validation_errors
-- Persiste errores detectados por auto_validator.py
-- Fecha: 2026-01-16

-- Tabla principal de errores de validación
CREATE TABLE IF NOT EXISTS validation_errors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    id_oferta TEXT NOT NULL,
    run_id TEXT,
    error_id TEXT NOT NULL,           -- Ej: "V02_isco_nulo_score_bajo"
    error_tipo TEXT,                  -- Ej: "error_matching", "error_nlp_ubicacion"
    severidad TEXT,                   -- "critico", "alto", "medio", "bajo", "info"
    mensaje TEXT,
    campo_afectado TEXT,              -- Campo que tiene el error
    valor_actual TEXT,                -- Valor que causó el error
    detectado_timestamp TEXT NOT NULL,
    corregido INTEGER DEFAULT 0,      -- 1 si auto-corrector lo arregló
    corregido_timestamp TEXT,
    corregido_metodo TEXT,            -- "auto", "manual", "regla_nueva"
    escalado_claude INTEGER DEFAULT 0, -- 1 si requiere regla nueva
    resuelto INTEGER DEFAULT 0,       -- 1 si se resolvió (manual o auto)
    notas TEXT,
    FOREIGN KEY (id_oferta) REFERENCES ofertas(id_oferta)
);

-- Índices para búsquedas frecuentes
CREATE INDEX IF NOT EXISTS idx_validation_errors_oferta ON validation_errors(id_oferta);
CREATE INDEX IF NOT EXISTS idx_validation_errors_run ON validation_errors(run_id);
CREATE INDEX IF NOT EXISTS idx_validation_errors_tipo ON validation_errors(error_tipo);
CREATE INDEX IF NOT EXISTS idx_validation_errors_no_resuelto ON validation_errors(resuelto) WHERE resuelto = 0;
CREATE INDEX IF NOT EXISTS idx_validation_errors_escalado ON validation_errors(escalado_claude) WHERE escalado_claude = 1;

-- Vista para errores pendientes
CREATE VIEW IF NOT EXISTS v_errores_pendientes AS
SELECT
    ve.id,
    ve.id_oferta,
    ve.error_id,
    ve.error_tipo,
    ve.severidad,
    ve.mensaje,
    ve.detectado_timestamp,
    o.titulo,
    m.isco_code,
    m.estado_validacion
FROM validation_errors ve
LEFT JOIN ofertas o ON ve.id_oferta = o.id_oferta
LEFT JOIN ofertas_esco_matching m ON ve.id_oferta = m.id_oferta
WHERE ve.resuelto = 0
ORDER BY
    CASE ve.severidad
        WHEN 'critico' THEN 1
        WHEN 'alto' THEN 2
        WHEN 'medio' THEN 3
        WHEN 'bajo' THEN 4
        ELSE 5
    END,
    ve.detectado_timestamp DESC;

-- Vista para resumen por tipo de error
CREATE VIEW IF NOT EXISTS v_errores_por_tipo AS
SELECT
    error_tipo,
    severidad,
    COUNT(*) as total,
    SUM(CASE WHEN corregido = 1 THEN 1 ELSE 0 END) as corregidos,
    SUM(CASE WHEN escalado_claude = 1 THEN 1 ELSE 0 END) as escalados,
    SUM(CASE WHEN resuelto = 0 THEN 1 ELSE 0 END) as pendientes
FROM validation_errors
GROUP BY error_tipo, severidad
ORDER BY total DESC;
