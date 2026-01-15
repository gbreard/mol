# SECCIÓN 6: ¿CÓMO SE VE EL DASHBOARD NUEVO?
## Interfaz de Usuario - Dashboard Shiny v3.0

---

## 6.1. VISIÓN GENERAL: DOS DASHBOARDS, DOS PROPÓSITOS

El sistema MOL tiene **DOS dashboards diferentes** con públicos y objetivos distintos:

```
┌─────────────────────────────────────────────────────────────────┐
│                    ARQUITECTURA DUAL                            │
└─────────────────────────────────────────────────────────────────┘

DASHBOARD 1: SHINY (Puerto 3840 / shinyapps.io)
├─ Audiencia: Público general, investigadores, analistas
├─ Objetivo: Explorar y analizar ofertas laborales
├─ Lenguaje: Español, sin jerga técnica
├─ Acceso: Web pública (con autenticación)
├─ Tecnología: R + Shiny
└─ Esta sección cubre este dashboard

DASHBOARD 2: PLOTLY (Puerto 8052)
├─ Audiencia: Equipo técnico OEDE
├─ Objetivo: Monitorear pipeline, calidad de datos, errores
├─ Lenguaje: Técnico (códigos, logs, métricas)
├─ Acceso: Solo red interna
├─ Tecnología: Python + Plotly + Dash
└─ Sección 7 cubre este dashboard
```

**Esta sección se enfoca en el Dashboard Shiny (público).**

---

## 6.2. ESTADO ACTUAL: DASHBOARD v2.4

### Problemas identificados

En el documento **"Comentarios al dashboard del Monitor de Ofertas Laborales.docx"** se identificaron múltiples problemas del dashboard actual:

#### **Problema 1: Fragmentación en 6 tabs**

```
Dashboard actual (v2.4):

┌──────────────────────────────────────────────────────────────┐
│ [Tab 1] [Tab 2] [Tab 3] [Tab 4] [Tab 5] [Tab 6]             │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  Contenido del tab seleccionado                              │
│                                                              │
└──────────────────────────────────────────────────────────────┘

❌ Problema: Usuario tiene que ir y venir entre tabs
❌ Filtros se pierden al cambiar de tab
❌ No hay visión integrada
❌ Difícil encontrar información específica
```

**Ejemplo de frustración del usuario:**

```
Analista quiere: "Ver ofertas de IT en CABA con salario >$300K"

Paso 1: Tab "Filtros" → seleccionar sector IT
Paso 2: Tab "Ubicación" → seleccionar CABA
Paso 3: ❌ No hay filtro de salario visible
Paso 4: Volver a Tab "Filtros"
Paso 5: ❌ Se perdió la selección de CABA
Paso 6: Frustración → abandona el dashboard
```

---

#### **Problema 2: Jerga técnica incomprensible**

```
Dashboard actual muestra:

┌─────────────────────────────────────────────────────────────┐
│ Ofertas por CIUO-08                                         │
├─────────────────────────────────────────────────────────────┤
│ 2512: 1,234 ofertas                                         │
│ 2431: 987 ofertas                                           │
│ 5120: 678 ofertas                                           │
└─────────────────────────────────────────────────────────────┘

❌ Usuario promedio: "¿Qué es CIUO-08?"
❌ Usuario promedio: "¿Qué significa 2512?"
❌ Tiene que buscar en Google o preguntar
```

**Lo que debería mostrar:**

```
✅ Ofertas por Ocupación

Desarrolladores de software: 1,234 ofertas
Profesionales de marketing: 987 ofertas
Cocineros: 678 ofertas
```

---

#### **Problema 3: Falta información clave**

```
Dashboard actual NO muestra:

❌ Edad requerida (muchas ofertas lo mencionan)
❌ Género (cuando hay preferencia explícita)
❌ Tipo de contrato (dependencia vs monotributo)
❌ Ubicación normalizada (usa nombres sin estandarizar)
❌ Presencialidad (presencial/remoto/híbrido)
❌ Permanencia de ofertas (cuánto duran online)
```

**Impacto:**
Investigadores quieren hacer análisis como:
- "¿Hay discriminación etaria en IT?" → No se puede responder
- "¿Cuántas ofertas son para monotributo?" → No se puede responder
- "¿Las ofertas remotas duran más o menos?" → No se puede responder

---

#### **Problema 4: Sin exportación por gráfico**

```
Dashboard actual:

Investigador ve gráfico interesante:
"Top 10 skills más demandadas en IT"

Quiere exportar datos para paper académico

❌ Solo puede exportar TODO el dataset (6,521 ofertas)
❌ No puede exportar solo los datos de ESE gráfico
❌ Tiene que procesar el CSV completo en Excel/R
```

---

#### **Problema 5: Filtros no intuitivos**

```
Dashboard actual:

Filtros dispersos en diferentes lugares
Algunos filtros solo en ciertos tabs
No hay "limpiar todos los filtros"
No se ve cuántas ofertas quedan después de filtrar
```

---

## 6.3. REDISEÑO PROPUESTO: DASHBOARD v3.0

### Principios de diseño basados en expertos

El rediseño del dashboard se fundamenta en principios establecidos por expertos en visualización de datos y experiencia de usuario. Estos principios NO son arbitrarios, sino que están respaldados por investigación académica e implementados en los mejores dashboards del mercado (Google Analytics, Tableau, Power BI).

---

#### **Principio 1: Data-Ink Ratio (Edward Tufte)**

**Autor:** Edward Tufte - "The Visual Display of Quantitative Information" (1983)

**Concepto:**
```
Data-Ink Ratio = Tinta usada para mostrar datos / Tinta total usada

Objetivo: Maximizar datos, minimizar decoración
```

**Problema en v2.4:**
```
❌ Mucho diseño decorativo (bordes, sombras, fondos de colores)
❌ Poco espacio para los datos reales
❌ Ratio estimado: 40% (bajo)
```

**Solución en v3.0:**
```
✅ Eliminar elementos decorativos innecesarios
✅ Más espacio para visualizaciones
✅ Ratio objetivo: >70%

Ejemplo concreto:
ANTES: Box con borde grueso + fondo coloreado + sombra = 60px de "decoración"
DESPUÉS: Sin borde, fondo blanco simple = 5px → más espacio para el gráfico
```

---

#### **Principio 2: Jerarquía de Información (Stephen Few)**

**Autor:** Stephen Few - "Information Dashboard Design" (2006)

**Concepto:**
```
Usuario debe saber QUÉ es importante con solo mirar 2 segundos
→ La información más crítica debe ser más grande/prominente
```

**Problema en v2.4:**
```
❌ Todas las métricas tienen el mismo tamaño
❌ Usuario no sabe cuál mirar primero
❌ Jerarquía visual plana
```

