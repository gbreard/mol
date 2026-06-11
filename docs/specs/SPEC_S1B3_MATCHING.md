# SPEC S1.B.3 — Relevamiento de Matching

> Versión 0.1 (capa 5.1 — Memoria operativa de Gerardo + Cyn) · 2026-06-05
> Tercer spec de la fase S1.B — Relevamiento del sistema. Releva el estado actual del matching del proyecto MOL. Sigue la plantilla común definida en `docs/specs/MOL_master_relevamiento.md` v0.2.
> **Novedad**: la capa 5.1 integra dos fuentes — Gerardo (memoria técnica) y Cynthia (validadora humana, experiencia de uso diaria, cuestionario respondido por escrito el 2026-06-05).

---

## 5.1 Memoria operativa — Gerardo + Cyn

### Contexto fundante: por qué existe este relevamiento

Frase textual de Gerardo (2026-06-05): **"Todo este quilombo nace porque quisimos pasar a otro modelo y nos dimos cuenta que no se puede."**

El proyecto intentó migrar de modelo y descubrió que el sistema no estaba en condiciones de soportar el cambio. De ahí nace toda la fase de setup y relevamiento. Esto define el norte del diseño objetivo final: **un sistema donde cambiar de modelo sea posible**.

### Lo que Gerardo sabe (y lo que no) del matcher

- **Versión real (3.5.4 según doc vs 3.5.5 según archivo `MATCHER_VERSION`)**: Gerardo no sabe cuál corre en producción. A verificar en capa 5.2.
- **Reglas R-XXX** (quién las crea, cuándo, cómo se mantienen): a relevar por Claude Code.
- **Regresión R240** (la regla devuelve `esco_code = None` donde el gold set espera `9329.1`, detectada en los tests del 2026-06-03): a Gerardo no le suena la regla. A investigar en capa 5.2.
- **Tabla `ofertas_matching_history`** (111.357 filas en BD local): Gerardo no recuerda qué guarda.

### El Gold Set ampliado — historia conocida, ubicación desconocida

- El Gold Set se amplió hace aproximadamente un mes (mayo 2026) durante el fine-tuning del LoRA. **El propio modelo propuso casos**, se validaron, se agregaron. Pasó de 49 casos a **más de 100**.
- **Gerardo no sabe dónde está físicamente hoy** el Gold Set ampliado (¿archivo no versionado? ¿Supabase? ¿planilla?). El archivo del repo (`database/gold_set_manual_v2.json`) sigue en 49.
- Cyn recuerda que se agregaron al menos dos ofertas específicas: **una de Sommelier y otra de Carnicero**. Estas dos sirven como trazadores para encontrar el Gold Set ampliado: donde estén esos casos, ahí está la versión ampliada.

### La experiencia de Cyn con el matching (validadora humana)

**Frecuencia de errores**: "Seguido. Me pasa bastante encontrar ocupaciones ESCO que están claramente mal asignadas."

**El patrón de error dominante**: el sistema asigna una **ocupación parecida pero no la correcta**. El mecanismo que Cyn observa: **"el sistema parece quedarse con una palabra puntual del aviso y no con el contexto completo."**

**Ejemplos concretos documentados por Cyn**:
- Aviso "Sobrestante de obra" → el sistema asignó "7111 constructor inmobiliario/constructora inmobiliaria" (incorrecto).
- Aviso "Ing. eléctrica o electromecánica" → asignó "7412 mecánico electricista/mecánica electricista" (incorrecto: confunde nivel profesional con nivel técnico/oficio).

**Tipos de ofertas que siempre fallan**: aquellas donde el título puede confundirse con otra ocupación, o donde el sistema toma una palabra puntual en lugar del contexto.

**Lo que Cyn pide que el sistema entienda** (su respuesta N-5, aplica directamente al matching): extraer mejor **la acción principal, el objeto de trabajo, el nivel del rol y el contexto del aviso**. Su ejemplo: "no es lo mismo instalar iluminación en una vivienda que instalar iluminación para shows o eventos. La acción puede parecer parecida, pero la ocupación correcta cambia según el sector y el objeto de trabajo."

