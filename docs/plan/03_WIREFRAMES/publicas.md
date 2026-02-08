# Wireframes: Pantallas Públicas

> Última actualización: 2026-02-07
> Versión: 2.0 — Narrativa institucional OEDE + estructura SaaS

## Referencias

| Documento | Relación |
|-----------|----------|
| [02_ARQUITECTURA_PANTALLAS](../02_ARQUITECTURA_PANTALLAS.md) | Lista de pantallas P-01 a P-05 |
| [01_MODELO_NEGOCIO](../01_MODELO_NEGOCIO.md) | Define tipos de usuario y flujo de acceso |

## Origen del cambio

Propuesta de colegas OEDE (2026-02-07) en `docs/Wireframes_MOL_con_diagramas_comentarios.docx`:
- Narrativa institucional en vez de SaaS genérica
- 4 funcionalidades concretas alineadas al pipeline real
- Pricing simplificado (integrado con modelo híbrido v2.0)

---

## P-01: Landing Page (`/`)

**Cambios v2.0:** Hero con narrativa institucional, recuadros "Desafío/Solución", 4 funcionalidades reales.

```
┌─────────────────────────────────────────────────────────────────────────┐
│  [Logo MOL]                    Informes  Precios  [Iniciar Sesión]      │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│          ╔═══════════════════════════════════════════════════╗          │
│          ║                                                    ║          │
│          ║   Inteligencia de datos para un mercado de        ║          │
│          ║   trabajo y un sistema productivo en              ║          │
│          ║   transformación                                   ║          │
│          ║                                                    ║          │
│          ║   Sistematizamos la demanda de ocupaciones,       ║          │
│          ║   competencias y brechas de habilidades en        ║          │
│          ║   tiempo real para optimizar la toma de           ║          │
│          ║   decisiones de empresas, gobiernos y             ║          │
│          ║   trabajadores.                                    ║          │
│          ║                                                    ║          │
│          ║   [  Registrarse gratis  ]   [  Ver Informes  ]   ║          │
│          ║                                                    ║          │
│          ╚═══════════════════════════════════════════════════╝          │
│                                                                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌────────────────────────────────┐  ┌─────────────────────────────────┐│
│  │                                │  │                                 ││
│  │  EL DESAFÍO                    │  │  LA SOLUCIÓN MOL                ││
│  │                                │  │                                 ││
│  │  En un contexto de innovación  │  │  Una herramienta que utiliza    ││
│  │  tecnológica y reconversión    │  │  IA y webscraping para          ││
│  │  productiva, empresas,         │  │  transformar los datos de       ││
│  │  gobiernos y trabajadores      │  │  miles de vacantes publicadas   ││
│  │  deben reconocer los cambios   │  │  en la red en conocimiento      ││
│  │  en la demanda de habilidades  │  │  para el trabajo y la           ││
│  │  y competencias laborales.     │  │  producción.                    ││
│  │                                │  │                                 ││
│  └────────────────────────────────┘  └─────────────────────────────────┘│
│                                                                          │
├─────────────────────────────────────────────────────────────────────────┤
│                         NÚMEROS QUE HABLAN                               │
│                                                                          │
│    ┌──────────────┐   ┌──────────────┐   ┌──────────────┐               │
│    │   +13,000    │   │     300+     │   │    1,200+    │               │
│    │   ofertas    │   │  ocupaciones │   │    skills    │               │
│    │  analizadas  │   │    ESCO      │   │   mapeadas   │               │
│    └──────────────┘   └──────────────┘   └──────────────┘               │
│                                                                          │
├─────────────────────────────────────────────────────────────────────────┤
│                    PRINCIPALES FUNCIONALIDADES                           │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  📊 EVOLUCIÓN DE OFERTAS                                        │    │
│  │  Medimos la evolución de las ofertas laborales y sus            │    │
│  │  principales características a nivel nacional, provincial       │    │
│  │  y local.                                                        │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  🔍 OCUPACIONES Y COMPETENCIAS MÁS DEMANDADAS                   │    │
│  │  Detectamos cuáles son las ocupaciones y competencias más       │    │
│  │  solicitadas en el mercado argentino hoy, permitiendo           │    │
│  │  anticipar tendencias.                                           │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  📋 REQUISITOS Y COMPARACIÓN DE COMPETENCIAS                     │    │
│  │  Acceda a descripciones detalladas de los requisitos de         │    │
│  │  competencias para cada puesto y compare las diferencias        │    │
│  │  de habilidades entre distintas ocupaciones para optimizar      │    │
│  │  la formación.                                                   │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  🎯 MATCHING Y BRECHAS DE HABILIDADES                           │    │
│  │  El sistema identifica vacantes activas que coinciden con el    │    │
│  │  perfil del trabajador y señala la "brecha de habilidades"      │    │
│  │  necesaria para alcanzar el puesto deseado.                     │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
├─────────────────────────────────────────────────────────────────────────┤
│                            ACCESO                                        │
│                                                                          │
│  ┌─────────────────────┐   ┌───────────────────────────────────────┐    │
│  │                     │   │                                       │    │
│  │   REGISTRADO        │   │      TABLERO INTERACTIVO              │    │
│  │   $0                │   │      Consultar precio                 │    │
│  │                     │   │                                       │    │
│  │ ✓ Informes y notas  │   │ ✓ Todo de Registrado                 │    │
│  │ ✓ Análisis por      │   │ ✓ Dashboard interactivo              │    │
│  │   email             │   │ ✓ Histórico completo                 │    │
│  │ ✓ Contenido         │   │ ✓ Exports Excel/PDF                  │    │
│  │   periódico         │   │ ✓ Skills Intelligence                │    │
│  │                     │   │ ✓ Análisis de empresas               │    │
│  │                     │   │                                       │    │
│  │ [Registrarse]       │   │ [Solicitar acceso]                   │    │
│  │                     │   │                                       │    │
│  └─────────────────────┘   └───────────────────────────────────────┘    │
│                                                                          │
│    ¿Sos una institución? [Contactanos para un plan a medida]            │
│                                                                          │
├─────────────────────────────────────────────────────────────────────────┤
│  © 2026 MOL - OEDE                              Términos | Privacidad   │
└─────────────────────────────────────────────────────────────────────────┘
```

