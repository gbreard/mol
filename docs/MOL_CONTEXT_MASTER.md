# MOL - Contexto Maestro del Sistema

> **Versión:** 3.0
> **Fecha:** 2025-12-07
> **Propósito:** Documento de referencia completo para Claude Code

---

## 1. Estado Actual del Sistema

### 1.1 Métricas de Datos

| Métrica | Valor | Fecha |
|---------|-------|-------|
| Ofertas en BD | 9,564 | 2025-12-06 |
| IDs en tracking | 10,223 | 2025-12-06 |
| Cobertura estimada | 89% | 2025-12-06 |
| Keywords activos | 1,148 | - |
| Portales activos | 1 (Bumeran) | - |
| Portales pendientes | 4 | ZonaJobs, Computrabajo, LinkedIn, Indeed |

### 1.2 Versiones de Componentes

| Componente | Versión | Estado | Precisión |
|------------|---------|--------|-----------|
| NLP Pipeline | v8.0 | Estable | ~90% |
| Regex Patterns | v4.0 | Estable | 60-70% campos |
| Matching Rules | v8.3 | Estable | 78.9% |
| Gold Set NLP | Pendiente | Por crear | - |
| Gold Set Matching | v1 (19 casos) | Beta | - |
| ESCO Ontology | v1.2.0 | Cargada | 99.96% skill_type |

### 1.3 Infraestructura

| Componente | Tecnología | Estado |
|------------|------------|--------|
| Base de datos | SQLite | ✅ Operativo |
| LLM local | Ollama (Qwen2.5:14b) | ✅ Operativo |
| Embeddings | ChromaDB | ✅ Operativo |
| Scraping | API REST + Selenium | ✅ Operativo |
| Storage cloud | AWS S3 (sa-east-1) | ✅ Configurado |
| Dashboard local | Streamlit | Pendiente |
| Dashboard validación | Vercel (Next.js) | Pendiente |
| Dashboard producción | Vercel (Next.js) | Pendiente |

---

## 2. Arquitectura del Sistema

### 2.1 Flujo Principal

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           FLUJO SEMANAL MOL                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  LUNES/JUEVES 08:00                                                        │
│       │                                                                     │
│       ▼                                                                     │
│  ┌─────────────────┐                                                       │
│  │ run_scheduler.py │◄── 1,148 keywords                                    │
│  └────────┬────────┘                                                       │
│           │                                                                 │
│           ▼                                                                 │
│  ┌─────────────────┐                                                       │
│  │ Scraping        │──► tracking JSON + SQLite                             │
│  │ ~700 nuevas/sem │                                                       │
│  └────────┬────────┘                                                       │
│           │                                                                 │
│           ▼                                                                 │
│  ┌─────────────────┐                                                       │
│  │ Detectar Bajas  │──► estado_oferta, permanencia                         │
│  └────────┬────────┘                                                       │
│           │                                                                 │
│           ▼                                                                 │
│  ┌─────────────────┐     ┌─────────────────┐                               │
│  │ NLP Pipeline    │────►│ Test Gold Set   │                               │
│  │ (Qwen2.5:14b)   │     │ ¿>= 90%?        │                               │
│  └────────┬────────┘     └────────┬────────┘                               │
│           │                       │                                         │
│           │◄──────────────────────┘ Si pasa                                │
│           ▼                                                                 │
│  ┌─────────────────┐     ┌─────────────────┐                               │
│  │ Matching ESCO   │────►│ Test Gold Set   │                               │
│  │ (Multicriteria) │     │ ¿>= 95%?        │                               │
│  └────────┬────────┘     └────────┬────────┘                               │
│           │                       │                                         │
│           │◄──────────────────────┘ Si pasa                                │
│           ▼                                                                 │
│  ┌─────────────────┐                                                       │
│  │ Export Parquet  │──► S3/production/                                     │
│  │ + Metadata      │                                                       │
│  └─────────────────┘                                                       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Stack Técnico

