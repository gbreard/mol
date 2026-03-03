# Análisis de Issues de Usuario

> Fecha: 2026-03-03 (actualizado)
> Fuente: Issues de admin@oede.gob.ar en Supabase

## Resumen Ejecutivo

Se analizaron **12 issues** reportados por los usuarios. El 67% de los issues (8/12) corresponden al Dashboard Principal (P-09), y el 33% restante (4/12) a Skills Intelligence (P-10).

**Temas principales:**
1. Exportación de datos (4 issues)
2. Simplificación de filtros (2 issues)
3. Rediseño funcional (2 issues)
4. Indicadores de mercado laboral (3 issues)

**Estado actual:**
- ✅ Completados: 7 (Sprint 1 + Sprint 2 + Sprint 5)
- 🔨 En desarrollo: 1 (Sprint 5 — tensión demanda UI)
- 🟡 Parcial: 1 (Issue #7 — wireframes oficina empleo creados, funcionalidad pendiente)
- ⏳ Pendientes: 3 (Sprint 3 + Sprint 4 parcial)

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

#### Issue #3: Simplificar Filtros Ofertas ⏳ PENDIENTE
- **Sección:** Tab Ofertas
- **Solicitud:** Reducir filtros, dejar solo "Buscar por título"
- **Tipo:** UX improvement
- **Impacto:** Medio (simplifica experiencia pero reduce funcionalidad)
- **Sprint:** 3
- **Estado:** ⏳ Pendiente validación usuario

#### Issue #4: Export Archivos Requerimientos ✅ RESUELTO
- **Sección:** Tab Requerimientos
- **Solicitud:** Exportar datos de requerimientos
- **Tipo:** Feature nueva
- **Impacto:** Alto
- **Estado:** ✅ Implementado (2026-02-06) - Botón "Exportar" con CSV y Excel

#### Issue #5: Filtros Requerimientos en Sidebar Global ⏳ PENDIENTE
- **Sección:** Sidebar
- **Solicitud:** Incluir en "Filtros" la sección "Requerimientos"
- **Tipo:** UX improvement
- **Impacto:** Medio (consistencia de interfaz)
- **Sprint:** 3
- **Estado:** ⏳ Pendiente validación usuario

**Filtros a agregar:**

| Filtro | Tipo |
|--------|------|
| Nivel Educativo | Select |
| Experiencia | Select |
| Seniority | Select |
| Modalidad | Select |
| Jornada | Select |
| Skills digitales | Checkbox |

#### Issue #6: Rediseño Requerimientos ⏳ PENDIENTE
- **Sección:** Tab Requerimientos
- **Solicitud:** Rediseño completo de la sección
- **Tipo:** Rediseño funcional
- **Impacto:** Alto (nuevo caso de uso)
- **Sprint:** 4
- **Estado:** ⏳ Pendiente validación usuario

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

#### Issue #7: Rediseño "Mis Skills" para Oficina de Empleo 🟡 PARCIAL
- **Sección:** MySkillsSearch → `/oficina-empleo/*`
- **Solicitud:** Sistema de apoyo a oficina de empleo con perfiles de trabajadores
- **Tipo:** Rediseño funcional
- **Impacto:** Muy Alto (nuevo caso de uso estratégico)
- **Sprint:** 4 → 13 (wireframes)
- **Estado:** 🟡 Wireframes creados (2026-03-03), funcionalidad pendiente

> **Sprint 13:** Se creó la sección `/oficina-empleo` con 3 páginas wireframe (hub, perfil trabajador, ofertas coincidentes). El rol `oficina_empleo` está implementado con middleware gating. Falta la funcionalidad real: tabla `perfiles_trabajadores`, matching con ocupaciones, búsqueda de ofertas.

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

#### Issue #11: Filtro Permanencia no funcionaba ✅ RESUELTO
- **Sección:** Sidebar (filtros globales)
- **Reportado por:** Breard
- **Solicitud:** El filtro de permanencia no filtraba las ofertas — dato no estaba sincronizado a Supabase
- **Tipo:** Bug fix
- **Impacto:** Alto (filtro visible pero sin efecto)
- **Sprint:** 5
- **Estado:** ✅ Resuelto (2026-02-11) — campo `categoria_permanencia` sincronizado a Supabase (2089 ofertas)

#### Issue #12: Evaluar permanencia como indicador de mercado 🔨 EN DESARROLLO
- **Sección:** Tab Panorama (P-09)
- **Reportado por:** Trajtemberg
- **Solicitud:** Evaluar si la permanencia de las ofertas puede usarse como indicador del mercado laboral (tensión de demanda)
- **Tipo:** Feature nueva / investigación
- **Impacto:** Muy Alto (nuevo indicador diferenciador)
- **Sprint:** 5
- **Estado:** 🔨 En desarrollo — análisis de datos validó el indicador, derivó en [V-16](./08_PROPUESTA_VALOR.md#v-16-indicador-de-tensión-de-demanda) (Tensión de Demanda). Datos listos, UI pendiente.

**Resultado del análisis:**
- Combinar permanencia (persistencia) con republicación (insistencia) genera un indicador de 4 cuadrantes
- Tabla `tension_ocupaciones` pre-calculada por ocupación ISCO
- Scatter plot diseñado para Panorama General
- Filtro de cuadrantes en sidebar

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

### Sprint 3: UX Filtros ⏳ PENDIENTE
**Issues:** #3, #5
**Razón:** Mejora experiencia sin cambiar funcionalidad core

**Cambios:**
- Simplificar filtros en Ofertas
- Agregar filtros de Requerimientos al Sidebar global
- Filtros: Nivel Educativo, Experiencia, Seniority, Modalidad, Jornada, Skills digitales

### Sprint 4: Rediseños Mayores ⏳ PENDIENTE
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

### Sprint 5: Permanencia e Indicadores 🔨 EN PROGRESO
**Issues:** #11, #12
**Razón:** Bug de filtro + solicitud de indicador de mercado laboral

**Issue #11 - Filtro permanencia:**
- ✅ Sincronizar `categoria_permanencia` a Supabase
- ✅ Filtro funcional en sidebar (3 checkboxes)

**Issue #12 - Tensión de demanda:**
- ✅ Análisis de datos y diseño del indicador
- ✅ Campos republicación sincronizados
- ⏳ Tabla `tension_ocupaciones` (pendiente crear en Supabase)
- ⏳ Scatter plot en Panorama General
- ⏳ Filtro de cuadrantes en sidebar

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
| #7 | 4→13 | P-10→P-32/33/34 | Rediseño Mis Skills (oficina empleo) | 🟡 Wireframes |
| #8 | 2 | P-10 | Banner ofertas en Comparar | ✅ |
| #9 | 2 | P-10 | Columna ocupaciones con ofertas | ✅ |
| #10 | 2 | P-10 | Export ofertas desde Skills | ✅ |
| #11 | 5 | P-09 | Filtro permanencia (bug sync) | ✅ |
| #12 | 5 | P-09 | Tensión de demanda (indicador) | 🔨 |

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

| Feature | Dependencia | Sprint | Estado |
|---------|-------------|--------|--------|
| Exports Excel | Librería xlsx instalada | 1 | ✅ |
| Ofertas activas por ocupación | Funciones Supabase implementadas | 2 | ✅ |
| Ocupaciones similares con ofertas | SimilarOccupations + ofertasCountMap | 2 | ✅ |
| Filtros Requerimientos | Campos en ofertas_dashboard | 3 | ⏳ |
| Perfiles trabajadores | Nueva tabla `perfiles_trabajadores` | 4 | ⏳ |

---

## Referencias

- [02_ARQUITECTURA_PANTALLAS](./02_ARQUITECTURA_PANTALLAS.md) - P-09, P-10
- [03_WIREFRAMES/suscriptor.md](./03_WIREFRAMES/suscriptor.md) - Wireframes actuales
- [10_OBSERVABILIDAD](./10_OBSERVABILIDAD.md) - Arquitectura técnica