**Notas de diseño:**
- CTAs primarios: "Registrarse gratis" (hero) y "Solicitar acceso" (pricing)
- "Ver Informes" como CTA secundario lleva a P-03
- Sección pricing muestra 2 niveles visibles + link institucional
- Números reales del sistema (no inflados)

---

## P-02: Precios (`/precios`)

**Cambios v2.0:** 2 niveles visibles + institucional como contacto. Sin Free/Pro/Enterprise.

```
┌─────────────────────────────────────────────────────────────────────────┐
│  [Logo MOL]                    Informes  Precios  [Iniciar Sesión]      │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│                    Accedé a la inteligencia del                          │
│                       mercado laboral argentino                          │
│                                                                          │
│  ┌───────────────────────────────┐  ┌───────────────────────────────┐   │
│  │                               │  │                               │   │
│  │       REGISTRADO              │  │       TABLERO COMPLETO        │   │
│  │                               │  │                               │   │
│  │      Gratis                   │  │       $ (consultar)           │   │
│  │                               │  │                               │   │
│  ├───────────────────────────────┤  ├───────────────────────────────┤   │
│  │                               │  │                               │   │
│  │ ✓ Informes periódicos         │  │ ✓ Todo de Registrado          │   │
│  │ ✓ Notas y análisis por email  │  │ ✓ Dashboard interactivo       │   │
│  │ ✓ Contenido descargable       │  │ ✓ Filtros avanzados           │   │
│  │                               │  │ ✓ Histórico completo          │   │
│  │                               │  │ ✓ Export Excel/PDF            │   │
│  │                               │  │ ✓ Skills Intelligence         │   │
│  │                               │  │ ✓ Análisis de empresas        │   │
│  │                               │  │ ✓ Alertas por email           │   │
│  │                               │  │                               │   │
│  │ [ Registrarse gratis ]        │  │ [ Solicitar acceso ]          │   │
│  │                               │  │                               │   │
│  └───────────────────────────────┘  └───────────────────────────────┘   │
│                                                                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │                                                                   │  │
│  │  🏛️  INSTITUCIONES Y ORGANISMOS                                   │  │
│  │                                                                   │  │
│  │  Planes a medida para ministerios, universidades,                │  │
│  │  organismos internacionales y grandes consultoras.               │  │
│  │                                                                   │  │
│  │  Incluye: Tablero completo + API + documentos a demanda          │  │
│  │           + soporte dedicado                                      │  │
│  │                                                                   │  │
│  │  [  Contactar para más información  ]                             │  │
│  │                                                                   │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                                                          │
├─────────────────────────────────────────────────────────────────────────┤
│                         COMPARATIVA DETALLADA                            │
│                                                                          │
│  ┌────────────────────────────┬────────────┬───────────┬──────────────┐ │
│  │ Feature                    │ Registrado │  Tablero  │ Institucional│ │
│  ├────────────────────────────┼────────────┼───────────┼──────────────┤ │
│  │ Informes y notas           │     ✓      │     ✓     │      ✓       │ │
│  │ Email con contenido nuevo  │     ✓      │     ✓     │      ✓       │ │
│  │ Dashboard interactivo      │     ✗      │     ✓     │      ✓       │ │
│  │ Histórico completo         │     ✗      │     ✓     │      ✓       │ │
│  │ Skills Intelligence        │     ✗      │     ✓     │      ✓       │ │
│  │ Análisis de empresas       │     ✗      │     ✓     │      ✓       │ │
│  │ Export Excel/PDF           │     ✗      │     ✓     │      ✓       │ │
│  │ Alertas por email          │     ✗      │     ✓     │      ✓       │ │
│  │ API REST                   │     ✗      │     ✗     │      ✓       │ │
│  │ Documentos a demanda       │     ✗      │     ✗     │      ✓       │ │
│  │ Soporte                    │     -      │   Email   │   Dedicado   │ │
│  └────────────────────────────┴────────────┴───────────┴──────────────┘ │
│                                                                          │
├─────────────────────────────────────────────────────────────────────────┤
│                              FAQ                                         │
│                                                                          │
│  ▸ ¿Cómo funciona el período de prueba?                                 │
│    Al solicitar acceso al tablero, recibís 7 días de prueba gratis     │
│    una vez que tu solicitud sea aprobada.                               │
│                                                                          │
│  ▸ ¿Qué métodos de pago aceptan?                                        │
│    Tarjeta de crédito/débito, transferencia bancaria, MercadoPago.     │
│    Instituciones: orden de compra y facturación.                        │
│                                                                          │
│  ▸ ¿Los datos se actualizan en tiempo real?                             │
│    Los datos se actualizan diariamente desde múltiples fuentes          │
│    de ofertas laborales en Argentina.                                   │
│                                                                          │
│  ▸ ¿Puedo cancelar en cualquier momento?                                │
│    Sí, sin compromiso de permanencia.                                   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## P-03: Informes Públicos (`/informes`)

**Cambios v2.0:** Preview para visitantes, contenido completo para registrados. CTA de registro.

```
┌─────────────────────────────────────────────────────────────────────────┐
│  [Logo MOL]                    Informes  Precios  [Iniciar Sesión]      │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Informes del Mercado Laboral Argentino                                  │
│                                                                          │
│  Análisis periódicos generados a partir de los datos del sistema MOL.   │
│  Registrate gratis para recibir cada informe nuevo por email.           │
│                                                                          │
│  Filtrar: [Todos ▼]  [2026 ▼]  [Buscar...]                             │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                                                                 │    │
│  │  ┌─────────┐  INFORME MENSUAL - ENERO 2026                     │    │
│  │  │  📄     │  Análisis completo del mercado laboral argentino  │    │
│  │  │  PDF    │  con tendencias, ocupaciones más demandadas y     │    │
│  │  │  2.3MB  │  skills en crecimiento.                           │    │
│  │  └─────────┘  Publicado: 05/02/2026                            │    │
│  │               [Descargar PDF] o [🔒 Registrate para acceder]   │    │
│  │                                                                 │    │
│  ├─────────────────────────────────────────────────────────────────┤    │
│  │                                                                 │    │
│  │  ┌─────────┐  INFORME TRIMESTRAL - Q4 2025                     │    │
│  │  │  📄     │  Resumen del último trimestre del año con         │    │
│  │  │  PDF    │  proyecciones para 2026.                          │    │
│  │  │  4.1MB  │                                                   │    │
│  │  └─────────┘  Publicado: 15/01/2026                            │    │
│  │               [Descargar PDF] o [🔒 Registrate para acceder]   │    │
│  │                                                                 │    │
│  ├─────────────────────────────────────────────────────────────────┤    │
│  │                                                                 │    │
│  │  ┌─────────┐  ESPECIAL: TECNOLOGÍA 2025                        │    │
│  │  │  📄     │  Análisis profundo del sector tecnológico:        │    │
│  │  │  PDF    │  salarios, skills, y empresas que más contratan.  │    │
│  │  │  3.7MB  │                                                   │    │
│  │  └─────────┘  Publicado: 20/12/2025                            │    │
│  │               [Descargar PDF] o [🔒 Registrate para acceder]   │    │
│  │                                                                 │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  ─────────────────────────────────────────────────────────────────      │
│  ¿Querés acceso al tablero interactivo? [Solicitar acceso]              │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

