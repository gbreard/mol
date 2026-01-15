# SECCIÓN 1: SITUACIÓN ACTUAL - ¿Dónde estamos hoy?

## 1.1 ¿Qué hace el sistema MOL actualmente?

El **Monitor de Ofertas Laborales (MOL)** es un sistema que analiza el mercado laboral argentino a través del procesamiento automático de ofertas de empleo publicadas en internet.

### El flujo completo del sistema

```
┌─────────────────────────────────────────────────────────────────────┐
│                         PORTALES LABORALES                           │
│  Bumeran | ComputRabajo | ZonaJobs | LinkedIn | Indeed              │
└────────────────────────┬────────────────────────────────────────────┘
                         │
                         ↓ Scraping (recolección automática)
                         │
┌────────────────────────┴────────────────────────────────────────────┐
│                    BASE DE DATOS SQLITE                              │
│  6,521 ofertas almacenadas con toda su información                  │
└────────────────────────┬────────────────────────────────────────────┘
                         │
                         ↓ Procesamiento con Inteligencia Artificial
                         │
┌────────────────────────┴────────────────────────────────────────────┐
│              EXTRACCIÓN DE INFORMACIÓN ESTRUCTURADA                  │
│  De texto libre → Datos organizados (experiencia, educación, etc.)  │
└────────────────────────┬────────────────────────────────────────────┘
                         │
                         ↓ Clasificación con estándar europeo ESCO
                         │
┌────────────────────────┴────────────────────────────────────────────┐
│                    CLASIFICACIÓN OCUPACIONAL                         │
│  Cada oferta se asigna a una ocupación estándar internacional       │
└────────────────────────┬────────────────────────────────────────────┘
                         │
                         ↓ Visualización
                         │
┌────────────────────────┴────────────────────────────────────────────┐
│                         2 DASHBOARDS                                 │
│  ┌─────────────────────┬─────────────────────────────────────────┐ │
│  │ Dashboard Técnico   │ Dashboard de Análisis                    │ │
│  │ (Control interno)   │ (Análisis público)                       │ │
│  └─────────────────────┴─────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

### ¿Para qué sirve?

El MOL permite responder preguntas como:

- **¿Qué ocupaciones son más demandadas?** (ej: "Desarrolladores web" aparecen en 245 ofertas)
- **¿Qué habilidades técnicas piden?** (ej: SQL aparece en 387 ofertas, Python en 356)
- **¿Qué competencias blandas valoran?** (ej: Trabajo en equipo en 487 ofertas)
- **¿Dónde hay más ofertas?** (ej: CABA concentra el 45% de ofertas IT)
- **¿Cómo evolucionan las ofertas en el tiempo?** (ej: Pico en octubre, baja en enero)

---

## 1.2 Los dos dashboards y sus propósitos

El sistema tiene **DOS dashboards completamente distintos**, cada uno para un propósito y audiencia diferente:

### Dashboard 1: Técnico / Operativo (Plotly)

**Para quién:** Equipo técnico que mantiene el sistema

**Propósito:** Monitorear que todo funcione correctamente

**Lo que muestra:**

```
┌──────────────────────────────────────────────────────────────┐
│ DASHBOARD TÉCNICO - Control del Sistema                      │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│ [TAB: OVERVIEW]                                              │
│                                                               │
│ 📊 Total ofertas: 6,521                                      │
│ 🏢 Empresas únicas: 1,247                                     │
│ 🔑 Keywords activos: 87                                       │
│ 📅 Última actualización: 14/11/2025 08:15                    │
│                                                               │
│ ┌────────────────────────────────────────────────────────┐  │
│ │ Ofertas por día (últimos 30 días)                      │  │
│ │ │                                                       │  │
│ │ │     ╱╲                                               │  │
│ │ │    ╱  ╲      ╱╲                                      │  │
│ │ │   ╱    ╲    ╱  ╲    ╱╲                               │  │
│ │ │  ╱      ╲  ╱    ╲  ╱  ╲                              │  │
│ │ │ ╱        ╲╱      ╲╱    ╲                             │  │
│ │ └───────────────────────────────────────────────────── │  │
│ │  Oct 15  Oct 22  Oct 29  Nov 5   Nov 12              │  │
│ └────────────────────────────────────────────────────────┘  │
│                                                               │
│ [TAB: KEYWORDS]                                              │
│ Rendimiento de palabras clave usadas para buscar            │
│                                                               │
│ [TAB: CALIDAD]                                               │
│ Qué porcentaje de campos tiene información completa          │
│                                                               │
│ [TAB: ALERTAS]                                               │
│ Errores, warnings, problemas detectados                      │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

