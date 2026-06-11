# SPEC S1.B.4 — Relevamiento de Skills

> Versión 0.1 (capa 5.1 — Memoria operativa de Gerardo + Cyn + modelo conceptual) · 2026-06-05
> Cuarto spec de la fase S1.B — Relevamiento del sistema. Releva el componente de Skills del proyecto MOL. Sigue la plantilla común del master v0.2.
> **Particularidad**: este componente tiene marco teórico propio — el "Modelo conceptual del MOL: pipeline, escenarios de skills y vocabulario vivo" v1.0 (2026-05-30), que define los 5 escenarios de skills y un mapeo de capacidades que la capa 5.2 verifica contra el código.

---

## 5.1 Memoria operativa — Gerardo + Cyn + modelo conceptual

### El marco: el modelo conceptual de los 5 escenarios

Gerardo escribió en mayo 2026 un documento conceptual que teoriza el componente de Skills a partir de 7 meses de prueba y error. Sus piezas centrales:

- **Las tareas son el ancla confiable**: las empresas describen con precisión las tareas; las skills explícitas declaradas en requisitos son mezcla heterogénea. Principio: las skills se infieren de las tareas matcheando contra la ontología vectorizada.
- **Dos naturalezas de skill**: institucionalizada (tiene URI ESCO, interoperable) vs emergente (aparece en el mercado argentino, sin URI todavía — GCP, Grafana, RAG, Bejerman, Xubio). La ausencia de URI no equivale a ausencia de valor: las emergentes son la señal anticipada del mercado.
- **Cinco escenarios** según origen (tarea vs declarada) y relación con ESCO (en canon / fuera de canon / mapeo deficiente / sin URI / genérica): A conservar · B perfil argentino → conectar a la decisión de ocupación · C1 distorsión silenciosa / C2 pérdida · D emergente → capturar · E transversal → registrar sin peso.
- **El embudo único actual**: hoy toda skill pasa por un gate ESCO-cerrado (similitud ≥0.40 o se pierde). El modelo propone reemplazarlo por ruteo explícito por escenario con centinelas en las fronteras.
- **Mapeo de capacidades (sección 6 del documento)**: CONSERVAR (extracción de skills desde tareas; ocupación granular; atributos) · CONECTAR (perfil argentino que hoy solo ajusta presentación; training data de correcciones que no alimenta mejora; ciclo de detección de frecuentes incompleto) · CREAR (registro de emergentes con identidad propia; clasificador de ruteo; centinelas; abstracción de modelos de IA) · DESCARTAR (derivación inversa ocupación→skill arbitraria; log de descartes como cementerio).
- **Principio transversal — abstracción de modelos de IA**: ningún LLM ni modelo de embeddings clavado en el código. Converge exactamente con el contexto fundante registrado en S1.B.3 ("quisimos pasar a otro modelo y nos dimos cuenta que no se puede") y con el Principio 7 de Matching.

El documento es un punto de partida que puede cambiar (palabras de Gerardo), pero define el horizonte conceptual del componente. **Verificación pendiente en 5.2: si el documento está versionado en el repo.**

### Arquitectura conceptual confirmada por Gerardo

**Las tareas NO son skills.** De las tareas se infieren los skills usando ESCO (BGE-M3 sobre la ontología vectorizada). Las skills explícitas declaradas en la oferta complementan. Coincide con el ancla del modelo conceptual.

### El diccionario argentino — origen y rol actual

- **Cómo se armó**: junto con Claude (el LLM), combinando lo que Claude sabe sobre el mercado argentino con curaduría humana. 44 ocupaciones, 291 skills.
- **Rol actual**: actúa como **boost +0.05 post-match** — ajusta la presentación después de que la ocupación ya fue decidida. El modelo conceptual identifica esto como la desconexión central (Escenario B sin conectar): el perfil argentino captura las asociaciones que la realidad local demanda, pero no participa de la decisión de ocupación. Es la intervención de mayor retorno según el modelo (Sprint 1, esfuerzo chico, avance ~60%).

### Los embeddings ESCO — generados una vez, nunca actualizados

Respuesta textual de Gerardo (SK-3): los embeddings se generaron **una sola vez desde la ontología ESCO en RDF** y nunca se pensó en su actualización ni en su almacenamiento centralizado.

Dos consecuencias que Gerardo identifica:

1. **ESCO saca versiones nuevas** y el sistema no tiene camino de actualización. La vectorización está congelada en la versión de ESCO con que se generó (¿cuál? — a verificar en 5.2).
2. **Idea arquitectónica de Gerardo**: la vectorización de ESCO debería ser un **repositorio centralizado en la máquina local** que provea vectores a todos los proyectos que los soliciten — por ejemplo, un harness en un sandbox que quiera probar contra ESCO sin regenerar todo. Hoy cada proyecto que necesita los vectores los duplica o no puede acceder.

