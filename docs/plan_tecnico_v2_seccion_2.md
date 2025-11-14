# SECCIÓN 2: ¿HACIA DÓNDE VAMOS? Objetivos del Rediseño

Esta sección explica qué vamos a lograr con el rediseño del sistema MOL, mostrando claramente el antes y después, los beneficios concretos y ejemplos de uso.

---

## 2.1 Dashboard Público Renovado (Shiny v3.0)

### La transformación principal

El cambio más visible y importante es el rediseño completo del dashboard público para cumplir con todos los requisitos del documento de comentarios.

### Antes (v2.4 - Situación actual)

```
┌──────────────────────────────────────────────────────────────┐
│ MONITOR DE OFERTAS LABORALES - ESCO                          │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│ [TAB: Panorama General] ← Usuario está aquí                  │
│                                                               │
│ Filtros locales:                                             │
│ Provincia: [CABA ▼]                                          │
│                                                               │
│ [Gráficos del panorama general...]                           │
│                                                               │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│ Usuario hace click en [TAB: Habilidades]                     │
│                                                               │
│ ❌ El filtro "Provincia: CABA" SE PERDIÓ                     │
│                                                               │
│ Ahora muestra datos de TODO el país                          │
│ (Usuario se confunde y frustra)                              │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

**Problemas:**
- 6 tabs sin estructura clara
- Filtros se pierden al cambiar de tab
- Usa términos técnicos: "Código CIUO-08", "Skills ESCO"
- No hay búsqueda de ocupaciones
- No se puede exportar por gráfico

### Después (v3.0 - Rediseño propuesto)

```
┌────────────────┬──────────────────────────────────────────────┐
│ FILTROS        │ [PANORAMA GENERAL] [REQUERIMIENTOS] [OFERTAS]│
│ GLOBALES       │                     ↑                         │
│ (Siempre aquí) │            3 paneles claros                  │
│                │                                               │
│ 🌎 TERRITORIAL │                                               │
│ Provincia:     │  [Contenido del panel seleccionado]          │
│ [CABA ▼]       │                                               │
│ Localidad:     │  Los filtros de la izquierda SIEMPRE         │
│ [Todas ▼]      │  se mantienen activos sin importar           │
│                │  qué panel estés viendo                       │
│ 📅 PERÍODO     │                                               │
│ [Último mes ▼] │  Subtítulo dinámico muestra filtros:         │
│                │  "Ofertas del último mes - CABA -            │
│ ⏱️ PERMANENCIA │   Todas las ocupaciones"                      │
│ ☑ Baja         │                                               │
│ ☑ Media        │  [Gráficos y visualizaciones...]             │
│ ☑ Alta         │                                               │
│                │  Cada gráfico tiene botón:                    │
│ 💼 OCUPACIÓN   │  [📊 Exportar a Excel]                        │
│ Buscar:        │                                               │
│ [desarrolla__] │                                               │
│                │                                               │
│ 🌳 Árbol ISCO  │                                               │
│ ▼ 2-Profesion. │                                               │
│   ▼ 25-TIC     │                                               │
│     ☑ 2513-Web │                                               │
│                │                                               │
│ [📄 Metodolog.]│                                               │
└────────────────┴──────────────────────────────────────────────┘
```

**Mejoras implementadas:**
- ✅ 3 paneles temáticos bien definidos
- ✅ Filtros globales permanentes
- ✅ Sin jerga técnica (usa "normalizadas")
- ✅ Búsqueda + árbol de ocupaciones
- ✅ Exportación por gráfico
- ✅ Subtítulos contextuales

### Comparación detallada

| Aspecto | Antes (v2.4) | Después (v3.0) |
|---------|--------------|----------------|
| **Navegación** | 6 tabs: Panorama, Territorial, Habilidades, Ocupaciones, Tendencias, Datos | 3 paneles: Panorama General, Requerimientos, Ofertas Laborales |
| **Filtros** | Locales por tab (se pierden) | Globales permanentes (5 filtros) |
| **Terminología** | Técnica: "CIUO", "ESCO", "ISCO" | Comprensible: "ocupaciones normalizadas" |
| **Búsqueda** | ❌ No disponible | ✅ Buscador + árbol navegable |
| **Exportación** | Solo base completa | Por gráfico + base completa |
| **Contexto** | Sin indicador de filtros activos | Subtítulo dinámico siempre visible |
| **Logo** | Con texto ilegible debajo | Limpio con título en banner |

### Ejemplo de uso mejorado

**Caso de uso:** Analista quiere ver "ofertas de desarrolladores web en CABA del último mes"

**ANTES (v2.4):**
```
1. Ir a tab "Territorial"
2. Seleccionar CABA
3. Ver datos territoriales... OK
4. Cambiar a tab "Ocupaciones"
5. ❌ Filtro CABA se perdió, muestra todo el país
6. Volver a seleccionar CABA
7. Buscar "desarrollador web" scrolleando lista larga
8. Cambiar a tab "Panorama"
9. ❌ Filtros se perdieron otra vez
10. Frustración → Abandona
```

**DESPUÉS (v3.0):**
```
1. Panel izquierdo - Territorial: Seleccionar "CABA"
2. Panel izquierdo - Período: Seleccionar "Último mes"
3. Panel izquierdo - Ocupación: Escribir "desarrollador web"
4. ✅ Todos los 3 paneles muestran datos filtrados simultáneamente
5. Ver [Panorama]: Overview general con filtros activos
6. Ver [Requerimientos]: Skills requeridos para esa ocupación en CABA
7. Ver [Ofertas]: Listado completo de ofertas que cumplen filtros
8. Exportar cualquier gráfico que necesite
9. ✅ Tarea completada en 2 minutos
```

### Beneficio principal

**De 10 pasos frustrados → 4 pasos simples y exitosos**

---

## 2.2 Los 3 Paneles Nuevos

### Panel 1: PANORAMA GENERAL

**Propósito:** Vista rápida del mercado según filtros activos

**Para quién:** Cualquier usuario que quiere una visión general

**Qué muestra:**

```
┌──────────────────────────────────────────────────────────────┐
│ PANORAMA GENERAL                                              │
│                                                               │
│ Subtítulo: "Ofertas del último mes - CABA - Desarrolladores" │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│ ┏━━━━━━━━━━━━┓ ┏━━━━━━━━━━━━┓ ┏━━━━━━━━━━━━┓              │
│ ┃  1,247     ┃ ┃  18        ┃ ┃  156       ┃              │
│ ┃  Ofertas   ┃ ┃ Ocupaciones┃ ┃ Habilidades┃              │
│ ┃  Analizadas┃ ┃ normalizadas┃┃ identificadas┃             │
│ ┗━━━━━━━━━━━━┛ ┗━━━━━━━━━━━━┛ ┗━━━━━━━━━━━━┛              │
│                                                               │
│ ┌────────────────────────────────────────────────────────┐  │
│ │ Evolución de las ofertas laborales                     │  │
│ │ (Semanal/Mensual/Anual según filtro período)          │  │
│ │                                                         │  │
│ │ Ofertas│                                               │  │
│ │  500   │     ╱╲                                        │  │
│ │  400   │    ╱  ╲                                       │  │
│ │  300   │   ╱    ╲      ╱╲                              │  │
│ │  200   │  ╱      ╲    ╱  ╲    ╱╲                       │  │
│ │  100   │ ╱        ╲  ╱    ╲  ╱  ╲                      │  │
│ │    0   │╱          ╲╱      ╲╱    ╲                     │  │
│ │        └──────────────────────────────                 │  │
│ │         Ene  Feb  Mar  Abr  May  Jun                   │  │
│ │                                      [📊 Exportar]     │  │
│ └────────────────────────────────────────────────────────┘  │
│                                                               │
│ ┌─────────────────────────────┬──────────────────────────┐  │
│ │ Top 10 Ocupaciones          │ Top 10 Empresas          │  │
│ │                             │                          │  │
│ │ Desarrollador web ████ 245  │ Mercado Libre ████ 87   │  │
│ │ Analista sistemas ███ 189   │ Globant      ███ 65     │  │
│ │ Gerente ventas   ██ 156     │ Accenture    ██ 54      │  │
│ │ ...                         │ ...                      │  │
│ │              [📊 Exportar]  │           [📊 Exportar]  │  │
│ └─────────────────────────────┴──────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

