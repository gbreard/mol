# SPEC S1.B.5 — Relevamiento de NLP

> Versión 0.1 (capa 5.1 — Memoria operativa de Gerardo + Cyn + diagnósticos de mayo) · 2026-06-05
> Quinto spec de la fase S1.B — Relevamiento del sistema. Releva el componente de NLP del proyecto MOL. Sigue la plantilla común del master v0.2.
> **Particularidad**: la capa 5.1 incorpora dos diagnósticos internos de mayo 2026 ("MOL en perspectiva v2" e "Informe MOL COMPLETO", ambos fuera del repo) que aportan datos cuantitativos y discrepancias doc/código que la capa 5.2 resuelve.

---

## 5.1 Memoria operativa — Gerardo + Cyn + diagnósticos de mayo

### Contexto fundante (compartido con S1.B.3 y S1.B.4)

"Todo este quilombo nace porque quisimos pasar a otro modelo y nos dimos cuenta que no se puede" (Gerardo). El intento de migrar de Qwen2.5 a la familia Qwen3.5/3.6 (feb-abr 2026) expuso el acoplamiento estructural del sistema al modelo. El documento "MOL en perspectiva" (mayo 2026) es el análisis estratégico de esa situación; el NLP es el componente más acoplado de todos.

### El acoplamiento al modelo, cuantificado ("MOL en perspectiva", sección 4.1)

- **323 reglas de negocio acumuladas para corregir errores específicos de Qwen2.5.** Estimación del documento: entre 60 y 100 son dominio genuino; entre 180 y 220 son parches del modelo. **"Mientras esa clasificación no se haga, no se puede migrar de modelo."** Esta clasificación pendiente es la tarea concreta detrás del contexto fundante. (Nota de reconciliación: S1.B.3 relevó 357 reglas en el matcher; el informe habla de 323; el NLP Gate tiene 49-51 propias. Los conteos y los universos a reconciliar en 5.2.)
- **Schema y prompt entrelazados en código**: sintaxis del prompt y formato de output calibrados para Qwen2.5 específicamente.
- **Threshold del matcher calibrado empíricamente para los outputs de Qwen2.5**: cualquier cambio de modelo invalida la calibración.

### Discrepancias declaradas doc vs código ("MOL en perspectiva", sección 4.2) — a resolver en 5.2

1. **Schema declarado: 153 campos. Schema en código: 20.**
2. **Modelo declarado: qwen2.5:14b. Modelo en código: qwen2.5:7b.** (El Informe COMPLETO declara 14b; la memoria del proyecto decía 7b.)
3. **Versión del pipeline NLP**: el Informe dice 11.3.0; el archivo del repo decía 11.3.1; CLAUDE.md menciona 11.4. Tres números.
4. **Reglas NLP**: la documentación histórica decía 35; los tests detectaron 51; el Informe COMPLETO dice que el NLP Gate tiene 49 reglas que generaron 253.032 marcas sobre el 99,9% del corpus.
5. **"100% precisión en Gold Set"** se logró iterando reglas hasta que pasaran los 49 casos — overfitting al test set, no métrica real. Hay 89.189 errores pendientes de validación que el Gold Set no representa.

### Datos cuantitativos del NLP (Informe COMPLETO, al 14 de mayo de 2026)

- Corpus: 66.499 ofertas crudas; 60.930 con NLP (91,6%). Latencia mediana scraping→NLP: **6 días**.
- **Lag negativo en 4.778 ofertas (7,9%)**: timestamp de NLP anterior al de scraping — la columna `scrapeado_en` fue sobrescrita durante una migración o reimportación. Anomalía estructural declarada.
- Cobertura por campo (selección): modalidad 99,28% (84% presencial / 9% híbrida / 7% remota) · seniority 99,4% · experiencia mínima 87% · provincia 87,2% (24 jurisdicciones, sin valores espurios) · nivel educativo 81,4% · cantidad de vacantes 47,6% · **salario 1,71%** (limitación estructural: MOL no puede ofrecer análisis salarial).
- **`sector_empresa`: 99,2% de cobertura nominal pero 75% de los valores colapsados en "Otro".** Coincide exactamente con lo que Cyn reporta como el campo más roto. La cuantificación confirma su percepción.
- **Seniority con sesgo estructural del modelo**: 18,4% de las ofertas marcadas "manager" tienen el campo de personal a cargo en cero — inconsistencia interna que obliga a tratar el campo con cuidado.
- El pipeline NLP tiene tres sub-capas (Informe, anexo B.2): pre-llenado de campos estructurados de portales → validación contra catálogos cerrados (24 provincias, secciones CLAE) → normalización de clasificatorios.
- 1.355.025 menciones de skills extraídas, 87,6% con score de confianza media-baja.

