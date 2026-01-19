# 🗺️ Mapa Completo del Proyecto - De Scraping a Análisis

## 📊 Vista General del Flujo

```
INTERNET → SCRAPING → CONSOLIDACIÓN → NLP EXTRACTION → ESCO MATCHING → ANÁLISIS
  (Web)      (1)          (2)              (3)              (4)           (5)
```

---

## 🔄 Flujo Detallado por Fase

### FASE 0: 🌐 Web (Datos originales)

**Fuentes:**
- Bumeran.com.ar
- ZonaJobs.com.ar
- Indeed.com.ar
- ComputrabajoArgentina
- LinkedIn

---

### FASE 1: 📥 SCRAPING (Carpeta: `01_sources/`)

**Objetivo:** Extraer ofertas laborales de cada portal web

#### 🎯 Por cada fuente:

```
01_sources/
├── bumeran/
│   ├── scripts/
│   │   ├── bumeran_scraper.py          [Scraper principal]
│   │   └── run_bumeran_scraper.py      [Ejecutor]
│   ├── data/
│   │   ├── raw/
│   │   │   └── bumeran_full_YYYYMMDD.csv    [OUTPUT: Ofertas scrapeadas]
│   │   └── tracking/
│   │       └── bumeran_tracking.json        [Control de scraping incremental]
│   └── README.md
│
├── zonajobs/
│   ├── scripts/
│   │   ├── zonajobs_scraper.py
│   │   └── consolidar_zonajobs.py      [Consolida múltiples archivos]
│   ├── data/
│   │   ├── raw/
│   │   │   ├── zonajobs_YYYYMMDD.csv         [Scraping individual]
│   │   │   └── zonajobs_consolidacion_*.csv  [OUTPUT: Consolidado]
│   │   └── tracking/
│   │       └── zonajobs_tracking.json
│   └── README.md
│
├── indeed/
│   ├── scripts/
│   │   ├── indeed_scraper.py
│   │   └── consolidar_indeed.py
│   ├── data/
│   │   ├── raw/
│   │   │   ├── indeed_YYYYMMDD_HHMMSS.json   [Scraping individual]
│   │   │   └── indeed_consolidacion.json     [OUTPUT: Consolidado]
│   │   └── tracking/
│   │       └── indeed_tracking.json
│   └── README.md
│
├── computrabajo/  [Similar estructura]
└── linkedin/      [Similar estructura]
```

**Archivos clave de OUTPUT de Fase 1:**
- ✅ `01_sources/bumeran/data/raw/bumeran_full_20241025.csv` (2,460 ofertas)
- ✅ `01_sources/zonajobs/data/raw/zonajobs_consolidacion_20241025.csv` (3 ofertas)
- ✅ `01_sources/indeed/data/raw/indeed_consolidacion.json` (6,009 ofertas)

**Características:**
- Tracking incremental (no duplica ofertas)
- Datos RAW sin procesar
- Columnas originales de cada portal

---

### FASE 2: 🧠 NLP EXTRACTION (Carpeta: `02.5_nlp_extraction/`)

**Objetivo:** Extraer información estructurada de descripciones de texto

#### Estructura:

```
02.5_nlp_extraction/
├── scripts/
│   ├── extractors/
│   │   ├── base_nlp_extractor.py       [Clase abstracta base]
│   │   ├── bumeran_extractor.py        [Extractor Bumeran - Regex]
│   │   ├── zonajobs_extractor.py       [Extractor ZonaJobs - Regex]
│   │   ├── indeed_extractor.py         [Extractor Indeed - Regex bilingüe]
│   │   └── base_ner_extractor.py       [Extractor NER (Fase 2B)]
│   │
│   ├── patterns/
│   │   └── regex_patterns.py           [Patrones regex para extracción]
│   │
│   ├── run_nlp_extraction.py           [EJECUTOR: Procesa con Regex]
│   ├── consolidate_nlp_sources.py      [Consolida multi-fuente]
│   │
│   │   ── FASE 2B: NER (Anotación + Training) ──
│   ├── prepare_ner_dataset.py          [Selecciona 500 muestras]
│   ├── auto_annotate_with_ollama.py    [Anota con LLM local] ⭐ CORRIENDO
│   ├── auto_annotate_with_llm.py       [Anota con API (OpenAI/Claude)]
│   ├── auto_annotate_with_regex.py     [Pre-anota con Fase 1]
│   ├── convert_annotations_to_spacy.py [Convierte a formato spaCy]
│   ├── train_ner_model.py              [Entrena modelo NER]
│   └── compare_phase1_vs_phase2.py     [Compara Regex vs NER]
│
├── data/
│   ├── processed/
│   │   ├── bumeran_nlp_20251025.csv            [Bumeran con NLP Regex]
│   │   ├── zonajobs_nlp_20251025.csv           [ZonaJobs con NLP Regex]
│   │   ├── indeed_nlp_20251025.csv             [Indeed con NLP Regex]
│   │   ├── all_sources_nlp_20251025_141134.csv [OUTPUT FASE 2A: Consolidado Regex]
│   │   └── all_sources_ner_YYYYMMDD.csv        [OUTPUT FASE 2B: Con NER]
│   │
│   └── ner_training/
│       ├── ner_samples_for_annotation_*.jsonl  [500 muestras seleccionadas]
│       ├── ner_samples_*_ollama_annotated.jsonl [Anotadas con Ollama] ⭐ GENERANDO
│       └── spacy_format/
│           ├── train_data.json                  [80% para training]
│           └── dev_data.json                    [20% para validación]
│
├── models/
│   └── ner_model/
│       ├── model_YYYYMMDD_HHMMSS/              [Modelo NER entrenado]
│       └── latest/ → symlink                    [Apunta al último]
│
├── config/
│   ├── fields_mapping.json             [Esquema de campos NLP]
│   └── skills_database.json            [215 skills técnicas + 60 soft]
│
├── docs/
│   ├── WEEK3_PROGRESS.md               [Reporte Fase 2A completada]
│   ├── PHASE2_NER_WORKFLOW.md          [Workflow Fase 2B]
│   └── ANNOTATION_GUIDE.md             [Guía para anotadores]
│
└── reports/
    └── phase1_vs_phase2_comparison_*.md [Comparación Regex vs NER]
```

**INPUT de Fase 2:**
- ⬅️ `01_sources/*/data/raw/*.csv` (Datos scrapeados)

**OUTPUT de Fase 2A (Regex - COMPLETADO):**
- ✅ `all_sources_nlp_20251025_141134.csv` (8,472 ofertas con 23 campos NLP)
  - Campos extraídos: experiencia, educación, skills, idiomas, etc.
  - Método: Patrones Regex
  - Confidence: 0.26 promedio
  - Cobertura: 29-63% según campo

**OUTPUT de Fase 2B (NER - EN PROCESO):**
- ⏳ Anotaciones: 55% completado (277/500) ⭐ CORRIENDO AHORA
- ⏳ Modelo NER: Pendiente training
- ⏳ `all_sources_ner_*.csv`: Pendiente procesamiento

---

### FASE 3: 🏷️ ESCO MATCHING (Carpeta: `03_esco_matching/`)

**Objetivo:** Clasificar ocupaciones usando taxonomía ESCO/ISCO

```
03_esco_matching/
├── scripts/
│   └── integrate_nlp_with_esco.py      [Matcher NLP → ESCO]
│
├── data/
│   └── esco_ocupaciones_con_isco_completo.json [Taxonomía ESCO]
│
└── output/
    └── nlp_esco_enriched_*.csv         [OUTPUT: Ofertas + ESCO]
```

**INPUT de Fase 3:**
- ⬅️ `02.5_nlp_extraction/data/processed/all_sources_nlp_*.csv`
- ⬅️ `D:\Trabajos en PY\EPH-ESCO\07_esco_data\esco_ocupaciones_con_isco_completo.json`

**OUTPUT de Fase 3:**
- ⏳ `nlp_esco_enriched_*.csv` (Ofertas con código ESCO/ISCO)
- Matching en background (corriendo en paralelo)

**Características:**
- Matching semántico: SequenceMatcher + Jaccard
- Threshold configurable (default: 0.6)
- Agrega: `ocupacion_esco_uri`, `isco_code`, `similarity_score`

---

### FASE 4: 📊 ANÁLISIS (Carpeta: `04_analysis/`)

**Objetivo:** Análisis exploratorio y visualizaciones

```
04_analysis/
└── [FUTURO - No implementado aún]
```

**INPUT de Fase 4:**
- ⬅️ `03_esco_matching/output/nlp_esco_enriched_*.csv`

**OUTPUT esperado de Fase 4:**
- Dashboards
- Visualizaciones
- Estadísticas por ocupación/sector
- Tendencias de skills demandadas

---

## 📈 Estado Actual del Proyecto

### ✅ COMPLETADO

| Fase | Descripción | Archivos Principales | Estado |
|------|-------------|---------------------|--------|
| **1. Scraping** | Extracción de web | `bumeran_full_*.csv` (2,460)<br>`indeed_consolidacion.json` (6,009)<br>`zonajobs_consolidacion_*.csv` (3) | ✅ 100% |
| **2A. NLP Regex** | Extracción con regex | `all_sources_nlp_20251025_141134.csv` (8,472)<br>23 campos NLP extraídos | ✅ 100% |

