# 📊 CLASIFICACIÓN DE VARIABLES POR COMPLETITUD DE DATOS

**Base de datos:** ofertas_consolidadas.xlsx
**Total de registros:** 1,156
**Total de variables:** 91

---

## 🎯 RESUMEN EJECUTIVO

| Categoría | Variables | Porcentaje | ¿Usable? |
|-----------|-----------|------------|----------|
| **100% completas** | 7 | 7.7% | ✅ SÍ |
| **90-99% completas** | 5 | 5.5% | ✅ SÍ |
| **75-89% completas** | 3 | 3.3% | ✅ SÍ |
| **50-74% completas** | 8 | 8.8% | ⚠️ LIMITADO |
| **25-49% completas** | 3 | 3.3% | ⚠️ NO RECOMENDADO |
| **1-24% completas** | 24 | 26.4% | ❌ NO |
| **0% vacías** | 41 | 45.1% | ❌ NO |

### Conclusión:
- ✅ **USABLES (≥50%):** 23 variables (25.3%)
- ❌ **NO USABLES (<50%):** 68 variables (74.7%)

---

## CATEGORÍA 1: 100% COMPLETAS - DATOS TOTALES ✅
**7 variables | 7.7% del total**

Estas variables tienen información en TODOS los registros. Son las más confiables.

| # | Variable | Completitud | Registros |
|---|----------|-------------|-----------|
| 1 | `_metadata.source` | 100.0% | 1,156/1,156 |
| 2 | `_metadata.source_id` | 100.0% | 1,156/1,156 |
| 3 | `_metadata.url_oferta` | 100.0% | 1,156/1,156 |
| 4 | `informacion_basica.titulo` | 100.0% | 1,156/1,156 |
| 5 | `Fecha_final` | 100.0% | 1,156/1,156 |
| 6 | `Periodo` | 100.0% | 1,156/1,156 |
| 7 | `ubicacion.pais` | 100.0% | 1,156/1,156 |

**💡 Uso recomendado:** Todas estas variables son ideales para filtros, agrupaciones y análisis.

---

## CATEGORÍA 2: 90-99% COMPLETAS - MUY ALTA CALIDAD ✅
**5 variables | 5.5% del total**

Casi completas, faltan menos del 10% de los datos.

| # | Variable | Completitud | Registros |
|---|----------|-------------|-----------|
| 1 | `fechas.fecha_publicacion` | 98.2% | 1,135/1,156 |
| 2 | `ubicacion.ubicacion_raw` | 96.1% | 1,111/1,156 |
| 3 | `ubicacion.provincia` | 96.1% | 1,111/1,156 |
| 4 | `ubicacion.ciudad` | 96.1% | 1,111/1,156 |
| 5 | `informacion_basica.empresa` | 92.9% | 1,074/1,156 |

**💡 Uso recomendado:** Excelentes para análisis geográfico, temporal y por empresa.

---

## CATEGORÍA 3: 75-89% COMPLETAS - ALTA CALIDAD ✅
**3 variables | 3.3% del total**

Buena calidad, faltan entre 11-25% de los datos.

| # | Variable | Completitud | Registros |
|---|----------|-------------|-----------|
| 1 | `_metadata.version_schema` | 81.7% | 945/1,156 |
| 2 | `_metadata.fecha_scraping` | 81.7% | 945/1,156 |
| 3 | `informacion_basica.empresa_validada` | 81.7% | 945/1,156 |

**💡 Uso recomendado:** Útiles para metadatos y validación.

---

## CATEGORÍA 4: 50-74% COMPLETAS - CALIDAD MEDIA ⚠️
**8 variables | 8.8% del total**

Calidad media, faltan entre 26-50% de los datos. Usar con precaución.

| # | Variable | Completitud | Registros |
|---|----------|-------------|-----------|
| 1 | `informacion_basica.empresa_url` | 74.7% | 863/1,156 |
| 2 | `compensacion.beneficios` | 66.0% | 763/1,156 |
| 3 | `requisitos.idiomas` | 66.0% | 763/1,156 |
| 4 | `requisitos.habilidades` | 66.0% | 763/1,156 |
| 5 | `compensacion.mostrar_salario` | 66.0% | 763/1,156 |
| 6 | `clasificacion_esco.habilidades_esco` | 66.0% | 763/1,156 |
| 7 | `source_specific.fecha_publicacion_raw` | 66.0% | 763/1,156 |
| 8 | `source_specific.url_relativa` | 66.0% | 763/1,156 |

**💡 Uso recomendado:** Solo para análisis secundarios. Considerar sesgo por datos faltantes.

---

## CATEGORÍA 5: 25-49% COMPLETAS - CALIDAD BAJA ⚠️
**3 variables | 3.3% del total**

