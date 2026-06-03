# SPEC W Sprint 1 — Guía de uso para Cyn

**Versión:** Sprint 1 (mayo 2026)
**Validador:** `mol-nextjs.vercel.app/admin/validacion`

---

## Lo nuevo en este sprint

### 1. Filtros nuevos — Bloque "Revisión" en el sidebar

Abajo del bloque de filtros que ya conocés (ISCO, Score, Estado, etc.) aparece una fila nueva con el título **"Revisión"** que separa visualmente los filtros que se agregaron.

| Filtro | Qué hace |
|---|---|
| Radio **Todas** / **Pendientes** / **Revisadas** / **Mal extraídas** | Filtra por tu propio estado de revisión (lo que vos marcaste). "Pendientes" = todavía no la tocaste. |
| Checkbox **Solo datos incompletos** | Muestra solo ofertas con campos vacíos críticos (sin ESCO, sin skills, sin tareas, o score bajo). Útil para ir directo a las que necesitan más trabajo. |
| Checkbox **Solo corregidas manualmente** | Muestra solo ofertas donde marcaste algo a mano (tarea/skill mal, no incluye solo "Revisada"). |

Los filtros se **combinan** entre sí y con los que ya usabas. Por ejemplo: "Pendientes" + "Solo datos incompletos" + ISCO 2511 te deja únicamente analistas IT que aún no revisaste y que tienen campos faltantes.

### 2. Botones nuevos — Sticky bar (panel detalle)

En la barra de acciones del panel detalle de cada oferta aparecen dos botones nuevos:

| Botón | Atajo | Qué hace |
|---|---|---|
| ✅ **Revisada** | `Alt+7` | Marca la oferta como revisada por vos. Volver a tocarlo la desmarca. |
| ⚠️ **Mal extraída** | `Alt+8` | Marca la oferta como "extraída incorrectamente en su totalidad" (ej: puesto civil clasificado como militar). Abre un cuadro donde podés escribir una nota opcional explicando qué falló. |

**Diferencias importantes:**
- "Revisada" es para "ya la miré y está OK" (el atajo es rápido para procesar lotes).
- "Mal extraída" es para casos graves donde TODO el matching de la oferta está mal. Esos casos alimentan el sistema de aprendizaje para que el modelo mejore.
- Si la oferta ya está marcada como "Revisada", el botón de "Mal extraída" se desactiva (y al revés). Solo uno de los dos puede estar activo a la vez.
- Tocar "Revisada" o "Mal extraída" no impide editar los campos NLP, tareas o skills después.

### 3. Fixes incluidos

| Bug | Estado |
|---|---|
| **B1** — Oferta cambia automáticamente entre secciones al escribir en notas o cuadros de diálogo | Resuelto |
| **B2** — Buscador por ID daba lista vacía sin avisar cuando combinabas con filtros que no encontraban resultados | Resuelto. Ahora aparece un mensaje claro de "sin resultados". |

---

## Lo que pediste y todavía no está

Estas funcionalidades quedan para sprints posteriores:

| Pedido | Cuándo |
|---|---|
| Marcar **tareas individuales** como mal extraídas (no toda la oferta, solo una tarea puntual) | Sprint 2 — backend ya está listo, falta UI |
| Marcar **skills individuales** como incorrectas o sugerir skills nuevas | Sprint 2 — backend ya está listo, falta UI |
| **Denominación argentina** de la ocupación (que veas "plomero" además del europeo "fontanero") | Pendiente curación de catálogo (SPEC AR-Cat — investigación lista, requiere decisión del equipo) |
| **Loop de feedback** — que el sistema te muestre patrones detectados desde tus correcciones | Etapa 3 (después del Sprint 2) |

Lo que reportaste en su momento sigue priorizado. La denominación argentina está esperando que se defina cómo se va a curar el catálogo (no es algo que se pueda inventar oferta por oferta, es trabajo aparte).

---

## Cómo reportar problemas

Si algo no funciona como esperás, hay tres caminos:

1. **Avisar a Gerardo directamente** (Slack/WhatsApp) si bloquea tu trabajo.
2. **Anotar en una planilla / mail** para casos no bloqueantes; los acumulamos y los abordamos en lote.
3. **Mensaje al equipo técnico** con el patrón:
   - **Qué hiciste:** "abrí oferta X, clickeé el botón Mal extraída"
   - **Qué esperabas:** "que se marque y aparezca el modal con la nota"
   - **Qué pasó:** "se marca pero el modal no abre" / "tira un error" / "se vuelve atrás sola"
   - **ID de la oferta** si aplica.

Lo importante es el "qué esperabas vs qué pasó" — eso permite reproducir el caso rápidamente.

---

## Cambios que NO te van a afectar (pero existen)

- Detrás de los botones nuevos hay una tabla `audit_actions` que registra cada acción tuya con timestamp, validador y nota. Esto NO se ve en la UI pero alimenta los reportes que el equipo usa para entender qué se está corrigiendo.
- Las marcas son **revertibles** (sacar el check te las quita), salvo las marcas granulares de tareas/skills que van a llegar en Sprint 2 (esas no se podrán revertir, hay que crear una marca nueva con criterio actualizado).
- Las acciones son **inmutables** en la base: incluso si desmarcás algo, queda registro de que la marcaste y la desmarcaste. Esto es a propósito (auditoría).

---

**Última actualización:** mayo 2026, cierre Sprint 1.
**Branch en producción:** `spec/w-validacion-estructurada` (no mergeado a main todavía — se hace después de tu OK).
