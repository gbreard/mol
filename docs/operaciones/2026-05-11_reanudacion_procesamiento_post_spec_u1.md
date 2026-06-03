# Reanudación de procesamiento post-SPEC U-1

**Fecha inicio:** 2026-05-11
**Última corrida pipeline pre-pausa:** 2026-04-30 10:42 (run_20260430_1042)
**Días de backlog acumulado:** 11
**Estado pipeline pre-reanudación:**
- Matcher: v3.5.2 con JSON v2 activo
- Bug del cruce URI×label corregido (C1)
- Flags ESCO funcionales (C4)
- Sync VPS→Local→Supabase activo (cron horario, `scripts/auto_sync.sh`)
- Poller `pipeline_commands` activo (cron c/minuto)
- Embeddings ESCO restaurados (C3)

## Correcciones al plan original (5 — todas aprobadas)

| # | Corrección | Detalle |
|---|------------|---------|
| 1 | Schema local | BD = `database/bumeran_scraping.db`. Tablas locales: `ofertas`, `ofertas_nlp`, `ofertas_esco_matching`. NO `ofertas_dashboard` (esa es Supabase). |
| 2 | Comando real | `python scripts/run_validated_pipeline.py --ids X,Y` o `--limit N`. NO existe `run_canary.py` ni `--batch_size`. Usar `OLLAMA_HOST=172.17.0.1` si Ollama está en Windows. |
| 3 | Baseline medido | Comparar canary contra **últimas 100 ofertas validadas pre-pausa** (run_20260430_1042 o cercano), no contra números de memoria. |
| 4 | Pre-flight Ollama | Antes de Fase 2: `curl http://172.17.0.1:11434/api/tags` para confirmar que Ollama responde. |
| 5 | Snapshot pre-Fase 2 | Antes del canary: `python scripts/spec_u1/snapshot_supabase_full.py` (o equivalente) para tener punto de comparación si algo se rompe. |

## Plan de reanudación

- **Fase 1**: Inventario read-only (corregida)
- **Fase 2**: Canary 100 ofertas con monitoreo + spot-check humano
- **Fase 3**: Procesamiento masivo en background, escalonado

## Reglas operativas

- NO modificar configs ni reglas del matcher. Reanudar con el sistema tal cual quedó cerrado SPEC U-1.
- NO arrancar sub-tareas residuales SPEC U-1 (RPC SQL, R240, monitoreo cron formal).
- Si aparece algo inesperado en cualquier fase: PARAR y reportar.
- El cron sync sigue activo en background — no interferir.

---

## Bitácora

### Fase 1 — Inventario read-only (2026-05-11 14:19-14:35)

**A. Backlog NLP**
- Total: **7.048 ofertas** sin extracción NLP

**B. Backlog matching (NLP OK, sin URI ESCO)**
- Total: **1.474 ofertas**

**C. Estado cron sync**
- Ubicación: **local** (crontab del usuario `gerardo`)
- Cron activos:
  - `0 * * * * /mnt/d/OEDE/Webscrapping/scripts/auto_sync.sh` — VPS→Local→Supabase, horario
  - `* * * * * scripts/pipeline_command_poller.py` — poller pipeline_commands, c/minuto
- Última ejecución `auto_sync.sh` exitosa: 2026-05-11 14:00 (sin ofertas nuevas)
- Última sync Supabase efectiva: 2026-05-11 02:55 (50.893 ofertas, 1.084.251 skills)
- Errores: ninguno detectado en `/tmp/mol_auto_sync.log` ni `/tmp/pipeline_poller.log`

**D. Última corrida scraping VPS**
- Última sync VPS→Local: 2026-05-11 11:42 (sin ofertas nuevas desde entonces)
- Total ofertas en BD local: **64.948**
- Sync VPS funcionando OK (corridas 8:00, 9:00, 10:00, 11:00 de hoy)

**E. Procesos activos**
- Pipeline procesador: **PAUSADO** (último run pipeline_runs = 2026-04-30 10:42, hace 11 días) ✓
- `pipeline_command_poller.py`: activo (PID 22713) — normal, esperando órdenes Admin UI
- `run_indeed_local.py`: ⚠️ **ACTIVO desde 11:42** (PID 22729) — es scraper, NO pipeline. No bloquea reanudación pero conviene saberlo.

