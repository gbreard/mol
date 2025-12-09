# MOL - Metodología Linear Integrada

> **Versión:** 2.0
> **Fecha:** 2025-12-03
> **Objetivo:** Integrar mejores prácticas de gestión de proyectos de ML/Data sin romper lo existente

---

## 1. Estructura Organizativa

### Team
```
Team: molar (ya existe)
```

### Project
```
Project: MOL - Monitor Ofertas Laborales (ya existe)
URL: https://linear.app/molar/project/mol-monitor-ofertas-laborales-2a9662bfa15f
```

---

## 2. Épicas (Milestones)

Reemplazar la estructura actual de "Carriles" por **6 Épicas** que reflejan mejor el flujo del sistema:

### Épica 1: Scraping y Captura
**Objetivo:** Traer ofertas de 5 plataformas con esquema común

| Issue | Título | Prioridad |
|-------|--------|-----------|
| MOL-18 | Automatizar scrapers faltantes | 🔴 Alta |
| MOL-22 | Documentar APIs de scrapers | ⚪ Baja |
| MOL-25 | Drift detection | 🟡 Media |

---

### Épica 2: Normalización y NLP
**Objetivo:** Parsear y estructurar información de ofertas

| Issue | Título | Prioridad |
|-------|--------|-----------|
| MOL-10 | Regex abreviaciones argentinas | ⚪ Baja |
| MOL-11 | Niveles jerárquicos | ⚪ Baja |
| MOL-12 | Consolidar NLP v6+v7 | ⚪ Baja |

---

### Épica 3: Matching ESCO
**Objetivo:** Asignar ocupaciones y skills ESCO a cada oferta

| Issue | Título | Prioridad | Tipo |
|-------|--------|-----------|------|
| MOL-5 | [v8.4] Resolver sector_funcion | 🔴 Alta | feature |
| MOL-8 | Resolver casos bilingües | 🟡 Media | feature |
| MOL-XX | Spike: probar modelo embeddings alternativo | 🟡 Media | spike |
| MOL-XX | Spike: prompt engineering para matching | 🟡 Media | spike |

**Nota:** Esta épica tiene issues de tipo `spike` (experimentos) y `feature` (productivización).

---

### Épica 4: Dashboards y Visualización
**Objetivo:** Tableros para usuarios finales y administradores

| Issue | Título | Prioridad | Dashboard |
|-------|--------|-----------|-----------|
| MOL-16 | Fix shinyTree | 🟡 Media | Usuario final |
| MOL-17 | Auth shinymanager | ⚪ Baja | Usuario final |
| MOL-13 | Panel administración | ⚪ Baja | Admin |
| MOL-21 | Deprecar dashboards antiguos | ⚪ Baja | Limpieza |

---

### Épica 5: Evaluación de Calidad
**Objetivo:** Medir y mejorar calidad del matching

| Issue | Título | Prioridad |
|-------|--------|-----------|
| MOL-6 | Expandir Gold Set a 50+ | 🔴 Alta |
| MOL-7 | Métricas Recall y F1 | 🟡 Media |
| MOL-9 | CI/CD tests automáticos | ⚪ Baja |

---

### Épica 6: Infraestructura
**Objetivo:** Soporte técnico del sistema

| Issue | Título | Prioridad |
|-------|--------|-----------|
| MOL-26 | Backup automático SQLite | 🔴 Alta |
| MOL-23 | Versionado de datos | 🔴 Alta |
| MOL-14 | Alertas email/Slack | 🟡 Media |
| MOL-19 | Pipeline automático post-scraping | 🟡 Media |
| MOL-20 | Centralizar logs | ⚪ Baja |
| MOL-15 | Limpieza JSONs | ⚪ Baja |
| MOL-24 | Entity resolution cross-source | 🟡 Media |

---

## 3. Workflow States

