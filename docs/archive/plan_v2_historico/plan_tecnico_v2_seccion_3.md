# SECCIÓN 3: ¿CÓMO RECOLECTAMOS LOS DATOS?
## Sistema de Scraping y Búsqueda Inteligente

---

## 3.1. VISIÓN GENERAL DEL SCRAPING

### ¿Qué es el scraping y por qué lo usamos?

El scraping es el proceso automatizado de **recolección de datos públicos** desde portales de empleo en internet. En lugar de que un analista entre manualmente a cada portal, copie ofertas de trabajo una por una, y las pegue en una planilla, tenemos un sistema que:

1. **Se conecta automáticamente** a los portales de empleo
2. **Busca ofertas** usando palabras clave estratégicas
3. **Extrae la información** relevante (título, descripción, empresa, etc.)
4. **Guarda todo** en una base de datos estructurada
5. **Se ejecuta periódicamente** para capturar ofertas nuevas

**Beneficio principal:** Podemos monitorear miles de ofertas laborales en tiempo real, algo imposible de hacer manualmente.

---

### El desafío de la búsqueda exhaustiva

**Problema:**
Los portales de empleo funcionan como buscadores (tipo Google). Si buscás "programador", te muestra ofertas que contienen esa palabra. Pero **NO te muestra**:
- Ofertas que dicen "desarrollador" (sinónimo)
- Ofertas que dicen "Python developer" (término técnico)
- Ofertas que dicen "software engineer" (término en inglés)
- Ofertas que dicen "backend" sin mencionar "programador"

**Nuestra solución:**
En lugar de buscar con 10-20 keywords generales, usamos **1,148 keywords ultra específicas** organizadas en 59 categorías ocupacionales.

**Ejemplo real:**

```
❌ Búsqueda simple (3 keywords):
   - "programador" → 450 ofertas
   - "desarrollador" → 320 ofertas
   - "ingeniero software" → 180 ofertas
   Total: ~950 ofertas (con mucha superposición)

✅ Búsqueda exhaustiva (67 keywords solo IT):
   - "python", "javascript", "react", "nodejs", "django"
   - "backend", "frontend", "fullstack", "devops"
   - "qa", "tester", "analista-sistemas"
   - "arquitecto-software", "tech-lead", "scrum-master"
   - ... y 53 keywords más
   Total: ~3,200 ofertas únicas (sin duplicar)
```

---

## 3.2. LOS 5 PORTALES DE EMPLEO

### Estado actual de automatización

| Portal | Estado Actual | Ofertas Capturadas | Cobertura |
|--------|---------------|-------------------|-----------|
| **Bumeran** | ✅ Automatizado | ~4,500/mes | Alta (70%) |
| **ComputRabajo** | 🟡 Manual | ~800/mes | Media (15%) |
| **ZonaJobs** | 🟡 Manual | ~400/mes | Baja (8%) |
| **LinkedIn** | 🟡 Manual | ~250/mes | Baja (5%) |
| **Indeed** | 🟡 Manual | ~150/mes | Baja (2%) |
| **TOTAL** | Semi-automático | ~6,100/mes | 100% |

**Nota:** Los porcentajes indican qué fracción de nuestras ofertas totales viene de cada portal.

---

### ¿Por qué solo Bumeran está automatizado?

**Respuesta técnica simple:**
- **Bumeran:** Tiene una estructura web estable y predecible → fácil de automatizar
- **Los otros 4:** Tienen protecciones anti-bot, estructuras dinámicas, o requieren login → difíciles de automatizar

**Consecuencia práctica:**
Actualmente un analista debe:
1. Entrar manualmente a ComputRabajo, ZonaJobs, LinkedIn, Indeed
2. Hacer búsquedas con algunas keywords
3. Descargar/copiar ofertas
4. Subirlas al sistema

**Objetivo para v2.0:**
Automatizar al menos 3 de los 5 portales (prioridad: ComputRabajo y ZonaJobs).

---

## 3.3. SISTEMA DE KEYWORDS: 1,148 TÉRMINOS EN 59 CATEGORÍAS

### ¿Cómo se construyó el diccionario de 1,148 keywords?

El sistema de keywords NO fue creado arbitrariamente. Es el resultado de **4 fases de análisis iterativo basado en ofertas reales**.

---

#### **FASE 1: Versión 2.1 - Base inicial (35 keywords)**

**Método:** Análisis de frecuencia en títulos de ofertas

**Fuente de datos:**
- 1,156 ofertas reales scrapeadas de 5 portales
- Análisis de términos más frecuentes en títulos

**Resultado:**
- 35 keywords de "alto valor"
- Basados exclusivamente en frecuencia real de aparición

**Ejemplo:**
```
Términos más frecuentes encontrados:
- "vendedor" → 147 menciones (12.7%)
- "administrativo" → 98 menciones (8.5%)
- "desarrollador" → 76 menciones (6.6%)
- "contador" → 54 menciones (4.7%)
...

✅ Se incluyen en v2.1 como keywords base
```

**Limitación identificada:**
- Cobertura baja (~30-40% de ofertas)
- Faltaban sinónimos y variantes (ej: "developer" vs "desarrollador")

---

#### **FASE 2: Versión 3.0 - Expansión semántica (~600 keywords)**

**Método:** Expansión manual + categorización

**Acciones:**
1. **Creación de 10 categorías nuevas:**
   - UX_Diseño_Digital
   - Data_Analytics
   - Sistemas_Infraestructura
   - Seguros_Banca
   - Legal_Juridico
   - Y 5 más...

2. **Expansión de 6 categorías existentes:**
   - IT_Tecnologia: 30 → 80 keywords
   - Atencion_Cliente: 7 → 15 keywords
   - Administracion: 15 → 45 keywords
   - Ventas: 12 → 38 keywords
   - Gastronomia: 8 → 25 keywords
   - Logistica: 10 → 30 keywords

3. **Inclusión de sinónimos y variantes:**
   - "desarrollador" + "developer" + "programador"
   - "vendedor" + "ejecutivo-comercial" + "sales"
   - "administrativo" + "asistente" + "assistant"

**Resultado:**
- ~600 keywords en estrategia "exhaustiva"
- Cobertura teórica: ~90% del mercado laboral argentino

---

#### **FASE 3: Versión 3.1 - Descubrimiento de términos faltantes (~1,000 keywords)**

**Fecha:** 31 de octubre de 2025

**Método:** Análisis automatizado de términos NO capturados

**Fuente de datos:**
- 3,484 ofertas scrapeadas (corpus actualizado)

**Proceso automatizado:**