### Las skills emergentes — estado desconocido

Gerardo cree que es deuda ("me parece que eso es deuda, no lo sé"). El sistema tiene una función `recalcular_emergentes` en Supabase con 3 versiones SQL conviviendo (hallazgo de S1.B.1, deuda D-07 de BD). El modelo conceptual dice que existe "un mecanismo de detección de skills frecuentes y un panel de aprobación humana, pero la cadena posterior a la aprobación está cortada" (Sprint 3, avance ~15%). A verificar en 5.2: qué existe realmente y en qué estado.

### El LoRA perdido (registrado también en S1.B.3)

El modelo fine-tuneado de mayo se hizo en disco C, se borró sin querer, no quedó nada. `data/finetuning/matching/` vacío. Se registra acá porque el fine-tuning era del componente de skills/matching semántico.

### La experiencia de Cyn con las skills (validadora humana)

- **Calidad de extracción**: mezclada. "Algunas skills salen de una palabra suelta y no de la tarea completa" — coincide con el patrón de error del matching (palabra puntual vs contexto).
- **Explícitas vs implícitas**: las explícitas (declaradas en el aviso) andan mejor que las implícitas (inferidas).
- **Evolución que Cyn nota**: antes el sistema inventaba skills que no estaban; ahora el problema dominante es la **omisión** — faltan skills que sí están en el aviso.
- **Duplicadas**: no ve duplicadas (ej. "Excel" y "Microsoft Excel" a la vez).
- **Su herramienta de trabajo está rota para skills**: **no puede agregar skills faltantes ni borrar incorrectas desde la UI**. Trabaja copiando todo al campo "observaciones" como texto libre y justificando por escrito. La validadora del sistema trabaja alrededor de la herramienta, no con ella. (Deuda de UI, S1.B.7, registrada también en S1.B.3 D-09.)

### Lo que Gerardo no sabe (a verificar en 5.2)

- **Gold set de skills** (`tests/nlp/gold_set.json`, 49 casos): cree que son de matching, una parte hecha a mano. Relación real con los gold sets de matching: a verificar.
- **`filtrar_por_trust`** (método eliminado del extractor, detectado en drift de tests): Gerardo ni sabía que existía.
- **Diccionarios de skills vivos vs abandonados**: no sabe cuáles son los vigentes.

### Hipótesis tentativas para la capa 5.2

1. **El mapeo de capacidades del modelo conceptual (sección 6) es verificable contra el código**: las 3 capacidades a CONECTAR existen pero desconectadas; las 4 a CREAR no existen; las 2 a DESCARTAR existen y estorban. La 5.2 confirma o corrige ese mapa.
2. **El gate del embudo único (similitud ≥0.40) existe en el código** y es el punto donde hoy se pierden las emergentes.
3. **El "log de descartes como cementerio"** del modelo conceptual probablemente se relacione con la tabla `validation_errors` (278K filas, sorpresa de S1.B.1) o con un log propio del extractor de skills.
4. **La vectorización ESCO no registra de qué versión de ESCO proviene** ni cuándo se generó — sin trazabilidad de origen.

### Notas para fases posteriores

- **Repo centralizado de vectores ESCO** (idea de Gerardo): principio arquitectónico para la 5.4 y candidato a spec propio en la reparación.
- **La conexión del perfil argentino a la decisión** (Sprint 1 del modelo) es la intervención de mayor retorno identificada — pero se diseña en S1.C con el cuadro completo, no acá.
- **Deuda de UI para skills** (no poder agregar/borrar): pertenece a S1.B.7.

---

## 5.2 Estado actual relevado (verificado contra el código, solo lectura)

> Relevamiento read-only sobre el árbol de trabajo y la BD local (`database/bumeran_scraping.db`, `mode=ro`). Lo que vive en Supabase y no es reconstruible desde el repo se marca como **no verificable sin conexión viva**.

### 5.2.1 Flujo real tarea → skill y el embudo

**Extractor**: `database/skills_implicit_extractor.py`, clase `SkillsImplicitExtractor`. **VERSION = "2.9.0"** (SPEC K — "L2 compatibility filter"). Entry points: `extract_from_tasks()`, `extract_skills()`, `extract_skills_dual()`. Lo invocan `database/match_ofertas_v3.py` y `database/process_nlp_from_db_v11.py`.
- **Drift de versión (instancia menor de D-15)**: CLAUDE.md declara v2.4; el docstring de cabecera del módulo dice `2.0.0`; la clase dice `2.9.0`. Tres números distintos para el mismo archivo. La fuente real es la constante de clase: **2.9.0**.

