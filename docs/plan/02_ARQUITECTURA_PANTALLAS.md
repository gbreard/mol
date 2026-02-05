# 2. Arquitectura de Pantallas

> Última actualización: 2026-02-05

## Referencias

| Documento | Relación |
|-----------|----------|
| [01_MODELO_NEGOCIO](./01_MODELO_NEGOCIO.md) | Define permisos por plan |
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
| - | `/admin/usuarios` | ⚠️ Básico | Falta editar/eliminar |
| - | `/admin/issues` | ✅ Funcional | - |
| - | `/admin/skills` | ✅ Funcional | 6 tabs |
| - | `/admin/scraping` | ⚠️ Solo lectura | No ejecuta |
| - | `/admin/metricas` | ✅ Funcional | - |
| - | `/admin/logs` | ⚠️ Prueba | Datos de prueba |
| - | `/admin/configuracion` | ⚠️ UI | Sin backend |

### Componentes Existentes

- **Filtros globales:** Territorio, provincia, fechas, ocupaciones
- **Visualizaciones:** Sunburst ESCO, gráficos Recharts, tablas
- **Sistema de tabs:** Implementado en Home y Skills
- **Autenticación:** Supabase Auth con roles
- **Issues/Feedback:** FAB flotante + drawer + página admin

---

## Árbol de Navegación Propuesto

```
MOL Platform
│
├── PÚBLICO (sin auth)
│   ├── / ────────────────── P-01 Landing Page
│   ├── /precios ─────────── P-02 Precios
│   ├── /informes ────────── P-03 Informes Públicos
│   ├── /login ───────────── P-04 Login
│   ├── /registro ────────── P-05 Registro
│   └── /skills ──────────── (existente, versión limitada)
│
├── CHECKOUT
│   ├── /checkout ────────── P-06 Checkout
│   ├── /checkout/exito ──── P-07 Éxito
│   └── /checkout/cancelado  P-08 Cancelado
│
├── SUSCRIPTOR (auth + plan)
│   ├── /dashboard ───────── P-09 Dashboard (actual `/`)
│   │   ├── Tab: Panorama General
│   │   ├── Tab: Requerimientos
│   │   └── Tab: Ofertas Laborales
│   ├── /dashboard/skills ── P-10 Skills (actual `/admin/skills`)
│   ├── /dashboard/empresas  P-11 Análisis Empresas
│   ├── /dashboard/reportes  P-12 Reportes
│   └── /dashboard/alertas   P-13 Alertas
│
├── CUENTA
│   ├── /cuenta ──────────── P-14 Mi Cuenta (Perfil)
│   ├── /cuenta/suscripcion  P-15 Suscripción
│   └── /cuenta/facturacion  P-16 Facturación
│
└── ADMIN (auth + rol admin)
    ├── /admin ───────────── P-17 Dashboard Admin
    ├── /admin/usuarios ──── P-18 Usuarios
    ├── /admin/issues ────── P-19 Issues
    ├── /admin/skills ────── P-20 Skills Intelligence
    ├── /admin/scraping ──── P-21 Scraping
    ├── /admin/metricas ──── P-22 Métricas
    ├── /admin/logs ──────── P-23 Logs
    └── /admin/configuracion P-24 Configuración
```

---

## Lista de Pantallas (P-*)

### Públicas

