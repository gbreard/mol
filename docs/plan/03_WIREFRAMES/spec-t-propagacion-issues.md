# Wireframe — UI de Propagación de Correcciones (SPEC T Fase 4)

**Fecha:** 2026-04-27
**Spec:** `docs/specs/2026-04-27_T_flujo_propagacion_correcciones.md`
**Audiencia:** Cyn, Diego, Gerardo (analistas que cierran issues)
**Ubicación en dashboard:** integrada en `/admin/issues` y `/admin/validacion`
**Estado:** propuesta — pendiente aprobación antes de implementar

---

## 1. Contexto

Hoy cuando Cyn/Diego cierran un issue, **se arregla solo esa oferta**. La propagación a ofertas similares es manual y casi nunca pasa (468 de 469 issues sin propagar).

Con SPEC T Fase 1, ya existe el helper Python `propagate_correction(patron)`. **Falta la UI** para que humanos lo disparen desde el dashboard sin tocar la línea de comandos.

**Principio de diseño:** la propagación debe ser **un click al cerrar el issue**, no un step extra que se puede saltear.

---

## 2. Pantallas afectadas

### 2.1 `/admin/issues` (lista) — agregar columnas

```
┌─ Issues ─────────────────────────────────────────────────────────────────┐
│                                                                          │
│ [Pendientes (1000)] [Resueltos (542)] [Todos]   🔍 Buscar...             │
│                                                                          │
│ ┌──────────┬─────────────────────┬──────────┬────────┬────────────────┐ │
│ │ Fecha    │ Título              │ Autor    │ Estado │ Propagación ⚡  │ │
│ ├──────────┼─────────────────────┼──────────┼────────┼────────────────┤ │
│ │ 27/04    │ Operario depósito   │ Cynthia  │ ✓ res. │ +313 ofertas   │ │
│ │ 27/04    │ Despacho metalúrg.  │ Cynthia  │ ✓ res. │ +0 (puntual)   │ │
│ │ 24/04    │ Analista marketing  │ Cynthia  │ ✓ res. │ ⚠ Sin propag.  │ │
│ └──────────┴─────────────────────┴──────────┴────────┴────────────────┘ │
└──────────────────────────────────────────────────────────────────────────┘
```

**Cambios respecto al actual:**
- Nueva columna **Propagación** que muestra:
  - `+N ofertas` si `propagacion_n > 0`
  - `+0 (puntual)` si fue marcado como excepción única
  - `⚠ Sin propag.` si `patron_corregido IS NULL` y el issue es resuelto (alerta — debería tener propagación)
- Filtro nuevo: "Sin propagación" para identificar issues que requieren auditoría retrospectiva

---

### 2.2 `/admin/issues/[id]` (detalle) — panel nuevo "Propagar corrección"

#### Estado A — issue pendiente (no resuelto todavía)