**Ejemplos de preguntas que responde:**

- ¿Funcionó el scraping de esta mañana?
- ¿Hay algún error en el proceso?
- ¿Qué keywords traen más ofertas nuevas?
- ¿Los datos están completos o faltan campos?

**Acceso:** Solo equipo interno (localhost:8052)

### Dashboard 2: Análisis / Público (Shiny)

**Para quién:** Analistas, investigadores, público general

**Propósito:** Analizar el mercado laboral y generar insights

**Lo que muestra:**

```
┌──────────────────────────────────────────────────────────────┐
│ MONITOR DE OFERTAS LABORALES                                 │
├──────────────────────────────────────────────────────────────┤
│ 👤 Usuario: analista@oede.gob.ar                             │
│                                                               │
│ [TAB: PANORAMA GENERAL]                                      │
│                                                               │
│ 📊 268 ofertas analizadas                                    │
│ 💼 87 ocupaciones distintas                                  │
│ 🎯 1,245 habilidades identificadas                           │
│                                                               │
│ ┌────────────────────────────────────────────────────────┐  │
│ │ Top 10 Ocupaciones                                      │  │
│ │                                                         │  │
│ │ Desarrollador web          ████████████ 45              │  │
│ │ Analista de sistemas       ██████████ 38                │  │
│ │ Gerente comercial          ████████ 29                  │  │
│ │ Contador público           ███████ 24                   │  │
│ │ Asistente administrativo   ██████ 19                    │  │
│ │ ...                                                     │  │
│ └────────────────────────────────────────────────────────┘  │
│                                                               │
│ [TAB: HABILIDADES]                                           │
│ Skills técnicos y competencias blandas más demandadas       │
│                                                               │
│ [TAB: OCUPACIONES ESCO]                                      │
│ Árbol navegable de ocupaciones clasificadas                  │
│                                                               │
│ [TAB: EXPLORADOR]                                            │
│ Búsqueda y listado de ofertas individuales                   │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

**Ejemplos de preguntas que responde:**

- ¿Qué ocupaciones son más demandadas en el sector IT?
- ¿Qué habilidades técnicas piden para desarrolladores?
- ¿Cuáles son las competencias blandas más valoradas?
- ¿Cómo evolucionaron las ofertas en los últimos 6 meses?
- ¿Dónde se concentran las ofertas geográficamente?

**Acceso:** Público con autenticación (shinyapps.io)

### Comparación lado a lado

| Característica | Dashboard Técnico | Dashboard Análisis |
|----------------|-------------------|-------------------|
| **Usuario** | Equipo de desarrollo | Analistas, investigadores |
| **Pregunta clave** | ¿Funciona el sistema? | ¿Qué dice el mercado? |
| **Datos** | Tiempo real (auto-refresh) | Snapshot actualizado manualmente |
| **Enfoque** | Performance, errores, logs | Insights, tendencias, estadísticas |
| **Complejidad** | Técnico (SQL, logs, métricas) | Amigable (gráficos, filtros) |
| **Cantidad datos** | Todas las 6,521 ofertas | Muestra de 268 ofertas con ESCO |
| **Hosting** | Servidor local (8052) | Cloud público (shinyapps.io) |
| **Autenticación** | No | Sí (4 usuarios) |

**Analogía:** El dashboard técnico es como el **panel del motor** de un auto (para el mecánico), mientras que el dashboard de análisis es como el **tablero del conductor** (para quien maneja).

---

## 1.3 ¿Qué está funcionando bien?

### ✅ 1. Scraping automático de Bumeran

**Estado:** Operativo y estable

**Frecuencia:** Lunes y Jueves a las 8:00 AM

**Resultado típico:** ~500 ofertas nuevas por ejecución

**Proceso:**
1. Sistema se despierta automáticamente (Windows Task Scheduler)
2. Busca ofertas usando **1,148 palabras clave** organizadas en 59 categorías
   - Ejemplos IT: "desarrollador", "python", "javascript", "devops"
   - Ejemplos Administración: "contador", "administrativo", "asistente"
   - Ejemplos Comercial: "ventas", "ejecutivo-comercial", "marketing"
   - Y 56 categorías más (Salud, Gastronomía, Legal, Ingeniería, etc.)
3. Descarga toda la información de cada oferta
4. Elimina duplicados
5. Guarda en la base de datos
6. Genera backup en CSV
7. Registra métricas y alertas

**Control de calidad automático:**
- Detecta si el portal dejó de funcionar
- Alerta si hay demasiados duplicados (señal de problema)
- Guarda logs detallados de cada ejecución

**Ejemplo de ejecución exitosa:**
```
📅 Fecha: Lunes 13/11/2025 - 08:00 AM
⏱️ Duración: 1 hora 23 minutos
📊 Resultados:
   • Ofertas encontradas: 2,847
   • Ofertas nuevas: 523
   • Duplicados filtrados: 2,324
   • Errores: 0
