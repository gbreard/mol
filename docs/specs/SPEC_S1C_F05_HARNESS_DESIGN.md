# SPEC S1C-F0.5 — Harness de medición (DISEÑO)

> Versión 0.1 (diseño para revisión) · 2026-06-12 · Fase 0(c) del master S1.C
> Documento de DISEÑO. No construye el harness: define su contrato, su ground truth, su métrica y su reutilización, para revisión del hilo del harness y de Gerardo antes de construir. La construcción es F0.5-build, con el experimento puente como primer consumidor.

## 1. Propósito

El harness es la infraestructura de medición del procesamiento: dado un cambio en el cerebro (corpus, reglas, modelo, aristas argentinas), responde **"¿mejora o empeora, en qué casos, y por qué vía?"** contra un ground truth estable y local. No mejora el procesamiento — es la regla con la que se mide que las mejoras, mejoran. Reemplaza la práctica ad-hoc de los experimentos de mayo por infraestructura versionada.

## 2. Alcance de la primera versión

- **Mide OCUPACIÓN** (no skills todavía). Es donde está el Gold Set confirmado y la decisión más central del pipeline. Skills queda para una extensión posterior, pero el contrato (sección 5) se diseña para admitirla sin reescritura.
- **Read-only sobre producción**: carga el matcher en memoria (patrón `exp_raiz_skills/`), nunca persiste. No toca `ofertas_esco_matching` ni ninguna tabla de producción.
- **100% local**: ground truth en snapshot local fechado; sin Supabase en runtime (principio de residencia).

## 3. Inventario de reutilización

Verificado contra el repo vivo el 2026-06-16. **Todas las rutas y firmas que el prompt de diseño asumía existen y calzan** — no hubo que parar por desajuste.

### 3.1 `exp_raiz_skills/` — el prototipo del harness de ocupación

`harness.py` (skills→ocupación con poda) y `harness_cierre.py` (inyección de skills perfectas) ya demuestran el patrón completo de medición read-only. Lo que hacen, y cómo se traduce al harness:

| Pieza del prototipo | Qué hace hoy | Estado para el harness |
|---|---|---|
| Carga del matcher | `from match_ofertas_v3 import MatcherV3; matcher = MatcherV3(db_conn=conn, verbose=False)` con `sys.path.insert(0,'database')` | **Reutilizable tal cual.** Es el modo "matcher en memoria, BD compartida, sin persistir". |
| Lectura de la oferta | `SELECT * FROM ofertas_nlp WHERE id_oferta=?` → dict por columnas (`cols=[r[1] for r in PRAGMA table_info]`) | **Reutilizable tal cual.** La entrada de `match()` es la fila `ofertas_nlp` como dict. |
| Inyección de overlay | monkeypatch de `matcher.skills_extractor.extract_skills_dual` (captura el baseline, lo reemplaza por una versión podada/inyectada, restaura el original) | **Reutilizable como mecanismo**, hay que **generalizarlo**: hoy el overlay es específico (poda de ruido / skills perfectas de Cyn). El harness necesita un overlay nombrado y declarativo (sección 5) para que "baseline" y "aristas-AR" sean dos configs intercambiables. |
| Llamada al matcher | `matcher.match(nlp)` → `MatchResult`, **sin** `match_and_persist` | **Reutilizable tal cual.** Es la garantía read-only: `match()` no escribe. |
| Veredicto por caso | clasifica `pruned_isco` vs `base_isco` vs `target` en `CORRIGIO / NO_CAMBIO / EMPEORO / CAMBIO_NO_TARGET`, comparando a ISCO-4 (`(isco or '')[:4]`, con `.lstrip('C')` en `harness_cierre`) | **Es el embrión de la matriz de transición A→B** (sección 5). Reutilizable como lógica; hay que renombrar a las cuatro celdas estándar (`mal→bien` = CORRIGIO, `bien→mal` = EMPEORO, etc.) y generalizarlo a comparar dos configs cualesquiera, no baseline-vs-podado. |
| Instrumentación por método | ya lee `base.metodo`, `base.metadata.get('decision_metodo')`, `base.metadata.get('regla_aplicada')` | **Reutilizable tal cual.** El desglose por método (sección 5.3) ya está disponible en estos campos. |

