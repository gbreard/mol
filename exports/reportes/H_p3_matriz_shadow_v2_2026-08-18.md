# [FRENTE H — P3] Matriz v2 del shadow (v0.3.2) — GATE (2026-08-18)

**NADA activado.** Re-shadow tras los laudos H_v032 (L1 evaluador+léxico v0.3.2, L2 piso regenerado, L3 14 especializadas marcadas), corpus 84.524, **baseline POST-K2: reglas 58,4% / dict 11,1% / semántico 30,5%**. Bandera reducida a solo-R14 (R226 retirada en K2). Muestra NUEVA de 30 (seed distinta, ids de la v1 excluidos — mismo método, cero re-mirada).

## Veredicto del gate: **NO pasa** — regresión bruta 50% (15/30), neta-L3 ~37% (> umbral 15%)

Pero el cuadro cambió de naturaleza: **los mecanismos de la v1 están muertos** y el residuo son tres patrones nuevos, chicos y nombrables, cada uno con fix candidato que requiere laudo (no improvisamos ninguno).

## 1. Los números v1 → v2 (7 hubs congelados)

| Métrica | v1 (v0.3.1) | v2 (v0.3.2) | Δ |
|---|---|---|---|
| decidido | 5.484 | 4.179 | −24% |
| **divergencias** | 3.852 | **2.353** | **−39%** |
| convergente | 1.579 (29% de decidido) | 1.773 (**42%**) | +13pp |
| **evidencia_mixta** | 1.222 | **179** | **−85%** |
| trad fuerza / baseline no | 53 | 37+53→ ver §4 | — |
| trad no fuerza / baseline sí | 7.828 | 6.067 | −23% (inocuo bajo L4) |
| bandera R14 (solo) | 656 (con R226) | 546 | — |

Los shifts por hub ganador confirman que L1 hizo su trabajo: capturas de 3313.2 631→195 (−69%), 1211.1.1 325→56 (−83%), 4312.1 287→95 (los gerentes ya no van a auditor); 2411.1.1 677→877 (la inclusión analista-contable decide más — es SU territorio).

Piso L2: 245→239 triggers. **Corrección factual al laudo registrada:** «administrativo» NO era fragmento — es **alt-label LITERAL de 4110.1** en ESCO. La decisión del laudo se cumplió igual (exclusión nominal documentada: desparramaba a 4 hubs); la premisa "fragmento" queda corregida en el registro. La regla general label-completo eliminó el resto.

## 2. Muestra nueva clasificada (30 divergencias, una por una)

**Mejora 11 (37%) · Neutral 4 (13%) · Regresión 15 (50% bruta).**

Las mejoras siguen siendo el diseño de Cyn: B2B→3322.1 («Vendedor técnico industrial», «Vendedor b2b seguridad industrial»), asistentes/auxiliares contables operativos→3313.2/4311.1 exactamente como su prosa K2, «Asistente administrativo cuentas a pagar»→4311.1 fino contra el 4110 genérico del dict.

**Las 15 regresiones, desagregadas por patrón (esto es lo nuevo):**

| Patrón | Casos | Qué pasa | Fix candidato (requiere laudo) |
|---|---|---|---|
| **P0 — L3 en acción** (no es defecto: la precedencia la neutraliza) | 4 | «Asistente contable e impositiva»→4311.1 pisando a R242→2411.1.12 (marcada L3 ✓); «Auditor interno»×2 pisando a R190→2411.1.7 y «Analista financiero»→R69→2413.1 — **L3 por derecho pero SIN marcar** (eran validadas-IGUAL del K, que no dejó linaje) | Completar el registro L3 recomputando las IGUAL del K (barato: config vs JSON de Cyn) — criterio ya laudado, solo falta el registro |
| **P1 — título = label de satélite puro** | 4 | «Cajero/a», «Camarero/a», «Cajero», «Recepcionista/cajera» titulados: el piso (label completo VÁLIDO por L2) activa el hub y la inclusión/D los captura — pisando planas correctas (R34, R31, R26) | Laudo nuevo: si el título ≈ label exacto del satélite, el traductor propone el satélite o se abstiene (no_aplica) |
| **P2 — inclusión sin anclas (D gana 1-0)** | 5 | «Vendedor en calle» (cobros→cajero), «Vendedor combustible GNC», «Vendedor»×2 (reclamos→posventa 4225), «Vendedor/preventista» (stock→asistente tienda): la inclusión matchea 0 (vocabulario de venta-externa fuera del léxico) y una D redirige con 1 único match | Léxico: anclar venta-externa/ruta en las inclusiones 5223.4/3322.1; y/o laudo: D no redirige con 1 match único si la inclusión dio 0 y el trigger es denominación propia del hub |
| **P3 — señales de jerarquía sin compilar** | 2 | «Contador», «Contador/a senior» → D02 los baja a 3313.2; la prosa K2 de Cyn dice "responsabilidad profesional integral → 2411.1" — esa señal (liderar, asegurar, cierres a cargo) no está compilada | Compilar la rama responsabilidad-integral de la prosa K2 (excluye en D02 o rama propia) |

