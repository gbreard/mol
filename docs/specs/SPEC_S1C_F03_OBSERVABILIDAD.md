# SPEC S1C-F0.3 — Observabilidad del Eje 1: acta de corrida + alertas (log + UI)

> **Estado:** Parte 1 (verificación + diseño) — **esperando OK del punto de control antes de implementar.**
> **Fase:** 0 (cimientos) del master S1.C — Reparación.
> **Tipo:** primer spec que toca código de producción (los anteriores fueron discovery read-only).
> **Riesgo:** contenido — agrega registro y visualización, **no cambia la lógica de qué se procesa**.
> **Fecha:** 2026-06-16. **Branch:** `spec/s1c-f03-observabilidad`.

---

## 1. Propósito

Que la fábrica deje rastro de sí misma: **cada corrida del pipeline debe dejar acta** (inicio, fin, alcance, resultado, fallos), **cada fallo debe registrarse como alerta** estructurada (no solo un print que se pierde), y **un panel en la pantalla de fábrica que ya existe** debe mostrar la última corrida y las alertas recientes sin abrir terminal.

Este spec construye el primer cimiento del **Eje 1** del master ("la fábrica corre sola"): no se puede operar una fábrica que no se observa. **No incluye** el criterio único de elegibilidad (4 mecanismos + 8 estados) — eso es F0.4, de alto riesgo, separado a propósito.

---

## 2. Estado verificado (read-only, 2026-06-16)

Antes de diseñar se verificó contra código y BD local. **El alcance asumido cambia parcialmente: parte del "acta + panel" ya existe.** Detalle:

### 2.1 `pipeline_runs` (sqlite local, 616 filas) — es matching-scoped, no pipeline-scoped
- **Quién la escribe:** `database/match_ofertas_v3.py` vía `RunTracker.create_run` (`scripts/run_tracking.py:158`). Es decir, la fila nace **dentro del paso de matching**, no al inicio del pipeline.
- **Qué tiene:** `run_id`, **un solo** `timestamp` (inicio), `source`, versiones NLP/matcher, git branch/commit, `ofertas_count`/`ofertas_ids` (alcance), métricas de matching, `errores_detectados/corregidos/escalados`.
- **Qué NO tiene:** `finished_at` (fin), columna `resultado`/`estado` ∈ {ok, fallida, incompleta}, lista de fallos. Última fila: 2026-05-16.
- **Consecuencia (confirma D-03 de S1.B.6):** no hay marca de "corrida incompleta". Y si la corrida **muere en NLP antes de llegar a matching** (caso Ollama caído), **no deja ninguna fila local** → el fallo más importante es hoy invisible localmente.

### 2.2 Puntos de fallo en `scripts/run_validated_pipeline.py`
| Punto | Línea | Comportamiento hoy |
|---|---|---|
| NLP (Ollama, extracción) | 290-297 | `try/except` → imprime `Error en NLP: …` y **continúa silenciosamente** |
| Paso bloqueante (errores sin resolver) | 711-721 | `sys.exit(1)` controlado, imprime motivo |
| Sin ofertas pendientes | 732-735 | `sys.exit(0)` |
| Export Excel | 638-653 | `try/except` → "Warning", continúa |
| Sync learnings.yaml | 661-666 | `try/except` → "Warning", continúa |
| Exit por escalamiento | 780-782 | `sys.exit(1)` si hay `patrones_claude` |

`OLLAMA_HOST` lo fija el poller (`env['OLLAMA_HOST']='172.17.0.1'`, poller L257). No hay healthcheck explícito de Ollama antes de NLP.

### 2.3 Logging
**No hay logger estructurado.** Todo es `safe_print` → stdout. El único que captura el stdout/stderr es el **poller**, que guarda los últimos 5K/2K caracteres en `pipeline_commands.log` (Supabase). Una corrida lanzada **directo por terminal no deja ese rastro**. Existe dir `logs/` (con `.gitkeep`) para logs a archivo.

### 2.4 El poller ya registra un acta **por comando** (en Supabase)
`scripts/pipeline_command_poller.py` ya escribe, por cada comando que ejecuta, en la tabla Supabase `pipeline_commands`:
`estado` (pendiente → ejecutando → completado/error), `started_at`, `completed_at`, `duracion_seg`, `log` (stdout+stderr truncado), `error_message`, `resultado` (JSON con exit_code + salida estructurada M-08c). Distingue completado / error / timeout. Cada ciclo además hace `sync_local_status` → tabla `pipeline_local_status` (snapshot de conteos).
**Limitación:** vive en Supabase y **solo para corridas invocadas vía poller**; no respeta el principio nº7 (residencia local como fuente de verdad), y es por-comando, no por-corrida con resultado normalizado + fallos.