### El hallazgo doble: el loop de aprendizaje no existe

Dos fuentes independientes confirman la misma deuda desde ángulos distintos:

- **Cyn (experiencia)**: "En la mayoría de los casos siento que el sistema vuelve a cometer el mismo error. Aunque una oferta se corrija manualmente, después aparecen casos parecidos con el mismo problema. Mi impresión es que la corrección manual todavía no siempre se transforma en una regla que el sistema aplique después."
- **Gerardo (técnica)**: el pipeline de feedback está **desconectado** — las correcciones de Cyn no vuelven al NLP/matcher de forma automática.

La percepción de Cyn tiene explicación técnica exacta: el sistema no aprende porque el loop no existe. Las correcciones se acumulan como issues pero no se transforman en mejoras del sistema.

### Las herramientas de validación de Cyn — deuda de UI que afecta al matching

- **Las correcciones no quedan visibles en la oferta**: cuando Cyn corrige una ocupación, la corrección se envía como issue, pero si vuelve a entrar a la oferta la ve igual que al principio. No puede hacer seguimiento ni reutilizar el criterio en casos parecidos.
- **Pedido explícito de Cyn (su cambio número uno)**: historial visible de correcciones dentro de la oferta — qué trajo el sistema, qué corrigió, qué observación dejó, cuál fue la validación final. Más estados claros por oferta (pendiente / en revisión / corregida / finalizada).
- **Bug de UX que hace perder trabajo**: al guardar una corrección, el sistema **cambia automáticamente a otra oferta**. Si Cyn no está muy atenta, la corrección queda incompleta sin que se dé cuenta. Es pérdida silenciosa de trabajo humano validado.
- **Filtros imprecisos**: muchas ofertas filtradas no corresponden al sector que Cyn está trabajando; pierde tiempo revisando ofertas que no deberían estar en el filtro.

Estas deudas son de UI (S1.B.7) pero afectan directamente la calidad y eficiencia de la validación de matching, por eso se registran acá también.

### Convergencia de principio: trazabilidad

El pedido número uno de Cyn (historial de correcciones visible) y el pedido de Gerardo registrado en el spec de Scraping (seguir una oferta a través del pipeline completo) son **el mismo principio desde dos usuarios distintos: trazabilidad**. Esto lo eleva a principio de diseño de primer orden para el sistema entero.

### Hipótesis tentativas para la capa 5.2

Son hipótesis, no conclusiones. La verificación debe confirmarlas, refutarlas o refinarlas:

1. **La regresión R240 podría ser síntoma del Gold Set desincronizado**: el archivo versionado dice 49 casos, la realidad operativa es 100+. Los tests corren contra una mezcla de expectativas viejas y nuevas. R240 podría ser una regla correcta evaluada contra una expectativa obsoleta, o viceversa.
2. **El Gold Set ampliado existe en algún lado**: Supabase (tablas de validación), archivos no versionados en el working tree, exports, planillas. Los casos "Sommelier" y "Carnicero" son los trazadores para encontrarlo.
3. **El camino del issue de Cyn termina en una tabla y no vuelve**: la corrección se guarda (probablemente en la tabla `issues` de Supabase) pero ningún proceso la transforma en regla, ajuste o entrenamiento del matcher. A verificar el camino completo.

### Notas para fases posteriores

- **Deuda de UI registrada acá pero perteneciente a S1.B.7**: correcciones no visibles, bug del cambio automático de oferta, filtros imprecisos, estados de oferta inexistentes.
- **La meta de migración de modelo** (el origen del quilombo) es el criterio de éxito final de toda la fase de reparación: cuando el sistema esté sano, cambiar de modelo debería ser posible.

---

## 5.2 Estado actual relevado (Claude Code, read-only)

