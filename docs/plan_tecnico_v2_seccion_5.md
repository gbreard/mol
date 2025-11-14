# SECCIÓN 5: ¿CÓMO CLASIFICAMOS OCUPACIONES Y HABILIDADES?
## Sistema ESCO - Lenguaje Común Europeo

---

## 5.1. ¿QUÉ ES ESCO Y POR QUÉ LO USAMOS?

### Definición: ESCO (European Skills, Competences, Qualifications and Occupations)

**ESCO** es una **ontología multilingüe** desarrollada por la Comisión Europea que clasifica:
- **Ocupaciones:** ¿Qué trabajos existen? (ej: "Desarrollador de software")
- **Skills/Habilidades:** ¿Qué competencias requieren esos trabajos? (ej: "Python", "Trabajo en equipo")
- **Calificaciones:** ¿Qué títulos/certificaciones son relevantes? (ej: "Ingeniería en Sistemas")

**Versión que usamos:** ESCO v1.2.0 (última versión estable en español)

---

### ¿Por qué necesitamos ESCO?

**Problema sin ESCO:**

```
Oferta A: "Desarrollador de software"
Oferta B: "Programador"
Oferta C: "Software Engineer"
Oferta D: "Ingeniero en desarrollo"

❓ ¿Son la misma ocupación?
   → Sí, pero escritas diferente

❓ ¿Cómo las agrupamos en reportes?
   → Imposible sin clasificación estándar
```

**Solución con ESCO:**

```
Oferta A: "Desarrollador de software"  → CIUO-08: 2512
Oferta B: "Programador"                → CIUO-08: 2512
Oferta C: "Software Engineer"          → CIUO-08: 2512
Oferta D: "Ingeniero en desarrollo"    → CIUO-08: 2512

✅ Todas clasificadas como: "Desarrolladores de software"
✅ Podemos agruparlas, contarlas, analizarlas
```

---

### Beneficios de usar ESCO

#### **1. Comparabilidad internacional**
```
Argentina (MOL):
  "Desarrollador de software" → CIUO-08: 2512

España (SEPE):
  "Desarrollador de aplicaciones" → CIUO-08: 2512

Francia (Pôle Emploi):
  "Développeur logiciel" → CIUO-08: 2512

✅ Podemos comparar mercados laborales de 3 países usando el mismo código
```

---

#### **2. Análisis agregado**
```
❌ Sin ESCO:
   Pregunta: "¿Cuántas ofertas de IT hay?"
   Respuesta: ???
   (Tendríamos que buscar manualmente: "programador", "desarrollador",
   "ingeniero software", "IT", "sistemas", etc. → incompleto)

✅ Con ESCO:
   Pregunta: "¿Cuántas ofertas de IT hay?"
   Respuesta: Filtrar por CIUO-08 grupo 25 (Profesionales en TIC)
   → 2,345 ofertas (dato preciso)
```

---

#### **3. Matching candidato-oferta**
```
Candidato:
  Skills: ["Python", "Django", "PostgreSQL"]

Ofertas en el sistema:
  Oferta A: Requiere skills ["Python", "Django", "React"]
            → Match: 2/3 (66%) ✅

  Oferta B: Requiere skills ["Java", "Spring", "MySQL"]
            → Match: 0/3 (0%) ❌

  Oferta C: Requiere skills ["Python", "Flask", "MongoDB"]
            → Match: 1/3 (33%) 🟡

✅ Sistema puede recomendar Oferta A al candidato
   (solo posible con skills estandarizadas)
```

---

#### **4. Detección de brechas de habilidades**
```
Pregunta: "¿Qué skills demanda el mercado que los candidatos NO tienen?"

Paso 1: Skills demandadas en ofertas (top 10)
  1. Python (567 ofertas)
  2. Excel avanzado (432 ofertas)
  3. Inglés avanzado (389 ofertas)
  4. SQL (301 ofertas)
  5. React (245 ofertas)
  ...

Paso 2: Skills de candidatos registrados (top 10)
  1. Excel básico (1,245 candidatos)
  2. Inglés intermedio (987 candidatos)
  3. Atención al cliente (876 candidatos)
  4. Python (234 candidatos) ← BRECHA
  5. Administración (654 candidatos)
  ...

Paso 3: Identificar brechas
  - Python: 567 ofertas vs 234 candidatos → BRECHA de 58%
  - React: 245 ofertas vs 89 candidatos → BRECHA de 64%

✅ Insight: Necesitamos capacitar más personas en Python y React
```

---

## 5.2. LA ONTOLOGÍA ESCO v1.2.0

### Estructura de la ontología

```
┌─────────────────────────────────────────────────────────────────┐
│                       ESCO v1.2.0                               │
└─────────────────────────────────────────────────────────────────┘

PILAR 1: OCUPACIONES
├─ 3,137 ocupaciones clasificadas según CIUO-08
│  ├─ Nivel 1: 10 grandes grupos
│  ├─ Nivel 2: 43 subgrupos principales
│  ├─ Nivel 3: 130 subgrupos
│  └─ Nivel 4: 436 grupos primarios
│
│  Ejemplos:
│  - CIUO-08: 2512 → "Desarrolladores de software"
│  - CIUO-08: 2431 → "Profesionales de publicidad y comercialización"
│  - CIUO-08: 5120 → "Cocineros"

PILAR 2: SKILLS/HABILIDADES
├─ 14,279 skills clasificadas en 4 jerarquías:
│  │
│  ├─ KNOWLEDGE (Conocimientos): 1,456 skills
│  │  Ejemplos: "Python", "Contabilidad financiera", "Derecho laboral"
│  │
│  ├─ COMPETENCIES (Competencias): 10,287 skills
│  │  Ejemplos: "Trabajo en equipo", "Resolución de problemas"
│  │
│  ├─ LANGUAGE SKILLS (Idiomas): 89 skills
│  │  Ejemplos: "Inglés", "Francés", "Alemán"
│  │
│  └─ TRANSVERSAL SKILLS (Transversales): 2,447 skills
│     Ejemplos: "Comunicación efectiva", "Adaptabilidad"

PILAR 3: CALIFICACIONES
└─ ~3,000 títulos y certificaciones reconocidas
   Ejemplos: "Ingeniería en Sistemas", "Licenciatura en Administración"
```

