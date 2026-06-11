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

> *Versión 0.1 — Capa 5.1 cerrada (fuentes: Gerardo + Cyn + "MOL en perspectiva v2" + "Informe MOL COMPLETO", ambos de mayo 2026). Capa 5.2 pendiente, próximo paso.*
