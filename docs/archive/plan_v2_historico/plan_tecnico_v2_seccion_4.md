# SECCIÓN 4: ¿CÓMO PROCESAMOS LOS DATOS?
## Pipeline de Análisis y Extracción Inteligente

---

## 4.1. VISIÓN GENERAL DEL PIPELINE

### El flujo completo de datos

Una vez que tenemos las ofertas scrapeadas, comienza el proceso de **transformación de texto crudo en datos estructurados**.

```
┌─────────────────────────────────────────────────────────────────┐
│                    PIPELINE DE PROCESAMIENTO                    │
└─────────────────────────────────────────────────────────────────┘

ETAPA 1: SCRAPING
│ Ofertas crudas desde 5 portales
│ → ofertas_raw (tabla SQL)
│
├─> 6,521 ofertas con HTML, texto, metadata
│
▼

ETAPA 2: CONSOLIDACIÓN
│ Limpieza y normalización básica
│ - Eliminar HTML tags
│ - Detectar duplicados
│ - Normalizar fechas
│ - Validar campos obligatorios
│
├─> ofertas_consolidadas (tabla SQL)
│
▼

ETAPA 3: NLP - EXTRACCIÓN INTELIGENTE
│ Análisis de texto con LLM (Ollama llama3.1:8b)
│ - Experiencia requerida (años)
│ - Nivel educativo
│ - Idiomas y niveles
│ - Skills técnicas
│ - Soft skills
│ - Certificaciones
│ - Salario (si se menciona)
│ - Beneficios
│ - Requisitos excluyentes vs deseables
│ - Jornada laboral
│ - Modalidad (presencial/remoto/híbrido)
│
├─> ofertas_nlp (tabla SQL)
│
▼

ETAPA 4: ESCO - CLASIFICACIÓN OCUPACIONAL
│ Matching con ontología ESCO v1.2.0
│ - Ocupación CIUO-08 (de 3,137 opciones)
│ - Skills requeridas (de 14,279 opciones)
│ - Nivel de skill (esencial vs opcional)
│ - Clasificación Knowledge vs Competencies
│
├─> ofertas_esco (tabla SQL)
│
▼

ETAPA 5: NORMALIZACIÓN Y ENRIQUECIMIENTO
│ Agregado de metadata adicional
│ - Normalización territorial INDEC (24 provincias)
│ - Cálculo de permanencia (días online)
│ - Clasificación por sector económico
│ - Detección de sector público/privado
│
├─> ofertas_finales (tabla SQL)
│
▼

ETAPA 6: EXPORTACIÓN
│ Generación de datasets para análisis
│ - CSV v2.0 para Shiny dashboard
│ - JSON para APIs
│ - Parquet para análisis masivo
│
└─> ofertas_esco_shiny.csv (6,521 ofertas)
```

**Tiempo de procesamiento actual:**
- Scraping: ~2-3 horas (automático, diario)
- Consolidación: ~5 minutos (automático, post-scraping)
- NLP: ~4-6 horas para 200 ofertas (manual, semanal)
- ESCO: ~10 minutos (manual, post-NLP)
- Normalización: ~2 minutos (automático, post-ESCO)

**Objetivo v2.0:**
- TODO automático, ejecutándose diariamente
- Tiempo total: <4 horas end-to-end

---

## 4.2. ETAPA 2: CONSOLIDACIÓN Y LIMPIEZA

### ¿Qué hace la consolidación?

Convierte HTML crudo en texto estructurado y limpio, listo para análisis.

---

### Proceso paso a paso

#### **Paso 1: Limpieza de HTML**

**Problema:**
Las ofertas vienen con HTML completo (tags, estilos, scripts).

**Ejemplo real:**

```html
Entrada (HTML crudo):
<div class="job-description">
  <h2>Desarrollador Python</h2>
  <p><strong>Requisitos:</strong></p>
  <ul>
    <li>3 años de experiencia</li>
    <li>Python, Django, React</li>
  </ul>
  <script>trackView();</script>
</div>

Salida (texto limpio):
Desarrollador Python
Requisitos:
- 3 años de experiencia
- Python, Django, React
```

**Acciones:**
- Eliminar tags HTML (`<div>`, `<p>`, `<ul>`, etc.)
- Eliminar scripts y estilos
- Preservar estructura (saltos de línea, bullets)
- Convertir entidades HTML (`&aacute;` → `á`)

---

#### **Paso 2: Normalización de campos**

**Campos normalizados:**

| Campo Original | Normalizado | Ejemplo |
|----------------|-------------|---------|
| `fecha_publicacion` | Formato ISO 8601 | "Hace 2 días" → "2025-01-12" |
| `ubicacion_raw` | Provincia + Localidad | "Caba" → "Ciudad Autónoma de Buenos Aires" |
| `empresa` | Nombre limpio | "GLOBANT S.A." → "Globant" |
| `titulo` | Sin caracteres especiales | "Desarrollador ★★★" → "Desarrollador" |

---

#### **Paso 3: Validación de calidad**

**Reglas de validación:**

```
✅ Oferta VÁLIDA si cumple:
   - Título no vacío (≥10 caracteres)
   - Descripción no vacía (≥100 caracteres)
   - Fecha válida (entre 2020-01-01 y hoy)
   - URL única (no duplicada)

❌ Oferta RECHAZADA si:
   - Descripción <100 caracteres (muy corta)
   - Título contiene spam ("GANA $$$")
   - Fecha fuera de rango válido
   - URL duplicada (ya procesada)
```

**Resultado:**
- 97% de ofertas pasan validación
- 3% se marcan como "requiere_revision"

---

#### **Paso 4: Detección de duplicados cross-portal**

Ya vimos esto en Sección 3, pero aquí se aplica:

**Ejemplo:**
```
Oferta A (Bumeran):
  Título: "Desarrollador Python Sr"
  Empresa: "Globant"
  Descripción: "Buscamos desarrollador Python..."

Oferta B (ZonaJobs):
  Título: "Python Developer Senior"
  Empresa: "Globant"
  Descripción: "Buscamos desarrollador Python..."

Similitud: 95% → DUPLICADO
Acción: Marcar B como duplicado de A
```

---

### Tabla: `ofertas_consolidadas`

**Estructura:**

| Campo | Tipo | Ejemplo |
|-------|------|---------|
| `id` | Entero | 12345 |
| `id_raw` | Entero | 67890 (FK a ofertas_raw) |
| `titulo_limpio` | Texto | "Desarrollador Python Sr" |
| `descripcion_limpia` | Texto | "Buscamos desarrollador con experiencia..." |
| `empresa_normalizada` | Texto | "Globant" |
| `provincia` | Texto | "Ciudad Autónoma de Buenos Aires" |
| `localidad` | Texto | "CABA" |
| `fecha_publicacion` | Fecha | "2025-01-15" |
| `es_valida` | Booleano | true |
| `es_duplicado` | Booleano | false |
| `fecha_consolidacion` | Timestamp | "2025-01-16 08:15:30" |

---

## 4.3. ETAPA 3: NLP - EXTRACCIÓN INTELIGENTE

### ¿Por qué necesitamos NLP?

Las ofertas son **texto libre**. Los analistas no pueden leer 6,000+ ofertas manualmente.

**Necesitamos extraer:**
- ¿Cuántos años de experiencia piden?
- ¿Qué nivel educativo requieren?
- ¿Qué skills técnicas mencionan?
- ¿Qué idiomas piden?
- ¿Cuánto pagan?
- ¿Es presencial, remoto o híbrido?

**Solución:** Usar un LLM (Large Language Model) para leer y extraer información estructurada.

---

### Tecnología: Ollama + llama3.1:8b

**¿Qué es Ollama?**
- Herramienta que permite correr modelos LLM **localmente** (sin enviar datos a APIs externas como OpenAI)
- Gratuito y open source
- Rápido (corre en CPU/GPU local)

**¿Por qué llama3.1:8b?**
- Modelo de Meta AI (Facebook)
- 8 mil millones de parámetros (balance entre calidad y velocidad)
- Funciona en español
- Bueno para tareas de extracción estructurada

**Alternativas evaluadas:**

| Modelo | Ventajas | Desventajas | Decisión |
|--------|----------|-------------|----------|
| GPT-4 (OpenAI) | Muy preciso | De pago ($$$), requiere internet, envía datos fuera | ❌ No usar |
| Claude (Anthropic) | Muy bueno | De pago ($$), requiere internet | ❌ No usar |
| Mistral 7B | Rápido | Menos preciso en español | 🟡 Backup |
| llama3.1:8b | Balance precio/calidad | Requiere 8GB RAM | ✅ Elegido |
| llama3.1:70b | Muy preciso | Requiere 64GB RAM (inviable) | ❌ No usar |

---

### Evolución del sistema NLP

Tuvimos **3 versiones** del sistema de extracción:

```
┌─────────┬────────────┬─────────────────┬───────────────────┐
│ Versión │ Fecha      │ Campos extraídos│ Quality Score     │
├─────────┼────────────┼─────────────────┼───────────────────┤
│ v4.0    │ 2024-10    │ 17 campos       │ 7.89 campos/oferta│
│ v5.0    │ 2024-12    │ 17 campos       │ 7.52 campos/oferta│
│ v5.1    │ 2025-01    │ 17 campos       │ 8.81 campos/oferta│
└─────────┴────────────┴─────────────────┴───────────────────┘
```

**¿Qué cambió entre versiones?**
- **v4.0:** Prompt inicial, extraía bien pero confiaba mucho (confidence score alto)
- **v5.0:** Prompt más conservador, extraía menos pero más seguro (bajó quality score)
- **v5.1:** Prompt optimizado, mejores instrucciones de extracción (subió quality score)

**Test A/B realizado:**
- 50 ofertas procesadas con las 3 versiones
- v5.1 ganó con +11.6% más campos completos vs v4.0
- Decisión: **Activar v5.1 en producción**

---

### Campos extraídos por el NLP

**17 campos estructurados:**

#### **1. Experiencia laboral**
```json
{
  "experiencia_min_anios": 3,
  "experiencia_max_anios": 5
}
```
**Ejemplos de extracción:**
- "3 a 5 años de experiencia" → min: 3, max: 5
- "Mínimo 2 años" → min: 2, max: null
- "Senior (5+ años)" → min: 5, max: null
- "Sin experiencia" → min: 0, max: 0

---

#### **2. Nivel educativo**
```json
{
  "nivel_educativo": "universitario",
  "estado_educativo": "completo",
  "carrera_especifica": "Ingeniería en Sistemas"
}
```

**Valores posibles (nivel_educativo):**
- `secundario`
- `terciario`
- `universitario`
- `posgrado`
- `no_especificado`

**Valores posibles (estado_educativo):**
- `completo`
- `en_curso`
- `trunco`
- `no_especificado`

**Ejemplos de extracción:**
- "Ingeniero en Sistemas" → universitario, completo, "Ingeniería en Sistemas"
- "Estudiante avanzado de Administración" → universitario, en_curso, "Administración"
- "Secundario completo" → secundario, completo, null

---

#### **3. Idiomas**
```json
{
  "idioma_principal": "inglés",
  "nivel_idioma_principal": "avanzado"
}
```

**Valores posibles (idioma):**
- `inglés`, `portugués`, `francés`, `alemán`, `italiano`, `chino`, `otro`

**Valores posibles (nivel):**
- `basico`, `intermedio`, `avanzado`, `nativo`

