# Fase 2 - NER Custom Models - Workflow Completo

**Fecha de inicio:** 27 de Octubre, 2025
**Estado:** Scripts preparados - Pendiente anotación manual
**Objetivo:** Mejorar extracción mediante modelo NER custom entrenado con spaCy

---

## Índice

1. [Resumen Ejecutivo](#resumen-ejecutivo)
2. [Contexto: Fase 1 vs Fase 2](#contexto-fase-1-vs-fase-2)
3. [Pipeline Completo](#pipeline-completo)
4. [Paso 1: Preparación del Dataset](#paso-1-preparación-del-dataset)
5. [Paso 2: Anotación Manual](#paso-2-anotación-manual)
6. [Paso 3: Conversión a spaCy](#paso-3-conversión-a-spacy)
7. [Paso 4: Entrenamiento del Modelo](#paso-4-entrenamiento-del-modelo)
8. [Paso 5: Procesamiento con NER](#paso-5-procesamiento-con-ner)
9. [Paso 6: Comparación y Evaluación](#paso-6-comparación-y-evaluación)
10. [Métricas Esperadas](#métricas-esperadas)
11. [Troubleshooting](#troubleshooting)

---

## Resumen Ejecutivo

La Fase 2 implementa un modelo **Named Entity Recognition (NER) custom** entrenado con spaCy para mejorar la extracción de información estructurada de ofertas laborales.

**Principales ventajas sobre Fase 1 (Regex):**
- Captura variaciones lingüísticas no cubiertas por patrones
- Aprende contexto semántico de las entidades
- Puede detectar skills técnicas implícitas
- Mayor precisión en extracción de años de experiencia
- Mejor handling de requisitos con estructura no estándar

**Limitaciones:**
- Requiere anotación manual de 500 ofertas (~8-10 horas de trabajo)
- Necesita reentrenamiento para nuevos tipos de entidades
- Mayor complejidad de deployment

---

## Contexto: Fase 1 vs Fase 2

### Resultados Fase 1 (Regex) - Baseline

| Métrica | Valor | Objetivo |
|---------|-------|----------|
| **Total ofertas procesadas** | 8,472 | ✅ Completo |
| **Confidence promedio** | 0.260 | 🟡 Bajo (obj: 0.60) |
| **Cobertura Experiencia** | 29.2% | ❌ Bajo (obj: 60%) |
| **Cobertura Educación** | 38.6% | ❌ Bajo (obj: 70%) |
| **Cobertura Skills Técnicas** | 40.3% | 🟡 Aceptable (obj: 70%) |
| **Cobertura Soft Skills** | 63.1% | ✅ Excelente |

### Objetivos Fase 2 (NER)

| Métrica | Fase 1 | Objetivo Fase 2 | Mejora esperada |
|---------|--------|-----------------|-----------------|
| **Confidence** | 0.260 | 0.600 | +130% |
| **Cobertura Experiencia** | 29% | 60% | +107% |
| **Cobertura Educación** | 39% | 70% | +79% |
| **Cobertura Skills Técnicas** | 40% | 70% | +75% |
| **Precision** | ~60% | 85% | +42% |

---

## Pipeline Completo

```
┌─────────────────────────────────────────────────────────────────┐
│                      FASE 2 - NER WORKFLOW                      │
└─────────────────────────────────────────────────────────────────┘

1. PREPARACIÓN DEL DATASET (✅ COMPLETADO)
   ├─ Input: all_sources_nlp_20251025_141134.csv (8,472 ofertas)
   ├─ Script: prepare_ner_dataset.py
   └─ Output:
      ├─ ner_samples_for_annotation.jsonl (500 ofertas)
      ├─ ner_samples_for_annotation.csv
      ├─ iob_annotation_template.json
      └─ ANNOTATION_GUIDE.md

2. ANOTACIÓN MANUAL (⏳ PENDIENTE - 8-10 horas)
   ├─ Herramienta: Doccano o Label Studio
   ├─ Entidades: YEARS, EDUCATION, SKILL, SOFT_SKILL, LANGUAGE, AREA
   ├─ Anotadores: 1-2 personas
   └─ Output: annotated_data.jsonl

3. CONVERSIÓN A SPACY (⏳ PENDIENTE)
   ├─ Input: annotated_data.jsonl
   ├─ Script: convert_annotations_to_spacy.py
   └─ Output:
      ├─ train_data.json (400 ejemplos, 80%)
      ├─ dev_data.json (100 ejemplos, 20%)
      └─ label_scheme.json

4. ENTRENAMIENTO DEL MODELO (⏳ PENDIENTE)
   ├─ Input: train_data.json, dev_data.json
   ├─ Script: train_ner_model.py
   ├─ Base model: es_core_news_sm (o blank)
   ├─ Hyperparams: 30 iter, batch 8, dropout 0.3, lr 0.001
   └─ Output: models/ner_model/model_YYYYMMDD_HHMMSS/

5. PROCESAMIENTO CON NER (⏳ PENDIENTE)
   ├─ Input: all_sources_nlp_20251025_141134.csv
   ├─ Script: base_ner_extractor.py
   ├─ Model: models/ner_model/latest/
   └─ Output: all_sources_ner_YYYYMMDD_HHMMSS.csv

6. COMPARACIÓN Y EVALUACIÓN (⏳ PENDIENTE)
   ├─ Input: Fase 1 CSV + Fase 2 CSV
   ├─ Script: compare_phase1_vs_phase2.py
   └─ Output:
      ├─ phase1_vs_phase2_comparison.json
      └─ phase1_vs_phase2_comparison.md
```

---

## Paso 1: Preparación del Dataset

### ✅ Estado: COMPLETADO

**Objetivo:** Seleccionar 500 ofertas representativas para anotación manual.

### Script ejecutado

```bash
python prepare_ner_dataset.py --n-samples 500 --format both
```

### Resultados

- **Total seleccionadas:** 500 ofertas
- **Distribución por fuente:**
  - Indeed: 353 ofertas (70.6%)
  - Bumeran: 145 ofertas (29.0%)
  - ZonaJobs: 2 ofertas (0.4%)

- **Estratificación por riqueza NLP:**
  - Alta (4-5 campos): 40%
  - Media (2-3 campos): 40%
  - Baja (0-1 campos): 20%

### Archivos generados

```
02.5_nlp_extraction/data/ner_training/
├── ner_samples_for_annotation_20251027_101013.jsonl  (1.3 MB)
├── ner_samples_for_annotation_20251027_101013.csv    (1.3 MB)
├── iob_annotation_template.json
└── ANNOTATION_GUIDE.md
```

---

## Paso 2: Anotación Manual

### ⏳ Estado: PENDIENTE

**Objetivo:** Anotar manualmente 500 ofertas con entidades NER.

### Tipos de Entidades

| Entidad | Descripción | Ejemplos |
|---------|-------------|----------|
| **YEARS** | Años de experiencia | "3 años", "mínimo 5 años", "2 a 4 años" |
| **EDUCATION** | Nivel educativo / título | "universitario completo", "licenciatura en sistemas" |
| **SKILL** | Habilidad técnica | "Python", "Django", "SQL", "AWS" |
| **SOFT_SKILL** | Habilidad blanda | "trabajo en equipo", "liderazgo" |
| **LANGUAGE** | Idioma y nivel | "inglés avanzado", "portugués intermedio" |
| **AREA** | Área de experiencia | "desarrollo backend", "análisis de datos" |

### Herramientas Recomendadas

#### Opción 1: Doccano (Recomendado)

**Instalación:**
```bash
pip install doccano
doccano init
doccano createuser --username admin --password admin
doccano webserver --port 8000
```

**Uso:**
1. Acceder a http://localhost:8000
2. Login con admin/admin
3. Crear proyecto "NER Job Offers"
4. Importar `ner_samples_for_annotation.jsonl`
5. Definir labels: YEARS, EDUCATION, SKILL, SOFT_SKILL, LANGUAGE, AREA
6. Anotar ofertas
7. Exportar como JSONL

#### Opción 2: Label Studio

**Instalación:**
```bash
pip install label-studio
label-studio start
```

**Uso:**
1. Acceder a http://localhost:8080
2. Crear proyecto "NER Job Offers"
3. Configurar interfaz de Named Entity Recognition
4. Importar CSV o JSONL
5. Anotar
6. Exportar como JSON

### Tiempo Estimado

- **Tiempo por oferta:** 1-2 minutos
- **Total 500 ofertas:** 8-16 horas
- **Recomendado:** 2 anotadores × 4-8 horas = 8-16 horas totales

### Guías de Anotación

Ver `ANNOTATION_GUIDE.md` para:
- Reglas de anotación detalladas
- Ejemplos por tipo de entidad
- Casos especiales y ambigüedades
- Formato IOB explicado

---

## Paso 3: Conversión a spaCy

### ⏳ Estado: PENDIENTE (después de anotación)

**Objetivo:** Convertir anotaciones a formato de entrenamiento de spaCy.

### Script

```bash
python convert_annotations_to_spacy.py \
    --input annotated_data.jsonl \
    --format doccano \
    --dev-ratio 0.2 \
    --seed 42
```

### Parámetros

- `--input`: Archivo JSONL exportado de Doccano/Label Studio
- `--format`: Formato del archivo (`doccano` o `labelstudio`)
- `--dev-ratio`: Proporción para validation set (default: 0.2 = 20%)
- `--seed`: Seed para reproducibilidad

### Output Esperado

```
02.5_nlp_extraction/data/ner_training/spacy_format/
├── train_data.json       (400 ejemplos, 80%)
├── dev_data.json         (100 ejemplos, 20%)
└── label_scheme.json     (esquema de etiquetas)
```

### Validaciones Automáticas

El script valida:
- ✅ No hay anotaciones superpuestas
- ✅ `start < end` para todas las entidades
- ✅ Todas las entidades tienen texto asociado
- ✅ Balance de clases (warnings si alguna entidad <5% del total)

---

## Paso 4: Entrenamiento del Modelo

### ⏳ Estado: PENDIENTE (después de conversión)

**Objetivo:** Entrenar modelo NER custom con spaCy.

### Prerrequisitos

```bash
# Instalar spaCy y modelo español base
pip install spacy
python -m spacy download es_core_news_sm
```

### Script de Entrenamiento

```bash
python train_ner_model.py \
    --train-data data/ner_training/spacy_format/train_data.json \
    --dev-data data/ner_training/spacy_format/dev_data.json \
    --base-model es_core_news_sm \
    --n-iter 30 \
    --batch-size 8 \
    --dropout 0.3 \
    --learn-rate 0.001 \
    --seed 42
```

### Hyperparameters

| Parámetro | Valor | Descripción |
|-----------|-------|-------------|
| `--n-iter` | 30 | Número de epochs |
| `--batch-size` | 8 | Tamaño de batch |
| `--dropout` | 0.3 | Dropout rate (previene overfitting) |
| `--learn-rate` | 0.001 | Learning rate inicial |
| `--base-model` | es_core_news_sm | Modelo base (o blank) |

### Proceso de Entrenamiento

El script:
1. Carga modelo base de spaCy
2. Agrega componente NER con tipos de entidades custom
3. Entrena durante N iteraciones
4. Evalúa cada 5 iteraciones en dev set
5. Reporta métricas (Precision, Recall, F-score)
6. Guarda modelo entrenado

### Output Esperado

```
02.5_nlp_extraction/models/ner_model/
├── model_20251027_150000/
│   ├── config.cfg
│   ├── meta.json
│   ├── metadata.json        (custom metadata)
│   ├── ner/
│   ├── tokenizer
│   └── vocab/
└── latest -> model_20251027_150000  (symlink)
```

### Métricas Durante Entrenamiento

```
Iter   1 | Loss: 45.2314
Iter   2 | Loss: 38.4521
Iter   3 | Loss: 32.1234
Iter   4 | Loss: 27.8945
Iter   5 | Loss: 24.5612 | P: 0.723 | R: 0.651 | F: 0.685
...
Iter  30 | Loss: 8.2341 | P: 0.857 | R: 0.823 | F: 0.840
```

**Valores deseados al final:**
- Precision (P): > 0.85
- Recall (R): > 0.80
- F-score (F): > 0.82

---

## Paso 5: Procesamiento con NER

### ⏳ Estado: PENDIENTE (después de entrenamiento)

**Objetivo:** Procesar dataset completo con modelo NER entrenado.

### Script de Procesamiento

```bash
# Procesar con modelo NER
python -c "
from extractors.base_ner_extractor import BaseNERExtractor
import pandas as pd

# Cargar dataset Fase 1
df = pd.read_csv('data/processed/all_sources_nlp_20251025_141134.csv')

# Crear extractor NER (usa modelo latest automáticamente)
extractor = BaseNERExtractor()

# Procesar
df_ner = extractor.process_dataframe(
    df,
    descripcion_col='descripcion',
    titulo_col='titulo'
)

# Guardar
df_ner.to_csv('data/processed/all_sources_ner_20251027.csv', index=False)

# Stats
stats = extractor.get_extraction_stats(df_ner)
print(stats)
"
```

### Output Esperado

```
02.5_nlp_extraction/data/processed/
└── all_sources_ner_20251027_HHMMSS.csv  (~30 MB)
```

### Nuevas Columnas Agregadas

Además de las columnas de Fase 1, se agregan:
- `ner_confidence_score`: Score de confianza NER
- `ner_processed_at`: Timestamp de procesamiento
- `ner_model`: Nombre del modelo usado

**Nota:** Los campos extraídos (experiencia, educación, skills, etc.) se sobrescriben con los valores del modelo NER.

---

## Paso 6: Comparación y Evaluación

### ⏳ Estado: PENDIENTE (después de procesamiento)

**Objetivo:** Comparar resultados Fase 1 vs Fase 2 y evaluar mejora.

### Script de Comparación

```bash
python compare_phase1_vs_phase2.py \
    --phase1 data/processed/all_sources_nlp_20251025_141134.csv \
    --phase2 data/processed/all_sources_ner_20251027.csv \
    --output-dir reports/
```

### Reportes Generados

```
02.5_nlp_extraction/reports/
├── phase1_vs_phase2_comparison_YYYYMMDD_HHMMSS.json
└── phase1_vs_phase2_comparison_YYYYMMDD_HHMMSS.md
```

### Métricas Analizadas

1. **Cobertura por campo:**
   - Experiencia, Educación, Skills, Idiomas, etc.
   - Comparación Fase 1 vs Fase 2
   - Delta absoluto y porcentual

2. **Confidence scores:**
   - Promedio Fase 1 vs Fase 2
   - Por fuente (Bumeran, Indeed, ZonaJobs)

3. **Análisis de mejoras:**
   - N° de ofertas mejoradas (más campos extraídos)
   - N° de ofertas sin cambio
   - N° de ofertas empeoradas

4. **Comparación por fuente:**
   - Métricas separadas por fuente
   - Identificar qué fuente se benefició más del NER

### Formato del Reporte Markdown

```markdown
# Comparación Fase 1 (Regex) vs Fase 2 (NER)

## Resumen Ejecutivo
- Total ofertas: 8,472
- Ofertas mejoradas: 3,456 (40.8%)
- Ofertas sin cambio: 4,012 (47.4%)
- Ofertas empeoradas: 1,004 (11.8%)

## Comparación de Cobertura
| Campo | Fase 1 | Fase 2 | Δ | Mejora |
|-------|--------|--------|---|--------|
| Experiencia | 29.2% | 58.3% | +29.1% | ✅ |
| Educación | 38.6% | 67.2% | +28.6% | ✅ |
| Skills técnicas | 40.3% | 68.9% | +28.6% | ✅ |
...
```

---

## Métricas Esperadas

### Escenarios de Éxito

| Métrica | Actual (Fase 1) | Conservador | Optimista | Realista |
|---------|----------------|-------------|-----------|----------|
| **Confidence** | 0.260 | 0.450 | 0.650 | 0.550 |
| **Cob. Experiencia** | 29% | 50% | 70% | 58% |
| **Cob. Educación** | 39% | 60% | 80% | 68% |
| **Cob. Skills** | 40% | 60% | 80% | 67% |
| **Precision** | ~60% | 75% | 90% | 82% |

### Criterios de Éxito

#### ✅ Éxito Total
- Confidence > 0.60
- Cobertura promedio > 65%
- Precision > 85%
- Mejora >30% en al menos 4 campos

#### 🟡 Éxito Parcial
- Confidence > 0.45
- Cobertura promedio > 55%
- Precision > 75%
- Mejora >20% en al menos 3 campos

#### ❌ No Alcanza Expectativas
- Confidence < 0.40
- Cobertura promedio < 50%
- Precision < 70%
- Mejora <15% en mayoría de campos

### Consideraciones de Costo-Beneficio

| Aspecto | Fase 1 (Regex) | Fase 2 (NER) |
|---------|----------------|--------------|
| **Tiempo desarrollo** | 3 semanas | +2 semanas |
| **Tiempo anotación** | 0 horas | 8-16 horas |
| **Costo computacional** | Muy bajo | Bajo-Medio |
| **Mantenibilidad** | Fácil (editar regex) | Media (reentrenar modelo) |
| **Escalabilidad** | Media | Alta |
| **Accuracy esperada** | 60-65% | 80-85% |

**Recomendación:** Fase 2 justificada si:
1. Mejora > 25% en cobertura promedio
2. Precision > 80%
3. Se planea escalar a más fuentes/campos

---

## Troubleshooting

### Problema: Modelo NER no mejora durante entrenamiento

**Síntomas:**
- Loss no disminuye después de primeras iteraciones
- F-score en dev set < 0.50

**Posibles causas y soluciones:**

1. **Datos de entrenamiento insuficientes**
   - Solución: Anotar más ofertas (750-1000 en vez de 500)
   - O: Usar data augmentation

2. **Anotaciones inconsistentes**
   - Solución: Revisar guía de anotación
   - Verificar IAA (Inter-Annotator Agreement) si hay múltiples anotadores
   - Reconciliar discrepancias

3. **Hyperparameters inadecuados**
   - Solución: Probar diferentes combinaciones:
     ```bash
     # Más iteraciones
     --n-iter 50

     # Dropout más bajo (si overfitting)
     --dropout 0.2

     # Learning rate más bajo (si loss oscila)
     --learn-rate 0.0005
     ```

4. **Desbalance de clases**
   - Solución: Verificar distribución de entidades
   - Asegurar al menos 50 ejemplos por tipo de entidad

### Problema: Modelo overfittea

**Síntomas:**
- Loss en train muy bajo (<5) pero en dev alto (>20)
- F-score en train >0.90 pero en dev <0.60

**Soluciones:**
- Aumentar dropout: `--dropout 0.4` o `0.5`
- Reducir n_iter: `--n-iter 20`
- Agregar más datos de entrenamiento

### Problema: Entidades no detectadas en producción

**Síntomas:**
- Modelo detecta pocas o ninguna entidad en nuevas ofertas
- Cobertura similar o peor que Fase 1

**Posibles causas:**
1. **Desajuste train/producción:**
   - Ofertas de producción muy diferentes a las anotadas
   - Solución: Revisar distribución de samples en Step 1

2. **Umbral de confianza muy alto:**
   - spaCy puede estar filtrando entidades con baja confianza
   - Solución: Ajustar threshold en el modelo

3. **Tokenización inconsistente:**
   - Textos con caracteres especiales mal manejados
   - Solución: Mejorar limpieza de texto en preprocessing

### Problema: Tiempo de procesamiento muy lento

**Síntomas:**
- Procesar 8,472 ofertas toma >1 hora
- CPU/GPU al 100% constante

**Soluciones:**
1. **Usar batch processing:**
   ```python
   # En vez de doc = nlp(text)
   docs = nlp.pipe(texts, batch_size=50)
   ```

2. **Deshabilitar pipes innecesarios:**
   ```python
   nlp = spacy.load(model_path, disable=['parser', 'tagger'])
   ```

3. **Usar GPU si disponible:**
   ```bash
   pip install spacy[cuda]
   spacy.require_gpu()
   ```

### Problema: Doccano/Label Studio no carga el JSONL

**Síntomas:**
- Error al importar archivo
- "Invalid format"

**Soluciones:**
1. Verificar encoding UTF-8
2. Verificar formato JSONL (un objeto por línea)
3. Usar herramienta alternativa o formato CSV

---

## Próximos Pasos (Post Fase 2)

### Fase 3: LLM Enhancement (Opcional)

Si Fase 2 no alcanza objetivos o se quiere maximizar accuracy:

1. **LLM Few-shot prompting:**
   - Usar GPT-4 / Claude con ejemplos anotados
   - Mayor accuracy pero más costoso

2. **Ensemble Regex + NER + LLM:**
   - Combinar predicciones de los 3 métodos
   - Maximizar recall (Regex) + precision (NER) + contexto (LLM)

3. **Fine-tuning de LLM:**
   - Fine-tune BERT/RoBERTa en español para task específico
   - Mejor que NER vanilla pero más complejo

### Mejoras Incrementales

- **Agregar más tipos de entidades:** Salario, Jornada, Ubicación
- **Named Entity Linking:** Mapear skills a taxonomía estandarizada
- **Normalización:** "Python" = "python" = "PYTHON"
- **Relaciones entre entidades:** "5 años de Python" → (YEARS=5, SKILL=Python)

---

## Archivos del Proyecto

### Scripts Creados (Fase 2)

```
02.5_nlp_extraction/scripts/
├── prepare_ner_dataset.py                    (✅ 320 líneas)
├── convert_annotations_to_spacy.py           (✅ 280 líneas)
├── train_ner_model.py                        (✅ 420 líneas)
├── compare_phase1_vs_phase2.py               (✅ 380 líneas)
└── extractors/
    └── base_ner_extractor.py                 (✅ 480 líneas)
```

**Total Fase 2:** ~1,880 líneas de código

### Documentación

```
02.5_nlp_extraction/docs/
├── WEEK3_PROGRESS.md                         (Fase 1 completada)
├── PHASE2_NER_WORKFLOW.md                    (Este documento)
└── ANNOTATION_GUIDE.md                       (Guía para anotadores)
```

### Estructura de Directorios

```
02.5_nlp_extraction/
├── scripts/
│   ├── extractors/
│   │   ├── base_nlp_extractor.py            (Fase 1)
│   │   ├── base_ner_extractor.py            (Fase 2)
│   │   ├── bumeran_extractor.py
│   │   ├── zonajobs_extractor.py
│   │   └── indeed_extractor.py
│   ├── patterns/
│   │   └── regex_patterns.py
│   ├── prepare_ner_dataset.py               (Fase 2)
│   ├── convert_annotations_to_spacy.py      (Fase 2)
│   ├── train_ner_model.py                   (Fase 2)
│   ├── compare_phase1_vs_phase2.py          (Fase 2)
│   ├── run_nlp_extraction.py                (Fase 1)
│   └── consolidate_nlp_sources.py           (Fase 1)
├── data/
│   ├── processed/
│   │   ├── all_sources_nlp_*.csv            (Fase 1 output)
│   │   └── all_sources_ner_*.csv            (Fase 2 output)
│   └── ner_training/
│       ├── ner_samples_for_annotation.jsonl
│       ├── ner_samples_for_annotation.csv
│       ├── iob_annotation_template.json
│       └── spacy_format/                    (post-conversión)
│           ├── train_data.json
│           ├── dev_data.json
│           └── label_scheme.json
├── models/
│   └── ner_model/
│       ├── model_YYYYMMDD_HHMMSS/
│       └── latest/                          (symlink)
├── config/
│   └── skills_database.json
├── docs/
│   ├── WEEK3_PROGRESS.md
│   ├── PHASE2_NER_WORKFLOW.md
│   └── ANNOTATION_GUIDE.md
└── reports/                                  (Fase 2 comparisons)
    ├── phase1_vs_phase2_comparison.json
    └── phase1_vs_phase2_comparison.md
```

---

## Conclusión

### Estado Actual

✅ **Scripts preparados y testeados**
✅ **Dataset de 500 ofertas seleccionado estratificadamente**
✅ **Guías de anotación creadas**
✅ **Pipeline completo documentado**

⏳ **Pendiente:**
1. Anotación manual (8-16 horas)
2. Conversión a spaCy
3. Entrenamiento
4. Evaluación

### Esfuerzo Estimado

| Actividad | Tiempo | Responsable |
|-----------|--------|-------------|
| Anotación (500 ofertas) | 8-16 h | Anotador(es) |
| Conversión + Training | 1-2 h | Automático |
| Procesamiento dataset | 30 min | Automático |
| Análisis resultados | 2-3 h | Analista |
| **TOTAL** | **12-22 h** | |

### Recomendación

**Proceder con Fase 2 si:**
- Hay presupuesto para 8-16 horas de anotación
- Los resultados de Fase 1 no son suficientes (cobertura <40%)
- Se planea usar el sistema en producción (justifica inversión)

**Considerar alternativas si:**
- Presupuesto limitado → Mejorar patrones Regex primero
- Necesidad urgente → Usar LLM few-shot (sin training)
- Datos insuficientes → Anotar más ofertas o usar transfer learning

---

**Autor:** Claude Code
**Fecha:** 27 de Octubre, 2025
**Versión:** 1.0