**F. Estados de validación actuales** (56.433 ofertas con matching)

| Estado | N |
|--------|---|
| validado_claude | 38.157 |
| validado | 6.275 |
| pendiente_humano_C1 | 4.488 |
| validado_claude_C1 | 3.691 |
| validado_claude_subfaseD | 2.770 |
| pendiente_humano_subfaseD | 974 |
| en_revision | 45 |
| pendiente | 33 |

**G. Banderas SPEC W**
- `bandera_spec_w_C1`: 304 ofertas (solo existe esa bandera; `bandera_spec_w` general no está en schema actual)
- Cola humana total = `pendiente_humano_C1` + `pendiente_humano_subfaseD` = **5.462 ofertas**

**H. Notas / desviaciones**
- Sub-fase de scraping local Indeed corriendo en paralelo no estaba en el plan. No bloquea, queda registrado.
- Plan original estimaba ~6 días sin procesamiento. Real = **11 días** desde último run pipeline.

### Decisiones de Gerardo para reanudación (autorización 2026-05-11 ~15:00)

1. **Cola humana durante Fase 3**: statu quo. Cyn sigue validando si quiere. Si aparece más H18 (re-rematch que invalida nota humana), registrar en bitácora para SPEC W pero no bloquear.
2. **Ofertas nuevas durante Fase 3b**: snapshot fijo al inicio. Las que entren después quedan para Fase 4.
3. **Sync Supabase durante batch**: suspender cron durante Fase 3b. Sync manual al cierre de cada tanda. Reactivar cron al cierre de Fase 3b. Documentar suspensión/reactivación.
4. **78 ofertas en limbo (`pendiente` + `en_revision`)**: ignorar. Registrar como issue residual SPEC U-3.
5. **Lock vs `pipeline_command_poller`**: implementar antes del canary.

Autonomía técnica para Claude: 4 correcciones (SQL SQLite, baseline N=500-1000 + run_id, flag real Fase 3a, distribución backlog antes de estratos).

---

### Paso 1 — Pre-flight (2026-05-11 15:05-15:20)

**1.1 — Scraper Indeed**
- Estado al chequear: **YA NO ESTABA CORRIENDO** (ps aux vacío). Indeed había sido disparado por el poller via comando `scrape_indeed` desde Admin UI (PID 22729) y terminó por su cuenta entre el inventario de Fase 1 y este chequeo.
- Acción: ninguna necesaria.

**1.2 — Pre-flight Ollama**
- `curl http://172.17.0.1:11434/api/tags`: OK
- Modelos disponibles relevantes: `qwen2.5:7b`, `bge-m3:latest`
- Ready para NLP.

**1.3 — Snapshot pre-Fase 2**
- Archivo: `data/reanudacion/snapshot_pre_fase2_20260511_151505.json`
- Contenido:
  - total_ofertas: 64.948
  - total_nlp: 57.900
  - total_match_con_uri: 56.426
  - total_match_sin_uri: 7 (entries con URI vacía)
  - total_skills_detalle: 1.268.844
  - backlog_nlp: 7.048
  - backlog_matching: 1.474 (= 1.467 sin entry + 7 con URI vacía)
  - estados_validacion: snapshot completo

**1.4 — Lock vs `pipeline_command_poller`**
- Implementación: `scripts/pipeline_lock.py` (helper acquire/release/is_locked con cleanup de stale locks por PID).
- Lock file: `/tmp/mol_pipeline_running.lock` con `{pid, started_at, reason}`.
- Poller modificado en `scripts/pipeline_command_poller.py`:
  - Set `BLOCKING_COMMANDS = {run_pipeline, run_nlp, run_matching, reprocess_errors, revalidate_nlp, revalidate_matching, reapply_rules}`.
  - Función `_pipeline_lock_active()` con cleanup de PID huérfano.
  - En `execute_command()`: si comando en BLOCKING + lock activo → `return False` sin marcar como `ejecutando`. El comando queda en estado `pendiente` y se reintenta al próximo poll cuando el lock se libere.