```
LOCAL (Centro de Control)
├── Python 3.10+
├── SQLite (ofertas, ESCO, validaciones)
├── Ollama + Qwen2.5:14b (NLP)
├── ChromaDB (embeddings)
├── Streamlit (Dashboard Admin)
└── Selenium/Requests (Scraping)

CLOUD (Colaboración)
├── AWS S3 sa-east-1 (mol-validation-data)
│   ├── /experiment/  (datos para validación)
│   ├── /production/  (datos limpios)
│   └── /goldset/     (casos de prueba)
├── Vercel (Dashboards)
│   ├── Optimización (3 admins)
│   └── Producción (analistas OEDE)
└── Lambda + API Gateway (API backend)
```

### 2.3 Estructura de Directorios

```
MOL/
├── 01_sources/
│   └── bumeran/
│       └── scrapers/
│           ├── bumeran_scraper.py          # API básica (interno)
│           ├── scrapear_con_diccionario.py # Multi-keyword (usar este)
│           └── keywords/
│               └── estrategias.json        # 1,148 keywords
│
├── database/
│   ├── mol_database.db                     # SQLite principal
│   ├── matching_rules_v83.py               # Reglas matching actuales
│   ├── match_ofertas_multicriteria.py      # Motor de matching
│   ├── gold_set_manual_v1.json             # 19 casos validados
│   ├── test_gold_set_manual.py             # Test contra gold set
│   ├── detectar_bajas_integrado.py         # Detección de bajas
│   ├── calcular_permanencia.py             # Cálculo permanencia
│   └── esco_skills_extractor.py            # Extractor ESCO
│
├── nlp/
│   ├── nlp_pipeline_v8.py                  # Pipeline NLP principal
│   ├── regex_patterns_v4.py                # Patterns regex
│   └── prompts/
│       └── extraction_v8.txt               # Prompt LLM
│
├── data/
│   └── tracking/
│       └── bumeran_scraped_ids.json        # IDs vistos
│
├── Visual--/                               # Dashboards R (legacy)
│   ├── app.R                               # Usuario final
│   └── validacion_pipeline_app_v3.R        # Experimentos
│
├── dashboards/                             # Dashboards nuevos
│   ├── admin/                              # Streamlit local
│   ├── optimization/                       # Next.js Vercel
│   └── production/                         # Next.js Vercel
│
├── exports/
│   ├── export_nlp.py
│   ├── export_matching.py
│   └── export_production.py
│
├── run_scheduler.py                        # PUNTO DE ENTRADA SCRAPING
├── run_full_pipeline.py                    # Pipeline completo 5 portales
│
└── docs/
    ├── CHANGELOG.md
    ├── STATUS.md
    └── CLAUDE.md
```

---

## 3. Componentes Detallados

### 3.1 Scraping

**Punto de entrada único:** `run_scheduler.py`

```python
# SIEMPRE usar este comando para scraping
python run_scheduler.py --test

# Internamente ejecuta:
from scrapers.scrapear_con_diccionario import BumeranMultiSearch
scraper = BumeranMultiSearch()
df = scraper.scrapear_multiples_keywords(
    estrategia='ultra_exhaustiva_v3_2',  # 1,148 keywords
    max_paginas_por_keyword=1,            # Workaround bug API
    incremental=True
)

# Post-scraping automático:
from database.detectar_bajas_integrado import DetectorBajasIntegrado
detector = DetectorBajasIntegrado()
detector.ejecutar()
```

**Bug conocido de API Bumeran:**
- `page_size=100` → devuelve solo 20
- Página 11+ → duplicados
- Workaround: 1 página × 1,148 keywords

**Scripts a NO usar directamente:**
- `bumeran_scraper.py` (solo ~20 ofertas)
- `run_scraping_completo.py` (incompleto)
- `bumeran_selenium_scraper.py` (legacy)

### 3.2 NLP Pipeline

**Versión actual:** v8.0 (3 capas anti-alucinación)

