# [FRENTE K] P4 — Baseline re-medido post-auditoría (el entregable para el frente H)

**Método:** réplica en memoria de `_evaluate_rule_only` (v3.5.8: orden por prioridad, first-match, claves vivas + area/sector + exclusiones, target resoluble) + réplica del diccionario para los residuales, sobre el corpus completo con NLP (84.524 ofertas). Config viejo = `main:config/matching_rules_business.json`; nuevo = post-tandas K. Script: `frente_k_p4.py` (scratchpad), datos crudos en este directorio (`K_datos_p4_2026-08-13.json`).

**Validación de la réplica:** el canal reglas del config viejo da **67,0%**, consistente con el 66,4% medido sobre BD histórica en M1 (FRENTE C) — la réplica reproduce el sistema real. (El 63,5% citado en el encargo era la cifra de una medición anterior sobre otro corte; la referencia operativa es esta.)

## El número para el shadow

| Canal | Baseline VIEJO | Baseline NUEVO (corregido) | Δ |
|---|---|---|---|
| **Reglas de negocio** | 56.623 (**67,0%**) | 50.168 (**59,4%**) | **−7,6 pp** |
| Diccionario forzador | 4.334 (5,1%) | 5.032 (6,0%) | +0,9 pp |
| Diccionario contextual | 3.706 (4,4%) | 4.215 (5,0%) | +0,6 pp |
| Semántico (residual) | 19.861 (23,5%) | 25.109 (29,7%) | +6,2 pp |

## Ofertas cuyo outcome cambia (20.069 = 23,7% del corpus)

| Tipo de cambio | n |
|---|---|
| Mismo trigger, destino corregido (T3 + hijas con código nuevo) | 12.454 |
| Regla retirada → cae al siguiente canal (T1 + colas de T4) | 6.577 |
| Cambia la regla que gana (splits madre→hija, reordenamientos) | 916 |
| Sin regla antes → regla nueva la toma (hijas más anchas que la madre en su rama) | 122 |

Las 12 apagadas + reemplazos mueven 7,6 pp del canal reglas al semántico/diccionario — la mayor parte es no-forzar deliberado de la experta (los falsos positivos que el traductor viene a recuperar con contexto). Las 12.454 con destino corregido NO cambian de canal: mismo trigger, código sano.

## Estado de aplicación (qué contiene este baseline)

- T1 ✔ (7 retiros, P-17 graduada) · T2 = opción (a), sin cambios, gap declarado · T3a+T3b ✔ (68 correcciones) · T4a ✔ (24 grupos, 40 hijas) · T4b ✔ R17/R229/R237 · **R14 y R226 vivas** (verificación dio cola-por-pérdida/territorio-hub → esperan a Cyn; sus 2.504 ofertas siguen en el canal reglas de este baseline) · HOLD 6 grupos mixtos (819) → traductor.
- El corpus histórico en BD conserva los destinos viejos hasta el re-matching masivo (evento aparte). Este baseline describe cómo decide el sistema HOY sobre una corrida fresca.

## Aviso al frente H

**El shadow (P3 del H) queda desbloqueado con este baseline.** Comparar contra el config corregido (main una vez mergeado el PR, o el branch `spec/k-auditoria-reglas-cyn`): reglas 59,4% / dict 11,0% / semántico 29,7%. El cohort de las 7 retiradas (4.686 id_oferta, `exports/cohorts/cohort_T1_pre_retiro_2026-08-13.json`) es la población cuya recuperación mide la fase 2 del traductor — el JOIN está servido.
