# [FRENTE K2] Segunda ronda de Cyn — verificación, aplicación y baseline (2026-08-14)

**Fuente:** `exports/cyn_backlog/segunda_ronda_respuestas_2026-08-14.xlsx` (commiteada como primer commit del branch; prosa textual de Cyn = la verdad de dominio). Circuito del K: verificación → blast → tandas → TEST. Linaje `segunda_ronda_cyn_2026-08-14` con prosa citada en cada `_linaje`.

## Verificación de códigos — LIMPIA (21/21 OK-exacto)

Los 9 del encargo (3321.3.1, 2423.3, 2423.6, 2513.3, 3431.1, 9333.8, 9333.8.1, 5244.1, 1221.3.2.1) **más los 12 adicionales que aparecen en la prosa** (4313.1, 1221.3.2, 9333.3, y los del bloque contable) resuelven todos exactos contra el catálogo. Sin paradas.

**Matiz prosa-manda:** el mini-hub RRHH tiene **3 ramas**, no 2 — Cyn suma nómina→4313.1 al par generalista→2423.3 / selección→2423.6. Registrado así en insumos fase 2.

## Aplicado (config v5.21 → v5.23)

| Cambio | Detalle | Blast |
|---|---|---|
| **Retiro R226_analista_rrhh** | destino 2423 = error seguro; reemplazo condicional → mini-hub RRHH fase 2 (3 ramas), NO plana nueva | 770 |
| **Retiro R1_skills_cad** | "la sola mención de CAD no alcanza" — muere el disparador por herramienta | 238 |
| **Retiro R2_skills_diseno_grafico** | ídem Photoshop; destinos funcionales (2513.3/3431.1/1221.3.2) a fase 2 | 89 |
| **Retiro R137_picking** | ídem picking; partido en 3 ramas (9333.8 / 9333.8.1 / 9333.3) a fase 2 | 221 |
| **R229a += 5 variantes con barra** («ejecutivo/a comercial», «ejecutivo/a de ventas/venta»…) | + **exclusión `seguros`** (laudo L3: ninguna plana de seguros K-validada captura «ejecutivo de venta seguros patrimoniales» → exclusión simple, al semántico hasta hub fase 2) | +281 capturas nuevas |
| **R210 → 5244.1** | corrección de la contradicción de 1ª ronda + exclusión «líder de equipo» | 199 re-destino |
| **Alta R210b_lider_equipo_comercial** | distinguible por título → 1221.3.2.1 director de ventas | (dentro de las 281) |
| **R14 — NO tocada** | su territorio lo cubre el hub contable; la respuesta 3 de Cyn es **confirmatoria** del modelo de D del hub (5 destinos coincidentes; matiz: facturación 4311.1-vs-3313.2 anotado). Entra a `subordinadas_al_traductor` (laudo L4) | — |

Cohort snapshot PRE-retiro de las 3 auxiliares: **548 ids** (`exports/cohorts/cohort_K2_pre_retiro_auxiliares_2026-08-14.json`) — mismo patrón que PRE-T1; el JOIN de recuperación fase 2 queda servido.

**TEST entre tandas:** suite matching+harness+puente+spec_h después de los retiros y después de las correcciones: **194 passed ambas veces, mismos 7 fallos preexistentes** (idénticos al baseline del K).

## Insumos fase 2 (precompilación)

`exports/cyn_backlog/insumos_fase2_traductor_2026-08-14.md`: mini-hub RRHH (3 ramas citadas), territorio de las 3 auxiliares (CAD funcional / diseño con UX-fotógrafo-marketing / picking partido en 3), confirmatorio contable + `subordinadas_al_traductor = [R14_contador_auditor]`, rama seguros→3321.3.1, frontera 4222.1-atención.

## Baseline re-medido (el número del re-shadow)

Réplica fiel sobre 84.524 (validación: la pasada post-K reproduce exacto el 59,4/6,0/5,0/29,7 del K):

| Canal | Post-K | **Post-K2** |
|---|---|---|
| Reglas | 59,4% | **58,4%** |
| Diccionario | 11,0% | 11,1% |
| Semántico | 29,7% | **30,5%** |

Outcome cambia en **1.586 ofertas**: 1.104 dejan de forzarse (los 4 retiros), 199 re-destino (R210 y afines), 281 capturas nuevas (variantes de R229a + R210b), 2 splits. **El re-shadow del traductor (v0.3.2) compara contra reglas 58,4% / dict 11,1% / semántico 30,5%.** Y las banderas del shadow anterior quedan medio saldadas: la mitad R226 de `r14r226` ya no existe (retirada); R14 sigue viva y subordinada.

## Para el registro

- Respuestas de JD (hoja 6): acepta la auditoría de las 71 (estima 5-7 días hábiles, pide la lista con avisos asociados — ya está en `proxima_ronda_auditoria_reglas_2026-08-13.md` §1) y **acepta el checksum de integridad del generador** (se implementa de su lado, formato del archivo técnico). Sobre R10: el modelo de las 88 ya cubre «electricista industrial» como ocupación propia → no reactivar; verificar territorio residual en la próxima ronda.
- PR sin mergear, como se pidió.
