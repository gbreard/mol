# [FRENTE H — P3] Matriz v3 del shadow (v0.3.3) — GATE (2026-08-18)

**NADA activado.** Re-shadow con el bundle v0.3.3 completo (P0 registro L3=32 + paridad /a + P1 satélite-exacto + interacción P1×P2 + guard P2a + anclas P2b; P3 = fase 2 por binario). Corpus 84.524, baseline post-K2 (58,4/11,1/30,5). Muestra NUEVA de 30 (ids v1+v2 excluidos: 120 vedados). Tests: 24/24 del evaluador + regresión del case-set P2 completo (11 cambios, todos atribuibles por tag — artefacto commiteado).

## Veredicto del gate: **NO alcanzado — regresión neta 33% (10/30)** · mejoras intactas (37%)

Con el costo-P3 explícitamente aceptado por el laudo descontado: 23%. Sigue arriba del 15%. Tres ajustes chicos identificados abajo; el daño ABSOLUTO extrapolado cayó 3× desde la v1 (604 vs 1.926 ofertas).

## 1. Efecto por tag (la atribución que pidió el laudo)

| Fix/laudo | Efecto medido |
|---|---|
| **Paridad /a** (denominador nuevo declarado) | +826 ofertas entran a evaluación (+7,1%); +528 decididas; el territorio /a converge más que el promedio |
| **P1 satélite-exacto** | **656 abstenciones** con telemetría. Aterrizaje aguas-abajo: **~59% cae en la plana correcta del satélite** (R31 camarero 139, R34 cajero 69, R220 inmobiliario 61, R24 gerente ventas 54, R117 compras 32, R126 seguros 5…) — el laudo funcionando exactamente como se diseñó. **HALLAZGO «satélite sin red fina»: 232 (35%) con título auxiliar/asistente administrativo (satélite 3343.1) caen al dict `administrativo` → ISCO:4110 GRUESO** — la red existe pero pierde el grano fino. Candidato para la próxima ronda de Cyn: denominación fina auxiliar/asistente administrativo → 3343.1 |
| **Guard P2a (1-0)** | **693 ofertas** con bloqueo y sin decisión → siguen al canal actual (inocuo bajo L4). Auditoría de la muestra: mayoría analistas-contables con baseline R14-en-revisión y vendedores-en-calle — no se detectó supresión de redirects claramente verdaderos |
| **Interacción P1×P2** | Confirmatorios con 1 hit funcionando (cajeros con caja → 5230.1); UNA falla de orden detectada (abajo, ajuste A2) |
| **P3 = fase 2** | Costo visible y acotado: 3/30 regresiones son el género análisis-vs-registro (contador público → 3313.2) que la rama sin compilar habría evitado |
| **L3 (32 marcadas)** | 5/30 divergencias de la muestra llevan `L3=True` → neutralizadas por precedencia en activación (R132, R190, R242×3). El registro completado hace visible en la propia muestra lo que antes era regresión invisible |

## 2. Números v2 → v3 (7 hubs congelados)

| Métrica | v2 (v0.3.2) | v2.1 (+/a) | **v3 (v0.3.3)** |
|---|---|---|---|
| decidido | 4.179 | 4.707 | 4.051 |
| **divergencias** | 2.353 | 2.468 | **1.830 (−26%)** |
| convergente | 1.773 | 2.096 | **2.093 (intacta)** |
| satélite-abstención | — | — | 656 |
| evidencia_mixta | 179 | 199 | **86** |
| tasa divergencia/decidido | 56% | 52% | **45%** |

3 hubs propuesta: divergencias 1.232 → **315 (−74%)** — el satélite-exacto absorbe 1.567 títulos de ese vecindario (dominado por labels de satélites). Siguen en propuesta.

## 3. Muestra clasificada (30, una por una): mejora 11 · neutral 4 · neutral-L3 5 · regresión 10

**Mejoras** (el diseño de Cyn): vendedor-atención-al-público con tareas de local → 5223.4 (vs R323 genérica, una de las 71 sin auditar); vendedor mayorista con evidencia B2B → 3322.1 (la denominación-trampa laudada funcionando); asistentes contables operativos → 4311.1/3313.2 según prosa K2; «Vendedora» de pastelería → **5223.7.4** (¡grano fino correcto por D03!); auxiliares administrativos → 3343.1 fino.

**Las 10 regresiones netas, por mecanismo:**

| Mecanismo | Casos | Ajuste candidato |
|---|---|---|
| **A1 — D08/D10 del hub 51 por mención accesoria** («reclamos»/«llamados» en vendedores externos/técnicos → 4225.1/5244.1) | 4 | Léxico: las anclas P2b entraron a 3322.1 pero NO a la inclusión de 5223.4 (visitar clientes/cartera/recorrer zonas) — mismas anclas ahí, o `excluye` de venta-externa en D08/D10. Compilación, no semántica |
| **P3-género** (contador público/analista-con-análisis → 3313.2) | 3 | La rama de responsabilidad espera los marcadores de Cyn (costo aceptado por el laudo binario) |
| **A2 — orden vs confirmatorio en modo satélite** («Cajera»: D01-contraria con 2 hits le gana por ORDEN a D07-confirmatoria) | 1 | Laudo chico: en modo satélite-exacto, las D confirmatorias (destino==satélite) se evalúan PRIMERO |
| **A3 — especializada fuera-de-familia** (R123→2433.6 pisada por 3322.1; familia 243 fuera del criterio L3-por-prefijo) | 1 | Extender L3 al vecindario POR GRAFO (destino D de un hub) además del prefijo de familia |
| Borde léxico (mozo/fast-food → panadería por D03) | 1 | caso borde documentado |

## 4. Recomendación

**NO-GO en este gate.** Camino corto (v0.3.4 — solo compilación + 1 laudo chico, el evaluador casi no se toca):
1. **A1**: anclas de venta-externa también en la inclusión de 5223.4 (misma fuente prosa regla 16 — compilación con marca).
2. **A2**: laudo chico del orden confirmatorio en modo satélite.
3. **A3**: L3 extendido por grafo (criterio ya laudado, alcance más fiel al «vecindario»).
4. Re-shadow + muestra nueva → matriz v4.

Proyección honesta: A1+A2+A3 tocan 6 de las 10 netas → residuo proyectado ~13% (4/30: las 3 de P3-género aceptadas + 1 borde). **Eso rozaría el umbral — lo dirá la matriz v4, no la proyección.** Alternativa que puede laudar Gerardo: dado que el costo P3 fue aceptado explícitamente, medir el gate NETO-DE-P3 (hoy 23%, proyectado ~4-7% post-A1/A2/A3) — pero esa vara la fija el laudo, no este reporte.

**Para la próxima ronda de Cyn/JD** (se acumula al paquete): denominación fina auxiliar/asistente administrativo → 3343.1 (los 232 del hallazgo satélite-sin-red-fina); los marcadores de la rama responsabilidad-integral (P3); R123/R38/R69-género: especializadas correctas que el criterio de familia no cubre.

---
*Datos: `H_p3_datos_shadow_v3_2026-08-18.json`, muestra `H_p3_muestra_v3_2026-08-18.txt` (incluye las 2 auditorías de tag), regresión case-set `H_v033_regresion_caseset_p2_2026-08-18.json`.*