Calidad baja, faltan más del 50% de los datos. NO recomendado para análisis principal.

| # | Variable | Completitud | Registros |
|---|----------|-------------|-----------|
| 1 | `modalidad.modalidad_trabajo` | 42.3% | 489/1,156 |
| 2 | `source_specific.empresa_rating` | 37.0% | 428/1,156 |
| 3 | `informacion_basica.descripcion` | 26.9% | 311/1,156 |

**💡 Uso recomendado:** Evitar. Si se usan, mencionar explícitamente la alta tasa de datos faltantes.

---

## CATEGORÍA 6: 1-24% COMPLETAS - CALIDAD MUY BAJA ❌
**24 variables | 26.4% del total**

Muy baja calidad, más del 75% de datos faltantes. NO USAR.

| # | Variable | Completitud | Registros |
|---|----------|-------------|-----------|
| 1 | `fechas.fecha_modificacion` | 18.3% | 211/1,156 |
| 2 | `source_specific` | 18.3% | 211/1,156 |
| 3 | `_metadata.fecha_extraccion` | 18.3% | 211/1,156 |
| 4 | `informacion_basica.titulo_normalizado` | 18.3% | 211/1,156 |
| 5 | `modalidad.modalidad_raw` | 18.3% | 211/1,156 |
| 6 | `modalidad.tipo_trabajo_raw` | 18.3% | 211/1,156 |
| 7 | `informacion_basica.descripcion_limpia` | 18.3% | 211/1,156 |
| 8 | `modalidad.tipo_trabajo` | 18.3% | 211/1,156 |
| 9 | `fechas.fecha_publicacion_raw` | 18.3% | 211/1,156 |
| 10 | `_metadata.version_scraper` | 18.3% | 211/1,156 |
| 11 | `detalles.apto_discapacitado` | 18.3% | 211/1,156 |
| 12 | `detalles.cantidad_vacantes` | 18.3% | 211/1,156 |
| 13 | `_metadata.unified_id` | 18.3% | 211/1,156 |
| 14 | `detalles.confidencial` | 18.3% | 211/1,156 |
| 15 | `compensacion.moneda` | 18.3% | 211/1,156 |
| 16 | `informacion_basica.empresa_id` | 14.1% | 163/1,156 |
| 17 | `detalles.area_trabajo` | 13.0% | 150/1,156 |
| 18 | `descripcion.descripcion_completa` | 8.7% | 100/1,156 |
| 19 | `source_specific.search_term_usado` | 7.1% | 82/1,156 |
| 20 | `condiciones.tipo_contrato` | 6.7% | 77/1,156 |
| 21 | `source_specific.company_num_employees` | 6.1% | 70/1,156 |
| 22 | `informacion_basica.logo_url` | 6.0% | 69/1,156 |
| 23 | `source_specific.company_revenue` | 5.4% | 62/1,156 |
| 24 | `source_specific.company_industry` | 2.4% | 28/1,156 |

**💡 Nota:** Muchas de estas variables tienen exactamente 18.3% (211 registros), lo que sugiere que provienen de una sola fuente de scraping que tiene un esquema más completo.

---

## CATEGORÍA 7: 0% VACÍAS - SIN DATOS ❌
**41 variables | 45.1% del total**

Variables completamente vacías. ELIMINAR o ignorar.