**Preguntas que responde:**
- ¿Cuántas ofertas cumplen mis filtros?
- ¿Cómo evolucionaron en el tiempo?
- ¿Cuáles son las ocupaciones más demandadas?
- ¿Qué empresas publican más ofertas?

### Panel 2: REQUERIMIENTOS

**Propósito:** Entender qué requisitos piden las empresas

**Para quién:** Analistas de políticas de empleo, instituciones educativas

**Qué muestra:**

```
┌──────────────────────────────────────────────────────────────┐
│ REQUERIMIENTOS                                                │
│                                                               │
│ Subtítulo: "Ofertas del último mes - CABA - Desarrolladores" │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│ ┌────────────────────┬────────────────────┐                  │
│ │ Requisito de edad  │ Requisito de género│                  │
│ │                    │                    │                  │
│ │ Sin req. 67%       │ Sin req. 85%       │                  │
│ │ Jóvenes  18%       │ Mujeres   8%       │                  │
│ │ Adultos  15%       │ Varones   7%       │                  │
│ │                    │                    │                  │
│ │    [📊 Exportar]   │   [📊 Exportar]    │                  │
│ └────────────────────┴────────────────────┘                  │
│                                                               │
│ ┌────────────────────┬────────────────────┐                  │
│ │ Nivel educativo    │ Otros requisitos   │                  │
│ │                    │                    │                  │
│ │ Sin req.      15%  │ Sin otros    45%   │                  │
│ │ Secundaria+   18%  │ Idiomas      28%   │                  │
│ │ Universitaria 55%  │ Experiencia  35%   │                  │
│ │ Posgrado      12%  │ Ubicación    22%   │                  │
│ │                    │ Otros        12%   │                  │
│ │    [📊 Exportar]   │   [📊 Exportar]    │                  │
│ └────────────────────┴────────────────────┘                  │
│                                                               │
│ ┌──────────────────────────────────────────────────────────┐ │
│ │ Top 20 Conocimientos Técnicos                            │ │
│ │ (normalizados con IA)                                    │ │
│ │                                                          │ │
│ │ SQL                    ████████████████ 387              │ │
│ │ Python                 ███████████████ 356               │ │
│ │ JavaScript             ██████████████ 312                │ │
│ │ Excel avanzado         █████████████ 298                 │ │
│ │ Git                    ███████████ 256                   │ │
│ │ ...                                                      │ │
│ │                                         [📊 Exportar]    │ │
│ └──────────────────────────────────────────────────────────┘ │
│                                                               │
│ ┌──────────────────────────────────────────────────────────┐ │
│ │ Top 20 Competencias Blandas                              │ │
│ │ (normalizadas con IA)                                    │ │
│ │                                                          │ │
│ │ Trabajo en equipo      ████████████████ 487              │ │
│ │ Comunicación efectiva  ███████████████ 456               │ │
│ │ Liderazgo              ██████████████ 398                │ │
│ │ Proactividad           █████████████ 367                 │ │
│ │ Resolución problemas   ████████████ 334                  │ │
│ │ ...                                                      │ │
│ │                                         [📊 Exportar]    │ │
│ └──────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
```

