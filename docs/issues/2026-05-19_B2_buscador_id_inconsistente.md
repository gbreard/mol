# B2 — Buscador por ID no extrae rápidamente el aviso (inconsistente)

**ID:** B2
**Reportado por:** Cyn (cuestionario MOL — mayo 2026, Bloque 1.4 sobre bugs del validador)
**Fecha registro:** 2026-05-19
**Severidad:** Alta (afecta flujo diario de validación)
**Estado:** open
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
