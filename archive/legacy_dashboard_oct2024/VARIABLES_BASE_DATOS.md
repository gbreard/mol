# 📊 VARIABLES DE LA BASE DE DATOS - Ofertas Laborales

**Total de registros:** 1,156
**Total de variables:** 91
**Fuentes:** computrabajo (763), bumeran (150), indeed (100), linkedin (82), zonajobs (61)

---

## 🏷️ VARIABLES POR CATEGORÍA

### 1️⃣ METADATOS (_metadata)
Variables que identifican el origen y procesamiento de los datos

| Variable | Completitud | Valores Únicos | Descripción |
|----------|-------------|----------------|-------------|
| `_metadata.source` | 100.0% | 5 | Fuente del scraping (computrabajo, bumeran, indeed, linkedin, zonajobs) |
| `_metadata.source_id` | 100.0% | 1,026 | ID único en la fuente original |
| `_metadata.unified_id` | 18.3% | 81 | ID unificado del sistema |
| `_metadata.url_oferta` | 100.0% | 1,026 | URL de la oferta original |
| `_metadata.fecha_extraccion` | 18.3% | 211 | Timestamp de extracción |
| `_metadata.fecha_scraping` | 81.7% | 767 | Timestamp del scraping |
| `_metadata.version_scraper` | 18.3% | 2 | Versión del scraper utilizado |
| `_metadata.version_schema` | 81.7% | 1 | Versión del esquema de datos |

---

### 2️⃣ INFORMACIÓN BÁSICA (informacion_basica)
Datos principales de la oferta laboral

| Variable | Completitud | Valores Únicos | Descripción |
|----------|-------------|----------------|-------------|
| `informacion_basica.titulo` | 100.0% | 930 | **✅ PRINCIPAL** - Título de la oferta |
| `informacion_basica.titulo_normalizado` | 18.3% | 80 | Título normalizado (limpio) |
| `informacion_basica.empresa` | 92.9% | 418 | **✅ PRINCIPAL** - Nombre de la empresa |
| `informacion_basica.empresa_id` | 14.1% | 41 | ID de la empresa |
| `informacion_basica.empresa_validada` | 81.7% | 1 | Empresa verificada (0/1) |
| `informacion_basica.empresa_url` | 74.7% | 378 | URL del perfil de la empresa |
| `informacion_basica.descripcion` | 26.9% | 178 | Descripción de la oferta |
| `informacion_basica.descripcion_limpia` | 18.3% | 80 | Descripción limpia |
| `informacion_basica.logo_url` | 6.0% | 39 | URL del logo de la empresa |

---

### 3️⃣ UBICACIÓN (ubicacion)
Localización geográfica de la oferta

| Variable | Completitud | Valores Únicos | Descripción |
|----------|-------------|----------------|-------------|
| `ubicacion.pais` | 100.0% | 1 | **✅ PRINCIPAL** - País (Argentina) |
| `ubicacion.provincia` | 96.1% | 27 | **✅ PRINCIPAL** - Provincia (27 provincias) |
| `ubicacion.ciudad` | 96.1% | 215 | **✅ PRINCIPAL** - Ciudad (215 ciudades) |
| `ubicacion.ubicacion_raw` | 96.1% | 228 | Ubicación sin procesar |
| `ubicacion.zona` | 0.0% | 0 | Zona (sin datos) |
| `ubicacion.codigo_postal` | 0.0% | 0 | Código postal (sin datos) |

---

### 4️⃣ MODALIDAD (modalidad)
Modalidad y tipo de trabajo

| Variable | Completitud | Valores Únicos | Descripción |
|----------|-------------|----------------|-------------|
| `modalidad.modalidad_trabajo` | 42.3% | 3 | **✅ PRINCIPAL** - Modalidad (presencial/remoto/híbrido) |
| `modalidad.tipo_trabajo` | 18.3% | 3 | **✅ PRINCIPAL** - Tipo (full-time/part-time/pasantía) |
| `modalidad.modalidad_raw` | 18.3% | 2 | Modalidad sin procesar |
| `modalidad.tipo_trabajo_raw` | 18.3% | 3 | Tipo sin procesar |
| `modalidad.nivel_laboral` | 0.0% | 0 | Nivel laboral (sin datos) |
| `modalidad.esquema_horario` | 0.0% | 0 | Esquema horario (sin datos) |
| `modalidad.disponibilidad` | 0.0% | 0 | Disponibilidad (sin datos) |

