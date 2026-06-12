# SPEC S1.B.7 — Relevamiento de UI

> Versión 1.0 (capas 5.1 + 5.2 + 5.3 + 5.4 — Memoria operativa + estado relevado + deuda + principios) · 2026-06-12
> Séptimo y último spec de la fase S1.B — Relevamiento del sistema. Releva la UI del proyecto MOL. Sigue la plantilla común del master v0.2. Tras su cierre se abre S1.C — Master de reparación.

---

## 5.1 Memoria operativa — Gerardo + Cyn + consolidación

### El marco: la fábrica y los locales

Metáfora textual de Gerardo (2026-06-11): **"MOL es como la fábrica de pan y facturas; OE y las otras aplicaciones son como los locales de panadería — no necesitan fabricar porque la fabricación está concentrada en otro lado."**

MOL (la fábrica) produce los datos: ofertas procesadas, ocupaciones, skills, tareas, atributos. OE y las aplicaciones futuras (los locales) consumen esos datos para servirlos a terceros. Son **independientes**: el dashboard actual (fase3, 118 páginas) mezcla la UI de la fábrica (validación, scraping, administración del pipeline) con UIs de los locales (módulo OE: casos, personas, perfiles) y experimentos.

**Alcance de este spec**: la UI de la fábrica. Las UIs de los locales se identifican y delimitan, pero no se relevan en profundidad — son producto, no infraestructura, y tendrán su propio ciclo.

### Usuarios reales de la UI

- **Cyn (validadora)**: la usuaria principal. Su día a día es la pantalla de validación.
- **Gerardo (operador/arquitecto)**: mira mucho la sección de scraping; **le gustaría manejar más la UI pero desconfía de ella** — opera el sistema vía Claude Code en su lugar. Es el mismo patrón del botón de scraping (S1.B.2): la herramienta existe, la confianza no.
- **Sergio (constructor)**: construyó el dashboard con Gerardo, pero no entra al sistema como usuario.
- **Diego Schleser**: participó como validador en alguna ventana (las 218 validaciones de S1.B.3 incluyen marcas suyas).

### Uso real: desconocido

El dashboard tiene **118 páginas** construidas entre Gerardo y Sergio. Respuesta textual de Gerardo: "realmente no tengo idea cuánto de lo que está ahí realmente usamos. Algunas cosas son del OE o de las aplicaciones que estamos pensando." No hay analítica de uso ni inventario de qué pantallas viven y cuáles son restos.

### La deuda de Cyn (registrada en S1.B.3 D-09, pertenece a este spec)

1. **Las correcciones no quedan visibles en la oferta**: se envían como issue y la oferta se ve igual. Sin seguimiento, sin reutilización de criterio.
2. **Bug del guardado: al guardar, el sistema salta automáticamente a otra oferta** — riesgo de pérdida silenciosa de trabajo validado.
3. **Filtros imprecisos**: traen ofertas de sectores que no corresponden.
4. **Sin estados por oferta** (pendiente / en revisión / corregida / finalizada).
5. **No puede agregar ni borrar skills**: trabaja copiando todo al campo "observaciones" como texto libre. La validadora trabaja alrededor de la herramienta, no con ella.

Su pedido número uno: **historial visible de correcciones dentro de la oferta** (qué trajo el sistema, qué corrigió, criterio, validación final).

### Lo acumulado en los otros specs que la UI debería exponer o consumir

Este spec hereda una lista concreta de "consumidores faltantes" detectados en los seis relevamientos anteriores:

- **Configurabilidad de los validadores sin exposición** (S1.B.6 D-07): reglas, severidades y bloqueantes ya ajustables en JSON — sin UI que los muestre ni opere.
- **~18.500 marcas de sector sin consumidor** (S1.B.6 D-06): el colapso del sector diagnosticado oferta por oferta y el dashboard lo muestra colapsado igual.
- **El re-encolado con corrección humana** (S1.B.6 D-08, visión de Gerardo): Cyn viendo el procesamiento en vivo, corrigiendo y devolviendo la oferta a la cola.
- **El panel de emergentes con cadena a buffers muertos** (S1.B.4 D-05): 431 emergentes pendientes, 0 aprobadas (dato de mayo).
- **Trazabilidad por oferta a través del pipeline** (S1.B.2, pedido de Gerardo; converge con el pedido de Cyn).
- **El botón de scraping en el que Gerardo no confía** (S1.B.2) y la sección de scraping ya relevada.
- **La admin UI que dispara el sync a Supabase vía poller** (S1.B.1) — único disparo del último eslabón del pipeline.