**Ejemplos de extracción:**
- "Inglés avanzado" → inglés, avanzado
- "Inglés conversacional" → inglés, intermedio
- "Bilingüe inglés/español" → inglés, nativo
- "No requiere idiomas" → null, null

---

#### **4. Skills técnicas**
```json
{
  "skills_tecnicas_list": ["Python", "Django", "React", "PostgreSQL", "Docker"]
}
```

**Categorías detectadas:**
- Lenguajes de programación: Python, Java, JavaScript, C#, PHP
- Frameworks: Django, React, Angular, Spring, .NET
- Bases de datos: PostgreSQL, MySQL, MongoDB, Oracle
- Herramientas: Docker, Kubernetes, Jenkins, Git
- Software: SAP, Excel avanzado, Power BI, AutoCAD

**Ejemplos de extracción:**
- "Python, Django, y React" → ["Python", "Django", "React"]
- "Manejo de SAP" → ["SAP"]
- "Excel avanzado (tablas dinámicas, macros)" → ["Excel avanzado"]

---

#### **5. Soft skills**
```json
{
  "soft_skills_list": ["trabajo en equipo", "liderazgo", "comunicación efectiva"]
}
```

**Soft skills más comunes:**
- trabajo en equipo
- liderazgo
- comunicación efectiva
- proactividad
- resolución de problemas
- orientación a resultados
- adaptabilidad
- atención al detalle

**Ejemplos de extracción:**
- "Buscamos personas proactivas con capacidad de trabajo en equipo"
  → ["proactividad", "trabajo en equipo"]

---

#### **6. Certificaciones**
```json
{
  "certificaciones_list": ["PMP", "Scrum Master", "AWS Certified"]
}
```

**Ejemplos:**
- "Certificación PMP deseable" → ["PMP"]
- "Scrum Master (excluyente)" → ["Scrum Master"]

---

#### **7. Salario**
```json
{
  "salario_min": 300000,
  "salario_max": 400000,
  "moneda": "ARS"
}
```

**Desafío:**
Solo ~5% de ofertas mencionan salario explícitamente.

**Ejemplos de extracción:**
- "$300.000 a $400.000" → min: 300000, max: 400000, ARS
- "USD 2,000" → min: 2000, max: null, USD
- "Pretensión salarial a convenir" → null, null, null

---

#### **8. Beneficios**
```json
{
  "beneficios_list": ["prepaga", "capacitación", "home office", "bonus por objetivos"]
}
```

**Beneficios más comunes:**
- prepaga / obra social
- capacitación continua
- home office / trabajo remoto
- horario flexible
- bonus por objetivos
- comedor / viáticos
- día de cumpleaños libre
- buen ambiente laboral

---

#### **9. Requisitos excluyentes vs deseables**
```json
{
  "requisitos_excluyentes_list": ["título universitario", "3 años de experiencia"],
  "requisitos_deseables_list": ["inglés avanzado", "conocimiento de Docker"]
}
```

**Diferencia clave:**
- **Excluyentes:** SIN ellos, no podés aplicar
- **Deseables:** Suman puntos, pero no son obligatorios

**Ejemplos de extracción:**
- "Excluyente: título de ingeniero" → requisitos_excluyentes
- "Deseable: experiencia en React" → requisitos_deseables

---

#### **10. Jornada laboral y modalidad**
```json
{
  "jornada_laboral": "completa",
  "horario_flexible": true
}
```

**Valores (jornada_laboral):**
- `completa` (8 horas, lunes a viernes)
- `part_time` (menos de 8 horas)
- `por_proyecto` (freelance)
- `turnos_rotativos` (mañana/tarde/noche)

**Ejemplos de extracción:**
- "Jornada completa, lunes a viernes 9 a 18" → completa, false
- "Part-time, 4 horas" → part_time, false
- "Horario flexible" → completa, true

---

### Prompt engineering: Cómo le pedimos al LLM

**Estructura del prompt:**

```
SISTEMA:
Eres un experto analista de recursos humanos especializado en
extraer información estructurada de ofertas laborales en español.

TAREA:
Analiza la siguiente oferta laboral y extrae SOLO la información
que esté EXPLÍCITAMENTE mencionada. NO inventes ni asumas datos.

Si un campo no se menciona, devuelve null.

FORMATO DE SALIDA:
Devuelve un JSON válido con la siguiente estructura:
{
  "experiencia_min_anios": <número o null>,
  "experiencia_max_anios": <número o null>,
  "nivel_educativo": <"secundario"|"terciario"|"universitario"|"posgrado"|null>,
  ...
}

OFERTA LABORAL:
---
[AQUÍ VA EL TEXTO DE LA OFERTA]
---

IMPORTANTE:
- Solo extrae lo que está escrito
- Si dice "deseable" o "preferentemente", va a requisitos_deseables
- Si dice "excluyente" o "indispensable", va a requisitos_excluyentes
- Si no dice nada sobre experiencia, devuelve null (NO asumas 0 años)
```

**Mejoras de v4.0 a v5.1:**

| Aspecto | v4.0 | v5.1 |
|---------|------|------|
| Instrucciones | Genéricas | Específicas con ejemplos |
| Manejo de ausencia | "Asumir 0" | "Devolver null" |
| Formato salida | Texto libre | JSON estricto |
| Validación | No validaba | Valida JSON antes de guardar |

---

### Proceso de ejecución del NLP

