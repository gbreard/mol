# Bumeran Scraper

## 🎯 Descripción

Scraper completo para Bumeran.com.ar que extrae ofertas laborales usando la API interna del sitio.

## 📊 Datos Clave

- **Ofertas disponibles**: ~12,000
- **Metodología**: API REST directa
- **Campos extraídos**: 32 por oferta
- **Formato**: CSV, JSON, Excel

---

## 📁 Estructura

```
bumeran/
├── scrapers/
│   ├── bumeran_scraper.py            # Scraper principal ✅
│   ├── bumeran_explorer.py           # Explorador técnico
│   └── test_bumeran_api.py           # Tests de API
├── data/
│   └── raw/                          # Datos scrapeados
├── config/
│   └── scraping.ini                  # Configuración
└── README.md                         # Este archivo
```

---

## 🚀 Uso Rápido

### Instalación

```bash
cd 01_sources/bumeran
pip install requests pandas openpyxl
```

### Ejecutar Scraper

```bash
cd scrapers
python bumeran_scraper.py
```

Esto scrapeará:
- 100 ofertas generales
- 40 ofertas de "python"
- Guardará en CSV, JSON y Excel

---

## 💻 Uso Programático

### Ejemplo Básico

```python
from bumeran_scraper import BumeranScraper

# Crear scraper
scraper = BumeranScraper(delay_between_requests=2.0)

# Scrapear primeras 200 ofertas
ofertas = scraper.scrapear_todo(max_paginas=10, max_resultados=200)

# Guardar en todos los formatos
files = scraper.save_all_formats(ofertas)
```

### Búsqueda Específica

```python
# Buscar ofertas de Python
ofertas_python = scraper.scrapear_todo(
    max_paginas=5,
    max_resultados=100,
    query="python"
)

scraper.save_to_csv(ofertas_python, "bumeran_python.csv")
```

### Filtrado Local

```python
# Scrapear todas y filtrar después
todas = scraper.scrapear_todo(max_paginas=20)

# Filtrar por keyword
data_jobs = scraper.filtrar_local(todas, "data")
developer_jobs = scraper.filtrar_local(todas, "developer")
```

---

## 🔧 API Descubierta

### Endpoint

```
POST https://www.bumeran.com.ar/api/avisos/searchV2
```

### Headers Necesarios

```python
headers = {
    'User-Agent': 'Mozilla/5.0...',
    'Accept': 'application/json',
    'Content-Type': 'application/json',
    'x-site-id': 'BMAR',  # Bumeran Argentina
    'x-pre-session-token': '{UUID}'  # Generar con uuid.uuid4()
}
```

### Payload

```json
{
  "pageSize": 20,       // Ofertas por página (máx: probablemente 100)
  "page": 0,           // Página (0-indexed)
  "sort": "RELEVANTES", // RELEVANTES, FECHA, etc.
  "query": "python"    // Opcional: búsqueda por keyword
}
```

### Respuesta

```json
{
  "total": 12066,      // Total de ofertas disponibles
  "number": 0,         // Número de página actual
  "size": 20,          // Tamaño de página
  "content": [...]     // Array de ofertas
}
```

---

## 📊 Campos Disponibles

### Identificación
- `id`: ID único de la oferta
- `id_empresa`: ID de la empresa

### Información Básica
- `titulo`: Título de la oferta
- `empresa`: Nombre de la empresa
- `detalle`: Descripción HTML completa
- `confidencial`: Si la empresa es confidencial

### Ubicación y Modalidad
- `localizacion`: "Ciudad, Provincia"
- `modalidad_trabajo`: Presencial/Remoto/Híbrido
- `tipo_trabajo`: Full-time/Part-time/etc.

### Fechas
- `fecha_publicacion`: DD-MM-YYYY
- `fecha_hora_publicacion`: DD-MM-YYYY HH:MM:SS
- `fecha_modificado`: DD-MM-YYYY HH:MM:SS

### Detalles
- `cantidad_vacantes`: Número de vacantes
- `apto_discapacitado`: Boolean

### Empresa
- `logo_url`: URL del logo
- `empresa_validada`: Boolean
- `empresa_pro`: Boolean
- `promedio_empresa`: Rating

### Categorización
- `id_area`: Área de trabajo
- `id_subarea`: Subárea
- `id_pais`: País (1 = Argentina)

### Plan
- `plan_publicacion.id`: ID del plan
- `plan_publicacion.nombre`: Nombre del plan

### Otros
- `portal`: "bumeran"
- `tipo_aviso`: "simple", "talento", etc.
- `tiene_preguntas`: Boolean
- `salario_obligatorio`: Boolean

**Total**: 32+ campos

---

## ⚙️ Configuración

### Parámetros del Scraper

```python
scraper = BumeranScraper(
    delay_between_requests=2.0  # Segundos entre requests
)

scraper.scrapear_todo(
    max_paginas=10,        # Máximo de páginas
    max_resultados=200,    # Máximo de ofertas
    page_size=20,          # Ofertas por página
    query=None             # Keyword de búsqueda
)
```

### Rate Limiting

Por defecto: **2 segundos** entre requests.

Recomendación: No bajar de 1 segundo para evitar bloqueos.

---

## 📈 Performance

