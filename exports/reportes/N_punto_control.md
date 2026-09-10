# FRENTE N — Punto de control: rediseño de extracción de tareas (a Gerardo)

**Read-only sobre producción. NADA se re-extrajo masivamente — el techo del encargo es el gate.** El prompt de producción NO se tocó; v12 vive en el branch con flag. Esta nota trae, en orden: (0) el espejo, (1) gate 1, (2) gate 2, (3) la atribución 7b-vs-14b, (4) los 4 REVISAR, (5) el dimensionamiento por escenario, (6) la recomendación.

> Se lee JUNTO con: `N_espejo_prompt_v12.md` (espejo), `N_gate1_tabla.md` (28 caso×caso), `N_gate1_revisar4.md` (los 4), `N_gate2_*` (muestra fresca), y el gold set `metrics/gold_set_tareas.json`.

---

## 0. El espejo (se lee antes que los números)

Las **33 reglas** del prompt v12 mapean a las **28 claves metodológicas de Cyn** (columnas "Lógica de razonamiento" + "Claves metodológicas" de su validación). Los 28 casos citados, 0 claves sin cubrir. La prosa de Cyn se COMPILÓ, no se reescribió — cada regla lleva su caso de origen. Detalle: `N_espejo_prompt_v12.md`. Reparto por sección: PASO 1 recorrer-todo (4) · PASO 2 formas/nominalización/gerundio (4) · PASO 3 granularidad (5) · PASO 4 fidelidad/nivel-de-intervención (8→ver espejo) · PASO 5 atribución/qué-no-es-tarea (8) · PASO 6 vacío-estricto (2) · PASO 7 control final (3).

**Pregunta abierta para Cyn (no resuelta, anotada como manda el encargo):** su granularidad separa a veces lo que v12 fusiona (participar / articular; analizar / reportar). El gate lo cuenta como `cubierta-mal-granulada`, no como falla. ¿Confirma que la fusión de acciones sobre objetos distintos-pero-contiguos es aceptable, o exige separación estricta? Gobierna el ajuste fino.

---

## 1. Gate 1 — los 28 de Cyn (equivalencia funcional, granularidad aparte)

Pipeline **N1→v12→N3**, modelo **qwen2.5:14b**, cuerpo completo de BD (no el truncado del Excel).

| Métrica | Resultado |
|---|---|
| **PASA** (cob≥85%, prec≥90%, 0 sobras) | **23/28** |
| PASA-con-observación | 1 |
| REVISAR (near-threshold, granularidad) | 4 (C1, C6, C12, C28) |
| Cobertura funcional promedio | **97%** |
| Precisión promedio | **95%** |
| **Anti-alucinación (requisito DURO)** | **10/10 vacío-válido, 0 regresiones ✅** |
| **6 OK intocables** | **sin regresión ✅** (todos PASA/OK) |

Contraste con v11 (lo que hoy corre): en los casos ricos v11 extraía 1-2 tareas de 6-9 reales (truncamiento, el fallo dominante del frente M); v12 recupera el bloque completo. Ej. C1: v11 **1** → v12 **7** (las 9 unidades de Cyn con 2 fusiones); C2 ("Tareas a desarrollar:" 6 ítems): v11 **1 fragmento** → v12 **6 limpias** sin el fragmento huérfano "seguridad y usabilidad". Tabla caso×caso: `N_gate1_tabla.md`.

---

## 2. Gate 2 — muestra fresca de 200 (v11 vs v12) + población anti-alucinación

Estratificada por portal, ComputRabajo sobre-muestreado. v11 = lo almacenado en BD; v12 = N1→v12→N3 con 14b.

| Métrica (muestra 200) | v11 | v12 |
|---|---|---|
| n_tareas media | 5,37 | **6,00** |
| n_tareas mediana | 5 | **6** |
| % ofertas vacías | 2% | 16%* |
| **requisito/beneficio-como-tarea** | **3,6%** de los ítems | **0,0%** ✅ |

*El salto de %vacías (2%→16%) es CORRECTO: v11 alucinaba tareas en avisos sin acciones (título-only, requisitos-only); v12 devuelve []. El frente M ya había medido ~0,1% genuinamente sin-tareas es falso — muchos avisos son requisitos/perfil-only y v12 los deja vacíos como Cyn manda.