**El embudo NO es un solo gate de 0.40 — son tres capas superpuestas:**
1. `DEFAULT_THRESHOLD = 0.40` — gate de similitud BGE-M3 base (confirma el ≥0.40 del modelo conceptual). Comentario en código: el umbral es bajo porque sin LoRA fine-tuned los scores caen.
2. `UMBRAL_NLP_INDIVIDUAL = 0.45` + **modo "salvavidas"** anti-alucinación: si la mediana de similitud de la oferta cae por debajo del umbral-oferta, asume que el LLM alucinó masivamente y descarta casi todo salvo lo de score muy alto.
3. **Trust classifier** (`_classify_skill_trust`, SPEC B v2): clasifica por `origen` y largo de `texto_fuente`, sin consultar ESCO ni ISCO.

**El "cementerio" existe, está poblado y NO es `validation_errors`** (refuta hipótesis 3 de la 5.1): es la tabla dedicada **`skills_extraction_failures`** — **7.564 filas**, columnas estructuradas (`tarea_texto`, `mejor_skill_uri`, `mejor_score`, `gap_al_umbral`, `tipo_falla`). La pueblan `match_ofertas_v3.py:1453` y `process_nlp_from_db_v11.py:489` con `track_failures=True`. **Nadie la recupera ni reutiliza**: solo `sync_learnings.py` lee su conteo para métricas. Es un cementerio en el sentido literal del modelo conceptual: registro de descartes que no vuelve a entrar a ningún lado.

**El origen SÍ se registra** (refina el modelo conceptual, que lo pedía como capacidad a CREAR): la señal de ruteo tarea-vs-declarada **ya está en el dato**. Ver 5.2.4 para la verificación de consistencia.

**`filtrar_por_trust` — REFUTA la memoria de Gerardo**: no fue eliminado. Es un parámetro vivo (default `False`), agregado por SPEC B v2 (commit `e2ad5845`), única vez que se tocó en la historia del archivo. Con default `False` solo anota `trust_motivo` como telemetría; no descarta nada. Gerardo "ni sabía que existía" porque nunca se activó — está construido pero apagado (variante de D-15).

**Modelo conceptual**: ❌ **no está versionado en el repo** (verificado con `git ls-files`). El PDF v1.0 (2026-05-30) existe solo fuera del repo.

### 5.2.2 Vectorización ESCO y perfil argentino

**REFUTA parcialmente la memoria SK-3 de Gerardo** ("una sola vez desde el RDF, sin trazabilidad, congelado en el pasado"): existe `database/embeddings/corpus_manifest.json` con trazabilidad completa:

| | esco_skills | esco_occupations |
|---|---|---|
| shape | **[14257, 1024]** | **[3046, 1024]** |
| model | `BAAI/bge-m3` | `BAAI/bge-m3` |
| model_revision | `5617a9f6…` | `5617a9f6…` |
| generated_at | **2026-04-24T23:03** | 2026-04-24T23:09 |
| generated_by | `LOCAL:spec_e_fase_1` | `LOCAL:spec_e_fase_1` |
| source_table | `esco_skills_enriched` | `esco_occupations_enriched` |
| checksum_sha256 | presente | presente |

Matices:
1. Los embeddings **se regeneraron en SPEC E el 2026-04-24** — no son del pasado lejano congelado. Hay un mecanismo de regeneración (existe `scripts/upload_skills_embeddings.py`, `scripts/extract_skills_from_rdf.py`) y un `corpus_manifest.json` con checksum que `_check_corpus_sha()` compara contra el modelo en cache.
2. PERO el manifest **no estampa la release de ESCO** (¿v1.2.0?): registra `source_table` + `source_count`, no el tag de versión de ESCO. → Hipótesis 4 **parcialmente refutada**: hay trazabilidad de *generación* (modelo, revisión, fecha, checksum, fuente), falta trazabilidad de la *versión de ESCO* de origen.

**Ubicación**: archivos `.npy` + `.json` en `database/embeddings/` (local; el matcher NO usa pgvector para esto). Los activos de ocupaciones son **symlinks → `enriched/`**. Co-existen artefactos de varias épocas (enero, febrero, abril) en el mismo directorio — posibilidad de confusión sobre cuál es el vigente (D-15).

