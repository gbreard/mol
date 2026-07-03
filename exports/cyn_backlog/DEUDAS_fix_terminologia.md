# Deudas registradas — fix veneno terminologia (2026-07-03)

El fix cortó el grifo del café verde de skills. Estas deudas quedan pendientes (NO se resuelven acá).

## D1 — La pileta (residuo histórico persistido)
- **36.809 filas** con URI fabricada persistidas en **~15.986 ofertas** (`ofertas_esco_skills_detalle`), de las cuales 30.402 filas / 12.841 ofertas con `skill_tipo_fuente='terminologia'`.
- El fix corta el **grifo** (terminologia vaciado, skills_rules limpio, semántico solo emite catálogo+desync), **no vacía la pileta**.
- **Pendiente:** limpieza/reproceso de esas ofertas. **Coordinar con el candado F0.4b — NO reprocesar acá.**

## D2 — Observabilidad: la columna que miente (→ índice del harness)
- `ofertas_esco_skills_detalle.match_method` está **hardcodeado a `'implicit_bge_m3'`** para toda skill (`match_ofertas_v3.py:save_skills_detalle`), y `origen_tipo` sale `'semantico'` casi siempre. El **origen real** vive en `skill_tipo_fuente`.
- Esto casi produce un **diagnóstico falso**: la primera medición de blast-radius dio "0 terminologia" por consultar `origen_tipo`/`match_method` en vez de `skill_tipo_fuente`.
- **Pendiente:** dejar de hardcodear el método / documentar cuál columna es la fuente de verdad de origen. **Va al índice del harness** — cualquier medición futura que se apoye en `match_method`/`origen_tipo` vuelve a morder.

## D3 — Desync catálogo/embeddings (SY-02, ahora medido)
- El índice de embeddings tiene **14.257** URIs; la tabla SQLite `esco_skills` tiene **14.247**. **10 URIs reales** que el semántico puede emitir pero fallan el JOIN a `esco_skills` (label vacío en la persistencia).
- No es fabricación — es **drift silencioso** (el que la auditoría anticipó como SY-02). Acá queda **cuantificado: 14.257 vs 14.247 = 10**.
- **Pendiente:** reconciliar embeddings ↔ `esco_skills`. Vinculado a **SY-02**.

## D4 — skills_rules es first-match-wins (limitación de canal)
- `SkillsRulesMatcher.evaluate` aplica **una sola regla por oferta** (retorna en el primer match). terminologia era **aditivo** (PASO 0, siempre emitía); skills_rules es **exclusivo-primer-match**.
- Consecuencia: una oferta que matchea una regla anterior (p.ej. `RS21_almacen_deposito` por "deposito") **no recibe** las skills de una regla logística posterior migrada (p.ej. `RS28_picking`). Medido en el TEST: **1 de 18 ofertas** sombreada (7347150394). Efecto **benigno** — el semántico cubre el concepto (surfacea "preparar los pedidos para el envío", hermano de "preparar pedidos").
- **Pendiente (no acá, respeta "no tocar las 27 reglas"):** decidir si las reglas de skills deben **acumular** varias coincidencias en vez de first-match-wins, o fusionar las logísticas en una regla-familia.
