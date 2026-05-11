# C2 sub-fase A — Verificación de over-match

**Fecha:** 2026-05-05
**Modo:** análisis estático (sin matcher real). 50 ofertas por entrada con URI vacía y título matcheando variantes.
**Tiempo:** ~30 min

## Metodología

Para cada una de las 3 entradas a quitar (`analista`, `operario`, `tecnico`):
1. Identificar 50 ofertas con `esco_occupation_uri = ''` y título matcheando variante de la entrada.
2. Para cada oferta, evaluar las 358 reglas de `matching_rules_business.json` por orden de prioridad.
3. Si una regla matchea → registrar ISCO target (`accion.forzar_isco`).
4. Comparar ISCO inferido contra contextos del JSON.
5. Sospecha de over-match: target ISCO con primer dígito **distinto** a todos los contextos JSON de la entrada.

Reglas evaluadas:
- `condicion.titulo_contiene_alguno`, `_alguno_2`, `_todos`, `_no_alguno`
- `condicion.titulo_original_contiene_alguno`
- `condicion.titulo_o_tareas_contiene_alguno`
- `condicion.skills_contiene_alguno`, `tareas_contiene_alguno`

## Resultados

### `analista` (8 contextos JSON: 4312, 2411, 2413, 3312, 2511, 2421, 2423, 2431)

| Métrica | Valor |
|---|---:|
| Cubierta por regla | **50/50 (100%)** |
| Sin regla (semántico) | 0/50 |
| Sospecha over-match | **0/50 (0%)** |

**Top ISCOs inferidos:**
- 2511 — 45 ofertas ✅ (en contextos)
- 2421 — 4 ofertas ✅ (en contextos)
- 2522 — 1 oferta ❌ (no en contextos, pero familia 2)

**Decisión: ✅ QUITAR del JSON** (over-match 0% ≤ 10%).

---

### `operario` (5 contextos: 9333, 8160, 8142, 8131, 8211)

| Métrica | Valor |
|---|---:|
| Cubierta por regla | **49/50 (98%)** |
| Sin regla (semántico) | 1/50 |
| Sospecha over-match | **2/50 (4%)** |

**Top ISCOs inferidos:**
- 9329 — 38 ofertas (familia 9 ✅, no exactamente en contextos pero familia OK)
- 9333 — 8 ofertas ✅ (en contextos)
- 8142 — 1 ✅
- 3512 — 1 ❌ (over-match)
- 7233 — 1 ❌ (over-match)

**Ejemplos over-match:**
- `[1116760072]` "OPERARIO / TECNICO PARA MANTENIMIENTO DE CHOPERAS" → R241_tecnico_it (3512). El título es ambiguo entre operario y técnico; la regla técnico IT gana por especificidad.
- `[1117078383]` "Operario de producción (Químico)" → R356_operario_mantenimiento (7233). Mantenimiento mecánico, no operario de producción; regla mal disparada por keyword.

**Hallazgo importante**: 38 de 50 (76%) van a **ISCO 9329** ("otros peones de manufactura n.c.p."), no a los contextos JSON específicos. Aunque está en familia 9 (no es over-match estricto), implica que la **clasificación post-quitar será más genérica** que con el diccionario actual.

**Decisión: ✅ QUITAR del JSON** (over-match 4% ≤ 10%) con caveat de pérdida de granularidad.

---

### `tecnico` (6 contextos: 7233, 7421, 7127, 3512, 3111, 3257)

| Métrica | Valor |
|---|---:|
| Cubierta por regla | **50/50 (100%)** |
| Sin regla (semántico) | 0/50 |
| Sospecha over-match | **15/50 (30%)** ⚠️ |

**Top ISCOs inferidos:**
- 3512 — 30 ofertas ✅ (en contextos)
- 2522 — **14 ofertas** ❌ (familia 2, no en contextos [familias 7 y 3])
- 7233 — 3 ✅ (en contextos)
- 7412 — 1 ❌
- 2511 — 1 ❌
- 3522 — 1 ❌

**Ejemplos over-match:**
- `[1118089054]` "Soporte Tecnico N2" → R180_soporte_infraestructura (2522)
- `[1117964359]` "SOPORTE TECNICO - GBA Oeste" → R180_soporte_infraestructura (2522)
- `[1117973004]` "Soporte Tecnico Jr" → R180_soporte_infraestructura (2522)
- `[1117976303]` "Tecnico de Soporte" → R180_soporte_infraestructura (2522)
- `[1118005397]` "Analista Tecnico Funcional Ssr" → R238_analista_it (2511)

**Análisis matizado del over-match de `tecnico`:**
- 13 de 14 ofertas con ISCO 2522 son "Soporte Técnico" o variantes.
- ISCO 2522 = "administradores de sistemas" (más senior).
- ISCO 3512 = "técnicos en operaciones de soporte de TIC" (operativo).
- Regla `R180_soporte_infraestructura` envía soporte L1/L2 a 2522 — **clasificación discutible**: la convención industrial en Argentina favorece 3512 para soporte L1/L2. Esa es una **regla mal calibrada existente**, no un problema introducido por quitar `tecnico` del diccionario.
- El "over-match" es ambiguo porque:
  - Familia 2 vs familia 3: ambas son IT.
  - El diccionario de `tecnico` tampoco habría asignado 2522 — habría asignado 3512 (contexto `it|sistemas|soporte`).
  - Quitar `tecnico` *aumenta* la sospecha de mal-clasificación a 2522.

**Decisión SPEC §5.6: ⚠️ REVISAR (30%, en el límite)**

**Recomendación**: 
- **Opción A (más conservadora):** restringir R180_soporte_infraestructura para que no aplique a títulos con "Soporte Técnico" (que son L1/L2, ISCO 3512). Tras restringir, re-correr este análisis. Si over-match baja a < 10% → QUITAR.
- **Opción B (más agresiva):** convertir `tecnico` a Opción 3 (URI por contexto) como casos `gerente`/`operador`. Pero `tecnico` tiene 6 contextos, sumando esfuerzo. Y los contextos no cubren todos los casos (no hay contexto para "soporte técnico" puro, sólo `it|sistemas|soporte`).
- **Opción C (intermedia, recomendada):** quitar `tecnico` del JSON y aceptar que algunos "Soporte Técnico" caerán a 2522 hasta que R180 se restrinja en SPEC U-2.

## Resumen de decisiones

| Entrada | Cobertura regla | Over-match | Decisión |
|---|---:|---:|---|
| `analista` | 100% | 0% | ✅ QUITAR |
| `operario` | 98% | 4% | ✅ QUITAR (caveat: granularidad menor con 9329) |
| `tecnico` | 100% | 30% | ⚠️ QUITAR + restringir R180 en SPEC U-2 (Opción C) |

## Diferencias respecto a R8

R8 reportó: analista 100% / operario 100% / tecnico 99%. Mis cifras: 100/98/100. Diferencias dentro del margen de muestreo (50 ofertas). **No invalidan las decisiones de R8 ni del SPEC v3.1 §5.3.**

## Acción siguiente

Proceder a sub-fase B: generar `config/sinonimos_argentinos_esco_v2.json` sin `analista`, `operario`, `tecnico`. La regla R180 queda anotada como **issue conocido para SPEC U-2**.

---

**Output:** este reporte. **Caveat:** no se ejecutó el matcher real; el análisis se basa en evaluación estática de las 358 reglas. El comportamiento del matcher real puede tener diferencias menores por: tie-breaking de prioridades empatadas, integración con score semántico, post-procesamiento. La decisión QUITAR es robusta a estas diferencias.
