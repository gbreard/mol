# Micro-gate CT (vía buscador) — resultado 2026-10-08

**Rama:** `fix/verificador-computrabajo` · **Spec:** `SPEC_ct_verificacion_busqueda.md`
**Estado:** GATE NO PASA → **NO activar** (decisión de iterar/holdear es de Gerardo).

## Qué se corrió
Vía nueva (presencia en el buscador de CT, id derivado de la URL como la BD),
sobre muestra aleatoria de 150 de la franja [63,126]d de CT presunta_baja (11.333
en la franja), dry-run, lock-aware, circuit-breaker.

## Bug encontrado y corregido durante el gate
1ª corrida dio **0% vivas** (falso). Causa: el `data-id` del buscador es HEX y
**cambia según el keyword** (bug CT conocido 2026-03-11); el id de BD se deriva de
`5e9 + crc32(slug-URL-sin-hash32)`. La vía comparaba por data-id → 0 matches.
**Fix:** derivar el id de la URL de cada resultado con `computrabajo_id_to_int`.

## Resultado con id corregido
| métrica | valor |
|---|---|
| %vivas sobre decididas (viva/(viva+caída)) | **13,2%** (objetivo 20-25%) |
| viva / caída / ambigua | 12 / 79 / 59 |
| ambiguas | 39,3% (tope_alcanzado) |
| n_resultados buscador | min 0 · mediana 21 · max 40 |

**Control de ground-truth (25 CT `activa`, scrapeadas hoy = vivas seguras):**
22/25 detectadas viva, **3/25 = 12% FALSA-CAÍDA**, 0 ambiguas. Los 3 fallos son
títulos con ruido de ubicación ("Zona Zárate", "Exaltación de la Cruz", "por la
Zona de…") cuyo slug no matchea en el buscador.

## Lectura
- El 13,2% está **por debajo** de la banda → el gate, como está, dice NO activar.
- Pero está **sesgado hacia abajo** por el 12% de falsa-caída medido contra
  ground-truth: la query por slug **no surfacea** ~12% de ofertas vivas (devuelve 0
  o resultados ajenos), así que cuenta vivas como caídas. La supervivencia real de
  la franja es probablemente mayor que 13,2%; parte de la brecha con la banda es
  artefacto de la query, no de la realidad.
- ⚠️ La falsa-caída es **sistemática** (el slug siempre falla para ese título) →
  las 2 verificaciones ≥72h **no la mitigan** (ambas darían caída → confirma baja
  de una oferta viva). Es el riesgo más serio.
- 39% de ambiguas (tope) también es alto: gran parte de la cola quedaría sin confirmar.

## Opciones (decisión de Gerardo)
1. **Iterar la query (recomendado si se quiere CT):** construir el query con
   keywords de TÍTULO limpias (quitar ubicación/cualificadores "zona X", "por la
   zona de…", paréntesis), o usar el parámetro de búsqueda `?q=` en vez del slug de
   ruta; bajar la falsa-caída (<~5%) y la ambigüedad contra el control de
   ground-truth, y RE-correr el gate. Recién si cae en banda → activar + recalibrar
   curva/umbral (§4 de la spec).
2. **Holdear:** dejar CT en `extraccion_A` (actual), con las 19.357 presuntas sin
   confirmar, hasta invertir en (1).
3. **Abandonar** la vía buscador para CT.

## Estado del código
Implementación + 10 tests + micro-gate en la rama (`963ec1f3`). **Config SIN tocar
(`extraccion_A`)** → nada activado. Cron NO modificado. No mergeado a main.