```
┌─────────────────────────────────────────────────────────────┐
│ Script: analizar_keywords_faltantes.py                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ 1. Carga 3,484 ofertas scrapeadas                          │
│                                                             │
│ 2. Extrae términos de títulos:                             │
│    - Tokens individuales (ej: "python")                    │
│    - Bigramas (ej: "desarrollador python")                 │
│    - Trigramas (ej: "desarrollador python senior")         │
│                                                             │
│ 3. Aplica filtros:                                          │
│    - Elimina stopwords en español                          │
│    - Filtra por frecuencia mínima (≥3 menciones)           │
│    - Normaliza texto (minúsculas, sin tildes)              │
│                                                             │
│ 4. Compara contra diccionario v3.0:                        │
│    - ¿Está el término ya incluido? → ignorar               │
│    - ¿Es término nuevo? → marcar para revisión             │
│                                                             │
│ 5. Categoriza automáticamente:                             │
│    - rol_tech: "devops", "qa-automation"                   │
│    - ubicacion: "cordoba", "rosario"                       │
│    - modalidad: "remoto", "hibrido"                        │
│    - nivel: "junior", "senior", "trainee"                  │
│    - industria: "fintech", "healthtech"                    │
│                                                             │
│ 6. Genera reporte:                                          │
│    - CSV con términos faltantes ordenados por frecuencia   │
│    - Estimación de impacto (% ofertas que mencionan el     │
│      término)                                               │
└─────────────────────────────────────────────────────────────┘
```

**Resultado del análisis:**
- **267 términos nuevos** descubiertos
- Organizados en 22 categorías

**Ejemplos de términos faltantes encontrados:**

```
Categoría: Tecnologías emergentes
- "blockchain" → 18 menciones (0.52%)
- "terraform" → 14 menciones (0.40%)
- "microservicios" → 12 menciones (0.34%)

Categoría: Soft skills
- "proactividad" → 156 menciones (4.48%)
- "trabajo-en-equipo" → 134 menciones (3.85%)
- "comunicacion-efectiva" → 87 menciones (2.50%)

Categoría: Modalidades
- "hibrido" → 234 menciones (6.72%)
- "part-time" → 45 menciones (1.29%)
- "freelance" → 28 menciones (0.80%)
```

**Acción:**
- Script `expandir_diccionario_v3_1.py` integra los 267 términos
- Se crea nueva estrategia **"ultra_exhaustiva"** con ~1,000 keywords
- Cobertura estimada: >95%

---

#### **FASE 4: Versión 3.2 - Análisis exhaustivo por categorías (~1,200 keywords)**

**Fecha:** 31 de octubre de 2025 (EN DESARROLLO)

**Método:** Análisis profundo con patrones regex en 8 dimensiones

**Fuente de datos:**
- 5,255 ofertas consolidadas

**Proceso automatizado:**

```
┌─────────────────────────────────────────────────────────────┐
│ Script: analizar_ofertas_v3_2.py                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ Analiza 5,255 ofertas en 8 categorías con regex patterns:  │
│                                                             │
│ 1. ESTUDIOS REQUERIDOS                                      │
│    Patrones:                                                │
│    - "ingeniería? en (\w+)"                                 │
│    - "licenciatura en (\w+)"                                │
│    - "técnico en (\w+)"                                     │
│    - "secundario completo"                                  │
│                                                             │
│    Resultado: 89 términos educativos                        │
│                                                             │
│ 2. EXPERIENCIA LABORAL                                      │
│    Patrones:                                                │
│    - "(\d+) años? de experiencia"                           │
│    - "experiencia (previa|comprobable|demostrable)"         │
│    - "(junior|senior|semi-senior)"                          │
│                                                             │
│    Resultado: 34 términos de experiencia                    │
│                                                             │
│ 3. TAREAS Y RESPONSABILIDADES                               │
│    Patrones:                                                │
│    - Verbos de acción: "gestionar", "coordinar",            │
│      "desarrollar", "implementar", "analizar"               │
│                                                             │
│    Resultado: 127 verbos/tareas comunes                     │
│                                                             │
│ 4. SKILLS TÉCNICAS                                          │
│    Patrones:                                                │
│    - Software: "SAP", "ERP", "CRM", "WMS"                   │
│    - Lenguajes: "Python", "Java", "JavaScript"              │
│    - Frameworks: "React", "Angular", "Django"               │
│    - Herramientas: "Excel avanzado", "Power BI"             │
│                                                             │
│    Resultado: 203 skills técnicas                           │
│                                                             │
│ 5. SOFT SKILLS                                              │
│    Patrones:                                                │
│    - "trabajo en equipo"                                    │
│    - "liderazgo"                                            │
│    - "comunicación efectiva"                                │
│    - "resolución de problemas"                              │
│                                                             │
│    Resultado: 67 soft skills                                │
│                                                             │
│ 6. IDIOMAS                                                  │
│    Patrones:                                                │
│    - "inglés (avanzado|intermedio|básico)"                  │
│    - "portugués"                                            │
│    - "(bilingüe|trilingüe)"                                 │
│                                                             │
│    Resultado: 18 términos de idiomas                        │
│                                                             │
│ 7. BENEFICIOS                                               │
│    Patrones:                                                │
│    - "prepaga"                                              │
│    - "capacitación"                                         │
│    - "home office"                                          │
│    - "bonus por objetivos"                                  │
│                                                             │
│    Resultado: 45 beneficios comunes                         │
│                                                             │
│ 8. MODALIDADES Y HORARIOS                                   │
│    Patrones:                                                │
│    - "(presencial|remoto|híbrido)"                          │
│    - "(jornada completa|part-time)"                         │
│    - "horario flexible"                                     │
│    - "turnos rotativos"                                     │
│                                                             │
│    Resultado: 28 modalidades                                │
│                                                             │
│ TOTAL: ~600 nuevos términos candidatos                      │
└─────────────────────────────────────────────────────────────┘
```

**Filtrado por umbrales de frecuencia:**

Cada categoría tiene un umbral mínimo para evitar ruido:

| Categoría | Umbral | % del corpus | Razón |
|-----------|--------|--------------|-------|
| Estudios | ≥20 menciones | 0.38% | Títulos universitarios relevantes |
| Experiencia | ≥10 menciones | 0.19% | Niveles de senioridad comunes |
| Tareas | ≥50 menciones | 0.95% | Solo verbos muy frecuentes |
| Skills técnicas | ≥15 menciones | 0.29% | Software/herramientas relevantes |
| Soft skills | ≥50 menciones | 0.95% | Solo soft skills muy pedidas |
| Idiomas | ≥10 menciones | 0.19% | Idiomas con demanda real |
| Beneficios | ≥20 menciones | 0.38% | Beneficios importantes |
| Modalidades | ≥15 menciones | 0.29% | Modalidades comunes |

**Resultado esperado:**
- Script `expandir_diccionario_v3_2.py` consolidará términos aprobados
- Estrategia **"ultra_exhaustiva_v3_2"** con top 1,200 keywords
- Cobertura estimada: ~97% del mercado

---

### Resumen de la evolución

```
┌─────────┬──────────────────┬──────────┬──────────┬─────────────────┐
│ Versión │ Fecha            │ Keywords │ Fuente   │ Cobertura       │
├─────────┼──────────────────┼──────────┼──────────┼─────────────────┤
│ v2.1    │ 2024             │ 35       │ 1,156    │ ~40%            │
│         │                  │          │ ofertas  │                 │
├─────────┼──────────────────┼──────────┼──────────┼─────────────────┤
│ v3.0    │ 2025 (Q1)        │ ~600     │ Expansión│ ~90%            │
│         │                  │          │ semántica│                 │
├─────────┼──────────────────┼──────────┼──────────┼─────────────────┤
│ v3.1    │ 2025-10-31       │ ~1,000   │ 3,484    │ ~95%            │
│         │                  │          │ ofertas  │                 │
├─────────┼──────────────────┼──────────┼──────────┼─────────────────┤
│ v3.2    │ 2025-10-31       │ ~1,200   │ 5,255    │ ~97%            │
│         │ (desarrollo)     │          │ ofertas  │                 │
└─────────┴──────────────────┴──────────┴──────────┴─────────────────┘
```

