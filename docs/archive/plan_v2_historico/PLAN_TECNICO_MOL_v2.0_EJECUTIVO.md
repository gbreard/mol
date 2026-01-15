# PLAN TÉCNICO: Monitor de Ofertas Laborales (MOL) v2.0

**Versión**: 2.0
**Fecha**: Noviembre 2025
**Autor**: Equipo OEDE
**Estado**: Planificación

---

## RESUMEN EJECUTIVO

El Monitor de Ofertas Laborales (MOL) actual procesa diariamente entre 2,500 y 5,000 ofertas de empleo de plataformas como Bumeran, extrayendo información estructurada y clasificándola según la ontología ESCO (European Skills, Competences, Qualifications and Occupations).

**Situación actual**: El sistema funciona pero tiene limitaciones importantes en la clasificación de habilidades, normalización territorial y capacidades de análisis.

**Objetivo v2.0**: Mejorar la calidad de los datos, ampliar las capacidades analíticas y ofrecer dashboards más potentes para análisis del mercado laboral argentino.

**Impacto esperado**:
- **+11.6%** en calidad de extracción de datos (quality score)
- **+31%** en confianza de clasificación ESCO (confidence score)
- **+98%** de cobertura en clasificación ocupacional
- **Nuevas capacidades**: filtros territoriales, análisis por tipo de contrato, búsqueda en árbol de ocupaciones

---

## TABLA DE CONTENIDOS