**Solución en v3.0:**
```
✅ Métrica PRINCIPAL (HERO): 2x más grande
✅ Métricas secundarias: tamaño normal
✅ Métricas terciarias: más pequeñas

Ejemplo:
┌──────────────────────────┐
│  6,521 OFERTAS          │  ← HERO (48px, bold)
│  TOTALES                 │
├──────────────────────────┤
│ 2,345 Empresas  │ 14 días│  ← Secundarias (24px)
└──────────────────────────┘
```

**Justificación:** Investigación de eye-tracking muestra que usuarios leen dashboards en patrón "F" - esquina superior izquierda es lo primero que ven.

---

#### **Principio 3: Ley de Hick (5±2 Opciones)**

**Autor:** William Hick (1952) / George Miller (1956)

**Concepto:**
```
Ley de Hick: Tiempo de decisión aumenta logarítmicamente con opciones
Ley de Miller: Humanos procesan 5±2 elementos a la vez (límite cognitivo)
```

**Problema en v2.4:**
```
❌ 6 tabs (sobrecarga cognitiva)
❌ Algunas pestañas con 6-8 gráficos simultáneos (muy alto)
❌ Usuario paralizado por exceso de opciones
```

**Solución en v3.0:**
```
✅ 3 paneles (dentro del límite 5±2)
✅ Máximo 3-4 visualizaciones por panel
✅ Decisiones más rápidas

Fórmula de Hick: T = b × log₂(n+1)
Donde T = tiempo, n = opciones

Ejemplo:
6 tabs: T = b × log₂(7) = 2.8b
3 paneles: T = b × log₂(4) = 2.0b
→ 28% más rápido en v3.0
```

---

#### **Principio 4: Recognition over Recall (Jakob Nielsen)**

**Autor:** Jakob Nielsen - "10 Usability Heuristics" (1994)

**Concepto:**
```
Es más fácil RECONOCER información visible
que RECORDAR información que viste antes

→ Minimizar carga de memoria del usuario
```

**Problema en v2.4:**
```
❌ Usuario aplica filtros en Tab 1
❌ Cambia a Tab 2
❌ Tiene que RECORDAR qué filtros aplicó
❌ No hay indicador visual de filtros activos
```

**Solución en v3.0:**
```
✅ Filtros SIEMPRE visibles en sidebar
✅ Badge visual con filtros activos
✅ Contador en tiempo real: "Mostrando 487 de 6,521 ofertas"
✅ Usuario RECONOCE (no tiene que recordar)

Ejemplo visual:
┌─────────────────────────────────────┐
│ FILTROS ACTIVOS:                    │
│ [Provincia: CABA ✕]                 │
│ [Sector: IT ✕]                      │
│ [Modalidad: Remoto ✕]               │
│                                     │
│ 📊 Mostrando 487 ofertas            │
└─────────────────────────────────────┘
```

---

#### **Principio 5: Above the Fold (Stephen Few)**

**Autor:** Stephen Few - "Dashboard Confusion" (2007)

**Concepto:**
```
Información CRÍTICA debe estar visible sin hacer scroll
(Término tomado del periodismo: "sobre el pliegue del periódico")
```

**Problema en v2.4:**
```
❌ Usuario debe hacer scroll para ver métricas importantes
❌ Información clave "enterrada" abajo
❌ Primera impresión: dashboard vacío o incompleto
```

**Solución en v3.0:**
```
✅ Métricas principales en primera pantalla
✅ Gráficos más importantes arriba
✅ Información detallada abajo (para quien quiera profundizar)

Prioridad visual:
1. Hero metrics (0-200px): SIN scroll
2. Gráficos principales (200-600px): Scroll mínimo
3. Detalles/tablas (>600px): Scroll para explorar
```

---

#### **Principio 6: Filtros Instantáneos (UX Moderno)**

**Referencia:** Google Analytics, Tableau, Power BI (estándar de industria 2020+)

**Concepto:**
```
Usuarios esperan feedback INSTANTÁNEO al cambiar filtros
No toleran botones "Aplicar" (UX anticuada de 2010)
```

**Problema en v2.4:**
```
❌ Usuario cambia filtro
❌ DEBE hacer click en "Aplicar Filtros"
❌ 2 clicks en lugar de 1 → frustración
❌ Flujo lento de exploración
```

**Solución en v3.0:**
```
✅ Filtros reactivos con debounce(300ms)
✅ Dashboard se actualiza automáticamente
✅ Sin botones "Aplicar"

Implementación técnica:
reactive({
  # Espera 300ms después del último cambio
  # Evita re-renderizar con cada tecla presionada
  input$filtro %>% debounce(300)
})
```

**Benchmarking:**
- Google Analytics: ✅ Instantáneo
- Tableau: ✅ Instantáneo
- Power BI: ✅ Instantáneo
- Excel (filtros): ✅ Instantáneo
- MOL v2.4: ❌ Requiere botón

---

#### **Principio 7: Feedback Visual de Contexto**

**Referencia:** Don Norman - "The Design of Everyday Things" (1988)

**Concepto:**
```
Sistema debe MOSTRAR su estado actual en todo momento
Usuario nunca debe preguntarse: "¿Qué está pasando?"
```

**Problema en v2.4:**
```
❌ Usuario cambia de tab → pierde contexto
❌ No sabe si está viendo datos filtrados o totales
❌ No hay indicador de "cargando"
```

**Solución en v3.0:**
```
✅ Feedback constante:
   "Estos gráficos muestran: Ofertas IT en CABA | Última semana"

✅ Indicadores de carga:
   [⏳ Cargando datos...]

✅ Estados vacíos informativos:
   "No hay ofertas con estos filtros. Intenta ampliar la búsqueda."
```

---

#### **Principio 8: Top N en Visualizaciones (Edward Tufte)**

**Autor:** Edward Tufte + Cleveland & McGill (1984) - "Graphical Perception"

**Concepto:**
```
Gráficos con >10 categorías son difíciles de leer
Usuario pierde capacidad de comparar

Cleveland encontró: Humanos comparan MÁXIMO 7-10 barras eficientemente
```

**Problema en v2.4:**
```
❌ Gráficos con Top 20, Top 30 categorías
❌ Barras muy delgadas (ilegibles)
❌ Labels solapados
❌ Usuario abrumado
```

**Solución en v3.0:**
```
✅ Máximo Top 10 visible por defecto
✅ Botón "Ver más" para expandir si es necesario
✅ Categoría "Otros" agrupa el resto

Ejemplo:
ANTES: 20 barras de 10px cada una = difícil de leer
DESPUÉS: 10 barras de 25px cada una = fácil de comparar
```