### Seguridad y acceso (deuda conocida, a verificar estado)

- **OE-11**: 13 endpoints sin guard (registrado en la deuda general del proyecto).
- **Contraseña hardcodeada** (marcada por Gerardo como baja urgencia en su momento).
- El dashboard deploya en Vercel (`mol-nextjs.vercel.app`, S1.B.1) — exposición pública a verificar.
- **Dashboard legacy `dashboards/production/`** (S1.B.1 D-08): no deployado, apunta a la misma Supabase.

### Hipótesis tentativas para la capa 5.2

1. **Una fracción menor de las 118 páginas tiene uso real**; el resto se reparte entre módulo OE (local), experimentos y restos de iteraciones.
2. **La frontera fábrica/local no está delimitada en el código**: rutas, componentes y tablas de Supabase mezcladas sin separación clara.
3. **La desconfianza de Gerardo tiene causas identificables en el código**: acciones sin feedback de resultado, estados stale, operaciones que fallan en silencio — verificable en el manejo de errores de las acciones de la UI.
4. **El bug del guardado de Cyn es localizable**: la navegación automática post-save debe estar en el código del formulario de validación.

### Notas para fases posteriores

- **La separación arquitectónica fábrica/locales** (qué UI pertenece a quién, sobre qué tablas) es input directo del master S1.C y de la planificación comercial.
- **La UI como el consumidor faltante**: la lista de "lo que la UI debería exponer" es, en buena medida, el plan de cierre de las cadenas muertas detectadas en todo el relevamiento.

---

## 5.2 Estado actual relevado

> Relevamiento de solo lectura sobre `fase3_dashboard/mol-dashboard/`. Sin Supabase viva, sin ejecutar el dashboard, sin probar endpoints. Lo no verificable sin conexión viva está marcado **[no verificable sin BD viva]**.

### 5.2.1 Cartografía: fábrica, local y resto

El dashboard tiene **118 páginas** (`app/**/page.tsx`) y **77 API routes** (`app/api/**/route.ts`). La clasificación por grupo:

| Grupo | Páginas | Qué es |
|---|---:|---|
| **Fábrica MOL** (`/admin/*`) | 40 | Validación, scraping, procesamiento/pipeline, catálogo, issues, métricas, usuarios. **8 son `/admin/laboratorio/*`** (indicadores experimentales, duplicados en OE y vip → más producto que fábrica). **Núcleo fábrica real ≈ 32.** |
| **Local OE** (`/oficina-empleo/*`) | 27 | Casos, personas, perfiles, vacantes, formación, laboratorio. El local más desarrollado. |
| **Otros productos** (`empresas` 9, `mi-futuro-laboral` 7, `vip` 11, `dashboard` 4) | 31 | Locales comerciales futuros. `empresas/*` y `mi-futuro-laboral/*` están casi todos con `MOCK_*` hardcodeado — pre-MVP, sin backend. |
| **Comercio** (`checkout`, `cuenta`) | 6 | Flujo de pago. Sin tocar desde 2026-02-07/08 (~4 meses). |
| **Público / marketing / auth + root** | 14 | home, precios, login, registro, términos, etc. |

**La frontera fábrica/local NO está delimitada en el código, pero el cruce es asimétrico y acotado:**
- Admin **no** toca tablas del local OE (`personas`/`perfiles`/`casos`).
- OE **sí** lee `ofertas_dashboard` (tabla de la fábrica) directo desde páginas cliente (`app/oficina-empleo/perfiles/matching/page.tsx:96`, `.../futuro/page.tsx`). Dependencia unidireccional local→fábrica, sin capa intermedia.
- Las API "puente" (`matching-offers`, `training-*`, `occupations/*`) leen de ambos mundos sin aislamiento. **No hay barrera de datos; la separación es solo convención de carpetas.**