### ⏳ EN PROCESO

| Fase | Descripción | Estado | ETA |
|------|-------------|--------|-----|
| **2B. NLP NER** | Anotación con Ollama | 55% (277/500) ⭐ | ~10 min |
| **3. ESCO Matching** | Clasificación ocupacional | Running background | ~15 min |

### 📋 PENDIENTE

| Fase | Descripción | Depende de |
|------|-------------|------------|
| **2B. NER Training** | Entrenar modelo spaCy | Anotación Ollama |
| **2B. NER Processing** | Procesar 8,472 ofertas con NER | Modelo entrenado |
| **2B. Comparison** | Comparar Regex vs NER | NER processing |
| **4. Análisis** | Dashboards y visualizaciones | ESCO matching |

---

## 🔀 Flujo de Datos Completo

```
┌────────────────────────────────────────────────────────────────┐
│                     INTERNET (5 portales)                      │
└────────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────────┐
│  FASE 1: SCRAPING (01_sources/)                                │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │  Bumeran    │  │  ZonaJobs   │  │   Indeed    │  ...       │
│  │  scraper.py │  │  scraper.py │  │  scraper.py │            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
│         ↓               ↓                 ↓                     │
│  bumeran_full.csv  zonajobs_*.csv  indeed_*.json               │
│    (2,460)            (3)            (6,009)                    │
└────────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────────┐
│  FASE 2A: NLP EXTRACTION - REGEX (02.5_nlp_extraction/)  ✅    │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  run_nlp_extraction.py                                   │ │
│  │    ├─ BumeranExtractor  (regex_patterns.py)             │ │
│  │    ├─ ZonaJobsExtractor                                 │ │
│  │    └─ IndeedExtractor                                   │ │
│  └──────────────────────────────────────────────────────────┘ │
│                         ↓                                      │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  consolidate_nlp_sources.py                              │ │
│  └──────────────────────────────────────────────────────────┘ │
│                         ↓                                      │
│  all_sources_nlp_20251025_141134.csv (8,472 ofertas)          │
│  Columnas: 56 (originales + 23 NLP)                           │
│  - experiencia_min_anios, experiencia_max_anios               │
│  - nivel_educativo, titulo_requerido                          │
│  - idioma_principal, nivel_idioma_principal                   │
│  - skills_tecnicas_list, soft_skills_list                     │
│  - jornada_laboral, modalidad_trabajo                         │
│  - nlp_confidence_score (0.26 promedio)                       │
└────────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────────┐
│  FASE 2B: NLP EXTRACTION - NER (02.5_nlp_extraction/)    ⏳   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │  1. prepare_ner_dataset.py                         ✅  │  │
│  │     └─ Selecciona 500 muestras estratificadas          │  │
│  │        └─ ner_samples_for_annotation_*.jsonl           │  │
│  └─────────────────────────────────────────────────────────┘  │
│                         ↓                                      │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │  2. auto_annotate_with_ollama.py               ⏳ 55%  │  │
│  │     └─ Anota con llama3 local                          │  │
│  │        └─ ner_samples_*_ollama_annotated.jsonl         │  │
│  └─────────────────────────────────────────────────────────┘  │
│                         ↓                                      │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │  3. convert_annotations_to_spacy.py            ⏳      │  │
│  │     └─ train_data.json + dev_data.json                 │  │
│  └─────────────────────────────────────────────────────────┘  │
│                         ↓                                      │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │  4. train_ner_model.py                         ⏳      │  │
│  │     └─ models/ner_model/model_YYYYMMDD/                │  │
│  └─────────────────────────────────────────────────────────┘  │
│                         ↓                                      │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │  5. base_ner_extractor.process_dataframe()     ⏳      │  │
│  │     └─ all_sources_ner_YYYYMMDD.csv (8,472 + NER)      │  │
│  └─────────────────────────────────────────────────────────┘  │
│                         ↓                                      │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │  6. compare_phase1_vs_phase2.py                ⏳      │  │
│  │     └─ phase1_vs_phase2_comparison.md                  │  │
│  └─────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────────┐
│  FASE 3: ESCO MATCHING (03_esco_matching/)            ⏳      │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  integrate_nlp_with_esco.py                              │ │
│  │    ├─ INPUT: all_sources_nlp_*.csv                       │ │
│  │    ├─ ESCO: esco_ocupaciones_con_isco_completo.json     │ │
│  │    └─ Matching: SequenceMatcher + Jaccard               │ │
│  └──────────────────────────────────────────────────────────┘ │
│                         ↓                                      │
│  nlp_esco_enriched_YYYYMMDD.csv                                │
│  Nuevas columnas:                                              │
│  - ocupacion_esco_uri                                          │
│  - ocupacion_esco_codigo                                       │
│  - ocupacion_esco_label                                        │
│  - isco_code (clasificación internacional)                    │
│  - similarity_score                                            │
└────────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────────┐
│  FASE 4: ANÁLISIS (04_analysis/)                      📋      │
│  [FUTURO - No implementado]                                    │
│  - Dashboards interactivos                                     │
│  - Análisis por sector/ocupación                              │
│  - Tendencias de skills                                        │
│  - Visualizaciones                                             │
└────────────────────────────────────────────────────────────────┘
```

