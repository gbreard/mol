# SPEC U-1 — Crítico: datos producto-visibles

**Versión:** 1.0
**Fecha:** 2026-05-04
**Autor:** Gerardo + Claude
**Estado:** Borrador para revisión
**Predecesor:** `2026-04-29_U_diagnostico_codificaciones_mol.md` (SPEC U original — diagnóstico, no implementación)
**Reportes que sustentan este SPEC:**
- R1: `2026-05-04_conteos_pre_spec_u.md`
- R2: `2026-05-04_conteos_2_diccionario_argentino.md`
- R3: `2026-05-04_conteos_3_label_drift_y_zombies.md`
- R4: `2026-05-04_conteos_4_consolidado.md`
- R5: `2026-05-04_conteos_5_bge_scraping.md`
- R6: `2026-05-04_conteos_6_supabase_nlp_uris.md`

---

## 1. Propósito y alcance

**Propósito:** corregir los bugs que producen datos visibles incorrectos al usuario del MOL (analistas OEDE, dashboard Skill Intelligence, validadores de Cynthia) y que bloquean la implementación de cualquier fix posterior.

**Alcance:** 5 fixes críticos (F0 + C1 + C2 + C3 + C4 + C5) más una métrica de validación (F-meta). Todo lo demás queda fuera de este SPEC y va a SPEC U-2 (pipeline) o SPEC U-3 (deuda técnica).

**Fuera de alcance:**
- Anti-alucinación NLP, sesgos del LLM, regresiones de scrapers → SPEC U-2
- Tablas zombies, schema mismatch, performance → SPEC U-3
- LoRA fine-tuning → diferido hasta que el sistema esté limpio
- VPS embed-server → issue separado fuera de los SPECs

---

## 2. Contexto y evidencia

Los reportes 1-6 confirmaron 5 problemas que producen datos incorrectos visibles al usuario y se refuerzan entre sí:

1. **Bug del cruce URI×label** (R3 §E1, R4 §A2). Commit `94f0d73c` (2026-04-25 16:46) en `rematch_isco_spec_h.py` introdujo un UPDATE que escribía 9 columnas pero dejaba `esco_occupation_uri`, `regla_aplicada`, `isco_label` y otros 5 campos con valores stale del run anterior. Ventana del bug: 24h hasta el fix `7aeb16a3` (2026-04-26 17:39). Resultado: 4.203 ofertas con cruce, 1.237 URIs con drift de labels, hasta 41 labels distintos para una sola URI.

2. **Bug del diccionario argentino** (R2 §A4). El path "diccionario argentino" del matcher v3.5.x escribe `isco_code` y `esco_label` pero **nunca** `esco_occupation_uri`. No es regresión — es feature que nunca se construyó. Resultado: 3.762 ofertas con `esco_occupation_uri = ''` (99,9% vienen del diccionario, no de reglas). De estas, 1.904 son ISCO 4110 (administrativo).

3. **Embeddings de ocupaciones borrados** (R4 §A3). Commit `25828fbf` (2026-04-24 22:45) destrackeó los binarios autogenerados, **1 minuto después** de promoverlos a producción (`66f922fa`). Los archivos quedaron en `database/embeddings/enriched/` pero el matcher los busca en `database/embeddings/`. Resultado: `_semantic_match_title()` retorna `[]` siempre, `code_to_occupation = {}` siempre, SPEC J nominalmente activo pero efectivamente apagado. 12.231 ofertas (20% del matching actual) procesadas post-destrackeo.

4. **Regresión de flags ESCO (DIAG A)** (R1 §B1, SPEC U original §3.1-3.2). Al refactorizar a v3.5.4, se eliminó la lógica que poblaba `is_essential_for_occupation` e `is_optional_for_occupation` en `ofertas_esco_skills_detalle`. Resultado: 1.116.011 filas con flags en cero (100% de la tabla). Imposible filtrar skills esenciales vs opcionales en el dashboard, métricas de cobertura ESCO devuelven 0/0/0.

5. **Sin sync automático a Supabase + zombies** (R6 §B1, R6 §B2). No existe cron de `sync_to_supabase.py`. Última corrida manual: 2026-04-28 (6 días atrás). Drift acumulado: −8.420 ofertas (esperable por filtro de validación) y **+28.395 skills zombies en Supabase** (skills de ofertas borradas localmente quedan en Supabase porque el re-sync hace `delete + insert` solo de las ofertas del sync actual). Vercel lee directo de Supabase sin caché propia → drift se refleja al usuario en tiempo real. Las 257 validaciones humanas reales viven solo en Supabase.

