# docs(spec-s1c-f07): discovery del lenguaje de Cyn — categorías validadas + split

Discovery **read-only** del texto libre de Cyn (818 fragmentos literales / **309 ofertas**:
811 issues del ledger + 7 notas delta de Supabase). Primer paso de la Fase 2 del master y
habilitante del cierre del loop de Cyn (Eje 2). F0.6 probó que el loop está roto ((b)=0);
este spec **lee y ordena lo que Cyn escribe** para entender por qué vías deben volver sus
correcciones — sin cerrar el loop, sin generar nada.

## Reencuadre que rige el spec

**"Cerrar el loop" NO es "convertir cada corrección en una regla."** F0.6 mostró que las
reglas son la mayor fuente de error; fabricar una regla por corrección empeoraría el problema.
Las correcciones vuelven por **vías distintas según su tipo**, y para eso primero hay que saber
qué tipos existen. Las categorías **salieron de leer a Cyn** (Fase 1) y **las validó Cyn/Gerardo**
(Fase 2) — no se impusieron.

## Hallazgo de forma

Cyn no escribe una corrección por dimensión: escribe **revisiones estructuradas
multi-dimensionales** con un vocabulario de marcado propio (`❌ Incorrecto`, `✔ Explícita`,
`⚠ Implícita`, `DENOMINACION — Argentina: … / España: …`, `Ubicación sugerida dentro del Excel:
ESCO XXXX`). **267 de 309 ofertas son multi-categoría** (moda = 6 categorías por oferta); solo
37 puras. **Una corrección alimenta varias vías a la vez** — manda en el diseño del loop.

## Las 11 categorías validadas + presencia (no exclusiva)

| categoría | ofertas | vía de vuelta | Eje |
|---|---:|---|---|
| **G3** denominación argentina ↔ España/ESCO | **229** | perfil / vocabulario (el activo) | 3 |
| **G6** skills faltantes/validadas | 237 | registro de emergentes / perfil | 3 |
| **G4** atributos del aviso (sector/área/exp…) | 225 | corrección NLP | 3/NLP |
| **G2** target ESCO/ISCO | 200 | dato de apoyo del training pair | 2 |
| **G1** ocupación mal | 161 | training pair; si bug de regla → corregir regla | 2/4 |
| **G5** skills ruido | 122 | señal negativa para el extractor | 3/NLP |
| **G9** confirma correcto | 49 | positivos para el harness (ground truth) | medición |
| **G7a** tareas no extraídas | 20 | corrección NLP (extracción) | 3/NLP |
| **G7b** tareas sin verbo / mal normalizadas | 14 | normalización lista→verbo, sin inventar (regla de Cyn) | 3/NLP |
| **G8** multi-ocupación | 3 | desagregar en subofertas (NO reclasificar) | 2 |
| **AMB** dudas | 4 | estado "pendiente de revisión" (no existe hoy) | 2 |

Refinamientos de Cyn incorporados: **G1≠G3 separados**, **G7→G7a/G7b**, **G8** = desagregar,
**AMB** = pedido de funcionalidad de estado. El mapeo categoría→vía se confirma; único matiz:
**G2 casi nunca es autónomo** (14/200 puras) → es atributo, no categoría.

## Dimensión del activo

- **Lectura del aviso / NLP** (G4+G5+G6+G7): **259 (84%)**
- **Vocabulario argentino** (G3): **229 (74%)**
- Ocupación (G1): 161 (52%) · Confirmaciones (G9): 49 (16%) · Multi-ocup (G8): 3 · Dudas: 4

Los dos frentes mayores son **Eje 3/NLP**, no reglas — coherente con el reencuadre.

## Train/test split (fijado, NO usado)

- Estratificado por categoría primaria, `seed=42`, test=30%.
- **TRAIN 216 / TEST 93.** Balance por presencia: cada categoría sustancial **27–32%** en test.
- El TEST queda **reservado**: nunca se usa para generar nada; mide si el loop funcionó. Va
  desde el día uno para no contaminar la medición. **No se usa en este spec.**

## Naturaleza y reglas

Read-only absoluto: leer, clasificar, mapear, preparar el split. **No cierra el loop, no genera
reglas/vocabulario/training, no toca código/datos/config.** Solo escribe el spec + 3 artefactos
fechados en `tests/harness/`. No se tocó `config/training_pairs.json` ni
`metrics/gold_set_history.json`. **No mergear — el merge es de Gerardo.**

## Artefactos

```
docs/specs/SPEC_S1C_F07_LENGUAJE_CYN.md                     spec (Fase 1 + Fase 2)
tests/harness/lenguaje_cyn_extraccion_2026-06-18.json       818 fragmentos literales + marcadores
tests/harness/lenguaje_cyn_clasificacion_2026-06-18.json    309 ofertas × 11 categorías + pureza + dimensión
tests/harness/lenguaje_cyn_split_2026-06-18.json            train(216)/test(93) estratificado
```

🤖 Generated with [Claude Code](https://claude.com/claude-code)
