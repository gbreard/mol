# 03_esco_matching - Matching con ESCO

## 🎯 Propósito

Este módulo clasifica ofertas laborales usando la taxonomía ESCO (European Skills, Competences, Qualifications and Occupations) y enriquece con skills.

## 📁 Estructura

```
03_esco_matching/
├── scripts/
│   ├── integracion_esco_semantica.py    # Matching principal
│   ├── matching_algorithms.py           # Algoritmos de matching
│   ├── enriquecimiento_skills.py        # Enriquecimiento con skills
│   └── extraccion_ner.py               # Named Entity Recognition
├── data/
│   ├── input/                          # Lee datos consolidados
│   ├── matched/                        # Resultados con ESCO
│   └── logs/
├── esco_tables/                        # Tablas de referencia ESCO
│   ├── occupations_es.csv
│   ├── skills_es.csv
│   └── isco_mappings.csv
├── models/                             # Modelos de NLP
│   └── tfidf_vectorizer.pkl
└── README.md
```

## 🔄 Proceso

### 1. Carga de Datos Consolidados

```python
import pandas as pd

# Lee desde 02_consolidation/data/consolidated/
df = pd.read_csv('../02_consolidation/data/consolidated/ofertas_consolidadas_20251021.csv')
```

### 2. Matching Semántico

Varios algoritmos disponibles:

#### TF-IDF + Similitud Coseno

```python
from matching_algorithms import TFIDFMatcher

matcher = TFIDFMatcher(threshold=0.7)
df['ocupacion_esco'] = df['informacion_basica.titulo'].apply(matcher.match)
```

#### Embeddings + Similitud Semántica

```python
from matching_algorithms import EmbeddingMatcher

matcher = EmbeddingMatcher(model='paraphrase-multilingual-mpnet-base-v2')
df['ocupacion_esco'] = df['informacion_basica.titulo'].apply(matcher.match)
```

### 3. Asignación de Códigos ISCO

```python
from matching_algorithms import asignar_isco

df['isco_code'] = df['ocupacion_esco_code'].apply(asignar_isco)
```

### 4. Enriquecimiento con Skills

```python
from enriquecimiento_skills import enriquecer_skills

df_enriquecido = enriquecer_skills(df)
```

### 5. NER para Habilidades

Extrae habilidades del texto de la oferta:

```python
from extraccion_ner import extraer_skills_del_texto

df['skills_extraidas'] = df['informacion_basica.descripcion'].apply(extraer_skills_del_texto)
```

## 📊 Salida

Datos con clasificación ESCO en `data/matched/`:

```
ofertas_esco_matched_20251021_143000.csv
ofertas_esco_matched_20251021_143000.json
ofertas_esco_analisis_20251021.xlsx  # Con estadísticas
```

## 🎯 Campos Añadidos

El matching añade la sección `clasificacion_esco`:

```json
{
  "clasificacion_esco": {
    "ocupacion_esco_code": "http://data.europa.eu/esco/occupation/...",
    "ocupacion_esco_label": "Software Developer",
    "isco_code": "2512",
    "isco_label": "Software developers",
    "similarity_score": 0.87,
    "skills": [...],
    "matching_method": "tfidf_cosine",
    "matching_timestamp": "2025-10-21T14:30:00Z"
  }
}
```

## 🛠️ Uso

### Ejecutar matching completo

```bash
cd 03_esco_matching/scripts
python integracion_esco_semantica.py
```

### Con opciones

```bash
python integracion_esco_semantica.py \
  --input ../02_consolidation/data/consolidated/ofertas_consolidadas_20251021.csv \
  --threshold 0.75 \
  --method tfidf \
  --enrich-skills
```

## 📈 Métricas de Calidad

El módulo genera métricas:

- **Cobertura**: % de ofertas clasificadas
- **Similitud promedio**: Score promedio de matching
- **Distribución ISCO**: Ofertas por grupo ocupacional
- **Skills más comunes**: Top skills identificadas

## 🔧 Configuración

Editar `config/esco_matching.ini`:

```ini
[matching]
similarity_threshold = 0.70
algorithm = tfidf  # tfidf, embeddings, hybrid
language = es

[esco]
occupations_path = ../esco_tables/occupations_es.csv
skills_path = ../esco_tables/skills_es.csv
isco_mapping_path = ../esco_tables/isco_mappings.csv

[enrichment]
enrich_skills = true
extract_ner = true
max_skills_per_occupation = 20
```

## ➡️ Siguiente Etapa

Los datos clasificados pasan a:
- **04_analysis/** para análisis descriptivo y visualizaciones

---

**Última actualización**: 2025-10-21
