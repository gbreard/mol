# Análisis de Issues de Usuario

> Fecha: 2026-02-06 (actualizado)
> Fuente: Issues de admin@oede.gob.ar en Supabase

## Resumen Ejecutivo

Se analizaron **10 issues** reportados por el usuario principal. El 60% de los issues (6/10) corresponden al Dashboard Principal (P-09), y el 40% restante (4/10) a Skills Intelligence (P-10).

**Temas principales:**
1. Exportación de datos (4 issues)
2. Simplificación de filtros (2 issues)
3. Rediseño funcional (2 issues)
4. Indicadores de mercado laboral (3 issues)

**Estado actual:**
- ✅ Completados: 6 (Sprint 1 + Sprint 2)
- ⏳ Pendientes: 4

---

## Issues Detallados

### P-09: Dashboard Principal (`/`)

#### Issue #1: Export Excel Gráficos Panorama General ✅ RESUELTO
- **Sección:** Tab Panorama
- **Solicitud:** Exportar los 3 gráficos de Panorama General a Excel formateado
- **Tipo:** Feature nueva
- **Impacto:** Alto (funcionalidad core para analistas)
- **Estado:** ✅ Implementado (2026-02-06)

**Requisitos implementados:**
1. ✅ **Datos:** Todas las categorías del gráfico con número de ofertas y porcentajes
2. ✅ **Título:** El mismo que el gráfico correspondiente
3. ✅ **Subtítulo:** Enumeración de filtros aplicados
4. ✅ **Fuente:** "MOL, en base a portales de intermediación laboral"

**Función reutilizable:** `downloadFormattedExcel()` en ExportButton.tsx

#### Issue #2: Export CSV/Excel Ofertas Laborales ✅ RESUELTO
- **Sección:** Tab Ofertas
- **Solicitud:** Descargar tabla de ofertas en formato CSV o Excel
- **Tipo:** Feature nueva
- **Impacto:** Alto (necesario para análisis offline)
- **Estado:** ✅ Implementado (2026-02-06) - Botón "Exportar" con CSV y Excel

#### Issue #3: Simplificar Filtros Ofertas
- **Sección:** Tab Ofertas
- **Solicitud:** Reducir filtros, dejar solo "Buscar por título"
- **Tipo:** UX improvement
- **Impacto:** Medio (simplifica experiencia pero reduce funcionalidad)
- **Sprint:** 3
- **Nota:** Considerar filtros colapsables en lugar de eliminar

#### Issue #4: Export Archivos Requerimientos ✅ RESUELTO
- **Sección:** Tab Requerimientos
- **Solicitud:** Exportar datos de requerimientos
- **Tipo:** Feature nueva
- **Impacto:** Alto
- **Estado:** ✅ Implementado (2026-02-06) - Botón "Exportar" con CSV y Excel

#### Issue #5: Filtros Requerimientos en Sidebar Global
- **Sección:** Sidebar
- **Solicitud:** Incluir en "Filtros" la sección "Requerimientos"
- **Tipo:** UX improvement
- **Impacto:** Medio (consistencia de interfaz)
- **Sprint:** 3

**Filtros a agregar:**

| Filtro | Tipo |
|--------|------|
| Nivel Educativo | Select |
| Experiencia | Select/Range |
| Seniority | Select |
| Modalidad | Select |
| Jornada | Select |
| Skills digitales | Toggle/Select |

#### Issue #6: Rediseño Requerimientos
- **Sección:** Tab Requerimientos
- **Solicitud:** Rediseño completo de la sección
- **Tipo:** Rediseño funcional
- **Impacto:** Alto (nuevo caso de uso)
- **Sprint:** 4

**Cambios solicitados:**

1. ❌ **Eliminar** sección de filtros inicial
2. **Reordenar contenido:**
   - Primero: "Análisis de habilidades"
   - Segundo: "Distribución de los requerimientos"
3. **Gráfico "Análisis de habilidades":**
   - Default: mostrar competencias específicas
   - Selector 1: cantidad de competencias (20, 40, 60, 100)
   - Selector 2: tipo (específica / agregada)
   - ❌ Eliminar listado de competencias

---

### P-10: Skills Intelligence (`/skills`)