Expandir los estados actuales para reflejar mejor el ciclo de vida:

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                              WORKFLOW STATES                                  │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────┐    ┌───────────┐    ┌────────────────┐    ┌───────────┐        │
│  │ Backlog │───▶│Por diseñar│───▶│En implementación│───▶│ En pruebas│        │
│  └─────────┘    └───────────┘    └────────────────┘    └─────┬─────┘        │
│                                                              │               │
│                      ┌───────────────────────────────────────┘               │
│                      ▼                                                       │
│               ┌──────────────┐    ┌─────────────────────┐                   │
│               │En producción │───▶│Monitoreando/Afinando│                   │
│               └──────────────┘    └─────────────────────┘                   │
│                                                                              │
│  PARA SPIKES:                                                                │
│  ┌─────────┐    ┌───────────────┐    ┌──────────────────┐                   │
│  │ Backlog │───▶│Experimentando │───▶│Decisión (Go/NoGo)│                   │
│  └─────────┘    └───────────────┘    └──────────────────┘                   │
│                                           │                                  │
│                          ┌────────────────┴────────────────┐                │
│                          ▼                                 ▼                │
│                   ┌────────────┐                    ┌────────────┐          │
│                   │ Descartado │                    │Productivizar│          │
│                   │   (Done)   │                    │ (→ feature) │          │
│                   └────────────┘                    └────────────┘          │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Descripción de estados

| Estado | Descripción | Cuándo usar |
|--------|-------------|-------------|
| **Backlog** | Idea priorizada pero no iniciada | Issues nuevos |
| **Por diseñar** | Requiere análisis antes de implementar | Issues complejos |
| **En implementación** | Código siendo escrito | Durante desarrollo |
| **En pruebas** | Código listo, validando | Después de implementar |
| **En producción** | Deployado y funcionando | Post-merge |
| **Monitoreando/Afinando** | En prod pero requiere seguimiento | Matching, NLP |
| **Experimentando** | Spike en curso | Para spikes |
| **Decisión (Go/NoGo)** | Spike terminado, esperando decisión | Fin de spike |

---

## 4. Labels

### Labels por Módulo Técnico

| Label | Color | Uso |
|-------|-------|-----|
| `scraping` | 🔵 Azul | Código que baja info de plataformas |
| `etl` | 🟢 Verde | Transformaciones, carga a BD |
| `nlp` | 🟣 Púrpura | Parseo, extracción de texto |
| `esco` | 🟠 Naranja | Todo lo que toque taxonomía ESCO |
| `matching` | 🔴 Rojo | Lógica de asignar ofertas → ocupaciones |
| `embeddings` | 🟡 Amarillo | Vectores para similitud |
| `dashboard` | 🔷 Celeste | Visualizaciones, tableros |
| `api` | ⚫ Negro | Endpoints |
| `eval-calidad` | 🟤 Marrón | Evaluaciones, benchmarks, gold set |
| `infra` | ⬜ Gris | Infraestructura, backups, logs |

### Labels por Tipo de Trabajo

| Label | Descripción | Cuándo usar |
|-------|-------------|-------------|
| `feature` | Funcionalidad nueva | La mayoría de issues |
| `bug` | Corrección de error | Algo roto |
| `refactor` | Mejora sin cambiar funcionalidad | Limpieza de código |
| `spike` | **Experimento/Investigación** | Probar nuevos modelos, prompts |
| `tech-debt` | Deuda técnica | Código que "funciona pero..." |
| `docs` | Documentación | README, CHANGELOG, etc. |

### Regla clave para `spike`

```
UN SPIKE SIEMPRE TERMINA EN UNA DECISIÓN:
├── "Lo descartamos" → Estado: Done, comentario con conclusión
└── "Vale la pena" → Crear nuevo issue tipo `feature` para productivizar
```

---

## 5. Custom Fields

### Campo 1: Tipo de Artefacto

| Valor | Descripción | Ejemplos |
|-------|-------------|----------|
| `Pipeline datos` | Scripts de ETL/scraping | bumeran_scraper.py, consolidar_fuentes.py |
| `Matching/Modelo` | Lógica de ML/matching | match_ofertas_multicriteria.py, matching_rules_v84.py |
| `Dashboard` | Visualizaciones | app.R, validacion_pipeline_app_v3.R |
| `Infraestructura` | Soporte técnico | backup_database.py, alert_manager.py |
| `Evaluación` | Testing y benchmarks | test_gold_set_manual.py |

