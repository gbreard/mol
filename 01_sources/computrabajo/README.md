# ComputRabajo Scraper

## 🎯 Descripción

Scraper completo para ar.computrabajo.com que extrae ofertas laborales usando HTML scraping (requests + BeautifulSoup).

## 📊 Datos Clave

- **Ofertas disponibles**: ~500-1,000+ por keyword
- **Metodología**: HTML Scraping (requests + BeautifulSoup)
- **Campos extraídos**: 13 por oferta
- **Formato**: CSV, JSON, Excel

---

## ⚠️ IMPORTANTE: Requiere Diccionario de Búsqueda

**ComputRabajo NO devuelve ofertas en la home page sin búsqueda específica.**

Para scrapear, debes usar:
1. **Script simple** (`computrabajo_scraper.py`) - 1 keyword manual
2. **Script multi-keyword** (`scrapear_con_diccionario.py`) - Múltiples keywords automático ✅ Recomendado

---

## 📁 Estructura

```
computrabajo/
├── scrapers/
│   ├── computrabajo_scraper.py            # Scraper base (1 keyword)
│   ├── scrapear_con_diccionario.py        # Multi-keyword ✅ Usar este
│   ├── computrabajo_explorer.py           # Explorador técnico
│   ├── test_requests.py                   # Test de metodología
│   └── analizar_html.py                   # Análisis de estructura
├── config/
│   └── search_keywords.json               # Diccionario de búsquedas
├── data/
│   └── raw/                                # Datos scrapeados
└── README.md                               # Este archivo
```

---

## 🚀 Uso Rápido

### Instalación

```bash
cd 01_sources/computrabajo
pip install requests pandas beautifulsoup4 openpyxl
```

### Método Recomendado: Multi-Keyword

```bash
cd scrapers
python scrapear_con_diccionario.py
```

Esto scrapeará **4 keywords** (estrategia "minima") y consolidará resultados automáticamente.

**Resultado esperado**: ~150-200 ofertas únicas

---

## 💻 Uso Programático

### Opción 1: Script Multi-Keyword (Recomendado)

```python
from scrapear_con_diccionario import ComputRabajoMultiSearch

# Crear scraper multi-keyword
scraper = ComputRabajoMultiSearch(
    delay_between_requests=2.0,
    delay_between_keywords=5.0
)

# Scrapear con estrategia predefinida
df_ofertas = scraper.scrapear_multiples_keywords(
    estrategia="general",  # 14 keywords
    max_paginas_por_keyword=5,
    max_resultados_por_keyword=100
)

# Guardar resultados
files = scraper.guardar_resultados(df_ofertas)
```

### Opción 2: Keywords Personalizadas

```python
# Keywords custom
mis_keywords = ["python", "react", "data-analyst", "contabilidad"]

df_ofertas = scraper.scrapear_multiples_keywords(
    keywords=mis_keywords,
    max_paginas_por_keyword=3
)
```

### Opción 3: Scraper Simple (1 keyword)

```python
from computrabajo_scraper import ComputRabajoScraper

scraper = ComputRabajoScraper(delay_between_requests=2.0)

# Solo 1 keyword
ofertas = scraper.scrapear_todo(
    max_paginas=5,
    query="python"  # Requerido!
)

scraper.save_to_csv(ofertas)
```

---

## 📖 Diccionario de Búsquedas

Ubicación: `config/search_keywords.json`

### Estrategias Disponibles

| Estrategia | Keywords | Descripción | Uso |
|---|---|---|---|
| **minima** | 4 | Testing rápido | Development |
| **general** | 14 | Áreas principales | Producción ✅ |
| **tecnologia** | 20 | IT/Tech focus | Análisis IT |
| **amplia** | 15 | Máxima cobertura | Data collection |

### Editar Diccionario

Archivo: `config/search_keywords.json`

```json
{
  "estrategias": {
    "mi_estrategia": {
      "descripcion": "Mi estrategia custom",
      "keywords": [
        "python",
        "java",
        "ventas"
      ]
    }
  }
}
```

---

## 📊 Campos Disponibles

### Información Básica
- `id_oferta`: ID único de la oferta
- `titulo`: Título del puesto
- `empresa`: Nombre de la empresa
- `empresa_url`: URL de la empresa
- `empresa_rating`: Rating (1.0-5.0)

### Ubicación
- `ubicacion`: "Barrio/Ciudad, Capital Federal"
- Parseado a: `ciudad` y `provincia` en normalización

### Modalidad
- `modalidad`: Remoto/Presencial/Híbrido

