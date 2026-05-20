# Diagnóstico read-only — B1 y B2

**Fecha:** 2026-05-19
**Branch:** `fix/validador-bugs-cyn`
**Modo:** read-only sobre código del validador. Cero modificaciones.
**Issues referenciados:** [B1](2026-05-19_B1_oferta_cambia_entre_secciones.md), [B2](2026-05-19_B2_buscador_id_inconsistente.md)

---

## B1 — La oferta cambia automáticamente entre secciones

### Componentes inspeccionados

| Path | Líneas relevantes |
|---|---|
| `fase3_dashboard/mol-dashboard/app/admin/validacion/page.tsx` | 130-135, 158-196, 198-211 |
| `fase3_dashboard/mol-dashboard/components/validacion/ValidationActions.tsx` | 159-203, 281-308 |
| `fase3_dashboard/mol-dashboard/components/validacion/OfertaList.tsx` | 75 |
| `fase3_dashboard/mol-dashboard/components/validacion/wizard/` | — (no inspeccionado, ver hipótesis A) |

### Hipótesis principal — Listener global de ArrowUp/ArrowDown sin filtrar inputs

`app/admin/validacion/page.tsx:198-211`:

```tsx
useEffect(() => {
  function handleKey(e: KeyboardEvent) {
    if (e.key === "ArrowUp") {
      e.preventDefault();
      navigateTo("prev");
    } else if (e.key === "ArrowDown") {
      e.preventDefault();
      navigateTo("next");
    }
  }
  window.addEventListener("keydown", handleKey);
  return () => window.removeEventListener("keydown", handleKey);
}, [navigateTo]);
```

**Problema:** este handler escucha en `window` SIN chequear `e.target`. No verifica si el foco está en un `<input>`, `<textarea>`, contentEditable, o un componente del wizard que abra otro modal con campos editables.

**Consecuencia:** Cuando Cyn abre el wizard de Edición (Alt+5 o click "Editar") y escribe texto en cualquier campo, **cada vez que usa flecha arriba/abajo para navegar el texto (comportamiento normal en cualquier input multi-línea o select dropdown), la página navega a la oferta anterior/siguiente.** La oferta seleccionada cambia y Cyn pierde el contexto.

Esto matchea la descripción literal: "la oferta cambia automáticamente al pasar entre secciones de edición". Cyn no necesariamente está "pasando entre secciones"; está escribiendo en un input y usando las flechas, y la oferta cambia sin que ella entienda por qué.

**Evidencia adicional que apoya esta hipótesis:**
- El handler de Alt+1..6 en `ValidationActions.tsx:281-308` SÍ está protegido (`if (saving || wizardOpen) return;`).
- El handler de ArrowUp/Down NO tiene esa protección.
- El wizard de Edición tiene multi-campos (NLP / Tareas / Skills / Ocupación), todos con inputs y posibles dropdowns/selects — terreno fértil para que ↑↓ sean naturales.

**Confianza:** alta. Esta es la causa más coherente con la descripción de Cyn.

### Hipótesis alternativa A — Auto-navegación tras guardar (`handleEvaluated`)

`page.tsx:190-193`:

```tsx
// Auto-navigate to next
if (currentIndex < ofertas.length - 1) {
  navigateTo("next");
}
```

`handleEvaluated` se dispara después de **toda** acción de guardado (OK / Error / Revisar / Basura desde sticky bar, o cualquier save desde el wizard de Edición). El sistema avanza automáticamente a la siguiente oferta SIN preguntar.

**Por qué podría confundir a Cyn:** si ella usa el wizard de Editar (Alt+5), modifica algunos campos, guarda, el wizard se cierra y la oferta avanza. Cyn esperaba quedarse en la misma oferta para seguir revisando (el wizard guardó las correcciones pero ella podría querer verificar otras secciones).

**Confianza:** media. La auto-navegación es un comportamiento intencional para validación rápida (OK/Error/Revisar/Basura), pero combinada con el wizard genera confusión.

### Hipótesis alternativa B — `useEffect[filters]` resetea selección

`page.tsx:130-135`:

```tsx
useEffect(() => {
  setSelectedOferta(null);
  setCurrentIndex(0);
  setOffset(0);
}, [filters]);
```