> Verificación contra el código y la BD local (`database/bumeran_scraping.db`, solo lectura). No se ejecutó el matcher ni se conectó a Supabase. Lo que requiere conexión viva queda marcado **[no verificable en esta pasada]**.

### 5.2.1 Versión real y arquitectura del matcher

**Versión real: `3.5.5`** (desfase 3.5.4/3.5.5 resuelto).
- `database/MATCHER_VERSION` = `3.5.5`; `MatcherV3.VERSION = _read_matcher_version()` lo lee dinámicamente de ese archivo. El bump a 3.5.5 es del commit `b86d7dc1` (disciplina de versionado, 2026-05-18).
- El "3.5.4" del `CLAUDE.md` es **prosa stale**. La fuente de verdad es el archivo plano.
- **Deuda documental**: el changelog del header de `match_ofertas_v3.py` se congeló en **v3.4.0**; las versiones 3.5.1→3.5.5 no figuran ahí. Quedan, en cambio, **auto-documentadas inline** dentro de `_decide_dual_match` y en el comentario de la penalización de sector (buena práctica que compensa parcialmente, pero el header miente).

**Arquitectura — "Dual Matching" (v3.4.0+).** El matcher **siempre corre las dos vías** y luego decide:
1. **Semántico**: diccionario argentino → si no matchea, skills (BGE-M3, `ALPHA_SKILLS=0.6`) + título (`BETA_TITLE=0.4`) → penalización de sector y seniority.
2. **Reglas de negocio** (`_evaluate_rule_only`): se evalúan sin bypass.
3. **`_decide_dual_match`** elige el ISCO final por prioridad encadenada:
   - regla con `correccion_critica` → **siempre gana**;
   - `override_semantico` (términos inequívocos: enfermero, soldador…) → gana aunque el score ≥0.95;
   - coinciden en ISCO-4 → `dual_coinciden`;
   - divergen: score <0.55 → regla · score ≥0.95 → semántico · 0.55–0.95 → **regla gana**.

**Evolución 3.5.x leída del código** (es el comportamiento vigente): 3.5.1 decisión inteligente · 3.5.2 semántico ≥0.80 ganaba (revertido) · 3.5.3 reglas críticas siempre ganan · **3.5.4** threshold subido 0.80→0.95 ("con 0.80 el semántico overrideaba 860 reglas correctas") · **3.5.5** dos cambios: `override_semantico` + **penalización de sector solo si `sector_confianza=='alta'`** (84% de los sectores vienen del LLM con confianza media, copiando `area_funcional` como `sector_empresa` → penalizaba mal).

**Entry points**: producción vía `scripts/run_validated_pipeline.py` y `scripts/reapply_rules_to_validated.py`; gold set vía `scripts/matching/gold_set/run_matching_gold_set_100.py`; propagación de correcciones vía `scripts/correcciones/propagators/matching_esco.py`; además de la suite de tests.

### 5.2.2 Mapa de gold sets y el Gold Set ampliado

Conviven **al menos cinco nociones distintas de "gold set"**, sin una fuente única:

| Archivo / fuente | Casos | Fecha | ¿Lo usa el harness? | Trazadores |
|---|---|---|---|---|
| `database/gold_set_manual_v2.json` | **49** | 2026-04-14 | Sí — `tests/matching/test_gold_set_manual.py` (escribe `gold_set_history.json`) | No |
| `tests/matching/gold_set_v2.json` | **36** (8 R240/operario) | 2026-04-28 | Sí — `tests/matching/test_gold_set_v2_verified.py` | No |
| `database/gold_set_nlp_100_ids.json` | 106 IDs | 2026-01-27 | Universo NLP de enero (solo IDs) | No |
| `exports/matching_v3_gold_set_100.json` | 100 | 2026-01-27 | Gold set matching de enero | No |
| set de **113** | 113 | — | `tests/matching/test_m10_gold_set.py` falla: "Expected 49, got 113" | [no verificable] |

