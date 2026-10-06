# DOCTRINA — corridas largas sobre el main DB (ops)

> Lección generalizada del incidente del lock en la cascada v12.4 (d01 murió a las
> 5.199/15.000 con `database is locked`). Aplica a TODA corrida larga futura (re-extracción,
> re-matching, backfills, cualquier job de horas/días que toque `bumeran_scraping.db`).

## El problema
`database/bumeran_scraping.db` tiene **escritores continuos** que no se detienen solos:
- `scripts/pipeline_command_poller.py` — **cron cada minuto**.
- `scripts/auto_sync.sh` — cron horario.
- `scripts/sync_scraping_dinamica.py` / `sync_from_vps.py` — sync manual/programado.
- scraping crons (`run_indeed_headed` 0/3h, `run_portalempleo_vps` 6:15, `verificador_bajas` 7:00).

Un job largo que ESCRIBE el main compite con ellos por el lock de escritura de SQLite. Aunque
esté en WAL (un solo escritor a la vez), un lock sostenido supera cualquier `busy_timeout`
razonable y **tira el proceso** con `OperationalError: database is locked`. En un run de días,
esto es cuestión de tiempo.

## La doctrina — "staging en DB propia + main read-only"
Para cualquier corrida larga que PRODUZCA datos derivados:
1. **Escribí a una DB propia del job** (ej. `database/<job>_staging.db`), nunca al main en
   caliente. Solo tu proceso la toca → cero contención.
2. **Leé el main en modo read-only**: `sqlite3.connect('file:...bumeran_scraping.db?mode=ro', uri=True)`
   o `ATTACH DATABASE 'file:...?mode=ro' AS src`. Los lectores WAL **nunca** bloquean ni son
   bloqueados por el escritor.
3. **Hacé el job resumible**: PK en la tabla de staging + `WHERE id NOT IN (staging)` →
   relanzar continúa donde quedó. Un lock/corte no cuesta trabajo, solo un relaunch.
4. **`busy_timeout` alto** (120s) como cinturón, aunque con la DB propia no haga falta.
5. **El merge staging → main es un paso APARTE y coordinado**: ventana muerta con los
   escritores pausados (parar el poller, evitar las horas de cron), transacción por lotes,
   backup/snapshot como rollback. Nunca mezclar "producir" con "escribir el main".

## Patrón de referencia
`scripts/ops/reextraccion_tareas_v124.py` (cascada v12.4): `_conectar()` abre la staging DB
propia + ATTACH del main RO; candidatos por `src.*` excluyendo el staging local; writes solo
al staging. Ver también `scripts/ops/run_con_tmpfs.sh` para jobs I/O-heavy (NLP de 20 campos),
donde además conviene la BD en tmpfs + sync-back (lección del frente D).

## Regla corta
**Producir ≠ escribir el main.** Producí en lo tuyo, leé el main RO, mergeá en ventana muerta.