**A construir (no existe en el prototipo):** el cargador de ground truth desde snapshot local (hoy los targets están **hardcodeados** en un dict `TARGETS` dentro del script); la comparación a doble nivel (ISCO-4 + ESCO); la matriz de transición generalizada A↔B; el reporte estructurado con regresiones listadas caso por caso.

### 3.2 Firma del matcher y metadata de decisión

`database/match_ofertas_v3.py`:

- **Firma:** `def match(self, oferta_nlp: Dict) -> MatchResult`. Recibe la fila `ofertas_nlp` como dict; devuelve un dataclass `MatchResult`. No persiste (la persistencia vive en otra ruta).
- **`MatchResult` expone:** `status`, `esco_uri`, `esco_label`, `isco_code`, `score`, `metodo`, `skills_extracted`, `skills_matched`, `alternativas`, `metadata` (dict).
- **Metadata de decisión** (lo que habilita el desglose por método): `metadata['decision_metodo']` (`regla_prioridad` / `semantico_default` / diccionario), `metadata['regla_aplicada']` (id de regla), más `isco_semantico`/`isco_regla` cuando aplican. **El nivel de instrumentación que pide la sección 5.3 ya está disponible sin tocar el matcher.**
- **Acoplamiento:** el harness depende de (a) la firma `match(dict)→MatchResult` y (b) el nombre del punto de monkeypatch `skills_extractor.extract_skills_dual`. Ambos son superficie estable hoy; el riesgo de acoplamiento se trata en la sección 7.

### 3.3 Bajada del Gold Set y formato de los gold sets

- **`scripts/sync_gold_set.py`** baja de Supabase la tabla `gold_set` (columnas `id_oferta, esco_ok, isco_esperado, esco_esperado, tipo_error, comentario`, filtrando `activo=True`) y la tabla `gold_set_skills`, y **escribe el resultado en `database/gold_set_manual_v2.json`**. ⚠️ **Esta ruta de salida es exactamente el archivo que la regresión vieja (49) consume — ver el blindaje en la sección 4.** El harness NO puede usar `sync_gold_set.py` tal cual: necesita una variante (flag de destino o script hermano) que escriba en `tests/harness/`.
- **Formato y nivel de los esperados** (verificado sobre `database/gold_set_manual_v2.json`, 49 casos — misma forma de columnas que la tabla Supabase de 113):
  - `esco_ok` (bool): presente en el 100%.
  - `isco_esperado`: string **ISCO-4** (ej. `"4321"`). Presente solo en **16/49** (los casos con error de ocupación).
  - `esco_esperado`: **etiqueta legible**, NO URI ni `esco_code` (ej. `"Jefe de almacen/jefa de almacen"`). Presente solo en **10/49**.
  - `skills_esperadas`: lista de labels (48/49) — insumo de la extensión de skills, no de la v1 de ocupación.
  - **Hallazgo crítico para el ground truth:** los casos `esco_ok=true` **no traen ningún esperado explícito** — solo el booleano que confirma que el match vigente *en el momento de validar* era correcto. No hay target almacenado para ellos. Esto condiciona el diseño de la comparación (sección 4, validación de unidad).

## 4. Ground truth