- Comandos NO bloqueados (siguen funcionando): `sync_supabase`, `sync_supabase_full`, `export_excel`, `generate_training`, `scrape_indeed`, `recluster_*`.
- Tests: acquire / is_locked / stale cleanup / re-acquire / release → todos PASS.
- Syntax check del poller: OK.

### Bug recurrente ComputRabajo (2026-05-11 17:30 - 2026-05-12 11:30)

Detectado durante canary inicial: 98.7% del backlog CT sin descripción procesable. Diagnóstico read-only confirmó 2 bugs distintos:

**Bug B — Extractor regresionado del scraper VPS:**
- VPS está en branch `feature/nuevo-vps` HEAD `8cb83887` (10/03). Fix `51d6592f` del 11/03 (selector `p.mbB`) nunca llegó al VPS.
- Resultado: scraper VPS extrae `box_detail` entero con UI noise ("Ocultaste esta oferta...").
- **Fix aplicado**: patch quirúrgico líneas 333-357 de `01_sources/computrabajo/scrapers/computrabajo_scraper.py` en VPS (no committed). Backup en `.bak_20260511_192359`.
- Test 3 URLs reales: 3/3 con descripciones limpias (733/299/1491 chars), sin UI noise.

**Bug A — Sync `INSERT OR IGNORE`:**
- `export_nuevas.py` del VPS genera `INSERT OR IGNORE` → cuando local ya tiene la oferta (del Paso 1 sin desc), `INSERT OR IGNORE` no actualiza descripción al sincronizar después del Paso 2.
- **Fix aplicado**: línea 144 `export_nuevas.py` VPS reemplazada por `INSERT INTO ... ON CONFLICT(id_oferta) DO UPDATE SET descripcion = excluded.descripcion WHERE LENGTH(excluded.descripcion) > LENGTH(COALESCE(ofertas.descripcion, ''))`. Backup en `.bak_20260512_105200`.
- Test 3 ofertas: 0/0/36 chars → 5769/4815/4309 chars. Solo `descripcion` cambió (53 cols comparadas, 1 cambió).

**A1.3 Backfill CT (workaround inmediato):**
- 3.019 ofertas procesadas (90.6% fetched, 9.4% failed por rate-limit al final)
- CT con desc OK: 5.1% → **96.5%**
- 285 failed quedan para segunda corrida o esperar próximo cron VPS jueves (ahora con Bug A fixed, descripciones limpias se propagarán al local).

**Issue documentado:** `docs/issues/2026-05-12_logging_unbuffered_alertas_realtime.md` — observabilidad insuficiente en procesos batch largos (los 285 fails no fueron detectados a tiempo por stdout bufferizado).

**Deuda técnica residual:** ambos fixes en VPS no committeados. El VPS está 2 meses behind main. Formalización pendiente para SPEC W o U-3.

### Paso 2 — Baseline real (2026-05-11 15:25-15:55)

**Set baseline**: últimos 3 runs `run_*` pre-pausa SPEC U-1, todos del 30/04/2026, con matcher v3.5.2:
- `run_20260430_1042`: 295 ofertas
- `run_20260430_0840`: 115 ofertas
- `run_20260430_0125`: 869 ofertas
- **Total N = 1.279 ofertas**

**Criterio**: ofertas que conservan estos `run_id` son las que NO fueron re-matched por SPEC U-1. Representan limpiamente el comportamiento del matcher pre-pausa.

**Archivo**: `data/reanudacion/baseline_pre_pausa_20260511.json`

**Métricas baseline (las cuatro que pidió Gerardo + 3 más):**

1. **`occupation_match_method` agrupado:**
   - `regla_negocio` (~150 reglas): **74.9%** (958)
   - `semantico` (skills_first_v3 = BGE-M3): **25.1%** (321)
   - `diccionario_argentino`: 0% (en este matcher el diccionario está integrado dentro del loop de reglas)

2. **URIs vacías:** **0 (0.00%)** — baseline limpio.

