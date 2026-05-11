# Conteos 7 — Bug del path "semántico" con `esco_occupation_uri = ''`

**Fecha:** 2026-05-04
**Pipeline activo:** No (no hay procesos `process_nlp_*` ni `match_ofertas` corriendo; `/tmp/pipeline.log` no existe).
**Modo:** READ-ONLY estricto. SQLite `?mode=ro`. Sin escrituras a BD/Supabase, sin tocar código ni configs.
**Tiempo total:** ~50 min.
**Output ubicación:** este archivo. `/mnt/user-data/outputs/` no escribible (Permission denied — bloqueo conocido).

---

## TL;DR

**El SPEC U-1 §5 (C2) tenía razón en la causa raíz.** El bug está en el path del diccionario argentino que no setea `esco_occupation_uri`. La corrección que hice durante la revisión de factibilidad (PROMPT 6 follow-up) era **incorrecta**: confundí `decision_metodo` con `occupation_match_method`. El filtro correcto para identificar las afectadas es `occupation_match_method LIKE 'diccionario_argentino%'`, no `decision_metodo='semantico_unico'`.

- **Ofertas afectadas reales: 3.758** (no 3.753 ni 9). 100% vienen del diccionario argentino.
- **El campo `decision_metodo='semantico_unico'`** simplemente significa "ganó la rama no-regla del dual matching". Tanto el diccionario como el cosine real reportan `semantico_unico`. El path real se distingue en `occupation_match_method`.
- **C3 (restaurar embeddings de ocupaciones) NO arregla este bug.** Las 3.758 nunca pasan por `_semantic_match_title()` porque el diccionario corta antes.

---

## A — Caracterización de las afectadas

### A1. Distribución por `occupation_match_method` (filtro `decision_metodo='semantico_unico' AND uri=''`)

```
diccionario_argentino_administrativo            2155
diccionario_argentino_vendedor                   492
diccionario_argentino_analista                   354
diccionario_argentino_gerente                    302
diccionario_argentino_operario                   156
diccionario_argentino_operador                   144
diccionario_argentino_tecnico                    104
diccionario_argentino_repositor                   22
diccionario_argentino_recepcionista                7
diccionario_argentino_martillero                   6
diccionario_argentino_capataz                      5
diccionario_argentino_albañil                      4
diccionario_argentino_operador_de_atencion         1
diccionario_argentino_administrativo_contable      1
                                          ─────────
Total                                           3753
```

**100% del set viene del diccionario argentino**, sin excepciones. No hay un solo caso con URI vacía + `decision_metodo='semantico_unico'` que NO venga del diccionario.

### A2. Por `matching_version`

```
3.5.2              3745
spec_h_rematch        8
```

Los 8 de `spec_h_rematch` se procesaron el 2026-04-25 entre 15:58 y 16:25 — dentro de la ventana del bug `94f0d73c` → `7aeb16a3` (SPEC H). Son arrastre histórico del rematch buggy. Los otros 3.745 son del matcher principal v3.5.2.

### A3. ¿Tienen `esco_occupation_label`?

| | count |
|---|---|
| Label vacío + URI vacía | 0 |
| **Label SÍ + URI vacía** | **3.753** |

Todas tienen label persistido. Sample:

```
isco=9333 | label='estibador/estibadora'                                | match_score=0.9
isco=4110 | label='empleado de oficina/empleada de oficina'             | match_score=0.9
isco=9333 | label='operador de carretilla elevadora/operadora ...'      | match_score=0.9
isco=8160 | label='hornero de panadería/hornera de panadería'           | match_score=0.9
isco=5223 | label='vendedor/vendedora'                                  | match_score=0.9
isco=2423 | label='consultor de selección de personal/...'              | match_score=0.9
```

**Score uniforme 0.9** — coincide con el hardcoded del diccionario (`match_ofertas_v3.py:312`).

### A4. ¿Tienen `isco_code`?

| | count |
|---|---|
| `isco_code` poblado | 3.753 |
| `isco_code` vacío | 0 |

Todas con ISCO. Solo falta la URI ESCO específica.

### A5. Distribución temporal

- Min: 2026-02-04 18:46
- Max: 2026-04-30 10:48

Distribución mensual:

```
2026-02   1248
2026-03    680
2026-04   1825
```

**No es un evento concentrado** — es continuo desde febrero. Confirma que el bug **no es regresión del SPEC H**: existe desde antes. SPEC H (24-25/04) solo agregó 8 casos más. La causa raíz es estructural en el path del diccionario, vigente desde v3.5.x.

---

## B — Búsqueda en código

### B1. Apariciones del literal `'semantico_unico'`

Una sola escritura en producción:

```
database/match_ofertas_v3.py:1136
    return (semantic_isco, "semantico_unico", "sin regla aplicable")
```

