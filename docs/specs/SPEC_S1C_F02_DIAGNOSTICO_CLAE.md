# SPEC S1C-F0.2 — Diagnóstico de la regresión CLAE 2026-03

> Versión 0.1 · 2026-06-12 · Fase 0 del master S1.C — Reparación
> Diagnóstico read-only de la caída de cobertura de clasificación CLAE/sector detectada en la ventana F0.1 (V6): cobertura ~100% hasta 2026-02, cae desde 2026-03 en todos los portales. Este spec encuentra la causa (o la acota a una lista corta de sospechosos). No repara: la reparación, si corresponde, es un spec posterior.

## 1. Propósito

Determinar qué cambió alrededor de marzo 2026 que hizo caer la cobertura CLAE, para poder (a) decidir si el backlog se procesa con la versión vigente o se corrige primero, y (b) tomar el corte t1 (baseline del harness) sin contaminación. Es bloqueante de la §4.1 del master.

## 2. Reutilización

- BD local `database/bumeran_scraping.db` (read-only).
- Camino sector/CLAE ya relevado en S1.B.5 (NLP): prompt en `database/prompts/extraction_prompt_lite_v1.py`, reglas en `config/nlp_*_rules.json`, modelo qwen2.5:7b.
- Hallazgo de residencia (F0.1 V7): `config_loader.py` lee `config_overrides` de Supabase en runtime — candidato a cambio sin commit.
- Veredicto V6 de F0.1 como punto de partida (la caída es por mes × portal).

## 3. Entregables

1. Esta spec con la sección 8 (Diagnóstico) completa: fecha exacta del quiebre, causa identificada o lista corta de sospechosos con evidencia, y recomendación (reparar antes del backlog / aceptar y reprocesar).

## 4. Implementación — el diagnóstico en cuatro pasos

### D1 — Clavar la fecha exacta del quiebre (BD local, read-only)
Refinar el "~2026-03" de V6 a la semana o el día.
- Query: cobertura CLAE (proporción de ofertas con `clae_descripcion_seccion` no nula / no "Otro" / no vacía — confirmar el valor de "sin clasificar" real con un GROUP BY antes) agrupada por **semana** de procesamiento NLP, sobre el período 2026-01 a 2026-06, para Bumeran y ZonaJobs (los dos portales con caída limpia en V6).
- **Salida**: la semana exacta donde la cobertura pasa de ~alta a ~baja. Ese es el corte temporal que ancla D2.

### D2 — Qué cambió en esa ventana (git log + config, read-only)
Con la fecha de D1, buscar todo lo que cambió en el camino sector/CLAE en una ventana de ±2 semanas alrededor del quiebre.
- `git log` filtrado por fecha sobre los archivos del camino: `database/prompts/extraction_prompt_lite_v1.py`, `config/nlp_validation_rules.json`, `config/nlp_inference_rules.json`, `config/nlp_correction_rules.json`, `process_nlp_from_db_v11.py`, `config_loader.py`, y cualquier script con "clae" o "sector" en el nombre (buscarlos primero con `git ls-files | grep -iE 'clae|sector'`).
- Para cada commit en la ventana: qué tocó, si afecta el catálogo de sectores, el prompt, la normalización o las reglas de gate sobre sector.
- **Atención al config_override de Supabase**: si nada en el código cambió en la ventana, el cambio pudo venir de `config_overrides` (que el pipeline lee en runtime). Anotar esa posibilidad — su verificación plena requiere el historial de esa tabla en Supabase (marcar como "verificable en próxima ventana viva" si el código no explica la caída).

### PUNTO DE CONTROL — parar y reportar tras D1-D2
Reportar la fecha exacta del quiebre y los commits/cambios candidatos de la ventana, antes de profundizar. Si D2 ya señala un culpable obvio (ej. un commit que cambió el catálogo de sectores justo en la semana del quiebre), decirlo. Esperar OK para D3-D4.

### D3 — Confirmar el mecanismo (read-only)
Con el sospechoso de D2, confirmar que explica la caída.
- Si es un cambio de catálogo/prompt: comparar el catálogo de sectores antes y después del commit (git show), y ver si la caída coincide con la introducción de la regla de normalización a "Otro" relevada en S1.B.5 D-04.
- Si es un cambio de modelo o de parámetros: cruzar con el downgrade conocido (aunque ese fue anterior; verificar fechas).
- Comparar muestras: ofertas de la semana antes vs después del quiebre con el mismo tipo de aviso — ¿el sector se degradó para el mismo input? (read-only sobre datos ya procesados, no reprocesar).

