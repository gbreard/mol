# [FRENTE H — P3] Matriz v4 del shadow (v0.3.4) — LA LECTURA DEL GATE (2026-08-18)

**NADA activado — el OK es de Gerardo.** Bundle v0.3.4 completo (A1-bis term-set único + A2 confirmatorias-primero + A3 L3-por-grafo, sobre v0.3.3: P0+paridad/a+P1+P2+interacción). Corpus 84.524, baseline post-K2 (58,4/11,1/30,5). Muestra NUEVA de 30 (ids v1+v2+v3 vedados: 196). Tests 28/28; regresión case-set: 5 cambios, todos A1-bis (incluye el bonus «Vendedor viajante»→3322.1 y el riesgo-documentado «Telemarketer»→abstención+plana).

## ⚠ Señalamiento previo a la lectura (lo pide el propio laudo de la vara)

La formulación de la bajada tiene un matiz ambiguo: si «neta-de-explicadas» = las regresiones SIN laudo citable, entonces «cero regresiones sin explicar» implicaría neta=0 y el «<15%» sería redundante. Se presentan LAS DOS lecturas; si el texto completo del harness difiere, ese texto manda.

## La vara dual

**Muestra clasificada (30): mejora 17 (57%) · neutral 2 · neutral-L3 7 · regresión BRUTA 4 (13,3%).**

| Vara | Valor | Umbral | ¿Pasa? |
|---|---|---|---|
| **BRUTA** (declarada al lado, con contexto) | **4/30 = 13,3%** | — | (contexto) |
| **NETA-de-explicadas** (bruta − laudo-citable) | **2/30 = 6,7%** | <15% | **SÍ** |
| Mejoras intactas | 57% (v3: 37%) — récord de la serie | intactas | **SÍ** |
| «Cero regresiones sin explicar» — lectura (i) estricta: sin-laudo-citable = 0 | 2 sin laudo | 0 | **NO** |
| «Cero sin explicar» — lectura (ii): toda regresión con MECANISMO nombrado y diagnóstico | 4/4 diagnosticadas | 0 sin diagnóstico | **SÍ** |

**Las 4 regresiones, una por una:**
1. **«Contador especializado en gestión financiera»** y 2. **«Contador/a»** → D02 los baja a 3313.2 con cierres/estados/DDJJ en las tareas — **P3-género, laudo citable** (el binario mandó la rama responsabilidad a fase 2; costo aceptado explícitamente).
3. **«Representante comercial vendedor»** → inclusión 5223.4 (baseline R40→3322.1 correcto): la denominación «representante comercial» NO está en los titulos_aviso de la regla 16 (sí «representante de ventas») → solo el hub 51 evaluó. **Mecanismo nombrado, sin laudo**: agregar denominación = tocar la fuente (JSON 2.0) → pregunta a Cyn, no compilación.
4. **«Gerente administrativo contable»** → inclusión hub 1 lo hace *analista* (baseline R303→1211.1 director): señales de jerarquía sin rama que las frene (hermana del P3-género, pero el laudo P3 habló de análisis-vs-registración, no de conducción). **Mecanismo nombrado, sin laudo.**

## Efecto por tag (v4)

| Tag/fix | Efecto |
|---|---|
| **excluye_venta_externa** (A1-bis) | **1.795 ofertas** con alguna D bloqueada por el set: 1.045 deciden igual por otra vía (dominado por el flip D08/D10→**D11→3322.1**: vendedor de calle, b2b, preventista — converge con R106-K-corregida —, viajante — converge con R317) + 750 sin decisión → subordinación. Auditoría: el bonus del laudo funcionando en serie. **Sub-riesgo anotado**: teleoperadores CON cartera/prospección real van a 3322.1 vía D11 (no abstienen) — frontera venta-telefónica-de-cartera, material Cyn |
| **A2 confirmatorias-primero** | El testigo v3 resuelto (test 26 verde); en la muestra: «Empleado/a administrativo/a» = label-exacto de 3343.1 → D confirmatoria decide **3343.1 fino** (antes: dict grueso 4110) — P1+A2+paridad/a componiendo |
| **A3 L3-por-grafo** | Registro 32 → **63** (+31: R123 el testigo, R31/R34 — las redes de los satélites P1 —, R210/R210b, R38, R15…). En la muestra: **7/30 divergencias neutralizadas visibles** (`L3=True`), incluida la de seguros (R126 precede — el diseño exacto). Nota: en «Vendedor telefónico call center» L3 protege a R15→4222.1 donde la prosa K2 de Cyn daría 5244.1 — frontera R15-venta para su próxima ronda |
| P1 satélite | 658 abstenciones estables; aterrizajes ahora mayormente en planas **L3-marcadas** (R31/R34/R117/R85a) — el circuito cerrado |
| guard_1a0 | 693 → 644 (D11 ahora decide parte) |

## Números v3 → v4

| Métrica | v3 | v4 |
|---|---|---|
| decidido | 4.051 | 4.446 |
| divergencias | 1.830 | 2.203 (+373 — dominadas por el flip D11→3322.1 contra R111: en la muestra son MEJORAS) |
| convergente | 2.093 | 2.115 |
| evidencia_mixta | 86 | 77 |
| **mejoras en muestra** | 37% | **57%** |
| **regresión bruta en muestra** | 33% | **13,3%** |

3 hubs propuesta: sin cambios de estado (divergencias 298, muestra dominada por D07-caja de 5223.7 — sus fixes llegan con su propio ciclo).

## Recomendación contra el gate formal

**La neta pasa: 6,7% < 15%, con las mejoras no solo intactas sino en récord (57%).** La bruta (13,3%) queda declarada al lado y hasta ELLA está bajo el umbral. El único punto abierto es el matiz de la tercera condición:

- **Lectura (ii)** (toda regresión diagnosticada): **GO** — en modo decide-cuando-decide + subordinación (L4), hubs congelados solamente, con las 2 sin-laudo como deuda visible para Cyn (denominación «representante comercial» en regla 16; rama de jerarquía del vecindario contable) y los 2 sub-riesgos anotados (venta-telefónica-de-cartera; frontera R15).
- **Lectura (i)** (cero sin-laudo-citable): NO-GO hasta laudar esos 2 mecanismos (ambos son pregunta-a-Cyn, no compilación — la vuelta sería con su respuesta, no con código).

**Mi recomendación: GO por la lectura (ii)** — las 2 sin-laudo están contenidas por el mismo diseño que el gate ya exige (subordinación: en el caso 3 la plana R40 sigue decidiendo si el traductor no fuerza... no aplica: acá el traductor SÍ fuerza; el daño real es 5223.4-vs-3322.1 con-arista en el caso 3, y gerente→analista en el caso 4 — ese último es el único daño duro sin red). Si preferís la letra estricta, la vuelta es corta y pasa por Cyn. **La decisión es tuya; nada se activa hasta tu OK.**

---
*Datos: `H_p3_datos_shadow_v4_2026-08-18.json`, muestra `H_p3_muestra_v4_2026-08-18.txt` (con las 3 auditorías de tag), case-set `H_v034_regresion_caseset_2026-08-18.json` (5 cambios A1-bis).*