---

### 5️⃣ FECHAS (fechas)
Información temporal de las ofertas

| Variable | Completitud | Valores Únicos | Descripción |
|----------|-------------|----------------|-------------|
| `fechas.fecha_publicacion` | 98.2% | 800 | **✅ PRINCIPAL** - Fecha de publicación |
| `Fecha_final` | 100.0% | 48 | **✅ PRINCIPAL** - Fecha formateada (DD/MM/YYYY) |
| `Periodo` | 100.0% | 44 | **✅ PRINCIPAL** - Periodo (YYYY-MM-DD) |
| `fechas.fecha_modificacion` | 18.3% | 80 | Fecha de modificación |
| `fechas.fecha_publicacion_raw` | 18.3% | 33 | Fecha publicación sin procesar |
| `fechas.fecha_cierre` | 0.0% | 0 | Fecha de cierre (sin datos) |
| `fechas.fecha_actualizacion` | 0.0% | 0 | Fecha de actualización (sin datos) |
| `fechas.fecha_inicio` | 0.0% | 0 | Fecha de inicio (sin datos) |

---

### 6️⃣ REQUISITOS (requisitos)
Requisitos y habilidades solicitadas

| Variable | Completitud | Valores Únicos | Descripción |
|----------|-------------|----------------|-------------|
| `requisitos.idiomas` | 66.0% | 1 | Idiomas requeridos (array vacío) |
| `requisitos.habilidades` | 66.0% | 1 | Habilidades requeridas (array vacío) |
| `requisitos.experiencia_minima` | 0.0% | 0 | Experiencia mínima (sin datos) |
| `requisitos.experiencia_requerida` | 0.0% | 0 | Experiencia requerida (sin datos) |
| `requisitos.nivel_educativo` | 0.0% | 0 | Nivel educativo (sin datos) |
| `requisitos.estudios_minimos` | 0.0% | 0 | Estudios mínimos (sin datos) |
| `requisitos.areas_estudio` | 0.0% | 0 | Áreas de estudio (sin datos) |
| `requisitos.certificaciones` | 0.0% | 0 | Certificaciones (sin datos) |
| `requisitos.conocimientos_tecnicos` | 0.0% | 0 | Conocimientos técnicos (sin datos) |

---

### 7️⃣ COMPENSACIÓN (compensacion)
Información salarial y beneficios

| Variable | Completitud | Valores Únicos | Descripción |
|----------|-------------|----------------|-------------|
| `compensacion.moneda` | 18.3% | 1 | Moneda (ARS) |
| `compensacion.mostrar_salario` | 66.0% | 1 | Mostrar salario (0/1) |
| `compensacion.beneficios` | 66.0% | 1 | Beneficios (array vacío) |
| `compensacion.salario_minimo` | 0.0% | 0 | Salario mínimo (sin datos) |
| `compensacion.salario_maximo` | 0.0% | 0 | Salario máximo (sin datos) |
| `compensacion.periodo` | 0.0% | 0 | Periodo salarial (sin datos) |
| `compensacion.salario_raw` | 0.0% | 0 | Salario sin procesar (sin datos) |

---

### 8️⃣ DETALLES (detalles)
Detalles adicionales de la oferta

| Variable | Completitud | Valores Únicos | Descripción |
|----------|-------------|----------------|-------------|
| `detalles.cantidad_vacantes` | 18.3% | 5 | Cantidad de vacantes (1-15) |
| `detalles.area_trabajo` | 13.0% | 11 | Área de trabajo |
| `detalles.apto_discapacitado` | 18.3% | 2 | Apto para discapacitados (0/1) |
| `detalles.confidencial` | 18.3% | 2 | Oferta confidencial (0/1) |
| `detalles.nivel_puesto` | 0.0% | 0 | Nivel del puesto (sin datos) |
| `detalles.subarea` | 0.0% | 0 | Subárea (sin datos) |

---

