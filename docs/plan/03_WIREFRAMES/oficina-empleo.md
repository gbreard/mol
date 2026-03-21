# Wireframes: Oficina de Empleo + Reporte Compatibilidad

> Ultima actualizacion: 2026-03-18

## Referencias

| Documento | Relacion |
|-----------|----------|
| [02_ARQUITECTURA_PANTALLAS](../02_ARQUITECTURA_PANTALLAS.md) | Pantallas P-32 a P-35 |
| [08_PROPUESTA_VALOR](../08_PROPUESTA_VALOR.md) | V-17 Reporte Compatibilidad |
| [05_USER_FLOWS](../05_USER_FLOWS.md) | F-06 Flujo reporte |
| [04_MODELO_DATOS](../04_MODELO_DATOS.md) | T-reportes_compatibilidad |

---

## P-32: Hub Oficina de Empleo (`/oficina-empleo`)

**Estado:** Wireframe estatico (2026-03-03)
**Nivel:** U-OFICINA_EMPLEO / U-ADMIN

```
+---------------------------------------------------------------------+
|  [Logo]  Dashboard  Skills  Oficina de Empleo           [Usuario v] |
+---------------------------------------------------------------------+
|                                                                       |
|  Oficina de Empleo                                                    |
|                                                                       |
|  +-------------------+  +-------------------+  +-------------------+  |
|  | [icon]            |  | [icon]            |  | [icon]            |  |
|  | Perfil            |  | Ofertas           |  | Reportes          |  |
|  | Trabajador        |  | Coincidentes      |  | Compatibilidad    |  |
|  |                   |  |                   |  |                   |  |
|  | Cargar y gestio-  |  | Ver ofertas que   |  | Generar reportes  |  |
|  | nar perfiles de   |  | coinciden con el  |  | PDF para entregar |  |
|  | trabajadores      |  | perfil cargado    |  | a empresas        |  |
|  |                   |  |                   |  |                   |  |
|  | [Ir a Perfiles]   |  | [Ver Ofertas]     |  | [Ver Reportes]    |  |
|  +-------------------+  +-------------------+  +-------------------+  |
|                                                                       |
+---------------------------------------------------------------------+
```

---

## P-33: Perfil Trabajador (`/oficina-empleo/perfil`)

**Estado:** Wireframe estatico (2026-03-03)
**Nivel:** U-OFICINA_EMPLEO / U-ADMIN

> Funcionalidad real pendiente. El componente `MySkillsSearch` ya implementa el flujo completo de carga de perfil + matching.

---

## Captura de competencias (Paso 2) — Rediseño con 3 vias de entrada

**Estado:** Propuesta (2026-03-18)
**Aplica a:** P-33 (Oficina Empleo) y P-10 tab Mis Skills (Mi Futuro Laboral)
**Feature:** V-17

El paso 2 actual solo permite buscar por ocupacion ESCO, lo que asume que el trabajador conoce su ocupacion formal. El rediseño propone 3 vias de entrada combinables:

### Via 1: Por ocupacion (existe)

```
+---------------------------------------------------------------+
|  "En que trabajaste?"                                          |
|                                                                 |
|  [Buscar ocupacion: albanil, electricista, vendedor...]        |
|                                                                 |
|  Busca ocupacion ESCO y extrae las competencias del perfil     |
|  consolidado argentino (ESCO + emergentes aprobadas).          |
+---------------------------------------------------------------+
```

### Via 2: Por tarea o habilidad (nuevo)

```
+---------------------------------------------------------------+
|  "Que sabes hacer?"                                            |
|                                                                 |
|  [Buscar: soldar, programar, atender clientes...]              |
|                                                                 |
|  Busca en el catalogo de competencias (ESCO + emergentes       |
|  argentinas). Busca por nombre Y por definicion.               |
|  Ejemplo: escribir "soldar" muestra todas las competencias     |
|  de soldadura con su definicion para confirmar.                |
+---------------------------------------------------------------+
```

### Via 3: Texto libre (nuevo)

```
+---------------------------------------------------------------+
|  "Conta con tus palabras"                                      |
|                                                                 |
|  [Trabaje 5 anios en una fabrica haciendo soldadura y         |
|   mantenimiento de maquinas industriales. Tambien se de        |
|   electricidad porque hice un curso...]                        |
|                                                                 |
|  El sistema identifica competencias del texto.                 |
+---------------------------------------------------------------+
```

### Panel de competencias identificadas (con definiciones)

**Elemento clave:** cada competencia muestra su definicion ESCO para que el trabajador confirme o descarte.

```
+---------------------------------------------------------------+
|  Tus competencias (12)                                         |
|                                                                 |
|  [✓] Soldadura                                    [skill]     |
|      "Realizar diversas tecnicas de soldeo y union             |
|       de piezas metalicas."                                    |
|      via: ocupacion                                            |
|                                                                 |
|  [✓] Mantenimiento de maquinas                    [skill]     |
|      "Actividades regulares de mantenimiento                   |
|       preventivo y correctivo."                                |
|      via: ocupacion                                            |
|                                                                 |
|  [✓] Electricidad industrial                      [knowledge] |
|      "Principios de instalacion y reparacion                   |
|       de sistemas electricos."                                 |
|      via: busqueda manual                                      |
|                                                                 |
|  [?] Lectura de planos                            [skill]     |
|      "Leer e interpretar planos tecnicos y                     |
|       diagramas de ingenieria."                                |
|      via: ocupacion                                            |
|                                                                 |
|  [?] = "No estoy seguro" - lee la definicion y                |
|        decidi si aplica a lo que sabes hacer.                  |
+---------------------------------------------------------------+
```

### Via 4: Por formacion o titulo (nuevo — del documento v5)