#### Issue #7: Rediseño "Mis Skills" para Oficina de Empleo
- **Sección:** MySkillsSearch
- **Solicitud:** Sistema de apoyo a oficina de empleo con perfiles de trabajadores
- **Tipo:** Rediseño funcional
- **Impacto:** Muy Alto (nuevo caso de uso estratégico)
- **Sprint:** 4

**Flujo completo:**

```
┌─────────────────────────────────────────────────────────────┐
│  1. REGISTRO                                                │
│     └── Nombre del trabajador/a (para guardar perfil)       │
├─────────────────────────────────────────────────────────────┤
│  2. CONSTRUCCIÓN DEL PERFIL                                 │
│                                                             │
│     a) Ingresar ocupaciones de trayectoria laboral          │
│              ↓                                              │
│     b) Sistema despliega competencias vinculadas            │
│              ↓                                              │
│     c) Eliminar competencias que NO tiene el trabajador     │
│              ↓                                              │
│     d) Agregar competencias via buscador (sin semántica)    │
│              ↓                                              │
│     e) Mostrar perfil de competencias resultante            │
├─────────────────────────────────────────────────────────────┤
│  3. MATCHING                                                │
│     └── Ocupaciones similares al perfil del trabajador      │
├─────────────────────────────────────────────────────────────┤
│  4. ACCIONES EXISTENTES                                     │
│     └── Se mantienen (Comparar, Detalle, etc.)              │
│     └── "Comparar" aplica cambios de Issue #8               │
└─────────────────────────────────────────────────────────────┘
```

**Dependencias:**
- Issue #8 (indicador ofertas en Comparar)
- Nueva tabla `perfiles_trabajadores` en Supabase

#### Issue #8: Modificación "Comparar Ocupaciones" ✅ RESUELTO
- **Sección:** OccupationCompare
- **Solicitud:** Indicar si la ocupación objetivo tiene ofertas activas
- **Tipo:** Feature nueva
- **Impacto:** Alto (conecta skills con mercado real)
- **Sprint:** 2
- **Estado:** ✅ Implementado (2026-02-06)

**Cambios solicitados:**

1. Si la ocupación **objetivo** tiene ofertas activas:
   - Mostrar cartel: **"Ofertas laborales activas en esta ocupación"**
   - Incluir **link** que lleva a esas ofertas

#### Issue #9: Modificaciones en "Ocupación" (Detalle) ✅ RESUELTO
- **Sección:** OccupationDetail
- **Solicitud:** Nueva columna con ocupaciones similares que tienen ofertas
- **Tipo:** Feature nueva
- **Impacto:** Alto (ayuda a reorientación laboral)
- **Sprint:** 2
- **Estado:** ✅ Implementado (2026-02-06)

**Cambios solicitados:**

| Elemento | Cambio |
|----------|--------|
| Nueva columna | "Ocupaciones similares con ofertas laborales activas" (junto a "Ocupaciones similares") |
| Links | Cada ocupación con ofertas incluye link a las ofertas |
| Selector cantidad | Mostrar hasta 20 o hasta 30 ocupaciones (ambas columnas) |

#### Issue #10: Export Ofertas desde Skills ✅ RESUELTO
- **Sección:** Skills → al ver ofertas de una ocupación
- **Solicitud:** Descargar ofertas vinculadas a ocupación
- **Tipo:** Feature nueva
- **Impacto:** Alto
- **Sprint:** 2
- **Estado:** ✅ Implementado (2026-02-06)

**Archivos a generar:**

| Formato | Contenido |
|---------|-----------|
| **CSV** | Título ocupación, fecha, link oferta |
| **Excel formateado** | Ver estructura abajo |

**Estructura Excel:**
```
┌─────────────────────────────────────────────────────────────┐
│ Título: "Ofertas laborales disponibles activas a la fecha  │
│         según selección"                                    │
├─────────────────────────────────────────────────────────────┤
│ Subtítulo: Fecha extracción + filtros aplicados            │
├─────────────────────────────────────────────────────────────┤
│ Título | Fecha | Competencias | Link oferta                │
│ ────── │ ───── │ ──────────── │ ───────────                │
│ ...    │ ...   │ ...          │ ...                        │
├─────────────────────────────────────────────────────────────┤
│ Fuente: MOL, en base a portales de intermediación laboral  │
└─────────────────────────────────────────────────────────────┘
```

---

## Priorización por Sprints

### Sprint 1: Exports Dashboard ✅ COMPLETADO
**Issues:** #1, #2, #4
**Estado:** ✅ Implementado (2026-02-06)

