# SPEC S1C-G3 — Punto de control tras 3.c (las 48 SEM_LIBRE)

**2026-06-24, branch `spec/s1c-g3-cierre-loop`. Parar y reportar antes de las 15.**

Primer spec que toca procesamiento — primer cierre de loop del proyecto. Este es
el control obligatorio: ver el efecto real medido antes de seguir.

---

## Qué se hizo (commiteado, NO mergeado)

| Commit | Parte | Contenido |
|---|---|---|
| `33a37937` | Paso 0 (limpieza, no se mide) | borra `_find_occupation_uri` (muerto); `_get_esco_label_for_isco` falla ruidoso en vez de label arbitrario. MATCHER 3.5.5→3.5.6. |
| `d098b302` | Parte 3 (re-routeo + carga, se mide) | `_match_by_argentino_dict` resuelve por `esco_code` vía `code_to_occupation`; +6 denominaciones SEM_LIBRE TRAIN. MATCHER 3.5.6→3.5.7. |

Tests: 12 verdes (`test_s1c_g3_paso0_resolver.py` ×3, `test_s1c_g3_resolver_codigo.py` ×3, `test_spec_j_coherencia.py` ×6 sin regresión).

---

## Medición (3.c) — matriz de transición sobre el TEST reservado (93 ofertas)

Tres corridas read-only del matcher completo (`matcher.match()`), aislando cada cambio:

| Transición | Aísla | Ofertas que cambiaron URI | ISCO-4 |
|---|---|---:|---:|
| baseline → **paso0** | limpieza | **0** | 0 |
| paso0 → **full** | re-routeo + 6 entradas | **0** | 0 |
| baseline → full | total | **0** | — |

- **Paso 0 movió 0** — confirma lo previsto: el fallback estaba muerto (P.3: 0/3839). La limpieza no toca el camino de decisión. ✓
- **El re-routeo + las 6 entradas movieron 0 en el TEST.** Ni ganancia ni regresión.

**Por qué 0 (no es un fallo del mecanismo, es estructural):** **0 de 93** títulos del
TEST contienen alguna de las 6 variantes cargadas. Las denominaciones argentinas de
Cyn **no recurren** entre TRAIN y TEST — son casi-únicas por oferta. Una entrada de
diccionario TRAIN solo ayuda a un caso TEST si el mismo término reaparece; no reaparece.

---

## Las tres precisiones del reporte honesto

**1. Cargar ≠ medir.** Se evaluaron las 48 SEM_LIBRE; **cargables con URI real: 8 en
TRAIN** (de 35) — porque solo esos 8 tienen un `esco_code` capturado por el parser P.1
que resuelve en `code_to_occupation`. De esos 8 se **cargaron 6** (2 en HOLD, ver abajo).
Los 2 cargables en TEST **no se cargan** (TEST reservado, "NUNCA usado para generar nada").
La generalización se midió sobre los **13 SEM_LIBRE TEST**: 0 mejoraron, 0 empeoraron.
**Veredicto: no hay veredicto de generalización** — es prueba de mecanismo, no juicio,
y el resultado nulo es por dispersión de denominaciones, no por el mecanismo.

**2. Las 6 cargadas, por vía de resolución:** **6/6 por código** (alta confianza, token
inequívoco de Cyn). 0 por label. 0 a label arbitrario. El camino frágil (label) no se usó.

**3. Conflicto regla–diccionario:** N/A — 0 regresiones, no hubo nada que atribuir.

---

## Prueba de mecanismo (las 6 ofertas-fuente TRAIN, `matcher.match()` completo)

El loop cierra end-to-end sobre las ofertas que Cyn corrigió:

| Oferta-fuente | método | → ISCO / ESCO (target de Cyn) |
|---|---|---|
| project control manager | `diccionario_argentino_*` | 1330 · gestor de proyectos de TIC |
| editor de videos | `diccionario_argentino_*` | 2654 · editor de cine y televisión |
| intendente de obra | `diccionario_argentino_*` | 5153 · conserje de edificio ⚠ |
| asistente de ingeniería jr | `diccionario_argentino_*` | 3119 · ingeniero técnico industrial |
| líder de mantenimiento de flota | `diccionario_argentino_*` | 7231 · supervisor mantenimiento vehículos |
| oficial armador | `diccionario_argentino_*` | 8219 · montador de productos metálicos |

Las 6 resuelven por `esco_code` a la URI exacta que Cyn citó. **El mecanismo funciona.**

---

## Decisiones por caso (8 cargables TRAIN → 6 cargadas, 2 en HOLD)

El punto de control sirvió para esto: un dry-run de match-count destapó riesgos.

| Caso | match en BD | Decisión | Motivo |
|---|---:|---|---|
| operario de produccion → 8160 (alimentos) | **72** | **HOLD** | variante genérica de toda industria; forzaría 71 ofertas no-alimentarias a "producción de alimentos". Requiere scope de Cyn. |
| estudiantes…pasantía stellantis 2026 → 2421 | 2 | **HOLD** | título de aviso de un caso, no denominación recurrente; no generaliza. |
| intendente de obra → 5153 (conserje) | 1 | **CARGADA + flag** | mapeo semánticamente dudoso (obra→conserje), pero es la corrección de Cyn; blast radius 1. |
| otras 5 | 1–9 | **CARGADA** | denominaciones angostas y plausibles. |

Ninguna se cargó a label arbitrario; ninguna a URI inventada. Los HOLD quedan
registrados en `notas` del diccionario.

---

## Reencuadre del techo (corrige la NOTA de descubrimiento)

La NOTA estimó 11→37 alcanzables con URI integrando el mapa por código. **Real con el
ground-truth P.1: solo 14 de 63** tienen `esco_code` capturado (12 TRAIN + 2 TEST), todos
resuelven. La diferencia con el 37 es **recall de extracción de código**: el parser P.1
fue conservador (solo headers positivos + guarda de coherencia). Los ~23 códigos extra que
la NOTA contó salen de un regex más amplio sobre el texto libre, sin la guarda. Subir ese
recall (con validación, sin inventar) es una decisión aparte — no se hizo aquí.

---

## Lo que NO se tocó (deuda registrada, no resuelta)

- **Fallback label-LIKE de reglas** (`_resolve_rule_target`, `match_ofertas_v3.py:1314-1318`):
  único resolver-por-label silencioso VIVO y a escala. Es el canal de reglas (Eje 4), no G3.
  **P-01 reubicada**: el riesgo de resolución-por-label arbitraria migró del diccionario
  (ahora muerto) a las reglas (vivo). Ítem de arranque del Eje 4, junto a los override-duro.

---

## La pregunta para Gerardo (decisión del punto de control)

1. **¿Avanzo a las 15 DICC_YA?** (4 cargables por código en TRAIN, 1 en TEST; mismo método,
   riesgo medio porque pueden mover casos que hoy aciertan por casualidad.)

2. **Más de fondo — ¿es la generalización-en-TEST la métrica correcta para G3?** El
   resultado nulo dice que las denominaciones de Cyn no recurren entre ofertas. El valor
   de cerrar el loop acá **no es** que un caso TEST mejore por una corrección TRAIN; **es**
   que el diccionario acumula las correcciones de Cyn y las aplica cuando el término
   reaparece en producción (carga futura completa, incluido TEST, ya validado el loop).
   Si se acepta eso, el éxito de G3 se mide por "mecanismo verificado + entradas que
   resuelven por código", no por movimiento en un hold-out — y conviene decidir si
   subir el recall de extracción de código (para pasar de 6 a ~30+ entradas cargables)
   es el próximo paso antes que las 15.

**No avanzo a las 15 ni mergeo hasta tu OK.**