```
+---------------------------------------------------------------+
|  "Que estudiaste?"                                             |
|                                                                 |
|  [Buscar titulo: tecnico electricista, lic. administracion...]  |
|                                                                 |
|  El sistema mapea la formacion a skills ESCO usando la base    |
|  de resoluciones oficiales de carreras argentinas + catalogo   |
|  de cursos de academias locales e internacionales.             |
|                                                                 |
|  Ejemplo: "Tecnicatura en Redes" -> Redes, TCP/IP, Linux,     |
|  Ciberseguridad basica, Administracion de servidores           |
+---------------------------------------------------------------+
```

**Nota sobre Via 4:** Requiere la construccion de una base de resoluciones oficiales de aprobacion de carreras (pre, grado, posgrado) y catalogo de cursos mapeados a ESCO. Es la via mas ambiciosa pero la que mejor captura formacion formal.

**Nota:** Las competencias que vienen del perfil consolidado argentino incluyen tanto skills ESCO estandar como emergentes aprobadas por analistas del MOL. Cada una muestra su origen (via ocupacion, via busqueda manual, via texto libre, via formacion).

---

## P-34: Ofertas Coincidentes (`/oficina-empleo/ofertas`)

**Estado:** Wireframe estatico (2026-03-03) — se reemplaza por tab en paso 3
**Nivel:** U-OFICINA_EMPLEO / U-ADMIN

> La funcionalidad de ofertas coincidentes se integra como **tab "Ofertas laborales"** en el paso 3 de resultados (tanto para Oficina de Empleo como Mi Futuro Laboral). No es una pagina separada.

---

## Paso 3: Resultados — 3 tabs (Ocupaciones + Ofertas + Capacitacion)

**Estado:** Ocupaciones existe (parcial). Ofertas y Capacitacion por crear.
**Aplica a:** Ambos caminos (Mi Futuro Laboral y Oficina de Empleo)
**Feature:** V-17

Despues de construir el perfil (paso 2), el paso 3 muestra resultados en 3 tabs:

### Tab 1: Ocupaciones compatibles (existe parcial)

```
+---------------------------------------------------------------------+
|  Paso 3: Resultados                                                  |
|                                                                      |
|  [Ocupaciones compatibles]  [Ofertas laborales]  [Capacitacion]      |
|   ==========================                                         |
|                                                                      |
|  +----------------------------------------------------------------+ |
|  | Ocupacion               | Compat. | Esenciales | Brecha | Acc. | |
|  |-------------------------|---------|------------|--------|------| |
|  | Desarrollador software  | 78%     | 7/9        | 2      | [Rep]| |
|  | Analista de sistemas    | 72%     | 6/8        | 2      | [Rep]| |
|  | Administrador de BD     | 65%     | 5/8        | 3      | [Rep]| |
|  +----------------------------------------------------------------+ |
|                                                                      |
|  [Rep] = Generar Reporte de Compatibilidad (PDF + QR)               |
+---------------------------------------------------------------------+
```

### Tab 2: Ofertas laborales (nuevo)

Ofertas reales de `ofertas_dashboard` filtradas por las ocupaciones compatibles. Cada oferta muestra compatibilidad personalizada y gap especifico.

```
+---------------------------------------------------------------------+
|  Paso 3: Resultados                                                  |
|                                                                      |
|  [Ocupaciones compatibles]  [Ofertas laborales]  [Capacitacion]      |
|                              ===================                     |
|                                                                      |
|  47 ofertas activas para tus ocupaciones compatibles                 |
|  Filtros: [Provincia v] [Ocupacion v] [Modalidad v] [Ordenar v]     |
|                                                                      |
|  +----------------------------------------------------------------+ |
|  | Desarrollador Python - Senior                                   | |
|  | TechCorp SA  |  CABA  |  Remoto  |  Hace 3 dias               | |
|  | Compatibilidad: 78% (7/9 esenciales)                           | |
|  | Skills que tenes: Python, SQL, Git, Testing, REST APIs         | |
|  | Te faltan: Docker, CI/CD                                       | |
|  |                                    [Ver oferta]  [Reporte]      | |
|  +----------------------------------------------------------------+ |
|  | Analista de Sistemas                                            | |
|  | Banco Nacion  |  Buenos Aires  |  Hibrido  |  Hace 5 dias      | |
|  | Compatibilidad: 72% (6/8 esenciales)                           | |
|  | Skills que tenes: SQL, Python, Testing, Agile                  | |
|  | Te faltan: SAP, COBOL                                          | |
|  |                                    [Ver oferta]  [Reporte]      | |
|  +----------------------------------------------------------------+ |
|                                                                      |
|  Mostrando 2 de 47  |  [Cargar mas]                                |
|                                                                      |
|  [Ver oferta] = Link al portal original                             |
|  [Reporte] = Genera reporte vinculado a esta oferta especifica      |
+---------------------------------------------------------------------+
```

**Datos:** JOIN entre ocupaciones compatibles (paso 3) y `ofertas_dashboard` filtrado por `isco_code`. Se calcula gap personalizado comparando skills del perfil vs skills de cada oferta.

### Tab 3: Capacitacion sugerida (nuevo)

Cursos que cubren las brechas tecnicas. Organizado por skill faltante. Incluye sugerencia de transicion laboral.