**Actualmente en producción:** **1,148 keywords** (configuración activa de v3.1/v3.2)

---

### Scripts de análisis y generación

El sistema tiene 4 scripts principales para gestión de keywords:

#### **1. `analizar_keywords_faltantes.py`**
**Función:** Descubre términos NO incluidos en el diccionario actual

**Entrada:**
- CSV/JSON de ofertas scrapeadas
- Diccionario actual (master_keywords.json)

**Salida:**
- CSV con términos faltantes ordenados por frecuencia
- JSON con análisis completo
- Estimación de impacto por término

**Uso:**
```
Ejecutar cada 3 meses con nuevas ofertas scrapeadas
→ Identificar términos emergentes
→ Validar manualmente antes de agregar
```

---

#### **2. `expandir_diccionario_v3_1.py`**
**Función:** Integra nuevos términos descubiertos en v3.0 → v3.1

**Proceso:**
1. Carga diccionario v3.0
2. Carga análisis de términos faltantes
3. Organiza 267 nuevos términos en 22 categorías
4. Crea estrategia "ultra_exhaustiva"
5. Genera backup de v3.0
6. Guarda v3.1

**Resultado:**
- `master_keywords.json` versión v3.1
- Backup automático: `master_keywords_v3.0_backup.json`

---

#### **3. `expandir_diccionario_v3_2.py`**
**Función:** Integra análisis exhaustivo de 8 categorías en v3.1 → v3.2

**Proceso:**
1. Carga diccionario v3.1
2. Lee reportes de 8 categorías (estudios, experiencia, etc.)
3. Aplica umbrales de frecuencia por categoría
4. Filtra duplicados y términos ya existentes
5. Consolida nuevos términos
6. Crea estrategia "ultra_exhaustiva_v3_2"
7. Genera backup de v3.1

**Resultado:**
- `master_keywords_v3_2.json` (en desarrollo)

---

#### **4. `analizar_eficiencia_keywords.py`**
**Función:** Mide productividad y detecta keywords redundantes

**Métricas calculadas:**
- **Ofertas únicas:** Cuántas ofertas SOLO esta keyword captura
- **Ofertas compartidas:** Cuántas ofertas otras keywords también capturan
- **Productividad:** Ofertas únicas por segundo de búsqueda
- **Redundancia:** % de overlap con otras keywords

**Clasificación:**
- **Keywords CRÍTICAS:** Tienen ofertas únicas > 0 (no se pueden eliminar sin perder cobertura)
- **Keywords REDUNDANTES:** 100% overlap con otras (candidatas a eliminación)

**Resultado documentado:**
```
"Tasa de productividad: 58.4%"
(671 de 1,148 keywords generan resultados únicos)
```

**Acción:**
- Keywords redundantes se marcan para revisión
- Se evalúa eliminar ~40% de keywords sin perder cobertura

---

### Proceso de actualización continua

**Frecuencia:** Cada 3 meses

**Workflow:**

```
1. RECOLECCIÓN (día 1)
   - Ejecutar scraping exhaustivo con keywords actuales
   - Consolidar 3-6 meses de ofertas nuevas

2. ANÁLISIS (día 2-3)
   - Ejecutar analizar_keywords_faltantes.py
   - Identificar términos nuevos con frecuencia ≥5

3. VALIDACIÓN (día 4-5)
   - Revisar manualmente términos candidatos
   - Clasificar por categoría
   - Descartar falsos positivos (errores de tipeo, ruido)

4. EXPANSIÓN (día 6)
   - Ejecutar expandir_diccionario_vX.py
   - Generar nueva versión del diccionario
   - Validar que no haya errores de formato

5. PRUEBA (día 7-10)
   - Ejecutar scraping de prueba con nuevo diccionario
   - Comparar cobertura vs versión anterior
   - Validar que no haya regresiones

6. DESPLIEGUE (día 11)
   - Reemplazar master_keywords.json en producción
   - Actualizar documentación
   - Comunicar cambios al equipo

7. MONITOREO (día 12-30)
   - Revisar dashboard de scraping
   - Validar que nuevas keywords generen resultados
   - Detectar keywords problemáticas (muchas ofertas irrelevantes)
```

---

### Balance cobertura vs ruido

No todas las keywords son iguales. Algunas generan muchas ofertas pero con mucho "ruido" (ofertas irrelevantes).

**Ejemplo:**

```
Keyword: "java"
├─ ✅ Ofertas relevantes (70%):
│  - "Desarrollador Java Sr - Globant"
│  - "Java Backend Engineer - Mercado Libre"
│  - "Programador Java Junior - Accenture"
│
└─ ❌ Ofertas irrelevantes (30%):
   - "Vendedor de café Java - Starbucks"
   - "Libro: Aprende Java en 21 días"
   - "Curso Java - UTN"

→ Keyword se mantiene (70% relevancia es aceptable)
```

**Umbrales de calidad:**

| Relevancia | Acción |
|------------|--------|
| >80% | ✅ Keyword excelente, mantener |
| 60-80% | 🟡 Keyword aceptable, monitorear |
| 40-60% | ⚠️ Keyword cuestionable, evaluar alternativas |
| <40% | ❌ Keyword ruidosa, considerar eliminar |

**Solución para keywords ruidosas:**
- Usar bigramas/trigramas más específicos
- Ejemplo: "java" → "desarrollador-java", "programador-java"

---

### Ejemplos de categorías y sus keywords

#### **CATEGORÍA 1: Tecnología e IT (67 keywords)**

```
Desarrollo de software:
- python, java, javascript, typescript, csharp, php
- react, angular, vue, nodejs, django, spring
- frontend, backend, fullstack

DevOps e infraestructura:
- devops, sre, cloud, aws, azure, gcp
- docker, kubernetes, jenkins, terraform
- linux, sysadmin

Datos y análisis:
- data-scientist, data-analyst, data-engineer
- machine-learning, ai, deep-learning
- sql, nosql, mongodb, postgresql

QA y testing:
- qa, tester, automation-tester
- selenium, cypress, junit

Otros IT:
- ui-ux, diseñador-web, scrum-master
- product-owner, tech-lead, cto
```

#### **CATEGORÍA 2: Administración y Finanzas (82 keywords)**

```
Contabilidad:
- contador, asistente-contable, analista-contable
- liquidacion-sueldos, impuestos, auditoria

Finanzas:
- analista-financiero, tesorero, controller
- creditos, cobranzas, facturacion

Administración general:
- administrativo, asistente-administrativo
- recepcionista, secretaria, office-manager

Recursos Humanos:
- rrhh, recruiter, generalista-rrhh
- capacitacion, desarrollo-organizacional
```

#### **CATEGORÍA 3: Ventas y Comercial (58 keywords)**

```
Ventas directas:
- vendedor, ejecutivo-comercial, representante-ventas
- preventa, postventa, atencion-cliente

Marketing:
- marketing, community-manager, seo-sem
- content-creator, growth-hacker

E-commerce:
- ecommerce, marketplace, analista-ecommerce
```

