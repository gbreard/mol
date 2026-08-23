# SYNC CONSOLIDADO v2 — PRE-REPORTE de volumen (2026-08-23)

**PUNTO DE CONTROL: nada de esto se ejecuto.** Numeros contra el snapshot
pre-rematching (2026-08-19) con la BD local de hoy.

| Poblacion | Ofertas |
|---|---|
| A. Cambiadas (re-matching: destino/campos dashboard distintos) | 76,857 |
| B. Nuevas (backlog NLP posterior al snapshot) | 20,071 |
| C. Skills cambiadas (set difiere) | 39,246 |
| **Upserts ofertas_dashboard (A∪B)** | **96,928** |
| **Ofertas con reemplazo de skills (C∪B)** | **59,317** (1,805,285 filas) |

**Requests estimados:** 970 batches de ofertas (x100) + 118,634
requests de skills (delete+insert por oferta) ≈ **119,604 requests**.
**Duracion estimada** al rate configurado (sleep 1.0s/batch, 0.25s/oferta-skills):
**~263 min** — multiplicar x2-3 para presupuestar (historial de estimaciones cortas).

Ejecucion SOLO tras OK de Gerardo, en horario valle (fuera de 09-21 ART):
`python scripts/ops/sync_consolidado_v2.py --ejecutar --aprobado-por-gerardo`
