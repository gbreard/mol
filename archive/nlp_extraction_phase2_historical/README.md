# 02.5 - NLP Extraction

Módulo de extracción de información estructurada desde descripciones de ofertas laborales usando técnicas de NLP.

## Objetivo

Extraer **23 campos estructurados** de las descripciones de texto de ofertas laborales:
- Experiencia requerida (años, área)
- Educación (nivel, estado, carrera)
- Idiomas (idioma, nivel)
- Skills (técnicas, blandas, certificaciones)
- Compensación (salario, beneficios)
- Requisitos (excluyentes, deseables)
- Jornada laboral

## Estructura del Directorio

```
02.5_nlp_extraction/
├── scripts/
│   ├── base_nlp_extractor.py       # Clase base abstracta
│   ├── extractors/                 # Extractores por fuente
│   │   ├── bumeran_extractor.py
│   │   ├── zonajobs_extractor.py
│   │   └── indeed_extractor.py
│   ├── cleaning/                   # Limpieza de texto
│   │   ├── text_cleaner.py
│   │   ├── html_stripper.py
│   │   └── encoding_fixer.py
│   ├── patterns/                   # Patrones regex
│   │   ├── regex_patterns.py
│   │   ├── experiencia_patterns.py
│   │   ├── educacion_patterns.py
│   │   ├── skills_patterns.py
│   │   └── idiomas_patterns.py
│   └── utils/                      # Utilidades
├── data/
│   ├── processed/                  # Resultados finales
│   ├── intermediate/               # Datos intermedios
│   └── logs/                       # Logs de procesamiento
├── tests/                          # Tests unitarios
├── config/
│   └── fields_mapping.json         # Schema de campos
└── README.md
```

## Flujo de Datos

```
01_sources/[fuente]/data/raw/*.csv
    ↓
[Limpieza de texto]
    ↓
[Extracción NLP por fuente]
    ↓
02.5_nlp_extraction/data/processed/[fuente]_nlp_TIMESTAMP.csv
    ↓
[Consolidación multi-fuente]
    ↓
02.5_nlp_extraction/data/processed/all_sources_nlp_TIMESTAMP.csv
    ↓
03_esco_matching/
```

## Fuentes Soportadas

| Fuente | Prioridad | Cobertura Esperada | Estado |
|--------|-----------|-------------------|--------|
| Bumeran | Alta | 90% | Pendiente |
| ZonaJobs | Alta | 90% | Pendiente |
| Indeed | Media | 70% | Pendiente |
| LinkedIn | Baja | 0% (sin descripción) | N/A |
| ComputRabajo | Baja | 0% (sin descripción) | N/A |

## Campos Extraídos (23 campos)

### Experiencia (3 campos)
- `experiencia_min_anios`: int
- `experiencia_max_anios`: int
- `experiencia_area`: string

### Educación (4 campos)
- `nivel_educativo`: enum (secundario, terciario, universitario, posgrado)
- `estado_educativo`: enum (completo, en_curso, incompleto)
- `carrera_especifica`: string
- `titulo_excluyente`: boolean

### Idiomas (4 campos)
- `idioma_principal`: string
- `nivel_idioma_principal`: enum (basico, intermedio, avanzado, nativo)
- `idioma_secundario`: string
- `nivel_idioma_secundario`: enum

### Skills (4 campos)
- `skills_tecnicas_list`: array[string]
- `niveles_skills_list`: array[string]
- `soft_skills_list`: array[string]
- `certificaciones_list`: array[string]

### Compensación (4 campos)
- `salario_min`: float
- `salario_max`: float
- `moneda`: enum (ARS, USD, EUR, BRL)
- `beneficios_list`: array[string]

### Requisitos (2 campos)
- `requisitos_excluyentes_list`: array[string]
- `requisitos_deseables_list`: array[string]

### Jornada (2 campos)
- `jornada_laboral`: enum (full_time, part_time, por_proyecto, freelance)
- `horario_flexible`: boolean

### Metadata (3 campos automáticos)
- `nlp_extraction_timestamp`: string ISO8601
- `nlp_version`: string
- `nlp_confidence_score`: float (0-1)

## Estrategia de Implementación

### Fase 1: Regex Patterns (Semanas 1-2)
- Patrones regex para cada categoría
- Precisión esperada: **70%**
- Implementación rápida
- Base para refinamiento

### Fase 2: NER Custom Models (Semanas 3-4)
- Modelos de Named Entity Recognition
- Precisión esperada: **85%**
- Mejor reconocimiento de skills y certificaciones

### Fase 3: LLM Enhancement (Semanas 5-6)
- LLM para casos complejos
- Precisión esperada: **90%+**
- Refinamiento y edge cases

## Uso

### Procesar una fuente

```python
from scripts.extractors.bumeran_extractor import BumeranExtractor
import pandas as pd

# Cargar datos raw
df = pd.read_csv("01_sources/bumeran/data/raw/bumeran_full_20251023.csv")

# Crear extractor
extractor = BumeranExtractor()

# Procesar
df_nlp = extractor.process_dataframe(
    df,
    descripcion_col="descripcion",
    titulo_col="titulo"
)

# Guardar resultado
df_nlp.to_csv("02.5_nlp_extraction/data/processed/bumeran_nlp_20251025.csv", index=False)
```

### Ver estadísticas de extracción

```python
stats = extractor.get_extraction_stats(df_nlp)
print(stats)
# {
#   'total_ofertas': 2460,
#   'avg_confidence': 0.75,
#   'ofertas_con_experiencia': 1845,
#   'ofertas_con_educacion': 2100,
#   'ofertas_con_idiomas': 980,
#   'ofertas_con_salario': 320
# }
```

## Testing

```bash
# Ejecutar tests
cd 02.5_nlp_extraction
pytest tests/ -v

# Test específico
pytest tests/test_bumeran_extractor.py -v
```

## Limpieza de Datos

Los módulos de limpieza procesan el texto antes de extracción:

```python
from scripts.cleaning import TextCleaner, HTMLStripper, EncodingFixer

# Limpieza completa
text_clean = EncodingFixer.fix_all(text_raw)
text_clean = HTMLStripper.clean_html_full(text_clean)
text_clean = TextCleaner.clean_full(text_clean)
```

## Logs

Los logs de procesamiento se guardan en `data/logs/`:
- `bumeran_extraction_20251025.log`
- `zonajobs_extraction_20251025.log`
- `indeed_extraction_20251025.log`

## Próximos Pasos

1. **Semana 1-2**: Implementar extractores con regex (Bumeran, ZonaJobs, Indeed)
2. **Semana 3-4**: Entrenar modelos NER custom
3. **Semana 5-6**: Integrar LLM para casos complejos
4. **Post-implementación**: Integrar con 03_esco_matching

## Contacto

Para preguntas o mejoras, contactar al equipo de desarrollo.
