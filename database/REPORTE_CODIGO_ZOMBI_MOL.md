# Reporte de Código Zombi - MOL

**Fecha:** 2025-12-09
**Proyecto:** Monitor de Ofertas Laborales (MOL)
**Directorio:** `D:\OEDE\Webscrapping`

---

## Resumen Ejecutivo

| Categoría | Cantidad | Impacto |
|-----------|----------|---------|
| ESCO-XLM referencias (modelo deshabilitado) | 6 archivos | ALTO |
| Versiones múltiples matching_rules | 4 versiones | MEDIO |
| Versiones múltiples prompts NLP | 4 versiones | MEDIO |
| Versiones múltiples process_nlp | 3 versiones | MEDIO |
| Dashboards duplicados | 5 versiones | BAJO |
| Scripts test huérfanos | 35+ archivos | BAJO |
| Scrapers duplicados (scrapear_con_diccionario) | 3 copias | MEDIO |

---

## 1. ESCO-XLM Reranker (ALTO IMPACTO)

**Estado:** Deshabilitado en MOL-49, pero código permanece.

### Archivos con referencias:

| Archivo | Líneas | Estado |
|---------|--------|--------|
| `match_ofertas_multicriteria.py` | 72-75, 96-99, 164-227, 813-821 | **ACTIVO** (USE_RERANKER=False) |
| `match_ofertas_to_esco.py` | 49-52, 63-227 | LEGACY |
| `spike_reranker_eval.py` | 43-452 | EXPERIMENTAL (spike MOL-49) |
| `evaluar_matching_esco.py` | 6, 83, 235, 287 | LEGACY |
| `evaluar_matching_esco_v2.py` | 170, 251-318 | LEGACY |
| `experiment_logger.py` | 23-32, 112, 209, 237 | UTIL (ejemplo) |

### Código zombi específico:

```python
# En match_ofertas_multicriteria.py:
class ESCOReranker:  # Líneas 164-227 - NUNCA SE USA (USE_RERANKER=False)
    """Re-ranker usando ESCO-XLM-RoBERTa-Large"""
    ...
```

**Recomendación:**
- Mover `ESCOReranker` a archivo separado `esco_xlm_reranker.py` (por si se reactiva)
- Eliminar imports de transformers/torch cuando `USE_RERANKER=False`
- Archivar `match_ofertas_to_esco.py` → `archive_old_versions/`

---

## 2. Versiones Múltiples de matching_rules

### Archivos encontrados:

| Versión | Archivo | Estado | Usado por |
|---------|---------|--------|-----------|
| v8.1 | `matching_rules_v81.py` | LEGACY | `apply_v81_rules_gold19.py`, `simulate_v81_gold19.py` |
| v8.2 | `matching_rules_v82.py` | LEGACY | `verify_v82_confirmados.py` |
| v8.3 | `matching_rules_v83.py` | **ACTIVO** | `match_ofertas_multicriteria.py` (fallback) |
| v8.4 | `matching_rules_v84.py` | **ACTIVO** | `match_ofertas_multicriteria.py` (primary) |

### Dependencias:

```
matching_rules_v84.py
  └── imports from matching_rules_v83.py
      └── standalone
```

**Recomendación:**
- Archivar v81 y v82: `archive_old_versions/matching_rules_v81.py`
- Mantener v83 (importado por v84)
- Consolidar scripts de simulación/apply en un solo archivo parametrizable

---

## 3. Versiones Múltiples de Prompts NLP

| Versión | Archivo | Estado |
|---------|---------|--------|
| v5 | `extraction_prompt_v5.py` | LEGACY (usado por archive/process_nlp_v5) |
| v6 | `extraction_prompt_v6.py` | LEGACY (usado por process_nlp_v6) |
| v7 | `extraction_prompt_v7.py` | LEGACY |
| v8 | `extraction_prompt_v8.py` | **ACTIVO** |

**Recomendación:**
- Archivar v5, v6, v7: `02.5_nlp_extraction/prompts/archive/`
- Solo mantener v8 activo

---

## 4. Versiones Múltiples de process_nlp

