# MOL - Arquitectura del Sistema

> **Monitor de Ofertas Laborales - Argentina**
> **Versión:** 2.0
> **Última actualización:** 2026-01-03

---

## 1. VISIÓN GENERAL

### 1.1 Problema que resuelve MOL

MOL es un sistema de monitoreo y análisis del mercado laboral argentino que:

1. **Recolecta** ofertas de trabajo de múltiples portales (Bumeran, ZonaJobs, Indeed, ComputrabajoArgentina, LinkedIn)
2. **Extrae** información estructurada mediante NLP (experiencia, educación, skills, beneficios)
3. **Clasifica** cada oferta según la taxonomía ocupacional internacional ESCO/ISCO-08
4. **Normaliza** ubicaciones geográficas según códigos INDEC
5. **Visualiza** tendencias del mercado laboral mediante dashboards interactivos

### 1.2 Flujo de Datos End-to-End

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              INTERNET (5 portales)                               │
│     Bumeran    │    ZonaJobs    │    Indeed    │  Computrabajo  │   LinkedIn    │
└───────┬────────┴───────┬────────┴───────┬──────┴───────┬────────┴───────┬───────┘
        │                │                │              │                │
        ▼                ▼                ▼              ▼                ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        FASE 1: SCRAPING (01_sources/)                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌────────┐ │
│  │bumeran_     │  │zonajobs_    │  │indeed_      │  │computrabajo_│  │linkedin│ │
│  │scraper.py   │  │scraper.py   │  │scraper.py   │  │scraper.py   │  │_scraper│ │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └───┬────┘ │
└─────────┼────────────────┼────────────────┼────────────────┼─────────────┼──────┘
          │                │                │                │             │
          ▼                ▼                ▼                ▼             ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                   FASE 2: CONSOLIDACIÓN (02_consolidation/)                     │
│                          consolidar_fuentes.py                                   │
│                                    │                                             │
│                                    ▼                                             │
│                            SQLite: ofertas                                       │
│                          (6,521 registros)                                       │
└────────────────────────────────────┬────────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                FASE 3: NLP EXTRACTION (02.5_nlp_extraction/)                    │
│                                                                                  │
│  ┌────────────────────────────────────────────────────────────────────────────┐ │
│  │ Pipeline Anti-Alucinación v10.0 (3 Capas)                                  │ │
│  │                                                                             │ │
│  │  CAPA 0: Regex Determinístico    →  60-70% campos con 100% precisión       │ │
│  │          (regex_patterns_v4.py)                                            │ │
│  │                     │                                                       │ │
│  │                     ▼                                                       │ │
│  │  CAPA 1: LLM Restringido         →  7 campos semánticos (Qwen2.5:14b)      │ │
│  │          (extraction_prompt_v10.py)                                        │ │
│  │                     │                                                       │ │
│  │                     ▼                                                       │ │
│  │  CAPA 2: Verificación Substring  →  Descartar alucinaciones                │ │
│  │          (verificación literal)                                            │ │
│  └────────────────────────────────────────────────────────────────────────────┘ │
│                                    │                                             │
│                                    ▼                                             │
│                            SQLite: ofertas_nlp                                   │
│                          (5,479 registros - 84%)                                 │
└────────────────────────────────────┬────────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                  FASE 4: ESCO MATCHING (03_esco_matching/)                      │
│                                                                                  │
│  ┌────────────────────────────────────────────────────────────────────────────┐ │
│  │ Algoritmo BGE-M3 v2.1.1 (100% Gold Set)                                    │ │
│  │                                                                             │ │
│  │  PASO 1: Título (50%)       →  BGE-M3 embeddings + cosine similarity       │ │
│  │  PASO 2: Skills (40%)       →  ChromaDB lookup semántico                   │ │
│  │  PASO 3: Descripción (10%)  →  BGE-M3 embeddings                          │ │
│  │  PASO 4: Filtros ISCO       →  area_funcional + nivel_seniority            │ │
│  └────────────────────────────────────────────────────────────────────────────┘ │
│                                    │                                             │
│                                    ▼                                             │
│                        SQLite: ofertas_esco_matching                             │
│                          (6,521 registros)                                       │
└────────────────────────────────────┬────────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                       FASE 5: DASHBOARDS (Visual--/)                            │
│                                                                                  │
│  ┌──────────────────────┐  ┌──────────────────────┐  ┌──────────────────────┐   │
│  │ validacion_pipeline_ │  │ dashboard_ocupaciones│  │ dashboard_territorial│   │
│  │ app_v3.R (validación)│  │ _v2.R                │  │ _v2.R                │   │
│  └──────────────────────┘  └──────────────────────┘  └──────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 1.3 Stack Tecnológico

