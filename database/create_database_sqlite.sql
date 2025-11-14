-- =====================================================================
-- BASE DE DATOS: Bumeran Scraping - Producción (SQLite)
-- =====================================================================
--
-- Schemas:
--   1. ofertas: Ofertas scrapeadas de Bumeran
--   2. metricas_scraping: Métricas de performance de cada ejecución
--   3. alertas: Alertas generadas durante scraping
--   4. circuit_breaker_stats: Estadísticas del circuit breaker
--   5. rate_limiter_stats: Estadísticas del rate limiter
--
-- Uso:
--   sqlite3 bumeran_scraping.db < create_database_sqlite.sql
-- =====================================================================

-- =====================================================================
-- TABLA: ofertas
-- =====================================================================
-- Almacena todas las ofertas laborales scrapeadas de Bumeran
-- Incluye todas las columnas de Fase 1+2+3 (38 columnas)
-- =====================================================================

CREATE TABLE IF NOT EXISTS ofertas (
    -- IDs
    id_oferta INTEGER PRIMARY KEY,
    id_empresa INTEGER,

    -- Información básica
    titulo TEXT NOT NULL,
    empresa TEXT,
    descripcion TEXT,
    confidencial INTEGER,  -- 0=False, 1=True

    -- Ubicación y modalidad
    localizacion TEXT,
    modalidad_trabajo TEXT,
    tipo_trabajo TEXT,

    -- Fechas (formato original DD-MM-YYYY)
    fecha_publicacion_original TEXT,
    fecha_hora_publicacion_original TEXT,
    fecha_modificado_original TEXT,

    -- Fechas ISO 8601 (para ordenamiento y filtrado)
    fecha_publicacion_iso TEXT,  -- YYYY-MM-DD
    fecha_hora_publicacion_iso TEXT,  -- YYYY-MM-DD HH:MM:SS
    fecha_modificado_iso TEXT,  -- YYYY-MM-DD

    -- Fechas datetime con timezone Argentina (UTC-3)
    fecha_publicacion_datetime TEXT,  -- ISO 8601 with timezone
    fecha_hora_publicacion_datetime TEXT,
    fecha_modificado_datetime TEXT,

    -- Detalles
    cantidad_vacantes INTEGER,
    apto_discapacitado INTEGER,  -- 0=False, 1=True

    -- Categorización
    id_area INTEGER,
    id_subarea INTEGER,
    id_pais INTEGER,

    -- Empresa
    logo_url TEXT,
    empresa_validada INTEGER,  -- 0=False, 1=True
    empresa_pro INTEGER,  -- 0=False, 1=True
    promedio_empresa REAL,

    -- Plan de publicación
    plan_publicacion_id INTEGER,
    plan_publicacion_nombre TEXT,

    -- Otros
    portal TEXT,
    tipo_aviso TEXT,
    tiene_preguntas INTEGER,  -- 0=False, 1=True
    salario_obligatorio INTEGER,  -- 0=False, 1=True
    alta_revision_perfiles INTEGER,  -- 0=False, 1=True
    guardado INTEGER,  -- 0=False, 1=True
    gptw_url TEXT,

    -- Metadata
    url_oferta TEXT,
    scrapeado_en TEXT NOT NULL DEFAULT (datetime('now'))  -- ISO 8601
);

-- Índices para performance
CREATE INDEX IF NOT EXISTS idx_ofertas_fecha_pub_iso ON ofertas(fecha_publicacion_iso DESC);
CREATE INDEX IF NOT EXISTS idx_ofertas_empresa ON ofertas(empresa);
CREATE INDEX IF NOT EXISTS idx_ofertas_localizacion ON ofertas(localizacion);
CREATE INDEX IF NOT EXISTS idx_ofertas_scrapeado_en ON ofertas(scrapeado_en DESC);
CREATE INDEX IF NOT EXISTS idx_ofertas_id_area ON ofertas(id_area);

-- =====================================================================
-- TABLA: metricas_scraping
-- =====================================================================
-- Almacena métricas de performance de cada ejecución de scraping
-- Permite análisis histórico y detección de degradación
-- =====================================================================

CREATE TABLE IF NOT EXISTS metricas_scraping (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Tiempos
    start_time TEXT NOT NULL,  -- ISO 8601
    end_time TEXT NOT NULL,
    total_time_seconds REAL NOT NULL,

    -- Páginas
    pages_scraped INTEGER NOT NULL DEFAULT 0,
    pages_failed INTEGER NOT NULL DEFAULT 0,
    pages_total INTEGER NOT NULL DEFAULT 0,
    success_rate REAL,  -- Porcentaje (0-100)
    avg_time_per_page REAL,  -- Segundos

    -- Ofertas
    offers_total INTEGER NOT NULL DEFAULT 0,
    offers_new INTEGER NOT NULL DEFAULT 0,
    offers_duplicates INTEGER NOT NULL DEFAULT 0,
    offers_per_second REAL,

    -- Validación
    validation_rate_avg REAL,  -- Porcentaje (0-100)
    validation_rate_min REAL,
    validation_rate_max REAL,

    -- Errores
    errors_count INTEGER NOT NULL DEFAULT 0,
    warnings_count INTEGER NOT NULL DEFAULT 0,

    -- Metadata
    incremental_mode INTEGER NOT NULL DEFAULT 1,  -- 0=False, 1=True
    query TEXT,  -- Query de búsqueda si se usó

    -- Timestamp de inserción
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Índices
CREATE INDEX IF NOT EXISTS idx_metricas_start_time ON metricas_scraping(start_time DESC);
CREATE INDEX IF NOT EXISTS idx_metricas_created_at ON metricas_scraping(created_at DESC);

-- =====================================================================
-- TABLA: alertas
-- =====================================================================
-- Almacena alertas generadas durante el scraping
-- Para monitoreo y troubleshooting
-- =====================================================================

CREATE TABLE IF NOT EXISTS alertas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Relación con ejecución de scraping
    metrica_id INTEGER,

    -- Timestamp
    timestamp TEXT NOT NULL,  -- ISO 8601

    -- Tipo y severidad
    level TEXT NOT NULL,  -- INFO, WARNING, ERROR, CRITICAL
    type TEXT NOT NULL,   -- scraping, validation, circuit_breaker, rate_limiter, etc.
    message TEXT NOT NULL,

    -- Contexto adicional (JSON string)
    context TEXT,

    -- Metadata
    created_at TEXT NOT NULL DEFAULT (datetime('now')),

    -- Foreign key
    FOREIGN KEY (metrica_id) REFERENCES metricas_scraping(id) ON DELETE CASCADE
);

