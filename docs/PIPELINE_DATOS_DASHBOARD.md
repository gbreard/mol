# Pipeline de Datos: Scraping → Dashboard Shiny

**Sistema:** Monitor de Ofertas Laborales (MOL)
**Fecha:** 2025-11-07
**Versión:** 2.0

---

## Visión General del Pipeline

```
┌───────────────────────────────────────────────────────────────────────┐
│                    PIPELINE DE DATOS MOL v2.0                         │
│                                                                        │
│  Web Scraping → NLP Processing → ESCO Matching → CSV Export → Shiny  │
└───────────────────────────────────────────────────────────────────────┘
```

---

## 1. Etapa de Scraping

### Scripts Responsables
- `01_sources/bumeran/scrapers/scrapear_con_diccionario.py`
- `01_sources/bumeran/scrapers/run_scraping_completo.py`

### Datos Capturados
```
┌─────────────────────────────────────┐
│     WEB SCRAPING - Bumeran.com      │
├─────────────────────────────────────┤
│  Inputs:                            │
│    • Diccionario de keywords        │
│    • Parámetros de búsqueda         │
│                                     │
│  Outputs:                           │
│    • titulo                         │
│    • empresa                        │
│    • descripcion                    │
│    • localizacion                   │
│    • modalidad_trabajo              │
│    • url_oferta                     │
│    • fecha_publicacion_original     │
│    • fecha_scraping                 │
└─────────────────────────────────────┘
           ↓
    [SQLite Database]
    tabla: ofertas
```

### Tabla de Destino: `ofertas`

| Columna | Tipo | Descripción |
|---------|------|-------------|
| id_oferta | INTEGER PK | ID único autogenerado |
| titulo | TEXT | Título de la oferta laboral |
| empresa | TEXT | Nombre de la empresa |
| descripcion | TEXT | Descripción completa (HTML/texto) |
| localizacion | TEXT | Ubicación de la oferta |
| modalidad_trabajo | TEXT | Presencial/Remoto/Híbrido |
| url_oferta | TEXT UNIQUE | URL única de la oferta |
| fecha_publicacion_original | TEXT | Fecha de publicación en el portal |
| fecha_scraping | TIMESTAMP | Timestamp de captura |

**Completitud Actual:** ~100% para ofertas activas

---

## 2. Etapa de Procesamiento NLP

### Script Responsable
- `database/process_nlp_from_db_v5.py` (versión actual: v5.1.0)

### Flujo de Procesamiento

```
┌─────────────────────────────────────────────────────────────┐
│            NLP PROCESSING v5.1 - Claude API                 │
├─────────────────────────────────────────────────────────────┤
│  Input:                                                     │
│    • ofertas.descripcion (texto completo)                   │
│    • ofertas.titulo                                         │
│                                                             │
│  Procesamiento:                                             │
│    • Claude API (Haiku/Sonnet)                              │
│    • Prompt estructurado v5.1                               │
│    • JSON schema validation                                 │
│                                                             │
│  Outputs:                                                   │
│    • experiencia_min_anios / _max_anios                     │
│    • nivel_educativo / estado_educativo                     │
│    • carrera_especifica                                     │
│    • idioma_principal / nivel_idioma_principal              │
│    • skills_tecnicas_list (JSON array)                      │
│    • soft_skills_list (JSON array)                          │
│    • certificaciones_list (JSON array)                      │
│    • salario_min / salario_max / moneda                     │
│    • beneficios_list (JSON array)                           │
│    • requisitos_excluyentes_list / requisitos_deseables_    │
│      list (JSON arrays)                                     │
│    • jornada_laboral                                        │
│    • horario_flexible                                       │
│    • quality_score (0-100)                                  │
└─────────────────────────────────────────────────────────────┘
           ↓
    [SQLite Database]
    tabla: ofertas_nlp_history
```

### Tabla de Destino: `ofertas_nlp_history`

| Columna | Tipo | Descripción |
|---------|------|-------------|
| id | INTEGER PK | ID único autogenerado |
| id_oferta | INTEGER FK | → ofertas.id_oferta |
| nlp_version | TEXT | Versión del procesador (ej: "5.1.0") |
| extracted_data | TEXT JSON | Todos los campos extraídos en JSON |
| quality_score | REAL | Score de calidad (0-100) |
| processing_time_ms | INTEGER | Tiempo de procesamiento |
| processed_at | TIMESTAMP | Timestamp de procesamiento |
| model_used | TEXT | Modelo Claude usado |

