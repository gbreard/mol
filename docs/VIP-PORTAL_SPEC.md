# VIP-PORTAL — Portal de Inversores

## Contexto

Portal dedicado para inversores. Rol nuevo `visit_vip` en user_metadata.
Ven datos reales. Acceden a secciones existentes del sistema con navegación
controlada — no se duplica ninguna página ni componente.

---

## Pre-condición — Gerardo crea cuentas VIP en Supabase

Para cada inversor:
```sql
-- 1. Crear usuario desde Supabase Dashboard → Auth → Invite user
-- 2. Asignar rol:
UPDATE auth.users 
SET raw_user_meta_data = raw_user_meta_data || '{"role": "visit_vip", "plan": "enterprise"}'
WHERE email = 'inversor@ejemplo.com';
```

---

## Parte 1 — Middleware: aislamiento

**En middleware.ts**, agregar:

```typescript
// VIP gating: /vip/* solo para visit_vip + admin
const isVipRoute = request.nextUrl.pathname.startsWith('/vip')
if (isVipRoute && user) {
  const role = (user.user_metadata?.role as string) || 'viewer'
  if (role !== 'visit_vip' && role !== 'admin' && role !== 'super_admin') {
    return NextResponse.redirect(new URL('/home', request.url))
  }
}

// Bloquear VIP del sistema principal
const isMainSystemRoute = 
  request.nextUrl.pathname.startsWith('/dashboard') ||
  request.nextUrl.pathname.startsWith('/admin') ||
  request.nextUrl.pathname.startsWith('/skills') ||
  request.nextUrl.pathname.startsWith('/mi-futuro-laboral')

if (isMainSystemRoute && user) {
  const role = (user.user_metadata?.role as string) || 'viewer'
  if (role === 'visit_vip') {
    return NextResponse.redirect(new URL('/vip', request.url))
  }
}
```

**Nota:** `/oficina-empleo` y `/contenido` NO se bloquean para VIP —
se accede desde el portal VIP directamente a esas rutas existentes.

---

## Parte 2 — GlobalNav: agregar visit_vip

**En components/navigation/GlobalNav.tsx**, modificar NAV_ITEMS:

```typescript
const NAV_ITEMS: NavItem[] = [
  // Items existentes — no tocar
  { label: "Inicio",         href: "/home",            roles: "*" },
  { label: "Dashboard",      href: "/dashboard",        roles: ["super_admin","admin","analyst","viewer"], plans: ["pro","enterprise","trial"] },
  { label: "Contenido",      href: "/contenido",        roles: ["super_admin","admin","analyst","viewer","oficina_empleo"] },
  { label: "Skills",         href: "/admin/skills",     roles: ["super_admin","admin","oficina_empleo"] },
  { label: "Oficina Empleo", href: "/oficina-empleo",   roles: ["super_admin","admin","oficina_empleo"] },
  { label: "Mi Futuro",      href: "/mi-futuro-laboral",roles: "*" },
  { label: "Admin",          href: "/admin",            roles: ["super_admin","admin"] },

  // Items nuevos para visit_vip
  { label: "Inicio",            href: "/vip",              roles: ["visit_vip"] },
  { label: "Dashboard",         href: "/vip/dashboard",    roles: ["visit_vip"] },
  { label: "Oficina de Empleo", href: "/oficina-empleo",   roles: ["visit_vip"] },
  { label: "Políticas Laborales",href: "/vip/politicas",   roles: ["visit_vip"] },
  { label: "Informes",          href: "/contenido",        roles: ["visit_vip"] },
]
```

Agregar badge de rol para visit_vip: `"Inversor"` (igual que existe
`"Administrador"` y `"Oficina de Empleo"`).

---

## Parte 3 — Página de Inicio (/vip)

