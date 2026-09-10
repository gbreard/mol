# FRENTE M — Diagnóstico de extracción de TAREAS

**¿El aviso no las tiene o el LLM no las ve?** · 2026-08-25 · read-only sobre producción, cero cambios al NLP, cero reprocesamiento.

> Las tareas extraídas son el micro-fundamento del sistema: de ellas salen los skills indirectos, sobre ellas evalúa el traductor (las 88 reglas de Cyn deciden por tareas), y son la unidad de análisis del programa de investigación del MOL (enfoque de tareas Acemoglu-Autor). Cyn detectó errores de extracción; este frente los mide y produce el material para que ella los marque sobre casos.

---

## 0. Respuesta corta (la pregunta madre)

Sobre **98.229 ofertas con NLP** (base; +541 sub-ofertas multi-posición aparte):

- **El corpus NO está genuinamente sin tareas.** Solo **~0,1%** son avisos pobres realmente sin tareas. La inmensa mayoría de los avisos SÍ enuncian tareas.
- **El problema es real pero acotado, sistémico y concentrado.** La población con extracción severamente pobre (≤2 tareas sobre descripción rica) es una **cota superior de 7.288 (7,4%)**; calibrada contra lectura humana baja a **~4.300 fallos reales (~4,4% del corpus)**.
- **El fallo dominante NO es "0 tareas" sino pérdida parcial (truncamiento).** El LLM levanta algunas tareas y **dropea otras — incluida la tarea nuclear del puesto** — y esto ocurre **también en avisos limpios y bien estructurados** (3 de 12 controles limpios perdieron la tarea que define el puesto). Por eso el 4,4% es piso, no techo: mide solo los casos que caen a ≤2.
- **El confound es ComputRabajo.** El 59% del texto scrapeado de CT es chrome (blurbs de empresa, ratings, "Ofertas similares" con avisos ajenos, footer legal). Eso infla la "riqueza aparente" y ensucia el conteo: la heurística acierta **82%** en Bumeran/ZonaJobs pero solo **45%** en CT.
- **La causa raíz es el prompt, no el modelo ni un lote.** El problema es uniforme entre versiones NLP (11.3.0 vs 11.3.1) y entre meses. La instrucción de extracción solo busca marcadores explícitos (bullets/numeración/"Responsabilidades:") y **no cubre el 17% de avisos en prosa, ni los encabezados no canónicos (interrogativos, "misión", inglés), ni excluye requisitos/beneficios, ni descarta el chrome, ni permite salida vacía.**

**Recomendación (no se ejecuta nada acá):** rediseño del prompt de extracción + un pre-limpiado de chrome de ComputRabajo (barato, ni siquiera toca el prompt) + un post-filtro de exclusión, con un **gold set de tareas** validado por Cyn como gate. Detalle en §6.

---

## 1. P1 — Medición de cobertura

**Tareas promedio: 5,42 por oferta.** Distribución de tareas extraídas:

| n_tareas | ofertas | % |
|---|---|---|
| 0 | 4.211 | 4,3% |
| 1–2 | 7.933 | 8,1% |
| 3–5 | 41.308 | 42,1% |
| 6+ | 44.777 | 45,6% |

### La matriz clave — riqueza de la descripción × n_tareas

Riqueza = longitud del texto scrapeado (proxy barato; ver corrección por chrome en §1b).

| Riqueza \ n_tareas | 0 | 1–2 | 3–5 | 6+ | total |
|---|---|---|---|---|---|
| pobre (<200) | 81 | 102 | 135 | 19 | 337 |
| media (200–600) | 1.429 | 1.519 | 2.751 | 826 | 6.525 |
| rica (600–1500) | 1.005 | 2.553 | 16.310 | 10.290 | 30.158 |
| muy rica (1500+) | 1.696 | 3.759 | 22.112 | 33.642 | 61.209 |