---

#### **Principio 9: Responsive Design (Mobile First)**

**Referencia:** Luke Wroblewski - "Mobile First" (2011)

**Concepto:**
```
Diseñar primero para pantallas pequeñas
Luego expandir para pantallas grandes
(No al revés)
```

**Problema en v2.4:**
```
❌ Dashboard diseñado solo para desktop
❌ En mobile: sidebar ocupa 75% de pantalla (inutilizable)
❌ Gráficos cortados
❌ Texto ilegible
```

**Solución en v3.0:**
```
✅ Sidebar colapsable automáticamente en mobile
✅ Gráficos adaptan tamaño
✅ Texto legible (mínimo 14px)
✅ Botones touch-friendly (mínimo 44×44px)

Breakpoints:
- Mobile: <768px → sidebar colapsado
- Tablet: 768-1024px → sidebar reducido
- Desktop: >1024px → sidebar completo
```

---

#### **Principio 10: Loading States (Performance UX)**

**Referencia:** Nielsen Norman Group - "Response Time Guidelines" (1993/2020)

**Concepto:**
```
Tiempos de respuesta percibidos:
- <0.1s: Instantáneo (no necesita feedback)
- 0.1-1s: Ligero delay (no molesta)
- 1-10s: DEBE mostrar indicador de carga
- >10s: Mostrar barra de progreso
```

**Problema en v2.4:**
```
❌ Usuario hace click en filtro
❌ Dashboard se congela 2-3 segundos
❌ No hay indicador de "estoy procesando"
❌ Usuario hace click múltiples veces (frustrante)
```

**Solución en v3.0:**
```
✅ Spinner de carga visible
✅ Mensaje: "Cargando datos..."
✅ Usuario sabe que el sistema está funcionando

Implementación:
withSpinner(plotlyOutput("grafico"))
→ Muestra spinner automáticamente mientras renderiza
```

---

### Resumen: 10 Principios Implementados

| # | Principio | Experto | Impacto UX |
|---|-----------|---------|------------|
| 1 | Data-Ink Ratio | Edward Tufte | Más espacio para datos |
| 2 | Jerarquía de Información | Stephen Few | Lectura más rápida |
| 3 | Ley de Hick (5±2) | Hick/Miller | Decisiones 28% más rápidas |
| 4 | Recognition over Recall | Jakob Nielsen | Menos carga cognitiva |
| 5 | Above the Fold | Stephen Few | Info crítica visible |
| 6 | Filtros Instantáneos | UX Moderno | Exploración fluida |
| 7 | Feedback de Contexto | Don Norman | Usuario siempre orientado |
| 8 | Top N Visualizaciones | Tufte/Cleveland | Gráficos legibles |
| 9 | Responsive Design | Luke Wroblewski | Funciona en mobile |
| 10 | Loading States | Nielsen Norman | Percepción de rapidez |

**Resultado esperado:**
- Puntuación UX: 6.5/10 (v2.4) → 8.5/10 (v3.0)
- Tiempo para encontrar información: -80%
- Satisfacción de usuario: +50%

---

### Aplicaciones concretas en v3.0

**1. Menos es más** (Tufte)
```
v2.4: 6 tabs fragmentados + elementos decorativos
v3.0: 3 paneles claros + diseño minimalista
```

**2. Lenguaje humano** (Nielsen - Recognition)
```
v2.4: "CIUO-08 2512", "ESCO skills", "NLP v5.1"
v3.0: "Desarrolladores de software", "Habilidades requeridas"
```

**3. Filtros siempre visibles** (Nielsen - Recognition)
```
v2.4: Filtros se pierden entre tabs
v3.0: Filtros globales en barra lateral fija con badges
```

**4. Exportación granular** (Usabilidad)
```
v2.4: Solo exportar dataset completo
v3.0: Botón "Exportar" en cada gráfico
```

**5. Información completa** (Completitud)
```
v2.4: 17 campos mostrados
v3.0: 23 campos (+ edad, género, contrato, permanencia, presencialidad)
```

---

### Arquitectura de 3 paneles

```
┌─────────────────────────────────────────────────────────────────┐
│                    DASHBOARD SHINY v3.0                         │
└─────────────────────────────────────────────────────────────────┘

┌──────────────┬──────────────────────────────────────────────────┐
│              │                                                  │
│  FILTROS     │  [PANORAMA GENERAL] [REQUERIMIENTOS] [OFERTAS]   │
│  GLOBALES    │              ↑                                    │
│              │         3 paneles claros                          │
│  (Siempre    │                                                  │
│   visibles)  │  Contenido del panel seleccionado                │
│              │                                                  │
│              │                                                  │
└──────────────┴──────────────────────────────────────────────────┘
```

---

## 6.4. BARRA LATERAL: FILTROS GLOBALES

### Los 5 filtros principales

Estos filtros están **siempre visibles** y aplican a TODOS los paneles.

```
┌─────────────────────────────────────────────┐
│ FILTROS                                     │
├─────────────────────────────────────────────┤
│                                             │
│ 🔍 Búsqueda libre                           │
│ ┌─────────────────────────────────────────┐ │
│ │ Buscar por palabra clave...             │ │
│ └─────────────────────────────────────────┘ │
│                                             │
│ 📍 Provincia                                │
│ ☐ Ciudad Autónoma de Buenos Aires (3,245)  │
│ ☐ Buenos Aires (1,876)                     │
│ ☐ Córdoba (687)                            │
│ ☐ Santa Fe (234)                           │
│ ☐ Mendoza (98)                             │
│ ... (19 más)                                │
│                                             │
│ 💼 Sector                                   │
│ ☐ Tecnología e IT (2,345)                  │
│ ☐ Administración y Finanzas (1,567)        │
│ ☐ Ventas y Comercial (987)                 │
│ ☐ Gastronomía y Hotelería (678)            │
│ ☐ Salud (456)                              │
│ ... (15 más)                                │
│                                             │
│ 🏢 Tipo de empleo                           │
│ ☐ Relación de dependencia (5,234)          │
│ ☐ Monotributo / Freelance (987)            │
│ ☐ No especificado (300)                    │
│                                             │
│ 🏠 Modalidad                                │
│ ☐ Presencial (3,456)                       │
│ ☐ Remoto (1,987)                           │
│ ☐ Híbrido (876)                            │
│ ☐ No especificado (202)                    │
│                                             │
│ ⏱️ Fecha de publicación                     │
│ ○ Última semana (487 ofertas)              │
│ ○ Último mes (1,876 ofertas)               │
│ ○ Últimos 3 meses (4,234 ofertas)          │
│ ● Todas (6,521 ofertas) [seleccionado]     │
│                                             │
├─────────────────────────────────────────────┤
│ 📊 Ofertas mostradas: 6,521                 │
│                                             │
│ [🗑️ Limpiar filtros]                       │
└─────────────────────────────────────────────┘
```