3. **`decision_metodo`:**
   - `regla_prioridad`: **47.9%** (613)
   - `dual_coinciden`: **25.4%** (325)
   - `semantico_unico`: **25.1%** (321)
   - `regla_por_score_bajo`: 1.2% (15)
   - `regla_override_semantico`: 0.4% (5)

4. **Skills por oferta:**
   - Promedio: **23.24**
   - Min (si tiene): 2 | Max: 57
   - Ofertas sin skills: 0
   - Total skills baseline: 29.729

**Métricas auxiliares:**

5. **`occupation_match_score`:** Avg 0.884 | Min 0.350 | Max 0.980 — alto y consistente.
6. **`estado_validacion` del baseline:** validado_claude 1.276 / pendiente 3 (residual).
7. **`dual_coinciden`** (URI semántico vs URI regla en cada oferta):
   - regla y semántico coinciden: 25.7% (328)
   - difieren (gana regla por prioridad): **49.3% (630)**
   - solo semántico (sin regla aplicable): 25.1% (321)

**Tolerancias para canary (±20% de baseline):**

| Métrica | Baseline | Banda aceptable canary |
|---------|----------|------------------------|
| % regla_negocio | 74.9% | 59.9% – 89.9% |
| % semantico | 25.1% | 5.1% – 45.1% |
| URIs vacías | 0% | 0% – 2% (umbral absoluto del plan) |
| Skills/oferta | 23.24 | 18.59 – 27.89 |
| match_score avg | 0.884 | 0.707 – 1.000 |

### Fase 2 — pendiente (Paso 3 siguiente)

### Fase 3a (2026-05-12) — bottleneck identificado + fix preventivo

**Lanzamiento 1 (PID 98552, 13:26-13:45):** Colgó 18 min en estado `D` (uninterruptible sleep), stack `p9_client_rpc + pread64`. Kill -9 + preload de archivos al cache.

**Lanzamiento 2 (PID 21870, 20:36, en curso):** Reanudó tras preload. Tras 1h 11min: 415/1488 procesadas (27.9%), CPU 333% multithread, estable. ETA ~3h.

**Bottleneck identificado** (post-diagnóstico read-only):
- Paso 1.6 (multi-position detection) en `database/limpiar_titulos.py` líneas 786-813 ejecuta 2 queries con `IN ({N placeholders})` donde N = cantidad de IDs del batch.
- Con N=100 (canary) tarda <30s. Con N=1.488 (Fase 3a) tarda 15-20 min y se cuelga en I/O 9p (WSL2 ↔ Windows) leyendo páginas de la BD de 3 GB.
- El stack `pread64` confirma que SQLite está siguiendo el índice de `ofertas_nlp.id_oferta` y leyendo páginas de `ofertas.descripcion` (texto largo) via 9p para cada uno de los 1.488 IDs.

**Fix aplicado (2026-05-12 ~21:00):** `database/limpiar_titulos.py` función `expandir_ofertas_multi_perfil()`. Las 2 queries con `IN (N placeholders)` reemplazadas por bucle que itera en chunks de **100 IDs por query** y acumula los resultados. CHUNK_SIZE constante. Resultado equivalente, sin queries gigantes.

**Estado del fix:**
- Aplicado en disco, py_compile OK.
- NO afecta el pipeline en curso (PID 21870 ya importó la versión vieja en memoria).
- Test pendiente con 200 IDs cuando se libere el lock (ver `data/reanudacion/test_fix_multiposition_ids.txt`).
- Universo de test: 200 random con NLP procesado (solo 33 candidatos puros del backlog matching no en Fase 3a — insuficientes). El test re-procesa, no afecta integridad porque el matching idempotente sobrescribe con misma data.

**Criterios de éxito del test:**
- Paso 1.6 termina en <2 min (vs 15-20 min de la corrida actual con N=1488).
- Sin estado `D` ni `p9_client_rpc` bloqueado.
- Multi-position candidatos consistentes (esperado: 0-2 detectados, ya que la mayoría tienen `multi_position_status='single'` de runs anteriores).

