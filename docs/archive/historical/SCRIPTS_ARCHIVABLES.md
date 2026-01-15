# Scripts Archivables - MOL

> Generado: 2025-12-09
> Propósito: Lista de scripts que pueden moverse a `archive/` después de validar

---

## 1. Scripts Migrados a tests/ (ARCHIVAR)

Estos scripts fueron reemplazados por tests pytest en `tests/`:

| Script Legacy | Nuevo Test | Motivo |
|--------------|-----------|--------|
| `database/test_gold_set_manual.py` | `tests/matching/test_precision.py` | Migrado a pytest |
| `database/check_gold_set_precision.py` | `tests/matching/test_precision.py` | Duplicado |
| `database/check_gold_set_v2_precision.py` | `tests/matching/test_precision.py` | Duplicado |
| `database/verify_gold_set_nlp.py` | `tests/nlp/test_extraction.py` | Migrado a pytest |

---

## 2. Scripts de Debug One-Time (ARCHIVAR)

Scripts creados para depurar problemas específicos ya resueltos:

| Script | Problema Original | Estado |
|--------|------------------|--------|
| `database/debug_v81_join.py` | Debug join v8.1 | Resuelto |
| `database/debug_mozo_boost.py` | Boost específico para "mozo" | Resuelto |
| `database/debug_mozo_candidates.py` | Candidatos matching "mozo" | Resuelto |
| `database/test_session_fix.py` | Fix de sesión SQLite | Resuelto |
| `database/test_bypass.py` | Testing de bypass | One-time |
| `database/test_dual_write.py` | Dual write experiment | Completado |
| `database/check_repositor_result.py` | Check específico | One-time |
| `database/check_nivel_cases.py` | Casos nivel jerárquico | One-time |

---

## 3. Scripts de Versiones Obsoletas (ARCHIVAR)

Scripts para versiones ya no activas (v8.1, v8.2, etc.):

| Script | Versión | Activo |
|--------|---------|--------|
| `database/check_v81_skills.py` | v8.1 | ❌ (ahora v8.3) |
| `database/check_v81_ofertas.py` | v8.1 | ❌ (ahora v8.3) |
| `database/check_v81_progress.py` | v8.1 | ❌ (ahora v8.3) |
| `database/check_v84_improvements.py` | v8.4 | ❌ (experimental) |
| `database/verify_v82_confirmados.py` | v8.2 | ❌ (ahora v8.3) |
| `database/test_nlp_v6.py` | NLP v6 | ❌ (ahora v8) |
| `database/test_patterns_v2.py` | Patterns v2 | ❌ (ahora v4) |

---

## 4. Scripts Duplicados (MANTENER UNO)

Scripts con funcionalidad similar - mantener el mejor:

| Scripts | Mantener | Archivar |
|---------|----------|----------|
| `check_db_stats.py`, `check_db_structure.py` | `check_db_structure.py` | `check_db_stats.py` |
| `check_schema.py`, `check_esco_isco_schema.py` | `check_esco_isco_schema.py` | `check_schema.py` |
| `check_nlp_status.py`, `check_nlp_pending.py` | `check_nlp_status.py` | `check_nlp_pending.py` |

---

## 5. Scripts Útiles (MANTENER)

Scripts que siguen siendo útiles y NO deben archivarse:

### Validación de datos
- `database/check_ofertas_stats.py` - Estadísticas de ofertas
- `database/verify_data_quality.py` - Calidad de datos
- `database/verify_matches.py` - Verificar matches ESCO
- `database/verify_nlp_matching_sync.py` - Sincronización NLP-Matching

### Estructura ESCO
- `database/check_esco_structure.py` - Estructura taxonomía ESCO
- `database/check_isco_subdivisions.py` - Subdivisiones ISCO
- `database/check_isco_mapping.py` - Mapping ISCO

### ChromaDB/Embeddings
- `database/check_chromadb_results.py` - Resultados ChromaDB

### Tests de regresión
- `database/test_nlp_v8_regression.py` - Regresión NLP v8 (MANTENER)
- `database/test_esco_matching_regression.py` - Regresión matching (MANTENER)
- `database/test_validacion_incremental.py` - Validación incremental (MANTENER)

### Otros
- `database/check_diccionario_db.py` - Diccionario local
- `database/check_source_classification.py` - Clasificación por fuente
- `database/check_dict_source.py` - Fuentes de diccionario
- `database/check_processing_order.py` - Orden de procesamiento
- `database/check_nlp_v8_matching_status.py` - Estado actual v8

---

## Resumen

| Categoría | Cantidad | Acción |
|-----------|----------|--------|
| Migrados a pytest | 4 | ARCHIVAR |
| Debug one-time | 8 | ARCHIVAR |
| Versiones obsoletas | 7 | ARCHIVAR |
| Duplicados | 3 | ARCHIVAR uno |
| **Total archivables** | **22** | - |
| Útiles a mantener | 14 | MANTENER |

---

## Comando para archivar

```bash
# Crear directorio archive
mkdir -p database/archive/legacy_tests

# Mover scripts migrados
mv database/test_gold_set_manual.py database/archive/legacy_tests/
mv database/check_gold_set_precision.py database/archive/legacy_tests/
mv database/check_gold_set_v2_precision.py database/archive/legacy_tests/
mv database/verify_gold_set_nlp.py database/archive/legacy_tests/

# Mover debug one-time
mv database/debug_*.py database/archive/legacy_tests/
mv database/test_session_fix.py database/archive/legacy_tests/
mv database/test_bypass.py database/archive/legacy_tests/
mv database/test_dual_write.py database/archive/legacy_tests/

# Mover versiones obsoletas
mv database/check_v81_*.py database/archive/legacy_tests/
mv database/check_v84_improvements.py database/archive/legacy_tests/
mv database/verify_v82_confirmados.py database/archive/legacy_tests/
mv database/test_nlp_v6.py database/archive/legacy_tests/
mv database/test_patterns_v2.py database/archive/legacy_tests/
```

---

## Próximos pasos

1. Validar con el equipo antes de archivar
2. Ejecutar `pytest tests/ -v` para confirmar cobertura
3. Archivar scripts según lista
4. Actualizar `.gitignore` si necesario

---

*Nota: NO eliminar scripts, solo mover a archive/ para mantener historial*