### 9️⃣ CLASIFICACIÓN ESCO (clasificacion_esco)
Clasificación según estándar europeo de ocupaciones

| Variable | Completitud | Valores Únicos | Descripción |
|----------|-------------|----------------|-------------|
| `clasificacion_esco.habilidades_esco` | 66.0% | 1 | Habilidades ESCO (array vacío) |
| `clasificacion_esco.ocupacion_esco_code` | 0.0% | 0 | Código ESCO (sin datos) |
| `clasificacion_esco.ocupacion_esco_label` | 0.0% | 0 | Etiqueta ESCO (sin datos) |
| `clasificacion_esco.ocupacion_esco_uri` | 0.0% | 0 | URI ESCO (sin datos) |
| `clasificacion_esco.ocupacion_esco_codigo` | 0.0% | 0 | Código ESCO alt (sin datos) |
| `clasificacion_esco.ocupacion_esco_titulo` | 0.0% | 0 | Título ESCO (sin datos) |
| `clasificacion_esco.isco_code` | 0.0% | 0 | Código ISCO (sin datos) |
| `clasificacion_esco.isco_label` | 0.0% | 0 | Etiqueta ISCO (sin datos) |
| `clasificacion_esco.similarity_score` | 0.0% | 0 | Score de similitud (sin datos) |
| `clasificacion_esco.confidence_score` | 0.0% | 0 | Score de confianza (sin datos) |
| `clasificacion_esco.skills` | 0.0% | 0 | Habilidades (sin datos) |
| `clasificacion_esco.matching_method` | 0.0% | 0 | Método de matching (sin datos) |
| `clasificacion_esco.matching_timestamp` | 0.0% | 0 | Timestamp matching (sin datos) |

---

### 🔟 CONDICIONES (condiciones)
Condiciones laborales del puesto

| Variable | Completitud | Valores Únicos | Descripción |
|----------|-------------|----------------|-------------|
| `condiciones.tipo_contrato` | 6.7% | 5 | Tipo de contrato (fulltime/parttime/etc) |
| `condiciones.nivel_jerarquico` | 0.0% | 0 | Nivel jerárquico (sin datos) |
| `condiciones.rango_salarial` | 0.0% | 0 | Rango salarial (sin datos) |
| `condiciones.beneficios` | 0.0% | 0 | Beneficios (sin datos) |

---

### 1️⃣1️⃣ DESCRIPCIÓN (descripcion)
Descripción extendida de la oferta

| Variable | Completitud | Valores Únicos | Descripción |
|----------|-------------|----------------|-------------|
| `descripcion.descripcion_completa` | 8.7% | 98 | Descripción completa del puesto |
| `descripcion.responsabilidades` | 0.0% | 0 | Responsabilidades (sin datos) |
| `descripcion.requisitos_deseables` | 0.0% | 0 | Requisitos deseables (sin datos) |

---

### 1️⃣2️⃣ ESPECÍFICOS DE FUENTE (source_specific)
Variables específicas de cada portal

| Variable | Completitud | Valores Únicos | Descripción |
|----------|-------------|----------------|-------------|
| `source_specific` | 18.3% | 2 | Objeto con datos específicos de la fuente |
| `source_specific.empresa_rating` | 37.0% | 15 | Rating de la empresa (0.0-5.0) |
| `source_specific.fecha_publicacion_raw` | 66.0% | 31 | Fecha publicación raw de la fuente |
| `source_specific.url_relativa` | 66.0% | 763 | URL relativa de la oferta |
| `source_specific.company_industry` | 2.4% | 8 | Industria de la empresa (LinkedIn) |
| `source_specific.company_num_employees` | 6.1% | 7 | Número de empleados (LinkedIn) |
| `source_specific.company_revenue` | 5.4% | 7 | Ingresos de la empresa (LinkedIn) |
| `source_specific.search_term_usado` | 7.1% | 3 | Término de búsqueda usado |
| `source_specific.job_function` | 0.0% | 0 | Función laboral (sin datos) |
| `source_specific.listing_type` | 0.0% | 0 | Tipo de listado (sin datos) |
| `source_specific.work_from_home_type` | 0.0% | 0 | Tipo de trabajo remoto (sin datos) |

