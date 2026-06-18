# SPEC S1C-F0.6 — Discovery de anatomía del error (read-only)

> **Estado:** en curso · **Fecha:** 2026-06-18 · **Branch:** `spec/s1c-f06-anatomia-error`
> **Tipo:** discovery puro (read-only, cero implementación).

## Propósito

Confirmar o refutar la **hipótesis dirigente** del master (Eje 3): *el Eje 3 está
bloqueado por el Eje 4 — el vocabulario argentino no tiene dónde actuar mientras
las reglas decidan el ~69% de los casos río arriba*. El experimento puente
(F0.5-exp) la sugirió con una sonda de 4 casos; este discovery la mide sobre el
**universo completo de correcciones de Cyn** y responde la pregunta de fondo:
**¿la Fase 2 arranca por las reglas (Eje 4) o por el vocabulario (Eje 3)?**

## Naturaleza: read-only absoluto

Lee el ledger, baja correcciones de Supabase (lectura), re-corre el matcher en
memoria sin persistir (patrón harness / F0.5), lee las reglas. **No cambia código,
datos ni config.** Lo único que escribe es documentación (este spec) y artefactos
de análisis fechados en `tests/harness/`, vía branch + PR que mergea Gerardo.

## Doble entregable (una corrida, dos ejes)

- **Eje 3 — dónde están los errores:** tabla error × ocupación × familia ocupacional
  × nivel de unidad. ¿Hacia dónde debe crecer el perfil argentino?
- **Eje 4 — cuántas reglas son parche de Cyn vs dominio genuino:** primer corte de
  la clasificación habilitante de la migración de modelo (C5, ~180-220 parche vs
  60-100 de dominio). El número queda apuntado con su consumidor declarado (anti-D-15).

## Insumos

- **Ledger** `exports/cyn_backlog/ledger_correcciones_cyn.jsonl` — 811 issues / **302
  ofertas únicas**, ya parseado en mayo con `cyn_correccion` (verdict, isco_sugerido,
  esco_sugerido_texto) y `pipeline_actual` (isco, **metodo_decision** = canal,
  **metodo_match** / **regla_aplicada**). Snapshot de mayo: referencia, se re-corre.
- **`validacion_correcciones`** (JSONB en `ofertas_dashboard`, Supabase): 278 ofertas.
- **Las tres vías para identificar regla-parche-de-Cyn** (probar en orden):
  1. `_linaje` en `matching_rules_business.json` (si registra origen, alcanza).
  2. `rule_candidates` (Supabase, 361 candidatos M-09b, `issue_ids` con agujeros).
  3. Fallback por nombre/rango de ID de regla (cruce de mayo).
- **El matcher** `MatcherV3(db_conn).match(dict)→MatchResult`, con
  `metadata['decision_metodo']` y `metadata['regla_aplicada']` (instrumentación F0.5).

## Plan

1. Paso cero — consolidar el universo (ledger + delta Supabase). → **PC1**.
2. Determinar la vía de clasificación de regla-parche (probar las 3).
3. Re-corrida read-only del matcher; clasificar en 3 estados (a)/(b)/(c). → **PC2**.
4. Tabla de anatomía (4 cortes) + doble entregable + veredicto de la hipótesis.

## Los cuatro cortes (sobre casos que erraban / siguen errando)

1. **Ocupación × canal de decisión** (regla/semántico/diccionario): ¿qué canal toma
   las decisiones equivocadas?
2. **Familia ocupacional**: ¿se concentran en ingeniería/oficios técnicos (donde el
   perfil argentino no cubre)? — confirma/refuta a escala la pata 1 del doble desajuste.
3. **Nivel de unidad del error**: ISCO-4 mal (rubro entero, matching grueso) vs solo
   granular mal (rubro bien, ocupación exacta mal, vocabulario fino).
4. **Estado tras la re-corrida**: (a) sigue errando · (b) acierta por parche de Cyn
   (circular, no es salud) · (c) acierta por mejora del canal general (salud real).