✅ Ejecución exitosa
```

### ✅ 2. Base de datos operativa

**Estado:** Funcionando correctamente

**Contenido actual:**
- **6,521 ofertas** almacenadas
- **1,247 empresas** únicas
- **1,148 keywords** en diccionario activo
- **~50 MB** de tamaño

**Información que guarda de cada oferta:**
- Título y descripción completa (HTML)
- Empresa y logo
- Ubicación (texto libre)
- Fecha de publicación y fecha de scraping
- Salario (si lo menciona)
- Modalidad (Presencial/Remoto/Híbrido)
- Link a la oferta original
- Keyword que la encontró

**Backup automático:** Se guarda copia en CSV en cada ejecución

### ✅ 3. Dashboard técnico operativo

**Estado:** Funcionando en tiempo real

**Características:**
- Se actualiza automáticamente cada 5 minutos
- Muestra 6 tabs con información operativa
- Detecta y alerta sobre problemas
- Permite exportar datos para análisis

**Usuarios activos:** Equipo técnico OEDE (3 personas)

### ✅ 4. Dashboard público con seguridad

**Estado:** Publicado y accesible

**Características:**
- Autenticación con usuario y contraseña
- 4 usuarios configurados (admin, analista, invitado)
- Hosting en la nube (shinyapps.io)
- Acceso desde cualquier navegador

**Usuarios registrados:** Analistas del equipo OEDE

---

## 1.4 ¿Qué necesita mejorar?

Esta sección resume los problemas identificados y los requisitos del **documento de comentarios al dashboard**.

### ❌ Problema 1: Dashboard público no cumple requisitos de usabilidad

**1.1 Navegación confusa**

**Situación actual:**
- 6 tabs separados: Panorama, Territorial, Habilidades, Ocupaciones, Tendencias, Datos
- El usuario debe adivinar dónde buscar la información
- No hay una estructura clara de navegación

**Consecuencia:**
```
Usuario pregunta: "¿Cuántas ofertas de desarrolladores hay en CABA?"

