# DATA RELEASE — Corpus MOL 2026-08-22

Nota de release para consumidores del corpus (harness, dashboard, proyectos externos). Se actualiza en cada release grande; los releases futuros (sync consolidado v2, K4) referencian y reemplazan esta nota.

## Versión

| Componente | Versión |
|---|---|
| Matcher | **3.6.0** (traductor contextual en producción desde 2026-08-19) |
| Reglas de negocio | `matching_rules_business.json` **v5.32** (370 históricas 100% auditadas por experta en 3 rondas: 33 retiradas, ~135 destinos corregidos; 407 entradas con altas de splits) |
| Léxico del traductor | `lexico_traductor.json` **v0.4.0** (88 reglas contextuales de Cyn, 7 hubs) |
| NLP | v11.3.1 (qwen2.5:7b, source-aware) |
| Merge de referencia | `87da0330377ed9fd...` (PR #64, main 2026-08-22) |

**Cómo citar:** *Corpus MOL, release 2026-08-22 (matcher 3.6.0 / reglas v5.32 / léxico v0.4.0, merge 87da0330).* Cada oferta lleva `matching_version` — filtrar `LIKE '3.6%'` para quedarse solo con decisiones de esta generación.

## Censo (corte 2026-08-22 17:16, BD local)

| Población | N |
|---|---|
| Ofertas totales scrapeadas (6 portales, desde 2025) | **112.809** |
| Con NLP completo (20 campos) | **96.609** |
| Con matching de ocupación | 92.640 — de las cuales **86.301 (93%) con matcher 3.6.x** |
| Título-only / inertes (sin descripción utilizable, ≤100 chars; nunca tendrán NLP) | 14.580 |
| Validadas por humano (`validado`/`validado_humano` — intocables por reprocesos) | **6.275** |
| Filas de skills (detalle por oferta) | 2.704.975 |

## Calidad por canal de decisión (distribución post re-matching masivo)

El 2026-08-20/22 se re-decidió TODO el corpus histórico con la versión actual (frente L): 44,4% cambió de destino (54% de ese cambio = auditoría experta materializada). Sobre las re-matcheadas:

| Canal | % | Qué es |
|---|---|---|
| Semántico | 36,7% | Embeddings BGE-M3 skills+título; el fallback cuando ningún conocimiento curado aplica |
| Regla plana | 31,5% | Regla de negocio auditada por Cyn que fuerza el destino ESCO |
| Diccionario argentino | 14,0% | Denominación local validada → ESCO exacto (225 entradas, la vía más confiable) |
| Regla L3 | 8,5% | Regla que precede al traductor (registro L3, específica y validada) |
| Regla subordinada | 5,3% | Regla que cede al traductor cuando éste decide (subordinación L4) |
| Árbol / traductor | 4,0% | Modelo contextual de Cyn: decide-cuando-decide leyendo señales del aviso |

Jerarquía de confianza sugerida para consumidores: dict ≈ L3 > árbol > regla plana/subordinada > semántico (usar `occupation_match_score` dentro del canal semántico).

## Campos disponibles por oferta

- **Ocupación:** `esco_occupation_uri/label`, `titulo_esco_code`, ISCO derivado (`isco_code/label`, niveles 1-2), `occupation_match_score`.
- **Traza completa de la decisión:** `occupation_match_method` (canal), `regla_aplicada`, `decision_metodo`, `decision_razon` (tags de telemetría), dual (`isco_semantico`, `isco_regla`, `dual_coinciden`), árbol (`arbol_hub_id`, `arbol_regla_id`, `arbol_camino`, `arbol_traza_json`), `matching_version`, `run_id`.
- **Skills:** tabla detalle por oferta — skill mencionada (texto original), URI+label ESCO, tipo/fuente (explícita/implícita), scores, esencial/opcional para la ocupación, clasificación L1/L2 y `es_digital`.
- **NLP (20 campos):** título limpio, tareas explícitas, misión, área funcional, seniority, sector+CLAE, ubicación normalizada (provincia/localidad/departamento INDEC), modalidad, contrato, educación, experiencia, listas de skills/tecnologías/herramientas, linaje multi-posición (`parent_id_oferta`/`es_suboferta`).
- **Scraping:** portal, fechas (publicación/scrapeo/último visto), permanencia, republicaciones, estado.

## Salvedades (leer antes de consumir)

1. **Capa 11-18/08 completándose:** el backlog NLP de ofertas scrapeadas ~11-18/08 corre en estos días; al corte quedan ~2.100 procesables sin NLP (además de las 14.580 inertes). El censo crece unos puntos hasta que cierre.
2. **Inertes censadas:** las 14.580 sin descripción utilizable (mayormente ComputRabajo/walls de Cloudflare) cuentan como oferta publicada pero no tienen NLP/matching — excluirlas de análisis de contenido, son válidas para conteos de publicación.
3. **Huecos de scraping conocidos:** Indeed con bloqueos Cloudflare intermitentes (corridas en cero); CABA/Portal Empleo congelados por bug de watermark en jun/2026 (backfill aplicado); julio/2026 procesado en lote diferido. Para series temporales, validar cobertura mensual por portal antes de comparar meses.
4. **13 ofertas con matching pre-3.6** en estados de revisión humana intermedia (protegidas por diseño, documentadas en el cierre del frente L).
5. **El dashboard público aún refleja el estado pre-re-matching:** el sync está diferido por presupuesto I/O de Supabase y corre consolidado con el cierre del backlog (script preparado con punto de control previo). Hasta entonces, BD local ≠ dashboard.

**Referencias:** medición completa `exports/reportes/L_p3_medicion_2026-08-22.md` · cierre `L_cierre_2026-08-22.md` · snapshot reversible `exports/cohorts/snapshot_pre_rematching_2026-08-19_*`.
