# 2. Arquitectura de Pantallas

> Ultima actualizacion: 2026-03-03
> Versión: 2.4 — Acceso gated, oficina empleo, contenido placeholder

## Referencias

| Documento | Relación |
|-----------|----------|
| [01_MODELO_NEGOCIO](./01_MODELO_NEGOCIO.md) | Define niveles de acceso por tipo de usuario |
| [03_WIREFRAMES/](./03_WIREFRAMES/) | Diseño visual de cada P-XX |
| [04_MODELO_DATOS](./04_MODELO_DATOS.md) | Tablas que usa cada pantalla |
| [05_USER_FLOWS](./05_USER_FLOWS.md) | Flujos que atraviesan pantallas |

## Matriz de Impacto

| Si cambia... | Actualizar... |
|--------------|---------------|
| Ruta de pantalla | 03_WIREFRAMES, 05_USER_FLOWS, middleware.ts |
| Permisos | 01_MODELO_NEGOCIO, 06_SEGURIDAD |
| Layout | 03_WIREFRAMES correspondiente |

---

## Estado Actual (Relevamiento)

### Pantallas Existentes

| ID | Ruta | Estado | Notas |
|----|------|--------|-------|
| - | `/` | ✅ Funcional | Se moverá a `/dashboard` |
| - | `/login` | ✅ Funcional | - |
| - | `/skills` | ✅ Funcional | 4 tabs |
| - | `/admin` | ✅ Funcional | Estado sistema |
| - | `/admin/usuarios` | ⚠️ Parcial | CRUD: C+R+U (falta eliminar) |
| - | `/admin/issues` | ✅ Funcional | - |
| - | `/admin/skills` | ✅ Funcional | 6 tabs |
| - | `/admin/scraping` | ⚠️ Solo lectura | No ejecuta |
| - | `/admin/metricas` | ✅ Funcional | - |
| - | `/admin/logs` | ⚠️ Prueba | Datos de prueba |
| - | `/admin/configuracion` | ✅ Fase 1 | Solo lectura - [11_CONFIGURACION](./11_CONFIGURACION_ADMIN.md) |
| P-31 | `/admin/laboratorio` | ✅ Funcional | Landing indicadores experimentales |
| P-31a | `/admin/laboratorio/tension-demanda` | ✅ Funcional | V-16: scatter chart + tabla + metodología |

### Componentes Existentes

- **Filtros globales:** Territorio, provincia, fechas, ocupaciones, permanencia (baja/media/alta), tensión de demanda (4 cuadrantes)
- **Visualizaciones:** Sunburst ESCO, gráficos Recharts, tablas
- **Sistema de tabs:** Implementado en Home y Skills
- **Autenticación:** Supabase Auth con roles
- **AnimatedNav auth-aware:** Detecta sesión. Logueado → nombre + "Ir al Dashboard" + "Cerrar Sesión". No logueado → "Iniciar Sesión" + "Registrarse".
- **Issues/Feedback:** FAB flotante + drawer + página admin

---

## Arquitectura Skills Intelligence v5

> **Documento fuente:** `docs/MOL_Skills_Intelligence.docx` (v5.0) + `docs/mol_screens_v5.html` (32 wireframes)
> **Decisión (2026-03-20):** Se adopta la arquitectura de 3 servicios como marco para la evolución de Skills Intelligence. Las pantallas existentes del dashboard (P-01 a P-31a) se mantienen. Las pantallas de Skills Intelligence (S1/S2/S3) se agregan como un módulo paralelo.

### Motor y Capacidades

El sistema se estructura como un **motor con 6 capacidades** expuestas a través de **3 servicios**:

| Capacidad | Descripción | Servicios |
|-----------|-------------|-----------|
| Cap. 1 — Diagnóstico | Perfil de skills desde 4 vías (ocupación, tarea, texto libre, formación/título) | S1, S2, S3 |
| Cap. 2 — Matching oferta-demanda | Cruzar perfiles con vacantes en ambas direcciones | S1, S2, S3 |
| Cap. 3 — Matching formación | Brechas cruzadas con oferta de cursos, impacto medible | S1, S2, S3 |
| Cap. 4 — Inteligencia de mercado | Tendencias, escasez, brechas por sector/región/tiempo | S2, S3 |
| Cap. 5 — Reporte y certificación | PDF+QR → validación OE → certificación MOL (evolución) | S1, S2, S3 |
| Cap. 6 — Gestión de pools | Bases de personas, vacantes, cursos (propias y terceros) | S1, S2, S3 |

### Tres Servicios (pantallas Skills Intelligence)

| Servicio | Usuario | Pantallas | Estado |
|----------|---------|-----------|--------|
| S1 — Mi Futuro Laboral | Trabajador independiente | 9 (MVP) | Landing existe, flujo por crear |
| S2 — Oficina de Empleo | Técnico/coordinador OE | 11 (MVP) | Hub wireframe, funcionalidad por crear |
| S3 — Empresas | Reclutador/RRHH | 12 (3 MVP libre, 9 v2) | Reporte QR por crear, resto v2 |

