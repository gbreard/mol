# Issue: `sistema_estado` congelado desde 2026-07-25 (deuda del monitor)

**Fecha:** 2026-09-01
**Detectado en:** frente `fix/monitor-scraping-fuente-local` (diagnóstico del monitor de scraping)
**Severidad:** media — desinforma la RPC `get_scraping_stats`; NO bloquea el fix del monitor (que pasó a leer `scraping_live_stats` recalculada desde la BD local).

## Hallazgo

La tabla Supabase `sistema_estado` no se actualiza desde **2026-07-25**. El registro más reciente:

```
ts: 2026-07-25T18:11:59
fase1_fuentes: { indeed: 790, bumeran: 546, zonajobs: 615, computrabajo: 1268, portalempleo: 12 }
fase1_ultimo_scraping: 2026-07-25
```

Problemas que causa:
1. **`get_scraping_stats()`** (`fase3_dashboard/sql/021_rpc_scraping_stats.sql`) arma su lista de portales y totales desde `sistema_estado.fase1_fuentes`. Al estar congelada:
   - Los `total` por portal de la RPC son de julio.
   - **CABA no aparece** en `fase1_fuentes` → la RPC no emite fila para caba → `procesadas/en_dashboard = 0` en el panel (uno de los síntomas del "CABA 0 en Dashboard").
2. Las **alertas de la RPC** `get_scraping_stats.v_alertas` que dependen de `sistema_estado` ("Scraping general sin ejecutar hace N días", "N ofertas sin procesar") saldrían con números de julio → **por eso el monitor NO renderiza `d.alertas`** y las alertas se calculan client-side (ver `lib/scraping-alerts.ts`).

## Deuda asociada (reuso no aplicado)

La sub-alerta **"scrapeado pero trajo 0"** de la RPC (`021_rpc_scraping_stats.sql:123-144`) SÍ es sana: lee `scraping_daily` (local, fresco), **no** `fase1_fuentes`. Es reutilizable. No se reusó en este frente porque:
- viene mezclada en el mismo array `v_alertas` con las alertas dependientes de `sistema_estado` (stale), y
- no cubre el caso "CABA goteo: 3 corridas seguidas en cero" que sí pide el monitor.
Cuando se arregle `sistema_estado`, evaluar mover toda la lógica de alertas a la RPC (server-side) y que el frontend solo renderice `d.alertas`.

## Causa raíz (a investigar)

`sistema_estado` lo escriben `scripts/exports/sync_to_supabase.py` y `scripts/sync_learnings.py`. Verificar por qué dejaron de actualizarlo el 2026-07-25 (¿excepción silenciosa? ¿rama del código que dejó de llamarse? ¿esquema cambiado?). Confirmar que `fase1_fuentes` se pueble desde la BD local con los **6** portales (incl. caba).

## Fuera de alcance de este frente

El monitor ya no depende de `sistema_estado` para lo crítico (usa `scraping_live_stats` recalculada local, fuente de verdad). Este issue queda para un frente propio de `sync_to_supabase`/`sistema_estado`.
