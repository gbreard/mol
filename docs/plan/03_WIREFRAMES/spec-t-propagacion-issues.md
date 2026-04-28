# Wireframe — UI de Propagación de Correcciones (SPEC T Fase 4) — v2

**Fecha:** 2026-04-28
**Spec:** `docs/specs/2026-04-27_T_flujo_propagacion_correcciones.md`
**Audiencia:** Cyn, Diego (analistas — solo solicitan); Claude, Gerardo (admin — aplican)
**Ubicación:** integrada en `/admin/issues` y `/admin/validacion`

---

## 1. Cambio respecto a v1

**v1 (descartado):** todos los usuarios podían aplicar propagación con un click.

**v2 (esta versión):** separación de roles estricta:

| Rol | Puede VER propagación? | Puede SOLICITAR propagación? | Puede APLICAR propagación? |
|---|:---:|:---:|:---:|
| **Analista** (Cyn, Diego) | ✅ | ✅ | ❌ |
| **Admin** (Gerardo) + Claude | ✅ | ✅ | ✅ |

**Razón:** una propagación mal calibrada puede dañar miles de ofertas. El admin hace controles previos (dry-run, sample, validar target ESCO) antes de aplicar.

---

## 2. Modelo de datos adicional

Agregar columna a `issues`:

| Columna | Tipo | Para qué |
|---|---|---|
| `propagacion_solicitada` | boolean default false | Analista marca que la corrección probablemente aplica a otras ofertas similares. Genera orden pendiente. |
| `propagacion_solicitada_por` | text | Email del analista que pidió la propagación. |
| `propagacion_solicitada_at` | timestamp | Cuándo se pidió. |

Migration:
```sql
ALTER TABLE issues
  ADD COLUMN IF NOT EXISTS propagacion_solicitada boolean DEFAULT false,
  ADD COLUMN IF NOT EXISTS propagacion_solicitada_por text,
  ADD COLUMN IF NOT EXISTS propagacion_solicitada_at timestamptz;

CREATE INDEX IF NOT EXISTS idx_issues_propagacion_solicitada
  ON issues(propagacion_solicitada) WHERE propagacion_solicitada = true;
```

---

## 3. Pantallas — versión analista (Cyn/Diego)

### 3.1 `/admin/issues` (lista) — vista analista

```
┌─ Issues ─────────────────────────────────────────────────────────────────┐
│ [Pendientes (1000)] [Resueltos (542)] [Todos]   🔍 Buscar...             │
│                                                                          │
│ Filtros: [▼ Solo "Sin propagación"]  [▼ Solo "Pendientes propagar"]     │
│                                                                          │
│ ┌──────────┬──────────────────┬─────────┬────────┬─────────────────┐   │
│ │ Fecha    │ Título           │ Autor   │ Estado │ Propagación     │   │
│ ├──────────┼──────────────────┼─────────┼────────┼─────────────────┤   │
│ │ 27/04    │ Operario depós.  │ Cynthia │ ✓ res. │ ✅ +313 ofertas │   │
│ │ 27/04    │ Despacho metal.  │ Cynthia │ ✓ res. │ ➡ Excepción     │   │
│ │ 28/04    │ Vendedor X       │ Diego   │ ✓ res. │ 🟡 Solicitada   │   │
│ │ 24/04    │ Analista mkt.    │ Cynthia │ ✓ res. │ ⚠ Sin auditar   │   │
│ └──────────┴──────────────────┴─────────┴────────┴─────────────────┘   │
└──────────────────────────────────────────────────────────────────────────┘
```

**Badges en columna Propagación (read-only para analistas):**
- ✅ `+N ofertas` — propagación efectiva ya aplicada
- ➡ `Excepción` — declarado puntual, no aplica a otros
- 🟡 `Solicitada` — alguien (analista) marcó orden, admin todavía no procesó
- ⚠ `Sin auditar` — issue cerrado sin pasar por sistema de propagación (los 462 de Fase 3 retrospectiva)

### 3.2 `/admin/issues/[id]` (detalle) — vista analista

```
┌─ Issue 6fde657e ─────────────────────────────────────────────────────────┐
│ Estado:    ✅ Resuelto el 27/04 16:48                                    │
│ Resuelto por:  Cynthia                                                   │
│                                                                          │
│ ┌─ Propagación ─────────────────────────────────────────────────────┐   │
│ │ ✅ Esta corrección se propagó a 7 ofertas similares.              │   │
│ │                                                                   │   │
│ │ Patrón aplicado:                                                  │   │
│ │   Tipo:           matching_esco                                   │   │
│ │   Condición:      regla_aplicada = R358_despacho_metalurgico_grua │   │
│ │   Valor anterior: 9333.3                                          │   │
│ │   Valor nuevo:    8343.4                                          │   │
│ │                                                                   │   │
│ │ Aplicada por:  Gerardo el 27/04 16:48                            │   │
│ │ [ Ver lista de ofertas afectadas ▼ ]                             │   │
│ └────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────┘
```

