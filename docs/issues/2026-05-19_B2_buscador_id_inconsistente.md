# B2 — Buscador por ID no extrae rápidamente el aviso (inconsistente)

**ID:** B2
**Reportado por:** Cyn (cuestionario MOL — mayo 2026, Bloque 1.4 sobre bugs del validador)
**Fecha registro:** 2026-05-19
**Severidad:** Alta (afecta flujo diario de validación)
**Estado:** fixed (pendiente validación en producción por Cyn)
**Bloqueante para:** SPEC W Etapa 1 (Visualizador estructurado)

---

## Cita literal de Cyn

> "El buscador por ID no siempre extrae rápidamente el aviso. A veces hay
> que intentarlo varias veces, usando ENTER, la lupita, o ingresando el
> dato manualmente"

## Comportamiento observado

Cyn ingresa un ID de oferta en el buscador de `/admin/validacion`. El sistema **no responde de forma consistente**:
- A veces funciona al primer intento (ENTER, click en lupita, o auto-trigger por debounce)
- A veces requiere reintentar varias veces
- A veces requiere "ingresar el dato manualmente" — interpretación: borrar y reescribir el ID

El comportamiento es no determinístico desde la perspectiva del usuario, lo que sugiere una condición de carrera o un timing dependiente del estado previo del input/filtros.

## Comportamiento esperado

Ingresar ID en el campo de búsqueda + presionar ENTER (o esperar el debounce normal) debe disparar la búsqueda de forma confiable al primer intento. La lupita debe ser un trigger redundante consistente. Sin reintentos, sin borrar y reescribir.

## Pasos para reproducir

**No confirmados.** Hipótesis a verificar con Cyn:

1. Buscar oferta A por ID → OK
2. Limpiar input o sin limpiar
3. Buscar oferta B por ID
4. Observar si requiere reintento

**Variante 1:** Quizás falla cuando un filtro previo (ISCO/portal/score) está activo y el ID no matchea ese filtro → la lista queda vacía y parece que el buscador falló.

**Variante 2:** Quizás el debounce es muy largo y ENTER no fuerza el flush.

**Variante 3:** Quizás hay un race condition entre el setState del input y el fetch — si Cyn escribe rápido y presiona ENTER antes del setState, el fetch usa valor anterior.

**Variante 4:** Quizás el ID tiene formato específico (entero de 10 dígitos vs string) y el campo no normaliza, fallando match exacto en el query.

## Componentes potencialmente involucrados

| Path | Rol |
|---|---|
| `fase3_dashboard/mol-dashboard/components/validacion/ValidationFilters.tsx` | Contiene input de búsqueda + lógica de debounce + onChange/onSubmit |
| `fase3_dashboard/mol-dashboard/app/admin/validacion/page.tsx` | Maneja el estado `filters` y dispara el fetch en useEffect |
| `fase3_dashboard/mol-dashboard/lib/supabase.ts` | Función `getOfertasValidacion(filters, limit, offset)` |
| `fase3_dashboard/mol-dashboard/lib/types.ts` | Tipo `ValidationFiltersState` con campo `search` |

## Impacto

- **Diario:** Cyn busca por ID al revisar issues reportados por usuarios o cuando alguien le pasa un ID específico para auditar.
- **Tiempo perdido:** Reintentos múltiples + reescritura manual suman ~5-10s por búsqueda. Si busca 10 IDs por día, son ~1-2 minutos perdidos diarios + frustración.
- **Riesgo de error:** Cyn podría asumir que un ID "no existe" cuando en realidad el buscador falló al disparar — falsos negativos operativos.
- **Adopción SPEC W:** El flujo de "ver casos similares ya validados" (Etapa 3) depende fuertemente del buscador. Sin B2 resuelto, ese flujo arrastra el mismo problema.

## Próximo paso

Diagnóstico read-only sin tocar código (Fase 3 del plan de fix). Ver `docs/issues/2026-05-19_diagnostico_B1_B2.md`.

## Notas operativas

- Sesión con Cyn (pantalla compartida o video) ayudaría a confirmar bajo qué condiciones específicas falla.
- Verificar si la deuda se reproduce sin filtros previos activos (test A) y con filtros previos activos (test B) — esto descarta o confirma Variante 1.

---

## Fix aplicado

**Commit:** `a79075ed` fix(B2): feedback visual cuando búsqueda + filtros activos retorna vacío
**Branch:** `fix/validador-bugs-cyn`
**Fecha:** 2026-05-19

### Resumen del cambio

Cuando la búsqueda + filtros activos no devuelven ofertas, en lugar del mensaje genérico "No se encontraron ofertas con los filtros seleccionados" ahora aparece un panel que:

1. **Explica** qué filtros están activos y por qué probablemente la búsqueda no devuelve resultados.
2. **Ofrece un botón** "Limpiar filtros (mantener búsqueda)" que setea todo a `EMPTY_FILTERS` pero preserva `filters.search`.
3. **Ofrece un botón alternativo** "Limpiar todo" para reset total.

Esto convierte la percepción de "el buscador no funciona" en "los filtros están filtrando mi resultado, click para resolverlo". No modifica el comportamiento del buscador en sí.

### Archivos modificados

| Path | Cambio |
|---|---|
| `fase3_dashboard/mol-dashboard/components/validacion/EmptyResultsWithFilters.tsx` | Nuevo. Componente con 3 ramas según presencia de búsqueda y filtros. |
| `fase3_dashboard/mol-dashboard/app/admin/validacion/page.tsx` | Reemplaza el div genérico de empty state por `<EmptyResultsWithFilters />` y pasa handlers para limpiar manteniendo/no la búsqueda. |
| `fase3_dashboard/mol-dashboard/__tests__/component/empty-results-with-filters.test.tsx` | Nuevo. 7 tests component. |

### Tests

Archivo: `__tests__/component/empty-results-with-filters.test.tsx` — **7/7 verdes**.

| # | Test | Cubre |
|---|---|---|
| 1 | mensaje + botón limpiar cuando hay search Y otros filtros activos | caso principal del bug |
| 2 | NO muestra mensaje de filtros cuando sólo hay búsqueda | caso degenerado: sin otros filtros, no hay nada que limpiar |
| 3 | click en "Limpiar filtros (mantener búsqueda)" dispara callback correcto | UX |
| 4 | click en "Limpiar todo" dispara callback correcto | UX alternativa |
| 5 | mensaje genérico cuando no hay búsqueda ni filtros (vacío total) | regresión: empty state base sigue funcionando |
| 6 | mensaje genérico cuando hay filtros pero no búsqueda | regresión: caso ya cubierto antes |
| 7 | enumera los 11 filtros activos sin perder ninguno | regresión: completitud del mapeo |

### Lo que NO se hizo (fixes complementarios, postergados)

- Debounce en el input de búsqueda (`onChange` solo dispara en ENTER/lupita).
- Match exacto por `.eq('id_oferta', X)` cuando el input parece ID puro (en lugar del `ilike` actual).

Esos quedan para iteración posterior si Cyn reporta que el fix mínimo no es suficiente.

### Validación pendiente

Cyn debe confirmar en producción que ahora entiende por qué un ID no aparece (y puede resolverlo con el botón). **Hasta entonces este issue queda en estado `fixed`, no `closed`.**