### Fechas
- `fecha_publicacion`: ISO 8601
- `fecha_publicacion_raw`: "Hace X horas", "Ayer"

### URLs
- `url_completa`: URL de la oferta
- `url_relativa`: Path relativo

### Metadata
- `scrapeado_en`: Timestamp ISO
- `fuente`: "computrabajo"
- `keyword_busqueda`: Keyword usada (solo multi-keyword)

**Total**: 13-14 campos

---

## ⚙️ Configuración

### Parámetros del Scraper

```python
# Scraper base
scraper = ComputRabajoScraper(
    delay_between_requests=2.0  # Segundos entre páginas
)

# Multi-keyword
multi_scraper = ComputRabajoMultiSearch(
    delay_between_requests=2.0,  # Entre páginas
    delay_between_keywords=5.0   # Entre keywords
)

# Scraping
df = scraper.scrapear_multiples_keywords(
    estrategia="general",           # Estrategia a usar
    max_paginas_por_keyword=5,      # Páginas por keyword
    max_resultados_por_keyword=100  # Ofertas por keyword
)
```

### Rate Limiting

**Recomendado**:
- Entre páginas: 2 segundos
- Entre keywords: 5 segundos

**No bajar de**:
- Entre páginas: 1 segundo
- Entre keywords: 3 segundos

---

## 📈 Performance

- **Velocidad**: ~20 ofertas/minuto (con delays recomendados)
- **Recursos**: CPU < 5%, RAM ~30 MB
- **Almacenamiento**: ~2-3 KB por oferta
- **Deduplicación**: ~1-2% duplicados entre keywords

### Tiempo Estimado por Estrategia

| Estrategia | Keywords | Ofertas (aprox) | Tiempo |
|---|---|---|---|
| minima | 4 | 150-200 | ~1-2 min |
| general | 14 | 500-700 | ~5-7 min |
| tecnologia | 20 | 700-1000 | ~8-12 min |
| amplia | 15 | 600-800 | ~6-9 min |

---

## 🔍 Metodología Técnica

### ¿Por qué HTML Scraping y no API?

**Investigación realizada**:
1. ✅ Playwright - Interceptó network calls
2. ✅ NO se encontró API REST pública
3. ✅ Ofertas están en HTML Server-Side Rendered
4. ✅ `requests` funciona sin JavaScript rendering

**Ventajas**:
- Rápido (sin navegador)
- Bajo consumo de recursos
- Simple de mantener
- Efectivo (20 ofertas/página)

### Estructura HTML

```html
<article class="box_offer" data-id="2E9C1804DA7CAC8F...">
  <h2>
    <a class="js-o-link">Senior Python Developer</a>
  </h2>
  <p class="dFlex">
    <a href="/empresa">Kaizen Recursos Humanos</a>
    <span class="fwB">4.1</span>
  </p>
  <p class="fs16">
    <span class="mr10">Monserrat, Capital Federal</span>
  </p>
  <div class="fs13">
    <span class="icon i_home">Remoto</span>
  </div>
  <p class="fc_aux">Hace 4 horas</p>
</article>
```

---

## 🔄 Integración con Pipeline

### Consolidación

Las ofertas de ComputRabajo se normalizan automáticamente al schema unificado:

```bash
cd ../../02_consolidation/scripts
python consolidar_fuentes.py --fuentes computrabajo
```

**Mapeo de campos**:
- `id_oferta` → `_metadata.source_id`
- `titulo` → `informacion_basica.titulo`
- `ubicacion` → `ubicacion.ubicacion_raw` (parseado a ciudad/provincia)
- `modalidad` → `modalidad.modalidad_trabajo` (normalizado)
- `empresa_rating` → `source_specific.empresa_rating`

### Pipeline Completo

```bash
cd ../..
python pipeline_completo.py --all --fuentes computrabajo
```

Ejecuta:
1. Scraping (con diccionario)
2. Normalización
3. ESCO Matching
4. Análisis
5. Productos finales

---

## 🧪 Tests

### Test de Metodología

```bash
cd scrapers
python test_requests.py
```

Verifica que requests funciona (vs Playwright).

### Test del Scraper Simple

```bash
python computrabajo_scraper.py
```

Scrapea ofertas de "python" como ejemplo.

### Test Multi-Keyword

```bash
python scrapear_con_diccionario.py
```

Scrapea 4 keywords y consolida resultados.

---

## ⚖️ Consideraciones Legales

### ✅ Antes de Usar