---

### Los 10 grandes grupos de ocupaciones (CIUO-08 nivel 1)

| Código | Grupo | Ejemplos | Ofertas MOL (estimado) |
|--------|-------|----------|----------------------|
| **1** | Directores y gerentes | CEO, Gerente General, Director | 234 (3.6%) |
| **2** | Profesionales científicos e intelectuales | Ingenieros, Médicos, Profesores | 1,876 (28.8%) |
| **3** | Técnicos y profesionales de nivel medio | Técnicos IT, Enfermeros, Agentes comerciales | 1,245 (19.1%) |
| **4** | Personal de apoyo administrativo | Administrativos, Secretarias, Recepcionistas | 987 (15.1%) |
| **5** | Trabajadores de servicios y vendedores | Vendedores, Cocineros, Mozos, Peluqueros | 1,456 (22.3%) |
| **6** | Agricultores y trabajadores calificados agropecuarios | Agricultores, Ganaderos | 23 (0.4%) |
| **7** | Oficiales, operarios y artesanos | Electricistas, Plomeros, Mecánicos | 345 (5.3%) |
| **8** | Operadores de instalaciones y máquinas | Choferes, Operarios de máquinas | 287 (4.4%) |
| **9** | Ocupaciones elementales | Limpieza, Seguridad, Repositores | 68 (1.0%) |
| **0** | Ocupaciones militares | Fuerzas Armadas | 0 (0.0%) |

---

### CIUO-08: La clasificación internacional

**CIUO-08** = Clasificación Internacional Uniforme de Ocupaciones (2008)

**¿Por qué "08"?**
Revisión del año 2008 (hay versiones anteriores: CIUO-88, CIUO-68).

**Estructura jerárquica de 4 niveles:**

```
Ejemplo: Desarrollador de software

Nivel 1: 2     → Profesionales científicos e intelectuales
Nivel 2: 25    → Profesionales en tecnologías de la información
Nivel 3: 251   → Diseñadores y administradores de software
Nivel 4: 2512  → Desarrolladores de software

Código completo: CIUO-08 2512
```

---

### Ejemplo detallado: CIUO-08 2512 "Desarrolladores de software"

```
┌─────────────────────────────────────────────────────────────────┐
│ CIUO-08: 2512 - Desarrolladores de software                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ DESCRIPCIÓN OFICIAL:                                            │
│ "Los desarrolladores de software investigan, analizan,          │
│ evalúan, diseñan, programan y modifican sistemas de software"  │
│                                                                 │
│ TÍTULOS ALTERNATIVOS (en español):                              │
│ - Programador de aplicaciones                                   │
│ - Ingeniero de software                                         │
│ - Desarrollador de aplicaciones                                 │
│ - Analista programador                                          │
│ - Desarrollador web                                             │
│                                                                 │
│ TAREAS TÍPICAS:                                                 │
│ - Escribir código de programación                               │
│ - Diseñar arquitectura de software                              │
│ - Probar y depurar aplicaciones                                 │
│ - Documentar código y procesos                                  │
│ - Colaborar con clientes y equipos                              │
│                                                                 │
│ SKILLS ESENCIALES (top 10):                                     │
│ 1. Programación en lenguajes específicos (Python, Java, etc.)   │
│ 2. Algoritmos y estructuras de datos                            │
│ 3. Bases de datos (SQL, NoSQL)                                  │
│ 4. Control de versiones (Git)                                   │
│ 5. Metodologías ágiles (Scrum, Kanban)                         │
│ 6. Testing y debugging                                          │
│ 7. Diseño de software                                           │
│ 8. APIs y servicios web                                         │
│ 9. Trabajo en equipo                                            │
│ 10. Resolución de problemas                                     │
│                                                                 │
│ SKILLS OPCIONALES (top 10):                                     │
│ 1. Cloud computing (AWS, Azure, GCP)                            │
│ 2. DevOps (Docker, Kubernetes, CI/CD)                           │
│ 3. Machine Learning                                             │
│ 4. Blockchain                                                   │
│ 5. Seguridad informática                                        │
│ 6. UX/UI design                                                 │
│ 7. Idiomas extranjeros (inglés avanzado)                        │
│ 8. Gestión de proyectos                                         │
│ 9. Arquitectura de sistemas                                     │
│ 10. Big Data                                                    │
│                                                                 │
│ TOTAL ASOCIACIONES: 347 skills vinculadas                       │
└─────────────────────────────────────────────────────────────────┘
```

---

## 5.3. LAS 240,000 ASOCIACIONES OCUPACIÓN-SKILL

### ¿Qué son las asociaciones?

**Asociación** = vínculo entre una **ocupación** y una **skill**, con metadata:

