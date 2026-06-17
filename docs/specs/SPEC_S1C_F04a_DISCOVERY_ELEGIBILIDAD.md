# SPEC S1C-F0.4a — Discovery de elegibilidad

> Versión 0.1 · 2026-06-12 · Fase 0 del master S1.C — Reparación
> Discovery read-only que produce los datos para diseñar el criterio único de elegibilidad (F0.4b). No diseña el criterio ni toca producción. Responde tres preguntas: el acoplamiento selección↔estados, la regla de negocio real de hoy, y el motivo de exclusión de las ~13K ofertas que nunca entraron.

## 1. Propósito

Reemplazar la decisión en abstracto por decisión informada: F0.4b (diseño del criterio único) necesita saber qué hace el sistema hoy, qué tan entrelazada está la lógica con los estados históricos, y por qué hay ofertas afuera. Este spec lo averigua sin tocar nada.

## 2. Reutilización

- BD local `database/bumeran_scraping.db` (read-only).
- `scripts/run_validated_pipeline.py` v3.3 y los módulos de selección (RunTracker, refresh_priorities, las queries de selección NLP/matching).
- Relevamiento S1.B.6 (los 4 mecanismos y 8 estados ya identificados) como punto de partida a verificar, no a asumir.

## 3. Entregables

Esta spec con la sección 8 (Hallazgos) completa: las tres preguntas respondidas con evidencia, en forma que Gerardo pueda reaccionar (reglas escritas en lenguaje claro, tabla de motivos de exclusión, veredicto de acoplamiento).

## 4. Implementación — el discovery en tres frentes

### D1 — La regla de negocio real de hoy (código + BD)
Reconstruir, leyendo el código de selección, **qué oferta entra a una corrida hoy** — la regla efectiva que resulta de combinar los 4 mecanismos.
- Trazar en `run_validated_pipeline.py` (y lo que invoque) las queries/condiciones exactas que deciden qué ofertas se toman para NLP y para matching. Transcribir los WHERE reales.
- Reconstruir la regla combinada en **lenguaje claro de negocio**, una o dos frases del tipo: "se procesa toda oferta que [condición], excepto [excepción], priorizando [criterio]". Que sea legible para alguien no técnico.
- Señalar las **contradicciones o solapamientos** entre los 4 mecanismos: ¿hay condiciones que se pisan? ¿un mecanismo puede incluir lo que otro excluye? ¿qué gana cuando hay conflicto?
- **Salida**: la regla efectiva escrita + lista de solapamientos/contradicciones.

### PUNTO DE CONTROL tras D1 — parar y reportar
Reportar a Gerardo la regla de negocio reconstruida en lenguaje claro y los solapamientos. Esta es la pieza que Gerardo necesita ver para opinar. Esperar OK antes de D2-D3.

### D2 — Acoplamiento selección ↔ estados (código)
Medir qué tan entrelazada está la lógica de selección con los 8 valores de `estado_validacion`.
- ¿Cuáles de los 4 mecanismos leen `estado_validacion`? ¿Cuáles de los 8 valores aparecen en condiciones de selección y cuáles son solo "residuo histórico" que nadie consulta?
- Para cada uno de los 8 valores: ¿algún código de selección/procesamiento lo lee hoy, o solo existe en datos? (grep de cada valor en el código).
- **Veredicto binario para F0.4b**: ¿la lógica de selección se puede unificar SIN tocar los datos históricos de `estado_validacion` (porque la selección solo mira un subconjunto), o están tan acoplados que hay que limpiarlos juntos? Con evidencia.