**Anti-alucinación (población genuinamente-sin-tareas):** de 30 avisos muestreados por longitud corta, v12 dio [] en 21; los 9 con n>0 se investigaron UNO POR UNO (como exige el laudo):
- **5 eran extracciones CORRECTAS** de avisos cortos con tareas reales ("Liquidación de sueldos, confección de recibos…", "Instalación y mantenimiento de instalaciones eléctricas…"). Mi muestreo por longitud los etiquetó mal; NO son alucinaciones.
- **4 eran alucinación REAL** — todas **título-only** (el cuerpo es apenas un título + un bloque de metadata que N1 recorta): "AYUDANTE DE FARMACIA"→5 tareas, "administrador de redes"→8, "ayudante logística"→7, y una nota de buscador ("me gustaría ser cajera").

**Corrección aplicada y verificada (dentro del gate, antes de cualquier GO):** guard determinístico `parece_solo_titulo` (cuerpo corto SIN verbo ni nominalización → [] sin LLM). Post-fix: los 3 título-only claros → [] ✅, y los avisos cortos con tareas reales siguen extrayendo ✅ (repositor "Reponer góndolas", abogado "Asistir a audiencias"). Queda 1 residual: notas de buscador de empleo ("me gustaría ser…") — outlier de calidad de dato de origen, no un aviso; anotado.

---

## 3. Atribución del bundle — prompt-solo (v12+7b) vs prompt+modelo (v12+14b)

El hallazgo 14b convierte el cambio en DOS: el prompt nuevo Y el modelo mayor. Descomposición sobre la misma submuestra (n=70), mismo prompt v12:

| Métrica (n=70, mismo prompt v12) | v12 + **7b** | v12 + **14b** |
|---|---|---|
| n_tareas media | 7,09 | 6,30 |
| n_tareas mediana | 7 | 6 |
| % vacías | 17% | 14% |
| **requisito-como-tarea** | **0,0%** | **0,0%** |
| latencia media (servidor compartido) | 3,4 s | 5,5 s |
| **of/h efectiva** (contended) | **≈ 1.069** | **≈ 650** |
| ítems totales | 496 | 441 |
| ofertas con distinto n_tareas 7b↔14b | — | 36/70 |

**Atribución:** la ganancia de **recall** y la **precisión de requisito (3,6%→0,0%)** son del **prompt** — se dan en AMBOS modelos. La **granularidad** es del **modelo**: el 7b microfragmenta (496 ítems, media 7,09 = más unidades por sobre-división), el 14b respeta la unidad funcional (441 ítems, media 6,30, más cerca de la granularidad de Cyn — confirmado en gate 1). 36/70 difieren: casi siempre por granularidad, no por contenido. **14b estable en corrida sostenida: 10,3 GB VRAM, 0% offload a CPU** (140 llamadas seguidas, sin degradación).

Cualitativo (ya observado en gate 1): con el MISMO prompt v12, el 7b **microfragmenta** unidades multi-verbo ("desarrollar, configurar y mantener" → 3 tareas) y a veces filtra un atributo ("iniciativa para investigar causas raíz"); el 14b respeta la unidad funcional y la atribución. La ganancia de RECALL y la eliminación de alucinación son del **prompt** (ambos modelos mejoran sobre v11); la disciplina de GRANULARIDAD y precisión fina es del **modelo 14b**.

---

## 4. Los 4 REVISAR del gate 1 (decide Gerardo, ojo humano)

Cerca del umbral por granularidad/fidelidad, no por ceguera. Tabla tarea-oro | cubierta | por qué, en `N_gate1_revisar4.md`. Resumen:
- **C1** (78%): las 9 unidades de Cyn cubiertas con 2 fusiones (seguimiento-pedidos+coordinar; seguimiento-cobranzas+controlar-vencimientos). Funcionalmente completo; disenso de granularidad.
- **C6** (75%): perdió especificidad — "monitorear indicadores CPA/ROAS" salió como "analizar resultados" (fidelidad blanda) + sobre-división del primer bloque.
- **C12** (83%): recuperó la misión (captar/comercializar) tras el fix; borde por granularidad.
- **C28** (83%): con cuerpo completo recuperó documentación; borde por fusión/división de las unidades SCADA.

---

## 5. Dimensionamiento POR ESCENARIO (nada se ejecuta — decide Gerardo)

**Población a re-extraer (opciones):**
- **Total con NLP:** 98.229 ofertas (frente M).
- **Dirigida:** CT post-limpieza + cortos + los ~7.288 "ciegos" del frente M + los que hoy tienen requisito-como-tarea (~3,6% de ~530K ítems). PERO el frente M mostró que el truncamiento (e) es TRANSVERSAL (afecta también avisos con 3-5/6+ tareas) → la dirigida deja fuera pérdidas parciales. Recomendación de cobertura: total, salvo restricción de tiempo.