1. [Contexto y Situación Actual](#1-contexto-y-situación-actual)
2. [Fase 1: Enriquecimiento de la Ontología ESCO](#2-fase-1-enriquecimiento-de-la-ontología-esco)
3. [Fase 2: Mejoras en el Pipeline de Datos](#3-fase-2-mejoras-en-el-pipeline-de-datos)
4. [Fase 3: Rediseño del Dashboard Público (Shiny)](#4-fase-3-rediseño-del-dashboard-público-shiny)
5. [Fase 4: Mejoras en Dashboard Operativo (Plotly)](#5-fase-4-mejoras-en-dashboard-operativo-plotly)
6. [Fase 5: Validación y Control de Calidad](#6-fase-5-validación-y-control-de-calidad)
7. [Cronograma y Recursos](#7-cronograma-y-recursos)
8. [Anexos](#8-anexos)

---

## 1. CONTEXTO Y SITUACIÓN ACTUAL

### 1.1 ¿Cómo funciona el sistema actual?

El MOL opera en 5 etapas consecutivas:

```
ETAPA 1: SCRAPING
Plataformas web → Sistema MOL
• Extrae ofertas de Bumeran (HTML/JSON)
• ~2,500-5,000 ofertas/día
• Resultado: Texto crudo de las ofertas

↓

ETAPA 2: CONSOLIDACIÓN
Limpieza y deduplicación
• Elimina ofertas duplicadas
• Normaliza formato de texto
• Resultado: Ofertas únicas y limpias

↓

ETAPA 3: EXTRACCIÓN NLP (v5.1 actual)
Procesamiento con Inteligencia Artificial
• Extrae: experiencia, educación, habilidades, salario
• Usa modelo Ollama llama3.1 (8B parámetros)
• Resultado: Datos estructurados

↓

ETAPA 4: CLASIFICACIÓN ESCO
Matching con ontología europea
• Asigna código de ocupación (ej: ISCO 2513 = Desarrollador web)
• Clasifica habilidades requeridas
• Resultado: Oferta clasificada según estándar ESCO

↓

ETAPA 5: PRODUCTOS (Dashboards)
Visualización y análisis
• Dashboard Plotly (control operativo interno)
• Dashboard Shiny (análisis público)
• Resultado: Insights sobre mercado laboral
```

### 1.2 ¿Qué es ESCO y por qué lo usamos?

**ESCO** (European Skills, Competences, Qualifications and Occupations) es una clasificación multilingüe desarrollada por la Comisión Europea que funciona como un "diccionario universal" del mercado laboral.

**Contenido de ESCO v1.2.0:**
- **3,137 ocupaciones** (ej: Desarrollador web, Contador público, Gerente de ventas)
- **14,279 habilidades** (ej: SQL, Liderazgo, Comunicación efectiva)
- **240,000 relaciones** entre ocupaciones y habilidades

**¿Por qué ESCO?**
1. **Estandarización**: Permite comparar el mercado laboral argentino con Europa y otros países
2. **Estructura jerárquica**: Usa ISCO-08 (4 niveles de clasificación ocupacional)
3. **Multilingüe**: Disponible en español y 26 idiomas más
4. **Gratuito y mantenido**: Actualizado anualmente por la UE

**Ejemplo práctico:**

Una oferta de Bumeran dice: *"Buscamos programador con conocimientos de bases de datos y Python"*

El sistema ESCO la clasifica como:
- **Ocupación**: ISCO 2513 "Desarrolladores web y multimedia"
- **Habilidades esenciales**: SQL (conocimiento técnico), Python (conocimiento técnico)
- **Habilidades opcionales**: Liderazgo (competencia), Trabajo en equipo (competencia)

### 1.3 ¿Qué problemas tiene el sistema actual?

Identificamos 3 brechas principales:

#### **BRECHA 1: Información ESCO incompleta**

**Problema:** Tenemos las ocupaciones y habilidades de ESCO, pero falta la información más valiosa: ¿qué habilidades requiere cada ocupación?

| Componente ESCO | Estado Actual | Registros Esperados | Cobertura |
|----------------|---------------|---------------------|-----------|
| Ocupaciones | ✅ Completo | 3,137 | 100% |
| Habilidades | ✅ Completo | 14,279 | 100% |
| **Asociaciones ocupación-skill** | ❌ **VACÍO** | **240,000** | **0%** |
| Jerarquía ISCO | ⚠️ Parcial | 4 niveles | 60% |

**Consecuencia:** La clasificación actual es "a ciegas" - el sistema no sabe qué habilidades corresponden a cada ocupación.

**Ejemplo del problema:**

```
Oferta: "Desarrollador Full Stack - Requiere: Python, React, SQL"

MATCHING ACTUAL (sin asociaciones):
→ Compara el título "Desarrollador Full Stack" con nombres de ocupaciones ESCO
→ Resultado: ISCO 2513 "Desarrollador web" (confidence: 65%)
→ No usa las habilidades para validar

MATCHING MEJORADO (con asociaciones):
→ Identifica habilidades: Python, React, SQL
→ Busca ocupaciones que requieren esas habilidades
→ ISCO 2513 requiere Python (esencial) + SQL (esencial) + React (opcional)
→ Resultado: ISCO 2513 "Desarrollador web" (confidence: 90%)
```

**Impacto medido en A/B test (50 ofertas):**
- Cobertura: 95% → 98% (+3%)
- Confidence promedio: 0.65 → 0.90 (+38%)

#### **BRECHA 2: No distinguimos Conocimientos vs Competencias**

**Problema:** Mezclamos todo como "habilidades" cuando en realidad hay 2 tipos distintos:

**Conocimientos** (saberes técnicos):
- SQL, Python, contabilidad, normativa laboral
- Específicos de sectores o tecnologías
- Se aprenden con formación técnica

**Competencias** (habilidades blandas):
- Liderazgo, comunicación, trabajo en equipo, adaptabilidad
- Transversales a múltiples ocupaciones
- Se desarrollan con experiencia

**¿Por qué importa esta distinción?**

Los analistas del mercado laboral necesitan responder preguntas como:
- ¿Qué conocimientos técnicos son más demandados en el sector IT?
- ¿Qué competencias blandas requieren los puestos gerenciales?
- ¿Cómo evolucionan los requerimientos de conocimientos vs competencias?

**Actualmente NO podemos responder estas preguntas porque todo está mezclado.**

**Solución propuesta:** Clasificación automática en 2 categorías usando 3 criterios:

1. **Criterio 1 - Tipo declarado en ESCO** (75% de casos)
   - Si ESCO dice "knowledge" → Conocimiento
   - Si ESCO dice "skill" → Revisar criterio 2

2. **Criterio 2 - Alcance de la habilidad** (20% de casos)
   - Si es "transversal" o "cross-sector" → Competencia (soft skill)
   - Si es "sector-specific" o "occupation-specific" → Conocimiento (técnico)

3. **Criterio 3 - Palabras clave** (5% de casos ambiguos)
   - Keywords competencias: "comunicación", "liderazgo", "creatividad"
   - Keywords conocimientos: "programar", "base de datos", "metodología"

**Ejemplos de clasificación:**

| Habilidad | Tipo ESCO | Alcance | Clasificación Final | Confianza |
|-----------|-----------|---------|-------------------|-----------|
| SQL | knowledge | cross-sector | **Conocimiento** | 100% |
| liderazgo de equipos | skill | transversal | **Competencia** | 95% |
| programación en Python | skill | sector-specific | **Conocimiento** | 90% |
| comunicación efectiva | skill | transversal | **Competencia** | 95% |
| normativa laboral argentina | knowledge | occupation-specific | **Conocimiento** | 100% |

**Meta:** 90% de habilidades clasificadas con confianza >= 85%

#### **BRECHA 3: Datos faltantes en las ofertas**

**Problema:** El sistema actual no extrae campos importantes que aparecen en las ofertas.

**Campos que faltan:**

| Campo Faltante | ¿Por qué importa? | Ejemplo en oferta real |
|---------------|-------------------|----------------------|
| **Edad requerida** | Detectar discriminación etaria | "Buscamos desarrollador de 25 a 35 años" |
| **Ubicación requerida** | Distinguir remoto vs presencial | "EXCLUYENTE vivir en CABA" vs "100% remoto" |
| **Tipo de contrato** | Analizar estabilidad laboral | "Relación de dependencia" vs "Contrato 3 meses" |
| **Provincia normalizada** | Filtros territoriales precisos | "Bs.As." → Buenos Aires (código INDEC 06) |
| **Localidad normalizada** | Análisis por ciudad | "Bahia Blanca" → Bahía Blanca (código 060007) |

**Consecuencias actuales:**

1. **No podemos filtrar por tipo de contrato** en el dashboard
   - ¿Cuántas ofertas son indefinidas vs plazo fijo?
   - ¿Qué ocupaciones ofrecen más estabilidad?

2. **No podemos hacer mapas territoriales precisos**
   - Las ubicaciones están en texto libre: "CABA", "Capital Federal", "Buenos Aires", "Bs.As."
   - Imposible agrupar correctamente por provincia

3. **No podemos analizar requisitos de presencialidad**
   - ¿Cuántas ofertas son 100% remotas?
   - ¿Qué provincias tienen más ofertas locales?

4. **No detectamos discriminación etaria**
   - Requisito de edad aparece en ~30% de ofertas
   - Actualmente no se captura ni se puede analizar

**Solución:** NLP v6.0 extraerá estos 4 campos adicionales.

#### **BRECHA 4: Ubicaciones sin normalizar**

**Problema:** Las ofertas mencionan ubicaciones en texto libre, con múltiples variantes:

```
"CABA"
"Capital Federal"
"Ciudad de Buenos Aires"
"Bs.As. - Belgrano"
"Buenos Aires (Capital)"
```

Todas se refieren al mismo lugar, pero el sistema las trata como distintas.

**Solución: Normalización territorial con códigos INDEC**

El INDEC (Instituto Nacional de Estadísticas) mantiene una codificación oficial:
- **24 provincias** (código 2 dígitos)
- **~4,000 localidades** (código 6 dígitos)

**Proceso de normalización:**

```
Texto libre en oferta → Fuzzy matching → Código INDEC + Nombre oficial

EJEMPLOS:
"CABA - Belgrano" → Código: 02 | Provincia: Ciudad de Bs. As.
"Bahia Blanca, Bs As" → Código: 060007 | Localidad: Bahía Blanca, Provincia: 06 (Buenos Aires)
"Cordoba Capital" → Código: 140007 | Localidad: Córdoba, Provincia: 14 (Córdoba)
```

**Beneficios:**
1. Filtros territoriales precisos en dashboards
2. Mapas coropléticos (provincias coloreadas según cantidad de ofertas)
3. Análisis por región geográfica
4. Comparaciones entre provincias y localidades

### 1.4 Situación de los Dashboards

**Actualmente tenemos 2 dashboards con propósitos diferentes:**

#### **Dashboard Plotly v4 (Operativo - Interno)**
- **URL:** http://localhost:8052
- **Audiencia:** Equipo técnico OEDE
- **Propósito:** Monitorear el funcionamiento del sistema
- **5 tabs actuales:**
  1. Overview - Métricas generales
  2. Keywords - Análisis de términos frecuentes
  3. Calidad - Scores de parseo
  4. Alertas - Errores y warnings
  5. Calidad de Parseo NLP - Evaluación del modelo

**Estado:** Funciona bien, solo necesita agregar tab de monitoreo de pipeline completo

#### **Dashboard Shiny R v2.4 (Público - Análisis)**
- **Audiencia:** Analistas, investigadores, público en general
- **Propósito:** Análisis del mercado laboral con clasificación ESCO
- **6 tabs actuales:**
  - Overview General
  - Análisis Territorial
  - Habilidades
  - Ocupaciones ESCO
  - Tendencias
  - Datos Crudos

**Problemas:**
1. Filtros globales insuficientes (falta: tipo de contrato, edad, modalidad remoto/presencial)
2. No hay búsqueda por ocupación
3. No hay navegación por árbol ISCO
4. Organización de tabs confusa (6 tabs vs 3 paneles temáticos sería más claro)
5. No distingue conocimientos vs competencias

**Rediseño propuesto:** 3 paneles temáticos con 5 filtros globales

### 1.5 Base de datos actual

**SQLite: bumeran_scraping.db (28 MB)**
- **5,479 ofertas activas**
- **32 tablas** (ofertas, NLP history, ESCO matching, keywords, etc.)
- **Tablas ESCO:**
  - `esco_occupations`: 3,045 registros ✅
  - `esco_skills`: 14,247 registros ✅
  - `esco_occupation_skill_associations`: **0 registros** ❌ (VACÍA)
  - `esco_isco_hierarchy`: Parcialmente poblada ⚠️

**Formato de salida actual: CSV v1.0**
- **48 columnas**
- **268 ofertas** (muestra para dashboard Shiny)
- Encoding: UTF-8

---

## 2. FASE 1: ENRIQUECIMIENTO DE LA ONTOLOGÍA ESCO

**Objetivo:** Poblar las 240,000 relaciones faltantes entre ocupaciones y habilidades.

**Duración estimada:** 2 semanas

### 2.1 ¿Dónde está la información faltante?

La información completa de ESCO está en un archivo RDF (Resource Description Framework):

**Archivo:** `esco-v1.2.0.rdf`
**Ubicación:** D:\Trabajos en PY\EPH-ESCO\01_datos_originales\Tablas_esco\Data\
**Tamaño:** 1.35 GB
**Formato:** XML con estructura semántica

**¿Qué contiene?**
- Todas las ocupaciones con descripciones completas
- Todas las habilidades con clasificaciones
- **Las 240K asociaciones** ocupación-habilidad (esenciales y opcionales)
- Jerarquías ISCO completas (4 niveles)
- Traducciones en 27 idiomas

### 2.2 Estrategia de extracción

**Decisión arquitectónica clave:** Procesar el RDF **UNA SOLA VEZ** y poblar la base de datos SQLite.

**¿Por qué no consultar el RDF en tiempo real?**
- Es demasiado grande (1.35 GB)
- Requeriría un servidor especializado (triple-store)
- Las consultas serían lentas
- ESCO se actualiza solo 1 vez al año

**Flujo de extracción:**

```
┌─────────────────────────┐
│  esco-v1.2.0.rdf        │
│  (1.35 GB)              │
│  Archivo único          │
└────────────┬────────────┘
             │
             │ Procesar UNA VEZ
             │ (Tarda ~30 minutos)
             ↓
┌─────────────────────────┐
│  bumeran_scraping.db    │
│  Tablas SQLite          │
│                         │
│  • esco_occupations     │ ← 3,137 ocupaciones
│  • esco_skills          │ ← 14,279 habilidades
│  • esco_associations    │ ← 240,000 relaciones ⭐ NUEVO
│  • esco_isco_hierarchy  │ ← 4 niveles jerárquicos
│                         │
│  Total: ~50 MB          │
└─────────────────────────┘
             │
             │ Consultas rápidas
             │ en producción
             ↓
      Sistema MOL
```

### 2.3 ¿Qué información extraeremos?

#### **Extracción 1: Ocupaciones (3,137 registros)**

De cada ocupación obtendremos:

| Campo | Descripción | Ejemplo |
|-------|-------------|---------|
| URI | Identificador único | http://data.europa.eu/esco/occupation/114e1eff-... |
| Nombre (ES) | Título en español | "desarrollador web y multimedia" |
| Código ISCO | Clasificación 4 dígitos | 2513 |
| Descripción (ES) | Qué hace esta ocupación | "Los desarrolladores web diseñan, codifican..." |
| Variantes | Nombres alternativos | ["programador web", "web developer"] |

#### **Extracción 2: Habilidades (14,279 registros)**

De cada habilidad obtendremos:

| Campo | Descripción | Ejemplo |
|-------|-------------|---------|
| URI | Identificador único | http://data.europa.eu/esco/skill/S1.2.3 |
| Nombre (ES) | Título en español | "SQL" |
| Tipo | knowledge / skill | "knowledge" |
| Alcance | transversal / sector / ocupación | "cross-sector" |
| Descripción (ES) | Qué es esta habilidad | "Lenguaje de consulta estructurada..." |

#### **Extracción 3: Asociaciones (240,000 registros)** ⭐ CLAVE

Esta es la información MÁS VALIOSA que nos falta:

| Campo | Descripción | Ejemplo |
|-------|-------------|---------|
| Ocupación | URI de la ocupación | http://.../occupation/114e1eff-... (Desarrollador web) |
| Habilidad | URI de la habilidad | http://.../skill/S1.2.3 (SQL) |
| Tipo de relación | Esencial u opcional | "essential" |

**Ejemplo concreto: Ocupación "Desarrollador web" (ISCO 2513)**

| Habilidad | Nombre | Tipo de relación |
|-----------|--------|------------------|
| SQL | Lenguaje de consulta | **Esencial** |
| JavaScript | Lenguaje de programación | **Esencial** |
| HTML | Lenguaje de marcado | **Esencial** |
| Python | Lenguaje de programación | Opcional |
| Trabajo en equipo | Competencia blanda | Opcional |
| Git | Control de versiones | **Esencial** |
| Docker | Contenedores | Opcional |

Con esta información, cuando una oferta menciona "SQL + JavaScript + HTML", el sistema podrá decir con alta confianza: "Esta es una oferta de Desarrollador web" (porque cumple con las 3 habilidades esenciales).

#### **Extracción 4: Jerarquía ISCO (4 niveles)**

ISCO-08 organiza ocupaciones en 4 niveles jerárquicos:

```
Nivel 1 (Gran Grupo)
  └─ Nivel 2 (Subgrupo)
      └─ Nivel 3 (Grupo primario)
          └─ Nivel 4 (Ocupación específica)
```

**Ejemplo: Desarrollador web**

```
2 - Profesionales científicos e intelectuales          [Nivel 1]
└─ 25 - Profesionales de tecnología de la información  [Nivel 2]
    └─ 251 - Desarrolladores de software y analistas   [Nivel 3]
        └─ 2513 - Desarrolladores web y multimedia     [Nivel 4]
```

**Beneficio:** El dashboard podrá mostrar un árbol navegable donde los analistas puedan:
1. Explorar la jerarquía completa
2. Seleccionar un nivel completo (ej: "todos los profesionales TIC")
3. Ver cantidad de ofertas en cada rama
4. Comparar entre grupos ocupacionales

### 2.4 Clasificación de Conocimientos vs Competencias

Una vez extraídas las 14,279 habilidades, las clasificaremos en 2 categorías.

**Método de 3 niveles (de más confiable a menos):**

```
Para cada habilidad:

┌─────────────────────────────────────┐
│ NIVEL 1: Revisar tipo declarado    │ ← 75% de casos
│ Si tipo = "knowledge"               │
│   → CONOCIMIENTO (confianza 100%)   │
└──────────────┬──────────────────────┘
               │
               ↓ Si tipo = "skill", revisar alcance
               │
┌──────────────┴──────────────────────┐
│ NIVEL 2: Revisar alcance            │ ← 20% de casos
│ Si alcance = "transversal"          │
│   → COMPETENCIA (confianza 95%)     │
│ Si alcance = "sector-specific"      │
│   → CONOCIMIENTO (confianza 90%)    │
└──────────────┬──────────────────────┘
               │
               ↓ Si aún es ambiguo
               │
┌──────────────┴──────────────────────┐
│ NIVEL 3: Buscar palabras clave     │ ← 5% de casos
│ Si contiene: "comunicación",        │
│ "liderazgo", "creatividad"          │
│   → COMPETENCIA (confianza 75%)     │
│ Si contiene: "programar", "base de  │
│ datos", "normativa"                 │
│   → CONOCIMIENTO (confianza 75%)    │
│ Si ninguno coincide:                │
│   → CONOCIMIENTO por defecto (50%)  │
└─────────────────────────────────────┘
```

**Resultado en la base de datos:**

Cada habilidad tendrá 3 campos nuevos:

| Habilidad | skill_category | classification_method | classification_confidence |
|-----------|---------------|----------------------|---------------------------|
| SQL | conocimiento | nivel_1_tipo | 1.00 |
| liderazgo | competencia | nivel_2_reusability | 0.95 |
| Python programming | conocimiento | nivel_2_reusability | 0.90 |
| comunicación oral | competencia | nivel_2_reusability | 0.95 |
| contabilidad | conocimiento | nivel_1_tipo | 1.00 |

### 2.5 Re-matching de ofertas existentes

Una vez que tengamos las 240K asociaciones, vamos a **volver a clasificar** las 5,479 ofertas existentes.

**¿Por qué re-procesar?**

Las ofertas actuales fueron clasificadas "a ciegas" (sin saber qué habilidades requiere cada ocupación). Ahora que tendremos esa información, podemos mejorar significativamente la clasificación.

**Mejora esperada (validada con A/B test en 50 ofertas):**

| Métrica | Sistema Actual (v5.1) | Sistema Mejorado (v6.0) | Mejora |
|---------|----------------------|------------------------|--------|
| Ofertas clasificadas | 95% (4,705/5,479) | 98% (5,369/5,479) | +3% |
| Confidence promedio | 0.65 | 0.90 | **+38%** |
| Quality score (campos completos) | 7.89 | 8.81 | +11.6% |

**Ejemplo de mejora en una oferta real:**

```
OFERTA ID: 2162282
Título: "Desarrollador Full Stack Senior"
Skills extraídos por NLP: Python, JavaScript, React, SQL, Git

CLASIFICACIÓN ANTERIOR (sin asociaciones):
• Método: Fuzzy matching del título
• Resultado: ISCO 2513 "Desarrolladores web"
• Confidence: 0.65
• Justificación: El título es similar a "desarrollador web"

CLASIFICACIÓN NUEVA (con asociaciones):
• Método: Matching de skills contra asociaciones
• Ocupaciones candidatas analizadas:
  - ISCO 2513 "Desarrolladores web":
    · 4 skills esenciales matchean (JavaScript, SQL, Git, HTML implícito en React)
    · 1 skill opcional matchea (Python)
    · Score: 9.0

  - ISCO 2512 "Desarrolladores de software":
    · 3 skills esenciales matchean
    · 2 skills opcionales matchean
    · Score: 8.0

• Resultado: ISCO 2513 "Desarrolladores web"
• Confidence: 0.90 (+38%)
• Justificación: Cumple con 4/5 habilidades esenciales de esta ocupación
```

---

## 3. FASE 2: MEJORAS EN EL PIPELINE DE DATOS

**Objetivo:** Extraer 4 campos adicionales y normalizar ubicaciones.

**Duración estimada:** 2 semanas

### 3.1 NLP v6.0 - Nuevos campos

Vamos a mejorar el modelo de extracción para capturar información que actualmente se pierde.

**Campos actuales de NLP v5.1:**
- Experiencia mínima/máxima (años)
- Nivel educativo (secundario/terciario/universitario/posgrado)
- Estado educativo (en curso/completo)
- Carrera específica
- Habilidades técnicas (lista)
- Habilidades blandas (lista)
- Salario mínimo/máximo
- Jornada laboral (completa/parcial)

**Campos NUEVOS en NLP v6.0:**
1. **Edad mínima requerida**
2. **Edad máxima requerida**
3. **Ubicación requerida** (true/false: ¿requiere presencialidad en la ubicación?)
4. **Tipo de permanencia** (indefinido/plazo_fijo/temporal/pasantia)

### 3.2 Ejemplos de extracción

#### **Ejemplo 1: Oferta con rango etario**

```
TEXTO DE LA OFERTA:
"Buscamos Desarrollador Full Stack para incorporación inmediata.

Requisitos:
• 3-5 años de experiencia en Python y Django
• Edad: 25 a 40 años
• Relación de dependencia
• Jornada completa
• Modalidad: 100% remoto"

EXTRACCIÓN NLP v6.0:
{
  "experiencia_min_anios": 3,
  "experiencia_max_anios": 5,
  "edad_min": 25,                    ← NUEVO
  "edad_max": 40,                    ← NUEVO
  "ubicacion_required": false,       ← NUEVO (remoto = no requiere ubicación)
  "permanencia_tipo": "indefinido",  ← NUEVO (relación de dependencia)
  "jornada_laboral": "completa",
  "skills_tecnicas": ["Python", "Django"],
  ...
}
```

#### **Ejemplo 2: Oferta con ubicación requerida**

```
TEXTO DE LA OFERTA:
"Analista Contable - CABA (Belgrano)

EXCLUYENTE: vivir en CABA o GBA Norte
Presentismo en oficina de lunes a viernes
Experiencia mínima: 2 años
Contador Público recibido o próximo a recibirse"

EXTRACCIÓN NLP v6.0:
{
  "experiencia_min_anios": 2,
  "nivel_educativo": "universitario",
  "estado_educativo": "completo",
  "carrera_especifica": "Contador Público",
  "edad_min": null,                  ← No especifica
  "edad_max": null,
  "ubicacion_required": true,        ← NUEVO (EXCLUYENTE vivir en CABA)
  "permanencia_tipo": null,          ← No especifica
  "jornada_laboral": "completa",
  ...
}
```

#### **Ejemplo 3: Oferta con contrato temporal**

```
TEXTO DE LA OFERTA:
"Reemplazo por licencia - Proyecto 3 meses

Analista de Marketing Digital
Contrato por tiempo determinado - renovable según performance
Jornada completa en oficina Microcentro"

EXTRACCIÓN NLP v6.0:
{
  "experiencia_min_anios": null,
  "edad_min": null,
  "edad_max": null,
  "ubicacion_required": true,        ← NUEVO (jornada en oficina)
  "permanencia_tipo": "temporal",    ← NUEVO (proyecto 3 meses, reemplazo)
  "jornada_laboral": "completa",
  ...
}
```

### 3.3 Detección de tipo de contrato

El campo "permanencia_tipo" se detecta con 2 métodos combinados:

**Método 1: Extracción directa por NLP** (prioridad 1)

El modelo de IA analiza el contexto y extrae directamente el tipo.

**Método 2: Palabras clave** (fallback si NLP no detecta)

| Categoría | Palabras clave | Ejemplo |
|-----------|---------------|---------|
| **indefinido** | "relación de dependencia", "contrato indefinido", "efectivo", "planilla permanente" | "Incorporación efectiva, relación de dependencia indeterminada" |
| **plazo_fijo** | "plazo fijo", "contrato determinado", "6 meses", "1 año", "renovable" | "Contrato por 6 meses renovable según desempeño" |
| **temporal** | "proyecto", "reemplazo", "temporal", "eventual", "campaña", "freelance" | "Reemplazo por licencia - Proyecto de migración 3 meses" |
| **pasantia** | "pasantía", "pasante", "beca", "práctica profesional", "trainee" | "Buscamos pasante de Sistemas para sumar al equipo" |

### 3.4 Normalización territorial INDEC

**Objetivo:** Convertir texto libre en ubicaciones a códigos oficiales INDEC.

#### **¿Qué es el código INDEC?**

El INDEC (Instituto Nacional de Estadísticas y Censos) mantiene la codificación geográfica oficial de Argentina:

**Estructura:**
- **Provincia**: 2 dígitos (ej: 02 = CABA, 06 = Buenos Aires, 14 = Córdoba)
- **Localidad**: 6 dígitos (primeros 2 = provincia, siguientes 4 = localidad específica)

**Ejemplo:** Bahía Blanca
- Código provincia: **06** (Buenos Aires)
- Código localidad: **060007** (Bahía Blanca)

#### **Tablas de referencia**

Vamos a crear 2 tablas con la información oficial del INDEC:

**Tabla 1: Provincias (24 registros)**

| Código | Nombre Oficial | Variantes |
|--------|---------------|-----------|
| 02 | Ciudad de Bs. As. | ["CABA", "Capital Federal", "Buenos Aires (Capital)", "Ciudad Autónoma"] |
| 06 | Buenos Aires | ["Bs.As.", "Bs As", "BA", "Prov. Buenos Aires", "PBA"] |
| 14 | Córdoba | ["Cordoba", "Cba", "Prov. Córdoba"] |
| 82 | Santa Fe | ["Sta Fe", "Sta. Fe", "Prov. Santa Fe"] |

**Tabla 2: Localidades (~4,000 registros)**

| Código | Nombre Oficial | Provincia | Variantes |
|--------|---------------|-----------|-----------|
| 020007 | Comuna 1 | 02 | ["Retiro", "San Nicolás", "Puerto Madero", "C1"] |
| 060007 | Bahía Blanca | 06 | ["Bahia Blanca", "B. Blanca", "Bahia Bca"] |
| 140007 | Córdoba | 14 | ["Cordoba Capital", "Cba Capital"] |
| 820007 | Rosario | 82 | ["Rosario (Santa Fe)"] |

#### **Proceso de normalización**

```
Paso 1: Extraer ubicación de la oferta
"CABA - Belgrano"

Paso 2: Limpiar texto
"caba belgrano"

Paso 3: Fuzzy matching con localidades
• Comparar contra 4,000 localidades
• Calcular similitud (algoritmo RapidFuzz)
• Mejor match: "Comuna 1" (score: 88%)

Paso 4: Validar score
• Si score >= 85% → Aceptar localidad
• Si score < 85% → Buscar solo provincia

Paso 5: Resultado
{
  "provincia_codigo": "02",
  "provincia_nombre": "Ciudad de Bs. As.",
  "localidad_codigo": "020007",
  "localidad_nombre": "Comuna 1",
  "confidence": 0.88
}
```

#### **Ejemplos de normalización**

| Texto en oferta | Provincia | Localidad | Confidence |
|----------------|-----------|-----------|------------|
| "CABA - Belgrano" | 02 - Ciudad de Bs. As. | 020007 - Comuna 1 | 88% |
| "Bahia Blanca, Bs As" | 06 - Buenos Aires | 060007 - Bahía Blanca | 93% |
| "Cordoba Capital" | 14 - Córdoba | 140007 - Córdoba | 95% |
| "Rosario, Santa Fe" | 82 - Santa Fe | 820007 - Rosario | 97% |
| "Buenos Aires" | 06 - Buenos Aires | NULL (ambiguo) | 85% |
| "Remoto - Argentina" | NULL | NULL | 0% |

#### **Beneficios de la normalización**

1. **Filtros precisos en dashboards**
   - Dropdown con lista oficial de provincias
   - Segundo dropdown con localidades de la provincia seleccionada
   - No más "CABA" y "Capital Federal" como opciones separadas

2. **Mapas coropléticos**
   - Provincias coloreadas según cantidad de ofertas
   - Click en provincia → zoom a localidades

3. **Análisis geográfico**
   - Top 10 provincias con más ofertas
   - Top 10 localidades por provincia
   - Comparación regional (NOA, NEA, Centro, Cuyo, Patagonia)

4. **Datos limpios para exportar**
   - CSV con códigos INDEC
   - Compatible con otros sistemas del Estado
   - Interoperable con EPH, SIPA, etc.

### 3.5 Generación de CSV v2.0 enriquecido

El CSV actual tiene 48 columnas. El nuevo tendrá **65 columnas**.

**Columnas NUEVAS (17):**

**Del enriquecimiento ESCO (5):**
1. `esco_isco_hierarchy_level1` - Gran Grupo (ej: "2 - Profesionales científicos")
2. `esco_isco_hierarchy_level2` - Subgrupo (ej: "25 - Profesionales TIC")
3. `esco_essential_skills_count` - Cantidad de habilidades esenciales de esta ocupación
4. `esco_optional_skills_count` - Cantidad de habilidades opcionales
5. `esco_matching_confidence` - Score de confianza del matching (0-1)

**De NLP v6.0 (4):**
6. `edad_min` - Edad mínima requerida
7. `edad_max` - Edad máxima requerida
8. `ubicacion_required` - Requiere presencialidad (true/false)
9. `permanencia_tipo` - Tipo de contrato

**De normalización territorial INDEC (5):**
10. `provincia_codigo_indec` - Código oficial (2 dígitos)
11. `provincia_nombre_norm` - Nombre normalizado
12. `localidad_codigo_indec` - Código oficial (6 dígitos)
13. `localidad_nombre_norm` - Nombre normalizado
14. `ubicacion_norm_confidence` - Confianza de normalización (0-1)

**De clasificación de skills (3):**
15. `conocimientos_count` - Cantidad de conocimientos técnicos
16. `competencias_count` - Cantidad de competencias blandas
17. `skills_tecnicas_clasificadas` - JSON con categorización

**Ejemplo de fila del CSV v2.0:**

```
id: 2162282
titulo: "Desarrollador Full Stack Senior"
empresa: "TechCorp SA"
ubicacion_original: "CABA - Belgrano"
provincia_codigo_indec: "02"
provincia_nombre_norm: "Ciudad de Bs. As."
localidad_codigo_indec: "020007"
localidad_nombre_norm: "Comuna 1"
ubicacion_norm_confidence: 0.88

experiencia_min_anios: 3
experiencia_max_anios: 5
nivel_educativo: "universitario"
carrera_especifica: "Ingeniería en Sistemas"

edad_min: 25
edad_max: 40
ubicacion_required: false
permanencia_tipo: "indefinido"
jornada_laboral: "completa"

skills_tecnicas: ["Python", "Django", "React", "PostgreSQL", "Docker", "Git"]
soft_skills: ["liderazgo", "trabajo en equipo", "comunicación"]
conocimientos_count: 6
competencias_count: 3

esco_occupation_label: "desarrollador web"
esco_isco_code: "2513"
esco_isco_hierarchy_level1: "2 - Profesionales científicos e intelectuales"
esco_isco_hierarchy_level2: "25 - Profesionales TIC"
esco_matching_confidence: 0.92
esco_essential_skills_count: 15
esco_optional_skills_count: 8

fecha_publicacion: 2025-11-10
fecha_scraping: 2025-11-10
```

---

## 4. FASE 3: REDISEÑO DEL DASHBOARD PÚBLICO (SHINY)

**Objetivo:** Transformar el dashboard actual (6 tabs) en una interfaz más clara (3 paneles) con filtros globales potentes.

**Duración estimada:** 2 semanas

### 4.1 Problema con el diseño actual

**Dashboard actual (v2.4):**
- 6 tabs separados que fragmentan el análisis
- Filtros locales por tab (no se mantienen al cambiar)
- No hay búsqueda por ocupación
- No se puede filtrar por tipo de contrato
- No hay navegación por jerarquía ISCO
- Conocimientos y competencias mezclados

**Experiencia del usuario:**

```
Usuario: "Quiero ver ofertas de desarrolladores en CABA con contrato indefinido"

PROBLEMA CON DASHBOARD ACTUAL:
1. ¿Dónde busco? ¿Tab "Ocupaciones ESCO"? ¿"Análisis Territorial"?
2. Filtro por provincia en "Análisis Territorial"
3. Cambio al tab "Ocupaciones ESCO" → ❌ Se perdió el filtro de provincia
4. No hay filtro de tipo de contrato → ❌ Imposible hacer esta consulta
5. Frustración y abandono
```

### 4.2 Diseño propuesto: 3 paneles + 5 filtros globales

**Concepto:** Filtros que se aplican a TODOS los paneles + 3 vistas temáticas.

```
┌────────────────────────────────────────────────────────────────────┐
│ MONITOR DE OFERTAS LABORALES - ESCO                                │
├────────────────────────────────────────────────────────────────────┤
│                                                                     │
│ FILTROS GLOBALES (Sidebar izquierdo - siempre visible)            │
│                                                                     │
│ 📍 TERRITORIAL                                                      │
│    Provincia: [Todas ▼]                                            │
│    Localidad: [Todas ▼] (se activa al seleccionar provincia)      │
│                                                                     │
│ 📅 PERÍODO                                                          │
│    Agrupar por: [Mes ▼]                                            │
│    Desde: [01/01/2025]  Hasta: [31/12/2025]                       │
│                                                                     │
│ 📋 PERMANENCIA                                                      │
│    ☑ Indefinido                                                    │
│    ☑ Plazo fijo                                                    │
│    ☑ Temporal                                                      │
│    ☑ Pasantía                                                      │
│                                                                     │
│ 💼 OCUPACIÓN                                                        │
│    Buscar: [desarrollador...]                                      │
│    🌳 Árbol ISCO-08 (click para expandir)                          │
│      └─ 2 - Profesionales                                          │
│          └─ 25 - Prof. TIC (127 ofertas)                           │
│              ☑ 251 - Desarrolladores (89 ofertas)                  │
│                  ☑ 2513 - Dev. web (45 ofertas)                    │
│                                                                     │
│ 👤 EDAD REQUERIDA                                                   │
│    [18 ═══════●═══════ 65]  (slider)                              │
│                                                                     │
│ [APLICAR FILTROS]                                                  │
│                                                                     │
├────────────────────────────────────────────────────────────────────┤
│                                                                     │
│ PANELES PRINCIPALES (contenido derecho - cambia según tab)        │
│                                                                     │
│ [PANORAMA GENERAL] [REQUERIMIENTOS] [OFERTAS LABORALES]           │
└────────────────────────────────────────────────────────────────────┘
```

### 4.3 Panel 1: Panorama General

**Objetivo:** Vista rápida del mercado laboral según filtros activos.

**Contenido:**

```
┌─────────────────────────────────────────────────────────────────┐
│ INDICADORES CLAVE (Row 1)                                        │
│                                                                  │
│  ┏━━━━━━━━━━━┓  ┏━━━━━━━━━━━┓  ┏━━━━━━━━━━━┓  ┏━━━━━━━━━━━┓  │
│  ┃ 1,247     ┃  ┃ 18        ┃  ┃ 156       ┃  ┃ 87        ┃  │
│  ┃ OFERTAS   ┃  ┃ PROVINCIAS┃  ┃ OCUPACIONES┃  ┃ EMPRESAS  ┃  │
│  ┃ ACTIVAS   ┃  ┃ ACTIVAS   ┃  ┃ ESCO      ┃  ┃ PUBLICANDO┃  │
│  ┗━━━━━━━━━━━┛  ┗━━━━━━━━━━━┛  ┗━━━━━━━━━━━┛  ┗━━━━━━━━━━━┛  │
│                                                                  │
├─────────────────────────────────────────────────────────────────┤
│ EVOLUCIÓN TEMPORAL (Row 2 - izquierda)                          │
│                                                                  │
│  Ofertas por mes                                                 │
│  ┃                                                               │
│  ┃     ╱╲                                                        │
│  ┃    ╱  ╲      ╱╲                                              │
│  ┃   ╱    ╲    ╱  ╲    ╱╲                                       │
│  ┃  ╱      ╲  ╱    ╲  ╱  ╲                                      │
│  ┃ ╱        ╲╱      ╲╱    ╲                                     │
│  ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━                                  │
│   Ene  Feb  Mar  Abr  May  Jun                                  │
│                                                                  │
├─────────────────────────────────────────────────────────────────┤
│ DISTRIBUCIÓN TERRITORIAL (Row 2 - derecha)                      │
│                                                                  │
│  Mapa de Argentina                                               │
│  ┏━━━━━━━━━┓                                                    │
│  ┃░░░░░░░░░┃  ← CABA (487 ofertas) [color oscuro]              │
│  ┃▒▒▒▒▒▒▒▒▒┃  ← Buenos Aires (312 ofertas)                     │
│  ┃▓▓▓▓▓▓▓▓▓┃  ← Córdoba (156 ofertas)                          │
│  ┃         ┃  ← Santa Fe (98 ofertas) [color claro]            │
│  ┗━━━━━━━━━┛                                                    │
│                                                                  │
├─────────────────────────────────────────────────────────────────┤
│ TOP 10 OCUPACIONES (Row 3 - izquierda)                          │
│                                                                  │
│  Desarrollador web (2513)           ████████████ 245            │
│  Analista de sistemas (2511)        ██████████ 189              │
│  Gerente de ventas (1221)           ████████ 156                │
│  Contador público (2411)            ███████ 134                 │
│  Asistente administrativo (3341)    ██████ 112                  │
│  Especialista marketing (2431)      █████ 98                    │
│  Desarrollador software (2512)      █████ 87                    │
│  Técnico soporte IT (3512)          ████ 76                     │
│  Analista contable (2411)           ████ 65                     │
│  Diseñador gráfico (2166)           ███ 54                      │
│                                                                  │
├─────────────────────────────────────────────────────────────────┤
│ TOP 10 EMPRESAS (Row 3 - derecha)                               │
│                                                                  │
│  Mercado Libre                      ████████████ 87             │
│  Accenture Argentina                ██████████ 76               │
│  Globant                            █████████ 65                │
│  IBM Argentina                      ████████ 54                 │
│  Despegar.com                       ███████ 48                  │
│  Banco Galicia                      ██████ 42                   │
│  TechCorp SA                        ██████ 38                   │
│  BBVA Argentina                     █████ 34                    │
│  Santander Argentina                ████ 29                     │
│  Telecom Argentina                  ████ 27                     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Interactividad:**
- Click en barra de ocupación → Filtra automáticamente esa ocupación
- Click en provincia del mapa → Filtra esa provincia
- Hover en gráfico temporal → Tooltip con detalle del mes

### 4.4 Panel 2: Requerimientos

**Objetivo:** Entender qué requisitos solicitan las empresas.

**Contenido:**

```
┌─────────────────────────────────────────────────────────────────┐
│ EDUCACIÓN Y EXPERIENCIA (Row 1)                                  │
│                                                                  │
│  Nivel educativo requerido         Años de experiencia          │
│  ┏━━━━━━━━━━━━━━━━━━━━┓           ┏━━━━━━━━━━━━━━━━━━━━┓       │
│  ┃ Universitario 42%  ┃           ┃                     ┃       │
│  ┃ Terciario 28%      ┃           ┃     ╱╲              ┃       │
│  ┃ Secundario 18%     ┃           ┃    ╱  ╲             ┃       │
│  ┃ Posgrado 12%       ┃           ┃   ╱    ╲            ┃       │
│  ┗━━━━━━━━━━━━━━━━━━━━┛           ┃  ╱      ╲           ┃       │
│                                    ┃ ╱        ╲          ┃       │
│                                    ┗━━━━━━━━━━━━━━━━━━━━┛       │
│                                     0-1  1-3  3-5  5-10  10+    │
│                                                                  │
├─────────────────────────────────────────────────────────────────┤
│ TOP 20 CONOCIMIENTOS TÉCNICOS (Row 2 - izquierda)              │
│                                                                  │
│  SQL                                ████████████████ 387        │
│  Python                             ███████████████ 356         │
│  JavaScript                         ██████████████ 312          │
│  Excel avanzado                     █████████████ 298           │
│  Contabilidad                       ████████████ 287            │
│  Git                                ███████████ 256             │
│  React                              ██████████ 234              │
│  Java                               █████████ 212               │
│  Docker                             ████████ 189                │
│  PostgreSQL                         ████████ 178                │
│  Normativa laboral                  ███████ 167                 │
│  HTML/CSS                           ███████ 156                 │
│  Node.js                            ██████ 145                  │
│  AWS                                ██████ 134                  │
│  Facturación electrónica            █████ 123                   │
│  Angular                            █████ 118                   │
│  MongoDB                            ████ 109                    │
│  Análisis de datos                  ████ 98                     │
│  Kubernetes                         ████ 87                     │
│  Linux                              ███ 76                      │
│                                                                  │
├─────────────────────────────────────────────────────────────────┤
│ TOP 20 COMPETENCIAS BLANDAS (Row 2 - derecha)                  │
│                                                                  │
│  Trabajo en equipo                  ████████████████ 487        │
│  Comunicación efectiva              ███████████████ 456         │
│  Liderazgo                          ██████████████ 398          │
│  Proactividad                       █████████████ 367           │
│  Resolución de problemas            ████████████ 334            │
│  Adaptabilidad                      ███████████ 312             │
│  Orientación a resultados           ██████████ 289              │
│  Organización                       █████████ 267               │
│  Creatividad                        ████████ 245                │
│  Pensamiento analítico              ████████ 234                │
│  Atención al detalle                ███████ 223                 │
│  Gestión del tiempo                 ██████ 198                  │
│  Empatía                            ██████ 187                  │
│  Negociación                        █████ 176                   │
│  Toma de decisiones                 █████ 165                   │
│  Aprendizaje continuo               ████ 154                    │
│  Manejo de conflictos               ████ 143                    │
│  Visión estratégica                 ████ 132                    │
│  Innovación                         ███ 121                     │
│  Resiliencia                        ███ 109                     │
│                                                                  │
├─────────────────────────────────────────────────────────────────┤
│ JORNADA Y CONTRATO (Row 3)                                       │
│                                                                  │
│  Tipo de jornada                   Tipo de contrato             │
│  ┏━━━━━━━━━━━━━━━━━━━━┓           ┏━━━━━━━━━━━━━━━━━━━━┓       │
│  ┃ Completa 78%       ┃           ┃ Indefinido 62%      ┃       │
│  ┃ Parcial 15%        ┃           ┃ Plazo fijo 23%      ┃       │
│  ┃ Por horas 7%       ┃           ┃ Temporal 10%        ┃       │
│  ┗━━━━━━━━━━━━━━━━━━━━┛           ┃ Pasantía 5%         ┃       │
│                                    ┗━━━━━━━━━━━━━━━━━━━━┛       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Valor para analistas:**
- Identificar skills técnicos más demandados por sector
- Comparar competencias blandas más solicitadas
- Analizar relación entre nivel educativo y tipo de contrato
- Detectar brechas de habilidades en el mercado

### 4.5 Panel 3: Ofertas Laborales

**Objetivo:** Búsqueda y exploración detallada de ofertas individuales.

**Contenido:**

```
┌─────────────────────────────────────────────────────────────────┐
│ BÚSQUEDA AVANZADA (Row 1 - colapsable)                          │
│                                                                  │
│  Título: [desarrollador...]  Empresa: [mercado libre...]        │
│  Salario mínimo: [50000 ARS]  [BUSCAR]                          │
│                                                                  │
├─────────────────────────────────────────────────────────────────┤
│ RESULTADOS (Row 2 - tabla interactiva)                           │
│                                                                  │
│  Mostrando 1-25 de 487 ofertas  |  [Descargar CSV]             │
│                                                                  │
│  ┏━━━━━━━┯━━━━━━━━━━━━━━━━━━━━━━━━┯━━━━━━━━━━━━━━━━━━━━━━━━┓ │
│  ┃ ID    │ Título                  │ Empresa                 ┃ │
│  ┠───────┼─────────────────────────┼─────────────────────────┨ │
│  ┃2162282│Dev. Full Stack Senior  │TechCorp SA              ┃ │
│  ┃2162220│Analista de Sistemas    │Mercado Libre            ┃ │
│  ┃2162133│Contador Senior         │Banco Galicia            ┃ │
│  ┃2161887│Gerente Comercial       │Despegar.com             ┃ │
│  ┃...    │...                     │...                      ┃ │
│  ┗━━━━━━━┷━━━━━━━━━━━━━━━━━━━━━━━━┷━━━━━━━━━━━━━━━━━━━━━━━━┛ │
│                                                                  │
│  Columnas: Provincia, Ocupación ESCO, Experiencia, Contrato,   │
│            Salario, Fecha, [Ver detalle]                         │
│                                                                  │
├─────────────────────────────────────────────────────────────────┤
│ DETALLE DE OFERTA SELECCIONADA (Row 3 - colapsable)            │
│                                                                  │
│  ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓  │
│  ┃ Desarrollador Full Stack Senior                           ┃  │
│  ┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫  │
│  ┃                                                            ┃  │
│  ┃ EMPRESA: TechCorp SA                                       ┃  │
│  ┃ UBICACIÓN: Ciudad de Bs. As. - Comuna 1                   ┃  │
│  ┃ PUBLICADO: 10/11/2025                                      ┃  │
│  ┃ LINK: https://bumeran.com/ofertas/...                     ┃  │
│  ┃                                                            ┃  │
│  ┃ CLASIFICACIÓN ESCO:                                        ┃  │
│  ┃ • Ocupación: Desarrollador web (ISCO 2513)                ┃  │
│  ┃ • Confianza: 92%                                           ┃  │
│  ┃                                                            ┃  │
│  ┃ REQUISITOS:                                                ┃  │
│  ┃ • Educación: Universitario - Ingeniería en Sistemas       ┃  │
│  ┃ • Experiencia: 3-5 años                                    ┃  │
│  ┃ • Edad: 25-40 años                                         ┃  │
│  ┃ • Contrato: Indefinido                                     ┃  │
│  ┃ • Jornada: Completa                                        ┃  │
│  ┃ • Modalidad: 100% remoto                                   ┃  │
│  ┃                                                            ┃  │
│  ┃ CONOCIMIENTOS TÉCNICOS (6):                                ┃  │
│  ┃ • Python, Django, React, PostgreSQL, Docker, Git          ┃  │
│  ┃                                                            ┃  │
│  ┃ COMPETENCIAS BLANDAS (3):                                  ┃  │
│  ┃ • Liderazgo, Trabajo en equipo, Comunicación              ┃  │
│  ┃                                                            ┃  │
│  ┃ DESCRIPCIÓN COMPLETA:                                      ┃  │
│  ┃ "Buscamos Desarrollador Full Stack con experiencia en..." ┃  │
│  ┃ [Texto completo de la oferta]                             ┃  │
│  ┃                                                            ┃  │
│  ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Funcionalidades:**
- Tabla ordenable y filtrable por cualquier columna
- Click en fila → Expande detalle completo
- Exportar resultados filtrados a CSV
- Links directos a ofertas originales

### 4.6 Navegación por árbol ISCO-08

El filtro de ocupación incluirá un árbol interactivo con los 4 niveles jerárquicos:

```
🌳 Árbol de Ocupaciones ISCO-08

▼ 1 - Directores y gerentes (87 ofertas)
  ▼ 11 - Directores ejecutivos, personal político (23 ofertas)
    ☐ 111 - Legisladores y altos funcionarios (5 ofertas)
    ☐ 112 - Directores generales y ejecutivos (18 ofertas)
  ▼ 12 - Directores administrativos y comerciales (64 ofertas)
    ☑ 121 - Directores de finanzas (28 ofertas) ← Seleccionado
    ☐ 122 - Directores de RRHH (19 ofertas)
    ☐ 123 - Directores de ventas (17 ofertas)

▼ 2 - Profesionales científicos e intelectuales (543 ofertas)
  ▼ 25 - Profesionales TIC (312 ofertas)
    ▼ 251 - Desarrolladores de software (245 ofertas)
      ☑ 2511 - Analistas de sistemas (89 ofertas) ← Seleccionado
      ☑ 2512 - Desarrolladores de software (67 ofertas) ← Seleccionado
      ☑ 2513 - Desarrolladores web (54 ofertas) ← Seleccionado
      ☐ 2514 - Programadores de aplicaciones (35 ofertas)
    ☐ 252 - Especialistas en bases de datos (42 ofertas)
    ☐ 253 - Administradores de sistemas (25 ofertas)

▶ 3 - Técnicos y profesionales de nivel medio (234 ofertas)
▶ 4 - Personal de apoyo administrativo (178 ofertas)
...
```

**Interactividad:**
- Click en ▼ / ▶ → Expandir/Contraer nivel
- Checkbox ☐ / ☑ → Seleccionar para filtrar
- Al seleccionar un nivel, se seleccionan todos sus hijos
- Número entre paréntesis = ofertas que cumplen filtros actuales

---

## 5. FASE 4: MEJORAS EN DASHBOARD OPERATIVO (PLOTLY)

**Objetivo:** Agregar visibilidad del pipeline completo para el equipo técnico.

**Duración estimada:** 1 semana

### 5.1 Nuevo Tab: Pipeline Monitor

El dashboard Plotly actual tiene 5 tabs operativos. Agregaremos un 6to tab especializado.

**Tab 6: PIPELINE MONITOR**

**Objetivo:** Monitorear el flujo completo de datos desde scraping hasta publicación.

**Contenido:**

```
┌─────────────────────────────────────────────────────────────────┐
│ INDICADORES DEL PIPELINE (Row 1)                                 │
│                                                                  │
│  ┏━━━━━━━━━━━━━━━━┓ ┏━━━━━━━━━━━━━━━━┓ ┏━━━━━━━━━━━━━━━━┓   │
│  ┃  2,847         ┃ ┃  2,734         ┃ ┃  2,698         ┃   │
│  ┃  Scraped hoy   ┃ ┃  Procesadas    ┃ ┃  Clasificadas  ┃   │
│  ┃                ┃ ┃  NLP v6.0      ┃ ┃  ESCO          ┃   │
│  ┗━━━━━━━━━━━━━━━━┛ ┗━━━━━━━━━━━━━━━━┛ ┗━━━━━━━━━━━━━━━━┛   │
│                                                                  │
│  ┏━━━━━━━━━━━━━━━━┓                                            │
│  ┃  268           ┃                                            │
│  ┃  Publicadas    ┃                                            │
│  ┃  en dashboard  ┃                                            │
│  ┗━━━━━━━━━━━━━━━━┛                                            │
│                                                                  │
├─────────────────────────────────────────────────────────────────┤
│ FLUJO DEL PIPELINE (Row 2 - Diagrama Sankey)                    │
│                                                                  │
│  Scraping ──────────2,847───────────┐                          │
│                                      ↓                           │
│                           Consolidación ─────2,734───┐          │
│                                      ↑                ↓          │
│                           Duplicados ─113             │          │
│                                               NLP v6.0 ──2,698─┐│
│                                      ↑                 ↑        ││
│                              Sin NLP ─36   Sin procesar ─0      ││
│                                                                 ↓│
│                                                   ESCO Matching ││
│                                      ↑                          ││
│                         Sin matching ─34                        ││
│                                                                 ↓│
│                                                         Productos││
│                                                             268 ││
│                                                                  │
├─────────────────────────────────────────────────────────────────┤
│ COMPARACIÓN DE CALIDAD (Row 3)                                  │
│                                                                  │
│  Quality Score NLP                 Confidence Score ESCO        │
│  ┏━━━━━━━━━━━━━━━━━━━━┓           ┏━━━━━━━━━━━━━━━━━━━━┓       │
│  ┃ v4.0: 7.89         ┃           ┃                     ┃       │
│  ┃ v5.1: 7.52         ┃           ┃ Sin associations   ┃       │
│  ┃ v6.0: 8.81 ⬆       ┃           ┃     (promedio: 0.65)┃       │
│  ┃                     ┃           ┃          ╱╲         ┃       │
│  ┃ Mejora: +11.6%     ┃           ┃         ╱  ╲        ┃       │
│  ┗━━━━━━━━━━━━━━━━━━━━┛           ┃        ╱    ╲       ┃       │
│                                    ┃   ────╱──────╲──────┃       │
│                                    ┃                     ┃       │
│                                    ┃ Con associations    ┃       │
│                                    ┃     (promedio: 0.90)┃       │
│                                    ┃              ╱╲     ┃       │
│                                    ┃             ╱  ╲    ┃       │
│                                    ┃        ────╱────╲───┃       │
│                                    ┃                     ┃       │
│                                    ┃ Mejora: +38%        ┃       │
│                                    ┗━━━━━━━━━━━━━━━━━━━━┛       │
│                                                                  │
├─────────────────────────────────────────────────────────────────┤
│ ERRORES RECIENTES (Row 4 - tabla)                               │
│                                                                  │
│  ┏━━━━━━━━━━━━━━━┯━━━━━━━━┯━━━━━━━━━━━━┯━━━━━━━━━━━━━━━━━┓  │
│  ┃ Timestamp     │ Etapa  │ Tipo Error │ Oferta ID      ┃  │
│  ┠───────────────┼────────┼────────────┼────────────────┨  │
│  ┃ 13/11 14:32   │ NLP    │ Timeout    │ 2162289        ┃  │
│  ┃ 13/11 13:18   │ ESCO   │ No match   │ 2162245        ┃  │
│  ┃ 13/11 11:05   │ Scrape │ HTTP 503   │ -              ┃  │
│  ┗━━━━━━━━━━━━━━━┷━━━━━━━━┷━━━━━━━━━━━━┷━━━━━━━━━━━━━━━━┛  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Valor para el equipo técnico:**
- Identificar cuellos de botella en el pipeline
- Monitorear tasas de éxito por etapa
- Detectar degradación de calidad
- Troubleshooting rápido de errores

### 5.2 Mejoras en Tab "Calidad de Parseo NLP"

Agregaremos métricas específicas de NLP v6.0:

**Nuevos gráficos:**

1. **Cobertura de campos nuevos**

```
Campos NLP v6.0 - Porcentaje de extracción exitosa

edad_min                 ████████░░ 78%
edad_max                 ███████░░░ 72%
ubicacion_required       █████████░ 89%
permanencia_tipo         ███████░░░ 76%

Meta: >= 70% de cobertura en cada campo
```

2. **Distribución de permanencia detectada**

```
Tipo de contrato detectado (4,234 ofertas con dato)

Indefinido      ████████████████ 62% (2,625)
Plazo fijo      ██████ 23% (974)
Temporal        ███ 10% (423)
Pasantía        █ 5% (212)
```

3. **Análisis de edad requerida**

```
Ofertas con requisito de edad: 1,687 (31%)

Rango más frecuente: 25-35 años (45%)
Rango más amplio: 18-65 años (8%)
Promedio edad mínima: 24 años
Promedio edad máxima: 42 años

⚠️ ALERTA: 31% de ofertas con discriminación etaria potencial
```

---

## 6. FASE 5: VALIDACIÓN Y CONTROL DE CALIDAD

**Objetivo:** Asegurar que todas las mejoras funcionan correctamente antes de producción.

**Duración estimada:** 1 semana

### 6.1 Validaciones automáticas

**Test Suite 1: Extracción ESCO**

```
Verificaciones:
✓ Ocupaciones extraídas: 3,045 (esperado: ~3,137)
✓ Habilidades extraídas: 14,247 (esperado: ~14,279)
✓ Asociaciones extraídas: 238,456 (esperado: ~240,000)
✓ Jerarquía ISCO 4 niveles completos
✓ Clasificación conocimientos/competencias >= 90% cobertura
✓ Confidence promedio clasificación >= 0.85
```

**Test Suite 2: NLP v6.0**

```
Casos de prueba (20 ofertas manuales):

Test 1: Edad explícita "25 a 40 años"
  → Esperado: edad_min=25, edad_max=40
  → Resultado: ✓ PASS

Test 2: Modalidad remota "100% remoto"
  → Esperado: ubicacion_required=false
  → Resultado: ✓ PASS

Test 3: Contrato indefinido "relación de dependencia"
  → Esperado: permanencia_tipo="indefinido"
  → Resultado: ✓ PASS

Test 4: Oferta sin requisitos especiales
  → Esperado: edad_min=null, permanencia_tipo=null
  → Resultado: ✓ PASS

...

Resultado: 18/20 tests passed (90%)
```

**Test Suite 3: Normalización territorial**

```
Casos de prueba (50 ubicaciones variadas):

Test: "CABA - Belgrano"
  → Esperado: provincia_codigo=02, confidence >= 0.85
  → Resultado: ✓ PASS (confidence=0.88)

Test: "Bahia Blanca, Bs As"
  → Esperado: localidad_codigo=060007
  → Resultado: ✓ PASS (confidence=0.93)

Test: "Buenos Aires" (ambiguo)
  → Esperado: provincia_codigo=06, localidad_codigo=null
  → Resultado: ✓ PASS

...

Resultado: 47/50 tests passed (94%)
```

### 6.2 Validación de calidad de datos

**Validación del CSV v2.0:**

```
Archivo: ofertas_esco_shiny_v2.csv

✓ Total ofertas: 5,479
✓ Total columnas: 65 (esperado: 65)
✓ Encoding: UTF-8 con BOM ✓
✓ Campos críticos sin nulos:
  - titulo: 0% nulos ✓
  - empresa: 0% nulos ✓
  - fecha_publicacion: 0% nulos ✓
  - esco_occupation_code: 2% nulos ✓ (meta: < 5%)

✓ Nuevos campos - cobertura:
  - provincia_codigo_indec: 92% ✓ (meta: >= 90%)
  - permanencia_tipo: 81% ✓ (meta: >= 80%)
  - edad_min: 31% ✓ (solo cuando especifica)
  - ubicacion_required: 89% ✓

✓ Clasificación ESCO:
  - Confidence promedio: 0.87 ✓ (meta: >= 0.85)
  - Ofertas con match: 98% ✓ (meta: >= 95%)

VALIDACIÓN EXITOSA
```

### 6.3 Validación con usuarios

**Prueba piloto del dashboard Shiny v3.0:**

Convocar a 3-5 analistas para sesión de testing:

**Tareas a realizar:**
1. Buscar ofertas de desarrolladores en CABA con contrato indefinido
2. Comparar cantidad de conocimientos técnicos vs competencias blandas en sector IT
3. Generar reporte de Top 10 ocupaciones más demandadas en Córdoba
4. Exportar CSV filtrado por profesionales TIC
5. Navegar por árbol ISCO hasta encontrar "Analistas de sistemas"

**Métricas de éxito:**
- Tasa de éxito de tareas: >= 90%
- Tiempo promedio por tarea: <= 3 minutos
- Satisfacción subjetiva: >= 4/5
- Errores encontrados documentados para corrección

---

## 7. CRONOGRAMA Y RECURSOS

### 7.1 Cronograma estimado

**Total: 8 semanas**

```
SEMANA 1-2: Fase 1 - Ontología ESCO
├─ Día 1-3: Extracción RDF → SQLite
├─ Día 4-6: Clasificación conocimientos/competencias
├─ Día 7-10: Re-matching de 5,479 ofertas existentes
└─ Día 11-14: Validación y ajustes

SEMANA 3-4: Fase 2 - Pipeline de Datos
├─ Día 15-18: Desarrollo NLP v6.0
├─ Día 19-22: Normalización territorial INDEC
├─ Día 23-25: Procesamiento de ofertas con v6.0
└─ Día 26-28: Generación CSV v2.0 y validación

SEMANA 5-6: Fase 3 - Dashboard Shiny
├─ Día 29-32: Rediseño UI (3 paneles + filtros globales)
├─ Día 33-36: Implementación árbol ISCO
├─ Día 37-39: Integración CSV v2.0
└─ Día 40-42: Testing y ajustes UX

SEMANA 7: Fase 4 - Dashboard Plotly
├─ Día 43-45: Nuevo tab Pipeline Monitor
├─ Día 46-47: Mejoras en tab Calidad NLP
└─ Día 48-49: Testing e integración

SEMANA 8: Fase 5 - Testing y Validación
├─ Día 50-52: Test suites automatizados
├─ Día 53-54: Validación de calidad de datos
├─ Día 55-56: Prueba piloto con usuarios
└─ Día 57: Documentación y cierre
```

### 7.2 Recursos necesarios

**Humanos:**
- 1 desarrollador Python (pipeline + Plotly)
- 1 desarrollador R (Shiny dashboard)
- 1 analista de datos (validación + documentación)

**Infraestructura:**
- Servidor de desarrollo (recomendado: >= 16 GB RAM para procesamiento RDF)
- Ollama instalado con modelo llama3.1:8b (~4.5 GB)
- ~150 GB de espacio en disco (datos intermedios)

**Software:**
- Python 3.10+ con librerías: rdflib, rapidfuzz, pandas, docx, plotly
- R 4.0+ con librerías: shiny, shinydashboard, shinyTree, plotly, DT
- SQLite 3.x

### 7.3 Riesgos y mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|---------|------------|
| Extracción RDF falla por memoria | Media | Alto | Usar procesamiento por chunks, servidor con >= 16 GB RAM |
| NLP v6.0 no alcanza cobertura esperada | Media | Medio | A/B test previo, ajuste de prompts iterativo |
| Normalización territorial < 90% | Baja | Medio | Ampliar lista de variantes INDEC, fallback a provincia |
| Performance de dashboard Shiny lento | Media | Medio | Limitar CSV a últimos 6 meses, paginación, caching |
| Usuarios no adoptan nuevo dashboard | Baja | Alto | Prueba piloto temprana, capacitación, feedback iterativo |

---

## 8. ANEXOS

### Anexo A: Glosario de términos

**ESCO**: European Skills, Competences, Qualifications and Occupations - Clasificación multilingüe de ocupaciones y habilidades.

**ISCO-08**: International Standard Classification of Occupations - Estándar de 4 niveles para clasificar ocupaciones.

**NLP**: Natural Language Processing - Procesamiento de lenguaje natural con inteligencia artificial.

**RDF**: Resource Description Framework - Formato estándar para representar información en la web semántica.

**Fuzzy matching**: Búsqueda de similitud aproximada entre textos (ej: "Bahia Blanca" match con "Bahía Blanca").

**Quality Score**: Métrica de calidad que cuenta cuántos campos fueron exitosamente extraídos de una oferta (0-17 campos).

**Confidence Score**: Nivel de confianza del sistema en una clasificación ESCO (0.0 a 1.0, donde 1.0 es máxima confianza).

**Shiny**: Framework de R para crear dashboards web interactivos.

**Plotly Dash**: Framework de Python para crear dashboards operativos.

**CSV**: Comma-Separated Values - Formato de archivo de texto plano para tablas de datos.

### Anexo B: Preguntas frecuentes

**P1: ¿Por qué no extraemos el campo "género"?**

R: Por riesgo legal. El artículo 81 de la Ley de Contrato de Trabajo prohíbe discriminación por sexo. Almacenar esta información podría facilitar usos discriminatorios y no aporta valor analítico justificable para un organismo del Estado.

**P2: ¿Por qué procesamos el RDF solo una vez en lugar de en tiempo real?**

R: El archivo RDF de ESCO pesa 1.35 GB y requeriría un servidor triple-store especializado para consultas en tiempo real. Como ESCO se actualiza solo 1 vez al año, es más eficiente extraer toda la información a SQLite (~50 MB) y consultar desde ahí. Esto reduce costos de infraestructura y mejora la velocidad.

**P3: ¿Qué pasa con las ofertas que no tienen ubicación?**

R: Las ofertas 100% remotas o sin ubicación explícita tendrán `provincia_codigo_indec = NULL`. El dashboard permitirá filtrar por "Ubicación no especificada" o "Remoto". Estimamos ~8% de ofertas en esta categoría.

**P4: ¿Cómo se decide si una habilidad es "esencial" u "opcional"?**

R: Esa información viene directamente de la ontología ESCO. Los expertos de la Comisión Europea determinaron para cada ocupación qué habilidades son imprescindibles (esenciales) y cuáles son deseables pero no obligatorias (opcionales). Nosotros solo consumimos esa clasificación existente.

**P5: ¿El sistema puede detectar salarios no declarados?**

R: No. Si la oferta no menciona salario, el campo queda en NULL. El NLP no puede inventar información que no existe en el texto.

**P6: ¿Cuánto tarda en procesarse una oferta nueva en producción?**

R: Aproximadamente:
- Scraping: instantáneo (ya viene en caché)
- NLP v6.0: ~8 segundos (llamada a Ollama)
- ESCO matching: ~2 segundos (consultas SQLite)
- Normalización territorial: < 1 segundo (fuzzy matching)
- **Total: ~11 segundos por oferta**

Con 2,500 ofertas/día → ~7.6 horas de procesamiento. Se ejecuta en batch nocturno.

**P7: ¿El dashboard Shiny podrá exportar datos en otros formatos además de CSV?**

R: Sí, agregaremos opciones de exportación a Excel (.xlsx) y JSON. El CSV seguirá siendo el formato principal por compatibilidad con herramientas estadísticas.

**P8: ¿Qué pasa si ESCO actualiza la ontología?**

R: ESCO v1.3.0 saldrá en 2026. Cuando eso suceda, repetiremos el proceso de extracción del RDF (Fase 1), actualizaremos la base de datos y re-clasificaremos las ofertas activas. Estimamos 1 semana de trabajo para la actualización.

### Anexo C: Referencias

**Documentación oficial ESCO:**
- Portal ESCO: https://esco.ec.europa.eu/
- Descargas: https://esco.ec.europa.eu/en/use-esco/download
- API Reference: https://ec.europa.eu/esco/api

**ISCO-08:**
- ILO ISCO-08 Structure: https://www.ilo.org/public/english/bureau/stat/isco/isco08/

**INDEC:**
- Códigos geográficos: https://www.indec.gob.ar/indec/web/Institucional-Indec-Codgeo

**Normativa legal:**
- Ley de Contrato de Trabajo (LCT): http://servicios.infoleg.gob.ar/infolegInternet/anexos/25000-29999/25552/texact.htm

---

## PRÓXIMOS PASOS

1. **Revisión y aprobación de este plan** por el equipo directivo
2. **Asignación de recursos** (desarrolladores, analista, infraestructura)
3. **Kick-off meeting** para alinear expectativas y cronograma
4. **Inicio de Fase 1** (extracción ESCO)

**Contacto para consultas:**
Equipo OEDE - Monitor de Ofertas Laborales
Noviembre 2025
