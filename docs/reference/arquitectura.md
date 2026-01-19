# Arquitectura del Sistema

**Versión**: 4.0
**Fecha**: 2025-10-21

---

## 🎯 Visión General

Sistema modular de web scraping multi-fuente con pipeline automatizado de 5 etapas que extrae, normaliza, clasifica y analiza ofertas laborales.

### Principios de Diseño

1. **Separación de Responsabilidades**: Cada etapa es independiente
2. **Escalabilidad**: Fácil agregar nuevas fuentes
3. **Modularidad**: Componentes reutilizables
4. **Schema Único**: Formato común para todas las fuentes
5. **Automatización**: Pipeline end-to-end
6. **Trazabilidad**: Logs y metadatos en cada etapa

---

## 📐 Arquitectura de 5 Etapas

```
┌─────────────────────────────────────────────────────────────┐
│                        PIPELINE COMPLETO                     │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌───────────────┐     ┌───────────────┐    ┌───────────────┐
│ 01_sources    │     │ 02_consolida  │    │ 03_esco       │
│ - zonajobs    │────▶│ - Normaliza   │───▶│ - Clasifica   │
│ - bumeran     │     │ - Deduplica   │    │ - Enriquece   │
│ - computra... │     │ - Valida      │    │               │
└───────────────┘     └───────────────┘    └───────────────┘
                              │
                    ┌─────────┴─────────┐
                    │                   │
                    ▼                   ▼
            ┌───────────────┐   ┌───────────────┐
            │ 04_analysis   │   │ 05_products   │
            │ - Estadísticas│   │ - Datasets    │
            │ - Visualiza.  │   │ - Reportes    │
            │ - Reportes    │   │ - APIs        │
            └───────────────┘   └───────────────┘
```

---

## 🔧 Etapa 01: Sources (Fuentes)

### Responsabilidad
Extraer datos crudos de cada sitio web.

### Características
- ✅ Scrapers independientes por fuente
- ✅ Rate limiting y respeto a robots.txt
- ✅ Datos crudos sin procesar
- ✅ Logs por fuente
- ✅ Configuración independiente

### Estructura
```
01_sources/
├── zonajobs/
│   ├── scrapers/           # Código de scraping
│   ├── data/raw/          # Datos crudos
│   ├── config/            # Config específica
│   └── README.md
└── [otras_fuentes]/
```

### Tecnologías
- `requests` / `httpx` para HTTP
- `BeautifulSoup` / `lxml` para parsing HTML
- `Playwright` para JavaScript
- `pandas` para estructurar datos

### Output
```
zonajobs_raw_20251021_143000.csv
- Campos en formato original
- Sin normalización
- Con metadatos de extracción
```

---

## 🔗 Etapa 02: Consolidation (Consolidación)

### Responsabilidad
Unificar datos de múltiples fuentes en schema común.

### Proceso

```python
# 1. Leer datos crudos de cada fuente
for fuente in fuentes:
    df_raw = leer_datos_crudos(fuente)

    # 2. Normalizar al schema unificado
    normalizer = get_normalizer(fuente)
    df_norm = normalizer.normalize(df_raw)

    dfs.append(df_norm)

# 3. Consolidar todas
df_consolidated = pd.concat(dfs)

# 4. Deduplicar
df_unique = deduplicador.deduplicar(df_consolidated)

# 5. Validar
validar_schema(df_unique)
```

### Componentes Clave

#### Normalizadores
```python
class ZonaJobsNormalizer(BaseNormalizer):
    def normalize(self, df):
        # Mapea campos ZonaJobs → Schema Unificado
        return df_normalized
```

#### Deduplicador
```python
class DeduplicadorOfertas:
    def deduplicar(self, df):
        # 1. Por ID exacto
        # 2. Por similitud de título + empresa
        return df_unique
```

#### Validador
```python
class ValidadorSchema:
    def validar(self, df):
        # Verifica contra schema_unificado.json
        return resultados
```

### Output
```
ofertas_consolidadas_20251021.csv
- Schema unificado
- Sin duplicados
- Validado
```

---

## 🎯 Etapa 03: ESCO Matching

### Responsabilidad
Clasificar ofertas con taxonomía ESCO y enriquecer con skills.

### Proceso

