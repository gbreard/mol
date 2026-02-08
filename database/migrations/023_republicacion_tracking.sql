-- ============================================================
-- MIGRACIÓN 023: Sistema de detección de republicaciones
-- ============================================================
-- Fecha: 2026-02-07
-- Descripción: Detecta ofertas republicadas (mismo titulo+empresa,
--   distinto id_oferta) como indicador de demanda insatisfecha.
--
-- Columnas nuevas en ofertas:
--   - grupo_republicacion: hash del grupo (titulo_norm + id_empresa)
--   - es_republicacion: 0=primera publicación, 1=republicación
--   - numero_republicacion: N-ésima vez que se publica (1, 2, 3...)
--   - id_oferta_original: FK a la primera publicación del grupo
--
-- Vista analítica: v_republicaciones_resumen
-- ============================================================

-- Columnas de tracking en ofertas
ALTER TABLE ofertas ADD COLUMN grupo_republicacion TEXT;
ALTER TABLE ofertas ADD COLUMN es_republicacion INTEGER DEFAULT 0;
ALTER TABLE ofertas ADD COLUMN numero_republicacion INTEGER;
ALTER TABLE ofertas ADD COLUMN id_oferta_original INTEGER;

-- Índices para queries de republicaciones
CREATE INDEX IF NOT EXISTS idx_ofertas_grupo_repub
    ON ofertas(grupo_republicacion) WHERE grupo_republicacion IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_ofertas_es_repub
    ON ofertas(es_republicacion) WHERE es_republicacion = 1;

-- Compuesto: para agrupar y ordenar dentro del grupo
CREATE INDEX IF NOT EXISTS idx_ofertas_grupo_fecha
    ON ofertas(grupo_republicacion, fecha_publicacion_iso)
    WHERE grupo_republicacion IS NOT NULL;

-- Vista: resumen de grupos republicados
CREATE VIEW IF NOT EXISTS v_republicaciones_resumen AS
SELECT
    grupo_republicacion,
    MIN(titulo) AS titulo,
    MIN(empresa) AS empresa,
    COUNT(*) AS veces_publicada,
    MIN(fecha_publicacion_iso) AS primera_publicacion,
    MAX(fecha_publicacion_iso) AS ultima_publicacion,
    CAST(
        julianday(MAX(fecha_publicacion_iso)) -
        julianday(MIN(fecha_publicacion_iso))
    AS INTEGER) AS dias_persistencia,
    SUM(CASE WHEN estado_oferta = 'activa' THEN 1 ELSE 0 END) AS activas_ahora,
    SUM(CASE WHEN estado_oferta = 'baja' THEN 1 ELSE 0 END) AS dadas_de_baja,
    GROUP_CONCAT(id_oferta, ',') AS ids_ofertas
FROM ofertas
WHERE grupo_republicacion IS NOT NULL
GROUP BY grupo_republicacion
HAVING COUNT(*) > 1
ORDER BY veces_publicada DESC;

-- Vista: top puestos difíciles de cubrir (republicados 3+ veces)
CREATE VIEW IF NOT EXISTS v_puestos_dificiles_cubrir AS
SELECT
    grupo_republicacion,
    MIN(titulo) AS titulo,
    MIN(empresa) AS empresa,
    COUNT(*) AS veces_publicada,
    CAST(
        julianday(MAX(fecha_publicacion_iso)) -
        julianday(MIN(fecha_publicacion_iso))
    AS INTEGER) AS dias_sin_cubrir,
    SUM(cantidad_vacantes) AS vacantes_totales_acumuladas
FROM ofertas
WHERE grupo_republicacion IS NOT NULL
GROUP BY grupo_republicacion
HAVING COUNT(*) >= 3
ORDER BY veces_publicada DESC, dias_sin_cubrir DESC;