- Componente `ExportButton` con CSV/Excel
- Función `downloadFormattedExcel()` reutilizable
- Librería xlsx instalada

### Sprint 2: Indicadores Mercado ✅ COMPLETADO
**Issues:** #8, #9, #10
**Estado:** ✅ Implementado (2026-02-06)

**Implementación realizada:**
- Funciones Supabase: `getOfertasCountByIsco()`, `getOfertasByIsco()`, `getOfertasByMultipleIsco()`
- Banner en OccupationCompare cuando ocupación B tiene ofertas activas
- Badges de ofertas en cada ocupación similar
- Nueva sección "Ocupaciones Similares con Ofertas Activas"
- Selector de cantidad (10/20/30) en SimilarOccupations
- Modal OfertasOcupacionModal con export CSV/Excel
- Links directos a ofertas desde cada ocupación

### Sprint 3: UX Filtros
**Issues:** #3, #5
**Razón:** Mejora experiencia sin cambiar funcionalidad core

**Cambios:**
- Simplificar filtros en Ofertas
- Agregar filtros de Requerimientos al Sidebar global
- Filtros: Nivel Educativo, Experiencia, Seniority, Modalidad, Jornada, Skills digitales

### Sprint 4: Rediseños Mayores
**Issues:** #6, #7
**Razón:** Requieren arquitectura nueva y más desarrollo

**Issue #6 - Requerimientos:**
- Reordenar secciones
- Nuevos selectores en gráfico
- Eliminar elementos

**Issue #7 - Perfiles Trabajadores:**
- Nueva tabla en Supabase
- Flujo completo de registro y construcción de perfil
- Matching con ocupaciones

---

## Tabla Resumen

| Issue | Sprint | Pantalla | Descripción | Estado |
|-------|--------|----------|-------------|--------|
| #1 | 1 | P-09 | Export Excel Panorama | ✅ |
| #2 | 1 | P-09 | Export CSV/Excel Ofertas | ✅ |
| #3 | 3 | P-09 | Simplificar filtros Ofertas | ⏳ |
| #4 | 1 | P-09 | Export Requerimientos | ✅ |
| #5 | 3 | P-09 | Filtros Requerimientos en Sidebar | ⏳ |
| #6 | 4 | P-09 | Rediseño Requerimientos | ⏳ |
| #7 | 4 | P-10 | Rediseño Mis Skills (oficina empleo) | ⏳ |
| #8 | 2 | P-10 | Banner ofertas en Comparar | ✅ |
| #9 | 2 | P-10 | Columna ocupaciones con ofertas | ✅ |
| #10 | 2 | P-10 | Export ofertas desde Skills | ✅ |

---

## Wireframes Requeridos

| Issue | Wireframe | Documento |
|-------|-----------|-----------|
| #1-2, #4 | Componente ExportButton | ✅ Implementado |
| #3, #5 | Sidebar unificado v2 | 03_WIREFRAMES/suscriptor.md |
| #6 | Requerimientos v2 | 03_WIREFRAMES/suscriptor.md |
| #7 | Perfil Trabajador | 03_WIREFRAMES/suscriptor.md (nuevo) |
| #8 | Comparador con banner | ✅ Implementado |
| #9 | Detalle con columna ofertas | ✅ Implementado |
| #10 | Export desde Skills | ✅ Implementado |

---

## Dependencias Técnicas

| Feature | Dependencia | Sprint |
|---------|-------------|--------|
| Exports Excel | ✅ Librería xlsx instalada | 1 |
| Ofertas activas por ocupación | ✅ Funciones Supabase implementadas | 2 |
| Ocupaciones similares con ofertas | ✅ SimilarOccupations + ofertasCountMap | 2 |
| Filtros Requerimientos | Campos en ofertas_dashboard | 3 |
| Perfiles trabajadores | Nueva tabla `perfiles_trabajadores` | 4 |

---

## Referencias

- [02_ARQUITECTURA_PANTALLAS](./02_ARQUITECTURA_PANTALLAS.md) - P-09, P-10
- [03_WIREFRAMES/suscriptor.md](./03_WIREFRAMES/suscriptor.md) - Wireframes actuales
- [10_OBSERVABILIDAD](./10_OBSERVABILIDAD.md) - Arquitectura técnica