- **Fuente**: tabla `gold_set` de Supabase (113 casos confirmados, adenda A-1 de S1.B.3).
- **Mecanismo**: el harness consume un **snapshot local fechado** (`tests/harness/gold_set_snapshot_<fecha>.json`), generado por la bajada que hoy nadie corre (`sync_gold_set.py`). Bajar el snapshot es un acto deliberado y versionado (su propio commit), NO un espejo vivo: el ground truth no se mueve bajo los pies entre la medición de la versión A y la de la versión B.
- **No-disruptividad (blindaje explícito)**: el snapshot es un **archivo NUEVO** en `tests/harness/`. **NO sobrescribe `gold_set_manual_v2.json` (49 casos) que consume la regresión actual.** El harness nuevo (113) y los tests de regresión viejos (49) miden contra archivos distintos a propósito — esa desincronización es parte del diagnóstico (el harness de regresión quedó desactualizado, S1.B.3), y su reconciliación es decisión de S1.C, no algo que la bajada del snapshot deba forzar pisando un archivo que otros tests consumen. La bajada del Gold Set NO toca ningún gold set preexistente del repo.
  - **Consecuencia operativa para F0.5-build**: como `sync_gold_set.py` escribe HOY en `database/gold_set_manual_v2.json` (verificado, sección 3.3), la construcción NO puede invocarlo tal cual. Debe agregarle un destino parametrizable (o un script hermano `sync_gold_set_snapshot.py`) que escriba SOLO en `tests/harness/gold_set_snapshot_<fecha>.json`. Esto es parte del blindaje, no un detalle de implementación: si build reutiliza el script sin cambiar el destino, pisa el archivo de la regresión vieja.
- **Validación de unidad del ground truth** (crítico — diagnóstico de jerarquía ESCO/ISCO): cada caso del Gold Set declara su esperado. El diseño debe resolver **a qué nivel está expresado cada esperado**: ISCO-4 (`7126`), ESCO-URI/granular (`7126.1.2`), o mezcla. **Verificado contra los datos reales (sección 3.3): los esperados NO están a un solo nivel ni en una sola representación.**
  - `isco_esperado` viene a **ISCO-4** (string de 4 dígitos).
  - `esco_esperado` viene como **etiqueta legible** (no URI ni `esco_code`) — para comparar a nivel ESCO contra el `esco_label`/`esco_uri` que devuelve el matcher hace falta una resolución label→código/URI, que el diseño de build debe especificar (no es comparación de strings ingenua).
  - Los casos `esco_ok=true` **no traen esperado** — su "target" implícito es el match que el sistema producía al validarse. El harness debe decidir explícitamente cómo trata estos casos: o bien captura el match del baseline como su target implícito (y entonces toda divergencia de B respecto del baseline en un caso `true` es una candidata a regresión), o bien los excluye de la matriz de transición y solo los usa para precisión global. **Recomendación: capturar el baseline como target implícito de los `true`, porque es justamente ahí donde una regresión silenciosa (bien→mal) se esconde.**
  - El harness compara a DOS niveles y reporta ambos por separado, porque "acierto a ISCO-4" y "acierto a ESCO granular" son números muy distintos (en el diccionario: 16/17 vs ~2/17) y el segundo es el estándar real de Cyn.

## 5. El contrato del harness

**Entrada**:
- Una "configuración de procesamiento" a probar. En la v1, una config es: el matcher actual + opcionalmente un **overlay** (ej. aristas argentinas inyectadas al grafo skills→ocupación, vía el monkeypatch que `exp_raiz_skills/` ya demuestra). El diseño define cómo se nombra y se pasa una config — de modo que "baseline" y "con perfil argentino inyectado" sean dos configs comparables.
- El snapshot de ground truth (sección 4).

**Salida** (en orden de importancia para decidir):
1. **Matriz de transición A→B**: por cada caso del Gold Set, su veredicto en la config A vs la config B → conteos de `mal→bien` (ganancia), `bien→mal` (REGRESIÓN), `bien→bien`, `mal→mal`. **El número de decisión no es la precisión nueva: es ganancia − regresión, con TODAS las regresiones listadas caso por caso** (oferta, esperado, A, B, método). Una regresión en un trazador conocido pesa más que varias ganancias en cola larga. *(El prototipo `harness.py` ya produce este veredicto por caso con las etiquetas CORRIGIO/EMPEORO/NO_CAMBIO/CAMBIO_NO_TARGET — sección 3.1; build solo lo generaliza a A↔B y lo reporta por nivel.)*
2. **Precisión global y por nivel** (ISCO-4 y ESCO granular), para A y para B.
3. **Desglose por método de decisión** (`regla` / `semantico` / `diccionario`): de las que acertaron/erraron, por qué vía se decidieron. Es lo que permite saber si una mejora vino del canal que el cambio tocó (semántico, en el caso del perfil argentino) o de las reglas (que no se tocaron) — sin esto, un cambio puede mover el número por azar de reglas y atribuirse mérito que no tiene. *(Disponible ya en `MatchResult.metodo` + `metadata['decision_metodo']` + `metadata['regla_aplicada']` — sección 3.2.)*