Las demás referencias son del path SPEC H y consultas SQL para análisis (`scripts/embeddings/rematch_isco_spec_h.py`, `unlock_spec_h.py`, `analyze_spec_h_impact.py`). Ninguna escritura adicional.

`decision_metodo='semantico_unico'` se setea **solamente** en `_decide_dual_match()` cuando `regla_isco is None and semantic_isco is not None` (línea 1132-1136).

### B2. Flujo desde `_match_by_argentino_dict` hasta la persistencia

**Función `_match_by_argentino_dict` — líneas 241-316.** El return de la rama exitosa (líneas 308-314):

```python
return {
    "isco_code": isco,
    "esco_label": esco_label,
    "score": 0.90,
    "metodo": f"diccionario_argentino_{termino.replace(' ', '_')}",
    "termino_matched": termino
}
```

**No incluye `esco_uri`.** Esta es la primera omisión.

**Llamada desde `match()` — líneas 575-594:**

```python
# 2a: Intentar match por diccionario argentino
dict_match = self._match_by_argentino_dict(oferta_nlp)

# Variables para resultado semántico
semantic_isco = None
semantic_score = 0.0
semantic_label = ""
semantic_metodo = ""
semantic_uri = ""                          ← inicialización por default
semantic_skills_matched = []

if dict_match:
    # Diccionario argentino matcheó
    semantic_isco = dict_match["isco_code"]
    semantic_label = dict_match["esco_label"]
    semantic_score = dict_match["score"]
    semantic_metodo = dict_match["metodo"]
    # ← semantic_uri NUNCA se setea cuando dict_match es truthy
```

**`semantic_uri` queda en `""`** porque la rama `if dict_match:` no la asigna. La rama `else:` (línea 595+, semántico real con embeddings) sí lo hace en la línea 648:

```python
semantic_uri = best.get("occupation_uri", "")
```

### B3. Punto de persistencia

**Función `save_matching_result()` — líneas 1404-1517 (`match_ofertas_v3.py`).**
- INSERT OR REPLACE de las 26 columnas (incluyendo `esco_occupation_uri`).
- Línea 1462: `result.esco_uri` se persiste como segundo campo.
- `result.esco_uri` viene del `MatchResult` construido en línea 782-784:

```python
return MatchResult(
    status=status,
    esco_uri=semantic_uri,      ← cuando dict_match ganó, semantic_uri=""
    esco_label=semantic_label,
    ...
)
```

**No es un bug de la persistencia. Es un bug del setter intermedio**: el path del diccionario nunca puebla `semantic_uri`.

### B4. Comparación con el fix SPEC H (commit `7aeb16a3`)

El fix de SPEC H corrigió un bug **distinto**: en `rematch_isco_spec_h.py:persist_matching_result()`, el UPDATE escribía 9 columnas y dejaba 10 stale. Ese fix replicó la lista completa al UPDATE de spec_h.

**El fix de SPEC H no toca el matcher principal.** El bug del diccionario en `match_ofertas_v3.py:577-594` quedó intacto. Confirma que son dos bugs independientes:

- Bug SPEC H (94f0d73c): UPDATE incompleto → 4.203 ofertas con drift URI×label.
- **Bug del diccionario (estructural):** setter omite URI → 3.753 ofertas con URI vacía.

El SPEC U-1 §4 (C1) cubre el primero. El SPEC U-1 §5 (C2) cubre el segundo.

---

## C — Hipótesis

### C1. Hipótesis 1 — Bug del setter en path diccionario (CONFIRMADA)

**Línea exacta del bug:** `match_ofertas_v3.py:587-594`. La asignación de `semantic_uri` está ausente en la rama `if dict_match:`.

Adicional: `_match_by_argentino_dict()` líneas 308-314 no incluye URI en el dict retornado, por lo que aunque la rama `if` quisiera leerla del dict, no estaría disponible.

**Verificación cuantitativa:**

```
Filas con match_method LIKE 'diccionario_argentino%':
  Con URI poblada:    0      ← determinístico al 100%
  Con URI vacía:  3.758
```

Cero falsos positivos, cero falsos negativos. Es la causa raíz.

### C2. Hipótesis 2 — Embeddings de ocupaciones apagados (C3) — DESCARTADA

`_semantic_match_title()` (línea 1286-1312) sí depende de `self.occ_embeddings` y retorna `[]` si está en `None`. Pero **las 3.758 con URI vacía no pasan por esta función**: el path del diccionario (rama `if dict_match:`) corta el flujo antes de llegar a `_semantic_match_title()` y `_combine_candidates()`.

Verificación: filas con `match_method = 'semantic_fallback_v3'` (que sí dependen de `_semantic_match_title()`) tienen URI poblada en **el 100% de los casos** (1.094 / 1.094). Si C3 estuviera causando URIs vacías por esa rama, esas 1.094 también tendrían el problema.