Si por alguna razón `filters` cambia mientras Cyn está editando, este efecto deselecciona la oferta. Luego el `useEffect[fetchOfertas]` recarga, y dentro de `fetchOfertas` la línea 114-118 auto-selecciona `ofertas[0]`:

```tsx
if (!selectedOferta) {
  setSelectedOferta(ofertas[0] || null);
  setCurrentIndex(0);
}
```

**Cuándo se dispara `filters` change:** sólo desde `ValidationFilters` cuando el usuario edita un filtro. No debería ocurrir durante edición de una oferta.

**Confianza:** baja. Es trampa si el wizard de edición de la oferta llama indirectamente a `setFilters` (no debería).

### Hipótesis alternativa C — `useCallback` con dependencias incompletas

`fetchOfertas` (`page.tsx:72-124`) tiene `useCallback` con `deps = [goldSetMode, filters, offset]`, pero usa `selectedOferta` y `ofertas` dentro del closure (líneas 114-118). Estos valores se capturan stale en cada recreación del callback. La línea 116 `setSelectedOferta(ofertas[0] || null)` usa `ofertas` stale (vacío o anterior) y puede setear `null` o algo incorrecto.

**Cuándo afecta:** si `fetchOfertas` se re-ejecuta (cambio de `filters` o `offset`) y `ofertas` aún no se actualizó, puede setear `selectedOferta` a un valor obsoleto.

**Confianza:** baja. Es bug latente pero probablemente no es el síntoma reportado por Cyn (este causaría "selección vacía", no "oferta cambia").

### Plan de fix propuesto B1

**Fix mínimo (resuelve hipótesis principal):**

En `page.tsx:198-211`, agregar guardia para no navegar si el foco está en input/textarea/contentEditable/dialog:

```tsx
function handleKey(e: KeyboardEvent) {
  // Skip si el foco está en un input editable o dentro de un dialog/modal
  const target = e.target as HTMLElement | null;
  if (target) {
    const tag = target.tagName;
    if (tag === "INPUT" || tag === "TEXTAREA" || target.isContentEditable) return;
    // Skip si está dentro de un Radix dialog (el wizard abre uno)
    if (target.closest('[role="dialog"]')) return;
  }
  if (e.key === "ArrowUp") {
    e.preventDefault();
    navigateTo("prev");
  } else if (e.key === "ArrowDown") {
    e.preventDefault();
    navigateTo("next");
  }
}
```

**Fix complementario (resuelve hipótesis alternativa A):**

Hacer la auto-navegación post-save opcional con un flag, o sólo cuando la acción viene del sticky bar (OK/Error/Revisar/Basura), no cuando viene del wizard de Edición:

```tsx
// Opción 1: solo auto-next para acciones rápidas, no para wizard
const handleEvaluated = useCallback(
  (resultado, opts?: { autoNext?: boolean }) => {
    // ... update state ...
    if (opts?.autoNext !== false && currentIndex < ofertas.length - 1) {
      navigateTo("next");
    }
  },
  [...]
);

// En ValidationActions: pasar autoNext=true en handleQuickAction, autoNext=false en handleWizardSave
```

**Riesgo del fix:** Bajo.
- El guardia de input/textarea es estándar y no rompe la UX de Cyn al navegar la lista (cuando el foco no está en input, las flechas siguen funcionando).
- Hacer el auto-next opcional en wizard requiere modificar la firma de `onEvaluated`. Es backward-compatible.

**Pasos:**
1. Reproducir con Cyn (sesión 10 min) para confirmar que esto es realmente lo que pasa.
2. Si confirmado: aplicar fix mínimo + test E2E.
3. Si Cyn confirma además molestia con auto-next en wizard: aplicar fix complementario.

---

## B2 — Buscador por ID inconsistente

### Componentes inspeccionados

| Path | Líneas relevantes |
|---|---|
| `fase3_dashboard/mol-dashboard/components/validacion/ValidationFilters.tsx` | 131, 141-143, 249-262 |
| `fase3_dashboard/mol-dashboard/lib/supabase.ts` | 2036-2135 (función `getOfertasValidacion`) |
| `fase3_dashboard/mol-dashboard/app/admin/validacion/page.tsx` | 130-135 |

