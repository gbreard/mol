# Baseline F-meta cobertura ESCO post-C4

**Fecha:** 2026-05-10
**Tras:** C4 backfill flags ESCO (UPDATE 51s + commit 18s = 3m30s total)

## Métrica F-meta (SPEC §7.5)

| Métrica | Valor | Significado |
|---|---:|---|
| **cobertura_K1** | **74.87%** | % ofertas con ≥1 skill que es essential u optional para su URI ESCO |
| **cobertura_K3** | **38.03%** | % ofertas con ≥3 skills en catálogo de su URI |
| **cobertura_K5** | **14.49%** | % ofertas con ≥5 skills en catálogo de su URI |
| Avg skills en catálogo / oferta | 2.26 | promedio simple |
| n_ofertas | 54.774 | con `esco_occupation_uri != ''` |

## Distribución global de flags

| Filas con… | Cantidad | % del total | % de backfilleables |
|---|---:|---:|---:|
| `is_essential_for_occupation = 1` | **76.038** | 6.0% | 6.0% |
| `is_optional_for_occupation = 1` | **47.630** | 3.8% | 3.8% |
| Ambos en 0 | 1.145.201 | 90.3% | 90.3% |
| **Total filas** | 1.268.844 | 100% | — |
| Backfilleables | 1.268.705 | 99.99% | — |
| No backfilleables (URI vacía) | 139 | 0.01% | — |

## Discrepancia vs SPEC v3.1 §7.6

SPEC v3.1 estimaba ~784.000 filas en cero post-C4 (32.4% essential):
- 92.100 no-backfilleables + (0.676 × 1.023.911) = 784.263

Real:
- 139 no-backfilleables + (0.903 × 1.268.705) = 1.145.201
- **+360.938 filas en cero respecto a la estimación SPEC**

**Razón de la discrepancia:**
- Mucho mejor cobertura URI post-D + C1 (139 vs 92.100 esperadas no-backfilleables)
- Menos coincidencias skill↔catálogo de lo esperado: solo ~10% de skills extraídas son essential/optional según ESCO, no ~32%
- El extractor de skills v2.4 produce más skills de las que ESCO reconoce para la ocupación target

**Esto es información valiosa para SPEC W (H9 — ruido del extractor):** el dataset cuantificado disponible es ~1.14M skills extraídas que no caen en el catálogo ESCO de su ocupación target. Permite estudiar:
- Si esas skills son razonables pero ESCO no las incluye (catálogo incompleto)
- Si son ruido del extractor (skills falsas/genéricas)
- Si son skills de otras ocupaciones cercanas (drift)

## Validación Q3 (5 ocupaciones aleatorias)

Validado que `skills_essential_post_update ≤ skills_essential_catalogo` para las 5 ocupaciones sample. El backfill no genera skills más allá del catálogo. ✅

| Ocupación sample | Catálogo essential / optional | BD backfill essential / optional | OK |
|---|---|---|---|
| operador de trenzado textil | 12 / 2 | 4 / 0 | ✅ |
| operador de máquinas textiles | 17 / 1 | 1 / 0 | ✅ |
| profesor universitario de literatura | 32 / 46 | 3 / 1 | ✅ |
| ingeniero diseño herramientas | 28 / 24 | 2 / 0 | ✅ |
| presentador pronóstico tiempo | 12 / 11 | 0 / 0 | ✅ |

## Sample Q2 (10 ofertas con flags poblados)

Skills essential capturadas son conceptualmente coherentes con la ocupación ESCO:
- "Mecánico Automotriz" → `controles del automóvil`, `reparación de vehículos`
- "Chef" → `técnicas de cocina`, `preparación de alimentos`, `equipo de hostelería`
- "Bartender" → `servir bebidas`, `atención a clientes`, `equipo de hostelería`
- "Veterinaria" → `realizar diagnósticos veterinarios`
- "Asesor de ventas" → `responder a solicitudes de presupuesto`, `análisis de ventas`
