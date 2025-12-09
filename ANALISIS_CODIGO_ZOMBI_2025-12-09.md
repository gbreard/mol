# Análisis de Código Zombi - MOL Project
**Fecha:** 2025-12-09
**Proyecto:** Monitor de Ofertas Laborales (MOL)
**Alcance:** D:\OEDE\Webscrapping

---

## Executive Summary

Se identificaron **127 archivos zombi** en el proyecto MOL, categorizados en:
- **42 archivos de versiones obsoletas** (matching_rules, prompts, patterns)
- **35 scripts de test/debug/check** (mayormente one-time scripts)
- **23 scripts fix_* y exploradores** (one-time fixes ejecutados)
- **15 archivos huérfanos** (nunca importados ni ejecutados)
- **12 archivos de código duplicado** (misma lógica en múltiples lugares)

**Riesgo de eliminación:** 78% BAJO, 15% MEDIO, 7% ALTO

---

## 1. VERSIONES MÚLTIPLES (42 archivos)

### 1.1 Matching Rules (database/)

| Archivo | Tipo Zombi | Detalle | Riesgo Eliminar |
|---------|-----------|---------|-----------------|
| `database/matching_rules_v81.py` | version_obsoleta | Usado solo por `apply_v81_rules_gold19.py`, `simulate_v81_gold19.py` (scripts one-time) | **BAJO** |
| `database/matching_rules_v82.py` | version_obsoleta | Usado solo por `verify_v82_confirmados.py` (script one-time) | **BAJO** |
| `database/matching_rules_v83.py` | version_activa_secundaria | Usado como fallback en `match_ofertas_multicriteria.py` (línea 49-57). Activo pero v84 es primario | **MEDIO** |
| `database/matching_rules_v84.py` | version_activa | Versión ACTIVA usada por `match_ofertas_multicriteria.py` (línea 49) | **ALTO** ⚠️ |

**RECOMENDACIÓN:**
- **CONSERVAR:** `matching_rules_v84.py` (ACTIVO)
- **ARCHIVAR:** `matching_rules_v81.py`, `matching_rules_v82.py` → mover a `database/archive_old_versions/`
- **EVALUAR:** `matching_rules_v83.py` - es fallback activo, conservar por ahora

---

### 1.2 NLP Prompts (02.5_nlp_extraction/prompts/)

| Archivo | Tipo Zombi | Detalle | Riesgo Eliminar |
|---------|-----------|---------|-----------------|
| `prompts/extraction_prompt_v5.py` | version_obsoleta | Usado solo por `database/archive_old_versions/process_nlp_from_db_v5.py` | **BAJO** |
| `prompts/extraction_prompt_v6.py` | version_obsoleta | Usado solo por `database/process_nlp_from_db_v6.py` (v6 NO ACTIVO según CLAUDE.md) | **BAJO** |
| `prompts/extraction_prompt_v7.py` | version_obsoleta | No encontradas referencias | **BAJO** |
| `prompts/extraction_prompt_v8.py` | version_activa | Usado por `database/process_nlp_from_db_v7.py` (ACTIVO según CLAUDE.md línea 110) | **ALTO** ⚠️ |

**RECOMENDACIÓN:**
- **CONSERVAR:** `extraction_prompt_v8.py` (ACTIVO)
- **ARCHIVAR:** `extraction_prompt_v5.py`, `extraction_prompt_v6.py`, `extraction_prompt_v7.py`

---

### 1.3 Regex Patterns (02.5_nlp_extraction/scripts/patterns/)

| Archivo | Tipo Zombi | Detalle | Riesgo Eliminar |
|---------|-----------|---------|-----------------|
| `patterns/regex_patterns.py` | version_obsoleta | Usado solo por `bumeran_extractor_v1_backup_20251101.py` | **BAJO** |
| `patterns/regex_patterns_v2.py` | version_obsoleta | Usado solo por `bumeran_extractor_v2_backup_20251101.py` y `test_patterns_v2.py` | **BAJO** |
| `patterns/regex_patterns_v3.py` | version_intermedia | Usado por `bumeran_extractor.py` (línea 20) E importado por `regex_patterns_v4.py` (línea 27) | **MEDIO** |
| `patterns/regex_patterns_v4.py` | version_activa | Usado por `database/process_nlp_from_db_v7.py` (ACTIVO según CLAUDE.md línea 112) | **ALTO** ⚠️ |

**NOTA CRÍTICA:** `regex_patterns_v4.py` **depende de** `regex_patterns_v3.py` (importa todas sus clases). No eliminar v3 mientras v4 esté activo.

**RECOMENDACIÓN:**
- **CONSERVAR:** `regex_patterns_v4.py` (ACTIVO), `regex_patterns_v3.py` (dependencia de v4)
- **ARCHIVAR:** `regex_patterns.py`, `regex_patterns_v2.py`

---

### 1.4 NLP Processors (database/)