### La experiencia de Cyn con el NLP (validadora humana)

- **El campo con más errores: Sector.** "Casi todo queda como Otro" — confirmado por el Informe con el 75%.
- **Las tareas se extraen BIEN y separadas de las skills.** Es la fortaleza del componente, coherente con el rol de ancla que el modelo conceptual les asigna.
- **El problema específico que Cyn identifica: listas de conceptos sin verbo.** Cuando el aviso lista conceptos sueltos ("Excel, inglés, atención al cliente") en lugar de describir tareas con acción, el sistema no normaliza a tareas con verbo. Pide que el sistema extraiga el núcleo real del puesto: acción principal, objeto de trabajo, nivel del rol, contexto.
- **Avisos en inglés se procesan bien.**

### Lo que Gerardo sabe (y lo que no)

- **Tareas ≠ skills** (arquitectura conceptual): de las tareas se infieren los skills usando ESCO. Confirmado en S1.B.4 (origen `tarea` domina con 45,1%).
- **El feedback de Cyn está desconectado del NLP** (NG-4): confirmado y refinado en S1.B.3/S1.B.4 — el loop se rompe en la segunda mitad; `regla_cynthia`/`regla_issue` con 0 filas.
- **Versión NLP, historia de las reglas 35→51, drift de tests**: Gerardo no sabe (NG-1, NG-2). A verificar en 5.2.
- **Qwen2.5 y el intento de migración** (NG-5): el detonante de todo. El documento de mayo lo desarrolla.

### Hipótesis tentativas para la capa 5.2

1. **Los "153 campos" son el schema declarado/documental y los "20" el schema real del código** — o bien hay un schema extendido que algún módulo genera y otro descarta. La discrepancia es demasiado grande para ser un error de conteo; debe haber dos cosas distintas llamadas "schema".
2. **El modelo real del código es qwen2.5:7b**, no 14b — la documentación (incluido el Informe COMPLETO) declara el modelo aspiracional, no el operativo.
3. **El colapso de sector en "Otro" tiene causa identificable en el prompt o en la validación**: o el prompt no da catálogo de sectores utilizable, o la validación contra catálogo cerrado rechaza y degrada a "Otro", o el modelo no infiere y el default es "Otro". El gate de confianza del sector ya apareció en S1.B.3 (la penalización de sector solo aplica con confianza alta porque el 84% viene con confianza media).
4. **Las 49-51 reglas del NLP Gate son una capa distinta de las 323-357 reglas del matcher** — universos diferentes que la documentación mezcla.
5. **El lag negativo (scrapeado_en sobrescrito) es rastro de una migración no documentada** — arqueología de BD que conecta con S1.B.1.

### Notas para fases posteriores

- **La clasificación de las 323 reglas (dominio genuino vs parche del modelo)** es LA tarea habilitante de la migración de modelo — candidata fuerte a spec propio en la reparación (S1.C).
- **Los diagnósticos de mayo viven fuera del repo** (docx de trabajo). La formalización del corpus documental estratégico es deuda transversal de documentación.
- **El sesgo de seniority** (manager sin gente a cargo) es relevante para cualquier producto comercial que use ese campo.

---

## 5.2 Estado actual relevado (contra código, solo lectura · 2026-06-11)

