-- ============================================================
-- MIGRACIÓN: Agregar campos para tracking de permanencia
-- ============================================================
-- Fecha: 2025-12-06
-- Descripción: Agrega campos para detectar bajas y calcular permanencia
--
-- Campos nuevos:
--   - estado_oferta: 'activa', 'baja', 'expirada'
--   - fecha_ultimo_visto: Última vez que apareció en la API
--   - fecha_baja: Cuándo dejó de aparecer
--   - dias_publicada: Permanencia calculada (puede ser NULL si sigue activa)
--   - veces_vista: Contador de cuántas veces se vio en scraping
-- ============================================================

-- Agregar columnas nuevas
ALTER TABLE ofertas ADD COLUMN estado_oferta TEXT DEFAULT 'activa';
ALTER TABLE ofertas ADD COLUMN fecha_ultimo_visto TEXT;
ALTER TABLE ofertas ADD COLUMN fecha_baja TEXT;
ALTER TABLE ofertas ADD COLUMN dias_publicada INTEGER;
ALTER TABLE ofertas ADD COLUMN veces_vista INTEGER DEFAULT 1;
ALTER TABLE ofertas ADD COLUMN categoria_permanencia TEXT;

-- Índices para consultas de permanencia
CREATE INDEX IF NOT EXISTS idx_ofertas_estado ON ofertas(estado_oferta);
CREATE INDEX IF NOT EXISTS idx_ofertas_fecha_baja ON ofertas(fecha_baja);
CREATE INDEX IF NOT EXISTS idx_ofertas_fecha_ultimo_visto ON ofertas(fecha_ultimo_visto);
CREATE INDEX IF NOT EXISTS idx_ofertas_categoria_permanencia ON ofertas(categoria_permanencia);

-- Inicializar fecha_ultimo_visto con scrapeado_en para ofertas existentes
UPDATE ofertas
SET fecha_ultimo_visto = scrapeado_en
WHERE fecha_ultimo_visto IS NULL;

-- Vista para análisis de permanencia
CREATE VIEW IF NOT EXISTS v_permanencia_ofertas AS
SELECT
    id_oferta,
    titulo,
    empresa,
    fecha_publicacion_iso,
    fecha_ultimo_visto,
    fecha_baja,
    estado_oferta,
    dias_publicada,
    categoria_permanencia,
    veces_vista,
    CASE
        WHEN estado_oferta = 'activa' THEN
            CAST(julianday('now') - julianday(fecha_publicacion_iso) AS INTEGER)
        ELSE dias_publicada
    END as dias_publicada_actual
FROM ofertas
WHERE fecha_publicacion_iso IS NOT NULL;

-- Vista resumen de permanencia por categoría
CREATE VIEW IF NOT EXISTS v_permanencia_resumen AS
SELECT
    categoria_permanencia,
    estado_oferta,
    COUNT(*) as cantidad,
    AVG(dias_publicada) as promedio_dias,
    MIN(dias_publicada) as min_dias,
    MAX(dias_publicada) as max_dias
FROM ofertas
WHERE dias_publicada IS NOT NULL
GROUP BY categoria_permanencia, estado_oferta
ORDER BY categoria_permanencia, estado_oferta;
