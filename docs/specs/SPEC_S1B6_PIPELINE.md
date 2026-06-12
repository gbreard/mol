# SPEC S1.B.6 — Relevamiento de Pipeline

> Versión 0.2 (capas 5.1 + 5.2 — Memoria operativa + estado relevado) · 2026-06-11
> Sexto spec de la fase S1.B — Relevamiento del sistema. Releva la orquestación del pipeline del proyecto MOL. Sigue la plantilla común del master v0.2.
> **Particularidad**: el pipeline es el componente orquestador. Parte de su memoria ya está capturada en los specs S1.B.1–S1.B.5; esta capa la consolida y suma las respuestas operativas de Gerardo del 2026-06-11.

---

## 5.1 Memoria operativa — Gerardo + consolidación

### Cómo se opera el pipeline hoy (la realidad, no el diseño)

**El operador del pipeline es Claude Code bajo demanda de Gerardo.** Gerardo no corre comandos directamente ni hay automatización periódica: le pide a Claude Code que ejecute el comando único, cuando puede o cuando se acuerda. Esa cadencia manual y esporádica explica la **latencia mediana de 6 días scraping→NLP** que midió el Informe de mayo — no es que el procesamiento sea lento; es que arranca tarde.

**Deseo declarado de Gerardo**: que la corrida sea **periódica y automatizada**. Es objetivo, no estado.

### El comando único — lo que ya sabemos de specs anteriores

- Orquesta NLP + matching (S1.B.1, refinado): **NO incluye la sincronización a Supabase**, que va aparte vía poller disparado desde la admin UI.
- El cron del VPS dispara los scrapers y el sync VPS→local al terminar cada corrida del scraper (S1.B.2).
- Identificación exacta de qué orquesta, en qué orden y con qué límites: a verificar en 5.2.

### La selección de qué procesar — "nunca quedó prolijo"

Respuesta textual de Gerardo sobre si el procesamiento es por lotes: **"sí y no, nunca logré que eso quede prolijo, tenemos que resolverlo"**. La selección de ofertas a procesar en cada corrida (¿todas las nuevas? ¿filtros? ¿límites?) es desprolija y Gerardo lo reconoce como deuda sin poder detallar el mecanismo. A verificar en 5.2: cómo decide realmente el comando único qué procesar.

### Reanudación tras fallo

Gerardo **cree** que el pipeline reanuda donde quedó si se corta a mitad de camino. No está seguro. A verificar en 5.2: mecanismo de checkpoint/estados, qué pasa con ofertas a medias, si quedan estados intermedios huérfanos.

### Los validadores intermedios que Gerardo no controla — el hallazgo de esta capa

Respuesta textual (P-5): hay **validadores intermedios dentro del pipeline** que Gerardo no sabe cómo funcionan — **uno después del NLP y otro después del matching**. "Son una especie de test, pero realmente no tengo control sobre ellos para ver qué están midiendo, cómo mejorarlos, qué ocupación dejar que pase."

**Hipótesis fuerte para la 5.2** (conexión con specs anteriores): el validador post-NLP es el **NLP Gate** (51 reglas, 278K marcas en `validation_errors` sin consumidor — S1.B.5 D-08); el post-matching es el **sistema de validación estructurada de SPEC W** (AutoCorrector, gates de validación). Si la hipótesis se confirma, la percepción de Gerardo ("no tengo control ni visibilidad") es exacta y ya está cuantificada: los validadores marcan y nadie consume las marcas.

### La visión de Gerardo: validación humana durante el procesamiento

Lo que Gerardo querría (textual, reformulado): que los validadores intermedios **alerten durante el procesamiento** cuando algunas ofertas están saliendo mal, que eso **se vea en la UI**, y que **Cyn pueda controlar en vivo** qué está pasando, corregir, y **volver a colocar la oferta en la cola con la corrección aplicada**.

