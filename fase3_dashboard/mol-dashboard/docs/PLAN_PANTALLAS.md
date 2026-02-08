# Plan: Arquitectura de Pantallas MOL Dashboard

## Objetivo

Diseñar el sistema completo de pantallas del dashboard MOL, partiendo del relevamiento actual y planificando las pantallas faltantes.

---

## RELEVAMIENTO ACTUAL (10 pantallas existentes)

### Estructura de Navegación

```
MOL Dashboard
├── / (Home) ─────────────────── 3 tabs
│   ├── Panorama General
│   ├── Requerimientos
│   └── Ofertas Laborales
│
├── /login ───────────────────── Login
│
├── /skills (pública) ────────── 4 tabs
│   ├── Taxonomía ESCO
│   ├── Ocupación
│   ├── Comparar
│   └── Mis Skills
│
└── /admin (requiere auth) ───── 8 páginas
    ├── Dashboard (estado sistema)
    ├── Usuarios (CRUD usuarios)
    ├── Issues (feedback/errores)
    ├── Skills Intelligence ──── 6 tabs
    │   ├── Taxonomía
    │   ├── Ocupación
    │   ├── Comparar
    │   ├── Mis Skills
    │   ├── Perfil Argentina
    │   └── Consolidado
    ├── Scraping (estado fuentes)
    ├── Métricas (KPIs pipeline)
    ├── Logs (audit + eventos)
    └── Configuración (6 secciones)
```

### Detalle por Pantalla

| Ruta | Propósito | Estado |
|------|-----------|--------|
| `/` | Dashboard principal con filtros y 3 vistas de datos | ✅ Funcional |
| `/login` | Autenticación email/password | ✅ Funcional |
| `/skills` | Skills Intelligence público (sin auth) | ✅ Funcional |
| `/admin` | Estado del sistema (3 fases) | ✅ Funcional |
| `/admin/usuarios` | Gestión de usuarios | ⚠️ Básico (falta editar/eliminar) |
| `/admin/issues` | Sistema de feedback | ✅ Funcional |
| `/admin/skills` | Skills Intelligence completo | ✅ Funcional |
| `/admin/scraping` | Estado de scraping | ⚠️ Solo lectura (no ejecuta) |
| `/admin/metricas` | Métricas del pipeline | ✅ Funcional |
| `/admin/logs` | Audit logs | ⚠️ Datos de prueba |
| `/admin/configuracion` | Configuración sistema | ⚠️ UI sin backend real |

### Componentes Existentes

- **Filtros globales:** Territorio, provincia, fechas, ocupaciones
- **Visualizaciones:** Sunburst ESCO, gráficos Recharts, tablas
- **Sistema de tabs:** Implementado en Home y Skills
- **Autenticación:** Supabase Auth con roles
- **Issues/Feedback:** FAB flotante + drawer + página admin

---

## MODELO DE NEGOCIO: PLATAFORMA SaaS

### Visión
Plataforma que **vende acceso** a inteligencia del mercado laboral argentino.
- **Público**: Landing + informes PDF gratuitos
- **Suscriptores**: Dashboard completo (empresas, consultoras, recruiters)
- **Admin (OEDE)**: Solo visualización del sistema

### Tipos de Usuario

| Tipo | Acceso | Paga |
|------|--------|------|
| Visitante | Landing + informes públicos | No |
| Free (registrado) | Dashboard limitado (ej: solo CABA, últimos 7 días) | No |
| Pro | Dashboard completo + exports | Sí (mensual) |
| Enterprise | Todo + API + reportes custom | Sí (anual) |
| Admin OEDE | Panel admin (solo lectura) | No |

---

## ARQUITECTURA ACTUAL v2.1

```
MOL Platform
│
├── PÚBLICO (sin auth)
│   ├── / ────────────────── Landing Page (hero, features, pricing)
│   ├── /login ──────────── Login (email/password)
│   ├── /registro ───────── Registro (nombre/email/password)
│   ├── /precios ────────── Planes y comparativa
│   ├── /informes ───────── Informes públicos
│   ├── /skills ─────────── Skills Intelligence (Sunburst ESCO)
│   ├── /checkout ───────── Checkout MercadoPago (placeholder)
│   ├── /checkout/exito ─── Confirmación pago → /home
│   └── /checkout/cancelado  Pago fallido → /precios
│
├── AUTENTICADO (post-login)
│   ├── /home ───────────── Hub personalizado (redirect post-login)
│   ├── /dashboard ──────── Tablero con 3 tabs (datos reales)
│   │   ├── /dashboard/empresas ── Análisis empresas (placeholder)
│   │   ├── /dashboard/reportes ── Generador reportes (placeholder)
│   │   └── /dashboard/alertas ─── Alertas ocupación (placeholder)
│   └── /cuenta ─────────── Mi cuenta
│       ├── /cuenta/suscripcion ── Plan actual (placeholder)
│       └── /cuenta/facturacion ── Historial pagos (placeholder)
│
└── ADMIN OEDE (auth + rol admin)
    ├── /admin ───────────── Estado del sistema (3 fases)
    ├── /admin/usuarios ──── CRUD usuarios
    ├── /admin/issues ────── Feedback/errores
    ├── /admin/skills ────── Skills Intelligence (placeholder)
    ├── /admin/arquitectura ─ Mapa pantallas + pipeline
    ├── /admin/scraping ──── Estado scraping
    ├── /admin/metricas ──── KPIs del pipeline
    ├── /admin/logs ──────── Audit log + eventos
    └── /admin/configuracion  Estado sistema (solo lectura)
```

### Flujo de navegación

```
VISITANTE
  / ──→ /login ──→ /home (hub personalizado)
  / ──→ /registro ──→ confirmar email ──→ /login ──→ /home
  / ──→ /precios ──→ /checkout ──→ /checkout/exito ──→ /home
  / ──→ /informes (libre)
  / ──→ /skills (libre)

AUTENTICADO
  /home ──→ /dashboard (todos)
  /home ──→ /admin (solo admin)
  /home ──→ /cuenta/suscripcion
  /home ──→ /precios (upgrade, solo free)
  Logout ──→ / (landing)

MIDDLEWARE
  Sin auth + ruta protegida ──→ /login
  Con auth + /login ──→ /home
```

---

## PANTALLAS NUEVAS A CREAR

### 1. PÚBLICO

| Pantalla | Ruta | Descripción |
|----------|------|-------------|
| **Landing Page** | `/` | Hero, features, testimonios, CTA registro |
| **Informes Públicos** | `/informes` | Lista de PDFs descargables |
| **Precios** | `/precios` | 3-4 planes con comparativa |
| **Registro** | `/registro` | Form + selección de plan |

### 2. SUSCRIPTOR

| Pantalla | Ruta | Descripción |
|----------|------|-------------|
| **Análisis Empresas** | `/empresas` | Top empresas, filtros por sector |
| **Reportes** | `/reportes` | Generar y descargar Excel/PDF |
| **Alertas** | `/alertas` | Suscribirse a cambios |
| **Mi Cuenta** | `/mi-cuenta` | Perfil, plan, facturación |

### 3. CHECKOUT

| Pantalla | Ruta | Descripción |
|----------|------|-------------|
| **Checkout** | `/checkout` | Selección plan + pago |
| **Éxito** | `/checkout/exito` | Confirmación de pago |
| **Cancelado** | `/checkout/cancelado` | Pago fallido |

---

## HUB POST-LOGIN (`/home`)

### Propósito
Pantalla intermedia personalizada que actúa como hub después del login. Reemplaza el redirect directo a `/dashboard`.

### Redirects actualizados
- `middleware.ts`: auth + `/login` → `/home`
- `login/page.tsx`: login OK → `/home`
- `auth/callback/route.ts`: default → `/home`

### Campo `plan` en user_metadata
- Valores: `free` (default), `pro`, `enterprise`
- Usuarios sin campo `plan` → se tratan como `free`

### Árbol de decisión

```
Login OK → /home (SIEMPRE)
│
├── ADMIN (role = super_admin | admin)
│   → Accesos rápidos: [Panel Admin] [Dashboard]
│   → Informes recientes
│
├── FREE (role = viewer | analyst, plan = free | null)
│   → Dashboard (vista limitada)
│   → Informes recientes
│   → CTA Upgrade a Pro → /precios
│
└── SUSCRIPTOR (plan = pro | enterprise)
    → Dashboard (acceso completo, prominente)
    → Accesos rápidos: Reportes, Alertas, Suscripción
    → Informes recientes
    → Info de plan activo
```

### Archivos

| Archivo | Tipo |
|---------|------|
| `app/home/layout.tsx` | Auth guard (Server Component) |
| `app/home/page.tsx` | Hub personalizado (Server Component) |

---

## DECISIONES TOMADAS

| Decisión | Valor |
|----------|-------|
| **Pasarela de pago** | MercadoPago (Argentina, pesos) |
| **Limitación Free vs Pro** | Por tiempo: Free = últimos 7 días, Pro = histórico completo |
| **Informes PDF** | Hay que crearlos desde cero |

---

## DEFINICIÓN DE PLANES

| Plan | Precio | Acceso temporal | Features |
|------|--------|-----------------|----------|
| **Visitante** | Gratis | - | Landing + informes públicos PDF |
| **Free** | Gratis | Últimos 7 días | Dashboard básico, sin export |
| **Pro** | $X/mes | Histórico completo | Todo + exports + alertas |
| **Enterprise** | $X/año | Todo | Todo + API + reportes custom |
| **Admin OEDE** | Gratis | Todo | Panel admin (solo lectura) |

---

## LISTA COMPLETA DE PANTALLAS (25 rutas)

> **Leyenda:** Funcional = con lógica real | Placeholder = UI sin backend | Nuevo = recién creado

### PÚBLICAS (6)