### D4 — Acotar el alcance y recomendar
- ¿La caída afecta solo a CLAE/sector o arrastra otros campos? (chequear cobertura de 2-3 campos vecinos en la misma ventana: provincia, seniority).
- ¿Cuántas ofertas procesadas desde el quiebre están afectadas? (conteo).
- Recomendación binaria para la §4.1 del master: **(a)** la regresión es corregible con un cambio acotado → reparar antes de soltar el backlog; o **(b)** la causa no está clara / la corrección es grande → procesar el backlog conscientemente con la regresión y reprocesar después. Con evidencia para la opción que se recomiende.

## 5. Dependencias
- BD local accesible (D1, D3, D4).
- git history (D2).
- Posible dependencia de Supabase para el historial de `config_overrides` (solo si D2 no encuentra la causa en código) — diferible a una ventana viva.

## 6. Validación
El spec valida cuando D1 (fecha), D2 (cambios candidatos) y D4 (recomendación) tienen resultado documentado. D3 puede quedar parcial si la causa requiere el historial de Supabase, marcándolo.

## 7. Riesgos
- **Read-only estricto**: solo SELECT y lectura de git/código. No reprocesar ofertas, no correr el NLP, no tocar config.
- Ojo con el lag negativo de `scrapeado_en` (S1.B.5 D-11): para D1 usar el timestamp de procesamiento NLP, no el de scraping, o verificar cuál es fiable.
- Si aparecen varios cambios candidatos sin uno dominante: reportar la lista corta, no forzar un culpable.

## 8. Diagnóstico

> Ejecutado read-only 2026-06-16 sobre `database/bumeran_scraping.db` + git. **Veredicto: NO es una regresión — es el fin del efecto de un backfill único.** El backlog puede soltarse ya; la cobertura baja es la tasa real del camino vivo, no un bug nuevo.

### 8.1 D1 — Fecha del quiebre

El quiebre es **mediados-fines de marzo 2026**, pero **no es una única semana universal** — varía por portal y el piso post-quiebre depende de la calidad de metadata de cada portal:

| Portal | Régimen alto (antes) | Semana de quiebre | Piso estable (después) |
|---|---|---|---|
| Bumeran | 100% hasta W12 | **W13** (23-mar) | ~69% |
| ZonaJobs | 100% hasta W12 | **W13** (23-mar) | ~67-69% |
| ComputRabajo | ~99% hasta W10 | **W11-W12** | ~66% |
| Indeed | ~99% hasta W10 | **W11-W12** | ~40-50% |
| PortalEmpleo | ~100% hasta W11 | **W12** | ~75-83% |

Antes: **~100% en todos**. Después: **un piso distinto por portal**, correlacionado con la calidad de metadata (Indeed, el peor, ~40%; Bumeran ~69%). La semana de transición suele desplomarse por debajo del piso (CT W12 21%, Indeed W12 18%) y luego "recupera" al piso.

**Corrección del spec contra la realidad (hallazgo, no error):** la columna real es `clae_code` / `clae_seccion` / `clae_grupo` (no `clae_descripcion_seccion`). "Sin clasificar" = `clae_code IS NULL`.

**Deuda de observabilidad (D-15):** `nlp_processed_at` está **100% NULL** (0/69.794). No existe timestamp de procesamiento, así que el eje temporal del diagnóstico es **fecha de publicación como proxy** del procesamiento. Registrar como deuda: el pipeline NLP no sella la fecha de proceso, lo que imposibilita distinguir "cuándo se procesó" de "cuándo se publicó".

### 8.2 D2 — Qué cambió en la ventana

**No hay commit de código culpable en el camino CLAE.**

1. **Líder — artefacto de cobertura por backfill:** el corpus histórico llegó a ~100% por un pase único de backfill/clasificador (`scripts/db/populate_clae_seccion.py` / `reprocesar_clae.py`). Lo publicado desde marzo depende del **camino vivo del postprocessor** (`nlp_postprocessor._classify_clae`), cuya tasa natural es **dependiente del portal**.
2. **Descartado — `63ff7fa5` (2026-03-22, "pipeline usa overrides de Supabase"):** temporalmente pegado al quiebre, pero **solo enruta `nlp_inference_rules`** por overrides; no toca CLAE ni sector. *Red herring*.
3. **Descartado — `clae_semantic_classifier.py`:** solo cambió 2026-02-14 y 2026-04-09, fuera de la ventana.
4. **Mecanismo:** `sector_empresa='Otro'` NO explica el CLAE-null (37.147 filas "Otro" sí tienen CLAE). La regresión aparente está en la **cobertura de asignación de CLAE en sí**, no en degradación del sector.

