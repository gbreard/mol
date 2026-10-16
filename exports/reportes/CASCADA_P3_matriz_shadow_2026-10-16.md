# [CASCADA] P3 — MATRIZ DEL SHADOW DEL ÁRBOL — tu gate del swap (2026-10-16)

**Veredicto: la vara dual FALLA en el eje costo → por el laudo, regresión del evaluador = PARAR.**
El shadow hizo exactamente su trabajo: detectó un **acople sistémico del árbol a la redacción
v11** antes de que contaminara el re-matching. No avanzo al swap ni al P4. **Decisión tuya.**

> Shadow: `TraductorContexto.evaluar()` sobre las 119.081 del staging, dos veces — mismo título
> y mismos otros campos; SOLO cambian las tareas (v11 del snapshot vs v12.5 neteado). Aísla el
> efecto de las tareas sobre el árbol (Eje 4). Read-only, no cambió ninguna decisión.
> Crudo: `CASCADA_P3_shadow_2026-10-16.json`.

## La matriz (árbol standalone: decide v11=5.693 / v12.5=5.622 de 119.081)

| Transición | n | eje de la vara dual |
|---|---|---|
| decidía ambos, **mismo** código | 4.578 | estabilidad (80,4% de decide-v11) |
| decidía ambos, **cambió** destino | 240 | **no-explicadas = 5,0%** de decididos-ambos · **✅ < 15%** |
| **decidía v11 → abstiene v12.5** | 875 | **costo = 15,4%** de decide-v11 · **❌ > 10%** |
| abstenía v11 → **decide** v12.5 | 804 | mejora (cobertura nueva) |
| abstiene ambos | 112.584 | — |

## El costo (875), clasificado por riqueza de la tarea v12.5
| | n | % de 875 | lectura |
|---|---|---|---|
| v12.5 con **3+ tareas** (ricas) y el árbol abstiene | **594** | 68% | **REGRESIÓN dura del evaluador** |
| v12.5 con 1-2 tareas (adelgazó tras neteo) | 132 | 15% | frontera |
| v12.5 vacío ([]) | 149 | 17% | abstención probablemente legítima |

**Aun contando solo la regresión dura (594), es 10,4% de decide-v11 — sigue por encima del
techo 10%.** No es precisión ganada: en 594 ofertas v12.5 extrajo tareas buenas (a veces mejores)
y el árbol dejó de decidir.

## Causa raíz (confirmada)
El árbol arma **hubs candidatos por el TÍTULO** (idéntico en ambas corridas) y luego evalúa las
**condiciones del hub contra las tareas**. v12.5 cambia las tareas de dos formas que rompen esas
condiciones:
1. **Normalización nominalización→verbo** (el método de Cyn): v11 "Asesoramiento", "Prospección",
   "Registración" → v12.5 "asesorar", "prospectar", "registrar". Las condiciones del hub fueron
   calibradas contra la redacción v11.
2. **Adelgazamiento por el neteo HSE + extracción más estricta**: menos ítems → no se alcanza el
   umbral de evidencia del hub.
Ejemplos (muestra de 15, ~11 con tareas v12.5 buenas y árbol abstiene): 2188264 (11 tareas
contables buenas → `familia_sin_rama`), 8100134345 ("asesorar y demostrar…" casi idéntico a v11
→ abstiene), 1118409617 (4 tareas de venta → abstiene). **El árbol está calibrado a la redacción
v11; v12.5 es mejor pero el evaluador no la reconoce.**

## Escala y contención
- 875 ofertas = **0,7% del corpus**; el árbol decide solo **3,8%** en producción (3.710). Las que
  el árbol deja de decidir **caen al canal siguiente** (subordinadas → semántico) — siguen
  decidiéndose, con otro método (posible pérdida de precisión del Eje 4, no abstención total).
- Las 804 mejoras (cobertura nueva) muestran que v12.5 TAMBIÉN habilita decisiones que v11 no
  lograba — el efecto neto en cobertura es casi neutro (5.693 → 5.622), pero la COMPOSICIÓN cambió.

## Recomendación (tu gate)
**PARAR el avance al swap/P4 hasta re-alinear el árbol.** El fix es acotado y claro:
- **Mini-frente "árbol v12.5"**: re-alinear el léxico/condiciones de los 7 hubs a la redacción
  verb-normalizada + granularidad de v12.5 (agregar formas verbales que falten, recalibrar el
  umbral de evidencia del hub a la densidad de tareas v12.5). Target medible: las **594** de
  regresión dura (auditable, el snapshot las fija).
- Re-correr este mismo shadow como **gate de re-check**: costo < 10%, no-explicadas < 15%, mejoras
  intactas. Recién ahí el árbol corre limpio sobre v12.5 en el re-matching.

Alternativas que decidís vos:
- **(A) Mini-frente árbol primero** (recomendado): corrige la causa raíz; ~0,7% del corpus pero es
  el Eje 4, la joya de la precisión argentina.
- **(B) Aceptar el shift** sabiendo que las 594 caen a subordinadas/semántico (no se pierden, se
  deciden con menos precisión) y re-alinear el árbol como frente post-swap. Más rápido al P4, paga
  precisión del Eje 4 en 0,7%.

No hay regresión en los otros ejes (no-explicadas 5,0% ✅). El swap y el P4 esperan tu decisión
sobre el árbol. El P4 ya tiene su diseño cerrado (congelar skills, las 4 condiciones del harness).