#### **CATEGORÍA 4: Gastronomía y Hotelería (45 keywords)**

```
Cocina:
- cocinero, chef, sous-chef, ayudante-cocina
- pastelero, parrillero, pizzero

Servicio:
- mozo, camarero, bartender, barista
- maitre, encargado-salon

Hotelería:
- recepcionista-hotel, conserje, housekeeping
- gerente-hotel, revenue-manager
```

**... y 55 categorías más:**
- Salud (médico, enfermero, farmacéutico...)
- Educación (docente, profesor, tutor...)
- Legal (abogado, paralegal, escribano...)
- Ingeniería (ingeniero-civil, arquitecto, agrimensor...)
- Logística (chofer, operario-deposito, supervisor-logistica...)
- Seguridad (vigilador, seguridad, monitorista...)
- Construcción (albanil, plomero, electricista...)
- Retail (cajero, repositor, encargado-sucursal...)
- Producción (operario, supervisor-produccion, jefe-planta...)
- Y muchas más...

---

## 3.4. PROCESO DE SCRAPING AUTOMATIZADO (BUMERAN)

### Flujo paso a paso

```
┌─────────────────────────────────────────────────────────────┐
│ PASO 1: ACTIVACIÓN AUTOMÁTICA                              │
├─────────────────────────────────────────────────────────────┤
│ - Windows Task Scheduler despierta el sistema              │
│ - Horario: Todos los días a las 6:00 AM                    │
│ - Duración promedio: 2-3 horas                             │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ PASO 2: CARGA DE KEYWORDS                                  │
├─────────────────────────────────────────────────────────────┤
│ - Lee archivo master_keywords.json                         │
│ - Carga las 1,148 keywords de estrategia ultra_exhaustiva  │
│ - Organiza por prioridad (IT > Admin > Ventas > etc.)      │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ PASO 3: BÚSQUEDA POR KEYWORD (1,148 iteraciones)           │
├─────────────────────────────────────────────────────────────┤
│ Para cada keyword:                                          │
│   1. Construye URL de búsqueda                              │
│      Ejemplo: bumeran.com.ar/empleos-busqueda-python.html  │
│                                                             │
│   2. Descarga página de resultados                          │
│      - Obtiene primeras 50 ofertas por keyword              │
│      - Extrae: título, empresa, ubicación, fecha, link      │
│                                                             │
│   3. Aplica filtros básicos                                 │
│      - Ignora ofertas con más de 30 días                    │
│      - Ignora ofertas ya descargadas (no duplicar)          │
│                                                             │
│   4. Guarda metadata en base de datos                       │
│      - Tabla: ofertas_bumeran_metadata                      │
│      - Campos: id, titulo, empresa, url, fecha, keyword_usada│
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ PASO 4: DESCARGA DE CONTENIDO COMPLETO                     │
├─────────────────────────────────────────────────────────────┤
│ Para cada oferta nueva:                                     │
│   1. Abre URL individual de la oferta                       │
│   2. Extrae contenido completo                              │
│      - Título                                               │
│      - Descripción detallada (HTML + texto plano)           │
│      - Empresa (nombre, descripción)                        │
│      - Ubicación (provincia, localidad)                     │
│      - Fecha de publicación                                 │
│      - Área/Categoría                                       │
│      - Modalidad (presencial/remoto/híbrido)                │
│                                                             │
│   3. Guarda contenido completo en base de datos             │
│      - Tabla: ofertas_raw                                   │
│      - Todo el HTML original (para referencia futura)       │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ PASO 5: CONTROL DE CALIDAD AUTOMÁTICO                      │
├─────────────────────────────────────────────────────────────┤
│ Validaciones:                                               │
│   ✓ Título no vacío (mínimo 10 caracteres)                 │
│   ✓ Descripción no vacía (mínimo 100 caracteres)           │
│   ✓ Fecha válida (formato reconocible)                     │
│   ✓ URL única (no duplicada)                               │
│   ✓ Empresa identificada (no "N/A")                        │
│                                                             │
│ Ofertas rechazadas → log para revisión manual              │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ PASO 6: REPORTE DE EJECUCIÓN                               │
├─────────────────────────────────────────────────────────────┤
│ Genera estadísticas:                                        │
│   - Total keywords procesadas: 1,148                        │
│   - Ofertas nuevas encontradas: ~150-200/día               │
│   - Ofertas duplicadas ignoradas: ~300-400/día             │
│   - Ofertas con errores: ~5-10/día                         │
│   - Tiempo total de ejecución: ~2.5 horas                  │
│   - Próxima ejecución: Mañana 6:00 AM                      │
│                                                             │
│ Envía notificación por email si hay errores críticos       │
└─────────────────────────────────────────────────────────────┘
```

---

### Ejemplo real de una búsqueda

**Keyword:** `python`

**URL generada:**
```
https://www.bumeran.com.ar/empleos-busqueda-python.html?
  recientes=true&
  publicacion=30
```

**Resultados obtenidos (primeros 5):**

```
1. Desarrollador Python Sr - Globant
   Ubicación: CABA
   Fecha: Hace 2 días
   URL: bumeran.com.ar/empleos/12345-desarrollador-python...

2. Python Backend Developer - Mercado Libre
   Ubicación: CABA, Buenos Aires
   Fecha: Hace 1 día
   URL: bumeran.com.ar/empleos/12346-python-backend...

3. Ingeniero de Datos Python - Banco Galicia
   Ubicación: CABA
   Fecha: Hace 5 días
   URL: bumeran.com.ar/empleos/12347-ingeniero-datos...

4. Analista Python - Accenture
   Ubicación: Córdoba, Córdoba
   Fecha: Hace 3 días
   URL: bumeran.com.ar/empleos/12348-analista-python...

5. Python Developer Trainee - Naranja X
   Ubicación: Córdoba, Córdoba
   Fecha: Hace 1 día
   URL: bumeran.com.ar/empleos/12349-python-trainee...
```

**Acción del sistema:**
- Descarga contenido completo de las 5 ofertas
- Las guarda en `ofertas_raw` (tabla de base de datos)
- Marca como procesadas para no volver a descargarlas mañana
- Continúa con la siguiente keyword (`java`)

---

## 3.5. PROCESO DE SCRAPING MANUAL (OTROS 4 PORTALES)

### Estado actual: Workflow semi-manual

**Responsable:** Analista de datos OEDE

**Frecuencia:** 1 vez por semana (los lunes)

**Proceso:**