```
OFERTA RAW
    │
    ▼
┌─────────────────────────────────────────┐
│ CAPA 1: Regex Patterns v4.0             │
│ • Salarios: /\$?\d+[\.,]?\d*[kK]?/      │
│ • Experiencia: /(\d+)\s*años?/          │
│ • Educación: keywords nivel educativo   │
│ • Precisión: 100% (lo que extrae)       │
│ • Cobertura: 60-70% de campos           │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│ CAPA 2: LLM (Qwen2.5:14b)               │
│ • Solo campos que regex no extrajo      │
│ • Prompt estructurado con schema        │
│ • Temperature: 0.1                      │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│ CAPA 3: Validación Cruzada              │
│ • Consistencia interna                  │
│ • Flags de calidad                      │
│ • Score NLP (0-7)                       │
└────────────────┬────────────────────────┘
                 │
                 ▼
OFERTA PARSED (16 bloques, ~130 campos)
```

**Schema NLP v5 (16 bloques):**

| # | Bloque | Campos clave |
|---|--------|--------------|
| 1 | Metadata portal | id, titulo, url_fuente |
| 2 | Empresa | sector_empresa, es_tercerizado |
| 3 | Ubicación | provincia, localidad, modalidad |
| 4 | Experiencia | experiencia_min_anios, nivel_previo |
| 5 | Educación | nivel_educativo, titulo_requerido |
| 6 | Skills | tech_skills, soft_skills, marcas |
| 7 | Idiomas | idioma_principal, nivel_idioma |
| 8 | Rol/Tareas | tareas, tiene_gente_cargo |
| 9 | Condiciones | area_funcional, nivel_seniority |
| 10 | Compensación | salario_min, salario_max, moneda |
| 11 | Beneficios | beneficios_lista |
| 12 | Metadatos NLP | nlp_score, pasa_a_matching |
| 13 | Licencias | licencia_conducir |
| 14 | Calidad | tiene_req_discriminatorios |
| 15 | Certificaciones | certificaciones_requeridas |
| 16 | Especiales | trabajo_en_altura, riesgo |

### 3.3 Matching ESCO

**Versión actual:** v8.3 (Multicriteria)

```
OFERTA PARSED
    │
    ▼
┌─────────────────────────────────────────┐
│ PASO 1: Detectar Familia Funcional      │
│ • 10 familias: comercial, tecnologia,   │
│   salud, educacion, manufactura,        │
│   logistica, administracion,            │
│   gastronomia, construccion, servicios  │
│ • Keywords + patterns por familia       │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│ PASO 2: Filtrar Ocupaciones ESCO        │
│ • Solo ocupaciones de la familia        │
│ • Reduce de 3,045 a ~300               │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│ PASO 3: Scoring Multicriteria           │
│ • Embedding similarity: 40%             │
│ • Keyword matching: 30%                 │
│ • Skill overlap: 20%                    │
│ • Level matching: 10%                   │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│ PASO 4: Selección + Validación          │
│ • Top 3 candidatos                      │
│ • Reglas never_confirm                  │
│ • Threshold mínimo: 0.50                │
└────────────────┬────────────────────────┘
                 │
                 ▼
MATCH: esco_uri, esco_label, isco_code, score
```

**Ontología ESCO cargada:**

| Métrica | Valor |
|---------|-------|
| Ocupaciones | 3,045 |
| Skills | 11,009 (77.3%) |
| Knowledge | 3,232 (22.7%) |
| Associations | 134,805 |
| skill_type poblado | 99.96% |

### 3.4 Sistema de Validación

**Dos ciclos independientes:**

```
CICLO 1: NLP                    CICLO 2: MATCHING
────────────────                ──────────────────
Gold Set: 200+ casos            Gold Set: 200+ casos
Umbral: 90%                     Umbral: 95%
Validación: campo por campo     Validación: ocupación correcta
```

**Capas de validación:**

| Capa | Tipo | Casos | Uso |
|------|------|-------|-----|
| Gold Set | Automático | 200+ | Cada iteración |
| Sampling | Humano | 90/semana | Versiones candidatas |
| Producción | Batch | ~800/semana | Release final |

### 3.5 Permanencia de Ofertas

