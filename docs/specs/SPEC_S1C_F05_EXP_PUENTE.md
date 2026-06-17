# SPEC S1C-F0.5-exp — Experimento puente, corrida 1 (esco_argentino)

**Estado:** chequeo de cobertura hecho · A↔B pendiente de OK de Gerardo
**Fecha:** 2026-06-17
**Branch:** `spec/s1c-f05-exp-puente`
**Baseline (cero congelado):** `tests/harness/baseline_2026-06-17.json`

---

## 1. Propósito

Primer **uso** del harness construido en F0.5-build. Mide si inyectar las aristas
argentinas curadas (`esco_argentino`) a la **decisión de ocupación** mueve la
precisión del matcher, contra el baseline fechado.

Es **medición read-only, NO intervención.** Monkeypatch en memoria (mismo patrón
que `exp_raiz_skills/` y la capa runner de F0.5-build). No toca
`match_ofertas_v3.py` productivo, no persiste, no cambia el pipeline. Calibra si
el refactor del matcher (Eje 3) vale la pena; **no lo hace**. El refactor real,
si el número lo justifica, es trabajo posterior y aparte.

## 2. Alcance — corrida 1 = solo `esco_argentino`

- **Config A** = baseline (matcher actual), ya fechado en F0.5-build. No se recalcula.
- **Config B** = baseline + overlay `esco_argentino` (44 ocupaciones / 291 skills,
  curaduría humana validada por Cyn — máxima confianza) inyectado al grafo
  skills→ocupación.

**Separación metodológica de los 3.292 pares B_FUERTE:** NO se mezclan en esta
corrida. Viven solo en el sandbox del harness (`exp_raiz_skills/`), no cruzaron al
repo, y son otra clase de evidencia (señal estadística sin validar humanamente).
Van a una **corrida 2 posterior**, para no confundir "mejoró por curaduría
confiable" con "mejoró por señal cruda". La corrida 2 queda pendiente del export
del harness.

## 3. Mecanismo de inyección (config B)

Hoy `esco_argentino` se usa **solo como re-rank post-match**: `MatcherV3.match()`
decide la ocupación y *después* llama `rerank_with_argentino_boost()` para subir
+0.05·(freq/max_freq) el score de las skills que están en el perfil de esa
ocupación (`database/skills_implicit_extractor.py:1267`). No afecta qué ocupación
se elige — solo reordena skills de una ocupación ya decidida.

El experimento mueve esa señal **un paso antes**: inyecta las aristas
skill→ocupación de `esco_argentino` al canal que decide la ocupación (vía
monkeypatch en memoria de `extract_skills_dual` / el grafo de candidatos), para
medir si la decisión de ocupación cambia. Nunca se edita el matcher productivo.

## 4. Chequeo de cobertura (2026-06-17) — read-only

`esco_argentino`: **44 ocupaciones / 291 skills**, 44 ESCO-URI únicos, 39 ISCO-4 distintos.
Cruce contra los 113 casos del snapshot `tests/harness/gold_set_snapshot_2026-06-17.json`.

### A nivel ESCO-URI (exacto — lo que el overlay realmente keyea)

| Población | true | false | total |
|---|---:|---:|---:|
| Esperado en las 44 | 27 | 4 | 31 |
| Match-A en las 44 | 31 | 3 | 34 |
| **Afectables** (esperado **o** match-A en 44) | 31 | 5 | **36** |

### El subconjunto que mide GANANCIA (los 15 `false`)

- **4** de los 15 `false` tienen su esperado-ESCO **resuelto y dentro de las 44**
  → único lugar donde se puede medir *ganancia hacia lo correcto de Cyn* a ESCO granular.
- **5** `false` afectables en total (1 más, "Gerente de ventas" 1117984105, con
  esperado-ESCO sin resolver → medible solo a ISCO-4).
- Los **31 `true` afectables son solo monitores de regresión**: su target implícito
  *es* la salida A actual, así que **no pueden ganar**, solo empeorar (bien→mal).

### A nivel ISCO-4 (más laxo — sobreestima)

Esperado en ISCO-4 cubiertos: 52 (true 45 / false 7). Match-A: 55. El overlay
keyea por URI exacto, no por ISCO-4, así que la cobertura ISCO-4 **sobreestima** lo
afectable; el número honesto es el de ESCO-URI.

## 5. Interpretación que habilita la cobertura

Dos lecturas, ambas verdaderas, que NO hay que confundir:

1. **Mecanismo + regresión: cobertura fuerte (36 afectables, 31 monitores de
   regresión).** La corrida responde con solidez "¿la inyección hace *algo* /
   causa daño?".
2. **Veredicto de ganancia: débil (solo 4 `false` medibles a ESCO granular,
   ≤ 5).** Por el umbral del prompt (~15-20 = veredicto; ≤ 5 = prueba de
   plomería), la corrida 1 **NO es veredicto sobre si las aristas corrigen los
   errores reales de Cyn** — es prueba de que el mecanismo de inyección funciona y
   no rompe.

El reporte final debe declarar esto explícitamente: un "no movió la aguja" en los
4 `false` significaría "casi no había casos donde mover", **NO** "las aristas no
sirven".

## 6. Plan de corrida A vs B (tras OK de Gerardo)

1. Config A: reusar `baseline_2026-06-17.json` (no recalcular).
2. Config B: matcher en memoria + overlay vía monkeypatch, 113 casos read-only.
   Red de seguridad de F0.5-build activa (RuntimeError si cambian conteos de producción).
3. Matriz de transición a doble nivel (ISCO-4 + ESCO granular): `mal→bien`,
   `bien→mal`, `bien→bien`, `mal→mal`. Todas las regresiones listadas caso por caso.
   Número de decisión = ganancia − regresión.
4. Desglose por método de las que cambiaron (regla / semántico / diccionario).
5. Resultado fechado en `tests/harness/exp_puente_esco_argentino_2026-06-17.json` +
   resumen legible. No se toca el baseline ni el snapshot.

## 7. Reglas

Read-only sobre producción (nunca `match_and_persist`, nunca escritura). No se
toca el baseline ni el snapshot de F0.5-build (cero congelado). No se incluyen los
3.292 pares B_FUERTE. No mergear — el merge es de Gerardo. Punto de control
obligatorio tras el chequeo de cobertura: no se corre A vs B sin OK sobre la
interpretación.