### 2.5 La pantalla de fábrica ya tiene panel + polling
`app/admin/procesamiento/fabrica/page.tsx`:
- Sección **"Actividad reciente"**: últimos 8 comandos (estado, duración, `error_message`, procesadas).
- **Polling cada 5s** sobre `/api/pipeline-commands` (solo si hay `estado==='ejecutando'`).
- **Toast inline** (`message` ok/error).
- API routes con **service-role client** (`SUPABASE_SERVICE_ROLE_KEY`).
- **`pipeline_runs` NO se lee en fábrica** (sí en `/api/processing-metrics` y `/admin/metricas`, contra Supabase `pipeline_runs_history`).

### 2.6 Sync / pollers
`auto_sync.sh` (cron horario): VPS→local→Supabase, loguea a `/tmp/mol_auto_sync.log`, **sin registro de resultado consultable**. `pipeline_command_poller.py`: ver 2.4.

### 2.7 Tablas locales preexistentes relevantes
- `alertas` (5 filas, 2025-10, **legacy data-quality** escrita por `dashboard_scraping_v4.py`/`db_manager.py`; schema `timestamp/level/type/message/context`). Reutilizable o a evitar por colisión semántica — ver Riesgos.
- `batch_runs` (34 filas, vincula lote↔run), `run_ofertas`.

### 2.8 Contradicción con el alcance asumido → **delta real de este spec**
El acta **por-comando** y el **panel** ya existen (Supabase, solo vía poller). Lo que falta de verdad y respeta residencia local:
1. **Acta LOCAL a nivel-corrida**, creada al **inicio** del pipeline (no mid-matching), fuente de verdad, independiente de Supabase y del camino de invocación, con `resultado ∈ {ok, fallida, incompleta}` y lista de fallos.
2. **Registro estructurado de alertas** emitido en los puntos de fallo de 2.2 (hoy se tragan o solo quedan en el blob de stdout de Supabase).
3. **Panel**: en gran parte ya existe; el delta es mostrar el **acta a nivel-corrida + alertas**, no solo el log crudo del comando.

---

## 3. Reutilización (no reinventar)

| Se reutiliza | De dónde |
|---|---|
| Patrón toast + polling 5s | `fabrica/page.tsx` (sección Actividad reciente) |
| Cliente service-role + `requireAdmin` | API routes `/api/pipeline-*` |
| Empuje local→Supabase cada ciclo | `pipeline_command_poller.py::sync_local_status` (se le suma acta+alertas) |
| Tabla `pipeline_runs` local | se mantiene intacta; el acta de corrida vive en tabla nueva que la referencia |
| Dir `logs/` | destino del log estructurado de alertas |

---

## 4. Entregables (diseño propuesto)

### 4.1 Acta de corrida (local, fuente de verdad)
**Decisión de diseño:** tabla nueva `pipeline_run_actas` (sqlite local) escrita por `run_validated_pipeline.py`, **sin tocar** lo que `pipeline_runs` ya escribe (no disruptividad). Se crea al **inicio** y se cierra al **fin**.

| Columna | Tipo | Significado |
|---|---|---|
| `acta_id` | TEXT PK | `acta_YYYYMMDD_HHMMSS` |
| `started_at` | TEXT | inicio de la corrida (al entrar a `run_full_pipeline`) |
| `finished_at` | TEXT NULL | fin; NULL mientras corre |
| `invocador` | TEXT | `poller` \| `terminal` |
| `args` | TEXT | flags de invocación (limit/ids/skip-*) |
| `alcance_entrada` | INTEGER | ofertas que entraron a la corrida |
| `alcance_procesado` | INTEGER | ofertas efectivamente procesadas |
| `resultado` | TEXT | `ok` \| `fallida` \| `incompleta` \| (NULL mientras corre) |
| `fallos` | TEXT | JSON array de alertas-clave de esta corrida |
| `matching_run_id` | TEXT NULL | FK lógica a `pipeline_runs.run_id` (si llegó a matching) |
| `pid` | INTEGER | PID del proceso que abrió el acta (para distinguir en curso vs muerta) |
| `host` | TEXT | hostname donde corrió (PID solo es comparable dentro del mismo host) |

**Estados de `resultado`:**
- `ok`: la corrida llegó al final sin fallos bloqueantes.
- `fallida`: terminó por un fallo (bloqueante, o exit≠0 controlado).
- `incompleta`: empezó y no cerró — corrida interrumpida/crash.
- `NULL`: acta abierta de una corrida **en curso** (todavía no cerró, pero viva).

