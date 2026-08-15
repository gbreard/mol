# [FRENTE K] P2 — Plan de aplicación (PUNTO DE CONTROL — nada aplicado)

Base: `K_verificacion_entrada_2026-08-13.md`. Todo cambio traza al JSON de Cyn por `regla_id` + `nota_revision_final`. Linaje: `auditoria_cyn_2026-08-12`. Los triggers vivos NO se tocan (auditoría de destinos). El corpus histórico NO se reprocesa (queda con destinos viejos hasta el re-matching, que es otro evento).

## Resumen del blast total

| Bloque | Cambio | Reglas | Ofertas (uso histórico = proxy del flujo) | Efecto en corridas frescas |
|---|---|---|---|---|
| **T1** | Retiro de destino (desactivar) | 7 | **4.686** | dejan de forzarse → dict-contextual/semántico |
| **T2** | ISCO-familia (gap — decisión) | 2 | 73 | según opción elegida |
| **T3** | Corrección de destino | 68 | **10.758** | mismo trigger, destino corregido |
| **T4** | Reemplazo madre→hijas (grupos completos) | 29 madres → 42 hijas nuevas | **7.154** (2.343 re-asignadas por hijas + **4.811 cola genérica** dejan de forzarse) | split fino + no-forzar deliberado |
| — | HOLD: grupos mixtos (hijas contextuales) | 6 madres (11 hijas + 2 NULL) | 819 | material del traductor — no se aplica |
| — | LISTADOS (no se aplican) | R210, R10, 8 auxiliares, 71 post-export | ~5.900 | preguntas/próxima ronda |
| | **Total outcome-change si se aplica todo** | | **≈ 22.700 de 45.291 decididas por reglas (~50%)** | |

La escala lo dice: esta auditoría reescribe la mitad del canal que decide el 63,5% del sistema. Por eso las tandas con TEST reservado entre cada una.

## T1 — Los 7 retiros (primera tanda, la más urgente)

Desactivar (`activa: false` + `_linaje.retirada_por: auditoria_cyn_2026-08-12` + nota de Cyn citada): R49_jefe_generico (1.623), R240_operario_produccion (1.584), R235_mecanico (1.242), R158_jefe_operaciones (188), R160_tecnico_instalador (43), R176_auditor_franquicias (5), R250_supervisor_fractura (1).

**Al aplicar: GRADÚA P-17** — R240_operario_produccion, la mayor fuente de error individual (9/67 en la anatomía), retirada por decisión de la experta. R235 y R49 (cabezas genéricas del mismo género) caen en el mismo acto.

Trade-off medido (muestreo P1 §5): R49 mejora claro; R240/R235 cambian falso-positivo-uniforme por mezcla acierto/disparate del semántico a 0.6. Es el estado honesto que el shadow del H debe ver.

## T2 — Las 2 ISCO-familia (decisión de Gerardo, no se improvisa)

El matcher no soporta destino ISCO-sin-ESCO (`_resolve_rule_target` exige esco_code/label). Opciones para R263 (uso 4) y R82 (uso 69):

- **(a) Dejarlas como están** (9129.2 / 8131.20) hasta que el traductor soporte nivel-familia. Costo: mantiene el ESCO fino que Cyn declaró NO defendible; beneficio: cero pérdida de cobertura. **Recomendada** por blast chico y porque el criterio 8 de Cyn es "asignar a familia", no "apagar".
- (b) Retirarlas como las 12. Contradice el criterio de Cyn (ella las mantiene a nivel ISCO).
- (c) Implementar soporte ISCO-familia en el matcher. Cambio de código (bump de versión) fuera del alcance de este frente.

## T3 — Las 68 correcciones de destino (2 tandas de ~34, TEST entre tandas)

Editar solo `accion.esco_code` + `esco_label` (+ `forzar_isco` derivado del código nuevo) con linaje. Top por blast:

| Regla | uso | actual → nuevo |
|---|---|---|
| R111_vendedor_generico | 3.882 | 5223.7 → **5223.4** (converge con las 88, hub 51) |
| R238_analista_it | 732 | 2511.7 → 2511.13 |
| R14d_administrativo_contable | 509 | 4311.1 → 3313.2 (hub 3) |
| R231_supervisor_operaciones | 433 | 3122.2 → 3122.4 |
| R106_preventista | 388 | 5243.1 → 3322.1 |
| R242_asistente_impuestos | 365 | 2411.1.1 → 2411.1.12 |
| R220_asesor_inmobiliario | 325 | 3334.3 → 3334.2 |
| R152_ecommerce_manager | 317 | 1221.5 → 2431.10.2 |
| … (60 más, 3 con uso 0) | | lista completa en `frente_k_p1.json` |