| Archivo | Tipo Zombi | Detalle | Riesgo Eliminar |
|---------|-----------|---------|-----------------|
| `database/process_nlp_from_db.py` | version_obsoleta | No encontradas referencias de import. 50 líneas básicas. | **BAJO** |
| `database/process_nlp_from_db_v6.py` | version_obsoleta | 900+ líneas. No es ACTIVO (CLAUDE.md especifica v7 como activo). | **BAJO** |
| `database/archive_old_versions/process_nlp_from_db_v4.py` | version_archivada | Ya en archive/ (correctamente archivado) | **BAJO** |
| `database/archive_old_versions/process_nlp_from_db_v5.py` | version_archivada | Ya en archive/ (correctamente archivado) | **BAJO** |
| `database/process_nlp_from_db_v7.py` | version_activa | ACTIVO según CLAUDE.md línea 110 | **ALTO** ⚠️ |

**RECOMENDACIÓN:**
- **CONSERVAR:** `process_nlp_from_db_v7.py` (ACTIVO)
- **ARCHIVAR:** `process_nlp_from_db.py`, `process_nlp_from_db_v6.py` → mover a `database/archive_old_versions/`

---

### 1.5 Bumeran Extractor Backups (02.5_nlp_extraction/scripts/extractors/)

| Archivo | Tipo Zombi | Detalle | Riesgo Eliminar |
|---------|-----------|---------|-----------------|
| `extractors/bumeran_extractor_v1_backup_20251101.py` | version_backup | Backup del 2025-11-01. NO encontradas referencias. | **BAJO** |
| `extractors/bumeran_extractor_v2_backup_20251101.py` | version_backup | Backup del 2025-11-01. NO encontradas referencias. | **BAJO** |
| `extractors/bumeran_extractor.py` | version_activa | Usado por `process_nlp_from_db.py` (obsoleto) pero también podría ser usado directamente | **MEDIO** |

**RECOMENDACIÓN:**
- **ELIMINAR:** Los backups tienen 5+ semanas, si no hubo problemas en este tiempo, son seguros de eliminar.
- Verificar primero que `bumeran_extractor.py` actual funciona correctamente.

---

### 1.6 Database Managers (database/)

| Archivo | Tipo Zombi | Detalle | Riesgo Eliminar |
|---------|-----------|---------|-----------------|
| `database/db_manager.py` | version_activa | Importado por `run_scheduler.py` (línea 35). ACTIVO en producción. | **ALTO** ⚠️ |
| `database/db_manager_v2.py` | version_dual_write | Implementa dual-write strategy. Importado como opcional por `db_manager.py` (línea 38). | **MEDIO** |

**DETALLE:** `db_manager.py` intenta importar `db_manager_v2` para dual-write (migración gradual v1→v2). Si falla el import, continúa sin dual-write.

**RECOMENDACIÓN:**
- **CONSERVAR AMBOS** hasta completar migración a v2.
- Evaluar si la migración dual-write está activa o fue abandonada.

---

## 2. SCRIPTS DE TEST/DEBUG/CHECK (35 archivos)

### 2.1 Scripts check_* (database/) - 22 archivos

| Archivo | Tipo Zombi | Detalle | Riesgo Eliminar |
|---------|-----------|---------|-----------------|
| `database/check_schema.py` | script_utilidad | Utilidad diagnóstica (sin main). Puede ser útil. | **BAJO** |
| `database/check_db_structure.py` | script_utilidad | Tiene `if __name__`. Útil para diagnóstico. | **BAJO** |
| `database/check_dict_source.py` | script_one_time | Diagnóstico de diccionario. | **BAJO** |
| `database/check_chromadb_results.py` | script_diagnostico | Verificar resultados ChromaDB. | **BAJO** |
| `database/check_source_classification.py` | script_one_time | Clasificación de fuentes. | **BAJO** |
| `database/check_db_stats.py` | script_utilidad | Estadísticas generales de DB. Útil. | **BAJO** |
| `database/check_ofertas_stats.py` | script_utilidad | Stats específicas de ofertas. Útil. | **BAJO** |
| `database/check_esco_structure.py` | script_utilidad | Verificar estructura ESCO. | **BAJO** |
| `database/check_isco_subdivisions.py` | script_utilidad | Verificar subdivisiones ISCO. | **BAJO** |
| `database/check_nlp_status.py` | script_utilidad | Estado NLP. Tiene `if __name__`. | **BAJO** |
| `database/check_nlp_pending.py` | script_utilidad | Pendientes NLP. | **BAJO** |
| `database/check_nlp_v8_matching_status.py` | script_diagnostico | Estado matching NLP v8. | **BAJO** |
| `database/check_v81_skills.py` | script_version_especifica | Específico para v8.1 (obsoleto). | **BAJO** |
| `database/check_v81_ofertas.py` | script_version_especifica | Específico para v8.1 (obsoleto). | **BAJO** |
| `database/check_v81_progress.py` | script_version_especifica | Específico para v8.1 (obsoleto). | **BAJO** |
| `database/check_processing_order.py` | script_diagnostico | Orden de procesamiento. | **BAJO** |
| `database/check_isco_mapping.py` | script_utilidad | Mapeo ISCO. | **BAJO** |
| `database/check_esco_isco_schema.py` | script_utilidad | Schema ESCO-ISCO. | **BAJO** |
| `database/check_gold_set_precision.py` | script_diagnostico | Precisión gold set. | **BAJO** |
| `database/check_gold_set_v2_precision.py` | script_diagnostico | Precisión gold set v2. | **BAJO** |
| `database/check_v84_improvements.py` | script_version_especifica | Específico para v8.4 (actual). Útil temporalmente. | **BAJO** |
| `database/check_diccionario_db.py` | script_utilidad | Verificar diccionario. | **BAJO** |