**Caso "no propagado todavía" (analista solicitó):**

```
┌─ Issue 1234abcd ─────────────────────────────────────────────────────────┐
│ ┌─ Propagación ─────────────────────────────────────────────────────┐   │
│ │ 🟡 Solicitada por Cynthia el 28/04 — pendiente revisión admin    │   │
│ │                                                                   │   │
│ │ Justificación: "Esto seguro aplica a otros vendedores similares"  │   │
│ │                                                                   │   │
│ │ ⏳ El admin va a hacer dry-run + controles antes de aplicar.      │   │
│ │ [ Cancelar solicitud ] (solo si vos la creaste)                  │   │
│ └────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────┘
```

**Caso "sin auditar" (issue resuelto sin sistema):**

```
┌─ Issue ───────────────────────────────────────────────────────────────────┐
│ ┌─ Propagación ─────────────────────────────────────────────────────┐   │
│ │ ⚠ Este issue se cerró antes del sistema de propagación SPEC T.   │   │
│ │ No hay registro de si la corrección se aplicó a ofertas similares.│   │
│ │                                                                   │   │
│ │ ¿Considerás que esta corrección debería aplicarse a otras ofertas │   │
│ │ similares?                                                        │   │
│ │                                                                   │   │
│ │ [ Sí, solicitar propagación ]   [ No, fue puntual ]              │   │
│ └────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────┘
```

Click en "Solicitar propagación" → modal corta:

```
┌─ Solicitar propagación ──────────────────────────┐
│ Justificación (1-2 líneas):                       │
│ [ textarea ]                                      │
│                                                   │
│ Tipo aproximado (opcional, ayuda al admin):       │
│ [▼ Selecciona...                              ]   │
│   - Área funcional incorrecta                     │
│   - Ocupación ESCO incorrecta                     │
│   - Skills alucinadas                             │
│   - Tareas mal extraídas                          │
│                                                   │
│ [ Cancelar ]   [ Enviar solicitud ]              │
└────────────────────────────────────────────────────┘
```

### 3.3 `/admin/validacion` — modal "Crear issue con marca de propagación"

Cuando Cyn/Diego marcan Error en una oferta, el modal incluye **checkbox al final**:

```
┌─ Crear issue de error ───────────────────────────────────────┐
│ ¿Qué está mal?                                               │
│  ☑ Ocupación ESCO incorrecta                                 │
│  ☐ Área funcional incorrecta                                 │
│  ☐ Skills alucinadas / faltantes                             │
│  ☐ Tareas mal extraídas                                      │
│                                                              │
│ ESCO correcto sugerido:  [ 7222.2 armero/armera        ]    │
│                                                              │
│ Justificación:                                               │
│ [ textarea ]                                                 │
│                                                              │
│ ──────────────────────────────────────────────────────────── │
│ ☑ Esta corrección probablemente aplica a otras ofertas      │
│    similares — solicitar propagación                        │
│                                                              │
│ [ Cancelar ]    [ Crear issue ]                             │
└──────────────────────────────────────────────────────────────┘
```

Si el checkbox está marcado, al crear el issue automáticamente se setea:
- `propagacion_solicitada = true`
- `propagacion_solicitada_por = email_de_cyn`
- `propagacion_solicitada_at = now()`

---

## 4. Pantallas — versión admin (Gerardo)

### 4.1 `/admin/issues/cola-propagacion` (NUEVA, solo admin)

```
┌─ Cola de propagación ────────────────────────────────────────────────────┐
│                                                                          │
│ 🟡 12 órdenes pendientes solicitadas por analistas                      │
│                                                                          │
│ ┌──────────┬──────────────────┬─────────┬────────────┬───────────────┐ │
│ │ Sol. el  │ Issue            │ Solicit.│ Tipo aprox │ Acción        │ │
│ ├──────────┼──────────────────┼─────────┼────────────┼───────────────┤ │
│ │ 28/04    │ Vendedor X       │ Diego   │ Matching   │ [ Procesar ]  │ │
│ │ 28/04    │ Cocinero PyME    │ Cyn     │ Skills     │ [ Procesar ]  │ │
│ │ ...      │ ...              │ ...     │ ...        │ [ Procesar ]  │ │
│ └──────────┴──────────────────┴─────────┴────────────┴───────────────┘ │
│                                                                          │
│ [ Procesar todas en lote (con review) ]                                 │
└──────────────────────────────────────────────────────────────────────────┘
```