```
┌─────────────────────────────────────────────────────────────────┐
│ Script: procesar_ofertas_nlp_v5_1.py                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ 1. Cargar ofertas consolidadas pendientes de NLP               │
│    SELECT * FROM ofertas_consolidadas                          │
│    WHERE nlp_procesado = false                                 │
│    LIMIT 200  -- Procesar en lotes de 200                      │
│                                                                 │
│ 2. Para cada oferta:                                            │
│    a) Construir prompt con template v5.1                       │
│    b) Enviar a Ollama (POST http://localhost:11434/api/generate)│
│    c) Recibir respuesta JSON                                   │
│    d) Validar JSON (schema correcto)                           │
│    e) Guardar en ofertas_nlp                                   │
│    f) Marcar como procesada                                    │
│                                                                 │
│ 3. Si hay error:                                                │
│    - Registrar en log                                          │
│    - Marcar oferta como "nlp_error"                            │
│    - Continuar con siguiente oferta                            │
│                                                                 │
│ 4. Generar reporte:                                             │
│    - Total procesadas: 200                                     │
│    - Exitosas: 197 (98.5%)                                     │
│    - Con errores: 3 (1.5%)                                     │
│    - Tiempo promedio: 1.2 seg/oferta                           │
│    - Tiempo total: 4 minutos                                   │
└─────────────────────────────────────────────────────────────────┘
```

**Velocidad de procesamiento:**
- 1 oferta: ~1-2 segundos
- 100 ofertas: ~2-3 minutos
- 1,000 ofertas: ~20-30 minutos
- 6,521 ofertas: ~3-4 horas

---

### Validación de calidad: A/B Testing

Realizamos un test A/B con 50 ofertas procesadas con las 3 versiones.

**Resultados:**

```
┌───────────────────────────────────────────────────────────────┐
│ COMPARACIÓN A/B: v4.0 vs v5.0 vs v5.1                        │
├───────────────────────────────────────────────────────────────┤
│ Total ofertas: 50                                             │
│                                                               │
│ COBERTURA:                                                    │
│   v4.0:  50/50 (100%)                                         │
│   v5.0:  49/50 (98%)                                          │
│   v5.1:  47/50 (94%)                                          │
│                                                               │
│ QUALITY SCORE (campos completados promedio):                  │
│   v4.0:  7.89 campos/oferta                                   │
│   v5.0:  7.52 campos/oferta (-4.7% vs v4.0)                   │
│   v5.1:  8.81 campos/oferta (+11.6% vs v4.0) ✅               │
│                                                               │
│ ANÁLISIS POR CAMPO (ofertas con v5.1):                        │
│                                                               │
│ Campo                    v4.0    v5.0    v5.1   Delta         │
│ ─────────────────────────────────────────────────────────     │
│ experiencia_min_anios     38      11      16    -22           │
│ nivel_educativo           47      21      34    -13           │
│ estado_educativo          35      20      32     -3           │
│ carrera_especifica         0      11      18    +18 ✅        │
│ idioma_principal          47      27      47     +0           │
│ skills_tecnicas_list      39      36      36     -3           │
│ soft_skills_list          47      34      43     -4           │
│ beneficios_list            0      16      18    +18 ✅        │
│ requisitos_excluyentes    14      39      37    +23 ✅        │
│ requisitos_deseables       6      17      19    +13 ✅        │
│ horario_flexible           1      41      17    +16 ✅        │
│                                                               │
│ CONCLUSIÓN:                                                   │
│ v5.1 extrae MEJOR en campos complejos:                        │
│   ✅ +18 carrera_especifica                                   │
│   ✅ +18 beneficios_list                                      │
│   ✅ +23 requisitos_excluyentes                               │
│   ✅ +13 requisitos_deseables                                 │
│                                                               │
│ DECISIÓN: Activar v5.1 en producción                          │
└───────────────────────────────────────────────────────────────┘
```

**Por qué v5.1 es mejor:**
- Extrae campos difíciles que v4.0 ignoraba (carrera específica, beneficios)
- Diferencia mejor entre requisitos excluyentes vs deseables
- Menor tasa de "falsos positivos" (v4.0 inventaba datos)

---

### Tabla: `ofertas_nlp`

**Estructura:**

| Campo | Tipo | Ejemplo |
|-------|------|---------|
| `id` | Entero | 12345 |
| `id_consolidada` | Entero | 67890 (FK) |
| `experiencia_min_anios` | Entero | 3 |
| `experiencia_max_anios` | Entero | 5 |
| `nivel_educativo` | Texto | "universitario" |
| `estado_educativo` | Texto | "completo" |
| `carrera_especifica` | Texto | "Ingeniería en Sistemas" |
| `idioma_principal` | Texto | "inglés" |
| `nivel_idioma_principal` | Texto | "avanzado" |
| `skills_tecnicas_list` | JSON | `["Python", "Django", "React"]` |
| `soft_skills_list` | JSON | `["liderazgo", "trabajo en equipo"]` |
| `certificaciones_list` | JSON | `["PMP", "Scrum Master"]` |
| `salario_min` | Decimal | 300000 |
| `salario_max` | Decimal | 400000 |
| `moneda` | Texto | "ARS" |
| `beneficios_list` | JSON | `["prepaga", "capacitación"]` |
| `requisitos_excluyentes_list` | JSON | `["título universitario"]` |
| `requisitos_deseables_list` | JSON | `["inglés avanzado"]` |
| `jornada_laboral` | Texto | "completa" |
| `horario_flexible` | Booleano | true |
| `version_nlp` | Texto | "v5.1" |
| `fecha_procesamiento` | Timestamp | "2025-01-16 10:30:00" |

---

## 4.4. ETAPA 5: NORMALIZACIÓN Y ENRIQUECIMIENTO

### Normalización territorial INDEC

**Problema:**
Las ofertas mencionan ubicaciones de forma inconsistente:

```
❌ Ejemplos de ubicaciones NO normalizadas:
- "Caba"
- "Capital Federal"
- "Ciudad Autónoma de Buenos Aires"
- "CABA, Buenos Aires"
- "Bs As"
- "Buenos Aires" (¿provincia o ciudad?)
```

**Solución:**
Normalizar contra catálogo oficial de INDEC.

---

### Catálogo INDEC

**Estructura:**