**El Gold Set ampliado (mayo 2026, 49→100+, LoRA) NO está en el working tree como archivo de gold set.**
- La corrida del **2026-06-03** (`gold_set_history.json`) registra `total: 49`, precisión 81.6% → el test de regresión sigue corriendo contra **49 casos**.
- `data/finetuning/matching/` está **vacío** (solo `training.log` de 18 bytes): el modelo LoRA y su gold set ampliado no están versionados.
- Los archivos "100" son de **enero**, anteriores al ampliado del LoRA.
- Los trazadores **Sommelier / Carnicero** no aparecen en ningún gold set, ni en `config/training_pairs.json`, ni en el dump `data/spec_w/cyn_30_validaciones_recientes_crudo.md`. Solo aparecen como keywords en configs de reglas y CSVs de archive (scraping).
- El test `test_m10_gold_set.py` espera 49 y encuentra **113** → hay un set de 113 en algún punto (probablemente Supabase o generado en runtime). **[no verificable en esta pasada]**.

**Dónde buscar el ampliado (acción pendiente, requiere conexión viva).** El candidato más fuerte son las **validaciones humanas en Supabase**: `scripts/spec_u1/export_validaciones_humanas.py` extrae **218 validaciones humanas** (validadores `cinvazquez4@gmail.com` (Cyn), `dschlese@trabajo.gob.ar` (Diego), `gbreard@gmail.com`, ventana 2026-03 a 05) leyendo la tabla Supabase **`ofertas_dashboard`** + la tabla local `validacion_historial`, y produce `data/spec_w/dataset_validaciones_humanas_2026_03_a_05.xlsx`. Ese script incluso tiene una hoja **"Patrón R240 — errores explícitos de Cyn"**. Las validaciones de Cyn **no** están en `validacion_historial` (su columna `usuario` es 99% automática: `claude`, `claude_bulk`, `sistema`; solo 37 `gerardo` + 8 `manual`); viven en **Supabase (`issues` y/o `ofertas_dashboard`)**. La recuperación real del Gold Set ampliado (filtrar el set de 100+/113 y confirmar Sommelier/Carnicero) **queda como acción pendiente que requiere conexión a Supabase o lectura del .xlsx**.

### 5.2.3 Reglas R-XXX y diagnóstico de R240

**Sistema de reglas** — viven en `config/matching_rules_business.json` bajo `reglas_forzar_isco` (no en código):
- **357 reglas**, rango R1..R358 (346 numeradas distintas; gaps por reglas removidas). 354 activas, 3 inactivas (`R10`, `R11`, `R314`).
- **350/357 ya tienen `esco_code`** (cobertura SPEC J casi total a nivel config); 7 sin él.
- **259/357 (73%) llevan `_linaje.requiere_revision=True`** — un flag de drift masivo: casi 3 de cada 4 reglas están marcadas "requiere revisión" y nunca se revisaron. El changelog interno llega hasta `_cambios_v516`; varias entradas documentan fixes de prioridad entre reglas que pisan (ej. R211 soldador vs R240).

**Diagnóstico de R240 — no es lo que parecía.**
La regresión la detecta `test_gold_set_v2_verified.py` (no el test de 49): "Oferta 7938726540: esperaba esco_code 9329.1, got None. Regla: R240_operario_produccion" (×3 ofertas: 7938726540, 7057631179, 7171410854).

Cadena verificada en BD (read-only):
1. R240 **sí dispara**: las 3 ofertas tienen `area_funcional='Produccion'`, `regla_aplicada='R240_operario_produccion'`, `decision_metodo='regla_prioridad'`.
2. El **ISCO es correcto y está persistido**: `isco_code=9329` en las 3 (validado por Cyn según notas del gold set).
3. La acción de R240 declara `esco_code: 9329.1`, y **`9329.1` SÍ existe** en `database/embeddings/esco_occupations_metadata.json` (3046 ocupaciones) — la resolución no falla por dato faltante.
4. El test lee la **columna `titulo_esco_code`** de `ofertas_esco_matching` y asierta `== 9329.1`. Esa columna está en **`None`** en las 3 ofertas.