**Perfil argentino / boost +0.05 — CONFIRMA el modelo conceptual (Escenario B sin conectar)**: `rerank_with_argentino_boost()` (línea 1267) carga `esco_argentino` desde Supabase; `boost_factor = 0.05 * (frequency / max_frequency)`. Se invoca en `match_ofertas_v3.py:1820` **después** de que `result.esco_uri` ya fue decidido — usa la ocupación ya elegida (`occupation_uri = result.esco_uri`) para re-rankear la *lista de skills*. **No participa de la decisión de ocupación**, confirmado en código. No está flag-gateado en este path, pero depende de cargar `esco_argentino` de Supabase viva; si falla, el cache queda vacío → sin boost.

**Repo centralizado de vectores (idea de Gerardo)**: hoy NO existe. Los `.npy` viven en `database/embeddings/` del proyecto; cualquier otro proyecto/harness que los necesite los duplicaría o no podría acceder. La preocupación de Gerardo está bien fundada — no hay servicio ni ubicación compartida.

### 5.2.3 Emergentes, cementerio y cadenas cortadas

**`recalcular_emergentes` — tres versiones SQL coexisten** (confirma D-07 de BD), activa la v3:
- `028_emergentes_pendientes.sql` (2026-03-22) · `043_recalcular_emergentes_v2.sql` (2026-03-31) · `050_fix_recalcular_emergentes_v3.sql` (2026-04-09, vigente).
- Define "emergente" como: skill cuya **frecuencia ≥30%** dentro de un ISCO (con ≥10 ofertas) y que NO está en el `perfil_skills` de esa ocupación. El v3 corrige tres bugs reales del v2 (isco_code NULL, parsing JSONB roto, doble nombre de campo URI). Es un componente que se reparó iterando, no abandonado.

**El panel de aprobación humana EXISTE** (refina el modelo conceptual): UI en `app/admin/skills/page.tsx`, API `app/api/emergentes-pendientes/route.ts` (GET lista vía RPC `get_emergentes`; PATCH aprobar/rechazar).

**La cadena posterior a la aprobación NO está cortada — está cableada a buffers que no se descargan** (refina con precisión el "Sprint 3, cadena cortada" del modelo). Al aprobar, el endpoint llama `aprobar_emergente_con_triggers` (RPC definida y desplegada en `057_e24_downstream_triggers.sql`), que ejecuta 4 triggers transaccionales:
- **T1 → `esco_argentino.skills_consolidadas`**: la skill entra al perfil argentino… que solo alimenta el boost +0.05 post-match (5.2.2). Dead-end respecto de la decisión de ocupación.
- **T2 → `approved_training_pairs`**: inserta un par contrastivo en una tabla **distinta** de `config/training_pairs.json` (S1.B.3). Hay ahora **dos almacenes de training pairs**, y ningún fine-tuning consume ninguno (LoRA ausente). Dead-end.
- **T3 → `pipeline_commands`**: encola un comando para el poller local. Es la única conexión real de vuelta a producción — pero depende de que el gateway local lo ejecute (no verificable read-only).
- **T4 → alerta**.

Conclusión: la cadena de emergentes está **más construida de lo que el modelo conceptual asume** (tabla + 4 triggers desplegados), pero termina en los mismos dos buffers que S1.B.3 identificó como rotos: perfil argentino (solo post-match) y training pairs (sin fine-tuning). No es "cadena cortada"; es "cadena cableada a destinos que no retroalimentan la decisión".

**Estado de la tabla de emergentes** (cuántas pendientes/aprobadas): vive en Supabase → **no verificable sin conexión viva**.

**Derivación inversa ocupación → skill (categoría DESCARTAR del modelo)**: existe `filter_skills_by_l2_compatibility()` (SPEC K) + `_l2_compatible()`. Carga `esco_occupation_skills.json` (essential/optional por ocupación) y **descarta** skills cuya categoría L2 sectorial (S*/K) no esté en el set de la ocupación target ni de su grupo ISCO-4. Matiz importante: es un **filtro de compatibilidad** (poda lo incoherente, permisivo si falta metadata del target), **no una generación arbitraria** de skills desde la ocupación. El modelo conceptual lo etiqueta como "derivación inversa a descartar"; el código real es más defendible (constraint vía ESCO oficial), pero comparte el riesgo: usa el grafo EU de associations para podar señal AR (converge con el diagnóstico de `[[project_perfil_argentino_matcher]]`).

### 5.2.4 Gold set, contrato con matching y verificación del mapeo conceptual

**Gold set** (`tests/nlp/gold_set.json`): **49 casos**. Es un gold set de **NLP**, pero su bloque `expected` **sí incluye skills**: `skills_tecnicas_list`, `soft_skills_list`, `herramientas_list` (además de los 17 campos NLP restantes). Confirma a medias la intuición de Gerardo ("cree que son de matching"):
- **Mismo universo de ofertas que el gold set de matching**: overlap **49/49** con `database/gold_set_manual_v2.json`. Son las mismas 49 ofertas, validadas en dos capas distintas (NLP+skills vs ISCO).
- **Antigüedad (D-15)**: último commit que lo tocó `3d3b7807` (refactor 3-fases); creado en `3f0069dc` ("NLP v10"). Está congelado en la era **NLP v10**, mientras producción corre **v11.4**. El harness de skills valida contra expectativas viejas — mismo patrón que el gold set de matching en S1.B.3.