---

### Comportamiento de filtros

#### **Filtrado acumulativo (AND)**

```
Usuario selecciona:
✅ Provincia: "Ciudad Autónoma de Buenos Aires"
✅ Sector: "Tecnología e IT"
✅ Modalidad: "Remoto"

Resultado:
Ofertas que cumplen las 3 condiciones simultáneamente
→ 487 ofertas

Contador se actualiza en tiempo real:
"📊 Ofertas mostradas: 487"
```

---

#### **Múltiple selección dentro del mismo filtro (OR)**

```
Usuario selecciona:
✅ Provincia: "Ciudad Autónoma de Buenos Aires"
✅ Provincia: "Córdoba"

Resultado:
Ofertas de CABA O Córdoba
→ 3,245 + 687 = 3,932 ofertas
```

---

#### **Búsqueda libre (busca en título + descripción)**

```
Usuario escribe en búsqueda: "python"

Resultado:
Todas las ofertas que mencionan "python" en título o descripción
→ 567 ofertas

Se combina con otros filtros:
Si además selecciona "Provincia: CABA"
→ 345 ofertas de Python en CABA
```

---

#### **Limpiar todos los filtros**

```
Botón: [🗑️ Limpiar filtros]

Acción:
- Deselecciona todos los checkboxes
- Borra texto de búsqueda libre
- Resetea a "Todas" en fecha de publicación
- Muestra contador: "📊 Ofertas mostradas: 6,521" (total)
```

---

## 6.5. PANEL 1: PANORAMA GENERAL

### Objetivo

Dar una **visión de alto nivel** del mercado laboral:
- ¿Cuántas ofertas hay en total?
- ¿Qué sectores tienen más demanda?
- ¿Dónde se concentran las ofertas?
- ¿Qué ocupaciones son las más buscadas?

---

### Estructura del panel

```
┌─────────────────────────────────────────────────────────────────┐
│ PANORAMA GENERAL                                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌───────────┐ │
│ │ 6,521       │ │ 2,345       │ │ 3,245       │ │ 14.2 días │ │
│ │ Ofertas     │ │ Empresas    │ │ Ofertas     │ │ Promedio  │ │
│ │ totales     │ │ publicando  │ │ en CABA     │ │ online    │ │
│ └─────────────┘ └─────────────┘ └─────────────┘ └───────────┘ │
│                                                                 │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ TOP 10 SECTORES CON MÁS OFERTAS          [📥 Exportar CSV] │ │
│ ├─────────────────────────────────────────────────────────────┤ │
│ │                                                             │ │
│ │ Tecnología e IT          ████████████████████ 2,345 (36%)  │ │
│ │ Administración           ███████████ 1,567 (24%)           │ │
│ │ Ventas y Comercial       ██████ 987 (15%)                  │ │
│ │ Gastronomía              ████ 678 (10%)                    │ │
│ │ Salud                    ███ 456 (7%)                      │ │
│ │ Logística                ██ 298 (5%)                       │ │
│ │ Construcción             █ 112 (2%)                        │ │
│ │ Educación                █ 45 (1%)                         │ │
│ │ Legal                    █ 23 (0.3%)                       │ │
│ │ Otros                    █ 30 (0.5%)                       │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                 │
│ ┌────────────────────────┐ ┌────────────────────────────────┐  │
│ │ MAPA: OFERTAS POR      │ │ TOP 10 OCUPACIONES             │  │
│ │ PROVINCIA              │ │                  [📥 Exportar] │  │
│ ├────────────────────────┤ ├────────────────────────────────┤  │
│ │                        │ │ 1. Desarrolladores de          │  │
│ │     [Mapa interactivo  │ │    software: 1,234             │  │
│ │      de Argentina      │ │ 2. Vendedores: 987             │  │
│ │      con colores por   │ │ 3. Administrativos: 876        │  │
│ │      cantidad ofertas] │ │ 4. Contadores: 654             │  │
│ │                        │ │ 5. Cocineros: 567              │  │
│ │ Hover: muestra         │ │ 6. Enfermeros: 456             │  │
│ │ provincia + cantidad   │ │ 7. Analistas de datos: 389     │  │
│ │                        │ │ 8. Recepcionistas: 298         │  │
│ │ Click: filtra por      │ │ 9. Choferes: 234               │  │
│ │ esa provincia          │ │ 10. Diseñadores: 198           │  │
│ └────────────────────────┘ └────────────────────────────────┘  │
│                                                                 │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ EVOLUCIÓN TEMPORAL: OFERTAS POR MES      [📥 Exportar CSV] │ │
│ ├─────────────────────────────────────────────────────────────┤ │
│ │                                                             │ │
│ │    │                          ╭─╮                           │ │
│ │600 │                    ╭─╮   │ │                           │ │
│ │    │             ╭──╮   │ │╭──╯ ╰──╮                        │ │
│ │400 │      ╭──╮   │  │╭──╯ ││       │                        │ │
│ │    │   ╭──╯  ╰───╯  ╰╯     ╰╯       ╰───                    │ │
│ │200 │╭──╯                                                    │ │
│ │    └─────────────────────────────────────────────           │ │
│ │    Ene Feb Mar Abr May Jun Jul Ago Sep Oct Nov Dic          │ │
│ │                                                             │ │
│ │ Insight: Pico en Nov-Dic (verano), caída en Ene (vacaciones)│ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                 │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ DISTRIBUCIÓN: MODALIDAD DE TRABAJO       [📥 Exportar CSV] │ │
│ ├─────────────────────────────────────────────────────────────┤ │
│ │                                                             │ │
│ │         Presencial: 53%  (3,456 ofertas)                    │ │
│ │         Remoto: 30%      (1,987 ofertas)                    │ │
│ │         Híbrido: 13%     (876 ofertas)                      │ │
│ │         No especif.: 3%  (202 ofertas)                      │ │
│ │                                                             │ │
│ │       [Gráfico de torta con 4 porciones]                    │ │
│ └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

---

### Interactividad

**1. Hover en gráficos**
```
Usuario pasa mouse sobre barra "Tecnología e IT"
→ Tooltip aparece: "2,345 ofertas (36% del total)"
```

**2. Click en gráfico de barras**
```
Usuario hace click en "Tecnología e IT"
→ Automáticamente se filtra dashboard por ese sector
→ Todos los paneles se actualizan
→ Contador: "📊 Ofertas mostradas: 2,345"
```

**3. Click en provincia del mapa**
```
Usuario hace click en "Córdoba" en el mapa
→ Se filtra por Provincia: Córdoba
→ Mapa destaca Córdoba con color más intenso
→ Contador actualizado
```

**4. Botón exportar**
```
Usuario hace click en [📥 Exportar CSV] en "Top 10 sectores"
→ Descarga CSV con 2 columnas:
   Sector,Cantidad_Ofertas
   Tecnología e IT,2345
   Administración,1567
   ...