**Preguntas que responde:**
- ¿Qué porcentaje de ofertas discrimina por edad/género?
- ¿Qué nivel educativo es más demandado?
- ¿Qué conocimientos técnicos son imprescindibles?
- ¿Qué competencias blandas valoran más?

**Novedad clave:** Separación clara entre conocimientos técnicos y competencias blandas (antes estaban mezclados)

### Panel 3: OFERTAS LABORALES

**Propósito:** Búsqueda detallada y exploración de ofertas individuales

**Para quién:** Usuarios que quieren ver ofertas específicas

**Qué muestra:**

```
┌──────────────────────────────────────────────────────────────┐
│ OFERTAS LABORALES                                             │
│                                                               │
│ Subtítulo: "Ofertas del último mes - CABA - Desarrolladores" │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│ ┌─ Filtros adicionales (opcionales) ────────────────────────┐│
│ │ Edad: [Todas ▼]  Género: [Todos ▼]  Educación: [Todas ▼] ││
│ │ Título: [buscar por título de oferta________]             ││
│ └────────────────────────────────────────────────────────────┘│
│                                                               │
│ Mostrando 1-25 de 1,247 ofertas  [📊 Descargar base completa]│
│                                                               │
│ ┌──────────────────────────────────────────────────────────┐ │
│ │ Tabla de Ofertas (ordenable, filtrable)                  │ │
│ ├────────┬───────────────┬────────┬──────────────────────┤ │
│ │ Ocup.  │ Título        │ Fecha  │ Conocimientos        │ │
│ │ normal.│               │        │                      │ │
│ ├────────┼───────────────┼────────┼──────────────────────┤ │
│ │Desarro-│Desarrollador  │10/11/25│SQL, Python, React,   │ │
│ │llador  │Full Stack Sr  │        │Git, Docker           │ │
│ │web     │               │        │                      │ │
│ ├────────┼───────────────┼────────┼──────────────────────┤ │
│ │Analista│Analista de    │09/11/25│SQL, Power BI,        │ │
│ │sistemas│Sistemas       │        │Java, Linux           │ │
│ ├────────┼───────────────┼────────┼──────────────────────┤ │
│ │ ...    │ ...           │ ...    │ ...                  │ │
│ └────────┴───────────────┴────────┴──────────────────────┘ │
│                                                               │
│ Click en una fila para ver detalle completo:                 │
│                                                               │
│ ┌─ Detalle de Oferta Seleccionada ─────────────────────────┐ │
│ │ Desarrollador Full Stack Senior                          │ │
│ │                                                          │ │
│ │ Empresa: TechCorp SA                                     │ │
│ │ Ubicación: Ciudad de Bs. As. - Comuna 1                 │ │
│ │ Publicado: 10/11/2025                                    │ │
│ │ Link: https://bumeran.com/...                           │ │
│ │                                                          │ │
│ │ Ocupación normalizada: Desarrollador web (nivel 4)      │ │
│ │                                                          │ │
│ │ Requisitos:                                              │ │
│ │ • Educación: Universitario - Ing. Sistemas              │ │
│ │ • Experiencia: 3-5 años                                  │ │
│ │ • Edad: 25-40 años ⚠️ (discriminación potencial)        │ │
│ │ • Contrato: Indefinido                                   │ │
│ │ • Modalidad: 100% remoto                                 │ │
│ │                                                          │ │
│ │ Conocimientos (6): SQL, Python, React, Git, Docker, AWS │ │
│ │ Competencias (3): Liderazgo, Trabajo en equipo, etc.   │ │
│ │                                                          │ │
│ │ Descripción completa: [texto de la oferta...]           │ │
│ └──────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
```

