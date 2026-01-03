# Código Zombi - Resumen Ejecutivo
**Proyecto MOL - 2025-12-09**

---

## Vista Rápida

| Categoría | Archivos | Líneas Código | Riesgo | Acción |
|-----------|----------|---------------|--------|--------|
| Versiones obsoletas | 42 | ~8,500 | BAJO | Archivar |
| Scripts test/debug/check | 35 | ~4,200 | BAJO | Consolidar |
| Scripts fix_* one-time | 7 | ~700 | BAJO | Archivar |
| Archivos huérfanos | 15 | ~3,800 | BAJO-MEDIO | Archivar |
| Código duplicado | 12 | ~640 | MEDIO | Refactorizar |
| **TOTAL** | **127** | **~17,840** | **78% BAJO** | **8-12 hrs** |

---

## Top 10 Archivos a Archivar (Prioridad Alta)

| # | Archivo | Categoría | Líneas | Razón |
|---|---------|-----------|--------|-------|
| 1 | `database/match_ofertas_to_esco.py` | Huérfano | 728 | Obsoleto, reemplazado por multicriteria |
| 2 | `database/process_nlp_from_db_v6.py` | Versión obsoleta | 900+ | Versión anterior, v7 es activo |
| 3 | `database/matching_rules_v81.py` | Versión obsoleta | 300+ | Solo usado por scripts one-time |
| 4 | `database/matching_rules_v82.py` | Versión obsoleta | 350+ | Solo usado por scripts one-time |
| 5 | `01_sources/zonajobs/scrapers/test_*.py` (8 archivos) | Tests exploración | 800+ | Exploración completada |
| 6 | `02.5_nlp_extraction/prompts/extraction_prompt_v5.py` | Versión obsoleta | 200 | v8 es activo |
| 7 | `02.5_nlp_extraction/prompts/extraction_prompt_v6.py` | Versión obsoleta | 250 | v8 es activo |
| 8 | `02.5_nlp_extraction/prompts/extraction_prompt_v7.py` | Versión obsoleta | 220 | v8 es activo |
| 9 | `database/evaluar_matching_esco.py` | Huérfano | 300 | No usado, función movida |
| 10 | `database/evaluar_matching_esco_v2.py` | Huérfano | 280 | No usado, función movida |

**Impacto:** Archivar estos 10 archivos/grupos elimina ~4,300 líneas de código zombi.

---

## Código Duplicado - Alta Prioridad

| Código Duplicado | Ubicaciones | Líneas Duplicadas | Ahorro Potencial |
|------------------|-------------|-------------------|------------------|
| **scrapear_con_diccionario.py** | 3 archivos | ~400 | ~300 líneas (refactor a clase base) |
| **ESCOReranker class** | 2 archivos | ~90 | ~90 líneas (extraer a módulo) |
| **analisis_completo.py** | 2 archivos | ~300 | ~300 líneas (eliminar duplicado) |
| **explorar_datos.py** | 2 archivos | ~200 | ~200 líneas (eliminar duplicado) |
| **manual_matcher vs claude_manual_matcher** | 2 archivos | ~150 | ~150 líneas (unificar) |
| **TOTAL** | 12 archivos | ~1,140 | **~1,040 líneas** |

---

## Quick Wins (Bajo Riesgo, Alto Impacto)

### 1. Eliminar Duplicados Accidentales (5 minutos)
```bash
rm D:\OEDE\Webscrapping\Webscrapping\analisis_completo.py
rm D:\OEDE\Webscrapping\Webscrapping\explorar_datos.py
```
**Ahorro:** 500 líneas

---

### 2. Archivar Scripts Fix One-Time (10 minutos)
```bash
mkdir -p database/archive_old_versions/scripts_one_time/fix_historical
mv database/fix_*.py database/archive_old_versions/scripts_one_time/fix_historical/
```
**Archivos:** 7 | **Ahorro:** 700 líneas

---

### 3. Archivar Prompts Obsoletos (5 minutos)
```bash
mkdir -p 02.5_nlp_extraction/archive/prompts_old
mv 02.5_nlp_extraction/prompts/extraction_prompt_v5.py 02.5_nlp_extraction/archive/prompts_old/
mv 02.5_nlp_extraction/prompts/extraction_prompt_v6.py 02.5_nlp_extraction/archive/prompts_old/
mv 02.5_nlp_extraction/prompts/extraction_prompt_v7.py 02.5_nlp_extraction/archive/prompts_old/
```
**Archivos:** 3 | **Ahorro:** 670 líneas

---

### 4. Archivar Patterns Obsoletos (5 minutos)
```bash
mkdir -p 02.5_nlp_extraction/archive/patterns_old
mv 02.5_nlp_extraction/scripts/patterns/regex_patterns.py 02.5_nlp_extraction/archive/patterns_old/
mv 02.5_nlp_extraction/scripts/patterns/regex_patterns_v2.py 02.5_nlp_extraction/archive/patterns_old/
```
**Archivos:** 2 | **Ahorro:** 600 líneas

---