Debe hacer:
1. Ir al tab "Territorial"
2. Filtrar por CABA
3. Cambiar al tab "Ocupaciones"
4. ❌ El filtro de CABA SE PERDIÓ (cada tab tiene sus propios filtros)
5. Debe volver a filtrar
6. Frustración y abandono
```

**Lo que requiere el documento:**
- 3 paneles claros y temáticos (Panorama / Requerimientos / Ofertas)
- Filtros globales en panel izquierdo que apliquen a TODO
- Navegación intuitiva sin tabs redundantes

**1.2 Jerga técnica incomprensible**

**Situación actual:**
- Usa siglas: "CIUO", "ESCO", "ISCO-08"
- Términos técnicos: "skill reusability level", "preferred label"
- El usuario promedio no entiende qué significan

**Ejemplos problemáticos:**

| Lo que dice ahora | Lo que debería decir |
|-------------------|---------------------|
| "Código CIUO-08" | "Ocupación normalizada" |
| "Skills ESCO clasificados" | "Habilidades normalizadas con IA" |
| "ISCO Level 3" | "Categoría de ocupación" |

**Consecuencia:** Analistas sin conocimiento técnico se confunden y no usan el dashboard

**Lo que requiere el documento:**
- Eliminar TODAS las siglas técnicas visibles
- Usar términos comprensibles para cualquier persona
- Ocultar la complejidad técnica detrás de la interfaz

**1.3 Filtros que no se mantienen**

**Situación actual:**
- Cada tab tiene sus propios filtros locales
- Al cambiar de tab, los filtros se pierden
- Hay que volver a seleccionar todo

**Lo que requiere el documento:**
- Filtros globales en panel izquierdo (siempre visibles)
- 5 filtros principales:
  1. Territorial (Provincia → Localidad)
  2. Período (Última semana / Último mes / Último año)
  3. Permanencia (Baja / Media / Alta)
  4. Ocupación (Buscador + Árbol navegable)
  5. [Otros filtros según panel]
- Los filtros aplican a TODOS los paneles simultáneamente

**1.4 Falta búsqueda de ocupaciones**

**Situación actual:**
- No hay forma de buscar una ocupación específica
- Hay que scrollear una lista larga
- No hay exploración por categorías

**Lo que requiere el documento:**
- Buscador de texto libre (ej: escribir "desarrollador")
- Árbol navegable de ocupaciones con 4 niveles
- Click para expandir/contraer categorías
- Contador de ofertas por categoría

**Ejemplo de árbol esperado:**
```
▼ 2 - Profesionales científicos (543 ofertas)
  ▼ 25 - Profesionales TIC (312 ofertas)
    ▼ 251 - Desarrolladores de software (245 ofertas)
      ☑ 2511 - Analistas de sistemas (89 ofertas)
      ☑ 2513 - Desarrolladores web (54 ofertas)
      ☐ 2514 - Programadores de aplicaciones (35 ofertas)
```

**1.5 No hay exportación por gráfico**

**Situación actual:**
- Solo se puede exportar la base completa (todo o nada)
- No se pueden exportar datos de un gráfico específico

**Lo que requiere el documento:**
- Botón "Exportar a Excel/CSV" en CADA gráfico
- Exportar datos completos (no solo lo visible en pantalla)
- Ejemplo: Top 10 ocupaciones muestra 10, pero exporta todas las existentes

**1.6 Logo y diseño**

**Situación actual:**
- Logo con texto debajo que no se lee bien
- No se ve claramente "Monitor de Ofertas Laborales"

**Lo que requiere el documento:**
- Quitar texto debajo del logo
- Mostrar "Monitor de Ofertas Laborales" en letras blancas en el banner
- Mejorar legibilidad

### ❌ Problema 2: Información ESCO incompleta

**2.1 ¿Qué es ESCO?**

ESCO es un sistema europeo que clasifica:
- **Ocupaciones**: 3,137 categorías (ej: "Desarrollador web", "Contador público")
- **Habilidades**: 14,279 skills (ej: "SQL", "Liderazgo", "Excel")
- **Relaciones**: 240,000 vínculos (ej: "Desarrollador web requiere SQL como habilidad esencial")

**Es como un diccionario universal del trabajo.**

**2.2 ¿Qué tenemos hoy?**

✅ Ocupaciones: Sí (3,008 cargadas)
✅ Habilidades: Sí (14,247 cargadas)
❌ Relaciones: **NO** (0 de 240,000) ← **CRÍTICO**

**Consecuencia: Clasificación imprecisa**

Sin las relaciones, el sistema funciona así:

```
Oferta: "Desarrollador Full Stack - Requiere: Python, React, SQL, Git"