**Uso/abandono** (aproximación por `git log` por directorio):
- **Vivo** (~1-2 meses): `/admin/validacion` (2026-06-03, el más activo), `/admin/aprendizaje`, `/admin/issues/*`, `/admin/procesamiento/catalogo`, `oficina-empleo/perfiles/*`.
- **Frío/abandonado** (4+ meses): `checkout/*`, `cuenta/*`, `dashboard/*`, `precios`, `registro` (2026-02), `/admin/logs` (2026-01-30, el más viejo).
- **Huérfanas sin link en menú: ~30+.** En admin, **7 rutas de `/admin/procesamiento/`** (correcciones, editores, fine-tuning, nlp-inference, oficios, reglas, sinonimos) y las 8 de `/admin/laboratorio/*` no están en el sidebar; se llega solo por URL directa.

→ ~20-30 páginas con mantenimiento activo; el resto (~90) en mantenimiento pasivo, mockeado o abandonado.

### 5.2.2 Las herramientas de la fábrica

**La pantalla de validación de Cyn** (`app/admin/validacion/page.tsx` + `components/validacion/`):

- **El "bug del guardado" — diagnóstico corregido.** No es race-condition ni pérdida silenciosa por la BD. `ValidationActions.tsx:80` hace `await saveValidacion(...)`; si falla salta al `catch` (`:200`), muestra `toast.error` y `return false` **sin navegar**. `onEvaluated(resultado)` (`:198`) corre **solo en éxito**, y recién ahí `page.tsx:218-220` ejecuta `navigateTo("next")` (comentado `// Auto-navigate to next`). **El problema real es el auto-avance intencional**: tras guardar OK el sistema salta a la oferta siguiente sin opción de quedarse, sin confirmación y sin undo. Cyn lo vive como "me salta de oferta" porque pierde el lugar y no puede revisar lo que acaba de marcar. La reparación es de diseño UX (no auto-avanzar / permitir quedarse), no arreglar una condición de carrera.
- **Corrección → issue (por qué "se ve igual").** Estructural: al marcar error/revisar, `saveValidacion` escribe `validacion_correcciones` (JSONB) en `ofertas_dashboard` **y** `createIssue` inserta en la tabla `issues` (`ValidationActions.tsx:132`). Pero los paneles de la oferta (`PuestoPanel`, `ClasificacionPanel`) leen solo de `ofertas_dashboard` y **no renderizan ni `validacion_correcciones` ni los issues asociados**. La corrección se guarda en dos lados y no se muestra en ninguno.
- **Estados / historial: el esqueleto existe, falta la UI.** Hay `estado_revision` (`'revisada'|'mal_extraida_total'|null`, SPEC W) en `lib/types.ts:342`, `AuditActionToolbar` que fetchea `/api/oferta/{id}/audit-history`, y `validacion_correcciones` en BD. **Nada se visualiza como historial.** El pedido nº1 de Cyn (historial visible dentro de la oferta) está a un componente de distancia de datos que ya se guardan.
- **Filtros por sector.** Filtra con `eq('clae_descripcion_seccion', value)` (`lib/supabase.ts:2113`), igualdad exacta, sin colapso de "Otro". La imprecisión que reporta Cyn **no está en el código del filtro**: apunta a datos sucios en `clae_descripcion_seccion` o a opciones de filtro desincronizadas. **[no verificable sin BD viva]**

**Las tres herramientas de disparo tienen tres niveles de feedback distintos** — esto explica la desconfianza de Gerardo:

| Herramienta | Disparo | Feedback en error | Persistencia |
|---|---|---|---|
| **Pipeline** (`procesamiento/fabrica`) | inserta en `pipeline_commands` (guard anti-duplicado, 409 si hay pendiente/ejecutando) | toast rojo | **polling cada 5s** que actualiza estado/resultado/duración. El mejor. |
| **Scraping** (`scraping/comandos`) | inserta en `scraping_commands` | `alert()` efímero solo si el POST falla | recarga historial al click. Sin toast persistente — disparo semi-a-ciegas. |
| **Emergentes** (`PerfilArgentinoAdmin.tsx:111`) | PATCH `/api/emergentes-pendientes` → `aprobar_emergente_con_triggers` | **`console.error` — silencio total en UI** | ninguna. La fila queda, el spinner desaparece, el usuario no sabe si funcionó. El peor. |