```
┌─────────────────────────────────────────────────────────────┐
│ LUNES 9:00 AM - SESIÓN DE SCRAPING MANUAL                  │
└─────────────────────────────────────────────────────────────┘

📌 PORTAL 1: ComputRabajo (30 minutos)
   ├─ Entrar a www.computrabajo.com.ar
   ├─ Buscar con 15 keywords principales:
   │  "programador", "administrativo", "vendedor", etc.
   ├─ Copiar ofertas interesantes (título + link)
   ├─ Pegar en planilla Excel temporal
   └─ ~80-100 ofertas capturadas

📌 PORTAL 2: ZonaJobs (20 minutos)
   ├─ Entrar a www.zonajobs.com.ar
   ├─ Buscar con 10 keywords principales
   ├─ Copiar ofertas interesantes
   ├─ Pegar en misma planilla Excel
   └─ ~40-60 ofertas capturadas

📌 PORTAL 3: LinkedIn (20 minutos)
   ├─ Entrar a www.linkedin.com/jobs
   ├─ Filtrar: Argentina, últimos 7 días
   ├─ Buscar con 10 keywords principales
   ├─ Copiar ofertas interesantes
   └─ ~30-40 ofertas capturadas

📌 PORTAL 4: Indeed (15 minutos)
   ├─ Entrar a ar.indeed.com
   ├─ Buscar con 8 keywords principales
   ├─ Copiar ofertas interesantes
   └─ ~20-30 ofertas capturadas

📌 CONSOLIDACIÓN (20 minutos)
   ├─ Subir planilla Excel al sistema
   ├─ Script importa ofertas a tabla ofertas_raw
   ├─ Validación básica (no duplicados)
   └─ Total agregado: ~170-230 ofertas/semana
```

**Tiempo total:** ~2 horas por semana

---

### Limitaciones del proceso manual

| Problema | Impacto | Ejemplo |
|----------|---------|---------|
| **Cobertura limitada** | Solo se buscan 15-20 keywords (vs 1,148 en Bumeran) | Se pierden ofertas nicho como "scala developer", "sap-abap", "qa-automation" |
| **Baja frecuencia** | Solo 1 vez/semana (vs diario en Bumeran) | Ofertas publicadas martes se capturan el lunes siguiente (6 días tarde) |
| **Sesgo humano** | Analista elige qué ofertas copiar | Puede ignorar ofertas relevantes por error de interpretación |
| **No escalable** | 2 horas/semana fijas | Si queremos agregar más portales → +2 horas más |
| **Errores de tipeo** | Al copiar manualmente se pueden introducir errores | Nombres de empresas mal escritos, links rotos |

---

### Objetivo para v2.0: Automatización completa

**Prioridades de automatización:**

```
PRIORIDAD 1 (Impacto alto, factibilidad alta):
✅ ComputRabajo
   - Estructura web similar a Bumeran
   - ~800 ofertas/mes adicionales
   - Ahorro: 30 minutos/semana

PRIORIDAD 2 (Impacto medio, factibilidad media):
✅ ZonaJobs
   - Estructura más compleja pero predecible
   - ~400 ofertas/mes adicionales
   - Ahorro: 20 minutos/semana

PRIORIDAD 3 (Impacto bajo, factibilidad baja):
🟡 LinkedIn
   - Requiere login, tiene protecciones anti-bot
   - ~250 ofertas/mes adicionales
   - Ahorro: 20 minutos/semana
   - Desafío: puede bloquear cuenta

PRIORIDAD 4 (Impacto bajo, factibilidad muy baja):
⛔ Indeed
   - Protecciones anti-bot muy agresivas
   - ~150 ofertas/mes adicionales
   - Ahorro: 15 minutos/semana
   - Riesgo: bloqueo de IP

AHORRO TOTAL POTENCIAL: ~1.5 horas/semana = 6 horas/mes = 72 horas/año
```

**Estrategia:**
- Automatizar ComputRabajo y ZonaJobs en Fase 1 (3 meses)
- LinkedIn y Indeed: evaluar alternativas (APIs oficiales, servicios de terceros)

---

## 3.6. GESTIÓN DE DUPLICADOS

### ¿Por qué hay duplicados?

**Razón 1: Misma oferta en múltiples portales**
Una empresa puede publicar la misma oferta en Bumeran, ComputRabajo, ZonaJobs, LinkedIn e Indeed.

**Ejemplo:**
```
Bumeran:       "Desarrollador Python Sr - Globant"
ComputRabajo:  "Desarrollador Python Senior - Globant"
ZonaJobs:      "Python Developer Sr - Globant"
LinkedIn:      "Senior Python Developer - Globant"
Indeed:        "Sr. Python Dev - Globant"

→ Son la MISMA oferta, pero con títulos ligeramente diferentes
```

---

### ¿Cómo detectamos duplicados?

**Estrategia multi-nivel:**

#### **Nivel 1: Duplicado exacto (URL)**
Si dos ofertas tienen la misma URL → son idénticas (obvio).

```sql
SELECT url, COUNT(*)
FROM ofertas_raw
GROUP BY url
HAVING COUNT(*) > 1
```

**Resultado:** ~5% de duplicados exactos (re-publicaciones)

---

#### **Nivel 2: Duplicado por empresa + título similar**

Si dos ofertas tienen:
- Misma empresa
- Títulos con >80% de similitud (algoritmo de distancia de Levenshtein)
- Publicadas con <7 días de diferencia

→ Probablemente son la misma oferta

**Ejemplo:**
```
Oferta A: "Desarrollador Python Sr - Globant"
Oferta B: "Desarrollador Python Senior - Globant"
Similitud: 92% → DUPLICADO
```

**Resultado:** ~15% de duplicados por título similar

---

#### **Nivel 3: Duplicado por contenido**

Si dos ofertas tienen:
- Misma empresa
- Descripción con >70% de similitud (comparación de texto)
- Títulos diferentes (pero descripciones idénticas)

→ Son la misma oferta con títulos distintos

**Ejemplo:**
```
Oferta A: "Desarrollador Backend"
Oferta B: "Backend Developer"
Descripción: [Exactamente la misma en ambas]
→ DUPLICADO
```

**Resultado:** ~10% de duplicados por descripción

---

### Estrategia de consolidación

**Regla:** Cuando detectamos duplicados, **mantenemos la más completa** y marcamos las otras como duplicadas (no las borramos, por si acaso).

**Criterio de "más completa":**
1. Descripción más larga (más información)
2. Portal con mejor calidad de datos (Bumeran > ComputRabajo > ZonaJobs > etc.)
3. Fecha de publicación más reciente

**Ejemplo:**
```
Oferta A (Bumeran):
  - Descripción: 1,500 caracteres
  - Fecha: 2025-01-10
  - Campos adicionales: Área, Modalidad

Oferta B (ZonaJobs):
  - Descripción: 800 caracteres
  - Fecha: 2025-01-12
  - Campos adicionales: Ninguno

DECISIÓN: Mantener Oferta A (más completa)
          Marcar Oferta B como duplicada
```

---

### Estadísticas de duplicación

En una muestra de 1,000 ofertas:

```
Ofertas únicas:              700 (70%)
Duplicados exactos (URL):     50 (5%)
Duplicados por título:       150 (15%)
Duplicados por descripción:  100 (10%)
```

**Impacto:**
- Sin detección de duplicados → 1,000 ofertas (30% inflado)
- Con detección de duplicados → 700 ofertas (dato real)

**Beneficio:**
- Métricas precisas (no contamos la misma oferta 3 veces)
- Análisis no sesgado por re-publicaciones

---

## 3.7. ALMACENAMIENTO DE DATOS CRUDOS

### Tabla: `ofertas_raw`

**Propósito:** Guardar la oferta original **tal cual** fue descargada, sin procesar.