| Capa | Tecnología | Uso |
|------|------------|-----|
| **Scraping** | Python 3.11, Playwright, Requests, Tenacity | Extracción de portales web |
| **Base de Datos** | SQLite 3 | Almacenamiento local (6 tablas principales) |
| **NLP - Regex** | Python re, unicodedata | Extracción determinística (Capa 0) |
| **NLP - LLM** | Qwen2.5:14b via Ollama | Extracción semántica (Capa 1) |
| **Matching** | Sentence-Transformers (BGE-M3), ChromaDB | Búsqueda semántica de ocupaciones |
| **ESCO Model** | jjzha/esco-xlm-roberta-large | Re-ranking especializado |
| **Dashboards** | R Shiny, shinyTree, plotly | Visualización interactiva |
| **Embeddings** | NumPy, .npy files | Almacenamiento de vectores |

---

## 2. COMPONENTES DEL SISTEMA

### 2.1 Scraping (01_sources/)

#### Propósito
Extraer ofertas laborales de 5 portales de empleo argentinos de forma incremental.

#### Archivos principales
```
01_sources/
├── bumeran/
│   └── scrapers/
│       └── bumeran_scraper.py          # Scraper principal (API REST)
├── zonajobs/
│   └── scrapers/
│       └── zonajobs_scraper_final.py   # Scraper con bypass Cloudflare
├── indeed/
│   └── scrapers/
│       └── indeed_scraper.py           # Scraper API/HTML
├── computrabajo/
│   └── scrapers/
│       └── computrabajo_scraper.py     # Scraper HTML
└── linkedin/
    └── scrapers/
        └── linkedin_scraper.py         # Scraper (limitado)
```

#### Inputs
- Credenciales/tokens de APIs (configurados en headers)
- Keywords de búsqueda (`data/config/search_keywords.json`)
- IDs ya scrapeados (`data/tracking/*_scraped_ids.json`)

#### Outputs
- JSONs crudos: `01_sources/{portal}/data/raw/{portal}_*.json`
- CSVs consolidados: `01_sources/{portal}/data/raw/{portal}_consolidacion.csv`
- Métricas: `01_sources/{portal}/data/metrics/metrics_*.json`

#### Dependencias
- `02_consolidation/scripts/incremental_tracker.py` (tracking de IDs)
- `tenacity` (reintentos)
- `playwright` (para sitios con JavaScript)

---

### 2.2 Consolidación (02_consolidation/)

#### Propósito
Unificar ofertas de múltiples fuentes en un esquema común y cargarlas a SQLite.

#### Archivos principales
```
02_consolidation/
└── scripts/
    ├── consolidar_fuentes.py           # Consolidación multi-fuente
    ├── normalizar_campos.py            # Normalización de campos
    ├── deduplicacion.py                # Detección de duplicados
    └── incremental_tracker.py          # Tracking de IDs procesados
```

#### Inputs
- JSONs/CSVs de `01_sources/*/data/raw/`

#### Outputs
- Tabla `ofertas` en `database/bumeran_scraping.db`
- Campos normalizados: `provincia_normalizada`, `codigo_provincia_indec`

#### Dependencias
- Ninguna externa (solo pandas, sqlite3)

---

### 2.3 NLP Extraction (02.5_nlp_extraction/)

#### Propósito
Extraer información estructurada de las descripciones de ofertas usando un pipeline de 3 capas anti-alucinación.

#### Archivos principales
```
02.5_nlp_extraction/
├── scripts/
│   └── patterns/
│       ├── regex_patterns_v4.py        # CAPA 0: 7 clases de regex
│       └── regex_patterns_v3.py        # Clases base heredadas
├── prompts/
│   └── extraction_prompt_v10.py        # CAPA 1: Prompt ultra-conservador
└── (pipeline ejecuta desde database/)

database/
└── process_nlp_from_db_v10.py          # Pipeline principal v10.0 (153 campos)
```

#### Inputs
- Tabla `ofertas` (columna `descripcion_utf8`)
- Ollama corriendo con modelo `qwen2.5:14b`

#### Outputs
- Tabla `ofertas_nlp` (153 campos - NLP Schema v5)
- Postprocessor para correcciones y normalizaciones

#### Dependencias
- Ollama (`http://localhost:11434`)
- `qwen2.5:14b` model (14B params)

---

### 2.4 ESCO Matching (03_esco_matching/ + database/)

#### Propósito
Clasificar cada oferta según la taxonomía ocupacional ESCO/ISCO-08 usando matching multicriteria.

