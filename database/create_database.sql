-- =====================================================================
-- BASE DE DATOS: Bumeran Scraping - Producción
-- =====================================================================
--
-- Schemas:
--   1. ofertas: Ofertas scrapeadas de Bumeran
--   2. metricas_scraping: Métricas de performance de cada ejecución
--   3. alertas: Alertas generadas durante scraping
--
-- Uso:
--   psql -U postgres -f create_database.sql
-- =====================================================================

-- Crear base de datos
CREATE DATABASE bumeran_scraping
    WITH
    ENCODING = 'UTF8'
    LC_COLLATE = 'Spanish_Argentina.1252'
    LC_CTYPE = 'Spanish_Argentina.1252'
    TEMPLATE = template0;

-- Conectar a la base de datos
\c bumeran_scraping

-- =====================================================================
-- TABLA: ofertas
-- =====================================================================
-- Almacena todas las ofertas laborales scrapeadas de Bumeran
-- Incluye todas las columnas de Fase 1+2+3 (38 columnas)
-- =====================================================================

CREATE TABLE ofertas (
    -- IDs
    id_oferta BIGINT PRIMARY KEY,
    id_empresa BIGINT,

    -- Información básica
    titulo TEXT NOT NULL,
    empresa TEXT,
    descripcion TEXT,
    confidencial BOOLEAN,

    -- Ubicación y modalidad
    localizacion TEXT,
    modalidad_trabajo TEXT,
    tipo_trabajo TEXT,

    -- Fechas (formato original DD-MM-YYYY)
    fecha_publicacion_original TEXT,
    fecha_hora_publicacion_original TEXT,
    fecha_modificado_original TEXT,

    -- Fechas ISO 8601 (para ordenamiento y filtrado)
    fecha_publicacion_iso DATE,
    fecha_hora_publicacion_iso TIMESTAMP,
    fecha_modificado_iso DATE,

    -- Fechas datetime con timezone Argentina (UTC-3)
    fecha_publicacion_datetime TIMESTAMP WITH TIME ZONE,
    fecha_hora_publicacion_datetime TIMESTAMP WITH TIME ZONE,
    fecha_modificado_datetime TIMESTAMP WITH TIME ZONE,

    -- Detalles
    cantidad_vacantes INTEGER,
    apto_discapacitado BOOLEAN,

    -- Categorización
    id_area INTEGER,
    id_subarea INTEGER,
    id_pais INTEGER,

    -- Empresa
    logo_url TEXT,
    empresa_validada BOOLEAN,
    empresa_pro BOOLEAN,
    promedio_empresa DECIMAL(3,2),

    -- Plan de publicación
    plan_publicacion_id INTEGER,
    plan_publicacion_nombre TEXT,

    -- Otros
    portal TEXT,
    tipo_aviso TEXT,
    tiene_preguntas BOOLEAN,
    salario_obligatorio BOOLEAN,
    alta_revision_perfiles BOOLEAN,
    guardado BOOLEAN,
    gptw_url TEXT,

    -- Metadata
    url_oferta TEXT,
    scrapeado_en TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

    -- Índices para performance
    CONSTRAINT ofertas_id_oferta_unique UNIQUE (id_oferta)
);

-- Índices para queries comunes
CREATE INDEX idx_ofertas_fecha_pub_iso ON ofertas(fecha_publicacion_iso DESC);
CREATE INDEX idx_ofertas_empresa ON ofertas(empresa);
CREATE INDEX idx_ofertas_localizacion ON ofertas(localizacion);
CREATE INDEX idx_ofertas_scrapeado_en ON ofertas(scrapeado_en DESC);
CREATE INDEX idx_ofertas_id_area ON ofertas(id_area);

-- Comentarios
COMMENT ON TABLE ofertas IS 'Ofertas laborales scrapeadas de Bumeran.com.ar';
COMMENT ON COLUMN ofertas.id_oferta IS 'ID único de la oferta en Bumeran';
COMMENT ON COLUMN ofertas.fecha_publicacion_iso IS 'Fecha de publicación en formato ISO 8601 (YYYY-MM-DD)';
COMMENT ON COLUMN ofertas.scrapeado_en IS 'Timestamp de cuándo fue scrapeada esta oferta';