---

## 📊 Archivos Clave del Proyecto

### 🔴 ARCHIVOS FINALES (Los que importan)

| Archivo | Descripción | Filas | Columnas |
|---------|-------------|-------|----------|
| **`01_sources/bumeran/data/raw/bumeran_full_20241025.csv`** | Ofertas Bumeran RAW | 2,460 | ~30 |
| **`01_sources/indeed/data/raw/indeed_consolidacion.json`** | Ofertas Indeed RAW | 6,009 | ~25 |
| **`01_sources/zonajobs/data/raw/zonajobs_consolidacion_*.csv`** | Ofertas ZonaJobs RAW | 3 | ~28 |
| **`02.5_nlp_extraction/data/processed/all_sources_nlp_20251025_141134.csv`** ⭐ | **Ofertas + NLP Regex** | **8,472** | **56** |
| `02.5_nlp_extraction/data/processed/all_sources_ner_*.csv` ⏳ | **Ofertas + NLP NER** (futuro) | 8,472 | ~60 |
| `03_esco_matching/output/nlp_esco_enriched_*.csv` ⏳ | **Ofertas + NLP + ESCO** (futuro) | 8,472 | ~65 |

### 🟢 ARCHIVOS INTERMEDIOS (Proceso)

| Archivo | Propósito |
|---------|-----------|
| `02.5_nlp_extraction/data/ner_training/ner_samples_*_ollama_annotated.jsonl` ⏳ | Anotaciones para NER |
| `02.5_nlp_extraction/data/ner_training/spacy_format/train_data.json` | Training NER |
| `02.5_nlp_extraction/models/ner_model/latest/` | Modelo NER entrenado |

---

## 🎯 Comandos para Reproducir el Flujo

### 1. Scraping (COMPLETADO ✅)

```bash
# Bumeran
cd D:\OEDE\Webscrapping\01_sources\bumeran\scripts
python run_bumeran_scraper.py

# Indeed
cd D:\OEDE\Webscrapping\01_sources\indeed\scripts
python indeed_scraper.py
python consolidar_indeed.py

# ZonaJobs
cd D:\OEDE\Webscrapping\01_sources\zonajobs\scripts
python zonajobs_scraper.py
python consolidar_zonajobs.py
```

### 2A. NLP Extraction - Regex (COMPLETADO ✅)

```bash
cd D:\OEDE\Webscrapping\02.5_nlp_extraction\scripts

# Procesar cada fuente
python run_nlp_extraction.py --source all

# Consolidar
python consolidate_nlp_sources.py

# OUTPUT: all_sources_nlp_20251025_141134.csv ✅
```

### 2B. NLP Extraction - NER (EN PROCESO ⏳)

```bash
cd D:\OEDE\Webscrapping\02.5_nlp_extraction\scripts

# 1. Preparar dataset ✅
python prepare_ner_dataset.py

# 2. Anotar con Ollama ⏳ CORRIENDO AHORA (55%)
python auto_annotate_with_ollama.py --model llama3

# 3. Convertir a spaCy (después de anotación)
python convert_annotations_to_spacy.py \
    --input ../data/ner_training/ner_samples_*_ollama_annotated.jsonl

# 4. Entrenar modelo NER
python train_ner_model.py \
    --train-data ../data/ner_training/spacy_format/train_data.json \
    --dev-data ../data/ner_training/spacy_format/dev_data.json

# 5. Procesar dataset completo con NER
python -c "
from extractors.base_ner_extractor import BaseNERExtractor
import pandas as pd
df = pd.read_csv('../data/processed/all_sources_nlp_20251025_141134.csv')
extractor = BaseNERExtractor()
df_ner = extractor.process_dataframe(df)
df_ner.to_csv('../data/processed/all_sources_ner_YYYYMMDD.csv', index=False)
"

# 6. Comparar
python compare_phase1_vs_phase2.py \
    --phase1 ../data/processed/all_sources_nlp_20251025_141134.csv \
    --phase2 ../data/processed/all_sources_ner_YYYYMMDD.csv
```