---

## 📈 RESUMEN ESTADÍSTICO

### Variables con Completitud > 90% (ALTA CALIDAD)
- ✅ `_metadata.source` - 100%
- ✅ `_metadata.source_id` - 100%
- ✅ `_metadata.url_oferta` - 100%
- ✅ `informacion_basica.titulo` - 100%
- ✅ `informacion_basica.empresa` - 92.9%
- ✅ `ubicacion.pais` - 100%
- ✅ `ubicacion.provincia` - 96.1%
- ✅ `ubicacion.ciudad` - 96.1%
- ✅ `ubicacion.ubicacion_raw` - 96.1%
- ✅ `fechas.fecha_publicacion` - 98.2%
- ✅ `Fecha_final` - 100%
- ✅ `Periodo` - 100%

### Variables con Completitud 50-90% (MEDIA CALIDAD)
- ⚠️ `_metadata.fecha_scraping` - 81.7%
- ⚠️ `_metadata.version_schema` - 81.7%
- ⚠️ `informacion_basica.empresa_validada` - 81.7%
- ⚠️ `informacion_basica.empresa_url` - 74.7%
- ⚠️ `requisitos.idiomas` - 66.0%
- ⚠️ `requisitos.habilidades` - 66.0%
- ⚠️ `compensacion.mostrar_salario` - 66.0%
- ⚠️ `compensacion.beneficios` - 66.0%
- ⚠️ `source_specific.fecha_publicacion_raw` - 66.0%
- ⚠️ `source_specific.url_relativa` - 66.0%
- ⚠️ `clasificacion_esco.habilidades_esco` - 66.0%

### Variables con Completitud < 50% (BAJA CALIDAD)
- ❌ 50+ variables con completitud menor al 50%
- ❌ 30+ variables completamente vacías (0%)

### Top 10 Ciudades con más ofertas
1. Buenos Aires
2. CABA
3. Córdoba
4. Rosario
5. Mendoza
6. La Plata
7. Mar del Plata
8. Neuquén
9. Salta
10. Tucumán

### Top 5 Fuentes de Scraping
1. **computrabajo** - 763 ofertas (66.0%)
2. **bumeran** - 150 ofertas (13.0%)
3. **indeed** - 100 ofertas (8.7%)
4. **linkedin** - 82 ofertas (7.1%)
5. **zonajobs** - 61 ofertas (5.3%)

---

## 🎯 RECOMENDACIONES PARA USO DE DATOS

### ✅ Variables Recomendadas para Análisis Principal
1. `informacion_basica.titulo` - 100% completa
2. `informacion_basica.empresa` - 92.9% completa
3. `ubicacion.provincia` - 96.1% completa
4. `ubicacion.ciudad` - 96.1% completa
5. `fechas.fecha_publicacion` / `Periodo` - 100% completa
6. `_metadata.source` - 100% completa
7. `modalidad.modalidad_trabajo` - 42.3% completa

### ⚠️ Variables con Potencial pero Incompletas
1. `modalidad.tipo_trabajo` - Solo 18.3% completa
2. `detalles.cantidad_vacantes` - Solo 18.3% completa
3. `source_specific.empresa_rating` - Solo 37.0% completa
4. `condiciones.tipo_contrato` - Solo 6.7% completa

### ❌ Variables No Utilizables (0% completitud)
- Toda la sección de requisitos detallados
- Clasificación ESCO completa
- Información salarial
- Códigos postales
- Fechas de cierre/inicio

---

## 💡 OPORTUNIDADES DE MEJORA

### 1. Enriquecimiento de Datos
- Completar `clasificacion_esco.*` mediante procesamiento de lenguaje natural
- Extraer requisitos de las descripciones
- Normalizar nombres de empresas

### 2. Calidad de Datos
- Validar provincias y ciudades contra nomenclador oficial
- Normalizar modalidades de trabajo
- Eliminar duplicados por `_metadata.unified_id`

### 3. Nuevas Variables Calculadas
- Edad de la oferta (días desde publicación)
- Categorización automática de títulos
- Detección de palabras clave en descripciones
- Scoring de calidad por fuente

---

**Última actualización:** 24/10/2025