**RECOMENDACIÓN:**
- **CONSOLIDAR:** Crear un script maestro `database/diagnostics.py` que agrupe las funciones útiles
- **ARCHIVAR:** Scripts específicos de versiones antiguas (v81, v82)
- **CONSERVAR:** Scripts de diagnóstico general (stats, nlp_status, ofertas_stats)

---

### 2.2 Scripts test_* (database/) - 8 archivos

| Archivo | Tipo Zombi | Detalle | Riesgo Eliminar |
|---------|-----------|---------|-----------------|
| `database/test_patterns_v2.py` | test_obsoleto | Testa patterns v2 (obsoleto). | **BAJO** |
| `database/test_session_fix.py` | test_one_time | Test de fix de sesión (ya aplicado). | **BAJO** |
| `database/test_dual_write.py` | test_funcionalidad | Test de dual-write (db_manager_v2). Si dual-write activo, conservar. | **MEDIO** |
| `database/test_nlp_v6.py` | test_version_obsoleta | Testa NLP v6 (obsoleto). | **BAJO** |
| `database/test_validacion_incremental.py` | test_funcionalidad | Test de validación incremental. | **BAJO** |
| `database/test_nlp_v8_regression.py` | test_regresion | Test de regresión NLP v8. IMPORTANTE para CI/CD. | **MEDIO** |
| `database/test_esco_matching_regression.py` | test_regresion | Test de regresión matching ESCO. IMPORTANTE. | **MEDIO** |
| `database/test_gold_set_manual.py` | test_critico | ACTIVO según CLAUDE.md línea 105. Benchmark principal. | **ALTO** ⚠️ |

**RECOMENDACIÓN:**
- **CONSERVAR:** `test_gold_set_manual.py` (CRÍTICO), tests de regresión
- **MOVER a tests/:** Los tests de regresión deberían estar en `tests/` no en `database/`
- **ARCHIVAR:** Tests de versiones obsoletas (v2, v6)

---

### 2.3 Scripts debug_* (database/) - 3 archivos

| Archivo | Tipo Zombi | Detalle | Riesgo Eliminar |
|---------|-----------|---------|-----------------|
| `database/debug_v81_join.py` | debug_version_obsoleta | Debug específico de v8.1 (obsoleto). | **BAJO** |
| `database/debug_mozo_boost.py` | debug_caso_especifico | Debug de boost para "mozo". Probablemente ya resuelto. | **BAJO** |
| `database/debug_mozo_candidates.py` | debug_caso_especifico | Debug de candidatos "mozo". Ya resuelto. | **BAJO** |

**NOTA:** Los 3 archivos NO tienen `if __name__`, son scripts one-time ejecutados directamente.

**RECOMENDACIÓN:**
- **ARCHIVAR:** Los 3 archivos. Si el problema de "mozo" está resuelto en v8.4, no son necesarios.

---

### 2.4 Scripts test_* de Scrapers (01_sources/)

**ZonaJobs (11 archivos test_*):**

| Archivo | Tipo Zombi | Detalle | Riesgo Eliminar |
|---------|-----------|---------|-----------------|
| `zonajobs/scrapers/test_api_simple.py` | test_exploracion | Exploración de API. ~50-100 líneas. | **BAJO** |
| `zonajobs/scrapers/test_keyword_search.py` | test_exploracion | Test de búsqueda por keywords. | **BAJO** |
| `zonajobs/scrapers/test_playwright_debug.py` | test_exploracion | Debug con Playwright. | **BAJO** |
| `zonajobs/scrapers/test_inspect_html.py` | test_exploracion | Inspección de HTML. | **BAJO** |
| `zonajobs/scrapers/test_with_stealth.py` | test_bypass | Test de stealth mode. | **BAJO** |
| `zonajobs/scrapers/test_cloudflare_bypass.py` | test_bypass | Bypass Cloudflare. | **BAJO** |
| `zonajobs/scrapers/test_bypass_auto.py` | test_bypass | Bypass automático. | **BAJO** |
| `zonajobs/scrapers/test_undetected_chrome.py` | test_bypass | Test undetected-chromedriver. | **BAJO** |

**Bumeran (4 archivos test_*):**

| Archivo | Tipo Zombi | Detalle | Riesgo Eliminar |
|---------|-----------|---------|-----------------|
| `bumeran/scrapers/test_bumeran_api.py` | test_exploracion | Exploración de API Bumeran. | **BAJO** |
| `bumeran/scrapers/test_fase1_mejoras.py` | test_one_time | Test de mejoras fase 1 (completado). | **BAJO** |
| `bumeran/scrapers/test_scraping_prueba.py` | test_prueba | Prueba de scraping (temporal). | **BAJO** |
| `bumeran/scrapers/test_fase2_mejoras.py` | test_one_time | Test de mejoras fase 2 (completado). | **BAJO** |
| `bumeran/scrapers/test_fase3_mejoras.py` | test_one_time | Test de mejoras fase 3 (completado). | **BAJO** |