### 4.2 `/admin/issues/[id]` (detalle) — vista admin (Gerardo)

Cuando es admin Y el issue tiene `propagacion_solicitada=true`, aparece panel "Procesar propagación":

```
┌─ Issue 1234abcd ─────────────────────────────────────────────────────────┐
│ Estado:    ✅ Resuelto                                                   │
│ Solicitante: Cynthia el 28/04                                            │
│ Justificación: "Esto seguro aplica a otros vendedores similares"        │
│                                                                          │
│ ┌─ Procesar propagación (admin) ────────────────────────────────────┐   │
│ │                                                                    │  │
│ │ Paso 1 / 3: Estructurar patrón                                    │  │
│ │   Tipo:        [▼ matching_esco                  ]                │  │
│ │   Campo:       [▼ esco_label                      ]                │  │
│ │   Condición:                                                       │  │
│ │     [▼ regla_aplicada       ] [ R358_despacho_metalurgico_grua ]  │  │
│ │   Valor anterior: [ 9333.3 ]                                       │  │
│ │   Valor nuevo:    [ 8343.4 ]                                       │  │
│ │                                                                    │  │
│ │ [ ⏵ Estimar propagación (dry-run) ]                                │  │
│ └────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────┘
```

Estado dry-run:

```
│ ┌─ Procesar propagación (admin) ────────────────────────────────────┐   │
│ │ Paso 2 / 3: Resultado dry-run                                     │  │
│ │                                                                    │  │
│ │ 📊 7 ofertas matchean el patrón                                   │  │
│ │                                                                    │  │
│ │ Sample:                                                            │  │
│ │   8299423434  Operarios/as despacho metalúrgico                   │  │
│ │   1118228703  Operario de despacho / Maquinista                   │  │
│ │   5922467194  Operario de Despacho Administrativo                 │  │
│ │   ...                                                              │  │
│ │                                                                    │  │
│ │ ⚠ Esta acción modificará 7 ofertas en BD y dashboard.             │  │
│ │                                                                    │  │
│ │ [ ✗ Rechazar solicitud ]   [ ⏯ Aplicar a las 7 ]                 │  │
│ └────────────────────────────────────────────────────────────────────┘  │
```

Estado post-aplicación (mismo de v1, no cambia).

### 4.3 `/admin/issues/sin-propagacion` — vista admin con auditoría retrospectiva

```
┌─ Issues resueltos sin propagación ───────────────────────────────────────┐
│                                                                          │
│ 462 issues resueltos antes de SPEC T no tienen propagación auditada.    │
│ Pueden contener correcciones aplicables a otras ofertas.                │
│                                                                          │
│ Filtros: [▼ Por autor]  [▼ Por categoría inferida]                      │
│                                                                          │
│ ┌──────────┬───────────────────┬──────────┬──────────┬──────────────┐  │
│ │ Fecha    │ Título            │ Autor    │ Categoría│ Solicitada?  │  │
│ ├──────────┼───────────────────┼──────────┼──────────┼──────────────┤  │
│ │ 23/04    │ Operario depós.   │ Cynthia  │ NLP area │ [Solicitar]  │  │
│ │ 22/04    │ Cocinero planch.  │ Diego    │ ESCO     │ [Solicitar]  │  │
│ │ ...      │ ...               │ ...      │ ...      │ [Solicitar]  │  │
│ └──────────┴───────────────────┴──────────┴──────────┴──────────────┘  │
│                                                                          │
│ [ Procesar todos en batch (Claude infiere patrones) ]                  │
└──────────────────────────────────────────────────────────────────────────┘
```

Para los **462 issues sin patrón estructurable** (de Fase 3), Cyn/Diego pueden:
- Click "Solicitar" → marca `propagacion_solicitada=true` → entra a cola admin
- O si ya saben que era puntual, dejarlo como está

### 4.4 Estado E (resuelto post-aplicación) — visible para todos