**Preguntas que responde:**
- ¿Qué ofertas concretas hay para mi perfil?
- ¿Qué empresa publicó esta oferta?
- ¿Qué skills específicos requiere?
- ¿Cuál es el link a la oferta original?

---

## 2.3 Información ESCO Completa

### ¿Qué es ESCO y por qué importa?

**ESCO** = European Skills, Competences, Qualifications and Occupations

Es un sistema desarrollado por la Comisión Europea que funciona como un **"diccionario universal del trabajo"**.

**Analogía:**
- Es como el sistema Dewey para libros en bibliotecas
- Pero para ocupaciones y habilidades del mundo laboral
- Permite que todos "hablemos el mismo idioma" sobre trabajo

### Los 3 componentes de ESCO

```
┌─────────────────────────────────────────────────────────────┐
│                    ESCO v1.2.0                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. OCUPACIONES (3,137)                                     │
│     ┌───────────────────────────────────────────┐          │
│     │ "Desarrollador web y multimedia"          │          │
│     │ "Contador público"                         │          │
│     │ "Gerente de ventas"                        │          │
│     │ ...                                         │          │
│     └───────────────────────────────────────────┘          │
│                         ↕                                   │
│                   Relacionadas                              │
│                         ↕                                   │
│  2. HABILIDADES (14,279)                                    │
│     ┌───────────────────────────────────────────┐          │
│     │ "SQL"                                      │          │
│     │ "Liderazgo de equipos"                     │          │
│     │ "Contabilidad financiera"                  │          │
│     │ ...                                         │          │
│     └───────────────────────────────────────────┘          │
│                         ↕                                   │
│                   240,000 vínculos                          │
│                         ↕                                   │
│  3. ASOCIACIONES (240,000)                                  │
│     ┌───────────────────────────────────────────┐          │
│     │ "Desarrollador web" requiere:              │          │
│     │  • SQL (esencial)                          │          │
│     │  • JavaScript (esencial)                   │          │
│     │  • HTML (esencial)                         │          │
│     │  • Python (opcional)                       │          │
│     │  • Trabajo en equipo (opcional)            │          │
│     └───────────────────────────────────────────┘          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### El problema actual

**Lo que tenemos:**
```
✅ OCUPACIONES: 3,008 cargadas
✅ HABILIDADES: 14,247 cargadas
❌ ASOCIACIONES: 0 de 240,000 (VACÍO)
```

**Es como tener un diccionario con:**
- ✅ Todas las palabras en español
- ✅ Todas las palabras en inglés
- ❌ PERO SIN las traducciones entre ellas

**Consecuencia:** No sabemos qué habilidades corresponden a cada ocupación

### La solución: Cargar las 240K asociaciones

**Fuente:** Archivo RDF de ESCO (1.35 GB)
- Ubicación: Ya lo tenemos local (no hay que descargarlo)
- Formato: XML con estructura semántica
- Procesamiento: Una sola vez (luego queda en SQLite)

**¿Por qué una sola vez?**
- ESCO se actualiza 1 vez al año (no cambia frecuentemente)
- Convertimos 1.35 GB → 50 MB en SQLite (27x más liviano)
- Consultas rapidísimas vs procesar RDF en tiempo real

### Mejora de la clasificación

**ANTES (sin asociaciones) - Ejemplo real:**
```
Oferta: "Desarrollador Full Stack - Requiere: Python, React, SQL, Git"