```

---

## 6.6. PANEL 2: REQUERIMIENTOS

### Objetivo

Analizar **qué están pidiendo las empresas**:
- ¿Qué habilidades técnicas son más demandadas?
- ¿Qué soft skills buscan?
- ¿Qué nivel educativo requieren?
- ¿Cuántos años de experiencia piden?
- ¿Qué idiomas necesitan?

---

### Estructura del panel

```
┌─────────────────────────────────────────────────────────────────┐
│ REQUERIMIENTOS                                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ TOP 20 HABILIDADES TÉCNICAS MÁS DEMANDADAS [📥 Exportar]   │ │
│ ├─────────────────────────────────────────────────────────────┤ │
│ │                                                             │ │
│ │ 1. Python               ████████████ 567 ofertas (24%)     │ │
│ │ 2. Excel avanzado       ██████████ 432 ofertas (18%)       │ │
│ │ 3. Inglés avanzado      █████████ 389 ofertas (16%)        │ │
│ │ 4. SQL                  ████████ 301 ofertas (13%)         │ │
│ │ 5. React                ██████ 245 ofertas (10%)           │ │
│ │ 6. SAP                  █████ 198 ofertas (8%)             │ │
│ │ 7. JavaScript           ████ 176 ofertas (7%)              │ │
│ │ 8. Java                 ████ 165 ofertas (7%)              │ │
│ │ 9. Power BI             ███ 134 ofertas (6%)               │ │
│ │ 10. Contabilidad        ███ 128 ofertas (5%)               │ │
│ │ ...                                                         │ │
│ │                                                             │ │
│ │ 💡 Insight: Python supera a Java por primera vez           │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                 │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ TOP 10 SOFT SKILLS MÁS VALORADAS             [📥 Exportar] │ │
│ ├─────────────────────────────────────────────────────────────┤ │
│ │                                                             │ │
│ │ 1. Trabajo en equipo              1,987 ofertas (30%)      │ │
│ │ 2. Proactividad                   1,654 ofertas (25%)      │ │
│ │ 3. Buena comunicación             1,432 ofertas (22%)      │ │
│ │ 4. Resolución de problemas        1,098 ofertas (17%)      │ │
│ │ 5. Liderazgo                      876 ofertas (13%)        │ │
│ │ 6. Orientación a resultados       654 ofertas (10%)        │ │
│ │ 7. Adaptabilidad                  543 ofertas (8%)         │ │
│ │ 8. Atención al detalle            432 ofertas (7%)         │ │
│ │ 9. Capacidad analítica            321 ofertas (5%)         │ │
│ │ 10. Creatividad                   234 ofertas (4%)         │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                 │
│ ┌────────────────────────┐ ┌────────────────────────────────┐  │
│ │ NIVEL EDUCATIVO        │ │ AÑOS DE EXPERIENCIA            │  │
│ │ REQUERIDO              │ │ REQUERIDOS                     │  │
│ ├────────────────────────┤ ├────────────────────────────────┤  │
│ │                        │ │                                │  │
│ │ Universitario: 45%     │ │ 0-1 años: 23%                  │  │
│ │ Secundario: 32%        │ │ 2-3 años: 34%                  │  │
│ │ Terciario: 15%         │ │ 4-5 años: 28%                  │  │
│ │ Posgrado: 5%           │ │ >5 años: 15%                   │  │
│ │ No especif.: 3%        │ │                                │  │
│ │                        │ │ [Gráfico de barras]            │  │
│ │ [Gráfico de barras]    │ │                                │  │
│ └────────────────────────┘ └────────────────────────────────┘  │
│                                                                 │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ IDIOMAS REQUERIDOS                           [📥 Exportar] │ │
│ ├─────────────────────────────────────────────────────────────┤ │
│ │                                                             │ │
│ │ Inglés (avanzado):      ██████████ 1,234 ofertas           │ │
│ │ Inglés (intermedio):    ████ 567 ofertas                   │ │
│ │ Inglés (básico):        ██ 234 ofertas                     │ │
│ │ Portugués:              █ 89 ofertas                       │ │
│ │ Otros idiomas:          █ 34 ofertas                       │ │
│ │                                                             │ │
│ │ 💡 68% de las ofertas NO requieren idioma extranjero        │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                 │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ ANÁLISIS: CONOCIMIENTOS VS COMPETENCIAS      [📥 Exportar] │ │
│ ├─────────────────────────────────────────────────────────────┤ │
│ │                                                             │ │
│ │ ¿Qué es esto?                                               │ │
│ │ Clasificamos requerimientos en:                             │ │
│ │ - CONOCIMIENTOS: Saberes técnicos (ej: Python, SAP)         │ │
│ │ - COMPETENCIAS: Habilidades prácticas (ej: liderazgo)       │ │
│ │                                                             │ │
│ │ Distribución promedio por sector:                           │ │
│ │                                                             │ │
│ │ Tecnología e IT:         [████████░░] 72% Conocimientos    │ │
│ │ Salud:                   [███████░░░] 68% Conocimientos    │ │
│ │ Administración:          [█████░░░░░] 55% Conocimientos    │ │
│ │ Ventas:                  [███░░░░░░░] 27% Conocimientos    │ │
│ │ Gestión:                 [██░░░░░░░░] 32% Conocimientos    │ │
│ │                                                             │ │
│ │ 💡 Sectores técnicos requieren más conocimientos            │ │
│ │    Sectores de servicios requieren más competencias        │ │
│ └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

---

### Features especiales

#### **1. Búsqueda de skill específica**

```
┌─────────────────────────────────────────────┐
│ Buscar habilidad específica:                │
│ ┌─────────────────────────────────────────┐ │
│ │ react                                   │ │
│ └─────────────────────────────────────────┘ │
│                                             │
│ Resultados:                                 │
│ - React: 245 ofertas                        │
│ - React Native: 34 ofertas                  │
│ - Redux (relacionado): 89 ofertas           │
└─────────────────────────────────────────────┘
```

---

#### **2. Comparación de skills**

```
Usuario selecciona 2 skills para comparar:
☑ Python (567 ofertas)
☑ Java (165 ofertas)

Gráfico de comparación:
- Evolución temporal (Python creciendo, Java estable)
- Distribución geográfica (Python en CABA, Java más distribuido)
- Salarios promedio (Python $350K, Java $320K)
```