| # | Pantalla | Ruta | Estado | Descripción |
|---|----------|------|--------|-------------|
| 1 | **Landing Page** | `/` | Funcional | Hero, features, stats, CTA |
| 2 | **Precios** | `/precios` | Funcional | 3 planes (Free, Pro, Enterprise) |
| 3 | **Informes Públicos** | `/informes` | Funcional (mock) | Lista de informes, descarga pendiente |
| 4 | **Login** | `/login` | Funcional | Email/password, link a registro |
| 5 | **Registro** | `/registro` | Funcional | Signup con nombre/email/password |
| 6 | **Skills Intelligence** | `/skills` | Funcional | Sunburst ESCO, 4 tabs |

### CHECKOUT (3)

| # | Pantalla | Ruta | Estado | Descripción |
|---|----------|------|--------|-------------|
| 7 | **Checkout** | `/checkout` | Placeholder | MercadoPago pendiente |
| 8 | **Éxito** | `/checkout/exito` | Placeholder | Confirmación, redirect a `/home` |
| 9 | **Cancelado** | `/checkout/cancelado` | Placeholder | Pago fallido |

### AUTENTICADO - HUB (1)

| # | Pantalla | Ruta | Estado | Descripción |
|---|----------|------|--------|-------------|
| 10 | **Home (Hub post-login)** | `/home` | Funcional | Hub personalizado por rol/plan |

### AUTENTICADO - DASHBOARD (4)

| # | Pantalla | Ruta | Estado | Descripción |
|---|----------|------|--------|-------------|
| 11 | **Dashboard** | `/dashboard` | Funcional | 3 tabs con datos reales de Supabase |
| 12 | **Análisis Empresas** | `/dashboard/empresas` | Placeholder | Top empresas, sectores |
| 13 | **Reportes** | `/dashboard/reportes` | Placeholder | Generar Excel/PDF |
| 14 | **Alertas** | `/dashboard/alertas` | Placeholder | Suscribirse a cambios |

### AUTENTICADO - CUENTA (3)

| # | Pantalla | Ruta | Estado | Descripción |
|---|----------|------|--------|-------------|
| 15 | **Mi Cuenta** | `/cuenta` | Placeholder | Hub con links a sub-secciones |
| 16 | **Suscripción** | `/cuenta/suscripcion` | Placeholder | Plan actual, upgrade |
| 17 | **Facturación** | `/cuenta/facturacion` | Placeholder | Historial de pagos |

### ADMIN OEDE (8)

| # | Pantalla | Ruta | Estado | Descripción |
|---|----------|------|--------|-------------|
| 18 | **Admin Dashboard** | `/admin` | Funcional | Estado del sistema, 3 fases |
| 19 | **Admin Usuarios** | `/admin/usuarios` | Funcional | CRUD usuarios |
| 20 | **Admin Issues** | `/admin/issues` | Funcional | Feedback/errores |
| 21 | **Admin Skills** | `/admin/skills` | Placeholder | Skills Intelligence interno |
| 22 | **Admin Métricas** | `/admin/metricas` | Funcional | KPIs del pipeline |
| 23 | **Admin Arquitectura** | `/admin/arquitectura` | Funcional | Mapa pantallas + pipeline |
| 24 | **Admin Logs** | `/admin/logs` | Funcional | Audit log + eventos |
| 25 | **Admin Configuración** | `/admin/configuracion` | Funcional (solo lectura) | Estado sistema |

---

## RESUMEN

| Categoría | Total | Funcional | Placeholder |
|-----------|-------|-----------|-------------|
| Públicas | 6 | 6 | 0 |
| Checkout | 3 | 0 | 3 |
| Hub | 1 | 1 | 0 |
| Dashboard | 4 | 1 | 3 |
| Cuenta | 3 | 0 | 3 |
| Admin | 8 | 7 | 1 |
| **TOTAL** | **25** | **15** | **10** |

---

## FASES DE IMPLEMENTACIÓN

### FASE 1: Esqueleto (placeholder pages)
**Objetivo:** Crear todas las rutas con contenido mínimo para navegar

1. Crear estructura de carpetas
2. Placeholder para cada página (título + "Próximamente")
3. Navegación básica entre páginas
4. Middleware de autenticación actualizado

**Archivos:**
```
app/
├── (public)/
│   ├── page.tsx           # Landing
│   ├── precios/page.tsx
│   ├── informes/page.tsx
│   └── registro/page.tsx
├── (checkout)/
│   ├── checkout/page.tsx
│   ├── checkout/exito/page.tsx
│   └── checkout/cancelado/page.tsx
├── dashboard/
│   ├── layout.tsx         # Sidebar suscriptor
│   ├── page.tsx           # Mover actual home
│   ├── empresas/page.tsx
│   ├── reportes/page.tsx
│   └── alertas/page.tsx
├── cuenta/
│   ├── page.tsx
│   ├── suscripcion/page.tsx
│   └── facturacion/page.tsx
└── admin/                  # Ya existe
```

### FASE 2: Landing + Registro + Auth
- Landing page con hero y CTA
- Página de precios
- Registro con selección de plan
- Actualizar auth para manejar planes

### FASE 3: MercadoPago + Checkout
- Integrar SDK MercadoPago
- Flujo de checkout
- Webhooks para confirmar pago
- Tabla `suscripciones` en Supabase

### FASE 4: Restricciones por Plan
- Middleware que verifica plan activo
- Filtro de datos por fecha según plan
- UI que indica límites (Free vs Pro)

### FASE 5: Features Suscriptor
- Análisis de empresas
- Reportes (export)
- Alertas

### FASE 6: Informes Públicos
- Diseño de informes PDF
- Generación automática
- Página de descarga

---

## WIREFRAMES ASCII

### 1. Landing Page (`/`)

```
┌─────────────────────────────────────────────────────────────────────────┐
│  [Logo MOL]                    Precios  Informes  [Iniciar Sesión]      │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│          ╔═══════════════════════════════════════════════════╗          │
│          ║                                                    ║          │
│          ║   Inteligencia del Mercado Laboral Argentino      ║          │
│          ║                                                    ║          │
│          ║   Datos en tiempo real sobre ofertas de empleo,   ║          │
│          ║   skills demandadas y tendencias del mercado.     ║          │
│          ║                                                    ║          │
│          ║   [  Comenzar Gratis  ]   [  Ver Demo  ]          ║          │
│          ║                                                    ║          │
│          ╚═══════════════════════════════════════════════════╝          │
│                                                                          │
├─────────────────────────────────────────────────────────────────────────┤
│                         NÚMEROS QUE HABLAN                               │
│                                                                          │
│    ┌──────────────┐   ┌──────────────┐   ┌──────────────┐               │
│    │   +50,000    │   │     300+     │   │    1,200+    │               │
│    │   ofertas    │   │  ocupaciones │   │    skills    │               │
│    │   activas    │   │    ESCO      │   │   mapeadas   │               │
│    └──────────────┘   └──────────────┘   └──────────────┘               │
│                                                                          │
├─────────────────────────────────────────────────────────────────────────┤
│                         CARACTERÍSTICAS                                  │
│                                                                          │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐             │
│  │ 📊 Dashboard   │  │ 🔍 Skills      │  │ 🏢 Empresas    │             │
│  │ KPIs y métricas│  │ Intelligence   │  │ Quién contrata │             │
│  │ del mercado    │  │ ESCO + MOL     │  │ más y qué      │             │
│  └────────────────┘  └────────────────┘  └────────────────┘             │
│                                                                          │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐             │
│  │ 📈 Reportes    │  │ 🔔 Alertas     │  │ 🔌 API         │             │
│  │ Export Excel   │  │ Notificaciones │  │ Acceso directo │             │
│  │ y PDF          │  │ personalizadas │  │ a los datos    │             │
│  └────────────────┘  └────────────────┘  └────────────────┘             │
│                                                                          │
├─────────────────────────────────────────────────────────────────────────┤
│                            PRECIOS                                       │
│                                                                          │
│  ┌─────────────┐   ┌─────────────────┐   ┌─────────────────┐            │
│  │    FREE     │   │      PRO        │   │   ENTERPRISE    │            │
│  │   $0/mes    │   │   $XX.XXX/mes   │   │    Contactar    │            │
│  │             │   │                 │   │                 │            │
│  │ • 7 días    │   │ • Histórico     │   │ • Todo PRO      │            │
│  │ • Sin export│   │ • Exports       │   │ • API acceso    │            │
│  │             │   │ • Alertas       │   │ • Soporte       │            │
│  │             │   │                 │   │                 │            │
│  │ [Registrar] │   │  [Suscribir]    │   │  [Contactar]    │            │
│  └─────────────┘   └─────────────────┘   └─────────────────┘            │
│                                                                          │
├─────────────────────────────────────────────────────────────────────────┤
│  © 2026 MOL - OEDE                              Términos | Privacidad   │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2. Página de Precios (`/precios`)

```
┌─────────────────────────────────────────────────────────────────────────┐
│  [Logo MOL]                    Precios  Informes  [Iniciar Sesión]      │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│                    Elegí el plan que mejor se adapte                     │
│                       a tus necesidades                                  │
│                                                                          │
│  ┌───────────────────┐  ┌───────────────────┐  ┌───────────────────┐    │
│  │                   │  │    ★ POPULAR ★    │  │                   │    │
│  │       FREE        │  │       PRO         │  │    ENTERPRISE     │    │
│  │                   │  │                   │  │                   │    │
│  │      $0/mes       │  │   $XX.XXX/mes     │  │     Contactar     │    │
│  │                   │  │                   │  │                   │    │
│  ├───────────────────┤  ├───────────────────┤  ├───────────────────┤    │
│  │                   │  │                   │  │                   │    │
│  │ ✓ Dashboard       │  │ ✓ Todo de FREE    │  │ ✓ Todo de PRO     │    │
│  │ ✓ Últimos 7 días  │  │ ✓ Histórico       │  │ ✓ API REST        │    │
│  │ ✓ Skills básico   │  │   completo        │  │ ✓ Webhooks        │    │
│  │ ✗ Exports         │  │ ✓ Export Excel    │  │ ✓ Reportes custom │    │
│  │ ✗ Alertas         │  │ ✓ Export PDF      │  │ ✓ SLA 99.9%       │    │
│  │ ✗ Empresas        │  │ ✓ Alertas email   │  │ ✓ Soporte prio    │    │
│  │                   │  │ ✓ Análisis emp    │  │ ✓ Onboarding      │    │
│  │                   │  │                   │  │                   │    │
│  │                   │  │                   │  │                   │    │
│  │ [ Comenzar ]      │  │ [ Suscribir ]     │  │ [ Contactar ]     │    │
│  │                   │  │                   │  │                   │    │
│  └───────────────────┘  └───────────────────┘  └───────────────────┘    │
│                                                                          │
├─────────────────────────────────────────────────────────────────────────┤
│                         COMPARATIVA DETALLADA                            │
│                                                                          │
│  ┌────────────────────────────┬────────┬────────┬────────────┐          │
│  │ Feature                    │  FREE  │  PRO   │ ENTERPRISE │          │
│  ├────────────────────────────┼────────┼────────┼────────────┤          │
│  │ Dashboard con filtros      │   ✓    │   ✓    │     ✓      │          │
│  │ Acceso temporal            │ 7 días │  Todo  │    Todo    │          │
│  │ Skills Intelligence        │ Básico │  Full  │    Full    │          │
│  │ Análisis de empresas       │   ✗    │   ✓    │     ✓      │          │
│  │ Export Excel               │   ✗    │   ✓    │     ✓      │          │
│  │ Export PDF                 │   ✗    │   ✓    │     ✓      │          │
│  │ Alertas por email          │   ✗    │   ✓    │     ✓      │          │
│  │ API REST                   │   ✗    │   ✗    │     ✓      │          │
│  │ Soporte                    │ Email  │ Email  │  Dedicado  │          │
│  └────────────────────────────┴────────┴────────┴────────────┘          │
│                                                                          │
├─────────────────────────────────────────────────────────────────────────┤
│                              FAQ                                         │
│                                                                          │
│  ▸ ¿Puedo cancelar en cualquier momento?                                │
│  ▸ ¿Qué métodos de pago aceptan?                                        │
│  ▸ ¿Los datos se actualizan en tiempo real?                             │
│  ▸ ¿Puedo cambiar de plan?                                              │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 3. Registro (`/registro`)

