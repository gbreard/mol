# MOL - Monitor de Ofertas Laborales

## Descripcion
Sistema de monitoreo del mercado laboral argentino para OEDE. Scrapea ofertas de empleo, extrae informacion con NLP, clasifica segun taxonomia ESCO, y provee dashboards para analistas.

## Estado Actual (2025-12-10)
- 9,564 ofertas en BD
- 10,223 IDs en tracking
- 89% cobertura de scraping
- NLP v10.0 (153 campos, ~90% precision)
- Matching v2.1.1 BGE-M3 (100% precision Gold Set, filtros ISCO contextuales)

---

## VERSIONES ACTUALES - USAR SIEMPRE ESTAS

### NLP Pipeline

| Componente | Archivo ACTUAL | NO USAR |
|------------|----------------|---------|
| Pipeline NLP | `database/process_nlp_from_db_v10.py` | v7, v8, v9 |
| Prompt | `02.5_nlp_extraction/prompts/extraction_prompt_v10.py` | v8, v9 |
| Schema | 153 columnas (NLP Schema v5) | schemas anteriores |
| Normalizador | `database/normalize_nlp_values.py` | - |

### Matching Pipeline v2.1.1 BGE-M3

| Componente | Archivo ACTUAL | NO USAR |
|------------|----------------|---------|
| Pipeline Matching | `database/match_ofertas_v2.py` | match_ofertas_multicriteria.py, v8.x |
| Version | **v2.1.1** | v2.0, v8.x |
| Precision Gold Set | **100% (49/49)** | - |
| Modelo Embeddings | **BAAI/bge-m3** | - |
| Estrategia v2 | `docs/MATCHING_STRATEGY_V2.md` | - |
| Config principal | `config/matching_config.json` | valores hardcodeados |
| Config area | `config/area_funcional_esco_map.json` | - |
| Config seniority | `config/nivel_seniority_esco_map.json` | - |
| Config sector | `config/sector_isco_compatibilidad.json` | - |

### Tests

| Componente | Ubicacion |
|------------|-----------|
| Tests NLP | `tests/nlp/test_extraction.py` |
| Tests Matching | `tests/matching/` (por crear) |
| Gold Set NLP | `tests/nlp/gold_set.json` (49 casos) |
| Gold Set Matching | `database/gold_set_manual_v2.json` (49 casos) |

### Configuracion

| Archivo | Proposito |
|---------|-----------|
| `config/matching_config.json` | Config principal matching v2 (pesos, umbrales, penalizaciones) |
| `config/area_funcional_esco_map.json` | Mapeo area_funcional → codigos ISCO |
| `config/nivel_seniority_esco_map.json` | Mapeo seniority → ISCO + matriz penalizacion |
| `config/sector_isco_compatibilidad.json` | Compatibilidad sector empresa ↔ ISCO |

### Diccionarios de Extraccion

| Archivo | Proposito | Items |
|---------|-----------|-------|
| `config/skills_database.json` | Skills tecnicas, LATAM, logistica, contables | ~320 |
| `config/oficios_arg.json` | Oficios y ocupaciones argentinas | ~170 |
| `config/nlp_preprocessing.json` | Preprocesamiento ubicacion | - |
| `config/nlp_validation.json` | Validacion tipos (rechazo booleanos) | - |
| `config/nlp_extraction_patterns.json` | Patterns regex experiencia | - |
| `config/nlp_inference_rules.json` | Inferencia modalidad/seniority/area | - |
| `config/nlp_defaults.json` | Valores default campos | - |
| `config/nlp_normalization.json` | Normalizacion provincias (CABA) | - |

**Agregar nuevas skills:**
```python
# Editar config/skills_database.json, categoria correspondiente
# NO hardcodear en codigo Python
# Categorias disponibles: lenguajes_programacion, frameworks_web, bases_datos,
# cloud_devops, plataformas_latam, skills_logistica, skills_contables,
# skills_operativas_retail, skills_gastronomia, certificaciones_arg
```

---

## ARCHIVOS DEPRECADOS - NO USAR

Los siguientes archivos estan en `database/archive_old_versions/` y NO deben usarse:

**NLP:**
- `process_nlp_from_db_v*.py` (v1-v9) → usar v10
- `extraction_prompt_v*.py` (v1-v9) → usar v10

**Matching:**
- `matching_rules_v*.py` (v81-v84) → archivados, usar match_ofertas_v2.py
- `match_ofertas_multicriteria.py` → archivado, usar match_ofertas_v2.py
- Scripts de matching antiguos

**Tests sueltos:**
- Cualquier `check_*.py`, `debug_*.py`, `test_*.py` fuera de `tests/`

Ver `database/archive_old_versions/DEPRECATED.md` para lista completa.

---

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

## Convenciones del Proyecto

### Estructura de Codigo

| Tipo de archivo | Ubicacion | Ejemplo |
|-----------------|-----------|---------|
| Tests pytest | `tests/` | `tests/nlp/test_extraction.py` |
| Migraciones BD | `database/migrations/` | `001_initial.sql` |
| Prompts LLM | `02.5_nlp_extraction/prompts/` | `extraction_prompt_v9.py` |
| Configuracion | `config/` | `matching_config.json` |
| Scripts one-time | `scripts/` | `fix_descripcion_nulls.py` |
| Archivos obsoletos | `database/archive_old_versions/` | Versiones antiguas |

### Tests

- **SIEMPRE** crear tests en `tests/`, nunca en `database/` u otras carpetas
- Estructura: `tests/{modulo}/test_{funcionalidad}.py`
- Gold sets van en `tests/{modulo}/gold_set.json` o `database/gold_set_*.json`
- Usar pytest: `python -m pytest tests/ -v`
- Fixtures compartidos: `tests/conftest.py`

### Versionado de Archivos

| Componente | Patron | Version ACTIVA |
|------------|--------|----------------|
| Prompts | `extraction_prompt_v{N}.py` | **v10** |
| Procesos NLP | `process_nlp_from_db_v{N}.py` | **v10** |
| Matching Rules | `matching_rules_v{NN}.py` | **v84** |
| Configs | Campo `"version"` interno | matching_config v2.0 |

### Scripts Temporales

- Si es debugging/one-time -> crear en `scripts/` con fecha: `2025-12-09_fix_xyz.py`
- Si es test -> crear en `tests/`
- **NUNCA** crear `check_*.py`, `debug_*.py` o `test_*.py` sueltos en `database/`
- Scripts obsoletos -> mover a `database/archive_old_versions/`

### Gold Sets

| Gold Set | Ubicacion | Casos |
|----------|-----------|-------|
| Matching ESCO | `database/gold_set_manual_v2.json` | 49 casos |
| NLP Extraction | `tests/nlp/gold_set.json` | 20+ casos |

### Commits

- Usar conventional commits: `feat:`, `fix:`, `docs:`, `refactor:`
- Incluir issue Linear si aplica: `feat(MOL-XX): descripcion`

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
| Precision Matching | **100%** | >= 95% |
| Gold Set NLP | 0 | 200+ |
| Gold Set Matching | **49** | 200+ |
| Portales | 1 | 5 |

---

> **Ultima actualizacion:** 2025-12-10