Proceso actual:
1. Lee el título: "Desarrollador Full Stack"
2. Busca ocupaciones similares en ESCO
3. Encuentra: "Desarrollador web" (parecido)
4. Asigna esa ocupación
5. ❌ NUNCA verifica si los skills (Python, React, SQL) son correctos

Resultado: Confidence 65% (no muy confiable)
```

Con las relaciones, funcionaría así:

```
Oferta: "Desarrollador Full Stack - Requiere: Python, React, SQL, Git"

Proceso mejorado:
1. Lee el título: "Desarrollador Full Stack"
2. Extrae skills: Python, React, SQL, Git
3. Busca ocupaciones que requieren esos skills
4. "Desarrollador web" requiere:
   • SQL (esencial) ✓ Match
   • JavaScript (esencial) ✗ No match (pero React es similar)
   • HTML (esencial) ✗ No match
   • Python (opcional) ✓ Match
5. Calcula score ponderado
6. Asigna ocupación con mayor score

Resultado: Confidence 90% (+38% mejora)
```

**2.3 No distinguimos conocimientos técnicos vs competencias blandas**

**Situación actual:**
Todo se muestra junto como "habilidades":

```
Habilidades de la oferta (mezcladas):
• SQL
• Python
• Liderazgo
• Excel
• Comunicación efectiva
• Git
• Trabajo en equipo
```

**Problema:** No podemos responder preguntas como:
- ¿Qué conocimientos técnicos son más demandados en IT?
- ¿Qué competencias blandas valoran más para puestos gerenciales?
- ¿Cómo evolucionan los requerimientos técnicos vs sociales?

**Solución requerida:**
Clasificar automáticamente en 2 categorías:

```
Conocimientos técnicos (27 en esta oferta):
• SQL
• Python
• Excel
• Git
• AWS
• ...

Competencias blandas (8 en esta oferta):
• Liderazgo
• Comunicación efectiva
• Trabajo en equipo
• Proactividad
• ...
```

**Beneficio:** Análisis diferenciado en el dashboard
- Gráfico 1: Top 20 conocimientos técnicos
- Gráfico 2: Top 20 competencias blandas (separado)

### ❌ Problema 3: Datos faltantes en las ofertas

El documento de requisitos solicita capturar información que hoy NO extraemos:

**3.1 Requisito de edad**

**¿Por qué importa?**
- Detectar discriminación etaria (ilegal en Argentina)
- Analizar perfiles demográficos demandados
- Identificar ofertas con prácticas cuestionables

**Hoy:** No capturamos
**Requerido:** Extraer y clasificar en:
- Sin requisito (67% de ofertas)
- Jóvenes solamente (< 30 años) (18%)
- Adultos y mayores (30+ años) (15%)

**Ejemplo:**
```
Oferta dice: "Buscamos jóvenes de 25 a 35 años con ganas de crecer"

Extracción:
• edad_min: 25
• edad_max: 35
• Clasificación: "Jóvenes" (discriminación potencial)
```

**3.2 Requisito de género**

**¿Por qué importa?**
- Detectar discriminación de género (ilegal)
- Analizar brecha de género por ocupación
- Identificar sectores con sesgo

**Hoy:** No capturamos
**Requerido:** Extraer y clasificar en:
- Sin requisito (85%)
- Mujeres (8%)
- Varones (7%)

**Ejemplo:**
```
Oferta dice: "Buscamos contador/a, preferentemente mujeres"