→ La desconfianza tiene raíz en código: acciones que fallan en silencio (emergentes) o sin rastro persistente (scraping). Donde hay buen feedback (pipeline) es por polling explícito, no por patrón general.

### 5.2.3 Seguridad y acceso

**Autenticación.** Supabase Auth vía `middleware.ts` → `lib/supabase/middleware.ts` (`updateSession`). El matcher cubre todo salvo estáticos, `/skills` y `/data`; **incluye `/api/*`**. Gating por rol en `user_metadata.role`: `/admin/*` exige `admin`/`super_admin` (`:80-88`), `/dashboard/*` exige pago/trial (`:91-117`), `/oficina-empleo/*` exige `oficina_empleo`/`admin`/`super_admin`/`visit_vip` (`:120-128`), `/vip/*` (`:130-139`). Un usuario sin login en una **página** no pública es redirigido a `/login` (`:73`).

**El hueco real: las API routes están eximidas del middleware.** `lib/supabase/middleware.ts:70-73` excluye explícitamente `/api/*` del redirect con el comentario *"Rutas API manejan su propia autenticación (por header)"*. El contrato es: cada route se auto-protege. **OE-11 lo rompe**: los endpoints de datos personales tienen su guard comentado con `// TODO: OE-11` y quedan callables por HTTP directo sin auth:
- `/api/personas` (GET/POST) — nombre, DNI, edad, teléfono, email, ubicación.
- `/api/casos` (GET/POST) y `/api/casos/[id]` (PATCH) — persona_nombre, persona_dni, estado, objetivo.
- `/api/perfiles` (GET/POST), `/api/perfiles/[id]/skills`, `/api/perfiles/cursos-gap`, `/api/cursos-formacion/*`, `/api/laboratorio/brecha-formacion`.

~10 endpoints con `// TODO: OE-11`; los de mutación (POST/PATCH) son los más graves (permiten crear/modificar personas y casos sin auth). **Severidad afinada:** la *página* `/oficina-empleo/*` está cerrada por el middleware (el stub de `layout.tsx:16` es redundante), pero la *API de datos* no. Quien conozca la URL del endpoint (o lea el bundle JS) puede leer/escribir PII de buscadores de empleo por `curl`. **Crítico.**

**Otros vectores:**
- **Backdoor de dev.** `lib/supabase/middleware.ts:5-31`: `DEV_MOCK_USER` (admin/enterprise hardcodeado) activable por `process.env.DEV_MOCK_AUTH === "true"`. Hoy `DEV_BYPASS = false`, pero si esa env var se setea en el deploy, **todos pasan como admin**. El comentario `:18` admite que "Vercel Edge Runtime no recibe env vars del dashboard en deploys CLI" — frágil. **[estado en Vercel no verificable sin acceso al deploy]**
- **Rol en `user_metadata`.** Todo el gating lee `user.user_metadata?.role`. En Supabase `user_metadata` es **escribible por el propio usuario** (`auth.updateUser({data})`), a diferencia de `app_metadata`. Candidato a escalación de privilegios: un usuario logueado podría auto-asignarse `role: admin`. A verificar contra la config real de Supabase. **[no verificable sin BD viva]**
- **Contraseña hardcodeada.** Búsqueda en `app/` → **no encontrada** en el dashboard. Service_role solo en API routes (servidor), nunca en código cliente (`'use client'`). La contraseña que Gerardo recuerda como "baja urgencia" no está en el dashboard — probablemente en un script fuera de este árbol. A confirmar dónde.
- **RLS.** En el repo solo `audit_log` y `perfiles_trabajadores` tienen `CREATE POLICY` (`docs/sql/`). **`personas`, `casos`, `perfiles`, `perfil_skills`, `ofertas_dashboard`, `issues` no tienen RLS versionada.** Si además están sin RLS en Supabase, la exposición de los endpoints OE-11 es total (sin segunda capa). **[existencia de RLS en Supabase no verificable sin BD viva]**