```
┌─────────────────────────────────────────────────────────────────────────┐
│  [Logo MOL]                                        [← Volver al inicio] │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│                         Crear cuenta                                     │
│                                                                          │
│         ┌─────────────────────────────────────────────┐                 │
│         │                                             │                 │
│         │  Nombre completo                            │                 │
│         │  ┌─────────────────────────────────────┐    │                 │
│         │  │                                     │    │                 │
│         │  └─────────────────────────────────────┘    │                 │
│         │                                             │                 │
│         │  Email                                      │                 │
│         │  ┌─────────────────────────────────────┐    │                 │
│         │  │                                     │    │                 │
│         │  └─────────────────────────────────────┘    │                 │
│         │                                             │                 │
│         │  Contraseña                                 │                 │
│         │  ┌─────────────────────────────────────┐    │                 │
│         │  │                                     │    │                 │
│         │  └─────────────────────────────────────┘    │                 │
│         │                                             │                 │
│         │  Empresa/Organización (opcional)            │                 │
│         │  ┌─────────────────────────────────────┐    │                 │
│         │  │                                     │    │                 │
│         │  └─────────────────────────────────────┘    │                 │
│         │                                             │                 │
│         │  Plan seleccionado:                         │                 │
│         │  ○ Free (7 días de datos)                   │                 │
│         │  ● Pro ($XX.XXX/mes) ← viene preseleccionado│                 │
│         │                                             │                 │
│         │  □ Acepto términos y condiciones            │                 │
│         │                                             │                 │
│         │  [        Crear cuenta        ]             │                 │
│         │                                             │                 │
│         │  ─────────────────────────────────────      │                 │
│         │  ¿Ya tenés cuenta? Iniciar sesión           │                 │
│         │                                             │                 │
│         └─────────────────────────────────────────────┘                 │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 4. Checkout (`/checkout`)

```
┌─────────────────────────────────────────────────────────────────────────┐
│  [Logo MOL]                               Pago seguro 🔒                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────────────────────┐  ┌─────────────────────────────┐       │
│  │                             │  │                             │       │
│  │   RESUMEN DE TU PEDIDO      │  │      MÉTODO DE PAGO         │       │
│  │                             │  │                             │       │
│  │   Plan: PRO                 │  │  ┌───────────────────────┐  │       │
│  │   Período: Mensual          │  │  │                       │  │       │
│  │                             │  │  │    [MercadoPago]      │  │       │
│  │   ───────────────────       │  │  │                       │  │       │
│  │   Subtotal:    $XX.XXX      │  │  │   Tarjeta de crédito  │  │       │
│  │   IVA (21%):   $X.XXX       │  │  │   Tarjeta de débito   │  │       │
│  │   ───────────────────       │  │  │   Transferencia       │  │       │
│  │   TOTAL:       $XX.XXX      │  │  │   Efectivo            │  │       │
│  │                             │  │  │                       │  │       │
│  │                             │  │  └───────────────────────┘  │       │
│  │   Incluye:                  │  │                             │       │
│  │   ✓ Histórico completo      │  │  Al continuar serás        │       │
│  │   ✓ Exports ilimitados      │  │  redirigido a MercadoPago  │       │
│  │   ✓ Alertas por email       │  │  para completar el pago.   │       │
│  │   ✓ Análisis de empresas    │  │                             │       │
│  │                             │  │                             │       │
│  │   Renovación automática     │  │  [    Pagar $XX.XXX    ]   │       │
│  │   Cancelá cuando quieras    │  │                             │       │
│  │                             │  │                             │       │
│  └─────────────────────────────┘  └─────────────────────────────┘       │
│                                                                          │
│  🔒 Pago procesado por MercadoPago. No almacenamos datos de tarjeta.    │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 5. Dashboard Suscriptor (`/dashboard`)

```
┌─────────────────────────────────────────────────────────────────────────┐
│  [Logo]  Dashboard  Empresas  Skills  Reportes  Alertas    [Usuario ▼] │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────────┐                                                    │
│  │ FILTROS         │  ┌───────────────────────────────────────────────┐ │
│  │                 │  │                                               │ │
│  │ Territorio      │  │  [Panorama] [Requerimientos] [Ofertas]        │ │
│  │ [Nacional    ▼] │  │                                               │ │
│  │                 │  │  ┌─────────┐ ┌─────────┐ ┌─────────┐          │ │
│  │ Provincia       │  │  │ 12,345  │ │   156   │ │  1,200  │          │ │
│  │ [Todas       ▼] │  │  │ ofertas │ │ ocupac. │ │ empresas│          │ │
│  │                 │  │  └─────────┘ └─────────┘ └─────────┘          │ │
│  │ Fecha desde     │  │                                               │ │
│  │ [01/01/2026  ] │  │  ┌─────────────────────────────────────────┐  │ │
│  │                 │  │  │                                         │  │ │
│  │ Fecha hasta     │  │  │         GRÁFICO DE EVOLUCIÓN            │  │ │
│  │ [05/02/2026  ] │  │  │                                         │  │ │
│  │                 │  │  │    /\      /\                           │  │ │
│  │ Ocupación       │  │  │   /  \    /  \    /\                    │  │ │
│  │ [Buscar...   ] │  │  │  /    \  /    \  /  \                   │  │ │
│  │                 │  │  │ /      \/      \/    \                  │  │ │
│  │ [Aplicar]       │  │  │                                         │  │ │
│  │ [Limpiar]       │  │  └─────────────────────────────────────────┘  │ │
│  │                 │  │                                               │ │
│  │ ─────────────── │  │  ┌──────────────────┐ ┌──────────────────┐   │ │
│  │                 │  │  │ Top Ocupaciones  │ │ Por Provincia    │   │ │
│  │ PLAN: PRO ✓     │  │  │ 1. Vendedor 234  │ │ CABA      45%    │   │ │
│  │ Histórico       │  │  │ 2. Programador   │ │ Buenos A. 30%    │   │ │
│  │ completo        │  │  │ 3. Contador 89   │ │ Córdoba   10%    │   │ │
│  │                 │  │  └──────────────────┘ └──────────────────┘   │ │
│  │                 │  │                                               │ │
│  └─────────────────┘  └───────────────────────────────────────────────┘ │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 6. Análisis de Empresas (`/dashboard/empresas`)

```
┌─────────────────────────────────────────────────────────────────────────┐
│  [Logo]  Dashboard  Empresas  Skills  Reportes  Alertas    [Usuario ▼] │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Análisis de Empresas                                   [Exportar ▼]   │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │ Buscar empresa...                                        [🔍]    │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  Filtros: [Sector ▼] [Tamaño ▼] [Provincia ▼] [Período ▼]              │
│                                                                          │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐                            │
│  │  456   │ │  123   │ │  89    │ │  45%   │                            │
│  │empresas│ │ >10 of.│ │sectores│ │ CABA   │                            │
│  │ total  │ │activas │ │        │ │        │                            │
│  └────────┘ └────────┘ └────────┘ └────────┘                            │
│                                                                          │
│  TOP EMPRESAS POR OFERTAS                                               │
│  ┌────────────────────────────────────────────────────────────────┐     │
│  │ #  │ Empresa            │ Sector      │ Ofertas │ Tendencia   │     │
│  ├────┼────────────────────┼─────────────┼─────────┼─────────────┤     │
│  │ 1  │ Mercado Libre      │ Tecnología  │   234   │ ↑ +15%      │     │
│  │ 2  │ Globant            │ Tecnología  │   189   │ ↑ +8%       │     │
│  │ 3  │ Techint            │ Industria   │   156   │ → 0%        │     │
│  │ 4  │ Banco Galicia      │ Finanzas    │   134   │ ↓ -5%       │     │
│  │ 5  │ YPF                │ Energía     │   98    │ ↑ +12%      │     │
│  └────────────────────────────────────────────────────────────────┘     │
│                                                                          │
│  ┌────────────────────────────┐  ┌────────────────────────────┐         │
│  │ OFERTAS POR SECTOR         │  │ TOP SKILLS DEMANDADAS      │         │
│  │                            │  │                            │         │
│  │ Tecnología    ████████ 35% │  │ 1. Excel           456     │         │
│  │ Comercio      █████    20% │  │ 2. Inglés          389     │         │
│  │ Finanzas      ████     15% │  │ 3. Comunicación    345     │         │
│  │ Industria     ███      12% │  │ 4. Python          234     │         │
│  │ Salud         ██        8% │  │ 5. SAP             198     │         │
│  │ Otros         ██       10% │  │                            │         │
│  └────────────────────────────┘  └────────────────────────────┘         │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 7. Mi Cuenta (`/cuenta`)