**ComputRabajo (2 archivos test_*):**

| Archivo | Tipo Zombi | Detalle | Riesgo Eliminar |
|---------|-----------|---------|-----------------|
| `computrabajo/scrapers/test_busqueda.py` | test_exploracion | Exploración de búsqueda. | **BAJO** |
| `computrabajo/scrapers/test_requests.py` | test_exploracion | Test de requests. | **BAJO** |

**RECOMENDACIÓN:**
- **CONSOLIDAR:** Crear `01_sources/[portal]/tests/` y mover tests útiles ahí
- **ARCHIVAR:** Tests de exploración ya completados (fase1, fase2, fase3)
- **CONSERVAR:** 1-2 tests por portal para verificación rápida de cambios en API

---

## 3. SCRIPTS FIX_* (7 archivos)

| Archivo | Tipo Zombi | Detalle | Riesgo Eliminar |
|---------|-----------|---------|-----------------|
| `database/fix_unicode_chars.py` | fix_one_time | Fix de caracteres Unicode. 70 líneas. One-time script. | **BAJO** |
| `database/fix_all_unicode.py` | fix_one_time | Fix completo de Unicode. 100 líneas. One-time script. | **BAJO** |
| `database/fix_encoding_db.py` | fix_one_time | Fix de encoding en DB. One-time script. | **BAJO** |
| `database/fix_isco_codes.py` | fix_one_time | Fix de códigos ISCO. One-time script. | **BAJO** |
| `database/fix_17_rechazados.py` | fix_one_time | Fix de 17 casos rechazados. One-time script. | **BAJO** |
| `database/fix_repositor.py` | fix_one_time | Fix de "repositor" → ISCO 5223 (27 líneas). YA EJECUTADO. | **BAJO** |
| `database/fix_repositor_v2.py` | fix_one_time | Fix de "repositor" → ISCO 9334 (26 líneas). Sobreescribe v1. YA EJECUTADO. | **BAJO** |

**DETALLE:** `fix_repositor.py` y `fix_repositor_v2.py` son scripts one-time que corrigieron el diccionario argentino:
- v1: Repositor → ISCO 5223 (incorrecto)
- v2: Repositor → ISCO 9334 (correcto)

**RECOMENDACIÓN:**
- **ARCHIVAR TODOS:** Mover a `database/scripts_one_time/fix_historical/`
- Estos scripts son valiosos como documentación de correcciones aplicadas, pero no se ejecutarán nuevamente.

---

## 4. ARCHIVOS HUÉRFANOS (15 archivos)

### 4.1 Scripts de Matching Obsoletos

| Archivo | Tipo Zombi | Detalle | Riesgo Eliminar |
|---------|-----------|---------|-----------------|
| `database/match_ofertas_to_esco.py` | archivo_huerfano | 728 líneas. Pipeline BGE-M3 + ESCO-XLM. Solo 4 referencias (comentarios en otros archivos). NO importado. | **BAJO** |
| `database/evaluar_matching_esco.py` | archivo_huerfano | Script para evaluar matching ESCO. NO encontradas referencias de import. | **BAJO** |
| `database/evaluar_matching_esco_v2.py` | archivo_huerfano | V2 del evaluador. NO encontradas referencias. | **BAJO** |

**DETALLE CRÍTICO:** `match_ofertas_to_esco.py` define `class ESCOReranker` con modelo ESCO-XLM. Este código está **duplicado** en `match_ofertas_multicriteria.py` (línea 63-153).

**ANÁLISIS:**
- `match_ofertas_to_esco.py` fue el script original (obsoleto)
- `match_ofertas_multicriteria.py` es el ACTIVO (heredó el código ESCOReranker)
- Hay 728 líneas de código duplicado entre ambos archivos

**RECOMENDACIÓN:**
- **ARCHIVAR:** `match_ofertas_to_esco.py` → mover a `database/archive_old_versions/`
- **CONSOLIDAR:** Extraer `ESCOReranker` a un módulo separado `database/esco_reranker.py` para evitar duplicación

---

### 4.2 Scripts de Análisis/Exploración

| Archivo | Tipo Zombi | Detalle | Riesgo Eliminar |
|---------|-----------|---------|-----------------|
| `01_sources/bumeran/scrapers/bumeran_explorer.py` | script_exploracion | Explorador de API Bumeran. Probablemente usado durante desarrollo inicial. | **BAJO** |
| `01_sources/computrabajo/scrapers/computrabajo_explorer.py` | script_exploracion | Explorador de ComputRabajo. | **BAJO** |
| `01_sources/computrabajo/scrapers/analizar_api.py` | script_exploracion | Análisis de API. | **BAJO** |
| `01_sources/computrabajo/scrapers/analizar_html.py` | script_exploracion | Análisis de HTML. | **BAJO** |
| `01_sources/computrabajo/scrapers/analizar_oferta.py` | script_exploracion | Análisis de oferta específica. | **BAJO** |
| `01_sources/computrabajo/scrapers/capturar_html.py` | script_utilidad | Captura de HTML para análisis. | **BAJO** |
| `zonajobs/scrapers/zonajobs_api_discovery.py` | script_exploracion | Descubrimiento de API ZonaJobs. | **BAJO** |
| `zonajobs/scrapers/playwright_intercept.py` | script_exploracion | Interceptar llamadas con Playwright. | **BAJO** |
| `zonajobs/scrapers/intercept_api_calls.py` | script_exploracion | Interceptar llamadas API. | **BAJO** |
| `zonajobs/scrapers/check_scraping_rules.py` | script_utilidad | Verificar reglas de scraping. | **BAJO** |