**Wireframes interactivos:** `docs/mol_screens_v5.html` (abrir en navegador para ver las 32 pantallas)

### S1 — Mi Futuro Laboral (9 pantallas)

| # | Pantalla | Capacidad | Estado |
|---|----------|-----------|--------|
| S1-1 | Landing | — | ✅ Existe (/mi-futuro-laboral) |
| S1-2 | Onboarding | — | ⬜ Por crear |
| S1-3 | Primer trabajo (4 vías captura) | Cap. 1 | ⚠️ Parcial (vía 1 existe) |
| S1-4 | Skills derivadas | Cap. 1 + 2 | ✅ Existe (MySkillsSearch) |
| S1-5 | Enriquecer perfil | Cap. 1 | ⬜ Por crear |
| S1-6 | Resultados (ocupaciones + ofertas) | Cap. 2 | ⚠️ Parcial (ocupaciones existe) |
| S1-7 | Elegir destino (transición) | Cap. 2 | ⬜ Por crear |
| S1-8 | Brecha específica + capacitación | Cap. 2 + 3 | ⬜ Por crear |
| S1-9 | PDF + QR | Cap. 5 | ⬜ Por crear |

### S2 — Oficina de Empleo (11 pantallas)

| # | Pantalla | Capacidad | Estado |
|---|----------|-----------|--------|
| S2-1 | Importar datos (Excel/CSV) | Cap. 6 | ⬜ Por crear |
| S2-2 | Login institucional | — | ⬜ Por crear |
| S2-3 | Panel de casos | Cap. 2 + 6 | ⬜ Por crear |
| S2-4 | Perfil del caso (2 cols: datos + tabs) | Cap. 1 + 2 | ⚠️ Wireframe (P-33) |
| S2-5 | Nota del técnico | Cap. 1 | ⬜ Por crear |
| S2-6 | Matching con vacantes | Cap. 2 | ⬜ Por crear |
| S2-7 | Gestión de vacantes (empresa trae puesto) | Cap. 2 | ⬜ Por crear |
| S2-8 | Formación (catálogo OE + impacto) | Cap. 3 | ⬜ Por crear |
| S2-9 | Comparar casos | Cap. 2 + 6 | ⬜ Por crear |
| S2-10 | Inteligencia local | Cap. 4 | ⬜ Por crear (v2) |
| S2-11 | Exportar diagnóstico (PDF institucional) | Cap. 5 | ⬜ Por crear |

### S3 — Empresas (12 pantallas)

| # | Pantalla | Nivel | Capacidad | Estado |
|---|----------|-------|-----------|--------|
| S3-1 | Acceso vía QR | Libre MVP | Cap. 5 | ⬜ Por crear |
| S3-2 | Reporte de compatibilidad | Libre MVP | Cap. 2 + 5 | ⬜ Por crear (= P-35) |
| S3-3 | Personalizar competencias | Libre MVP | Cap. 2 | ⬜ Por crear |
| S3-4 | Landing empresas | Registrado v2 | — | ⬜ Futuro |
| S3-5 | Dashboard empresa | Registrado v2 | Cap. 6 | ⬜ Futuro |
| S3-6 | Perfil de puesto | Registrado v2 | Cap. 6 | ⬜ Futuro |
| S3-7 | Historial candidatos | Registrado v2 | Cap. 6 | ⬜ Futuro |
| S3-8 | Comparar candidatos | Registrado v2 | Cap. 2 + 6 | ⬜ Futuro |
| S3-9 | Benchmark del mercado | Registrado v2 | Cap. 4 | ⬜ Futuro |
| S3-10 | Buscar en pool | Registrado v2 | Cap. 2 + 6 | ⬜ Futuro |
| S3-11 | Reskilling plantilla | Registrado v2 | Cap. 1 + 3 | ⬜ Futuro |
| S3-12 | Inteligencia sectorial | Registrado v2 | Cap. 4 | ⬜ Futuro |

> **Pendiente:** Seguridad y perfiles de usuario para los 3 servicios (próximo paso de planificación).

---

## Árbol de Navegación — Dashboard + Plataforma

> Las pantallas del dashboard de análisis (P-01 a P-31a) coexisten con los 3 servicios de Skills Intelligence. El dashboard es para analistas/suscriptores; los servicios S1/S2/S3 son para trabajadores, OEs y empresas.