```
┌─────────────────────────────────────────────────────────────────────────┐
│  [Logo]  Dashboard  Empresas  Skills  Reportes  Alertas    [Usuario ▼] │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────────┐  ┌─────────────────────────────────────────────┐   │
│  │                 │  │                                             │   │
│  │   Mi Cuenta     │  │  INFORMACIÓN PERSONAL                       │   │
│  │   ─────────     │  │                                             │   │
│  │                 │  │  Nombre                                     │   │
│  │   [•] Perfil    │  │  ┌─────────────────────────────────────┐    │   │
│  │   [ ] Suscrip.  │  │  │ Juan Pérez                          │    │   │
│  │   [ ] Facturac. │  │  └─────────────────────────────────────┘    │   │
│  │                 │  │                                             │   │
│  │                 │  │  Email                                      │   │
│  │                 │  │  ┌─────────────────────────────────────┐    │   │
│  │                 │  │  │ juan@empresa.com                    │    │   │
│  │                 │  │  └─────────────────────────────────────┘    │   │
│  │                 │  │                                             │   │
│  │                 │  │  Empresa                                    │   │
│  │                 │  │  ┌─────────────────────────────────────┐    │   │
│  │                 │  │  │ Consultora ABC                      │    │   │
│  │                 │  │  └─────────────────────────────────────┘    │   │
│  │                 │  │                                             │   │
│  │                 │  │  [       Guardar cambios       ]            │   │
│  │                 │  │                                             │   │
│  │                 │  │  ─────────────────────────────────────      │   │
│  │                 │  │                                             │   │
│  │                 │  │  SEGURIDAD                                  │   │
│  │                 │  │  [ Cambiar contraseña ]                     │   │
│  │                 │  │                                             │   │
│  └─────────────────┘  └─────────────────────────────────────────────┘   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 8. Home Actual (`/` → se moverá a `/dashboard`)

```
┌─────────────────────────────────────────────────────────────────────────┐
│  [Logo MOL]                                          [Admin] [Logout]   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────────┐  ┌─────────────────────────────────────────────┐   │
│  │ FILTROS         │  │                                             │   │
│  │                 │  │  [Panorama General] [Requerimientos] [Ofertas]  │
│  │ Territorio      │  │                                             │   │
│  │ [Nacional    ▼] │  │  ════════════════════════════════════════   │   │
│  │                 │  │                                             │   │
│  │ Provincia       │  │  PANORAMA GENERAL (tab activo)              │   │
│  │ [Todas       ▼] │  │                                             │   │
│  │                 │  │  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐│   │
│  │ Período         │  │  │ 12,345 │ │   156  │ │  1,200 │ │  85%   ││   │
│  │ [Último mes  ▼] │  │  │ofertas │ │ ocupac.│ │empresa │ │ perman.││   │
│  │                 │  │  └────────┘ └────────┘ └────────┘ └────────┘│   │
│  │ Permanencia     │  │                                             │   │
│  │ [Todas       ▼] │  │  ┌─────────────────────────────────────┐    │   │
│  │                 │  │  │      EVOLUCIÓN MENSUAL              │    │   │
│  │ Ocupación       │  │  │   /\      /\                        │    │   │
│  │ [Buscar...   ▼] │  │  │  /  \    /  \    /\                 │    │   │
│  │                 │  │  │ /    \  /    \  /  \                │    │   │
│  │ Modalidad       │  │  │/      \/      \/    \               │    │   │
│  │ [Todas       ▼] │  │  │ Ene Feb Mar Abr May Jun             │    │   │
│  │                 │  │  └─────────────────────────────────────┘    │   │
│  │ Seniority       │  │                                             │   │
│  │ [Todos       ▼] │  │  ┌───────────────┐ ┌───────────────────┐   │   │
│  │                 │  │  │ TOP OCUPAC.   │ │ POR PROVINCIA     │   │   │
│  │ ─────────────── │  │  │ 1. Vendedor   │ │ CABA      ████ 45%│   │   │
│  │                 │  │  │ 2. Programador│ │ Bs.As.    ███  30%│   │   │
│  │ [Aplicar]       │  │  │ 3. Contador   │ │ Córdoba   ██   12%│   │   │
│  │ [Limpiar]       │  │  │ 4. Administ.  │ │ Santa Fe  █     8%│   │   │
│  │                 │  │  └───────────────┘ └───────────────────┘   │   │
│  └─────────────────┘  └─────────────────────────────────────────────┘   │
│                                                                          │
│  [?] FAB Issues                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 9. Login (`/login`)

```
┌─────────────────────────────────────────────────────────────────────────┐
│  [Logo MOL]                                        [← Volver al inicio] │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│                                                                          │
│                                                                          │
│         ┌─────────────────────────────────────────────┐                 │
│         │                                             │                 │
│         │           Iniciar Sesión                    │                 │
│         │                                             │                 │
│         │  Email                                      │                 │
│         │  ┌─────────────────────────────────────┐    │                 │
│         │  │ usuario@empresa.com                 │    │                 │
│         │  └─────────────────────────────────────┘    │                 │
│         │                                             │                 │
│         │  Contraseña                                 │                 │
│         │  ┌─────────────────────────────────────┐    │                 │
│         │  │ ••••••••••                          │    │                 │
│         │  └─────────────────────────────────────┘    │                 │
│         │                                             │                 │
│         │  □ Recordarme                               │                 │
│         │                                             │                 │
│         │  [        Iniciar Sesión        ]          │                 │
│         │                                             │                 │
│         │  ─────────────────────────────────────      │                 │
│         │                                             │                 │
│         │  ¿Olvidaste tu contraseña?                  │                 │
│         │                                             │                 │
│         │  ─────────────────────────────────────      │                 │
│         │                                             │                 │
│         │  ¿No tenés cuenta? Registrate               │                 │
│         │                                             │                 │
│         └─────────────────────────────────────────────┘                 │
│                                                                          │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 10. Skills Público (`/skills`) - 4 tabs

```
┌─────────────────────────────────────────────────────────────────────────┐
│  [Logo MOL]                              [Precios] [Login] [Registrar]  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Skills Intelligence - Explorador ESCO                                   │
│                                                                          │
│  [Taxonomía ESCO] [Ocupación] [Comparar] [Mis Skills]                   │
│  ═══════════════                                                         │
│                                                                          │
│  TAXONOMÍA ESCO (tab activo)                                            │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                                                                 │    │
│  │                      ┌─────────────┐                            │    │
│  │              ┌───────┤   ESCO      ├───────┐                    │    │
│  │              │       └─────────────┘       │                    │    │
│  │      ┌───────┴───────┐           ┌────────┴───────┐            │    │
│  │      │  Directivos   │           │ Profesionales  │            │    │
│  │      └───────┬───────┘           └────────┬───────┘            │    │
│  │              │                            │                     │    │
│  │    ┌─────────┼─────────┐        ┌─────────┼─────────┐          │    │
│  │    │         │         │        │         │         │          │    │
│  │  [Dir.    [Dir.    [Dir.     [Ing.    [Médicos] [Docentes]     │    │
│  │   Gral]   Ventas]  RRHH]     Soft]                             │    │
│  │                                                                 │    │
│  │                    SUNBURST INTERACTIVO                         │    │
│  │                    (click para explorar)                        │    │
│  │                                                                 │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  Ocupaciones: 3,045  |  Skills: 13,890  |  Grupos: 436                  │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 11. Informes Públicos (`/informes`)

```
┌─────────────────────────────────────────────────────────────────────────┐
│  [Logo MOL]                              [Precios] [Login] [Registrar]  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Informes del Mercado Laboral Argentino                                  │
│                                                                          │
│  Descargá gratis nuestros informes periódicos con análisis del mercado. │
│                                                                          │
│  Filtrar: [Todos ▼]  [2026 ▼]  [Buscar...]                             │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                                                                 │    │
│  │  ┌─────────┐  INFORME MENSUAL - ENERO 2026                     │    │
│  │  │  📄     │  Análisis completo del mercado laboral argentino  │    │
│  │  │  PDF    │  con tendencias, ocupaciones más demandadas y     │    │
│  │  │  2.3MB  │  skills en crecimiento.                           │    │
│  │  └─────────┘  Publicado: 05/02/2026    [Descargar PDF]         │    │
│  │                                                                 │    │
│  ├─────────────────────────────────────────────────────────────────┤    │
│  │                                                                 │    │
│  │  ┌─────────┐  INFORME TRIMESTRAL - Q4 2025                     │    │
│  │  │  📄     │  Resumen del último trimestre del año con         │    │
│  │  │  PDF    │  proyecciones para 2026.                          │    │
│  │  │  4.1MB  │                                                   │    │
│  │  └─────────┘  Publicado: 15/01/2026    [Descargar PDF]         │    │
│  │                                                                 │    │
│  ├─────────────────────────────────────────────────────────────────┤    │
│  │                                                                 │    │
│  │  ┌─────────┐  ESPECIAL: TECNOLOGÍA 2025                        │    │
│  │  │  📄     │  Análisis profundo del sector tecnológico:        │    │
│  │  │  PDF    │  salarios, skills, y empresas que más contratan.  │    │
│  │  │  3.7MB  │                                                   │    │
│  │  └─────────┘  Publicado: 20/12/2025    [Descargar PDF]         │    │
│  │                                                                 │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  ─────────────────────────────────────────────────────────────────      │
│  ¿Querés acceso a datos en tiempo real? [Ver planes de suscripción]     │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 12. Checkout Éxito (`/checkout/exito`)

```
┌─────────────────────────────────────────────────────────────────────────┐
│  [Logo MOL]                                                             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│                                                                          │
│                                                                          │
│         ┌─────────────────────────────────────────────┐                 │
│         │                                             │                 │
│         │              ✓                              │                 │
│         │           (verde)                           │                 │
│         │                                             │                 │
│         │      ¡Pago completado con éxito!            │                 │
│         │                                             │                 │
│         │  ─────────────────────────────────────      │                 │
│         │                                             │                 │
│         │  Plan: PRO                                  │                 │
│         │  Monto: $15,000 ARS                         │                 │
│         │  Próximo cobro: 05/03/2026                  │                 │
│         │                                             │                 │
│         │  ─────────────────────────────────────      │                 │
│         │                                             │                 │
│         │  Tu cuenta ya está activa con acceso        │                 │
│         │  completo al histórico de datos.            │                 │
│         │                                             │                 │
│         │  Te enviamos un email de confirmación       │                 │
│         │  a usuario@empresa.com                      │                 │
│         │                                             │                 │
│         │  [      Ir al Dashboard      ]              │                 │
│         │                                             │                 │
│         │  [    Descargar comprobante    ]            │                 │
│         │                                             │                 │
│         └─────────────────────────────────────────────┘                 │
│                                                                          │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 13. Checkout Cancelado (`/checkout/cancelado`)

