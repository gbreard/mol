# 📋 INVENTARIO DE SCRIPTS PRINCIPALES - MOL

**Proyecto:** Monitor de Ofertas Laborales (MOL)
**Total scripts en proyecto:** 248 (213 Python + 35 R)
**Scripts críticos documentados:** 20
**Fecha:** 14/11/2025

---

## 📊 TABLA RESUMEN

| # | Script | Grupo | Propósito | Frecuencia |
|---|--------|-------|-----------|------------|
| 1 | run_full_pipeline.py | Pipeline Maestro | Orquestador completo scraping multi-fuente | Manual/Programada |
| 2 | run_scheduler.py | Automatización | Scheduler 2x/semana (lunes y jueves 8 AM) | Loop continuo |
| 3 | bumeran_scraper.py | Scraping | Scraper API REST Bumeran (~12K ofertas) | Pipeline/Scheduler |
| 4 | scrapear_con_diccionario.py | Scraping | Multi-keyword Bumeran (máxima cobertura) | Incremental/Full |
| 5 | computrabajo_scraper.py | Scraping | Scraper HTML ComputRabajo (~500-1K) | Pipeline |
| 6 | linkedin_scraper.py | Scraping | Scraper JobSpy LinkedIn multi-keyword | Pipeline |
| 7 | zonajobs_scraper_final.py | Scraping | Scraper API REST ZonaJobs (~5K) | Pipeline |
| 8 | consolidar_fuentes.py | Consolidación | Consolida multi-fuente a schema único | Post-scraping |
| 9 | normalizar_campos.py | Consolidación | Normalizadores por fuente (40+ campos) | Consolidación |
| 10 | incremental_tracker.py | Utilidad | Tracking IDs scrapeados (evita duplicados) | Cada scraping |
| 11 | run_nlp_extraction.py | NLP | Ejecutor NLP datasets completos | Manual post-consolidación |
| 12 | bumeran_extractor.py | NLP | Extractor NLP Bumeran (regex patterns v3) | run_nlp_extraction |
| 13 | regex_patterns_v3.py | NLP | Patrones regex optimizados extracción | Extractores |
| 14 | esco_hybrid_matcher.py | ESCO | Matcher Fuzzy + Embeddings + LLM | Manual clasificación |
| 15 | integracion_esco_semantica.py | ESCO | Integración ofertas NLP + ESCO + skills | Post-NLP |
| 16 | db_manager.py | Base de Datos | Gestor SQLite dual-write schema v2 | Pipeline/Scheduler |
| 17 | init_sqlite.py | Base de Datos | Inicializador database SQLite | Setup inicial |
| 18 | populate_esco_from_rdf.py | Base de Datos | Parser ESCO RDF (3K ocupaciones + 13K skills) | Setup inicial |
| 19 | app.R | Dashboards | Dashboard Shiny análisis mercado laboral | On-demand |
| 20 | dashboard_scraping_v4.py | Dashboards | Dashboard Python monitoreo scraping | On-demand |

---

## 1️⃣ PIPELINE MAESTRO

### 1. run_full_pipeline.py
**Ruta:** `D:\OEDE\Webscrapping\run_full_pipeline.py`

**Propósito:**
Orquestador principal que ejecuta el pipeline completo de scraping multi-fuente (Bumeran, ComputRabajo, ZonaJobs, LinkedIn, Indeed) + consolidación.

**Inputs:**
- Diccionario de keywords (data/config/keywords_loader.py)
- Configuración de fuentes (01_sources/)

**Outputs:**
- Datos consolidados (02_consolidation/data/consolidated/)
- Logs de ejecución por fuente

**Frecuencia:** Manual o programada (modo incremental o full)

**Dependencias:**
- BumeranScraper, ComputRabajoMultiSearch
- ZonaJobsScraperFinal, LinkedInScraper, IndeedScraper
- ConsolidadorMultiFuente, IncrementalTracker

**Notas:**
Script maestro que permite ejecutar una o todas las fuentes con `--source=X` o `--full`.

---

### 2. run_scheduler.py
**Ruta:** `D:\OEDE\Webscrapping\run_scheduler.py`

**Propósito:**
Scheduler automatizado que ejecuta scraping de Bumeran según calendario (lunes y jueves 8 AM por defecto).

**Inputs:**
- database/config.py (SCHEDULER_CONFIG)
- Diccionario v3.2 (keywords)