**Estos 5 problemas son producto-visibles**, lo que significa:
- Dashboards muestran labels cruzados, conteos inflados, ofertas con URI vacía.
- Filtros por skill esencial/opcional no funcionan (todos los flags son cero).
- Datos del dashboard tienen 6 días de retraso.
- Cualquier mejora downstream (M-08b, OE matching persona→oferta) hereda estos problemas.

---

## 3. Fix F0 — Snapshot BD + canarios SQL

**Esfuerzo estimado:** 1–2 horas
**Bloquea:** todos los fixes posteriores
**Tipo:** precondición operativa (no es un fix, es un seguro)

### 3.1 Problema

Los reportes 1-6 demostraron un patrón recurrente: refactors silenciosos introducen regresiones que solo se detectan meses después por reporte humano (Diego). Sin snapshots ni canarios, **cualquier fix de este SPEC puede introducir nueva regresión sin detección automática**.

### 3.2 Acción

Antes de ejecutar cualquier otro fix:

- Snapshot completo de SQLite local: dump SQL con timestamp a `data/snapshots/pre_spec_u1_YYYYMMDD_HHMMSS.sql`.
- Snapshot de tablas críticas en Supabase: export JSON de `ofertas_dashboard`, `ofertas_skills`, `issues`, `rule_candidates`.
- Crear archivo `scripts/canarios/canarios_spec_u1.sql` con 5 queries:
  - Cantidad de ofertas con `esco_occupation_uri = ''`
  - Cantidad de filas en `ofertas_esco_skills_detalle` con `is_essential_for_occupation = 0 AND is_optional_for_occupation = 0`
  - Cantidad de URIs con drift de labels (>1 label distinto por URI)
  - Cantidad de skills zombies en Supabase (filas en Supabase no presentes en local)
  - Diff Local↔Supabase de `ofertas_dashboard` (cantidad y delta vs snapshot inicial)
- Configurar cron horario que corre los canarios y escribe a `logs/canarios_YYYYMMDD.log`.
- Definir umbrales de alarma: si algún canario cambia más de X% en una hora durante la ejecución del SPEC, alarmar y pausar.

### 3.3 Criterios de éxito

- Snapshot SQL existe y es restaurable (test: restaurar a BD temporal y comparar count de filas).
- Canarios corriendo cada hora con valores baseline registrados.
- Los 5 valores baseline documentados en este SPEC para comparar después.

### 3.4 Riesgos y rollback

- **Riesgo:** snapshot grande (~3 GB BD local). Solución: usar pg_dump con compresión gzip, descartar tablas backup.
- **Rollback:** N/A. F0 no modifica nada, solo crea snapshots.

---

## 4. Fix C1 — Bug del cruce URI×label

**Esfuerzo estimado:** 4–6 horas (no incluye espera del re-rematch)
**Depende de:** F0
**Tipo:** corrección de datos

### 4.1 Problema

1.237 URIs en `ofertas_esco_matching` aparecen con más de un label distinto. Ejemplo: la URI `7235d075-...` (que canónicamente es "mozo de almacén/moza de almacén") aparece en BD con 24 labels distintos: "soldador/soldadora", "operario de prensado de fruta", "mecánico de maquinaria industrial", etc.

### 4.2 Root cause

Commit `94f0d73c` introdujo un UPDATE incompleto en `scripts/embeddings/rematch_isco_spec_h.py:persist_matching_result()`. Versión buggy escribía 9 columnas; versión fix `7aeb16a3` escribe 19. Las 8 columnas omitidas:
- `esco_occupation_uri`
- `regla_aplicada`
- `isco_label`
- `isco_regla`
- `isco_semantico`
- `decision_razon`
- `occupation_match_method`
- `dual_coinciden`

Cuando el rematch del 25/04 calculó nuevo match (URI = `U_new`, label = `L_new`), escribió `esco_occupation_label = L_new` pero dejó `esco_occupation_uri = U_old`. Resultado: 4.203 ofertas con cruce.

Evidencia: distribución por `matching_version` muestra ratio 2,62 labels/URI en `spec_h_rematch` vs 1,01 en v3.5.2 (sano).