### Hipótesis principal — Filtros previos activos hacen que la búsqueda devuelva vacío

`lib/supabase.ts:2049-2124`: todos los filtros (`iscoGroup`, `portal`, `provincia`, `metodo`, `seniority`, `modalidad`, `sector`, `nivelEducativo`, `scoreRange`, `estadoValidacion`, `runId`) se aplican como **AND** sobre la query, junto con `search`.

`lib/supabase.ts:2061-2078` la cláusula de search:

```ts
if (filters.search) {
  const tokens = filters.search.split(/[\s,;\n]+/).map(t => t.trim()).filter(Boolean);
  if (tokens.length > 1) {
    query = query.in('id_oferta', tokens);  // match exacto múltiple
  } else {
    const term = tokens[0] ?? '';
    const safe = term.replace(/[(),:]/g, ' ').trim();
    if (safe) {
      query = query.or(
        `titulo_limpio.ilike.%${safe}%,titulo.ilike.%${safe}%,id_oferta.ilike.%${safe}%`
      );
    }
  }
}
```

**Problema:** si Cyn dejó activos filtros previos (ej: filtró por ISCO group 5000, provincia Buenos Aires, estado pendiente) y luego busca por ID de una oferta que **no satisface esos filtros**, la búsqueda devuelve **0 resultados**.

**Síntoma desde la perspectiva de Cyn:** "el buscador no funcionó". Reintenta presionando ENTER → mismo resultado vacío. Reintenta con la lupita → mismo resultado vacío. **Borra el input y reescribe** → si en el medio cambió algún filtro (incluyendo limpiar el search anterior), el comportamiento puede cambiar.

Esto matchea exacto: "a veces hay que intentarlo varias veces, usando ENTER, la lupita, o ingresando el dato manualmente".

**Confianza:** alta. Es la causa más probable.

### Hipótesis alternativa A — Sin debounce, depende exclusivamente de ENTER o lupita

`ValidationFilters.tsx:251-261`:

```tsx
<Input
  value={searchInput}
  onChange={(e) => setSearchInput(e.target.value)}
  onKeyDown={(e) => e.key === "Enter" && handleSearchSubmit()}
  ...
/>
<Button onClick={handleSearchSubmit}>
  <Search />
</Button>
```

El `onChange` SOLO actualiza el estado local `searchInput`. La búsqueda se dispara **únicamente** con ENTER o click en lupita. Si Cyn no presiona ENTER (por ej. tabula al siguiente filtro pensando que se buscó), la búsqueda no ocurre.

**Confianza:** media. Cyn sabe que hay que apretar ENTER, pero el comportamiento puede ser sutil — si tipea y hace clic fuera del input sin presionar ENTER, no busca.

### Hipótesis alternativa B — `useEffect[filters]` resetea selección inmediatamente

Cuando `handleSearchSubmit` ejecuta `onChange({...filters, search: searchInput})`, el `useEffect[filters]` en `page.tsx:131-135` corre:

```tsx
useEffect(() => {
  setSelectedOferta(null);
  setCurrentIndex(0);
  setOffset(0);
}, [filters]);
```

El primer render post-search muestra: `selectedOferta=null`, lista cargando. Si fetch tarda, hay un momento donde se ve "No se encontraron ofertas con los filtros seleccionados" (línea 282-285) o el loader, según el estado intermedio. Cyn puede interpretar esto como "buscador falló" cuando en realidad está esperando el fetch.

**Confianza:** baja-media. Es UX confuso pero no exactamente "no responde".

### Hipótesis alternativa C — `id_oferta.ilike.%X%` con ID parcial trae múltiples resultados

Cuando Cyn busca "12345", el `ilike` con wildcards `%12345%` matchea cualquier ID que contenga esa subcadena (ej: 7891234567 contiene "1234567"). Si Cyn busca por ID parcial, puede aparecer una lista con varias ofertas y la suya en posición desconocida.

**Confianza:** baja. Cyn usualmente conoce el ID completo (10 dígitos). Pero si pega un fragmento, podría confundirse.

### Plan de fix propuesto B2