1. Lee los [Términos de Servicio](https://ar.computrabajo.com/terminos-y-condiciones)
2. Verifica [robots.txt](https://ar.computrabajo.com/robots.txt)
3. Implementa rate limiting (mínimo 2 segundos)
4. Usa User-Agent identificable
5. Solo para investigación/análisis personal

### Límites Recomendados

- **Delay mínimo entre páginas**: 2 segundos
- **Delay mínimo entre keywords**: 5 segundos
- **Ofertas por sesión**: Hasta 500-1,000
- **Frecuencia**: No más de 1 vez por hora

---

## 🐛 Troubleshooting

### No se obtienen ofertas

**Problema**: El scraper devuelve 0 ofertas.

**Solución**:
- ✅ Usar `scrapear_con_diccionario.py` (multi-keyword)
- ✅ O especificar `query=` en scraper simple
- ❌ NO funciona sin keyword

### Muchos duplicados

**Problema**: Mismas ofertas en múltiples keywords.

**Solución**: El script multi-keyword deduplica automáticamente por `id_oferta`.

### Ubicación mal parseada

**Problema**: Ciudad/provincia incorrectos.

**Solución**: Ya corregido en normalizer. Formato esperado: "Ciudad, Capital Federal" → Ciudad="Ciudad", Provincia="Buenos Aires"

---

## 📝 Ejemplos de Uso

### Caso 1: Análisis del Mercado IT

```python
from scrapear_con_diccionario import ComputRabajoMultiSearch

scraper = ComputRabajoMultiSearch()

# Usar estrategia "tecnologia" (20 keywords IT)
df = scraper.scrapear_multiples_keywords(
    estrategia="tecnologia",
    max_paginas_por_keyword=10
)

# Análisis
print(df['keyword_busqueda'].value_counts())
print(df.groupby('modalidad')['id_oferta'].count())

scraper.guardar_resultados(df, "analisis_it")
```

### Caso 2: Ofertas Remotas

```python
# Scrapear
df = scraper.scrapear_multiples_keywords(estrategia="general")

# Filtrar remotas
remotas = df[df['modalidad'] == 'Remoto']

print(f"Ofertas remotas: {len(remotas)}/{len(df)}")
```

### Caso 3: Por Provincia

```python
from normalizar_campos import ComputRabajoNormalizer

# Scrapear
df_raw = scraper.scrapear_multiples_keywords(estrategia="amplia")

# Normalizar
normalizer = ComputRabajoNormalizer()
df_norm = normalizer.normalize(df_raw)

# Agrupar por provincia
por_provincia = df_norm.groupby('ubicacion.provincia').size()
print(por_provincia.sort_values(ascending=False))
```

---

## 📚 Documentación Adicional

- [Schema Unificado](../../shared/schemas/SCHEMA_DOCUMENTATION.md)
- [Pipeline Completo](../../docs/arquitectura.md)
- [Comparativa de Fuentes](../../RESUMEN_BUMERAN.md)

---

## 🔗 Enlaces Útiles

- [ComputRabajo Argentina](https://ar.computrabajo.com)
- [Términos de Servicio](https://ar.computrabajo.com/terminos-y-condiciones)
- [robots.txt](https://ar.computrabajo.com/robots.txt)

---

## 📊 Estadísticas

### Datos de Implementación (2025-10-21)

- **Ofertas disponibles**: ~500-1,000+ por keyword
- **Ofertas scrapeadas (test)**: 158 (4 keywords)
- **Campos por oferta**: 13-14
- **Formatos de exportación**: CSV, JSON, Excel
- **Tiempo de implementación**: 2-3 horas
- **Duplicados promedio**: 1-2%

### Comparativa vs Otras Fuentes

| Métrica | ZonaJobs | Bumeran | **ComputRabajo** |
|---|---|---|---|
| Ofertas | ~3,000 | ~12,000 | **~1,000/keyword** |
| Metodología | API REST | API REST | **HTML Scraping** |
| Complejidad | Media | Media | **Media** |
| Campos | 33 | 32 | **13** |
| **Requiere keywords** | ❌ | ❌ | **✅ Sí** |

---

## 🎯 Tips y Recomendaciones

1. **Siempre usa el script multi-keyword** para maximizar cobertura
2. **Estrategia "general"** es ideal para producción (14 keywords)
3. **Deduplicación automática** elimina ~1-2% duplicados
4. **Respeta rate limiting** (2s mínimo) para evitar bloqueos
5. **Customiza keywords** según tu necesidad específica
6. **Ubicación parseada** automáticamente en normalización

---

**Scraper implementado**: 2025-10-21
**Versión**: 1.0
**Estado**: ✅ Funcional (requiere diccionario)
**Mantenedor**: OEDE