**Completitud Actual:**
- Soft Skills: ~85% de ofertas
- Skills Técnicas: ~72% de ofertas
- Nivel Educativo: ~40% de ofertas (no siempre especificado en ofertas)

---

## 3. Etapa de Matching ESCO - Ocupaciones

### Script Responsable
- `database/match_ofertas_to_esco.py`

### Flujo de Matching

```
┌──────────────────────────────────────────────────────────────┐
│         ESCO OCCUPATION MATCHING - Claude API                │
├──────────────────────────────────────────────────────────────┤
│  Inputs:                                                     │
│    • ofertas.titulo                                          │
│    • ofertas.descripcion                                     │
│    • ofertas_nlp_history.extracted_data (context)            │
│                                                              │
│  Procesamiento:                                              │
│    • Claude API con taxonomía ESCO completa                  │
│    • Matching semántico de ocupación                         │
│    • Mapping a jerarquía ISCO                                │
│                                                              │
│  Outputs:                                                    │
│    ✅ claude_esco_code (ej: "2512")                          │
│    ✅ claude_esco_label (ej: "Desarrollador de software")    │
│    ✅ claude_esco_uri                                        │
│    ✅ claude_confidence_score (0-100)                        │
│    ✅ isco_nivel1 / nivel2 / nivel3 / nivel4                 │
│    ✅ isco_nivel1_label / ... / nivel4_label                 │
│    ✅ is_official_translation (bool)                         │
│    ✅ matched_at (timestamp)                                 │
│                                                              │
│    ❌ esco_skills_esenciales_json → NULL                     │
│    ❌ esco_skills_opcionales_json → NULL                     │
│    ❌ esco_knowledge_json → NULL                             │
└──────────────────────────────────────────────────────────────┘
           ↓
    [SQLite Database]
    tabla: ofertas_esco_matching
```

### Tabla de Destino: `ofertas_esco_matching`

| Columna | Tipo | Completitud | Descripción |
|---------|------|-------------|-------------|
| id_oferta | INTEGER PK FK | 100% | → ofertas.id_oferta |
| claude_esco_code | TEXT | **95%** ✅ | Código ESCO (ej: "2512") |
| claude_esco_label | TEXT | **95%** ✅ | Label en español |
| claude_esco_uri | TEXT | **95%** ✅ | URI completa ESCO |
| claude_confidence_score | REAL | **95%** ✅ | Confianza del match (0-100) |
| isco_nivel1 | TEXT | **95%** ✅ | ISCO 1 dígito |
| isco_nivel1_label | TEXT | **95%** ✅ | Label nivel 1 |
| isco_nivel2 | TEXT | **95%** ✅ | ISCO 2 dígitos |
| isco_nivel2_label | TEXT | **95%** ✅ | Label nivel 2 |
| isco_nivel3 | TEXT | **95%** ✅ | ISCO 3 dígitos |
| isco_nivel3_label | TEXT | **95%** ✅ | Label nivel 3 |
| isco_nivel4 | TEXT | **95%** ✅ | ISCO 4 dígitos |
| isco_nivel4_label | TEXT | **95%** ✅ | Label nivel 4 |
| is_official_translation | BOOLEAN | **95%** ✅ | Traducción oficial |
| matched_at | TIMESTAMP | **95%** ✅ | Timestamp de matching |
| **esco_skills_esenciales_json** | TEXT JSON | **0%** ❌ | **VACÍO** |
| **esco_skills_opcionales_json** | TEXT JSON | **0%** ❌ | **VACÍO** |
| **esco_knowledge_json** | TEXT JSON | **0%** ❌ | **VACÍO** |

**Problema Identificado:**
- Líneas 320-327 de `match_ofertas_to_esco.py` NO incluyen columnas de skills en el INSERT
- Líneas 489-490: Skills matching comentado ("deshabilitado temporalmente por incompatibilidad de schema")

---

## 4. Etapa de Enriquecimiento de Skills ESCO

### ⚠️ **ETAPA FALTANTE EN PIPELINE ACTUAL**

