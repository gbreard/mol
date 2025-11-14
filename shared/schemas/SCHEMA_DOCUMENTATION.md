# Documentación del Schema Unificado

**Versión**: 1.0.0
**Fecha**: 2025-10-21

## 🎯 Objetivo

Este schema define la estructura común para ofertas laborales de **todas las fuentes** de scraping (ZonaJobs, Bumeran, ComputRabajo, LinkedIn, etc.).

## 📋 Principios del Diseño

### 1. **Campos Obligatorios Mínimos**
Toda oferta debe tener al menos:
- `source`: Fuente de la oferta
- `source_id`: ID único en la fuente
- `titulo`: Título de la oferta
- `empresa`: Nombre de la empresa
- `url_oferta`: URL de la oferta
- `fecha_extraccion`: Timestamp de extracción

### 2. **Campos Normalizados + RAW**
Para campos que requieren normalización (fechas, modalidad, tipo de trabajo), guardamos:
- **Campo normalizado**: Valor estandarizado (ej: `modalidad_trabajo: "remoto"`)
- **Campo raw**: Valor original (ej: `modalidad_raw: "100% Home Office"`)

### 3. **Flexibilidad por Fuente**
- `source_specific`: Objeto para campos únicos de cada fuente
- No todos los campos son obligatorios (excepto los básicos)

### 4. **Separación de Etapas**
- **Scraping** (`01_sources`): Extrae datos de cada fuente
- **Consolidación** (`02_consolidation`): Normaliza a este schema
- **ESCO Matching** (`03_esco_matching`): Añade `clasificacion_esco`
- **Análisis** (`04_analysis`): Consume datos ya estructurados

## 📊 Estructura de Secciones

### `_metadata`
Información sobre el origen y extracción de los datos.

```json
{
  "_metadata": {
    "source": "zonajobs",
    "source_id": "12345",
    "unified_id": "zonajobs_12345",
    "url_oferta": "https://www.zonajobs.com.ar/...",
    "fecha_extraccion": "2025-10-21T10:30:00Z",
    "version_scraper": "3.0"
  }
}
```

### `informacion_basica`
Título, empresa, descripción.

```json
{
  "informacion_basica": {
    "titulo": "Desarrollador Python Senior",
    "titulo_normalizado": "desarrollador python senior",
    "empresa": "Tech Corp",
    "empresa_id": "789",
    "descripcion": "Buscamos...",
    "descripcion_limpia": "Buscamos desarrollador..."
  }
}
```

### `ubicacion`
Localización del puesto.

```json
{
  "ubicacion": {
    "pais": "Argentina",
    "provincia": "Buenos Aires",
    "ciudad": "CABA",
    "ubicacion_raw": "Capital Federal, Buenos Aires",
    "codigo_postal": null
  }
}
```

### `modalidad`
Tipo de trabajo y modalidad.

```json
{
  "modalidad": {
    "tipo_trabajo": "full_time",
    "modalidad_trabajo": "remoto",
    "tipo_trabajo_raw": "Tiempo completo",
    "modalidad_raw": "Remoto"
  }
}
```

### `fechas`
Fechas relevantes de la oferta.

```json
{
  "fechas": {
    "fecha_publicacion": "2025-10-15T00:00:00Z",
    "fecha_modificacion": "2025-10-20T12:00:00Z",
    "fecha_cierre": null,
    "fecha_publicacion_raw": "Publicado hace 6 días"
  }
}
```

### `requisitos`
Requisitos del puesto.

```json
{
  "requisitos": {
    "experiencia_minima": "3-5 años",
    "nivel_educativo": "Universitario",
    "idiomas": ["Español", "Inglés"],
    "habilidades": ["Python", "Django", "PostgreSQL"],
    "certificaciones": []
  }
}
```

### `compensacion`
Información salarial.

```json
{
  "compensacion": {
    "salario_minimo": 500000,
    "salario_maximo": 800000,
    "moneda": "ARS",
    "periodo": "mes",
    "salario_raw": "$500.000 - $800.000",
    "beneficios": ["Prepaga", "Home office"]
  }
}
```

### `detalles`
Detalles adicionales.

```json
{
  "detalles": {
    "cantidad_vacantes": 2,
    "area_trabajo": "Tecnología",
    "nivel_puesto": "Senior",
    "apto_discapacitado": true,
    "confidencial": false
  }
}
```

### `clasificacion_esco`
**Añadido en etapa `03_esco_matching`**.

```json
{
  "clasificacion_esco": {
    "ocupacion_esco_code": "http://data.europa.eu/esco/occupation/...",
    "ocupacion_esco_label": "Software Developer",
    "isco_code": "2512",
    "isco_label": "Software developers",
    "similarity_score": 0.87,
    "skills": [
      {
        "skill_uri": "http://data.europa.eu/esco/skill/...",
        "skill_label": "Python",
        "skill_type": "essential"
      }
    ],
    "matching_method": "semantic_tfidf",
    "matching_timestamp": "2025-10-21T11:00:00Z"
  }
}
```

### `source_specific`
Campos únicos de cada fuente.

```json
{
  "source_specific": {
    "zonajobs_views": 123,
    "zonajobs_aplicaciones": 45,
    "bumeran_destacada": true,
    "linkedin_easy_apply": false
  }
}
```