```json
{
  "ocupacion_ciuo": "2512",
  "ocupacion_titulo": "Desarrolladores de software",
  "skill_uri": "http://data.europa.eu/esco/skill/abc123",
  "skill_titulo": "Python",
  "relacion_tipo": "essential",
  "skill_type": "knowledge",
  "skill_reusability": "cross-sector"
}
```

---

### Tipos de relación ocupación-skill

**ESCO define 2 tipos:**

#### **1. Essential skills (Esenciales)**
Skills que son **indispensables** para desempeñar la ocupación.

```
Ocupación: Desarrollador de software (2512)

Essential skills:
✅ Programación (sin esto, NO eres desarrollador)
✅ Algoritmos y estructuras de datos
✅ Bases de datos
✅ Control de versiones (Git)
✅ Testing y debugging

Total: 89 essential skills para CIUO-08 2512
```

---

#### **2. Optional skills (Opcionales)**
Skills que **mejoran** el desempeño pero no son indispensables.

```
Ocupación: Desarrollador de software (2512)

Optional skills:
🟡 Python (puedes ser desarrollador sin saber Python, usando Java)
🟡 React (frontend, no todos los devs lo necesitan)
🟡 AWS (cloud, no todos trabajan con cloud)
🟡 Machine Learning (nicho específico)
🟡 Inglés avanzado (ayuda pero no es excluyente)

Total: 258 optional skills para CIUO-08 2512
```

---

### Distribución de las 240,000 asociaciones

```
┌─────────────────────────────────────────────────────────────────┐
│ ESTADÍSTICAS: 240,000 ASOCIACIONES                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ Por tipo de relación:                                           │
│   Essential:  87,456 asociaciones (36.4%)                       │
│   Optional:  152,544 asociaciones (63.6%)                       │
│                                                                 │
│ Por tipo de skill:                                              │
│   Knowledge:         98,234 asociaciones (40.9%)                │
│   Competencies:     126,453 asociaciones (52.7%)                │
│   Language:           8,912 asociaciones (3.7%)                 │
│   Transversal:        6,401 asociaciones (2.7%)                 │
│                                                                 │
│ Promedio de skills por ocupación:                               │
│   Essential: 27.9 skills/ocupación                              │
│   Optional: 48.6 skills/ocupación                               │
│   Total: 76.5 skills/ocupación                                  │
│                                                                 │
│ Ocupaciones con más skills asociadas:                           │
│   1. Médicos especialistas (CIUO 2212): 347 skills              │
│   2. Desarrolladores de software (CIUO 2512): 347 skills        │
│   3. Gerentes de ventas y comercialización (CIUO 1221): 289    │
│   4. Ingenieros civiles (CIUO 2142): 267 skills                │
│   5. Profesores de enseñanza secundaria (CIUO 2330): 245       │
│                                                                 │
│ Ocupaciones con menos skills asociadas:                         │
│   1. Recogedores de basura (CIUO 9613): 12 skills              │
│   2. Limpiadores de vehículos (CIUO 9122): 15 skills           │
│   3. Repartidores (CIUO 9621): 18 skills                       │
└─────────────────────────────────────────────────────────────────┘
```

---

## 5.4. CLASIFICACIÓN KNOWLEDGE VS COMPETENCIES

### ¿Cuál es la diferencia?

**KNOWLEDGE (Conocimiento):**
- Saberes **teóricos** o **técnicos** adquiridos mediante estudio/capacitación
- Se pueden **enseñar** en cursos, libros, tutoriales
- Son **específicos** de un dominio

**Ejemplos:**
- Python (lenguaje de programación)
- Contabilidad financiera
- Derecho laboral argentino
- Anatomía humana
- Marketing digital

---

**COMPETENCIES (Competencias):**
- Habilidades **prácticas** o **blandas** aplicadas en contextos reales
- Se desarrollan con **experiencia** y **práctica**
- Son más **transversales** (aplican a múltiples ocupaciones)

**Ejemplos:**
- Trabajo en equipo
- Liderazgo
- Resolución de problemas
- Comunicación efectiva
- Pensamiento crítico

---

### ¿Por qué clasificar Knowledge vs Competencies?

#### **Uso 1: Diseño de capacitaciones**

```
Brecha detectada en "Desarrollador de software":

KNOWLEDGE faltante:
- Python → Capacitación: Curso de 3 meses "Python para backend"
- React → Capacitación: Bootcamp de 6 semanas "React avanzado"

COMPETENCIES faltantes:
- Trabajo en equipo → Capacitación: Talleres vivenciales de 2 días
- Resolución de problemas → Capacitación: Metodología de casos reales

✅ Cada tipo requiere estrategia de capacitación diferente
```

---

#### **Uso 2: Matching candidato-oferta más preciso**

```
Candidato:
  Knowledge: ["Python", "Django", "PostgreSQL"]
  Competencies: ["Trabajo en equipo", "Liderazgo"]

Oferta A:
  Knowledge requerido: ["Python", "Django", "React"]
  Competencies requeridas: ["Trabajo en equipo"]

Match:
  Knowledge: 2/3 (66%)
  Competencies: 1/1 (100%)
  → Score ponderado: (66% × 0.7) + (100% × 0.3) = 76.2%

✅ Ponderamos diferente Knowledge (70%) vs Competencies (30%)
   porque Knowledge es más crítico para este puesto
```

---

#### **Uso 3: Análisis de perfiles ocupacionales**