Neutrales: fronteras genuinas (analista contable con tareas mixtas registro+impuestos, comercio exterior comercial-vs-especialista, mostrador+telefónica).

**Neta-L3:** si el registro L3 estuviera completo, las 4 de P0 no son regresiones de activación (la plana precede) → 11/30 = **37%**. Sigue arriba del umbral.

## 3. Los 3 hubs en propuesta — siguen en propuesta

1.215 divergencias; muestra 8: mejora 2 / neutral 1 / **regresión 5** (los mismos P1/P2 amplificados: vendedor-de-calle→cajero vía D07 de 5223.7; administrativos→4321.1 coordinador de inventario vía D07 de 4110.1; D02 de 5223.7 sigue sobre-disparando pese al re-modado — sus términos matchean en skills). Sin cambios de estado.

## 4. Recuperación (trad fuerza / baseline no): ya no es uniformemente buena

Muestra 13: mejora 6 («Jefe de contabilidad»→1211.1.1 ×2, inmobiliario→3334.2, teleoperador→5244.1), neutral 3, **regresión 4** — dos «Agente comercial» con tareas vacías de contenido («disponibilidad para viajar, actitud comercial») → **4110.1 empleado de oficina** vía D13, y un «Gerente de contabilidad»→4311.1 vía D05. D13 del hub 16 es sospechosa de matchear por skills genéricas — anotada para el barrido P2.

## 5. Hallazgos colaterales (registrados, sin acción improvisada)

1. **Gap «/a» en triggers del hub**: títulos escritos con barra literal («Ejecutivo/a comercial B2B») NO disparan los triggers del hub (el word-boundary no cruza la barra) — mismo género de variante que Cyn corrigió en las planas. Para fase 2 (o laudo chico: normalizar '/a' en `_norm` del trigger).
2. R190_auditor_interno y R69_analista_financiero: L3-por-derecho sin marca (P0) — el registro K de las validadas-IGUAL no dejó linaje.
3. Test de interacción K2 (pedido de Gerardo): limpio — exclusión seguros funciona, R210b/R210 se reparten bien, cero interacción con triggers del hub.

## 6. Recomendación

**NO-GO en este gate — y otra vuelta corta, no un rediseño.** La v0.3.2 demolió los mecanismos estructurales (−39% divergencias, −85% evidencia mixta, +13pp convergencia); el residuo son P1/P2/P3 + registro L3 incompleto: cuatro arreglos chicos, tres de ellos con laudo pendiente del harness y uno (L3-registro) ya laudado y solo administrativo. Secuencia propuesta:

1. Completar registro L3 con las validadas-IGUAL del K recomputadas (sin laudo nuevo — criterio ya firme).
2. Laudos P1 (satélite-puro), P2 (D 1-0 con inclusión en cero) y P3 (rama responsabilidad-integral de la prosa K2) → v0.3.3.
3. Re-shadow (4 min) + muestra nueva + matriz v3.

Con P0 saldado y P1+P2 laudados, 9-11 de las 15 regresiones muestreadas desaparecen por mecánica → la proyección de la v3 queda en zona del umbral (~13-20%). El gate no se fuerza: lo dirá la matriz v3.

---
*Datos: `H_p3_datos_shadow_v2_2026-08-18.json` + muestra clasificable `H_p3_muestra_v2_2026-08-18.txt`. Método idéntico a v1 (réplica baseline post-K2 + evaluador real inyectado); muestra con seed nueva e ids v1 excluidos.*
