# 02_consolidation - Consolidación y Normalización

## 🎯 Propósito

Este módulo consolida datos de múltiples fuentes (ZonaJobs, Bumeran, etc.) en un formato unificado según el [Schema Unificado](../shared/schemas/SCHEMA_DOCUMENTATION.md).

## 📁 Estructura

```
02_consolidation/
├── scripts/
│   ├── consolidar_fuentes.py      # Script principal
│   ├── normalizar_campos.py       # Normalizadores por fuente
│   ├── deduplicacion.py          # Detección de duplicados
│   └── validacion.py             # Validación de schema
├── data/
│   ├── consolidated/             # Datos unificados
│   └── logs/                     # Logs de consolidación
├── config/
│   └── consolidation.ini         # Configuración
└── README.md
```

## 🔄 Proceso

### 1. Carga de Datos Crudos

Lee los datos de todas las fuentes desde `01_sources/*/data/raw/`

### 2. Normalización

Cada fuente tiene su normalizador que convierte campos crudos al schema unificado:

```python
from normalizar_campos import ZonaJobsNormalizer, BumeranNormalizer

# ZonaJobs
zj_normalizer = ZonaJobsNormalizer()
df_zonajobs_norm = zj_normalizer.normalize(df_zonajobs_raw)

# Bumeran
bm_normalizer = BumeranNormalizer()
df_bumeran_norm = bm_normalizer.normalize(df_bumeran_raw)
```

### 3. Consolidación

Une todas las fuentes en un DataFrame único:

```python
from consolidar_fuentes import ConsolidadorMultiFuente

consolidador = ConsolidadorMultiFuente()
df_unificado = consolidador.consolidar_todas()
```

### 4. Deduplicación

Identifica ofertas duplicadas entre fuentes:

```python
from deduplicacion import DeduplicadorOfertas

deduplicador = DeduplicadorOfertas()
df_sin_duplicados = deduplicador.deduplicar(df_unificado)
```

### 5. Validación

Valida que los datos cumplan el schema:

```python
from validacion import validar_schema

validar_schema(df_sin_duplicados, strict=True)
```

## 📊 Salida

Archivo consolidado en `data/consolidated/`:

```
ofertas_consolidadas_20251021_143000.csv
ofertas_consolidadas_20251021_143000.json
```

## 🛠️ Uso

### Consolidar todas las fuentes

```bash
cd 02_consolidation/scripts
python consolidar_fuentes.py
```

### Con opciones

```bash
python consolidar_fuentes.py --fecha-desde 2025-10-01 --deduplicar --validar
```

## 🔍 Mapeo de Campos

Ver documentación completa en [SCHEMA_DOCUMENTATION.md](../shared/schemas/SCHEMA_DOCUMENTATION.md#mapeo-por-fuente)

### Ejemplo: ZonaJobs

| Campo Original | Campo Unificado |
|---|---|
| `id_oferta` | `_metadata.source_id` |
| `titulo` | `informacion_basica.titulo` |
| `modalidad_trabajo` | `modalidad.modalidad_trabajo` |

## ✅ Validaciones

El módulo verifica:
- ✅ Campos obligatorios presentes
- ✅ Tipos de datos correctos
- ✅ Fechas en formato ISO 8601
- ✅ Valores enumerados válidos
- ✅ No hay IDs duplicados dentro de la misma fuente

## ➡️ Siguiente Etapa

Los datos consolidados pasan a:
- **03_esco_matching/** para clasificación con ESCO

---

**Última actualización**: 2025-10-21