-- =====================================================================
-- TABLA: metricas_scraping
-- =====================================================================
-- Almacena métricas de performance de cada ejecución de scraping
-- Permite análisis histórico y detección de degradación
-- =====================================================================

CREATE TABLE metricas_scraping (
    id SERIAL PRIMARY KEY,

    -- Tiempos
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE NOT NULL,
    total_time_seconds DECIMAL(10,2) NOT NULL,

    -- Páginas
    pages_scraped INTEGER NOT NULL DEFAULT 0,
    pages_failed INTEGER NOT NULL DEFAULT 0,
    pages_total INTEGER NOT NULL DEFAULT 0,
    success_rate DECIMAL(5,2),  -- Porcentaje (0-100)
    avg_time_per_page DECIMAL(10,2),  -- Segundos

    -- Ofertas
    offers_total INTEGER NOT NULL DEFAULT 0,
    offers_new INTEGER NOT NULL DEFAULT 0,
    offers_duplicates INTEGER NOT NULL DEFAULT 0,
    offers_per_second DECIMAL(10,2),

    -- Validación
    validation_rate_avg DECIMAL(5,2),  -- Porcentaje (0-100)
    validation_rate_min DECIMAL(5,2),
    validation_rate_max DECIMAL(5,2),

    -- Errores
    errors_count INTEGER NOT NULL DEFAULT 0,
    warnings_count INTEGER NOT NULL DEFAULT 0,

    -- Metadata
    incremental_mode BOOLEAN NOT NULL DEFAULT TRUE,
    query TEXT,  -- Query de búsqueda si se usó

    -- Timestamp de inserción
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Índices
CREATE INDEX idx_metricas_start_time ON metricas_scraping(start_time DESC);
CREATE INDEX idx_metricas_created_at ON metricas_scraping(created_at DESC);

-- Comentarios
COMMENT ON TABLE metricas_scraping IS 'Métricas de performance de cada ejecución de scraping';
COMMENT ON COLUMN metricas_scraping.success_rate IS 'Tasa de éxito de páginas (%)';
COMMENT ON COLUMN metricas_scraping.offers_per_second IS 'Velocidad de scraping';

-- =====================================================================
-- TABLA: alertas
-- =====================================================================
-- Almacena alertas generadas durante el scraping
-- Para monitoreo y troubleshooting
-- =====================================================================

CREATE TABLE alertas (
    id SERIAL PRIMARY KEY,

    -- Relación con ejecución de scraping
    metrica_id INTEGER REFERENCES metricas_scraping(id) ON DELETE CASCADE,

    -- Timestamp
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,

    -- Tipo y severidad
    level VARCHAR(20) NOT NULL,  -- INFO, WARNING, ERROR, CRITICAL
    type VARCHAR(50) NOT NULL,   -- scraping, validation, circuit_breaker, rate_limiter, etc.
    message TEXT NOT NULL,

    -- Contexto adicional (JSON)
    context JSONB,

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Índices
CREATE INDEX idx_alertas_metrica_id ON alertas(metrica_id);
CREATE INDEX idx_alertas_timestamp ON alertas(timestamp DESC);
CREATE INDEX idx_alertas_level ON alertas(level);
CREATE INDEX idx_alertas_created_at ON alertas(created_at DESC);

-- Comentarios
COMMENT ON TABLE alertas IS 'Alertas generadas durante scraping para monitoreo';
COMMENT ON COLUMN alertas.level IS 'Severidad: INFO, WARNING, ERROR, CRITICAL';
COMMENT ON COLUMN alertas.context IS 'Información adicional en formato JSON';

-- =====================================================================
-- TABLA: circuit_breaker_stats
-- =====================================================================
-- Almacena estadísticas del circuit breaker por ejecución
-- =====================================================================

CREATE TABLE circuit_breaker_stats (
    id SERIAL PRIMARY KEY,

    -- Relación con ejecución de scraping
    metrica_id INTEGER REFERENCES metricas_scraping(id) ON DELETE CASCADE,

    -- Estadísticas
    state VARCHAR(20) NOT NULL,  -- closed, open, half_open
    consecutive_failures INTEGER NOT NULL DEFAULT 0,
    consecutive_successes INTEGER NOT NULL DEFAULT 0,
    total_calls INTEGER NOT NULL DEFAULT 0,
    total_successes INTEGER NOT NULL DEFAULT 0,
    total_failures INTEGER NOT NULL DEFAULT 0,
    total_rejected INTEGER NOT NULL DEFAULT 0,
    success_rate DECIMAL(5,2),
    times_opened INTEGER NOT NULL DEFAULT 0,
    time_in_state_seconds DECIMAL(10,2),

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Índices
CREATE INDEX idx_cb_stats_metrica_id ON circuit_breaker_stats(metrica_id);
CREATE INDEX idx_cb_stats_state ON circuit_breaker_stats(state);

-- Comentarios
COMMENT ON TABLE circuit_breaker_stats IS 'Estadísticas del circuit breaker por ejecución';

-- =====================================================================
-- TABLA: rate_limiter_stats
-- =====================================================================
-- Almacena estadísticas del rate limiter adaptativo por ejecución
-- =====================================================================

CREATE TABLE rate_limiter_stats (
    id SERIAL PRIMARY KEY,

    -- Relación con ejecución de scraping
    metrica_id INTEGER REFERENCES metricas_scraping(id) ON DELETE CASCADE,

    -- Estadísticas
    current_delay DECIMAL(5,2) NOT NULL,  -- Segundos
    min_delay DECIMAL(5,2) NOT NULL,
    max_delay DECIMAL(5,2) NOT NULL,
    total_requests INTEGER NOT NULL DEFAULT 0,
    total_success INTEGER NOT NULL DEFAULT 0,
    total_errors INTEGER NOT NULL DEFAULT 0,
    total_rate_limits INTEGER NOT NULL DEFAULT 0,  -- 429s
    success_rate DECIMAL(5,2),
    consecutive_success INTEGER NOT NULL DEFAULT 0,
    consecutive_errors INTEGER NOT NULL DEFAULT 0,

    -- Historial de delays (array de últimos 10 delays)
    delay_history DECIMAL(5,2)[],

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Índices
CREATE INDEX idx_rl_stats_metrica_id ON rate_limiter_stats(metrica_id);

-- Comentarios
COMMENT ON TABLE rate_limiter_stats IS 'Estadísticas del rate limiter adaptativo por ejecución';

-- =====================================================================
-- VISTAS ÚTILES
-- =====================================================================

-- Vista: Últimas 10 ejecuciones con resumen
CREATE VIEW v_ultimas_ejecuciones AS
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
CREATE VIEW v_ofertas_recientes AS
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
CREATE VIEW v_alertas_criticas AS
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
-- GRANTS (Ajustar según tu usuario PostgreSQL)
-- =====================================================================

-- Crear usuario para la aplicación (opcional)
-- CREATE USER bumeran_app WITH PASSWORD 'tu_password_seguro';

-- Dar permisos (descomentar y ajustar usuario si es necesario)
-- GRANT CONNECT ON DATABASE bumeran_scraping TO bumeran_app;
-- GRANT USAGE ON SCHEMA public TO bumeran_app;
-- GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO bumeran_app;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO bumeran_app;

-- =====================================================================
-- FIN
-- =====================================================================

-- Verificar tablas creadas
SELECT
    table_name,
    table_type
FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY table_name;

-- Mensaje de éxito
\echo '✅ Base de datos creada exitosamente!'
\echo 'Tablas: ofertas, metricas_scraping, alertas, circuit_breaker_stats, rate_limiter_stats'
\echo 'Vistas: v_ultimas_ejecuciones, v_ofertas_recientes, v_alertas_criticas'