**Notas de diseño:**
- Visitante ve títulos y descripciones, pero descarga requiere registro
- Registrado descarga directamente
- CTA inferior empuja hacia solicitud de tablero

---

## P-04: Login (`/login`)

**Estado:** ✅ Existe — Sin cambios

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

**Cambios v2.0:** Sin selección de plan. El registro es libre y da acceso a contenido. El tablero se solicita después.

```
┌─────────────────────────────────────────────────────────────────────────┐
│  [Logo MOL]                                        [← Volver al inicio] │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│                         Crear cuenta                                     │
│                                                                          │
│   Registrate gratis para acceder a informes y análisis del mercado      │
│   laboral argentino.                                                     │
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
│         │  Perfil (opcional):                         │                 │
│         │  ○ Investigador / Académico                 │                 │
│         │  ○ Consultor / Recruiter                    │                 │
│         │  ○ Empresa / RRHH                           │                 │
│         │  ○ Organismo público                        │                 │
│         │  ○ Trabajador / Buscador de empleo          │                 │
│         │  ○ Otro                                     │                 │
│         │                                             │                 │
│         │  □ Acepto términos y condiciones            │                 │
│         │  □ Quiero recibir informes por email        │                 │
│         │                                             │                 │
│         │  [        Crear cuenta        ]             │                 │
│         │                                             │                 │
│         │  ─────────────────────────────────────      │                 │
│         │  ¿Ya tenés cuenta? Iniciar sesión           │                 │
│         │                                             │                 │
│         └─────────────────────────────────────────────┘                 │
│                                                                          │
│   Al registrarte accedés a informes y análisis periódicos.              │
│   Para acceder al tablero interactivo, podrás solicitarlo               │
│   desde tu cuenta.                                                       │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

**Notas de diseño:**
- Sin selección de plan (todos entran como U-REGISTRADO)
- Campo "Perfil" para segmentación futura de contenido por interés
- Checkbox de opt-in para emails (CMS)
- Texto inferior aclara: registro = contenido, tablero = solicitar después

---

## P-10: Skills Público (`/skills`)

**Estado:** ✅ Existe — Sin cambios

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

---

## Historial de Cambios

| Fecha | Versión | Cambio |
|-------|---------|--------|
| 2026-02-05 | 1.0 | Wireframes SaaS (Free/Pro/Enterprise, hero genérico) |
| 2026-02-07 | 2.0 | Narrativa institucional OEDE, 4 funcionalidades reales, pricing 2 niveles + institucional, registro sin plan |