### 4.3 Acción

- Identificar el conjunto exacto de ofertas afectadas: las que tienen `matching_version = 'spec_h_rematch'` (8.221 filas).
- **Decisión cerrada (R3, tu decisión 04/05):** re-rematch global con matcher arreglado, asumiendo desvalidación de las 8.210 ofertas afectadas (afecta el estado pero corrige el drift de raíz).
- Antes del re-rematch: confirmar que el código del matcher (commit actual o posterior a `7aeb16a3`) escribe las 19 columnas correctamente. Verificar contra el diff documentado en R4 §A2.
- Ejecutar re-rematch dirigido a las 8.221 ofertas con `matching_version = 'spec_h_rematch'`.
- **No** tocar las 4.203 ofertas con drift que ya fueron sobreescritas por el path correcto post-fix; el re-rematch las cubre.

### 4.4 Criterios de éxito

- Después del re-rematch, query: `SELECT COUNT(DISTINCT esco_occupation_label) FROM ofertas_esco_matching WHERE esco_occupation_uri = ?` para muestra de 50 URIs aleatorias → debe devolver 1 por URI.
- Cantidad de URIs con drift baja a < 50 (residuos esperables por casos edge).
- Las 63 URIs con drift donde el label canónico ni siquiera está en BD (R4 §D3) son visitadas por el re-rematch y reciben el label canónico.
- Canario de drift baja al menos 95% respecto al baseline F0.

### 4.5 Riesgos y rollback

- **Riesgo 1:** el re-rematch desvalida 8.210 ofertas que estaban en estado `validado_claude` o `validado`. Mitigación: aceptado por decisión tuya del 04/05.
- **Riesgo 2:** el matcher actual aún tiene la rama título-semántico apagada (C3). Si C3 no se ejecuta antes de C1, el re-rematch usa solo skills + reglas + diccionario. Decisión: ejecutar **C3 antes de C1** (ver §10 orden de ejecución).
- **Rollback:** restaurar desde snapshot F0. Las 8.210 ofertas vuelven a su estado pre-rematch.

---

## 5. Fix C2 — Bug del diccionario argentino

**Esfuerzo estimado:** 8–12 horas (incluye fix código + esquema JSON + reprocesamiento)
**Depende de:** F0, C3
**Tipo:** corrección de código + datos

### 5.1 Problema

3.762 ofertas con `esco_occupation_uri = ''`. De estas, 99,9% vienen del path "diccionario argentino" del matcher. 1.904 son ISCO 4110 (administrativo). El dashboard no las puede filtrar por URI ESCO.

### 5.2 Root cause

El path del diccionario argentino, en `match_ofertas_v3.py:584,587-594,782-784` y `_match_by_argentino_dict()` líneas 308-314:
- Lee la entrada del diccionario en `config/sinonimos_argentinos_esco.json`.
- Setea `result.isco_code` (desde la entrada).
- Setea `result.esco_occupation_label` (desde la entrada).
- **No setea** `result.esco_occupation_uri`. La inicialización por default queda `""`.

El JSON `sinonimos_argentinos_esco.json` no tiene URIs (0/24 entradas con campo `esco_uri`). No es regresión — es feature que nunca se construyó: el diseño original asumió que la URI se resolvería downstream pero ese downstream nunca se implementó.

### 5.3 Acción

**Fix del schema JSON** (decisión tuya del 04/05: schema mixto):
- Para entradas con default ESCO único (ej: `administrativo` → ISCO 4110 con 2 hijos ESCO, default `4110.1`): agregar campo `esco_code` que el matcher resuelve en runtime via lookup `code_to_occupation`.
- Para entradas con ambigüedad de hijos (ej: `gerente`, `analista`, `operario`, `operador`, `tecnico` — los 5 `isco_familia`): agregar campo `esco_uri` con la URI específica decidida manualmente. Esto requiere decidir un caso por entrada (~5 decisiones).

**Fix del código del matcher** (`match_ofertas_v3.py:_match_by_argentino_dict()` líneas 308-314):
- Si la entrada tiene `esco_uri`: usarlo directamente.
- Si la entrada tiene `esco_code` pero no `esco_uri`: hacer lookup en `code_to_occupation` para resolver la URI. **Precondición:** `code_to_occupation` debe estar poblado (depende de C3).
- Si ninguno está presente: error explícito (no escribir URI vacía silenciosa).