```
+---------------------------------------------------------------------+
|  Paso 3: Resultados                                                  |
|                                                                      |
|  [Ocupaciones compatibles]  [Ofertas laborales]  [Capacitacion]      |
|                                                   ==============     |
|                                                                      |
|  Basado en tus brechas tecnicas, estos cursos pueden ayudarte:      |
|                                                                      |
|  -- Te falta: Docker ----------------------------------------+      |
|  |                                                           |      |
|  |  Iniciacion a DevOps y contenedores                       |      |
|  |  Microcredencial  |  4 meses  |  Virtual                  |      |
|  |  Cubre: Docker, CI/CD, Linux                              |      |
|  |  [Ver curso]                                              |      |
|  |                                                           |      |
|  |  Administracion de servidores Linux                       |      |
|  |  Capacitacion Laboral  |  1 cuatrimestre  |  Presencial   |      |
|  |  Cubre: Linux, Docker, Redes                              |      |
|  |  [Ver curso]                                              |      |
|  +-----------------------------------------------------------+      |
|                                                                      |
|  -- Te falta: Testing de software ----------------------------+      |
|  |                                                           |      |
|  |  Testing QA                                               |      |
|  |  Microcredencial  |  4 meses  |  Virtual                  |      |
|  |  Cubre: Testing, Automatizacion, QA                       |      |
|  |  [Ver curso]                                              |      |
|  +-----------------------------------------------------------+      |
|                                                                      |
|  +----------------------------------------------------------------+ |
|  |  TRANSICION LABORAL SUGERIDA                                    | |
|  |  Con solo 2 skills mas (Docker + Testing), podes pasar de:     | |
|  |  Analista de sistemas (72%) --> Desarrollador (89%)            | |
|  |  Tiempo estimado de capacitacion: 4-8 meses                    | |
|  +----------------------------------------------------------------+ |
|                                                                      |
|  Fuente: Portal de Capacitacion CABA  |  2,255 cursos disponibles  |
+---------------------------------------------------------------------+
```

**Datos:** Skills gap del trabajador matcheadas contra nombre + descripcion + plan de estudio de cursos del Portal CABA.

### Transicion laboral: dos opciones

El tab de capacitacion incluye un bloque de **transicion laboral** con dos enfoques:

**Opcion A — Por preferencia del trabajador:**
El trabajador elige hacia donde quiere transicionar. El sistema le muestra que skills le faltan y donde capacitarse.

```
+----------------------------------------------------------------+
|  TRANSICION POR PREFERENCIA                                     |
|                                                                  |
|  A donde te gustaria transicionar?                              |
|  [Buscar ocupacion: desarrollador, analista...]                 |
|                                                                  |
|  Elegiste: Desarrollador de software                            |
|  Tu compatibilidad actual: 58%                                  |
|  Skills que te faltan: Docker, CI/CD, Testing (3)               |
|  Capacitacion estimada: 4-8 meses                               |
|                                                                  |
|  Cursos sugeridos:                                              |
|  - Iniciacion a DevOps (Docker, CI/CD) — 4 meses, Virtual      |
|  - Testing QA — 4 meses, Virtual                                |
+----------------------------------------------------------------+
```

**Opcion B — Por demanda del mercado:**
El sistema analiza la tendencia temporal de las ofertas (crecimiento mes a mes) y sugiere ocupaciones que estan creciendo y que son alcanzables desde el perfil actual.

```
+----------------------------------------------------------------+
|  TRANSICION POR DEMANDA DEL MERCADO                             |
|                                                                  |
|  Ocupaciones en crecimiento cercanas a tu perfil:               |
|                                                                  |
|  1. Ingeniero de datos          Tendencia: +35% (3 meses)      |
|     Tu compatibilidad: 62%      Te faltan: 3 skills             |
|     Capacitacion: ~6 meses      [Ver cursos] [Ver ofertas]      |
|                                                                  |
|  2. Especialista en ciberseg.   Tendencia: +28% (3 meses)      |
|     Tu compatibilidad: 55%      Te faltan: 4 skills             |
|     Capacitacion: ~8 meses      [Ver cursos] [Ver ofertas]      |
|                                                                  |
|  3. Analista de datos            Tendencia: +22% (3 meses)      |
|     Tu compatibilidad: 71%      Te faltan: 2 skills             |
|     Capacitacion: ~3 meses      [Ver cursos] [Ver ofertas]      |
|                                                                  |
|  Basado en ofertas publicadas en los ultimos 3 meses.           |
|  Ordenado por: accesibilidad (menos skills faltantes primero).  |
+----------------------------------------------------------------+
```

**Logica de "Transicion por demanda":**
1. Calcular tendencia temporal: contar ofertas por ISCO en ventana reciente (3 meses) vs ventana anterior.
2. Filtrar ocupaciones con crecimiento > 15%.
3. Calcular compatibilidad de cada una con el perfil del trabajador.
4. Ordenar por accesibilidad: menos skills faltantes primero.
5. Mostrar top 5 con cursos sugeridos para cada brecha.

**Datos necesarios:** `ofertas_dashboard` tiene `fecha_publicacion_iso` y `isco_code`, suficiente para calcular tendencia. `occupation_similarity.json` complementa con ocupaciones cercanas.

**Fuentes de capacitacion (expansible):**

| Fuente | Estado | Cursos |
|--------|--------|--------|
| Portal Capacitacion CABA | Scrapeado (2,255 cursos con desc + plan) | Primera fuente |
| Plataformas nacionales | Pendiente | Futuro |
| MOOCs (Coursera, edX) | Pendiente | Futuro |

---

## P-35: Reporte de Compatibilidad (`/reporte/:token`)

**Estado:** Por crear
**Nivel:** PUBLICO (sin autenticacion, acceso por token)
**Feature:** V-17

Pagina que ve el reclutador al escanear el QR de la carta PDF.
Las competencias mostradas provienen del **Perfil Consolidado Argentino** (ESCO + emergentes aprobadas), no del ESCO generico. El reporte indica la version del perfil usado.

### Layout principal

