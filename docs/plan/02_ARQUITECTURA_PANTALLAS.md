# 2. Arquitectura de Pantallas

> Ultima actualizacion: 2026-03-04
> Versión: 2.5 — 5 páginas públicas (landings + legal)

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

## Árbol de Navegación Propuesto

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
│   ├── /para-oficinas ──── P-35 Landing Oficina de Empleo
│   ├── /mi-futuro-laboral  P-36 Landing Mi Futuro Laboral
│   ├── /metodologia ────── P-37 Metodología MOL
│   ├── /terminos ────────── P-38 Términos de Uso
│   └── /politica-datos ──── P-39 Política de Datos
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
├── TABLERO (auth + trial/suscriptor/institucional)
│   ├── /dashboard ───────── P-09 Dashboard (actual `/`)
│   │   ├── Tab: Panorama General
│   │   ├── Tab: Requerimientos
│   │   └── Tab: Ofertas Laborales
│   ├── /dashboard/skills ── P-10 Skills (actual `/admin/skills`)
│   ├── /dashboard/empresas  P-11 Análisis Empresas
│   ├── /dashboard/reportes  P-12 Reportes
│   └── /dashboard/alertas   P-13 Alertas
│
├── CUENTA (auth)
│   ├── /cuenta ──────────── P-14 Mi Cuenta (Perfil)
│   ├── /cuenta/suscripcion  P-15 Suscripción
│   └── /cuenta/facturacion  P-16 Facturación
│
├── OFICINA DE EMPLEO (auth + rol oficina_empleo/admin)
│   ├── /oficina-empleo ─────── P-32 Hub Oficina de Empleo (wireframe)
│   ├── /oficina-empleo/perfil ─ P-33 Perfil Trabajador (wireframe)
│   └── /oficina-empleo/ofertas  P-34 Ofertas Coincidentes (wireframe)
│
└── ADMIN (auth + rol admin)
    ├── /admin ───────────── P-17 Dashboard Admin
    ├── /admin/usuarios ──── P-18 Usuarios
    ├── /admin/solicitudes ─ P-29 Gestión Solicitudes Acceso
    ├── /admin/issues ────── P-19 Issues
    ├── /admin/skills ────── P-20 Skills Intelligence
    ├── /admin/scraping ──── P-21 Scraping
    ├── /admin/metricas ──── P-22 Métricas
    ├── /admin/logs ──────── P-23 Logs
    ├── /admin/configuracion P-24 Configuración
    ├── /admin/contenidos ── P-30 Gestión Contenidos (CMS)
    ├── /admin/arquitectura  P-25 Arquitectura Sistema
    └── /admin/laboratorio ─ P-31 Laboratorio de Indicadores Experimentales
        └── /tension-demanda P-31a Detalle Tensión de Demanda (V-16)
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
| P-35 | `/para-oficinas` | U-VISITANTE | ✅ Funcional (2026-03-04) | Landing hub oficina empleo |
| P-36 | `/mi-futuro-laboral` | U-VISITANTE | ✅ Funcional (2026-03-04) | Landing exploración laboral |
| P-37 | `/metodologia` | U-VISITANTE | ✅ Funcional (2026-03-04) | Contenido estático |
| P-38 | `/terminos` | U-VISITANTE | ✅ Placeholder (2026-03-04) | Pendiente contenido legal |
| P-39 | `/politica-datos` | U-VISITANTE | ✅ Placeholder (2026-03-04) | Pendiente contenido legal |

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

---

## Resumen

| Categoría | Total | Existentes | Por crear |
|-----------|-------|------------|-----------|
| Públicas | 10 | 6 | 4 |
| Contenido | 3 | 1 (placeholder) | 2 |
| Checkout | 3 | 0 | 3 |
| Tablero | 5 | 2 | 3 |
| Oficina Empleo | 3 | 3 (wireframes) | 0 (funcionalidad pendiente) |
| Cuenta | 3 | 0 | 3 |
| Admin | 13 | 10 | 3 |
| **TOTAL** | **40** | **22** | **18** |

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

const PUBLIC_ROUTES = ['/', '/precios', '/informes', '/login', '/registro', '/skills', '/para-oficinas', '/mi-futuro-laboral', '/metodologia', '/terminos', '/politica-datos'];

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
