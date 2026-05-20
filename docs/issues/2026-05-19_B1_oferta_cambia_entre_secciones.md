# B1 — La oferta cambia automáticamente al pasar entre secciones de edición

**ID:** B1
**Reportado por:** Cyn (cuestionario MOL — mayo 2026, Bloque 1.4 sobre bugs del validador)
**Fecha registro:** 2026-05-19
**Severidad:** Alta (afecta flujo diario de validación)
**Estado:** open
**Bloqueante para:** SPEC W Etapa 1 (Visualizador estructurado)

---

## Cita literal de Cyn

> "La oferta cambia automáticamente al pasar entre secciones de edición
> (Editar NLP → Editar Tareas/Skills)"

## Comportamiento observado

Cyn está revisando una oferta específica en `/admin/validacion`. Empieza a editar una sección (por ejemplo NLP), luego pasa a otra (Tareas o Skills), y **la oferta seleccionada cambia sola** a otra oferta distinta sin que ella lo haya pedido. Esto interrumpe el flujo de auditoría: pierde el contexto de qué estaba revisando y debe volver a buscar la oferta original.

## Comportamiento esperado

La oferta seleccionada debe permanecer fija durante toda la sesión de edición. El cambio de sección/panel dentro de la misma oferta no debe disparar navegación a otra oferta. La navegación entre ofertas debe ser exclusivamente acción explícita del usuario (click en lista, flechas, tecla atajo).

## Pasos para reproducir

**No confirmados.** Las descripciones de Cyn no precisan exactamente qué acción dispara el bug. Hipótesis a verificar con ella en sesión:

1. Seleccionar oferta X en lista
2. Empezar a editar campo NLP (cualquiera)
3. Click o switch a sección Tareas / Skills
4. Observar si la oferta seleccionada cambia

**Variante 1:** Tal vez ocurre solo cuando se guarda primero la edición (autoNext después de save).
**Variante 2:** Tal vez ocurre solo al usar atajos de teclado (ArrowUp / ArrowDown en página activa).
**Variante 3:** Tal vez ocurre cuando la lista de ofertas se refresca (refetch tras save) y el item index cambia.

## Componentes potencialmente involucrados

| Path | Rol |
|---|---|
| `fase3_dashboard/mol-dashboard/app/admin/validacion/page.tsx` | Orquestador 3-paneles, mantiene `selectedOferta` |
| `fase3_dashboard/mol-dashboard/components/validacion/OfertaList.tsx` | Panel 1 (selección) |
| `fase3_dashboard/mol-dashboard/components/validacion/PuestoPanel.tsx` | Panel 2 (NLP + tareas + skills text) |
| `fase3_dashboard/mol-dashboard/components/validacion/ClasificacionPanel.tsx` | Panel 3 (ISCO + skills ESCO) |
| `fase3_dashboard/mol-dashboard/components/validacion/ValidationActions.tsx` | Sticky bottom bar OK/Error/Revisar/Basura |
| `fase3_dashboard/mol-dashboard/components/validacion/wizard/*` | Wizard de correcciones |

## Impacto

- **Diario:** Cyn valida ~30 ofertas/día. Si el bug ocurre incluso 1 de 5 veces, son 6 interrupciones diarias.
- **Riesgo de error:** Si guarda una validación pensando que es sobre la oferta A pero el sistema cambió a la B, queda una validación cruzada incorrecta.
- **Adopción SPEC W:** El visualizador estructurado introduce más interacciones (marcar tarea, marcar skill, etc.). Sin B1 resuelto, estas acciones serían aún más propensas a errores.

## Próximo paso

Diagnóstico read-only sin tocar código (Fase 3 del plan de fix). Ver `docs/issues/2026-05-19_diagnostico_B1_B2.md`.

## Notas operativas

- No hay logs estructurados de qué oferta estaba seleccionada al momento del bug. Una sesión grabada con Cyn (pantalla compartida) permitiría confirmar la causa.
- El feedback loop con Cyn debe ser corto: cualquier fix sin confirmar con ella corre el riesgo de "ya no se cambia sola pero ahora la pierdo de otra forma".