```
Pregunta: "¿Qué ocupaciones son más intensivas en Knowledge vs Competencies?"

Intensivas en KNOWLEDGE (>70% knowledge):
- Médicos especialistas: 78% knowledge
- Desarrolladores de software: 72% knowledge
- Contadores: 75% knowledge
- Abogados: 71% knowledge

Intensivas en COMPETENCIES (>70% competencies):
- Gerentes generales: 68% competencies
- Vendedores: 73% competencies
- Profesores: 65% competencies
- Trabajadores sociales: 71% competencies

✅ Insight: Ocupaciones técnicas requieren más knowledge,
            ocupaciones de gestión/servicio requieren más competencies
```

---

### El algoritmo de clasificación de 3 niveles

ESCO no clasifica explícitamente TODAS las skills como knowledge o competencies.
Algunas tienen metadata ambigua. Necesitamos un **algoritmo de inferencia**.

---

#### **Nivel 1: Clasificación explícita (60% de skills)**

Si ESCO ya dice qué es:

```json
{
  "skill_uri": "http://data.europa.eu/esco/skill/abc123",
  "skill_titulo": "Python",
  "skill_type": "knowledge"  ← EXPLÍCITO
}
```

✅ Usar clasificación de ESCO directamente

---

#### **Nivel 2: Inferencia por URI (30% de skills)**

Si la URI contiene pistas:

```
Ejemplos:

URI: http://data.europa.eu/esco/skill/knowledge/...
→ Clasificar como: KNOWLEDGE

URI: http://data.europa.eu/esco/skill/competence/...
→ Clasificar como: COMPETENCIES

URI: http://data.europa.eu/esco/skill/language/...
→ Clasificar como: LANGUAGE (subcategoría de knowledge)

URI: http://data.europa.eu/esco/skill/transversal/...
→ Clasificar como: COMPETENCIES (transversales son competencias)
```

---

#### **Nivel 3: Inferencia por contexto (10% de skills)**

Si aún no sabemos, usar heurísticas:

```python
def clasificar_skill(skill_titulo, skill_descripcion):
    # Reglas heurísticas

    keywords_knowledge = [
        "programación", "software", "lenguaje", "base de datos",
        "contabilidad", "finanzas", "derecho", "medicina",
        "ingeniería", "matemática", "física", "química"
    ]

    keywords_competencies = [
        "trabajo en equipo", "liderazgo", "comunicación",
        "gestión", "organización", "planificación",
        "resolución de problemas", "pensamiento crítico",
        "creatividad", "adaptabilidad", "negociación"
    ]

    # Buscar keywords en título/descripción
    if any(kw in skill_titulo.lower() for kw in keywords_knowledge):
        return "knowledge"

    if any(kw in skill_titulo.lower() for kw in keywords_competencies):
        return "competencies"

    # Si no hay match, clasificar como "unknown"
    return "unknown"
```

**Resultado:**
- 60% clasificadas explícitamente
- 30% inferidas por URI
- 9% inferidas por contexto
- 1% quedan como "unknown" (revisión manual)

---

### Validación de la clasificación

**Proceso:**
1. Clasificar 14,279 skills con algoritmo de 3 niveles
2. Tomar muestra aleatoria de 200 skills
3. Revisar manualmente
4. Calcular precisión

**Resultado esperado:**
- Precisión objetivo: >95%
- Si precisión <95% → ajustar heurísticas de nivel 3

---

## 5.5. EXTRACCIÓN DESDE RDF

### ¿Qué es RDF y por qué ESCO lo usa?

**RDF** = Resource Description Framework

Es un formato estándar para representar **ontologías** (relaciones entre conceptos).

**¿Por qué ESCO usa RDF?**
- Estándar internacional (W3C)
- Permite relaciones complejas (no solo tablas planas)
- Multilingüe (mismo concepto en 27 idiomas)
- Interoperable (se puede combinar con otras ontologías)

---

### Estructura de un archivo RDF

```xml
<?xml version="1.0" encoding="UTF-8"?>
<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
         xmlns:esco="http://data.europa.eu/esco/model#">

  <!-- OCUPACIÓN -->
  <esco:Occupation rdf:about="http://data.europa.eu/esco/occupation/2512">
    <esco:code>2512</esco:code>
    <esco:preferredLabel xml:lang="es">Desarrolladores de software</esco:preferredLabel>
    <esco:preferredLabel xml:lang="en">Software developers</esco:preferredLabel>
    <esco:description xml:lang="es">
      Los desarrolladores de software investigan, analizan, evalúan,
      diseñan, programan y modifican sistemas de software
    </esco:description>

    <!-- ASOCIACIONES CON SKILLS -->
    <esco:hasEssentialSkill rdf:resource="http://data.europa.eu/esco/skill/abc123"/>
    <esco:hasOptionalSkill rdf:resource="http://data.europa.eu/esco/skill/def456"/>
  </esco:Occupation>

  <!-- SKILL -->
  <esco:Skill rdf:about="http://data.europa.eu/esco/skill/abc123">
    <esco:preferredLabel xml:lang="es">Python</esco:preferredLabel>
    <esco:preferredLabel xml:lang="en">Python</esco:preferredLabel>
    <esco:skillType>knowledge</esco:skillType>
    <esco:reuseLevel>cross-sector</esco:reuseLevel>
  </esco:Skill>

</rdf:RDF>
```

---

### Proceso de extracción RDF → SQL