> Relevamiento read-only contra el código y la BD SQLite local (`bumeran_scraping.db?mode=ro`). No se ejecutó el NLP, no se invocó Ollama, no se conectó a Supabase viva.

### 5.2.1 Versión, modelo y schema reales

**Versión real = `11.3.1`.** Fuente única de verdad: el archivo plano `database/NLP_VERSION`, leído en runtime por `_read_nlp_version()` (`process_nlp_from_db_v11.py:86`) y expuesto como `NLPExtractorV11.VERSION` / `NLP_VERSION_TAG`. Los otros dos números de la discrepancia 3 son **prosa stale**: CLAUDE.md dice "11.4", el Informe COMPLETO dice "11.3.0". Mismo patrón flat-file que resolvió la versión del matcher en S1.B.3 — la fuente de verdad está en el archivo, no en los docstrings.

**Modelo real = `qwen2.5:7b`.** Constante de clase hardcodeada (`OLLAMA_MODEL = "qwen2.5:7b"`, línea 101), usada en el payload del request a Ollama (línea 211). **No hay override de entorno para el nombre del modelo** — solo `OLLAMA_HOST` es configurable por env (línea 103). El "14b" de la discrepancia 2 vive **únicamente en docstrings** (líneas 9 de `process_nlp_from_db_v11.py` y del prompt). El comentario de la línea 100 justifica el downgrade de forma explícita: *"7b es suficiente para extracción JSON (3x más rápido que 14b)"*. El 7b también está en `limpiar_titulos.py:477` y `config/nlp_titulo_limpieza.json`. **Hipótesis 2 CONFIRMADA**: el modelo operativo es 7b; el 14b es aspiracional/documental.

**Schema: dos cosas distintas llamadas "schema", ninguna es 153.** La discrepancia 1 se resuelve identificando dos artefactos reales:

| Artefacto | Tamaño | Evidencia |
|---|---|---|
| **Schema de extracción** | **20 campos** | Triple coincidencia: el prompt pide 20 claves JSON; `config/nlp_schema_lite.json` se autodescribe *"20 campos (15 NLP + 5 Matching ESCO)"*; la lista de claves coincide. |
| **Tabla de persistencia** | **171 columnas** | `ofertas_nlp` acumuló columnas a lo largo de versiones. El guardado es **dinámico** (`PRAGMA table_info` → filtra solo las claves que matchean columnas existentes, `process_nlp_from_db_v11.py:571-587`), así que de las 171 columnas solo se escriben las ~24 que el extractor produce hoy (20 campos + meta + 2 de fine-tuning v11.4). |

El "153" **no tiene artefacto literal** en código ni config (grep exhaustivo: el único "153" del repo es el propio texto de la capa 5.1). Es un conteo documental stale, en el orden de magnitud de la tabla de 171 columnas — probablemente el conteo de `ofertas_nlp` en un momento anterior. **Hipótesis 1 CONFIRMADA y refinada**: hay dos schemas (extracción 20 / persistencia 171), pero el 153 es prosa, no un tercer schema.

**El prompt es monolítico y hardcodeado.** Vive en `database/prompts/extraction_prompt_lite_v1.py` (225 líneas), pide los 20 campos en un solo bloque, con el catálogo de valores embebido (ver 5.2.3). No está en config — versionarlo o parametrizarlo requeriría tocar código.

### 5.2.2 Los universos de reglas reconciliados

Los conteos de la capa 5.1 (35 / 49 / 51 / 323 / 357) mezclaban **universos distintos**. Mapa real:

| Universo | Conteo real | Archivo | Estructura |
|---|---|---|---|
| **NLP Gate** | **51** (V×20 + NV×15 + NQ×14 = 49 prefijadas + 2 sin prefijo) | `config/nlp_validation_rules.json` v1.1.0 | lista `reglas` |
| Matcher (negocio) | ~357 (S1.B.3) — el "323" del doc de mayo | `config/matching_rules_business.json` | dict anidado |
| NLP inference (relleno de vacíos) | n/a (dict por campo) | `config/nlp_inference_rules.json` | dict por campo |
| NLP correction (post-LLM) | n/a (dict por campo) | `config/nlp_correction_rules.json` | dict por campo |

