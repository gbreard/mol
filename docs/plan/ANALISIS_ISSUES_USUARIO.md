# Análisis de Issues de Usuario

> Fecha: 2026-02-06
> Fuente: Issues de admin@oede.gob.ar en Supabase

## Resumen Ejecutivo

Se analizaron **9 issues** reportados por el usuario principal. El 67% de los issues (6/9) corresponden al Dashboard Principal (P-09), y el 33% restante (3/9) a Skills Intelligence (P-10).

**Temas principales:**
1. Exportación de datos (4 issues)
2. Simplificación de filtros (2 issues)
3. Rediseño funcional (2 issues)
4. Indicadores de mercado laboral (2 issues)

---

## Issues Detallados

### P-09: Dashboard Principal (`/dashboard`)

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
- **Estado:** Implementado (2026-02-06) - Botón "Exportar" con CSV y Excel

#### Issue #3: Simplificar Filtros Ofertas
- **Sección:** Tab Ofertas
- **Solicitud:** Reducir filtros, dejar solo "Buscar por título"
- **Tipo:** UX improvement
- **Impacto:** Medio (simplifica experiencia pero reduce funcionalidad)
- **Nota:** Considerar filtros colapsables en lugar de eliminar

#### Issue #4: Export Archivos Requerimientos ✅ RESUELTO
- **Sección:** Tab Requerimientos
- **Solicitud:** Exportar datos de requerimientos
- **Tipo:** Feature nueva
- **Impacto:** Alto
- **Estado:** Implementado (2026-02-06) - Botón "Exportar" con CSV y Excel

#### Issue #5: Filtros Requerimientos en Sidebar Global
- **Sección:** Sidebar
- **Solicitud:** Los filtros de Requerimientos deben estar en el panel de filtros global
- **Tipo:** UX improvement
- **Impacto:** Medio (consistencia de interfaz)

#### Issue #6: Rediseño Requerimientos
- **Sección:** Tab Requerimientos
- **Solicitud:** Reordenar contenido, agregar selectores de competencias
- **Tipo:** Rediseño funcional
- **Impacto:** Alto (nuevo caso de uso)
- **Detalle:** El usuario quiere poder seleccionar competencias específicas y ver qué ocupaciones las requieren

---

### P-10: Skills Intelligence (`/skills`)

#### Issue #7: Rediseño para Oficina de Empleo
- **Sección:** MySkillsSearch
- **Solicitud:** Adaptar para caso de uso de oficina de empleo: perfiles de trabajadores
- **Tipo:** Rediseño funcional
- **Impacto:** Muy Alto (nuevo caso de uso estratégico)
- **Detalle:**
  - Actualmente: búsqueda de skills genérica
  - Requerido: crear perfiles de trabajadores con sus skills y sugerir ocupaciones compatibles
  - Caso de uso: "El trabajador X tiene estas skills, ¿qué ocupaciones puede desempeñar?"

#### Issue #8: Indicador Ofertas Activas en Comparador
- **Sección:** OccupationCompare
- **Solicitud:** Mostrar si cada ocupación tiene ofertas activas actualmente
- **Tipo:** Feature nueva
- **Impacto:** Alto (conecta skills con mercado real)
- **Implementación sugerida:** Badge con contador de ofertas activas

#### Issue #9: Ocupaciones Similares con Ofertas
- **Sección:** OccupationDetail
- **Solicitud:** Columna que muestre ocupaciones similares que tienen ofertas activas
- **Tipo:** Feature nueva
- **Impacto:** Alto (ayuda a reorientación laboral)
- **Implementación sugerida:** Lista de "ocupaciones cercanas con demanda"

---

## Priorización Sugerida

### Sprint 1: Exports (Issues #1, #2, #4)
**Razón:** Funcionalidad básica que desbloquea trabajo de analistas
- Componente compartido: `ExportButton` con opciones CSV/Excel
- API routes para generación de archivos

### Sprint 2: Indicadores Mercado (Issues #8, #9)
**Razón:** Alto valor diferencial, implementación acotada
- Query a ofertas_dashboard por isco_code
- Badges y listas de sugerencias

### Sprint 3: UX Filtros (Issues #3, #5)
**Razón:** Mejora experiencia sin cambiar funcionalidad
- Sidebar unificado
- Filtros colapsables

### Sprint 4: Rediseños (Issues #6, #7)
**Razón:** Requieren más análisis y diseño
- Issue #7 (perfiles trabajadores) es estratégico pero complejo
- Issue #6 (requerimientos) necesita más detalle del usuario

---

## Wireframes Requeridos

| Issue | Wireframe | Documento |
|-------|-----------|-----------|
| #1-2, #4 | Componente ExportButton | 03_WIREFRAMES/componentes.md |
| #3, #5 | Sidebar unificado v2 | 03_WIREFRAMES/suscriptor.md |
| #6 | Requerimientos v2 | 03_WIREFRAMES/suscriptor.md |
| #7 | Perfil Trabajador | 03_WIREFRAMES/suscriptor.md (nuevo) |
| #8 | Comparador con badges | 03_WIREFRAMES/suscriptor.md |
| #9 | Detalle con sugerencias | 03_WIREFRAMES/suscriptor.md |

---

## Dependencias Técnicas

| Feature | Dependencia |
|---------|-------------|
| Exports Excel | Librería xlsx o similar |
| Ofertas activas por ocupación | Vista SQL en Supabase |
| Ocupaciones similares | ESCO skill overlap ya calculado |
| Perfiles trabajadores | Nueva tabla `perfiles_trabajadores` |

---

## Referencias

- [02_ARQUITECTURA_PANTALLAS](./02_ARQUITECTURA_PANTALLAS.md) - P-09, P-10
- [03_WIREFRAMES/suscriptor.md](./03_WIREFRAMES/suscriptor.md) - Wireframes actuales
- [10_OBSERVABILIDAD](./10_OBSERVABILIDAD.md) - Arquitectura técnica