| Versión | Archivo | Estado |
|---------|---------|--------|
| v5 | `archive_old_versions/process_nlp_from_db_v5.py` | ARCHIVADO |
| v6 | `process_nlp_from_db_v6.py` | **EN database/** (debería archivarse) |
| v7 | `process_nlp_from_db_v7.py` | **ACTIVO** |

**Recomendación:**
- Mover v6 a `archive_old_versions/`

---

## 5. Dashboards Duplicados

| Archivo | Estado |
|---------|--------|
| `dashboard_scraping.py` | Original |
| `dashboard_scraping_v2.py` | LEGACY |
| `dashboard_scraping_v3.py` | LEGACY |
| `dashboard_scraping_v4.py` | **¿ACTIVO?** |
| `01_sources/bumeran/scrapers/dashboard_keywords.py` | Especializado |

**Recomendación:**
- Determinar cuál es el dashboard activo
- Archivar versiones anteriores

---

## 6. Scrapers Duplicados

### `scrapear_con_diccionario.py` aparece en 3 ubicaciones:

| Ubicación | Notas |
|-----------|-------|
| `01_sources/bumeran/scrapers/scrapear_con_diccionario.py` | Bumeran |
| `01_sources/computrabajo/scrapers/scrapear_con_diccionario.py` | Computrabajo |
| `01_sources/linkedin/scrapers/scrapear_con_diccionario.py` | LinkedIn |

**Análisis:** Probablemente código similar/copiado entre portales.

**Recomendación:**
- Crear módulo común: `common/scraper_base.py`
- Refactorizar scrapers para heredar de base

---

## 7. Scripts Test Huérfanos (35+ archivos)

### En raíz del proyecto:
- `test_sqlite_integration.py`
- `test_insert_offers.py`
- `test_fresh_insert.py`
- `test_pagination_api.py`
- `test_duplicate_detection.py`
- `test_api_parametros.py`
- `test_session_jwt.py`
- `test_cobertura_evolutiva.py`

### En scrapers:
- Múltiples `test_*.py` en cada portal (zonajobs, bumeran, computrabajo)

### En database:
- `test_patterns_v2.py`
- `test_session_fix.py`
- `test_dual_write.py`
- `test_nlp_v6.py`
- `test_validacion_incremental.py`
- `test_nlp_v8_regression.py`
- `test_esco_matching_regression.py`

**Recomendación:**
- Consolidar tests útiles en `tests/`
- Eliminar tests obsoletos de scrapers

---

## 8. Archivos de Versiones Específicas (Candidatos a Archivar)

### Scripts v81:
- `apply_v81_rules_gold19.py`
- `simulate_v81_gold19.py`
- `check_v81_skills.py`
- `compare_v80_v81.py`
- `rerun_matching_v81.py`
- `debug_v81_join.py`
- `check_v81_ofertas.py`
- `match_v81_ofertas.py`
- `match_v81_specific.py`
- `match_v81_complete.py`
- `insert_v81_records.py`
- `check_v81_progress.py`
- `experiment_nlp_v81.py`

### Scripts v82:
- `verify_v82_confirmados.py`
- `export_batch_v82_csv.py`
- `apply_v82_rules_gold19.py`
- `apply_v82_rules_batch.py`

### Scripts v83:
- `populate_skills_detalle_v83.py` - **PUEDE SER ÚTIL**

### Scripts v84:
- `check_v84_improvements.py`

---

## 9. Acciones Recomendadas

### Inmediatas (ALTA prioridad):
1. Mover clase `ESCOReranker` fuera de `match_ofertas_multicriteria.py`
2. Archivar `match_ofertas_to_esco.py`
3. Mover `process_nlp_from_db_v6.py` a archive

### A corto plazo (MEDIA prioridad):
4. Archivar matching_rules v81 y v82
5. Archivar prompts v5, v6, v7
6. Consolidar dashboards
7. Refactorizar scrapers con clase base común

### A largo plazo (BAJA prioridad):
8. Consolidar tests en `tests/`
9. Eliminar scripts de versiones específicas (v81, v82)
10. Documentar qué tests son necesarios

---

## 10. Estructura Propuesta Post-Limpieza

```
database/
├── archive_old_versions/
│   ├── matching_rules_v81.py
│   ├── matching_rules_v82.py
│   ├── process_nlp_from_db_v5.py
│   ├── process_nlp_from_db_v6.py
│   ├── match_ofertas_to_esco.py
│   ├── evaluar_matching_esco.py
│   ├── evaluar_matching_esco_v2.py
│   └── spike_reranker_eval.py  # Mantener como documentación del spike
│
├── matching_rules_v83.py       # Base (importado por v84)
├── matching_rules_v84.py       # ACTIVO
├── match_ofertas_multicriteria.py  # ACTIVO (sin ESCOReranker inline)
├── process_nlp_from_db_v7.py   # ACTIVO
├── normalizacion_arg.py        # ACTIVO
└── ...

02.5_nlp_extraction/prompts/
├── archive/
│   ├── extraction_prompt_v5.py
│   ├── extraction_prompt_v6.py
│   └── extraction_prompt_v7.py
└── extraction_prompt_v8.py     # ACTIVO
```

---

**Generado por:** Claude Code
**Fecha:** 2025-12-09