**Outputs:**
- SQLite database actualizada (ofertas + métricas)
- Logs mensuales (logs/scheduler_YYYYMM.log)

**Frecuencia:** Loop continuo (2x por semana configurado)

**Dependencias:**
- BumeranMultiSearch, DatabaseManager
- schedule library

**Notas:**
Ejecutar con `python run_scheduler.py`. Loop infinito con heartbeat logging.

---

## 2️⃣ SCRAPING - FUENTES PRINCIPALES

### 3. bumeran_scraper.py
**Ruta:** `D:\OEDE\Webscrapping\01_sources\bumeran\scrapers\bumeran_scraper.py`

**Propósito:**
Scraper principal de Bumeran usando API REST (~12K ofertas disponibles).

**Inputs:**
- API POST: https://www.bumeran.com.ar/api/avisos/searchV2
- Headers: x-site-id, x-pre-session-token

**Outputs:**
- CSV/JSON/Excel en 01_sources/bumeran/data/raw/
- 40+ campos por oferta (fechas normalizadas, descripción limpia)

**Frecuencia:** Llamado por pipeline o scheduler

**Dependencias:**
- IncrementalTracker (evita duplicados)
- BumeranSchemas (validación)
- ScrapingMetrics, AdaptiveRateLimiter, CircuitBreaker, AlertManager

**Notas:**
Implementa retry automático, validación de schema, detección de paginación rota. Fuente principal del proyecto.

---

### 4. scrapear_con_diccionario.py
**Ruta:** `D:\OEDE\Webscrapping\01_sources\bumeran\scrapers\scrapear_con_diccionario.py`

**Propósito:**
Scraper multi-keyword de Bumeran que itera diccionario de búsquedas para máxima cobertura.

**Inputs:**
- Diccionario maestro:
  - Estrategia máxima: ~90 keywords
  - Estrategia completa: ~55 keywords
  - Estrategia general: ~30 keywords
- data/config/keywords_loader.py

**Outputs:**
- DataFrame consolidado deduplicado
- Métricas de cobertura vs API directa

**Frecuencia:** Modo incremental (diaria) o full (primera ejecución)

**Dependencias:**
- BumeranScraper, IncrementalTracker
- keywords_loader, date_filter

**Notas:**
Detecta duplicados masivos (paginación rota), filtro temporal de 7 días por defecto.

---

### 5. computrabajo_scraper.py
**Ruta:** `D:\OEDE\Webscrapping\01_sources\computrabajo\scrapers\computrabajo_scraper.py`

**Propósito:**
Scraper de ComputRabajo usando HTML parsing (BeautifulSoup) - ~500-1K ofertas.

**Inputs:**
- URL base: https://ar.computrabajo.com
- Paginación HTML

**Outputs:**
- CSV/JSON/Excel con 20+ campos estructurados

**Frecuencia:** Llamado por pipeline

**Dependencias:**
- BeautifulSoup4, requests

**Notas:**
Modo rápido (solo listados) o lento (fetch_description=True). Menor volumen que Bumeran.

---

### 6. linkedin_scraper.py
**Ruta:** `D:\OEDE\Webscrapping\01_sources\linkedin\scrapers\linkedin_scraper.py`

**Propósito:**
Scraper de LinkedIn usando JobSpy library con estrategia multi-keyword.

**Inputs:**
- JobSpy library (wrapper de LinkedIn API)
- Diccionario de keywords (30 keywords general)

**Outputs:**
- CSV/JSON/Excel consolidado deduplicado

**Frecuencia:** Llamado por pipeline

**Dependencias:**
- jobspy library
- IncrementalTracker

**Notas:**
Límite conservador ~500 ofertas/keyword por rate limits de LinkedIn. Requiere validación manual periódica.

---

### 7. zonajobs_scraper_final.py
**Ruta:** `D:\OEDE\Webscrapping\01_sources\zonajobs\scrapers\zonajobs_scraper_final.py`

**Propósito:**
Scraper de ZonaJobs usando API REST (~5K ofertas).

**Inputs:**
- POST: https://www.zonajobs.com.ar/api/avisos/searchHomeV2
- Headers similares a Bumeran

**Outputs:**
- JSON/CSV/Excel parseados y normalizados

**Frecuencia:** Llamado por pipeline

**Dependencias:**
- IncrementalTracker
- ZonaJobsParser (normalización específica)