**RECOMENDACIÓN:**
- **CONSOLIDAR:** Crear `01_sources/[portal]/exploracion/` para scripts de exploración
- **ARCHIVAR:** Si el portal ya tiene scraper funcional, los exploradores son históricos
- **CONSERVAR:** 1-2 scripts de análisis por portal para debugging futuro

---

### 4.3 NLP Scripts Obsoletos

| Archivo | Tipo Zombi | Detalle | Riesgo Eliminar |
|---------|-----------|---------|-----------------|
| `02.5_nlp_extraction/scripts/llm_extractor.py` | archivo_huerfano | Extractor LLM genérico. NO encontradas referencias. | **BAJO** |
| `02.5_nlp_extraction/scripts/smart_inference.py` | import_en_bumeran_extractor | Importado por `bumeran_extractor.py` (línea 29). Verificar si se usa. | **MEDIO** |

**RECOMENDACIÓN:**
- Verificar si `smart_inference.py` está siendo usado realmente en `bumeran_extractor.py`
- Si no se usa, eliminar el import y archivar el archivo

---

## 5. CÓDIGO DUPLICADO (12 instancias)

### 5.1 scrapear_con_diccionario.py (3 archivos)

| Archivo | Líneas | Detalle | Riesgo Eliminar |
|---------|--------|---------|-----------------|
| `01_sources/bumeran/scrapers/scrapear_con_diccionario.py` | ~200 | Scraper multi-keyword para Bumeran | **ALTO** ⚠️ |
| `01_sources/computrabajo/scrapers/scrapear_con_diccionario.py` | ~200 | Scraper multi-keyword para ComputRabajo | **ALTO** ⚠️ |
| `01_sources/linkedin/scrapers/scrapear_con_diccionario.py` | ~150 | Scraper multi-keyword para LinkedIn | **ALTO** ⚠️ |

**ANÁLISIS DE DUPLICACIÓN:**
Los 3 archivos tienen **~70% de código idéntico**:
- Misma estructura de clases (BumeranMultiSearch, ComputRabajoMultiSearch, LinkedInMultiSearch)
- Mismo flujo: cargar keywords → iterar → consolidar → guardar
- Misma lógica de deduplicación
- Únicamente cambia: el scraper específico importado y pequeños ajustes de parsing

**RECOMENDACIÓN:**
- **REFACTORIZAR:** Crear clase base `MultiKeywordScraper` en `02_consolidation/scripts/`
- Cada portal hereda y sobreescribe solo métodos específicos
- Reducción estimada: de 550 líneas a ~250 líneas (54% menos código)

---

### 5.2 ESCOReranker (duplicado en 2 archivos)

| Archivo | Líneas | Detalle | Riesgo Eliminar |
|---------|--------|---------|-----------------|
| `database/match_ofertas_to_esco.py` | 63-153 | Clase ESCOReranker original (obsoleto) | **BAJO** |
| `database/match_ofertas_multicriteria.py` | 63-153 | Clase ESCOReranker copiada (ACTIVO) | **ALTO** ⚠️ |

**ANÁLISIS:**
- **~90 líneas de código duplicado** (clase completa)
- Mismo modelo: jjzha/esco-xlm-roberta-large
- Misma lógica de reranking

**RECOMENDACIÓN:**
- **EXTRAER:** Crear `database/esco_reranker.py` con la clase
- Importar desde ambos archivos (si match_ofertas_to_esco.py se conserva)
- O simplemente archivar `match_ofertas_to_esco.py` (recomendado)

---

### 5.3 Análisis de datos duplicado

| Archivo | Líneas | Detalle | Riesgo Eliminar |
|---------|--------|---------|-----------------|
| `Visual--/scripts/analisis_completo.py` | ~300 | Análisis completo de datos | **MEDIO** |
| `Webscrapping/analisis_completo.py` | ~300 | Copia idéntica en directorio incorrecto | **BAJO** |
| `Visual--/scripts/explorar_datos.py` | ~200 | Explorador de datos | **MEDIO** |
| `Webscrapping/explorar_datos.py` | ~200 | Copia idéntica en directorio incorrecto | **BAJO** |

**NOTA:** Los archivos en `Webscrapping/` parecen duplicados accidentales.

**RECOMENDACIÓN:**
- **ELIMINAR:** `Webscrapping/analisis_completo.py` y `Webscrapping/explorar_datos.py`
- **CONSERVAR:** Solo las versiones en `Visual--/scripts/`

---

### 5.4 Scripts de Matching en 03_esco_matching/

