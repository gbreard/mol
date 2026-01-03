# INFORME FUNCIONAL
# MONITOR DE OFERTAS LABORALES (MOL)
## Sistema Integral de Inteligencia del Mercado Laboral Argentino

**Fecha:** Noviembre 2025
**Organismo:** Secretaría de Trabajo, Empleo y Seguridad Social (STEYSS)
**Unidad Ejecutora:** Observatorio de Empleo y Dinámica Empresarial (OEDE)
**Versión:** 1.0

---

## TABLA DE CONTENIDOS

1. [Resumen Ejecutivo](#1-resumen-ejecutivo)
2. [Componentes del Sistema](#2-componentes-del-sistema)
3. [Indicadores de Desempeño](#3-indicadores-de-desempeño)
4. [Casos de Uso - Fase Actual](#4-casos-de-uso---fase-actual)
5. [Casos de Uso - Fase Futura](#5-casos-de-uso---fase-futura)
6. [Potenciales Usuarios y Aplicaciones](#6-potenciales-usuarios-y-aplicaciones)
7. [Brechas Actuales y Próximos Pasos](#7-brechas-actuales-y-próximos-pasos)
8. [Beneficios y Valor Agregado](#8-beneficios-y-valor-agregado)
9. [Glosario de Términos](#9-glosario-de-términos)
10. [Anexos](#10-anexos)

---

## 1. RESUMEN EJECUTIVO

### ¿Qué es el Monitor de Ofertas Laborales (MOL)?

El **Monitor de Ofertas Laborales (MOL)** es un sistema automatizado de inteligencia que recolecta, procesa y analiza ofertas de empleo publicadas en portales argentinos, con el objetivo de generar información estratégica sobre el mercado laboral en tiempo real.

### Visión de Triple Impacto

El MOL está diseñado para transformarse en una plataforma integral con **tres grandes propósitos**:

#### 1. Políticas Públicas Basadas en Evidencia
Proveer a tomadores de decisión en el Estado datos actualizados y confiables sobre:
- Ocupaciones más demandadas
- Habilidades técnicas y blandas requeridas
- Brechas entre oferta y demanda de talento
- Tendencias salariales por sector y región
- Skills emergentes y del futuro

#### 2. Orientación Vocacional y Formativa
Brindar a instituciones educativas información para:
- Diseñar currículas pertinentes
- Identificar necesidades de capacitación
- Orientar a estudiantes en elecciones de carrera
- Validar la empleabilidad de programas académicos

#### 3. Intermediación Laboral Inteligente y Personalizada
Conectar directamente a **buscadores de empleo** y **empresas** mediante:
- Matching automatizado candidato-oferta
- Notificaciones personalizadas en celular
- Orientación sobre brechas de formación
- Benchmarking salarial para empleadores
- Análisis de competencia por talento

### Estado Actual y Proyección

**FASE ACTUAL:** Sistema de análisis para políticas públicas
✅ En producción desde Octubre 2025
✅ 5,704 ofertas procesadas
✅ Scraping automatizado 2 veces por semana
✅ Dashboard público operativo

**FASE FUTURA:** Plataforma de intermediación directa
🔄 En diseño y planificación
🎯 Objetivo: Convertirse en el Portal Nacional de Empleo
🎯 Usuarios objetivo: 500,000+ buscadores + 10,000+ empresas

---

## 2. COMPONENTES DEL SISTEMA

El MOL está compuesto por cuatro módulos principales que trabajan de forma integrada:

### A. Módulo de Recolección Automatizada

**¿Qué hace?**
Recolecta automáticamente ofertas de empleo de múltiples portales argentinos, dos veces por semana (lunes y jueves), sin intervención manual.

**Portales integrados:**
- Bumeran (principal - automatizado)
- ZonaJobs
- Computrabajo
- LinkedIn
- Indeed

**Estado actual:** ✅ **EN PRODUCCIÓN**

**Métricas clave:**
- Total ofertas en base de datos: **5,704**
- Nuevas ofertas por semana: **~600**
- Tiempo de ejecución: 38 minutos por corrida
- Keywords de búsqueda utilizadas: **1,148** términos
- Tasa de productividad: 58.4% (1,340 keywords generan resultados)

**¿Cómo funciona?**
El sistema consulta cada portal con 1,148 términos de búsqueda cuidadosamente seleccionados (ej: "ingeniero civil", "vendedor", "programador Python") y descarga todas las ofertas publicadas en los últimos 30 días. Cada oferta incluye:

- Título del puesto
- Empresa publicante
- Descripción completa del puesto
- Ubicación (provincia/ciudad)
- Modalidad (presencial, remoto, híbrido)
- Fecha de publicación
- URL de la oferta original

**Ventajas:**
- Cobertura amplia del mercado laboral argentino
- Actualización continua y automática
- Sin costo de licencias (datos públicos)
- Trazabilidad completa de cada oferta

---

### B. Módulo de Análisis Inteligente (NLP)

**¿Qué hace?**
Lee y entiende el texto de cada oferta para extraer **18 variables clave** de forma automatizada, como si un analista humano leyera cada aviso.

**Estado actual:** ⚠️ **EN DESARROLLO ACTIVO**
**Cobertura:** 96% de ofertas procesadas (5,479 de 5,704)

**Variables extraídas:**

**Experiencia (3 variables)**
- Años mínimos de experiencia requerida
- Años máximos de experiencia
- Área de experiencia específica

**Educación (4 variables)**
- Nivel educativo (secundario, terciario, universitario, posgrado)
- Estado educativo (completo, en curso, incompleto)
- Carrera específica requerida
- Si el título es excluyente o no

**Idiomas (4 variables)**
- Idioma principal requerido
- Nivel del idioma principal (básico, intermedio, avanzado, nativo)
- Idioma secundario
- Nivel del idioma secundario

**Habilidades (4 variables)**
- Skills técnicas (ej: Python, Excel, AutoCAD) - lista
- Niveles requeridos de cada skill
- Soft skills (ej: trabajo en equipo, liderazgo, proactividad) - lista
- Certificaciones requeridas (ej: PMP, CPA, Six Sigma) - lista

**Compensación (4 variables)**
- Salario mínimo ofrecido
- Salario máximo ofrecido
- Moneda (ARS, USD, EUR)
- Beneficios adicionales (obra social, capacitaciones, etc.) - lista

**Requisitos (2 variables)**
- Requisitos excluyentes (condiciones obligatorias)
- Requisitos deseables (condiciones preferibles pero no obligatorias)

**Jornada (2 variables)**
- Tipo de jornada (full-time, part-time, freelance, por proyecto)
- Horario flexible (sí/no)

**¿Cómo funciona?**
Utiliza técnicas de **Procesamiento de Lenguaje Natural (NLP)** para leer y entender texto, similar a cómo ChatGPT o Google Translate comprenden idiomas. El sistema identifica patrones como "se requiere experiencia de 3 a 5 años" o "excluyente título universitario".

**Gap crítico identificado:**
> "Todavía no tenemos bien trabajado el tema de las habilidades, carreras, formación, demanda laboral para determinados perfiles en determinadas regiones del país"

**Objetivo de mejora:** Aumentar precisión de 40% a 85% en todos los campos.

---

### C. Módulo de Clasificación Ocupacional (ESCO)

**¿Qué hace?**
Clasifica cada oferta según un estándar internacional de ocupaciones y habilidades utilizado en la Unión Europea, permitiendo comparar el mercado argentino con otros países.

**Estado actual:** ✅ **FUNCIONAL**

**Métricas:**
- Ofertas clasificadas: **5,479** (96% del total)
- Ocupaciones ESCO catalogadas: **3,045**
- Skills ESCO en base de datos: **~13,890**

**¿Qué es ESCO?**
ESCO (European Skills, Competences, Qualifications and Occupations) es una clasificación multilingüe desarrollada por la Comisión Europea que describe:
- **Ocupaciones:** 3,000+ perfiles profesionales
- **Habilidades:** 13,000+ competencias técnicas y blandas
- **Calificaciones:** Niveles educativos y certificaciones

Cada ocupación tiene un código único. Ejemplo:
- **2511**: Analista de sistemas y software
- **5223**: Vendedor de tienda
- **2411**: Contador

**¿Por qué es útil?**
- Permite comparar Argentina con España, Francia, Alemania, etc.
- Facilita análisis de migraciones laborales internacionales
- Estándar reconocido por OIT, BID, Banco Mundial
- Integrable con sistemas europeos de empleo

---

### D. Dashboards de Visualización

El sistema cuenta con dos interfaces visuales para diferentes audiencias:

#### Dashboard Operativo (Plotly/Dash)
**Audiencia:** Equipo técnico de OEDE
**URL:** http://localhost:8052 (interno)
**Estado:** ✅ EN PRODUCCIÓN

**Funciones:**
- Monitoreo en tiempo real del scraping
- Métricas de calidad del procesamiento NLP
- Performance de keywords (cuáles funcionan mejor)
- Detección de errores y alertas del sistema
- Análisis de correlación entre variables
- Identificación de ofertas mal procesadas

**Tabs disponibles:**
1. Panorama General (KPIs, distribución temporal, top empresas)
2. Keywords Performance (productividad, cobertura)
3. Métricas de Sistema (tiempos de ejecución, rate limiting)
4. **Calidad de Parseo NLP** (análisis de completitud por campo)

#### Dashboard Público (Shiny)
**Audiencia:** Analistas, investigadores, decisores de política
**URL:** https://dos1tv-gerardo-breard.shinyapps.io/dashboard-esco-argentina/
**Estado:** ✅ EN PRODUCCIÓN
**Dataset:** 268 ofertas de muestra (100% validadas manualmente)

**6 Pestañas:**

1. **Panorama General**
   - Total de ofertas, ocupaciones, skills y empresas
   - Distribución por grandes grupos ocupacionales (gráfico de torta)
   - Top 10 ocupaciones más demandadas
   - Distribución geográfica por provincia
   - Top 10 empresas que más publican

2. **Perfil Demandado**
   - Requisitos educativos (secundario 35%, universitario 45%, etc.)
   - Experiencia requerida promedio por tipo de ocupación
   - Top 20 soft skills más demandadas (liderazgo, comunicación, etc.)
   - Top 20 skills técnicas más solicitadas (Excel, Python, etc.)

3. **Análisis de Skills ESCO**
   - Skills esenciales según clasificación europea
   - Vista extendida de competencias por categoría
   - Tabla de skills agrupadas por código ISCO

4. **Ocupaciones & Empresas**
   - Tabla interactiva: Empresa - Ocupación - Código ISCO - Provincia
   - Distribución de ocupaciones por nivel de detalle
   - Filtros múltiples

5. **Explorador de Ofertas**
   - Buscador de texto libre por título
   - Filtro por código de ocupación
   - Tabla con enlaces directos a ofertas originales (clickeables)
   - Descarga de datos filtrados en Excel

6. **Árbol ESCO** (novedad v2.2)
   - Visualización jerárquica interactiva de ocupaciones
   - 4 niveles navegables (expandir/colapsar con click)
   - Tooltips con cantidad de ofertas por categoría
   - Estadísticas por nivel de agregación

**Filtros Globales (aplicables a todas las pestañas):**
- Grupo ocupacional (ISCO Nivel 1)
- Provincia
- Empresa
- Fuente (Bumeran/ZonaJobs)

**Seguridad:**
- Sistema de autenticación con usuario y contraseña
- 4 perfiles: Admin, Analista, Gerardo (desarrollo), Invitado

---

## 3. INDICADORES DE DESEMPEÑO

### Cobertura del Scraping

| Indicador | Valor | Interpretación |
|-----------|-------|----------------|
| **Keywords Productivos** | 58.4% (1,340/1,148) | 6 de cada 10 términos de búsqueda generan resultados |
| **Ofertas nuevas por semana** | ~600 | Crecimiento sostenido de la base de datos |
| **Tiempo de ejecución** | 38 minutos | Proceso eficiente y escalable |
| **Portales integrados** | 5 (1 automatizado) | Bumeran cubre 85% del volumen |
| **Completitud de campos** | 85%+ promedio | Alta calidad de datos básicos (título, empresa, descripción) |

**Interpretación:**
El sistema captura una porción significativa del mercado laboral formal argentino publicado online. La tasa de productividad de keywords (58.4%) es sana y permite identificar 478 términos que no generan resultados para optimizar en futuras versiones.

---

### Calidad del Análisis NLP

Análisis sobre 8,472 ofertas procesadas con diferentes versiones del motor NLP:

| Campo | Ofertas con dato | Cobertura | Estado |
|-------|------------------|-----------|--------|
| **Soft Skills** | 5,343 | **63.1%** | ✅ Excelente |
| **Skills Técnicas** | 3,414 | 40.3% | ✅ Bueno |
| **Educación** | 3,273 | 38.6% | ⚠️ Aceptable |
| **Experiencia** | 2,474 | 29.2% | ⚠️ Por mejorar |
| **Jornada** | 2,132 | 25.2% | ⚠️ Bajo |
| **Idiomas** | 1,734 | 20.5% | ⚠️ Bajo |
| **Salario** | <500 | <6% | ❌ Crítico |
| **Certificaciones** | <200 | <3% | ❌ Crítico |

**Confidence Score promedio:** 0.26 (escala 0-1)

**Interpretación:**
El sistema identifica correctamente soft skills en 6 de cada 10 ofertas, pero tiene dificultades con información más específica como salarios (que rara vez se publican) y certificaciones. La mejora del NLP es la prioridad #1 del proyecto.

**Meta objetivo:** 85% de cobertura en todos los campos principales (experiencia, educación, skills técnicas, soft skills, jornada).

---

### Clasificación ESCO

| Indicador | Valor | Interpretación |
|-----------|-------|----------------|
| **Ofertas clasificadas** | 5,479 | 96% del total |
| **Ocupaciones ESCO únicas** | 3,045 | Gran diversidad de perfiles |
| **Skills ESCO catalogadas** | ~13,890 | Base de referencia completa |
| **Precisión del matching** | ~80% | Validación manual en muestra |

**Interpretación:**
El sistema clasifica exitosamente casi todas las ofertas en ocupaciones estándar internacionales, facilitando comparaciones con otros países y análisis de tendencias globales.

---

## 4. CASOS DE USO - FASE ACTUAL

### Para Analistas de STEYSS y OEDE

**Escenario 1: Diseñar un programa de capacitación focalizado**

**Pregunta de política:**
¿En qué habilidades deberíamos capacitar a jóvenes sin experiencia para mejorar su empleabilidad en el sector comercial?

**Uso del MOL:**
1. Filtrar ofertas por ocupación: "Vendedor" (ISCO 5223)
2. Analizar soft skills más demandadas
3. Revisar skills técnicas requeridas
4. Identificar nivel educativo exigido
5. Verificar requisitos de experiencia

**Resultado:**
Descubre que 80% requiere "atención al cliente" y "persuasión", 60% pide "experiencia con CRM" o "manejo de Excel", y 45% acepta nivel secundario completo. Diseña un curso de 3 meses en "Vendedor Profesional" con estos contenidos.

**Impacto:**
Capacitaciones pertinentes → Mayor empleabilidad → Reducción del desempleo juvenil

---

**Escenario 2: Detectar ocupaciones emergentes**

**Pregunta de política:**
¿Qué nuevos perfiles están demandando las empresas que no existían hace 2 años?

**Uso del MOL:**
1. Comparar distribución de ocupaciones año a año
2. Identificar ocupaciones con crecimiento >50%
3. Analizar skills asociadas a esos perfiles
4. Revisar salarios y beneficios ofrecidos

**Resultado:**
Detecta crecimiento explosivo de "Especialista en Marketing Digital" (+120%) y "Analista de Datos" (+80%). Identifica skills críticas: Python, SQL, Google Analytics, Power BI.

**Impacto:**
Alerta temprana para ajustar oferta formativa → Reducir brechas de skills → Evitar "apagones" de talento

---

### Para Instituciones Educativas

**Escenario 3: Validar pertinencia de una carrera**

**Pregunta institucional:**
¿La tecnicatura en "Administración de Empresas" que ofrecemos prepara a nuestros egresados para lo que el mercado demanda?

**Uso del MOL:**
1. Filtrar ofertas para "Asistente Administrativo" y "Auxiliar Contable"
2. Extraer skills técnicas requeridas
3. Comparar con programa de estudios actual
4. Identificar gaps (skills demandadas no cubiertas en currícula)

**Resultado:**
Descubre que 70% de ofertas piden "dominio de sistemas de gestión (ERP)", pero su programa solo enseña contabilidad manual. Incorpora módulo de SAP/Odoo al plan de estudios.

**Impacto:**
Egresados más empleables → Mayor matrícula → Mejor reputación institucional

---

**Escenario 4: Orientación vocacional basada en datos**

**Pregunta institucional:**
¿Qué carreras deberíamos recomendar a estudiantes de secundario que viven en Córdoba y les interesan las ciencias?

**Uso del MOL:**
1. Filtrar ofertas por provincia: Córdoba
2. Analizar ocupaciones STEM más demandadas
3. Revisar salarios promedio por carrera
4. Verificar nivel de saturación (oferta vs demanda)

**Resultado:**
Identifica alta demanda de Ingenieros en Sistemas (120 ofertas/mes) y Técnicos Electromecánicos (80 ofertas/mes), ambos con salarios 40% superiores al promedio provincial.

**Impacto:**
Orientación basada en evidencia → Decisiones de carrera más informadas → Reducción de deserción universitaria

---

### Para Investigadores

**Escenario 5: Estudio sobre brechas de género**

**Pregunta de investigación:**
¿Existen diferencias en los requisitos de experiencia y educación para ocupaciones tradicionalmente masculinas vs femeninas?

**Uso del MOL:**
1. Clasificar ocupaciones por segregación de género (datos de EPH)
2. Comparar años de experiencia requeridos
3. Comparar nivel educativo exigido
4. Analizar lenguaje inclusivo en descripciones

**Resultado:**
Paper académico en revista indexada sobre "Sesgos implícitos en ofertas laborales argentinas" con evidencia cuantitativa del MOL.

**Impacto:**
Visibilización de desigualdades → Insumo para políticas de equidad de género → Publicación internacional

---

## 5. CASOS DE USO - FASE FUTURA

### Para Buscadores de Empleo

**Escenario 6: Primer empleo con orientación personalizada**

**Protagonista:** Lucía, 22 años, egresada de Licenciatura en Administración, vive en Rosario, sin experiencia laboral.

**Interacción con MOL:**

1. **Registro y carga de perfil**
   - Completa formulario: edad, ubicación, carrera, promedio, idiomas
   - Adjunta CV en PDF
   - Indica preferencias: full-time, presencial o híbrido, disponibilidad inmediata

2. **Análisis automático**
   - El sistema lee su CV y extrae skills
   - Calcula su "perfil competitivo" vs otros egresados
   - Identifica 23 ofertas compatibles en Rosario (85%+ match)

3. **Recibe notificación en celular**
   - "Lucía, hay 3 ofertas nuevas 90% compatibles con tu perfil"
   - "Oferta destacada: Asistente Administrativo en [Empresa X] - $450K - Híbrido"

4. **Análisis de brecha**
   - "Tu perfil calza 88% con esta oferta"
   - "Te falta: Excel avanzado (solicitado en 75% de ofertas similares)"
   - "Recomendación: Curso gratuito de Excel en [plataforma] - 20 horas"

5. **Orientación geográfica**
   - "En Rosario hay 23 ofertas para tu perfil"
   - "En CABA hay 87 ofertas similares (+278%)"
   - "Considerá ampliar búsqueda a remoto: 45 ofertas más"

6. **Postulación simplificada**
   - Un click para postularse con perfil completo
   - Tracking de estado (postulada, vista por empresa, entrevista agendada)

**Resultado:**
Lucía completa el curso de Excel (20 horas), actualiza su perfil, y recibe entrevista para 2 de las ofertas recomendadas. Consigue su primer empleo en 3 semanas.

**Impacto individual:** Reducción de tiempo de búsqueda de 6 meses → 3 semanas
**Impacto social:** Acceso equitativo a oportunidades, especialmente en provincias con menor desarrollo

---

**Escenario 7: Reconversión laboral informada**

**Protagonista:** Carlos, 38 años, vendedor en comercio minorista hace 12 años, secundario completo, vive en Mendoza. El local donde trabaja cierra.

**Interacción con MOL:**

1. **Evaluación de opciones**
   - Carga su perfil con 12 años de experiencia en ventas
   - El sistema identifica sus "skills transferibles": atención al cliente, negociación, persuasión

2. **Análisis de demanda**
   - "Hay 45 ofertas en Mendoza para vendedores como vos"
   - "Ocupaciones relacionadas con alta demanda:"
     - Telemarketing (+60 ofertas, requiere mismo skillset)
     - Ejecutivo de cuentas B2B (+35 ofertas, salario +40%)
     - Asesor comercial inmobiliario (+20 ofertas, alto potencial de comisiones)

3. **Análisis de brecha**
   - Para pasar a "Ejecutivo de cuentas B2B" necesita:
     - Curso de CRM (Salesforce o Zoho) - 30 horas
     - Inglés intermedio - 6 meses
   - "Con estas 2 capacitaciones, accedés a 35 ofertas más con salario 40% superior"

4. **Proyección de inversión**
   - Costo de capacitaciones: $80,000 (cursos online)
   - Incremento salarial esperado: $200,000/mes
   - Retorno de inversión: 1 mes

5. **Notificaciones personalizadas**
   - "Nueva oferta: Ejecutivo Comercial en [Empresa Y] - $550K - Se valora experiencia en retail"

**Resultado:**
Carlos decide invertir en capacitación, completa curso de CRM y mejora su inglés. A los 4 meses consigue puesto como Ejecutivo de Cuentas con 35% de aumento salarial.

**Impacto:** Movilidad social ascendente basada en datos, no en contactos

---

### Para Empresas

**Escenario 8: Optimizar oferta salarial para ser competitivo**

**Protagonista:** StartUp tecnológica en CABA busca contratar "Desarrollador Python Senior" y no recibe postulaciones.

**Interacción con MOL:**

1. **Benchmarking salarial**
   - Portal empresarial: "Analizar mi oferta"
   - Sube descripción del puesto
   - El sistema compara con 85 ofertas similares en CABA

2. **Análisis de competitividad**
   - "Tu oferta: $600K/mes"
   - "Promedio del mercado: $850K/mes"
   - "**Tu oferta está 29% por debajo del mercado**"
   - "Percentil 10: $700K | Percentil 50: $850K | Percentil 90: $1.2M"

3. **Análisis de beneficios**
   - "80% de ofertas similares incluyen:"
     - Home office 100% (tu oferta: solo 2 días/semana)
     - Presupuesto de capacitaciones (tu oferta: no menciona)
     - Horario flexible (tu oferta: no menciona)

4. **Simulación de ajuste**
   - "Si aumentás a $750K y agregás home office full:"
     - Pool estimado: 120 candidatos → 340 candidatos (+183%)
     - Probabilidad de cubrir vacante: 40% → 85%
     - Tiempo de vacancia estimado: 90 días → 30 días

5. **Alerta de competencia**
   - "3 empresas publicaron ofertas similares esta semana:"
     - [Competidor A]: $900K + stock options
     - [Competidor B]: $800K + 100% remoto
     - [Competidor C]: $850K + capacitaciones ilimitadas

**Resultado:**
La startup ajusta salario a $800K, ofrece home office 100% y capacitaciones. Recibe 15 postulaciones en 2 semanas, contrata en 25 días.

**Impacto:** Reducción de time-to-hire de 90 → 25 días, ahorro de $500K en productividad perdida

---

**Escenario 9: Decidir ubicación de oficina regional basado en disponibilidad de talento**

**Protagonista:** Empresa nacional de software evalúa abrir oficina en interior del país (Córdoba vs Rosario vs Mendoza).

**Interacción con MOL:**

1. **Análisis de disponibilidad de talento**
   - Portal empresarial: "Estudio de Mercado Regional"
   - Filtro: "Desarrolladores de Software" en 3 provincias

2. **Reporte comparativo**

| Métrica | Córdoba | Rosario | Mendoza |
|---------|---------|---------|---------|
| Ofertas activas (competencia) | 120/mes | 65/mes | 35/mes |
| Postulaciones promedio por oferta | 8 | 12 | 15 |
| Salario promedio mercado | $700K | $650K | $600K |
| Disponibilidad estimada de talento | Alta | Media | Media-Baja |
| Costo de vida (índice) | 95 | 90 | 85 |
| Universidades con carreras IT | 4 | 2 | 2 |
| Egresados IT por año (estimado) | 800 | 400 | 250 |

3. **Análisis de competencia**
   - Córdoba: 15 empresas IT grandes compitiendo por talento
   - Rosario: 8 empresas IT medianas
   - Mendoza: 3 empresas IT (menor competencia)

4. **Proyección de costos**
   - Córdoba: Salarios +15% más altos, pero mayor pool de candidatos
   - Rosario: Balance óptimo costo/disponibilidad
   - Mendoza: Salarios más bajos, pero dificultad para cubrir 10+ posiciones

5. **Recomendación del sistema**
   - "Para equipo de 5-8 personas: **Mendoza** (menor competencia, costos bajos)"
   - "Para equipo de 15+ personas: **Rosario** (balance óptimo, suficiente talento)"
   - "Para equipo de 30+ personas: **Córdoba** (único lugar con pool suficiente)"

**Resultado:**
La empresa decide abrir en Rosario (plan inicial: 12 personas, expansión a 25 en 2 años). Ahorra 6 meses de research y $2M en consultoría.

**Impacto:** Decisiones estratégicas basadas en datos → Inversión eficiente → Crecimiento sostenible en regiones

---

**Escenario 10: Sourcing inteligente de candidatos pasivos**

**Protagonista:** Empresa busca "Contador Senior con experiencia en auditoría Big Four" en CABA - perfil escaso.

**Interacción con MOL:**

1. **Búsqueda en base de candidatos**
   - Portal empresarial: "Buscar Candidatos"
   - Filtros: Ocupación (Contador), Experiencia (5+ años), Skills (auditoría, IFRS, Big Four)

2. **Resultados del matching**
   - 8 candidatos con 85%+ de compatibilidad
   - Todos actualmente empleados (candidatos pasivos)
   - Disponibilidad: "Evaluando ofertas" o "No busco activamente, pero abierto a propuestas"

3. **Perfiles anonimizados**
   - Candidato #3:
     - 7 años de experiencia en auditoría
     - Ex-PwC
     - Skills: IFRS, US GAAP, SOX, Excel avanzado
     - Ubicación: CABA
     - Pretensión salarial: $1.2M-1.5M
     - **Compatibilidad: 92%**

4. **Invitación directa**
   - Sistema envía mensaje: "Una empresa líder está interesada en tu perfil para posición de Contador Senior. ¿Te interesa conocer más?"
   - Candidato acepta → empresa ve perfil completo y contacto

5. **Ventaja competitiva**
   - Alcanza candidatos que no están buscando activamente
   - Reduce dependencia de consultoras (ahorro 20-30% del salario anual)
   - Time-to-hire: 45 días vs 90 días con búsqueda tradicional

**Resultado:**
Empresa contacta a Candidato #3, realiza 2 entrevistas, hace oferta de $1.4M. Candidato acepta. Ahorro en fee de consultora: $280K.

**Impacto:** Acceso a talento pasivo (60% del mercado) + Reducción de costos de reclutamiento

---

## 6. POTENCIALES USUARIOS Y APLICACIONES

### Usuarios Institucionales (Fase Actual)

#### Secretaría de Trabajo, Empleo y Seguridad Social (STEYSS)
**Áreas usuarias:**
- Subsecretaría de Empleo
- Subsecretaría de Formación Profesional
- Dirección de Estudios y Análisis Laboral

**Aplicaciones:**
- Diseño de programas de empleo (Jóvenes con Más y Mejor Trabajo, etc.)
- Priorización de sectores para capacitación
- Monitoreo de cumplimiento de cupo laboral trans/discapacidad
- Reportes periódicos al Congreso y organismos internacionales
- Ajuste de políticas activas de empleo

---

#### Observatorio de Empleo y Dinámica Empresarial (OEDE)
**Aplicaciones:**
- Boletines mensuales de coyuntura laboral
- Series estadísticas para análisis longitudinal
- Cruce con Encuesta Permanente de Hogares (EPH)
- Informes sectoriales (construcción, IT, agro, servicios)
- Identificación de ocupaciones críticas

---

#### Ministerios de Trabajo Provinciales
**Aplicaciones:**
- Observatorios laborales locales
- Programas de empleo focalizados por provincia
- Articulación con empresas locales
- Diseño de centros de formación profesional
- Reportes de gestión

---

#### Universidades e Institutos de Formación
**Aplicaciones:**
- Investigación académica sobre mercado laboral
- Validación de pertinencia curricular
- Diseño de nuevas carreras y diplomaturas
- Seguimiento de egresados (empleabilidad)
- Vinculación con sector productivo
- Orientación vocacional a ingresantes

---

#### Organismos Internacionales
**Usuarios:** OIT (Organización Internacional del Trabajo), BID (Banco Interamericano de Desarrollo), CEPAL, Banco Mundial

**Aplicaciones:**
- Benchmarking de Argentina con otros países de la región
- Estudios comparativos sobre futuro del trabajo
- Análisis de impacto de automatización
- Monitoreo de trabajo decente (Objetivo de Desarrollo Sostenible 8)
- Investigación sobre brechas de género y juventud

---

### Usuarios Finales (Fase Futura)

#### Buscadores de Empleo Activos
**Segmento:** 500,000+ potenciales usuarios

**Perfiles:**
- Desempleados buscando reinserción (20%)
- Empleados buscando mejor oferta (50%)
- Personas en empleo informal buscando formalización (30%)

**Edades:** 18-55 años, con mayor concentración en 22-35 años

**Aplicaciones:**
- Recibir notificaciones de ofertas compatibles
- Evaluar competitividad de su perfil
- Identificar skills faltantes para aspirar a mejores puestos
- Descubrir oportunidades en otras provincias
- Postularse a ofertas con un click

**Impacto esperado:**
- Reducción de tiempo de búsqueda: 6 meses → 1-2 meses
- Aumento de postulaciones por usuario: 5 → 20
- Mejora de match (evitar postulaciones irrelevantes)

---

#### Estudiantes Secundarios y Universitarios
**Segmento:** 100,000+ usuarios potenciales

**Aplicaciones:**
- Orientación vocacional basada en datos de demanda real
- Comparar carreras por empleabilidad y salario esperado
- Identificar skills complementarias para mejorar perfil
- Planificar pasantías según ocupaciones en crecimiento

**Impacto esperado:**
- Reducción de deserción universitaria (mejor elección de carrera)
- Mayor claridad sobre inserción laboral futura
- Planificación de capacitaciones complementarias

---

#### Trabajadores en Reconversión Laboral
**Segmento:** 50,000+ usuarios potenciales

**Perfiles:**
- Personas en sectores en declive (ej: comercio minorista, industria tradicional)
- Víctimas de despidos masivos
- Personas de 40+ años buscando reinvención

**Aplicaciones:**
- Identificar ocupaciones relacionadas con skills transferibles
- Evaluar costo/beneficio de capacitaciones
- Descubrir nichos laborales no conocidos
- Recibir alertas de programas de reconversión del Estado

**Impacto esperado:**
- Movilidad horizontal facilitada
- Reducción de desempleo de larga duración
- Aprovechamiento de experiencia previa

---

#### Migrantes Internos
**Segmento:** 20,000+ usuarios potenciales

**Aplicaciones:**
- Comparar oportunidades laborales entre provincias
- Evaluar costo de vida vs salarios por región
- Identificar ciudades con alta demanda de su perfil
- Planificar migraciones laborales informadas

**Impacto esperado:**
- Migraciones más exitosas (menor retorno por falta de empleo)
- Desarrollo regional más equilibrado
- Reducción de concentración en CABA/GBA

---

### Usuarios Empresariales (Fase Futura)

#### Áreas de Recursos Humanos
**Segmento:** 10,000+ empresas

**Tamaño:**
- Grandes empresas (500+ empleados): 2,000 empresas
- Medianas empresas (50-500 empleados): 5,000 empresas
- Pequeñas empresas (10-50 empleados): 3,000 empresas

**Aplicaciones:**
- Benchmarking salarial para retener talento
- Validación de descripciones de puesto
- Acceso a base de candidatos pre-calificados
- Análisis de competencia por talento
- Reportes de tiempo de vacancia y efectividad de ofertas

**Impacto esperado:**
- Reducción de time-to-hire: 60 días → 30 días
- Aumento de tasa de aceptación de ofertas
- Reducción de rotación por salarios no competitivos

---

#### Gerencias y Direcciones Comerciales
**Aplicaciones:**
- Evaluar factibilidad de expansión regional (disponibilidad de talento)
- Decisiones sobre apertura de oficinas
- Análisis de costos laborales por provincia
- Planificación de estructura de equipos

**Impacto esperado:**
- Inversiones más informadas
- Reducción de fracasos en expansiones regionales
- Optimización de estructura de costos

---

#### Consultoras de RRHH
**Segmento:** 500+ consultoras

**Aplicaciones:**
- Sourcing de candidatos para clientes
- Estudios de mercado salarial para venta a clientes
- Identificación de nichos de talento escaso
- Análisis de tendencias para servicios de consultoría

**Impacto esperado:**
- Mayor eficiencia en búsquedas (reducción de tiempos)
- Nuevas líneas de servicio (reportes de mercado)
- Valor agregado para clientes corporativos

---

#### Startups
**Segmento:** 2,000+ startups tecnológicas

**Aplicaciones:**
- Entender mercado de talento antes de primera contratación
- Benchmark para ofrecer paquete competitivo con recursos limitados
- Identificar ciudades alternativas a CABA (menores costos)
- Validar si existe suficiente talento para escalar equipo

**Impacto esperado:**
- Mejores decisiones de compensación (equity vs salario)
- Expansión sostenible de equipos
- Competitividad vs empresas grandes

---

#### CFOs y Controllers
**Aplicaciones:**
- Proyección de costos laborales para presupuesto anual
- Benchmarking de estructura salarial interna vs mercado
- Análisis de eficiencia en compensaciones
- Evaluación de impacto de ajustes salariales en rotación

**Impacto esperado:**
- Presupuestos más realistas
- Optimización de inversión en talento
- Reducción de costos de rotación

---

### Usuarios Complementarios

#### Red Nacional de Oficinas de Empleo
**Aplicaciones:**
- Integración de ofertas del MOL en portales municipales
- Capacitación de buscadores en uso de la plataforma
- Intermediación asistida para poblaciones vulnerables
- Seguimiento de resultados de programas de empleo

---

#### Sindicatos y Cámaras Empresariales
**Aplicaciones:**
- Monitoreo de condiciones laborales por sector
- Negociaciones de convenios colectivos basadas en datos
- Identificación de sectores con precarización
- Estudios sobre tercerización y flexibilización

---

#### ONGs de Empleabilidad
**Ejemplos:** Fundación Forge, Cimientos, Potenciar

**Aplicaciones:**
- Orientación de beneficiarios hacia ocupaciones demandadas
- Diseño de programas de capacitación pertinentes
- Medición de impacto (inserción laboral post-programa)
- Articulación con empresas demandantes

---

## 7. BRECHAS ACTUALES Y PRÓXIMOS PASOS

### Gap Crítico Identificado

Durante el desarrollo del sistema se identificó una brecha fundamental:

> **"Todavía no tenemos bien trabajado el tema de las habilidades, carreras, formación, demanda laboral para determinados perfiles en determinadas regiones del país"**

Esta limitación afecta:
- **Buscadores:** No pueden saber qué habilidades concretas les faltan
- **Instituciones educativas:** No pueden ajustar currículas con precisión
- **Empresas:** No pueden entender brechas de talento locales
- **Políticas públicas:** Dificulta focalización territorial de programas

---

### Hitos de Desarrollo

El proyecto se estructura en 8 hitos secuenciales, cada uno construyendo sobre el anterior:

---

### HITO 1: Mejorar Extracción de Información

**Objetivo:** Aumentar drásticamente la precisión del análisis inteligente

**Actividades:**
1. **Mejorar extracción de skills**
   - Expandir diccionario de skills técnicas de 215 → 500
   - Incluir variaciones regionales (ej: "carnet de conducir" = "registro de conducir" = "licencia de manejo")
   - Detectar niveles de competencia (básico, intermedio, avanzado, experto)
   - Meta: 40% → 85% de cobertura

2. **Identificar carreras específicas**
   - Detectar menciones explícitas (ej: "Ing. Civil", "Lic. en RRHH", "Técnico Electromecánico")
   - Mapear a clasificador de carreras (CNO educativo)
   - Diferenciar excluyente vs deseable
   - Meta: 38% → 85% de cobertura

3. **Extraer certificaciones**
   - Expandir diccionario de certificaciones de 25 → 100
   - Incluir certificaciones argentinas (ej: matrícula profesional, registro de conductor)
   - Detectar si es requisito excluyente
   - Meta: 3% → 40% de cobertura

4. **Detectar nivel de seniority**
   - Identificar menciones de Junior, Semi-Senior, Senior
   - Inferir de años de experiencia (0-2 años = Junior, 2-5 = SSr, 5+ = Sr)
   - Meta: 80% de ofertas con seniority asignado

5. **Capturar formación en curso**
   - Diferenciar "título completo" vs "en curso" vs "incompleto"
   - Detectar frases como "estudiantes avanzados", "últimos años de carrera"
   - Meta: 90% de cobertura en ofertas que mencionan educación

**Entregables:**
- Base de datos con 18 variables al 85% de completitud
- Reporte de calidad comparando antes/después
- Dashboard actualizado con nuevas métricas

**Indicador de éxito:** Quality Score promedio aumenta de 7.89 → 15.3 (de 18 campos posibles)

---

### HITO 2: Análisis Regional y Sectorial

**Objetivo:** Generar inteligencia de mercado geolocalizada y por industria

**Actividades:**
1. **Mapa de demanda por perfil y provincia**
   - Agrupar ofertas por ocupación y provincia
   - Calcular oferta/demanda por región
   - Identificar provincias con escasez vs abundancia de talento
   - Detectar migraciones laborales internas sugeridas

2. **Brechas de skills por región**
   - Comparar skills demandadas por provincia
   - Identificar skills críticas por región (ej: inglés en CABA, maquinaria agrícola en provincias pampeanas)
   - Sugerir capacitaciones prioritarias por provincia

3. **Ranking de ocupaciones por zona**
   - Top 20 ocupaciones más demandadas por provincia
   - Evolución temporal (crecimiento/decrecimiento)
   - Comparación con estructura ocupacional de EPH

4. **Benchmarking salarial regional**
   - Salarios promedio por ocupación y provincia
   - Ajuste por costo de vida (índice provincial)
   - Identificar provincias con mejor relación salario/costo de vida

5. **Análisis sectorial**
   - Clasificar ofertas por sector económico (construcción, IT, comercio, industria, servicios)
   - Cruzar con datos de VAB provincial
   - Detectar sectores en expansión/contracción por región

**Entregables:**
- Dashboard con mapa interactivo de Argentina
- Reporte mensual "Demanda Laboral por Provincia"
- API de consulta para sistemas provinciales
- Dataset público para investigadores

**Indicador de éxito:** 5 provincias utilizando datos del MOL para diseñar programas locales

---

### HITO 3: Motor de Matching

**Objetivo:** Emparejar candidatos con ofertas automáticamente

**Actividades:**
1. **Diseño del algoritmo de scoring**
   - Definir pesos para cada variable (experiencia: 25%, educación: 20%, skills: 35%, ubicación: 10%, otros: 10%)
   - Implementar lógica de compatibilidad:
     - Experiencia: +10 puntos si cumple mínimo, -5 puntos por cada año faltante
     - Educación: +15 puntos si cumple nivel, +10 si es equivalente (terciario ≈ universitario incompleto)
     - Skills: +2 puntos por cada skill en común, +5 si domina skill crítica
     - Ubicación: +10 si misma provincia, +5 si disposición a migrar
   - Score final: 0-100%

2. **Sistema de recomendaciones**
   - Para candidatos: "Top 10 ofertas para vos"
   - Para empresas: "Top 20 candidatos para esta oferta"
   - Actualización diaria de recomendaciones

3. **Detección de brechas de habilidades**
   - Comparar perfil del candidato con requisitos de oferta
   - Listar skills faltantes ordenadas por criticidad
   - Sugerir capacitaciones específicas (con links a cursos)

4. **Sugerencias de mejora de perfil**
   - "Agregá [skill X] a tu perfil y accedés a 45 ofertas más"
   - "Con [certificación Y] mejorás tu compatibilidad promedio 15%"
   - "Candidatos similares con inglés tienen 3x más entrevistas"

5. **Ranking bidireccional**
   - Candidato ve: "Estás en top 10 de 250 postulantes para esta oferta"
   - Empresa ve: "Este candidato está en percentil 90 de compatibilidad"

**Entregables:**
- API de matching con endpoints REST
- Documentación técnica del algoritmo
- Validación con muestra de 500 matches manuales
- Sistema de feedback para mejorar algoritmo (¿fue útil esta recomendación?)

**Indicador de éxito:** Precisión del matching >80% (validación manual en muestra de 200 casos)

---

### HITO 4: Plataforma Web para Buscadores

**Objetivo:** Lanzar MVP accesible para usuarios finales

**Actividades:**
1. **Registro y autenticación**
   - Registro con email/contraseña o Google/LinkedIn
   - Validación de email
   - Recuperación de contraseña

2. **Carga de perfil**
   - Formulario paso a paso:
     - Datos básicos (nombre, edad, ubicación, teléfono)
     - Educación (nivel, carrera, estado, institución)
     - Experiencia (ocupaciones previas, años, áreas)
     - Habilidades (selección de lista + agregado libre)
     - Idiomas y niveles
     - Certificaciones
     - Preferencias (tipo jornada, modalidad, rango salarial, disposición a migrar)
   - Opción de cargar CV (PDF/Word) para extracción automática
   - Foto de perfil (opcional)

3. **Dashboard personal**
   - "Mis ofertas recomendadas" (top 20, ordenadas por compatibilidad)
   - "Ofertas nuevas hoy" (badge con contador)
   - "Mis postulaciones" (estado: enviada, vista, entrevista, rechazada)
   - "Mi perfil competitivo" (gráfico radar comparando con promedio)

4. **Sistema de notificaciones**
   - Email diario con ofertas nuevas (configurable: diario, cada 3 días, semanal)
   - SMS para ofertas urgentes (>95% compatibilidad, vencen pronto)
   - Notificaciones en sitio web (campana con contador)

5. **Análisis de brechas**
   - Sección "Cómo mejorar tu perfil"
   - Lista de skills faltantes con impacto estimado
   - Links a cursos gratuitos (Argentina Programa, Coursera, edX)

6. **Postulación simplificada**
   - Un click para postularse (si perfil completo)
   - Carta de presentación opcional
   - Tracking de estado (visto por empresa, entrevista agendada)

7. **Orientación geográfica**
   - Mapa de Argentina con "calor" de oportunidades
   - Comparador "Tu provincia vs otras"
   - "Ofertas remotas" (sin restricción geográfica)

**Stack tecnológico sugerido:**
- Frontend: React + Tailwind CSS (responsive)
- Backend: Python (FastAPI) + PostgreSQL
- Autenticación: Auth0 o similar
- Hosting: AWS, Google Cloud o Render

**Entregables:**
- Sitio web responsive (mobile-first)
- 100 usuarios beta testers (OEDE, universidades)
- Métricas de uso (Google Analytics)
- Documentación de usuario (tutoriales, FAQs)

**Indicador de éxito:** 1,000 usuarios registrados en primer mes, 60% completa perfil completo, 40% postula al menos 1 vez

---

### HITO 5: Plataforma Web para Empresas

**Objetivo:** Ofrecer servicios de valor a empleadores

**Actividades:**
1. **Portal de benchmarking salarial**
   - Formulario: Ocupación, provincia, seniority
   - Reporte instantáneo:
     - Salario promedio del mercado
     - Percentil 10, 50, 90
     - Distribución de beneficios (% que ofrece home office, capacitaciones, etc.)
   - Comparación de oferta propia vs mercado

2. **Análisis de competencia por talento**
   - Listado de empresas publicando ofertas similares
   - Frecuencia de publicación
   - Salarios comparados (si públicos)
   - Beneficios ofrecidos

3. **Validador de descripciones**
   - La empresa pega su texto de oferta
   - Sistema analiza:
     - Cantidad de requisitos (¿son demasiados?)
     - Skills críticas (¿falta mencionar alguna?)
     - Beneficios (¿están explícitos?)
     - Lenguaje inclusivo (¿hay sesgos de género?)
   - Score de "atractivo" (0-100)
   - Sugerencias de mejora

4. **Acceso a base de candidatos (Fase inicial)**
   - Búsqueda por ocupación, skills, provincia
   - Perfiles anonimizados (sin nombre ni contacto)
   - Invitación a postularse (sistema envía mensaje)
   - Candidato decide si acepta compartir datos

5. **Reportes de mercado personalizados**
   - "Reporte Mensual: Desarrolladores Python en CABA"
   - "Tendencias: Demanda de Contadores en Córdoba (último trimestre)"
   - Descarga en PDF

**Modelo de acceso:**
- **Freemium:** Benchmarking básico gratis (1 consulta/mes)
- **Plan Empresa:** USD 200/mes - 20 consultas, acceso a candidatos, reportes
- **Plan Corporativo:** USD 800/mes - ilimitado, API access, soporte prioritario

**Entregables:**
- Portal empresarial con autenticación
- Sistema de facturación y suscripciones
- 50 empresas beta testers
- Casos de éxito documentados

**Indicador de éxito:** 200 empresas registradas, 30 suscripciones pagas en primer trimestre

---

### HITO 6: App Móvil Nativa

**Objetivo:** Maximizar alcance y engagement con notificaciones push

**Actividades:**
1. **Desarrollo nativo**
   - Android (Kotlin)
   - iOS (Swift)
   - Sincronización con backend web

2. **Funcionalidades clave**
   - Login con biometría (huella, Face ID)
   - Notificaciones push en tiempo real
     - "Nueva oferta 92% compatible"
     - "Empresa X vio tu perfil"
     - "Entrevista confirmada para mañana 10am"
   - Geolocalización de ofertas cercanas (mapa)
   - Postulación con un click
   - Chat con reclutadores (mensajería integrada)
   - Modo offline (ver ofertas guardadas sin internet)

3. **Gamificación**
   - "Completitud de perfil: 75%" (barra de progreso)
   - Logros: "Primera postulación", "Perfil 100% completo", "10 empresas vieron tu perfil"
   - Ranking (opcional, opt-in): "Sos top 5% en tu ocupación"

4. **Accesibilidad**
   - Modo alto contraste
   - Tamaño de fuente ajustable
   - Compatibilidad con TalkBack (Android) y VoiceOver (iOS)

**Entregables:**
- Apps publicadas en Google Play y App Store
- 10,000 descargas en primer mes (campaña con STEYSS)
- Rating >4.0 estrellas

**Indicador de éxito:** 50% de usuarios activos en app móvil vs web, 3x más engagement (abren notificaciones)

---

### HITO 7: Integración con Ecosistema

**Objetivo:** Interoperar con otros sistemas del Estado y privados

**Actividades:**
1. **Red de Oficinas de Empleo**
   - API para que oficinas municipales consuman ofertas del MOL
   - Registro de candidatos en oficinas sincroniza con MOL
   - Dashboard para orientadores laborales (asistir candidatos vulnerables)
   - Seguimiento de resultados (cuántos consiguieron empleo)

2. **Sistema de Certificaciones (INET/ANSES)**
   - Validación automática de certificaciones oficiales
   - Badge verificado en perfil ("Certificación INET verificada")
   - Integración con Carné de Discapacidad (identificar candidatos con discapacidad)

3. **Plataformas de Capacitación**
   - Argentina Programa, Codo a Codo, Potenciar Trabajo, etc.
   - Recomendación de cursos directamente en MOL
   - Tracking de finalización (el candidato completa curso → se actualiza su perfil)
   - Integración con Plataforma Guitalá

4. **CNO (Clasificador Nacional de Ocupaciones)**
   - Mapeo de ocupaciones ESCO → CNO
   - Permite usar estándar argentino en paralelo a ESCO
   - Integración con Declaración Jurada de Vacantes (obligación de empleadores)

5. **Portales de Empleo Privados**
   - APIs bidireccionales con Bumeran, ZonaJobs, Computrabajo
   - Candidato postula en MOL → postula automáticamente en portal origen
   - Empresa publica en portal privado → oferta se replica en MOL (con permiso)

**Entregables:**
- 5 integraciones funcionales
- Documentación de APIs públicas
- Acuerdos de intercambio de datos (firmados)

**Indicador de éxito:** 30% de postulaciones provienen de integraciones (no directas en MOL)

---

### HITO 8: Ecosistema Integral - Portal Nacional de Empleo

**Objetivo:** Consolidar como plataforma nacional de referencia

**Actividades:**
1. **Escalamiento de infraestructura**
   - Soportar 100,000 usuarios concurrentes
   - 1 millón de usuarios registrados
   - 50,000 ofertas activas simultáneas

2. **Interoperabilidad provincial**
   - 24 provincias con acceso a datos del MOL
   - Dashboards provinciales personalizados
   - Exportación de datos para observatorios locales

3. **Benchmarking regional**
   - Integración con portales de Chile, Uruguay, Brasil (piloto)
   - Comparación de mercados laborales Mercosur
   - Detectar migraciones laborales internacionales

4. **Observatorio de Skills del Futuro**
   - IA predictiva para detectar skills emergentes
   - Alertas tempranas: "Demanda de [skill X] creció 200% en 6 meses"
   - Reportes de tendencias globales (cruce con LinkedIn, OECD)

5. **Sistema de Micro-Credenciales**
   - Badges digitales por skills validadas
   - Empresas emiten credenciales a empleados (ej: "Experto en Salesforce certificado por [Empresa]")
   - Candidatos acumulan badges verificables blockchain

6. **Impacto medible**
   - Dashboard de impacto social:
     - Tiempo promedio de búsqueda de empleo (reducción)
     - Tasa de match exitoso (postulación → contratación)
     - Empleabilidad por programa de capacitación
   - Reportes de ROI para inversión pública en formación

**Entregables:**
- Plataforma con 100,000+ usuarios activos mensuales
- 5,000+ empresas usuarias
- 10,000+ contrataciones exitosas por mes
- Reconocimiento como Portal Nacional de Empleo (decreto/resolución)

**Indicador de éxito:** MOL es referencia #1 para búsqueda de empleo en Argentina (supera a portales privados en uso)

---

## 8. BENEFICIOS Y VALOR AGREGADO

### Para Políticas Públicas

**1. Diseño basado en evidencia, no en intuición**
- Reemplaza encuestas caras y lentas por datos en tiempo real
- Identifica necesidades de capacitación con precisión
- Permite focalizar recursos escasos donde generan más impacto

**Ejemplo concreto:**
En lugar de diseñar un programa genérico de "capacitación en informática", el MOL revela que en Rosario hay déficit específico de "Técnicos en Soporte IT con certificación CompTIA A+", permitiendo crear un curso focalizado con 85% de empleabilidad post-egreso.

---

**2. Detección temprana de brechas de formación**
- Alertas cuando crece demanda de ocupación no cubierta por oferta educativa
- Anticipa necesidades de formación 1-2 años antes (vs reacción tardía)
- Evita "apagones de talento" en sectores estratégicos

**Ejemplo concreto:**
El MOL detecta en 2024 crecimiento explosivo de "Analistas de Ciberseguridad" (+150% en 12 meses) pero solo 3 universidades ofrecen la carrera. Alerta permite al INET crear tecnicatura en tiempo récord, evitando cuello de botella.

---

**3. Focalización efectiva de programas de empleo**
- Identificar perfiles con mayor dificultad de inserción
- Priorizar regiones con desempleo estructural
- Diseñar programas diferenciados por grupo poblacional

**Ejemplo concreto:**
El MOL revela que en Santiago del Estero hay alta demanda de "Operarios de Construcción" pero 40% de jóvenes desempleados no tiene secundario completo (requisito en 70% de ofertas). Se diseña programa combinado: terminalidad educativa + capacitación en oficios + intermediación laboral.

---

**4. ROI medible en capacitaciones**
- Seguimiento de empleabilidad post-capacitación por programa
- Comparación de efectividad entre proveedores de formación
- Decisiones de continuidad/discontinuidad basadas en datos

**Ejemplo concreto:**
Se descubre que "Curso de Programación Python" de Proveedor A tiene 65% de inserción a 6 meses, vs 40% de Proveedor B. Se reasigna presupuesto al Proveedor A y se audita a B.

---

### Para Instituciones Educativas

**1. Currículas alineadas con demanda real**
- Actualización de contenidos basada en skills más solicitadas
- Incorporación de herramientas/tecnologías vigentes
- Eliminación de contenidos obsoletos

**Ejemplo concreto:**
Universidad detecta que 80% de ofertas para Contadores requieren SAP/ERP, pero su currícula no lo incluye. Agrega materia "Sistemas de Gestión Empresarial" en 4to año.

---

**2. Pertinencia de oferta formativa**
- Validar si existen ofertas laborales para nuevas carreras propuestas
- Decidir apertura/cierre de carreras con datos objetivos
- Proyectar empleabilidad de egresados

**Ejemplo concreto:**
Instituto evalúa crear "Tecnicatura en Energías Renovables". MOL muestra solo 15 ofertas/año en su provincia. Decide no abrir y en cambio ampliar cupos de "Electromecánica Industrial" (150 ofertas/año).

---

**3. Evidencia para diseño de nuevas carreras**
- Identificar nichos emergentes no cubiertos
- Diseñar diplomaturas cortas para necesidades puntuales
- Validar demanda antes de invertir en infraestructura

**Ejemplo concreto:**
Universidad detecta 200 ofertas mensuales de "Especialista en Marketing Digital" sin carrera específica en la región. Crea Diplomatura de 9 meses, llena cupos inmediatamente.

---

**4. Seguimiento de empleabilidad de egresados**
- Validar si los graduados consiguen empleo en su campo
- Medir tiempo desde egreso hasta primer empleo
- Identificar brechas entre formación y demanda real

**Ejemplo concreto:**
Facultad descubre que sus egresados de Ing. Industrial tardan 8 meses en conseguir empleo vs 3 meses del promedio. Investiga y descubre que mercado pide "experiencia con Lean Manufacturing" no enseñada. Incorpora contenido.

---

### Para Buscadores de Empleo

**1. Acceso equitativo a oportunidades**
- Ofertas llegan por mérito (compatibilidad), no por contactos
- Personas de provincias acceden a ofertas remotas de CABA
- Poblaciones vulnerables (discapacidad, trans, 50+) tienen visibilidad

**Impacto:** Reducción de desigualdad de oportunidades, especialmente en provincias con menor desarrollo económico.

---

**2. Orientación personalizada basada en datos**
- Saber exactamente qué skills les faltan
- Estimación de impacto de capacitaciones ("+45 ofertas si aprendés Excel avanzado")
- Claridad sobre competitividad de su perfil

**Impacto:** Empoderamiento en decisiones de carrera, inversión en capacitación con ROI claro.

---

**3. Reducción de tiempos de búsqueda**
- Notificaciones proactivas vs búsqueda manual diaria
- Matching reduce postulaciones irrelevantes (eficiencia)
- Visibilidad para empresas de candidatos pasivos

**Impacto:** Reducción estimada de tiempo de búsqueda de 6 meses → 1-2 meses (ahorro de 4 meses de ingresos perdidos).

---

**4. Claridad sobre brechas de formación**
- Listado concreto de skills faltantes
- Priorización por impacto (qué aprender primero)
- Links directos a cursos/capacitaciones

**Impacto:** Capacitación estratégica vs "estudiar por estudiar", mayor empleabilidad con menor inversión de tiempo.

---

**5. Empoderamiento en decisiones de carrera**
- Estudiantes eligen carreras con datos de empleabilidad
- Trabajadores deciden reconversión basada en demanda real
- Planificación de migraciones laborales informadas

**Impacto:** Reducción de deserción universitaria, trayectorias laborales más exitosas, movilidad social ascendente.

---

**6. Notificaciones proactivas de oportunidades relevantes**
- Reciben ofertas sin buscar activamente
- Alertas en celular de ofertas urgentes
- Descubren oportunidades que no sabían que existían

**Impacto:** Acceso a mercado oculto (ofertas que llenan rápido), mejores negociaciones salariales (reciben múltiples ofertas).

---

### Para Empresas

**1. Reducción de tiempo y costo de reclutamiento**
- Time-to-hire: 60 días → 30 días (ahorro de productividad)
- Menor dependencia de consultoras (ahorro 20-30% del salario anual)
- Sourcing automatizado de candidatos pre-calificados

**Impacto:** Empresa que contrata 10 personas/año ahorra ~$800K en fees de consultoras + $2M en productividad perdida por vacantes largas = **$2.8M/año**

---

**2. Decisiones de compensaciones competitivas**
- Benchmarking salarial en tiempo real
- Evitar contraofertas (pagar competitivo desde inicio)
- Reducción de rotación por salarios no competitivos

**Impacto:** Empresa con 100 empleados reduce rotación de 15% → 10% = ahorro de $6M/año en costos de rotación (reclutamiento + capacitación + pérdida de productividad).

---

**3. Visibilidad de disponibilidad de talento por región**
- Decidir dónde abrir oficinas basado en talento disponible
- Evaluar factibilidad de proyectos (¿hay suficientes ingenieros?)
- Anticipar brechas antes de expandir equipos

**Impacto:** Empresa evita abrir oficina en provincia sin talento suficiente → ahorro de $20M en inversión fallida.

---

**4. Optimización de descripciones de puesto**
- Validar que requisitos no sean excesivos (ahuyentan candidatos)
- Agregar beneficios competitivos
- Lenguaje inclusivo (ampliar pool de candidatos)

**Impacto:** Oferta optimizada recibe 2.5x más postulaciones de calidad → se llena vacante en mitad de tiempo.

---

**5. Acceso a candidatos pre-calificados**
- Filtrado automático (sistema ya hizo el trabajo)
- Invitación directa a candidatos pasivos (60% del mercado)
- Reducción de CV no calificados (pérdida de tiempo de RRHH)

**Impacto:** RRHH dedica tiempo a entrevistar candidatos calificados vs filtrar 100 CV irrelevantes → mejora calidad de contratación.

---

**6. Inteligencia competitiva sobre guerra por talento**
- Saber qué empresas compiten por mismo perfil
- Alertas cuando competencia publica ofertas similares
- Benchmark de salarios y beneficios de competidores

**Impacto:** Empresa puede reaccionar rápido (ajustar salario, acelerar procesos) → gana guerra por talento clave.

---

**7. Validación de estrategias de expansión regional**
- Datos objetivos sobre disponibilidad de talento por provincia
- Comparación de costos laborales ajustados por costo de vida
- Proyección de facilidad de reclutamiento

**Impacto:** Decisión informada de expansión → tasa de éxito 85% vs 50% sin datos (ahorro de inversiones fallidas).

---

**8. Mejora de employer branding con datos objetivos**
- Conocer percepción vs competencia
- Identificar oportunidades de diferenciación
- Medir impacto de cambios en beneficios (ej: home office)

**Impacto:** Empresa mejora atractivo → postulaciones aumentan 40% → se llena pipeline de talento.

---

### Para el Mercado Laboral (Efectos Sistémicos)

**1. Reducción de asimetrías de información**
- Candidatos saben qué se paga en el mercado (negocian mejor)
- Empresas saben qué talento está disponible (ofrecen competitivo)
- Transparencia salarial reduce brechas

**Impacto:** Mercado más eficiente, salarios se acercan al equilibrio, reducción de explotación.

---

**2. Matching más eficiente candidato-empresa**
- Reducción de rotación por mal match (candidato sobrecalificado o subcalificado)
- Ofertas llegan a personas correctas (no se pierden talentos)
- Empresas contratan mejor fit cultural (mayor productividad)

**Impacto:** Rotación promedio baja de 15% → 10% → ahorro sistémico de miles de millones en costos de rotación.

---

**3. Disminución de tiempos de vacancia**
- Puestos se llenan más rápido
- Menor pérdida de productividad empresarial
- Menor carga sobre equipos que cubren vacantes

**Impacto:** Reducción de tiempos de vacancia de 60 → 30 días → aumento de productividad agregada de la economía.

---

**4. Mejora de productividad agregada**
- Mejores matches → mayor productividad individual
- Menos rotación → mayor experiencia acumulada en empresas
- Capacitación focalizada → trabajadores más calificados

**Impacto:** Aumento estimado de 2-3% en productividad laboral agregada → crecimiento del PBI.

---

**5. Transparencia salarial**
- Reducción de discriminación salarial (género, edad, origen)
- Competencia sana por talento basada en calidad, no opacidad
- Mejora de poder de negociación de trabajadores

**Impacto:** Reducción de brecha salarial de género, aumento de salarios reales promedio.

---

### Impacto Social

**1. Inclusión laboral de poblaciones vulnerables**
- Personas con discapacidad acceden a ofertas con adaptaciones
- Comunidad trans visibiliza su identidad sin discriminación
- Jóvenes sin contactos acceden por mérito

**Impacto:** Reducción de exclusión laboral, sociedades más inclusivas.

---

**2. Movilidad social ascendente**
- Hijos de familias de bajos recursos acceden a mejores empleos
- Orientación vocacional previene elecciones de carrera con baja empleabilidad
- Capacitaciones estratégicas permiten saltos salariales

**Impacto:** Reducción de pobreza estructural, mayor igualdad de oportunidades.

---

**3. Desarrollo regional equilibrado**
- Empresas descubren talento en provincias (descentralización)
- Jóvenes provinciales no necesitan migrar a CABA obligatoriamente
- Inversión se distribuye en el territorio

**Impacto:** Menor concentración en CABA/GBA, desarrollo de polos regionales.

---

**4. Reducción de desempleo estructural**
- Matching eficiente reduce desempleo friccional
- Capacitaciones focalizadas reducen desempleo por brechas de skills
- Orientación vocacional reduce desempleo por mala elección de carrera

**Impacto:** Tasa de desempleo estructural baja de 8% → 5% → 1.5 millones de personas más empleadas.

---

## 9. GLOSARIO DE TÉRMINOS

**API (Application Programming Interface):**
Interfaz que permite que dos sistemas informáticos se comuniquen entre sí. Por ejemplo, el MOL puede ofrecer una API para que una oficina de empleo municipal consulte ofertas.

**Benchmarking:**
Proceso de comparar una métrica propia con el promedio del mercado. Ejemplo: "Mi empresa paga $600K a desarrolladores, el benchmark del mercado es $800K".

**Dashboard:**
Panel visual que muestra métricas e indicadores en gráficos, tablas y números. Facilita tomar decisiones rápidas viendo toda la información en un solo lugar.

**Employer Branding:**
Reputación de una empresa como empleador. Ejemplo: "Google tiene buen employer branding porque ofrece oficinas modernas y libertad creativa".

**ESCO (European Skills, Competences, Qualifications and Occupations):**
Clasificación europea de ocupaciones y habilidades. Es como el "idioma común" que permite comparar mercados laborales de diferentes países.

**Freemium:**
Modelo de negocio donde el servicio básico es gratuito y se cobra por funcionalidades premium. Ejemplo: Spotify gratis con publicidad, Spotify Premium sin publicidad.

**Matching:**
Proceso de emparejar dos cosas según compatibilidad. En el MOL, matching entre candidatos y ofertas.

**NLP (Natural Language Processing - Procesamiento de Lenguaje Natural):**
Tecnología que permite a computadoras entender texto humano. Ejemplo: cuando el MOL lee "se requiere experiencia de 3 a 5 años" y extrae: experiencia_min=3, experiencia_max=5.

**Scoring:**
Asignación de un puntaje a algo. Ejemplo: "Esta oferta tiene 85% de compatibilidad con tu perfil" → scoring de compatibilidad.

**Scraping:**
Técnica para extraer datos públicos de sitios web de forma automatizada. El MOL hace scraping de portales de empleo para descargar ofertas.

**Skills:**
Habilidades. Pueden ser técnicas (Python, Excel) o blandas (liderazgo, comunicación).

**Soft Skills:**
Habilidades interpersonales o de personalidad. Ejemplos: trabajo en equipo, proactividad, adaptabilidad, comunicación efectiva.

**Time-to-hire:**
Tiempo desde que se publica una oferta hasta que se contrata a alguien. Indicador clave de eficiencia de reclutamiento.

**ROI (Return on Investment - Retorno de Inversión):**
Relación entre el beneficio obtenido y el costo de una inversión. Ejemplo: "Invertí $80K en curso de programación, conseguí trabajo con $200K más de salario/mes → ROI positivo en 1 mes".

---

## 10. ANEXOS

### A. Métricas Clave Actuales

**Base de datos (Noviembre 2025):**
- Total ofertas: 5,704
- Ofertas con análisis NLP: 5,479 (96%)
- Ofertas con clasificación ESCO: 5,479 (96%)
- Ocupaciones ESCO únicas: 3,045
- Skills ESCO catalogadas: ~13,890
- Tamaño de base de datos: 13.83 MB

**Scraping:**
- Portales integrados: 5 (Bumeran, ZonaJobs, Computrabajo, LinkedIn, Indeed)
- Portal principal automatizado: Bumeran
- Keywords de búsqueda: 1,148
- Keywords productivos: 1,340 (58.4%)
- Tiempo de ejecución: 38 minutos
- Frecuencia: 2 veces por semana (Lunes y Jueves, 8:00 AM)
- Ofertas nuevas por semana: ~600

**Análisis NLP (sobre 8,472 ofertas):**
- Soft skills: 63.1% cobertura
- Skills técnicas: 40.3% cobertura
- Educación: 38.6% cobertura
- Experiencia: 29.2% cobertura
- Idiomas: 20.5% cobertura
- Salarios: <6% cobertura

**Dashboards:**
- Dashboard Operativo (Plotly/Dash): Activo en http://localhost:8052
- Dashboard Público (Shiny): Activo en https://dos1tv-gerardo-breard.shinyapps.io/dashboard-esco-argentina/
- Dataset dashboard público: 268 ofertas validadas manualmente
- UX Score dashboard público: 8.2/10

---

### B. Ejemplos de Casos de Uso

**Caso 1: Diseñador de políticas identificando skills emergentes**

**Perfil:** María, analista senior de OEDE, diseña programas de capacitación.

**Desafío:** Definir contenidos de programa "Argentina Programa 4.0" para jóvenes sin experiencia.

**Uso del MOL:**
1. Filtra ofertas para perfiles junior en IT
2. Analiza top 20 skills técnicas más demandadas
3. Identifica lenguajes de programación en crecimiento vs estancados
4. Revisa requisitos de certificaciones

**Descubrimiento:**
- Python: presente en 65% de ofertas (vs 45% hace 2 años → +44%)
- JavaScript/React: 58% de ofertas
- Java: 30% de ofertas (vs 50% hace 2 años → -40%)
- SQL: 70% de ofertas (crítico)
- Git/GitHub: 55% de ofertas (nuevo requisito estándar)

**Decisión:** Priorizar Python + React + SQL + Git en currícula de Argentina Programa 4.0, reducir horas de Java.

**Resultado:** Nueva camada tiene 78% de empleabilidad a 6 meses (vs 65% de camada anterior con currícula desactualizada).

---

**Caso 2: Universidad ajustando currícula de Ingeniería en Sistemas**

**Perfil:** Juan, director de carrera de Ingeniería en Sistemas, universidad privada de Córdoba.

**Desafío:** Egresados reportan que su formación está desactualizada vs demanda real.

**Uso del MOL:**
1. Filtra ofertas de "Desarrollador de Software" y "Analista de Sistemas" en Córdoba
2. Extrae skills técnicas requeridas
3. Compara con plan de estudios actual
4. Identifica gaps

**Descubrimiento:**
- 80% de ofertas requieren metodologías ágiles (Scrum, Kanban) → currícula solo menciona en 1 materia optativa
- 70% requiere cloud (AWS, Azure, GCP) → no enseñado
- 65% requiere contenedores (Docker, Kubernetes) → no enseñado
- 50% requiere experiencia con microservicios → solo se enseña arquitectura monolítica

**Decisión:**
- Agregar materia obligatoria "Metodologías Ágiles" en 3er año
- Incorporar módulo de cloud computing en "Arquitectura de Software"
- Crear materia optativa "DevOps y Contenedores"
- Actualizar proyecto final integrador para usar microservicios

**Resultado:** Egresados del nuevo plan consiguen empleo en promedio 3 meses vs 7 meses del plan anterior. Matrícula aumenta 15% por reputación de empleabilidad.

---

**Caso 3: Joven buscando primer empleo con orientación personalizada**

Ver Escenario 6 en Sección 5 (Lucía, egresada de Administración).

---

**Caso 4: Trabajador evaluando reconversión laboral**

Ver Escenario 7 en Sección 5 (Carlos, vendedor en reconversión a ejecutivo comercial).

---

**Caso 5: Empresa optimizando salarios para retener talento**

Ver Escenario 8 en Sección 5 (Startup ajustando salario de desarrollador Python).

---

**Caso 6: Startup evaluando dónde abrir oficina regional**

Ver Escenario 9 en Sección 5 (Empresa de software decidiendo entre Córdoba, Rosario y Mendoza).

---

### C. Roadmap Visual

```
FASE ACTUAL                  HITO 1-2                HITO 3-4                HITO 5-6                HITO 7-8
[Análisis]          →     [Datos de Calidad]   →   [Motor Matching]   →   [Plataformas]      →   [Ecosistema]

┌──────────────┐          ┌──────────────┐         ┌──────────────┐        ┌──────────────┐         ┌──────────────┐
│  Scraping    │          │ NLP 85%      │         │ Scoring      │        │ Web Busca-   │         │ Portal       │
│  Automatizado│          │ precisión    │         │ Auto-        │        │ dores        │         │ Nacional     │
│              │    →     │              │   →     │ mático       │   →    │              │    →    │ de Empleo    │
│  Dashboard   │          │ Análisis     │         │              │        │ Web          │         │              │
│  Operativo   │          │ Regional     │         │ Recomen-     │        │ Empresas     │         │ 100K+        │
│              │          │              │         │ daciones     │        │              │         │ usuarios     │
│  5,704       │          │ Benchmarks   │         │              │        │ App Móvil    │         │              │
│  ofertas     │          │ Salariales   │         │ Detección    │        │              │         │ Integración  │
│              │          │              │         │ de Brechas   │        │ Push         │         │ Ecosistema   │
└──────────────┘          └──────────────┘         └──────────────┘        └──────────────┘         └──────────────┘

   ✅ COMPLETO              ⚠️ EN PROGRESO            🔄 DISEÑO                🎯 FUTURO               🌟 VISIÓN
```

---

### D. Contacto

**Para consultas sobre este informe:**

**Observatorio de Empleo y Dinámica Empresarial (OEDE)**
Secretaría de Trabajo, Empleo y Seguridad Social (STEYSS)
Ministerio de Capital Humano
República Argentina

**Web:** [www.trabajo.gob.ar](https://www.trabajo.gob.ar)
**Email:** oede@trabajo.gob.ar

---

### E. Referencias y Fuentes

**Datos del sistema:**
- Base de datos SQLite: `D:\OEDE\Webscrapping\database\bumeran_scraping.db`
- Dashboard público: https://dos1tv-gerardo-breard.shinyapps.io/dashboard-esco-argentina/
- Documentación técnica: `D:\OEDE\Webscrapping\docs\`

**ESCO - European Classification:**
- Portal oficial: https://esco.ec.europa.eu
- RDF data: esco-v1.2.0.rdf (1.26 GB)
- Ocupaciones: 3,045 perfiles
- Skills: ~13,890 competencias

**Portales de empleo integrados:**
- Bumeran: https://www.bumeran.com.ar
- ZonaJobs: https://www.zonajobs.com.ar
- Computrabajo: https://www.computrabajo.com.ar
- LinkedIn: https://www.linkedin.com/jobs
- Indeed: https://ar.indeed.com

---

**Fecha de publicación:** 6 de Noviembre de 2025
**Versión:** 1.0
**Estado:** Documento público para difusión

---

**FIN DEL INFORME**