```
+---------------------------------------------------------------------+
|                                                                       |
|  [Logo MOL]           Reporte de Compatibilidad Laboral               |
|                                                                       |
+---------------------------------------------------------------------+
|                                                                       |
|  +---------------------------------------------------------------+   |
|  |  DATOS DEL PERFIL                                             |   |
|  |                                                               |   |
|  |  Candidato: Juan Perez                                        |   |
|  |  Vacante analizada: Desarrollador de software                 |   |
|  |  Codigo ISCO: 2512 | Codigo ESCO: 2512.1                     |   |
|  |  Fecha del reporte: 18/03/2026                                |   |
|  |                                                               |   |
|  |  Compatibilidad general:                                      |   |
|  |  78% [========------] 7 de 9 competencias esenciales          |   |
|  +---------------------------------------------------------------+   |
|                                                                       |
|  +---------------------------------------------------------------+   |
|  |  MAPA DE COMPETENCIAS REQUERIDAS                    [Editar]  |   |
|  |                                                               |   |
|  |  Competencias esenciales (9):                                 |   |
|  |  +-----------------------------------------------------------+|   |
|  |  | Competencia          | Estado      | Accion              ||   |
|  |  |----------------------|-------------|---------------------||   |
|  |  | JavaScript           | Detectada   |                     ||   |
|  |  | Python               | Detectada   |                     ||   |
|  |  | SQL                  | Detectada   |                     ||   |
|  |  | Testing              | Detectada   |                     ||   |
|  |  | Git                  | Detectada   |                     ||   |
|  |  | REST APIs            | Detectada   |                     ||   |
|  |  | Metodologias agiles  | Detectada   |                     ||   |
|  |  | Docker               | FALTANTE    | [x Quitar]          ||   |
|  |  | CI/CD                | FALTANTE    | [x Quitar]          ||   |
|  |  +-----------------------------------------------------------+|   |
|  |                                                               |   |
|  |  Competencias opcionales (5): 3 detectadas                    |   |
|  |  [Expandir para ver detalle]                                  |   |
|  |                                                               |   |
|  |  [+ Agregar competencia al mapa]                              |   |
|  |                                                               |   |
|  |  (Los cambios recalculan automaticamente la compatibilidad)   |   |
|  +---------------------------------------------------------------+   |
|                                                                       |
|  +---------------------------------------------------------------+   |
|  |  MATRIZ DE AFINIDAD                                           |   |
|  |                                                               |   |
|  |  Competencias detectadas (7):          Brechas tecnicas (2):  |   |
|  |  +---------------------------+         +-------------------+  |   |
|  |  | JavaScript           [S] |         | Docker        [E] |  |   |
|  |  | Python               [S] |         | CI/CD         [E] |  |   |
|  |  | SQL                  [K] |         +-------------------+  |   |
|  |  | Testing              [S] |                                 |   |
|  |  | Git                  [T] |         [S]=Skill [K]=Knowledge |   |
|  |  | REST APIs            [S] |         [T]=Transversal         |   |
|  |  | Metodologias agiles  [T] |         [E]=Esencial faltante   |   |
|  |  +---------------------------+                                 |   |
|  +---------------------------------------------------------------+   |
|                                                                       |
|  +---------------------------------------------------------------+   |
|  |  SOBRE EL MOL                                                 |   |
|  |                                                               |   |
|  |  El Monitor de Ofertas Laborales (MOL) es una herramienta     |   |
|  |  del Observatorio de Empleo y Dinamica Empresarial (OEDE)     |   |
|  |  que analiza la demanda laboral utilizando la taxonomia        |   |
|  |  ESCO (European Skills, Competences, Qualifications and       |   |
|  |  Occupations) para estandarizar competencias.                 |   |
|  |                                                               |   |
|  |  [Conocer mas sobre el MOL ->]                                |   |
|  |                                                               |   |
|  |  Consultas: contacto@oede.gob.ar                              |   |
|  +---------------------------------------------------------------+   |
|                                                                       |
+---------------------------------------------------------------------+
```

### Modo edicion (reclutador personaliza competencias)

Cuando el reclutador hace click en `[Editar]`:

```
+---------------------------------------------------------------+
|  MAPA DE COMPETENCIAS REQUERIDAS                 [Guardando..] |
|                                                                 |
|  Compatibilidad recalculada: 88% (era 78%)                     |
|  [=========-] 7 de 8 competencias esenciales                   |
|                                                                 |
|  Competencias esenciales (8):  <-- era 9, se quito Docker      |
|  +-----------------------------------------------------------+ |
|  | Competencia          | Estado      | Accion               | |
|  |----------------------|-------------|----------------------| |
|  | JavaScript           | Detectada   |           [x Quitar] | |
|  | Python               | Detectada   |           [x Quitar] | |
|  | SQL                  | Detectada   |           [x Quitar] | |
|  | Testing              | Detectada   |           [x Quitar] | |
|  | Git                  | Detectada   |           [x Quitar] | |
|  | REST APIs            | Detectada   |           [x Quitar] | |
|  | Metodologias agiles  | Detectada   |           [x Quitar] | |
|  | CI/CD                | FALTANTE    |           [x Quitar] | |
|  +-----------------------------------------------------------+ |
|                                                                 |
|  [+ Agregar competencia]    [Restaurar original]                |
+---------------------------------------------------------------+
```

**Nota:** Los cambios del reclutador son en frontend solamente — no se persisten en BD. Si recarga, vuelve al estado original del reporte.

### Estados del reporte

| Estado | Que ve el reclutador |
|--------|---------------------|
| `activo` | Reporte completo con interactividad |
| `expirado` | Mensaje: "Este reporte ha expirado. Contacte al candidato para uno actualizado." |
| `revocado` | Mensaje: "Este reporte ya no esta disponible." |

### Responsivo

- **Desktop:** Layout 2 columnas (detectadas | brechas)
- **Mobile:** Layout stack (primero detectadas, despues brechas)
- **PDF del QR:** El QR debe ser lo suficientemente grande para escanear desde papel impreso

---

## Modificacion P-10: Boton "Generar Reporte" en Mis Skills

En el tab "Mis Skills" de P-10, al llegar al paso 3 (resultados de matching), se agrega un boton por cada ocupacion compatible:

```
+---------------------------------------------------------------+
|  PASO 3: Ocupaciones Compatibles                               |
|                                                                 |
|  +-----------------------------------------------------------+ |
|  | Ocupacion               | Match | Esenciales | Acciones   | |
|  |-------------------------|-------|------------|------------| |
|  | Desarrollador software  | 78%   | 7/9        | [Reporte]  | |
|  | Analista de sistemas    | 72%   | 6/8        | [Reporte]  | |
|  | Administrador de BD     | 65%   | 5/8        | [Reporte]  | |
|  +-----------------------------------------------------------+ |
|                                                                 |
+---------------------------------------------------------------+
```

Al hacer click en `[Reporte]`:
1. Abre modal para confirmar datos del candidato (nombre, DNI)
2. Llama a `POST /api/compatibility-report`
3. Muestra opciones: Descargar PDF / Copiar link / Ver reporte web

---

## Carta PDF (descargable)

Layout del PDF generado:

```
+---------------------------------------------------------------+
|                                                                 |
|  [LOGO MOL]                                                     |
|                                                                 |
|  ACCESO AL REPORTE DE COMPATIBILIDAD                           |
|  DEL PERFIL LABORAL                                            |
|  Monitor de Ofertas Laborales                                   |
|                                                                 |
|  Fecha: 18 de marzo de 2026                                    |
|                                                                 |
|  ─────────────────────────────────────────────────────────     |
|                                                                 |
|  El Monitor de Ofertas Laborales (MOL) es una herramienta      |
|  disenada para optimizar el encuentro entre la oferta y la     |
|  demanda de trabajo. A traves de la identificacion de          |
|  competencias laborales estandarizadas (Taxonomia ESCO),       |
|  el MOL evalua la afinidad tecnica de los perfiles frente      |
|  a los requerimientos de las ocupaciones.                      |
|                                                                 |
|  De acuerdo con la informacion procesada, Juan Perez,          |
|  DNI 30.123.456, presenta un perfil de competencias            |
|  laborales alineado con los requerimientos definidos para      |
|  la posicion de Desarrollador de Software.                     |
|                                                                 |
|  Para acceder al analisis detallado de compatibilidad          |
|  tecnica, por favor escanee el siguiente codigo QR:            |
|                                                                 |
|              +------------------+                               |
|              |                  |                               |
|              |    [QR CODE]     |                               |
|              |                  |                               |
|              +------------------+                               |
|              mol-nextjs.vercel.app/reporte/abc123               |
|                                                                 |
|  ─────────────────────────────────────────────────────────     |
|                                                                 |
|  Consultas: contacto@oede.gob.ar                                |
|                                                                 |
+---------------------------------------------------------------+
```

---

## P-36: Gestión Perfil Consolidado Argentino (`/admin/perfil-argentino`)

**Estado:** Por crear
**Nivel:** U-ADMIN
**Feature:** PCA-1

Pantalla de administracion para gestionar las versiones del Perfil Consolidado Argentino. El analista controla que version del perfil usa todo el sistema (matching, reportes, busqueda de skills).

### Layout

```
+---------------------------------------------------------------------+
|  Perfil Consolidado Argentino                                        |
|                                                                      |
|  Version activa: v2.1 (2026-03-15)    [Crear nueva version]         |
|                                                                      |
|  +----------------------------------------------------------------+ |
|  |  ESTADO ACTUAL (cambios desde v2.1)                             | |
|  |                                                                 | |
|  |  Ofertas procesadas desde ultimo corte: 2,132                   | |
|  |  Emergentes nuevas detectadas (>=30%): 8                        | |
|  |  Emergentes pendientes de revision: 3                           | |
|  |  Skills aprobadas desde ultimo corte: 5                         | |
|  |  Skills removidas desde ultimo corte: 0                         | |
|  |  Ocupaciones afectadas: 12                                      | |
|  |                                                                 | |
|  |  [Ver emergentes pendientes]  [Ir al panel de aprobacion]       | |
|  +----------------------------------------------------------------+ |
|                                                                      |
|  +----------------------------------------------------------------+ |
|  |  HISTORIAL DE VERSIONES                                         | |
|  |                                                                 | |
|  |  Version | Fecha       | Skills | Emergentes | Creado por  | Act| |
|  |  --------|-------------|--------|------------|-------------|----| |
|  |  v2.1    | 2026-03-15  | 14,312 | 55 aprob.  | admin@oede  | * | |
|  |  v2.0    | 2026-02-28  | 14,290 | 33 aprob.  | admin@oede  |   | |
|  |  v1.0    | 2026-01-15  | 14,257 | 0 (base)   | admin@oede  |   | |
|  |                                                                 | |
|  |  * = version activa (la que usa el sistema)                     | |
|  |                                                                 | |
|  |  [v2.1] → Ver detalle  |  Comparar con v2.0  |  Rollback     | |
|  +----------------------------------------------------------------+ |
|                                                                      |
|  +----------------------------------------------------------------+ |
|  |  CREAR NUEVA VERSION                                            | |
|  |                                                                 | |
|  |  Se creara un snapshot completo del estado actual del perfil.   | |
|  |  Los reportes generados a partir de ahora usaran esta version. | |
|  |  Los reportes existentes mantienen su version original.         | |
|  |                                                                 | |
|  |  Version propuesta: v2.2                                        | |
|  |  Nota del corte: [Incorpora Docker, Kubernetes, Scrum...]      | |
|  |                                                                 | |
|  |  Emergentes pendientes: 3 (se recomienda revisar antes)        | |
|  |                                                                 | |
|  |  [Cancelar]              [Confirmar corte v2.2]                 | |
|  +----------------------------------------------------------------+ |
+---------------------------------------------------------------------+
```

### Logica del versionado

```
1. Analista aprueba/rechaza emergentes en el panel existente (/admin/skills → Consolidado)
2. Cuando esta conforme, viene a esta pantalla
3. Click "Crear nueva version" → el sistema:
   a. Congela snapshot completo (todas las ocupaciones + sus skills)
   b. Guarda en tabla perfil_argentino_versiones
   c. Actualiza puntero "version_activa" en config
   d. Regenera skills_searchable.json con las emergentes aprobadas
   e. A partir de ahora, matching y busquedas usan esta version
4. Los reportes ya generados mantienen su version (snapshot inmutable)
5. Si algo sale mal: rollback a version anterior
```