**C3 es ortogonal al bug de las 3.758.**

### C3. Hipótesis 3 — Asignación condicional con bug

Aplica a la Hipótesis 1. La condición rota es implícita: dentro de `if dict_match:` no hay asignación de `semantic_uri`. No es un `if score >= threshold` mal puesto — es directamente una omisión.

### C4. ¿Características comunes de las 3.753?

- **Score uniforme 0.9** (hardcoded del diccionario).
- **Match method: 14 variantes** todas `diccionario_argentino_*`.
- **Distribución temporal:** continua desde 2026-02-04. No es regresión.
- **ISCO concentrados:** ISCO 4110 (administrativo, 2.155 ≈ 57%), seguido de 5223, 2423, 9333, 8160 (todos comunes en mercado AR).
- **Sample muestra:** todas ofertas reales con título/descripción que matchea por keywords del diccionario.

---

## D — Impacto del fix C3 sobre las 3.758

### D1. Path del diccionario vs path semántico

`if dict_match:` (línea 587) es **excluyente**. Si el diccionario matchea, **nunca** se ejecuta `_semantic_match_title()`, `_combine_candidates()`, ni se accede a `code_to_occupation`.

Restaurar los embeddings de ocupaciones (C3) no afecta a las 3.758: ya tomaron el camino del diccionario antes de que esas funciones se invoquen.

### D2. Test conceptual sobre 1 oferta del set

Tomemos `id_oferta=2171915`:
- `isco_code` persistido: `4110`
- `esco_occupation_label`: `"empleado de oficina/empleada de oficina"`
- `match_method`: `diccionario_argentino_administrativo`
- `esco_occupation_uri`: `""`

El label "empleado de oficina/empleada de oficina" es la URI canónica `http://data.europa.eu/esco/occupation/...` que está disponible en `esco_occupations` SQL local. La info para reconstruir la URI **existe**: lookup directo `WHERE preferred_label_es = ?`.

El SPEC C2 propone exactamente esto: agregar `esco_uri` o `esco_code` a las entradas del JSON, y en runtime resolver vía `code_to_occupation` (que requiere C3) **o** por SQL lookup de label (que no requiere C3).

**Implicación:** C2 puede implementarse de dos formas:
- (a) Agregar URIs al JSON + resolver en runtime usando `code_to_occupation` → **depende de C3**.
- (b) Agregar URIs al JSON directamente, hardcoded → **no depende de C3**.
- (c) En el setter, después de poblar `semantic_label`, hacer SQL lookup `SELECT occupation_uri FROM esco_occupations WHERE preferred_label_es = ?` → **no depende de C3**.

El SPEC §5.3 sugiere la mezcla a/c con `_resolve_rule_target()` y `code_to_occupation`. Pero la solución mínima viable es (b) o (c), que no requiere C3.

### D3. Estimación

| Hipótesis | Cobertura sobre las 3.758 |
|---|---|
| (a) C3 (embeddings apagados) — bug cascada | **0%** |
| (b) Bug independiente del setter en path diccionario | **100%** |
| (c) Mix | n/a |
| (d) No estimable sin ejecutar | n/a |

**100% de las 3.758 son explicables por (b)** — bug del setter del diccionario, independiente de C3.

---

## E — Hallazgos colaterales

### E1. Las 5 entradas de `isco_familia` también propagan el bug

De las 14 variantes de `diccionario_argentino_*` con URI vacía, 6 corresponden a entradas con `isco_familia` (delegan al semántico solo si ningún contexto matchea):

| Entrada | URI vacía resultantes |
|---|---|
| `gerente` | 302 |
| `analista` | 354 |
| `operario` | 156 |
| `operador` | 144 |
| `tecnico` | 104 |

Total: **1.060 ofertas** vienen de las 5 entradas con `isco_familia`. Pero **el contexto SÍ matcheó** en estas (sino habrían delegado al semántico vía `continue` en línea 304). El problema no es el `isco_familia`, es el setter común de la línea 311-314 que aplica para todas las entradas del diccionario.

**Implicación para la decisión #2 del SPEC §13** (las 5 URIs específicas para `isco_familia`):

Mi sugerencia previa de "delegar al semántico arreglado" era inadecuada. Estas 1.060 sí matchearon por contexto. Las 5 entradas tienen contextos que resuelven a ISCO específicos (no al `isco_familia` genérico). Hay que agregar URIs específicas en cada contexto del JSON, no en la entrada raíz.

Ejemplo: `gerente` con contexto `ventas|comercial` → ISCO 1221 → URI específica de "director de ventas".

### E2. Score 0.9 hardcoded enmascara el problema en métricas