Es una visión de *human-in-the-loop durante el procesamiento* (no después), que conecta tres deudas ya relevadas:
1. El **loop de aprendizaje roto** (S1.B.3 D-04): hoy la corrección de Cyn no vuelve al sistema; en esta visión, vuelve inmediatamente vía re-encolado.
2. La **telemetría sin consumidor** (S1.B.5 D-05/D-08): el gate ya detecta y marca; el consumidor que falta es exactamente esta alerta en vivo.
3. La **deuda de UI de Cyn** (S1.B.3 D-09): sus herramientas actuales ni siquiera muestran las correcciones pasadas, mucho menos el procesamiento en vivo.

Se registra como visión para la capa 5.4 y para S1.C — no se diseña acá.

### Hipótesis tentativas para la capa 5.2

1. **Los dos validadores intermedios son el NLP Gate y el sistema de validación de SPEC W** — identificarlos con evidencia y mapear qué hacen con las ofertas que fallan (¿bloquean, marcan y dejan pasar, descartan?).
2. **La selección de qué procesar usa estados/flags en la BD local** (algo tipo `procesado_nlp`, `procesado_matching`) con criterios acumulados poco coherentes — el "nunca quedó prolijo" de Gerardo tendría forma de flags superpuestos de épocas distintas.
3. **La reanudación funciona por estados por oferta** (si una oferta ya tiene NLP, no se reprocesa), no por checkpoint de corrida — lo que implica que un fallo a mitad de lote deja el lote parcialmente procesado sin marca de "corrida incompleta".
4. **Existió automatización que se abandonó** (candidato conocido: `launch_nlp_batch.py` roto según la lectura previa de CLAUDE.md) — instancias de D-15 esperables en orquestación.

### Notas para fases posteriores

- **Automatización periódica del pipeline**: deseo declarado de Gerardo, diseño en S1.C (requiere primero observabilidad y manejo de fallos sanos).
- **La visión human-in-the-loop con re-encolado**: input mayor para el diseño objetivo del sistema (S1.C) y para el spec de UI (S1.B.7).

---

## 5.2 Estado actual relevado

> Relevamiento read-only del 2026-06-11 sobre `scripts/run_validated_pipeline.py` v3.3, los validadores, el sistema de prioridad, el crontab local y la BD local (`database/bumeran_scraping.db`, modo solo-lectura). No se ejecutó el pipeline, scrapers ni Ollama; no se conectó a Supabase viva.

### 5.2.1 Anatomía del comando único y la selección de procesamiento

**El comando único es `scripts/run_validated_pipeline.py` v3.3** (entry point confirmado de S1.B.3). Orquesta, en un solo loop con reproceso, este orden real:

| Paso | Qué hace | Componente |
|---|---|---|
| 1 | NLP (solo en la iteración 1) | `database/process_nlp_from_db_v11.py` |
| 1.5 | **NLP Gate** (51 reglas) + persiste + actualiza `nlp_gate_status` | `database/nlp_validator.py` |
| 1.5b | Auto-corrección NLP → re-validación → escala a Claude | `database/auto_corrector.py` |
| 1.6 | Multi-position detection (`usar_llm=True`) | `database/limpiar_titulos.py` |
| 2 | **Matching** (incluye extracción de skills) | `database/match_ofertas_v3.py` |
| 3 | **Validación post-matching** | `database/auto_validator.py` |
| 4 | Auto-corrección de matching | `database/auto_corrector.py` |
| 4.5 | Auto-transición `pendiente`→`validado_claude` (salvo errores bloqueantes) | inline |
| 5 | Loop de reproceso NLP (máx. 2 iteraciones) | inline |
| 6 / 7 / 8 | Reporte de patrones para Claude → Excel de validación → sync `learnings.yaml` | — |

**Confirmado (S1.B.1): el comando único NO incluye la sincronización a Supabase.** Termina en el sync de `learnings.yaml`. El sync a Supabase va por otro carril (ver 5.2.3 y 5.2.4).

**La selección de qué procesar — el "nunca quedó prolijo" tiene forma concreta.** No hay un mecanismo único: hay **cuatro mecanismos superpuestos de épocas distintas**:

1. **Sistema de prioridad v3.1** (tabla `ofertas_prioridad`, estados `pendiente`/`en_proceso`/`procesado`). Activo solo con `--limit` sin `--ids` y sin `--no-priority`. Calcula score (fecha 40% + vacantes 30% + permanencia 30%) y entrega el lote ordenado.
2. **Selección de NLP por ausencia de fila** en `ofertas_nlp` (`LEFT JOIN ... WHERE n.id_oferta IS NULL`), no por flag — una oferta "necesita NLP" si no tiene fila, no porque un campo lo diga.
3. **`estado_validacion='validado'`** como candado de protección (excluye de reproceso).
4. **`validation_errors.resuelto` + `errores_bloqueantes`** (de `config/validation_rules.json`) para bloquear el avance del lote siguiente.

→ **Confirma la hipótesis 2 (flags superpuestos).** El censo de la BD muestra **8 valores distintos de `estado_validacion`** acumulados por capas históricas:

| estado_validacion | ofertas |
|---|---|
| `validado_claude` | 49.949 |
| `validado` | 6.275 |
| `pendiente_humano_C1` | 4.488 |
| `validado_claude_C1` | 3.691 |
| `validado_claude_subfaseD` | 2.770 |
| `pendiente_humano_subfaseD` | 974 |
| `pendiente` | 56 |
| `en_revision` | 38 |

Los sufijos `_C1` y `_subfaseD` son de SPEC W (etapas posteriores) y conviven con los originales sin unificación. Ningún paso del comando único normaliza este vocabulario: cada época agregó valores nuevos.

**Reanudación — Gerardo tiene razón parcial.** No existe un checkpoint de corrida; la reanudación es **por estado por oferta**:

- NLP no reprocesa una oferta que ya tiene fila en `ofertas_nlp` → una corrida cortada reanuda salteando lo hecho.
- `mark_batch_as_completed(run_id)` cierra como `procesado` **solo** las ofertas que quedaron persistidas en `ofertas_esco_matching` para ese `run_id`; **las que faltan vuelven a `pendiente`** para el próximo lote. Es reanudación parcial real, pero el estado vive en `ofertas_prioridad`, **sin marca explícita de "corrida incompleta"**.
- `refresh_priorities` / `sanear_estados_inconsistentes` sanean "zombis" (`en_proceso` huérfano: con o sin NLP) al inicio de cada lote.
- **Coste del modelo**: deja huérfanas que ningún saneamiento recoge. Censo: **1.553 ofertas con NLP hecho pero sin matching** — estado intermedio estable que nadie reabre.

**Registro de corridas.** Existen dos tablas:
- `pipeline_runs` (**616 filas**): rica — `run_id`, timestamp, `source`, versiones NLP/matcher, `git_branch`/`git_commit`, snapshot de config, métricas, diffs vs run anterior, contadores `errores_detectados`/`corregidos`/`escalados`.
- `run_ofertas` (**99.076 filas**): mapeo `run_id` → `id_oferta` → `created_at` (confirma lo visto en S1.B.1: es el detalle por oferta de cada corrida).

### 5.2.2 Los dos validadores intermedios

→ **Confirma la hipótesis 1.** Los dos validadores que Gerardo "no controla" son exactamente el NLP Gate y el validador post-matching:

| | Post-NLP | Post-matching |
|---|---|---|
| **Identidad** | NLP Gate — `nlp_validator.py` (51 reglas, `config/nlp_validation_rules.json`) | `auto_validator.py` (reglas matching V02/V10/V27) |
| **Punto** | Paso 1.5, antes de matching | Paso 3, después de matching |
| **Qué hace con lo que falla** | **BLOQUEA** si severidad `critico`/`alto` (la oferta no entra a matching); marca `nlp_gate_status` + escribe `validation_errors` | **Solo MARCA** en `validation_errors`. El "bloqueo" lo aplica el Paso 4.5: una oferta con error bloqueante queda en `pendiente`, no promueve a `validado_claude` |
| **Severidades** | `critico`/`alto` bloquean; el resto solo marca | `warning`/`info`/`bajo` no bloquean |