### 5. Archivar Extractors Backup (2 minutos)
```bash
mkdir -p 02.5_nlp_extraction/archive/extractors_backup
mv 02.5_nlp_extraction/scripts/extractors/*_backup_20251101.py 02.5_nlp_extraction/archive/extractors_backup/
```
**Archivos:** 2 | **Ahorro:** 400 líneas

---

**TOTAL QUICK WINS:** 30 minutos | 14 archivos | ~2,870 líneas eliminadas

---

## Versiones Activas vs Obsoletas

### Matching Rules

| Versión | Estado | Usado Por | Acción |
|---------|--------|-----------|--------|
| v81 | OBSOLETO | `apply_v81_rules_gold19.py`, `simulate_v81_gold19.py` | Archivar |
| v82 | OBSOLETO | `verify_v82_confirmados.py` | Archivar |
| v83 | FALLBACK | `match_ofertas_multicriteria.py` (fallback) | Conservar temporalmente |
| v84 | **ACTIVO** | `match_ofertas_multicriteria.py` (primario) | **CONSERVAR** |

---

### NLP Processors

| Versión | Estado | Usado Por | Acción |
|---------|--------|-----------|--------|
| v4 | ARCHIVADO | Ya en `archive_old_versions/` | OK |
| v5 | ARCHIVADO | Ya en `archive_old_versions/` | OK |
| v6 | OBSOLETO | No usado (v7 es activo) | Archivar |
| v7 | **ACTIVO** | CLAUDE.md confirma como activo | **CONSERVAR** |

---

### Prompts

| Versión | Estado | Usado Por | Acción |
|---------|--------|-----------|--------|
| v5 | OBSOLETO | `process_nlp_from_db_v5.py` (archivado) | Archivar |
| v6 | OBSOLETO | `process_nlp_from_db_v6.py` (obsoleto) | Archivar |
| v7 | OBSOLETO | No encontradas referencias | Archivar |
| v8 | **ACTIVO** | `process_nlp_from_db_v7.py` (activo) | **CONSERVAR** |

---

### Patterns

| Versión | Estado | Usado Por | Acción |
|---------|--------|-----------|--------|
| v1 (sin sufijo) | OBSOLETO | `bumeran_extractor_v1_backup` | Archivar |
| v2 | OBSOLETO | `bumeran_extractor_v2_backup` | Archivar |
| v3 | DEPENDENCIA | Importado por v4 | **CONSERVAR** |
| v4 | **ACTIVO** | `process_nlp_from_db_v7.py` | **CONSERVAR** |

---

## Scripts Test/Debug/Check - Consolidación

### Scripts a Conservar (utilidad recurrente)

| Archivo | Razón | Ubicación Sugerida |
|---------|-------|-------------------|
| `test_gold_set_manual.py` | Benchmark crítico | `tests/benchmarks/` |
| `test_nlp_v8_regression.py` | Regresión NLP | `tests/regression/` |
| `test_esco_matching_regression.py` | Regresión matching | `tests/regression/` |
| `check_db_stats.py` | Diagnóstico DB | `database/diagnostics.py` (consolidar) |
| `check_nlp_status.py` | Estado NLP | `database/diagnostics.py` (consolidar) |
| `check_ofertas_stats.py` | Stats ofertas | `database/diagnostics.py` (consolidar) |

---

### Scripts a Archivar (one-time o específicos de versión)

| Patrón | Cantidad | Razón | Destino |
|--------|----------|-------|---------|
| `check_v81_*.py` | 3 | Específicos de v8.1 (obsoleto) | `archive/check_historical/` |
| `debug_*.py` | 3 | Debug one-time (problemas resueltos) | `archive/debug_historical/` |
| `fix_*.py` | 7 | Fixes aplicados (one-time) | `archive/fix_historical/` |
| `test_fase*.py` | 3 | Tests de fases completadas | `archive/tests_old/` |
| `01_sources/*/test_*.py` | 17 | Exploración de APIs (completada) | `archive_scrapers/*/tests_old/` |

**TOTAL:** 33 archivos

---

## Referencias a ESCO-XLM y ESCOReranker

### Archivos que Usan ESCO-XLM

| Archivo | Estado | Clase ESCOReranker | Líneas |
|---------|--------|--------------------|--------|
| `match_ofertas_to_esco.py` | OBSOLETO | Define clase (línea 63-153) | 728 |
| `match_ofertas_multicriteria.py` | **ACTIVO** | Define clase (línea 63-153) - DUPLICADO | 947 |
| `evaluar_matching_esco.py` | HUÉRFANO | Solo menciona en comentarios | 300 |
| `evaluar_matching_esco_v2.py` | HUÉRFANO | Solo menciona en comentarios | 280 |

**PROBLEMA:** Clase `ESCOReranker` está duplicada en 2 archivos (match_ofertas_to_esco.py y match_ofertas_multicriteria.py).

**SOLUCIÓN:**
1. Extraer `ESCOReranker` a `database/esco_reranker.py`
2. Archivar `match_ofertas_to_esco.py` (obsoleto)
3. Importar desde `esco_reranker.py` en `match_ofertas_multicriteria.py`

