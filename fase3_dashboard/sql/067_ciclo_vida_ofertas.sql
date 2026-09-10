-- 067_ciclo_vida_ofertas.sql
-- Fase 5 (B.1) — columnas del ciclo de vida de ofertas en ofertas_dashboard,
-- + la columna de frescura del sync en scraping_live_stats.
--
-- CONTEXTO
-- El sistema declaraba baja a toda oferta no vista en la ultima corrida: 111K
-- "bajas" que eran artefacto del muestreo (el scraping de Bumeran es rotativo,
-- 165 de 1.148 keywords por dia). El motor de ciclo de vida en sombra ya midio
-- 17.176 falsas bajas del legacy. Estas columnas son lo que el dashboard y la
-- API de OE van a leer en la Etapa C, en lugar de `estado`.
--
-- IDEMPOTENTE: se puede correr dos veces sin error (IF NOT EXISTS en todo).
-- ADITIVO: no toca ninguna columna existente. `estado` (legacy) sigue igual y
-- se mantiene en dual-write una semana mas como rollback.
--
-- APLICAR: Supabase Dashboard -> SQL Editor -> pegar y ejecutar.
-- (El MCP de Supabase de esta sesion solo expone authenticate/complete_auth,
--  sin execute_sql ni apply_migration, asi que el DDL va por esta via.)

-- ---------------------------------------------------------------------------
-- 1. ofertas_dashboard: 5 columnas del ciclo de vida
-- ---------------------------------------------------------------------------

-- Estado del ciclo de vida. Valores del motor:
--   activa | presunta_baja | baja_confirmada | baja_no_verificada | baja_inferida
-- NULL = todavia no calculado (filas viejas hasta el backfill de B.4).
ALTER TABLE ofertas_dashboard
  ADD COLUMN IF NOT EXISTS estado_ciclo TEXT;

-- Fecha estimada de baja, para indicadores de duracion/vida media.
-- Solo tiene sentido con estado_ciclo='baja_confirmada'; en los demas es NULL.
ALTER TABLE ofertas_dashboard
  ADD COLUMN IF NOT EXISTS fecha_baja_estimada TIMESTAMPTZ;

-- Intervalo de confianza de esa fecha: la baja ocurrio en algun punto entre la
-- ultima vez que se vio la oferta y la verificacion que la confirmo caida.
ALTER TABLE ofertas_dashboard
  ADD COLUMN IF NOT EXISTS fecha_baja_intervalo_desde TIMESTAMPTZ;

ALTER TABLE ofertas_dashboard
  ADD COLUMN IF NOT EXISTS fecha_baja_intervalo_hasta TIMESTAMPTZ;

-- Ancho del intervalo en dias. Es el dato que permite ponderar o descartar una
-- baja en un indicador: una con incertidumbre de 40 dias no vale lo mismo que
-- una de 2. Se publica junto a la fecha, nunca la fecha sola.
ALTER TABLE ofertas_dashboard
  ADD COLUMN IF NOT EXISTS fecha_baja_incertidumbre_dias INTEGER;

-- Agrupador de la MISMA vacante publicada en varios portales. Todavia sin
-- poblar: la fuente inicial son las colisiones de id de backend Navent
-- (colisiones_id.accion='reemplazo_evitado'), que son pares confirmados sin
-- heuristica. Ver exports/reportes/medicion_duplicacion_crossportal.md.
ALTER TABLE ofertas_dashboard
  ADD COLUMN IF NOT EXISTS grupo_oferta_id TEXT;

-- ---------------------------------------------------------------------------
-- 2. scraping_live_stats: frescura del sync
-- ---------------------------------------------------------------------------
-- El monitor vigilaba la cadencia de los PORTALES pero no la del sync que
-- alimenta al propio dashboard: ofertas_dashboard estuvo 2 semanas sin
-- actualizarse y nada lo senalo. sync_scraping_stats.py ya publica aca
-- {ultima_sync, horas_desde, umbral_horas: 26, alerta}; hasta que exista la
-- columna, el upsert la omite con fallback y la alerta solo va al log.
ALTER TABLE scraping_live_stats
  ADD COLUMN IF NOT EXISTS sync_supabase JSONB;

-- ---------------------------------------------------------------------------
-- 3. Indices
-- ---------------------------------------------------------------------------
-- El filtro de la API de OE y de los conteos del panel es estado_ciclo.
CREATE INDEX IF NOT EXISTS idx_ofertas_dashboard_estado_ciclo
  ON ofertas_dashboard (estado_ciclo);

-- Parcial: los indicadores de duracion solo miran las confirmadas.
CREATE INDEX IF NOT EXISTS idx_ofertas_dashboard_fecha_baja_estimada
  ON ofertas_dashboard (fecha_baja_estimada)
  WHERE fecha_baja_estimada IS NOT NULL;

-- Parcial: agrupar duplicados cross-portal sin pagar el indice completo
-- mientras la columna este mayormente vacia.
CREATE INDEX IF NOT EXISTS idx_ofertas_dashboard_grupo_oferta
  ON ofertas_dashboard (grupo_oferta_id)
  WHERE grupo_oferta_id IS NOT NULL;

-- ---------------------------------------------------------------------------
-- 4. Verificacion (correr despues; deben aparecer las 6 columnas)
-- ---------------------------------------------------------------------------
-- SELECT table_name, column_name, data_type
--   FROM information_schema.columns
--  WHERE (table_name = 'ofertas_dashboard'
--         AND column_name IN ('estado_ciclo','fecha_baja_estimada',
--              'fecha_baja_intervalo_desde','fecha_baja_intervalo_hasta',
--              'fecha_baja_incertidumbre_dias','grupo_oferta_id'))
--     OR (table_name = 'scraping_live_stats' AND column_name = 'sync_supabase')
--  ORDER BY table_name, column_name;
--
-- ROLLBACK (aditivo, se puede revertir sin perdida):
-- ALTER TABLE ofertas_dashboard DROP COLUMN IF EXISTS estado_ciclo, ...;
-- ALTER TABLE scraping_live_stats DROP COLUMN IF EXISTS sync_supabase;