```
Argentina
├─ 24 Provincias
│  ├─ Ciudad Autónoma de Buenos Aires (CABA)
│  ├─ Buenos Aires
│  ├─ Córdoba
│  ├─ Santa Fe
│  ├─ Mendoza
│  ├─ ... (20 más)
│
└─ ~4,000 Localidades
   ├─ CABA → Ciudad Autónoma de Buenos Aires
   ├─ Buenos Aires (provincia)
   │  ├─ La Plata
   │  ├─ Mar del Plata
   │  ├─ Bahía Blanca
   │  ├─ ... (135 partidos)
   │
   ├─ Córdoba (provincia)
   │  ├─ Córdoba (ciudad capital)
   │  ├─ Villa Carlos Paz
   │  ├─ Río Cuarto
   │  ├─ ... (26 departamentos)
   │
   └─ ... (más localidades)
```

---

### Proceso de normalización

```
┌─────────────────────────────────────────────────────────────────┐
│ Script: normalizar_territorios_indec.py                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ 1. Cargar catálogo INDEC                                        │
│    - 24 provincias                                              │
│    - ~4,000 localidades                                         │
│    - Aliases conocidos (ej: "Caba" = "Ciudad Autónoma...")     │
│                                                                 │
│ 2. Para cada oferta:                                            │
│    a) Leer ubicacion_raw de ofertas_consolidadas               │
│    b) Limpiar texto:                                            │
│       - Minúsculas                                              │
│       - Sin tildes                                              │
│       - Sin caracteres especiales                               │
│                                                                 │
│    c) Buscar coincidencias:                                     │
│       PASO 1: Búsqueda exacta en localidades                   │
│       PASO 2: Búsqueda en aliases                              │
│       PASO 3: Búsqueda fuzzy (similitud >85%)                  │
│       PASO 4: Buscar solo provincia si no hay localidad        │
│                                                                 │
│    d) Guardar resultado normalizado:                            │
│       - provincia_indec                                         │
│       - localidad_indec (si se encontró)                        │
│       - codigo_provincia_indec (2 dígitos)                      │
│       - codigo_localidad_indec (si corresponde)                 │
│                                                                 │
│ 3. Casos sin match:                                             │
│    - Marcar como "ubicacion_no_normalizada"                     │
│    - Agregar a reporte para revisión manual                     │
│                                                                 │
│ 4. Generar reporte:                                             │
│    - Total ofertas: 6,521                                       │
│    - Normalizadas: 6,387 (97.9%)                                │
│    - Sin match: 134 (2.1%)                                      │
└─────────────────────────────────────────────────────────────────┘
```

---

### Ejemplos de normalización

```
Entrada                              → Salida normalizada
─────────────────────────────────────────────────────────────────
"Caba"                               → Provincia: Ciudad Autónoma de Buenos Aires
                                       Código: 02

"Capital Federal"                    → Provincia: Ciudad Autónoma de Buenos Aires
                                       Código: 02

"Buenos Aires"                       → Provincia: Buenos Aires
(sin más contexto)                     Código: 06
                                       Localidad: null (provincia completa)

"Córdoba, Córdoba"                   → Provincia: Córdoba (código 14)
                                       Localidad: Córdoba (capital)

"Rosario, Santa Fe"                  → Provincia: Santa Fe (código 82)
                                       Localidad: Rosario

"Villa Carlos Paz"                   → Provincia: Córdoba (inferido)
                                       Localidad: Villa Carlos Paz

"Remoto - Todo el país"              → Provincia: null
                                       Localidad: "Remoto"
                                       (flag especial: modalidad_remota = true)
```

---

### Beneficios de la normalización territorial

**1. Análisis geográfico preciso**
```
Pregunta: ¿Cuántas ofertas hay en CABA?

❌ Sin normalización:
   WHERE ubicacion LIKE '%caba%'
   OR ubicacion LIKE '%capital federal%'
   OR ubicacion LIKE '%Ciudad Autónoma%'
   → 1,234 ofertas (probablemente incompleto)

✅ Con normalización:
   WHERE provincia_indec = 'Ciudad Autónoma de Buenos Aires'
   → 1,457 ofertas (dato preciso)
```

**2. Mapas y visualizaciones**
```
En Shiny Dashboard:
- Mapa de Argentina coloreado por cantidad de ofertas/provincia
- Drill-down: click en provincia → ver localidades
- Solo posible con normalización INDEC
```

**3. Comparaciones entre provincias**
```
TOP 5 provincias con más ofertas IT:
1. Ciudad Autónoma de Buenos Aires: 3,245 ofertas (49.8%)
2. Buenos Aires: 1,876 ofertas (28.8%)
3. Córdoba: 687 ofertas (10.5%)
4. Santa Fe: 234 ofertas (3.6%)
5. Mendoza: 98 ofertas (1.5%)
```

---

### Cálculo de permanencia de ofertas

**Pregunta clave:**
¿Cuánto tiempo permanece una oferta publicada?

**¿Por qué es importante?**
- Ofertas que duran poco (1-3 días) → Se llenan rápido (mucha demanda)
- Ofertas que duran mucho (30+ días) → Difíciles de llenar (requisitos muy específicos o mal redactadas)

---

### Proceso de cálculo