**Issue infraestructura documentado:** `docs/issues/2026-05-12_migracion_filesystem_linux_nativo.md` — migración a Linux filesystem nativo para evitar 9p en I/O intensivo.

**Lección operativa:**
- Lotes grandes con `--skip-nlp` (N>500 IDs) requieren batching interno o particionar en tandas de 100-200.
- Pipelines existentes en sistemas Linux-only no exponen este bottleneck. Específico de WSL2 + path Windows.

### Fase 3a — completada 2026-05-12

- Run `run_20260512_2139`: **1.455/1.488 ofertas** procesadas con matching.
- Tiempo: 1h 44min (incluye 18 min iniciales perdidos por cuelgue I/O en estado D + cache warmup + kill + relaunch).
- Métricas dentro de baseline ±20%: regla_negocio 68.5%, semantico 24.7%, URIs vacías 0%, match_score 0.900, skills/oferta 33.0.
- 0.07% errores graves. Canarios C-Q1/Q3/Q7 OK. C-Q2/Q5/Q6 falsos positivos esperados.
- Excel: `Pipeline_completo_validacion_20260512_2220.xlsx`.

### Test fix multi-position — validado 2026-05-12

- 200 ofertas backlog NLP (CT 91 + Indeed 61 + BMR 34 + ZJ 14).
- Tiempo: 1h 25min.
- PASO 1.6 con fix ejecutó sin cuelgue (criterio <2 min en queries SQL cumplido).
- 27 candidatos LLM evaluados, 0 multi confirmados.
- Métricas dentro tolerancia: regla 66%, semantico 29%, URIs vacías 0/200, match_score 0.886.
- **Fix validado para producción.**

### Tanda 1 Fase 3b — CANCELADA por cuelgue I/O 2026-05-13

- Lanzada 2026-05-13 00:56 con 1.500 IDs estratificados (CT 570 + Indeed 570 + BMR 190 + ZJ 170).
- NLP completó 1.500/1.500 después de ~6h.
- **Cuelgue en transición NLP → PASO 1.5 NLP Gate**. Hijo PID 58125 en estado `Dl + p9_client_rpc` durante 30+ min.
- Nunca llegó a PASO 1.5, 1.6, ni matching.
- Kill -9 ejecutado 2026-05-13 ~08:15.
- Estado BD post-kill: **1.500 ofertas con NLP procesado, 0 con matching**.

**Cron auto_sync.sh:** suspendido 00:56 (#PAUSED-tanda1#) → reactivado 08:16. No verificada próxima ejecución (cron horario, siguiente disparo a las 09:00).

**Lock:** liberado.

### Cierre sesión 2026-05-12/13

Estado al cerrar:
- Fase 3a: ✓ completa (1.455/1.488 matching).
- Test fix multi-position: ✓ validado.
- Tanda 1 Fase 3b: ✗ colgada en PASO 1.5 NLP Gate (transición NLP → gate). NLP completo en BD, matching pendiente para las 1.500.
- 1.500 ofertas (`data/reanudacion/tanda1_ids_20260513_005556.txt`) en estado consistente "NLP OK, matching pendiente".
- Cron auto_sync: reactivado.
- Lock: liberado.
- Backups del scraper VPS (.bak_20260511_192359) y export_nuevas (.bak_20260512_105200) intactos.

**Patrón sistémico identificado:**

El fix del PASO 1.6 (`limpiar_titulos.py`, queries con IN N→ chunks de 100) cubre solo ese paso. Otras queries con `IN (N placeholders)` y N>500 sobre 9p WSL2 también se cuelgan. Pasos candidatos:

- PASO 1.5 (NLP Gate, `database/nlp_validator.py`): cuelga aquí en Tanda 1.
- PASO 1.5b (auto-corrección NLP): probable.
- PASO 4 (auto-corrección matching): probable.
- Otros lookups con IN list de IDs en `match_ofertas_v3.py`, `auto_validator.py`, `auto_corrector.py`.

**Decisión para próxima sesión: elegir entre:**

- **A) Parchar queries una por una.** Identificar todas con grep + batchear cada una a chunks de 100. Esfuerzo: 2-3h auditando + 1-2h parches.
- **B) Migración mínima a Linux nativo.** Copiar BD + embeddings a `~/mol-data/` + ajustar paths via env var. Esfuerzo: 3-4h + tests. Resuelve raíz.
- **C) Procesamiento por lotes externos.** Tandas chicas (200 ofertas cada una) lanzadas secuencialmente. Lento (15 corridas × 1h cada una = 15h cómputo) pero seguro. No requiere modificar código.