```
┌─────────────────────────────────────────────────────────────────┐
│ Script: extraer_esco_desde_rdf.py                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ INPUT:                                                          │
│   - ESCO_v1.2.0_es.rdf (archivos RDF en español)               │
│   - occupations.rdf (3,137 ocupaciones)                         │
│   - skills.rdf (14,279 skills)                                  │
│                                                                 │
│ PASO 1: Parsear RDF                                             │
│   - Usar librería rdflib (Python)                               │
│   - Cargar archivos RDF en memoria                              │
│   - Construir grafo de relaciones                               │
│                                                                 │
│ PASO 2: Extraer OCUPACIONES                                     │
│   Query SPARQL:                                                 │
│   SELECT ?occ ?code ?label_es ?label_en ?description           │
│   WHERE {                                                       │
│     ?occ rdf:type esco:Occupation .                            │
│     ?occ esco:code ?code .                                     │
│     ?occ esco:preferredLabel ?label_es .                       │
│     FILTER (lang(?label_es) = "es")                            │
│   }                                                             │
│                                                                 │
│   Resultado: 3,137 ocupaciones                                  │
│                                                                 │
│ PASO 3: Extraer SKILLS                                          │
│   Query SPARQL:                                                 │
│   SELECT ?skill ?label_es ?skill_type ?reuse_level             │
│   WHERE {                                                       │
│     ?skill rdf:type esco:Skill .                               │
│     ?skill esco:preferredLabel ?label_es .                     │
│     ?skill esco:skillType ?skill_type .                        │
│     FILTER (lang(?label_es) = "es")                            │
│   }                                                             │
│                                                                 │
│   Resultado: 14,279 skills                                      │
│                                                                 │
│ PASO 4: Extraer ASOCIACIONES                                    │
│   Query SPARQL:                                                 │
│   SELECT ?occ ?skill ?relation_type                             │
│   WHERE {                                                       │
│     {                                                           │
│       ?occ esco:hasEssentialSkill ?skill .                     │
│       BIND("essential" AS ?relation_type)                      │
│     } UNION {                                                   │
│       ?occ esco:hasOptionalSkill ?skill .                      │
│       BIND("optional" AS ?relation_type)                       │
│     }                                                           │
│   }                                                             │
│                                                                 │
│   Resultado: ~240,000 asociaciones                              │
│                                                                 │
│ PASO 5: Guardar en SQLite                                       │
│   - Tabla: esco_occupations (3,137 registros)                  │
│   - Tabla: esco_skills (14,279 registros)                      │
│   - Tabla: esco_associations (240,000 registros)                │
│                                                                 │
│ PASO 6: Aplicar clasificación Knowledge vs Competencies         │
│   - Ejecutar algoritmo de 3 niveles                             │
│   - Actualizar columna skill_classification                     │
│                                                                 │
│ PASO 7: Crear índices                                           │
│   - Índice en ciuo_code (búsquedas por código)                 │
│   - Índice en skill_titulo (búsquedas por nombre)              │
│   - Índice en relation_type (filtrar essential/optional)        │
│                                                                 │
│ OUTPUT:                                                         │
│   - bumeran_scraping.db actualizada con tablas ESCO            │
│   - Reporte de extracción (estadísticas)                        │
│   - Log de warnings/errores                                     │
│                                                                 │
│ TIEMPO ESTIMADO: ~15 minutos                                    │
└─────────────────────────────────────────────────────────────────┘
```

---

### Tablas SQL generadas

#### **Tabla 1: `esco_occupations`**

| Campo | Tipo | Descripción | Ejemplo |
|-------|------|-------------|---------|
| `id` | Entero | ID autoincremental | 1 |
| `uri` | Texto | URI ESCO única | "http://data.europa.eu/esco/occupation/2512" |
| `ciuo_code` | Texto | Código CIUO-08 (4 dígitos) | "2512" |
| `titulo_es` | Texto | Nombre en español | "Desarrolladores de software" |
| `titulo_en` | Texto | Nombre en inglés | "Software developers" |
| `descripcion_es` | Texto | Descripción en español | "Los desarrolladores de software..." |
| `grupo_nivel_1` | Texto | Gran grupo (1 dígito) | "2" (Profesionales) |
| `grupo_nivel_2` | Texto | Subgrupo principal (2 dígitos) | "25" (Profesionales TIC) |
| `grupo_nivel_3` | Texto | Subgrupo (3 dígitos) | "251" (Diseñadores de software) |

**Total registros:** 3,137

---

#### **Tabla 2: `esco_skills`**

| Campo | Tipo | Descripción | Ejemplo |
|-------|------|-------------|---------|
| `id` | Entero | ID autoincremental | 1 |
| `uri` | Texto | URI ESCO única | "http://data.europa.eu/esco/skill/abc123" |
| `titulo_es` | Texto | Nombre en español | "Python" |
| `titulo_en` | Texto | Nombre en inglés | "Python" |
| `descripcion_es` | Texto | Descripción | "Lenguaje de programación..." |
| `skill_type` | Texto | Tipo según ESCO | "knowledge" |
| `skill_classification` | Texto | Clasificación MOL | "knowledge" |
| `reuse_level` | Texto | Reutilización | "cross-sector" |

**Total registros:** 14,279

---

#### **Tabla 3: `esco_associations`**

| Campo | Tipo | Descripción | Ejemplo |
|-------|------|-------------|---------|
| `id` | Entero | ID autoincremental | 1 |
| `ocupacion_uri` | Texto | FK a esco_occupations | "http://...occupation/2512" |
| `skill_uri` | Texto | FK a esco_skills | "http://...skill/abc123" |
| `relation_type` | Texto | "essential" o "optional" | "essential" |

**Total registros:** ~240,000

---