**Contrato Skills → Matching** (qué consume el matcher): `match_ofertas_v3.py` invoca al extractor y recibe `skills_extracted` (lista de dicts con `skill_label`, `origen`, `score`, `uri`), la re-rankea con el boost argentino y la persiste. Persistencia en dos tablas:
- `ofertas_esco_skills_detalle` (**1.569.227 filas**): `esco_skill_uri`, `match_score`, `match_method`, `skill_tipo_fuente`, `is_essential/optional_for_occupation`, `source_classification`.
- `ofertas_skills` (consumida por `recalcular_emergentes` y el dashboard).

Relación con el `esco_code` granular perdido (D-01 de Matching): el lado skills **sí persiste URIs de skill** correctamente (`esco_skill_uri`), distinto del `esco_code` de *ocupación* que MatchResult perdía. NO comparte el bug puntual, pero **sí comparte el patrón**: señal granular calculada en runtime que se aplana al cruzar el borde a BD (ver `origen_tipo` abajo).

**Verificación de consistencia de la señal de origen (adición de Gerardo):**
- ⚠️ **Dos columnas de origen coexisten, una viva y una muerta:**
  - `origen_tipo`: **100% "semantico"** en las 1.569.227 filas. Columna **muerta** — no la escribe ningún script de `database/` ni `scripts/exports/`; quedó clavada en un valor único.
  - `skill_tipo_fuente`: **la señal real**, **11 valores distintos, 0 nulos/vacíos**. Distribución:

    | skill_tipo_fuente | filas | % |
    |---|---|---|
    | tarea | 708.061 | 45,1% |
    | semantico | 278.602 | 17,8% |
    | skills_nlp | 156.215 | 10,0% |
    | titulo | 141.021 | 9,0% |
    | skills_nlp_declarada | 112.241 | 7,2% |
    | soft_skill_declarada | 72.231 | 4,6% |
    | terminologia | 30.402 | 1,9% |
    | soft_skills_nlp | 24.512 | 1,6% |
    | regla | 21.666 | 1,4% |
    | tecnologia_declarada | 14.478 | 0,9% |
    | herramienta_declarada | 9.798 | 0,6% |

  - **Lectura**: la señal de ruteo está **limpia y poblada** (sin nulos), y **`tarea` domina con 45%** — confirma empíricamente el ancla "las tareas son la fuente de verdad". La distribución tarea/título/declarada/regla es exactamente la materia prima que el ruteo por escenarios del modelo conceptual necesitaría. El obstáculo no es la calidad del dato sino que hay **dos columnas y la documentada (`origen_tipo`) es la muerta** — riesgo de que el ruteo futuro lea la columna equivocada.
- 🔴 **`regla_cynthia` y `regla_issue` = 0 filas persistidas.** El trust classifier los incluye en su whitelist de "origen confiable", pero **ningún dato real los lleva**. El rastro del feedback humano de Cyn **no existe dentro del dato de skills**: el origen `regla` (21.666) es genérico y no distingue corrección humana de regla automática. Converge con el hallazgo de S1.B.3: las correcciones de Cyn se acumulan en `issues`/observaciones-texto-libre y **no bajan al grano de la skill**. La señal de feedback humano está prevista en el código pero vacía en la práctica.

**Mapeo de capacidades (sección 6 del modelo conceptual) verificado contra el código:**