Issue infraestructura ya documentado en `docs/issues/2026-05-12_migracion_filesystem_linux_nativo.md`.

### Diagnóstico — qué cambió durante SPEC U-1 (2026-05-13)

**Hipótesis original (Gerardo):** SPEC U-1 introdujo lecturas BD más intensivas que provocan los cuelgues 9p.

**Resultado del análisis: HIPÓTESIS RECHAZADA. SPEC U-1 NO introdujo queries pesadas al pipeline.**

#### A. Commits relevantes (3 sobre pipeline durante 2026-05-05 a 2026-05-13)

| Commit | Fecha | Resumen |
|--------|-------|---------|
| `10d4889d` | 2026-05-11 12:08 | matcher sub-fase C — diccionario v2 + URI resolution (SPEC U-1 C2) |
| `d851f9c1` | 2026-05-11 12:09 | scripts SPEC U-1 (`scripts/spec_u1/`) — standalone, NO se llaman desde pipeline |
| `1145aad3` | 2026-05-11 12:10 | sanear zombis `get_priority_batch.py` (solo afecta `--limit` mode, no `--ids`) |

#### B. Análisis del commit principal (`10d4889d`)

Diff completo revisado. Cambios introducidos en `match_ofertas_v3.py`:

| Cambio | Tipo | I/O nuevo? |
|--------|------|------------|
| Index `isco_to_canonical_occupation` (líneas 179-199) | Iteración en memoria sobre `occ_metadata` ya cargada | **NO** |
| Variantes implícitas (286-291) | Append en lista Python | **NO** |
| Contextos sin pipe (308-310) | Lógica de string | **NO** |
| Soporte ctx_value dict (312-323) | Parseo dict | **NO** |
| Resolución URI por prioridad (342-357) | Lookups in-memory en dict | **NO** |
| Bug fix setter (646-651) | Asignación variable | **NO** |

**Ninguno introduce queries SQL nuevas ni lectura adicional de BD durante el matching.**

Los scripts standalone (`scripts/spec_u1/*`) corrieron una sola vez durante SPEC U-1 para reprocesar. No están en el flujo regular de `run_validated_pipeline.py`.

#### C. Análisis hipótesis específicas

| # | Hipótesis | Resultado |
|---|-----------|-----------|
| (a) | Multi-position (paso 1.6) nuevo en SPEC | **FALSO**. Existe desde commit `85796feb` (2025-12-09). Existía mucho antes de SPEC U-1. |
| (b) | NLP Gate (paso 1.5) nuevo en SPEC | **FALSO**. Introducido por commit `737f5f50` (pre-SPEC). |
| (c) | Auto-corrección (paso 4) nueva | **FALSO**. Pre-existente. |
| (d) | JSON v2 sinonimos genera lookups BD nuevos | **FALSO**. JSON v2 se carga 1 vez al arranque, lookups en memoria. |
| (e) | esco_occupation_ancestors carga nueva | **FALSO**. La columna se llenó UNA VEZ por `scripts/spec_u1/load_esco_ancestors.py`, el matcher no la consulta durante runtime. |
| (f) | Flags ESCO post-C4 introducen queries | **FALSO**. C4 hizo UPDATE one-time + se agregó al SELECT del sync (no del pipeline). |

#### D. Lo que SÍ cambió (factor real del cuelgue)

**No es código SPEC U-1. Es escalamiento de tamaño de lote que cruza el umbral WSL2+9p:**