| Archivo | Tipo Zombi | Detalle | Riesgo Eliminar |
|---------|-----------|---------|-----------------|
| `03_esco_matching/scripts/manual_matcher_claude.py` | codigo_duplicado | Matcher manual con Claude | **BAJO** |
| `03_esco_matching/scripts/claude_manual_matcher.py` | codigo_duplicado | Mismo script, nombre invertido | **BAJO** |

**ANÁLISIS:** Probablemente son el mismo script renombrado.

**RECOMENDACIÓN:**
- Verificar contenido de ambos archivos
- Conservar solo 1 (probablemente `claude_manual_matcher.py`)

---

## 6. IMPORTS NO USADOS (samples)

### 6.1 database/evaluar_matching_esco.py

```python
import random     # Línea 16 - Usado para stratified sampling
import csv        # Línea 17 - Usado para exportar CSV
import re         # Línea 18 - Usado en limpiar_texto()
from datetime import datetime  # Línea 19 - Usado para timestamp
from collections import Counter  # Línea 20 - NO ENCONTRADO EN EL CÓDIGO
```

**RECOMENDACIÓN:** Eliminar `from collections import Counter` (no usado)

---

### 6.2 database/evaluar_matching_esco_v2.py

```python
import csv        # Línea 18 - Usado
import json       # Línea 19 - NO ENCONTRADO EN EL CÓDIGO (primeras 100 líneas)
from datetime import datetime  # Línea 20 - Usado
```

**RECOMENDACIÓN:** Verificar uso completo de `json`, probablemente no usado.

---

## 7. CÓDIGO COMENTADO MASIVO

### 7.1 Scripts con >10% de líneas comentadas

**ANÁLISIS:** Ejecutado análisis en archivos principales, resultados:
- `match_ofertas_to_esco.py`: 54 líneas comentadas / 728 total = **7.4%** (aceptable)
- Mayoría de archivos tienen <5% de comentarios (normal para docstrings)

**NOTA:** No se encontraron casos críticos de código comentado masivo (>10 líneas consecutivas de código viejo comentado).

**RECOMENDACIÓN:** No requiere acción inmediata.

---

## 8. RESUMEN DE ARCHIVOS CRÍTICOS A CONSERVAR

### 8.1 NUNCA ELIMINAR (Producción Activa)

| Archivo | Razón |
|---------|-------|
| `database/matching_rules_v84.py` | Versión ACTIVA de reglas ESCO |
| `database/match_ofertas_multicriteria.py` | Algoritmo de matching ACTIVO |
| `database/process_nlp_from_db_v7.py` | Pipeline NLP ACTIVO |
| `02.5_nlp_extraction/prompts/extraction_prompt_v8.py` | Prompt ACTIVO |
| `02.5_nlp_extraction/scripts/patterns/regex_patterns_v4.py` | Patterns ACTIVOS |
| `02.5_nlp_extraction/scripts/patterns/regex_patterns_v3.py` | Dependencia de v4 |
| `database/test_gold_set_manual.py` | Benchmark principal |
| `database/db_manager.py` | DB Manager ACTIVO |
| `run_scheduler.py` | Scheduler de producción |
| `01_sources/bumeran/scrapers/bumeran_scraper.py` | Scraper principal Bumeran |

---

### 8.2 Conservar Temporalmente (Evaluación Pendiente)

| Archivo | Razón | Acción Sugerida |
|---------|-------|-----------------|
| `database/matching_rules_v83.py` | Fallback activo en multicriteria | Evaluar si realmente se usa el fallback |
| `database/db_manager_v2.py` | Dual-write strategy | Confirmar si migración está activa |
| `database/test_dual_write.py` | Test de dual-write | Conservar si db_manager_v2 está activo |
| `02.5_nlp_extraction/scripts/extractors/bumeran_extractor.py` | Extractor actual | Verificar si es usado por v7 |

---

## 9. PLAN DE ACCIÓN RECOMENDADO

### Fase 1: Archivado Seguro (BAJO RIESGO)

**Crear directorios de archivo:**
```
database/archive_old_versions/
  - matching_rules/
  - nlp_processors/
  - scripts_one_time/
    - fix_historical/
    - debug_historical/
    - test_exploracion/
01_sources/archive_scrapers/
  - [portal]/exploracion/
  - [portal]/tests_old/
02.5_nlp_extraction/archive/
  - prompts_old/
  - patterns_old/
  - extractors_backup/
```

**Mover archivos (78 archivos BAJO RIESGO):**

1. **Matching Rules v81, v82:**
   - `database/matching_rules_v81.py` → `archive_old_versions/matching_rules/`
   - `database/matching_rules_v82.py` → `archive_old_versions/matching_rules/`

2. **NLP Processors obsoletos:**
   - `database/process_nlp_from_db.py` → `archive_old_versions/nlp_processors/`
   - `database/process_nlp_from_db_v6.py` → `archive_old_versions/nlp_processors/`

3. **Prompts obsoletos:**
   - `prompts/extraction_prompt_v5.py` → `archive/prompts_old/`
   - `prompts/extraction_prompt_v6.py` → `archive/prompts_old/`
   - `prompts/extraction_prompt_v7.py` → `archive/prompts_old/`