**El drift 35→49→51 reconstruido por git** (no hay fecha por regla — `0/51` reglas tienen `fecha`):
- **35** = conteo de lanzamiento del gate. Commit `d8c9b7d4`: *"NLP validator v1.1.0 — 35 reglas, gate pre-matching"* (feb-2026).
- **49** = solo las reglas **prefijadas** (V+NV+NQ). Es el conteo que reporta el Informe COMPLETO.
- **51** = total actual, incluye 2 reglas sin prefijo reconocido. El changelog `_cambios_v1_1` documenta: eliminadas V04/V05/V06 (código muerto "exterior") + NV_CLAE; agregadas 8 NV_*; recalibraciones posteriores (V10/V30/V31, NV02/NV04) cerraron 1.380 falsos positivos.

**Hipótesis 4 CONFIRMADA**: el NLP Gate (51) y las reglas del matcher (357) son universos separados; el "323" del documento de mayo refiere al universo del matcher, no al gate. La doc estratégica los mezcla.

**Las 253.032 marcas → `validation_errors` (hoy 278.565 filas). Misterio de S1.B.1 RESUELTO.** La tabla de 278K filas que sorprendió en S1.B.1 **es la acumulación de marcas del NLP Gate**: el 100% de los `error_id` lleva prefijo del gate.
- Por prefijo: **V = 260.291 (93%)**, NQ = 10.040, NV = 8.234.
- Por severidad: info 156.694 / medio 78.229 / warning 34.115 / bajo 7.179 / **alto 2.348**.
- **69.698 ofertas distintas** marcadas (≈99,9% del corpus con NLP, como decía el Informe).
- Top marcas: `V14_descripcion_muy_corta` (99.749 = 36%), `V03_skills_insuficientes` (35.681), `V24_skills_baja_coherencia` (32.193), `V12_provincia_vacia` (18.196), `V16_clae_missing` (15.300).

La tabla creció de 253.032 (14-may, Informe) a 278.565 (hoy) — el gate sigue acumulando marcas. **Nadie las consume para mejorar la extracción** (ver 5.2.4, telemetría sin consumidor).

### 5.2.3 El colapso del sector y los campos problemáticos

**Mecanismo del colapso de sector → "Otro" (cuantificado al 75% por el Informe, "el campo más roto" según Cyn).** El sector se resuelve en `nlp_postprocessor.py` con un embudo de confianza de 3 pasos:

1. **PASO 0** — lookup en catálogo de empresas por `id_empresa` → confianza `alta` (solo si la empresa está catalogada; catálogo escaso).
2. **PASO 1** — frase explícita tipo *"somos una empresa de [sector]"* en la descripción → confianza `alta`.
3. **PASO 2** — si el LLM extrajo algo y no hubo frase explícita → confianza `media` (default del output del LLM).
4. **PASO 3** — sin fallback por keywords sueltos (deshabilitado deliberadamente para evitar falsos positivos).

Luego, la normalización canónica (línea ~1790): si el valor **no es canónico y no está en el alias map** → se fuerza a **"Otro"**. El prompt (línea 101) pide el sector *"de la EMPRESA, no del puesto"* contra un catálogo cerrado de 25 valores — pero los avisos describen el **puesto**, no la empresa. Resultado triple: (a) la mayoría cae en `media` porque casi nunca hay frase explícita ni empresa catalogada (explica el 84% confianza media de S1.B.3); (b) cualquier valor fuera del catálogo/aliases → "Otro"; (c) cuando el aviso no permite inferir el rubro de la empresa → "Otro". El colapso es **estructural**, no un bug puntual.