```
┌──────────────────────────────────────────────────────────────┐
│       ESCO SKILLS ENRICHMENT - NO INTEGRADO                  │
├──────────────────────────────────────────────────────────────┤
│  Script existente (NO ejecutado automáticamente):            │
│    • database/enriquecer_con_skills_esco.py                  │
│                                                              │
│  Funcionalidad:                                              │
│    • Lee ofertas con claude_esco_code ya asignado            │
│    • Lookup en taxonomía ESCO:                               │
│      - Skills esenciales para la ocupación                   │
│      - Skills opcionales para la ocupación                   │
│      - Knowledge areas asociadas                             │
│    • Escribe resultados                                      │
│                                                              │
│  Problema Actual:                                            │
│    ❌ Trabaja sobre archivos CSV, no sobre base de datos     │
│    ❌ No está integrado en workflow automatizado             │
│    ❌ Requiere conversión CSV → DB → CSV                     │
│                                                              │
│  Solución Propuesta:                                         │
│    ✅ Crear populate_esco_skills_in_db.py                    │
│    ✅ Query ofertas con claude_esco_code                     │
│    ✅ Lookup skills en taxonomía ESCO                        │
│    ✅ UPDATE ofertas_esco_matching con skills                │
└──────────────────────────────────────────────────────────────┘
           ↓ (NO EJECUTADO)
    [SQLite Database]
    tabla: ofertas_esco_matching
    (columnas de skills permanecen NULL)
```

**Impacto:**
- Skills ESCO: 0% de completitud
- Dashboard section vacía

---

## 5. Etapa de Generación de CSV

### Script Responsable
- `database/generar_csv_shiny_desde_db.py`

### Flujo de Exportación

```
┌──────────────────────────────────────────────────────────────┐
│           CSV EXPORT - Database → CSV para Shiny             │
├──────────────────────────────────────────────────────────────┤
│  Query Principal:                                            │
│    SELECT                                                    │
│      o.*,                    -- datos de scraping            │
│      n.extracted_data,       -- datos NLP v5.1               │
│      n.quality_score,                                        │
│      e.*                     -- datos ESCO                   │
│    FROM ofertas o                                            │
│    LEFT JOIN ofertas_nlp_history n                           │
│      ON o.id_oferta = n.id_oferta                            │
│      AND n.nlp_version = '5.1.0'                             │
│    LEFT JOIN ofertas_esco_matching e                         │
│      ON o.id_oferta = e.id_oferta                            │
│    ORDER BY o.fecha_scraping DESC                            │
│                                                              │
│  Transformaciones:                                           │
│    • Parseo de JSON extracted_data → columnas planas         │
│    • Conversión de listas JSON a strings delimitados por "|" │
│    • Cálculo de banderas booleanas:                          │
│      - tiene_skills_nlp                                      │
│      - tiene_ocupacion_esco                                  │
│      - tiene_skills_esco ← SIEMPRE FALSE (datos vacíos)      │
│    • Limpieza y normalización de strings                     │
│                                                              │
│  Output CSV: ofertas_esco_shiny.csv                          │
│    • ~120 columnas                                           │
│    • 5,890 filas (datos actuales)                            │
│    • Encoding: UTF-8 con BOM                                 │
│    • Separador: coma                                         │
└──────────────────────────────────────────────────────────────┘
           ↓
    [Archivo CSV]
    Visual--/ofertas_esco_shiny.csv
```

### Columnas Relevantes del CSV

**Columnas de Skills ESCO (actualmente vacías):**

| Columna | Posición | Formato | Estado Actual |
|---------|----------|---------|---------------|
| `esco_skills_esenciales` | 20 | String (delimitado por "\|") | ❌ Vacía ("") |
| `esco_skills_opcionales` | 22 | String (delimitado por "\|") | ❌ Vacía ("") |
| `tiene_skills_esco` | 46 | Boolean ("True"/"False") | ❌ Siempre "False" |

**Columnas de Skills NLP (funcionando):**

| Columna | Formato | Estado Actual |
|---------|---------|---------------|
| `soft_skills` | String (delimitado por "\|") | ✅ ~85% completitud |
| `skills_tecnicas` | String (delimitado por "\|") | ✅ ~72% completitud |
| `tiene_skills_nlp` | Boolean ("True"/"False") | ✅ Calculado correctamente |

**Columnas de Ocupación ESCO (funcionando):**

| Columna | Estado Actual |
|---------|---------------|
| `claude_esco_label` | ✅ ~95% completitud |
| `isco_nivel1` ... `isco_nivel4` | ✅ ~95% completitud |
| `tiene_ocupacion_esco` | ✅ Calculado correctamente |

---

## 6. Etapa de Visualización - Dashboard Shiny

### Script Responsable
- `Visual--/app.R`

### Flujo de Carga y Visualización