| ID | Ruta | Plan | Estado | Wireframe |
|----|------|------|--------|-----------|
| P-01 | `/` | - | Por crear | [publicas.md#p-01](./03_WIREFRAMES/publicas.md#p-01-landing-page) |
| P-02 | `/precios` | - | Por crear | [publicas.md#p-02](./03_WIREFRAMES/publicas.md#p-02-precios) |
| P-03 | `/informes` | - | Por crear | [publicas.md#p-03](./03_WIREFRAMES/publicas.md#p-03-informes) |
| P-04 | `/login` | - | ✅ Existe | [publicas.md#p-04](./03_WIREFRAMES/publicas.md#p-04-login) |
| P-05 | `/registro` | - | Por crear | [publicas.md#p-05](./03_WIREFRAMES/publicas.md#p-05-registro) |

### Checkout

| ID | Ruta | Plan | Estado | Wireframe |
|----|------|------|--------|-----------|
| P-06 | `/checkout` | [U-FREE](./01_MODELO_NEGOCIO.md#u-free) | Por crear | [checkout.md#p-06](./03_WIREFRAMES/checkout.md#p-06-checkout) |
| P-07 | `/checkout/exito` | [U-FREE](./01_MODELO_NEGOCIO.md#u-free) | Por crear | [checkout.md#p-07](./03_WIREFRAMES/checkout.md#p-07-exito) |
| P-08 | `/checkout/cancelado` | [U-FREE](./01_MODELO_NEGOCIO.md#u-free) | Por crear | [checkout.md#p-08](./03_WIREFRAMES/checkout.md#p-08-cancelado) |

### Suscriptor

| ID | Ruta | Plan | Estado | Wireframe |
|----|------|------|--------|-----------|
| P-09 | `/dashboard` | [U-FREE](./01_MODELO_NEGOCIO.md#u-free) | ✅ Mover | [suscriptor.md#p-09](./03_WIREFRAMES/suscriptor.md#p-09-dashboard) |
| P-10 | `/dashboard/skills` | [U-FREE](./01_MODELO_NEGOCIO.md#u-free) | ✅ Mover | [suscriptor.md#p-10](./03_WIREFRAMES/suscriptor.md#p-10-skills) |
| P-11 | `/dashboard/empresas` | [U-PRO](./01_MODELO_NEGOCIO.md#u-pro) | Por crear | [suscriptor.md#p-11](./03_WIREFRAMES/suscriptor.md#p-11-empresas) |
| P-12 | `/dashboard/reportes` | [U-PRO](./01_MODELO_NEGOCIO.md#u-pro) | Por crear | [suscriptor.md#p-12](./03_WIREFRAMES/suscriptor.md#p-12-reportes) |
| P-13 | `/dashboard/alertas` | [U-PRO](./01_MODELO_NEGOCIO.md#u-pro) | Por crear | [suscriptor.md#p-13](./03_WIREFRAMES/suscriptor.md#p-13-alertas) |

### Cuenta

| ID | Ruta | Plan | Estado | Wireframe |
|----|------|------|--------|-----------|
| P-14 | `/cuenta` | [U-FREE](./01_MODELO_NEGOCIO.md#u-free) | Por crear | [cuenta.md#p-14](./03_WIREFRAMES/cuenta.md#p-14-perfil) |
| P-15 | `/cuenta/suscripcion` | [U-FREE](./01_MODELO_NEGOCIO.md#u-free) | Por crear | [cuenta.md#p-15](./03_WIREFRAMES/cuenta.md#p-15-suscripcion) |
| P-16 | `/cuenta/facturacion` | [U-PRO](./01_MODELO_NEGOCIO.md#u-pro) | Por crear | [cuenta.md#p-16](./03_WIREFRAMES/cuenta.md#p-16-facturacion) |

### Admin

| ID | Ruta | Plan | Estado | Wireframe |
|----|------|------|--------|-----------|
| P-17 | `/admin` | [U-ADMIN](./01_MODELO_NEGOCIO.md#u-admin) | ✅ Existe | [admin.md#p-17](./03_WIREFRAMES/admin.md#p-17-dashboard) |
| P-18 | `/admin/usuarios` | [U-ADMIN](./01_MODELO_NEGOCIO.md#u-admin) | ⚠️ Básico | [admin.md#p-18](./03_WIREFRAMES/admin.md#p-18-usuarios) |
| P-19 | `/admin/issues` | [U-ADMIN](./01_MODELO_NEGOCIO.md#u-admin) | ✅ Existe | [admin.md#p-19](./03_WIREFRAMES/admin.md#p-19-issues) |
| P-20 | `/admin/skills` | [U-ADMIN](./01_MODELO_NEGOCIO.md#u-admin) | ✅ Existe | [admin.md#p-20](./03_WIREFRAMES/admin.md#p-20-skills) |
| P-21 | `/admin/scraping` | [U-ADMIN](./01_MODELO_NEGOCIO.md#u-admin) | ⚠️ Lectura | [admin.md#p-21](./03_WIREFRAMES/admin.md#p-21-scraping) |
| P-22 | `/admin/metricas` | [U-ADMIN](./01_MODELO_NEGOCIO.md#u-admin) | ✅ Existe | [admin.md#p-22](./03_WIREFRAMES/admin.md#p-22-metricas) |
| P-23 | `/admin/logs` | [U-ADMIN](./01_MODELO_NEGOCIO.md#u-admin) | ⚠️ Prueba | [admin.md#p-23](./03_WIREFRAMES/admin.md#p-23-logs) |
| P-24 | `/admin/configuracion` | [U-ADMIN](./01_MODELO_NEGOCIO.md#u-admin) | ⚠️ UI | [admin.md#p-24](./03_WIREFRAMES/admin.md#p-24-configuracion) |

---

## Resumen

| Categoría | Total | Existentes | Por crear |
|-----------|-------|------------|-----------|
| Públicas | 5 | 1 | 4 |
| Checkout | 3 | 0 | 3 |
| Suscriptor | 5 | 2 | 3 |
| Cuenta | 3 | 0 | 3 |
| Admin | 8 | 8 | 0 |
| **TOTAL** | **24** | **11** | **13** |

---

## Permisos por Ruta

### Middleware de Autenticación

```typescript
// middleware.ts (propuesto)

const PUBLIC_ROUTES = ['/', '/precios', '/informes', '/login', '/registro', '/skills'];
const AUTH_ROUTES = ['/dashboard', '/cuenta', '/checkout'];
const ADMIN_ROUTES = ['/admin'];
const PRO_ROUTES = ['/dashboard/empresas', '/dashboard/reportes', '/dashboard/alertas', '/cuenta/facturacion'];

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const session = getSession(request);

  // Rutas públicas: permitir
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
      return NextResponse.redirect('/dashboard');
    }
  }

  // Rutas PRO: verificar plan
  if (PRO_ROUTES.some(r => pathname.startsWith(r))) {
    if (!['pro', 'enterprise'].includes(session.user.plan)) {
      return NextResponse.redirect('/precios?upgrade=true');
    }
  }

  return NextResponse.next();
}
```

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
├── (checkout)/
│   ├── checkout/page.tsx     # P-06
│   ├── checkout/exito/page.tsx    # P-07
│   └── checkout/cancelado/page.tsx # P-08
├── dashboard/
│   ├── layout.tsx            # Sidebar suscriptor
│   ├── page.tsx              # P-09 (mover de `/`)
│   ├── skills/page.tsx       # P-10 (mover de `/admin/skills`)
│   ├── empresas/page.tsx     # P-11
│   ├── reportes/page.tsx     # P-12
│   └── alertas/page.tsx      # P-13
├── cuenta/
│   ├── page.tsx              # P-14
│   ├── suscripcion/page.tsx  # P-15
│   └── facturacion/page.tsx  # P-16
└── admin/                    # P-17 a P-24 (existente)
```