**Estado:** Primera ejecución completada

| Métrica | Valor |
|---------|-------|
| Bajas detectadas | 0 (normal, primera ejecución) |
| Permanencia calculada | 9,556 ofertas |

**Categorías:**

| Categoría | Días | Interpretación |
|-----------|------|----------------|
| baja | <7 | Alta demanda, se cubren rápido |
| media | 7-30 | Proceso normal |
| alta | >30 | Difíciles de cubrir |

**Campos BD:**
- `estado_oferta`: 'activa' / 'baja' / 'expirada'
- `fecha_ultimo_visto`, `fecha_baja`
- `dias_publicada`, `categoria_permanencia`

---

## 4. Dashboards

### 4.1 Dashboard Admin Local (Streamlit)

**Ubicación:** `dashboards/admin/`
**Puerto:** 8501
**Usuario:** Solo administrador

**Tabs:**

| Tab | Función | Componentes |
|-----|---------|-------------|
| Modelos | Configurar NLP/Matching | Motor, modelo, prompts |
| Scraping | Ejecutar/monitorear | Estrategia, keywords, estado |
| Pipeline | Ejecutar NLP/Matching | Progreso, errores |
| Tests | Gold set, métricas | Precisión, F1, errores |
| S3 Sync | Exportar/importar | Upload, download validaciones |
| Logs | Monitoreo | Últimas ejecuciones |

### 4.2 Dashboard Optimización (Vercel)

**Ubicación:** `dashboards/optimization/`
**URL:** https://mol-optimizacion.vercel.app
**Usuarios:** 3 admins validadores

**Funciones:**
- Validar NLP (campo por campo)
- Validar Matching (ocupación correcta)
- Feedback sobre errores
- Métricas en tiempo real

### 4.3 Dashboard Producción (Vercel)

**Ubicación:** `dashboards/production/`
**URL:** https://mol-produccion.vercel.app
**Usuarios:** Analistas OEDE

**3 Pestañas:**

| Tab | Contenido |
|-----|-----------|
| Panorama General | KPIs + Evolución + Top 10 ocupaciones + Jurisdicciones |
| Requerimientos | 4 tortas (edad, género, educación, otros) + Top 20 skills |
| Ofertas Laborales | Tabla explorable con filtros secundarios |

**Filtros globales:**
- Territorio (Nacional/Provincial/Localidad)
- Período (Semana/Mes/Año)
- Permanencia (Todas/Baja/Media/Alta)
- Buscador ocupación
- Árbol ocupaciones

---

## 5. Estructura S3

```
s3://mol-validation-data/
│
├── experiment/
│   ├── nlp/
│   │   ├── 2025-W50/
│   │   │   ├── parsed.json.gz
│   │   │   └── validations.json
│   │   └── latest.json
│   │
│   └── matching/
│       ├── 2025-W50/
│       │   ├── matched.json.gz
│       │   ├── candidates.json.gz
│       │   └── validations.json
│       └── latest.json
│
├── production/
│   ├── current/
│   │   └── ofertas.parquet          ◄── Lambda lee esto
│   │
│   ├── history/
│   │   └── year=2025/
│   │       ├── week=49/ofertas.parquet
│   │       ├── week=50/ofertas.parquet
│   │       └── ...
│   │
│   └── metadata.json
│
├── goldset/
│   ├── nlp_gold.json
│   └── matching_gold.json
│
└── config/
    └── esco_occupations.json.gz
```

---

## 6. Scripts Principales

### 6.1 Existentes (Operativos)

| Script | Función | Comando |
|--------|---------|---------|
| `run_scheduler.py` | Scraping semanal | `python run_scheduler.py --test` |
| `detectar_bajas_integrado.py` | Detectar ofertas dadas de baja | Automático post-scraping |
| `calcular_permanencia.py` | Calcular permanencia | Automático |
| `test_gold_set_manual.py` | Test matching gold set | `python database/test_gold_set_manual.py` |
| `esco_skills_extractor.py` | Extraer skills ESCO | `python database/esco_skills_extractor.py` |