**Lo que el harness NO hace**: no decide si el trade-off ganancia/regresión vale (eso es humano); no persiste; no se conecta a la UI.

## 6. El primer uso: baseline honesto + experimento puente

- **Primer entregable de la construcción (F0.5-build)**: el **baseline** — precisión real del pipeline actual sobre los 113, a nivel ISCO-4 y ESCO, fechada. Reemplaza el 81,63% estático de diciembre (marca humana que nunca se recomputa). Será incómodo; es el cero honesto.
- **Segundo**: el **experimento puente** (Hueco 1 del índice del harness) — config B = aristas argentinas (`esco_argentino` + los 3.292 pares B_FUERTE multi-empresa del sandbox) inyectadas al grafo skills→ocupación; medir la matriz de transición contra el baseline. **Es MEDICIÓN read-only, NO intervención**: corre con el monkeypatch en memoria (patrón `exp_raiz_skills/`), no toca `match_ofertas_v3.py` productivo, no persiste, no cambia el pipeline. Calibra si el refactor vale la pena, no lo hace. Resultado: si la ganancia neta es fuerte, el refactor real de `match_ofertas_v3.py` —que es trabajo **posterior, aparte y solo si el número lo justifica**— se justifica con número; si es débil, se rediseña antes de gastar. **Construir el harness y correr el experimento puente NO modifica el procesamiento en ningún punto.**

## 7. Riesgos del diseño

- **Sesgo del instrumento**: si el harness mide al nivel equivocado (ISCO-4 cuando el estándar es ESCO) o reporta escalar sin regresiones, valida mal y no se nota. Mitigación: doble nivel + matriz de transición obligatoria.
- **Drift del ground truth**: snapshot fechado y versionado, no espejo vivo.
- **Representatividad del Gold Set**: 113 casos, sesgados a las ofertas que se validaron (no muestra aleatoria del corpus). El harness mide mejora *sobre el Gold Set*, que es necesario pero no suficiente — un cambio puede mejorar los 113 y empeorar la cola larga invisible. Se declara como límite; la extensión futura contempla una muestra aleatoria validada.
- **Acoplamiento al matcher actual**: el monkeypatch depende de la firma de `match()`. Si el Eje 4 abstrae el modelo, el harness se adapta — se diseña la interfaz para minimizar ese acoplamiento.
- **Representación heterogénea del esperado** (riesgo nuevo, surgido del inventario): el ground truth mezcla niveles y formatos — ISCO-4 como código, ESCO como etiqueta legible, y casos sin esperado explícito (sección 4). Si build compara strings ingenuamente (esco_label del matcher vs esco_esperado-label del gold) sin resolver a un identificador común, va a contar como error diferencias de redacción que no lo son. Mitigación: el doble nivel obliga a una resolución label→código explícita, y los casos `esco_ok=true` se tratan con el baseline como target implícito.

## 8. Lo que este diseño deja para decidir en la revisión

- ¿El doble nivel (ISCO-4 + ESCO) desde la v1, o ISCO-4 primero y ESCO en la extensión? (Recomendación: ambos desde v1; el dato ya está y el costo es bajo.)
- ¿Dónde viven los snapshots y los resultados? (`tests/harness/`?)
- ¿La config de "overlay de aristas argentinas" se diseña ahora o en F0.5-build? (Recomendación: el contrato ahora, la implementación en build.)

## 9. Criterio de aceptación del DISEÑO

Este documento está listo para construir cuando: el inventario de reutilización está completo, el nivel de comparación del ground truth está resuelto contra los datos reales, el contrato (entrada/salida) está revisado por el hilo del harness y por Gerardo, y las decisiones de la sección 8 están tomadas. La construcción es el spec F0.5-build.