**Reprocesamiento de las 3.762 ofertas** (decisión tuya del 04/05: estrategia B, reprocesar todo):
- Identificar las 3.762 ofertas con `esco_occupation_uri = ''`.
- Re-correr el matcher sobre cada una con el código fijado.
- Verificar que escribe URI correcta.

### 5.4 Criterios de éxito

- Tras el reprocesamiento: 0 ofertas con `esco_occupation_uri = ''`.
- Las 1.904 ofertas con ISCO 4110 reciben URI canónica de "empleado de oficina/empleada de oficina" (URI específica).
- Las ofertas con `isco_familia` reciben URI específica según la decisión manual del schema.
- Test unit: `_match_by_argentino_dict()` con entrada nueva escribe URI no vacía, fallar test si retorna URI vacía.

### 5.5 Riesgos y rollback

- **Riesgo 1:** las 5 decisiones manuales sobre `isco_familia` requieren juicio humano. Si Claude Code las hace solo, puede asignar URIs subóptimas. Mitigación: este SPEC pide que las 5 decisiones las cierres vos antes de la implementación.
- **Riesgo 2:** el reprocesamiento de las 3.762 ofertas asume que el matcher arreglado produce mejor resultado que la URI vacía. En casos edge puede producir URIs incorrectas (no peores que vacías, pero mal asignadas). Mitigación: muestra de 50 ofertas re-procesadas validada manualmente antes del backfill global.
- **Rollback:** las 3.762 ofertas vuelven a `esco_occupation_uri = ''` desde snapshot F0. El cambio de código es revertible vía git revert.

---

## 6. Fix C3 — Embeddings de ocupaciones borrados

**Esfuerzo estimado:** 1–2 horas (es trivial técnicamente, importante por consecuencias)
**Depende de:** F0
**Bloquea:** C1, C2 (porque ambos dependen de `code_to_occupation` poblado)
**Tipo:** corrección de configuración

### 6.1 Problema

`database/embeddings/esco_occupations_embeddings.npy` y `database/embeddings/esco_occupations_metadata.json` no existen en disco. Están en `database/embeddings/enriched/` pero el matcher busca en raíz. Resultado:
- `_semantic_match_title()` retorna `[]` siempre.
- `code_to_occupation = {}` siempre.
- SPEC J ("esco_code como pivote autoritativo") está nominalmente activo pero efectivamente apagado.
- 20% del matching actual (12.231 ofertas) procesadas sin la rama título-semántico.

### 6.2 Root cause

Commit `25828fbf` (2026-04-24 22:45) destrackeó los archivos del repo **1 minuto después** de promoverlos a producción (`66f922fa` 22:44). Razonamiento del commit es válido (binarios autogenerados no van a git) pero el push los borró del filesystem productivo y nadie regeneró en `database/embeddings/` raíz.

### 6.3 Acción

**Decisión tuya pendiente (R5 fue en parte sobre esto):** la rama título-semántico procesó solo el 20% del matching actual. Tu pregunta del 04/05 fue *"como casi 60 mil oferta habría que ver si tiene sentido esa regla o hay que cambiarla"*.

**Dos opciones a cerrar antes de implementar:**

**Opción A — Restaurar la rama:** crear symlinks o copiar archivos de `enriched/` a la raíz, o cambiar el path en `match_ofertas_v3.py:147-163` para que apunte directamente a `enriched/`.

**Opción B — Aceptar el diseño sin esa rama:** documentar formalmente que el matcher funciona solo con skills + reglas + diccionario, eliminar el código muerto de `_semantic_match_title()`, ajustar el SPEC U §1.2 que declara peso 60/40.

**Mi recomendación: Opción A.** Razones:
- Es trivial (1 línea de código o 2 symlinks).
- Cierra una regresión silenciosa, no la oficializa.
- C1 y C2 dependen de `code_to_occupation` poblado para funcionar bien; sin esa rama, vuelven al fallback de label que es no-determinista.
- Si más adelante decidís deprecar la rama, lo hacés con datos en mano.

### 6.4 Criterios de éxito

- `_load_occupation_embeddings()` carga correctamente los archivos.
- `code_to_occupation` poblado con 3.046 ocupaciones.
- `_semantic_match_title("título de ejemplo")` retorna lista no vacía.
- Test sobre muestra de 100 ofertas con `decision_metodo = 'semantico_unico'`: el path título-semántico contribuye con score no nulo.

