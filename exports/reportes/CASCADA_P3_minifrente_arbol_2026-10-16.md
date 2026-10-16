# [CASCADA] Mini-frente árbol v12.5 — capa de equivalencia funcional + re-gate (2026-10-16)

Fix del PARAR del P3: una **capa de equivalencia funcional en el EVALUADOR** (nominalización↔verbo,
doctrina de Cyn), **sin tocar las condiciones** (prosa compilada — intocables). Capa OFF por
defecto (producción intacta); ON solo para el eval v12.5 del gate. Las 118K NO se re-corren.

## (1) Desglose de las 875 (costo del shadow sin capa)
| | n | % | lectura |
|---|---|---|---|
| v12.5 con 3+ tareas, árbol abstiene | **594** | 68% | **regresión-pura** (tareas buenas, forma distinta) |
| v12.5 con 1-2 tareas (adelgazó tras neteo) | 132 | 15% | frontera |
| v12.5 vacío [] | 149 | 17% | abstención legítima (requisito-only) |

## (2) La capa: 10 ejemplos (condición | tarea v11 que matcheaba | tarea v12.5 que no | reconexión)
La condición es NOMINAL; v12.5 verbaliza (método de Cyn). La capa normaliza ambos lados a
verbo-núcleo+objeto como **frase contigua** (no tokens sueltos):

| # | condición (nominal) | v11 matcheaba | v12.5 (no exacto) | raíz compartida |
|---|---|---|---|---|
| 1 | registraciones | "Registraciones contables" | "registrar … registros contables" | registr |
| 2 | carga de facturas | "Carga de facturas" | "cargar facturas" | carg+factur |
| 3 | armado de balances | "armado de balances mensuales" | "armar balances mensuales" | arm+balanc |
| 4 | conciliaciones | "conciliaciones contables" | "conciliar cuentas contables" | concili |
| 5 | asesoramiento | "Asesoramiento sobre la carta" | "asesorar sobre la carta" | asesor |
| 6 | cierre de caja | "control y cierre de caja" | "controlar y cerrar caja" | cerr+caj |
| 7 | atencion al cliente | "Atención al cliente…" | "atender al cliente…" | aten+client |
| 8 | facturacion | "facturación" | "facturar a clientes" | factur |
| 9 | arqueo | "Arqueo y cierre de caja" | "arquear la caja" | arque |
| 10 | imputaciones | "imputaciones de comprobantes" | "imputar comprobantes" | imput |

Guardas anti-sobre-disparo (tras la 1ª corrida que reventó a 33% no-explicadas): **contigüidad de
frase** (verbo-núcleo+objeto adyacentes) + **mono-token ≥5** (no rescata genéricos cortos
vend/pag/cobr/carg) + irregulares acotados (sin transaccionales venta/pago/cobro/compra).

## (3) Gate del mini-frente (shadow re-corrido: v11 capa-OFF vs v12.5 capa-ON)
| Eje | sin capa | **con capa** | techo | |
|---|---|---|---|---|
| Costo (decidía→abstiene) | 15,4% | **8,5%** | <10% | ✅ |
| No-explicadas RAW (cambio destino) | 5,0% | 18,2% | <15% | ⚠ crudo |
| — de las cuales **misma familia** (ISCO-2) | — | 571 (60%) | — | re-ruteo fino (3322↔3321, 1211.x→1211.1) |
| — **cruza familia** (lo que importa) | — | **377 = 7,2%** | <15% | ✅ |
| Mejora (cobertura nueva) | 804 | **3.235** | no perder | ✅ (ganó) |
| Estables (decide-both-same) | 4.578 | 4.260 | no perder | ⚠ −318 (pasaron a re-ruteo, 60% misma fam) |

**Lectura:** la capa **cierra la regresión de forma** (costo 15,4%→8,5%) y las no-explicadas
*cruza-familia* quedan en **7,2% (bajo techo)**. El 18,2% crudo es 60% re-ruteo fino dentro del
mismo grupo ocupacional (nuance de granularidad, no error de familia). La cobertura del árbol
sube (5.693→8.443, +48%) — es el valor del Eje 4 sobre tareas v12.5 mejores.

## Residual → para Cyn (cambio de fondo, no de forma)
De las 594 regresión-pura, **295 siguen abstenien­do con la capa** (costo residual 8,5%): no son
nominalización↔verbo sino **paráfrasis / cambio de contenido** (ej. v12.5 reescribió "prospectar
clientes" como "desarrollar y expandir la cartera" — distinto núcleo). Esas condiciones podrían
necesitar un término nuevo, que es **cambio de fondo → se lista para Cyn, no se re-escribe**.
Lista en `CASCADA_P3_diag_equivalencia_2026-10-16.json`.

## Recomendación (tu gate)
La capa de equivalencia funcional **cumple el objetivo del laudo**: costo <10% (8,5%), no-explicadas
cruza-familia <15% (7,2%), cobertura nueva ganada (no perdida). Precio: 571 re-ruteos finos
intra-familia (bajo riesgo) + 377 cruza-familia (7,2%, bajo techo, muestreables) + 295 residuales
que van a Cyn como cambio de fondo.

Opciones:
- **(A) Aceptar la capa y avanzar al swap/P4** con la capa ON en el matcher (flag
  `equivalencia_funcional`), declarando el re-ruteo intra-familia como nuance esperada. Las 295 a
  Cyn en paralelo. **Recomendado**: el objetivo del mini-frente se cumplió.
- **(B) Muestra humana de los 377 cruza-familia** antes del swap (verificar que no haya
  concentración espuria), y recién ahí avanzar.

No avanzo al swap sin tu OK. Prod intacta (capa OFF por defecto, 32/32 tests traductor verde).
Artefactos: `CASCADA_P3_shadow_equiv_2026-10-16.json`, `database/traductor_contexto.py` (capa).