```
┌─ Issue 1234abcd ─────────────────────────────────────────────────────────┐
│ ┌─ Propagación ─────────────────────────────────────────────────────┐   │
│ │ ✅ Aplicada por Gerardo el 28/04 14:32                            │   │
│ │ 7 ofertas re-matcheadas → target esco_code 8343.4                 │   │
│ │ Verificación: 7/7 OK                                              │   │
│ │                                                                   │   │
│ │ Patrón:        matching_esco                                      │   │
│ │ Condición:     regla_aplicada = R358_despacho_metalurgico_grua    │   │
│ │ Sol. original: Cynthia el 28/04 12:15                            │   │
│ │                                                                   │   │
│ │ [ Ver lista de ofertas afectadas ▼ ]                             │   │
│ └────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Componentes nuevos

| Componente | Path | Función | Roles |
|---|---|---|---|
| `<PropagationBadge>` | `components/issues/PropagationBadge.tsx` | Badge en lista (✅ +N / 🟡 Solicitada / ⚠ Sin auditar) | Todos |
| `<PropagationInfoPanel>` | `components/issues/PropagationInfoPanel.tsx` | Panel info read-only del estado de propagación | Todos |
| `<RequestPropagationButton>` | `components/issues/RequestPropagationButton.tsx` | Botón + modal para que analistas soliciten | Analistas |
| `<ProcessPropagationPanel>` | `components/issues/ProcessPropagationPanel.tsx` | Panel admin con dry-run + apply | Admin |
| `<PropagationQueue>` | `app/admin/issues/cola-propagacion/page.tsx` | Lista de órdenes pendientes | Admin |
| `<IssueErrorModalConSolicitud>` | `components/validacion/IssueErrorModal.tsx` | Modal error con checkbox solicitar | Analistas |

---

## 6. API endpoints nuevos

| Endpoint | Método | Función | Auth |
|---|---|---|---|
| `/api/issues/[id]/solicitar-propagacion` | POST | Marca `propagacion_solicitada=true` | analista+ |
| `/api/issues/[id]/cancelar-solicitud` | POST | Solo el solicitante puede cancelar | analista (solo el suyo) |
| `/api/issues/[id]/propagation/dry-run` | POST | Body: patron → llama `propagate_correction(dry_run=True)` | **admin** |
| `/api/issues/[id]/propagation/apply` | POST | Body: patron → `propagate_correction(dry_run=False)` | **admin** |
| `/api/issues/[id]/propagation/rechazar` | POST | Marca propagación rechazada (no aplicable) | **admin** |
| `/api/issues/cola-propagacion` | GET | Lista órdenes pendientes | **admin** |

**Backend (sigo recomendando Opción B):** API routes Next invocan `scripts/correcciones/propagate_correction.py` via subprocess. Servicio rápido, ya está testeado.

---

## 7. Flujo end-to-end

```
1. Cyn valida oferta en /admin/validacion
   → marca Error, completa modal
   → checkbox "solicitar propagación" si cree que aplica a otras
   → click "Crear issue"

2. Issue creado con propagacion_solicitada=true
   → aparece en /admin/issues/cola-propagacion (admin)
   → Cyn lo ve en su lista con badge 🟡 Solicitada

3. Gerardo (admin) entra a cola-propagacion
   → click "Procesar" en una orden
   → estructura patrón (autocompletado)
   → click "Estimar (dry-run)"
   → ve N ofertas + sample
   → decide: ✗ Rechazar / ⏯ Aplicar

4. Apply ejecutado
   → propagate_correction.py corre vía subprocess
   → BD local + Supabase actualizadas
   → issue.patron_corregido + propagacion_n + propagacion_ids llenos
   → Cyn ve badge ✅ +N en su lista

5. Para issues retrospectivos (462 sin auditar)
   → Cyn puede entrar a /admin/issues/sin-propagacion
   → click "Solicitar" en los que cree que aplican
   → entra a cola admin
   → admin procesa
```

---

## 8. Decisiones reducidas (vs v1)

Como definimos el modelo de roles, ya no hay 4 decisiones — solo:

1. **¿Backend Opción B (subprocess) confirmás?** Sigo recomendando B.
2. **¿Migration SQL adicional para los 3 campos `propagacion_solicitada*`?** Necesaria sí o sí — la aplico al arrancar.

Todo el flujo de roles + read-only para analistas + cola admin queda fijo según este wireframe.

**Estimación:** ~6-8 horas (sin cambio sustancial vs v1, solo redistribuye componentes según rol).

---

## 9. Copy/textos explicativos para analistas

Los analistas (Cyn/Diego) son usuarios no-técnicos. Cada punto donde aparece propagación debe tener una explicación breve y clara.

### 9.1 Tooltip en columna "Propagación" de la lista

Hover sobre el header de columna:

> **Propagación**
> Cuando una corrección que hiciste se aplica también a otras ofertas similares.
> Por ejemplo, si arreglás "Operario de depósito" → área Logística, el sistema
> puede aplicar lo mismo a las otras 313 ofertas similares en la BD.

### 9.2 Hover sobre cada badge

| Badge | Tooltip |
|---|---|
| ✅ `+N ofertas` | "Esta corrección ya se propagó a N ofertas similares además de la original." |
| ➡ `Excepción` | "Caso puntual: la corrección NO aplica a otras ofertas similares." |
| 🟡 `Solicitada` | "Pediste que se propague pero el admin todavía no lo procesó." |
| ⚠ `Sin auditar` | "Issue cerrado antes del sistema de propagación. Si creés que aplica a otras ofertas, podés solicitarlo." |

### 9.3 Banner explicativo arriba del panel "Propagación" en detalle de issue (vista analista)

Primera vez que el analista entra al detalle:

```
ℹ️  ¿Qué es la propagación?
Cuando reportás un error, hay que arreglarlo en la oferta que viste, pero
puede ser que el mismo error esté en muchas otras ofertas similares.
La "propagación" busca esas ofertas y aplica la misma corrección a todas.

