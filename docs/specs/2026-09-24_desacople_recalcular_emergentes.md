# SPEC: desacople offline de recalcular_emergentes

**Fecha:** 2026-09-24 · **Estado:** diseño (no implementado) · **Origen:** issue
`docs/issues/2026-09-24_timeout_rpcs_admin_metricas.md`

## Problema
El botón "recalcular" de emergentes hace `POST /api/emergentes-pendientes` →
`client.rpc('recalcular_emergentes')` **síncrono**. La RPC computa un JOIN
`ofertas_skills × ofertas_dashboard` + GROUP BY por ISCO + doble `NOT EXISTS`
(perfil_skills, emergentes_pendientes) + cross con esco_argentino sobre ~300K
skills → **30,3s**, choca su `statement_timeout='30s'` → **57014**. No es bloat
(descartado con pg_stat: ofertas_skills 0% dead; reconciliar scanea las mismas
tablas en 1,6-3,6s post-ANALYZE). Es costo intrínseco de la agregación.

## Principio
El **read path ya está desacoplado**: la UI lista vía `get_emergentes` (lee la
tabla precomputada `emergentes_pendientes`). Lo único acoplado a un request
interactivo es el **recompute**. Hay que sacarlo del request.

## Diseño

### 1. Quién dispara el recompute (offline)
Dos opciones, no excluyentes:

- **A (recomendada) — post-sync local.** Sumar el recompute al final del cron de
  sync (`auto_sync.sh` / `run_pipeline_loop.sh`), después de que las skills ya se
  sincronizaron. Un scriptito (`scripts/exports/recalcular_emergentes.py`) llama
  al RPC con el `service_role_key` (o corre el SQL directo). Frecuencia: 1×/día o
  tras cada sync completo. Nunca en carga de página.
- **B — vía poller (botón asíncrono).** Nuevo comando `recalcular_emergentes` en
  `pipeline_command_poller.py` (`build_args: lambda p: []`). El botón de la UI
  **encola** (INSERT en `pipeline_commands`) en vez de ejecutar síncrono →
  responde al toque; la UI polea el estado del comando. Reusa el patrón existente.

Recomendación: implementar **A** primero (elimina el 57014 de raíz: nadie llama
al recompute interactivo) y **B** después si se quiere botón manual.

### 2. El statement_timeout del RPC
La RPC tiene `SET statement_timeout='30s'` y aun así no cierra. Fuera del request
interactivo la latencia no molesta → **subir a `120s`** para el job offline
(cambio de una línea en el `CREATE OR REPLACE`). Si con 120s tampoco cierra, el
cómputo en sí necesita optimización aparte (materializar `skill_freq` por ISCO,
o partir la inserción en pasos desde Python). Anotar como sub-tarea; no bloquea
el desacople.

### 3. Cómo la UI muestra la antigüedad del dato precomputado
- `emergentes_pendientes.fecha_deteccion` (TIMESTAMPTZ, ya existe) → la última
  recomputación es `MAX(fecha_deteccion)`.
- Extender `get_emergentes` (o agregar RPC chica `get_emergentes_meta`) para
  devolver `ultima_actualizacion = MAX(fecha_deteccion)`.
- UI: badge "Emergentes actualizados: hace X" + warning si `> 7 días`.
- Botón "Recalcular ahora": de POST síncrono → encolar comando (opción B) →
  estado "recalculando…" → refrescar al terminar.

## Qué NO cambia
- Tabla `emergentes_pendientes`, read path `get_emergentes`, aprobar/rechazar.
- El resto del pipeline.

## Orden sugerido
1. Script offline + subir timeout RPC a 120s → recompute deja de correr en request.
2. Exponer `ultima_actualizacion` + badge de frescura.
3. (Opcional) Botón asíncrono vía poller.
4. (Si 120s no cierra) optimizar el cómputo — sub-tarea aparte.