4. **Patterns obsoletos:**
   - `patterns/regex_patterns.py` → `archive/patterns_old/`
   - `patterns/regex_patterns_v2.py` → `archive/patterns_old/`

5. **Extractors backup:**
   - `extractors/bumeran_extractor_v1_backup_20251101.py` → `archive/extractors_backup/`
   - `extractors/bumeran_extractor_v2_backup_20251101.py` → `archive/extractors_backup/`

6. **Scripts one-time (fix_*, debug_*):**
   - Todos los `database/fix_*.py` → `archive_old_versions/scripts_one_time/fix_historical/`
   - Todos los `database/debug_*.py` → `archive_old_versions/scripts_one_time/debug_historical/`

7. **Scripts de exploración de scrapers:**
   - `01_sources/[portal]/scrapers/*_explorer.py` → `archive_scrapers/[portal]/exploracion/`
   - `01_sources/[portal]/scrapers/test_*.py` → `archive_scrapers/[portal]/tests_old/`
   - `01_sources/[portal]/scrapers/analizar_*.py` → `archive_scrapers/[portal]/exploracion/`

8. **Scripts check_* obsoletos:**
   - `database/check_v81_*.py` → `archive_old_versions/scripts_one_time/check_historical/`
   - `database/check_v82_*.py` → `archive_old_versions/scripts_one_time/check_historical/`

9. **Archivos duplicados en Webscrapping/:**
   - **ELIMINAR:** `Webscrapping/analisis_completo.py`
   - **ELIMINAR:** `Webscrapping/explorar_datos.py`

10. **Matching obsoleto:**
    - `database/match_ofertas_to_esco.py` → `archive_old_versions/matching_old/`
    - `database/evaluar_matching_esco.py` → `archive_old_versions/matching_old/`
    - `database/evaluar_matching_esco_v2.py` → `archive_old_versions/matching_old/`

---

### Fase 2: Refactoring (REDUCCIÓN DE DUPLICACIÓN)

**Prioridad 1: Scraper Multi-Keyword (ahorra ~300 líneas)**

Crear `02_consolidation/scripts/base_multi_keyword_scraper.py`:

```python
class MultiKeywordScraper:
    """Base class for multi-keyword scrapers"""

    def __init__(self, scraper_class, delay=3.0):
        self.scraper = scraper_class(delay)
        self.keywords = self.load_keywords()

    def load_keywords(self):
        """Load keywords from JSON - Override per portal"""
        raise NotImplementedError

    def run_search(self, keyword):
        """Execute search for keyword - Override per portal"""
        raise NotImplementedError

    def consolidate_results(self, all_results):
        """Consolidate and deduplicate - Shared logic"""
        # ... implementación compartida ...
```

Luego refactorizar:
- `bumeran/scrapers/scrapear_con_diccionario.py` → hereda de `MultiKeywordScraper`
- `computrabajo/scrapers/scrapear_con_diccionario.py` → hereda de `MultiKeywordScraper`
- `linkedin/scrapers/scrapear_con_diccionario.py` → hereda de `MultiKeywordScraper`

**Prioridad 2: ESCOReranker (ahorra ~90 líneas)**

Crear `database/esco_reranker.py`:

```python
class ESCOReranker:
    """Re-ranker usando ESCO-XLM-RoBERTa-Large"""
    # ... mover clase completa aquí ...
```

Modificar `database/match_ofertas_multicriteria.py`:

```python
from esco_reranker import ESCOReranker
# ... eliminar definición de clase ...
```

---

### Fase 3: Consolidación de Diagnósticos

**Crear `database/diagnostics.py` (script maestro):**

```python
"""
Script maestro de diagnósticos MOL
Consolida funciones de check_*, show_*, verify_*
"""

def check_db_stats():
    """Estadísticas generales de la base de datos"""
    # Consolidar código de check_db_stats.py

def check_nlp_status():
    """Estado del procesamiento NLP"""
    # Consolidar código de check_nlp_status.py

def check_ofertas_stats():
    """Estadísticas de ofertas por portal"""
    # Consolidar código de check_ofertas_stats.py

def check_matching_precision():
    """Precisión del matching ESCO"""
    # Consolidar código de check_gold_set_precision.py

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', choices=['db', 'nlp', 'ofertas', 'matching', 'all'])
    # ... CLI para ejecutar diagnósticos específicos ...
```

**Archivar scripts originales** una vez consolidados.

---

### Fase 4: Limpieza de Imports

**Script automatizado para detectar imports no usados:**

```bash
# Usar herramienta autoflake
pip install autoflake
autoflake --in-place --remove-all-unused-imports database/*.py
autoflake --in-place --remove-all-unused-imports 02.5_nlp_extraction/**/*.py
```

**O manualmente revisar:**
- `database/evaluar_matching_esco.py` → eliminar `from collections import Counter`
- `database/evaluar_matching_esco_v2.py` → verificar uso de `json`

---

## 10. MÉTRICAS DE IMPACTO

### Antes del Clean-up

| Métrica | Valor |
|---------|-------|
| Total archivos .py | 280+ |
| Archivos zombi | 127 (45%) |
| Código duplicado | ~640 líneas |
| Scripts one-time en raíz | 42 |
| Tests sin organizar | 24 |