```python
# 1. Cargar datos consolidados
df = pd.read_csv('ofertas_consolidadas.csv')

# 2. Matching semántico
matcher = TFIDFMatcher(threshold=0.7)
for idx, row in df.iterrows():
    titulo = row['informacion_basica.titulo']

    # Match con ESCO
    match = matcher.match(titulo)

    df.loc[idx, 'clasificacion_esco.ocupacion'] = match['label']
    df.loc[idx, 'clasificacion_esco.isco_code'] = match['isco']
    df.loc[idx, 'clasificacion_esco.score'] = match['score']

# 3. Enriquecimiento con skills
df = enriquecer_skills(df)
```

### Algoritmos Disponibles

1. **TF-IDF + Cosine Similarity**
   - Rápido
   - Precisión: ~70%

2. **Embeddings Semánticos**
   - Más lento
   - Precisión: ~85%
   - Modelo: `paraphrase-multilingual-mpnet-base-v2`

3. **Híbrido**
   - Combina ambos
   - Precisión: ~80%

### Enriquecimiento

```python
# Para cada oferta clasificada
for ocupacion_code in df['clasificacion_esco.ocupacion_esco_code']:
    # Buscar skills asociadas en ESCO
    skills = esco_skills[ocupacion_code]

    # Filtrar por tipo
    essential_skills = [s for s in skills if s['type'] == 'essential']
    optional_skills = [s for s in skills if s['type'] == 'optional']
```

### Output
```
ofertas_esco_matched_20251021.csv
- Todas las ofertas con código ISCO
- Skills asociadas
- Scores de similitud
```

---

## 📊 Etapa 04: Analysis (Análisis)

### Responsabilidad
Generar estadísticas, visualizaciones y reportes.

### Análisis Implementados

#### 1. Análisis Descriptivo
```python
- Total de ofertas
- Distribución por fuente
- Top provincias
- Top ocupaciones ISCO
- Modalidades de trabajo
```

#### 2. Análisis Temporal
```python
- Series temporales diarias/semanales
- Tendencias por grupo ISCO
- Heatmaps día × mes
- Ocupaciones emergentes
```

#### 3. Análisis de Skills
```python
- Top 50 skills más demandadas
- Skills por ocupación
- Matriz de co-ocurrencia
```

#### 4. Análisis Geográfico
```python
- Distribución por provincia
- Ofertas remotas vs presenciales
- Densidad geográfica
```

### Visualizaciones

```python
# Generadas automáticamente
1. distribucion_isco.png           # Barras top 20 ISCO
2. temporal_ofertas.png            # Serie temporal
3. heatmap_dia_mes.png             # Heatmap
4. modalidades_trabajo.png         # Pie chart
5. top_skills.png                  # Wordcloud
6. salarios_isco.png               # Boxplots
...
13. dashboard_interactivo.html     # Plotly dashboard
```

### Reportes

```python
# Formatos disponibles
- HTML: Reporte interactivo auto-contenido
- PDF: Reporte imprimible
- Excel: Datos + gráficos
- PowerPoint: Presentación ejecutiva
```

### Output
```
04_analysis/outputs/
├── reports/
│   ├── reporte_completo.html
│   └── reporte_ejecutivo.pdf
└── figures/
    ├── distribucion_isco.png
    └── ...
```

---

## 📦 Etapa 05: Products (Productos)

### Responsabilidad
Empaquetar datasets y reportes para distribución.

### Productos

#### 1. Datasets Publicables
```
ofertas_laborales_argentina_2025.csv
ofertas_isco_clasificadas_2025.xlsx
diccionario_datos.md
metadata.json
```

#### 2. Reportes Finales
```
informe_anual_mercado_laboral_2025.pdf
dashboard_ofertas_2025.html
```

#### 3. API REST (opcional)
```python
FastAPI
├── GET /ofertas
├── GET /ofertas/{id}
├── GET /estadisticas/isco
└── GET /skills/top
```

### Metadatos

```json
{
  "dataset": "Ofertas Laborales Argentina",
  "version": "2025-10-21",
  "fuentes": ["zonajobs"],
  "total_ofertas": 61,
  "fecha_desde": "2025-10-01",
  "fecha_hasta": "2025-10-21",
  "cobertura_esco": "73.8%",
  "licencia": "CC BY 4.0"
}
```