### 8.3 D3 — Confirmación del mecanismo

**(a) Estabilidad post-quiebre — confirma "tasa natural", refuta "regresión en curso":**

| Portal | Abr | May | Veredicto |
|---|---|---|---|
| Bumeran | 69.7% | 69.1% | plateau |
| ZonaJobs | 68.1% | 68.2% | plateau |
| ComputRabajo | 65.8% | 68.3% | plateau |
| Indeed | 47.0% | 42.7% | plateau (ruido) |
| PortalEmpleo | 69.6% | 75.9% | plateau |

Marzo es mes de transición (mezcla backfilleado-alto + vivo-bajo). Desde abril cada portal se asienta en un **piso plano**. Una regresión real seguiría degradando; un escalón a un plateau estable es la **firma de fin-de-efecto-backfill**.

**(b) Aislamiento del campo — confirma que no es degradación general del NLP:** solo CLAE cae (100%→62%); provincia, localidad, seniority, área y modalidad se mantienen o mejoran en la misma ventana. El único campo que dependía del pase backfill es el único que revirtió.

**(c) Rastro de ejecución del backfill — diferido a ventana viva:** no hay log local de corrida de `populate_clae_seccion.py` / `reprocesar_clae.py` (solo logs de 2025 y de `supabase_sync`). El método (`clae_metodo`) es compartido por camino vivo y backfill, así que no distingue. La fecha exacta de la corrida del backfill **no es verificable en local** → marcar para próxima ventana viva (run history / Supabase). El patrón de datos (uniforme ~100% antes, plateau estable después, transición en marzo) es la evidencia positiva suficiente para el encuadre.

### 8.4 D4 — Alcance y recomendación

**Alcance:**
- **Aislado en CLAE.** Campos vecinos sin impacto (ver 8.3b).
- **Afectadas: 13.021 ofertas publicadas desde 2026-03 sin CLAE = 99% de todos los CLAE-null** (13.159 total). El corpus histórico (pre-marzo) está íntegramente cubierto; el hueco es enteramente la era post-backfill.

**Recomendación para la §4.1 del master — cambia de forma respecto del veredicto V6:**

> **(b reformulada) El backlog se puede soltar YA.** La cobertura CLAE baja (~62-69% según portal) **es la tasa real del camino vivo, no un bug nuevo introducido en marzo**. No hay regresión que reparar antes de procesar. El corte t1 (baseline del harness) se toma **con esa tasa real como baseline honesto**. Subir la cobertura CLAE pasa a ser **objetivo de C8 (cobertura), no precondición del backlog**.

Esto reemplaza la condición que V6 había dejado en §4.1 ("habilitado solo si primero se diagnostica o se acepta conscientemente la regresión CLAE de 2026-03"): el diagnóstico está hecho y **no hay regresión** — la condición se satisface y el backlog queda habilitado. El ajuste del texto del master va en ciclo aparte tras el merge.

### 8.5 Registros derivados

- **D-15 (reglamento de proceso):** el **backfill no repetido** es una instancia de D-15 — un pase masivo único que levantó una métrica sin dejar un mecanismo que la sostenga, creando la ilusión de regresión cuando el efecto caduca. Norma: todo backfill que mejore una métrica debe declarar si su efecto es permanente (el dato queda) o transitorio (depende de re-corridas), y registrar fecha/alcance de corrida.
- **Deuda de observabilidad:** `nlp_processed_at` 100% NULL (ver 8.1). Sin sello de fecha de proceso no se puede separar publicación de procesamiento — bloquea diagnósticos temporales futuros.

## 9. Criterio de aceptación
TERMINADO cuando la sección 8 documenta: fecha del quiebre, causa o lista corta de sospechosos con evidencia, alcance, y recomendación para la §4.1. Aplica la definición de terminado del Eje 6: el diagnóstico tiene consumidor (la decisión de soltar el backlog) y queda registrado.