| Capacidad (modelo) | Categoría | Estado REAL verificado |
|---|---|---|
| Extracción de skills desde tareas | CONSERVAR | ✅ Existe y funciona (`tarea`=45% de la señal, ancla confirmada) |
| Ocupación granular (esco_code) | CONSERVAR | ⚠️ Existe pero se pierde al persistir la ocupación (D-01 de Matching) |
| Atributos de skill (essential/optional, L1/L2) | CONSERVAR | ✅ Persistidos en `ofertas_esco_skills_detalle` |
| Perfil argentino → decisión de ocupación | CONECTAR | 🔴 Existe **desconectado**: solo boost +0.05 post-match |
| Training data de correcciones → mejora | CONECTAR | 🔴 Existe **desconectado**: 2 almacenes (`training_pairs.json` + `approved_training_pairs`), ningún fine-tuning los consume |
| Ciclo de detección de frecuentes | CONECTAR | 🟡 Más completo de lo asumido: detección + panel + 4 triggers; pero los triggers terminan en buffers sin descarga |
| Registro de emergentes con identidad propia | CREAR | 🔴 No existe: skill sin URI muere en `skills_extraction_failures` (7.564) o se fuerza a la ESCO más cercana (cf. `[[project_escenarios_skills_sin_uri]]`) |
| Clasificador de ruteo por escenario | CREAR | 🟡 La señal de entrada (`skill_tipo_fuente`) **ya existe limpia**; el clasificador que la consuma, no |
| Centinelas en las fronteras | CREAR | 🔴 No existen |
| Abstracción de modelos de IA | CREAR | 🔴 No existe: `BAAI/bge-m3` y la ruta LoRA están clavados como constantes de clase |
| Derivación inversa ocupación→skill arbitraria | DESCARTAR | 🟡 Existe como **filtro** L2 (SPEC K), no como generación arbitraria; defendible pero poda señal AR con grafo EU |
| Log de descartes como cementerio | DESCARTAR | 🔴 Existe y estorba: `skills_extraction_failures` (7.564 filas) acumula sin reuso |

### 5.2.5 Hipótesis refinadas (para 5.3/5.4, que se trabajan con Gerardo)

1. **El cuello de botella no es la calidad de la señal de origen — es su consumo y su duplicación.** `skill_tipo_fuente` está limpia (11 valores, 0 nulos, `tarea` dominante). Falta el ruteo que la lea, y sobra la columna muerta `origen_tipo` que la documentación señala como la buena.
2. **El feedback humano de Cyn no baja al grano de la skill.** `regla_cynthia`/`regla_issue` están previstos pero vacíos; las correcciones quedan en texto libre. Es el mismo break de loop de S1.B.3, visto desde el dato de skills.
3. **La cadena de emergentes está cableada, no cortada — pero a destinos muertos.** Reparar emergentes ≠ construir la cadena (ya existe); = **drenar los buffers** (perfil argentino → decisión; training pairs → fine-tuning). Converge con la intervención de mayor retorno del modelo (conectar el perfil argentino).
4. **La vectorización ESCO tiene trazabilidad de generación pero no de versión de ESCO**, vive duplicable en `database/embeddings/`, y los modelos están clavados como constantes. El "repo centralizado de vectores" de Gerardo y la "abstracción de modelos de IA" del modelo conceptual son el mismo principio visto desde dos lados.
5. **D-15 ("construido una vez y abandonado") se confirma por cuarta vez consecutiva** en este componente: `filtrar_por_trust` apagado, `origen_tipo` muerta, gold set congelado en NLP v10, embeddings multi-época en un mismo directorio, drift de versión 2.0/2.4/2.9, cementerio sin reuso, dos almacenes de training pairs.

---

> *Versión 0.2 — Capas 5.1 y 5.2 cerradas (fuentes: Gerardo + Cyn + modelo conceptual v1.0; 5.2 verificada read-only contra código y BD local). Capas 5.3 (deuda observada) y 5.4 (principios) pendientes — se trabajan con Gerardo. Acción pendiente con conexión viva: estado de la tabla de emergentes en Supabase.*

---

## 5.3 Deuda observada

Registro de problemas detectados durante el relevamiento de Skills, **sin priorización ni propietario asignado en esta etapa**. La priorización y el diseño de reparaciones se harán en S1.C — Master de reparación, cuando los 7 specs estén cerrados. Tocar Skills aisladamente sería peinar al muerto: su señal de origen alimenta el ruteo futuro, su cementerio es materia prima de las emergentes, su contrato alimenta al matcher, y sus cadenas muertas convergen con el loop roto relevado en Matching.

Las deudas están organizadas en categorías para legibilidad, sin orden de prioridad entre ellas.

### Categoría A — Señal y contrato de datos

#### D-01 — Columna documentada muerta, señal real sin documentar
`origen_tipo` está 100% en "semantico" (nadie la escribe) y es la columna que la documentación trata como la buena. La señal real y limpia vive en `skill_tipo_fuente` (11 valores, 0 nulos, distribución: tarea 45,1% › semantico 18% › skills_nlp 10% › titulo 9% › declaradas › regla 1,4%). La señal que el modelo conceptual pedía crear ya existe — pero el mapa oficial apunta al lugar equivocado.
**Componentes involucrados**: skills, NLP, documentación, el futuro clasificador de ruteo.
**Por qué no se prioriza acá**: la consolidación de la señal se diseña junto con el ruteo por escenario (cuadro completo en S1.C).