**Adición — el gate SÍ marca el colapso, y nadie consume la marca.** Hay **9 reglas del gate sobre `sector_empresa`**: `V16_clae_missing` (info), `V18_sector_igual_area` (warning, 8.662 marcas), `V19_sector_seguridad_no_vigilancia`, `V20_sector_salud_no_sanitario`, `V21_sector_tecnologia_no_it`, `V22_empresa_confidencial_con_sector` (info, 6.833 marcas), `NV02_sector_no_canonico` (alto), `NV11_sector_null_like` (alto), `NQ11_caba_sin_prefill` (info). El gate **detecta los síntomas del colapso** (sector = área inferida del puesto, valor no canónico, null-like del LLM) y escribe las marcas a `validation_errors` — **pero ningún proceso downstream las lee para corregir la extracción**. Es otra instancia del patrón **telemetría sin consumidor** (variante de D-15): el sistema ya sabe dónde está roto el sector y lo registra 15.000+ veces, sin que ese conocimiento vuelva a la extracción.

**Sesgo de seniority (18,4% "manager" sin gente a cargo).** El seniority se infiere de keywords del **título** (`prompt:142-148`: "manager = gerente, jefe de area"), independientemente de `tiene_gente_cargo`. Un "Jefe de cocina" o "Encargado" recibe `manager` por el título aunque no supervise a nadie. Hay reglas de cruce en el gate — `NV_CROSS_gente_seniority` (bajo), `NQ01`/`NQ02` (medio), `NV_EXP_SENIORITY`/`NQ04` (warning) — pero `NV_CROSS_gente_seniority` cubre la dirección **opuesta** (gente=true pero seniority bajo); la dirección del sesgo del Informe (manager con gente=0) **no tiene regla que la marque**, y aunque la tuviera sería severidad baja sin consumidor. El sesgo pasa el gate sin marca.

**Listas sin verbo (el problema que Cyn identifica) — confirmado a nivel de prompt.** La regla 3 del prompt (líneas 79-84) instruye extraer *"CADA responsabilidad/tarea como item separado, usando punto y coma"* — asume que el aviso **describe tareas con acción**. **No hay instrucción** sobre qué hacer cuando el aviso lista conceptos sueltos sin verbo ("Excel, inglés, atención al cliente"): el prompt no normaliza a tareas-con-acción ni extrae el "núcleo real del puesto" (acción + objeto + nivel + contexto) que Cyn pide. El prompt es estructuralmente **task-assuming**: cuando el insumo es una lista de conceptos, no hay capa que lo reencuadre. El diagnóstico de Cyn se confirma en el origen (el prompt), no en un postproceso.

### 5.2.4 Acoplamiento al modelo y rastros de la migración

**Inventario de puntos de acoplamiento a Qwen2.5** (insumo de la futura capa de abstracción de modelos):

1. **Nombre del modelo hardcodeado** — `OLLAMA_MODEL = "qwen2.5:7b"` (línea 101), sin parametrizar.
2. **Parámetros de generación Ollama-específicos** — `"format": "json"`, `temperature: 0.0`, `num_predict: 1024`, `num_ctx: 4096` (líneas 214-219). El `num_predict` está atado al tamaño del schema (comentario: "Mucho menos tokens").
3. **Parsing del output calibrado a Qwen** — `_parse_llm_response` (255-291) asume que Ollama devuelve JSON limpio vía `format: json`, con fallbacks para code-blocks markdown y regex `\{...\}`. Tolerancias específicas al comportamiento de salida de Qwen2.5.
4. **Sintaxis del prompt** — el docstring del prompt declara *"optimizado para Qwen2.5"*; el formato y el orden de campos están calibrados para ese modelo.
5. **El downgrade 14b→7b** (adición): es **una decisión de modelo tomada en código sin tocar la documentación**. La constante de la línea 101 y su comentario justifican el cambio ("3x más rápido"), pero los docstrings siguen diciendo 14b y el Informe COMPLETO declara 14b. Es exactamente el tipo de decisión que la futura capa de abstracción debe **volver explícita y versionada**: hoy vive como un literal hardcodeado y un comentario, no como una entrada de configuración con histórico.