---

#### **3. Análisis de brechas**

```
┌─────────────────────────────────────────────┐
│ SKILLS EMERGENTES (>50% crecimiento anual) │
├─────────────────────────────────────────────┤
│                                             │
│ 1. Terraform:        +87% vs año anterior  │
│ 2. Kubernetes:       +76% vs año anterior  │
│ 3. React Native:     +65% vs año anterior  │
│ 4. Power BI:         +54% vs año anterior  │
│                                             │
│ 💡 Oportunidad: Capacitar en estas skills   │
└─────────────────────────────────────────────┘
```

---

## 6.7. PANEL 3: OFERTAS LABORALES

### Objetivo

Explorar **ofertas individuales** con filtros avanzados:
- Ver tabla de ofertas con campos clave
- Leer descripción completa de cada oferta
- Filtrar por múltiples criterios
- Exportar lista de ofertas filtradas

---

### Estructura del panel

```
┌─────────────────────────────────────────────────────────────────┐
│ OFERTAS LABORALES                                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ 📊 Mostrando 6,521 ofertas                    [📥 Exportar CSV]│
│                                                                 │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ TABLA DE OFERTAS                                            │ │
│ ├──────┬──────────┬─────────┬─────────┬──────────┬──────────┤ │
│ │ Título│ Empresa │ Ubicación│ Sector │ Modalidad│ Publicada│ │
│ ├──────┼──────────┼─────────┼─────────┼──────────┼──────────┤ │
│ │ Desarr│ Globant │ CABA    │ IT      │ Remoto   │ Hace 2   │ │
│ │ ollado│          │         │         │          │ días     │ │
│ │ r Pyth│          │         │         │          │          │ │
│ │ on Sr │          │         │         │          │ [👁 Ver] │ │
│ ├──────┼──────────┼─────────┼─────────┼──────────┼──────────┤ │
│ │ Vended│ Coca-Cola│ Córdoba │ Ventas  │ Presenc. │ Hace 1   │ │
│ │ or Sr │          │         │         │          │ día      │ │
│ │       │          │         │         │          │ [👁 Ver] │ │
│ ├──────┼──────────┼─────────┼─────────┼──────────┼──────────┤ │
│ │ Admin │ YPF      │ CABA    │ Admin   │ Híbrido  │ Hace 5   │ │
│ │ istrat│          │         │         │          │ días     │ │
│ │ ivo   │          │         │         │          │ [👁 Ver] │ │
│ ├──────┴──────────┴─────────┴─────────┴──────────┴──────────┤ │
│ │ ...                                                         │ │
│ │                                                             │ │
│ │ [Paginación: < 1 2 3 ... 327 >]   (20 ofertas por página)  │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                 │
│ COLUMNAS CONFIGURABLES:                                         │
│ ☑ Título  ☑ Empresa  ☑ Ubicación  ☑ Sector  ☑ Modalidad        │
│ ☑ Fecha   ☐ Salario  ☐ Experiencia  ☐ Educación  ☐ Idioma      │
│                                                                 │
│ ORDENAR POR:                                                    │
│ ● Fecha de publicación (más reciente primero) [seleccionado]   │
│ ○ Título (A-Z)                                                  │
│ ○ Empresa (A-Z)                                                 │
│ ○ Ubicación (A-Z)                                               │
└─────────────────────────────────────────────────────────────────┘
```

---

### Modal: Ver detalle de oferta

Cuando el usuario hace click en [👁 Ver]:

```
┌─────────────────────────────────────────────────────────────────┐
│ DESARROLLADOR PYTHON SR                                    [✕]  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ 🏢 EMPRESA: Globant                                             │
│ 📍 UBICACIÓN: Ciudad Autónoma de Buenos Aires                   │
│ 🏠 MODALIDAD: Remoto                                            │
│ 📅 PUBLICADA: 15/01/2025 (hace 2 días)                          │
│ 🔗 LINK: [Ver en Bumeran]                                       │
│                                                                 │
│ ─────────────────────────────────────────────────────────────── │
│                                                                 │
│ 📝 DESCRIPCIÓN:                                                 │
│                                                                 │
│ En Globant buscamos incorporar un Desarrollador Python Senior   │
│ para trabajar en proyectos internacionales de alto impacto.     │
│                                                                 │
│ Trabajarás con tecnologías de vanguardia y en un equipo ágil    │
│ colaborativo...                                                 │
│                                                                 │
│ [Mostrar descripción completa]                                  │
│                                                                 │
│ ─────────────────────────────────────────────────────────────── │
│                                                                 │
│ ✅ REQUISITOS INDISPENSABLES:                                   │
│ • 3-5 años de experiencia en desarrollo Python                  │
│ • Título universitario (Ingeniería en Sistemas o afines)        │
│ • Inglés avanzado                                               │
│                                                                 │
│ 🟡 REQUISITOS DESEABLES:                                        │
│ • Experiencia con Django o Flask                                │
│ • Conocimiento de Docker y Kubernetes                           │
│ • Experiencia en metodologías ágiles                            │
│                                                                 │
│ ─────────────────────────────────────────────────────────────── │
│                                                                 │
│ 🔧 HABILIDADES TÉCNICAS:                                        │
│ Python • Django • React • PostgreSQL • Docker • Git             │
│                                                                 │
│ 💼 HABILIDADES BLANDAS:                                         │
│ Trabajo en equipo • Liderazgo • Resolución de problemas         │
│                                                                 │
│ ─────────────────────────────────────────────────────────────── │
│                                                                 │
│ 💰 SALARIO: $300.000 - $400.000                                 │
│                                                                 │
│ 🎁 BENEFICIOS:                                                  │
│ • Prepaga para el grupo familiar                                │
│ • Capacitación continua                                         │
│ • Trabajo 100% remoto                                           │
│ • Horario flexible                                              │
│ • Bonus por objetivos                                           │
│                                                                 │
│ ─────────────────────────────────────────────────────────────── │
│                                                                 │
│ 📊 CLASIFICACIÓN AUTOMÁTICA:                                    │
│ • Ocupación: Desarrolladores de software                        │
│ • Sector: Tecnología e IT                                       │
│ • Permanencia estimada: 10-15 días online                       │
│                                                                 │
│ ─────────────────────────────────────────────────────────────── │
│                                                                 │
│ [📥 Exportar esta oferta] [🔗 Compartir link] [✕ Cerrar]       │
└─────────────────────────────────────────────────────────────────┘
```

---

### Filtros avanzados adicionales

Además de los 5 filtros globales, en este panel hay filtros específicos:

```
┌─────────────────────────────────────────────┐
│ FILTROS AVANZADOS                           │
├─────────────────────────────────────────────┤
│                                             │
│ 🎓 Nivel educativo                          │
│ ☐ Secundario                                │
│ ☐ Terciario                                 │
│ ☐ Universitario                             │
│ ☐ Posgrado                                  │
│                                             │
│ 💼 Experiencia requerida                    │
│ ☐ Sin experiencia (junior)                  │
│ ☐ 1-3 años                                  │
│ ☐ 4-5 años                                  │
│ ☐ >5 años (senior)                          │
│                                             │
│ 🌐 Idiomas                                  │
│ ☐ Inglés (básico)                           │
│ ☐ Inglés (intermedio)                       │
│ ☐ Inglés (avanzado)                         │
│ ☐ Otros idiomas                             │
│                                             │
│ 💰 Salario mencionado                       │
│ ☐ Sí (300 ofertas)                          │
│ ☐ No (6,221 ofertas)                        │
│                                             │
│ 📌 Con beneficios                            │
│ ☐ Prepaga                                   │
│ ☐ Capacitación                              │
│ ☐ Trabajo remoto                            │
│ ☐ Horario flexible                          │
└─────────────────────────────────────────────┘
```

---

### Exportación granular

```
Botón: [📥 Exportar CSV]

Descarga CSV con SOLO las ofertas filtradas actualmente

Columnas incluidas (configurable):
- titulo
- empresa
- provincia
- localidad
- sector
- modalidad
- fecha_publicacion
- experiencia_min_anios
- nivel_educativo
- idioma_principal
- skills_tecnicas
- soft_skills
- salario_min
- salario_max
- beneficios
- url_original

Ejemplo:
Si hay 487 ofertas filtradas → CSV con 487 filas
```

---

## 6.8. TECNOLOGÍA: R + SHINY

### ¿Por qué Shiny?

**Shiny** es un framework de R para crear dashboards interactivos.

**Ventajas:**
```
✅ Integración nativa con R (lenguaje estadístico)
✅ Gran ecosistema de visualización (ggplot2, plotly)
✅ Fácil despliegue (shinyapps.io gratuito)
✅ Reactivo (actualización automática al cambiar filtros)
✅ Open source (sin costos de licencia)
```

**Desventajas:**
```
❌ Más lento que dashboards en JavaScript puro
❌ Limitado en personalización de UI vs React
❌ Requiere servidor con R instalado
```

**Decisión:** Shiny es ideal para dashboards analíticos con audiencia técnica/investigadora.

---

### Arquitectura técnica

```
┌─────────────────────────────────────────────────────────────────┐
│                    SHINY APP                                    │
└─────────────────────────────────────────────────────────────────┘

FRONTEND (UI)
├─ Archivo: ui.R
├─ Define estructura visual (sidebar, panels, gráficos)
├─ Define inputs (filtros, botones)
└─ Define outputs (placeholders para gráficos)

BACKEND (Server)
├─ Archivo: server.R
├─ Carga datos (ofertas_esco_shiny.csv)
├─ Procesa filtros (reactive expressions)
├─ Genera gráficos (renderPlot, renderDataTable)
└─ Maneja exportaciones (downloadHandler)

DESPLIEGUE
├─ Opción 1: shinyapps.io (cloud gratuito/pago)
│  ├─ URL: https://dos1tv-gerardo-breard.shinyapps.io/dashboard-mol
│  ├─ Autenticación con cuenta de email
│  └─ Actualizaciones vía rsconnect::deployApp()
│
└─ Opción 2: Shiny Server local (puerto 3840)
   ├─ URL: http://localhost:3840/
   ├─ Solo red interna OEDE
   └─ Actualizaciones copiando archivos al servidor
```

---

### Ejemplo de código (simplificado)

#### **ui.R - Estructura del dashboard**

```r
# NO incluir código completo, solo estructura conceptual

library(shiny)
library(shinydashboard)

ui <- dashboardPage(
  # Header
  dashboardHeader(title = "Monitor de Ofertas Laborales v3.0"),

  # Sidebar con filtros globales
  dashboardSidebar(
    textInput("busqueda", "Buscar palabra clave"),
    checkboxGroupInput("provincia", "Provincia", choices = provincias),
    checkboxGroupInput("sector", "Sector", choices = sectores),
    ...
  ),

  # Body con 3 tabs/paneles
  dashboardBody(
    tabsetPanel(
      tabPanel("Panorama General", ...),
      tabPanel("Requerimientos", ...),
      tabPanel("Ofertas Laborales", ...)
    )
  )
)
```

---

#### **server.R - Lógica de negocio**

```r
library(shiny)
library(dplyr)
library(ggplot2)

server <- function(input, output, session) {

  # Cargar datos
  datos <- read.csv("ofertas_esco_shiny.csv")

  # Reactive: datos filtrados según selección del usuario
  datos_filtrados <- reactive({
    df <- datos

    # Filtrar por búsqueda
    if (input$busqueda != "") {
      df <- df %>% filter(grepl(input$busqueda, titulo, ignore.case=TRUE))
    }

    # Filtrar por provincia
    if (!is.null(input$provincia)) {
      df <- df %>% filter(provincia %in% input$provincia)
    }

    # ... más filtros

    return(df)
  })

  # Output: gráfico de sectores
  output$grafico_sectores <- renderPlot({
    datos_filtrados() %>%
      group_by(sector) %>%
      summarise(n = n()) %>%
      ggplot(aes(x=reorder(sector, n), y=n)) +
      geom_bar(stat="identity") +
      coord_flip() +
      labs(title="Top sectores", x="", y="Cantidad ofertas")
  })

  # ... más outputs
}
```

---

### Librerías R utilizadas

| Librería | Uso |
|----------|-----|
| `shiny` | Framework base del dashboard |
| `shinydashboard` | Layout y componentes UI |
| `dplyr` | Manipulación de datos (filtros, agregaciones) |
| `ggplot2` | Visualizaciones estáticas |
| `plotly` | Visualizaciones interactivas |
| `DT` | Tablas interactivas con búsqueda/ordenamiento |
| `leaflet` | Mapas interactivos de Argentina |
| `stringr` | Procesamiento de texto |
| `jsonlite` | Parsing de campos JSON (skills, beneficios) |

---

## 6.9. DESPLIEGUE Y ACTUALIZACIÓN

### Despliegue en shinyapps.io