## 5.6. PROCESO DE MATCHING OFERTAS → ESCO

### ¿Cómo asignamos una ocupación ESCO a cada oferta?

**Input:**
- Título de la oferta: "Desarrollador Python Sr"
- Descripción: "Buscamos desarrollador con experiencia en Python, Django..."
- Skills extraídas por NLP: ["Python", "Django", "React"]

**Output:**
- Ocupación ESCO: CIUO-08 2512 "Desarrolladores de software"
- Match score: 87%

---

### Algoritmo de matching de 4 pasos

#### **PASO 1: Matching por título (50% del score)**

```
┌─────────────────────────────────────────────────────────────────┐
│ Buscar coincidencia entre título de oferta y títulos ESCO       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ Título oferta: "Desarrollador Python Sr"                        │
│                                                                 │
│ Candidatos ESCO:                                                │
│   1. "Desarrolladores de software" (CIUO 2512)                  │
│      Similitud: 85% ✅                                           │
│                                                                 │
│   2. "Desarrolladores de aplicaciones" (CIUO 2513)              │
│      Similitud: 78% 🟡                                           │
│                                                                 │
│   3. "Desarrolladores web y multimedia" (CIUO 2166)             │
│      Similitud: 72% 🟡                                           │
│                                                                 │
│ Seleccionar top 3 candidatos con similitud >70%                 │
└─────────────────────────────────────────────────────────────────┘
```

**Algoritmo de similitud:**
- Distancia de Levenshtein (caracteres)
- TF-IDF + similitud coseno (palabras)
- Normalización: minúsculas, sin tildes, sin stopwords

---

#### **PASO 2: Matching por skills (40% del score)**

```
┌─────────────────────────────────────────────────────────────────┐
│ Para cada candidato ESCO, calcular overlap de skills            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ Skills de la oferta (NLP):                                       │
│   ["Python", "Django", "React", "PostgreSQL", "Git"]            │
│                                                                 │
│ Candidato 1: CIUO 2512 "Desarrolladores de software"            │
│   Essential skills (89 total):                                  │
│     ["Programación", "Algoritmos", "Bases de datos",            │
│      "Control de versiones", ...]                               │
│                                                                 │
│   Optional skills (258 total):                                  │
│     ["Python", "Django", "React", "PostgreSQL", "Git", ...]     │
│                                                                 │
│   Match:                                                        │
│     - 3/5 skills de la oferta están en optional (60%)           │
│     - 2/5 skills relacionados con essential (40%)               │
│     - Score: (60% × 1.0) + (40% × 0.5) = 80%                    │
│                                                                 │
│ Candidato 2: CIUO 2513 "Desarrolladores de aplicaciones"        │
│   Match: 65%                                                    │
│                                                                 │
│ Candidato 3: CIUO 2166 "Desarrolladores web"                    │
│   Match: 72%                                                    │
└─────────────────────────────────────────────────────────────────┘
```

---

#### **PASO 3: Matching por descripción (10% del score)**

```
Buscar keywords en descripción de la oferta que coincidan
con descripción de la ocupación ESCO.

Ejemplo:
Descripción oferta: "...diseñar, programar y modificar sistemas..."
Descripción ESCO 2512: "...diseñan, programan y modifican sistemas..."

Coincidencia: 90%
```

---

#### **PASO 4: Calcular score final**

```
┌─────────────────────────────────────────────────────────────────┐
│ CIUO 2512 "Desarrolladores de software"                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ Paso 1 - Título:       85% (peso 50%) = 42.5 puntos             │
│ Paso 2 - Skills:       80% (peso 40%) = 32.0 puntos             │
│ Paso 3 - Descripción:  90% (peso 10%) =  9.0 puntos             │
│                                                                 │
│ SCORE FINAL: 83.5%                                              │
│                                                                 │
│ ✅ Si score >75% → MATCH CONFIRMADO                             │
│ 🟡 Si score 50-75% → MATCH PROBABLE (revisar manualmente)       │
│ ❌ Si score <50% → NO MATCH (buscar otros candidatos)           │
└─────────────────────────────────────────────────────────────────┘
```

**Decisión:**
- Asignar oferta a CIUO 2512 con confidence score 83.5%

---

### Casos especiales

#### **Caso 1: Título ambiguo**

```
Título: "Analista"

Candidatos ESCO:
- Analista de sistemas (CIUO 2511)
- Analista financiero (CIUO 2413)
- Analista de marketing (CIUO 2431)
- Analista de datos (CIUO 2161)

→ Imposible decidir solo por título
→ Priorizar PASO 2 (skills) con peso 70% en lugar de 40%
```

---

#### **Caso 2: Ningún candidato con score >50%**

```
Título: "Community Manager"

Candidatos ESCO:
- Profesionales de publicidad (CIUO 2431): 45%
- Especialistas en redes sociales (CIUO 2166): 48%

→ Ninguno supera 50%
→ Marcar como "esco_match_manual_review"
→ Analista humano decide
```

---

#### **Caso 3: Dos candidatos con scores muy similares**

```
Título: "Desarrollador Full Stack"

Candidatos:
- Desarrolladores de software (CIUO 2512): 82%
- Desarrolladores web (CIUO 2166): 81%

→ Diferencia <5%
→ Marcar ambos como candidatos
→ Permitir en dashboard filtrar por cualquiera de los dos
```

---

## 5.7. ESTADO ACTUAL Y ROADMAP

### 🚨 ESTADO CRÍTICO: Tablas ESCO VACÍAS

**Situación actual:**