```
┌──────────────────────────────────────────────────────────────┐
│              SHINY DASHBOARD - Visualización                 │
├──────────────────────────────────────────────────────────────┤
│  Carga de Datos (app.R líneas 1-50):                        │
│    datos <- read.csv("ofertas_esco_shiny.csv",              │
│                      encoding = "UTF-8", ...)                │
│                                                              │
│  Procesamiento de Skills:                                    │
│    • procesar_skills() (líneas 49-77)                        │
│      - Split por separador "|"                               │
│      - Conteo de frecuencias                                 │
│      - Ordenamiento descendente                              │
│                                                              │
│  Tabs del Dashboard:                                         │
│    ✅ Resumen General                                        │
│    ✅ Análisis Temporal                                      │
│    ✅ Análisis de Localización                               │
│    ✅ Análisis de Ocupaciones ESCO                           │
│    ✅ Clasificación ISCO                                     │
│    ❌ Análisis de Skills ESCO ← VACÍO (sin datos)           │
│    ✅ Análisis de Skills NLP                                 │
│    ✅ Análisis de Educación                                  │
│    ✅ Análisis de Salarios                                   │
│                                                              │
│  Tab "Análisis de Skills ESCO" (líneas 456-492):            │
│    • infoBox: Skills Esenciales → 0                          │
│    • infoBox: Skills Opcionales → 0                          │
│    • infoBox: Promedio por Oferta → 0                        │
│    • plotlyOutput: "Top 15 Skills Esenciales" → vacío        │
│    • plotlyOutput: "Top 15 Skills Opcionales" → vacío        │
│                                                              │
│  Código Dashboard: ✅ CORRECTO                               │
│  Datos de Entrada: ❌ VACÍOS                                 │
└──────────────────────────────────────────────────────────────┘
           ↓
    [Web Browser]
    http://localhost:3838
```

### Análisis de Dependencias de Datos

```
Pestaña del Dashboard             Datos Necesarios             Estado
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Resumen General              → titulo, empresa, fecha         ✅ OK
2. Análisis Temporal            → fecha_scraping                 ✅ OK
3. Análisis de Localización     → localizacion                   ✅ OK
4. Análisis de Ocupaciones      → claude_esco_label              ✅ OK (95%)
5. Clasificación ISCO           → isco_nivel1..4                 ✅ OK (95%)
6. Análisis de Skills ESCO      → esco_skills_esenciales         ❌ VACÍO (0%)
                                → esco_skills_opcionales         ❌ VACÍO (0%)
7. Análisis de Skills NLP       → soft_skills                    ✅ OK (85%)
                                → skills_tecnicas                ✅ OK (72%)
8. Análisis de Educación        → nivel_educativo                ✅ OK (40%)
9. Análisis de Salarios         → salario_min/max                ✅ OK (60%)
```

---

## 7. Sistema de Validación (Nuevo)

### Script de Validación
- `database/validate_shiny_data_quality.py`

### Arquitectura de Validación

```
┌──────────────────────────────────────────────────────────────┐
│         DATA QUALITY VALIDATION - Pre-CSV Generation         │
├──────────────────────────────────────────────────────────────┤
│  Ejecución:                                                  │
│    • Antes de generar CSV                                    │
│    • Valida datos en base de datos (no en CSV)               │
│    • 3 niveles de severidad                                  │
│                                                              │
│  NIVEL CRÍTICO (bloquea generación de CSV):                  │
│    ✅ ESCO Occupation: ≥95% (actual: 95.2%)                  │
│    ✅ ISCO Nivel 1: ≥95% (actual: 95.2%)                     │
│    ✅ Título: 100% (actual: 100%)                            │
│    ✅ Fecha Publicación: 100% (actual: 100%)                 │
│                                                              │
│  NIVEL IMPORTANTE (genera alertas):                          │
│    ❌ ESCO Skills Esenciales: ≥50% (actual: 0%) ← FALLA     │
│    ❌ ESCO Skills Opcionales: ≥50% (actual: 0%) ← FALLA     │
│    ✅ Soft Skills NLP: ≥80% (actual: 85%)                    │
│    ✅ Skills Técnicas NLP: ≥60% (actual: 72%)                │
│                                                              │
│  NIVEL ADVERTENCIA (monitoreo):                              │
│    ✅ Empresa: ≥90% (actual: 92%)                            │
│    ✅ Localización: ≥80% (actual: 85%)                       │
│    ⚠️ Nivel Educativo: ≥40% (actual: 40%)                    │
│                                                              │
│  Exit Codes:                                                 │
│    • 0: Todo OK                                              │
│    • 1: IMPORTANTE falló (warnings)                          │
│    • 2: CRÍTICO falló (error)                                │
│    • 3: Excepción                                            │
└──────────────────────────────────────────────────────────────┘
```

