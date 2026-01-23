-- Migration 017: Sistema de Priorización de Ofertas
-- Fecha: 2026-01-20
-- Propósito: Tabla para gestionar cola de procesamiento con prioridad
--
-- FUNCIONALIDAD:
-- 1. Persistir scores de prioridad (fecha + vacantes + permanencia)
-- 2. Rastrear estado de procesamiento por lote
-- 3. Bloquear avance si hay errores pendientes
-- 4. Integrar con reporte de fases

-- ============================================
-- TABLA: ofertas_prioridad
-- ============================================
-- Cola de procesamiento con scores calculados

CREATE TABLE IF NOT EXISTS ofertas_prioridad (
    id_oferta TEXT PRIMARY KEY,

    -- Scores de prioridad (0.0 - 1.0)
    score_total REAL NOT NULL,           -- Score compuesto final
    score_fecha REAL,                    -- 40% - Frescura (más reciente = mayor)
    score_vacantes REAL,                 -- 30% - Impacto (más vacantes = mayor)
    score_permanencia REAL,              -- 30% - Señal mercado (baja permanencia = mayor)

    -- Estado de procesamiento
    estado TEXT DEFAULT 'pendiente',     -- pendiente | en_proceso | procesado
    lote_asignado TEXT,                  -- ID del lote: "lote_20260120_1530"

    -- Timestamps
    fecha_calculo TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_asignado TIMESTAMP,            -- Cuando se asignó a un lote
    fecha_procesado TIMESTAMP,           -- Cuando terminó el procesamiento

    -- Foreign key
    FOREIGN KEY (id_oferta) REFERENCES ofertas(id_oferta)
);

-- ============================================
-- ÍNDICES
-- ============================================

-- Índice principal: ordenar por score descendente
CREATE INDEX IF NOT EXISTS idx_prioridad_score
ON ofertas_prioridad(score_total DESC);

-- Índice por estado (para filtrar pendientes rápidamente)
CREATE INDEX IF NOT EXISTS idx_prioridad_estado
ON ofertas_prioridad(estado);

-- Índice compuesto: estado + score (query principal del pipeline)
CREATE INDEX IF NOT EXISTS idx_prioridad_estado_score
ON ofertas_prioridad(estado, score_total DESC);

-- Índice por lote (para consultar estado de lotes)
CREATE INDEX IF NOT EXISTS idx_prioridad_lote
ON ofertas_prioridad(lote_asignado);

-- ============================================
-- VISTA: v_estado_lotes
-- ============================================
-- Resumen de estado por lote

DROP VIEW IF EXISTS v_estado_lotes;

CREATE VIEW v_estado_lotes AS
SELECT
    lote_asignado as lote,
    estado,
    COUNT(*) as ofertas,
    ROUND(AVG(score_total), 3) as score_promedio,
    MIN(fecha_asignado) as inicio,
    MAX(fecha_procesado) as fin,
    (
        SELECT COUNT(*)
        FROM validation_errors e
        WHERE e.id_oferta IN (
            SELECT id_oferta
            FROM ofertas_prioridad p2
            WHERE p2.lote_asignado = p.lote_asignado
        )
        AND e.resuelto = 0
    ) as errores_pendientes
FROM ofertas_prioridad p
WHERE lote_asignado IS NOT NULL
GROUP BY lote_asignado, estado
ORDER BY lote_asignado DESC;

-- ============================================
-- VISTA: v_cola_procesamiento
-- ============================================
-- Estado general de la cola

DROP VIEW IF EXISTS v_cola_procesamiento;

CREATE VIEW v_cola_procesamiento AS
SELECT
    SUM(CASE WHEN estado = 'pendiente' THEN 1 ELSE 0 END) as pendientes,
    SUM(CASE WHEN estado = 'en_proceso' THEN 1 ELSE 0 END) as en_proceso,
    SUM(CASE WHEN estado = 'procesado' THEN 1 ELSE 0 END) as procesados,
    COUNT(*) as total,
    COUNT(DISTINCT lote_asignado) as lotes_creados,
    ROUND(AVG(CASE WHEN estado = 'pendiente' THEN score_total END), 3) as score_promedio_pendientes,
    MAX(CASE WHEN estado = 'pendiente' THEN score_total END) as score_max_pendiente,
    MIN(CASE WHEN estado = 'pendiente' THEN score_total END) as score_min_pendiente
FROM ofertas_prioridad;

-- ============================================
-- VISTA: v_proximo_lote
-- ============================================
-- Preview del próximo lote (top 100 pendientes)

DROP VIEW IF EXISTS v_proximo_lote;

CREATE VIEW v_proximo_lote AS
SELECT
    id_oferta,
    score_total,
    score_fecha,
    score_vacantes,
    score_permanencia
FROM ofertas_prioridad
WHERE estado = 'pendiente'
ORDER BY score_total DESC
LIMIT 100;

-- ============================================
-- VERIFICACIÓN
-- ============================================

-- Verificar tabla creada
SELECT 'Tabla ofertas_prioridad creada' as status;

-- Verificar índices
SELECT name FROM sqlite_master
WHERE type = 'index'
AND tbl_name = 'ofertas_prioridad';

-- Verificar vistas
SELECT name FROM sqlite_master
WHERE type = 'view'
AND name LIKE 'v_%lote%' OR name LIKE 'v_%cola%' OR name LIKE 'v_%proximo%';
