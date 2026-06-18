# docs(spec-s1c-f06): discovery de anatomía del error

Discovery **read-only** sobre el universo completo de correcciones de Cyn (312
ofertas), para confirmar o refutar la hipótesis dirigente del master (Eje 3:
*"bloqueado por el Eje 4"*). Re-corre el matcher de hoy en memoria sin persistir
(patrón harness/F0.5), no cambia código, datos ni config. Los cambios al sistema se
diseñan después, con este dato en mano.

## ⭐ Hallazgo central — el loop de Cyn está roto (evidencia dura, Eje 2)

> **De 67 errores de ocupación con target claro, el matcher de HOY sigue errando en
> 65. Solo 2 se arreglaron** — y ambos por el semántico (rescate del default absurdo
> `0110` fuerzas armadas), **ninguno por regla**.

| estado (67 errores reales medibles) | n |
|---|---:|
| **(a) sigue errando** | **65** |
| (c) acierta por canal general (salud real) | 2 |
| **(b) acierta por parche de Cyn (circular)** | **0** |

**(b)=0 es la prueba dura:** las correcciones de Cyn **no volvieron como reglas** que
arreglen sus propios casos. El sistema casi no mejoró sobre el universo que ella marcó.
Robusto, no artefacto de detección: el formato `regla_aplicada` se verificó contra las
claves de origen; (b)=0 sale de que solo 2 casos se arreglaron en total.

## Veredicto sobre la hipótesis dirigente — matiz cerrado

No es *"Eje 3 bloqueado por Eje 4"*. **Son los dos canales rotos por su cuenta.**

| población | canal que decide los errores |
|---|---|
| 119 incorrecta **sin-target** | **regla 80%** · sem 13% · dicc 8% |
| 67 errores **medibles** | **regla load-bearing 49%** · sem solo **41%** · dual 6 · dicc 1 |

Las reglas son el mayor canal en el universo amplio (80%), pero en lo medible es **mitad
y mitad**. El semántico yerra ~40% por su cuenta → **arreglar solo las reglas deja el
residuo semántico sin tocar.** Eje 4 es la palanca mayor, pero Eje 3 no está meramente
bloqueado.

## Los tres límites — parte del veredicto, no nota al pie

1. **Medible solo en 67/312.** El a/b/c se sostiene sobre 1 de cada 5 ofertas (94 con
   target == respuesta de mayo = confirmación/otra dimensión; 151 sin target recuperable).
2. **Ciego a errores solo-granulares.** El target de texto libre es ISCO-4; el error
   granular ESCO fino — **donde el baseline F0.5 ubicó la brecha (ESCO 60%)** — es
   invisible a esta corrida.
3. **Linaje de reglas en 27%.** El número del Eje 4 es un **piso (26 autor-Cyn / 95
   con-marcador sobre 357), NO la confirmación de los 180-220** del master.

## Doble entregable

**Eje 3 — hacia dónde crecer el perfil:** el error se concentra en familias **técnicas/
profesionales** — Profesionales 21, Técnicos 11, Oficios 9, Operadores 9 (48%+27%), no en
servicios/ventas que el perfil ya cubre. Y **75% de los errores son gruesos** (gran grupo
ISCO-1 equivocado: 49/65), no afinamiento fino → el frente es matching grueso en familias
técnicas, no vocabulario fino.

**Eje 4 — reglas parche vs dominio (1er corte, consumidor C5 migración de modelo):** piso
**26-95 / 357**. **21 reglas deciden los 67 errores hoy**; la más ofensora
**`R240_operario_produccion` decide 9 ella sola** (sobre-dispara).

## Por qué difiere del baseline F0.5

F0.5 (Gold Set curado de 113) dio ISCO-4 91,7% sano. Acá, sobre el ledger completo, el
matcher falla a nivel rubro en 49/65. La diferencia es la **población**: el Gold Set ya
pasó por propagación; el ledger crudo expone la superficie de error real.

## Dos observaciones (registradas, no se resuelven acá)

- **Residencia (Eje 2/5):** **34 ofertas** están en el ledger pero **no** en
  `validacion_correcciones` de Supabase — desincronización del dato humano.
- **Canal cambió mayo→hoy:** **9/67** errores cambiaron de canal en el ínterin (una regla
  nueva se metió en el medio; siguen errando, por otro canal).

## Estructura

```
docs/specs/SPEC_S1C_F06_ANATOMIA_ERROR.md              spec + paso cero + resultado final
tests/harness/universo_errores_cyn_2026-06-18.json     universo consolidado (312)
tests/harness/anatomia_error.py                         re-corrida read-only del matcher
tests/harness/anatomia_recorrida_2026-06-18.json        canal+resultado hoy (312)
tests/harness/anatomia_clasificar.py                    clasificación a/b/c + 4 cortes
tests/harness/anatomia_clasificacion_2026-06-18.json    clasificación fechada
```

## Reglas respetadas

Read-only absoluto (guard de conteos de producción sostenido, nunca `match_and_persist`).
No se tocó el baseline/snapshot de F0.5, `config/training_pairs.json`,
`metrics/gold_set_history.json` ni ningún gold set. No mergear — el merge es de Gerardo.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