**Horas de máquina por escenario** (extracción SOLO-tareas con prompt v12; of/h medida en servidor compartido con 9+ sesiones — una GPU dedicada rinde ~2× y baja las horas a la mitad; se presenta el número contended, sin optimismo):

| Escenario | Población | of/h (contended) | Horas (contended, 1 GPU) | Nota |
|---|---|---|---|---|
| v12 + 7b — total | 98.229 | ~1.069 | **~92 h** | barato; microfragmenta (revisar granularidad) |
| v12 + 14b — total | 98.229 | ~650 | **~151 h** | granularidad limpia; **recomendado** |
| v12 + 14b — dirigida | ~30 K (ciegos+cortos+CT-post-limpieza+requisito) | ~650 | **~46 h** | ⚠ deja fuera el truncamiento (e), que es TRANSVERSAL (frente M) |

Notas de dimensionamiento:
- Es throughput de extracción SOLO-tareas. Si se folddea al pipeline NLP completo (20 campos), la throughput la domina el resto de la extracción (~300 of/h en producción) y la re-extracción total se mide en esa escala, no en la de tareas-solo.
- **VRAM/estabilidad 14b:** 10,3 GB residentes, 0% offload — entra holgado en la GPU; sin spillover ni degradación en las 140 llamadas del test. No hay riesgo de estabilidad para una corrida larga en esta máquina.
- Recomendación de población: **total**, salvo restricción dura de tiempo — la dirigida no cubre el truncamiento parcial en avisos con 3-5/6+ tareas.

**La cascada completa (laudada) que el dimensionamiento refleja** — NO es de este encargo, se ejecuta con la decisión de Gerardo:
snapshot pre-cascada (manifiesto+sha256 en `exports/cohorts/`, patrón frente L) → re-extracción v12 → re-derivación de skills indirectas → **shadow corto del árbol** (v12-tareas vs v11-tareas sobre los 7 hubs, dos poblaciones: las que hoy deciden [estabilidad] y **las que hoy abstienen y con v12 deciden — sobre-muestreada**, territorio nunca evaluado; vara dual del traductor: no-explicadas <15%, costo declarado ≤10%, mejoras intactas) → recién entonces re-matching masivo.
Dos decisiones del laudo escritas acá:
1. **El candado F0.4b protege DECISIONES, no datos de entrada:** las 6.326 validadas-humanas SÍ reciben re-extracción de tareas + actualización de skills derivadas; su matching NO se re-decide, jamás. Verificación de 0 pisadas (patrón frente L).
2. **El aviso de época es paso final:** cascada completa = release nuevo (tareas+skills+matching) → aviso → refresh del sandbox del harness → re-publicación a colegas. En el costo y la secuencia.

---

## 6. Recomendación

1. **El prompt v12 + N1 + N3 pasan el gate:** recall recuperado (v11 1-2 → v12 bloque completo), alucinación eliminada (requisito-como-tarea 3,6%→0%; título-only tapado por guard), separador colisión resuelto (JSON). Anti-alucinación y 6-OK sin regresión.
2. **Modelo: qwen2.5:14b para la re-extracción de tareas** — la disciplina de granularidad y precisión fina lo justifica; el 7b (producción) microfragmenta. Costo en §5.
3. **Antes del GO:** cerrar los 4 REVISAR con Cyn (granularidad) y su respuesta a la pregunta abierta del espejo; correr el gold set como gate de regresión permanente.
4. **La decisión de re-extraer (total vs dirigida) y de la cascada es de Gerardo**, con estos números.

---

## Anexo — artefactos y trazabilidad
- N1 `scripts/frente_n/limpiar_chrome.py` (+ guard título-only) · N2 `prompt_tareas_v12.py` (v12.2) · N3 `postfiltro_tareas.py` · gold `metrics/gold_set_tareas.json` · runners `gate_runner.py`/`gate2.py`/`decomp_modelo.py` · adjudicador `adjudicar_gate1.py`.
- Tests: `tests/frente_n/test_n1_n3.py` (12/12 verde).
- N1 medido: CT chrome removido 57% prom (71% mediana), Portal Empleo/CABA metadata 50%/39%, API portals 0%, cuerpo preservado (0 vacíos indebidos).