```
┌─ Issue 6fde657e ─────────────────────────────────────────────────────────┐
│                                                                          │
│ Título:    Correccion: #8299423434 - Operarios/as de despacho           │
│ Autor:     Diego Javier Schleser                                        │
│ Estado:    🟡 Pendiente                                                  │
│ Oferta:    8299423434  (link a /admin/validacion?id=...)                │
│                                                                          │
│ Descripción:                                                             │
│ "Ocupación ESCO: Peón de la industria metalúrgica. Código ESCO 9319.1.. │
│ ..."                                                                     │
│                                                                          │
│ ─────────────────────────────────────────────────────────────────────── │
│ ⚙ RESOLVER ISSUE                                                         │
│                                                                          │
│  Paso 1 / 5: Aplicar fix puntual                                        │
│   ¿Ya aplicaste el cambio en config y reprocesaste la oferta?           │
│   [ Sí, fix puntual aplicado ]   [ Cancelar ]                           │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

#### Estado B — fix puntual aplicado, ahora propagar

```
┌─ Issue 6fde657e ─────────────────────────────────────────────────────────┐
│ ⚙ PROPAGAR CORRECCIÓN                                                    │
│                                                                          │
│  Paso 2 / 5: Estructurar el patrón                                      │
│                                                                          │
│  Tipo de corrección:  [▼ matching_esco              ]                   │
│                                                                          │
│  Campo afectado:      [▼ esco_label                  ]                   │
│                                                                          │
│  Condición:                                                              │
│   [▼ regla_aplicada     ]   [ R358_despacho_metalurgico_grua  ]         │
│                                                                          │
│  Valor anterior:      [ 9333.3                       ]                   │
│  Valor nuevo:         [ 8343.4                       ]                   │
│                                                                          │
│  💡 Patrón inferido automáticamente del texto del issue                 │
│  ¿Querés ajustar algo? [editable]                                       │
│                                                                          │
│  [ ⏵ Estimar propagación (dry-run) ]                                    │
└──────────────────────────────────────────────────────────────────────────┘
```

#### Estado C — dry-run resultado

```
┌─ Issue 6fde657e ─────────────────────────────────────────────────────────┐
│ ⚙ PROPAGAR CORRECCIÓN                                                    │
│                                                                          │
│  Paso 3 / 5: Resultado dry-run                                          │
│                                                                          │
│  📊 Identificadas 7 ofertas con el mismo patrón                         │
│                                                                          │
│  Sample (primeras 5):                                                   │
│   ┌─────────────┬──────────────────────────────────────────────────┐    │
│   │ id_oferta   │ Título                                           │    │
│   ├─────────────┼──────────────────────────────────────────────────┤    │
│   │ 8299423434  │ Operarios/as de despacho metalúrgico Pompeya    │    │
│   │ 1118228703  │ Operario de despacho / Maquinista                │    │
│   │ 5922467194  │ Operario de Despacho Administrativo (Eventual)  │    │
│   │ 6602949585  │ Auxiliar de despacho                             │    │
│   │ 7710193867  │ Operario de Despacho c/exp. ind. metalúrgica    │    │
│   └─────────────┴──────────────────────────────────────────────────┘    │
│   (+ 2 más — ver lista completa)                                        │
│                                                                          │
│  ⚠ Esta acción modificará 7 ofertas en BD y dashboard.                  │
│                                                                          │
│  [ ✗ Cancelar ]    [ ⏯ Aplicar a las 7 ]    [ ⏸ Es solo puntual ]      │
└──────────────────────────────────────────────────────────────────────────┘
```

**3 botones:**
- **Aplicar a las 7** → ejecuta `propagate_correction(dry_run=False, issue_id=...)`
- **Es solo puntual** → marca issue con `propagacion_n=0`, nota "excepción puntual sin patrón generalizable"
- **Cancelar** → vuelve a estado B (ajustar patrón)

#### Estado D — resultado post-aplicación

```
┌─ Issue 6fde657e ─────────────────────────────────────────────────────────┐
│ ⚙ PROPAGAR CORRECCIÓN                                                    │
│                                                                          │
│  Paso 4 / 5: Aplicación completada ✅                                    │
│                                                                          │
│  📊 7 ofertas actualizadas exitosamente                                 │
│  📊 0 errores                                                            │
│  📊 0 ofertas saltadas (lock validado, etc.)                            │
│                                                                          │
│  Verificación post-fix:                                                 │
│   ✅ 7/7 ofertas tienen target esco_code = 8343.4                        │
│                                                                          │
│  Acciones realizadas:                                                   │
│   - UPDATE ofertas_esco_matching en 7 filas                             │
│   - issue.patron_corregido actualizado                                  │
│   - issue.propagacion_n = 7                                             │
│   - issue.propagacion_ids = [list]                                      │
│                                                                          │
│  Próximo paso:                                                          │
│   [ ⏵ Cerrar issue + Sync Supabase ]                                    │
└──────────────────────────────────────────────────────────────────────────┘
```

#### Estado E — issue resuelto (vista final)

```
┌─ Issue 6fde657e ─────────────────────────────────────────────────────────┐
│ Estado:    ✅ Resuelto el 27/04 16:48                                   │
│ Resuelto por:  Cynthia                                                  │
│                                                                          │
│ Solución:   "SPEC P + S aplicado. R358 + área Logística. 7 ofertas      │
│              propagadas."                                               │
│                                                                          │
│ ┌─ Propagación ─────────────────────────────────────────────────────┐   │
│ │ Patrón corregido:   matching_esco (regla_aplicada=R358)           │   │
│ │ Cantidad propagada: 7 ofertas                                     │   │
│ │ IDs tocados:        [ Ver lista completa ▼ ]                      │   │
│ │ Verificación:       ✅ 7/7 OK                                      │   │
│ └────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────┘
```

---

### 2.3 `/admin/validacion` — botón directo "Crear issue + propagar"

Cuando Cyn/Diego están validando ofertas y detectan un error, hoy crean issue desde el flujo normal. **Nuevo:** botón "Crear issue con propagación inteligente":

```
┌─ Validación oferta 8299423434 ───────────────────────────────────────────┐
│                                                                          │
│ Título: Operarios/as de despacho metalúrgico                            │
│ ESCO actual: 8343.4 operador de grúa de instalaciones de producción     │
│                                                                          │
│  [ ✓ OK ]   [ ✗ Error ]   [ ❓ Revisar ]                                 │
│                                                                          │
│  Si Error → modal:                                                       │
│   ┌─────────────────────────────────────────────────┐                   │
│   │ ¿Qué está mal?                                  │                   │
│   │  ☐ Ocupación ESCO incorrecta                    │                   │
│   │  ☐ Área funcional incorrecta                    │                   │
│   │  ☐ Skills alucinadas / faltantes                │                   │
│   │  ☐ Tareas mal extraídas                         │                   │
│   │                                                 │                   │
│   │ Cuál es el valor correcto?                      │                   │
│   │ [ esco_code: ____ ]  [ área: ____ ]             │                   │
│   │                                                 │                   │
│   │ Justificación:                                  │                   │
│   │ [ textarea ]                                    │                   │
│   │                                                 │                   │
│   │  [ Cancelar ]  [ Crear issue + Estimar prop. ] │                   │
│   └─────────────────────────────────────────────────┘                   │
└──────────────────────────────────────────────────────────────────────────┘
```

Al hacer click en **"Crear issue + Estimar propagación"**, automáticamente:
1. Crea el issue con `campo_afectado` y `valor_esperado` estructurados
2. Lleva al detalle del issue (estado B/C del wireframe 2.2)
3. Cyn ve cuántas ofertas similares hay
4. Decide aplicar o no

---

## 3. Componentes nuevos

| Componente | Path propuesto | Función |
|---|---|---|
| `<PropagationPanel>` | `components/issues/PropagationPanel.tsx` | Panel de los 5 pasos (estados B→E) |
| `<PatronEditor>` | `components/issues/PatronEditor.tsx` | Form de tipo+campo+condicion+valores (estado B) |
| `<PropagationDryRunResult>` | `components/issues/PropagationDryRunResult.tsx` | Tabla con sample y conteo (estado C) |
| `<PropagationBadge>` | `components/issues/PropagationBadge.tsx` | Badge con `+N` o `⚠ Sin propag.` |
| `<IssueErrorModal>` | `components/validacion/IssueErrorModal.tsx` | Modal "Crear issue + propagar" desde validación |

---

## 4. API endpoints nuevos

Backend Next.js API routes:

| Endpoint | Método | Función |
|---|---|---|
| `/api/issues/[id]/propagation/dry-run` | POST | Body: patron → llama propagate_correction(dry_run=True) → devuelve N + sample |
| `/api/issues/[id]/propagation/apply` | POST | Body: patron → propagate_correction(dry_run=False, issue_id=...) → devuelve resultado |
| `/api/issues/[id]/propagation/excepcion` | POST | Marca issue como `propagacion_n=0`, nota "puntual" |

**Implementación backend:** Python helper SPEC T (`scripts/correcciones/propagate_correction.py`) expuesto vía:
- Opción A: Edge function en Supabase que ejecuta el helper
- Opción B: API route Next.js que invoca el script Python via subprocess (más simple para empezar)
- Opción C: Llamadas directas a Supabase desde Next (replicar lógica en TS — más mantenible largo plazo)

**Recomendación:** Opción B para v1 (rápido), migrar a C si crece.

---

## 5. Flujo de uso completo

```
Cyn/Diego validan oferta
   ↓