```
┌─────────────────────────────────────────────────────────────────┐
│ Script: calcular_permanencia_ofertas.py                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ 1. Para cada oferta:                                            │
│    a) fecha_publicacion (de la oferta)                          │
│    b) fecha_ultima_vista (último scraping que la vio)           │
│                                                                 │
│    c) permanencia_dias = fecha_ultima_vista - fecha_publicacion │
│                                                                 │
│ 2. Detectar ofertas cerradas:                                   │
│    Si en el scraping de hoy NO apareció una oferta que ayer    │
│    estaba online → está cerrada                                 │
│                                                                 │
│    fecha_cierre = fecha_ultimo_scraping_donde_aparecio          │
│    permanencia_final = fecha_cierre - fecha_publicacion         │
│                                                                 │
│ 3. Clasificar por duración:                                     │
│    - Muy corta: 1-3 días                                        │
│    - Corta: 4-7 días                                            │
│    - Media: 8-15 días                                           │
│    - Larga: 16-30 días                                          │
│    - Muy larga: >30 días                                        │
│                                                                 │
│ 4. Calcular estadísticas:                                       │
│    - Permanencia promedio por sector                            │
│    - Permanencia promedio por provincia                         │
│    - Permanencia promedio por tipo de puesto                    │
└─────────────────────────────────────────────────────────────────┘
```

---

### Estadísticas de permanencia

**Distribución general:**

```
┌─────────────────────────────────────────────────────────────┐
│ PERMANENCIA DE OFERTAS - Últimos 6 meses                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ Muy corta (1-3 días):     987 ofertas (15.1%)              │
│ Corta (4-7 días):       1,456 ofertas (22.3%)              │
│ Media (8-15 días):      2,134 ofertas (32.7%)              │
│ Larga (16-30 días):     1,298 ofertas (19.9%)              │
│ Muy larga (>30 días):     646 ofertas (9.9%)               │
│                                                             │
│ Permanencia promedio: 14.2 días                             │
│ Mediana: 11 días                                            │
└─────────────────────────────────────────────────────────────┘
```

**Por sector:**

```
IT/Tecnología:        10.3 días (se llenan rápido)
Administración:       15.8 días (demanda media)
Ventas/Comercial:     12.1 días (rotación alta)
Gastronomía:          8.7 días (se llenan muy rápido)
Salud:                19.4 días (difíciles de llenar)
Ingeniería:           22.6 días (requisitos específicos)
```

**Por provincia:**

```
CABA:                 12.1 días (mucha oferta y demanda)
Buenos Aires:         15.3 días
Córdoba:              14.8 días
Santa Fe:             16.2 días
Resto del país:       18.7 días (menos oferta/demanda)
```

**Insight clave:**
Ofertas con salario mencionado duran 40% menos (9.2 días vs 15.4 días).

---

## 4.5. ETAPA 6: EXPORTACIÓN - CSV v2.0

### ¿Qué es el CSV v2.0?

Es el dataset final que alimenta el **Shiny Dashboard** (frontend público).

**Archivo:** `ofertas_esco_shiny.csv`
**Tamaño:** ~6,521 ofertas × 45 columnas = ~15 MB
**Formato:** CSV con encoding UTF-8, separador `,`

---

### Estructura del CSV v2.0

**45 columnas en total:**

#### **Grupo 1: Identificación (5 columnas)**
- `id`: ID único de la oferta
- `portal`: De dónde viene (bumeran, computrabajo, etc.)
- `url`: Link original
- `fecha_publicacion`: Cuándo se publicó
- `fecha_scraping`: Cuándo la descargamos

#### **Grupo 2: Básicos (4 columnas)**
- `titulo`: Título de la oferta
- `empresa`: Nombre de la empresa
- `descripcion`: Descripción completa (limitada a 2000 caracteres para performance)
- `keyword_usada`: Qué keyword la encontró

#### **Grupo 3: Ubicación (4 columnas)**
- `provincia_indec`: Provincia normalizada INDEC
- `localidad_indec`: Localidad normalizada INDEC
- `codigo_provincia_indec`: Código INDEC de 2 dígitos
- `modalidad_trabajo`: presencial / remoto / híbrido

#### **Grupo 4: Requerimientos NLP (10 columnas)**
- `experiencia_min_anios`
- `experiencia_max_anios`
- `nivel_educativo`
- `estado_educativo`
- `carrera_especifica`
- `idioma_principal`
- `nivel_idioma_principal`
- `jornada_laboral`
- `horario_flexible`
- `version_nlp`: Versión del NLP usado (v5.1)

#### **Grupo 5: Skills y Competencias (6 columnas)**
- `skills_tecnicas_list`: JSON array
- `soft_skills_list`: JSON array
- `certificaciones_list`: JSON array
- `beneficios_list`: JSON array
- `requisitos_excluyentes_list`: JSON array
- `requisitos_deseables_list`: JSON array

#### **Grupo 6: Salario (3 columnas)**
- `salario_min`
- `salario_max`
- `moneda`

#### **Grupo 7: ESCO (8 columnas)**
- `ciuo_code`: Código CIUO-08 (4 dígitos)
- `ciuo_title`: Título de la ocupación ESCO
- `esco_skills`: JSON array con skills ESCO identificadas
- `esco_skills_count`: Cantidad de skills ESCO
- `esco_essential_count`: Cantidad de skills esenciales
- `esco_optional_count`: Cantidad de skills opcionales
- `esco_match_score`: Score de matching (0-100)
- `esco_classification`: knowledge / competencies

#### **Grupo 8: Metadata (5 columnas)**
- `permanencia_dias`: Cuántos días estuvo online
- `fecha_cierre`: Cuándo se cerró (si ya cerró)
- `sector_economico`: IT, Salud, Administración, etc.
- `sector_publico_privado`: público / privado
- `es_duplicado`: true/false

---

### Proceso de generación del CSV

