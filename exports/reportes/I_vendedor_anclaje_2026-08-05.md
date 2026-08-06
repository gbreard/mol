# [FRENTE I — P3] Re-medición del anclaje léxico de vendedor — 2026-08-05

## Resultado

Con los términos de la **prosa REAL** de las reglas 16 (representante comercial 3322.1),
51 (vendedor 5223.4) y 52 (vendedor especializado 5223.7) del JSON 2.0 — 47 frases
extraídas de sus `tareas_definitorias` (las tres llegan en modo semántico, `terminos`
vacíos):

| Medición | Anclaje |
|---|---|
| **6,2% previo** (2-3 términos del prompt) | referencia |
| **ESTRICTO** (47 frases de la prosa real) | **44,9%** (3.470/7.732) |
| AMPLIO (+ raíces venta/vender/comercializ) | 81,8% (6.325/7.732) |

Universo: 7.732 ofertas familia-vendedor del corpus (head del título) con tareas
evaluables (>30 chars).

## Lectura (según el criterio pre-fijado)

**El 6,2% era artefacto del léxico incompleto. Vendedor SIGUE EN EL PILOTO sin más** —
44,9% cae en la banda 40-50% que el criterio marcaba como "sigue sin más".

## El hallazgo accionable para el compilador

Los sin-anclaje-estricto son mayormente **parafraseos flexionales** de las mismas
tareas, no vocabulario ajeno: «identificar **las** necesidades **de los clientes**» no
matchea «identificar necesidades»; «**Asesorar** a los clientes» no matchea «brindar
asesoramiento»; «venta directa al público» no matchea «concretar ventas». → **La
propuesta de términos del spec H (P2) debe generar variantes flexionales y
paráfrasis-cercanas por término, no frases literales** — el anclaje real con eso está
entre el 44,9% y el 81,8%. El vocabulario de variantes NO necesita trabajarse antes del
shadow como pre-requisito; se trabaja DENTRO del propositor de términos.