**Fix mínimo (resuelve hipótesis principal):**

Dar feedback visual claro cuando la búsqueda no devuelve resultados POR los filtros activos:

```tsx
// En page.tsx, cuando ofertas.length === 0 y hay search:
{ofertas.length === 0 && filters.search && hasOtherFiltersActive && (
  <div>
    No se encontraron ofertas con los filtros + búsqueda actual.
    <button onClick={limpiarFiltrosManteniendoSearch}>
      Limpiar filtros (mantener búsqueda)
    </button>
  </div>
)}
```

**Fix complementario A (descartar hipótesis alternativa A):**

Agregar debounce de ~300ms al `onChange` para que la búsqueda se dispare sola sin requerir ENTER:

```tsx
useEffect(() => {
  const timer = setTimeout(() => {
    if (searchInput !== filters.search) {
      onChange({ ...filters, search: searchInput });
    }
  }, 300);
  return () => clearTimeout(timer);
}, [searchInput]);
```

**Fix complementario B (mejor matching para ID exacto):**

Si el input parece un ID puro (sólo dígitos, length ≥ 8), usar `.eq('id_oferta', searchInput)` en lugar de `.ilike('%X%')`. Match exacto, sin ambigüedad de substring.

```tsx
if (/^\d{8,}$/.test(safe)) {
  query = query.eq('id_oferta', safe);
} else {
  query = query.or(`titulo_limpio.ilike.%${safe}%,titulo.ilike.%${safe}%,id_oferta.ilike.%${safe}%`);
}
```

**Riesgo del fix:** Bajo a medio.
- Feedback de "filtros activos" es aditivo, no rompe nada.
- Debounce cambia comportamiento UX — Cyn debe saber que ya no necesita ENTER (puede ser confuso al principio). Riesgo de disparar queries de más mientras tipea.
- Match exacto por ID puro descarta búsquedas parciales legítimas — es importante saber si Cyn alguna vez busca por fragmento de ID (probablemente no).

**Pasos:**
1. Reproducir con Cyn (10 min): confirmar que el fallo es por filtros previos activos.
2. Si confirmado: aplicar fix mínimo (feedback visual) → probablemente resuelve 80% del problema sin riesgo.
3. Evaluar fix complementario A (debounce) según preferencia de Cyn.
4. Evaluar fix complementario B (match exacto por ID puro) según si Cyn busca por fragmentos.

---

## Recomendación final

| Bug | Confianza diagnóstico | Recomendación |
|---|---|---|
| B1 | Alta — listener global de flechas sin guardia de input | **Avanzar a fix** después de confirmar con sesión de 10 min con Cyn (verificar si reproduce escribiendo en wizard + usando flechas) |
| B2 | Alta — filtros previos activos + búsqueda AND | **Avanzar a fix** después de confirmar con sesión de 10 min con Cyn (verificar si fallaba con filtros activos vs limpios) |

**Ambos fixes son de bajo riesgo y alcance acotado.** El tiempo estimado de implementación es:

- B1 fix mínimo: 30 min código + 30 min tests
- B1 fix complementario (wizard auto-next): 1h código + 30 min tests
- B2 fix mínimo (feedback): 30 min código + 30 min tests
- B2 fix complementario A (debounce): 20 min código + 20 min tests
- B2 fix complementario B (match exacto ID): 15 min código + 15 min tests

**Total estimado:** 3-4h para todos los fixes + tests, sin contar la sesión de confirmación con Cyn.

**Bloqueos:**
- Ningún bloqueo técnico.
- Idealmente sesión de 10-15 min con Cyn para confirmar reproducibilidad antes de implementar fix (especialmente B1, donde el comportamiento depende del foco/contexto del wizard que no inspeccioné en detalle en esta lectura).

**Decisión pendiente para Gerardo:**

1. ¿Avanzamos a Fase 5 (implementar fix) directamente con las hipótesis principales, o esperamos sesión con Cyn?
2. Si avanzamos: ¿implementamos sólo fix mínimo de cada bug, o también los complementarios?
3. ¿Quién hace la sesión con Cyn — Gerardo, alguien del equipo, o el fix se hace blind y Cyn verifica al final?