```
┌─────────────────────────────────────────────────────────────────┐
│ Script: generar_csv_v2_shiny.py                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ 1. JOIN de todas las tablas:                                    │
│                                                                 │
│    SELECT                                                       │
│      o.id, o.portal, o.url, o.fecha_publicacion,               │
│      c.titulo_limpio, c.empresa_normalizada,                   │
│      c.provincia_indec, c.localidad_indec,                     │
│      n.experiencia_min_anios, n.nivel_educativo,               │
│      n.skills_tecnicas_list, n.soft_skills_list,               │
│      e.ciuo_code, e.ciuo_title, e.esco_skills,                 │
│      m.permanencia_dias, m.sector_economico                    │
│    FROM ofertas_raw o                                           │
│    JOIN ofertas_consolidadas c ON o.id = c.id_raw              │
│    LEFT JOIN ofertas_nlp n ON c.id = n.id_consolidada          │
│    LEFT JOIN ofertas_esco e ON c.id = e.id_consolidada         │
│    LEFT JOIN ofertas_metadata m ON c.id = m.id_consolidada     │
│    WHERE c.es_valida = true                                     │
│      AND c.es_duplicado = false                                 │
│                                                                 │
│ 2. Transformaciones:                                            │
│    - JSON arrays → strings serializados                        │
│    - NULL → "" (strings vacíos para CSV)                       │
│    - Fechas → formato ISO 8601                                 │
│    - Texto largo → truncar a 2000 chars                        │
│                                                                 │
│ 3. Ordenar por fecha_publicacion DESC                           │
│                                                                 │
│ 4. Exportar a CSV:                                              │
│    - Encoding: UTF-8                                            │
│    - Separador: coma (,)                                        │
│    - Quote: doble comilla (")                                   │
│    - Escape: barra invertida (\)                                │
│    - Header: incluir nombres de columnas                        │
│                                                                 │
│ 5. Validar CSV generado:                                        │
│    - Contar filas (debe ser 6,521)                              │
│    - Validar encoding (sin caracteres raros)                    │
│    - Probar carga en R/Python                                   │
│                                                                 │
│ 6. Copiar a carpeta de Shiny:                                   │
│    - D:\OEDE\Webscrapping\shiny_dashboard\data\                │
│    - ofertas_esco_shiny.csv                                     │
└─────────────────────────────────────────────────────────────────┘
```

---

### Ejemplo de registro en CSV v2.0

```csv
id,portal,titulo,empresa,provincia_indec,experiencia_min_anios,nivel_educativo,skills_tecnicas_list,ciuo_code,permanencia_dias
12345,bumeran,"Desarrollador Python Sr",Globant,"Ciudad Autónoma de Buenos Aires",3,universitario,"[""Python"",""Django"",""React""]",2512,14
```

---

## 4.6. DESAFÍOS Y LIMITACIONES

### Desafío 1: Costo computacional del NLP

**Problema:**
Procesar 6,521 ofertas con NLP toma ~4 horas.

**Causas:**
- LLM local (llama3.1:8b) no es tan rápido como GPT-4 en cloud
- CPU-bound (no tenemos GPU dedicada)
- Procesamiento secuencial (1 oferta a la vez)

**Soluciones evaluadas:**

| Solución | Ventaja | Desventaja | Decisión |
|----------|---------|------------|----------|
| GPU dedicada | 10x más rápido | Caro ($1,000+ USD) | 🟡 Futuro |
| Procesamiento paralelo | 3x más rápido | Consume más RAM | ✅ Implementar |
| Usar GPT-4 API | Muy rápido | De pago ($$), datos salen del país | ❌ No usar |
| Modelo más chico | Más rápido | Menos preciso | 🟡 Backup |

**Plan para v2.0:**
- Implementar procesamiento paralelo (3 ofertas simultáneas)
- Reducir tiempo de 4 horas a ~1.5 horas

---

### Desafío 2: Calidad variable de descripciones

**Problema:**
No todas las ofertas están bien redactadas.

**Ejemplos:**

```
❌ Oferta mal redactada:
Título: "SE BUSCA"
Descripción: "Persona para trabajo. Interesados enviar CV."

→ NLP no puede extraer NADA (no dice qué puesto, qué requisitos, dónde)

✅ Oferta bien redactada:
Título: "Desarrollador Python Sr"
Descripción: "Buscamos desarrollador Python con 3-5 años de experiencia,
título universitario en Ingeniería en Sistemas o afines, inglés avanzado.
Ofrecemos: prepaga, capacitación, trabajo remoto."

→ NLP extrae 12 campos
```

**Estadísticas:**
- 40% de ofertas bien redactadas (>1,000 caracteres, detalladas)
- 30% de ofertas medias (500-1,000 caracteres)
- 30% de ofertas vagas (<500 caracteres)

**Impacto:**
El NLP solo puede extraer información que EXISTE en el texto. Ofertas vagas → datos incompletos.

---

### Desafío 3: Ambigüedad en requisitos

**Problema:**
Algunas ofertas no aclaran si un requisito es excluyente o deseable.

**Ejemplo ambiguo:**

```
"Requisitos:
- Título universitario
- 3 años de experiencia
- Inglés avanzado
- Conocimiento de Python"

¿Cuáles son excluyentes? ¿Cuáles deseables?
```

**Solución NLP v5.1:**
Si no dice explícitamente "excluyente" o "deseable", los pone en `requisitos_excluyentes_list` (asumimos que TODO es excluyente a menos que diga lo contrario).

**Mejora futura:**
Inferir excluyencia basándonos en el tipo de requisito:
- Títulos universitarios → probablemente excluyentes
- Skills técnicas específicas → probablemente deseables

---

### Desafío 4: Salarios casi nunca mencionados

**Problema:**
Solo ~5% de ofertas mencionan salario.

**Razones:**
- Empresas prefieren negociar caso por caso
- Salarios varían según experiencia del candidato
- Competencia: no quieren que otras empresas vean cuánto pagan

**Impacto:**
Campo `salario_min` y `salario_max` casi siempre NULL.

**Alternativa evaluada:**
- Inferir salario basándonos en puesto + experiencia + ubicación
- Problema: puede ser muy inexacto (rango de error ±30%)
- Decisión: NO inferir, dejar NULL si no se menciona

---

## 4.7. ROADMAP: MEJORAS PLANIFICADAS