```sql
SELECT COUNT(*) FROM esco_occupations;
-- Resultado: 0

SELECT COUNT(*) FROM esco_skills;
-- Resultado: 0

SELECT COUNT(*) FROM esco_associations;
-- Resultado: 0
```

**Las tablas existen pero NO tienen datos.**

**Consecuencia:**
- NO podemos clasificar ofertas con ESCO
- Dashboard público NO puede mostrar análisis por ocupación ESCO
- NO podemos hacer matching candidato-oferta
- NO podemos identificar brechas de habilidades

---

### ¿Por qué están vacías?

**Razón:** El script `extraer_esco_desde_rdf.py` **nunca se ejecutó** en producción.

**Bloqueadores identificados:**
1. **Archivos RDF no descargados:**
   - Los archivos ESCO v1.2.0 en español (~350 MB) no están en el servidor
   - Se deben descargar desde: https://esco.ec.europa.eu/en/use-esco/download

2. **Librería rdflib no instalada:**
   - Requerimiento: `pip install rdflib==6.3.2`

3. **Script incompleto:**
   - Falta implementar clasificación Knowledge vs Competencies
   - Falta validación de datos extraídos

---

### PRIORIDAD MÁXIMA: Poblar tablas ESCO

**Esto es CRÍTICO para v2.0**. Sin ESCO, el sistema pierde 50% de su valor.

---

### Roadmap: Implementación completa de ESCO

#### **FASE 1: Extracción y carga (Semana 1-2)**

**Tareas:**
1. Descargar archivos RDF de ESCO v1.2.0 en español
2. Instalar rdflib y dependencias
3. Completar script `extraer_esco_desde_rdf.py`
4. Ejecutar extracción RDF → SQL
5. Validar datos cargados (3,137 ocupaciones, 14,279 skills, ~240K asociaciones)

**Entregable:**
- Tablas ESCO pobladas correctamente
- Reporte de extracción con estadísticas

---

#### **FASE 2: Clasificación Knowledge vs Competencies (Semana 3)**

**Tareas:**
1. Implementar algoritmo de 3 niveles
2. Clasificar 14,279 skills
3. Validar muestra aleatoria de 200 skills (precisión >95%)
4. Actualizar tabla esco_skills con clasificación

**Entregable:**
- 14,279 skills clasificadas
- Reporte de precisión de clasificación

---

#### **FASE 3: Matching automático ofertas → ESCO (Semana 4-5)**

**Tareas:**
1. Implementar algoritmo de matching de 4 pasos
2. Procesar 6,521 ofertas existentes
3. Validar matching con muestra de 100 ofertas
4. Ajustar pesos si precisión <80%

**Entregable:**
- 6,521 ofertas clasificadas con ESCO
- Distribución de ofertas por ocupación CIUO-08
- Reporte de calidad de matching

---

#### **FASE 4: Re-matching con asociaciones (Semana 6)**

**Objetivo:** Mejorar matching usando las 240K asociaciones ocupación-skill

**Método mejorado:**

```
Matching v1 (FASE 3):
  Solo usa títulos y skills de la oferta

Matching v2 (FASE 4):
  Usa títulos + skills + ASOCIACIONES ESCO

  Ejemplo:
  Oferta con skill "Django"

  → Buscar en esco_associations qué ocupaciones tienen "Django"
  → CIUO 2512 tiene "Django" como optional skill
  → CIUO 2166 tiene "Django" como essential skill

  → Aumentar score de CIUO 2166 (más probable)
```

**Resultado esperado:**
- Precisión de matching: 75% → 85%

---

#### **FASE 5: Dashboard ESCO (Semana 7-8)**

**Tareas:**
1. Agregar visualizaciones ESCO a Shiny Dashboard
2. Panel: "Análisis por Ocupación"
   - Top 10 ocupaciones con más ofertas
   - Distribución de ofertas por gran grupo CIUO-08
   - Mapa de calor: ocupación × provincia
3. Panel: "Análisis de Skills"
   - Top 20 skills más demandadas
   - Skills emergentes (crecimiento >50% último año)
   - Brechas de skills (oferta vs demanda)

**Entregable:**
- Dashboard Shiny con análisis ESCO completo

---

#### **FASE 6: Matching candidato-oferta (Semana 9-12)**

**Requisitos previos:**
- Tener base de datos de candidatos (fuera de scope actual)
- Candidatos con skills registradas

**Funcionalidad:**
```
Input:
  Candidato ID: 12345
  Skills: ["Python", "Django", "React"]

Output:
  Top 10 ofertas compatibles:
  1. Oferta #4567 - Desarrollador Python Sr - Match 89%
  2. Oferta #8901 - Full Stack Developer - Match 82%
  3. Oferta #2345 - Backend Engineer - Match 78%
  ...
```

**Algoritmo:**
1. Cargar skills del candidato
2. Para cada oferta:
   - Calcular overlap de skills
   - Calcular overlap de ocupación (si candidato tiene experiencia previa)
   - Calcular score ponderado
3. Ordenar por score descendente
4. Devolver top 10

**Entregable:**
- API de matching candidato-oferta
- Integración con dashboard de candidatos (si existe)

---

## 5.8. DESAFÍOS Y LIMITACIONES

### Desafío 1: ESCO no cubre todas las ocupaciones argentinas

**Problema:**
ESCO es europeo. Algunas ocupaciones típicas de Argentina no están.

**Ejemplos:**

