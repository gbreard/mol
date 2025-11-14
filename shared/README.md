# shared - Recursos Compartidos

## 🎯 Propósito

Este directorio contiene código, configuraciones y recursos utilizados por múltiples etapas del pipeline.

## 📁 Estructura

```
shared/
├── utils/              # Utilidades reutilizables
├── schemas/            # Schemas y validaciones
├── config/             # Configuración global
└── logs/              # Logs centralizados
```

## 🛠️ Utils

### Módulos Disponibles

#### `text_processing.py`
Procesamiento de texto común:

```python
from shared.utils.text_processing import (
    limpiar_html,
    normalizar_texto,
    extraer_keywords,
    detectar_idioma
)

texto_limpio = limpiar_html(html_content)
texto_norm = normalizar_texto(texto, lowercase=True, remove_accents=False)
```

#### `date_utils.py`
Manejo de fechas:

```python
from shared.utils.date_utils import (
    parsear_fecha_flexible,
    convertir_a_iso,
    calcular_antiguedad
)

fecha = parsear_fecha_flexible("Publicado hace 3 días")
iso_date = convertir_a_iso(fecha)
```

#### `db_connector.py`
Conexiones a bases de datos (si se usa):

```python
from shared.utils.db_connector import DatabaseConnector

db = DatabaseConnector('postgresql://...')
df = db.query_to_dataframe("SELECT * FROM ofertas")
```

#### `validacion_utils.py`
Validaciones comunes:

```python
from shared.utils.validacion_utils import (
    validar_url,
    validar_email,
    validar_schema
)

if validar_url(url):
    # URL válida
```

#### `logging_utils.py`
Configuración de logging:

```python
from shared.utils.logging_utils import setup_logger

logger = setup_logger('mi_modulo', log_file='shared/logs/mi_modulo.log')
logger.info("Mensaje de log")
```

## 📋 Schemas

### `schemas/`

Contiene:
- `schema_unificado.json`: Schema principal
- `SCHEMA_DOCUMENTATION.md`: Documentación del schema
- Validadores de schema

## ⚙️ Config

### Configuración Global

`config/config_global.ini`:

```ini
[paths]
project_root = D:/OEDE/Webscrapping
data_root = ${project_root}/data
esco_root = D:/OEDE/ESCO

[database]
enabled = false
connection_string =

[logging]
level = INFO
format = %%(asctime)s - %%(name)s - %%(levelname)s - %%(message)s
centralized_log = ${project_root}/shared/logs/pipeline.log

[pipeline]
run_consolidation = true
run_esco_matching = true
run_analysis = true
```

### Uso en Scripts

```python
from shared.utils.config_loader import load_config

config = load_config('shared/config/config_global.ini')
project_root = config.get('paths', 'project_root')
```

## 📝 Logs

### Estructura de `logs/`

```
logs/
├── pipeline.log              # Log general del pipeline
├── consolidacion.log         # Logs de consolidación
├── esco_matching.log         # Logs de matching ESCO
└── analysis.log              # Logs de análisis
```

### Niveles de Log

- **DEBUG**: Información detallada para debugging
- **INFO**: Confirmación de que las cosas funcionan
- **WARNING**: Algo inesperado pero el programa continúa
- **ERROR**: Error que impide una función específica
- **CRITICAL**: Error crítico que detiene el programa

## 🔧 Utilidades Comunes

### Cargar Configuración

```python
from shared.utils.config_loader import ConfigLoader

config = ConfigLoader()
threshold = config.get_float('esco', 'similarity_threshold')
```

### Logging Centralizado

```python
from shared.utils.logging_utils import get_logger

logger = get_logger(__name__)
logger.info("Procesando ofertas...")
```

### Validar Datos

```python
from shared.utils.validacion_utils import ValidadorSchema

validador = ValidadorSchema('shared/schemas/schema_unificado.json')
if validador.validar(oferta):
    print("✅ Oferta válida")
```

### Normalizar Texto

```python
from shared.utils.text_processing import TextNormalizer

normalizer = TextNormalizer()
texto_limpio = normalizer.normalizar(texto_raw)
```

## 📦 Instalación de Dependencias

Las utilidades compartidas pueden tener dependencias específicas:

```bash
pip install -r shared/requirements.txt
```

## 🧪 Tests

Los tests de las utilidades compartidas están en:

```
tests/unit/shared/
├── test_text_processing.py
├── test_date_utils.py
└── test_validacion_utils.py
```

## 🔄 Versionado

Mantener compatibilidad hacia atrás en utilidades compartidas.
Cambios breaking deben incrementar versión major.

---

**Última actualización**: 2025-10-21