### Modelo de datos

```sql
CREATE TABLE perfil_argentino_versiones (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  version VARCHAR(20) NOT NULL UNIQUE,    -- 'v1.0', 'v2.1', etc.
  snapshot JSONB NOT NULL,                 -- Snapshot completo del perfil
  total_skills INTEGER NOT NULL,
  total_emergentes_aprobadas INTEGER NOT NULL,
  total_ocupaciones INTEGER NOT NULL,
  nota TEXT,                               -- Nota del analista al crear el corte
  creado_por UUID REFERENCES auth.users(id),
  activa BOOLEAN DEFAULT FALSE,           -- Solo una puede ser activa
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Config: version activa
-- Se puede resolver con: SELECT * FROM perfil_argentino_versiones WHERE activa = TRUE
```

---

## Historial de Cambios

| Fecha | Version | Cambio |
|-------|---------|--------|
| 2026-03-03 | 1.0 | P-32, P-33, P-34 wireframes estaticos (placeholder) |
| 2026-03-18 | 1.1 | P-35 Reporte de Compatibilidad (V-17): wireframe completo con modo edicion, carta PDF, modificacion P-10 |
| 2026-03-18 | 1.2 | Rediseño Paso 2 (3 vias de entrada + definiciones visibles), ESCO Argentino como taxonomia de referencia en P-35 |
| 2026-03-18 | 1.3 | Paso 3 con 3 tabs: Ocupaciones + Ofertas laborales (nuevo) + Capacitacion sugerida (nuevo, fuente CABA). Transicion laboral. P-34 integrado como tab |
| 2026-03-18 | 1.4 | Transicion laboral dual: por preferencia del trabajador + por demanda del mercado (tendencia temporal de ofertas). Wireframes de ambas opciones |
| 2026-03-20 | 2.0 | Skills Intelligence v5: Via 4 (formacion/titulo), referencias a arquitectura S1/S2/S3 y 6 capacidades. Fuente: MOL_Skills_Intelligence.docx + mol_screens_v5.html |
| 2026-03-20 | 2.1 | P-36 Gestion Perfil Consolidado Argentino: UI versionado global, historial, rollback, crear corte, tabla perfil_argentino_versiones |
| 2026-03-21 | 2.2 | Wireframes mobile (Bloque F): S1 landing, captura skills, resultados y S3 reporte QR en 375px. Reglas de adaptacion desktop→mobile |

---

## S2-8: Formacion con impacto medible (Bloque 8°)

**Estado:** Por crear
**Nivel:** U-TECNICO_OE
**Feature:** B-D3, B-D4

El tecnico orienta al trabajador con cursos del catalogo de la OE. Cada curso muestra cuanto sube el match si lo completa.

```
+---------------------------------------------------------------------+
|  Formacion > Juan Perez                                              |
|                                                                      |
|  Brechas del perfil: Docker (3 cursos), Testing (2 cursos)          |
|                                                                      |
|  -- Brecha: Docker ------------------------------------+             |
|  |                                                     |             |
|  |  Introduccion a contenedores                        |             |
|  |  CENOF Barracas | 3 meses | Presencial              |             |
|  |  Cubre: Docker, Linux, Redes                        |             |
|  |                                                     |             |
|  |  IMPACTO: Si completa este curso:                   |             |
|  |  +---------------------------------------------+   |             |
|  |  | Desarrollador SW:  61% --> 78% (+17%)       |   |             |
|  |  | Administrador BD:  45% --> 58% (+13%)       |   |             |
|  |  | Ingeniero datos:   52% --> 67% (+15%)       |   |             |
|  |  +---------------------------------------------+   |             |
|  |                                                     |             |
|  |  [Derivar a este curso]                             |             |
|  +-----------------------------------------------------+             |
|                                                                      |
|  -- Brecha: Testing -----------------------------------+             |
|  |                                                     |             |
|  |  Testing QA                                         |             |
|  |  Virtual | 4 meses | Microcredencial                |             |
|  |  Cubre: Testing funcional, Automatizacion            |             |
|  |                                                     |             |
|  |  IMPACTO: Si completa este curso:                   |             |
|  |  +---------------------------------------------+   |             |
|  |  | Desarrollador SW:  78% --> 89% (+11%)       |   |             |
|  |  +---------------------------------------------+   |             |
|  |                                                     |             |
|  |  [Derivar a este curso]                             |             |
|  +-----------------------------------------------------+             |
|                                                                      |
|  Catalogo propio: 45 cursos  |  [Importar cursos CSV]               |
+---------------------------------------------------------------------+
```

**Logica del impacto:** El sistema simula que el trabajador tiene las skills del curso, recalcula matching contra ocupaciones compatibles, y muestra el delta.

---

## S2-10: Inteligencia Local (Bloque 10°)

**Estado:** Por crear (v2)
**Nivel:** U-TECNICO_OE / U-COORDINADOR
**Feature:** E-D1, E-D2

Dashboard de inteligencia del mercado laboral de la jurisdiccion de la OE.