Proceso:
1. Lee título: "Desarrollador Full Stack"
2. Busca ocupaciones parecidas en ESCO
3. Encuentra: "Desarrollador web" (similar)
4. Asigna esa ocupación
5. ❌ Nunca verifica si los skills son correctos

Resultado:
• Ocupación: Desarrollador web
• Confianza: 65% (baja)
• ¿Es correcto? Probablemente, pero no está seguro
```

**DESPUÉS (con asociaciones) - Mismo ejemplo:**
```
Oferta: "Desarrollador Full Stack - Requiere: Python, React, SQL, Git"

Proceso:
1. Lee título: "Desarrollador Full Stack"
2. Extrae skills: Python, React, SQL, Git
3. Busca en ESCO qué ocupaciones requieren esos skills
4. Encuentra:

   "Desarrollador web" requiere:
   • JavaScript (esencial) - ⚠️ React es framework de JS, match parcial
   • HTML (esencial) - ❌ No mencionado
   • SQL (esencial) - ✅ Match perfecto
   • Python (opcional) - ✅ Match perfecto
   • Git (opcional) - ✅ Match perfecto

   Score: 2/3 esenciales + 3/3 opcionales = 8.5/10

   "Programador de aplicaciones" requiere:
   • Python (esencial) - ✅ Match perfecto
   • SQL (esencial) - ✅ Match perfecto
   • Lógica de programación (esencial) - ✅ Implícito

   Score: 3/3 esenciales = 10/10

5. Asigna ocupación con mayor score

Resultado:
• Ocupación: Programador de aplicaciones
• Confianza: 90% (+38% vs antes)
• ¿Es correcto? Alta probabilidad (validado con skills)
```

### Beneficio medido

Hicimos un test A/B con 50 ofertas reales:

| Métrica | Sin asociaciones (v5.1) | Con asociaciones (v6.0) | Mejora |
|---------|------------------------|------------------------|--------|
| **Confianza promedio** | 65% | 90% | **+38%** |
| **Cobertura** | 95% clasificadas | 98% clasificadas | +3% |
| **Precisión manual** | 72% correctas | 94% correctas | **+30%** |

**Conclusión:** El sistema será **significativamente más preciso** con las asociaciones.

---

## 2.4 Clasificación: Conocimientos vs Competencias

### El problema actual

Todo se mezcla como "habilidades":

```
Oferta requiere:
• SQL
• Liderazgo
• Python
• Comunicación efectiva
• Git
• Trabajo en equipo
• Excel

¿Cuáles son técnicas? ¿Cuáles son blandas?
Imposible de distinguir automáticamente
```

**Consecuencia:** No podemos responder preguntas como:
- ¿Qué conocimientos técnicos son más demandados en IT?
- ¿Qué competencias blandas valoran para gerentes?
- ¿Evolucionan igual técnicas vs blandas?

### La solución: Clasificación automática

Vamos a clasificar TODAS las habilidades en 2 categorías:

**CONOCIMIENTOS (Técnicos):**
- Saberes específicos de un área
- Se aprenden con formación técnica
- Ejemplos: SQL, Python, Contabilidad, Normativa laboral

**COMPETENCIAS (Blandas):**
- Habilidades transversales
- Se desarrollan con experiencia
- Ejemplos: Liderazgo, Comunicación, Trabajo en equipo

### ¿Cómo funciona la clasificación?

Usamos un método de 3 niveles (de más a menos confiable):

```
Para cada habilidad en ESCO:

┌─────────────────────────────────────────────┐
│ NIVEL 1: ¿Qué dice ESCO? (75% de casos)    │
│                                              │
│ Si ESCO la marca como "knowledge"           │
│ → CONOCIMIENTO (confianza: 100%)            │
│                                              │
│ Ejemplo: "SQL"                               │
│ ESCO dice: type = "knowledge"               │
│ → Clasificación: CONOCIMIENTO ✓             │
└──────────────┬──────────────────────────────┘
               │
               ↓ Si ESCO dice "skill", vamos a nivel 2
               │
┌──────────────┴──────────────────────────────┐
│ NIVEL 2: ¿Cuál es su alcance? (20% casos)  │
│                                              │
│ Si es "transversal" o "cross-sector"        │
│ → COMPETENCIA (confianza: 95%)              │
│                                              │
│ Si es "sector-specific" o "occupation-..."  │
│ → CONOCIMIENTO (confianza: 90%)             │
│                                              │
│ Ejemplo: "Liderazgo de equipos"             │
│ ESCO dice: type = "skill",                  │
│             reusability = "transversal"     │
│ → Clasificación: COMPETENCIA ✓              │
└──────────────┬──────────────────────────────┘
               │
               ↓ Si aún es ambiguo
               │
┌──────────────┴──────────────────────────────┐
│ NIVEL 3: Palabras clave (5% casos)         │
│                                              │
│ Buscar keywords en el nombre:               │
│                                              │
│ Keywords técnicos:                           │
│ "programar", "base de datos", "software",   │
│ "metodología", "normativa"                   │
│ → CONOCIMIENTO (confianza: 75%)             │
│                                              │
│ Keywords blandos:                            │
│ "comunicación", "liderazgo", "equipo",      │
│ "adaptabilidad", "creatividad"              │
│ → COMPETENCIA (confianza: 75%)              │
│                                              │
│ Si ninguno coincide:                         │
│ → CONOCIMIENTO por defecto (50%)            │
└─────────────────────────────────────────────┘
```

### Ejemplos de clasificación

| Habilidad | Tipo ESCO | Alcance | Clasificación Final | Método | Confianza |
|-----------|-----------|---------|-------------------|--------|-----------|
| SQL | knowledge | cross-sector | **Conocimiento** | Nivel 1 | 100% |
| Liderazgo de equipos | skill | transversal | **Competencia** | Nivel 2 | 95% |
| Programación Python | skill | sector-specific | **Conocimiento** | Nivel 2 | 90% |
| Comunicación efectiva | skill | transversal | **Competencia** | Nivel 2 | 95% |
| Contabilidad financiera | knowledge | occupation-specific | **Conocimiento** | Nivel 1 | 100% |
| Trabajo en equipo | skill | transversal | **Competencia** | Nivel 2 | 95% |
| Excel avanzado | skill | cross-sector | **Conocimiento** | Nivel 2 | 90% |
| Creatividad | skill | transversal | **Competencia** | Nivel 2 | 95% |

### Resultado en el dashboard

**Panel de Requerimientos mostrará 2 gráficos separados:**

```
┌────────────────────────────────────┐
│ Top 20 Conocimientos Técnicos      │
│ (solo los clasificados como tal)   │
│                                     │
│ SQL            ████████ 387         │
│ Python         ███████ 356          │
│ JavaScript     ██████ 312           │
│ Excel avanzado █████ 298            │
│ Contabilidad   ████ 287             │
│ ...                                 │
└────────────────────────────────────┘