**Causa raíz**: SPEC J dio a las reglas un `esco_code` granular y `_evaluate_rule_only` lo carga en `rule_info`, pero **el dataclass `MatchResult` no tiene campo `esco_code`** y la rama de regla de `match()` solo propaga `uri/label/isco_code`. El `esco_code` resuelto **nunca llega a la columna `titulo_esco_code`** → se persiste `None`.

**Alcance**: como 350/357 reglas tienen `esco_code`, el bug es **sistémico a toda la rama de regla**, no exclusivo de R240; el gold set v2 solo lo cazó en los casos operario. Es una **implementación incompleta de SPEC J en la capa MatchResult/persistencia**, no un test desactualizado ni un ISCO mal asignado.

### 5.2.4 El camino del feedback y `ofertas_matching_history`

**`ofertas_matching_history`** (111.357 filas) — columnas `id, id_oferta, run_id, isco_code, isco_label, match_method, score, created_at`. Es un **log append-only por corrida** de cada decisión de match. **No es acumulación muerta**: lo **lee** `scripts/exports/generate_training_pairs.py` para recuperar el "primer match (el incorrecto)" de cada oferta. Lo **escribe** `match_ofertas_v3.py` (INSERT). (Salvedad: el generador usa solo el primer match por issue; el resto de las 111K filas es histórico que nadie más consume.)

**El camino del feedback (hipótesis 3, refinada).** El loop está **medio construido**:
```
Cyn corrige en dashboard → issue en Supabase `issues` (pendiente)
   → [requiere resolución + propagación manual: SPEC T, 7 pasos]
      → issue estado='resuelto'
         → generate_training_pairs.py (lee issues resueltos + ofertas_matching_history)
            → config/training_pairs.json   [auto-trigger desde sync_learnings.py:1375]
               → ❌ fine-tuning que vuelva a producción  ← NO EXISTE
```
- **Sí conectado**: issue resuelto → training pair (el generador corre y acumula en `training_pairs.json`).
- **Roto en dos puntos**: (a) el issue debe resolverse y propagarse **manualmente** antes (SPEC T; el `CLAUDE.md` registra que el 99,8% de issues pre-SPEC-T nunca se propagaron); (b) los training pairs **nunca se consumen** por un fine-tuning que regrese a producción (`data/finetuning/matching/` vacío, LoRA ausente).

Esto **explica con precisión la percepción de Cyn** ("el sistema vuelve a cometer el mismo error"): la corrección se transforma en dato, pero el dato nunca actualiza el modelo. No es que el issue "termine en una tabla y nadie lo lea" (lo lee el generador); es que **el último tramo del loop —dato → modelo → producción— no existe**.

**Instancias del patrón D-15 ("construido una vez y abandonado") en matching:**
1. Modelo LoRA + su gold set ampliado: entrenados una vez, hoy ausentes del working tree.
2. `training_pairs.json`: se genera y acumula, nunca se consume por un fine-tuning productivo.
3. Gold set ampliado (mayo) desconectado del harness de regresión (sigue en 49/36).
4. 259/357 reglas marcadas `requiere_revision=True` y nunca revisadas.
5. `ofertas_matching_history`: 111K filas acumuladas; el único consumidor usa solo el "primer match" por issue.

### 5.2.5 Hipótesis refinadas (¿se confirmaron las 3 de la 5.1?)