Vos podés:  ✅ Ver si una corrección ya se propagó
            ✅ Solicitar que se propague (si creés que hay otras similares)
            ❌ NO aplicar la propagación directamente

Quien aplica:  el admin (Gerardo) hace controles previos antes de modificar
              cientos de ofertas.

[ Entendido, no mostrar más ]
```

(Banner colapsable — desaparece después del primer click.)

### 9.4 Modal "Solicitar propagación" — copy

```
┌─ Solicitar propagación ──────────────────────────────────────┐
│                                                              │
│ Si pensás que esta corrección debería aplicarse a otras      │
│ ofertas similares (no solo a esta), pedile al admin que       │
│ lo revise y lo aplique.                                      │
│                                                              │
│ Justificación (qué patrón ves):                              │
│ [ "todos los operarios de depósito tienen este problema" ]   │
│                                                              │
│ Tipo aproximado (opcional, ayuda al admin):                  │
│ [▼ Selecciona...                                         ]   │
│                                                              │
│ ⚠ El admin va a revisar antes de aplicar. Si está mal, te    │
│   avisa. Si está bien, lo aplica y te notifica con cuántas   │
│   ofertas se modificaron.                                    │
│                                                              │
│ [ Cancelar ]    [ Enviar solicitud ]                        │
└──────────────────────────────────────────────────────────────┘
```

### 9.5 Checkbox "Solicitar propagación" en modal validación

Texto al lado del checkbox:

> ☑ **Esta corrección probablemente aplica a otras ofertas similares — solicitar propagación**
>
> *Pequeño asterisco al lado:* (?)
>
> *Tooltip al hacer hover en (?):*
> Si marcás esto, le pedimos al admin que revise y aplique tu corrección a
> las otras ofertas que tengan el mismo problema. El admin hace los controles
> primero, no se aplica automáticamente.

### 9.6 Banner en pantalla `/admin/issues/sin-propagacion`

```
ℹ️  Issues resueltos antes de tener este sistema (462 issues)
   Estos issues fueron resueltos antes que existiera la propagación
   automática. Algunos pueden tener correcciones que aplican a muchas
   otras ofertas, pero nunca se propagaron.

   Si entrás a uno y pensás que la corrección debería aplicarse a otras
   ofertas similares, click en "Solicitar". El admin lo revisa.

   Si fue puntual (una sola oferta con problema único), no hace falta
   hacer nada — quedan así.
```

### 9.7 Mensaje cuando un analista intenta acceder a `/admin/issues/cola-propagacion`

Si un analista (Cyn/Diego) intenta acceder a la cola admin:

```
🔒 Esta sección es solo para admin.
   Vos podés solicitar propagaciones, pero quien las aplica es el admin.
   Las propagaciones que hayas pedido aparecen en tu lista de issues
   con badge 🟡 Solicitada.

[ Volver a /admin/issues ]
```

### 9.8 Mensaje cuando vuelve aplicada (notificación opcional)

Cuando el admin aplica una propagación que solicitó un analista, idealmente
se le avisa al analista. Versión simple: badge cambia de 🟡 a ✅ y al hacer
click muestra:

```
✅ Tu solicitud de propagación se aplicó
   Aplicada por: Gerardo el 28/04 14:32
   Ofertas afectadas: 7
   [ Ver lista ]
```

---

## 10. Lo que NO cubre v2

- Notificación push al admin cuando llega una solicitud nueva (queda manual: admin chequea cola).
- Histórico de quién aplicó cada propagación (queda en `solucion_aplicada` texto libre).
- Rollback de propagación desde UI (sigue siendo SQL manual).
- Permisos granulares por categoría (ej: Cyn puede aplicar matching pero no NLP). Todos los analistas tienen los mismos permisos.

Esos son nice-to-haves para v3.
