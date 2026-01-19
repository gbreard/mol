# MOL - Planificación Completa del Proyecto

> **Fecha:** 2025-12-02  
> **Proyecto Linear:** https://linear.app/molar/project/mol-monitor-ofertas-laborales-2a9662bfa15f

---

## 📊 Resumen Ejecutivo

| Métrica | Valor |
|---------|-------|
| **Total Issues** | 18 |
| **Carril A (Construcción)** | 10 issues |
| **Carril B (Optimización)** | 8 issues |
| **Prioridad Alta** | 3 issues |
| **Prioridad Media** | 7 issues |
| **Prioridad Baja** | 8 issues |

---

## 🏗️ Estructura de Dos Carriles

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           PROYECTO MOL                                      │
├─────────────────────────────────┬───────────────────────────────────────────┤
│  CARRIL A: CONSTRUCCIÓN         │  CARRIL B: OPTIMIZACIÓN                   │
│  (Tiene principio y fin)        │  (Mejora continua, iterativo)             │
├─────────────────────────────────┼───────────────────────────────────────────┤
│                                 │                                           │
│  📦 Infraestructura Base        │  🔄 Optimización Matching ESCO            │
│     7 issues                    │     5 issues                              │
│                                 │     Meta: Precisión >85%                  │
│  📦 Dashboard Usuario v3        │     Actual: ~80% (v8.3)                   │
│     2 issues                    │                                           │
│                                 │  🔄 Optimización NLP                      │
│  📋 General                     │     3 issues                              │
│     1 issue                     │     Meta: Cobertura >75%                  │
│                                 │     Actual: 60-70% (v4.0)                 │
│                                 │                                           │
└─────────────────────────────────┴───────────────────────────────────────────┘
```

---

## 🔴 CARRIL B: OPTIMIZACIÓN (8 Issues)

### Milestone: Optimización Matching ESCO
**Meta:** Precisión >85% | **Actual:** ~80% (v8.3) | **Medición:** test_gold_set_manual.py

| ID | Título | Prioridad | Descripción |
|----|--------|-----------|-------------|
| MOL-5 | [v8.4] Resolver errores sector_funcion (4 casos) | 🔴 Alta | 50% de errores del gold set. Casos: Account Executive, Analista admin, Asesor comercial |
| MOL-6 | Expandir Gold Set de 19 a 50+ casos | 🔴 Alta | Estratificar por sector, nivel y tipo de contrato |
| MOL-7 | Agregar métricas de Recall al benchmark | 🟡 Media | Solo medimos precisión, falta recall y F1 |
| MOL-8 | Resolver casos bilingües | 🟡 Media | "Account Executive" ≠ "Ejecutivo de cuentas" |
| MOL-9 | CI/CD: Test automático de gold set | ⚪ Baja | GitHub Action para proteger contra regresiones |

### Milestone: Optimización NLP
**Meta:** Cobertura >75% | **Actual:** 60-70% (regex v4) | **Pipeline:** 3 capas anti-alucinación

| ID | Título | Prioridad | Descripción |
|----|--------|-----------|-------------|
| MOL-10 | Regex v4.1: Agregar abreviaciones argentinas | 🟡 Media | Adm., Gte., Coord., Jfe., Aux. |
| MOL-11 | Mejorar detección de niveles jerárquicos | 🟡 Media | Junior/Senior/Lead/Manager |
| MOL-12 | Consolidar pipeline NLP v6 + v7 | ⚪ Baja | Unificar en un solo archivo con flags |

---

## 🔵 CARRIL A: CONSTRUCCIÓN (10 Issues)

### Milestone: Infraestructura Base (7 issues)

| ID | Título | Prioridad | Estado Actual |
|----|--------|-----------|---------------|
| MOL-18 | Automatizar scrapers faltantes (4 fuentes) | 🔴 Alta | Solo Bumeran automatizado, 4 fuentes manuales |
| MOL-19 | Automatizar pipeline completo post-scraping | 🟡 Media | NLP y Matching son manuales |
| MOL-14 | Implementar envío de alertas (email/Slack) | 🟡 Media | alert_manager.py existe pero email_enabled=False |
| MOL-15 | Limpieza de JSONs duplicados | ⚪ Baja | 10,800 archivos JSON, muchos duplicados |
| MOL-20 | Centralizar sistema de logs | ⚪ Baja | Logs distribuidos en múltiples carpetas |
| MOL-22 | Documentar APIs internas de scrapers | ⚪ Baja | Sin documentación formal |
| MOL-13 | Crear panel de administración centralizado | ⚪ Baja | No existe, todo es CLI |

### Milestone: Dashboard Usuario v3 (2 issues)

| ID | Título | Prioridad | Estado Actual |
|----|--------|-----------|---------------|
| MOL-16 | Resolver conflicto shinyTree (árbol ESCO) | 🟡 Media | Deshabilitado por bug input/output |
| MOL-17 | Rehabilitar autenticación shinymanager | ⚪ Baja | Deshabilitado para debug |

### General (1 issue)

| ID | Título | Prioridad | Estado Actual |
|----|--------|-----------|---------------|
| MOL-21 | Deprecar y limpiar dashboards antiguos | ⚪ Baja | v2, v3 de Python y R aún existen |

---

## 🎯 Prioridades Recomendadas

### Sprint 1 (Próximas 2 semanas)
| ID | Issue | Carril | Justificación |
|----|-------|--------|---------------|
| MOL-5 | Resolver sector_funcion | B | 50% de errores, alto impacto |
| MOL-6 | Expandir Gold Set | B | Base para medir mejoras |
| MOL-18 | Automatizar 4 scrapers | A | Solo 1/5 fuentes automatizadas |

### Sprint 2
| ID | Issue | Carril | Justificación |
|----|-------|--------|---------------|
| MOL-19 | Pipeline post-scraping | A | Automatizar NLP + Matching |
| MOL-7 | Métricas Recall | B | Completar benchmark |
| MOL-16 | Árbol ESCO shinyTree | A | Funcionalidad faltante en dashboard |

### Sprint 3+
| ID | Issue | Carril |
|----|-------|--------|
| MOL-8 | Casos bilingües | B |
| MOL-10 | Regex abreviaciones | B |
| MOL-11 | Niveles jerárquicos | B |
| MOL-14 | Alertas email/Slack | A |

### Backlog (cuando haya tiempo)
- MOL-9: CI/CD
- MOL-12: Consolidar NLP v6+v7
- MOL-13: Panel admin
- MOL-15: Limpieza JSONs
- MOL-17: Auth shinymanager
- MOL-20: Centralizar logs
- MOL-21: Deprecar dashboards
- MOL-22: Documentar APIs

---

## 📁 Archivos de Referencia

### Versiones Activas
| Componente | Archivo | Versión |
|------------|---------|---------|
| Matching Rules | `database/matching_rules_v83.py` | v8.3 |
| Matching Algorithm | `database/match_ofertas_multicriteria.py` | v8.1 |
| NLP Pipeline | `database/process_nlp_from_db_v7.py` | v8.0 |
| NLP Prompt | `02.5_nlp_extraction/prompts/extraction_prompt_v8.py` | v8.0 |
| Regex Patterns | `02.5_nlp_extraction/scripts/patterns/regex_patterns_v4.py` | v4.0 |
| Dashboard Producción | `Visual--/app.R` | v2.4.0 |
| Dashboard Validación | `Visual--/validacion_pipeline_app_v3.R` | v3 |
| Dashboard Scraping | `dashboard_scraping_v4.py` | v4 |
| Scheduler | `run_scheduler.py` | - |

### Gold Set y Validación
| Archivo | Propósito |
|---------|-----------|
| `database/gold_set_manual_v1.json` | 19 casos validados manualmente |
| `database/test_gold_set_manual.py` | Benchmark de precisión |
| `database/test_esco_matching_regression.py` | Tests de regresión |

---

## 🔗 Links Rápidos

### Linear
- **Proyecto:** https://linear.app/molar/project/mol-monitor-ofertas-laborales-2a9662bfa15f
- **Backlog:** https://linear.app/molar/team/MOL/backlog
- **Issues Alta Prioridad:** MOL-5, MOL-6, MOL-18

### Documentos Relacionados
- `STATUS.md` - Estado del proyecto (en repo)
- `CLAUDE.md` - Guía para Claude Code (en repo)
- `PROJECT_MAP.md` - Mapa de dependencias

### Dashboard Producción
- https://dos1tv-gerardo-breard.shinyapps.io/dashboard-esco-argentina

---

## 📝 Flujos de Trabajo

### Para trabajar en Carril B (Optimización)

```bash
# 1. Crear nueva versión de reglas
cp database/matching_rules_v83.py database/matching_rules_v84.py

# 2. Implementar cambios en v84

# 3. Validar con gold set
python database/test_gold_set_manual.py

# 4. Si mejora, ejecutar batch piloto
python database/run_batch_pilot.py --rules v84 --limit 100

# 5. Analizar resultados y decidir deploy
```

### Para trabajar en Carril A (Construcción)

```bash
# 1. Crear branch
git checkout -b feature/MOL-XX-descripcion

# 2. Implementar

# 3. Testear localmente

# 4. PR + merge

# 5. Deploy si aplica
```

---

## ⚠️ Reglas Críticas

1. **Nunca modificar sin backup:**
   - `database/bumeran_scraping.db`
   - `database/gold_set_manual_v1.json`
   - `database/matching_rules_v83.py` (crear v84)

2. **Siempre correr benchmark después de cambios en matching:**
   ```bash
   python database/test_gold_set_manual.py
   ```

3. **Documentar decisiones en Linear:**
   - Comentar en el issue qué se probó
   - Agregar métricas antes/después

---

**Documento generado:** 2025-12-02