**Mecanismo de `incompleta` — decisión consciente (el problema y su resolución).**
Una corrida **en curso** y una **muerta** se ven idénticas con `finished_at IS NULL`: nada las distingue por sí solo. Para resolverlo de forma determinista, sin depender de un timeout frágil:

- **Quién y cuándo hace el barrido:** `run_validated_pipeline.py` ejecuta `barrer_actas_huerfanas()` (de `scripts/observabilidad.py`) **al inicio de cada corrida, antes de crear la nueva acta**. Es el único momento garantizado y suficiente: como el poller ejecuta comandos en serie (single-execution) y las corridas de terminal son manuales, al arrancar una corrida nueva cualquier acta previa abierta pertenece a una corrida que ya no está. El barrido es además invocable on-demand (endpoint/poller) por si se quiere refrescar la UI sin arrancar corrida.
- **Regla de distinción (en curso vs muerta):** un acta abierta (`finished_at IS NULL`) se marca `incompleta` si, **en su mismo `host`**, se cumple **cualquiera** de:
  1. su `pid` ya no corresponde a un proceso vivo (`os.kill(pid, 0)` → `ProcessLookupError`), **o**
  2. su `started_at` supera el timeout máximo de corrida (8 h — el mismo `subprocess timeout` del poller), como respaldo cuando el PID no es confiable (reinicio de máquina que reusa PIDs, u otro host).
  - **En curso** = abierta + pid vivo + dentro del timeout → se respeta, no se toca.
  - **Muerta** = abierta + (pid no vivo **o** fuera de timeout) → `incompleta`.
- **Sesgo elegido:** la regla nunca marca `incompleta` a una corrida viva (un pid vivo dentro de 8 h siempre se respeta; el poller mata a las 8 h, así que ninguna corrida legítima excede ese límite viva). El único residuo es un falso negativo raro (un acta muerta cuyo PID fue reusado por otro proceso vivo dentro de la misma ventana de 8 h queda abierta hasta cumplirse el timeout). Se acepta a conciencia: preferimos no mentir sobre una corrida viva antes que cerrar agresivamente una muerta.
- **Efecto:** cada acta barrida emite una alerta `corrida_incompleta` (ver 4.2).

### 4.2 Registro de alertas (local + log)
**Tabla nueva `pipeline_alertas`** (no reutilizar `alertas` legacy — ver Riesgos):

| Columna | Tipo | |
|---|---|---|
| `id` | INTEGER PK | |
| `timestamp` | TEXT | |
| `severidad` | TEXT | `info` \| `warning` \| `error` \| `critico` |
| `tipo` | TEXT | `ollama_down` \| `nlp_fallo` \| `paso_bloqueante` \| `sync_no_corrio` \| `corrida_incompleta` \| `export_fallo` |
| `mensaje` | TEXT | texto claro y accionable |
| `acta_id` | TEXT NULL | corrida asociada |
| `contexto` | TEXT | JSON con detalle |

**Doble persistencia:** además de la tabla, append a `logs/pipeline_alertas.jsonl` (una alerta por línea, JSON) — log estructurado, fuente local independiente.

**Puntos de emisión** (de 2.2):
| Punto | severidad | tipo |
|---|---|---|
| NLP lanza excepción (L290-297) | `error` | `nlp_fallo` (si la causa es conexión Ollama → `ollama_down`) |
| Paso bloqueante (L711-721) | `warning` | `paso_bloqueante` |
| Export Excel falla (L638-653) | `warning` | `export_fallo` |
| Sync learnings falla (L661-666) | `warning` | `sync_no_corrio` |
| Acta cerrada como `incompleta` (barrido de apertura) | `error` | `corrida_incompleta` |

El emisor es un helper único (`scripts/observabilidad.py::emitir_alerta(severidad, tipo, mensaje, acta_id, contexto)`) que escribe tabla + jsonl. No cambia ninguna decisión de procesamiento; solo registra.

### 4.3 Panel en `procesamiento/fabrica`
**Se suma** una sección "Última corrida" + "Alertas recientes" a la pantalla existente (no pantalla nueva), reusando card + toast + polling.
- **Endpoint nuevo:** `GET /api/pipeline-last-run` (service-role + `requireAdmin`) → `{ ultimaActa, alertas[] }` leyendo de Supabase (espejo subido por el poller).
- **Camino del dato (residencia nº7):** acta + alertas se escriben **local primero**; `pipeline_command_poller.py::sync_local_status` (ya corre cada ciclo) **sube** la última acta + alertas recientes a Supabase (`pipeline_local_status` extendida o tabla espejo `pipeline_actas_mirror`). La UI lee Supabase como hoy.
- **Polling:** reusar el de 5s; o un fetch al montar + refresco al terminar un comando (suficiente, sin polling extra agresivo).

