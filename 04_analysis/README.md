# 04_analysis - Análisis Descriptivo

## 🎯 Propósito

Este módulo realiza análisis estadístico, visualizaciones y genera reportes sobre las ofertas laborales ya clasificadas con ESCO.

## 📁 Estructura

```
04_analysis/
├── notebooks/
│   ├── 01_exploratorio.ipynb           # Análisis exploratorio
│   ├── 02_temporal.ipynb               # Series temporales
│   ├── 03_ocupaciones.ipynb            # Análisis por ISCO
│   └── 04_skills.ipynb                 # Análisis de skills
├── scripts/
│   ├── analisis_estadistico.py         # Estadísticas generales
│   ├── analisis_temporal.py            # Análisis temporal
│   ├── visualizaciones.py              # Generación de gráficos
│   └── generar_reportes.py             # Reportes automatizados
├── outputs/
│   ├── reports/                        # Reportes PDF/HTML
│   ├── figures/                        # Gráficos PNG/SVG
│   └── dashboards/                     # Dashboards interactivos
└── README.md
```

## 📊 Tipos de Análisis

### 1. Análisis Descriptivo General

```python
from scripts.analisis_estadistico import AnalisisGeneral

analisis = AnalisisGeneral()
analisis.cargar_datos('../03_esco_matching/data/matched/ofertas_esco_matched_20251021.csv')

# Estadísticas básicas
stats = analisis.estadisticas_basicas()
# - Total de ofertas
# - Ofertas por fuente
# - Ofertas por provincia
# - Modalidades de trabajo
```

### 2. Análisis Temporal

```python
from scripts.analisis_temporal import AnalisisTemporal

temporal = AnalisisTemporal()

# Series temporales
temporal.ofertas_por_dia()
temporal.ofertas_por_semana()
temporal.tendencias_mensuales()

# Heatmaps
temporal.heatmap_dia_semana_mes()
```

### 3. Análisis por Ocupación (ISCO)

```python
from scripts.analisis_estadistico import AnalisisOcupacional

ocupacional = AnalisisOcupacional()

# Top ocupaciones
ocupacional.top_ocupaciones_isco(top=20)

# Distribución por gran grupo ISCO
ocupacional.distribucion_grandes_grupos()

# Ocupaciones emergentes
ocupacional.ocupaciones_emergentes()
```

### 4. Análisis de Skills

```python
from scripts.analisis_estadistico import AnalisisSkills

skills = AnalisisSkills()

# Skills más demandadas
skills.top_skills(top=50)

# Skills por ocupación
skills.skills_por_isco()

# Co-ocurrencia de skills
skills.matriz_coocurrencia()
```

### 5. Análisis Salarial

```python
from scripts.analisis_estadistico import AnalisisSalarial

salarial = AnalisisSalarial()

# Distribución salarial
salarial.distribucion_salarios()

# Salarios por ocupación
salarial.salarios_por_isco()

# Salarios por provincia
salarial.salarios_por_ubicacion()
```

### 6. Análisis Geográfico

```python
from scripts.analisis_estadistico import AnalisisGeografico

geografico = AnalisisGeografico()

# Mapa de calor por provincia
geografico.mapa_calor_provincias()

# Ofertas remotas vs presenciales
geografico.modalidades_por_provincia()
```

## 📈 Visualizaciones

### Generación Automática

```bash
cd 04_analysis/scripts
python visualizaciones.py --input ../03_esco_matching/data/matched/ofertas_esco_matched_20251021.csv
```

Genera 13+ visualizaciones:
1. Distribución por fuente
2. Top 20 ocupaciones ISCO
3. Ofertas por provincia
4. Series temporales diarias
5. Heatmap día × mes
6. Modalidades de trabajo
7. Top 30 skills
8. Salarios por ocupación
9. Skills por gran grupo ISCO
10. Tendencias mensuales
11. Ocupaciones emergentes
12. Co-ocurrencia de skills
13. Dashboard interactivo

### Formatos de Salida

- **PNG** (300 DPI) para impresión
- **SVG** para web
- **HTML** interactivo (Plotly)

## 📄 Reportes

### Generar Reporte Completo

```bash
python generar_reportes.py --formato html --output ../outputs/reports/
```

Incluye:
- Resumen ejecutivo
- Estadísticas descriptivas
- Todas las visualizaciones
- Tablas de datos
- Recomendaciones

### Formatos Disponibles

- **HTML**: Reporte interactivo auto-contenido
- **PDF**: Reporte para imprimir
- **Excel**: Tablas de datos + gráficos
- **PowerPoint**: Presentación ejecutiva

## 🎨 Notebooks Interactivos

### Análisis Exploratorio

```bash
cd 04_analysis/notebooks
jupyter notebook 01_exploratorio.ipynb
```

Permite:
- Explorar datos interactivamente
- Crear visualizaciones personalizadas
- Probar hipótesis
- Exportar resultados

## 🛠️ Uso

### Ejecutar análisis completo

```bash
cd 04_analysis/scripts
python analisis_estadistico.py
```

### Análisis temporal específico

```bash
python analisis_temporal.py --desde 2025-01-01 --hasta 2025-10-21
```

### Dashboard interactivo

```bash
python visualizaciones.py --dashboard
```

Abre en `http://localhost:8050`

## ⚙️ Configuración

Editar `config/analysis.ini`:

```ini
[analysis]
fecha_desde = 2025-01-01
fecha_hasta = 2025-12-31
top_n = 20

[visualizations]
dpi = 300
style = seaborn
color_palette = viridis
figsize_width = 12
figsize_height = 8

[reports]
format = html
include_raw_data = false
language = es
```

## 📦 Outputs Típicos

### Estructura de `outputs/`

```
outputs/
├── reports/
│   ├── reporte_completo_20251021.html
│   ├── reporte_ejecutivo_20251021.pdf
│   └── datos_completos_20251021.xlsx
├── figures/
│   ├── distribucion_isco.png
│   ├── temporal_ofertas.png
│   ├── heatmap_dia_mes.png
│   └── ...
└── dashboards/
    └── dashboard_ofertas_20251021.html
```

## ➡️ Siguiente Etapa

Los resultados finales pasan a:
- **05_products/** para publicación y distribución

---

**Última actualización**: 2025-10-21