1. **Lotes pre-SPEC eran <=1000 ofertas máximo:**
   - `run_20260429_2028`: **1000 ofertas** ← lote más grande pre-SPEC
   - `run_20260430_0125`: 926 ofertas
   - `run_20260430_0840`: 120 ofertas
   - `run_20260430_1042`: 320 ofertas
   - Mayoría histórica: <500 ofertas

2. **Lotes post-pausa son >1488:**
   - Fase 3a: 1488 ← cuelgue inicial, recuperado tras kill+preload
   - Tanda 1: 1500 ← cuelgue terminal en PASO 1.5

3. **BD creció ~24% durante SPEC U-1 + backfill:**
   - `ofertas`: +800 ofertas nuevas del scraping VPS
   - `ofertas_esco_skills_detalle`: 1.1M → 1.3M (+200K, +18%)
   - `validation_errors`: +8.4K (3%)
   - Total: BD pasó de ~2.5GB a ~3.1GB

4. **Page cache de Linux fragmentado por operaciones I/O intensivas consecutivas:**
   - Backfill A1.3 (~450 MB I/O HTTP)
   - Canary unificado (100 ofertas con BGE-M3)
   - Fase 3a (1488 ofertas)
   - Test fix (200 ofertas)
   - Cada uno toca páginas distintas de la BD; cache nunca se asienta.

#### E. Candidatos por prioridad

1. **Tamaño de lote >1000 cruza umbral WSL2+9p para queries IN(N).** El código ya tenía esas queries pre-SPEC pero nunca se ejecutaron con N>1000 en producción. **Evidencia:** lote 1000 del 29/04 corrió OK con código idéntico al de hoy.

2. **BD creció 24%** durante SPEC U-1 → queries con full scan implícito (IN N) más lentas.

3. **Cache fragmentado por múltiples operaciones I/O encadenadas** sin pausa para "warming".

#### F. Recomendación operativa para próxima sesión

**El "culpable" NO es código SPEC U-1.** Es escalamiento de tamaño de lote.

**No hace falta:**
- Migrar a Linux nativo ahora (B): es trabajo grande para un problema solucionable con A o C.
- Parchar TODAS las queries (A): sólo PASO 1.5 y 1.6 son los problemáticos a este volumen; el resto del pipeline maneja batches con IDs procesados de a uno.

**Recomendación:** **Opción C — Tandas chicas (≤800 ofertas)** como límite operativo conocido del sistema:
- 800 ofertas × 8 tandas = 6.400 ofertas (cubre todo el backlog actual)
- Cada tanda ~3-5h cómputo
- No requiere modificar código
- Histórico confirma que ≤1000 funciona

Si después de 800 sigue colgándose, escalar a Opción A (parchar PASO 1.5 NLP gate específicamente).

### Cierre sesión 2026-05-13 — sistema en estado conocido

**Estado de procesos y locks:**
- PID 58122/58125 (Tanda 1 colgada): kill -9 ejecutado 08:15, ambos muertos
- Lock pipeline: liberado
- Cron auto_sync.sh: reactivado 08:16 (próximo ciclo 09:00)
- pipeline_command_poller: sigue activo (cron c/minuto, no afectado)

**Estado BD:**
- Fase 3a `run_20260512_2139`: 1.455 ofertas con matching ✓
- Test fix `run_20260513_0004` + `run_20260513_0020`: 200 ofertas con matching ✓
- Tanda 1 (1.500 IDs): NLP completo, **matching pendiente** (set en `data/reanudacion/tanda1_ids_20260513_005556.txt`)

**Backups intactos:**
- VPS scraper: `.bak_20260511_192359` (Bug B)
- VPS export_nuevas: `.bak_20260512_105200` (Bug A)

**Issues abiertos para próxima sesión:**
- `docs/issues/2026-05-12_logging_unbuffered_alertas_realtime.md` — observabilidad batches largos
- `docs/issues/2026-05-12_migracion_filesystem_linux_nativo.md` — deuda técnica fs
- 2 fixes en VPS aplicados pero no committeados (Bug A + Bug B) — pendiente formalización

### Fase 3 — pendiente (Tanda 1 colgada en PASO 1.5 — escalamiento, no SPEC U-1)