**¿Por qué guardar datos crudos?**
1. **Trazabilidad:** Podemos volver a la fuente original si hay dudas
2. **Re-procesamiento:** Si mejoramos el NLP, podemos re-analizar ofertas antiguas
3. **Auditoría:** Verificar que el scraping funcionó correctamente
4. **Histórico:** Conservar ofertas aunque el portal las elimine

---

### Estructura de la tabla

| Campo | Tipo | Descripción | Ejemplo |
|-------|------|-------------|---------|
| `id` | Entero | ID único autoincremental | 12345 |
| `portal` | Texto | De dónde viene | "bumeran", "computrabajo" |
| `url` | Texto | Link original | "https://bumeran.com.ar/empleos/12345..." |
| `titulo` | Texto | Título de la oferta | "Desarrollador Python Sr" |
| `empresa` | Texto | Nombre empresa | "Globant" |
| `ubicacion_raw` | Texto | Ubicación sin normalizar | "Caba, Capital Federal" |
| `descripcion_raw` | Texto | Descripción completa | "Buscamos desarrollador con experiencia..." |
| `html_original` | Texto | HTML completo | `<div class="job">...</div>` |
| `fecha_publicacion` | Fecha | Cuándo se publicó | "2025-01-15" |
| `fecha_scraping` | Timestamp | Cuándo la descargamos | "2025-01-16 06:23:45" |
| `keyword_usada` | Texto | Keyword que la encontró | "python" |
| `metadata_json` | JSON | Datos adicionales del portal | `{"area": "IT", "modalidad": "remoto"}` |
| `es_duplicado` | Booleano | ¿Es duplicado de otra? | false |
| `id_original` | Entero | Si es duplicado, ID del original | NULL |

---

### Ejemplo de registro real

```json
{
  "id": 12345,
  "portal": "bumeran",
  "url": "https://www.bumeran.com.ar/empleos/desarrollador-python-sr-1234567.html",
  "titulo": "Desarrollador Python Sr",
  "empresa": "Globant",
  "ubicacion_raw": "Capital Federal, Buenos Aires",
  "descripcion_raw": "En Globant buscamos incorporar un Desarrollador Python Senior...",
  "html_original": "<div class='job-description'>...</div>",
  "fecha_publicacion": "2025-01-15",
  "fecha_scraping": "2025-01-16 06:23:45",
  "keyword_usada": "python",
  "metadata_json": {
    "area": "Tecnología / Sistemas",
    "modalidad": "Remoto",
    "tipo_contrato": "Relación de dependencia",
    "vacantes": 3
  },
  "es_duplicado": false,
  "id_original": null
}
```

---

## 3.8. MONITOREO Y CONTROL DE CALIDAD

### Dashboard técnico: Métricas de scraping

**¿Dónde se ve?**
Dashboard Plotly (puerto 8052) → Tab "Scraping Monitor"

**Métricas en tiempo real:**

#### **1. Volumen de ofertas capturadas**

```
┌─────────────────────────────────────────────────┐
│ OFERTAS CAPTURADAS - ÚLTIMOS 30 DÍAS           │
├─────────────────────────────────────────────────┤
│                                                 │
│     │                                           │
│ 300 │         ╭─╮                               │
│     │      ╭──╯ ╰─╮                             │
│ 200 │   ╭──╯      ╰──╮                          │
│     │╭──╯            ╰──╮                       │
│ 100 ││                  ╰───╮                   │
│     │╰──────────────────────╰───                │
│   0 └───────────────────────────────            │
│     1   5   10  15  20  25  30 (días)           │
│                                                 │
│ Total mes: 5,847 ofertas                        │
│ Promedio diario: 195 ofertas                    │
│ Hoy: 203 ofertas ✅ (+4% vs promedio)           │
└─────────────────────────────────────────────────┘
```

---

#### **2. Distribución por portal**

```
┌─────────────────────────────────────────────────┐
│ OFERTAS POR PORTAL - ÚLTIMO MES                 │
├─────────────────────────────────────────────────┤
│                                                 │
│ Bumeran         ████████████████████ 4,123 (70%)│
│ ComputRabajo    ██████ 876 (15%)                │
│ ZonaJobs        ███ 468 (8%)                    │
│ LinkedIn        ██ 234 (4%)                     │
│ Indeed          █ 146 (3%)                      │
│                                                 │
│ TOTAL: 5,847 ofertas                            │
└─────────────────────────────────────────────────┘
```

---

#### **3. Tasa de éxito/error**

```
┌─────────────────────────────────────────────────┐
│ CALIDAD DE SCRAPING - HOY                       │
├─────────────────────────────────────────────────┤
│                                                 │
│ ✅ Exitosos:     197 ofertas (97%)              │
│ ⚠️  Warnings:      4 ofertas (2%)               │
│ ❌ Errores:        2 ofertas (1%)               │
│                                                 │
│ Warnings:                                       │
│   - Descripción corta (<100 chars): 3           │
│   - Empresa no identificada: 1                  │
│                                                 │
│ Errores:                                        │
│   - URL inválida: 1                             │
│   - Timeout de conexión: 1                      │
│                                                 │
└─────────────────────────────────────────────────┘
```

---

#### **4. Keywords más productivas**

Top 10 keywords que generan más ofertas:

```
┌─────────────────────────────────────────────────┐
│ TOP 10 KEYWORDS - ÚLTIMO MES                    │
├─────────────────────────────────────────────────┤
│                                                 │
│ 1. vendedor          ████████████ 487 ofertas   │
│ 2. administrativo    ██████████ 412 ofertas     │
│ 3. python            ████████ 356 ofertas       │
│ 4. contador          ███████ 298 ofertas        │
│ 5. desarrollador     ██████ 267 ofertas         │
│ 6. chofer            ██████ 245 ofertas         │
│ 7. cocinero          █████ 223 ofertas          │
│ 8. enfermero         █████ 201 ofertas          │
│ 9. recepcionista     ████ 189 ofertas           │
│10. javascript        ████ 178 ofertas           │
│                                                 │
└─────────────────────────────────────────────────┘
```

**Insight:** Keywords de oficios tradicionales (vendedor, administrativo) generan más volumen que keywords técnicas (python, javascript).

---

#### **5. Alertas automáticas**

El sistema envía alertas por email si detecta:

```
🔴 ALERTA CRÍTICA:
   - Scraping fallido por >2 horas
   - Tasa de error >10%
   - 0 ofertas capturadas en 24 horas

🟡 ALERTA ADVERTENCIA:
   - Tasa de error >5%
   - Volumen 20% inferior al promedio
   - Keyword que solía generar ofertas ahora no genera nada
```

**Ejemplo de email:**

```
De: MOL System <mol@oede.gob.ar>
Para: analista@oede.gob.ar
Asunto: [MOL] 🟡 ADVERTENCIA - Volumen bajo de scraping

Hola,

El scraping de hoy capturó solo 98 ofertas,
20% menos que el promedio de 195 ofertas/día.

Portal más afectado: Bumeran (solo 65 ofertas vs 140 promedio)

Posibles causas:
- Bumeran cambió estructura web
- Problema de conectividad
- Feriado/fin de semana (menos publicaciones)

Recomendación: Revisar logs en Dashboard Técnico.

--
MOL System v2.0
```

---

## 3.9. LIMITACIONES Y DESAFÍOS TÉCNICOS