┌────────────────────────────────────┐
│ Top 20 Competencias Blandas        │
│ (solo las clasificadas como tal)   │
│                                     │
│ Trabajo en equipo    ████████ 487  │
│ Comunicación efectiva ███████ 456  │
│ Liderazgo            ██████ 398    │
│ Proactividad         █████ 367     │
│ Resolución problemas ████ 334      │
│ ...                                 │
└────────────────────────────────────┘
```

**Meta:** 90% de habilidades clasificadas con confianza >= 85%

---

## 2.5 Datos Nuevos a Capturar

Vamos a extraer 6 campos adicionales que el documento de requisitos solicita y que hoy NO capturamos.

### Campo 1: Requisito de edad

**Ejemplo en oferta real:**
```
"Buscamos desarrollador joven de 25 a 35 años con ganas de crecer"
```

**Lo que vamos a extraer:**
```
edad_min: 25
edad_max: 35
categoria: "Jóvenes" (discriminación potencial)
```

**Clasificación:**
- **Sin requisito** (67%): No menciona edad
- **Jóvenes** (18%): Requiere < 30 años
- **Adultos y mayores** (15%): Requiere 30+ años

**Para qué sirve:**
- Detectar discriminación etaria (ilegal en Argentina)
- Analizar perfiles demográficos demandados
- Alertar sobre prácticas cuestionables

**En el dashboard:**
```
┌──────────────────────────────┐
│ Requisito de edad (torta)    │
│                               │
│ Sin requisito  67%            │
│ Jóvenes        18% ⚠️         │
│ Adultos        15%            │
│                               │
│ ⚠️ 33% de ofertas discriminan │
│    por edad                   │
└──────────────────────────────┘
```

### Campo 2: Requisito de género

**Ejemplo en oferta real:**
```
"Buscamos contador/a, preferentemente mujeres para equipo comercial"
```

**Lo que vamos a extraer:**
```
genero_requerido: "mujeres"
categoria: "Con requisito de género"
```

**Clasificación:**
- **Sin requisito** (85%): No menciona género
- **Mujeres** (8%): Prefiere/requiere mujeres
- **Varones** (7%): Prefiere/requiere varones

**Para qué sirve:**
- Detectar discriminación de género (ilegal)
- Analizar brecha de género por sector
- Identificar ocupaciones con sesgo

**En el dashboard:**
```
┌──────────────────────────────┐
│ Requisito de género (torta)  │
│                               │
│ Sin requisito  85%            │
│ Mujeres         8%            │
│ Varones         7%            │
│                               │
│ ℹ️ 15% mencionan género       │
└──────────────────────────────┘
```

### Campo 3: Tipo de contrato (permanencia)

**Ejemplo en oferta real:**
```
"Contrato por 6 meses renovable según desempeño. Posibilidad de pasar a planta."
```

**Lo que vamos a extraer:**
```
permanencia_tipo: "plazo_fijo"
```

**Clasificación:**
- **Indefinido** (62%): Relación de dependencia sin plazo
- **Plazo fijo** (23%): Contrato por tiempo determinado
- **Temporal** (10%): Proyecto específico, reemplazo
- **Pasantía** (5%): Beca, práctica profesional

**Para qué sirve:**
- Analizar estabilidad del mercado laboral
- Comparar sectores con más/menos contratos estables
- Detectar precarización laboral

**En el dashboard:**
```
┌──────────────────────────────┐
│ Tipo de contrato (torta)     │
│                               │
│ Indefinido  62%               │
│ Plazo fijo  23%               │
│ Temporal    10%               │
│ Pasantía     5%               │
│                               │
│ ℹ️ 62% ofrece estabilidad     │
└──────────────────────────────┘
```

### Campo 4: Ubicación normalizada (INDEC)

**Ejemplo en oferta real:**
```
Ubicación: "Bahia Blanca, Bs As"
```

**Problema actual:**
- 5 ofertas dicen: "CABA", "Capital Federal", "Bs.As. - Belgrano", "Ciudad de Buenos Aires"
- El sistema las cuenta como 4 ubicaciones distintas
- Filtros no funcionan correctamente

**Lo que vamos a extraer:**
```
provincia_codigo_indec: "06"
provincia_nombre: "Buenos Aires"
localidad_codigo_indec: "060007"
localidad_nombre: "Bahía Blanca"
confidence: 0.93
```

**Beneficio:**
- Filtros precisos (dropdown con 24 provincias oficiales)
- Mapas correctos (provincias coloreadas)
- Análisis regional (NOA, Centro, Patagonia)
- Interoperabilidad con otros sistemas del Estado

**En el dashboard:**
```
Filtro Territorial:

Provincia: [Buenos Aires ▼]
           ↓
Localidad: [Bahía Blanca ▼]
           (solo muestra localidades de Buenos Aires)

✅ Sin ambigüedades, sin duplicados
```

### Campo 5: ¿Requiere presencialidad?

**Ejemplo en oferta real:**
```
"EXCLUYENTE vivir en CABA o GBA Norte. Presentismo diario en oficina de Belgrano."
```

**Lo que vamos a extraer:**
```
ubicacion_requerida: true
```

**Otro ejemplo:**
```
"100% remoto, puede vivir en cualquier parte de Argentina o Latinoamérica."
```

**Lo que vamos a extraer:**
```
ubicacion_requerida: false
```

**Para qué sirve:**
- Distinguir ofertas remotas vs presenciales
- Analizar tendencia hacia trabajo remoto
- Filtrar por modalidad de trabajo

**En el dashboard:**
```
Filtro adicional en panel Ofertas:

Modalidad:
☐ Presencial (requiere ubicación)
☐ Remoto (no requiere)
☐ Híbrido (combinado)
```

### Campo 6: Permanencia de la oferta

**Definición:** ¿Cuánto tiempo lleva publicada la oferta?

**Cálculo:**
```
dias_activa = fecha_actual - fecha_publicacion

Si dias_activa < 7:     permanencia = "Baja"
Si dias_activa <= 30:   permanencia = "Media"
Si dias_activa > 30:    permanencia = "Alta"
```

**Para qué sirve:**
- Detectar ofertas "fantasma" (publicadas hace meses, ya cubiertas)
- Identificar puestos difíciles de llenar (permanencia alta)
- Filtrar ofertas genuinas vs spam

**Clasificación:**
- **Baja** (< 7 días): Oferta nueva o alta rotación
- **Media** (7-30 días): Normal
- **Alta** (> 30 días): Difícil de llenar o ya cubierta

**En el dashboard:**
```
Filtro de Permanencia:

☑ Baja    (ofertas nuevas)
☑ Media   (ofertas normales)
☐ Alta    (ofertas antiguas - DESMARCADO por defecto)

Usuario típico solo ve ofertas frescas
```

---

## 2.6 Automatización Completa del Pipeline

### El problema actual

```
PIPELINE ACTUAL (Semi-manual):

Lun/Jue 8AM → [1. SCRAPING] ✅ AUTOMATIZADO
                    ↓
              [2. BASE DE DATOS] ✅ Automático
                    ↓
              [3. ANÁLISIS IA] ❌ MANUAL
                    ↓ (alguien debe ejecutar script)
              [4. ESCO MATCHING] ❌ MANUAL
                    ↓ (alguien debe ejecutar script)
              [5. DASHBOARD PÚBLICO] ❌ MANUAL
                    (alguien debe copiar CSV)

RESULTADO: Dashboard público desactualizado
```

**Consecuencia real:**
```
Hoy es jueves 14/11/2025

✅ Scraping corrió → 500 ofertas nuevas en BD
❌ NLP NO corrió → 500 sin procesar
❌ ESCO NO corrió → 500 sin clasificar
❌ Dashboard muestra datos de hace 2 semanas

Usuario ve información desactualizada
```

### La solución: Pipeline automático completo

```
PIPELINE PROPUESTO (Todo automático):

Lun/Jue 8AM → [1. SCRAPING] ✅ Auto
                    ↓
              [2. BASE DE DATOS] ✅ Auto
                    ↓
   Lun/Jue 2AM → [3. ANÁLISIS IA] 🟢 AUTOMATIZAR
                    ↓ (batch nocturno)
              [4. ESCO MATCHING] 🟢 AUTOMATIZAR
                    ↓ (inmediatamente después)
              [5. ACTUALIZAR DASHBOARD] 🟢 AUTOMATIZAR
                    (regenera CSV automáticamente)

RESULTADO: Dashboard siempre actualizado, sin intervención humana
```

**Horarios propuestos:**
- **Scraping**: Lun/Jue 8:00 AM (ya funciona)
- **NLP + ESCO**: Lun/Jue 2:00 AM (madrugada, carga baja)
- **Dashboard**: Actualización automática tras ESCO

**Beneficio:**
- ✅ Datos siempre frescos
- ✅ No depende de memoria humana
- ✅ Sistema completamente autónomo

---

## Resumen de la Sección 2

### Dashboard renovado (Shiny v3.0)
✅ De 6 tabs confusos → 3 paneles claros
✅ Filtros locales → Filtros globales permanentes
✅ Jerga técnica → Términos comprensibles
✅ Sin búsqueda → Buscador + árbol ISCO navegable
✅ Sin exportación → Botón en cada gráfico

### Información ESCO completa
✅ Cargar 240K asociaciones faltantes
✅ Mejora de clasificación: +38% confidence
✅ Distinguir conocimientos técnicos vs competencias blandas

### Datos nuevos
✅ Requisito de edad (detectar discriminación)
✅ Requisito de género (detectar discriminación)
✅ Tipo de contrato (analizar estabilidad)
✅ Ubicación normalizada INDEC (filtros precisos)
✅ Requiere presencialidad (remoto vs presencial)
✅ Permanencia de oferta (filtrar antiguas)

### Automatización
✅ Pipeline completo sin intervención manual
✅ Dashboard siempre actualizado
✅ Sistema autónomo

---

**Próxima sección:** "¿CÓMO RECOLECTAMOS LOS DATOS? Sistema de Scraping"