| # | Variable | Completitud |
|---|----------|-------------|
| 1 | `ubicacion.codigo_postal` | 0.0% |
| 2 | `fechas.fecha_cierre` | 0.0% |
| 3 | `detalles.nivel_puesto` | 0.0% |
| 4 | `compensacion.salario_raw` | 0.0% |
| 5 | `requisitos.nivel_educativo` | 0.0% |
| 6 | `requisitos.experiencia_minima` | 0.0% |
| 7 | `compensacion.periodo` | 0.0% |
| 8 | `compensacion.salario_maximo` | 0.0% |
| 9 | `compensacion.salario_minimo` | 0.0% |
| 10 | `modalidad.nivel_laboral` | 0.0% |
| 11 | `ubicacion.zona` | 0.0% |
| 12 | `clasificacion_esco.isco_code` | 0.0% |
| 13 | `clasificacion_esco.isco_label` | 0.0% |
| 14 | `clasificacion_esco.similarity_score` | 0.0% |
| 15 | `clasificacion_esco.skills` | 0.0% |
| 16 | `clasificacion_esco.matching_method` | 0.0% |
| 17 | `clasificacion_esco.matching_timestamp` | 0.0% |
| 18 | `clasificacion_esco.ocupacion_esco_label` | 0.0% |
| 19 | `clasificacion_esco.ocupacion_esco_code` | 0.0% |
| 20 | `requisitos.certificaciones` | 0.0% |
| 21 | `clasificacion_esco.ocupacion_esco_codigo` | 0.0% |
| 22 | `clasificacion_esco.ocupacion_esco_titulo` | 0.0% |
| 23 | `detalles.subarea` | 0.0% |
| 24 | `requisitos.estudios_minimos` | 0.0% |
| 25 | `fechas.fecha_actualizacion` | 0.0% |
| 26 | `requisitos.experiencia_requerida` | 0.0% |
| 27 | `fechas.fecha_inicio` | 0.0% |
| 28 | `modalidad.disponibilidad` | 0.0% |
| 29 | `modalidad.esquema_horario` | 0.0% |
| 30 | `clasificacion_esco.confidence_score` | 0.0% |
| 31 | `clasificacion_esco.ocupacion_esco_uri` | 0.0% |
| 32 | `requisitos.conocimientos_tecnicos` | 0.0% |
| 33 | `requisitos.areas_estudio` | 0.0% |
| 34 | `descripcion.responsabilidades` | 0.0% |
| 35 | `condiciones.beneficios` | 0.0% |
| 36 | `condiciones.rango_salarial` | 0.0% |
| 37 | `condiciones.nivel_jerarquico` | 0.0% |
| 38 | `source_specific.listing_type` | 0.0% |
| 39 | `source_specific.job_function` | 0.0% |
| 40 | `descripcion.requisitos_deseables` | 0.0% |
| 41 | `source_specific.work_from_home_type` | 0.0% |

**💡 Recomendación:** Estas variables ocupan espacio sin aportar información. Considerar eliminarlas del esquema.

---

## 📈 ANÁLISIS DE PATRONES

### Patrón 1: Variables con exactamente 18.3% (211 registros)
Estas 15 variables tienen exactamente 211 registros (18.3%):
- `_metadata.fecha_extraccion`
- `_metadata.version_scraper`
- `_metadata.unified_id`
- `informacion_basica.titulo_normalizado`
- `informacion_basica.descripcion_limpia`
- `modalidad.tipo_trabajo`
- `modalidad.tipo_trabajo_raw`
- `modalidad.modalidad_raw`
- `fechas.fecha_modificacion`
- `fechas.fecha_publicacion_raw`
- `detalles.cantidad_vacantes`
- `detalles.apto_discapacitado`
- `detalles.confidencial`
- `compensacion.moneda`
- `source_specific`

**Interpretación:** Estos 211 registros provienen de una fuente específica que tiene un esquema más completo (probablemente la más reciente o mejor estructurada).

### Patrón 2: Variables con exactamente 66.0% (763 registros)
Estas 8 variables tienen exactamente 763 registros (66.0%):
- `requisitos.idiomas`
- `requisitos.habilidades`
- `compensacion.beneficios`
- `compensacion.mostrar_salario`
- `clasificacion_esco.habilidades_esco`
- `source_specific.fecha_publicacion_raw`
- `source_specific.url_relativa`

**Interpretación:** Estos 763 registros corresponden a **computrabajo** (la fuente mayoritaria con 66% de los datos).

### Patrón 3: Variables con exactamente 81.7% (945 registros)
Estas 3 variables tienen exactamente 945 registros:
- `_metadata.version_schema`
- `_metadata.fecha_scraping`
- `informacion_basica.empresa_validada`

**Interpretación:** 945 = 1156 - 211, sugiere que 211 registros fueron procesados con una versión anterior del scraper.

---

## 🎯 RECOMENDACIONES FINALES

### ✅ Variables CORE (usar siempre):
1. `informacion_basica.titulo`
2. `informacion_basica.empresa`
3. `ubicacion.provincia`
4. `ubicacion.ciudad`
5. `fechas.fecha_publicacion` / `Periodo`
6. `_metadata.source`
7. `_metadata.url_oferta`

### ⚠️ Variables SECUNDARIAS (usar con precaución):
1. `modalidad.modalidad_trabajo` (42.3% - mencionar limitación)
2. `source_specific.empresa_rating` (37.0% - solo para LinkedIn)
3. `informacion_basica.empresa_url` (74.7% - buena para links)

### ❌ Variables DESCARTAR:
- Todas las de clasificación ESCO (0%)
- Todas las de compensación salarial (0%)
- Todas las de requisitos detallados (0%)

### 🔧 Oportunidades de Mejora del Scraper:
1. **Homogeneizar esquemas** entre fuentes
2. **Completar modalidad.tipo_trabajo** (solo 18.3%)
3. **Implementar clasificación ESCO** (actualmente 0%)
4. **Capturar salarios** cuando estén disponibles (actualmente 0%)
5. **Normalizar empresas** para análisis más preciso

---

**Última actualización:** 24/10/2025
**Generado por:** Claude Code