---

## Imports No Usados (Top 5)

| Archivo | Import No Usado | Línea |
|---------|-----------------|-------|
| `database/evaluar_matching_esco.py` | `from collections import Counter` | 20 |
| `database/evaluar_matching_esco_v2.py` | `import json` (verificar) | 19 |
| (Pendiente análisis completo con autoflake) | | |

**ACCIÓN:** Ejecutar `autoflake --remove-all-unused-imports` en todo el proyecto.

---

## Plan de Ejecución (Orden Recomendado)

### Semana 1: Quick Wins (4 horas)

| Día | Tarea | Tiempo | Archivos | Líneas |
|-----|-------|--------|----------|--------|
| Lun | Quick Wins 1-5 | 30 min | 14 | 2,870 |
| Lun | Archivar matching_rules v81, v82 | 30 min | 2 | 650 |
| Mar | Archivar process_nlp_from_db, v6 | 30 min | 2 | 950 |
| Mar | Archivar tests de exploración | 1 hr | 17 | 1,500 |
| Mie | Archivar check_v81_*, debug_* | 30 min | 6 | 600 |
| Mie | Verificar tests pasan | 1 hr | - | - |

**TOTAL Semana 1:** 4 horas | 41 archivos | ~6,570 líneas

---

### Semana 2: Refactoring (6 horas)

| Día | Tarea | Tiempo | Ahorro |
|-----|-------|--------|--------|
| Lun | Refactor: scrapear_con_diccionario (clase base) | 2 hrs | 300 líneas |
| Mar | Refactor: ESCOReranker (extraer módulo) | 1.5 hrs | 90 líneas |
| Mie | Consolidar: diagnostics.py maestro | 2 hrs | 15 scripts |
| Jue | Limpieza imports (autoflake) | 30 min | - |

**TOTAL Semana 2:** 6 horas | Reducción ~390 líneas duplicadas

---

### Semana 3: Documentación (2 horas)

| Día | Tarea | Tiempo |
|-----|-------|--------|
| Lun | Actualizar CLAUDE.md con nuevas rutas | 30 min |
| Mar | Actualizar ARCHITECTURE.md | 30 min |
| Mie | Crear MIGRATION_GUIDE.md (archivos movidos) | 1 hr |

**TOTAL Semana 3:** 2 horas

---

## Verificación Pre-Archivado (Checklist)

Antes de mover cualquier archivo, ejecutar:

```bash
# 1. Tests críticos pasan
python database/test_gold_set_manual.py
python database/test_nlp_v8_regression.py
python database/test_esco_matching_regression.py

# 2. Buscar imports de archivos a archivar
grep -r "matching_rules_v81" --include="*.py" --include="*.sh" .
grep -r "process_nlp_from_db_v6" --include="*.py" --include="*.sh" .
grep -r "extraction_prompt_v[567]" --include="*.py" .

# 3. Backup de database
python scripts/backup_database.py

# 4. Commit de seguridad
git add -A
git commit -m "chore: backup pre-archivado codigo zombi"
git tag backup-pre-cleanup-2025-12-09
```

---

## Impacto Estimado

### Antes

- **Archivos .py totales:** 280
- **Código zombi:** 127 archivos (45%)
- **Código duplicado:** ~640 líneas
- **Complejidad:** Alta (muchas versiones coexistiendo)

### Después (Proyectado)

- **Archivos .py activos:** ~150 (-46%)
- **Código zombi:** 0 archivos (-100%)
- **Código duplicado:** ~250 líneas (-61%)
- **Complejidad:** Media-Baja (1 versión activa por componente)

### ROI

- **Tiempo invertido:** 12 horas
- **Reducción de líneas:** ~7,000 líneas de código zombi
- **Reducción de archivos:** 127 archivos archivados/consolidados
- **Mejora mantenibilidad:** -45% complejidad
- **Facilita onboarding:** Estructura clara, sin "archivos fantasma"

---

## Issues Linear Sugeridos

1. **MOL-XX: Archivar código zombi - Fase 1 (versiones obsoletas)**
   - Labels: refactor, technical-debt
   - Épica: 6: Infraestructura
   - Estimado: 4 horas

2. **MOL-XX: Refactorizar código duplicado - Scrapers**
   - Labels: refactor, technical-debt
   - Épica: 1: Scraping
   - Estimado: 2 horas

3. **MOL-XX: Consolidar scripts de diagnóstico**
   - Labels: refactor, developer-experience
   - Épica: 6: Infraestructura
   - Estimado: 2 horas

4. **MOL-XX: Extraer ESCOReranker a módulo separado**
   - Labels: refactor, technical-debt
   - Épica: 3: Matching ESCO
   - Estimado: 1.5 horas

---

## Contacto

**Análisis generado por:** Claude Opus 4.5
**Fecha:** 2025-12-09
**Reportar issues:** Ver ANALISIS_CODIGO_ZOMBI_2025-12-09.md (completo)