### 5.2.4 Los consumidores faltantes y D-15

La UI es, en buena medida, **el consumidor faltante** de las cadenas muertas detectadas en los seis specs anteriores. Verificación ítem por ítem:

| Consumidor faltante (origen) | ¿En la UI? | Evidencia |
|---|---|---|
| Configurabilidad de validadores — reglas/severidades/bloqueantes (S1.B.6 D-07) | **Parcial** | `app/admin/procesamiento/reglas/` edita `matching_rules_business`; **no hay UI para `nlp_validation_rules` ni severidades/bloqueantes**. |
| Marcas de sector sin consumidor, ~18.500 (S1.B.6 D-06) | **Nada** | `PuestoPanel.tsx:88` muestra el sector colapsado; ninguna vista de diagnóstico ni de las marcas. |
| Trazabilidad por oferta a través del pipeline (S1.B.2) | **Nada** | `/api/oferta/[id]/audit-history` existe (`:29-47`) pero **ninguna página lo consume**. Sin vista scraping→NLP→gate→matching→validación. |
| Estado del sync a Supabase (S1.B.1) | **Completo** | `app/admin/procesamiento/page.tsx:128-133` muestra `en_supabase`, `pendientes`, `ultimo_run`. El único consumidor cerrado de la lista. |
| Re-encolado con corrección humana (S1.B.6 D-08) | **Parcial** | `fabrica/` tiene "Reprocesar errores" (`reprocess_errors`); **no hay en `/admin/validacion/` un botón para devolver la oferta corregida a la cola** — el hueco exacto de la visión human-in-the-loop. |
| Panel de emergentes (S1.B.4 D-05) | **Cableado** | `PerfilArgentinoAdmin.tsx:209-312` muestra pendientes/aprobadas y aprueba/rechaza; la cadena llega a `aprobar_emergente_con_triggers` (cuyos buffers downstream son los dead-ends ya relevados en S1.B.4). |

**Instancias de D-15 en la UI** ("construido y no conectado / a medias / abandonado"):
- **Datos para el pedido nº1 de Cyn ya existen y no se muestran** (`validacion_correcciones`, `audit-history`, `estado_revision`): D-15 puro en la herramienta más usada del sistema.
- **`empresas/*` y `mi-futuro-laboral/*` enteros con `MOCK_*`**: `empresas/pool`, `empresas/candidatos/comparar`, `empresas/puestos/nuevo`, `mi-futuro-laboral/brecha`, `mi-futuro-laboral/reporte` (fallback a `'MOCK_TOKEN_001'`). Páginas-fachada sin backend.
- **`/api/oferta/[id]/audit-history`**: endpoint definido que ningún componente llama.
- **config-editor soporta NLP configs que ninguna UI edita** (`nlp_inference_rules`, `nlp_titulo_limpieza` en `VALID_CONFIGS`).
- **~30+ páginas huérfanas** sin link de navegación (5.2.1).

**Variante nueva del patrón en este spec:** en los componentes de procesamiento, D-15 era "construido y no encendido"; en la UI aparece como **"el dato se produce y se guarda, pero no hay pantalla que lo muestre"** — el consumidor final (la UI) es el eslabón que falta para cerrar las cadenas muertas de todo el paraguas. La UI no es una cadena muerta más: es *la salida* de las otras.

**Cabos sueltos del paraguas iluminados por la UI:**
- El `audit-history` por oferta (producido, no consumido) conecta el pedido de trazabilidad de Gerardo (S1.B.2) con el pedido de historial de Cyn (este spec): **son el mismo consumidor faltante visto desde dos roles**.
- La cadena de emergentes (S1.B.4) tiene UI completa de entrada/aprobación pero termina en los mismos buffers downstream sin consumidor — la UI no es el problema ahí; el problema es aguas abajo.
- El sync (S1.B.1) es el único eslabón con consumidor de estado cerrado en toda la lista — la excepción que confirma la regla.

### 5.2.5 Hipótesis refinadas