Extracción:
• genero_requerido: "mujeres"
• Clasificación: Con requisito de género
```

**3.3 Tipo de contrato (permanencia)**

**¿Por qué importa?**
- Analizar estabilidad del mercado laboral
- Comparar sectores con más/menos contratos indefinidos
- Detectar precarización laboral

**Hoy:** No capturamos
**Requerido:** Extraer y clasificar en:
- Indefinido (relación de dependencia)
- Plazo fijo (contrato por tiempo determinado)
- Temporal (proyecto específico, reemplazo)
- Pasantía

**Ejemplo:**
```
Oferta dice: "Contrato por 6 meses renovable según desempeño"

Extracción:
• permanencia_tipo: "plazo_fijo"
```

**3.4 Ubicación sin normalizar**

**Problema:**
Ubicaciones en texto libre generan inconsistencias:

```
5 ofertas dicen:
• "CABA"
• "Capital Federal"
• "Buenos Aires (Capital)"
• "Bs.As. - Belgrano"
• "Ciudad de Buenos Aires"

→ El sistema las cuenta como 5 ubicaciones distintas
→ Filtro por provincia NO funciona correctamente
→ Mapas quedan mal
```

**Hoy:** Solo texto libre
**Requerido:** Normalizar con códigos oficiales INDEC

**Ejemplo:**
```
Texto: "Bahia Blanca, Bs As"

Normalización:
• Provincia: Buenos Aires (código INDEC: 06)
• Localidad: Bahía Blanca (código: 060007)
• Confidence: 93%
```

**Beneficio:**
- Filtros precisos (dropdown con 24 provincias oficiales)
- Mapas correctos (provincias coloreadas según ofertas)
- Análisis regional (agrupar por NOA, Centro, Patagonia, etc.)

**3.5 ¿Requiere presencialidad?**

**¿Por qué importa?**
- Distinguir ofertas remotas vs presenciales
- Analizar tendencia hacia trabajo remoto
- Filtrar por modalidad

**Hoy:** Tenemos campo "modalidad" pero no siempre está completo
**Requerido:** Detectar con IA si EXIGE estar en la ubicación

**Ejemplos:**
```
Oferta 1: "EXCLUYENTE vivir en CABA, presentismo diario"
→ ubicacion_requerida: TRUE

Oferta 2: "100% remoto, puede vivir en cualquier parte de Argentina"
→ ubicacion_requerida: FALSE

Oferta 3: "Modalidad híbrida, 2 días presenciales"
→ ubicacion_requerida: TRUE (requiere ir a la ubicación al menos 2 días)
```

**3.6 Permanencia de la oferta**

**Definición:** ¿Cuánto tiempo lleva publicada la oferta?

**¿Por qué importa?**
- Detectar ofertas "fantasma" (publicadas hace meses, ya cubiertas)
- Identificar puestos difíciles de llenar (permanencia alta)
- Filtrar ofertas genuinas vs spam

**Hoy:** No calculamos
**Requerido:** Clasificar en:
- **Baja** (< 7 días): Oferta nueva o de alta rotación
- **Media** (7-30 días): Normal
- **Alta** (> 30 días): Difícil de llenar o ya cubierta (no actualizada)

**Ejemplo:**
```
Oferta publicada: 15/10/2025
Hoy: 14/11/2025
Días activa: 30 días

Clasificación: Permanencia "Media"
```

**Uso en dashboard:** Filtro para mostrar solo ofertas recientes (baja/media permanencia)

### ❌ Problema 4: Proceso semi-manual

**Situación actual:**

```
┌──────────────────┐
│ 1. SCRAPING      │  ← ✅ AUTOMATIZADO (Lun/Jue 8AM)
└────────┬─────────┘
         ↓