**Mockup textual:**
```
┌─ Última corrida ──────────────────────────────┐
│ acta_20260616_1432 · hace 8 min · vía poller   │
│ ● ok   ·  entraron 100 · procesadas 97         │
│ matching run_20260616_1433                     │
├─ Alertas recientes (3) ────────────────────────┤
│ ⚠ warning · sync_no_corrio · hace 8 min        │
│   "learnings.yaml no sincronizó: timeout"      │
│ ✖ error · ollama_down · hace 2 h               │
│   "NLP abortó: conexión rechazada 172.17.0.1"  │
└────────────────────────────────────────────────┘
```

---

## 5. Implementación (SOLO tras OK del punto de control)

Orden incremental, un commit por paso; punto de control intermedio entre paso 2 y 3:
1. **Migración aditiva**: `pipeline_run_actas` + `pipeline_alertas` (sqlite local) + columnas/tabla espejo en Supabase. No toca `pipeline_runs`.
2. **Acta en `run_validated_pipeline.py`**: crear al inicio de `run_full_pipeline`, cerrar al fin con `resultado`; barrido de apertura para huérfanas. Sin cambiar lógica de selección/procesamiento.
   - **Punto de control intermedio**: verificar en una corrida real que el acta se escribe correcta (inicio/fin/resultado/alcance) antes de seguir.
3. **Alertas**: helper `emitir_alerta` + enganches en los 5 puntos de 4.2.
4. **Endpoint** `/api/pipeline-last-run` + empuje desde `sync_local_status`.
5. **Panel** en `fabrica/page.tsx` leyendo datos reales.

---

## 6. Dependencias
- Lectura BD local sqlite + Supabase service-role (ya configurado en poller y API routes).
- El empuje a Supabase depende del poller corriendo (ya es el caso en operación). Si el poller no corre, el acta+alertas **igual existen local** (fuente de verdad); solo no se reflejan en UI hasta el próximo ciclo.

---

## 7. Validación (criterios binarios)
| # | Test | Criterio binario |
|---|---|---|
| T1 | Una corrida (o dry-run seguro) escribe un acta con inicio, fin, alcance y resultado | el acta existe y tiene los 4 campos no-NULL |
| T2 | Una corrida interrumpida queda `incompleta`, distinguible de `ok` | `resultado='incompleta'` tras barrido de apertura |
| T3 | Un fallo simulado (ej. Ollama no disponible) emite alerta en tabla **y** en `logs/pipeline_alertas.jsonl` | la alerta aparece en ambos, con `tipo=ollama_down` |
| T4 | El panel muestra la última corrida + alertas recientes con datos reales | el panel renderiza el acta real (no mock) |

Tests Python en `tests/` (acta + alertas) y test de componente en `__tests__/component/` (panel), siguiendo los patrones existentes.

---

## 8. Riesgos
- **Aditividad estricta:** no tocar columnas/escritura de `pipeline_runs`; tabla de acta separada que la referencia.
- **No tocar lógica de selección/procesamiento:** los enganches de alerta solo registran; ningún `emitir_alerta` cambia el flujo (el flujo ya hace lo que hace en cada `except`).
- **Colisión con `alertas` legacy:** se usa tabla nueva `pipeline_alertas` para no contaminar ni romper lectores del `alertas` legacy (dashboards viejos).
- **Dependencia del poller para la UI:** mitigada porque local es fuente de verdad; la UI es espejo.
- **Doble fuente (Supabase `pipeline_commands` vs acta local):** se documenta que la acta local es la fuente de verdad a nivel-corrida; `pipeline_commands` queda como registro a nivel-comando del poller (no se elimina ni se duplica su rol).

---

## 9. Criterio de aceptación
- Acta local a nivel-corrida con `resultado ∈ {ok, fallida, incompleta}` escribiéndose en corridas reales.
- Alertas emitidas en los 5 puntos de fallo, en tabla + jsonl.
- Panel en `procesamiento/fabrica` mostrando última corrida + alertas con datos reales.
- T1-T4 verdes. Sin regresión en lo que `pipeline_runs` / el pipeline ya hacen.
- (Eje 6 / definición de terminado) consumidor conectado = panel mostrando datos reales.