**Sorpresa cuantitativa — el gate marca masivamente pero bloquea casi nada.** `validation_errors` tiene **278.565 marcas**:

| severidad | marcas |
|---|---|
| info | 156.694 |
| medio | 78.229 |
| warning | 34.115 |
| bajo | 7.179 |
| alto | 2.348 |

Pero `nlp_gate_status` registra **solo 70 ofertas bloqueadas** de 69.794 (0,1%). Es decir: el gate detecta cientos de miles de problemas y prácticamente todo pasa igual al matching. La percepción de Gerardo ("son un test pero no tengo control ni sé qué dejar pasar") es **exacta y ya cuantificada**: esto es la **telemetría sin consumidor** de S1.B.5 (D-08), confirmada desde el otro extremo del pipeline.

**El gate ya detecta el colapso de sector — y nadie lo consume** (adición 2.C). Las marcas de sector existen y son masivas:

| regla | marcas |
|---|---|
| `V18_sector_igual_area` | 8.662 |
| `V22_empresa_confidencial_con_sector` | 6.833 |
| `V21_sector_tecnologia_no_it` | 1.303 |
| `V20_sector_salud_no_sanitario` | 1.231 |
| `V19_sector_seguridad_no_vigilancia` | 394 |
| `NV02_sector_no_canonico` | 74 |

~**18.500 marcas de sector** que el gate produjo y nadie consume: el campo Sector sigue colapsado en el dashboard (S1.B.5) pese a que el pipeline ya lo diagnosticó oferta por oferta. Es otra instancia exacta de telemetría sin consumidor.

**Configurabilidad real vs. percibida.** Las reglas de ambos validadores viven en JSON editables (`config/nlp_validation_rules.json`, `config/validation_rules.json` con `errores_bloqueantes`, umbrales en config de matching). Un operador **puede** ajustar reglas activas, severidades y lista de bloqueantes **sin tocar código** — pero **no hay UI** que lo exponga ni que muestre qué marcó cada validador. La percepción de Gerardo ("no tengo control") es de **visibilidad y exposición**, no de imposibilidad técnica: el control existe, está enterrado en JSONs.

**¿Puede un validador DETENER el pipeline o RE-ENCOLAR hoy?** El gate detiene el avance a matching de la oferta bloqueada (si todas se bloquean, el loop corta). El re-encolado existe **solo automático** (`mark_batch_as_completed` devuelve las no-completadas a `pendiente`). **El re-encolado con corrección humana de Cyn que Gerardo imagina no existe** — es precisamente el hueco de la visión registrada en 5.1.

### 5.2.3 La cadena completa y la máquina de estados de una oferta

**Mapa de la orquestación de punta a punta** (verificado con los disparadores reales):

```
[VPS] cron Lun/Jue 08:00 → scrapers (Bumeran, ZonaJobs, ComputRabajo, CABA, Portal Empleo, Indeed)
        ↓ (al terminar, en el VPS)
[VPS] export_nuevas.py → dump incremental
        ↓
[LOCAL] cron HORARIO → auto_sync.sh:
          (1) sync_from_vps.py   (VPS → BD local)
          (2) sync_to_supabase.py (BD local → Supabase, solo ya procesadas)
          (3) sync_scraping_daily / dinamica
        ↓ ←——————————— HUECO: el procesamiento NO se dispara solo —————————→
[LOCAL] comando único (run_validated_pipeline.py): NLP → Gate → Matching → Validación
          disparado on-demand por:
            · Claude Code a pedido de Gerardo, o
            · pipeline_command_poller.py (cron cada minuto) cuando la admin UI encola un comando en `pipeline_commands`
        ↓
[LOCAL→Supabase] el sync horario (auto_sync.sh paso 2) sube las que ya quedaron procesadas
```

**El hueco está localizado y medido.** Los **extremos** de la cadena (sync de entrada VPS→local y sync de salida local→Supabase) están **automatizados por hora** vía `auto_sync.sh`. El **núcleo** (NLP + matching) es **on-demand**: solo corre cuando alguien lo dispara (Claude/Gerardo) o cuando la admin UI encola un comando que el poller levanta. No hay disparo periódico del procesamiento.

