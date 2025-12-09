# MOL - Estado del Proyecto

> **Última actualización:** 2025-12-04  
> **Linear:** https://linear.app/molar/project/mol-monitor-ofertas-laborales-2a9662bfa15f

---

## 🎯 Versiones Activas

### Pipeline NLP (v8.0)
```
Capa 0: regex_patterns_v4.py      → 60-70% campos con 100% precisión
Capa 1: extraction_prompt_v8.py   → Qwen2.5:14b, anti-alucinación
Capa 2: process_nlp_from_db_v7.py → Post-validación 3 capas
```

| Archivo | Versión | Modelo | Descripción |
|---------|---------|--------|-------------|
| `regex_patterns_v4.py` | v4.0 | - | 7 clases, 200+ oficios argentinos |
| `extraction_prompt_v8.py` | v8.0 | Qwen2.5:14b | Ultra-conservador, ejemplos negativos |
| `process_nlp_from_db_v7.py` | v8.0 | Qwen2.5:14b | Pipeline principal activo |

### Pipeline Matching ESCO (v8.3)
```
Paso 1: match_ofertas_multicriteria.py → Título(50%) + Skills(40%) + Descripción(10%)
Paso 2: matching_rules_v83.py          → 6 familias funcionales + 10 reglas never_confirm
```

| Archivo | Versión | Descripción |
|---------|---------|-------------|
| `match_ofertas_multicriteria.py` | v8.1 | Algoritmo 4 pasos, BGE-M3 + ESCO-XLM |
| `matching_rules_v83.py` | v8.3 | Familias funcionales + tareas 5-8 |

---

## 📊 Métricas Actuales

### Matching ESCO
| Métrica | Valor | Objetivo |
|---------|-------|----------|
| Precisión (Gold Set 19) | ~80% (v8.3) | >85% |
| Gold Set Size | 19 casos | 50+ casos |
| Familias funcionales | 6 | 10+ |
| Reglas never_confirm | 10 | Según necesidad |

### Distribución de Errores (Gold Set)
| Tipo Error | Casos | % |
|------------|-------|---|
| sector_funcion | 4 | 50% |
| nivel_jerarquico | 2 | 25% |
| tipo_ocupacion | 1 | 12.5% |
| programa_general | 1 | 12.5% |

### NLP Pipeline
| Métrica | Valor | Objetivo |
|---------|-------|----------|
| Cobertura Regex | 60-70% | 75% |
| Modelo activo | Qwen2.5:14b | - |
| Capas anti-alucinación | 3 | Mantener |

### Base de Datos
| Tabla | Registros |
|-------|-----------|
| ofertas | 6,521 |
| ofertas_nlp | 5,479 (84%) |
| ofertas_esco_matching | 6,521 |
| esco_occupations | 3,045 |
| esco_associations | 134,805 |

---

## 📁 Archivos Clave

### Matching (database/)
```
matching_rules_v83.py     ← ACTIVO (reglas de ajuste)
matching_rules_v82.py     ← Anterior
matching_rules_v81.py     ← Anterior
match_ofertas_multicriteria.py ← ACTIVO (algoritmo principal)
match_ofertas_to_esco.py  ← LEGACY (no usar)
gold_set_manual_v1.json   ← Gold set 19 casos
```

### NLP (02.5_nlp_extraction/)
```
prompts/extraction_prompt_v8.py  ← ACTIVO
prompts/extraction_prompt_v7.py  ← Anterior
prompts/extraction_prompt_v6.py  ← Anterior
scripts/patterns/regex_patterns_v4.py ← ACTIVO
```

### Procesadores (database/)
```
process_nlp_from_db_v7.py  ← ACTIVO (Qwen2.5:14b)
process_nlp_from_db_v6.py  ← ANTERIOR (Hermes 3:8b)
```

### Validación (database/)
```
test_gold_set_manual.py           ← Benchmark principal
test_esco_matching_regression.py  ← Tests de regresión
apply_v82_rules_gold19.py         ← Aplicar reglas a gold set
simulate_v81_gold19.py            ← Simular sin modificar DB
```

---

## 🔄 Flujo de Optimización

### Para mejorar Matching (v8.X → v8.X+1)
```
1. Identificar errores en batch CSV
2. Diseñar reglas (keywords, detectores)
3. Implementar en matching_rules_v8X.py
4. Validar: python test_gold_set_manual.py
5. Batch piloto: python run_batch_pilot_v8.py --rules v8.X --limit 100
6. Si mejora → deploy
```

### Criterios de Éxito
```python
CRITERIOS = {
    "precision_minima": 50.0,
    "top_3_match": True,
    "isco_correcto": True,
    "no_absurdos": True,
    "score_rango": (0.40, 0.95)
}
```

---

## 📁 Estructura por Épicas

