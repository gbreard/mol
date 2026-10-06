# [CASCADA v12.4] Diseño del SWAP staging → tabla viva (gate P3 → P4)

> Anotado durante P1 (post-incidente del lock de d01). **Leer esto ANTES de ejecutar el swap.**
> El swap es el único momento en que el main DB se ESCRIBE con las tareas v12.4. Ocurre
> recién con el **gate P3 aprobado**, justo antes del P4 (re-matching). Hasta entonces todo
> vive en `database/cascada_staging.db` y la tabla viva sigue en tareas v11.

## Qué hace el swap
Migrar `cascada_staging.db:ofertas_nlp_tareas_v124` → `bumeran_scraping.db:ofertas_nlp.tareas_explicitas`
(y los campos de tracking de época/versión), para las ~98K ofertas re-extraídas.

## ⚠ REQUISITO DURO — ventana de escritores pausados (lección del lock de d01)
El main DB tiene **escritores continuos** que durante P1 nos tiraron el runner con
`database is locked`. Para el swap (que SÍ escribe el main) hay que **coordinar una ventana
muerta** — minutos, no horas, pero **coordinado, no optimista**:

| Escritor | Origen | Acción antes del swap |
|---|---|---|
| `sync_scraping_dinamica.py` | manual / sync | que NO esté corriendo |
| `pipeline_command_poller.py` | **cron cada minuto** | pausar el cron durante la ventana |
| `auto_sync.sh` | cron horario (min 0) | evitar la hora en punto |
| scraping (`run_indeed_headed`, `run_portalempleo_vps`, `verificador_bajas`) | crons 0/3h, 6:15, 7:00 | elegir ventana fuera de esos horarios |

Checklist del swap:
1. Elegir ventana fuera de los crons (ni :00 horario, ni 0/3h, ni 6:15, ni 7:00).
2. Pausar el `pipeline_command_poller` (comentar la línea del crontab o parar el loop) y
   confirmar que no hay `sync_scraping_dinamica` activo (`pgrep -af`).
3. **Backup rápido** de `ofertas_nlp` (ya cubierto por el snapshot `tareas_v11` de P0 — es el
   rollback). Verificar el sha256 del snapshot antes de tocar.
4. Swap en una transacción por lotes (UPDATE ofertas_nlp SET tareas_explicitas=?,
   nlp_version='12.4-tareas', tareas_epoca='tareas_v124' WHERE id_oferta=?), `busy_timeout` alto.
5. Verificación post-swap: conteo de filas actualizadas == censo de staging; muestra de 10
   leída; distribución n_tareas antes/después coincide con el P1-censo.
6. Re-activar el poller / crons.

## Rollback (gratis mientras no se haya hecho el swap)
Mientras el swap NO corrió, la tabla viva es v11 intacta → descartar es borrar
`cascada_staging.db`. Post-swap, el rollback es restaurar `tareas_explicitas` desde
`snapshot_pre_cascada_2026-10-05_tareas_v11.jsonl.gz`.

## Nota de época (laudo e)
Tras el swap, declarar en el DATA_RELEASE la época POR CAPA: **tareas v12.4 / skills v11
(ventana abierta hasta frente O) / matching 3.6.x-post-cascada**. La inconsistencia visible.