#### D-02 — `regla_cynthia` / `regla_issue` con 0 filas
Los valores existen en el trust classifier pero nunca se escribieron: el rastro del feedback humano de Cyn no baja al grano de la skill. Converge con D-04 de Matching (loop roto en la segunda mitad).
**Componentes involucrados**: skills, matching, UI, proceso de feedback.
**Por qué no se prioriza acá**: es parte del cierre del loop de aprendizaje, que se diseña en S1.C con todas sus piezas a la vista.

### Categoría B — Embudo y cementerio

#### D-03 — Cementerio estructurado sin reutilización
`skills_extraction_failures`: 7.564 filas con columnas ricas (tarea_texto, mejor_skill_uri, mejor_score, gap_al_umbral, tipo_falla). La pueblan dos entry points con `track_failures=True`; solo `sync_learnings.py` lee el conteo para métricas. Nadie recupera ni reutiliza el contenido. Es la materia prima del Sprint 0 del modelo conceptual (captura de emergentes) ya acumulada y desaprovechada.
**Componentes involucrados**: skills, proceso operativo, ciclo de emergentes.
**Por qué no se prioriza acá**: la captura de emergentes con identidad propia es diseño del S1.C (Sprint 0 del modelo conceptual).

#### D-04 — El filtro de compatibilidad L2 poda señal argentina con el grafo europeo
Lo que el modelo conceptual etiquetaba "derivación inversa arbitraria" resultó ser un filtro de compatibilidad L2 (SPEC K, anti-ruido) — más defendible de lo asumido. Pero filtra usando las asociaciones skill→ocupación de ESCO (europeas) exactamente donde el Escenario B del modelo dice que la divergencia argentina es dato, no ruido.
**Componentes involucrados**: skills, matching, perfil argentino.
**Por qué no se prioriza acá**: decidir si el filtro se recalibra, se condiciona al perfil argentino o se retira requiere el diseño del ruteo completo.

### Categoría C — Emergentes

#### D-05 — Cadena de emergentes cableada a buffers muertos
Refinamiento del modelo conceptual (que la daba por "cortada"): la cadena está más construida de lo asumido. El panel de aprobación existe y `aprobar_emergente_con_triggers` (migración 057) dispara 4 triggers — pero T1 va al perfil argentino (que solo actúa post-match, no decide), T2 a `approved_training_pairs` (que ningún fine-tuning consume), T3 a `pipeline_commands` (única conexión real, dependiente del poller). No está cortada: está conectada a destinos que no consumen. Rompe en los mismos dead-ends que el loop de Matching.
**Componentes involucrados**: skills, matching, pipeline, UI.
**Por qué no se prioriza acá**: cerrar la cadena requiere decidir los consumidores finales (fine-tuning, decisión de ocupación), diseño de S1.C.

### Categoría D — Vectorización

#### D-06 — El manifest de embeddings no estampa la release de ESCO
`corpus_manifest.json` tiene trazabilidad de generación (BAAI/bge-m3, revisión, 2026-04-24, checksum, source_table) — mejor de lo que la memoria recordaba. Pero no registra de qué versión/release de ESCO provienen los vectores. ESCO publica versiones nuevas y no hay forma de saber contra cuál está vectorizado el sistema.
**Componentes involucrados**: skills, taxonomía ESCO.
**Por qué no se prioriza acá**: se resuelve junto con el diseño del repositorio centralizado (D-07).

#### D-07 — Sin repositorio centralizado de vectores ESCO
Idea arquitectónica de Gerardo (capa 5.1): la vectorización de ESCO debería ser un repositorio único en la máquina local que sirva vectores a todos los proyectos que los soliciten (producción, sandbox de escenarios, harness futuro). Hoy cada proyecto duplica o no accede.
**Componentes involucrados**: arquitectura del proyecto, todos los consumidores de embeddings.
**Por qué no se prioriza acá**: es decisión de arquitectura transversal, propia de S1.C.

#### D-08 — Embeddings multi-época conviviendo en un directorio
`database/embeddings/` acumula generaciones distintas (activos de ocupaciones como symlinks → `enriched/`). Sprawl que dificulta saber qué está vivo.
**Componentes involucrados**: skills.
**Por qué no se prioriza acá**: limpieza menor, se resuelve con el diseño de D-07.

### Categoría E — Gold set

#### D-09 — El gold set de skills no existe como tal
`tests/nlp/gold_set.json` son las mismas 49 ofertas del gold set de matching (overlap 49/49), congeladas en era NLP v10 mientras producción corre v11.4. No hay un gold set propio del componente de skills: el sistema valida skills con un set pensado para otra cosa y desactualizado dos versiones.
**Componentes involucrados**: skills, NLP, tests, proceso de validación.
**Por qué no se prioriza acá**: la consolidación de gold sets es transversal (D-02 de Matching) y se diseña con fuente única en S1.C.