```
+---------------------------------------------------------------------+
|  Inteligencia Local > OE CABA Sur                                    |
|                                                                      |
|  +-------------------------------+  +-----------------------------+  |
|  |  Skills mas demandadas        |  |  Skills menos disponibles   |  |
|  |  (en ofertas de la zona)      |  |  (en la cartera de la OE)   |  |
|  |                               |  |                             |  |
|  |  1. Python          78%      |  |  1. Docker          5%     |  |
|  |  2. SQL             72%      |  |  2. Kubernetes      3%     |  |
|  |  3. JavaScript      65%      |  |  3. CI/CD           8%     |  |
|  |  4. Git             60%      |  |  4. AWS            12%     |  |
|  |  5. Testing         55%      |  |  5. Scrum          15%     |  |
|  +-------------------------------+  +-----------------------------+  |
|                                                                      |
|  +----------------------------------------------------------------+ |
|  |  BRECHA ESTRUCTURAL                                             | |
|  |                                                                 | |
|  |  Skills que el mercado pide pero tu cartera no tiene:          | |
|  |                                                                 | |
|  |  Skill        | Demanda | Disponible | Gap   | Curso local?   | |
|  |  -------------|---------|------------|-------|----------------| |
|  |  Docker       | 78%     | 5%         | -73%  | NO - FALTA     | |
|  |  Kubernetes   | 45%     | 3%         | -42%  | NO - FALTA     | |
|  |  Testing      | 55%     | 25%        | -30%  | SI (2 cursos)  | |
|  |  AWS          | 40%     | 12%        | -28%  | NO - FALTA     | |
|  +----------------------------------------------------------------+ |
|                                                                      |
|  +----------------------------------------------------------------+ |
|  |  CURSOS QUE FALTAN                                              | |
|  |                                                                 | |
|  |  Tu catalogo no tiene formacion para estas brechas:            | |
|  |  - Docker/contenedores (gap -73%, 0 cursos)                    | |
|  |  - Cloud AWS/GCP (gap -28%, 0 cursos)                          | |
|  |  - Kubernetes (gap -42%, 0 cursos)                             | |
|  |                                                                 | |
|  |  Recomendacion: incorporar formacion en estas areas            | |
|  +----------------------------------------------------------------+ |
|                                                                      |
|  [Exportar reporte institucional PDF]                               |
+---------------------------------------------------------------------+
```

**Datos:** Cruza ofertas_dashboard (filtradas por jurisdiccion) × perfiles de la cartera de la OE × cursos_oe.

---

## S3 Registrado: Pantallas empresa con cuenta (Bloque 11°)

**Estado:** Por crear (v2, Etapa 3 del roadmap)
**Nivel:** U-EMPRESA_REGISTRADA

### S3-6: Perfil de puesto reutilizable

```
+---------------------------------------------------------------------+
|  Perfil de Puesto > Desarrollador Backend                            |
|                                                                      |
|  [Guardar]  [Duplicar]  [Eliminar]                                  |
|                                                                      |
|  Titulo: [Desarrollador Backend            ]                        |
|  Ocupacion ESCO: [Desarrollador de software v]                      |
|                                                                      |
|  Skills requeridas (del perfil argentino + personalizadas):         |
|  +----------------------------------------------------------------+ |
|  | [v] Python                    [esencial] [ESCO]                 | |
|  | [v] SQL                       [esencial] [ESCO]                 | |
|  | [v] Docker                    [esencial] [Emergente ARG]        | |
|  | [v] Git                       [deseable] [ESCO]                 | |
|  | [ ] Kubernetes                [deseable] [Emergente ARG]        | |
|  |                                                                 | |
|  | [+ Agregar skill]  [Cargar desde perfil argentino]              | |
|  +----------------------------------------------------------------+ |
|                                                                      |
|  Procesos activos con este perfil: 3                                |
|  Candidatos analizados total: 28                                    |
+---------------------------------------------------------------------+
```

### S3-9: Benchmark del mercado

```
+---------------------------------------------------------------------+
|  Benchmark > Sector: Tecnologia                                      |
|                                                                      |
|  Disponibilidad de skills en el pool:                               |
|                                                                      |
|  Skill         | Tu puesto | Pool MOL | Dificultad                  |
|  --------------|-----------|----------|-----------------------------  |
|  Python        | Esencial  | 45%      | Media (abundante)            |
|  Docker        | Esencial  | 12%      | Alta (escaso)                |
|  Kubernetes    | Deseable  | 5%       | Muy alta (muy escaso)        |
|  SQL           | Esencial  | 62%      | Baja (muy abundante)         |
|                                                                      |
|  Alerta: Docker y Kubernetes tienen tendencia creciente (+35%)      |
|  pero disponibilidad decreciente. Considerar reskilling interno.    |
|                                                                      |
|  [Buscar candidatos con estas skills]                               |
+---------------------------------------------------------------------+
```

---

## Via 4: Captura por formacion/titulo (Bloque 12°)

**Estado:** Por crear (Etapa 4 del roadmap)
**Aplica a:** S1-3 y S2-4 (como 4ta via de captura)

```
+---------------------------------------------------------------------+
|  Via 4: Que estudiaste?                                              |
|                                                                      |
|  [Buscar titulo: tecnicatura en redes, lic. administracion...]      |
|                                                                      |
|  Resultados:                                                        |
|  +----------------------------------------------------------------+ |
|  | Tecnicatura Superior en Redes Informaticas                      | |
|  | UTN — Res. ME 1234/2024                                         | |
|  | Skills derivadas: Redes, TCP/IP, Linux, Ciberseguridad,        | |
|  |   Administracion de servidores, Firewall                       | |
|  | Cobertura: 6 skills                                            | |
|  | [Verificado contra resolucion oficial]                          | |
|  | [Agregar al perfil]                                            | |
|  +----------------------------------------------------------------+ |
|  | Tecnicatura en Redes y Telecomunicaciones                      | |
|  | ISTEEC — Res. ME 5678/2023                                      | |
|  | Skills derivadas: Redes, Telecomunicaciones, VoIP, Fibra optica| |
|  | Cobertura: 5 skills                                            | |
|  | [Verificado]                                                    | |
|  | [Agregar al perfil]                                            | |
|  +----------------------------------------------------------------+ |
|                                                                      |
|  No encontras tu titulo?                                            |
|  [Cargar manualmente: nombre del titulo + institucion]              |
+---------------------------------------------------------------------+
```

**Fuentes de datos:**
- Resoluciones ministeriales de carreras (scraping)
- Catalogos de academias locales (Codehouse, Digital House, etc.)
- Plataformas internacionales (Coursera, edX) — futuro