- **Velocidad**: ~20 ofertas/minuto (con delay 2s)
- **Recursos**: CPU < 5%, RAM ~50 MB
- **Almacenamiento**: ~3-4 KB por oferta

---

## 🔄 Integración con Pipeline

### Consolidación

Las ofertas de Bumeran se normalizan automáticamente al schema unificado:

```bash
cd ../../02_consolidation/scripts
python consolidar_fuentes.py --fuentes bumeran
```

Mapeo de campos:
- `id_oferta` → `_metadata.source_id`
- `titulo` → `informacion_basica.titulo`
- `localizacion` → `ubicacion.ubicacion_raw` (parseado a provincia/ciudad)
- `modalidad_trabajo` → `modalidad.modalidad_trabajo` (normalizado)
- etc.

### Pipeline Completo

```bash
cd ../..
python pipeline_completo.py --all --fuentes bumeran
```

Ejecuta:
1. Scraping (este scraper)
2. Normalización
3. ESCO Matching
4. Análisis
5. Productos finales

---

## 🧪 Tests

### Test de API

```bash
python test_bumeran_api.py
```

Prueba:
- ✅ Conexión con API
- ✅ Headers correctos
- ✅ Búsqueda sin filtros
- ✅ Búsqueda con keyword
- ✅ Paginación

### Test del Scraper

```bash
python bumeran_scraper.py
```

Scrapea ofertas de ejemplo y guarda en todos los formatos.

---

## ⚖️ Consideraciones Legales

### ✅ Antes de Usar

1. Lee los [Términos de Servicio](https://www.bumeran.com.ar/terminos-y-condiciones)
2. Verifica [robots.txt](https://www.bumeran.com.ar/robots.txt)
3. Implementa rate limiting (mínimo 2 segundos)
4. Usa User-Agent identificable
5. Solo para investigación/análisis personal

### Límites Recomendados

- **Delay mínimo**: 2 segundos
- **Ofertas por sesión**: Hasta 1,000
- **Frecuencia**: No más de 1 vez por hora

---

## 🐛 Troubleshooting

### Error 400: "No se incluyo el header x-site-id"

**Solución**: El scraper ya incluye este header automáticamente. Si usas requests directamente, asegúrate de incluir:
```python
headers['x-site-id'] = 'BMAR'
headers['x-pre-session-token'] = str(uuid.uuid4())
```

### No se obtienen ofertas

**Problema**: El payload podría estar mal formado.

**Solución**: Verifica que el JSON tenga `pageSize`, `page` y `sort`.

### Ofertas con descripción HTML

**Solución**: La descripción viene en HTML. Usa `_limpiar_html()` o procesa en normalización.

---

## 📝 Ejemplos de Uso

### Caso 1: Análisis del Mercado IT

```python
scraper = BumeranScraper()

# Keywords relevantes
keywords = ["python", "javascript", "data", "devops"]

resultados = {}
for keyword in keywords:
    ofertas = scraper.scrapear_todo(max_paginas=5, query=keyword)
    resultados[keyword] = len(ofertas)
    scraper.save_to_csv(ofertas, f"bumeran_{keyword}.csv")

print(resultados)
# {'python': 21, 'javascript': 45, 'data': 88, 'devops': 12}
```

### Caso 2: Ofertas Remotas

```python
todas = scraper.scrapear_todo(max_paginas=50, max_resultados=1000)

remotas = [
    o for o in todas
    if o.get('modalidadTrabajo') == 'Remoto'
]

print(f"Ofertas remotas: {len(remotas)}/{len(todas)}")
scraper.save_to_excel(remotas, "bumeran_remotas.xlsx")
```

### Caso 3: Por Provincia

```python
import pandas as pd

todas = scraper.scrapear_todo(max_paginas=100)
df = scraper.procesar_ofertas(todas)

# Agrupar por provincia
por_provincia = df.groupby('localizacion').size().sort_values(ascending=False)

print(por_provincia.head(10))
```

---

## 📚 Documentación Adicional

- [API Bumeran (descubierta)](../../docs/BUMERAN_API_DOCUMENTATION.md) *(pendiente)*
- [Schema Unificado](../../shared/schemas/SCHEMA_DOCUMENTATION.md)
- [Pipeline Completo](../../docs/arquitectura.md)

---

## 🔗 Enlaces Útiles

- [Bumeran Argentina](https://www.bumeran.com.ar)
- [Términos de Servicio](https://www.bumeran.com.ar/terminos-y-condiciones)
- [robots.txt](https://www.bumeran.com.ar/robots.txt)

---

## 📊 Estadísticas

### Datos de Implementación (2025-10-21)

- **Ofertas disponibles**: ~12,000
- **Ofertas scrapeadas (prueba)**: 140
- **Campos por oferta**: 32
- **Formatos de exportación**: CSV, JSON, Excel
- **Tiempo de implementación**: 3 horas

### Comparativa vs ZonaJobs

| Métrica | Bumeran | ZonaJobs |
|---|---|---|
| Ofertas | ~12,000 | ~3,000 |
| Metodología | API REST | API REST |
| Complejidad | Media | Media |
| Campos | 32 | 33 |

---

**Scraper implementado**: 2025-10-21
**Versión**: 1.0
**Estado**: ✅ Funcional
**Mantenedor**: OEDE