#### Archivos principales
```
database/
├── match_ofertas_v2.py                 # Algoritmo v2.1.1 BGE-M3 (100% Gold Set)
├── test_gold_set_v211.py               # Test harness Gold Set
├── gold_set_manual_v2.json             # Gold Set (49 casos)
└── embeddings/
    ├── esco_occupations_embeddings.npy # Embeddings BGE-M3 de ocupaciones
    └── esco_occupations_metadata.json  # Metadata de 3,045 ocupaciones

config/
├── matching_config.json                # Config principal (pesos, umbrales)
├── area_funcional_esco_map.json        # Mapeo area_funcional → ISCO
├── nivel_seniority_esco_map.json       # Mapeo seniority → ISCO
└── sector_isco_compatibilidad.json     # Compatibilidad sector ↔ ISCO
```

#### Inputs
- Tabla `ofertas` (título, descripción)
- Tabla `ofertas_nlp` (skills extraídos)
- Tablas ESCO: `esco_occupations`, `esco_skills`, `esco_associations`

#### Outputs
- Tabla `ofertas_esco_matching` (28 campos)
- Campos clave: `esco_occupation_uri`, `isco_code`, `score_final_ponderado`

#### Dependencias
- `sentence-transformers` (BGE-M3)
- `transformers` (ESCO-XLM re-ranker)
- `numpy` (operaciones con embeddings)

---

### 2.5 Normalización Territorial (database/)

#### Propósito
Normalizar ubicaciones a códigos INDEC para análisis geográfico.

#### Archivos principales
```
database/
├── normalize_territorial.py            # Normalización de provincias/localidades
└── indec_codes.json                    # Diccionario INDEC
```

#### Inputs
- Columna `localizacion` de tabla `ofertas`

#### Outputs
- Columnas en `ofertas`:
  - `provincia_normalizada`
  - `codigo_provincia_indec`
  - `localidad_normalizada`
  - `codigo_localidad_indec`

---

### 2.6 Dashboards (Visual--/)

#### Propósito
Visualización interactiva de datos para validación y análisis.

#### Archivos principales
```
Visual--/
├── validacion_pipeline_app_v3.R        # Dashboard de validación NLP+ESCO
├── dashboard_ocupaciones_v2.R          # Análisis por ocupación ESCO
├── dashboard_territorial_v2.R          # Análisis geográfico
└── components/
    └── tree_esco.R                     # Árbol jerárquico ESCO
```

#### Inputs
- Base de datos SQLite (`database/bumeran_scraping.db`)

#### Outputs
- Aplicación web en puerto 3853

#### Dependencias
- R 4.x, shiny, shinyTree, plotly, DBI, RSQLite

---

## 3. CONTRATOS DE DATOS

### 3.1 Schema: `ofertas` (43 campos)

```sql
CREATE TABLE ofertas (
    -- Identificación
    id_oferta        INTEGER PRIMARY KEY,
    id_empresa       INTEGER,

    -- Contenido principal
    titulo           TEXT NOT NULL,
    empresa          TEXT,
    descripcion      TEXT,
    descripcion_utf8 TEXT,                -- Descripción limpia (UTF-8)

    -- Flags
    confidencial             INTEGER,
    apto_discapacitado       INTEGER,
    empresa_validada         INTEGER,
    empresa_pro              INTEGER,
    tiene_preguntas          INTEGER,
    salario_obligatorio      INTEGER,
    alta_revision_perfiles   INTEGER,
    guardado                 INTEGER,

    -- Ubicación
    localizacion             TEXT,
    provincia_normalizada    TEXT,        -- Normalizado INDEC
    codigo_provincia_indec   TEXT,        -- Código INDEC 2 dígitos
    localidad_normalizada    TEXT,
    codigo_localidad_indec   TEXT,

    -- Trabajo
    modalidad_trabajo        TEXT,        -- remoto/híbrido/presencial
    tipo_trabajo             TEXT,        -- full-time/part-time

    -- Fechas
    fecha_publicacion_original       TEXT,
    fecha_hora_publicacion_original  TEXT,
    fecha_modificado_original        TEXT,
    fecha_publicacion_iso            TEXT,    -- YYYY-MM-DD
    fecha_hora_publicacion_iso       TEXT,
    fecha_modificado_iso             TEXT,
    fecha_publicacion_datetime       TEXT,    -- ISO 8601 con TZ
    fecha_hora_publicacion_datetime  TEXT,
    fecha_modificado_datetime        TEXT,

    -- Clasificación portal
    id_area          INTEGER,
    id_subarea       INTEGER,
    id_pais          INTEGER,

    -- Empresa metadata
    logo_url         TEXT,
    promedio_empresa REAL,
    gptw_url         TEXT,

    -- Plan publicación
    plan_publicacion_id     INTEGER,
    plan_publicacion_nombre TEXT,
    tipo_aviso              TEXT,

    -- Metadata scraping
    portal        TEXT,                   -- bumeran/zonajobs/indeed/etc.
    url_oferta    TEXT,
    scrapeado_en  TEXT DEFAULT datetime('now'),
    cantidad_vacantes INTEGER
);
```