### D3 — Las ~13.000 excluidas, por motivo (BD)
Clasificar las ofertas que nunca entraron al procesamiento por **por qué** quedaron afuera.
- Identificar el universo: ofertas scrapeadas sin fila en `ofertas_nlp` (o el criterio real de "nunca procesada" que surja de D1). Confirmar el conteo (~13K) contra la BD.
- Clasificar por motivo de exclusión, cruzando con: portal de origen (¿son de portales sin keywords como CABA/PortalEmpleo?), fecha de scraping (¿son viejas previas a algún cambio?), presencia en `ofertas_prioridad` (¿quedaron fuera de la cola?), algún flag de exclusión deliberada.
- **Salida**: tabla "motivo de exclusión → cuántas ofertas", que permita a Gerardo decidir cuáles recuperar (bug a corregir) y cuáles son exclusión legítima.

## 5. Dependencias
- BD local (D1 parcial, D3).
- Código + git (D1, D2).
- Sin Supabase (todo el universo de selección es local).

## 6. Validación
Valida cuando D1 (regla + solapamientos), D2 (veredicto de acoplamiento) y D3 (tabla de motivos) están documentados con evidencia.

## 7. Riesgos
- **Read-only estricto**: SELECT y lectura de código/git. No reprocesar, no tocar estados, no correr el pipeline.
- No asumir los 4 mecanismos / 8 estados del relevamiento como verdad: verificarlos contra el código actual (pueden haber cambiado).
- Si el universo de "13K excluidas" no coincide con el conteo real, reportar el número real y su definición.

## 8. Hallazgos

> Ejecutado 2026-06-16 contra `database/bumeran_scraping.db` (read-only) + lectura de código y git. Cero escrituras a producción.

### Distribución real de `estado_validacion` (68.241 filas en `ofertas_esco_matching`)

| estado_validacion | filas |
|---|---:|
| validado_claude | 49.949 |
| validado | 6.275 |
| pendiente_humano_C1 | 4.488 |
| validado_claude_C1 | 3.691 |
| validado_claude_subfaseD | 2.770 |
| pendiente_humano_subfaseD | 974 |
| pendiente | 56 |
| en_revision | 38 |
| **validado_humano** | **0** |

(Confirma los 8 valores del relevamiento S1.B.6. `validado_humano` NO es uno de ellos — tiene 0 filas.)

---

### D1 — La regla de negocio real de hoy

**Regla efectiva, en lenguaje claro:**

> Cada corrida toma las ofertas más prioritarias (más nuevas, con más vacantes, de las que se llenan rápido) que todavía no tienen NLP y tienen una descripción de más de 100 caracteres; las procesa de punta a punta; y no arranca una tanda nueva si la anterior dejó errores graves sin resolver. Una vez que una oferta tiene NLP, sale para siempre del radar de la cola de prioridad. El matching la vuelve a tomar por su cuenta solo si nunca tuvo matching — salvo que esté marcada como *validada por un humano*, estado que hoy no usa ninguna oferta.

**Los 4 mecanismos, verificados contra el código actual:**

| # | Mecanismo | Dónde | Condición real (WHERE transcrito) |
|---|---|---|---|
| 1 | Cola de prioridad (`ofertas_prioridad`) | `get_priority_batch.py` — activa solo con `--limit` sin `--ids` sin `--no-priority` | Elegible = `NOT EXISTS (ofertas_nlp)` AND `descripcion IS NOT NULL AND LENGTH(descripcion)>100`. Ranking = fecha 40% + vacantes 30% + permanencia 30%. |
| 2 | Selección NLP por ausencia de fila | `run_validated_pipeline.py` (`get_ids_without_nlp`) | `LEFT JOIN ofertas_nlp ... WHERE n.id_oferta IS NULL AND (m.estado_validacion IS NULL OR m.estado_validacion != 'validado')` |
| 3 | Candado `estado_validacion` | `match_ofertas_v3.py` v3.4.3 | Matching solo protege `estado_validacion = 'validado_humano'`. `validado_claude` es reprocesable a propósito. |
| 4 | Bloqueo por errores | `check_pending_errors_block` + `transicion_pendientes` | No arranca lote nuevo si el lote `procesado` anterior tiene errores `escalado_claude=1, resuelto=0`. |