## 🔄 Mapeo por Fuente

### ZonaJobs → Schema Unificado

| Campo ZonaJobs | Campo Unificado | Notas |
|---|---|---|
| `id_oferta` | `_metadata.source_id` | |
| `titulo` | `informacion_basica.titulo` | |
| `empresa` | `informacion_basica.empresa` | |
| `id_empresa` | `informacion_basica.empresa_id` | |
| `localizacion` | `ubicacion.ubicacion_raw` | Parsear a provincia/ciudad |
| `modalidad_trabajo` | `modalidad.modalidad_trabajo` | Normalizar |
| `tipo_trabajo` | `modalidad.tipo_trabajo` | Normalizar |
| `fecha_publicacion` | `fechas.fecha_publicacion` | Convertir a ISO |
| `descripcion` | `informacion_basica.descripcion` | |
| `url_oferta` | `_metadata.url_oferta` | |
| `scrapeado_en` | `_metadata.fecha_extraccion` | |

### Bumeran → Schema Unificado (ejemplo)

| Campo Bumeran | Campo Unificado | Notas |
|---|---|---|
| `aviso_id` | `_metadata.source_id` | |
| `puesto` | `informacion_basica.titulo` | |
| `empresa_nombre` | `informacion_basica.empresa` | |
| `zona` | `ubicacion.ubicacion_raw` | Parsear |
| `jornada` | `modalidad.tipo_trabajo_raw` | Normalizar |
| ... | ... | ... |

### ComputRabajo → Schema Unificado (ejemplo)

| Campo ComputRabajo | Campo Unificado | Notas |
|---|---|---|
| `oferta_id` | `_metadata.source_id` | |
| `cargo` | `informacion_basica.titulo` | |
| ... | ... | ... |

## 🛠️ Uso en el Pipeline

### Etapa 1: Scraping (`01_sources/`)
Cada scraper extrae datos en su formato original.

```python
# zonajobs/scrapers/zonajobs_scraper_final.py
# Output: data/raw/zonajobs_YYYYMMDD.csv
```

### Etapa 2: Consolidación (`02_consolidation/`)
Script de normalización convierte a schema unificado.

```python
# scripts/consolidar_fuentes.py
from normalizar_campos import ZonaJobsNormalizer

normalizer = ZonaJobsNormalizer()
df_unificado = normalizer.normalize(df_raw)

# Output: data/consolidated/ofertas_unificadas_YYYYMMDD.csv
```

### Etapa 3: ESCO Matching (`03_esco_matching/`)
Añade clasificación ESCO al schema.

```python
# scripts/integracion_esco_semantica.py
# Lee: data/consolidated/ofertas_unificadas_YYYYMMDD.csv
# Añade: clasificacion_esco
# Output: data/matched/ofertas_esco_YYYYMMDD.csv
```

### Etapa 4: Análisis (`04_analysis/`)
Análisis sobre datos completamente estructurados.

```python
# scripts/analisis_estadistico.py
# Lee: data/matched/ofertas_esco_YYYYMMDD.csv
# Output: reports/, figures/
```

## ✅ Validación del Schema

### Ejemplo de validación con `jsonschema`

```python
import json
import jsonschema

# Cargar schema
with open('shared/schemas/schema_unificado.json') as f:
    schema = json.load(f)

# Validar oferta
with open('data/consolidated/oferta_ejemplo.json') as f:
    oferta = json.load(f)

try:
    jsonschema.validate(instance=oferta, schema=schema)
    print("✅ Oferta válida")
except jsonschema.ValidationError as e:
    print(f"❌ Error de validación: {e.message}")
```

## 📝 Campos Recomendados por Análisis

Para análisis estadístico robusto, se recomienda completar:

### Esenciales
- ✅ `titulo`
- ✅ `empresa`
- ✅ `ubicacion.provincia`
- ✅ `modalidad.tipo_trabajo`
- ✅ `modalidad.modalidad_trabajo`
- ✅ `fechas.fecha_publicacion`

### Deseables
- ⭐ `compensacion.salario_minimo`
- ⭐ `compensacion.salario_maximo`
- ⭐ `requisitos.experiencia_minima`
- ⭐ `requisitos.habilidades`
- ⭐ `detalles.area_trabajo`

### ESCO (añadidos automáticamente)
- 🎯 `clasificacion_esco.isco_code`
- 🎯 `clasificacion_esco.ocupacion_esco_label`
- 🎯 `clasificacion_esco.skills`

## 🔄 Evolución del Schema

### Versión 1.0.0 (2025-10-21)
- Schema inicial
- Soporta ZonaJobs completo
- Preparado para Bumeran, ComputRabajo, LinkedIn

### Futuras Versiones
- `v1.1`: Añadir campos de competencias transversales
- `v1.2`: Añadir geolocalización (lat/lon)
- `v2.0`: Soporte para ofertas internacionales

## 📚 Referencias

- [JSON Schema](https://json-schema.org/)
- [ESCO Ontology](https://ec.europa.eu/esco)
- [ISCO-08 Classification](https://www.ilo.org/public/english/bureau/stat/isco/isco08/)

---

**Mantenedor**: OEDE
**Última actualización**: 2025-10-21
