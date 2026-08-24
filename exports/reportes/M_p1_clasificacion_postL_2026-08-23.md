# M — P1: re-clasificación de escenarios sobre el corpus post-L

**Fecha:** 2026-08-23 · **Branch:** `feat/export-colegas-postL` · **Clasificador:** v1.0, umbrales sin tocar.

> **Las dos secciones siguientes se escribieron y commitearon ANTES de correr el `02` y de ver un
> solo número de la distribución nueva.** Es una pre-registración deliberada: la advertencia y la
> expectativa quedan fijadas de antemano para que la lectura de los resultados no se acomode a lo
> que salga.

## Advertencia de no-comparabilidad (pre-registrada)

**La distribución de escenarios que produzca esta corrida es una NUEVA LÍNEA DE BASE. No es
comparable, término a término, contra la de junio.** Dos cosas cambiaron a la vez y ninguna es un
error:

1. **El corpus creció:** 68.241 → 97.185 ofertas (**+42%**) y 1.569.227 → 2.827.507 pares
   oferta×skill (**+80%**).
2. **Los destinos ocupacionales se re-decidieron** en un 44% (frente L, matcher 3.6.0). Como la
   unidad de análisis del clasificador es el par (ocupación, skill), esto mueve por sí solo
   `en_canon`, `penetración` y la dispersión que define al comodín — y las masas son poblacionales,
   así que una fila puede cambiar de escenario sin que su propia oferta se haya tocado.

Los umbrales del clasificador se dejaron **intactos en v1.0 a propósito**: mover umbrales y corpus
en la misma corrida haría imposible atribuir cualquier diferencia a una causa u otra.

## Expectativa declarada de antemano

Los umbrales de v1.0 son **absolutos** (≥5 demandantes, ≥15/≥30 de masa de ocupación, ≥100
ocupaciones para comodín). Sobre un corpus más grande, las masas por ocupación crecen y **más pares
cruzan esos mínimos sin que la realidad del mercado haya cambiado**. Por lo tanto se anticipa:

- **Más `B_FUERTE` / `B_DECL_FUERTE`** — pares que en junio no llegaban a los mínimos de masa y
  demandantes, ahora sí.
- **Menos `C1_CANDIDATO` / `C1_DECL`** — el umbral de rareza (≤2 ofertas en el par) se cruza menos
  cuando hay más ofertas por ocupación.
- **Menos `CENTINELA` / `CENTINELA_DECL`** — el bucket residual se vacía hacia B_FUERTE y comodín.

**Todo eso es efecto del crecimiento del corpus, no cambio de la realidad.** Esa es la lectura por
defecto.

**Para qué sirve entonces el lado a lado:** no para comparar, sino porque **la magnitud del
corrimiento es diagnóstica**. Si algún escenario se mueve mucho más de lo que el crecimiento
explica —o se mueve en dirección contraria a la anticipada— eso sí es señal, y hay que mirarlo
antes de publicar.

## Distribución de junio (capturada antes de sobrescribir)

Clasificador v1.0 sobre 1.569.227 pares. Es el único registro que quedaba: el `02` hace DROP/CREATE
de `ofertas_skills_clasificadas` en cada corrida.

| Escenario | n | % |
|---|---:|---:|
| `COMODIN` | 496.094 | 31,61 % |
| `CENTINELA` | 194.693 | 12,41 % |
| `C1_CANDIDATO` | 191.252 | 12,19 % |
| `E` | 135.257 | 8,62 % |
| `A` | 126.028 | 8,03 % |
| `COMODIN_DECL` | 112.517 | 7,17 % |
| `B_FUERTE` | 104.634 | 6,67 % |
| `C1_DECL` | 70.058 | 4,46 % |
| `LEGACY` | 52.068 | 3,32 % |
| `CENTINELA_DECL` | 39.129 | 2,49 % |
| `A_DECLARADO` | 16.551 | 1,05 % |
| `URI_FABRICADA_DERIVED` | 14.983 | 0,95 % |
| `URI_FABRICADA_DECLARED` | 11.528 | 0,73 % |
| `B_DECL_FUERTE` | 4.435 | 0,28 % |
| **TOTAL** | **1.569.227** | **100 %** |

## Cambio al script (universo dinámico, gate duro intacto)

`UNIVERSO_ESPERADO` era la constante `1_569_227`: el corpus de junio hardcodeado, que abortaba la
corrida con `sys.exit(1)` contra cualquier snapshot nuevo. Ahora **se cuenta al inicio de cada
corrida** sobre `ofertas_skills`.

**La exigencia no se relajó**: la corrida sigue abortando si la clasificación no cubre exactamente
el universo, y sigue abortando si **una sola fila** queda en `SIN_BUCKET`. Lo que se eliminó es una
constante que caducaba en cada snapshot, no el control.

## Deuda registrada — re-calibración de umbrales (frente futuro, NO ahora)

Los umbrales de v1.0 son absolutos, y **envejecen con cada crecimiento del corpus**: los mismos
números significan cosas distintas sobre 68k ofertas que sobre 97k, y volverán a significar otra
cosa sobre 150k. Cada corrida futura va a arrastrar el mismo caveat de no-comparabilidad que este
reporte, indefinidamente.

**La pregunta de fondo:** ¿deberían ser **relativos** (percentiles de la distribución de masa y
penetración) en vez de absolutos? Un umbral por percentil se auto-ajusta al tamaño del corpus y
haría las corridas comparables entre épocas — que es justo lo que hoy no se puede hacer. El costo:
los percentiles son más difíciles de explicar y de auditar que "≥5 empresas", y hacen que el
escenario de un par dependa de la distribución global y no de un mínimo interpretable.

No se toca en este frente. Queda anotado con su fundamento para cuando se decida abrirlo.

---

## Resultado de la corrida

*(se completa abajo, después de correr)*