### Campo 2: Madurez

| Valor | Descripción | Cuándo asignar |
|-------|-------------|----------------|
| `Experimento` | En fase de prueba, puede fallar | Spikes, versiones nuevas |
| `Beta` | Funciona pero no validado completamente | Después de spike exitoso |
| `Estable` | Validado y en producción | Cuando pasa gold set + batch piloto |

### Mapeo de versiones actuales a Madurez

| Componente | Versión | Madurez |
|------------|---------|---------|
| Matching Rules | v8.3 | Estable |
| Matching Rules | v8.4 (futuro) | Experimento → Beta |
| NLP Pipeline | v8.0 | Estable |
| Regex Patterns | v4.0 | Estable |
| Gold Set | v1 (19 casos) | Beta |
| Gold Set | v2 (50+ casos, futuro) | Experimento → Beta |

---

## 6. Dos Tipos de Dashboard

### Dashboard de Experimentos (Interno)

**Propósito:** Laboratorio de modelos, para el desarrollador
**Aplicación:** `Visual--/validacion_pipeline_app_v3.R`
**Puerto:** 3853

**Métricas que muestra:**
- Precisión/Recall/F1 del gold set
- Comparación entre versiones de matching
- Casos problemáticos por tipo de error
- Resultados de spikes en curso

**Quién lo usa:**
- Desarrollador (Gerardo)
- Claude Code (para validar)

---

### Dashboard de Usuarios Finales (Producción)

**Propósito:** Monitor de demanda laboral para analistas
**Aplicación:** `Visual--/app.R`
**URL:** https://dos1tv-gerardo-breard.shinyapps.io/dashboard-esco-argentina

**Métricas que muestra:**
- Demanda por ocupación ESCO
- Top skills requeridos
- Evolución temporal
- Distribución geográfica

**Quién lo usa:**
- Analistas de políticas laborales (OEDE)
- Administradores del sistema

---

### Dashboard Admin (Futuro - MOL-13)

**Propósito:** Operación del sistema
**Aplicación:** `admin/admin_panel.py` (a crear)
**Puerto:** 8053

**Funcionalidades:**
- Estado de scrapers
- Ejecución manual de tareas
- Logs recientes
- Alertas

---

## 7. Ciclo de Mejora Continua (Matching/NLP)

Este es el flujo para trabajos de optimización (Carril B / Épicas 3 y 5):

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    CICLO DE MEJORA CONTINUA                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. IDENTIFICAR PROBLEMA                                                    │
│     └─▶ Revisar errores en gold set                                        │
│     └─▶ Analizar casos problemáticos en dash de experimentos               │
│                                                                             │
│  2. CREAR SPIKE                                                             │
│     Issue tipo: spike                                                       │
│     Madurez: Experimento                                                    │
│     Objetivo: probar hipótesis (nuevo modelo, prompt, regla)               │
│                                                                             │
│  3. EXPERIMENTAR                                                            │
│     └─▶ Implementar cambio en versión experimental (v8.4-exp)              │
│     └─▶ Medir contra gold set                                              │
│     └─▶ Documentar resultados en comentario del issue                      │
│                                                                             │
│  4. DECISIÓN                                                                │
│     ├─▶ NO SIRVE: Cerrar spike, documentar aprendizaje                     │
│     └─▶ SIRVE: Crear issue feature para productivizar                      │
│                                                                             │
│  5. PRODUCTIVIZAR (si sirve)                                                │
│     └─▶ Limpiar código experimental                                        │
│     └─▶ Crear versión oficial (v8.4)                                       │
│     └─▶ Batch piloto (100 ofertas)                                         │
│     └─▶ Deploy a producción                                                │
│     └─▶ Cambiar Madurez: Experimento → Beta → Estable                      │
│                                                                             │
│  6. DOCUMENTAR                                                              │
│     └─▶ Agregar entrada en CHANGELOG.md                                    │
│     └─▶ Actualizar STATUS.md                                               │
│     └─▶ Comentar en Linear                                                 │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 8. Ejemplos de Issues con Nueva Metodología

