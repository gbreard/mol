# [CASCADA v12.4] Ampliación del universo P1 — backlog sin-NLP (2026-10-06)

El censo P0 tomó solo las ofertas **con NLP v11** (98.709 filas → 98.168 primarias procesables).
El panel de scraping mostró **31.036 pendientes de NLP** (acumulado desde la pausa de la
semanal, 25/08) que P0 dejó fuera porque **no tienen fila en `ofertas_nlp`**. Corrección:

## Censo de las pendientes (31.577 ofertas sin fila NLP)
`ofertas` total = 129.745 · con NLP = 98.709 · **sin NLP = 31.577**. Split por el predicado
REAL del extractor (N1 `limpiar_chrome` + guard `parece_solo_titulo`):

| | Conteo | Trato |
|---|---|---|
| **Procesable** (N1 deja cuerpo) | **18.730** | **entra al universo** (primera-extracción v12.4) |
| Inerte (N1 vacío / solo-título) | 12.847 | NO re-extrae (sin cuerpo; CT chrome-only / título-only) |

Procesables por portal: computrabajo 10.054 · zonajobs 3.518 · bumeran 3.335 · indeed 1.734 · portalempleo 74 · caba 15. (El grueso es ComputRabajo — el backlog de la semanal.)

## Universo P1 corregido

| Capa | Conteo | primera_extraccion | Cola |
|---|---|---|---|
| Re-extracciones (con v11) | 98.168 | 0 | **primero** (el shadow P3 las necesita) |
| **Primeras-extracciones (sin v11)** | **18.730** | 1 | después de las 98K |
| **TOTAL procesable v12.4** | **~116.898** | — | una sola época para todo el corpus |

Las primeras-extracciones van al **mismo staging** (`cascada_staging.db`), con
`primera_extraccion=1`, y **entran al mismo swap P3 y al re-matching P4** — una sola época de
tareas v12.4 para todo el corpus. El runner (`reextraccion_tareas_v124.py`) hace UNION de las
dos ramas ordenando `primera ASC, fecha DESC` → agota re-extracciones y recién ahí toma primeras.

## Reproyección del reloj
Hecho ~5.700. Restante ~111.200. Throughput honesto observado **285–602 of/h** (oscila con la
riqueza del aviso; sin contención local medida):

| Ritmo | Restante ~111.200 |
|---|---|
| 285 of/h (tramos ricos) | ~16 días |
| ~450 of/h (mezcla) | ~10 días |
| 602 of/h (tramos livianos) | ~7,7 días |

**Lectura honesta: ~10–16 días** para el universo ampliado. Las primeras-extracciones son
mayormente CT (cuerpos cortos tras N1) → tienden a ser más rápidas, pero no vendo el optimista.
Reporte por tanda/día. Punto de control P1-total sin cambios (censo + muestra 15 al cierre).