**Esto explica la latencia con datos.** Medición read-only de latencia por tramo (mediana):

| Tramo | Mediana | Lectura |
|---|---|---|
| scraping → NLP | **6,6 días** (n=69.490) | El cuello de botella. Coincide con el Informe de mayo |
| NLP → matching | **1,0 día** (n=68.241) | Mismo comando único; gap = batching |
| matching → validado | **0,0 días** (n=56.234) | Misma corrida |

Confirma textualmente la 5.1: *"no es que el procesamiento sea lento; es que arranca tarde"*. Una vez disparado, el núcleo procesa en ≤1 día; los 6,6 días son el tiempo que la oferta espera a que alguien apriete el gatillo.

**Máquina de estados real de una oferta** (campos que la representan):

```
scrapeada (ofertas: scrapeado_en)
  → sincronizada a local (auto_sync horario)
  → priorizada (ofertas_prioridad.estado: pendiente)
  → en_proceso (lote asignado)
  → NLP hecho (ofertas_nlp: nlp_extraction_timestamp, nlp_processed_at)
  → gate (ofertas_nlp.nlp_gate_status: aprobado | bloqueado)
  → matcheada (ofertas_esco_matching: matching_timestamp)
  → validada (estado_validacion: pendiente → validado_claude / pendiente_humano_* / validado)
  → procesado (ofertas_prioridad)
  → sincronizada a Supabase (auto_sync horario)
```

**Dónde queda trabada una oferta** (censo read-only):
- **1.553 con NLP sin matching** — huérfanas estables, nadie las reabre.
- **70 bloqueadas por el gate** (`nlp_gate_status='bloqueado'`) — esperan corrección que en la práctica no llega.
- **~13.000 sin NLP** (82.726 ofertas vs. 69.794 con NLP) — fuera de cobertura del procesamiento.
- `ofertas_prioridad` tiene 57.276 filas, todas en `procesado` — la cola de prioridad cubre ~57K de las 82.726 ofertas; el resto nunca entró al sistema de prioridad.

**Timestamps por etapa: existen los necesarios para medir cada tramo** — `ofertas.scrapeado_en`, `ofertas_nlp.nlp_extraction_timestamp`/`nlp_processed_at`, `ofertas_esco_matching.matching_timestamp`/`validado_timestamp`. **Salvedad (S1.B.5 D-11)**: el lag negativo de `scrapeado_en` está presente — **4.876 de 69.490** ofertas tienen `nlp_extraction_timestamp` anterior a `scrapeado_en` (causa conocida: `migrate_historical_data.py:223` sella `scrapeado_en` con `datetime.now()` al migrar). Las medianas de arriba lo absorben pero cualquier métrica de latencia automática debe filtrarlo.

### 5.2.4 Automatización abandonada y bloqueos para la periodicidad

**Automatización que existió y se fue:**
- **`launch_nlp_batch.py` no existe** en ninguna parte del repo, pero CLAUDE.md lo documenta dos veces como entry point vigente ("NLP batch background: skip-matching, log a archivo"). Entry point fantasma. → **instancia de D-15** (adición 2.D): una capacidad documentada como viva que ya no está, sin que la documentación lo refleje.
- **`run_scheduler.py`** (scheduler local de scraping, legacy) sigue en el repo pero sus logs `logs/scheduler_2026{04,05,06}.log` están **en 0 bytes** — dormido desde que el scraping pasó al cron del VPS (S1.B.2).

**Automatización que sí está viva hoy** (matiz importante a la 5.1):
- `auto_sync.sh` (cron horario): sync de entrada y de salida. Funciona.
- `pipeline_command_poller.py` (cron cada minuto): gateway local que lee `pipeline_commands` de Supabase y ejecuta `run_validated_pipeline.py` cuando la admin UI encola una orden. Funciona, pero es **reactivo, no periódico**.