1. **Confirmada.** ~20-30 de 118 páginas con uso real; el resto repartido entre módulo OE (local), productos mockeados (`empresas`/`mi-futuro-laboral`), experimentos (`/admin/laboratorio`) y restos (`checkout`/`cuenta`). La fábrica real son ~32 páginas bajo `/admin/`.
2. **Confirmada con matiz.** La frontera fábrica/local no está delimitada en código: el cruce existe (OE lee `ofertas_dashboard`, las API puente leen ambos mundos) pero es asimétrico (admin no toca tablas de OE) y solo de lectura desde el local. No hay barrera de datos, solo convención de carpetas + gating por rol en middleware.
3. **Confirmada.** La desconfianza de Gerardo tiene causas identificables en código: feedback ausente (emergentes: `console.error` silencioso) o no persistente (scraping: `alert()` efímero). Donde el feedback es bueno (pipeline) es por polling explícito puntual, no por un patrón de diseño del dashboard.
4. **Refutada en su forma, confirmada en su raíz.** El "bug del guardado" no es un race-condition localizable en el formulario: el save está awaiteado y la navegación solo ocurre en éxito. Lo localizable es el **auto-avance intencional** (`page.tsx:218-220`) sin opción de quedarse ni undo — es decisión de diseño, no defecto de implementación.

---

## 5.3 Deuda observada

Registro de problemas detectados durante el relevamiento de la UI, **sin priorización ni propietario asignado en esta etapa**. La priorización y el diseño de reparaciones se harán en S1.C — Master de reparación, ahora que los 7 specs están cerrados. La UI es el componente donde la interconexión es más literal: buena parte de su deuda consiste en NO mostrar lo que los otros seis componentes ya producen.

Las deudas están organizadas en categorías para legibilidad, sin orden de prioridad entre ellas.

### Categoría A — Cartografía y frontera

#### D-01 — ~32 de 118 páginas son fábrica real; ~90 en mantenimiento pasivo, mock o abandono
Inventario verificado: 40 bajo `/admin/` (8 de laboratorio experimental → núcleo fábrica ≈ 32), 27 del local OE, 31 de productos futuros (`empresas/*` y `mi-futuro-laboral/*` enteros con `MOCK_*` hardcodeado — fachadas sin backend), 6 de comercio congeladas desde febrero, 14 públicas/auth. ~30+ rutas huérfanas sin link en el menú (se llega solo por URL directa), incluidas 7 de `/admin/procesamiento/` y las 8 de laboratorio.
**Componentes involucrados**: UI, planificación de producto.
**Por qué no se prioriza acá**: decidir qué se retira, qué se marca como mock y qué se mantiene requiere el plan comercial (los locales) y el diseño de la fábrica (S1.C).

