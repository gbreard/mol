# Diagnóstico Bumeran — 6 días sin datos en local (21-10)

**Fecha:** 2026-10-21 · **Tipo:** read-only · **Estado:** veredicto + fix propuesto, NO aplicado.

## Veredicto en una línea
**No es falla de scraping.** El VPS scrapea bumeran sano todos los días (91 hoy). Es el **bug del "watermark robado"** (documentado 2026-06-30): un export en el VPS avanza el cursor global de sync sin que esos datos lleguen a local → bumeran, por ser el scraper más temprano, queda crónicamente varado. Es el **caso 2** que vos anticipaste: VPS con datos / local sin.

---

## 1. ¿Corrió? SÍ
- Cron del VPS intacto: `0 7 * * * run_scheduler.py --test` (bumeran diario) + `0 8 * * 1,4 run_scraping_vps.sh` (lun/jue).
- `logs/bumeran_daily.log`: última corrida **165 requests, 100% éxito, 0 errores, 0 rate-limits**. El scraper anda perfecto.

## 2. ¿Trajo datos? SÍ en el VPS, NO en local → desfase de sync
Bumeran por día (`scrapeado_en`):

| día | VPS | local |
|---|---:|---:|
| 10-15 | 82 | 82 ✅ |
| 10-16 | 44 | **0** ❌ |
| 10-17 | 78 | **0** ❌ |
| 10-18 | 18 | **0** ❌ |
| 10-19 | 83 | **0** ❌ |
| 10-20 | 73 | **0** ❌ |
| 10-21 | 91 | **0** ❌ |

VPS MAX = `2026-10-21T07:05`, local MAX = `2026-10-15T08:05`. **~387 ofertas bumeran varadas** (10-16→10-21). Comparación: zonajobs/CT/caba en local llegan a **10-19** (4 días más adelante que bumeran) — la pista clave.

## 3. El tracker incremental NO es el culpable
`bumeran_scraped_ids.json` (24.911 IDs) no descarta de más: el VPS inserta 91 ids nuevos hoy. El scraping y el dedup del VPS funcionan. El problema es 100% del transporte VPS→local.

## 4. ZonaJobs funciona → confirma que es runner/sync, no el portal
ZonaJobs (mismo backend Navent) llega a 10-19 en local. La API del grupo anda. Apunta al mecanismo de sync, no a bumeran como portal. ✔ Tu hipótesis.

---

## Causa raíz (mecanismo, probado con datos)

El watermark de sync vive en el VPS: `/opt/mol/data/sync_log.json` → `last_export`. Hoy vale **`2026-10-21T07:05:55`** = exactamente el MAX de bumeran de hoy. El export incremental filtra `scrapeado_en > last_export OR descripcion_actualizada_en > last_export`. Dry-run incremental hoy: **"No hay ofertas nuevas"** (el cursor ya está en el futuro de todo lo pendiente).

**Quién roba el watermark:** `scripts/vps_command_poller.py` (proceso vivo, pid 684) ejecuta `export_nuevas.py` (líneas 165 y 190) tras cada corrida. Ese export **avanza el `last_export` global** y escribe su dump en el VPS, pero **no se envía ni importa a local**. El cursor es el MISMO que usa el sync real (`sync_from_vps.py`). Resultado: el poller "consume" el incremento (marca las filas como exportadas) sin que lleguen a local.

Es idéntico al bug que se tapó en `run_scraping_vps.sh` **Paso 7 (DESACTIVADO 2026-06-30)** — el comentario ahí lo describe palabra por palabra. Se desactivó en el `.sh` pero **quedó vivo por el poller**.

**Por qué bumeran y no los demás:** bumeran es el scraper más temprano (07:05). El export del poller avanza el watermark a esa hora cada día; como el sync local corre después (o días después, último real 10-19T14:00), al momento del sync el watermark ya pasó las filas de bumeran de la mañana → se excluyen. ZonaJobs/CT corren más tarde (lun/jue 08:16–10:50), por encima del watermark de la mañana, así que alcanzan a colarse en el sync local siguiente. Bumeran, estructuralmente, nunca está por encima del cursor cuando el sync corre.

---

## 5. Fix propuesto (NO aplicado — decidís vos)

**Parte A — Cerrar el robo de watermark (el dueño del cursor es el sync local y nadie más):**
Alinear con la decisión de 2026-06-30 ("el cron/local es el dueño"). Opciones, de menor a mayor cambio:
1. **Neutralizar el export del poller:** quitar/condicionar las llamadas a `export_nuevas.py` en `vps_command_poller.py` (líneas 165, 190) si su salida no se consume. Es lo más directo y lo más consistente con el Paso 7 ya desactivado.
2. **Aislar el cursor:** que el export del poller use un watermark propio (archivo separado), sin tocar `data/sync_log.json`.
3. **Export sin avance:** que el poller use la variante que NO toca el watermark (la misma salvaguarda que ya tiene `--portal`, comentada *"backfill, no toca watermark"*).

Recomendada: **A.1** (quitar el export del poller) — el único proceso que debe mover `last_export` es `sync_from_vps.py`, que es el que realmente importa a local.

**Parte B — Recuperar lo varado (one-time, quirúrgico, NO `--full`):**
Backfill por portal, que por diseño **no toca el watermark** (regla ya aprendida):
```bash
# 1. dry-run primero (SIEMPRE)
ssh root@187.124.150.28 'cd /opt/mol && python3 scripts/export_nuevas.py --portal bumeran --since 2026-10-15 --dry-run'
# 2. confirmar ~387 filas → correr real, scp, import local (INSERT OR IGNORE)
```
Esto trae bumeran 10-16→10-21 sin re-exportar los 133k ni mover el cursor. (Chequear de paso si zonajobs/CT/caba tienen algo >10-19 también.)

**Orden sugerido:** B primero (recuperar datos ya), luego A (que no vuelva a pasar). Si se aplica A sin B, los 387 ya varados igual no vuelven solos.

---

## Nota
El watermark global compartido es frágil por diseño (un solo cursor para N portales con horarios distintos + múltiples escritores). El fix de arriba lo parcha; el rediseño real (watermark por portal, o export idempotente desacoplado del import) sería un issue aparte si se quiere robustez. **PAUSA — decisión de Gerardo.**