**Lectura:**
- **Genuinamente sin tareas (honesto): esquina inferior-izquierda ≈ 81 (0,1%).** Casi nada del corpus es un aviso pobre sin tareas.
- **Candidatos a LLM-ciego: esquina superior-derecha** — descripciones ricas/muy-ricas con ≤2 tareas = 1.005+2.553+1.696+3.759 = **9.013** en bruto; con señal de estructura confirmada = **7.288 (7,4%)**. Es la cota superior de la ceguera.
- **El 64% de los "0 tareas" vienen de descripciones ricas/muy-ricas** (2.701 de 4.211) → no son avisos vacíos, son fallos de extracción.

### Por portal (la concentración)

| portal | 0 | 1–2 | 3–5 | 6+ | total | ciegos* |
|---|---|---|---|---|---|---|
| computrabajo | 1.896 | 3.519 | 13.758 | 11.895 | 31.068 | 4.551 |
| bumeran | 1.129 | 2.072 | 13.459 | 13.501 | 30.161 | 1.209 |
| indeed | 472 | 781 | 5.597 | 11.701 | 18.551 | 720 |
| zonajobs | 644 | 1.139 | 7.892 | 7.400 | 17.075 | 679 |
| portalempleo | 65 | 412 | 574 | 260 | 1.311 | 129 |
| caba | 5 | 10 | 28 | 20 | 63 | — |

*ciegos = descripción rica+estructurada con ≤2 tareas (heurística P1). **ComputRabajo concentra el 62% de la población ciega.**

### Por versión NLP y por mes — el problema es uniforme

| versión | ≤2 tareas | total | % |
|---|---|---|---|
| 11.3.0 | 9.108 | 69.490 | 13,1% |
| 11.3.1 | 3.036 | 28.739 | 10,6% |

Por mes: ~10–14% de ≤2 tareas de forma **estable** en todo 2025-09 → 2026-08. **No hay un lote ni una versión culpable** → el problema es estructural (prompt/modelo), no una regresión puntual.

### El costo sobre el consumidor más sensible (el traductor)

| canal de decisión | total | con ≤2 tareas | % |
|---|---|---|---|
| árbol/traductor (`arbol_contexto`) | 3.710 | 101 | 2,7% |
| semántico (`skills_first_v3`) | 36.156 | 4.728 | **13,1%** |

**Mecanismo:** el traductor casi no toca avisos con pocas tareas (2,7%) — **porque las tareas magras nunca llegan a él**: caen al fallback semántico (el canal más grande y más débil), donde el 13,1% (4.728 ofertas) tiene ≤2 tareas. Tareas magras → skills magros → matching semántico sobre poca señal. La ceguera de tareas **degrada silenciosamente** ofertas desde los canales confiables (dict/regla/traductor) hacia el más incierto.

---

## 1b. Corrección por chrome (ComputRabajo)

Al leer los casos apareció que la "riqueza" de ComputRabajo está inflada por boilerplate del scrape. Medido sobre las 31.068 ofertas CT con NLP:

- **59% del texto scrapeado, en promedio, es chrome**: header "Ocultaste esta oferta", "Requerimientos/Hace X días", "Acerca de [empresa]" + blurb (a veces duplicado), "Evaluación general 4.3 / N Evaluaciones / 58%…", **"Ofertas similares" seguido del texto de OTROS avisos**, footer legal "DGNET LTD / Finalidad…".
- Aun descontando el chrome, el cuerpo real de CT es sustancial (p50 = 1.081 chars): el chrome explica solo **~18%** de los "ciegos" brutos de CT. El resto es ceguera real.
- **Riesgo latente confirmado, no materializado:** el bloque "Ofertas similares" ofrece bullets de tareas de puestos ajenos; en la muestra leída (7+ casos con ese bloque) el extractor **no** importó tareas cruzadas (0 casos), pero el riesgo es estructural y crecería con cualquier extractor más agresivo por bullets.

**Consecuencia metodológica:** la heurística de P1 es una **cota superior**; la magnitud real de la ceguera debe leerse calibrada (§3), y el chrome de CT conviene recortarse **antes** del NLP (limpieza barata, independiente del prompt).

---

## 2. P2 — Cómo los avisos argentinos traen sus tareas