### 3.2 Schema: `ofertas_nlp` (26 campos)

```sql
CREATE TABLE ofertas_nlp (
    id_oferta                TEXT PRIMARY KEY,

    -- Experiencia
    experiencia_min_anios    INTEGER,
    experiencia_max_anios    INTEGER,
    experiencia_area         TEXT,

    -- Educación
    nivel_educativo          TEXT,        -- secundario/terciario/universitario/posgrado
    estado_educativo         TEXT,        -- en_curso/graduado/cursando_ultimo_anio
    carrera_especifica       TEXT,
    titulo_excluyente        INTEGER,     -- 0/1

    -- Idiomas
    idioma_principal         TEXT,
    nivel_idioma_principal   TEXT,        -- basico/intermedio/avanzado/nativo
    idioma_secundario        TEXT,
    nivel_idioma_secundario  TEXT,

    -- Skills (JSON arrays)
    skills_tecnicas_list     TEXT,        -- ["Python", "SQL", ...]
    niveles_skills_list      TEXT,        -- ["avanzado", "intermedio", ...]
    soft_skills_list         TEXT,        -- ["trabajo en equipo", ...]
    certificaciones_list     TEXT,        -- ["PMP", "AWS Certified", ...]

    -- Salario
    salario_min              REAL,
    salario_max              REAL,
    moneda                   TEXT,        -- ARS/USD

    -- Beneficios y requisitos (JSON arrays)
    beneficios_list               TEXT,
    requisitos_excluyentes_list   TEXT,
    requisitos_deseables_list     TEXT,

    -- Jornada
    jornada_laboral          TEXT,        -- full-time/part-time/por_horas
    horario_flexible         INTEGER,     -- 0/1

    -- Metadata NLP
    nlp_extraction_timestamp TEXT,
    nlp_version              TEXT,        -- "8.0.0"
    nlp_confidence_score     REAL         -- 0.0 - 1.0
);
```

### 3.3 Schema: `ofertas_esco_matching` (28 campos)

```sql
CREATE TABLE ofertas_esco_matching (
    id_oferta                TEXT PRIMARY KEY,

    -- Match ESCO
    esco_occupation_uri      TEXT,        -- URI de la ocupación ESCO
    esco_occupation_label    TEXT,        -- Nombre de la ocupación

    -- Scores del algoritmo multicriteria
    occupation_match_score   REAL,        -- Score BGE-M3 título
    rerank_score             REAL,        -- Score ESCO-XLM re-ranking
    score_titulo             REAL,        -- Paso 1: 50% peso
    score_skills             REAL,        -- Paso 2: 40% peso
    score_descripcion        REAL,        -- Paso 3: 10% peso
    score_final_ponderado    REAL,        -- Score final con ajustes

    -- Skills matching
    skills_oferta_json       TEXT,        -- Skills extraídos de la oferta
    skills_matched_essential TEXT,        -- Skills ESCO esenciales matcheados
    skills_matched_optional  TEXT,        -- Skills ESCO opcionales matcheados
    skills_cobertura         REAL,        -- % de cobertura de skills

    -- Estado del match
    match_confirmado         INTEGER,     -- 1 si score >= 0.60 y coverage >= 0.40
    requiere_revision        INTEGER,     -- 1 si necesita revisión humana

    -- Clasificación ISCO
    isco_code                TEXT,        -- Código ISCO-08 completo (ej: "2511")
    isco_nivel1              TEXT,        -- Gran grupo (1 dígito)
    isco_nivel2              TEXT,        -- Subgrupo principal (2 dígitos)

    -- Metadata legacy
    occupation_match_method  TEXT,        -- "v2.1.1_bge_m3"
    titulo_normalizado       TEXT,
    titulo_esco_code         TEXT,
    esco_skills_esenciales_json  TEXT,
    esco_skills_opcionales_json  TEXT,
    skills_demandados_total      INTEGER,
    skills_matcheados_esco       INTEGER,
    skills_sin_match_json        TEXT,

    -- Metadata
    matching_timestamp       TEXT,
    matching_version         TEXT,        -- "v2.1.1_bge_m3"
    confidence_score         REAL
);
```

### 3.4 Formato: `gold_set_manual_v2.json` (49 casos)