El SPEC H scope (`decision_metodo='semantico_unico' AND estado_validacion='validado'`) procesó algunas de estas ofertas con score uniforme 0.9. La métrica de "score promedio" no detecta el bug: 0.9 parece sano. Solo la cardinalidad de URIs vacías lo expone.

### E3. Adopción del fix tiene efecto en cascada sobre C4

Las 3.758 ofertas con URI vacía implican aproximadamente **N filas en `ofertas_esco_skills_detalle`** que NO son backfilleables por C4 (no tienen URI padre). Cuántas exactamente:

```
SELECT COUNT(*) FROM ofertas_esco_skills_detalle sd
JOIN ofertas_esco_matching m ON sd.id_oferta = m.id_oferta
WHERE m.esco_occupation_uri = '' OR m.esco_occupation_uri IS NULL
```

= **92.100** filas (coincide con el número del SPEC §7.3 "filas no backfilleables hasta C2"). El SPEC ya lo contabilizó correctamente.

**Si C2 se ejecuta antes de C4, el universo backfilleable de C4 sube de 1.023.911 a 1.116.011 (=100%).**

### E4. La confusión de mi reporte de factibilidad

El reporte de factibilidad (revisión del SPEC U-1) afirmó: "99,7% de URIs vacías son del path semántico, no del diccionario". **Es incorrecto.** El campo `decision_metodo='semantico_unico'` no equivale al path semántico. Es una etiqueta del dual-match que se asigna a cualquier match no-regla, incluyendo el diccionario.

El campo correcto para identificar el path real es `occupation_match_method`. Cuando se filtra por `match_method LIKE 'diccionario_argentino%'`: **3.758 con URI vacía, 0 con URI poblada**. El SPEC C2 era correcto al señalar el path del diccionario como causa raíz.

### E5. Pendientes para diagnóstico 8 (si se requieren)

- Verificar si los 14 valores de `match_method` de variantes diccionario corresponden 1:1 a las entradas del JSON `sinonimos_argentinos_esco.json` (debería haber 24 entradas — algunas no aparecen porque ningún título las matcheó aún).
- Investigar por qué hay 5 ofertas con `match_method='diccionario_*'` Y `decision_metodo` distinto a `semantico_unico` (`dual_coinciden`, `semantico_alta_confianza`, `regla_por_score_bajo`). El flujo en línea 587-594 setea diccionario, pero después puede ser overrideado por una regla evaluada en `_evaluate_rule_only()` (paso 3, línea 657). Esos 5 casos no son el bug central pero son ruido en la auditoría.

---

## Resumen ejecutivo

- **Causa raíz identificada:** `match_ofertas_v3.py:587-594` (rama `if dict_match:`). La rama no setea `semantic_uri`, y `_match_by_argentino_dict()` (líneas 308-314) no devuelve URI. Quedan ambas sin asignación, persisten `""`.
- **Hipótesis dominante:** Hipótesis 1 — Bug del setter en path diccionario.
- **Estimación impacto C3 sobre las 3.758:** 0%. C3 no arregla este bug. El fix necesario es independiente y vive en el path del diccionario.
- **El SPEC U-1 §5 (C2) tiene la causa raíz correcta.** Mi corrección durante la revisión de factibilidad confundió `decision_metodo` con `match_method`. Ignorar esa corrección — el SPEC C2 estaba bien diagnosticado.
- **Cantidad real de afectadas:** 3.758 (no 3.762 ni 3.753 ni 9). El SPEC dice 3.762; la diferencia (4 ofertas) son casos con `decision_metodo='error'`/`regla_manual_fix`/etc. que no vienen del diccionario y son problemas distintos de bajo volumen.

### Decisiones que requieren cierre antes de reescribir SPEC C2

1. **No reescribir el alcance de C2** — el SPEC original era correcto. Las 3.758 son del diccionario.
2. **Para las 5 entradas con `isco_familia`** (`gerente`, `analista`, `operario`, `operador`, `tecnico`): cuando el contexto matchea, el ISCO específico ya está resuelto. **Agregar `esco_uri` a cada contexto del JSON**, no a la entrada raíz. La entrada raíz solo aplica si ningún contexto matchea, en cuyo caso delega al semántico (caso ya manejado por `continue` línea 304).
3. **Estrategia de fix preferible (mi recomendación):**
   - Fix mínimo: agregar `esco_uri` directo al JSON (24 entradas y N contextos), modificar setter línea 311-314 para incluirlo, y en línea 587-594 leer `semantic_uri = dict_match.get("esco_uri", "")`.
   - **No depende de C3.** Permite ejecutar C2 sin C3 si se decide diferir C3.
   - Reprocesamiento de las 3.758 con matcher arreglado.
4. **Clarificar en el SPEC reescrito** que `occupation_match_method` (no `decision_metodo`) es el filtro autoritativo para identificar el path semántico real. Esto evita confusión futura.

---

**Fin del reporte 7.**