Muestra leída: 66 descripciones estratificadas por portal.

| patrón | n | % | qué es |
|---|---|---|---|
| **P-HEADER** | 43 | 65% | sección con encabezado + lista |
| **P-PROSA** | 11 | 17% | tareas embebidas en párrafo, sin lista |
| **P-AUSENTE** | 8 | 12% | el aviso no enuncia tareas (solo requisitos/beneficios/prosa de empresa) |
| **P-BULLETS** | 2 | 3% | lista sin encabezado que la nombre |
| **P-MEZCLA** | 2 | 3% | tareas revueltas con requisitos |

**Por portal — ComputRabajo es el outlier:**
- **ZonaJobs / CABA / Portal Empleo:** casi 100% P-HEADER, plantilla consistente ("Responsabilidades" / "Tareas principales:" / "Tareas a realizar:"). ZonaJobs es el más limpio (API estructurada, 0 chrome).
- **Bumeran:** 50% P-HEADER, headers variados; 0 chrome.
- **ComputRabajo:** solo 38% P-HEADER, **50% prosa+ausente**, y el único con chrome contaminante.
- **Portal Empleo / CABA:** 100% header, pero **embeben metadata** (`Estudios requeridos:`, `Modalidad:`, `Días laborables:`) que el NLP **levanta como si fueran tareas**.
- **Indeed:** headers frecuentes en **inglés** ("Responsibilities", "Key Responsibilities", "What you will be doing"); un caso extremo (descripción = solo el menú de navegación del portal) donde el NLP **alucinó 5 tareas inexistentes**.

**Encabezados reales observados (más allá de "Responsabilidades:"):** interrogativos ("¿Qué harás?", "¿Qué vas a hacer?", "¿QUÉ DESAFÍOS TE ESPERAN?", "¿Cuáles serán los principales desafíos?"), "Tu misión / Misión del puesto", "Lo que harás", "Funciones / Principales Funciones", "Tareas / Tareas principales / Las tareas son", y sus equivalentes en inglés.

---

## 3. P3 — Tipología de fallos (62 casos leídos)

44 "ciego" + 12 control + 6 honesto.

| clase | ciego (44) | control (12) | honesto (6) | total |
|---|---|---|---|---|
| **(a)** sección presente, no/apenas extraída | 8 | 0 | 0 | **8** |
| **(b)** requisito extraído como tarea | 7 | 0 | 0 | **7** |
| **(c)** skill suelto como tarea | 0 | 0 | 0 | **0** |
| **(d)** paráfrasis/invención | 1 | 0 | 0 | **1** |
| **(e)** truncamiento/pérdida parcial | 12 | 3 | 0 | **15** |
| **(f)** extracción correcta | 8 | 9 | 0 | **17** |
| **(g)** genuinamente sin tareas | 8 | 0 | 6 | **14** |

**Precisión de la heurística "ciego" de P1 = ~64%** (28/44 fallos reales). Pero sesgada por portal:

| subpoblación ciego | fallos reales | precisión |
|---|---|---|
| ComputRabajo | 10/22 | **45%** |
| Bumeran + ZonaJobs | 18/22 | **82%** |

**Calibración de la magnitud (aplicando precisión por portal a los ciegos de P1):**

| portal | ciegos P1 | precisión | fallos reales |
|---|---|---|---|
| computrabajo | 4.551 | 0,45 | 2.048 |
| bumeran | 1.209 | 0,82 | 991 |
| indeed | 720 | 0,82* | 590 |
| zonajobs | 679 | 0,82 | 557 |
| portalempleo | 129 | 0,82* | 106 |
| **total** | **7.288** | | **~4.292 (4,4% corpus)** |

*Indeed/Portal Empleo no se leyeron a fondo en la sub-población ciego; se asume la precisión de los portales estructurados (incertidumbre honesta).