**Solapamientos y contradicciones:**

- **A — El candado de matching protege un estado fantasma.** Matching solo bloquea el reproceso de `validado_humano` (0 filas). Los 6.275 `validado`, 49.949 `validado_claude` y los 7.433 `*_C1`/`*_subfaseD` son **todos reprocesables por matching**. El "candado absoluto" que CLAUDE.md describe (validado nunca se reprocesa) **no existe en el matching actual**.
- **B — Tres definiciones distintas de "ya está listo, no tocar", que no coinciden.** NLP excluye `= 'validado'` (6.275). Matching protege `= 'validado_humano'` (0). Ninguna cubre `validado_claude` (49.949) ni las variantes de subfase (7.433). La misma decisión usa criterios incompatibles según la etapa.
- **C — El filtro de descripción vive solo en la cola, no en la selección real.** `descripcion>100` filtra la cola (mec. 1), pero la selección directa por `--ids` y `get_ids_without_nlp` NO lo aplican. → 3.402 ofertas sin descripción útil que la cola nunca elige, pero que un run `--ids` mandaría a NLP igual (donde el extractor las descarta).
- **D — "Prioridad" solo prioriza NLP, no matching.** La cola se vacía en cuanto la oferta tiene NLP (eligibilidad = sin fila NLP). El matching selecciona por su cuenta (sin matching previo + gate no bloqueado), sin mirar score. Las dos etapas del mismo pipeline seleccionan con criterios desconectados.
- **E — El universo "nunca procesada" es 14.189, no ~13K.** Descompone limpio: 10.787 elegibles (desc>100) + 3.402 excluidas por descripción. (Ver D3.)
- **F (menor) — Type mismatch `id_oferta`:** `ofertas`=INTEGER, `ofertas_nlp`=TEXT. Verificado: el JOIN sin CAST (`get_ids_without_nlp`) y el JOIN con CAST (matching) devuelven idéntico (14.189), porque SQLite coacciona el TEXT a numérico por afinidad. Harmless hoy; frágil ante un cambio de motor.

---

### D2 — Acoplamiento selección ↔ estados

**Qué LEE cada uno de los 8 valores (grep en código, excluye tests/archive):**

| Valor | ¿Lo lee la SELECCIÓN del pipeline (mec. 1-4)? | ¿Quién más lo lee? |
|---|---|---|
| `pendiente` | **Sí** — transición pendiente→validado_claude | validar_ofertas, admin |
| `validado` | **Sí** — exclusión NLP (`!= 'validado'`) | sync Supabase, reapply |
| `validado_humano` | **Sí** — protección matching (pero 0 filas) | sync, reapply, canario |
| `validado_claude` | No (selección usa presencia de fila matching, no el estado) | sync Supabase, reapply |
| `validado_claude_C1` | No | **solo** sync Supabase (whitelist de espejo) |
| `validado_claude_subfaseD` | No | **solo** sync Supabase (whitelist de espejo) |
| `pendiente_humano_C1` | No | **solo** tooling SPEC U-1 (`scripts/spec_u1/`) |
| `pendiente_humano_subfaseD` | No | **solo** tooling SPEC U-1 + export validación humana |
| `en_revision` | No | admin_unlock, apply_config_changes, review_offer_chain |

**Veredicto binario para F0.4b:** la lógica de selección **se puede unificar SIN tocar los datos históricos** de `estado_validacion`. La selección del pipeline keya por **presencia/ausencia de filas** en `ofertas_nlp` / `ofertas_esco_matching` más **tres literales** (`pendiente`, `validado`, `validado_humano`). Los otros 5 valores (`validado_claude_*`, `pendiente_humano_*`, `en_revision`) son **residuo desde el punto de vista de la selección**: los consumen solo el sync a Supabase (whitelist de espejo) y el tooling de validación humana de SPEC U-1, no la decisión de qué se procesa.
→ **Acoplamiento bajo en la selección, pero alto en los consumidores downstream:** si F0.4b *renombra o colapsa* estados, debe actualizar el whitelist de `sync_to_supabase.py` y el tooling `scripts/spec_u1/` — pero puede unificar el criterio de elegibilidad sin migrar las 68K filas históricas.