```
MOL Platform
│
├── PÚBLICO (sin auth)
│   ├── / ────────────────── P-01 Landing Page
│   ├── /precios ─────────── P-02 Precios
│   ├── /informes ────────── P-03 Informes (preview para visitantes)
│   ├── /login ───────────── P-04 Login
│   ├── /registro ────────── P-05 Registro (libre, sin plan)
│   ├── /skills ──────────── (existente, versión pública)
│   └── /reporte/:token ──── S3-1/S3-2 Reporte Compatibilidad (público, sin auth)
│
├── S1 — MI FUTURO LABORAL (público o auth mínima)
│   ├── /mi-futuro-laboral ──── S1-1 Landing (existe)
│   ├── /mi-futuro-laboral/onboarding ── S1-2 Onboarding
│   ├── /mi-futuro-laboral/perfil ────── S1-3 a S1-5 (captura + enriquecer)
│   ├── /mi-futuro-laboral/resultados ── S1-6 a S1-8 (ocupaciones + ofertas + brecha)
│   └── /mi-futuro-laboral/reporte ───── S1-9 PDF + QR
│
├── S2 — OFICINA DE EMPLEO (auth + rol oficina_empleo)
│   ├── /oficina-empleo ──────── S2-1 Importar datos / Hub
│   ├── /oficina-empleo/casos ── S2-3 Panel de casos
│   ├── /oficina-empleo/caso/:id S2-4/S2-5 Perfil + nota técnico
│   ├── /oficina-empleo/vacantes S2-6/S2-7 Matching + gestión vacantes
│   ├── /oficina-empleo/formacion S2-8 Catálogo cursos OE
│   ├── /oficina-empleo/comparar S2-9 Comparar casos
│   ├── /oficina-empleo/inteligencia S2-10 Inteligencia local (v2)
│   └── /oficina-empleo/exportar S2-11 PDF institucional
│
├── S3 — EMPRESAS
│   ├── /reporte/:token ──────── S3-1/S3-2/S3-3 QR + Reporte + Personalizar (libre)
│   ├── /empresas ────────────── S3-4 Landing empresas (v2)
│   ├── /empresas/dashboard ──── S3-5 Dashboard (v2)
│   ├── /empresas/puestos ────── S3-6 Perfiles de puesto (v2)
│   ├── /empresas/candidatos ─── S3-7/S3-8 Historial + comparar (v2)
│   ├── /empresas/benchmark ──── S3-9 Benchmark mercado (v2)
│   ├── /empresas/pool ──────── S3-10 Buscar en pool (v2)
│   ├── /empresas/reskilling ─── S3-11 Reskilling plantilla (v2)
│   └── /empresas/inteligencia ─ S3-12 Inteligencia sectorial (v2)
│
├── REGISTRADO (auth, sin acceso a tablero)
│   ├── /contenido ──────────── P-26 Informes y Notas (contenido completo)
│   ├── /contenido/:slug ────── P-27 Detalle de Contenido
│   └── /solicitar-acceso ───── P-28 Solicitar Acceso al Tablero
│
├── CHECKOUT (auth + aprobación MOL)
│   ├── /checkout ────────── P-06 Checkout
│   ├── /checkout/exito ──── P-07 Éxito
│   └── /checkout/cancelado  P-08 Cancelado
│
├── TABLERO DE ANÁLISIS (auth + trial/suscriptor/institucional)
│   ├── /dashboard ───────── P-09 Dashboard
│   │   ├── Tab: Panorama General
│   │   ├── Tab: Requerimientos
│   │   └── Tab: Ofertas Laborales
│   ├── /dashboard/skills ── P-10 Skills (admin analytics)
│   ├── /dashboard/empresas  P-11 Análisis Empresas
│   ├── /dashboard/reportes  P-12 Reportes
│   └── /dashboard/alertas   P-13 Alertas
│
├── CUENTA (auth)
│   ├── /cuenta ──────────── P-14 Mi Cuenta (Perfil)
│   ├── /cuenta/suscripcion  P-15 Suscripción
│   └── /cuenta/facturacion  P-16 Facturación
│
└── ADMIN (auth + rol admin)
    ├── /admin ───────────── P-17 Centro de Control (Bloque J)
    ├── /admin/scraping ──── P-21 Scraping Admin (Bloque H)
    │   ├── /comandos        Comandos VPS
    │   └── /dinamica        Configuración dinámica
    │
    ├── /admin/procesamiento ── FÁBRICA DE PROCESAMIENTO (Bloques I+G)
    │   ├── /fabrica ────── P-42 Fábrica (vista dual: fabricación + mejora continua)
    │   │   ├── /nlp ────── P-47 Detalle NLP (modelo Ollama, métricas, campos)
    │   │   ├── /validacion-nlp ── P-48 Detalle Gate NLP (reglas, errores, evolución)
    │   │   ├── /skills ─── P-49 Detalle Skills (modelo BGE-M3, umbral, extracción)
    │   │   ├── /matching ─ P-50 Detalle Matching (método, scores, distribución)
    │   │   ├── /validacion-matching P-51 Detalle Gate Matching (errores, issues)
    │   │   ├── /tareas ─── P-52 Tareas canónicas (frecuencias, nuevas)
    │   │   └── /canonizacion P-53 Editor canonización (skills + tareas)
    │   ├── /diccionarios ─ P-43 Diccionarios (6 tabs: reglas, NLP, sinón, oficios, skills, limpieza)
    │   ├── /catalogo ───── P-44 Catálogo MOL (curación skills/ocupaciones argentinas)
    │   ├── /perfil-argentino P-45 Perfil Argentino (publicación versionada)
    │   └── /validacion ─── P-46 Validación Humana (estación del analista)
    │
    ├── /admin/laboratorio ─ P-31 Laboratorio de Indicadores Experimentales
    │   └── /tension-demanda P-31a Detalle Tensión de Demanda (V-16)
    ├── /admin/skills ────── P-20 Skills Intelligence
    ├── /admin/issues ────── P-19 Issues
    ├── /admin/usuarios ──── P-18 Usuarios
    ├── /admin/solicitudes ─ P-29 Gestión Solicitudes Acceso
    ├── /admin/organizaciones P-37 Gestión Organizaciones
    ├── /admin/metricas ──── P-22 Métricas
    ├── /admin/configuracion P-24 Configuración
    ├── /admin/contenidos ── P-30 Gestión Contenidos (CMS)
    └── /admin/arquitectura  P-25 Arquitectura Sistema
```