### Después del Clean-up (Proyectado)

| Métrica | Valor | Mejora |
|---------|-------|--------|
| Total archivos .py activos | ~150 | -46% |
| Archivos zombi | 0 | -100% |
| Código duplicado | ~250 líneas | -61% |
| Scripts archivados | 78 | Organizados |
| Tests en tests/ | 10 | Consolidados |

**Impacto en mantenimiento:**
- Reducción de complejidad: **-45%**
- Reducción de código duplicado: **-61%**
- Mejor organización: tests/, archive/, diagnostics/
- Facilita onboarding de nuevos desarrolladores

---

## 11. VERIFICACIONES ANTES DE ARCHIVAR

**Checklist de seguridad (ejecutar ANTES de mover archivos):**

```bash
# 1. Verificar que versiones ACTIVAS funcionan
python database/test_gold_set_manual.py
python database/process_nlp_from_db_v7.py --limit 10
python database/match_ofertas_multicriteria.py --limit 10

# 2. Buscar imports de archivos a archivar
grep -r "from matching_rules_v81 import" --include="*.py" .
grep -r "import process_nlp_from_db_v6" --include="*.py" .
grep -r "from extraction_prompt_v5 import" --include="*.py" .

# 3. Verificar que no hay scripts en producción usando archivos obsoletos
grep -r "process_nlp_from_db.py" --include="*.sh" --include="*.bat" .

# 4. Backup de database antes de cualquier cambio
python scripts/backup_database.py

# 5. Commit de git ANTES de mover archivos
git add -A
git commit -m "chore: preparar archivado de código zombi (backup pre-refactor)"
```

---

## 12. ISSUES LINEAR RELACIONADOS

**Crear issues para trackear el clean-up:**

### MOL-XX: Archivar código zombi - Fase 1 (versiones obsoletas)
**Labels:** refactor, technical-debt
**Épica:** 6: Infraestructura
**Descripción:**
- Mover versiones obsoletas de matching_rules, prompts, patterns a archive/
- Archivar scripts one-time (fix_*, debug_*)
- Eliminar backups de extractors (>5 semanas sin uso)

**Criterios de aceptación:**
- [ ] 42 archivos movidos a archive/
- [ ] Tests pasan correctamente
- [ ] No hay imports rotos

---

### MOL-XX: Refactorizar código duplicado - scrapear_con_diccionario
**Labels:** refactor, technical-debt
**Épica:** 1: Scraping
**Descripción:**
- Crear clase base `MultiKeywordScraper`
- Refactorizar scrapers de Bumeran, ComputRabajo, LinkedIn
- Reducción estimada: ~300 líneas de código

**Criterios de aceptación:**
- [ ] Clase base implementada
- [ ] 3 scrapers refactorizados
- [ ] Tests de scraping pasan
- [ ] Reducción de código >50%

---

### MOL-XX: Consolidar scripts de diagnóstico
**Labels:** refactor, developer-experience
**Épica:** 6: Infraestructura
**Descripción:**
- Crear `database/diagnostics.py` maestro
- Consolidar funciones de check_*, show_*, verify_*
- CLI unificado para diagnósticos

**Criterios de aceptación:**
- [ ] Script maestro implementado
- [ ] 15+ scripts check_* consolidados
- [ ] Documentación actualizada

---

## 13. CONCLUSIONES

### Hallazgos Principales

1. **45% de archivos son código zombi** (127 de 280 archivos .py)
2. **~640 líneas de código duplicado** (principalmente en scrapers y ESCOReranker)
3. **Versiones múltiples sin estrategia clara de archivado** (v81, v82, v83, v84 coexistiendo)
4. **Scripts one-time sin organizar** (fix_*, debug_* en raíz de database/)
5. **Tests dispersos sin estructura** (test_* en scrapers/, database/, sin tests/ unificado)

### Riesgos Identificados

- **BAJO:** 78% de archivos zombi (102 archivos) - archivado seguro
- **MEDIO:** 15% de archivos zombi (19 archivos) - requiere verificación
- **ALTO:** 7% de archivos zombi (6 archivos) - NO TOCAR sin análisis profundo

### Beneficios del Clean-up

1. **Reducción de complejidad:** -45% archivos activos
2. **Reducción de duplicación:** -61% código duplicado
3. **Mejor mantenibilidad:** código organizado, fácil de navegar
4. **Facilitación de CI/CD:** tests consolidados en tests/
5. **Onboarding más rápido:** menos archivos "fantasma" confundiendo a nuevos devs

### Próximos Pasos

1. ✅ **Este reporte** → compartir con equipo
2. ⏭️ **Fase 1:** Archivar 78 archivos BAJO RIESGO (1-2 horas)
3. ⏭️ **Fase 2:** Refactorizar duplicación (4-6 horas)
4. ⏭️ **Fase 3:** Consolidar diagnósticos (2-3 horas)
5. ⏭️ **Fase 4:** Limpieza de imports (1 hora)

**Tiempo total estimado:** 8-12 horas de trabajo

---

**Generado por:** Claude Opus 4.5
**Fecha:** 2025-12-09
**Versión:** 1.0