---

## 🔄 Pipeline Automatizado

### Orquestación

```python
class PipelineCompleto:
    def ejecutar_completo(self):
        # Etapa 1: Scraping
        self.etapa_01_scraping()

        # Etapa 2: Consolidación
        self.etapa_02_consolidacion()

        # Etapa 3: ESCO Matching
        self.etapa_03_esco_matching()

        # Etapa 4: Análisis
        self.etapa_04_analisis()

        # Etapa 5: Productos
        self.etapa_05_productos()
```

### Ejecución

```bash
# Todo el pipeline
python pipeline_completo.py --all

# Desde una etapa específica
python pipeline_completo.py --desde-consolidacion

# Solo algunas etapas
python pipeline_completo.py --scraping --consolidacion
```

---

## 🗄️ Schema Unificado

### Diseño

```json
{
  "_metadata": {...},           // Origen y extracción
  "informacion_basica": {...},  // Título, empresa, desc
  "ubicacion": {...},           // Provincia, ciudad
  "modalidad": {...},           // Tipo y modalidad trabajo
  "fechas": {...},              // Publicación, cierre
  "requisitos": {...},          // Experiencia, educación
  "compensacion": {...},        // Salario, beneficios
  "detalles": {...},            // Vacantes, área
  "clasificacion_esco": {...},  // ESCO + ISCO
  "source_specific": {...}      // Campos específicos fuente
}
```

### Ventajas

1. **Interoperabilidad**: Mismo formato para todas las fuentes
2. **Extensibilidad**: `source_specific` para campos únicos
3. **Trazabilidad**: `_metadata` con origen
4. **Validación**: JSON Schema para verificar
5. **Versionado**: Campo `version` en metadata

---

## 📈 Escalabilidad

### Agregar Nueva Fuente

```bash
# 1. Crear estructura
mkdir -p 01_sources/nueva_fuente/{scrapers,data/raw,config}

# 2. Implementar scraper
# 3. Crear normalizador
# 4. Listo - el pipeline lo detecta automáticamente
```

### Horizontal Scaling

```python
# Paralelizar scraping
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=4) as executor:
    futures = [
        executor.submit(scrapear, fuente)
        for fuente in fuentes
    ]
```

### Vertical Scaling

```python
# Usar bases de datos en lugar de CSVs
# PostgreSQL con SQLAlchemy
# Particionamiento por fecha
```

---

## 🔐 Seguridad y Buenas Prácticas

### Scraping Ético

```python
1. Rate limiting (mín 2 seg)
2. Respetar robots.txt
3. User-Agent identificable
4. Solo datos públicos
5. Uso académico/investigación
```

### Datos Sensibles

```python
# No guardar:
- Emails personales
- Teléfonos directos
- Datos de solicitantes

# Anonimizar:
- Empresas si son confidenciales
```

### Validación

```python
# Antes de publicar
1. Validar schema
2. Verificar calidad
3. Remover duplicados
4. Anonimizar si necesario
5. Documentar metadatos
```

---

## 📊 Monitoreo

### Logs Centralizados

```
shared/logs/
├── pipeline.log              # Log general
├── consolidacion.log         # Etapa 2
├── esco_matching.log         # Etapa 3
└── analysis.log              # Etapa 4
```

### Métricas

```python
- Ofertas/hora scrapeadas
- % cobertura ESCO
- Tiempo por etapa
- Errores por fuente
- Calidad de matching
```

---

## 🧪 Testing

### Tests Unitarios
```python
tests/unit/
├── test_normalizers.py
├── test_esco_matcher.py
└── test_deduplicacion.py
```

### Tests de Integración
```python
tests/integration/
└── test_pipeline_completo.py
```

---

## 📚 Tecnologías Utilizadas

| Componente | Tecnología |
|---|---|
| Scraping | requests, Playwright, BeautifulSoup |
| Procesamiento | pandas, numpy |
| NLP/Matching | scikit-learn, sentence-transformers |
| Visualización | matplotlib, seaborn, plotly |
| Validación | jsonschema |
| Pipeline | Python subprocess |
| Testing | pytest |

---

**Arquitectura diseñada para escalar y evolucionar** 🚀