### Wrapper de Generación Segura

**Script Propuesto:** `database/generar_csv_shiny_validado.py`

```bash
#!/usr/bin/env python3
# Pseudo-código del wrapper

# 1. Ejecutar validación
exit_code = subprocess.call(['python', 'validate_shiny_data_quality.py'])

if exit_code == 2:
    # CRÍTICO: abortar
    print("ERROR CRÍTICO: No se puede generar CSV")
    sys.exit(1)
elif exit_code == 1:
    # IMPORTANTE: avisar pero continuar
    print("ADVERTENCIA: Datos incompletos (skills ESCO vacíos)")
    print("Generando CSV de todos modos...")

# 2. Generar CSV
subprocess.call(['python', 'generar_csv_shiny_desde_db.py'])

# 3. Validar CSV resultante (opcional)
# ... validaciones adicionales en el archivo CSV
```

---

## 8. Flujo Completo Visualizado

### Estado Actual del Pipeline

```
┌───────────┐     ┌───────────┐     ┌────────────┐     ┌─────────┐     ┌───────────┐
│  Scraping │ ──► │    NLP    │ ──► │    ESCO    │ ──► │   CSV   │ ──► │  Shiny    │
│           │     │  v5.1.0   │     │ Occupation │     │  Export │     │ Dashboard │
└───────────┘     └───────────┘     └────────────┘     └─────────┘     └───────────┘
    100%              85%               95%                100%             ⚠️ 87.5%
                                                                          (1 de 8 tabs
                                                                            vacío)

                                    ┌────────────┐
                                    │    ESCO    │ ← MISSING STEP
                                    │   Skills   │   (no integrado)
                                    │ Enrichment │
                                    └────────────┘
                                         0%
```

### Flujo Propuesto con Validación

```
┌───────────┐     ┌───────────┐     ┌────────────┐     ┌────────────┐
│  Scraping │ ──► │    NLP    │ ──► │    ESCO    │ ──► │    ESCO    │
│           │     │  v5.1.0   │     │ Occupation │     │   Skills   │
└───────────┘     └───────────┘     └────────────┘     └────────────┘
    100%              85%               95%                TBD (0% actual)
                                                                │
                                                                ▼
                                        ┌────────────────────────────────┐
                                        │  Data Quality Validation       │
                                        │  • Crítico: Bloquea si falla   │
                                        │  • Importante: Alerta          │
                                        │  • Advertencia: Log            │
                                        └────────────────────────────────┘
                                                                │
                                                                ▼
                                        ┌─────────┐     ┌───────────┐
                                        │   CSV   │ ──► │  Shiny    │
                                        │  Export │     │ Dashboard │
                                        └─────────┘     └───────────┘
                                            100%           ✅ 100%
                                                          (todas las tabs
                                                           con datos)
```

---

## 9. Métricas de Completitud Actuales

### Por Etapa del Pipeline

| Etapa | Completitud | Comentario |
|-------|-------------|------------|
| Scraping | 100% | Datos base completos |
| NLP Processing | 85% | Algunas ofertas sin procesar |
| ESCO Occupation Matching | 95% | Alta tasa de éxito |
| **ESCO Skills Enrichment** | **0%** | **⚠️ Etapa no ejecutada** |
| CSV Export | 100% | Se genera pero con campos vacíos |
| Dashboard Shiny | 87.5% | 7 de 8 tabs funcionan |

### Por Tipo de Dato

| Tipo de Dato | Origen | Completitud |
|--------------|--------|-------------|
| Datos de Scraping | Scraping | 100% |
| Skills NLP | NLP v5.1 | 72-85% |
| Ocupación ESCO | ESCO Matching | 95% |
| Jerarquía ISCO | ESCO Matching | 95% |
| **Skills ESCO** | **(Missing step)** | **0%** |
| Educación NLP | NLP v5.1 | 40% |
| Salario NLP | NLP v5.1 | 60% |

---

## 10. Archivos y Directorios del Pipeline