```json
[
  {
    "id_oferta": "1118026700",
    "esco_ok": true,
    "comentario": "Match correcto. Vendedor de repuestos -> vendedor de piezas de repuesto de automoviles."
  },
  {
    "id_oferta": "1118027276",
    "esco_ok": false,
    "tipo_error": "sector_funcion",
    "comentario": "Ejecutivo de cuentas comercial mapeado a tecnico de contadores electricos (ocupacion totalmente distinta)."
  }
]
```

**Campos:**
- `id_oferta`: ID de la oferta en la tabla `ofertas`
- `esco_ok`: `true` si el match es correcto, `false` si es incorrecto
- `tipo_error`: Categoría del error (solo si `esco_ok: false`):
  - `sector_funcion`: Sector/área funcional incorrecta
  - `nivel_jerarquico`: Nivel jerárquico incorrecto (junior vs gerente)
  - `tipo_ocupacion`: Tipo de ocupación incorrecta
  - `programa_general`: Pasantías/trainee mal clasificados
- `comentario`: Explicación del match (correcto o incorrecto)

---

## 4. ESTÁNDARES Y ONTOLOGÍAS

### 4.1 ESCO (European Skills, Competences, Qualifications and Occupations)

**Versión utilizada:** ESCO v1.1.2

**Tablas en la base de datos:**

| Tabla | Registros | Descripción |
|-------|-----------|-------------|
| `esco_occupations` | 3,045 | Ocupaciones ESCO con labels en español |
| `esco_skills` | 13,890 | Skills/competencias ESCO |
| `esco_associations` | 134,805 | Relaciones ocupación-skill (essential/optional) |

**Estructura de `esco_occupations`:**
```sql
CREATE TABLE esco_occupations (
    occupation_uri         TEXT PRIMARY KEY,  -- URI único
    occupation_uuid        TEXT NOT NULL,
    esco_code              TEXT,              -- Código ESCO
    isco_code              TEXT,              -- Código ISCO-08 (4 dígitos)
    preferred_label_es     TEXT NOT NULL,     -- Nombre en español
    description_es         TEXT,              -- Descripción en español
    scope_note_es          TEXT,
    broader_occupation_uri TEXT,              -- Ocupación padre (jerarquía)
    hierarchy_level        INTEGER,
    is_regulated           INTEGER DEFAULT 0,
    status                 TEXT DEFAULT 'released'
);
```

**Cómo se hace el matching:**

1. **Generación de embeddings** (una vez):
   - Se generan embeddings BGE-M3 para cada `preferred_label_es`
   - Se guardan en `embeddings/esco_occupations_embeddings.npy`

2. **Matching multicriteria** (por cada oferta):
   ```
   PASO 1 (50%): Título
   - Generar embedding del título de la oferta
   - Buscar 10 ocupaciones más similares (cosine similarity)
   - Re-ranking con ESCO-XLM-RoBERTa

   PASO 2 (40%): Skills
   - Extraer skills de la oferta (NLP)
   - Buscar en esco_associations qué skills tiene cada candidato
   - Calcular matching semántico skill-por-skill

   PASO 3 (10%): Descripción
   - Comparar descripción de oferta vs descripción ESCO

   PASO 4: Ajustes v8.3
   - Aplicar reglas de familias funcionales
   - Aplicar never_confirm para casos ambiguos
   ```

### 4.2 ISCO-08 (International Standard Classification of Occupations)

Cada ocupación ESCO tiene un código ISCO-08 de 4 dígitos.

**Estructura jerárquica:**
```
1xxx - Directores y gerentes
2xxx - Profesionales científicos e intelectuales
3xxx - Técnicos y profesionales de nivel medio
4xxx - Personal de apoyo administrativo
5xxx - Trabajadores de los servicios y vendedores
6xxx - Agricultores y trabajadores agropecuarios
7xxx - Oficiales, operarios y artesanos
8xxx - Operadores de instalaciones y máquinas
9xxx - Ocupaciones elementales
```

### 4.3 INDEC (Códigos de Provincia Argentina)

**Archivo:** `database/indec_codes.json`

**Códigos de provincia (2 dígitos):**
```
02 - Ciudad Autónoma de Buenos Aires
06 - Buenos Aires
10 - Catamarca
14 - Córdoba
18 - Corrientes
22 - Chaco
26 - Chubut
30 - Entre Ríos
34 - Formosa
38 - Jujuy
42 - La Pampa
46 - La Rioja
50 - Mendoza
54 - Misiones
58 - Neuquén
62 - Río Negro
66 - Salta
70 - San Juan
74 - San Luis
78 - Santa Cruz
82 - Santa Fe
86 - Santiago del Estero
90 - Tucumán
94 - Tierra del Fuego
```

### 4.4 Formato de Reglas de Matching (`matching_rules_v83.py`)

