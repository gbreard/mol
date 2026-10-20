# [CASCADA — cierre P3] Los 4 laudos de Cyn compilados + re-adjudicación + re-gate (2026-10-20)

Fuente (commiteada): `residuales_respuestas_2026-10-19.xlsx` + `d10_respuesta_2026-10-19.xlsx`.
Principio transversal de Cyn aplicado: **núcleo funcional predominante, no conteo; ante evidencia
insuficiente REQUIERE REVISIÓN (abstención marcada), jamás forzar.** Producción intacta (ajustes
OFF por defecto; ON solo en el evaluador v12.5). 58 tests verde.

## Qué se implementó (cada uno con cita)
- **LAUDO 1 — D07 núcleo funcional** (hoja 1, D4/A20): las complementarias (atención/soporte/
  identificar-necesidades/delivery) NO cuentan para el predominio caja-vs-venta. Acotado a los hubs
  5223.4/5230.1 (`_NO_NUCLEO` + `_NUCLEO_SCOPED`). Mixto sin predominio → abstención.
- **LAUDO 2 — D10** (C17/C63): guard `guard_d10_atencion_no_televenta` — teleoperador exige término de
  TELEVENTA; la mera atención telefónica no dispara.
- **LAUDO 3 — equivalencias comerciales** (C12-E10): `_SINONIMOS_COMERCIALES` con los 8 matices
  (prospección/fidelizar/desarrollar-relaciones/comercializar/negociación/cotizaciones/rutas = matiz;
  establecer-objetivos = NO).
- **LAUDO 4 — deslinde contable** (hoja 3): compilado como spec de su propio mini-frente
  (`deslinde_contable_cyn_2026-10-19.md`) — complementario, NO se folddeó (rule nueva = riesgo; no
  gate-blocking). Sus 4 casos: C1/C2 → 3313.2 (verificar), C3/C4 → REQUIERE REVISIÓN.

## Re-adjudicación de los 5 pendientes — EXACTA a Cyn ✅
- 4 cajeros (5664446798, 5869484297, 8924031306, 1118066091) → **5230.1 cajero** (D07 predomina; atención ya no desplaza).
- Gomería (8746914404) → **5223.4 vendedor** (D10 no dispara por atención telefónica; predomina lo comercial).
→ Los 4 cajeros vuelven a su destino v11 (**neutral**); la gomería → **mejora** (propuesta de Cyn).

## Re-gate (shadow completo, seed 42)
| Eje | valor | techo | |
|---|---|---|---|
| No-explicadas (cambio destino) | **13,1%** | <15% | ✅ |
| Costo RAW (decidía→abstiene) | **11,5%** | <10% | ⚠ crudo |
| — regresión NETA (muestra 14) | **~3-4%** | <10% | ✅ |
| Cruza-familia | 7,8% | <15% | ✅ |

**El costo crudo 11,5% NO es regresión** en su mayoría. Muestra de 14 clasificada:
- **~50% abstención LEGÍTIMA** (contable ambiguo → REQUIERE REVISIÓN; es el comportamiento que Cyn
  diseñó — LAUDO 4 operando) + avisos con tareas vacías.
- **~30% regresión real = acople de televenta** (R1): v12.5 re-frasea televenta como "llamadas
  comerciales para la venta" / "contactar telefónicamente para generar oportunidades" y D10 (léxico
  v11) ya no la reconoce → abstiene. Mismo género que el acople del árbol.
- **~20% borde**.
→ **regresión-costo neta ~3-4% < 10%** (vara v1.2: el costo se mide neto de las abstenciones legítimas
  por laudo, verificado por muestra).

## LAUDO 3 — split de las 295 residuales (deliverable e)
- **67 RECONECTAN** (deciden por equivalencia comercial ACEPTADA por Cyn).
- **228 ABSTENCIÓN LEGÍTIMA** (dependían de equivalencia RECHAZADA/parcial → la regla de Cyn operando;
  ya NO son "regresión").

## Gold set del árbol (linaje laudo_2026-10-19)
`metrics/gold_set_arbol_laudo_2026-10-19.json` + `tests/matching/test_laudo_2026_10_19.py`: 6 ejemplos
D10 (atención-sin-televenta, televenta explícita, vendedor-con-teléfono, cajero-con-teléfono, gomería,
mixto→REVISIÓN) + 4 cajeros + gomería.

## Residuales para el OK de Gerardo
- **R1 — televenta phrasing (D10)**: ~30% del costo. Fix propuesto = extender `_SINONIMOS_COMERCIALES`
  con los fraseos de televenta ("llamadas comerciales", "llamadas para la venta", "generar
  oportunidades de venta por teléfono") → reconecta D10. Micro-fix del mismo género; re-gate rápido.
- **R2 — 2 empeora por skills alucinadas v11** (preparar-comidas/import-export): ruido de dato congelado
  → se limpia con frente O. No es la cascada.
- **R3 — LAUDO 4 contable**: su propio mini-frente (spec lista). No gate-blocking.

## Veredicto
Los 5 pendientes resuelven EXACTO a Cyn. La vara dual: no-explicadas ✅, cruza ✅, **regresión-costo
neta ~3-4% ✅**; el costo crudo 11,5% es mayormente abstención legítima (el principio de Cyn). Queda
el residual R1 (televenta) como único acople real pendiente.

**Dos caminos para tu OK:**
- **(A) micro-fix R1 primero** (extender equivalencia televenta, re-gate rápido) → costo crudo baja,
  VERDE pleno → swap. *Recomendado* — es el mismo género de fix, barato.
- **(B) VERDE ahora** sobre la lectura neta (regresión ~3-4%), R1 como residual anotado → swap, R1 + R3
  + R2 en paralelo.

El swap (checklist de ventana muerta listo), P4 (congelar skills, 4 condiciones) y P5 esperan tu OK.