```
❌ Ocupaciones NO en ESCO:
- "Fletero" (transporte informal)
- "Changarin" (trabajador de la construcción informal)
- "Vendedor ambulante" (ventas informales)

✅ Ocupaciones SÍ en ESCO (aproximadas):
- "Conductor de camión" (CIUO 8322) → similar a "fletero"
- "Peón de construcción" (CIUO 9313) → similar a "changarin"
- "Vendedor callejero" (CIUO 5211) → similar a "vendedor ambulante"
```

**Solución:**
- Mapear ocupaciones argentinas a las más cercanas en ESCO
- Crear tabla de "aliases" local: `esco_aliases_argentina`
- Ejemplo: "Fletero" → mapear a CIUO 8322 "Conductor de camión"

---

### Desafío 2: Skills tecnológicas evolucionan rápido

**Problema:**
ESCO v1.2.0 es de 2020. Tecnologías nuevas no están.

**Ejemplos:**

```
❌ Skills NO en ESCO v1.2.0:
- "ChatGPT" (2022)
- "GitHub Copilot" (2021)
- "Rust" (lenguaje emergente)
- "Next.js 13" (framework reciente)

✅ Skills SÍ en ESCO v1.2.0:
- "Python" ✅
- "React" ✅
- "Docker" ✅
```

**Solución:**
- Mantener tabla complementaria: `esco_skills_extended`
- Agregar skills nuevas manualmente cada 6 meses
- Cuando salga ESCO v1.3.0, migrar

---

### Desafío 3: Matching nunca es 100% preciso

**Realidad:**
- Matching automático alcanza ~80-85% de precisión
- 15-20% de ofertas necesitan revisión manual

**Casos difíciles:**

```
Título ambiguo:
"Responsable de Cuentas"
¿Es CIUO 2431 (Marketing) o CIUO 3313 (Contabilidad)?
→ Necesita revisión manual

Ocupación híbrida:
"Desarrollador Full Stack con foco en UX"
¿Es CIUO 2512 (Dev) o CIUO 2166 (Diseñador web)?
→ Podría ser ambos

Título en inglés:
"Senior DevOps Engineer"
Matching funciona peor en inglés (ESCO es en español)
→ Necesita traducción automática
```

**Solución:**
- Marcar ofertas con score <75% para revisión manual
- Dashboard técnico con lista de ofertas pendientes
- Analista revisa 100-150 ofertas/semana (~1 hora)

---

## 5.9. RESUMEN EJECUTIVO: SISTEMA ESCO

### Lo que DEBERÍA tener (objetivo v2.0)

```
✅ Ontología ESCO v1.2.0 cargada:
   - 3,137 ocupaciones CIUO-08
   - 14,279 skills
   - 240,000 asociaciones ocupación-skill

✅ Clasificación Knowledge vs Competencies:
   - Algoritmo de 3 niveles implementado
   - 14,279 skills clasificadas (precisión >95%)

✅ Matching automático ofertas → ESCO:
   - 6,521 ofertas clasificadas
   - Precisión: ~85%
   - 15% requiere revisión manual

✅ Dashboard con análisis ESCO:
   - Top ocupaciones con más demanda
   - Skills más demandadas
   - Brechas de habilidades
   - Análisis Knowledge vs Competencies

✅ Matching candidato-oferta:
   - API funcional
   - Top 10 ofertas recomendadas por candidato
```

---

### Lo que tenemos HOY (estado crítico)

```
❌ Tablas ESCO vacías (0 registros)
❌ Script de extracción RDF incompleto
❌ Archivos RDF no descargados
❌ NO hay clasificación ESCO de ofertas
❌ Dashboard sin análisis ESCO
❌ NO hay matching candidato-oferta
```

---

### Plan de acción urgente

```
SEMANA 1-2 (CRÍTICO):
→ Descargar RDF de ESCO v1.2.0
→ Completar script extracción
→ Poblar tablas ESCO (3,137 + 14,279 + 240K registros)

SEMANA 3 (ALTA PRIORIDAD):
→ Implementar clasificación Knowledge vs Competencies
→ Validar precisión >95%

SEMANA 4-5 (ALTA PRIORIDAD):
→ Implementar matching automático
→ Clasificar 6,521 ofertas existentes
→ Validar precisión >80%

SEMANA 6 (MEDIA PRIORIDAD):
→ Re-matching con asociaciones (mejorar a 85%)

SEMANA 7-8 (MEDIA PRIORIDAD):
→ Dashboard ESCO en Shiny

SEMANA 9-12 (BAJA PRIORIDAD):
→ Matching candidato-oferta (requiere BD de candidatos)
```

---

### Impacto esperado

| Métrica | Hoy | Con ESCO (v2.0) | Mejora |
|---------|-----|-----------------|--------|
| **Ofertas clasificadas** | 0% | 100% | +100pp |
| **Precisión clasificación** | N/A | 85% | N/A |
| **Análisis por ocupación** | ❌ No disponible | ✅ Disponible | Nueva funcionalidad |
| **Análisis de skills** | ❌ No disponible | ✅ Disponible | Nueva funcionalidad |
| **Matching candidato-oferta** | ❌ No disponible | ✅ Disponible | Nueva funcionalidad |
| **Comparabilidad internacional** | ❌ No | ✅ Sí (27 países UE) | Nuevo valor |

---

### Próximo paso

Con las ofertas clasificadas por ESCO, podemos **visualizarlas en dashboards interactivos**. Eso lo vemos en la Sección 6: "¿CÓMO SE VE EL DASHBOARD NUEVO? Interfaz de Usuario".

---

**FIN DE SECCIÓN 5**

---