## Resultado del paso cero (PC1)

| | ofertas |
|---|---:|
| Ledger (`ocupacion`/verdict estructurado) | **302** |
| Supabase `validacion_correcciones` | 278 |
| Delta (en Supabase, NO en ledger) | **10** |
| └─ con corrección de ocupación estructurada | 2 |
| En ledger, NO en Supabase | 34 |
| Intersección | 268 |
| **Universo consolidado** | **312** |

Verdict de ocupación por oferta (ledger 302): **274 tienen al menos un `incorrecta`**,
6 solo confirmada, 22 otro. Canal en el snapshot de mayo (811 issues): rule-driven
475 (regla_prioridad 441 + score_bajo 24 + override 9 + zona_gris 1), semantico_unico
237, dual_coinciden 99.

> El delta de Supabase es chico (10 ofertas, solo 2 con corrección de ocupación
> estructurada; las otras 8 son notas/skills o ESCO en texto libre). El ledger ya
> cubre el grueso del universo de correcciones de ocupación. Artefacto:
> `tests/harness/universo_errores_cyn_2026-06-18.json`.

---

## RESULTADO FINAL (2026-06-18)

### Hallazgo central — el loop está roto (Eje 2, evidencia dura)

> **De 67 errores de ocupación con target claro, el matcher de HOY sigue errando en 65. Solo 2 se arreglaron** (ambos por el semántico, rescatando casos del default absurdo `0110` fuerzas armadas; ninguno por regla).

| estado (sobre 67 errores reales medibles) | n |
|---|---:|
| **(a) sigue errando** | **65** |
| (c) acierta por mejora del canal general | 2 |
| **(b) acierta por parche de Cyn (circular)** | **0** |

**(b)=0 es la prueba dura del loop roto:** las correcciones de Cyn **no volvieron como
reglas** que arreglen sus propios casos. El sistema casi no mejoró sobre el universo que
Cyn marcó. No es falla de detección — el formato `regla_aplicada` se verificó contra las
claves de origen; (b)=0 es robusto porque solo 2 casos se arreglaron en total.

### Veredicto sobre la hipótesis dirigente — matiz cerrado

La hipótesis del master era *"Eje 3 bloqueado por Eje 4"*. **Se refina:** no es bloqueo,
**son los dos canales rotos por su cuenta.**

| población | canal que decide los errores |
|---|---|
| **119 incorrecta sin-target** (correctness no verificable) | **regla 80%** · sem 13% · dicc 8% |
| **67 errores reales medibles** | **regla load-bearing 49%** · sem solo **41%** · dual 6 · dicc 1 |

En el universo amplio las reglas dominan (80%); en el subconjunto medible es **mitad y
mitad**. El semántico yerra ~40% **por su cuenta** → **arreglar solo las reglas dejaría
el residuo semántico sin tocar.** Eje 4 es el mayor canal, pero Eje 3 no está meramente
bloqueado: el semántico está roto independientemente.

### Los tres límites — parte del veredicto, no nota al pie

1. **Medible solo en 67/312.** El resto: 94 con target == respuesta de mayo (confirmación
   o issue de otra dimensión, no error de ocupación) y 151 sin target recuperable (solo
   canal observable). El a/b/c se sostiene sobre 1 de cada 5 ofertas del universo.
2. **Método ciego a errores solo-granulares.** El target de texto libre es ISCO-4; el
   error granular (ESCO fino, rubro bien / ocupación exacta mal) — que es **donde el
   baseline F0.5 ubicó la brecha (ESCO 60%)** — es invisible a esta corrida.
3. **Linaje de reglas en 27%.** El número del Eje 4 es un **piso (26-95), no la
   confirmación de los 180-220** del master. `_linaje` registra origen por-regla solo en
   95/357; las otras 262 quedan indeterminadas (dominio o parche no registrado).