### 3. ESCO Matching (EN BACKGROUND ⏳)

```bash
cd D:\OEDE\Webscrapping\03_esco_matching\scripts

python integrate_nlp_with_esco.py \
    --nlp-dataset ../../02.5_nlp_extraction/data/processed/all_sources_nlp_20251025_141134.csv \
    --esco-data "D:\Trabajos en PY\EPH-ESCO\07_esco_data\esco_ocupaciones_con_isco_completo.json" \
    --threshold 0.5

# OUTPUT: nlp_esco_enriched_*.csv
```

---

## 🔍 Cómo Encontrar Archivos

### Por Fase:

```bash
# FASE 1: Datos scrapeados
ls D:\OEDE\Webscrapping\01_sources\*/data\raw\

# FASE 2A: NLP Regex (ACTUAL)
ls D:\OEDE\Webscrapping\02.5_nlp_extraction\data\processed\all_sources_nlp_*.csv

# FASE 2B: NER training
ls D:\OEDE\Webscrapping\02.5_nlp_extraction\data\ner_training\

# FASE 2B: Modelo NER
ls D:\OEDE\Webscrapping\02.5_nlp_extraction\models\ner_model\

# FASE 3: ESCO matching
ls D:\OEDE\Webscrapping\03_esco_matching\output\
```

### Archivo Principal Actual:

```bash
# ⭐ ESTE ES EL ARCHIVO MÁS IMPORTANTE AHORA:
D:\OEDE\Webscrapping\02.5_nlp_extraction\data\processed\all_sources_nlp_20251025_141134.csv

# Contiene:
# - 8,472 ofertas de trabajo
# - 56 columnas (33 originales + 23 NLP)
# - Extraídas de Bumeran (2,460) + Indeed (6,009) + ZonaJobs (3)
# - Con campos NLP: experiencia, educación, skills, idiomas, etc.
```

---

## 📚 Documentación por Fase

| Fase | Documentos |
|------|------------|
| **General** | `MAPA_COMPLETO_DEL_PROYECTO.md` (este archivo) |
| **Scraping** | `01_sources/*/README.md` |
| **NLP Regex** | `02.5_nlp_extraction/docs/WEEK3_PROGRESS.md` |
| **NLP NER** | `02.5_nlp_extraction/docs/PHASE2_NER_WORKFLOW.md`<br>`USAR_OLLAMA_GRATIS.md`<br>`ANNOTATION_OPTIONS.md` |
| **ESCO** | `03_esco_matching/scripts/integrate_nlp_with_esco.py` (docstrings) |

---

## ❓ FAQ

**P: ¿Cuál es el archivo más actual con todos los datos?**
R: `02.5_nlp_extraction/data/processed/all_sources_nlp_20251025_141134.csv` (8,472 ofertas con NLP Regex)

**P: ¿Qué estoy ejecutando ahora mismo?**
R: Anotación automática con Ollama para entrenar modelo NER (Fase 2B, paso 2/6, 55% completado)

**P: ¿Cuántos registros tengo en total?**
R: 8,472 ofertas únicas de trabajo

**P: ¿De dónde vienen esos 8,472?**
R: Bumeran (2,460) + Indeed (6,009) + ZonaJobs (3)

**P: ¿Qué columnas tiene el archivo principal?**
R: 56 columnas: ~33 originales (título, descripción, empresa, fecha, etc.) + 23 NLP (experiencia, educación, skills, etc.)

**P: ¿Cuál es la diferencia entre NLP Regex y NLP NER?**
R:
- **Regex (Fase 2A):** Patrones fijos, 0.26 confidence, 29-40% cobertura ✅ HECHO
- **NER (Fase 2B):** Modelo ML entrenado, esperado 0.6 confidence, 60-70% cobertura ⏳ EN PROCESO

**P: ¿Para qué sirve ESCO Matching?**
R: Para clasificar cada oferta con un código ocupacional estándar (ESCO/ISCO), útil para análisis por ocupación

**P: ¿Cuándo estará todo terminado?**
R:
- Anotación Ollama: ~10 minutos
- Training NER: ~30 minutos
- Processing NER: ~15 minutos
- **Total:** ~1 hora desde ahora

---

**Creado:** 27 de Octubre, 2025
**Última actualización:** Durante ejecución de anotación Ollama (55%)