1. **"R240 es síntoma del Gold Set desincronizado"** → **parcialmente refutada / reencauzada.** R240 no falla por expectativa obsoleta ni por gold set viejo: el ISCO 9329 es correcto y está persistido, y `9329.1` existe en metadata. El fallo real es un **bug de contrato SPEC J** (el `esco_code` granular nunca se propaga a `titulo_esco_code`), sistémico a la rama de regla. Lo que **sí** se confirma del espíritu de la hipótesis: el harness de regresión está desincronizado del ampliado (corre contra 49/36, no contra los 100+/113).
2. **"El Gold Set ampliado existe en algún lado"** → **confirmada como ubicación probable, no recuperada.** No está en el working tree; el candidato fuerte es **Supabase (`issues`/`ofertas_dashboard`)**, materializado parcialmente en `data/spec_w/*.xlsx` (218 validaciones humanas, ventana 2026-03..05). Recuperación pendiente de conexión viva.
3. **"El issue de Cyn termina en una tabla y no vuelve"** → **refinada.** El issue **sí** se lee (`generate_training_pairs.py`) y se transforma en training pair. El loop se rompe **después**: requiere propagación manual previa (SPEC T) y, sobre todo, **no hay fine-tuning que devuelva el aprendizaje a producción**. El resultado neto coincide con la percepción de Cyn, pero el punto de ruptura es otro.

---

## 5.3 Deuda observada

Registro de problemas detectados durante el relevamiento de Matching, **sin priorización ni propietario asignado en esta etapa**. La priorización y el diseño de reparaciones se harán en S1.C — Master de reparación, cuando los 7 specs de relevamiento estén cerrados. Tocar el matcher aisladamente sería peinar al muerto: sus errores de contexto pueden originarse en el NLP, su loop de aprendizaje involucra a la UI y al proceso operativo, y su contrato de datos afecta a quien consuma los resultados aguas abajo.

Las deudas están organizadas en categorías para legibilidad, sin orden de prioridad entre ellas.

### Categoría A — Contrato de datos

#### D-01 — El esco_code granular de las reglas nunca llega a la BD
Bug de contrato detectado a partir de la "regresión" R240: la regla dispara y persiste el ISCO correcto (9329), pero el `esco_code` granular (9329.1) que SPEC J definió en las reglas se pierde porque `MatchResult` no tiene ese campo. Afecta a 350 de las 357 reglas — R240 es solo la instancia que el gold set cazó. El trabajo de SPEC J se pierde silenciosamente en el camino a la BD desde que se hizo.
**Componentes involucrados**: matcher, contrato de datos del pipeline, tests de regresión, consumidores aguas abajo (Skills, dashboard).
**Por qué no se prioriza acá**: primero hay que saber si alguien consume ese esco_code granular aguas abajo — eso se sabe con los relevamientos de Skills (S1.B.4) y UI (S1.B.7).

### Categoría B — Gold Sets fragmentados

#### D-02 — Al menos 5 nociones distintas de "gold set" sin fuente única
Conviven: 49 manual (`gold_set_manual_v2.json`, lo que carga el test de regresión), 36 verified, 100/106 de enero (NLP y matching), 113 esperado por `test_m10_gold_set.py`, y el ampliado de mayo (ausente del repo). El harness de regresión evalúa contra las 49 expectativas viejas.
**Componentes involucrados**: matching, tests, proceso de validación.
**Por qué no se prioriza acá**: consolidar la fuente única requiere recuperar primero el ampliado (D-03) y definir proceso de ampliación con Cyn.

#### D-03 — El Gold Set ampliado de mayo no está versionado
El gold set ampliado durante el fine-tuning del LoRA (49→100+, con los trazadores Sommelier y Carnicero que recuerda Cyn) no está en el repo. `data/finetuning/matching/` está vacío. Candidato más fuerte: las 218 validaciones humanas de Cyn/Diego/Gerardo (ventana 2026-03 a 2026-05) en Supabase (`issues`/`ofertas_dashboard`), ya materializadas parcialmente en `data/spec_w/dataset_validaciones_humanas_2026_03_a_05.xlsx`.
**Componentes involucrados**: matching, Supabase, proceso de respaldo de artefactos.
**Por qué no se prioriza acá**: la recuperación requiere conexión viva a Supabase. Queda como acción pendiente documentada.

