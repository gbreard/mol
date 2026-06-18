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