| Épica | Issues | Descripción |
|-------|--------|-------------|
| 1. Scraping y Captura | 3 | Extracción de portales de empleo |
| 2. Normalización y NLP | 4 | Parseo y estructuración de ofertas |
| 3. Matching ESCO | 4 | Clasificación ocupacional |
| 4. Dashboards | 4 | Visualización para usuarios y admin |
| 5. Evaluación de Calidad | 3 | Gold set, métricas, CI/CD |
| 6. Infraestructura | 7 | Backups, logs, alertas, versionado |

**Total:** 29 issues (26 features + 3 spikes)

### Tipos de Issues
- `feature`: Funcionalidad nueva → va a producción
- `spike`: Experimento → termina en decisión Go/NoGo
- `bug`: Corrección de error
- `refactor`: Mejora sin cambiar funcionalidad

---

## 📋 Linear - Todos los Issues (29 total)

### 🔴 Prioridad Alta (5)
| ID | Issue | Épica |
|----|-------|-------|
| MOL-5 | [v8.4] Resolver errores sector_funcion (4 casos) | 3: Matching ESCO |
| MOL-6 | Expandir Gold Set de 19 a 50+ casos | 5: Evaluación |
| MOL-18 | Automatizar scrapers faltantes (4 fuentes) | 1: Scraping |
| MOL-23 | Backup automático de SQLite | 6: Infraestructura |
| MOL-24 | Versionado de datos (gold sets, snapshots) | 6: Infraestructura |

### 🟡 Prioridad Media (10)
| ID | Issue | Épica |
|----|-------|-------|
| MOL-7 | Agregar métricas de Recall al benchmark | 5: Evaluación |
| MOL-8 | Resolver casos bilingües | 3: Matching ESCO |
| MOL-14 | Implementar envío de alertas (email/Slack) | 6: Infraestructura |
| MOL-16 | Resolver conflicto shinyTree (árbol ESCO) | 4: Dashboards |
| MOL-19 | Automatizar pipeline completo post-scraping | 6: Infraestructura |
| MOL-25 | Entity Resolution cross-source | 6: Infraestructura |
| MOL-26 | Drift Detection (anomalías scraping) | 1: Scraping |
| MOL-27 | **Spike:** embeddings multilingual-e5 | 3: Matching ESCO |
| MOL-28 | **Spike:** NER spaCy vs regex | 2: NLP |
| MOL-29 | **Spike:** prompt engineering LLM | 3: Matching ESCO |

### ⚪ Prioridad Baja (10)
| ID | Issue | Épica |
|----|-------|-------|
| MOL-9 | CI/CD: Test automático de gold set | 5: Evaluación |
| MOL-10 | Regex v4.1: Abreviaciones argentinas | 2: NLP |
| MOL-11 | Mejorar detección niveles jerárquicos | 2: NLP |
| MOL-12 | Consolidar pipeline NLP v6 + v7 | 2: NLP |
| MOL-13 | Crear panel de administración centralizado | 4: Dashboards |
| MOL-15 | Limpieza de JSONs duplicados (10,800) | 6: Infraestructura |
| MOL-17 | Rehabilitar autenticación shinymanager | 4: Dashboards |
| MOL-20 | Centralizar sistema de logs | 6: Infraestructura |
| MOL-21 | Deprecar y limpiar dashboards antiguos | 4: Dashboards |
| MOL-22 | Documentar APIs internas de scrapers | 1: Scraping |

---

## 🚀 Comandos Frecuentes

```bash
# Correr benchmark de matching
python database/test_gold_set_manual.py

# Procesar NLP (batch)
python database/process_nlp_from_db_v7.py --limit 100

# Matching ESCO (batch)
python database/match_ofertas_multicriteria.py --limit 100

# Simular reglas nuevas
python database/simulate_v81_gold19.py

# Dashboard validación (puerto 3853)
Rscript -e "shiny::runApp('Visual--/validacion_pipeline_app_v3.R', port=3853)"
```

---

## ⚠️ NO TOCAR SIN BACKUP

1. **Base de datos:** `database/bumeran_scraping.db`
2. **Gold set:** `database/gold_set_manual_v1.json`
3. **Reglas activas:** `database/matching_rules_v83.py`
4. **Pipeline activo:** `database/process_nlp_from_db_v7.py`

---

## 📝 Historial de Versiones

| Fecha | Componente | Cambio |
|-------|------------|--------|
| 2025-11-28 | Matching v8.3 | Familias funcionales + tareas 5-8 |
| 2025-11-28 | Matching v8.2 | 6 familias + never_confirm |
| 2025-11-28 | Matching v8.1 | Reglas basadas en gold set 19 |
| 2025-11-27 | NLP v8.0 | Qwen2.5:14b + anti-alucinación 3 capas |
| 2025-11-27 | Regex v4.0 | 7 clases nuevas, 60-70% precisión |

---

## 🔗 Links

- **Linear:** https://linear.app/molar/project/mol-monitor-ofertas-laborales-2a9662bfa15f
- **GitHub:** https://github.com/gbreard/mol
- **Dashboard Shiny:** [shinyapps.io URL]
