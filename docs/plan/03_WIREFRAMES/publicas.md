# Wireframes: Pantallas Públicas

> Última actualización: 2026-02-05

## Referencias

| Documento | Relación |
|-----------|----------|
| [02_ARQUITECTURA_PANTALLAS](../02_ARQUITECTURA_PANTALLAS.md) | Lista de pantallas P-01 a P-05 |
| [01_MODELO_NEGOCIO](../01_MODELO_NEGOCIO.md) | Define qué ve cada tipo de usuario |

---

## P-01: Landing Page (`/`)

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

---

## P-02: Precios (`/precios`)

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

---

## P-03: Informes Públicos (`/informes`)

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

---

## P-04: Login (`/login`)

**Estado:** ✅ Existe

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

---

## P-05: Registro (`/registro`)

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

---

## P-10: Skills Público (`/skills`)

**Estado:** ✅ Existe (versión limitada sin auth)

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
