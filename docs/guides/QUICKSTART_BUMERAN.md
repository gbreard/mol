# ⚡ QUICKSTART: Bumeran Pipeline

**Última actualización:** 30 de octubre de 2025

---

## 🎯 TL;DR - Comandos Rápidos

```bash
# Pipeline completo (scraping → dashboard)
cd D:\OEDE\Webscrapping
python run_full_pipeline.py --source bumeran

# Solo scraping multi-keyword (RECOMENDADO)
cd 01_sources\bumeran\scrapers
python scrapear_con_diccionario.py
```

---

## 📋 Tabla de Contenidos

1. [Primera Ejecución](#primera-ejecución)
2. [Ejecución Incremental](#ejecución-incremental)
3. [Comandos por Etapa](#comandos-por-etapa)
4. [Verificación de Resultados](#verificación-de-resultados)
5. [Troubleshooting](#troubleshooting)

---

## 🚀 Primera Ejecución

### Paso 1: Verificar Dependencias

```bash
# Verificar Python
python --version
# Debe ser >= 3.8

# Instalar dependencias (si es primera vez)
cd D:\OEDE\Webscrapping
pip install -r config\requirements.txt
```

### Paso 2: Configurar Keywords

```bash
# Verificar que existe el diccionario de keywords
dir data\config\master_keywords.json

# Si no existe, crearlo con:
# (Ver ejemplo en docs/FLUJO_BUMERAN.md)
```

### Paso 3: Scraping Completo (Primera Vez)

```bash
cd D:\OEDE\Webscrapping\01_sources\bumeran\scrapers

# Opción A: Scraping multi-keyword (RECOMENDADO)
python scrapear_con_diccionario.py

# Opción B: Script principal
python bumeran_scraper.py
```

**⏱️ Tiempo estimado:** 1.5-2 horas (con 55 keywords)

**📦 Output esperado:**
```
01_sources/bumeran/data/raw/bumeran_full_YYYYMMDD_HHMMSS.csv
- 2,000-3,000 ofertas
- 32 columnas
- Tamaño: 3-5 MB
```

### Paso 4: Verificar Resultado

```bash
# Contar líneas (ofertas)
python -c "import pandas as pd; df=pd.read_csv('D:/OEDE/Webscrapping/01_sources/bumeran/data/raw/bumeran_full_20251023_213057.csv'); print(f'Total ofertas: {len(df)}')"

# Ver primeras 5 filas
python -c "import pandas as pd; df=pd.read_csv('D:/OEDE/Webscrapping/01_sources/bumeran/data/raw/bumeran_full_20251023_213057.csv'); print(df.head())"
```

**✅ Esperado:** Ver tabla con títulos, empresas, descripciones

---

## 🔄 Ejecución Incremental (Actualizaciones Diarias)

### Scraping Solo Ofertas Nuevas

```bash
cd D:\OEDE\Webscrapping\01_sources\bumeran\scrapers

# Ejecutar en modo incremental (default)
python scrapear_con_diccionario.py
```

**¿Cómo funciona?**
1. Lee `data/tracking/bumeran_scraped_ids.json`
2. Filtra ofertas ya scrapeadas
3. Solo guarda ofertas nuevas
4. Actualiza tracking con nuevos IDs

**⏱️ Tiempo estimado:** 30-60 minutos (depende de ofertas nuevas)

---

## 📦 Comandos por Etapa

### ETAPA 1: Scraping

```bash
# 1.1 Scraping multi-keyword (RECOMENDADO)
cd D:\OEDE\Webscrapping\01_sources\bumeran\scrapers
python scrapear_con_diccionario.py
```

**Parámetros configurables** (editar en el script):
```python
estrategia='completa'          # 55 keywords
max_paginas_por_keyword=10     # Max 10 páginas/keyword
incremental=True               # Solo ofertas nuevas
date_window_days=7             # Últimos 7 días
```

---

### ETAPA 2: Consolidación

```bash
# 2.1 Consolidar solo Bumeran
cd D:\OEDE\Webscrapping\02_consolidation\scripts
python consolidar_fuentes.py --fuentes bumeran

# 2.2 Consolidar todas las fuentes
python consolidar_fuentes.py
```

**📦 Output:**
```
02_consolidation/data/consolidated/ofertas_consolidadas_YYYYMMDD_HHMMSS.csv
```

---

### ETAPA 3: Extracción NLP

```bash
# 3.1 Extraer NLP solo de Bumeran
cd D:\OEDE\Webscrapping\02.5_nlp_extraction\scripts
python run_nlp_extraction.py --source bumeran

# 3.2 Consolidar resultados NLP
python consolidate_nlp_sources.py
```

**📦 Output:**
```
02.5_nlp_extraction/data/processed/bumeran_nlp_YYYYMMDD_HHMMSS.csv
```

---

### ETAPA 4: Matching ESCO

```bash
# 4.1 Matching con Claude AI (subset de 300 ofertas)
cd D:\OEDE\Webscrapping\03_esco_matching\scripts
python esco_isco_llm_fallback.py --limit 300

# 4.2 Enriquecer con skills ESCO
python enriquecer_con_skills_esco.py

# 4.3 Preparar para Shiny
python 02_preparar_csv_shiny.py
```

**📦 Output:**
```
Visual--/ofertas_esco_shiny.csv
```

---

### ETAPA 5: Dashboard

```r
# 5.1 Ejecutar dashboard local
setwd("D:/OEDE/Webscrapping/Visual--")
shiny::runApp("app.R")

# 5.2 Deployment a shinyapps.io
library(rsconnect)
rsconnect::deployApp(
  appName = "dashboard-esco-argentina",
  forceUpdate = TRUE
)
```

---

## ✅ Verificación de Resultados

### Verificar Scraping

```bash
# Contar ofertas
cd D:\OEDE\Webscrapping\01_sources\bumeran\data\raw
python -c "import pandas as pd; import glob; files=glob.glob('bumeran_full_*.csv'); latest=max(files); df=pd.read_csv(latest); print(f'Archivo: {latest}'); print(f'Ofertas: {len(df)}'); print(f'Columnas: {len(df.columns)}'); print(f'Campos vacíos (descripcion): {df.descripcion.isna().sum()}')"
```

**✅ Esperado:**
```
Archivo: bumeran_full_20251023_213057.csv
Ofertas: 2460
Columnas: 32
Campos vacíos (descripcion): 0
```

---

### Verificar NLP

```bash
cd D:\OEDE\Webscrapping\02.5_nlp_extraction\data\processed
python -c "import pandas as pd; import glob; files=glob.glob('bumeran_nlp_*.csv'); latest=max(files); df=pd.read_csv(latest); print(f'Archivo: {latest}'); print(f'Ofertas: {len(df)}'); print(f'Columnas: {len(df.columns)}'); exp_coverage=(~df.experiencia_min_anios.isna()).sum()/len(df)*100; print(f'Cobertura experiencia: {exp_coverage:.1f}%')"
```

**✅ Esperado:**
```
Archivo: bumeran_nlp_20251025_140906.csv
Ofertas: 2460
Columnas: 55
Cobertura experiencia: 60.0%
```

---

### Verificar Tracking Incremental

```bash
cd D:\OEDE\Webscrapping\data\tracking
python -c "import json; with open('bumeran_scraped_ids.json', 'r') as f: data=json.load(f); print(f'IDs trackeados: {len(data[\"scraped_ids\"])}'); print(f'Última actualización: {data.get(\"last_update\", \"N/A\")}')"
```

**✅ Esperado:**
```
IDs trackeados: 100
Última actualización: 2025-10-23T10:36:00
```

---

## 🔧 Troubleshooting

### Problema: "Solo scrapeó 20 ofertas"

**Causa:** No se usaron keywords

**Solución:**
```bash
# Verificar que master_keywords.json existe
dir D:\OEDE\Webscrapping\data\config\master_keywords.json

# Usar scrapear_con_diccionario.py (usa keywords automáticamente)
cd D:\OEDE\Webscrapping\01_sources\bumeran\scrapers
python scrapear_con_diccionario.py
```

---

### Problema: "Tracking incremental no funciona"

**Causa:** Archivo `bumeran_scraped_ids.json` corrupto

**Solución:**
```bash
# Restaurar desde backup
cd D:\OEDE\Webscrapping\data\tracking
dir bumeran_scraped_ids*.bak

# Copiar último backup
copy bumeran_scraped_ids_20251023.bak bumeran_scraped_ids.json

# O resetear tracking (scraping full)
del bumeran_scraped_ids.json
```

---

### Problema: "Encoding error al leer CSV"

**Causa:** Caracteres especiales españoles

**Solución:**
```python
# Leer con encoding UTF-8
df = pd.read_csv('archivo.csv', encoding='utf-8')

# Si falla, probar con latin-1
df = pd.read_csv('archivo.csv', encoding='latin-1')
```

---

### Problema: "API retorna error 429 (Too Many Requests)"

**Causa:** Demasiadas requests muy rápido

**Solución:**
```python
# Aumentar delay en bumeran_scraper.py
scraper = BumeranScraper(delay_between_requests=3.0)  # De 2.0 a 3.0
```

---

### Problema: "No hay columnas NLP en el output"

**Causa:** Descripciones vacías o error en extractor

**Solución:**
```bash
# Verificar descripciones no vacías
python -c "import pandas as pd; df=pd.read_csv('bumeran_full_*.csv'); print(f'Descripciones vacías: {df.descripcion.isna().sum()}')"

# Si hay descripciones, verificar logs de run_nlp_extraction.py
python run_nlp_extraction.py --source bumeran --verbose
```

---

## 📊 Checklist de Ejecución Exitosa

### ✅ Scraping

- [ ] Archivo generado en `01_sources/bumeran/data/raw/`
- [ ] Mínimo 2,000 ofertas (si es primera vez con 55 keywords)
- [ ] 32 columnas presentes
- [ ] Campo `descripcion` 100% completo
- [ ] Tracking actualizado en `data/tracking/bumeran_scraped_ids.json`

### ✅ Consolidación

- [ ] Archivo generado en `02_consolidation/data/consolidated/`
- [ ] Ofertas de Bumeran incluidas (columna `_metadata.source = "bumeran"`)
- [ ] Schema unificado aplicado (50+ columnas)

### ✅ NLP

- [ ] Archivo generado en `02.5_nlp_extraction/data/processed/`
- [ ] 55 columnas (32 originales + 23 NLP)
- [ ] Cobertura experiencia ~60%
- [ ] Cobertura skills técnicas ~70%

### ✅ ESCO

- [ ] Archivo `ofertas_esco_shiny.csv` generado
- [ ] 268 ofertas (subset clasificado)
- [ ] 48 columnas
- [ ] 100% con ESCO/ISCO + skills + URLs

### ✅ Dashboard

- [ ] Dashboard corre localmente en http://localhost:XXXX
- [ ] Login funciona
- [ ] 5 pestañas se muestran correctamente
- [ ] Datos de Bumeran visibles en tablas/gráficos

---

## 🎓 Ejemplos de Uso

### Ejemplo 1: Scraping Testing (Solo 3 Keywords)

```bash
cd D:\OEDE\Webscrapping\01_sources\bumeran\scrapers
python -c "
from scrapear_con_diccionario import BumeranMultiSearch
scraper = BumeranMultiSearch()
df = scraper.scrapear_multiples_keywords(
    estrategia='minima',  # Solo 4 keywords
    max_paginas_por_keyword=2,
    incremental=False
)
scraper.guardar_resultados(df, prefix='bumeran_test')
"
```

**⏱️ Tiempo:** 5-10 minutos

---

### Ejemplo 2: Pipeline Completo

```bash
# Ejecutar todo el pipeline
cd D:\OEDE\Webscrapping
python run_full_pipeline.py --source bumeran --verbose
```

**⏱️ Tiempo:** 3-4 horas

---

### Ejemplo 3: Solo Actualizar Dashboard

```bash
# Si ya tienes ofertas_esco_shiny.csv actualizado
cd D:\OEDE\Webscrapping\Visual--
Rscript -e "shiny::runApp('app.R')"
```

---

## 📞 Ayuda

**Documentación completa:** `docs/FLUJO_BUMERAN.md`

**Logs:** `D:\OEDE\Webscrapping\logs\pipeline_*.log`

**Reportar problemas:** Crear issue en repositorio

---

**FIN QUICKSTART**
