# Directorio de Datos - ZonaJobs Scraping

## Estructura

### data/raw/
Datos crudos scrapeados directamente de ZonaJobs.
- Formato: JSON, CSV, Excel
- Sin procesar ni limpiar
- Nombrado: `zonajobs_[tipo]_[timestamp].[ext]`

**Uso:** Estos son los datos de entrada para procesos de análisis posteriores.

### data/processed/
Datos procesados y listos para análisis.
- Datos limpios y normalizados
- Enriquecidos con clasificaciones ESCO
- Análisis semántico de ocupaciones aplicado

**Formato sugerido:**
```
ofertas_esco_[timestamp].csv        # Ofertas con clasificación ESCO
ocupaciones_normalizadas.csv        # Ocupaciones mapeadas
skills_extraidas.csv                # Skills identificadas
analisis_semantico.json             # Resultados de análisis NLP
```

### data/archive/
Históricos y backups de datos antiguos.
- Datos de scraping anteriores
- Versiones previas de datasets procesados
- Backups por fecha

---

## Integración con Análisis Posterior

### 1. Lectura de Datos Crudos

```python
import pandas as pd
from pathlib import Path

# Cargar últimos datos scrapeados
data_dir = Path("D:/OEDE/Webscrapping/data/raw")
latest_file = max(data_dir.glob("zonajobs_todas_*.csv"), key=lambda x: x.stat().st_mtime)

df = pd.read_csv(latest_file)
print(f"Cargadas {len(df)} ofertas")
```

### 2. Procesar y Guardar

```python
# Tu procesamiento aquí
df_processed = procesar_ofertas(df)

# Guardar en processed/
output_file = Path("D:/OEDE/Webscrapping/data/processed/ofertas_esco.csv")
df_processed.to_csv(output_file, index=False)
```

### 3. Campos Disponibles

Los datos scrapeados incluyen:
- `id_oferta`: ID único
- `titulo`: Título de la oferta
- `descripcion`: Descripción limpia (sin HTML)
- `descripcion_raw`: Descripción original con HTML
- `empresa`: Nombre de la empresa
- `localizacion`: Ubicación geográfica
- `modalidad_trabajo`: Presencial/Remoto/Híbrido
- `tipo_trabajo`: Full-time/Part-time/etc
- `fecha_publicacion`: Fecha de publicación
- `url_oferta`: URL completa de la oferta

Y 20+ campos adicionales. Ver `ZONAJOBS_API_DOCUMENTATION.md` para detalles.

---

## Workflow Sugerido

1. **Scraping** → `data/raw/`
2. **Limpieza** → `data/processed/`
3. **Clasificación ESCO** → `data/processed/ofertas_esco.csv`
4. **Análisis Semántico** → `data/processed/analisis_*.json`
5. **Archivo** → `data/archive/` (al final del mes)

---

Última actualización: 2025-10-16