**Rastros de la migración (feb-abr) en el repo: casi nulos.** El **NLP core** está acoplado monolíticamente a `qwen2.5:7b` — no hay configs comentadas, branches, ni scripts de prueba de otros modelos en el pipeline. Los únicos rastros viven en **scripts periféricos**, no en el NLP:
- `scripts/translate_esco_content.py:42` — comentario *"Remove thinking tags if present (qwen3 sometimes adds these)"*: el único fragmento real del intento con **qwen3**, en una utilidad de traducción ESCO, manejando una diferencia de comportamiento del modelo.
- `scripts/analysis/validate_locations_with_llm.py` — usa `llama3.1:8b` para validar ubicaciones ambiguas (utilidad de análisis, no el pipeline).

El intento de migración que detonó todo el relevamiento **dejó arqueología mínima en el código**: se exploró fuera del repo o en branches ya borradas. **No rastreable en detalle desde el repo.**

**Lag negativo (4.778 ofertas, scrapeado_en sobrescrito) — mecanismo localizado.** En la migración V1→V2, `database/migrations/migrate_historical_data.py:223` hace `scrapeado_en = oferta.get('scrapeado_en', datetime.now().isoformat())`: las ofertas migradas **sin** `scrapeado_en` original recibieron el **timestamp del momento de la migración**. Si su NLP había corrido antes de esa migración, el `scrapeado_en` resultante queda **posterior** al timestamp de NLP → lag negativo. Es rastro de una migración histórica (conecta con la arqueología de BD de S1.B.1). Mecanismo confirmado; el alcance exacto (cuántas de las 4.778 vienen de esta ruta) no es verificable sin correr sobre la BD viva.

**Instancias de D-15 ("construido una vez y abandonado") en NLP** — quinta aparición consecutiva del patrón transversal:
1. **`validation_errors` (278K marcas) como fuente de feedback abandonada** — el gate registra 49-51 reglas × 278K marcas que ningún proceso consume para mejorar la extracción. La instancia más grande del proyecto de "telemetría sin consumidor".
2. **Las 9 reglas de sector del gate** — detectan el colapso (15.000+ marcas) sin consumidor.
3. **Las reglas de cruce de seniority** (NV_CROSS, NQ01-04) — marcan inconsistencias en severidad baja/warning que nadie lee.
4. **La tabla `ofertas_nlp` de 171 columnas** — ~150 columnas nunca pobladas por el extractor de 20 campos; schema aspiracional construido y abandonado (el "153" documental es su fósil).
5. **Variante "decisión en código sin documentar"**: el downgrade 14b→7b (vivo, deliberado, sin reflejo en docs) — emparenta con el "construido y nunca encendido" de S1.B.4.

### 5.2.5 Hipótesis refinadas

1. **Schema (153 vs 20)** — CONFIRMADA y refinada: dos artefactos reales (extracción 20 / persistencia 171); el 153 es prosa documental sin artefacto literal.
2. **Modelo (7b vs 14b)** — CONFIRMADA: operativo `qwen2.5:7b` hardcodeado; el 14b es aspiracional/documental.
3. **Colapso de sector** — CONFIRMADA con mecanismo: embudo de confianza (alta solo con empresa catalogada o frase explícita; media por default del LLM) + normalización que fuerza a "Otro" todo lo no canónico, contra un catálogo cerrado de 25 valores que pide el rubro de la EMPRESA mientras el aviso describe el PUESTO. El gate marca el colapso pero nadie lo consume.
4. **Universos de reglas (gate vs matcher)** — CONFIRMADA: 51 (gate) y 357 (matcher) son universos separados; la doc los mezcla. Drift 35→49→51 reconstruido por git.
5. **Lag negativo (migración no documentada)** — CONFIRMADA con localización: `migrate_historical_data.py:223` estampa `datetime.now()` en `scrapeado_en` ausente durante la migración V1→V2. Conecta con S1.B.1.

---

> *Versión 0.2 — Capas 5.1 + 5.2 cerradas. Relevamiento read-only contra código y BD local (2026-06-11). Capas 5.3 (deuda observada) y 5.4 (principios de diseño) pendientes, se trabajan con Gerardo.*