Detectan error
   ↓
[Click "Error"] → modal con tipo + valor correcto + justificación
   ↓
Click "Crear issue + Estimar propag." → issue creado con campos estructurados
   ↓
Pantalla detalle issue → [Click "Sí, fix puntual aplicado"]
   ↓
Pantalla "Estructurar patrón" → patrón inferido automáticamente
   ↓
[Click "Estimar propagación (dry-run)"] → muestra N ofertas + sample
   ↓
[Click "Aplicar a las N"] → ejecuta propagate_correction
   ↓
Pantalla resultado → 7/7 OK
   ↓
[Click "Cerrar issue + Sync"] → cierra + dispara sync Supabase
   ↓
Issue ✅ resuelto con propagación trazable
```

---

## 6. Lista de issues sin propagación (auditoría retrospectiva)

Nueva pantalla `/admin/issues/sin-propagacion`:

```
┌─ Issues resueltos sin propagación ───────────────────────────────────────┐
│                                                                          │
│ 468 issues resueltos no tienen patron_corregido ni propagacion_n.       │
│ Sugerencia: ejecutar propagación retrospectiva.                         │
│                                                                          │
│ ┌──────────┬───────────────────┬───────────┬────────┬─────────────┐    │
│ │ Fecha    │ Título            │ Autor     │ Tipo   │ Acción      │    │
│ ├──────────┼───────────────────┼───────────┼────────┼─────────────┤    │
│ │ 23/04    │ Operario depósito │ Cynthia   │ NLP    │ [Propagar]  │    │
│ │ 23/04    │ Despacho metalúrg.│ Diego     │ ESCO   │ [Propagar]  │    │
│ │ ...      │ ...               │ ...       │ ...    │ [Propagar]  │    │
│ └──────────┴───────────────────┴───────────┴────────┴─────────────┘    │
│                                                                          │
│ [ Auditar todos automáticamente (batch) ]                               │
└──────────────────────────────────────────────────────────────────────────┘
```

Esta pantalla habilita la **Fase 3 SPEC T (auditoría retrospectiva)** desde la UI: Cyn/Diego pueden ir uno por uno o pedir auditoría batch.

---

## 7. Decisiones que necesito antes de implementar

1. **¿Aprobás el flujo de 5 pasos** o lo simplificamos a menos botones?
2. **¿Empezamos por la lista (2.1 + 2.2) y dejamos 2.3 (modal en /admin/validacion) para después?**
3. **¿Backend Opción B (subprocess Python)** vs Opción C (replicar TS)?
4. **¿Pantalla "sin propagación" se incluye en v1** o queda para Fase 3?

Una vez aprobado, estimo la implementación en **6-8 horas** (componentes nuevos + API routes + tests + integración).

---

## 8. Lo que este wireframe NO cubre

- Notificaciones push cuando una propagación afecta muchas ofertas (>100 podría requerir confirmación adicional).
- Rollback UI (si una propagación rompe cosas, hoy se hace por SQL manual).
- Undo de excepción puntual (si se marcó "es puntual" por error).
- Auditoría con diferencial por mes/autor.

Esos son nice-to-haves para v2.
