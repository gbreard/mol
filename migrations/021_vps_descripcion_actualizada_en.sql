-- =============================================================================
-- Migration 021 — descripcion_actualizada_en + trigger (VPS)
-- Fecha: 2026-05-15
-- Aplicada en: VPS bumeran_scraping.db (NO local — local recibe via sync)
-- =============================================================================
--
-- CONTEXTO:
-- Bug de race condition en el sync VPS→local. El scraping VPS funciona en
-- 2 fases (listado + detalle). Fase 2 completa la descripción pero NO
-- actualiza scrapeado_en, dejando ofertas invisibles al sync incremental
-- subsiguiente (que filtraba por scrapeado_en > last_sync).
--
-- Síntoma: al 2026-05-15 había 2.054 ofertas en local con descripción NULL,
-- de las cuales 1.769 (CT) tenían descripción válida en VPS pero nunca
-- se sincronizaron.
--
-- SOLUCIÓN:
-- 1. Nueva columna descripcion_actualizada_en TIMESTAMP (TEXT).
-- 2. Trigger AFTER UPDATE OF descripcion que pobla la columna con
--    timestamp local en formato isoformat (compatible con last_sync de
--    sync_log.json escrito por Python datetime.now().isoformat()).
-- 3. export_nuevas.py modificado para incluir
--    OR descripcion_actualizada_en > last_sync en el WHERE incremental.
-- 4. Backfill histórico inicial con scrapeado_en para que el primer sync
--    incremental no arrastre toda la BD de golpe.
--
-- DETALLES DE FORMATO (importante para comparación lexicográfica):
-- - scrapeado_en (Python scrapers): 'YYYY-MM-DDTHH:MM:SS.ffffff' local time
-- - last_sync (Python sync_log):    'YYYY-MM-DDTHH:MM:SS.ffffff' local time
-- - Trigger (este archivo):         'YYYY-MM-DDTHH:MM:SS.fff000' local time
--   (SQLite strftime '%f' da 3 dígitos; padding con '000' → 6 dígitos
--    para igualar precisión de Python isoformat).
-- - 'now', 'localtime' fuerza timezone local en lugar del default UTC,
--   matching el TZ del VPS y de los scrapers Python.
--
-- VERIFICACIÓN:
-- Test integrado del 2026-05-15: 5/5 criterios PASS, comparación
-- lexicográfica funciona correctamente entre last_sync isoformat y
-- descripcion_actualizada_en del trigger.
--
-- =============================================================================

-- 1. Agregar columna
ALTER TABLE ofertas ADD COLUMN descripcion_actualizada_en TIMESTAMP DEFAULT NULL;

-- 2. Trigger (versión final con padding microsegundos + localtime)
DROP TRIGGER IF EXISTS trg_ofertas_descripcion_updated;

CREATE TRIGGER trg_ofertas_descripcion_updated
AFTER UPDATE OF descripcion ON ofertas
FOR EACH ROW
WHEN NEW.descripcion IS NOT OLD.descripcion
BEGIN
    UPDATE ofertas
    SET descripcion_actualizada_en = strftime('%Y-%m-%dT%H:%M:%f', 'now', 'localtime') || '000'
    WHERE id_oferta = NEW.id_oferta;
END;

-- 3. Backfill histórico: poblar columna con scrapeado_en (formato ya isoformat)
--    Solo ofertas con descripción real; las NULL/vacías quedan con NULL.
UPDATE ofertas
SET descripcion_actualizada_en = scrapeado_en
WHERE descripcion_actualizada_en IS NULL
  AND descripcion IS NOT NULL
  AND LENGTH(descripcion) > 0;

-- =============================================================================
-- CAMBIO COMPLEMENTARIO en /opt/mol/scripts/export_nuevas.py (VPS):
--
-- WHERE clauses del export incremental modificadas de:
--     'WHERE scrapeado_en > ?'
-- a:
--     'WHERE scrapeado_en > ? OR descripcion_actualizada_en > ?'
--
-- Y params duplicado: (last_sync,) → (last_sync, last_sync)
--
-- Backup del original en /opt/mol/scripts/export_nuevas.py.bak_pre_migration_*
-- =============================================================================