---

## Lista de Pantallas (P-*)

### Públicas

| ID | Ruta | Nivel | Estado | Wireframe |
|----|------|-------|--------|-----------|
| P-01 | `/` | U-VISITANTE | Por crear | [publicas.md#p-01](./03_WIREFRAMES/publicas.md#p-01-landing-page) |
| P-02 | `/precios` | U-VISITANTE | Por crear | [publicas.md#p-02](./03_WIREFRAMES/publicas.md#p-02-precios) |
| P-03 | `/informes` | U-VISITANTE | Por crear | [publicas.md#p-03](./03_WIREFRAMES/publicas.md#p-03-informes) |
| P-04 | `/login` | U-VISITANTE | ✅ Existe | [publicas.md#p-04](./03_WIREFRAMES/publicas.md#p-04-login) |
| P-05 | `/registro` | U-VISITANTE | Por crear | [publicas.md#p-05](./03_WIREFRAMES/publicas.md#p-05-registro) |

### Contenido (Registrados)

| ID | Ruta | Nivel | Estado | Wireframe |
|----|------|-------|--------|-----------|
| P-26 | `/contenido` | U-REGISTRADO | ✅ Placeholder (2026-03-03) | [contenido.md#p-26](./03_WIREFRAMES/contenido.md#p-26-informes-y-notas) |
| P-27 | `/contenido/:slug` | U-REGISTRADO | Por crear (requiere CMS) | [contenido.md#p-27](./03_WIREFRAMES/contenido.md#p-27-detalle) |
| P-28 | `/solicitar-acceso` | U-REGISTRADO | ✅ Funcional (2026-03-03) | [contenido.md#p-28](./03_WIREFRAMES/contenido.md#p-28-solicitar-acceso) |

### Checkout

| ID | Ruta | Nivel | Estado | Wireframe |
|----|------|-------|--------|-----------|
| P-06 | `/checkout` | U-TRIAL (aprobado) | Por crear | [checkout.md#p-06](./03_WIREFRAMES/checkout.md#p-06-checkout) |
| P-07 | `/checkout/exito` | U-TRIAL (aprobado) | Por crear | [checkout.md#p-07](./03_WIREFRAMES/checkout.md#p-07-exito) |
| P-08 | `/checkout/cancelado` | U-TRIAL (aprobado) | Por crear | [checkout.md#p-08](./03_WIREFRAMES/checkout.md#p-08-cancelado) |

### Tablero (Dashboard)

| ID | Ruta | Nivel | Estado | Wireframe |
|----|------|-------|--------|-----------|
| P-09 | `/dashboard` | U-TRIAL / U-SUSCRIPTOR | ✅ Mover | [suscriptor.md#p-09](./03_WIREFRAMES/suscriptor.md#p-09-dashboard) |
| P-10 | `/dashboard/skills` | U-TRIAL / U-SUSCRIPTOR | ✅ Mover | [suscriptor.md#p-10](./03_WIREFRAMES/suscriptor.md#p-10-skills) |
| P-11 | `/dashboard/empresas` | U-SUSCRIPTOR | Por crear | [suscriptor.md#p-11](./03_WIREFRAMES/suscriptor.md#p-11-empresas) |
| P-12 | `/dashboard/reportes` | U-SUSCRIPTOR | Por crear | [suscriptor.md#p-12](./03_WIREFRAMES/suscriptor.md#p-12-reportes) |
| P-13 | `/dashboard/alertas` | U-SUSCRIPTOR | Por crear | [suscriptor.md#p-13](./03_WIREFRAMES/suscriptor.md#p-13-alertas) |

**Componentes de P-09 (Dashboard):**

| Área | Componentes |
|------|-------------|
| **Sidebar** | Filtros: Territorio, Provincia, Fecha, Ocupación, Permanencia (baja/media/alta), **Tensión de Demanda** (Crítica/Urgente/Pasiva/Fluida) |
| **Tab Panorama** | KPIs + Evolución + Top Ocupaciones + **Scatter Plot Tensión** + Distribución Geográfica |
| **Tab Requerimientos** | Sin cambios de layout |
| **Tab Ofertas** | Sin cambios de layout (filtrado por tensión si activo desde sidebar) |

> **Scatter Plot Tensión:** Eje X = Insistencia, Eje Y = Persistencia, tamaño = total posiciones. Ver [suscriptor.md](./03_WIREFRAMES/suscriptor.md#scatter-plot-tensión-de-demanda) y [V-16](./08_PROPUESTA_VALOR.md#v-16-indicador-de-tensión-de-demanda).

### Oficina de Empleo

| ID | Ruta | Nivel | Estado | Wireframe |
|----|------|-------|--------|-----------|
| P-32 | `/oficina-empleo` | U-OFICINA_EMPLEO | ✅ Wireframe (2026-03-03) | Hub con 3 cards |
| P-33 | `/oficina-empleo/perfil` | U-OFICINA_EMPLEO | ✅ Wireframe (2026-03-03) | Form deshabilitado + skeleton |
| P-34 | `/oficina-empleo/ofertas` | U-OFICINA_EMPLEO | ✅ Wireframe (2026-03-03) | Tabla skeleton |

> **Nota:** Las 3 páginas son wireframes estáticos con badge "PRÓXIMAMENTE". La funcionalidad real (perfiles de trabajadores, matching, ofertas coincidentes) está pendiente.

### Reporte Compatibilidad (Público)

| ID | Ruta | Nivel | Estado | Wireframe |
|----|------|-------|--------|-----------|
| P-35 | `/reporte/:token` | PÚBLICO (sin auth) | ⬜ Por crear | [oficina-empleo.md#p-35](./03_WIREFRAMES/oficina-empleo.md#p-35-reporte-compatibilidad) |

> **V-17:** Página pública accesible via QR desde carta PDF. El reclutador ve mapa de competencias, matriz de afinidad y puede editar competencias para recalcular en tiempo real. Protegida por token UUID con expiración. Ver [08_PROPUESTA_VALOR](./08_PROPUESTA_VALOR.md#v-17-reporte-de-compatibilidad-laboral-para-empresas).

**Modificación P-10 (paso 3 — resultados):** Se rediseña con 3 sub-tabs:
- **Tab Ocupaciones compatibles:** Ranking por % afinidad + botón "Reporte" por fila (existe parcial, agregar botón).
- **Tab Ofertas laborales (nuevo):** Ofertas reales de `ofertas_dashboard` filtradas por ocupaciones compatibles, con gap personalizado y botón "Reporte" vinculado a oferta específica.
- **Tab Capacitación (nuevo):** Cursos sugeridos según brechas técnicas. Fuente: Portal Capacitación CABA (2,255 cursos). Incluye sugerencias de transición laboral.

**Rediseño Paso 2 (captura de competencias):** El paso 2 de "Mis Skills" se rediseña con 3 vías de entrada combinables (por ocupación, por tarea/habilidad, texto libre) y definiciones ESCO visibles. Aplica tanto a P-10 como a P-33. Ver wireframe en [oficina-empleo.md](./03_WIREFRAMES/oficina-empleo.md#captura-de-competencias-paso-2--rediseño-con-3-vias-de-entrada).

**Taxonomía:** La evaluación de compatibilidad usa el **Perfil Consolidado Argentino** (tabla `esco_argentino`: ESCO + emergentes aprobadas), no ESCO genérico. El reporte registra la versión del perfil usado.

**Dos caminos de entrada (V-17):**
- Camino A: `/mi-futuro-laboral` (existe como hub) → `/skills?tab=myskills` → trabajador se autoevalúa
- Camino B: `/oficina-empleo` (wireframe) → gestor carga perfil del trabajador

### Cuenta

| ID | Ruta | Nivel | Estado | Wireframe |
|----|------|-------|--------|-----------|
| P-14 | `/cuenta` | U-REGISTRADO | Por crear | [cuenta.md#p-14](./03_WIREFRAMES/cuenta.md#p-14-perfil) |
| P-15 | `/cuenta/suscripcion` | U-REGISTRADO | Por crear | [cuenta.md#p-15](./03_WIREFRAMES/cuenta.md#p-15-suscripcion) |
| P-16 | `/cuenta/facturacion` | U-SUSCRIPTOR | Por crear | [cuenta.md#p-16](./03_WIREFRAMES/cuenta.md#p-16-facturacion) |

### Admin

| ID | Ruta | Nivel | Estado | Wireframe |
|----|------|-------|--------|-----------|
| P-17 | `/admin` | U-ADMIN | ✅ Existe | [admin.md#p-17](./03_WIREFRAMES/admin.md#p-17-dashboard) |
| P-18 | `/admin/usuarios` | U-ADMIN | ⚠️ Parcial (CRUD: C+R+U) | [admin.md#p-18](./03_WIREFRAMES/admin.md#p-18-usuarios) |
| P-29 | `/admin/solicitudes` | U-ADMIN | ✅ Funcional (2026-03-03) | [admin.md#p-29](./03_WIREFRAMES/admin.md#p-29-solicitudes) |
| P-19 | `/admin/issues` | U-ADMIN | ✅ Existe | [admin.md#p-19](./03_WIREFRAMES/admin.md#p-19-issues) |
| P-20 | `/admin/skills` | U-ADMIN | ✅ Existe | [admin.md#p-20](./03_WIREFRAMES/admin.md#p-20-skills) |
| P-21 | `/admin/scraping` | U-ADMIN | ⚠️ Lectura | [admin.md#p-21](./03_WIREFRAMES/admin.md#p-21-scraping) |
| P-22 | `/admin/metricas` | U-ADMIN | ✅ Existe | [admin.md#p-22](./03_WIREFRAMES/admin.md#p-22-metricas) |
| P-23 | `/admin/logs` | U-ADMIN | ⚠️ Prueba | [admin.md#p-23](./03_WIREFRAMES/admin.md#p-23-logs) |
| P-24 | `/admin/configuracion` | U-ADMIN | ✅ Fase 1 | [11_CONFIGURACION](./11_CONFIGURACION_ADMIN.md) |
| P-30 | `/admin/contenidos` | U-ADMIN | Por crear | [admin.md#p-30](./03_WIREFRAMES/admin.md#p-30-contenidos) |
| P-25 | `/admin/arquitectura` | U-ADMIN | ✅ Existe (fixes v1.1) | [10_OBSERVABILIDAD](./10_OBSERVABILIDAD.md), [admin.md#p-25](./03_WIREFRAMES/admin.md#p-25-admin-arquitectura-adminarquitectura) |
| P-31 | `/admin/laboratorio` | U-ADMIN | ✅ Existe | Staging de indicadores experimentales |
| P-31a | `/admin/laboratorio/tension-demanda` | U-ADMIN | ✅ Existe | Detalle V-16: scatter chart + tabla + metodología |
| P-42 | `/admin/procesamiento/fabrica` | U-ADMIN | Planificado | Fábrica: vista dual fabricación + mejora continua. [Wireframe](./03_WIREFRAMES/fabrica-procesamiento.md#3-wireframe-fábrica-vista-principal) |
| P-43 | `/admin/procesamiento/diccionarios` | U-ADMIN | Planificado | Diccionarios: 6 tabs editores config unificados. [Wireframe](./03_WIREFRAMES/fabrica-procesamiento.md#4-wireframe-diccionarios-herramientas-compartidas) |
| P-44 | `/admin/procesamiento/catalogo` | U-ADMIN | ✅ Existe | Catálogo MOL: curación skills/ocupaciones argentinas. [Wireframe](./03_WIREFRAMES/fabrica-procesamiento.md#5-wireframe-catálogo-mol-curación--input-de-mejora) |
| P-45 | `/admin/procesamiento/perfil-argentino` | U-ADMIN | ✅ Existe | Perfil Argentino: publicación versionada. [Wireframe](./03_WIREFRAMES/fabrica-procesamiento.md#6-wireframe-perfil-argentino-publicación--output-de-mejora) |
| P-46 | `/admin/procesamiento/validacion` | U-ADMIN | ✅ Existe | Validación humana: 3 paneles + wizard + auto-issues. [Wireframe](./03_WIREFRAMES/fabrica-procesamiento.md#7-wireframe-validación-estación-del-analista) |
| P-47 | `/admin/procesamiento/fabrica/nlp` | U-ADMIN | Planificado | Detalle NLP: modelo Ollama, métricas extracción, completitud campos |
| P-48 | `/admin/procesamiento/fabrica/validacion-nlp` | U-ADMIN | Planificado | Gate NLP: 51 reglas, errores por tipo/severidad, evolución |
| P-49 | `/admin/procesamiento/fabrica/skills` | U-ADMIN | Planificado | Skills: modelo BGE-M3/LoRA, umbral, % extracción, canonización |
| P-50 | `/admin/procesamiento/fabrica/matching` | U-ADMIN | Planificado | Matching v3.5.4: método, scores, distribución regla/semántico |
| P-51 | `/admin/procesamiento/fabrica/validacion-matching` | U-ADMIN | Planificado | Gate Matching: errores, issues, tasa por run |
| P-52 | `/admin/procesamiento/fabrica/tareas` | U-ADMIN | Planificado | Tareas canónicas: frecuencias, nuevas sin canónico |
| P-53 | `/admin/procesamiento/fabrica/canonizacion` | U-ADMIN | Planificado | Editor canonización: skills ESCO→canónicas + tareas canónicas |

---

## Resumen

### Pantallas Dashboard + Plataforma (existentes)

| Categoría | Total | Existentes | Por crear |
|-----------|-------|------------|-----------|
| Públicas | 6 | 1 | 5 |
| Contenido | 3 | 1 (placeholder) | 2 |
| Checkout | 3 | 0 | 3 |
| Tablero análisis | 5 | 2 | 3 |
| Cuenta | 3 | 0 | 3 |
| Admin | 13 | 10 | 3 |
| **Subtotal dashboard** | **33** | **14** | **19** |

### Pantallas Skills Intelligence v5 (nuevas — 3 servicios)

| Servicio | Total | MVP | v2 | Existente |
|----------|-------|-----|-----|-----------|
| S1 — Mi Futuro Laboral | 9 | 9 | 0 | 1 (landing) |
| S2 — Oficina de Empleo | 11 | 10 | 1 | 0 (wireframes) |
| S3 — Empresas | 12 | 3 | 9 | 0 |
| **Subtotal Skills Int.** | **32** | **22** | **10** | **1** |

| **TOTAL PLATAFORMA** | **65** | | | **15 existentes** |

---

## Permisos por Ruta

### Niveles de Acceso

| Nivel | Descripción | Ejemplo |
|-------|-------------|---------|
| PÚBLICO | Sin autenticación | Landing, precios, informes (preview) |
| REGISTRADO | Auth básica (registro libre) | Contenido completo, solicitar acceso |
| GATED | Auth + aprobación MOL + trial/suscripción | Dashboard, exports, alertas |
| ADMIN | Auth + rol admin | Panel admin, gestión accesos, CMS |

### Middleware de Autenticación

```typescript
// middleware.ts (propuesto v2.0)

const PUBLIC_ROUTES = ['/', '/precios', '/informes', '/login', '/registro', '/skills', '/reporte'];

const REGISTERED_ROUTES = ['/contenido', '/solicitar-acceso', '/cuenta'];

const GATED_ROUTES = ['/dashboard', '/checkout'];

const ADMIN_ROUTES = ['/admin'];

const SUSCRIPTOR_ONLY = [
  '/dashboard/empresas',
  '/dashboard/reportes',
  '/dashboard/alertas',
  '/cuenta/facturacion'
];

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const session = getSession(request);

  // Rutas públicas: permitir siempre
  if (PUBLIC_ROUTES.some(r => pathname.startsWith(r))) {
    return NextResponse.next();
  }

  // Sin sesión: redirect a login
  if (!session) {
    return NextResponse.redirect('/login?next=' + pathname);
  }

  // Rutas admin: verificar rol
  if (ADMIN_ROUTES.some(r => pathname.startsWith(r))) {
    if (session.user.role !== 'admin') {
      return NextResponse.redirect('/contenido');
    }
  }

  // Rutas gated (tablero): verificar trial/suscriptor/institucional
  if (GATED_ROUTES.some(r => pathname.startsWith(r))) {
    const nivel = session.user.nivel;
    if (!['trial', 'suscriptor', 'institucional'].includes(nivel)) {
      return NextResponse.redirect('/solicitar-acceso');
    }
  }

  // Rutas solo suscriptor: excluir trial
  if (SUSCRIPTOR_ONLY.some(r => pathname.startsWith(r))) {
    const nivel = session.user.nivel;
    if (!['suscriptor', 'institucional'].includes(nivel)) {
      return NextResponse.redirect('/cuenta/suscripcion?upgrade=true');
    }
  }

  return NextResponse.next();
}
```

### Matriz de Acceso por Ruta

| Ruta | Visitante | Registrado | Trial | Suscriptor | Institucional | Admin |
|------|-----------|------------|-------|------------|---------------|-------|
| `/` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `/precios` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `/informes` | ✓ (preview) | ✓ (preview) | ✓ | ✓ | ✓ | ✓ |
| `/contenido` | ✗ → registro | ✓ | ✓ | ✓ | ✓ | ✓ |
| `/solicitar-acceso` | ✗ → registro | ✓ | - | - | - | - |
| `/dashboard` | ✗ → login | ✗ → solicitar | ✓ | ✓ | ✓ | ✓ |
| `/dashboard/empresas` | ✗ | ✗ | ✗ → upgrade | ✓ | ✓ | ✓ |
| `/cuenta` | ✗ → login | ✓ | ✓ | ✓ | ✓ | ✓ |
| `/admin` | ✗ | ✗ | ✗ | ✗ | ✗ | ✓ |

---

## Estructura de Archivos Propuesta

```
app/
├── (public)/
│   ├── page.tsx              # P-01 Landing
│   ├── precios/page.tsx      # P-02
│   ├── informes/page.tsx     # P-03
│   └── registro/page.tsx     # P-05
├── reporte/
│   └── [token]/page.tsx     # P-35 Reporte Compatibilidad (público)
├── login/page.tsx            # P-04 (existente)
├── (contenido)/
│   ├── layout.tsx            # Layout registrados (navbar con cuenta)
│   ├── contenido/
│   │   ├── page.tsx          # P-26 Lista informes/notas
│   │   └── [slug]/page.tsx   # P-27 Detalle contenido
│   └── solicitar-acceso/
│       └── page.tsx          # P-28 Solicitud acceso tablero
├── (checkout)/
│   ├── checkout/page.tsx     # P-06
│   ├── checkout/exito/page.tsx    # P-07
│   └── checkout/cancelado/page.tsx # P-08
├── dashboard/
│   ├── layout.tsx            # Sidebar tablero
│   ├── page.tsx              # P-09 (mover de `/`)
│   ├── skills/page.tsx       # P-10 (mover de `/admin/skills`)
│   ├── empresas/page.tsx     # P-11
│   ├── reportes/page.tsx     # P-12
│   └── alertas/page.tsx      # P-13
├── cuenta/
│   ├── page.tsx              # P-14
│   ├── suscripcion/page.tsx  # P-15
│   └── facturacion/page.tsx  # P-16
└── admin/                    # P-17 a P-25 (existente)
    ├── solicitudes/page.tsx  # P-29 (nuevo)
    ├── contenidos/page.tsx   # P-30 (nuevo)
    └── laboratorio/
        ├── page.tsx          # P-31 Landing indicadores experimentales
        └── tension-demanda/
            └── page.tsx      # P-31a Detalle V-16
```

---

## Responsive — Mobile y Tablet (Bloque F)

> **Estado:** Pendiente. El sistema actual es desktop-first. Para S1 y S3 el acceso mobile es crítico.
> **Asignado a:** Sergio (puro frontend)

### Estrategia por servicio

| Servicio | Dispositivo principal | Estrategia | Prioridad |
|----------|----------------------|------------|-----------|
| S1 — Mi Futuro Laboral | **Mobile** (trabajador en búsqueda) | Mobile-first: diseñar para 375px, escalar a desktop | ALTA |
| S3 libre — Reporte QR | **Mobile** (reclutador escanea con teléfono) | Mobile-first: reporte legible en pantalla chica | ALTA |
| S2 — Oficina de Empleo | **Tablet** (técnico en atención presencial) | Tablet-friendly: layout 2 columnas → stack | MEDIA |
| Dashboard análisis | **Desktop** (analista en oficina) | Mantener como está, mejoras menores | BAJA |

### Breakpoints

| Breakpoint | Ancho | Dispositivo | Tailwind |
|-----------|-------|-------------|----------|
| Mobile | 375px | Celular | Default (sin prefijo) |
| Tablet | 768px | Tablet / iPad | `md:` |
| Desktop | 1280px | Monitor | `lg:` / `xl:` |

### Reglas de adaptación

| Elemento desktop | En mobile se convierte en |
|-----------------|--------------------------|
| Tabla con columnas | Cards apiladas (stack vertical) |
| Layout 2 columnas | Stack vertical (perfil arriba, datos abajo) |
| Sidebar filtros | Drawer colapsable (botón "Filtros") |
| Tabs horizontales | Tabs scrolleables o select dropdown |
| Gráficos anchos | Scroll horizontal o simplificación |
| Botones en fila | Stack vertical, ancho completo |
| Modales anchos | Fullscreen en mobile |

### Criterios de accesibilidad

- Touch target mínimo: **44x44px** (estándar WCAG 2.5.5)
- Sin scroll horizontal en ningún breakpoint
- Texto mínimo: **14px** en mobile (legible sin zoom)
- Contraste: mantener ratios existentes (ya pasan WCAG AA)
- Focus visible en navegación por teclado (ya implementado via Radix)

### Pantallas prioritarias para mobile

| # | Pantalla | Por qué es crítica en mobile |
|---|----------|------------------------------|
| S1-1 | Landing Mi Futuro Laboral | Primera impresión del trabajador |
| S1-2 | Onboarding | Input de nombre — tiene que ser rápido |
| S1-3 | Captura skills (4 vías) | La más compleja: búsqueda + resultados + checkboxes |
| S1-6 | Resultados (3 tabs) | Cards de ocupaciones/ofertas/cursos |
| S1-9 | PDF + QR | Botón descargar + vista previa |
| S3-2 | Reporte compatibilidad | Lo ve el reclutador en la entrevista con el celular |
| S3-3 | Personalizar competencias | Editar skills en pantalla chica |

---

## Historial de Cambios

| Fecha | Versión | Cambio |
|-------|---------|--------|
| 2026-02-05 | 1.0 | Arquitectura SaaS clásica (Free/Pro/Enterprise), 25 pantallas |
| 2026-02-07 | 2.0 | Modelo hibrido: nivel REGISTRADO, area `/contenido`, `/solicitar-acceso`, admin `/solicitudes` y `/contenidos` (CMS). Total 30 pantallas |
| 2026-02-08 | 2.0.1 | P-25 code review: 7 fixes aplicados (Tailwind, env vars, error handling, sidebar dup, labels, imports) |
| 2026-02-11 | 2.1 | Filtros permanencia y tensión de demanda en sidebar, componentes P-09 (scatter plot tensión) |
| 2026-02-23 | 2.2 | AnimatedNav auth-aware (sesión → dashboard/logout), P-18 CRUD: C+R+U (editar rol) |
| 2026-02-26 | 2.3 | P-31 Laboratorio de Indicadores Experimentales + P-31a Tensión de Demanda (V-16). Staging admin para indicadores antes de dashboard público. Total 32 pantallas |
| 2026-03-03 | 2.4 | P-26 placeholder, P-28+P-29 funcionales, P-32/P-33/P-34 oficina empleo wireframes. Acceso gated implementado. Total 35 pantallas |
| 2026-03-18 | 2.5 | P-35 Reporte Compatibilidad (V-17): ruta pública `/reporte/:token`, modificación P-10 (botón generar reporte en Mis Skills). Total 36 pantallas |
| 2026-03-18 | 2.6 | V-17 ampliado: 2 caminos (Mi Futuro Laboral + Oficina Empleo), rediseño paso 2 (3 vías captura + definiciones), ESCO Argentino como taxonomía de referencia |
| 2026-03-20 | 3.0 | Skills Intelligence v5: arquitectura de 3 servicios (S1/S2/S3) + 6 capacidades del motor. 32 pantallas nuevas (9+11+12). Árbol de navegación integrado con dashboard existente. Fuente: MOL_Skills_Intelligence.docx + mol_screens_v5.html |