```
┌─────────────────────────────────────────────────────────────────────────┐
│  [Logo MOL]                                                             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│                                                                          │
│                                                                          │
│         ┌─────────────────────────────────────────────┐                 │
│         │                                             │                 │
│         │              ✗                              │                 │
│         │           (rojo)                            │                 │
│         │                                             │                 │
│         │      El pago no pudo completarse            │                 │
│         │                                             │                 │
│         │  ─────────────────────────────────────      │                 │
│         │                                             │                 │
│         │  Motivo: Fondos insuficientes               │                 │
│         │                                             │                 │
│         │  ─────────────────────────────────────      │                 │
│         │                                             │                 │
│         │  No te preocupes, podés intentar            │                 │
│         │  nuevamente con otro método de pago.        │                 │
│         │                                             │                 │
│         │  [    Reintentar pago    ]                  │                 │
│         │                                             │                 │
│         │  [    Elegir otro plan    ]                 │                 │
│         │                                             │                 │
│         │  ─────────────────────────────────────      │                 │
│         │                                             │                 │
│         │  ¿Problemas? Contactanos:                   │                 │
│         │  soporte@mol.gob.ar                         │                 │
│         │                                             │                 │
│         └─────────────────────────────────────────────┘                 │
│                                                                          │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 14. Reportes (`/dashboard/reportes`)

```
┌─────────────────────────────────────────────────────────────────────────┐
│  [Logo]  Dashboard  Empresas  Skills  Reportes  Alertas    [Usuario ▼] │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Generador de Reportes                                   PLAN: PRO ✓    │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                                                                 │    │
│  │  CREAR NUEVO REPORTE                                            │    │
│  │                                                                 │    │
│  │  Tipo de reporte:                                               │    │
│  │  ○ Resumen general del mercado                                  │    │
│  │  ● Análisis por ocupación                                       │    │
│  │  ○ Análisis por provincia                                       │    │
│  │  ○ Análisis por empresa/sector                                  │    │
│  │  ○ Comparativa temporal                                         │    │
│  │                                                                 │    │
│  │  Período:  [01/01/2026] a [05/02/2026]                         │    │
│  │                                                                 │    │
│  │  Filtros adicionales:                                           │    │
│  │  Provincia: [Todas ▼]  Ocupación: [Todas ▼]                    │    │
│  │                                                                 │    │
│  │  Formato:  ○ Excel (.xlsx)  ● PDF                              │    │
│  │                                                                 │    │
│  │  [        Generar Reporte        ]                              │    │
│  │                                                                 │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  REPORTES GENERADOS RECIENTEMENTE                                        │
│  ┌────────────────────────────────────────────────────────────────┐     │
│  │ Fecha      │ Tipo              │ Período     │ Formato │ Acción│     │
│  ├────────────┼───────────────────┼─────────────┼─────────┼───────┤     │
│  │ 05/02/2026 │ Resumen general   │ Enero 2026  │ PDF     │ [⬇]  │     │
│  │ 01/02/2026 │ Por ocupación     │ Q4 2025     │ Excel   │ [⬇]  │     │
│  │ 28/01/2026 │ Por provincia     │ Enero 2026  │ PDF     │ [⬇]  │     │
│  └────────────────────────────────────────────────────────────────┘     │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 15. Alertas (`/dashboard/alertas`)

```
┌─────────────────────────────────────────────────────────────────────────┐
│  [Logo]  Dashboard  Empresas  Skills  Reportes  Alertas    [Usuario ▼] │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Configuración de Alertas                                PLAN: PRO ✓    │
│                                                                          │
│  Recibí notificaciones cuando haya cambios en el mercado.               │
│                                                                          │
│  [+ Nueva Alerta]                                                        │
│                                                                          │
│  MIS ALERTAS ACTIVAS                                                     │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                                                                 │    │
│  │  ┌─ 🔔 Desarrolladores Python ─────────────────────────────┐   │    │
│  │  │  Tipo: Ocupación                                        │   │    │
│  │  │  Criterio: Nuevas ofertas > 10 por día                  │   │    │
│  │  │  Frecuencia: Diaria                                     │   │    │
│  │  │  Estado: ● Activa                    [Editar] [Pausar]  │   │    │
│  │  └─────────────────────────────────────────────────────────┘   │    │
│  │                                                                 │    │
│  │  ┌─ 🔔 Skills en Crecimiento ──────────────────────────────┐   │    │
│  │  │  Tipo: Skill                                            │   │    │
│  │  │  Criterio: Skills con +20% demanda semanal              │   │    │
│  │  │  Frecuencia: Semanal                                    │   │    │
│  │  │  Estado: ● Activa                    [Editar] [Pausar]  │   │    │
│  │  └─────────────────────────────────────────────────────────┘   │    │
│  │                                                                 │    │
│  │  ┌─ 🔕 Mercado Libre ──────────────────────────────────────┐   │    │
│  │  │  Tipo: Empresa                                          │   │    │
│  │  │  Criterio: Nuevas ofertas de Mercado Libre              │   │    │
│  │  │  Frecuencia: Inmediata                                  │   │    │
│  │  │  Estado: ○ Pausada                   [Editar] [Activar] │   │    │
│  │  └─────────────────────────────────────────────────────────┘   │    │
│  │                                                                 │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  Límite: 3/10 alertas configuradas                                       │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 16. Suscripción (`/cuenta/suscripcion`)

```
┌─────────────────────────────────────────────────────────────────────────┐
│  [Logo]  Dashboard  Empresas  Skills  Reportes  Alertas    [Usuario ▼] │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────────┐  ┌─────────────────────────────────────────────┐   │
│  │                 │  │                                             │   │
│  │   Mi Cuenta     │  │  MI SUSCRIPCIÓN                             │   │
│  │   ─────────     │  │                                             │   │
│  │                 │  │  ┌─────────────────────────────────────┐    │   │
│  │   [ ] Perfil    │  │  │                                     │    │   │
│  │   [•] Suscrip.  │  │  │  Plan actual: PRO                   │    │   │
│  │   [ ] Facturac. │  │  │  Estado: ● Activa                   │    │   │
│  │                 │  │  │                                     │    │   │
│  │                 │  │  │  Precio: $15,000 ARS/mes            │    │   │
│  │                 │  │  │  Próximo cobro: 05/03/2026          │    │   │
│  │                 │  │  │  Método: Visa ****4532              │    │   │
│  │                 │  │  │                                     │    │   │
│  │                 │  │  └─────────────────────────────────────┘    │   │
│  │                 │  │                                             │   │
│  │                 │  │  BENEFICIOS DE TU PLAN                      │   │
│  │                 │  │  ✓ Acceso a histórico completo              │   │
│  │                 │  │  ✓ Exports ilimitados (Excel, PDF)          │   │
│  │                 │  │  ✓ Hasta 10 alertas configuradas            │   │
│  │                 │  │  ✓ Análisis de empresas                     │   │
│  │                 │  │  ✗ Acceso API (solo Enterprise)             │   │
│  │                 │  │                                             │   │
│  │                 │  │  ─────────────────────────────────────      │   │
│  │                 │  │                                             │   │
│  │                 │  │  [Cambiar método de pago]                   │   │
│  │                 │  │  [Upgrade a Enterprise]                     │   │
│  │                 │  │  [Cancelar suscripción]                     │   │
│  │                 │  │                                             │   │
│  └─────────────────┘  └─────────────────────────────────────────────┘   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 17. Facturación (`/cuenta/facturacion`)