Es decir: la 5.1 decía "no hay automatización periódica" y es cierto **para el procesamiento**, pero los bordes (sync) y el canal de disparo (poller) ya están automatizados. Lo que falta no es infraestructura de ejecución: es **el disparo periódico del procesamiento y el manejo sano de lo que falla**.

**Inventario de bloqueos para programar el comando único en un cron** (observados, sin diseñar la solución):

1. **Selección desprolija (5.2.1)**: cuatro mecanismos de selección superpuestos y 8 estados de validación de épocas distintas. Un cron necesita un criterio único y estable de "qué entra"; hoy no existe.
2. **Manejo de fallos sin alerta**: el gate bloquea 70 ofertas y marca 278K problemas, pero nadie se entera. Un cron corriendo solo acumularía bloqueos y huérfanas en silencio (las 1.553 NLP-sin-matching son la evidencia de que ya pasa con disparo manual).
3. **Sin marca de "corrida incompleta"**: la reanudación es por estado por oferta. Un cron que se pise con una corrida anterior, o que corte a medias, depende del saneamiento de zombis de `refresh_priorities` — frágil si dos corridas se solapan.
4. **Dependencia de Ollama local**: el Paso 1 (NLP) y el 1.6 (multi-position con `usar_llm=True`) requieren Ollama corriendo. Un cron debe verificar disponibilidad del modelo antes de arrancar; hoy si Ollama no está, el NLP falla y el loop sigue a matching con lo que haya.
5. **Pasos manuales / on-demand intercalados**: el procesamiento hoy se dispara a mano justamente porque alguien decide *cuándo*. Automatizarlo requiere decidir cadencia, tamaño de lote y qué hacer con el bloqueo de lote por errores pendientes (`check_pending_errors_block` detiene el lote siguiente — en un cron eso frena la cadena hasta intervención humana).
6. **Cobertura parcial de la cola**: `ofertas_prioridad` cubre 57K de 82K ofertas; ~13K sin NLP nunca entraron. Un cron periódico necesita que *todas* las nuevas entren a la cola, no solo algunas.

**Cierre del círculo con specs anteriores** (sin repetir contenido): los dos validadores intermedios son el NLP Gate (S1.B.5 — 51 reglas, telemetría sin consumidor D-08) y el validador post-matching que alimenta el loop de aprendizaje roto (S1.B.3 D-04). La cadena de marcas que nadie consume (gate, sector, post-matching) es el mismo patrón de *buffers muertos* relevado en Skills (S1.B.4) y Matching (S1.B.3).

### 5.2.5 Hipótesis refinadas

1. **Los dos validadores = NLP Gate + validador post-matching.** ✅ **Confirmada.** El post-NLP bloquea (critico/alto) y marca; el post-matching solo marca y delega el "bloqueo" a la auto-transición. Ambos sin UI ni consumidor de sus marcas (278K marcas, 70 bloqueos efectivos).
2. **La selección usa estados/flags superpuestos de épocas distintas.** ✅ **Confirmada.** Cuatro mecanismos (prioridad, ausencia-de-fila NLP, candado `validado`, errores bloqueantes) + 8 valores de `estado_validacion`. El "nunca quedó prolijo" de Gerardo es literal.
3. **Reanudación por estado por oferta, no por checkpoint de corrida.** ✅ **Confirmada con matiz.** `mark_batch_as_completed(run_id)` devuelve las no-completadas a `pendiente` (Gerardo tiene razón parcial), pero sin marca de corrida incompleta y dejando huérfanas (1.553 NLP-sin-matching).
4. **Existió automatización que se abandonó.** ✅ **Confirmada y ampliada.** `launch_nlp_batch.py` es un entry point fantasma (D-15) y `run_scheduler.py` está dormido. **Refinamiento clave**: la automatización no está toda muerta — los sync (entrada/salida) y el poller están vivos; lo que falta es el **disparo periódico del procesamiento**, no la infraestructura.

---

> *Versión 0.2 — Capas 5.1 y 5.2 cerradas. Capas 5.3 (deuda observada) y 5.4 (principios) se trabajan con Gerardo después.*