**Notas:**
Filtro local de keywords (API no soporta filtros complejos). Segunda fuente más importante.

---

## 3️⃣ CONSOLIDACIÓN Y NORMALIZACIÓN

### 8. consolidar_fuentes.py
**Ruta:** `D:\OEDE\Webscrapping\02_consolidation\scripts\consolidar_fuentes.py`

**Propósito:**
Consolida y normaliza datos de múltiples fuentes a schema unificado.

**Inputs:**
- CSV/JSON de 01_sources/*/data/raw/
- Normalizadores por fuente (Bumeran, ZonaJobs, ComputRabajo, LinkedIn, Indeed)

**Outputs:**
- 02_consolidation/data/consolidated/*.csv|json|xlsx
- Reporte de cobertura por fuente

**Frecuencia:** Llamado por pipeline después de scraping

**Dependencias:**
- normalizar_campos.py (BumeranNormalizer, ZonaJobsNormalizer, etc.)

**Notas:**
Soporta filtrado por fechas. Output final: 40+ campos normalizados.

---

### 9. normalizar_campos.py
**Ruta:** `D:\OEDE\Webscrapping\02_consolidation\scripts\normalizar_campos.py`

**Propósito:**
Normalizadores que convierten datos crudos de cada fuente al schema unificado (40+ campos estructurados).

**Inputs:**
- DataFrames crudos por fuente (schemas heterogéneos)

**Outputs:**
- DataFrames normalizados con estructura común:
  - titulo, descripcion, empresa, ubicacion
  - fecha_publicacion (ISO), modalidad_trabajo, tipo_jornada
  - salario_min/max, requisitos, etc.

**Frecuencia:** Llamado por consolidar_fuentes.py

**Dependencias:**
- BaseNormalizer (clase base abstracta)

**Notas:**
Incluye limpieza HTML, normalización de modalidad/tipo trabajo, conversión de fechas a ISO.

---

### 10. incremental_tracker.py
**Ruta:** `D:\OEDE\Webscrapping\02_consolidation\scripts\incremental_tracker.py`

**Propósito:**
Sistema de tracking de IDs scrapeados por fuente para modo incremental (evita duplicados entre ejecuciones).

**Inputs:**
- data/tracking/{source}_scraped_ids.json

**Outputs:**
- JSON con IDs + timestamps (formato v2.0 con operaciones atómicas)

**Frecuencia:** Usado en cada scraping

**Dependencias:**
- Ninguna (librería estándar Python)

**Notas:**
Escritura atómica con backups, detección de formato legacy. Crítico para scraping incremental eficiente.

---

## 4️⃣ EXTRACCIÓN NLP

### 11. run_nlp_extraction.py
**Ruta:** `D:\OEDE\Webscrapping\02.5_nlp_extraction\scripts\run_nlp_extraction.py`

**Propósito:**
Script principal para ejecutar extracción NLP en datasets completos (extrae requisitos, educación, experiencia, salario).

**Inputs:**
- CSV de 01_sources/*/data/raw/
- Extractores por fuente (Bumeran, ZonaJobs, Indeed)