```
┌─────────────────────────────────────────────────────────────────────────┐
│  [Logo]  Dashboard  Empresas  Skills  Reportes  Alertas    [Usuario ▼] │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────────┐  ┌─────────────────────────────────────────────┐   │
│  │                 │  │                                             │   │
│  │   Mi Cuenta     │  │  HISTORIAL DE FACTURACIÓN                   │   │
│  │   ─────────     │  │                                             │   │
│  │                 │  │  Datos de facturación:                      │   │
│  │   [ ] Perfil    │  │  Razón social: Consultora ABC S.A.          │   │
│  │   [ ] Suscrip.  │  │  CUIT: 30-12345678-9                        │   │
│  │   [•] Facturac. │  │  [Editar datos de facturación]              │   │
│  │                 │  │                                             │   │
│  │                 │  │  ─────────────────────────────────────      │   │
│  │                 │  │                                             │   │
│  │                 │  │  FACTURAS                                   │   │
│  │                 │  │  ┌────────────────────────────────────┐     │   │
│  │                 │  │  │ Fecha      │ Concepto    │ Monto   │     │   │
│  │                 │  │  ├────────────┼─────────────┼─────────┤     │   │
│  │                 │  │  │ 05/02/2026 │ PRO Febrero │ $15,000 │ [⬇] │   │
│  │                 │  │  │ 05/01/2026 │ PRO Enero   │ $15,000 │ [⬇] │   │
│  │                 │  │  │ 05/12/2025 │ PRO Diciem. │ $15,000 │ [⬇] │   │
│  │                 │  │  │ 05/11/2025 │ PRO Noviem. │ $15,000 │ [⬇] │   │
│  │                 │  │  └────────────────────────────────────┘     │   │
│  │                 │  │                                             │   │
│  │                 │  │  [Ver más facturas...]                      │   │
│  │                 │  │                                             │   │
│  └─────────────────┘  └─────────────────────────────────────────────┘   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 18. Admin Dashboard (`/admin`)

```
┌─────────────────────────────────────────────────────────────────────────┐
│  [Logo MOL]  ADMIN                                         [Logout]     │
├────────────────┬────────────────────────────────────────────────────────┤
│                │                                                        │
│  Dashboard  ●  │  Estado del Sistema                                    │
│  Usuarios      │                                                        │
│  Issues        │  ┌─────────────────────────────────────────────────┐   │
│  Skills        │  │ FASE 1: SCRAPING                    ● Online    │   │
│  Scraping      │  │                                                 │   │
│  Métricas      │  │ Última ejecución: Hace 2 horas                  │   │
│  Logs          │  │ Ofertas nuevas hoy: 234                         │   │
│  Config        │  │ Fuentes activas: 5/5                            │   │
│                │  └─────────────────────────────────────────────────┘   │
│                │                                                        │
│                │  ┌─────────────────────────────────────────────────┐   │
│                │  │ FASE 2: PROCESAMIENTO               ● Online    │   │
│                │  │                                                 │   │
│                │  │ NLP v11.3: 100% ofertas procesadas              │   │
│                │  │ Matching v3.4.2: 538 validadas                  │   │
│                │  │ Errores pendientes: 0                           │   │
│                │  └─────────────────────────────────────────────────┘   │
│                │                                                        │
│                │  ┌─────────────────────────────────────────────────┐   │
│                │  │ FASE 3: PRESENTACIÓN                ● Online    │   │
│                │  │                                                 │   │
│                │  │ Dashboard: mol-nextjs.vercel.app                │   │
│                │  │ Último deploy: Hace 1 día                       │   │
│                │  │ Supabase sync: 538 ofertas                      │   │
│                │  └─────────────────────────────────────────────────┘   │
│                │                                                        │
└────────────────┴────────────────────────────────────────────────────────┘
```

### 19. Admin Usuarios (`/admin/usuarios`)

```
┌─────────────────────────────────────────────────────────────────────────┐
│  [Logo MOL]  ADMIN                                         [Logout]     │
├────────────────┬────────────────────────────────────────────────────────┤
│                │                                                        │
│  Dashboard     │  Gestión de Usuarios                   [+ Nuevo]      │
│  Usuarios   ●  │                                                        │
│  Issues        │  Buscar: [                    ] [🔍]                   │
│  Skills        │  Filtrar: [Todos ▼] [Activos ▼]                       │
│  Scraping      │                                                        │
│  Métricas      │  ┌────────────────────────────────────────────────┐   │
│  Logs          │  │ Usuario          │ Plan   │ Estado  │ Acciones│   │
│  Config        │  ├──────────────────┼────────┼─────────┼─────────┤   │
│                │  │ juan@empresa.com │ PRO    │ ● Activo│ [✏][🗑] │   │
│                │  │ maria@consul.com │ PRO    │ ● Activo│ [✏][🗑] │   │
│                │  │ pedro@test.com   │ FREE   │ ● Activo│ [✏][🗑] │   │
│                │  │ ana@corp.com     │ ENTERP.│ ● Activo│ [✏][🗑] │   │
│                │  │ luis@demo.com    │ FREE   │ ○ Inact.│ [✏][🗑] │   │
│                │  └────────────────────────────────────────────────┘   │
│                │                                                        │
│                │  Mostrando 5 de 156 usuarios         [< 1 2 3 ... >]  │
│                │                                                        │
│                │  ─────────────────────────────────────────────────     │
│                │                                                        │
│                │  RESUMEN                                               │
│                │  Total: 156 | Free: 89 | Pro: 52 | Enterprise: 15     │
│                │  MRR: $930,000 ARS                                     │
│                │                                                        │
└────────────────┴────────────────────────────────────────────────────────┘
```

### 20. Admin Issues (`/admin/issues`)

```
┌─────────────────────────────────────────────────────────────────────────┐
│  [Logo MOL]  ADMIN                                         [Logout]     │
├────────────────┬────────────────────────────────────────────────────────┤
│                │                                                        │
│  Dashboard     │  Issues y Feedback                                     │
│  Usuarios      │                                                        │
│  Issues     ●  │  Filtrar: [Todos ▼] [Pendiente ▼] [Alta ▼]            │
│  Skills        │                                                        │
│  Scraping      │  ┌─────────────────────────────────────────────────┐   │
│  Métricas      │  │                                                 │   │
│  Logs          │  │  🔴 #45 - Error ISCO en oferta 12345            │   │
│  Config        │  │  Tipo: error_isco | Prioridad: Alta             │   │
│  │  │  Reportado: juan@empresa.com | Hace 2 horas       │   │
│                │  │  [Ver detalle] [Resolver] [Agrupar]             │   │
│                │  │                                                 │   │
│                │  ├─────────────────────────────────────────────────┤   │
│                │  │                                                 │   │
│                │  │  🟡 #44 - Sugerencia: agregar filtro por skill  │   │
│                │  │  Tipo: sugerencia | Prioridad: Media            │   │
│                │  │  Reportado: maria@test.com | Hace 1 día         │   │
│                │  │  [Ver detalle] [Resolver] [Agrupar]             │   │
│                │  │                                                 │   │
│                │  ├─────────────────────────────────────────────────┤   │
│                │  │                                                 │   │
│                │  │  🟢 #43 - Error de visualización en móvil       │   │
│                │  │  Tipo: bug | Prioridad: Baja                    │   │
│                │  │  Reportado: admin@oede.gob.ar | Hace 3 días     │   │
│                │  │  [Ver detalle] [Resolver] [Agrupar]             │   │
│                │  │                                                 │   │
│                │  └─────────────────────────────────────────────────┘   │
│                │                                                        │
│                │  Pendientes: 12 | Resueltos hoy: 3 | Total: 45        │
│                │                                                        │
└────────────────┴────────────────────────────────────────────────────────┘
```

### 21. Admin Skills Intelligence (`/admin/skills`) - 6 tabs

```
┌─────────────────────────────────────────────────────────────────────────┐
│  [Logo MOL]  ADMIN                                         [Logout]     │
├────────────────┬────────────────────────────────────────────────────────┤
│                │                                                        │
│  Dashboard     │  Skills Intelligence (Interno)                         │
│  Usuarios      │                                                        │
│  Issues        │  [Taxonomía] [Ocupación] [Comparar] [Mis Skills]       │
│  Skills     ●  │  [Perfil Argentina] [Consolidado]                      │
│  Scraping      │  ═══════════════════                                   │
│  Métricas      │                                                        │
│  Logs          │  PERFIL ARGENTINA (tab activo)                         │
│  Config        │                                                        │
│                │  Skills más demandadas en Argentina (MOL data)         │
│                │                                                        │
│                │  ┌─────────────────────────────────────────────────┐   │
│                │  │ # │ Skill              │ Ofertas │ Tendencia   │   │
│                │  ├───┼────────────────────┼─────────┼─────────────┤   │
│                │  │ 1 │ Microsoft Excel    │   2,345 │ ↑ +12%      │   │
│                │  │ 2 │ Comunicación       │   1,890 │ ↑ +8%       │   │
│                │  │ 3 │ Inglés             │   1,567 │ → 0%        │   │
│                │  │ 4 │ Python             │   1,234 │ ↑ +25%      │   │
│                │  │ 5 │ SAP                │     987 │ ↓ -5%       │   │
│                │  └─────────────────────────────────────────────────┘   │
│                │                                                        │
│                │  ┌──────────────────┐ ┌──────────────────┐             │
│                │  │ POR CATEGORÍA L1 │ │ SKILLS EMERGENTES│             │
│                │  │ S: Soft    45%   │ │ 1. IA Gen.  +150%│             │
│                │  │ T: Tech    30%   │ │ 2. LLMs     +120%│             │
│                │  │ K: Conocim.15%   │ │ 3. Next.js   +80%│             │
│                │  │ A: Actitud.10%   │ │ 4. Rust      +60%│             │
│                │  └──────────────────┘ └──────────────────┘             │
│                │                                                        │
└────────────────┴────────────────────────────────────────────────────────┘
```

### 22. Admin Scraping (`/admin/scraping`)

```
┌─────────────────────────────────────────────────────────────────────────┐
│  [Logo MOL]  ADMIN                                         [Logout]     │
├────────────────┬────────────────────────────────────────────────────────┤
│                │                                                        │
│  Dashboard     │  Estado de Scraping                                    │
│  Usuarios      │                                                        │
│  Issues        │  Última actualización: 05/02/2026 14:30                │
│  Skills        │                                                        │
│  Scraping   ●  │  ┌─────────────────────────────────────────────────┐   │
│  Métricas      │  │ Fuente      │ Estado  │ Última    │ Ofertas    │   │
│  Logs          │  │             │         │ ejecución │ hoy        │   │
│  Config        │  ├─────────────┼─────────┼───────────┼────────────┤   │
│                │  │ Bumeran     │ ● OK    │ Hace 2h   │ 89         │   │
│                │  │ ZonaJobs    │ ● OK    │ Hace 2h   │ 67         │   │
│                │  │ Computrabajo│ ● OK    │ Hace 2h   │ 45         │   │
│                │  │ Indeed      │ ● OK    │ Hace 2h   │ 23         │   │
│                │  │ LinkedIn    │ ○ WARN  │ Hace 4h   │ 10         │   │
│                │  └─────────────────────────────────────────────────┘   │
│                │                                                        │
│                │  ┌─────────────────────────────────────────────────┐   │
│                │  │         OFERTAS SCRAPEADAS (últimos 7 días)     │   │
│                │  │   300 ┤                              ██         │   │
│                │  │   250 ┤                    ██        ██         │   │
│                │  │   200 ┤          ██        ██   ██   ██         │   │
│                │  │   150 ┤     ██   ██   ██   ██   ██   ██         │   │
│                │  │   100 ┼─────────────────────────────────        │   │
│                │  │        Lun  Mar  Mié  Jue  Vie  Sáb  Dom        │   │
│                │  └─────────────────────────────────────────────────┘   │
│                │                                                        │
│                │  Bajas detectadas hoy: 34 | Duplicados: 12             │
│                │                                                        │
└────────────────┴────────────────────────────────────────────────────────┘
```

### 23. Admin Métricas (`/admin/metricas`)

```
┌─────────────────────────────────────────────────────────────────────────┐
│  [Logo MOL]  ADMIN                                         [Logout]     │
├────────────────┬────────────────────────────────────────────────────────┤
│                │                                                        │
│  Dashboard     │  Métricas del Pipeline                                 │
│  Usuarios      │                                                        │
│  Issues        │  Período: [Última semana ▼]                           │
│  Skills        │                                                        │
│  Scraping      │  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐          │
│  Métricas   ●  │  │ 2,345  │ │ 99.2%  │ │ 95.8%  │ │  538   │          │
│  Logs          │  │ofertas │ │NLP OK  │ │Match OK│ │validado│          │
│  Config        │  │ proces.│ │        │ │        │ │        │          │
│                │  └────────┘ └────────┘ └────────┘ └────────┘          │
│                │                                                        │
│                │  NLP PIPELINE v11.3                                    │
│                │  ┌─────────────────────────────────────────────────┐   │
│                │  │ Campo           │ Precision │ Trend            │   │
│                │  ├─────────────────┼───────────┼──────────────────┤   │
│                │  │ titulo_limpio   │ 99.5%     │ ↑ +0.3%          │   │
│                │  │ provincia       │ 98.2%     │ → 0%             │   │
│                │  │ skills_tecnicas │ 96.1%     │ ↑ +2.1%          │   │
│                │  │ nivel_seniority │ 94.5%     │ ↑ +1.2%          │   │
│                │  └─────────────────────────────────────────────────┘   │
│                │                                                        │
│                │  MATCHING v3.4.2                                       │
│                │  ┌─────────────────────────────────────────────────┐   │
│                │  │ Por regla: 81% | Por diccionario: 4%            │   │
│                │  │ Por semántico: 15%                              │   │
│                │  │ Reglas de negocio: 132 | Convergencia: 100%     │   │
│                │  └─────────────────────────────────────────────────┘   │
│                │                                                        │
└────────────────┴────────────────────────────────────────────────────────┘
```

### 24. Admin Logs (`/admin/logs`)

```
┌─────────────────────────────────────────────────────────────────────────┐
│  [Logo MOL]  ADMIN                                         [Logout]     │
├────────────────┬────────────────────────────────────────────────────────┤
│                │                                                        │
│  Dashboard     │  Audit Logs                                            │
│  Usuarios      │                                                        │
│  Issues        │  Filtrar: [Todos ▼] [Hoy ▼] [Buscar...]              │
│  Skills        │                                                        │
│  Scraping      │  ┌─────────────────────────────────────────────────┐   │
│  Métricas      │  │                                                 │   │
│  Logs       ●  │  │  14:32:15 │ INFO  │ Scraping completado        │   │
│  Config        │  │           │       │ bumeran: 89 ofertas nuevas │   │
│                │  │                                                 │   │
│                │  │  14:30:00 │ INFO  │ Scraping iniciado          │   │
│                │  │           │       │ Fuentes: 5                  │   │
│                │  │                                                 │   │
│                │  │  12:15:43 │ WARN  │ LinkedIn rate limit        │   │
│                │  │           │       │ Retry en 5 minutos          │   │
│                │  │                                                 │   │
│                │  │  10:00:00 │ INFO  │ Pipeline NLP completado    │   │
│                │  │           │       │ 234 ofertas procesadas      │   │
│                │  │                                                 │   │
│                │  │  09:45:22 │ INFO  │ Usuario login              │   │
│                │  │           │       │ juan@empresa.com            │   │
│                │  │                                                 │   │
│                │  │  09:30:00 │ INFO  │ Backup BD completado       │   │
│                │  │           │       │ ofertas_backup_20260205.db  │   │
│                │  │                                                 │   │
│                │  └─────────────────────────────────────────────────┘   │
│                │                                                        │
│                │  [Cargar más...]        Exportar: [JSON] [CSV]        │
│                │                                                        │
└────────────────┴────────────────────────────────────────────────────────┘
```

### 25. Admin Configuración (`/admin/configuracion`)

```
┌─────────────────────────────────────────────────────────────────────────┐
│  [Logo MOL]  ADMIN                                         [Logout]     │
├────────────────┬────────────────────────────────────────────────────────┤
│                │                                                        │
│  Dashboard     │  Configuración del Sistema                             │
│  Usuarios      │                                                        │
│  Issues        │  [General] [Scraping] [NLP] [Matching] [Email] [API]  │
│  Skills        │  ════════                                              │
│  Scraping      │                                                        │
│  Métricas      │  GENERAL (tab activo)                                  │
│  Logs          │                                                        │
│  Config     ●  │  ┌─────────────────────────────────────────────────┐   │
│                │  │                                                 │   │
│                │  │  Nombre del sitio                               │   │
│                │  │  ┌───────────────────────────────────────────┐  │   │
│                │  │  │ MOL - Monitor de Ofertas Laborales        │  │   │
│                │  │  └───────────────────────────────────────────┘  │   │
│                │  │                                                 │   │
│                │  │  URL base                                       │   │
│                │  │  ┌───────────────────────────────────────────┐  │   │
│                │  │  │ https://mol-nextjs.vercel.app             │  │   │
│                │  │  └───────────────────────────────────────────┘  │   │
│                │  │                                                 │   │
│                │  │  Modo mantenimiento                             │   │
│                │  │  [ ] Activar modo mantenimiento                 │   │
│                │  │                                                 │   │
│                │  │  Registro de usuarios                           │   │
│                │  │  [●] Abierto  [ ] Solo invitación  [ ] Cerrado │   │
│                │  │                                                 │   │
│                │  │  [         Guardar cambios         ]            │   │
│                │  │                                                 │   │
│                │  └─────────────────────────────────────────────────┘   │
│                │                                                        │
└────────────────┴────────────────────────────────────────────────────────┘
```

---

## MODELO DE DATOS (Supabase)

### Tablas Nuevas

```sql
-- =============================================
-- TABLA: planes
-- Definición de planes de suscripción
-- =============================================
CREATE TABLE planes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  nombre VARCHAR(50) NOT NULL,           -- 'free', 'pro', 'enterprise'
  nombre_display VARCHAR(100) NOT NULL,  -- 'Free', 'Pro', 'Enterprise'
  precio_mensual DECIMAL(10,2),          -- NULL para free y enterprise
  precio_anual DECIMAL(10,2),
  moneda VARCHAR(3) DEFAULT 'ARS',
  dias_historico INTEGER,                -- 7 para free, NULL para ilimitado
  features JSONB,                        -- Array de features incluidas
  limite_exports INTEGER,                -- NULL = ilimitado
  limite_alertas INTEGER,
  tiene_api BOOLEAN DEFAULT FALSE,
  activo BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Datos iniciales