┌────────┴─────────┐
│ 2. BASE DE DATOS │  ← ✅ Automático (se guarda directo)
└────────┬─────────┘
         ↓
┌────────┴─────────┐
│ 3. ANÁLISIS IA   │  ← ❌ MANUAL (hay que ejecutar script)
└────────┬─────────┘
         ↓
┌────────┴─────────┐
│ 4. ESCO MATCHING │  ← ❌ MANUAL (hay que ejecutar script)
└────────┬─────────┘
         ↓
┌────────┴─────────┐
│ 5. DASHBOARD     │  ← ❌ MANUAL (hay que copiar CSV)
│    PÚBLICO       │
└──────────────────┘
```

**Problema:** Los pasos 3, 4 y 5 requieren intervención manual
- Alguien debe acordarse de ejecutar los scripts
- Alguien debe copiar el archivo CSV actualizado
- El dashboard público queda desactualizado si no se hace

**Consecuencia:**
```
Hoy es jueves 14/11/2025
• Scraping corrió esta mañana → Base tiene 500 ofertas nuevas ✓
• Análisis IA NO corrió → Esas 500 no tienen info estructurada ✗
• ESCO matching NO corrió → No están clasificadas ✗
• Dashboard público muestra datos de hace 2 semanas ✗
```

**Solución requerida:**
Automatizar TODO el pipeline para que corra solo:

```
┌──────────────────┐
│ 1. SCRAPING      │  ← ✅ Auto Lun/Jue 8AM
└────────┬─────────┘
         ↓
┌────────┴─────────┐
│ 2. BASE DE DATOS │  ← ✅ Auto (se guarda)
└────────┬─────────┘
         ↓
┌────────┴─────────┐
│ 3. ANÁLISIS IA   │  ← 🟢 AUTOMATIZAR (batch nocturno)
└────────┬─────────┘
         ↓
┌────────┴─────────┐
│ 4. ESCO MATCHING │  ← 🟢 AUTOMATIZAR (después de IA)
└────────┬─────────┘
         ↓
┌────────┴─────────┐
│ 5. DASHBOARD     │  ← 🟢 AUTOMATIZAR (actualización auto)
│    PÚBLICO       │
└──────────────────┘

TODO FUNCIONA SOLO, SIN INTERVENCIÓN HUMANA
```

**Beneficio:**
- Dashboard siempre actualizado
- No depende de que alguien "se acuerde" de ejecutar
- Datos frescos disponibles inmediatamente

---

## Resumen de la Sección 1

### Lo que tenemos hoy (funciona)
✅ Scraping automático de Bumeran (500 ofertas nuevas cada 3-4 días)
✅ Base de datos operativa (6,521 ofertas)
✅ Dashboard técnico para control interno
✅ Dashboard público con análisis ESCO

### Lo que necesitamos mejorar (requisitos documento)

**Dashboard público:**
- ❌ Navegación confusa (6 tabs → 3 paneles claros)
- ❌ Jerga técnica (CIUO, ESCO → términos comprensibles)
- ❌ Filtros se pierden (locales → globales permanentes)
- ❌ Sin búsqueda ocupaciones (agregar buscador + árbol)
- ❌ Sin exportación por gráfico (agregar botones)

**Información ESCO:**
- ❌ Faltan 240K relaciones ocupación-habilidad
- ❌ No distinguimos conocimientos vs competencias

**Datos de ofertas:**
- ❌ No capturamos: edad, género, tipo contrato
- ❌ Ubicaciones sin normalizar (códigos INDEC)
- ❌ No sabemos si requiere presencialidad
- ❌ No clasificamos permanencia de la oferta

**Automatización:**
- ❌ Pipeline semi-manual (pasos 3, 4, 5 requieren intervención)

---

**Próxima sección:** "¿HACIA DÓNDE VAMOS? Objetivos del Rediseño"