### Ejemplo 1: Spike de experimento

```
Título: Spike: probar modelo de embeddings multilingual-e5 para matching ESCO

Épica: Épica 3 - Matching ESCO
Labels: matching, esco, embeddings, eval-calidad, spike
Tipo de artefacto: Matching/Modelo
Madurez: Experimento
Prioridad: Media

Contexto:
BGE-M3 actual tiene problemas con títulos en inglés (Account Executive).
Hipótesis: multilingual-e5 podría tener mejor representación cross-lingual.

Objetivo:
Evaluar si multilingual-e5 mejora F1 en casos bilingües del gold set.

Criterios de aceptación:
- [ ] Implementar función de matching con e5 (no reemplazar BGE-M3)
- [ ] Medir F1 en gold set completo
- [ ] Medir F1 específicamente en casos bilingües (5 casos)
- [ ] Documentar resultados comparativos
- [ ] Decisión: Go/NoGo documentada

Resultado esperado:
NO es código listo para producción, sino:
- Conclusión: "mejora F1 de X a Y" o "no mejora significativamente"
- Si mejora: crear issue feature para integrar al pipeline
```

---

### Ejemplo 2: Feature de productivización

```
Título: Integrar modelo multilingual-e5 al pipeline de matching

Épica: Épica 3 - Matching ESCO
Labels: matching, esco, embeddings, feature
Tipo de artefacto: Matching/Modelo
Madurez: Beta
Prioridad: Alta
Depende de: Spike multilingual-e5 (exitoso)

Contexto:
El spike demostró que multilingual-e5 mejora F1 en casos bilingües de 0.52 a 0.68.
Este issue productiviza ese experimento.

Objetivo:
Reemplazar BGE-M3 por multilingual-e5 en el pipeline oficial de matching.

Criterios de aceptación:
- [ ] Refactorizar match_ofertas_multicriteria.py para usar e5
- [ ] Regenerar embeddings de ocupaciones ESCO
- [ ] Validar con gold set: F1 >= 0.65
- [ ] Batch piloto: 100 ofertas sin errores
- [ ] Actualizar CHANGELOG.md
- [ ] Cambiar Madurez a Estable después de 1 semana en prod

Verificación:
python database/test_gold_set_manual.py
# F1 >= 0.65
```

---

## 9. Migración: Plan de Implementación

### Paso 1: Crear Épicas en Linear (15 min)
```
1. Épica 1: Scraping y Captura
2. Épica 2: Normalización y NLP
3. Épica 3: Matching ESCO
4. Épica 4: Dashboards y Visualización
5. Épica 5: Evaluación de Calidad
6. Épica 6: Infraestructura
```

### Paso 2: Configurar Labels (10 min)
Agregar los labels faltantes:
- spike
- tech-debt
- embeddings
- eval-calidad
- etl

### Paso 3: Configurar Custom Fields (10 min)
- Tipo de artefacto (dropdown)
- Madurez (dropdown)

### Paso 4: Reasignar Issues a Épicas (20 min)
Mover cada MOL-XX a su épica correspondiente

### Paso 5: Agregar Spikes identificados (15 min)
Crear issues tipo spike para experimentos conocidos:
- Spike: probar embeddings alternativos
- Spike: prompt engineering para matching
- Spike: NER con spaCy vs regex

### Paso 6: Actualizar CLAUDE.md (10 min)
Agregar referencia a esta metodología

---

## 10. Resumen de Cambios vs. Estructura Anterior

| Antes | Después | Beneficio |
|-------|---------|-----------|
| Carril A/B | 6 Épicas temáticas | Mejor organización por dominio |
| Sin tipo spike | Label spike + workflow | Distinguir experimentos de features |
| Versionado implícito | Custom field Madurez | Visualizar estado de cada componente |
| Un dashboard | Dos dashboards explícitos | Separar experimentos de producción |
| Issues planos | Issues con estructura estándar | Contexto completo para trabajo autónomo |

---

> **Documento generado:** 2025-12-03
> **Próximos pasos:** Implementar en Linear con Claude Code
