# Wireframes: Suscriptor

> Última actualización: 2026-02-05

## Referencias

| Documento | Relación |
|-----------|----------|
| [02_ARQUITECTURA_PANTALLAS](../02_ARQUITECTURA_PANTALLAS.md) | Lista de pantallas P-09 a P-13 |
| [01_MODELO_NEGOCIO](../01_MODELO_NEGOCIO.md) | Features por plan (U-FREE, U-PRO) |
| [04_MODELO_DATOS](../04_MODELO_DATOS.md) | Tablas ofertas, alertas_config |

---

## P-09: Dashboard (`/dashboard`)

**Estado:** ✅ Existe (actual `/`, se moverá)

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

### Restricciones por Plan

| Elemento | U-FREE | U-PRO |
|----------|--------|-------|
| Fecha desde | Máx 7 días atrás | Sin límite |
| Exportar | Deshabilitado | Habilitado |
| Indicador plan | "FREE - 7 días" | "PRO ✓" |

---

## P-10: Skills Intelligence (`/dashboard/skills`)

**Estado:** ✅ Existe (actual `/admin/skills`, se moverá)

```
┌─────────────────────────────────────────────────────────────────────────┐
│  [Logo]  Dashboard  Empresas  Skills  Reportes  Alertas    [Usuario ▼] │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Skills Intelligence                                                     │
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

## P-11: Análisis de Empresas (`/dashboard/empresas`)

**Plan requerido:** U-PRO

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

---

## P-12: Reportes (`/dashboard/reportes`)

**Plan requerido:** U-PRO

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

---

## P-13: Alertas (`/dashboard/alertas`)

**Plan requerido:** U-PRO

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

### Tipos de Alerta

| Tipo | Descripción | Criterios Disponibles |
|------|-------------|----------------------|
| `ocupacion` | Nueva oferta para ocupación X | umbral diario, semanal |
| `skill` | Skill con crecimiento en demanda | porcentaje cambio |
| `empresa` | Nuevas ofertas de empresa X | inmediato, diario |
| `provincia` | Cambios en provincia X | umbral, porcentaje |

### Límites por Plan

| Plan | Alertas Máximas |
|------|-----------------|
| U-FREE | 0 (deshabilitado) |
| U-PRO | 10 |
| U-ENTERPRISE | Ilimitadas |