INSERT INTO planes (nombre, nombre_display, precio_mensual, dias_historico, features) VALUES
('free', 'Free', 0, 7, '["dashboard", "skills_basico"]'),
('pro', 'Pro', 15000, NULL, '["dashboard", "skills_full", "exports", "alertas", "empresas"]'),
('enterprise', 'Enterprise', NULL, NULL, '["todo", "api", "soporte_dedicado"]');

-- =============================================
-- TABLA: suscripciones
-- Suscripciones activas de usuarios
-- =============================================
CREATE TABLE suscripciones (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  plan_id UUID REFERENCES planes(id),
  estado VARCHAR(20) NOT NULL,           -- 'activa', 'cancelada', 'vencida', 'trial'
  fecha_inicio TIMESTAMPTZ NOT NULL,
  fecha_fin TIMESTAMPTZ,                 -- NULL = indefinida (free)
  fecha_proximo_cobro TIMESTAMPTZ,
  mp_subscription_id VARCHAR(100),       -- ID de MercadoPago
  mp_payer_id VARCHAR(100),
  metadata JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),

  UNIQUE(user_id)                        -- Un usuario = una suscripción activa
);

-- =============================================
-- TABLA: pagos
-- Historial de pagos
-- =============================================
CREATE TABLE pagos (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  suscripcion_id UUID REFERENCES suscripciones(id),
  user_id UUID REFERENCES auth.users(id),
  monto DECIMAL(10,2) NOT NULL,
  moneda VARCHAR(3) DEFAULT 'ARS',
  estado VARCHAR(20) NOT NULL,           -- 'pendiente', 'aprobado', 'rechazado', 'reembolsado'
  mp_payment_id VARCHAR(100),
  mp_status VARCHAR(50),
  mp_status_detail VARCHAR(100),
  metodo_pago VARCHAR(50),               -- 'credit_card', 'debit_card', 'bank_transfer'
  fecha_pago TIMESTAMPTZ,
  metadata JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================
-- TABLA: alertas_config
-- Configuración de alertas por usuario
-- =============================================
CREATE TABLE alertas_config (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  nombre VARCHAR(100) NOT NULL,
  tipo VARCHAR(50) NOT NULL,             -- 'ocupacion', 'skill', 'empresa', 'provincia'
  criterios JSONB NOT NULL,              -- {ocupacion_id: 'xxx', umbral: 10}
  frecuencia VARCHAR(20) DEFAULT 'diaria', -- 'inmediata', 'diaria', 'semanal'
  activa BOOLEAN DEFAULT TRUE,
  ultima_ejecucion TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================
-- TABLA: informes_publicos
-- Informes PDF publicados
-- =============================================
CREATE TABLE informes_publicos (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  titulo VARCHAR(200) NOT NULL,
  descripcion TEXT,
  categoria VARCHAR(50),                 -- 'mensual', 'trimestral', 'especial'
  fecha_publicacion DATE NOT NULL,
  archivo_url TEXT NOT NULL,             -- URL del PDF en storage
  miniatura_url TEXT,
  descargas INTEGER DEFAULT 0,
  activo BOOLEAN DEFAULT TRUE,
  metadata JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================
-- VISTA: v_usuarios_con_plan
-- Usuarios con su plan actual
-- =============================================
CREATE VIEW v_usuarios_con_plan AS
SELECT
  u.id as user_id,
  u.email,
  u.raw_user_meta_data->>'nombre' as nombre,
  u.raw_user_meta_data->>'empresa' as empresa,
  COALESCE(p.nombre, 'free') as plan,
  s.estado as estado_suscripcion,
  s.fecha_fin,
  p.dias_historico
FROM auth.users u
LEFT JOIN suscripciones s ON u.id = s.user_id AND s.estado = 'activa'
LEFT JOIN planes p ON s.plan_id = p.id;
```

### Tablas Existentes a Modificar

```sql
-- Agregar campo de plan requerido a user_metadata
-- Se maneja en el registro, no necesita ALTER

-- Agregar tracking de uso para limitar features
CREATE TABLE uso_features (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users(id),
  feature VARCHAR(50) NOT NULL,          -- 'export', 'alerta', 'api_call'
  fecha DATE DEFAULT CURRENT_DATE,
  cantidad INTEGER DEFAULT 1,
  metadata JSONB,

  UNIQUE(user_id, feature, fecha)
);

-- Función para verificar límites
CREATE OR REPLACE FUNCTION check_feature_limit(
  p_user_id UUID,
  p_feature VARCHAR,
  p_limite INTEGER
) RETURNS BOOLEAN AS $$
DECLARE
  v_usado INTEGER;
BEGIN
  IF p_limite IS NULL THEN RETURN TRUE; END IF;

  SELECT COALESCE(SUM(cantidad), 0) INTO v_usado
  FROM uso_features
  WHERE user_id = p_user_id
    AND feature = p_feature
    AND fecha >= DATE_TRUNC('month', CURRENT_DATE);

  RETURN v_usado < p_limite;
END;
$$ LANGUAGE plpgsql;
```

---

## FLUJOS DE USUARIO

### Flujo 1: Visitante → Usuario Free

```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│  1. DESCUBRIMIENTO                                                       │
│     ┌─────────┐                                                          │
│     │ Landing │ ──→ Ve features, precios, CTA                           │
│     └────┬────┘                                                          │
│          │                                                               │
│          ▼                                                               │
│  2. REGISTRO                                                             │
│     ┌─────────┐     ┌─────────┐     ┌─────────┐                         │
│     │ Click   │ ──→ │ Form    │ ──→ │ Email   │                         │
│     │ "Free"  │     │ registro│     │ confirm │                         │
│     └─────────┘     └─────────┘     └────┬────┘                         │
│                                          │                               │
│                                          ▼                               │
│  3. ONBOARDING                                                           │
│     ┌─────────┐     ┌─────────┐     ┌─────────┐                         │
│     │ Welcome │ ──→ │ Tour    │ ──→ │Dashboard│                         │
│     │ screen  │     │ guiado  │     │ (7 días)│                         │
│     └─────────┘     └─────────┘     └─────────┘                         │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Flujo 2: Usuario Free → Pro

```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│  1. TRIGGER (cualquiera de estos)                                        │
│     ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                   │
│     │ Intenta     │  │ Ve banner   │  │ Click en    │                   │
│     │ exportar    │  │ "Upgrade"   │  │ "Ver más"   │                   │
│     └──────┬──────┘  └──────┬──────┘  └──────┬──────┘                   │
│            │                │                │                           │
│            └────────────────┼────────────────┘                           │
│                             ▼                                            │
│  2. UPGRADE MODAL                                                        │
│     ┌─────────────────────────────┐                                      │
│     │  "Desbloqueá todas las      │                                      │
│     │   funcionalidades"          │                                      │
│     │                             │                                      │
│     │  [Ver planes] [Ahora no]    │                                      │
│     └──────────────┬──────────────┘                                      │
│                    │                                                     │
│                    ▼                                                     │
│  3. CHECKOUT                                                             │
│     ┌─────────┐     ┌─────────────┐     ┌─────────┐                     │
│     │ Página  │ ──→ │ MercadoPago │ ──→ │ Éxito   │                     │
│     │ precios │     │ checkout    │     │ redirect│                     │
│     └─────────┘     └─────────────┘     └────┬────┘                     │
│                                              │                           │
│                                              ▼                           │
│  4. ACTIVACIÓN                                                           │
│     ┌─────────────────────────────────────────────┐                     │
│     │  ✓ Plan actualizado                         │                     │
│     │  ✓ Acceso a histórico completo              │                     │
│     │  ✓ Email de confirmación enviado            │                     │
│     │                                             │                     │
│     │  [Ir al Dashboard]                          │                     │
│     └─────────────────────────────────────────────┘                     │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Flujo 3: Usuario Pro usa Dashboard

```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│  1. LOGIN                                                                │
│     ┌─────────┐     ┌─────────────┐                                     │
│     │ Login   │ ──→ │ Verificar   │ ──→ Plan PRO activo ✓               │
│     │ page    │     │ suscripción │                                     │
│     └─────────┘     └─────────────┘                                     │
│                                                                          │
│  2. NAVEGACIÓN TÍPICA                                                    │
│                                                                          │
│     ┌──────────────────────────────────────────────────────────┐        │
│     │                                                          │        │
│     │  Dashboard ←──────→ Skills ←──────→ Empresas             │        │
│     │      │                 │                │                │        │
│     │      ▼                 ▼                ▼                │        │
│     │  Filtrar datos    Comparar         Buscar empresa        │        │
│     │      │            ocupaciones           │                │        │
│     │      ▼                 │                ▼                │        │
│     │  Ver ofertas           │            Ver detalle          │        │
│     │      │                 │                │                │        │
│     │      └────────────────┬┴────────────────┘                │        │
│     │                       │                                  │        │
│     │                       ▼                                  │        │
│     │               ┌─────────────┐                            │        │
│     │               │  EXPORTAR   │                            │        │
│     │               │  Excel/PDF  │                            │        │
│     │               └─────────────┘                            │        │
│     │                                                          │        │
│     └──────────────────────────────────────────────────────────┘        │
│                                                                          │
│  3. CONFIGURAR ALERTA                                                    │
│     ┌─────────┐     ┌─────────────┐     ┌─────────────┐                 │
│     │ Alertas │ ──→ │ Nueva alerta│ ──→ │ Confirmar   │                 │
│     │ page    │     │ ocupación X │     │ frecuencia  │                 │
│     └─────────┘     └─────────────┘     └─────────────┘                 │
│                                              │                           │
│                                              ▼                           │
│                                      Email cuando hay                    │
│                                      nuevas ofertas                      │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Flujo 4: Webhook MercadoPago

```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│  PAGO APROBADO                                                           │
│                                                                          │
│  MercadoPago ──→ POST /api/webhooks/mercadopago                         │
│       │                    │                                             │
│       │                    ▼                                             │
│       │         ┌─────────────────────┐                                 │
│       │         │ Verificar firma     │                                 │
│       │         │ (seguridad)         │                                 │
│       │         └──────────┬──────────┘                                 │
│       │                    │                                             │
│       │                    ▼                                             │
│       │         ┌─────────────────────┐                                 │
│       │         │ Buscar suscripción  │                                 │
│       │         │ por mp_subscription │                                 │
│       │         └──────────┬──────────┘                                 │
│       │                    │                                             │
│       │                    ▼                                             │
│       │         ┌─────────────────────┐                                 │
│       │         │ Actualizar estado   │                                 │
│       │         │ suscripcion='activa'│                                 │
│       │         └──────────┬──────────┘                                 │
│       │                    │                                             │
│       │                    ▼                                             │
│       │         ┌─────────────────────┐                                 │
│       │         │ Insertar en pagos   │                                 │
│       │         │ estado='aprobado'   │                                 │
│       │         └──────────┬──────────┘                                 │
│       │                    │                                             │
│       │                    ▼                                             │
│       │         ┌─────────────────────┐                                 │
│       │         │ Enviar email        │                                 │
│       │         │ confirmación        │                                 │
│       │         └─────────────────────┘                                 │
│                                                                          │
│  ─────────────────────────────────────────────────────────────────────  │
│                                                                          │
│  PAGO RECHAZADO                                                          │
│                                                                          │
│  MercadoPago ──→ POST /api/webhooks/mercadopago                         │
│                            │                                             │
│                            ▼                                             │
│                  ┌─────────────────────┐                                │
│                  │ Insertar en pagos   │                                │
│                  │ estado='rechazado'  │                                │
│                  └──────────┬──────────┘                                │
│                             │                                            │
│                             ▼                                            │
│                  ┌─────────────────────┐                                │
│                  │ Enviar email        │                                │
│                  │ "Problema con pago" │                                │
│                  └─────────────────────┘                                │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## PRÓXIMO PASO INMEDIATO

**FASE 1:** Crear las 13 páginas faltantes como placeholders para poder navegar el sistema completo y visualizar la arquitectura.

**Orden de implementación:**
1. Crear estructura de carpetas
2. Landing page (placeholder)
3. Registro (placeholder)
4. Precios (placeholder)
5. Checkout (placeholder)
6. Mi Cuenta (placeholder)
7. Empresas (placeholder)
8. Reportes (placeholder)
9. Alertas (placeholder)

**Después de placeholders:**
- Implementar MercadoPago
- Implementar restricciones por plan
- Diseñar informes PDF
