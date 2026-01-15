# 🔄 FLUJO COMPLETO: BUMERAN WEBSCRAPING → DASHBOARD

**Fecha:** 30 de octubre de 2025
**Versión:** 1.0
**Mantenedor:** OEDE - Observatorio de Empleo y Dinámica Empresarial

---

## 📋 Tabla de Contenidos

1. [Resumen Ejecutivo](#resumen-ejecutivo)
2. [Diagrama de Flujo](#diagrama-de-flujo)
3. [Etapa 1: Scraping](#etapa-1-scraping)
4. [Etapa 2: Consolidación](#etapa-2-consolidación)
5. [Etapa 3: Extracción NLP](#etapa-3-extracción-nlp)
6. [Etapa 4: Matching ESCO](#etapa-4-matching-esco)
7. [Etapa 5: Dashboard Shiny](#etapa-5-dashboard-shiny)
8. [Comandos Ejecutables](#comandos-ejecutables)
9. [Problemas Conocidos](#problemas-conocidos)
10. [Calidad de Datos](#calidad-de-datos)

---

## 📊 Resumen Ejecutivo

### Estado Actual

| Métrica | Valor |
|---------|-------|
| **Ofertas disponibles en Bumeran** | ~12,000 |
| **Ofertas scrapeadas** | 2,460 (20%) |
| **Calidad descripciones** | 100% ✅ |
| **Tiempo de scraping** | ~2 horas (con 55 keywords) |
| **Scripts funcionales** | 2/4 principales |
| **Modo incremental** | ✅ Activo |
| **Estado pipeline** | ✅ Funcional |

### Archivos Clave

```
📁 Ubicación base: D:\OEDE\Webscrapping\

📄 CSV final raw: 01_sources/bumeran/data/raw/bumeran_full_20251023_213057.csv
📄 CSV con NLP: 02.5_nlp_extraction/data/processed/bumeran_nlp_20251025_140906.csv
📄 CSV consolidado: 02_consolidation/data/consolidated/ofertas_consolidadas_*.csv
📄 Tracking: data/tracking/bumeran_scraped_ids.json
```

---

## 🔀 Diagrama de Flujo

```
┌─────────────────────────────────────────────────────────────────────┐
│                        API BUMERAN                                  │
│  https://www.bumeran.com.ar/api/avisos/searchV2                    │
│                                                                      │
│  • Ofertas disponibles: ~12,000                                     │
│  • Método: POST con headers especiales                              │
│  • Paginación: 20 ofertas/página                                    │
│  • ⚠️ CRÍTICO: Requiere keywords, sin ellas solo 20 ofertas         │
└─────────────────────────────────────────────────────────────────────┘
                               ↓
┌─────────────────────────────────────────────────────────────────────┐
│                    ETAPA 1: SCRAPING                                │
│  📍 01_sources/bumeran/scrapers/bumeran_scraper.py                  │
│                                                                      │
│  INPUTS:                                                            │
│  • master_keywords.json (estrategias: completa ~55 keywords)        │
│  • bumeran_scraped_ids.json (tracking incremental)                  │
│                                                                      │
│  PARÁMETROS:                                                        │
│  • delay_between_requests: 2.0s                                     │
│  • incremental: True (solo ofertas nuevas)                          │
│  • max_paginas: None (todas las páginas disponibles)                │
│                                                                      │
│  OUTPUTS:                                                           │
│  ✅ bumeran_full_20251023_213057.csv                                │
│     - 2,460 ofertas                                                 │
│     - 32 columnas raw                                               │
│     - Tamaño: 4.2 MB                                                │
│     - Ubicación: 01_sources/bumeran/data/raw/                       │
└─────────────────────────────────────────────────────────────────────┘
                               ↓
┌─────────────────────────────────────────────────────────────────────┐
│                ETAPA 2: CONSOLIDACIÓN                               │
│  📍 02_consolidation/scripts/consolidar_fuentes.py                  │
│  📍 Normalizer: normalizar_campos.py → BumeranNormalizer()          │
│                                                                      │
│  PROCESO:                                                           │
│  1. Lee CSV raw de Bumeran                                          │
│  2. Aplica BumeranNormalizer.normalize()                            │
│  3. Mapea campos al schema unificado (50+ campos)                   │
│                                                                      │
│  TRANSFORMACIONES PRINCIPALES:                                      │
│  • id_oferta → _metadata.source_id                                  │
│  • titulo → informacion_basica.titulo                               │
│  • descripcion (HTML) → descripcion_limpia (texto plano)            │
│  • "Ciudad, Provincia" → provincia + ciudad separados               │
│  • "DD-MM-YYYY" → ISO 8601 (YYYY-MM-DD)                             │
│  • Modalidades normalizadas ("Remoto" → "remoto")                   │
│                                                                      │
│  OUTPUTS:                                                           │
│  ✅ ofertas_consolidadas_20251025_125307.csv                        │
│     - ~8,472 ofertas (todas las fuentes)                            │
│     - Schema unificado: 50+ campos                                  │
│     - Tamaño: 792 MB                                                │
│     - Ubicación: 02_consolidation/data/consolidated/                │
└─────────────────────────────────────────────────────────────────────┘
                               ↓
┌─────────────────────────────────────────────────────────────────────┐
│               ETAPA 3: EXTRACCIÓN NLP                               │
│  📍 02.5_nlp_extraction/scripts/run_nlp_extraction.py               │
│  📍 Extractor: extractors/bumeran_extractor.py                      │
│                                                                      │
│  PROCESO:                                                           │
│  1. Lee campo 'descripcion' del CSV raw de Bumeran                  │
│  2. Limpia HTML con HTMLStripper                                    │
│  3. Aplica regex patterns para extraer 23 campos:                   │
│                                                                      │
│     EXPERIENCIA:                                                    │
│     • experiencia_min_anios, experiencia_max_anios                  │
│     • experiencia_area                                              │
│                                                                      │
│     EDUCACIÓN:                                                      │
│     • nivel_educativo, estado_educativo                             │
│     • carrera_especifica, titulo_excluyente                         │
│                                                                      │
│     IDIOMAS:                                                        │
│     • idioma_principal, nivel_idioma_principal                      │
│     • idioma_secundario, nivel_idioma_secundario                    │
│                                                                      │
│     SKILLS:                                                         │
│     • skills_tecnicas_list, soft_skills_list                        │
│     • certificaciones_list, niveles_skills_list                     │
│                                                                      │
│     OTROS:                                                          │
│     • salario_min/max, jornada_laboral                              │
│     • requisitos_excluyentes/deseables                              │
│                                                                      │
│  OUTPUTS:                                                           │
│  ✅ bumeran_nlp_20251025_140906.csv                                 │
│     - 2,460 ofertas                                                 │
│     - 55 columnas (32 originales + 23 NLP)                          │
│     - Tamaño: ~5 MB                                                 │
│     - Ubicación: 02.5_nlp_extraction/data/processed/                │
└─────────────────────────────────────────────────────────────────────┘
                               ↓
┌─────────────────────────────────────────────────────────────────────┐
│            ETAPA 4: MATCHING ESCO/ISCO                              │
│  📍 03_esco_matching/scripts/esco_isco_llm_fallback.py              │
│  📍 Manual: manual_matcher_claude.py                                │
│                                                                      │
│  PROCESO:                                                           │
│  1. Lee titulo normalizado de cada oferta                           │
│  2. Match contra taxonomía ESCO con Claude AI                       │
│  3. Asigna código ESCO + ISCO + skills                              │
│  4. Enriquece con skills esenciales y opcionales                    │
│                                                                      │
│  CAMPOS AGREGADOS:                                                  │
│  • claude_esco_id, claude_esco_label                                │
│  • claude_isco_code (4 dígitos ISCO-08)                             │
│  • isco_nivel1, isco_nivel1_nombre                                  │
│  • isco_nivel2, isco_4d                                             │
│  • esco_skills_esenciales (pipe-separated)                          │
│  • esco_skills_opcionales (pipe-separated)                          │
│  • claude_confidence, claude_razonamiento                           │
│                                                                      │
│  OUTPUTS:                                                           │
│  ✅ ofertas_esco_shiny.csv (subset perfecto de 268 ofertas)         │
│     - 268 ofertas clasificadas manualmente                          │
│     - 48 columnas                                                   │
│     - 100% con clasificación ESCO perfecta                          │
│     - 100% con URLs recuperadas                                     │
│     - Ubicación: Visual--/ofertas_esco_shiny.csv                    │
└─────────────────────────────────────────────────────────────────────┘
                               ↓
┌─────────────────────────────────────────────────────────────────────┐
│               ETAPA 5: DASHBOARD SHINY                              │
│  📍 Visual--/app.R                                                  │
│                                                                      │
│  INPUT:                                                             │
│  • ofertas_esco_shiny.csv (268 ofertas, 48 columnas)                │
│                                                                      │
│  DASHBOARD FEATURES:                                                │
│  • 5 pestañas interactivas                                          │
│  • Autenticación con shinymanager                                   │
│  • Filtros: Provincia, Fecha, Árbol ESCO navegable                  │
│  • Gráficos: plotly interactivos                                    │
│  • Tablas: DT con búsqueda y paginación                             │
│                                                                      │
│  DEPLOYED:                                                          │
│  🌐 https://dos1tv-gerardo-breard.shinyapps.io/dashboard-esco-...   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 📥 ETAPA 1: SCRAPING

### 🎯 Objetivo
Extraer ofertas laborales de la API de Bumeran Argentina.

### 📁 Ubicación
`D:\OEDE\Webscrapping\01_sources\bumeran\`

### 🔧 Scripts Principales

#### 1. bumeran_scraper.py (Script Principal)

**Propósito:** Scraper directo de la API REST de Bumeran

**Características:**
- Modo incremental (evita re-scrapear ofertas ya procesadas)
- Rate limiting (2s entre requests)
- Soporte para keywords
- Genera CSV/JSON/Excel

**Uso básico:**
```python
from bumeran_scraper import BumeranScraper

scraper = BumeranScraper()
ofertas = scraper.scrapear_todo(
    max_paginas=None,      # Todas las páginas
    query="python",        # Keyword de búsqueda
    incremental=True       # Solo ofertas nuevas
)
scraper.save_all_formats(ofertas, 'bumeran_full')
```

#### 2. scrapear_con_diccionario.py (RECOMENDADO)

**Propósito:** Scraping multi-keyword usando diccionario maestro

**Ventajas:**
- Usa múltiples keywords automáticamente
- Deduplicación incorporada
- Mejor cobertura (~55 keywords)
- Estrategias predefinidas

**Uso:**
```python
from scrapear_con_diccionario import BumeranMultiSearch

scraper = BumeranMultiSearch()
df = scraper.scrapear_multiples_keywords(
    estrategia='completa',          # 55 keywords
    max_paginas_por_keyword=10,
    incremental=True,
    date_window_days=7              # Últimos 7 días
)
scraper.guardar_resultados(df)
```

### 📊 Configuración API

```python
# Endpoint
URL = "https://www.bumeran.com.ar/api/avisos/searchV2"

# Headers OBLIGATORIOS
headers = {
    'x-site-id': 'BMAR',                      # Bumeran Argentina
    'x-pre-session-token': str(uuid.uuid4()),  # Token único por sesión
    'Content-Type': 'application/json'
}

# Payload
{
    "pageSize": 20,        # Ofertas por página (max: 100)
    "page": 0,             # Número de página (0-indexed)
    "sort": "FECHA",       # FECHA o RELEVANTES
    "query": "python"      # ⚠️ CRÍTICO: Sin keyword solo 20 ofertas
}
```

### ⚠️ LIMITACIONES CRÍTICAS

1. **Sin keyword → solo 20 ofertas**
   - Problema: API retorna máximo 20 ofertas si no hay `query`
   - Solución: SIEMPRE usar keywords del `master_keywords.json`

2. **Rate limiting**
   - Delay mínimo: 2 segundos entre requests
   - Reducir puede causar bloqueo de IP

3. **Paginación limitada**
   - Máximo 100 ofertas por request con `pageSize=100`
   - Óptimo: 20 ofertas por request (más estable)

### 📦 Outputs Generados

| Archivo | Ubicación | Descripción |
|---------|-----------|-------------|
| `bumeran_full_YYYYMMDD_HHMMSS.csv` | `data/raw/` | CSV con 32 columnas raw |
| `bumeran_consolidacion.json` | `data/raw/` | Backup en JSON |
| `bumeran_consolidacion.xlsx` | `data/raw/` | Backup en Excel |
| `bumeran_scraped_ids.json` | `../../data/tracking/` | Tracking incremental |

### 📋 Columnas Raw (32 campos)

```
Identificación:
- id_oferta, id_empresa

Básicas:
- titulo, empresa, descripcion (HTML), confidencial

Ubicación:
- localizacion ("Ciudad, Provincia")
- modalidad_trabajo, tipo_trabajo

Fechas:
- fecha_publicacion, fecha_hora_publicacion, fecha_modificado

Detalles:
- cantidad_vacantes, apto_discapacitado

Categorización:
- id_area, id_subarea, id_pais

Empresa:
- logo_url, empresa_validada, empresa_pro, promedio_empresa

Otros:
- plan_publicacion_id, portal, tipo_aviso
- url_oferta, scrapeado_en
```

---

## 🔄 ETAPA 2: CONSOLIDACIÓN

### 🎯 Objetivo
Normalizar datos de Bumeran al schema unificado multi-fuente.

### 📁 Ubicación
`D:\OEDE\Webscrapping\02_consolidation\`

### 🔧 Script Principal

**Archivo:** `scripts/consolidar_fuentes.py`
**Normalizer:** `scripts/normalizar_campos.py` → clase `BumeranNormalizer`

### 🔀 Transformaciones Principales

```python
# Ejemplo de normalización

# ANTES (raw):
{
    'id_oferta': '123456',
    'titulo': 'Desarrollador Python',
    'descripcion': '<p>Descripción con <b>HTML</b></p>',
    'localizacion': 'CABA, Buenos Aires',
    'fecha_publicacion': '23-10-2025',
    'modalidad_trabajo': 'Remoto'
}

# DESPUÉS (normalizado):
{
    '_metadata.source': 'bumeran',
    '_metadata.source_id': '123456',
    '_metadata.unified_id': 'bumeran_123456',
    '_metadata.url_oferta': 'https://www.bumeran.com.ar/empleos/123456.html',

    'informacion_basica.titulo': 'Desarrollador Python',
    'informacion_basica.titulo_normalizado': 'desarrollador python',
    'informacion_basica.descripcion': '<p>Descripción con <b>HTML</b></p>',
    'informacion_basica.descripcion_limpia': 'Descripción con HTML',

    'ubicacion.pais': 'Argentina',
    'ubicacion.provincia': 'Buenos Aires',
    'ubicacion.ciudad': 'CABA',
    'ubicacion.ubicacion_raw': 'CABA, Buenos Aires',

    'fechas.fecha_publicacion': '2025-10-23',  # ISO 8601

    'modalidad.modalidad_trabajo': 'remoto',   # Normalizado lowercase
    'modalidad.tipo_trabajo': 'full_time'      # Inferido si no está
}
```

### 📊 Schema Unificado

El schema tiene **50+ campos** organizados en secciones:

1. `_metadata`: Metadatos de scraping
2. `informacion_basica`: Título, empresa, descripción
3. `ubicacion`: País, provincia, ciudad
4. `modalidad`: Tipo de trabajo, modalidad
5. `fechas`: Publicación, modificación, cierre
6. `requisitos`: Experiencia, educación, idiomas (se llena en NLP)
7. `compensacion`: Salario, beneficios (generalmente vacío en Bumeran)
8. `detalles`: Vacantes, área, nivel
9. `clasificacion_esco`: ESCO/ISCO (se llena en etapa 4)
10. `source_specific`: Campos únicos de Bumeran

**Ver schema completo:** `shared/schemas/schema_unificado.json`

### 📦 Output

| Archivo | Descripción |
|---------|-------------|
| `ofertas_consolidadas_YYYYMMDD_HHMMSS.csv` | CSV con todas las fuentes consolidadas |
| Tamaño: ~792 MB | |
| Ofertas: ~8,472 | Incluye Bumeran + otras fuentes |
| Columnas: 50+ | Schema unificado |

---

## 🧠 ETAPA 3: EXTRACCIÓN NLP

### 🎯 Objetivo
Extraer información estructurada de las descripciones en texto libre usando regex.

### 📁 Ubicación
`D:\OEDE\Webscrapping\02.5_nlp_extraction\`

### 🔧 Scripts

**Principal:** `scripts/run_nlp_extraction.py`
**Extractor:** `extractors/bumeran_extractor.py` → clase `BumeranExtractor`

### 🔍 Campos Extraídos (23 campos)

#### 1. Experiencia (3 campos)
```python
# Ejemplo de texto:
"Requisitos: Experiencia de 2 a 3 años en desarrollo Python"

# Extracción:
{
    'experiencia_min_anios': 2,
    'experiencia_max_anios': 3,
    'experiencia_area': 'desarrollo python'
}
```

#### 2. Educación (4 campos)
```python
# Texto: "Título universitario en Ingeniería en Sistemas (excluyente)"

# Extracción:
{
    'nivel_educativo': 'universitario',
    'estado_educativo': 'completo',
    'carrera_especifica': 'Ingeniería en Sistemas',
    'titulo_excluyente': True
}
```

#### 3. Idiomas (4 campos)
```python
# Texto: "Inglés avanzado (excluyente), portugués intermedio deseable"

# Extracción:
{
    'idioma_principal': 'inglés',
    'nivel_idioma_principal': 'avanzado',
    'idioma_secundario': 'portugués',
    'nivel_idioma_secundario': 'intermedio'
}
```

#### 4. Skills (2+ campos)
```python
# Texto: "Requisitos técnicos: Python, Django, PostgreSQL, Docker"

# Extracción:
{
    'skills_tecnicas_list': ['Python', 'Django', 'PostgreSQL', 'Docker'],
    'soft_skills_list': ['trabajo en equipo', 'comunicación'],
}
```

### 📊 Calidad de Extracción (Bumeran)

| Campo | Cobertura | Confidence Promedio |
|-------|-----------|---------------------|
| Experiencia | ~60% | 0.5-0.8 |
| Educación | ~55% | 0.5-0.7 |
| Idiomas | ~45% | 0.4-0.7 |
| Skills técnicas | ~70% | 0.5-0.8 |
| Soft skills | ~40% | 0.3-0.5 |
| Jornada | ~50% | 0.6-0.9 |
| Salario | ~5% | 0.7-0.9 |

**Nota:** Bumeran tiene la mejor calidad de descripciones (100% cobertura, bien estructuradas).

### 📦 Output

| Archivo | Descripción |
|---------|-------------|
| `bumeran_nlp_YYYYMMDD_HHMMSS.csv` | CSV con campos NLP extraídos |
| Ofertas: 2,460 | |
| Columnas: 55 | 32 originales + 23 NLP |
| Tamaño: ~5 MB | |

---

## 🏷️ ETAPA 4: MATCHING ESCO

### 🎯 Objetivo
Clasificar ofertas según taxonomía ESCO/ISCO-08 y extraer skills asociadas.

### 📁 Ubicación
`D:\OEDE\Webscrapping\03_esco_matching\`

### 🔧 Scripts

1. `scripts/esco_isco_llm_fallback.py` - Matching con Claude AI
2. `scripts/manual_matcher_claude.py` - Matching manual perfecto
3. `scripts/enriquecer_con_skills_esco.py` - Agregar skills ESCO
4. `scripts/02_preparar_csv_shiny.py` - Preparar para dashboard

### 🔀 Proceso de Matching

```python
# INPUT
titulo = "Desarrollador Full Stack React + Node.js"

# MATCHING CON CLAUDE AI
↓
claude_esco_id = "6d1e2801-..."
claude_esco_label = "desarrollador de aplicaciones/desarrolladora de aplicaciones"
claude_isco_code = "2514.1"
claude_confidence = "alta"
claude_razonamiento = "El título menciona desarrollo full stack con tecnologías específicas..."

# ENRIQUECIMIENTO ESCO SKILLS
↓
esco_skills_esenciales = [
    "desarrollar prototipos de interfaz de usuario",
    "utilizar marcos de aplicaciones",
    "utilizar lenguajes de programación",
    ...
] (54 skills promedio)

esco_skills_opcionales = [
    "gestión de proyectos de TIC",
    "consultar usuarios de TIC",
    ...
] (67 skills promedio)

# PREPARACIÓN PARA SHINY (R)
↓
# Listas Python → strings pipe-separated
esco_skills_esenciales = "desarrollar prototipos | utilizar marcos | ..."
```

### 📊 Cobertura ESCO

| Métrica | Valor |
|---------|-------|
| Ofertas clasificadas | 268 de 8,472 (3.2%) |
| Método | Matching manual perfecto con Claude AI |
| Confidence alta | 156 (58.2%) |
| Confidence media | 44 (16.4%) |
| Confidence baja | 68 (25.4%) |
| Skills promedio/oferta | 54 esenciales + 67 opcionales |

**Nota:** Solo un subset de 268 ofertas tiene clasificación ESCO completa debido al costo de la API de Claude. El resto puede procesarse posteriormente.

### 📦 Output Final

| Archivo | Descripción |
|---------|-------------|
| `ofertas_esco_shiny.csv` | CSV preparado para dashboard Shiny |
| Ubicación | `Visual--/ofertas_esco_shiny.csv` |
| Ofertas | 268 (subset perfecto) |
| Columnas | 48 |
| Features | 100% con ESCO/ISCO + skills + URLs |
| Tamaño | 1.2 MB |

**Columnas clave agregadas:**
- `claude_esco_id`, `claude_esco_label`
- `claude_isco_code`, `isco_nivel1`, `isco_nivel2`, `isco_4d`
- `esco_skills_esenciales` (pipe-separated)
- `esco_skills_opcionales` (pipe-separated)
- `url_oferta` (recuperada del consolidado)

---

## 📊 ETAPA 5: DASHBOARD SHINY

### 🎯 Objetivo
Visualización interactiva de ofertas laborales clasificadas con ESCO.

### 📁 Ubicación
`D:\OEDE\Webscrapping\Visual--\`

### 🌐 Dashboard en Producción

**URL:** https://dos1tv-gerardo-breard.shinyapps.io/dashboard-esco-argentina/

**Versión actual:** 2.4.0

**Requiere autenticación:** Sí

**Credenciales de prueba:**
- Usuario: `admin` / Contraseña: `admin123`
- Usuario: `invitado` / Contraseña: `demo2024`

### 📊 Pestañas del Dashboard

1. **📊 Panorama General**
   - 3 ValueBoxes: Ofertas, Ocupaciones, Skills ESCO
   - Distribución por ISCO Nivel 1 (gráfico pie)
   - Top 10 ocupaciones más demandadas
   - Distribución geográfica (provincias)

2. **👤 Perfil Demandado**
   - Requisitos educativos (pie chart)
   - Experiencia requerida por ISCO
   - Top 20 soft skills parseadas
   - Top 20 skills técnicas parseadas

3. **🎯 Análisis de Skills ESCO**
   - Skills esenciales ESCO (top 20)
   - Skills opcionales ESCO (top 30)
   - Tabla skills por categoría ISCO

4. **🏢 Ocupaciones ESCO**
   - Tabla: Ocupación - ISCO - Provincia
   - Distribución ISCO Nivel 2

5. **🔍 Explorador de Ofertas**
   - Buscador por título
   - Filtro por ISCO (árbol navegable en sidebar)
   - Tabla con links clickeables a ofertas originales
   - Descarga de datos filtrados

### 🔧 Filtros Globales

**Barra horizontal superior:**
- Provincia (dropdown)
- Rango de Fechas (dateRangeInput)
- Botón "Limpiar Todo"

**Sidebar:**
- Árbol ESCO navegable (4 niveles jerárquicos)
- Click en nodo filtra todo el dashboard

### 📦 Tecnologías

```r
# R Packages
library(shiny)              # Framework dashboard
library(shinydashboard)     # Layout y componentes UI
library(shinymanager)       # Autenticación
library(shinyTree)          # Árbol navegable
library(dplyr)              # Manipulación datos
library(ggplot2)            # Gráficos base
library(plotly)             # Gráficos interactivos
library(DT)                 # Tablas interactivas
library(tidyr)              # Utilidades
library(stringr)            # Manipulación strings
library(scales)             # Formatos numéricos
```

---

## ⚡ Comandos Ejecutables

### 🚀 Pipeline Completo (Recomendado)

```bash
# Ejecutar pipeline completo de Bumeran
cd D:\OEDE\Webscrapping
python run_full_pipeline.py --source bumeran

# Con límite (testing)
python run_full_pipeline.py --source bumeran --limit 100
```

### 📥 Solo Scraping

```bash
# Opción 1: Scraping multi-keyword (RECOMENDADO)
cd D:\OEDE\Webscrapping\01_sources\bumeran\scrapers
python scrapear_con_diccionario.py

# Opción 2: Scraping directo
python bumeran_scraper.py
```

### 🔄 Solo Consolidación

```bash
cd D:\OEDE\Webscrapping\02_consolidation\scripts
python consolidar_fuentes.py --fuentes bumeran
```

### 🧠 Solo Extracción NLP

```bash
cd D:\OEDE\Webscrapping\02.5_nlp_extraction\scripts
python run_nlp_extraction.py --source bumeran
```

### 🏷️ Solo Matching ESCO

```bash
cd D:\OEDE\Webscrapping\03_esco_matching\scripts
python esco_isco_llm_fallback.py --limit 300
```

### 📊 Dashboard Local

```r
# En RStudio o R terminal
setwd("D:/OEDE/Webscrapping/Visual--")
shiny::runApp("app.R")
```

---

## ⚠️ Problemas Conocidos

### 🔴 Críticos

#### 1. API sin keywords retorna solo 20 ofertas

**Problema:**
```python
# SIN keyword
payload = {"pageSize": 100, "page": 0}
# → API retorna 20 ofertas (independiente de paginación)

# CON keyword
payload = {"query": "python", "pageSize": 100, "page": 0}
# → API retorna hasta 100 ofertas por página
```

**Solución:**
- SIEMPRE usar keywords del `master_keywords.json`
- Usar `scrapear_con_diccionario.py` que itera automáticamente

**Ubicación del código:**
`01_sources/bumeran/scrapers/bumeran_scraper.py:108-112`

---

#### 2. Tracking incremental puede corromperse

**Problema:**
Si el archivo `bumeran_scraped_ids.json` se corrompe (encoding, interrupción), se pierde el histórico de IDs scrapeados.

**Solución:**
- Hay backups automáticos en `data/tracking/*.bak`
- Validar JSON antes de usar

**Código de recuperación:**
```bash
# Restaurar desde último backup
cd D:\OEDE\Webscrapping\data\tracking
copy bumeran_scraped_ids_YYYYMMDD.bak bumeran_scraped_ids.json
```

---

### ⚠️ Advertencias

#### 3. Modalidad de trabajo incompleta

**Problema:**
~30% de ofertas de Bumeran no especifican modalidad (presencial/remoto/híbrido).

**Impacto:**
Análisis de trabajo remoto incompleto.

**Solución:**
Usar extracción NLP como fallback (campo `jornada_laboral`).

---

#### 4. Salarios no publicados

**Problema:**
<5% de ofertas de Bumeran tienen información salarial.

**Impacto:**
Análisis salarial imposible solo con Bumeran.

**Solución:**
Combinar con otras fuentes (LinkedIn, Indeed) que tienen mejor cobertura de salarios.

---

#### 5. Parsing de ubicación puede fallar

**Problema:**
Formato "Ciudad, Provincia" no siempre es consistente:
- "CABA, Buenos Aires"
- "San Miguel de Tucumán, Tucumán"
- "Capital Federal"

**Solución:**
Mapeo manual de provincias principales en `normalizar_campos.py:399-442`.

---

### 💡 Mejoras Futuras

#### 6. Rate limiting conservador

**Mejora:** Delay de 2s podría reducirse a 1.5s sin riesgo de bloqueo.

#### 7. HTML en descripciones

**Mejora:** Limpiar HTML en scraping para reducir tamaño de archivos (actualmente se limpia en NLP).

---

## 📊 Calidad de Datos

### 📈 Completitud por Campo

| Campo | Completitud | Calidad |
|-------|-------------|---------|
| **id_oferta** | 100% | ⭐⭐⭐⭐⭐ |
| **titulo** | 100% | ⭐⭐⭐⭐⭐ |
| **descripcion** | 100% | ⭐⭐⭐⭐⭐ (mejor de todas las fuentes) |
| **empresa** | ~95% | ⭐⭐⭐⭐ (algunas confidenciales) |
| **localizacion** | ~98% | ⭐⭐⭐⭐ |
| **modalidad_trabajo** | ~70% | ⭐⭐⭐ (muchas sin especificar) |
| **tipo_trabajo** | ~60% | ⭐⭐⭐ |
| **fecha_publicacion** | 100% | ⭐⭐⭐⭐⭐ |
| **cantidad_vacantes** | ~30% | ⭐⭐ |
| **salario** | <5% | ⭐ (rara vez publicado) |

### 🎯 Estadísticas NLP Extraction

| Categoría | Cobertura | Confidence |
|-----------|-----------|------------|
| Experiencia | ~60% | 0.5-0.8 |
| Educación | ~55% | 0.5-0.7 |
| Idiomas | ~45% | 0.4-0.7 |
| Skills técnicas | ~70% | 0.5-0.8 |
| Soft skills | ~40% | 0.3-0.5 |
| Jornada | ~50% | 0.6-0.9 |

**Nota importante:** Bumeran tiene las mejores descripciones de todas las fuentes analizadas (100% cobertura, bien estructuradas, con detalles técnicos).

---

## 📚 Documentación Adicional

### 📄 Archivos de Documentación

1. **README.md de Bumeran**
   - Ubicación: `01_sources/bumeran/README.md`
   - Contenido: Documentación técnica completa del scraper

2. **Schema Unificado**
   - Ubicación: `shared/schemas/schema_unificado.json`
   - Contenido: Especificación completa de todos los campos

3. **API de Bumeran**
   - Ubicación: `docs/ZONAJOBS_API_DOCUMENTATION.md` (similar para Bumeran)
   - Contenido: Endpoints, headers, parámetros

4. **Documentación ESCO**
   - Ubicación: `Visual--/docs/ESTRUCTURA_ESCO_ISCO.md`
   - Contenido: Jerarquía completa ESCO (5 niveles)

### 🔗 Enlaces Útiles

- Dashboard en producción: https://dos1tv-gerardo-breard.shinyapps.io/dashboard-esco-argentina/
- Clasificación ESCO: https://esco.ec.europa.eu/es/classification/occupation_main
- ISCO-08: https://www.ilo.org/public/english/bureau/stat/isco/

---

## 📞 Soporte

**Proyecto:** Monitor de Ofertas Laborales - OEDE
**Mantenedor:** Observatorio de Empleo y Dinámica Empresarial
**Última actualización:** 30 de octubre de 2025

---

**FIN DEL DOCUMENTO**
