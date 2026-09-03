# MINI-SPEC — Verificación de bajas CT por presencia en el buscador

**Fecha:** 2026-09-03 · **Rama:** `spec/ciclo-vida-ofertas` · **Estado:** BORRADOR — no implementar hasta aprobación.
**Origen:** decisión Gerardo 2026-09-02 (Fase 4). Complementa `SPEC_ciclo_vida_ofertas.md`.

## 1. Por qué

Opción A (activa) deja el middle `listado_seo` como **ambigua indefinidamente**: honesto pero deja
~78% de la cola CT sin poder confirmar baja. La causa medida en Fase 4: **el HTML de detalle de CT
es mentiroso para existencia** — sirve la ficha SEO (con `<title>` "Trabajo de…") también para avisos
**expirados**, así que ni la extracción (option-B: 5,3% vivas, sobre-caída) ni el título (existencia:
86% vivas, sobre-viva) discriminan bien. La curva medida (~20-25% en la franja) refuta a ambos.

**Señal genuina propuesta: presencia en el BUSCADOR de CompuTrabajo** (la maquinaria del PASO 1 del
scraper), **no** el re-fetch del detalle. Mismo principio que `searchV2` en Navent, que en Fase 4 dio
**0 ambiguas en 4.750** y distribución consistente con la curva: *si el aviso está indexado en la
búsqueda, existe; si el buscador devuelve resultados y no está, cayó.*

## 2. Vía

- **Buscar por título** en el buscador HTML de CT (reusar la maquinaria de listado del PASO 1 —
  `ComputRabajoScraper`, búsqueda por keyword), no el detalle.
- **Mapear id**: el buscador expone `data-id`; `id_oferta = 5_000_000_000 + data-id`. Se compara
  contra el `id_oferta` objetivo.
- **Clasificación** (espejo de searchV2):
  - `id` presente en los resultados → **viva**
  - resultados > 0 y sin el `id` (bajo el tope) → **caída**
  - 0 resultados → **caída** (caso fuerte)
  - tope alcanzado sin el `id` → **ambigua** → reintento con query más específica (título completo /
    + empresa / + localidad); si persiste, no cuenta.
- **2 verificaciones ≥72 h** para confirmar (igual que Navent) — mitiga falsos "caída" por
  des-indexado temporal.
- Pacing conservador + circuit-breaker (el buscador de CT puede rate-limitar como el scraping);
  `ConnectionError` → backoff (ya endurecido en el verificador).

## 3. Micro-gate CONTRA LA CURVA antes de activar (obligatorio)

Aprendizaje de Fase 4: un micro-gate que sólo mira "clasifica limpio" **no alcanza** (el discriminador
de existencia pasó 30/30 y aun así estaba mal). El gate debe contrastar contra la **curva medida**:
- Muestra **representativa** (aleatoria) de la franja `[63d, 126d]`, ~150 casos, clasificados por la
  vía nueva.
- **Debe dar ~20-25% vivas** (no 5%, no 86%). Si cae en esa banda → la vía es sólida → activar para CT.
- Reportar por señal cruda (id-presente / n_resultados) para auditar, como en Navent.

## 4. Recalibración obligatoria si la vía nueva funciona

⚠️ **La curva CT actual (95% / 56% / 7% a 1/2/3 meses) se midió con la SEÑAL DÉBIL** (drenaje
28-08/01-09, que usó `agotado_listado`/extracción como "caída"). Esa señal **sobre-cuenta caída**
(mata avisos vivos-inparseables), así que la **curva CT está sesgada hacia baja supervivencia**. Por lo tanto:

1. **Re-medir la curva CT** con la vía buscador (la señal genuina). Es esperable que la supervivencia
   real sea **mayor** que la medida (los vivos-inparseables vuelven a contar como vivos).
2. **Re-derivar el umbral `presunta_baja` de CT** (hoy **63 d**, calibrado sobre la curva débil) con la
   curva corregida. Probablemente **suba** (CT viviría más de lo que la señal débil sugería).
3. Actualizar `config/scraping/ciclo_vida_ofertas.json` (umbral CT) y documentar el cambio de curva.

Hasta recalibrar, el umbral 63 d queda como está (conservador-hacia-presunta, no confirma de más).

## 5. Riesgos / decisiones abiertas

- El buscador de CT podría **no indexar** todos los avisos vigentes (falsos "caída"); mitigado por las
  2 verificaciones y por el reintento de query. Medirlo en el micro-gate (¿cuántas vivas conocidas no
  aparecen?).
- Bloqueo/rate-limit del buscador desde la IP local: pacing + tope diario + circuit-breaker.
- ¿La búsqueda por título es suficientemente selectiva en CT (como lo fue en Navent, mediana 0
  resultados en caídas)? Verificar en el micro-gate.

## 6. Alcance

Redacción solamente. **No implementar hasta aprobación de Gerardo.** Al aprobar: implementar la vía +
micro-gate-contra-curva; si pasa, activar CT + recalibrar curva/umbral como una tarea propia.