**Archivo:** `app/vip/page.tsx`

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  Inteligencia del Mercado Laboral Argentino en Tiempo Real      │
│  Herramientas diseñadas para transformar datos dispersos        │
│  en inteligencia accionable                                     │
│                                                                 │
├──────────────┬──────────────┬──────────────────┬───────────────┤
│  📊          │  🏢          │  ⚖️              │  📄           │
│  Dashboard   │  Oficina de  │  Políticas       │  Informes     │
│              │  Empleo      │  Laborales       │               │
│  Panorama    │  Diagnóstico │  Inteligencia    │  Reportes y   │
│  del mercado │  y matching  │  de mercado y    │  análisis     │
│  laboral     │  de skills   │  políticas       │               │
│  argentino   │              │  basadas en      │               │
│              │              │  datos           │               │
│  [Abrir →]   │  [Abrir →]   │  [Abrir →]       │  [Abrir →]    │
└──────────────┴──────────────┴──────────────────┴───────────────┘
```

Texto: reutilizar h1 y párrafo de la landing existente (`/`).
Cards: mismo estilo visual que las cards de `/oficina-empleo` hub.
Links de las cards: a `/vip/dashboard`, `/oficina-empleo`,
`/vip/politicas`, `/contenido`.

---

## Parte 4 — Dashboard (/vip/dashboard)

**Archivo:** `app/vip/dashboard/page.tsx`

Versión recortada de M4 (`/oficina-empleo/dashboard-ejecutivo`).
Importar solo los bloques necesarios — no modificar M4 original.

**Mostrar:**
- Filtros: Territorio + Período (igual que M4)
- Bloque KPIs: ofertas activas, ocupaciones distintas, empresas, provincias
- Bloque Brecha de Formación (experimental)
- Bloque Indicadores de Laboratorio con links a `/vip/laboratorio/*`

**No mostrar:**
- Sectores con mayor demanda
- Evolución de ofertas publicadas
- Perfil de los puestos demandados
- Competencias más demandadas

**Laboratorio VIP:** los links del bloque de laboratorio apuntan a
`/vip/laboratorio/[indicador]` — crear esas rutas copiando las páginas
de `/oficina-empleo/laboratorio/*` con el mismo patrón que ya existe.

---

## Parte 5 — Políticas Laborales (/vip/politicas)

**Archivo:** `app/vip/politicas/page.tsx`

Dos secciones en una página con tabs o scroll:

### Sección 1 — Inteligencia de Mercado
Mismos KPIs + Brecha + Laboratorio que el Dashboard VIP.
Reutilizar los mismos componentes — no duplicar lógica.

### Sección 2 — Skills Intelligence

```
┌─────────────────────────────────────────────────────────────────┐
│  Skills Intelligence                                            │
│  [Ocupaciones ●]  [Comparar]                                    │
├─────────────────────────────────────────────────────────────────┤
│  Tab activo renderiza OccupationDetail o OccupationCompare      │
└─────────────────────────────────────────────────────────────────┘
```

Importar directamente:
- `OccupationDetail` de `@/components/OccupationDetail`
- `OccupationCompare` de `@/components/OccupationCompare`

Reducir font-size base a 13px en esta sección (wrapper con
`className="text-[13px]"`) para alinearse al estilo compacto de M4.

Necesita los datos de `occupationsData` (occupation_full_detail.json)
y `occupationsList` — cargarlos igual que en `/admin/skills`.

---

## Laboratorio VIP (/vip/laboratorio/*)

Copiar las 7 páginas de `/oficina-empleo/laboratorio/*` bajo
`/vip/laboratorio/*` cambiando solo:
- El link "Volver" de `/oficina-empleo` a `/vip/dashboard`
- El breadcrumb raíz de "Oficina de Empleo" a "Dashboard"

Mismo patrón que cuando se creó `/oficina-empleo/laboratorio`
desde `/admin/laboratorio`.

---

## Criterios de aceptación

**Aislamiento:**
- [ ] `visit_vip` → `/dashboard` redirige a `/vip`
- [ ] `visit_vip` → `/admin` redirige a `/vip`
- [ ] `visit_vip` → `/skills` redirige a `/vip`
- [ ] `viewer` → `/vip` redirige a `/home`

**Navegación:**
- [ ] GlobalNav muestra 5 items para visit_vip (Inicio, Dashboard,
      Oficina de Empleo, Políticas Laborales, Informes)
- [ ] GlobalNav muestra badge "Inversor" para visit_vip
- [ ] "Salir" en el menú de usuario hace signOut → `/login`
- [ ] Items del sistema principal NO aparecen para visit_vip

**Contenido:**
- [ ] /vip: 4 cards con texto de bienvenida y links correctos
- [ ] /vip/dashboard: KPIs + Brecha + Laboratorio (sin sectores/evolución)
- [ ] /oficina-empleo: accesible para visit_vip, M1+M2+M3 funcionando
- [ ] /vip/politicas: M4 recortado + tabs Ocupaciones y Comparar
- [ ] /contenido: accesible para visit_vip

---

## Tests

`tests/vip-auth.test.ts`
- visit_vip accede a /vip → 200
- visit_vip accede a /dashboard → redirect /vip
- visit_vip accede a /admin → redirect /vip
- viewer accede a /vip → redirect /home

`tests/vip-nav.test.ts`
- GlobalNav con rol visit_vip muestra exactamente 5 items
- Badge "Inversor" visible
- Items de admin/dashboard/skills NO visibles para visit_vip

---

## Notas

- No duplicar `/oficina-empleo` — el VIP accede directamente a esa
  ruta existente. El middleware permite `visit_vip` en `/oficina-empleo`.

- DEV_BYPASS = true hace que el aislamiento no funcione en desarrollo.
  Para testear el portal VIP: crear usuario real con rol visit_vip
  en Supabase y desactivar DEV_BYPASS temporalmente.

- Los informes (`/contenido`) ya son accesibles para cualquier usuario
  logueado — no necesita cambio en el middleware.

- `/vip/politicas` carga `occupation_full_detail.json` (45MB).
  Aplicar lazy loading igual que en M3 — solo cargar al activar
  la sección de Skills Intelligence, no al montar la página.

---

## Parte 9 — Redirect post-login por rol

### app/login/page.tsx

Cambiar el redirect fijo a `/home` por uno dinámico según el rol:

```typescript
// Después del signInWithPassword exitoso:
const { data: { user } } = await supabase.auth.getUser()
const role = user?.user_metadata?.role || 'viewer'

if (role === 'visit_vip') {
  router.push('/vip')
} else if (role === 'oficina_empleo') {
  router.push('/oficina-empleo')
} else if (role === 'admin' || role === 'super_admin') {
  router.push('/admin')
} else {
  router.push('/home')
}
```

### middleware.ts

El bloque que redirige a usuarios logueados que visitan `/login`
(líneas 24-26) también tiene que diferenciar por rol:

```typescript
if (user && request.nextUrl.pathname === '/login') {
  const role = (user.user_metadata?.role as string) || 'viewer'
  const url = request.nextUrl.clone()
  url.pathname = role === 'visit_vip' ? '/vip' : '/home'
  return NextResponse.redirect(url)
}
```

### Criterios adicionales

- [ ] VIP hace login → redirige directo a `/vip` (no pasa por `/home`)
- [ ] VIP logueado visita `/login` → redirige a `/vip`
- [ ] Admin hace login → redirige a `/admin`
- [ ] Oficina empleo hace login → redirige a `/oficina-empleo`
- [ ] Viewer hace login → redirige a `/home` (igual que ahora)