### 6.5 Riesgos y rollback

- **Riesgo 1:** los archivos en `enriched/` son de SPEC E (versión enriquecida con label + L1/L2 + broader + top_3_occupations). Si el matcher en alguna parte asume esquema antiguo, puede fallar. Mitigación: revisar `_load_occupation_embeddings()` y `_semantic_match_title()` antes de habilitar.
- **Riesgo 2:** SPEC J declara `esco_code` como pivote autoritativo. Activar `code_to_occupation` puede cambiar el comportamiento del matcher para casos donde antes caía al fallback. Mitigación: comparación A/B sobre 100 ofertas antes/después del fix para confirmar que cambia para bien.
- **Rollback:** eliminar symlinks o revert del cambio de path. El sistema vuelve a operar sin la rama título-semántico (estado actual).

---

## 7. Fix C4 — Regresión de flags ESCO (DIAG A)

**Esfuerzo estimado:** 30–60 minutos para el UPDATE + 1–2 horas verificación
**Depende de:** F0, C2 (porque las 3.762 ofertas con URI vacía no son backfilleables)
**Tipo:** corrección de datos

### 7.1 Problema

1.116.011 filas en `ofertas_esco_skills_detalle` tienen `is_essential_for_occupation = 0` y `is_optional_for_occupation = 0`. El cross-check ESCO (¿esta skill pertenece al catálogo de la ocupación matcheada?) **no se está ejecutando para nadie**. Imposible filtrar en dashboard, métricas ESCO devuelven 0/0/0.

### 7.2 Root cause

Al refactorizar el matcher a v3.5.4, se eliminó la lógica de `populate_skills_detalle_v83.py:439-456` que poblaba estos flags. La función actual `match_ofertas_v3.py:save_skills_detalle()` no recibe `occupation_uri` como parámetro, así que aunque quisiera no podría consultar `esco_associations`.

### 7.3 Acción

**Backfill UPDATE masivo** (R2 §B confirmó viabilidad):
- Query JOIN única: `ofertas_esco_skills_detalle` × `ofertas_esco_matching` × `esco_associations`.
- 1.023.911 filas backfilleables (las que tienen `esco_occupation_uri` no vacío en la oferta padre — depende de C2 ejecutado primero).
- 92.100 filas no backfilleables hasta C2 (oferta sin URI).
- Estimación: 30–60 minutos con WAL activado.

**No incluir** en este SPEC el fix del código del matcher (re-incorporar el cross-check en el INSERT). Eso es F2 del SPEC U original y va a SPEC U-2 (pipeline). El backfill C4 corrige los datos hoy; el cambio de pipeline asegura que no vuelva a romperse.

### 7.4 Criterios de éxito

- Después del backfill: 1.023.911 filas con al menos un flag poblado.
- Distribución esperada (R2 §B2): 32,4% `is_essential = 1` o `is_optional = 1`, 67,6% ambos en cero (skill no en catálogo de su ocupación, legítimo).
- **F-meta — métrica de validación nueva** (criterio de éxito del SPEC U-1 entero):

```sql
-- F-meta: cobertura ESCO por oferta
WITH oferta_cobertura AS (
  SELECT 
    om.id_oferta,
    om.esco_occupation_uri,
    SUM(CASE WHEN sd.is_essential_for_occupation = 1 
             OR sd.is_optional_for_occupation = 1
             THEN 1 ELSE 0 END) AS skills_en_catalogo
  FROM ofertas_esco_matching om
  JOIN ofertas_esco_skills_detalle sd ON om.id_oferta = sd.id_oferta
  WHERE om.esco_occupation_uri != ''
  GROUP BY om.id_oferta
)
SELECT 
  AVG(CASE WHEN skills_en_catalogo >= 1 THEN 1.0 ELSE 0.0 END) * 100 AS cobertura_K1,
  AVG(CASE WHEN skills_en_catalogo >= 3 THEN 1.0 ELSE 0.0 END) * 100 AS cobertura_K3,
  AVG(CASE WHEN skills_en_catalogo >= 5 THEN 1.0 ELSE 0.0 END) * 100 AS cobertura_K5
FROM oferta_cobertura;
```

