# [CASCADA] Laudos de Cyn a las 4 fronteras → v12.5 + deltas sobre staging (2026-10-16)

Fuente: `exports/cyn_backlog/fronteras_v124_respuestas_2026-10-16.xlsx`. Aplicados ANTES del
P3. El shadow P3 corre sobre el staging YA neteado (laudo 1). Las 118K ya extraídas NO se
re-corren; los laudos 1-2 las corrigen por delta.

## Laudo 4 — v12.5 (prompt + gold + re-gate) ✅ HECHO
Compilados los 4 laudos al prompt (prosa textual + cita de hoja): seguridad (hoja 1),
contador "para+acción" (hoja 2), 5 veredictos (hoja 4). Gold re-adjudicado: **Turismo 5→7**
(coordinar+asegurar juntos, facturación en 3), **CNC −#7** (HSE sale). PM/C1/Asistente/Contador
ya estaban bien.

**Re-gate v12.5 (43 casos, 14b):**

| | v12.4 | **v12.5** |
|---|---|---|
| PASA | 29 | **33** |
| PASA-obs | 9 | 4 |
| REVISAR | 5 | 6 |
| cobertura | 94% | **96%** |
| precisión | 93% | **95%** |
| anti-alucinación | 12/12 | **12/12, 0 regr. ✅** |
| 6-OK | sin regr. | **sin regr. ✅** |

Los laudos SUBIERON el gate (cob 94→96, prec 93→95). 6 REVISAR = granularidad cerca del
umbral (C1 pares, C12/C24 Medifé, PM, Asistente, Minería), no fallas. Tests 16/16.

## Laudo 1 — netear HSE/compliance en staging ✅ HECHO
N3 ampliado (hoja 1): "cumplir norma/procedimiento/estándar de seguridad/higiene/ambiente" =
condición, no tarea, **independiente del oficio**. Guard de enforcement: "cumplir y **hacer
cumplir**", "verificar/controlar/supervisar el cumplimiento" se CONSERVAN (acción concreta).
- **2.975 filas neteadas · 3.160 ítems HSE removidos** (preservados en `tareas_json_pre_laudo1`
  + `laudo1_removidas_json` → reversible). Ejemplos: "cumplir con las normas GMP/seguridad/MA",
  "cumplir con los estándares de higiene de la cocina".
- El oro del CNC (2176458) corregido (−#7). **El P3 ya evalúa el input final.**

## Laudo 2 — delta contador "para+acción" ⏸ REPORTO EL TAMAÑO (espera tu OK)
Censo de vacías (n_tareas=0, 15.105) con patrón "para + acción" en contexto requisito/experiencia:
- **Candidatos: 1.965** (regex amplio) — más grande que "población chica".
- **Tasa de flip real ~1/3** (muestra 2/6): v12.5 extrae la función genérica solo cuando "para"
  atribuye función al puesto; cuando es propósito-de-requisito, correctamente deja [] (la
  distinción exacta del laudo). → ~**650 flips reales** esperados, el resto queda [] (sin daño).
- Costo: re-correr los 1.965 con v12.5 ≈ **~3 h** (seguro e idempotente; auto-discrimina).
- **Decisión tuya:** ¿corro los 1.965 (barato, v12.5 separa real de falso), o refino el filtro
  primero? Pre-autorizaste el delta pero pediste el tamaño antes — acá está.

## Laudo 3 — multipuesto inline (dimensionado) ⏸ TU/GERARDO DECIDE
Patrón inline en el corpus (119.081): "según el puesto/para cada posición" (150) + lista de
oficios en paréntesis "(X / Y / Z)" (490) = **638 avisos (0,54%)**.
- Es fix de PIPELINE (el detector multi-position hoy va por título). **NO bloquea el P3.**
- **Decisión de Gerardo:** ¿el detector inline entra ANTES del swap, o como delta POST-swap?
  Con 0,54% del corpus, cualquiera de las dos es de bajo impacto; Cyn pide separar (multipuesto
  explícito ≠ multioficio) — queda a criterio de timing.

## Turismo — "inconsistencia de conteo" (JD) — VERIFICADO
Era **real, no cosmética**: el oro de Turismo estaba en 5 y subcontaba el triple de facturación
("revisar itinerarios / actualizar costos / coordinar facturación" como 1). El laudo hoja 4 lo
puso en **7** (facturación en 3, coordinar+asegurar juntos). Gold corregido (5→7). Resuelto.

## Estado de la cascada
Re-extracción P1 **COMPLETA**: staging 119.081 (re-ext 98.168 + primeras 20.913), neteado por
laudo 1. Pendiente antes del P3: la decisión del laudo 2 (correr delta sí/no) — el laudo 3 no
bloquea. Luego: **punto de control P1-total** (censo + muestra 15 + sub-ofertas) → P2 → P3.