**Hallazgos cualitativos:**
- **(e) truncamiento es el modo dominante y TRANSVERSAL.** No solo en avisos ruidosos: 3 de 12 **controles limpios** perdieron la tarea nuclear (ej. id 2176458 perdió *"Mecanizar en máquinas CNC con FAGOR"*, que define el puesto; id 2176620 perdió 3 de 7). **El ≤2 es cota inferior de la pérdida total** — hay avisos con 6 tareas reales que rinden 4, invisibles a la heurística.
- **(a) ceguera a secciones enumeradas con encabezado** — lo más grave: id 1118165658 lista 7 responsabilidades bajo encabezado y extrae 1; id 5790086984 ("Tareas a desarrollar:", 6 tareas) extrae 1 fragmento.
- **(b) confusión requisito→tarea** — cuando los requisitos van bulleteados, "buscar bullets" los captura (id 6477274334 extrajo "Disponibilidad fin de semana"; id 1118058753 "Disponibilidad presencial").
- **(d) invención** marginal (1/62): id 6171358600 extrajo "realizar dibujos y planos" — no está en el aviso, inferido del título.
- **(c) skill suelto: 0** en esta muestra.
- **separador-colisión (4 casos):** el split por `;` parte una sola tarea en fragmentos cuando el contenido trae `;`/`,` (id 5790086984, 2185030/2187269, 1118076732). A escala es raro (paréntesis desbalanceado en 0,07% de items) pero infla artificialmente el conteo de ceguera en los casos que toca.
- **contaminación-cruzada: 0 observada** (riesgo real, no materializado).

---

## 4. P4 — Artefacto para Cyn

`exports/cyn_backlog/validacion_tareas_muestra_2026-08-25.md` — **28 casos** representativos de la tipología (a/b/d/e/f/g + separador-colisión + falsos positivos de la heurística), cada uno con: id, título, cuerpo del aviso (chrome de CT ya recortado para que lea el cuerpo real), tareas extraídas, y 3 columnas para marcar (¿falta?/¿sobra?/veredicto). Encabezado con **la definición de tarea del MOL para su visto o corrección** — si Cyn ajusta la definición, ese ajuste gobierna el rediseño. Incluye una pre-clasificación interna de Claude por caso (a ocultar antes de dársela a Cyn, para no anclar su juicio).

---

## 5. La vara vs. la instrucción vigente (auditoría del prompt)

Instrucción actual (`database/prompts/extraction_prompt_lite_v1.py`, regla 3, textual):

> *"tareas_explicitas: Extraer CADA responsabilidad/tarea como item separado, usando punto y coma (;) como separador. Buscar bullets (-), numeracion (1., 2.), o 'Responsabilidades:' en la descripcion. Extraer cada tarea de forma INDIVIDUAL, no resumir ni condensar. Si hay 5 responsabilidades listadas, deben aparecer 5 items separados por punto y coma."*

Contrastada contra la vara y los patrones reales, tiene **cinco huecos**:

1. **Ancla solo en marcadores explícitos** (bullets/numeración/"Responsabilidades:") → ciega al **17% en prosa** y a las **listas por salto de línea sin viñeta**.
2. **Diccionario de encabezados demasiado chico** → pierde interrogativos ("¿Qué harás?"), "misión", "funciones", "tareas a desarrollar", y **todos los encabezados en inglés** (Indeed).
3. **Sin definición negativa** → no dice que requisitos/beneficios/atributos del candidato/metadata **NO son tareas** → alimenta (b) (y la captura de bullets de requisitos).
4. **Conflación "responsabilidad/tarea"** y sin instrucción de **fidelidad textual** → deja lugar a (d) paráfrasis/invención.
5. **No contempla el vacío legítimo ni el chrome** → ante P-AUSENTE fuerza/alucina (Indeed menú→5 tareas); y no descarta "Ofertas similares"/metadata de CT/Portal Empleo.

El separador `;` además **colisiona** con contenido que trae `;`/`,`.

---

## 6. Recomendación (nada se ejecuta — decisión de Gerardo)

Ordenado por costo/beneficio:

1. **Pre-limpiado de chrome ANTES del NLP (barato, alto impacto, no toca el prompt).** Recortar el boilerplate de ComputRabajo ("Ocultaste esta oferta", "Acerca de", "Ofertas similares", "Evaluación general", "Palabras clave", footer DGNET) y la metadata estructurada de Portal Empleo/CABA/Indeed. Reduce ruido, elimina el riesgo de contaminación-cruzada y mejora la relación señal/ruido que ve el LLM. Es una regla de preprocesamiento (`config/nlp_preprocessing.json`), reutilizable.

2. **Rediseño del prompt de extracción de tareas**, con correcciones dirigidas por tipo de fallo:
   - **(a/prosa)** modo prosa: segmentar por verbos de acción cuando no hay lista; tratar el salto de línea como delimitador válido.
   - **(headers)** ampliar el diccionario de encabezados: interrogativos, "misión/funciones/tareas a desarrollar", **y sus equivalentes en inglés**.
   - **(b)** definición negativa explícita: excluir requisitos del candidato, beneficios, condiciones, skills sueltos y metadata estructurada.
   - **(d)** exigir **fidelidad textual** (no inferir del título; no parafrasear).
   - **(g)** permitir **salida vacía** cuando el aviso genuinamente no enuncia tareas, en vez de forzar/alucinar.
   - **(separador)** cambiar el delimitador de `;` a uno robusto (p. ej. array JSON nativo) para eliminar la colisión.

3. **Post-filtro de limpieza** para los tipos (b)/(c): un pase que descarta items que matchean patrones de requisito/beneficio/condición (barato, complementa el prompt).

4. **Gold set de tareas como gate del rediseño.** Proponer **80–120 casos** validados por Cyn (usar la muestra P4 como semilla), estratificados por patrón (header/prosa/ausente) y por portal, con las tareas correctas anotadas. Métricas de gate: **recall de tareas** (¿cuántas de las reales levanta?, ataca a/e), **precisión** (¿cuántas de las extraídas son tareas reales?, ataca b/c/d), y **tasa de vacío correcto** (ataca g). El rediseño no pasa a producción sin superar el gold set.

5. **Dimensionar la re-extracción.** Si el rediseño se aprueba: la re-extracción total son las **98.229** con NLP (costoso, requiere Ollama; estimar en corrida por lotes). Alternativa dirigida: re-extraer solo la **población afectada** — los ~7.288 ciegos + los ~18.900 con fragmentos sospechosos (§quality) — pero **(e) es transversal**, así que la re-extracción dirigida deja fuera pérdidas parciales en avisos con 3-5/6+ tareas. La decisión total-vs-dirigida es de Gerardo con este diagnóstico en la mano.

---

## Anexo — método y trazabilidad

- **Read-only.** Toda la medición sobre `database/bumeran_scraping.db` en modo `ro`. Cero cambios a config/NLP, cero reprocesamiento.
- **Corpus:** 98.229 ofertas base con NLP (JOIN `ofertas`×`ofertas_nlp` por `CAST(id_oferta AS TEXT)`); las 541 restantes de `ofertas_nlp` son sub-ofertas multi-posición (id sintético sin fila en `ofertas`), analizadas aparte.
- **Riqueza:** `largo_descripcion` está 0% poblada en BD → longitud calculada sobre `COALESCE(descripcion_utf8, descripcion)`.
- **n_tareas:** split de `tareas_explicitas` por `;` (items no vacíos).
- **Muestras:** seed fijo 42. P2 = 66 (aleatoria estratificada por portal). P3 = 62 (ciegos estratificados por portal + 12 control 3-5 tareas + 6 honesto). Clasificación por lectura contra la vara.
- **Señales de calidad (proxies, no fallos confirmados):** items que empiezan en minúscula 14,4%; items ≤2 palabras 5,4%; paréntesis desbalanceado (colisión separador) 0,07%; ofertas con ≥1 item sospechoso 20%.
- **Scripts:** `scratchpad/m_p1.py` (matriz+cortes), `m_p1b.py` (chrome CT), `m_dump2.py` (muestras), `m_calib_p4.py` (calibración+artefacto). Poblaciones en `m_p1_poblaciones.json`.
