# MOL - Monitor de Ofertas Laborales

## Descripcion
Sistema de monitoreo del mercado laboral argentino para OEDE. Scrapea ofertas de empleo, extrae informacion con NLP, clasifica segun taxonomia ESCO, y provee dashboards para analistas.

## Estado Actual (2025-12-07)
- 9,564 ofertas en BD
- 10,223 IDs en tracking
- 89% cobertura de scraping
- NLP v8.0 (~90% precision)
- Matching v8.3 (78.9% precision)

## Documentacion

| Documento | Descripcion |
|-----------|-------------|
| `docs/MOL_CONTEXT_MASTER.md` | Contexto completo del sistema |
| `docs/MOL_LINEAR_ISSUES_V3.md` | Issues pendientes con specs detalladas |
| `docs/MOL_CLAUDE_CODE_PROMPT.md` | Resumen rapido para inicio de sesion |
| `docs/SISTEMA_VALIDACION_V2.md` | Arquitectura de validacion |
| `docs/DASHBOARD_WIREFRAMES.md` | Disenos de UI |
| `docs/SCRAPERS_INVENTARIO.md` | Inventario de scrapers |
| `docs/NLP_SCHEMA_V5.md` | Schema de campos NLP |

## Comandos Clave

```bash
# Scraping (SIEMPRE usar este, NUNCA bumeran_scraper.py directo)
python run_scheduler.py --test

# Test Matching
python database/test_gold_set_manual.py

# Dashboard Admin (cuando este creado)
streamlit run dashboards/admin/app.py

# Linear - Sincronizar cache
python scripts/linear_sync.py

# Linear - Actualizar issue (no bloqueante)
python scripts/linear_update_async.py MOL-XX --status=done --comment="..."
```

## Modelos LLM/ML Activos

| Modelo | Tipo | Uso |
|--------|------|-----|
| **Qwen2.5:14b** | LLM | NLP: extraccion semantica (30% campos) |
| **BGE-M3** | Embeddings | Matching: titulo (50%) + descripcion (10%) |
| **ESCO-XLM-RoBERTa-Large** | Re-ranker | Re-ranking candidatos ESCO |
| **ChromaDB** | Vector DB | Skills lookup (40%) |

**Requisitos:**
- Ollama en `localhost:11434` con `qwen2.5:14b`
- ChromaDB con vectores en `database/esco_vectors/`
- `sentence-transformers` para BGE-M3
- `transformers` para ESCO-XLM-RoBERTa

**Pipeline NLP:** Regex (70%) -> Qwen2.5 (30%) -> Anti-alucinacion
**Pipeline Matching:** Titulo (50%) -> Skills (40%) -> Descripcion (10%) -> Validacion

## Linear (Sistema No Bloqueante)

### Configuracion inicial (1x)
1. Crear `config/linear_config.json` con tu API key
2. Ejecutar: `python scripts/linear_sync.py`

### Flujo de trabajo

**INICIO DE SESION:**
```bash
python scripts/linear_sync.py
# Sincroniza issues de Linear a .linear/issues.json
```

**LEER CONTEXTO DE UN ISSUE:**
- Leer specs de `docs/MOL_LINEAR_ISSUES_V3.md`
- Leer estado de `.linear/issues.json`
- NUNCA usar MCP de Linear (bloquea)

**ACTUALIZAR ISSUE (no bloqueante):**
```bash
python scripts/linear_update_async.py MOL-XX --status=done --comment="Completado"
# Retorna inmediato, Linear se actualiza en background
```

**MULTIPLES UPDATES:**
```bash
python scripts/linear_queue.py add MOL-31 --status=done
python scripts/linear_queue.py add MOL-32 --status=done
python scripts/linear_queue.py process  # Al final de la sesion
```

## Reglas de Desarrollo

1. **Scraping:** SIEMPRE usar `run_scheduler.py`, NUNCA `bumeran_scraper.py` directo
2. **Tests:** Todo cambio en NLP/Matching debe pasar gold set
3. **Umbrales:** NLP >= 90%, Matching >= 95%
4. **S3:** Experimentos van a `/experiment/`, produccion a `/production/`
5. **UI:** Dashboard produccion SIN siglas tecnicas (CIUO, ESCO)
6. **Linear:** Usar sistema de cache, NUNCA MCP directo

## Estructura del Proyecto

```
MOL/
├── 01_sources/bumeran/scrapers/    # Scrapers
├── database/                        # BD, matching, tests
├── nlp/                            # Pipeline NLP
├── data/tracking/                  # IDs vistos
├── dashboards/                     # Dashboards nuevos
│   ├── admin/                      # Streamlit (por crear)
│   ├── optimization/               # Next.js Vercel (por crear)
│   └── production/                 # Next.js Vercel (por crear)
├── exports/                        # Scripts export
├── scripts/                        # Linear cache, utilidades
├── config/                         # Configuracion
├── .linear/                        # Cache de Linear (no commitear)
├── docs/                           # Documentacion
├── run_scheduler.py                # PUNTO DE ENTRADA SCRAPING
└── CLAUDE.md                       # Este archivo
```

## Epicas Activas

| Epica | Prioridad | Descripcion |
|-------|-----------|-------------|
| 1. Scraping | Alta | Dashboard tab, ZonaJobs, deduplicacion |
| 2. NLP | Alta | Gold set 200+, tests, export S3 |
| 3. Matching | Alta | sector_funcion v8.4, gold set 200+ |
| 4. Validacion | Alta | Tests tab, S3 sync, sampling |
| 5. Dashboards | Media | Admin, Validacion, Produccion |
| 6. Infraestructura | Baja | Logs, alertas, CI/CD |

## Metricas Objetivo

| Metrica | Actual | Objetivo |
|---------|--------|----------|
| Precision NLP | ~90% | >= 90% |
| Precision Matching | 78.9% | >= 95% |
| Gold Set NLP | 0 | 200+ |
| Gold Set Matching | 19 | 200+ |
| Portales | 1 | 5 |

---

> **Ultima actualizacion:** 2025-12-07