### Categoría F — Versionado

#### D-10 — Drift de versión del extractor
Tres versiones declaradas conviviendo: docstring del módulo 2.0.0, CLAUDE.md v2.4, clase `VERSION = "2.9.0"` (SPEC K). La fuente de verdad es la clase, pero nada lo hace explícito.
**Componentes involucrados**: skills, documentación.
**Por qué no se prioriza acá**: deuda documental menor; se resuelve con la disciplina de versionado ya aplicada al matcher (archivo VERSION).

### Categoría G — Training pairs duplicados

#### D-11 — Dos almacenes de training pairs, ninguno consumido
`training_pairs.json` (local) y `approved_training_pairs` (Supabase, destino del trigger T2). Ninguno alimenta fine-tuning alguno. Converge con D-04 de Matching y con el LoRA perdido: el sistema acumula material de entrenamiento en dos lugares y no entrena.
**Componentes involucrados**: skills, matching, proceso operativo.
**Por qué no se prioriza acá**: parte del cierre del loop de aprendizaje (S1.C).

### Categoría H — Patrón sistémico

#### D-12 — Patrón "construido una vez y abandonado": cuarta aparición consecutiva
Siete instancias en este componente: (1) `filtrar_por_trust` apagado desde su creación — **variante nueva del patrón: "construido y nunca encendido"**; (2) `origen_tipo` columna muerta; (3) gold set congelado en v10 con producción en v11.4; (4) embeddings multi-época sin limpieza; (5) drift de versión 2.0/2.4/2.9; (6) cementerio estructurado sin reuso; (7) dos almacenes de training pairs.
**Componentes involucrados**: todos. Es transversal.
**Por qué no se prioriza acá**: se cruza en S1.C con las instancias de BD, Scraping y Matching. Con cuatro componentes confirmados, el patrón es la regla del proyecto, no la excepción.

---

## 5.4 Principios de diseño objetivo

Principios generales de cómo debería comportarse el componente de Skills cuando esté sano. **No es diseño detallado** — eso surge del master S1.C. Estos principios son el norte conceptual.

### Principio 1 — Una sola columna de verdad por señal
Cada señal del sistema vive en un lugar, documentado y consumido. Las columnas muertas se retiran. Documentación que apunta a la columna equivocada es peor que no tener documentación: produce decisiones sobre datos que nadie escribe.

### Principio 2 — El cementerio es materia prima, no destino final
Toda skill descartada queda disponible para el ciclo de emergentes con su contexto completo (gap al umbral, tipo de falla, origen). Un descarte sin posibilidad de recuperación es información destruida; el sistema sano convierte sus fallas en su mejor fuente de descubrimiento.

### Principio 3 — Las cadenas terminan en consumidores reales
Un trigger que descarga en un buffer que nadie lee da apariencia de conexión sin conexión. Cadena que no llega a producción es cadena que no existe. El sistema sano no tiene buffers terminales: todo lo que se acumula tiene un consumidor definido o no se acumula.

### Principio 4 — Vectorización con trazabilidad completa, servida centralizadamente
Cada corpus de embeddings registra modelo, revisión, fecha, checksum y release de la taxonomía de origen. Un repositorio local único sirve los vectores a todos los proyectos (producción, harness, sandbox) — regenerar es una operación trazable, no un ritual artesanal.

### Principio 5 — Gold set propio por componente, sincronizado con producción
Cada componente valida contra un gold set propio, versionado y alineado con la versión que corre en producción. Un gold set congelado dos versiones atrás valida un sistema que ya no existe.

### Principio 6 — La señal argentina no se poda con el grafo europeo
Donde la realidad local diverge del canon ESCO (Escenario B del modelo conceptual), la divergencia es dato, no ruido a filtrar. Los filtros de compatibilidad reconocen el perfil argentino antes de podar.

### Principio 7 — Lo apagado se decide: se enciende o se retira
Un flag dormido desde su creación no es opcionalidad, es deuda con apariencia de feature. El sistema sano revisa periódicamente sus capacidades latentes y decide: a producción o afuera.

---

> *Spec S1.B.4 — Skills: capas 5.1 (Gerardo + Cyn + modelo conceptual), 5.2, 5.3 y 5.4 cerradas. Las 12 deudas observadas se vuelcan al master S1.C. Los 7 principios son input del diseño objetivo. D-12 confirma el patrón transversal por cuarta vez consecutiva, sumando la variante "construido y nunca encendido". Hallazgo central del spec: el sistema está más construido y menos conectado de lo que el propio modelo conceptual suponía — la categoría CONECTAR crece, la categoría CREAR se achica.*