-- Índices
CREATE INDEX IF NOT EXISTS idx_alertas_metrica_id ON alertas(metrica_id);
CREATE INDEX IF NOT EXISTS idx_alertas_timestamp ON alertas(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_alertas_level ON alertas(level);
CREATE INDEX IF NOT EXISTS idx_alertas_created_at ON alertas(created_at DESC);

-- =====================================================================
-- TABLA: circuit_breaker_stats
-- =====================================================================
-- Almacena estadísticas del circuit breaker por ejecución
-- =====================================================================

CREATE TABLE IF NOT EXISTS circuit_breaker_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Relación con ejecución de scraping
    metrica_id INTEGER,

    -- Estadísticas
    state TEXT NOT NULL,  -- closed, open, half_open
    consecutive_failures INTEGER NOT NULL DEFAULT 0,
    consecutive_successes INTEGER NOT NULL DEFAULT 0,
    total_calls INTEGER NOT NULL DEFAULT 0,
    total_successes INTEGER NOT NULL DEFAULT 0,
    total_failures INTEGER NOT NULL DEFAULT 0,
    total_rejected INTEGER NOT NULL DEFAULT 0,
    success_rate REAL,
    times_opened INTEGER NOT NULL DEFAULT 0,
    time_in_state_seconds REAL,

    -- Metadata
    created_at TEXT NOT NULL DEFAULT (datetime('now')),

    -- Foreign key
    FOREIGN KEY (metrica_id) REFERENCES metricas_scraping(id) ON DELETE CASCADE
);

-- Índices
CREATE INDEX IF NOT EXISTS idx_cb_stats_metrica_id ON circuit_breaker_stats(metrica_id);
CREATE INDEX IF NOT EXISTS idx_cb_stats_state ON circuit_breaker_stats(state);

-- =====================================================================
-- TABLA: rate_limiter_stats
-- =====================================================================
-- Almacena estadísticas del rate limiter adaptativo por ejecución
-- =====================================================================

CREATE TABLE IF NOT EXISTS rate_limiter_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Relación con ejecución de scraping
    metrica_id INTEGER,

    -- Estadísticas
    current_delay REAL NOT NULL,  -- Segundos
    min_delay REAL NOT NULL,
    max_delay REAL NOT NULL,
    total_requests INTEGER NOT NULL DEFAULT 0,
    total_success INTEGER NOT NULL DEFAULT 0,
    total_errors INTEGER NOT NULL DEFAULT 0,
    total_rate_limits INTEGER NOT NULL DEFAULT 0,  -- 429s
    success_rate REAL,
    consecutive_success INTEGER NOT NULL DEFAULT 0,
    consecutive_errors INTEGER NOT NULL DEFAULT 0,

    -- Historial de delays (JSON array como string)
    delay_history TEXT,

    -- Metadata
    created_at TEXT NOT NULL DEFAULT (datetime('now')),

    -- Foreign key
    FOREIGN KEY (metrica_id) REFERENCES metricas_scraping(id) ON DELETE CASCADE
);

-- Índices
CREATE INDEX IF NOT EXISTS idx_rl_stats_metrica_id ON rate_limiter_stats(metrica_id);

-- =====================================================================
-- VISTAS ÚTILES
-- =====================================================================

-- Vista: Últimas 10 ejecuciones con resumen
CREATE VIEW IF NOT EXISTS v_ultimas_ejecuciones AS
SELECT
    m.id,
    m.start_time,
    m.end_time,
    m.total_time_seconds,
    m.pages_scraped,
    m.pages_failed,
    m.success_rate,
    m.offers_total,
    m.offers_new,
    m.offers_per_second,
    m.validation_rate_avg,
    m.errors_count,
    m.warnings_count,
    COUNT(a.id) as alertas_count
FROM metricas_scraping m
LEFT JOIN alertas a ON m.id = a.metrica_id
GROUP BY m.id
ORDER BY m.start_time DESC
LIMIT 10;

-- Vista: Ofertas recientes (últimas 100)
CREATE VIEW IF NOT EXISTS v_ofertas_recientes AS
SELECT
    id_oferta,
    titulo,
    empresa,
    localizacion,
    fecha_publicacion_iso,
    scrapeado_en
FROM ofertas
ORDER BY scrapeado_en DESC
LIMIT 100;

-- Vista: Alertas críticas recientes
CREATE VIEW IF NOT EXISTS v_alertas_criticas AS
SELECT
    a.timestamp,
    a.level,
    a.type,
    a.message,
    m.start_time as scraping_start
FROM alertas a
JOIN metricas_scraping m ON a.metrica_id = m.id
WHERE a.level IN ('ERROR', 'CRITICAL')
ORDER BY a.timestamp DESC
LIMIT 50;

-- =====================================================================
-- FIN
-- =====================================================================