- Hoy esa query devuelve 0/0/0. **El primer valor que dé después del backfill es el baseline.** No fijar objetivo a priori.
- Registrar el baseline en `docs/diagnostico/baseline_cobertura_esco_K_post_C4.md`.

### 7.5 Riesgos y rollback

- **Riesgo 1:** UPDATE concurrente con pipeline activo puede generar locks. Mitigación: ejecutar con pipeline parado (declarar ventana de mantenimiento de 1-2 horas).
- **Riesgo 2:** los flags se poblan según `esco_associations` actual. Si el catálogo ESCO se actualiza después, los flags quedan stale. No es problema para C4 hoy, pero es razón para incluir el fix de código en SPEC U-2.
- **Rollback:** UPDATE inverso desde snapshot F0. Tabla `ofertas_esco_skills_detalle` vuelve a flags=0 en todas las filas.

---

## 8. Fix C5 — Sync automático Supabase + limpieza zombies

**Esfuerzo estimado:** 4–6 horas (cron es trivial; limpieza zombies requiere cuidado)
**Depende de:** F0, C1, C2, C4 (para que lo que se sincroniza sea correcto)
**Tipo:** corrección de infraestructura + datos

### 8.1 Problema

- No hay cron automático de `scripts/exports/sync_to_supabase.py`. Última corrida manual: 2026-04-28 (6 días atrás).
- Drift Local↔Supabase: −8.420 ofertas (esperable) y **+28.395 skills zombies en Supabase**.
- Vercel lee directo de Supabase sin caché propia → drift se refleja al usuario en tiempo real.
- 257 validaciones humanas reales viven solo en Supabase (riesgo si Supabase cae).

### 8.2 Root cause

- Sync diseñado como manual, nunca se cronizó.
- El re-sync de skills hace `delete + insert` solo de las ofertas del sync actual. Las skills de ofertas borradas localmente quedan zombies en Supabase. **Bug de gobierno de datos.**

### 8.3 Acción

**Cron de sync:**
- Configurar cron diario de `sync_to_supabase.py` (ej: 03:00 AR para no chocar con scraping de 08:00).
- Logs estructurados a `logs/sync_supabase_YYYYMMDD.log`.
- Notificación si la corrida falla.

**Limpieza de zombies en Supabase:**
- Antes de la primera corrida del cron post-fixes, ejecutar query de purga:
  ```sql
  DELETE FROM ofertas_skills 
  WHERE id_oferta NOT IN (SELECT id_oferta FROM ofertas_dashboard);
  ```
- Esto elimina las 28.395 skills zombies (skills cuyo padre ya no existe en `ofertas_dashboard`).
- **Verificación post-purga:** count `ofertas_skills` Supabase debe coincidir con `ofertas_esco_skills_detalle` local filtrando por las ofertas validadas (las que sincroniza el script).

**Fix del re-sync para que purgue al sincronizar:**
- Modificar `sync_to_supabase.py` para que el delete cubra todas las skills cuyas ofertas no están en el sync actual (no solo las que están).
- Añadir test de regresión: si una oferta se borra localmente, sus skills se borran en Supabase en la siguiente corrida del cron.

### 8.4 Criterios de éxito

- Cron corriendo diariamente, logs sin errores.
- Diff Local↔Supabase de `ofertas_skills` (cuando se filtra por ofertas validadas): 0.
- Las 257 validaciones humanas siguen disponibles en Supabase (no afectadas por la limpieza).
- Canario de zombies muestra 0 después de la purga.

### 8.5 Riesgos y rollback

- **Riesgo 1:** la query de purga puede borrar skills que sí son válidas si el filtro es incorrecto. Mitigación: ejecutar primero con `SELECT COUNT(*)` en lugar de `DELETE`, comparar contra el conteo esperado de zombies (28.395). Si difiere mucho, abortar.
- **Riesgo 2:** cambio en lógica de re-sync puede borrar más de la cuenta. Mitigación: test en BD de staging antes de aplicar a producción.
- **Riesgo 3:** la 257 de validaciones humanas pueden perderse si el cron falla durante la primera corrida y la limpieza ya se ejecutó. Mitigación: snapshot completo de Supabase antes de la purga (extensión de F0).
- **Rollback:** restaurar Supabase desde snapshot F0. Cron se desactiva.

---

## 9. Métrica F-meta como criterio de éxito del SPEC entero

**Esfuerzo estimado:** ya incluido en C4 (la query es la misma).