**Outputs:**
- 02.5_nlp_extraction/data/processed/*_nlp_YYYYMMDD.csv
- Stats de extracción:
  - Confidence score promedio
  - Cobertura por campo (% no nulos)
  - Distribución de valores

**Frecuencia:** Manual después de consolidación

**Dependencias:**
- BumeranExtractor, ZonaJobsExtractor, IndeedExtractor

**Notas:**
Procesa en batches para datasets grandes. Reporta métricas de calidad.

---

### 12. bumeran_extractor.py
**Ruta:** `D:\OEDE\Webscrapping\02.5_nlp_extraction\scripts\extractors\bumeran_extractor.py`

**Propósito:**
Extractor NLP específico para Bumeran usando regex patterns v3 + limpieza de texto.

**Inputs:**
- DataFrame con columnas: descripcion, titulo

**Outputs:**
- DataFrame con campos extraídos:
  - experiencia_años_min/max
  - nivel_educativo (primaria, secundaria, terciaria, universitaria, posgrado)
  - salario_min/max
  - idiomas (español, inglés, portugués, etc.)
  - certificaciones
  - modalidad_trabajo (presencial, híbrido, remoto)

**Frecuencia:** Llamado por run_nlp_extraction.py

**Dependencias:**
- regex_patterns_v3 (patrones optimizados)
- text_cleaner, html_stripper, encoding_fixer

**Notas:**
Versión v3 optimizada (backups v1, v2 disponibles en carpeta). Mayor precisión vs v1/v2.

---

### 13. regex_patterns_v3.py
**Ruta:** `D:\OEDE\Webscrapping\02.5_nlp_extraction\scripts\patterns\regex_patterns_v3.py`

**Propósito:**
Patrones regex optimizados para extracción de información laboral (v3 más preciso que v1/v2).

**Inputs:**
- Texto de ofertas (descripción)

**Outputs:**
- Matches de:
  - Experiencia: "2-3 años", "mínimo 5 años", "junior/semi-senior/senior"
  - Educación: "título universitario", "estudiante avanzado", "terciario completo"
  - Idiomas: "inglés avanzado", "portugués intermedio"
  - Certificaciones: nombres comunes de certificaciones
  - Modalidad: "trabajo remoto", "presencial", "modalidad híbrida"
  - Salario: "$50.000 a $80.000", "hasta $100k"

**Frecuencia:** Importado por extractores

**Dependencias:**
- re (Python regex)

**Notas:**
Múltiples versiones mantenidas (v1, v2, v3) para A/B testing. v3 actual.

---

## 5️⃣ ESCO MATCHING

### 14. esco_hybrid_matcher.py
**Ruta:** `D:\OEDE\Webscrapping\03_esco_matching\scripts\esco_hybrid_matcher.py`

**Propósito:**
Matcher híbrido que combina Fuzzy (rápido score≥80) + Embeddings (similitud semántica) + LLM (Ollama para casos complejos score<70).

**Inputs:**
- Títulos de ofertas de trabajo
- ESCO JSON (3,008 ocupaciones)
- Modelo embeddings: paraphrase-multilingual-MiniLM-L12-v2

**Outputs:**
- Mejor match ESCO:
  - esco_code (código ISCO-08)
  - occupation_name
  - confidence_score (0-100)
  - strategy ("fuzzy" / "embeddings" / "llm")

**Frecuencia:** Manual para clasificación de ofertas

**Dependencias:**
- sentence-transformers (embeddings)
- Ollama (llama3 para LLM fallback)
- difflib (fuzzy matching)

**Notas:**
Sistema de 3 niveles: Fuzzy primero (rápido), si falla → Embeddings, si falla → LLM (lento pero preciso).

---

### 15. integracion_esco_semantica.py
**Ruta:** `D:\OEDE\Webscrapping\03_esco_matching\scripts\integracion_esco_semantica.py`

**Propósito:**
Integración final de ofertas NLP procesadas con taxonomía ESCO + skills asociadas.

**Inputs:**
- Ofertas con NLP extraído (CSV)
- ESCO occupations (3,008 ocupaciones)
- ESCO skills (13,890 skills)
- ISCO hierarchy (jerarquía de ocupaciones)

**Outputs:**
- Dataset final con:
  - Clasificación ESCO (código + nombre)
  - Skills asociadas a la ocupación
  - Jerarquía ISCO (major group → sub-major → minor → unit)
  - Confidence score

**Frecuencia:** Manual después de NLP

**Dependencias:**
- esco_hybrid_matcher.py

**Notas:**
Output final listo para dashboard Shiny. Enriquece ofertas con taxonomía estándar europea.

---

## 6️⃣ BASE DE DATOS

### 16. db_manager.py
**Ruta:** `D:\OEDE\Webscrapping\database\db_manager.py`

**Propósito:**
Gestor principal de SQLite con dual-write al schema v2 (ofertas, métricas, alertas, circuit breaker, rate limiter).

**Inputs:**
- DataFrames de ofertas procesadas
- Métricas de ScrapingMetrics
- Alertas de AlertManager

**Outputs:**
- SQLite database: bumeran_scraping.db
- Tablas:
  - ofertas (datos principales)
  - metricas_scraping (performance)
  - alertas (errores/warnings)
  - circuit_breaker_stats (resiliencia)
  - rate_limiter_stats (control de velocidad)

**Frecuencia:** Usado por scheduler y pipeline

**Dependencias:**
- db_manager_v2 (dual-write para migración)
- sqlite3

**Notas:**
Validación de calidad pre-insert. Rechaza ofertas con campos críticos vacíos (titulo, empresa).

---

### 17. init_sqlite.py
**Ruta:** `D:\OEDE\Webscrapping\database\init_sqlite.py`

**Propósito:**
Inicializador de database SQLite (crea schema con 5+ tablas + vistas).

**Inputs:**
- create_database_sqlite.sql (DDL statements)

**Outputs:**
- bumeran_scraping.db con:
  - Foreign keys habilitados
  - Índices en campos clave
  - Vistas para reportes

**Frecuencia:** Una vez al inicio del proyecto (o con flag --reset)

**Dependencias:**
- sqlite3

**Notas:**
Incluye verificación de tablas requeridas. Safe to re-run (no pierde datos).

---

### 18. populate_esco_from_rdf.py
**Ruta:** `D:\OEDE\Webscrapping\database\populate_esco_from_rdf.py`

**Propósito:**
Parser del archivo ESCO RDF (1.26 GB) que extrae 3,008 ocupaciones + 13,890 skills + jerarquía ISCO + 60K+ associations.

**Inputs:**
- esco-v1.2.0.rdf (solo español xml:lang="es")
- Archivo RDF completo de taxonomía ESCO

**Outputs:**
- Tablas SQLite:
  - esco_occupations (3,008 filas)
  - esco_skills (13,890 filas)
  - esco_isco (jerarquía ISCO-08)
  - esco_associations (60K+ relaciones ocupación-skill)

**Frecuencia:** Una vez al inicio (15-30 min procesamiento)

**Dependencias:**
- rdflib (parser RDF/XML)
- tqdm (progress bar)

**Notas:**
Extracción completa de metadata ESCO (alternative labels, scope notes, ancestors ISCO). Solo ejecutar si la BD no tiene tablas ESCO.

---

## 7️⃣ DASHBOARDS Y ANÁLISIS

### 19. app.R
**Ruta:** `D:\OEDE\Webscrapping\Visual--\app.R`

**Propósito:**
Dashboard Shiny interactivo para análisis del mercado laboral con taxonomía ESCO (268 ofertas matcheadas actualmente).

**Inputs:**
- CSV con ofertas + clasificación ESCO
- Datos de skills, provincias, ocupaciones

**Outputs:**
- Dashboard web con 6 tabs:
  1. **Panorama General:** Métricas clave, mapa de provincias
  2. **Perfil Demandado:** Educación, experiencia, salarios
  3. **Skills Más Demandadas:** Top skills por ocupación
  4. **Ocupaciones ESCO:** Taxonomía y distribución
  5. **Explorador de Ofertas:** Búsqueda y filtros
  6. **Tendencias:** Series temporales
- Gráficos interactivos: plotly, ggplot2
- Mapas: leaflet
- Tablas: DT

**Frecuencia:** On-demand (deployment en shinyapps.io)

**Dependencias:**
- shiny, shinydashboard
- ggplot2, plotly, leaflet, DT

**Notas:**
Versión v2.4.0 con filtro temporal, responsive design. shinyTree deshabilitado por conflictos de versión. Desplegado en: https://dos1tv-gerardo-breard.shinyapps.io/dashboard-esco-argentina/

---

### 20. dashboard_scraping_v4.py
**Ruta:** `D:\OEDE\Webscrapping\dashboard_scraping_v4.py`

**Propósito:**
Dashboard Python de monitoreo de scraping en tiempo real (métricas, alertas, cobertura).

**Inputs:**
- SQLite database (tablas: metricas_scraping, alertas)
- Logs de scraping

**Outputs:**
- Dashboard web (Streamlit/Dash) con:
  - Métricas de performance (tiempo/oferta, tasa éxito)
  - Visualizaciones de cobertura por fuente
  - Alertas y errores recientes
  - Circuit breaker status
  - Rate limiter stats

**Frecuencia:** On-demand para monitoreo de operaciones

**Dependencias:**
- streamlit o dash
- pandas, plotly

**Notas:**
Versión v4 actual (v1-v3 deprecated). Dashboard técnico para DevOps, no público.

---

## 📊 FLUJO TÍPICO DE EJECUCIÓN

### Pipeline Completo (modo manual):

```bash
# 1. Scraping multi-fuente
python run_full_pipeline.py --full

# 2. Consolidación (incluida en pipeline)
# → consolidar_fuentes.py se ejecuta automáticamente

# 3. Extracción NLP (manual)
python 02.5_nlp_extraction/scripts/run_nlp_extraction.py

# 4. Clasificación ESCO (manual)
python 03_esco_matching/scripts/integracion_esco_semantica.py

# 5. Visualización
# → Iniciar dashboard Shiny
Rscript -e "shiny::runApp('Visual--/app.R', port=3840)"
```

### Pipeline Automatizado (modo scheduler):

```bash
# Ejecutar scheduler (loop continuo)
python run_scheduler.py

# → Ejecuta automáticamente 2x/semana:
#   - Scraping Bumeran con diccionario
#   - Guardado en SQLite
#   - Logs en logs/scheduler_YYYYMM.log
```

---

## 🔄 SCRIPTS CON VERSIONES MÚLTIPLES

### Usar ÚLTIMA versión en producción:

1. **bumeran_extractor.py**
   - ✅ v3 (actual): `02.5_nlp_extraction/scripts/extractors/bumeran_extractor.py`
   - 📦 v2 (backup): `02.5_nlp_extraction/scripts/extractors/bumeran_extractor_v2.py`
   - 📦 v1 (legacy): `02.5_nlp_extraction/scripts/extractors/bumeran_extractor_v1.py`

2. **regex_patterns.py**
   - ✅ v3 (actual): `02.5_nlp_extraction/scripts/patterns/regex_patterns_v3.py`
   - 📦 v2 (backup): `02.5_nlp_extraction/scripts/patterns/regex_patterns_v2.py`
   - 📦 v1 (legacy): `02.5_nlp_extraction/scripts/patterns/regex_patterns_v1.py`

3. **dashboard_scraping.py**
   - ✅ v4 (actual): `dashboard_scraping_v4.py`
   - 📦 v3 (deprecated): `dashboard_scraping_v3.py`
   - 📦 v2 (deprecated): `dashboard_scraping_v2.py`
   - 📦 v1 (deprecated): `dashboard_scraping.py`

4. **app.R**
   - ✅ v2.4.0 (actual): `Visual--/app.R`
   - 📦 v3 (backup): `Visual--/backup/app_v3.R`
   - 📦 v2.0 (backup): `Visual--/backup/app_v2.0_pre-mejoras.R`

---

## 📌 FRECUENCIAS DE EJECUCIÓN

### Automática (sin intervención):
- **2x por semana:** run_scheduler.py (lunes y jueves 8 AM)

### Manual (cuando hay nuevos datos):
- **Incremental diario:** run_full_pipeline.py --source=bumeran
- **Full semanal:** run_full_pipeline.py --full (todas las fuentes)

### Post-procesamiento (después de scraping):
- **NLP:** run_nlp_extraction.py (procesar ofertas nuevas)
- **ESCO:** integracion_esco_semantica.py (clasificar nuevas ofertas)

### Setup único (primera vez):
- **Database:** init_sqlite.py --reset
- **ESCO:** populate_esco_from_rdf.py

### On-demand (cuando se necesita):
- **Dashboard Shiny:** Rscript -e "shiny::runApp('Visual--/app.R')"
- **Dashboard Python:** python dashboard_scraping_v4.py

---

## 🎯 SCRIPTS EXCLUIDOS DEL TOP 20

Los siguientes tipos de scripts NO fueron incluidos (razones):

1. **Tests (43 scripts):** test_*.py - Útiles para desarrollo pero no críticos para producción
2. **Análisis exploratorios:** analizar_*.py, explorar_*.py - Temporales/ad-hoc
3. **Backups versionados:** *_v1.py, *_v2.py, *_backup.py - Versiones obsoletas
4. **Utils genéricos:** check_*.py, verify_*.py, fix_*.py - Mantenimiento secundario
5. **Deployment R:** instalar_*.R, deploy_*.R, configurar_*.R - Setup único
6. **Migraciones:** migrate_*.py - Ejecución única histórica
7. **Scripts duplicados:** Webscrapping/ folder (duplicados de Visual--/)

---

## 📞 CONTACTO

**Responsable:** Equipo Técnico OEDE
**Última actualización:** 14/11/2025
**Versión del documento:** 1.0

---

**Documentos relacionados:**
- `inventario_scripts_python.txt` - Listado completo de 213 scripts Python
- `inventario_scripts_R.txt` - Listado completo de 35 scripts R
- `schema_bd.sql` - Schema de 32 tablas SQLite
- `ARQUITECTURA_SISTEMA.md` - Diagrama de arquitectura (próximo)