### 6.2 Por Crear

| Script | Función | Prioridad |
|--------|---------|-----------|
| `test_nlp.py` | Evaluar NLP contra gold set | Alta |
| `generate_sample.py` | Generar muestra estratificada | Alta |
| `export_nlp.py` | Exportar parsed a S3/experiment | Alta |
| `export_matching.py` | Exportar matched a S3/experiment | Alta |
| `sync_validations.py` | Descargar validaciones de S3 | Alta |
| `export_production.py` | Generar Parquet, subir a S3/production | Alta |
| `lambda_ofertas.py` | Lambda para API queries | Media |
| `deduplicate_cross_portal.py` | Detectar duplicados entre portales | Media |
| `analyze_errors.py` | Analizar errores para optimización | Media |

---

## 7. Configuración

### 7.1 Variables de Entorno

```bash
# AWS
AWS_ACCESS_KEY_ID=xxx
AWS_SECRET_ACCESS_KEY=xxx
AWS_DEFAULT_REGION=sa-east-1
S3_BUCKET=mol-validation-data

# Ollama
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=qwen2.5:14b

# Database
MOL_DATABASE_PATH=./database/mol_database.db

# Scraping
SCRAPING_STRATEGY=ultra_exhaustiva_v3_2
SCRAPING_DAYS=0,3  # Lunes, Jueves
SCRAPING_HOUR=8
```

### 7.2 Dependencias Python

```
# Core
pandas>=2.0
numpy>=1.24
sqlite3  # built-in

# NLP
ollama>=0.1.0
chromadb>=0.4.0
rapidfuzz>=3.0

# Scraping
requests>=2.31
selenium>=4.15
beautifulsoup4>=4.12

# Export
pyarrow>=14.0
boto3>=1.34

# Dashboard
streamlit>=1.29
plotly>=5.18
```

---

## 8. Decisiones de Diseño

### 8.1 Principios

1. **LOCAL es el centro de control, CLOUD es para colaboración**
2. **Validación en capas: automática primero, humana para candidatos**
3. **Un solo punto de entrada para scraping**
4. **Gap de datos aceptable si se normaliza con el tiempo**
5. **Spec-driven development: diseñar completo antes de implementar**

### 8.2 Restricciones

- Sin siglas técnicas en dashboard usuario final (CIUO, ESCO → "normalizadas")
- Todos los gráficos con botón de descarga
- Scraping no agresivo (1 página por keyword)
- Free tier de AWS donde sea posible

### 8.3 Deuda Técnica Conocida

| Item | Impacto | Plan |
|------|---------|------|
| Dashboards R legacy | Mantenimiento | Migrar a Next.js |
| Scripts de scraping múltiples | Confusión | Deprecar innecesarios |
| Gold set pequeño (19 casos) | Baja confianza | Expandir a 200+ |
| Solo 1 portal activo | Cobertura limitada | Activar ZonaJobs |

---

## 9. Métricas de Éxito

| Métrica | Actual | Objetivo | Prioridad |
|---------|--------|----------|-----------|
| Precisión NLP | ~90% | >= 90% | Alta |
| Precisión Matching | 78.9% | >= 95% | Alta |
| Gold Set NLP | 0 casos | 200+ casos | Alta |
| Gold Set Matching | 19 casos | 200+ casos | Alta |
| Portales activos | 1 | 5 | Media |
| Tiempo iteración | días | < 1 día | Alta |

---

## 10. Contacto y Recursos

**Proyecto Linear:** https://linear.app/molar/project/mol-monitor-ofertas-laborales-2a9662bfa15f

**Documentación:**
- SISTEMA_VALIDACION_V2.md - Arquitectura completa
- NLP_SCHEMA_V5.md - Schema de campos NLP
- DASHBOARD_WIREFRAMES.md - Wireframes de dashboards
- SCRAPERS_INVENTARIO.md - Inventario de scrapers

---

*Documento generado: 2025-12-07*
*Para Claude Code: Este es el contexto maestro del sistema MOL*