```
D:\OEDE\Webscrapping\
│
├── 01_sources/
│   └── bumeran/
│       └── scrapers/
│           ├── scrapear_con_diccionario.py          [ETAPA 1]
│           └── run_scraping_completo.py
│
├── database/
│   ├── bumeran_scraping.db                          [BASE DE DATOS]
│   ├── process_nlp_from_db_v5.py                    [ETAPA 2]
│   ├── match_ofertas_to_esco.py                     [ETAPA 3]
│   ├── enriquecer_con_skills_esco.py                [NO INTEGRADO]
│   ├── validate_shiny_data_quality.py               [VALIDACIÓN]
│   ├── generar_csv_shiny_desde_db.py                [ETAPA 5]
│   └── generar_csv_shiny_validado.py                [PROPUESTO]
│
├── Visual--/
│   ├── app.R                                        [ETAPA 6]
│   └── ofertas_esco_shiny.csv                       [CSV EXPORT]
│
└── docs/
    ├── DIAGNOSTICO_SKILLS_ESCO_VACIOS.md
    ├── PIPELINE_DATOS_DASHBOARD.md                  [ESTE ARCHIVO]
    └── GUIA_VALIDACION_DATOS.md                     [TBD]
```

---

## 11. Comandos de Ejecución Manual

### Ejecutar Pipeline Completo (sin validación)

```bash
# 1. Scraping (si hay nuevas ofertas)
cd D:\OEDE\Webscrapping\01_sources\bumeran\scrapers
python run_scraping_completo.py

# 2. NLP Processing (solo ofertas sin procesar)
cd D:\OEDE\Webscrapping\database
python process_nlp_from_db_v5.py --mode production --only-empty

# 3. ESCO Occupation Matching (solo ofertas sin matching)
cd D:\OEDE\Webscrapping\database
python match_ofertas_to_esco.py

# ⚠️ 4. ESCO Skills Enrichment - MISSING STEP
#    (actualmente no existe script integrado)

# 5. CSV Export
cd D:\OEDE\Webscrapping\database
python generar_csv_shiny_desde_db.py

# 6. Iniciar Dashboard
cd D:\OEDE\Webscrapping\Visual--
powershell -File restart_dashboard.ps1
```

### Ejecutar con Validación (propuesto)

```bash
# Validar antes de generar CSV
cd D:\OEDE\Webscrapping\database
python validate_shiny_data_quality.py

# Generar CSV con validación
python generar_csv_shiny_validado.py
```

---

## 12. Tiempo de Ejecución Estimado

| Etapa | Tiempo (5,000 ofertas) | Tiempo (10,000 ofertas) |
|-------|------------------------|-------------------------|
| Scraping | ~30 min | ~60 min |
| NLP v5.1 (incremental) | ~5 min (100 ofertas nuevas) | ~10 min |
| ESCO Matching (incremental) | ~3 min (100 ofertas nuevas) | ~6 min |
| Skills Enrichment (propuesto) | ~2 min | ~4 min |
| Validación | ~5 segundos | ~10 segundos |
| CSV Export | ~15 segundos | ~30 segundos |
| **Total (incremental)** | **~40 min** | **~80 min** |

---

## 13. Dependencias Técnicas

### Python Packages
```
sqlite3 (built-in)
pandas
anthropic (Claude API)
numpy
json (built-in)
pathlib (built-in)
typing (built-in)
```

### R Packages
```r
shiny
shinydashboard
plotly
dplyr
tidyr
lubridate
DT
```

### APIs Externas
- Claude API (Anthropic)
- Bumeran.com (scraping)
- ESCO Taxonomy (offline, incluida en proyecto)

---

## 14. Próximos Pasos para Completar Pipeline

### Prioridad Alta (Corto Plazo)
1. ✅ Crear sistema de validación (HECHO)
2. ⏳ Crear wrapper `generar_csv_shiny_validado.py`
3. ⏳ Implementar `populate_esco_skills_in_db.py` (Etapa 4 faltante)
4. ⏳ Ejecutar skills enrichment sobre datos históricos
5. ⏳ Validar y regenerar CSV

### Prioridad Media (Mediano Plazo)
6. Integrar validación en workflow automatizado
7. Crear scheduled tasks / cron jobs
8. Añadir notificaciones por email/Slack

### Prioridad Baja (Largo Plazo)
9. Dashboard de monitoreo del pipeline
10. Métricas de calidad históricas
11. Alertas proactivas de degradación de datos

---

**Documento generado automáticamente**
**Última actualización:** 2025-11-07
**Versión:** 2.0