### Desafío 1: Cambios en estructura web de portales

**Problema:**
Los portales de empleo cambian su diseño web cada 6-12 meses. Cuando cambian:
- El scraper deja de funcionar
- Necesitamos actualizar el código de extracción

**Ejemplo real:**
```
Antes (HTML antiguo de Bumeran):
<div class="job-title">Desarrollador Python Sr</div>

Después (HTML nuevo):
<h2 class="offer-heading">Desarrollador Python Sr</h2>

→ Scraper buscaba "job-title" y ya no lo encuentra
→ Necesitamos cambiar código a "offer-heading"
```

**Solución actual:**
- Revisión mensual de funcionamiento
- Actualización manual del código cuando detectamos cambios

**Solución propuesta (v2.0):**
- Implementar scraping más robusto (menos dependiente de estructura HTML)
- Usar selectores múltiples (si no encuentra "job-title", buscar "offer-heading")
- Alertas automáticas cuando detectamos cambios

---

### Desafío 2: Protecciones anti-bot

**Problema:**
Los portales detectan cuando un bot (no humano) está accediendo y bloquean el acceso.

**Técnicas de detección:**
1. **Velocidad de navegación:** Un humano no puede ver 50 ofertas por minuto
2. **User-Agent:** Navegadores reales tienen User-Agent específico
3. **Cookies y sesiones:** Los humanos mantienen sesiones, los bots no
4. **Comportamiento del mouse:** Los humanos mueven el mouse, los bots no
5. **CAPTCHAs:** Desafíos que solo humanos pueden resolver

**Cómo los evitamos (técnicas permitidas):**

```
✅ Reducir velocidad de scraping
   - Esperar 2-5 segundos entre cada oferta
   - Simular comportamiento humano

✅ User-Agent realista
   - Simular navegador Chrome en Windows

✅ Respetar robots.txt
   - Archivo que indica qué se puede scrapear

✅ No saturar servidores
   - Máximo 1 request cada 2 segundos
```

**Lo que NO hacemos:**
```
⛔ Resolver CAPTCHAs automáticamente (ilegal)
⛔ Usar VPNs para esconder IP
⛔ Hacer requests masivos en paralelo
```

---

### Desafío 3: Ofertas con contenido dinámico (JavaScript)

**Problema:**
Algunos portales cargan contenido con JavaScript después de abrir la página. El scraper tradicional solo ve el HTML inicial (vacío).

**Ejemplo:**

```
Humano abre LinkedIn:
1. Página HTML se carga (sin ofertas aún)
2. JavaScript ejecuta y llama a API
3. API devuelve ofertas
4. JavaScript inserta ofertas en página
5. Humano ve ofertas ✅

Bot tradicional:
1. Descarga HTML inicial (sin ofertas)
2. No ejecuta JavaScript
3. Ve página vacía ❌
```

**Solución:**
Usar navegador automatizado (Selenium/Playwright) que sí ejecuta JavaScript.

**Pero:**
- Mucho más lento (5-10x más tiempo)
- Consume más recursos (memoria, CPU)
- Más fácil de detectar como bot

**Decisión actual:**
- Bumeran no necesita JavaScript → scraping simple (rápido)
- LinkedIn necesita JavaScript → scraping manual (por ahora)

---

### Desafío 4: Contenido parcial o faltante

**Problema:**
No todas las ofertas tienen todos los campos completos. Muchas son vagas.

**Ejemplo real:**

```
Oferta A (completa):
✅ Título: "Desarrollador Python Sr"
✅ Empresa: "Globant"
✅ Ubicación: "CABA, Buenos Aires"
✅ Descripción: 1,500 caracteres (detallada)
✅ Salario: "$300,000-$400,000"
✅ Modalidad: "Remoto"

Oferta B (incompleta):
✅ Título: "Programador"
❌ Empresa: "Empresa líder en tecnología" (anónima)
❌ Ubicación: "Buenos Aires" (provincia o ciudad?)
❌ Descripción: 200 caracteres (muy corta)
❌ Salario: No menciona
❌ Modalidad: No menciona
```

**Impacto:**
- Ofertas incompletas son difíciles de clasificar con ESCO
- El NLP no tiene suficiente información para extraer requerimientos
- Reportes y análisis son menos precisos

**Solución actual:**
- Guardar la oferta de todos modos (es mejor tener algo que nada)
- Marcar qué campos están vacíos
- Intentar inferir información faltante con NLP (ej: si dice "Buenos Aires" en IT → probablemente CABA)

**Métrica:**
- ~40% de ofertas tienen descripción completa (>1,000 caracteres)
- ~30% tienen descripción media (500-1,000 caracteres)
- ~30% tienen descripción corta (<500 caracteres)

---

### Desafío 5: Ofertas fraudulentas o spam

**Problema:**
Algunos portales permiten publicar ofertas falsas:
- Empresas que no existen
- "Trabajos desde casa" que son esquemas piramidales
- Ofertas con salarios irreales
- Phishing (robar datos personales)

**Ejemplos reales:**

```
🚩 OFERTA SOSPECHOSA 1:
Título: "Gana $500,000/mes trabajando desde casa"
Empresa: "Oportunidad única"
Descripción: "No necesitas experiencia, solo ganas de trabajar..."

🚩 OFERTA SOSPECHOSA 2:
Título: "Inversor buscado"
Empresa: "Empresa confidencial"
Descripción: "Invierte $50,000 y recupera $200,000 en 3 meses..."

🚩 OFERTA SOSPECHOSA 3:
Título: "Desarrollador Python Sr"
Empresa: "Google Argentina"
Descripción: "Envía CV con foto y DNI a email123@gmail.com"
[⚠️ Google no recluta así, es phishing]
```

**Cómo las detectamos:**

```
Filtros automáticos:
✓ Título con palabras prohibidas: "gana dinero fácil", "trabaja desde casa sin experiencia"
✓ Salarios irreales: >$1,000,000/mes para junior
✓ Emails sospechosos: @gmail.com, @hotmail.com (empresas serias usan dominio propio)
✓ Descripciones con URLs acortadas (bit.ly)
```

**Acción:**
- Marcar como "posible_spam"
- No incluir en análisis público
- Revisar manualmente antes de eliminar

---

## 3.10. ROADMAP: MEJORAS PLANIFICADAS PARA v2.0

### Corto plazo (0-3 meses)

#### **1. Automatizar ComputRabajo**

**Objetivo:** Sumar ~800 ofertas/mes automáticas

**Tareas:**
- Adaptar scraper de Bumeran a estructura de ComputRabajo
- Implementar detección de cambios en estructura web
- Pruebas con 50 keywords
- Despliegue completo con 1,148 keywords

**Impacto:**
- +30% de cobertura
- -30 minutos/semana de trabajo manual

---

#### **2. Mejoras en detección de duplicados**

**Objetivo:** Reducir duplicados de 30% a 15%

**Tareas:**
- Implementar algoritmo de similitud de texto mejorado
- Agregar detección cross-portal (misma oferta en Bumeran y ComputRabajo)
- Validar manualmente 500 ofertas para calibrar algoritmo

**Impacto:**
- Métricas más precisas
- Base de datos más limpia

---

#### **3. Optimización de keywords**