#### D-02 — Frontera fábrica/local solo por convención de carpetas
OE lee `ofertas_dashboard` (tabla de la fábrica) directo desde páginas cliente; las API puente (matching-offers, training-*, occupations/*) leen ambos mundos sin aislamiento. Admin no toca tablas de OE (el cruce es asimétrico y acotado), pero no hay barrera de datos: la separación que la metáfora fábrica/locales exige no existe en el código.
**Componentes involucrados**: UI, BD, arquitectura.
**Por qué no se prioriza acá**: la capa de acceso de los locales se diseña con la separación arquitectónica completa (S1.C).

### Categoría B — Herramientas de validación (Cyn)

#### D-03 — Auto-avance sin escape al guardar
Verificado contra el código (corrigiendo un diagnóstico previo): el save está awaiteado y la navegación solo ocurre en éxito — no es race condition ni pérdida silenciosa por BD. El problema es el auto-avance intencional (`// Auto-navigate to next`): tras guardar, salta a la siguiente oferta sin opción de quedarse, sin confirmación y sin undo. Cyn pierde el lugar y no puede revisar lo que acaba de marcar. La reparación es de diseño UX, no de bug.
**Componentes involucrados**: UI.
**Por qué no se prioriza acá**: se repara junto con el rediseño del flujo de validación (D-04, D-05) en S1.C.

#### D-04 — La corrección se guarda en dos lados y no se muestra en ninguno
`saveValidacion` escribe `validacion_correcciones` (JSONB en `ofertas_dashboard`) y `createIssue` inserta en `issues` — pero los paneles de la oferta leen solo los campos base y no renderizan ni las correcciones ni los issues. El endpoint `/api/oferta/{id}/audit-history` existe y se consulta, pero su resultado no se pinta. Es la causa exacta de la queja de Cyn ("la oferta se ve igual").
**Componentes involucrados**: UI, loop de aprendizaje (S1.B.3 D-04).
**Por qué no se prioriza acá**: es parte del cierre del loop human-in-the-loop (S1.C).

#### D-05 — El historial y los estados que Cyn pide ya tienen los datos guardados
`validacion_correcciones`, `audit-history`, `estado_revision` (SPEC W): todo se persiste, nada se visualiza. El pedido número uno de Cyn está a un componente de distancia de datos que ya existen. Instancia pura del patrón D-15 en su variante UI.
**Componentes involucrados**: UI.
**Por qué no se prioriza acá**: mismo paquete que D-04.

#### D-06 — Filtros por igualdad exacta sobre datos posiblemente sucios
El filtro de sector usa `eq('clae_descripcion_seccion', value)` — el código es correcto; la imprecisión que Cyn reporta apunta a datos sucios en la columna o a opciones de filtro desincronizadas. No verificable sin BD viva.
**Componentes involucrados**: UI, BD, NLP (origen del dato de sector).
**Por qué no se prioriza acá**: depende del rediseño del campo sector (S1.B.5 D-04) y de verificación con conexión viva.

### Categoría C — Feedback de acciones

#### D-07 — Tres niveles de feedback según herramienta; dos fallan
Graduación verificada: **pipeline** bien (toast + polling cada 5s, estado/resultado/duración visibles — el único patrón sano); **scraping** a medias (alert() efímero solo si el POST falla, sin rastro persistente — "disparo a ciegas" parcial); **emergentes** en silencio total (si el PATCH falla, solo `console.error`; y al aprobar dispara `aprobar_emergente_con_triggers` — la cadena a buffers muertos de S1.B.4 — sin confirmación visible). La desconfianza de Gerardo hacia la UI tiene raíz verificada en código.
**Componentes involucrados**: UI, pipeline, skills.
**Por qué no se prioriza acá**: el patrón de feedback se uniformiza en el rediseño de la fábrica (S1.C); el del pipeline es el piso de referencia.

### Categoría D — Seguridad

#### D-08 — API sin guard con PII expuesta
El hueco no son las páginas (el middleware redirige al anónimo a /login): es la API. `lib/supabase/middleware.ts:70-73` exime `/api/*` del middleware, y los ~10 endpoints de OE-11 tienen el guard comentado (`// TODO: OE-11`). Resultado: PII de buscadores de empleo (DNI, nombre, teléfono, email) leíble y escribible por curl sin auth. Agravantes: sin RLS versionada para personas/casos/perfiles, backdoor `DEV_MOCK_AUTH`, rol en `user_metadata` (escribible por el propio usuario → posible escalación). Tres ítems quedaron no verificables sin BD/deploy vivos (incluida la confirmación contra el deploy público).
**Componentes involucrados**: UI, módulo OE, Supabase.
**Decisión de Gerardo (2026-06-11)**: NO se trata como excepción al protocolo — converge en S1.C como el resto de la deuda. Prioridad declarada: la eficiencia de la máquina primero. Decisión consciente, registrada para que S1.C la retome con la verificación pendiente contra el deploy vivo.

### Categoría E — Consumidores faltantes

#### D-09 — La tabla de consumidores faltantes: 1 de 6 cerrado
Estado verificado de lo que los otros specs detectaron que la UI debería exponer: estado del sync **completo** (el único); validadores configurables **parcial** (matching sí, NLP no); marcas de sector (~18.500) **nada**; trazabilidad por oferta **nada** (audit-history existe, nadie lo consume); re-encolado humano **parcial** (en fábrica, no en validación); panel de emergentes **cableado a buffers muertos**.
**Componentes involucrados**: UI + los seis componentes de origen.
**Por qué no se prioriza acá**: esta tabla ES el insumo central de S1.C — el plan de cierre de las cadenas muertas del relevamiento entero.

#### D-10 — Trazabilidad (Gerardo) e historial (Cyn) son el mismo consumidor faltante
El pedido número uno de cada uno de los dos usuarios reales del sistema converge en la misma pieza: el audit-history por oferta, visto desde dos roles. Una pieza cierra los dos pedidos.
**Componentes involucrados**: UI, pipeline, validación.
**Por qué no se prioriza acá**: convergencia mayor para el diseño de S1.C; se registra para que no se diseñe dos veces.

### Categoría F — Patrón sistémico

#### D-11 — Patrón "construido una vez y abandonado": séptima aparición, variante UI
En la UI el patrón toma la forma: **"el dato se produce y se guarda, pero no hay pantalla que lo muestre"** (correcciones, historial, estados, marcas). Con el paraguas completo, el catálogo de variantes del patrón queda cerrado: abandonado tras uso (Scraping), nunca encendido (Skills), declarado completado sin estarlo (M-13), documentado sin existir (launch_nlp_batch), y producido sin pantalla (UI). La UI no es una cadena muerta más: **es la salida de las cadenas muertas de los otros seis specs** — el lugar donde casi toda la deuda transversal se volvería visible y operable.
**Componentes involucrados**: todos. Transversal.
**Por qué no se prioriza acá**: con 7 de 7 componentes confirmando el patrón, es EL tema de proceso de S1.C.

---

## 5.4 Principios de diseño objetivo

Principios generales de cómo debería comportarse la UI cuando esté sana. **No es diseño detallado** — eso surge del master S1.C. Estos principios son el norte conceptual.

### Principio 1 — La fábrica y los locales se separan por arquitectura, no por convención
Frontera de datos explícita: los locales consumen por capa de acceso definida, no leyendo tablas de la fábrica desde el cliente. La metáfora de Gerardo (la fábrica concentra la fabricación; los locales venden) se cumple en el código, no solo en las carpetas.

### Principio 2 — Toda acción da feedback persistente
Éxito, fallo y progreso visibles en el momento y consultables después. El patrón del pipeline (toast + polling + historial) es el piso para todas las herramientas, no la excepción. Una acción que falla en silencio destruye la confianza del operador en toda la herramienta.

### Principio 3 — El validador humano controla su ritmo
Sin auto-avance forzado: quedarse, revisar y deshacer son derechos de quien valida. El sistema optimiza el throughput de la validación sin quitarle al humano el control de su propio trabajo.

### Principio 4 — Lo que se guarda se muestra
Si el dato existe (correcciones, historial, estados, marcas), tiene pantalla. Es el inverso exacto de la variante UI del patrón D-15: producir sin mostrar es construir cadenas muertas con interfaz.

### Principio 5 — Una sola vista de trazabilidad para todos los roles
El recorrido completo de una oferta —scraping, NLP, matching, validaciones, correcciones, sync— en un lugar que sirve igual al operador (Gerardo) y a la validadora (Cyn). Sus dos pedidos número uno son la misma pieza.

### Principio 6 — PII bajo auth y RLS, siempre
Defensa en profundidad: middleware + guard por endpoint + RLS en la base. Ningún dato personal accesible sin identidad verificada. (Registrado como principio aunque su reparación converja en S1.C por decisión explícita de Gerardo.)

### Principio 7 — Las páginas viven o se retiran
Mocks y experimentos marcados como tales o fuera del deploy. El inventario de qué se usa es observable en todo momento, no arqueología de git log.

---

> *Spec S1.B.7 — UI: capas 5.1, 5.2, 5.3 y 5.4 cerradas. **CON ESTE SPEC, EL PARAGUAS S1.B QUEDA COMPLETO: 7 de 7 componentes relevados.** Las 11 deudas observadas se vuelcan al master S1.C junto con las ~80 del resto del paraguas. D-11 cierra el catálogo de variantes del patrón transversal con su séptima aparición. Hallazgo de cierre: la UI es la salida de las cadenas muertas de los otros seis specs — la tabla de consumidores faltantes (D-09) y la convergencia trazabilidad/historial (D-10) son insumos centrales del diseño de S1.C. Próximo paso: abrir el master S1.C — Reparación.*
