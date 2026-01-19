# ZonaJobs Scraper

## 🎯 Descripción

Scraper completo para ZonaJobs.com.ar que extrae ofertas laborales usando la API interna del sitio.

## 📁 Estructura

```
zonajobs/
├── scrapers/
│   ├── zonajobs_scraper_final.py     # Scraper principal
│   ├── zonajobs_api_discovery.py     # Descubrimiento de API
│   ├── test_api_simple.py            # Test rápido
│   ├── playwright_intercept.py       # Interceptor Playwright
│   ├── intercept_api_calls.py        # Interceptor de llamadas
│   └── check_scraping_rules.py       # Verifica robots.txt
├── data/
│   ├── raw/                          # Datos extraídos
│   └── logs/                         # Logs de scraping
├── config/
│   ├── scraping.ini                  # Configuración
│   └── requirements.txt              # Dependencias
└── README.md                         # Este archivo
```

## 🚀 Uso Rápido

### Instalación

```bash
cd 01_sources/zonajobs
pip install -r config/requirements.txt
python -m playwright install chromium  # Opcional, para interceptor
```

### Ejecutar Scraper

```bash
cd scrapers
python zonajobs_scraper_final.py
```

### Con Parámetros

```bash
python zonajobs_scraper_final.py \
  --max-paginas 10 \
  --max-resultados 500 \
  --delay 2.0 \
  --output ../data/raw/
```

## ⚙️ Configuración

Editar `config/scraping.ini`:

```ini
[scraping]
delay_between_requests = 2.0
max_pages = 10
max_results = 500

[data]
output_dir = ../data/raw
export_formats = all  # json, csv, excel, all
```

## 📊 Datos Extraídos

### Campos (33 campos totales)

#### Identificación
- `id_oferta`: ID único de la oferta
- `id_empresa`: ID de la empresa

#### Información Básica
- `titulo`: Título de la oferta
- `empresa`: Nombre de la empresa
- `descripcion`: Descripción completa

#### Ubicación y Modalidad
- `localizacion`: Ubicación del trabajo
- `modalidad_trabajo`: Presencial/Remoto/Híbrido
- `tipo_trabajo`: Full-time/Part-time/etc.

#### Fechas
- `fecha_publicacion`: Fecha de publicación
- `fecha_modificacion`: Última modificación

#### Otros
- `cantidad_vacantes`: Número de vacantes
- `apto_discapacitado`: Si es apto para personas con discapacidad
- `url_oferta`: URL de la oferta
- `scrapeado_en`: Timestamp de extracción

Ver documentación completa en [ZONAJOBS_API_DOCUMENTATION.md](../../docs/ZONAJOBS_API_DOCUMENTATION.md)

## 📈 Salida

Los datos se guardan en `data/raw/`:

```
zonajobs_raw_20251021_143000.csv
zonajobs_raw_20251021_143000.json
zonajobs_raw_20251021_143000.xlsx
```

## 🔧 Scripts Disponibles

### `zonajobs_scraper_final.py`
Scraper principal funcional.

```bash
python zonajobs_scraper_final.py
```

### `zonajobs_api_discovery.py`
Descubrimiento de la API de ZonaJobs.

```bash
python zonajobs_api_discovery.py
```

### `test_api_simple.py`
Test rápido de la API.

```bash
python test_api_simple.py
```

### `check_scraping_rules.py`
Verifica robots.txt y políticas.

```bash
python check_scraping_rules.py
```

## ⚖️ Consideraciones Legales

### ✅ Antes de Usar

1. Lee los [Términos de Servicio](https://www.zonajobs.com.ar/terminos-y-condiciones)
2. Verifica [robots.txt](https://www.zonajobs.com.ar/robots.txt)
3. Implementa rate limiting (mínimo 2 segundos)
4. Usa User-Agent identificable
5. Solo para investigación/análisis personal

### Rate Limiting

El scraper implementa delay automático:
- **Mínimo recomendado**: 2 segundos entre requests
- **Por defecto**: 2 segundos
- **Configurable** en `scraping.ini`

## 🐛 Troubleshooting

### Error 500 en API

**Problema**: La API devuelve error 500 con ciertos filtros.

**Solución**: Scrapear sin filtros y filtrar localmente.

```python
from zonajobs_scraper_final import ZonaJobsScraperFinal

scraper = ZonaJobsScraperFinal()
ofertas = scraper.scrapear_todo(max_paginas=5)
python_jobs = scraper.filtrar_local(ofertas, "python")
```

### No se obtienen cookies

**Problema**: El scraper no puede obtener cookies.

**Solución**: El scraper ya visita la página principal automáticamente para obtener cookies.

### Ofertas duplicadas

**Problema**: Algunas ofertas aparecen duplicadas.

**Solución**: Filtrar por `id_oferta` único.

```python
import pandas as pd
df = pd.read_csv('data/raw/zonajobs_raw_20251021.csv')
df = df.drop_duplicates(subset=['id_oferta'])
```

## 📊 Performance

- **Velocidad**: ~22 ofertas cada 44 segundos (con delay de 2s)
- **Recursos**: CPU < 5%, RAM ~50-100 MB
- **Almacenamiento**: ~2-5 KB por oferta

## ➡️ Siguiente Etapa

Los datos pasan a:
- **02_consolidation/** para normalización al schema unificado

## 🔗 Referencias

- [Documentación API ZonaJobs](../../docs/ZONAJOBS_API_DOCUMENTATION.md)
- [Schema Unificado](../../shared/schemas/SCHEMA_DOCUMENTATION.md)
- [Guía de Uso](../../docs/EJEMPLOS_USO.md)

## 📝 Changelog

### v3.0 (2025-10-21)
- Migración a nueva estructura modular
- Scraper independiente por fuente

### v2.0 (2025-10-16)
- Scraper funcional probado con 61 ofertas
- 33 campos por oferta
- Exportación a CSV, JSON, Excel

---

**Última actualización**: 2025-10-21
**Fuente**: ZonaJobs.com.ar
**Mantenedor**: OEDE