---

## Wireframes Mobile (Bloque F)

> Asignado a Sergio. Mobile-first para S1 y S3.

### S1 Landing — Mobile (375px)

```
+---------------------------+
| [=] MOL         [Iniciar] |
+---------------------------+
|                           |
|  Mi Futuro Laboral        |
|                           |
|  Descubri tu              |
|  compatibilidad           |
|  laboral                  |
|                           |
| [Evaluar mis skills    >] |
|  (boton full width)       |
|                           |
| +~~~~~~~~~~~~~~~~~~~~~~~+ |
| | Explora ocupaciones   | |
| | Descubri que se pide  | |
| +~~~~~~~~~~~~~~~~~~~~~~~+ |
|                           |
| +~~~~~~~~~~~~~~~~~~~~~~~+ |
| | Compara opciones      | |
| | Analiza lado a lado   | |
| +~~~~~~~~~~~~~~~~~~~~~~~+ |
|                           |
| +~~~~~~~~~~~~~~~~~~~~~~~+ |
| | Evalua compatibilidad | |
| | Carga tu trayectoria  | |
| +~~~~~~~~~~~~~~~~~~~~~~~+ |
|                           |
+---------------------------+
```

Cards en stack vertical (no grid 3 columnas). CTA principal full width.

### S1 Captura skills — Mobile (375px)

```
+---------------------------+
| [<] Paso 2 de 3           |
+---------------------------+
| Juan Perez | Skills: 12   |
+---------------------------+
|                           |
| Como queres cargar?       |
|                           |
| [Por ocupacion        v]  |
| [Por tarea            v]  |
| [Describilo           v]  |
|  (acordeones, 1 abierto)  |
|                           |
| --- Acordeon abierto ---  |
| "En que trabajaste?"      |
| [Buscar ocupacion...   ]  |
|                           |
| + Albanil           [x]  |
| + Electricista       [x]  |
+---------------------------+
| Tus competencias (12)     |
+---------------------------+
| [v] Soldadura     [skill] |
|     "Realizar diversas    |
|      tecnicas de soldeo"  |
|     via: ocupacion        |
+---------------------------+
| [v] Mantenimiento  [skill]|
|     "Actividades de       |
|      mant. preventivo"    |
|     via: ocupacion        |
+---------------------------+
| [?] Lectura planos [skill]|
|     "Leer e interpretar   |
|      planos tecnicos"     |
|     via: ocupacion        |
+---------------------------+
|                           |
| [<- Atras]  [Siguiente ->]|
+---------------------------+
```

Las 3 vias son acordeones (uno abierto a la vez). Panel izquierdo/derecho del desktop → stack vertical. Skills con definicion en cards full width.

### S1 Resultados — Mobile (375px)

```
+---------------------------+
| [<] Paso 3 de 3           |
+---------------------------+
| [Ocupaciones] [Ofertas]   |
| [Capacitacion]            |
|  (tabs scrolleables)      |
+---------------------------+
|                           |
| --- Tab Ocupaciones ---   |
|                           |
| +~~~~~~~~~~~~~~~~~~~~~~~+ |
| | Desarrollador SW      | |
| | [========--] 78%      | |
| | 7/9 esenciales        | |
| | Brechas: 2            | |
| | [Reporte]             | |
| +~~~~~~~~~~~~~~~~~~~~~~~+ |
|                           |
| +~~~~~~~~~~~~~~~~~~~~~~~+ |
| | Analista sistemas     | |
| | [======----] 62%      | |
| | 5/8 esenciales        | |
| | Brechas: 3            | |
| | [Reporte]             | |
| +~~~~~~~~~~~~~~~~~~~~~~~+ |
|                           |
| [Cargar mas]              |
+---------------------------+
```

Tabla → cards apiladas. Cada card: titulo, barra %, esenciales, brechas, boton reporte.

### S3 Reporte QR — Mobile (375px)

```
+---------------------------+
| [MOL] Reporte Compat.     |
+---------------------------+
|                           |
| Juan Perez                |
| Desarrollador SW          |
| ISCO: 2512                |
|                           |
| [==========--] 78%       |
| 7/9 esenciales            |
+---------------------------+
|                           |
| COMPETENCIAS REQUERIDAS   |
| [Personalizar]            |
|                           |
| [v] JavaScript            |
| [v] Python                |
| [v] SQL                   |
| [v] Testing               |
| [v] Git                   |
| [v] REST APIs             |
| [v] Agile                 |
| [x] Docker     FALTANTE   |
| [x] CI/CD      FALTANTE   |
|                           |
| [+ Agregar competencia]   |
+---------------------------+
|                           |
| BRECHAS TECNICAS          |
| - Docker                  |
| - CI/CD                   |
+---------------------------+
|                           |
| Sobre el MOL              |
| [Conocer mas ->]          |
| contacto@oede.gob.ar      |
+---------------------------+
```

Layout 2 columnas (detectadas|brechas) → stack vertical. Mapa de competencias en lista full width.

### Reglas de adaptacion desktop → mobile

| Componente | Desktop | Mobile |
|-----------|---------|--------|
| 3 vias captura | Paneles lado a lado | Acordeones (uno abierto) |
| Skills con definicion | Panel derecho scroll | Cards full width debajo |
| 3 tabs resultados | Tabs en fila | Tabs scrolleables o wrap |
| Cards ocupaciones | Tabla con columnas | Cards apiladas |
| Cards ofertas | Card ancha en fila | Card apilada vertical |
| Transicion dual (A/B) | 2 columnas lado a lado | Stack: A arriba, B abajo |
| Modal generar reporte | Modal centrado 550px | Fullscreen |
| Matriz afinidad | 2 columnas | Stack vertical |
| Sidebar filtros | Panel lateral fijo | Drawer colapsable |
| Botones en fila | Inline | Full width stacked |