Los 68 códigos nuevos ya verificados contra catálogo (P1 §1). 65/77 de los cambios son AMBIGUA/HUÉRFANA en M1 → el fix les llega SOLO por acá.

## T4 — Los 29 reemplazos madre→hijas completos (última tanda aplicable, posiblemente 2)

Por grupo: crear las hijas titulo-only (condición = el `titulo∈[...]` COMPLETO del JSON, target = su código verificado, prioridad heredada de la madre) + desactivar la madre. 42 hijas nuevas con código; 4 hijas-NULL no se crean (son el no-forzar del genérico: R17c, R65b, R68b + R229/R237 sin marca pero con cola 0-cubierta deliberada).

**Cola genérica por grupo** (ofertas de la madre que ninguna hija cubre → dejan de forzarse):

| Grupo | uso madre | cubre hijas | cola |
|---|---|---|---|
| R14_contador_auditor → R14a/R14e (+ b/c/d ya vivas) | 1.734 | 42,7% | 993 |
| R229_analista_comercial → R229a_ejecutivo_comercial | 825 | 0% | 825 |
| R17_compliance_legal → (solo R17c NULL; R17b ya viva) | 728 | 0% | 728 |
| R226_analista_rrhh → R226a/R226b | 770 | 20,6% | 611 |
| R237_analista_finanzas → R237a/R237b | 392 | 0% | 392 |
| R48_secretaria_admin → R48a/R48b | 499 | 49,3% | 253 |
| R65_jefe_delegacion → R65a (+R65b NULL) | 219 | 0% | 219 |
| … 22 grupos más (4 con cobertura 100%) | | | |
| **Total** | **7.154** | **32,8%** | **4.811** |

⚠ Lectura: en R17/R65/R229/R237 la cola-0 es coherente con la intención de Cyn (el genérico deja de forzarse — es la misma cirugía que las 12). Pero el tamaño agregado (4.811) amerita que Gerardo decida si T4 va entero, por sub-tandas (ej. primero los 8 grupos con cobertura ≥70%), o si los grupos de cola grande (R14, R229, R17, R226, R237) esperan al traductor. **Propuesta: aplicar entero — es el diseño de la experta — pero en 2 sub-tandas: (T4a) los 22 grupos con cola <300; (T4b) los 7 grandes, con re-medición entre medio.**

**HOLD explícito (no se aplica):** los 6 grupos mixtos R191, R193, R208, R213, R214, R283 (819 uso): sus hijas exigen contexto tareas/sector que las claves vivas del matcher no evalúan (claves muertas). Sus condiciones ya son árboles — van al traductor (frente H) tal cual están escritas en el JSON. Las madres siguen vivas mientras tanto.

## Listados que NO se aplican (van a devolución/decisión)

1. **R210_telefonista_ventas** (12): contradicción interna del JSON (validada con 5244.1, vivo 4222.1) → pregunta a Cyn.
2. **R10_electricista_industrial**: desactivada + condición muerta; Cyn da 7411.1.1.2 → alta nueva si Gerardo quiere (condición habría que redactarla → mejor con Cyn).
3. **Las 8 auxiliares**: R1/R2/R137 asignan por skills en producción (548 ofertas) con destinos NO validados por Cyn (código null en su JSON) → candidatas a próxima ronda de auditoría; no se tocan acá.
4. **Las 71 vivas post-export** (5.254): fuera del universo auditado → export fresco para la próxima ronda de Cyn.

## Orden de ejecución propuesto (con el OK)

```
Tanda 1: T1 (7 retiros) ................. commit + TEST reservado + graduación P-17
Tanda 2: T3a (34 correcciones top-uso) ... commit + TEST
Tanda 3: T3b (34 restantes) .............. commit + TEST
Tanda 4: T4a (22 grupos cola<300) ........ commit + TEST
Tanda 5: T4b (7 grupos grandes) .......... commit + TEST
T2 según opción elegida (si (a): sin cambios)
P4: baseline re-medido (corrida en memoria, muestra representativa) → entregable para el shadow del H
PR spec/k-auditoria-reglas-cyn (no mergear)
```

**Esperando el OK de Gerardo (total o por bloque: T1 / T2-opción / T3 / T4a / T4b).**