### Corto plazo (0-3 meses)

#### **1. Procesamiento paralelo del NLP**

**Objetivo:** Reducir tiempo de procesamiento de 4 horas a 1.5 horas

**Método:**
- Procesar 3 ofertas simultáneamente (en lugar de 1)
- Usar multithreading en Python

**Impacto:**
- ~60% reducción de tiempo
- Sin costo adicional de hardware

---

#### **2. Automatización completa del pipeline**

**Objetivo:** Pipeline end-to-end sin intervención manual

**Tareas:**
- Scraping (ya automatizado) → ejecuta diario a las 6 AM
- Consolidación (ya automatizado) → ejecuta post-scraping
- **NLP (AUTOMATIZAR)** → ejecuta post-consolidación
- **ESCO (AUTOMATIZAR)** → ejecuta post-NLP
- **Exportación CSV (AUTOMATIZAR)** → ejecuta post-ESCO

**Resultado:**
- Usuario se despierta cada mañana con datos frescos en dashboard
- 0 intervención manual

---

### Mediano plazo (3-6 meses)

#### **3. NLP v6.0 - Nuevos campos**

**Campos adicionales a extraer:**
- **Edad requerida:** "18-35 años" → edad_min: 18, edad_max: 35
- **Género:** "Buscamos mujeres" → genero: femenino
- **Tipo de contrato:** "Relación de dependencia" vs "Monotributo"
- **Turnos específicos:** "Turno noche 22-6" → turno: noche, horario: "22-6"
- **Discapacidad:** "Cupo para personas con discapacidad" → cupo_discapacidad: true

**Justificación:**
Estos campos están en las ofertas pero v5.1 no los extrae. Agregarlos mejora análisis.

---

#### **4. Dashboard de calidad del NLP**

**Objetivo:** Monitorear performance del NLP en tiempo real

**Métricas a trackear:**
- Quality Score por día (evolución)
- Campos más/menos completados
- Ofertas con errores de parsing
- Tiempo de procesamiento por oferta
- Comparación vs versiones anteriores

**Visualizaciones:**
- Gráfico de quality score en el tiempo
- Heatmap de completitud por campo
- Top 10 ofertas con peor calidad de extracción (para revisar prompts)

---

### Largo plazo (6-12 meses)

#### **5. Fine-tuning del LLM**

**Objetivo:** Entrenar llama3.1:8b específicamente para ofertas laborales argentinas

**Método:**
1. Tomar 1,000 ofertas procesadas manualmente (ground truth)
2. Fine-tunar llama3.1:8b con esas ofertas
3. Evaluar mejora en quality score
4. Si mejora >15% → desplegar modelo fine-tuned

**Beneficio esperado:**
- Quality score de 8.81 → ~10.5 campos/oferta (+19%)
- Menor tasa de errores
- Mejor manejo de jerga argentina

---

#### **6. Inferencia de salarios con ML**

**Objetivo:** Predecir salario cuando no se menciona

**Método:**
1. Entrenar modelo ML con ofertas que SÍ mencionan salario (5%)
2. Features: puesto, experiencia, educación, ubicación, empresa
3. Predecir rango salarial para ofertas sin salario

**Desafío:**
- Solo tenemos 300-400 ofertas con salario (dataset pequeño)
- Alta variabilidad (error ±25-30%)

**Decisión:**
- Implementar SOLO si logramos error <20%
- Marcar salarios inferidos como "estimado" (no "real")

---

## 4.8. RESUMEN EJECUTIVO: PIPELINE DE ANÁLISIS

### Lo que tenemos hoy

```
✅ Pipeline de 5 etapas operativo:
   1. Scraping (automatizado)
   2. Consolidación (automatizado)
   3. NLP v5.1 (manual, 4 horas)
   4. ESCO (manual, 10 minutos)
   5. Exportación CSV v2.0 (automático)

✅ NLP extrae 17 campos estructurados
✅ Quality Score: 8.81 campos/oferta (+11.6% vs v4.0)
✅ Normalización territorial INDEC (97.9% de ofertas)
✅ Cálculo de permanencia (promedio: 14.2 días)
✅ CSV v2.0 con 45 columnas listo para Shiny

🟡 Procesamiento semi-manual (NLP + ESCO)
🟡 4-6 horas de tiempo de procesamiento
🟡 Actualización semanal (debería ser diaria)
```

---

### Lo que vamos a mejorar

```
FASE 1 (0-3 meses):
→ Procesamiento paralelo del NLP (-60% tiempo)
→ Automatización completa del pipeline
→ Actualización diaria (vs semanal)

FASE 2 (3-6 meses):
→ NLP v6.0 con 6 campos adicionales
→ Dashboard de calidad del NLP
→ Optimización de prompts

FASE 3 (6-12 meses):
→ Fine-tuning del LLM (quality score >10)
→ Inferencia de salarios con ML
→ GPU dedicada para NLP
```

---

### Impacto esperado

| Métrica | Hoy | v2.0 (12 meses) | Mejora |
|---------|-----|-----------------|--------|
| **Tiempo de procesamiento** | 4-6 horas | 1.5 horas | -67% |
| **Automatización** | 60% | 100% | +40pp |
| **Quality Score** | 8.81 | 10.5 | +19% |
| **Campos extraídos** | 17 | 23 | +35% |
| **Frecuencia actualización** | Semanal | Diaria | 7x |
| **Ofertas con salario** | 5% reales | 5% reales + 95% inferidos | +95pp |

---

### Próximo paso

Con las ofertas procesadas y enriquecidas, necesitamos **clasificarlas con la ontología ESCO**. Eso lo vemos en la Sección 5: "¿CÓMO CLASIFICAMOS OCUPACIONES Y HABILIDADES? ESCO".

---

**FIN DE SECCIÓN 4**

---