**Objetivo:** Agregar 50 keywords nuevas, eliminar 20 obsoletas

**Tareas:**
- Analizar ofertas no capturadas (falsos negativos)
- Detectar términos emergentes (ej: "devops", "blockchain")
- Eliminar keywords que no generan resultados en 6 meses
- Validar con reclutadores de empresas

**Impacto:**
- +5% de cobertura en sectores emergentes
- Mejor calidad de búsqueda

---

### Mediano plazo (3-6 meses)

#### **4. Automatizar ZonaJobs**

**Objetivo:** Sumar ~400 ofertas/mes automáticas

**Tareas:**
- Desarrollar scraper para ZonaJobs (estructura más compleja)
- Implementar manejo de sesiones y cookies
- Pruebas A/B para evitar detección de bots
- Despliegue completo

**Impacto:**
- +15% de cobertura
- -20 minutos/semana de trabajo manual

---

#### **5. Sistema de alertas avanzado**

**Objetivo:** Detectar problemas antes de que afecten producción

**Tareas:**
- Implementar monitoreo de cambios en estructura HTML de portales
- Alertas predictivas (ej: "portal X cambió estructura, scraper podría fallar mañana")
- Dashboard con métricas históricas (evolución de capturas por keyword)
- Integración con Slack/Teams para alertas en tiempo real

**Impacto:**
- Menor tiempo de inactividad
- Resolución proactiva de problemas

---

### Largo plazo (6-12 meses)

#### **6. Machine Learning para detección de ofertas relevantes**

**Objetivo:** Filtrar ofertas irrelevantes automáticamente

**Problema actual:**
Algunas keywords generan ofertas no relacionadas con empleo formal:
- "Python" → ofertas de venta de libros de Python
- "Java" → ofertas de café Java (sí, en serio)

**Solución:**
Entrenar modelo ML que clasifica:
- Oferta de empleo real ✅
- Oferta irrelevante ❌

**Impacto:**
- Base de datos más limpia
- Menos ruido en análisis

---

#### **7. APIs oficiales de portales**

**Objetivo:** Reemplazar scraping por APIs oficiales (si existen)

**Ventajas:**
- Datos estructurados (no necesitamos parsear HTML)
- Sin riesgo de detección anti-bot
- Más rápido y confiable

**Desventajas:**
- Muchos portales no tienen API pública
- APIs suelen ser de pago
- Pueden tener límites de requests

**Evaluación:**
- Contactar a Bumeran, ComputRabajo, ZonaJobs
- Consultar costos y términos de uso
- Evaluar costo/beneficio vs scraping

---

#### **8. Expansión a más portales**

**Portales potenciales:**
- **Empleos Clarín** (portal de diario Clarín)
- **La Nación Empleos** (portal de diario La Nación)
- **Página 12 Empleos** (menor volumen pero nicho interesante)
- **Portales especializados:**
  - Get on Board (tech jobs)
  - Navent (IT y management)
  - Atyca (retail y gastronomía)

**Impacto estimado:**
+1,500 ofertas/mes adicionales

---

## 3.11. RESUMEN EJECUTIVO: SISTEMA DE SCRAPING

### Lo que tenemos hoy

```
✅ Scraping automatizado de Bumeran (70% de cobertura)
✅ 1,148 keywords en 59 categorías (estrategia ultra exhaustiva)
✅ Detección de duplicados (30% filtrado)
✅ ~6,100 ofertas/mes capturadas
✅ Calidad: 97% de éxito en scraping
✅ Dashboard técnico para monitoreo

🟡 Scraping manual de 4 portales (30% de cobertura)
🟡 2 horas/semana de trabajo manual
🟡 Baja frecuencia (1 vez/semana)
```

---

### Lo que vamos a mejorar

```
FASE 1 (0-3 meses):
→ Automatizar ComputRabajo (+800 ofertas/mes)
→ Mejorar detección duplicados (30% → 15%)
→ Optimizar keywords (+50 nuevas)

FASE 2 (3-6 meses):
→ Automatizar ZonaJobs (+400 ofertas/mes)
→ Sistema alertas avanzado
→ Monitoreo predictivo

FASE 3 (6-12 meses):
→ Machine Learning para filtrado inteligente
→ Explorar APIs oficiales
→ Expansión a más portales
```

---

### Impacto esperado

| Métrica | Hoy | v2.0 (12 meses) | Mejora |
|---------|-----|-----------------|--------|
| **Ofertas/mes** | 6,100 | 8,500 | +39% |
| **Automatización** | 70% | 95% | +25pp |
| **Trabajo manual** | 2 hrs/semana | 15 min/semana | -87% |
| **Duplicados** | 30% | 15% | -50% |
| **Portales automatizados** | 1/5 | 3/5 | +200% |
| **Keywords** | 1,148 | 1,200 | +4.5% |

---

### Riesgos y mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| Portal cambia estructura web | Alta | Alto | Monitoreo semanal + alertas automáticas |
| Portal bloquea scraping | Media | Alto | Usar APIs oficiales si están disponibles |
| Keywords obsoletas | Media | Medio | Revisión trimestral con expertos |
| Ofertas fraudulentas | Media | Bajo | Filtros anti-spam automáticos |
| Sobrecarga de servidor | Baja | Medio | Throttling (máx 1 request/2 seg) |

---

### Preguntas frecuentes

**P: ¿Por qué no usar APIs oficiales desde el principio?**
R: Porque la mayoría de portales no tienen APIs públicas, o son de pago. Scraping es la única opción viable para acceso gratuito a datos públicos.

**P: ¿Es legal el scraping?**
R: Sí, siempre que:
- Los datos sean públicos (no requieran login)
- No violemos términos de servicio del portal
- No saturemos sus servidores
- Respetemos robots.txt

**P: ¿Por qué no contratar un servicio de scraping de terceros?**
R: Evaluamos opciones como ScrapingBee, Bright Data, etc. Son caros (USD 200-500/mes) y no justifican el costo vs desarrollar in-house.

**P: ¿Cuántas ofertas se pierden por no tener scraping completo?**
R: Estimamos que capturamos ~60% del mercado total. Los 40% restantes están en portales pequeños, redes sociales, o publicaciones directas en sitios corporativos.

**P: ¿Podríamos hacer scraping de sitios corporativos (careers pages)?**
R: Sí, pero son miles de empresas con estructuras web muy diferentes. No es escalable. Mejor enfocarnos en los 5-10 portales principales que concentran 80% del mercado.

---

## 🎯 CONCLUSIÓN

El sistema de scraping es el **corazón del MOL**: sin datos de buena calidad y volumen, no hay análisis posible.

**Hoy tenemos:**
- Un sistema semi-automatizado que funciona
- Cobertura razonable (6,100 ofertas/mes)
- Margen de mejora claro (automatizar 30% restante)

**Hacia dónde vamos:**
- Automatización completa (95%)
- Mayor volumen (+39%)
- Menos trabajo manual (-87%)
- Mejor calidad (duplicados -50%)

**Próximo paso:** Con las ofertas capturadas, necesitamos **procesarlas y extraer información estructurada**. Eso lo vemos en la Sección 4: Pipeline de Análisis.

---

**FIN DE SECCIÓN 3**

---