### Categoría C — Loop de aprendizaje

#### D-04 — El loop de aprendizaje se rompe en la segunda mitad
Refinamiento del hallazgo doble de la 5.1: la primera mitad funciona (el issue de Cyn se lee y se convierte en training pair vía `generate_training_pairs.py`, alimentado por `ofertas_matching_history`). La segunda mitad no existe: la propagación es manual (SPEC T) y no hay fine-tuning que devuelva el aprendizaje a producción. Cyn siente que el sistema no aprende porque el aprendizaje se acumula en un buffer que nunca se descarga.
**Componentes involucrados**: matching, NLP, proceso operativo, UI (visibilidad de correcciones).
**Por qué no se prioriza acá**: cerrar el loop requiere decisiones de infraestructura de entrenamiento (dónde, con qué cadencia, con qué validación) que dependen del cuadro completo.

#### D-05 — LoRA borrado sin querer, sin backup, pérdida total
El modelo fine-tuneado en mayo se hizo en disco C local, se borró por accidente y no quedó nada. No fue decisión consciente de liberar espacio. Deuda de proceso: no había (ni hay) política de respaldo de artefactos costosos.
**Componentes involucrados**: proceso operativo del proyecto.
**Por qué no se prioriza acá**: la política de respaldo es transversal (afecta modelos, gold sets, datasets) y se define en S1.C.

### Categoría D — Gobernanza de reglas

#### D-06 — 259/357 reglas (73%) marcadas requiere_revision=True y nunca revisadas
El flag existe, la revisión no sucede. Un marcador que nadie procesa es acumulación de deuda con apariencia de control.
**Componentes involucrados**: matching, proceso de validación con Cyn.
**Por qué no se prioriza acá**: requiere definir proceso de revisión (quién, con qué cadencia, con qué criterio) que involucra el tiempo de Cyn.

#### D-07 — Changelog del header congelado en v3.4.0
El código va por 3.5.5 y la evolución 3.5.1→3.5.5 está auto-documentada inline (bien), pero el changelog formal del header del archivo quedó congelado. Deuda documental menor.
**Componentes involucrados**: matcher.
**Por qué no se prioriza acá**: deuda menor, puede resolverse en cualquier momento como parte de otra intervención al archivo.

### Categoría E — Errores de contexto

#### D-08 — El matcher se queda con una palabra puntual y no con el contexto
Patrón de error dominante según Cyn (validadora), con ejemplos documentados: "Sobrestante de obra" → 7111 constructor inmobiliario; "Ing. eléctrica o electromecánica" → 7412 mecánico electricista (confusión de nivel profesional vs técnico/oficio). Lo que Cyn pide que el sistema entienda: acción principal, objeto de trabajo, nivel del rol, contexto del aviso ("instalar iluminación en vivienda ≠ instalar iluminación para shows").
**Componentes involucrados**: matcher, NLP (extracción de contexto), modelo semántico.
**Por qué no se prioriza acá**: la solución puede estar en el NLP (extraer mejor los campos de contexto), en el matcher (usarlos mejor), o en ambos — requiere los relevamientos S1.B.4 (Skills) y S1.B.5 (NLP).

### Categoría F — UI que afecta la validación (pertenece a S1.B.7, registrada acá por su impacto en matching)

#### D-09 — Herramientas de validación que degradan el trabajo de Cyn
Cuatro problemas reportados por la validadora: (1) las correcciones no quedan visibles en la oferta — se envían como issue pero la oferta se ve igual, imposible hacer seguimiento o reutilizar criterio; (2) **bug del cambio automático: al guardar, el sistema salta a otra oferta**, con riesgo de pérdida silenciosa de trabajo; (3) filtros que traen ofertas de sectores que no corresponden; (4) sin estados por oferta (pendiente / en revisión / corregida / finalizada).
**Componentes involucrados**: UI (S1.B.7).
**Por qué no se prioriza acá**: pertenece al relevamiento de UI; se registra acá porque afecta directamente la calidad y eficiencia de la validación de matching.