### 9.1 Definición

`cobertura_esco_K1`, `cobertura_esco_K3`, `cobertura_esco_K5` (ver query en §7.4).

### 9.2 Mediciones esperadas en este SPEC

- **Antes de F0:** 0/0/0 (DIAG A activo, flags todos en cero).
- **Después de C4:** baseline real. Registrar.
- **Después de C5:** mismo baseline si el sync funcionó correctamente.
- **Aplicar como canario permanente** (correr diaria) → hereda al SPEC U-3 (D7).

### 9.3 Cuándo F-meta valida cada fix

- C4 exitoso: K1, K3, K5 > 0 (cualquier valor distinto de cero confirma que el backfill se aplicó).
- C5 exitoso: K1, K3, K5 medidos desde Supabase coinciden con los medidos desde local (drift = 0).

### 9.4 Lo que F-meta no valida

- Calidad del matching de ocupaciones (eso necesita Gold Set ampliado, fuera de alcance).
- Calidad de la extracción de skills (eso es F8 / SPEC U-2 sobre el extractor).
- Anti-alucinación NLP (SPEC U-2).

---

## 10. Orden de ejecución

```
F0 (snapshot + canarios)
 │
 ▼
C3 (embeddings ocupaciones — restaurar path)  ← bloquea C1 y C2
 │
 ▼
C2 (fix diccionario — código + JSON + reprocesamiento)  ← bloquea C4 (backfill)
 │
 ▼
C1 (re-rematch para corregir drift URI×label)
 │
 ▼
C4 (backfill flags ESCO)
 │   └─ medir F-meta baseline aquí
 ▼
C5 (cron sync + limpieza zombies Supabase)
 │   └─ medir F-meta desde Supabase y comparar
 ▼
SPEC U-1 cerrado.
```

**Ventana de ejecución sugerida:** 2-3 días con pipeline pausado durante C2 y C4 (que son los más invasivos). C5 puede correr con pipeline activo.

**Comunicación a stakeholders:** Cynthia y Diego deben saber que el dashboard puede mostrar valores cambiantes durante 2-3 días por desvalidación + re-validación de 8.210 ofertas (C1).

---

## 11. Lo que NO está en este SPEC

Para que quede claro y los stakeholders no tengan expectativas erradas:

- **Anti-alucinación NLP** (`semisenior` 49%, tareas alucinadas 6,5%) → SPEC U-2.
- **ZonaJobs paginación, ComputRabajo regresión** → SPEC U-2.
- **Tablas zombies locales (12), `issues` con 99,4% ruido, `id_oferta` TEXT vs INTEGER** → SPEC U-3.
- **Versionado del matcher (5 lugares), canarios estructurales, LoRA** → SPEC U-3.
- **Re-incorporar el cross-check ESCO en el pipeline futuro** (F2 del SPEC U original) → SPEC U-2 (porque es cambio de código, no de datos).
- **Gold Set expandido** → fuera de los 3 SPECs, es un proyecto en sí mismo.
- **VPS embed-server** → issue separado, decisión operativa tuya.

---

## 12. Dependencias hacia adelante

Una vez cerrado SPEC U-1:

- **SPEC U-2** puede empezar inmediatamente: anti-alucinación, fix de scrapers, re-incorporar cross-check en pipeline.
- **SPEC U-3** puede empezar en paralelo con U-2: limpieza de zombies, normalización de schema, observabilidad.
- **OE matching persona→oferta** (chat anterior) puede arrancar diseño una vez U-1 esté cerrado, porque depende de URIs correctas y flags poblados.

---

## 13. Decisiones que requieren cierre antes de implementar

Antes de pasar este SPEC a Claude Code para implementación:

1. **Confirmar Opción A en C3** (restaurar la rama título-semántico) o decidir Opción B.
2. **Cerrar las 5 decisiones manuales sobre `isco_familia`** en C2 (qué URI específica para `gerente`, `analista`, `operario`, `operador`, `tecnico`).
3. **Confirmar ventana de mantenimiento** de 2-3 días para ejecutar el SPEC.
4. **Comunicar a Cynthia y Diego** la desvalidación temporal de 8.210 ofertas durante C1.

Estas 4 decisiones son tuyas. Sin cerrarlas, el SPEC no se ejecuta.

---

**Fin del SPEC U-1.**