```python
# Estructura de familias funcionales
KEYWORDS_COMERCIAL_VENTAS_OFERTA = [
    "vendedor", "vendedora", "ejecutivo de cuentas",
    "asesor comercial", "sales", "ventas", ...
]

KEYWORDS_COMERCIAL_VENTAS_ESCO = [
    "representante comercial", "representante de ventas",
    "vendedor", "promotor de ventas", ...
]

# Detectores
def es_oferta_comercial_ventas(titulo: str, descripcion: str = "") -> bool:
    texto = (titulo + " " + descripcion).lower()
    return any(k in texto for k in KEYWORDS_COMERCIAL_VENTAS_OFERTA)

# Reglas de ajuste
def calcular_ajustes_v83(titulo, descripcion, esco_label) -> Tuple[float, dict, bool]:
    """
    Returns: (ajuste_total, detalle_ajustes, never_confirm)

    Ajustes:
    - Positivos (+0.05): Match correcto en misma familia
    - Negativos (-0.15 a -0.20): Mismatch de familia funcional
    - never_confirm=True: Requiere revisión humana obligatoria
    """
```

**Reglas implementadas en v8.3:**

| Regla | Descripción | Ajuste |
|-------|-------------|--------|
| R1 | Admin vs Analista de Negocios | -0.20, never_confirm |
| R2 | Comercial/Ventas mismatch | -0.20, never_confirm |
| R3 | Farmacia vs Ingeniero | -0.20, never_confirm |
| R4 | Pasantías/Trainee | never_confirm (siempre revisión) |
| R5 | Servicios vs Directivo | -0.15, never_confirm |
| R6 | Operario vs Negocios | -0.20, never_confirm |
| R7 | Vehículos 0KM vs Repuestos | -0.15, never_confirm |
| R8 | Barista vs Comercio café | -0.15, never_confirm |
| R9 | Abogado vs Admin jurídico | -0.15, never_confirm |
| R10 | Junior vs Directivo | -0.20, never_confirm |

---

## 5. PIPELINE DE EJECUCIÓN

### 5.1 Orden de Scripts para Nuevas Ofertas

```bash
# 1. SCRAPING - Obtener nuevas ofertas
cd D:\OEDE\Webscrapping\01_sources\bumeran\scrapers
python bumeran_scraper.py --max-pages 50

# 2. CONSOLIDACIÓN - Cargar a SQLite
cd D:\OEDE\Webscrapping\02_consolidation\scripts
python consolidar_fuentes.py

# 3. NLP EXTRACTION - Extraer datos estructurados
cd D:\OEDE\Webscrapping\database
python process_nlp_from_db_v10.py --mode production --limit 500

# 4. ESCO MATCHING - Clasificar ocupaciones
python match_ofertas_v2.py

# 5. VALIDACIÓN - Verificar contra gold set
python test_gold_set_manual.py
```

### 5.2 Comandos Específicos

**Scraping incremental:**
```bash
# Bumeran (principal)
python 01_sources/bumeran/scrapers/bumeran_scraper.py --max-pages 100

# ZonaJobs (requiere bypass)
python 01_sources/zonajobs/scrapers/zonajobs_scraper_final.py
```

**NLP con batch pequeño (testing):**
```bash
python database/process_nlp_from_db_v10.py --mode test --ids 2163782 2154549 --verbose
```

**Matching con límite:**
```bash
python database/match_ofertas_v2.py --limit 100
```

**Dashboard de validación:**
```bash
Rscript -e "shiny::runApp('Visual--/validacion_pipeline_app_v3.R', port=3853)"
```

### 5.3 Verificaciones Post-Ejecución

| Paso | Verificación | Comando |
|------|--------------|---------|
| Scraping | Nuevos registros en BD | `SELECT COUNT(*) FROM ofertas WHERE scrapeado_en > date('now', '-1 day')` |
| NLP | Cobertura de extracción | `SELECT AVG(nlp_confidence_score) FROM ofertas_nlp WHERE nlp_version = '8.0.0'` |
| Matching | Precisión gold set | `python test_gold_set_manual.py` (esperado: >50%) |
| Matching | Distribución confirmados | `SELECT match_confirmado, COUNT(*) FROM ofertas_esco_matching GROUP BY 1` |

---

## 6. VERSIONADO

### 6.1 Convención de Nombres

```
{componente}_v{major}.{minor}.py

Ejemplos:
- regex_patterns_v4.py       → CAPA 0 del NLP, versión 4
- extraction_prompt_v10.py   → Prompt LLM, versión 10
- match_ofertas_v2.py        → Matching ESCO, versión 2.1.1 BGE-M3
- process_nlp_from_db_v10.py → Pipeline NLP, versión 10 (153 campos)
```