### Categoría G — Patrón sistémico

#### D-10 — Patrón "construido una vez y abandonado" (D-15 de Scraping) confirmado en Matching
Tercera aparición consecutiva del patrón (BD, Scraping, Matching). Cinco instancias en este componente:

1. **LoRA**: entrenado en mayo, borrado sin backup.
2. **Training pairs**: se generan pero nada los consume aguas abajo (la cadena muere antes del fine-tuning).
3. **Gold Set ampliado**: construido en mayo, desconectado del harness de regresión que sigue corriendo contra los 49 viejos.
4. **Reglas**: 73% marcadas para revisión que nunca sucede.
5. **ofertas_matching_history**: alimenta una cadena (generate_training_pairs) cuyo final no existe.

**Componentes involucrados**: todos. Es transversal.
**Por qué no se prioriza acá**: se cruza en S1.C con las instancias de los otros componentes. La solución (si hay) es de proceso operativo del proyecto.

---

## 5.4 Principios de diseño objetivo

Principios generales de cómo debería comportarse el sistema de Matching cuando esté sano. **No es diseño detallado** — eso surge del master S1.C con el cuadro completo. Estos principios son el norte conceptual.

### Principio 1 — Contratos de datos completos extremo a extremo
Si una regla define un dato, ese dato llega a la BD. Si un componente produce información, el contrato garantiza que no se pierda silenciosamente en el camino. El bug del esco_code granular (350 reglas afectadas sin que nadie lo supiera) es exactamente lo que el sistema sano hace imposible.

### Principio 2 — Fuente única de verdad para el Gold Set
Un gold set canónico, versionado, con proceso claro de ampliación y dueño definido. Los tests de regresión corren contra esa fuente y solo esa. Cinco nociones de "gold set" conviviendo es la negación de la idea misma de gold set.

### Principio 3 — Loop de aprendizaje cerrado
Corrección humana → training pair → reentrenamiento o regla → producción → la validadora ve el efecto de su corrección. Hoy existe la primera mitad del ciclo; el sistema sano lo cierra. El trabajo de validación humana es el activo más caro del proyecto y hoy se acumula sin retornar.

### Principio 4 — Artefactos costosos con respaldo
Modelos entrenados, gold sets validados, datasets curados: todo lo que costó horas humanas o de cómputo tiene backup y versionado automático. "Se borró sin querer y no quedó nada" no puede volver a pasar.

### Principio 5 — Reglas con gobernanza
Toda regla tiene dueño, fecha y estado de revisión real. Un flag de revisión que nadie procesa es peor que no tenerlo: da apariencia de control sin control.

### Principio 6 — Matching por contexto, no por palabra
El norte que la validadora definió con precisión: el sistema debe entender la acción principal, el objeto de trabajo, el nivel del rol y el contexto del aviso. "Instalar iluminación en vivienda" y "instalar iluminación para shows" son ocupaciones distintas y el sistema sano las distingue.

### Principio 7 — Migración de modelo posible
El norte fundante de toda la fase (frase de Gerardo: "todo este quilombo nace porque quisimos pasar a otro modelo y nos dimos cuenta que no se puede"). Cuando el sistema esté sano, cambiar de modelo —de embeddings, de NLP, de fine-tuning— debe ser una operación posible y acotada, no una imposibilidad estructural. Es el criterio de éxito final de toda la reparación.

---

> *Spec S1.B.3 — Matching: capas 5.1 (Gerardo + Cyn), 5.2, 5.3 y 5.4 cerradas. Las 10 deudas observadas se vuelcan al master S1.C cuando esté listo. Los 7 principios son input del diseño objetivo. La deuda D-10 (patrón sistémico) suma la tercera aparición consecutiva del patrón transversal. Acción pendiente que requiere conexión viva: recuperar el Gold Set ampliado desde Supabase (218 validaciones humanas, ventana 2026-03..05).*
