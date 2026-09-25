# Rediseño del emisor de issues automáticos (prerequisito para re-activar)

**Fecha:** 2026-09-24 · **Estado:** abierto · **Prioridad:** media (feature pausado)
**Relacionado:** `docs/issues/2026-09-24_timeout_rpcs_admin_metricas.md`

## Contexto
`sync_validation_errors_to_issues` (`scripts/exports/sync_to_supabase.py`) infló
`issues` de 397K (mayo) a 1,69M por dos defectos (ver issue relacionado). Se
aplicaron dos parches de contención:
- **D2** (dedup acotada por `id_oferta`, chunked IN): la dedup ya no se trunca a
  1000 → deja de re-insertar en cada corrida.
- **D1** (`--skip-issues` en los 3 caminos automáticos: `auto_sync.sh`,
  `run_pipeline_loop.sh`, `pipeline_command_poller.py`): pausa el feature entero.

D1 deja el feature **apagado**. Este issue es el prerequisito para re-activarlo.

## Problema de diseño (lo que falta)
El diseño original baja filas a memoria y deduplica en Python por
`(id_oferta, titulo)`. Es frágil:
1. **Clave inestable:** `titulo = "[AUTO] {mensaje}"`. Si el texto de la regla
   cambia, la clave cambia → duplicados. Hoy funciona sólo porque los mensajes V
   son strings fijos (verificado 30/30), pero es una dependencia implícita.
2. **No hay unicidad server-side:** nada en Postgres impide el duplicado; toda la
   garantía vive en el código de sync.
3. **D2 acota pero neutraliza la auto-resolución per-oferta** (paso 5): sólo visita
   ofertas que todavía tienen error pendiente. La resolución quedó cubierta por la
   rama global (`if not errores_locales`), que es todo-o-nada.

## Rediseño propuesto
1. **Clave natural estable:** columna `error_key` en `issues` (p.ej.
   `id_oferta || ':' || error_id`), NOT dependiente del texto del mensaje.
2. **Unicidad + upsert server-side:** `UNIQUE (error_key) WHERE autor_email =
   'auto-validator@mol.gob.ar'` + `upsert(on_conflict='error_key')`. Postgres
   deduplica; el sync deja de bajar filas a memoria.
3. **Resolución explícita:** marcar resuelto por diferencia de conjuntos
   (`error_key` en Supabase pendientes − `error_key` pendientes locales) en una
   query, sin el escaneo per-oferta.
4. **Recién entonces** quitar `--skip-issues` de los caminos automáticos.

## Intento fallido: D2 "chunked IN" (NO reintentar)
Se probó acotar la dedup filtrando `existing` por `id_oferta` en chunks de 200
(en vez del SELECT global). **No funciona.** Verificado con una corrida real
(offer_ids=None, 292.754 pendientes): la tabla creció **+32.000** (1.693.234 →
1.725.234), `nuevos=222.082` intentados. Causa: cada chunk de 200 ofertas matchea
más de 1.000 issues existentes (medido: `content-range 0-999/1539`), así que el
cap default de 1000 de PostgREST **se aplica igual por chunk** — la dedup queda
ciega contra los duplicados que ya existen. Cualquier enfoque de "bajar existentes
y deduplicar en memoria" choca con el mismo cap mientras la tabla tenga duplicados.
Por eso el fix correcto es la unicidad server-side (abajo), no dedup en el cliente.

## Hallazgo FK (a resolver en el rediseño)
Muchos `validation_errors` pendientes apuntan a ofertas **ausentes de
`ofertas_dashboard`** → el INSERT viola `issues_id_oferta_fkey` (ej. id_oferta
1118221358). Esas nunca pueden volverse issue y se **reintentan eternamente** en
cada corrida (nunca entran a `existing_keys`, siempre son "nuevas", el FK las
rechaza, vuelven la próxima). En la corrida de prueba esto explica el gap entre
222.082 intentados y 32.000 insertados (los batches con una fila FK-mala se
rechazan enteros). El emisor nuevo **debe decidir qué hacer con ellas**: descartar
en origen (no extraer errores de ofertas no sincronizadas) o marcarlas
`no-sincronizable`. Si no, hereda el mismo bucle.

## Guarda para la limpieza previa (ya validada)
total 1.693.234 · auto-validator 1.692.308 (99,945%) · humanos 926 (374 pendientes)
· autor NULL 0. La limpieza del backlog apunta a los auto preservando los 926
humanos (`autor_email <> 'auto-validator@mol.gob.ar'`). Es decisión aparte.