### 6.2 Archivos que se Versionan

| Componente | Archivo actual | Anteriores |
|------------|----------------|------------|
| **Regex patterns** | `regex_patterns_v4.py` | v3, v2, v1 |
| **Prompt LLM** | `extraction_prompt_v10.py` | v9, v8, v7, v6 |
| **Pipeline NLP** | `process_nlp_from_db_v10.py` | v9, v8, v7, v6 |
| **Matching** | `match_ofertas_v2.py` | match_ofertas_multicriteria.py (archivado) |
| **Gold set** | `gold_set_manual_v2.json` | v1 |

### 6.3 Crear Nueva Versión Sin Romper Anterior

```bash
# 1. Copiar archivo actual
cp matching_rules_v83.py matching_rules_v84.py

# 2. Editar la nueva versión
# - Cambiar docstring version
# - Agregar nuevas reglas
# - NO modificar funciones existentes

# 3. Actualizar import en match_ofertas_multicriteria.py
# from matching_rules_v83 import ...  →  from matching_rules_v84 import ...

# 4. Testear contra gold set
python test_gold_set_manual.py

# 5. Si mejora → mantener v84
# Si empeora → revertir import a v83
```

---

## 7. TESTING Y VALIDACIÓN

### 7.1 Benchmark Principal

```bash
cd D:\OEDE\Webscrapping\database
python test_gold_set_manual.py
```

**Output esperado (v2.1.1):**
```
======================================================================
VALIDACION GOLD SET MANUAL - MATCHING ESCO v2.1.1 BGE-M3
======================================================================

[1] Gold set cargado: 49 casos
[2] Matches en DB: 49

----------------------------------------------------------------------
RESULTADOS DETALLADOS:
----------------------------------------------------------------------
[OK] 1118026700
       Titulo: Vendedor de repuestos automotrices...
       ESCO:   vendedor de piezas de repuesto de automoviles...
       Score:  0.782 | CONFIRMADO
...

======================================================================
RESUMEN DE VALIDACION:
======================================================================
  Total evaluados:  49
  Correctos:        49 (100%)
  Incorrectos:      0 (0%)

  PRECISION:        100%

  Sin errores - todos los casos validados correctamente
======================================================================
```

### 7.2 Métricas Medidas

| Métrica | Descripción | Cálculo |
|---------|-------------|---------|
| **Precisión** | % de matches correctos | `correctos / total_evaluados * 100` |
| **Top-3 Match** | ¿La ocupación correcta está en top 3? | Manual |
| **ISCO correcto** | ¿El código ISCO-08 nivel 2 es correcto? | `isco_nivel2 == isco_esperado` |
| **Score range** | ¿El score está en rango esperado? | `0.40 <= score <= 0.95` |

### 7.3 Umbrales de Aceptación

```python
CRITERIOS = {
    "precision_minima": 95.0,      # Gold set test falla si < 95% (actual: 100%)
    "top_3_match": True,           # Ocupación correcta en top 3
    "isco_correcto": True,         # ISCO nivel 2 correcto
    "no_absurdos": True,           # Sin errores sector_funcion graves
    "score_rango": (0.50, 0.95)    # Score final en rango razonable
}
```

### 7.4 Dashboard de Validación Manual

```bash
Rscript -e "shiny::runApp('Visual--/validacion_pipeline_app_v3.R', port=3853)"
```

Permite:
- Revisar ofertas con `requiere_revision = 1`
- Ver resultados de las 3 capas NLP
- Aprobar/rechazar matches ESCO
- Agregar casos al gold set

---

## 8. DECISIONES DE ARQUITECTURA (ADRs)

### ADR-001: ¿Por qué Qwen2.5:14b y no otro modelo?

**Contexto:**
El pipeline NLP v6 usaba Hermes 3:8b, pero tenía problemas de alucinación (inventaba skills no mencionados en el texto).

**Decisión:**
Migrar a Qwen2.5:14b con parámetros ultra-conservadores.

**Razones:**
1. **Más parámetros (14B vs 8B):** Mejor comprensión contextual
2. **Mejor seguimiento de instrucciones:** Qwen es conocido por seguir formatos JSON
3. **Temperatura 0.0:** Máximo determinismo, misma respuesta para mismo input
4. **top_p 0.1:** Restringe vocabulario a tokens más probables

**Consecuencias:**
- Procesamiento más lento (~15s por oferta vs ~8s)
- Requiere GPU con más VRAM (mínimo 12GB)
- Menor tasa de alucinación verificada en CAPA 2

---

### ADR-002: ¿Por qué 3 capas anti-alucinación?