### Los cuatro cortes (sobre los 67 errores reales)

**Corte 1 — canal de decisión** (ver veredicto arriba): regla 39/65 still-erring, sem 25, dicc 1.

**Corte 2 — familia ocupacional del target** (hacia dónde está el error):

| familia (ISCO-1) | n | regla | sem |
|---|---:|---:|---:|
| Profesionales/científicos (2) | 21 | 13 | 8 |
| Técnicos/prof. asociados (3) | 11 | 4 | 6 |
| Oficios y artesanos (7) | 9 | 7 | 2 |
| Operadores planta/máquinas (8) | 9 | 7 | 2 |
| Directivos (1) | 5 | 3 | 2 |
| Apoyo administrativo (4) | 5 | 3 | 2 |
| Servicios y ventas (5) | 5 | 1 | 4 |
| Ocupaciones elementales (9) | 2 | 1 | 1 |

El error se concentra en **Profesionales + Técnicos (32/67 = 48%)** y **Oficios +
Operadores (18/67 = 27%)** — familias técnicas/industriales donde el perfil argentino
**no cubre** (confirma a escala la pata 1 del doble desajuste de F0.5-exp).

**Corte 3 — nivel de unidad del error** (graduado, sobre los 65 que siguen errando):

| distancia al target | n |
|---|---:|
| **gran grupo DISTINTO (error grueso, ISCO-1 distinto)** | **49** |
| mismo ISCO-1 | 6 |
| mismo ISCO-2 (subgrupo) | 4 |
| mismo ISCO-3 (solo unidad menor difiere) | 6 |

**75% de los errores son gruesos** (gran grupo equivocado), no afinamiento fino. Sobre el
universo completo de Cyn, el matcher falla a nivel rubro — distinto del baseline F0.5
(Gold Set curado, ISCO-4 91,7% sano). La diferencia es la población: el Gold Set ya pasó
por propagación; el ledger completo expone la superficie cruda de error.

### Doble entregable

**Para el Eje 3 (hacia dónde crecer el perfil):** los errores se concentran en familias
**técnicas/profesionales** (Profesionales 21, Técnicos 11, Oficios 9, Operadores 9), no en
las ocupaciones de servicios/ventas que el perfil argentino ya cubre bien. Y el 75% son
errores **gruesos** (gran grupo), no granulares → el frente no es afinar vocabulario fino
sino corregir matching grueso en familias técnicas.

**Para el Eje 4 (reglas parche vs dominio — primer corte, consumidor: C5 migración de
modelo):** piso de **26 reglas con autor Cyn explícito / 95 con algún marcador de origen**,
sobre 357. **21 reglas distintas deciden los 67 errores hoy**; la más ofensora
**`R240_operario_produccion` decide 9 errores ella sola** (sobre-dispara). El número de
parches NO se puede cerrar desde `_linaje` (27% de cobertura) — es un piso, no los 180-220.

### Dos observaciones (registradas, no se resuelven acá)

- **Residencia (Eje 2/5):** 34 ofertas están en el ledger pero **no** en
  `validacion_correcciones` de Supabase — desincronización del dato humano (el issue existe
  pero no se escribió de vuelta al JSONB del dashboard).
- **Canal cambió mayo→hoy:** 9/67 errores cambiaron de canal entre mayo y hoy — el sistema
  se modificó activamente en el ínterin (siguen errando, pero por otro canal: una regla
  nueva se metió en el medio).

### Artefactos

```
tests/harness/universo_errores_cyn_2026-06-18.json      universo consolidado (312)
tests/harness/anatomia_error.py                          re-corrida read-only del matcher
tests/harness/anatomia_recorrida_2026-06-18.json         canal+resultado hoy (312)
tests/harness/anatomia_clasificar.py                     clasificación a/b/c + 4 cortes
tests/harness/anatomia_clasificacion_2026-06-18.json     clasificación fechada
```