```
┌─────────────────────────────────────────────────────────────────┐
│ PROCESO DE DESPLIEGUE                                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ 1. Preparar archivos locales:                                   │
│    - ui.R                                                       │
│    - server.R                                                   │
│    - ofertas_esco_shiny.csv (datos)                             │
│    - global.R (configuración)                                   │
│                                                                 │
│ 2. Autenticar con shinyapps.io:                                 │
│    rsconnect::setAccountInfo(                                   │
│      name="dos1tv-gerardo-breard",                              │
│      token="<token>",                                           │
│      secret="<secret>"                                          │
│    )                                                            │
│                                                                 │
│ 3. Desplegar aplicación:                                        │
│    rsconnect::deployApp(                                        │
│      appName="dashboard-mol",                                   │
│      account="dos1tv-gerardo-breard"                            │
│    )                                                            │
│                                                                 │
│ 4. Resultado:                                                   │
│    URL: https://dos1tv-gerardo-breard.shinyapps.io/dashboard-mol│
│    Estado: Online                                               │
│    Tiempo deploy: ~2-3 minutos                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

### Frecuencia de actualización

```
DATOS (ofertas_esco_shiny.csv):
├─ Estado actual: Manual, semanal
├─ Objetivo v2.0: Automático, diario
└─ Proceso:
   1. Pipeline genera CSV nuevo cada día (6 AM)
   2. Script R lee CSV nuevo
   3. Re-deploy automático con rsconnect

CÓDIGO (ui.R, server.R):
├─ Frecuencia: Cuando hay cambios en funcionalidad
├─ Proceso:
   1. Desarrollador modifica código localmente
   2. Prueba en localhost:3840
   3. Si funciona → deploy a shinyapps.io
```

---

### Autenticación y seguridad

**¿Quién puede acceder al dashboard?**

```
Opción 1: Público (sin autenticación)
├─ Cualquiera con el link puede acceder
├─ Ventaja: Máxima difusión
└─ Desventaja: No controlamos quién lo usa

Opción 2: Autenticación con email (recomendado)
├─ Solo usuarios con email autorizado pueden acceder
├─ Implementación: shinymanager package
└─ Base de datos de usuarios permitidos

Opción 3: Autenticación institucional (OEDE)
├─ Solo personal OEDE puede acceder
├─ Implementación: OAuth2 con servidor OEDE
└─ Más complejo de configurar
```

**Decisión actual:** Opción 1 (público) por simplicidad.
**Objetivo v2.0:** Migrar a Opción 2 (autenticación con email).

---

## 6.10. LIMITACIONES Y MEJORAS FUTURAS

### Limitaciones actuales

#### **1. Performance con datasets grandes**

```
Problema:
Con 6,521 ofertas, dashboard carga en ~2-3 segundos.
Si llega a 50,000 ofertas → 10-15 segundos (inaceptable).

Solución futura:
- Implementar paginación en backend (cargar solo 1,000 ofertas a la vez)
- Usar base de datos en lugar de CSV (queries más rápidas)
- Cachear agregaciones pre-calculadas
```

---

#### **2. Sin búsqueda avanzada**

```
Problema:
Búsqueda actual es simple: busca texto en título/descripción.
No permite búsquedas complejas como:
- "Python Y Django Y CABA"
- "Salario > $300K"
- "Publicadas en última semana CON inglés avanzado"

Solución futura:
- Implementar query builder visual
- Permitir operadores booleanos (AND, OR, NOT)
- Guardar búsquedas favoritas
```

---

#### **3. Sin comparación temporal**

```
Problema:
Dashboard muestra estado actual, pero no permite comparar:
- "¿Cómo cambió la demanda de Python en 2024 vs 2023?"
- "¿Aumentó o disminuyó el salario promedio en IT?"

Solución futura:
- Agregar selector de rango temporal
- Gráficos de evolución con 2+ líneas (comparación)
- Análisis de tendencias con proyecciones
```

---

#### **4. Sin alertas personalizadas**

```
Problema:
Usuario tiene que entrar manualmente al dashboard para ver nuevas ofertas.

Solución futura:
- Permitir crear alertas:
  "Notifícame cuando haya ofertas de Python en CABA con salario >$300K"
- Enviar email semanal con resumen de nuevas ofertas
- RSS feed para integraciones externas
```

---

## 6.11. RESUMEN EJECUTIVO: DASHBOARD SHINY

### Estado actual (v2.4)

```
❌ 6 tabs fragmentados (mala UX)
❌ Filtros se pierden entre tabs
❌ Jerga técnica (CIUO-08, ESCO)
❌ Falta información (edad, género, permanencia)
❌ Sin exportación granular
```

---

### Rediseño propuesto (v3.0)

```
✅ 3 paneles claros (Panorama, Requerimientos, Ofertas)
✅ 5 filtros globales siempre visibles
✅ Lenguaje humano (sin códigos técnicos)
✅ 23 campos de información (vs 17 actuales)
✅ Exportación por gráfico
✅ Análisis Knowledge vs Competencies
✅ Mapa interactivo de Argentina
✅ Detalle completo de cada oferta
✅ Clasificación ESCO integrada
```

---

### Plan de implementación

```
FASE 1 (Semana 1-2): Diseño UI/UX
→ Mockups de los 3 paneles
→ Validación con usuarios (directores, analistas)
→ Ajustes según feedback

FASE 2 (Semana 3-4): Desarrollo frontend
→ Implementar ui.R con nueva estructura
→ Implementar 5 filtros globales
→ Implementar 3 paneles con placeholders

FASE 3 (Semana 5-6): Desarrollo backend
→ Implementar server.R con lógica de filtros
→ Generar gráficos estáticos (ggplot2)
→ Implementar tablas interactivas (DT)

FASE 4 (Semana 7): Visualizaciones avanzadas
→ Mapa de Argentina (leaflet)
→ Gráficos interactivos (plotly)
→ Exportación por gráfico

FASE 5 (Semana 8): Testing y ajustes
→ Testing con usuarios reales
→ Corrección de bugs
→ Optimización de performance

FASE 6 (Semana 9): Despliegue
→ Deploy a shinyapps.io
→ Capacitación a usuarios
→ Documentación de uso
```

---

### Impacto esperado

| Métrica | v2.4 | v3.0 | Mejora |
|---------|------|------|--------|
| **Satisfacción de usuario** | 6/10 | 9/10 | +50% |
| **Tiempo para encontrar info** | ~5 min | ~1 min | -80% |
| **Campos de información** | 17 | 23 | +35% |
| **Exportaciones por sesión** | 0.5 | 3.2 | +540% |
| **Usuarios activos/mes** | 45 | 150 (proyección) | +233% |

---

### Próximo paso

El Dashboard Shiny es para el público general. Para el equipo técnico, tenemos el **Dashboard Plotly de monitoreo**. Eso lo vemos en la Sección 7: "¿CÓMO CONTROLAMOS LA CALIDAD? Dashboard Técnico".

---

**FIN DE SECCIÓN 6**

---