**Contexto:**
Los LLMs son propensos a "inventar" información cuando el texto es ambiguo. En ofertas laborales, esto genera skills falsos que contaminan el análisis.

**Decisión:**
Pipeline de 3 capas donde cada capa agrega precisión:

```
CAPA 0: Regex (100% precisión, ~70% cobertura)
   ↓ merge
CAPA 1: LLM (variable precisión, ~30% cobertura adicional)
   ↓ filtro
CAPA 2: Verificación substring (elimina alucinaciones)
```

**Razones:**
1. **Regex primero:** Lo que se puede extraer sin ambigüedad, se extrae con 100% precisión
2. **LLM restringido:** Solo campos semánticos que requieren comprensión
3. **Verificación literal:** Cada item del LLM debe citar texto EXACTO del aviso

**Consecuencias:**
- Se descartan items válidos si el LLM no cita correctamente
- Preferimos precision sobre recall (mejor tener menos datos correctos)
- Tasa de descarte ~20-30% de items del LLM

---

### ADR-003: ¿Por qué ChromaDB para embeddings?

**Contexto:**
Se necesita buscar ocupaciones ESCO similares a un título de oferta en <100ms.

**Decisión:**
Usar embeddings pre-calculados con búsqueda vectorial.

**Implementación actual:**
- Embeddings guardados en NumPy (.npy)
- Búsqueda con `np.dot()` (cosine similarity)
- ChromaDB disponible pero no activo en producción

**Razones:**
1. **Performance:** Búsqueda en ~3,000 ocupaciones < 50ms
2. **Simplicidad:** NumPy no requiere servidor adicional
3. **Escalabilidad futura:** ChromaDB permite filtros y metadatos

**Consecuencias:**
- Los embeddings deben regenerarse si se actualiza ESCO
- Memoria: ~50MB para embeddings de 3,045 ocupaciones

---

### ADR-004: ¿Por qué SQLite y no PostgreSQL?

**Contexto:**
El sistema procesa ~6,500 ofertas con writes frecuentes durante scraping.

**Decisión:**
SQLite como base de datos principal.

**Razones:**
1. **Portabilidad:** Un solo archivo (`bumeran_scraping.db`)
2. **Sin servidor:** No requiere instalación de daemon
3. **Performance suficiente:** <7,000 registros, reads > writes
4. **Backups simples:** `cp bumeran_scraping.db backup.db`

**Consecuencias:**
- Sin concurrencia de escritura (un proceso a la vez)
- Sin replicación ni clustering
- Máximo práctico: ~100,000 registros sin degradación

**Migración futura:**
Si el sistema crece a >100,000 ofertas o necesita acceso concurrente, considerar PostgreSQL con:
- Docker compose para desarrollo local
- Migraciones con Alembic

---

### ADR-005: ¿Por qué Shiny R y no Streamlit/Dash?

**Contexto:**
Los dashboards deben mostrar datos jerárquicos ESCO con árbol navegable.

**Decisión:**
R Shiny con shinyTree.

**Razones:**
1. **shinyTree:** Único widget maduro para árboles jerárquicos interactivos
2. **Ecosistema R:** Conexión nativa a SQLite con DBI/RSQLite
3. **plotly para R:** Gráficos interactivos consistentes

**Consecuencias:**
- Requiere R instalado (no solo Python)
- Deployment más complejo (shinyapps.io o shiny-server)
- Dos lenguajes en el proyecto (Python + R)

---

## 9. REFERENCIAS

### 9.1 Archivos de Documentación

| Documento | Path | Contenido |
|-----------|------|-----------|
| STATUS.md | `STATUS.md` | Estado actual, issues Linear, comandos frecuentes |
| MAPA_COMPLETO | `MAPA_COMPLETO_DEL_PROYECTO.md` | Flujo detallado end-to-end |
| SCHEMA_DOCUMENTATION | `shared/schemas/SCHEMA_DOCUMENTATION.md` | Schemas de datos |

### 9.2 URLs Externas

- **ESCO Portal:** https://esco.ec.europa.eu/
- **ISCO-08:** https://www.ilo.org/public/english/bureau/stat/isco/isco08/
- **INDEC:** https://www.indec.gob.ar/

### 9.3 Modelos de Machine Learning

| Modelo | Uso | HuggingFace |
|--------|-----|-------------|
| BGE-M3 | Embeddings multilingües | `BAAI/bge-m3` |
| ESCO-XLM | Re-ranking ESCO | `jjzha/esco-xlm-roberta-large` |
| Qwen2.5:14b | Extracción NLP | Via Ollama |

---

> **Mantenedor:** Equipo MOL
> **Licencia:** Uso interno OEDE
> **Última revisión:** 2026-01-03