**Pregunta de arqueología — ¿el candado `validado_humano` se rompió o nunca se conectó?**

- Introducido el **2026-01-23**, commit `2052761c` *"feat(validacion): sistema 3 estados + sync Supabase 238 ofertas"*.
- **Ningún código Python escribe nunca `estado_validacion = 'validado_humano'`** — las únicas dos apariciones en código de pipeline son las dos lecturas de protección en `match_ofertas_v3.py`. No hay (ni hubo, por `git log -S`) un `SET ... 'validado_humano'`.
- La herramienta canónica de validación manual `scripts/validar_ofertas.py` escribe `estado_validacion = 'validado'`, y su lista `ESTADOS_VALIDOS = ['pendiente','en_revision','validado','rechazado','descartado']` **ni siquiera incluye `validado_humano`**.

→ **Veredicto: el candado nunca se enchufó.** No es un candado que se rompió (un escritor que se removió): el check de protección (`= 'validado_humano'`) y el escritor real de validación humana (`= 'validado'`) discrepan en el string **desde el día 1**. El estado que de hecho produce una validación humana es `validado` (6.275 filas), que matching NO protege (solo NLP lo excluye de re-NLP). Por eso las ~60K "validadas" son reprocesables por matching: **no hay candado de inmutabilidad efectivo sobre el trabajo validado.**

---

### D3 — Las 14.189 nunca procesadas, por motivo

Universo = ofertas en `ofertas` sin fila en `ofertas_nlp` = **14.189** (no ~13K).

| Motivo de exclusión | N | Naturaleza | Decisión sugerida |
|---|---:|---|---|
| **Sin descripción útil** (descripción nula o ≤100 chars) — listados de ComputRabajo (3.053) / Indeed (345) sin detalle scrapeado | **3.402** | Exclusión **legítima**: NLP requiere descripción >100 chars y los descartaría. La cola los filtra a propósito. | Recuperables solo si se re-scrapea el detalle. Si no, exclusión correcta. |
| **Backlog de admisión** (desc>100, elegibles, ausentes de la cola) | **10.787** | **NO es exclusión.** El 100% fue scrapeado en 2026-05 (4.269) y 2026-06 (6.518). Ningún `refresh_priorities` corrió desde que llegaron. | **Recuperables sin cambio de código**: correr el pipeline / refrescar la cola los admite. |

**Desglose por portal:**

| portal | desc corta (A) | elegible (B) | total |
|---|---:|---:|---:|
| computrabajo | 3.053 | 2.753 | 5.806 |
| indeed | 345 | 3.108 | 3.453 |
| bumeran | 0 | 2.749 | 2.749 |
| zonajobs | 4 | 2.175 | 2.179 |
| caba | 0 | 2 | 2 |

**Hallazgos clave de D3:**
1. **No hay bucket de "exclusión deliberada"** ni de "viejas atascadas": 0 ofertas elegibles sin NLP anteriores a 2026-05. Todo lo scrapeado con buena descripción antes de mayo 2026 **ya fue procesado** — el throughput histórico cerró.
2. Las 14.189 son, en su mayoría (76%), **backlog reciente esperando que el pipeline corra**, no ofertas huérfanas-para-siempre.
3. El único motivo estructural de exclusión es la **falta de descripción** (3.402), concentrado en ComputRabajo/Indeed (portales que scrapean listados sin detalle completo).

## 9. Criterio de aceptación
TERMINADO cuando la sección 8 responde las tres preguntas con evidencia. Su consumidor es F0.4b (el diseño del criterio único), que arranca leyendo este discovery. Definición de terminado del Eje 6: el discovery tiene consumidor declarado y queda registrado.
