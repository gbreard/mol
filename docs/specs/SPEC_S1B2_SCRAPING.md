# SPEC S1.B.2 — Relevamiento de Scraping

> Versión 0.1 (capa 5.1 — Memoria operativa de Gerardo) · 2026-06-05
> Segundo spec de la fase S1.B — Relevamiento del sistema. Releva el estado actual del scraping del proyecto MOL, la deuda observada y los principios de diseño objetivo. Sigue la plantilla común definida en `docs/specs/MOL_master_relevamiento.md` v0.2.

---

## 5.1 Memoria operativa de Gerardo

Lo que Gerardo aporta sobre el scraping antes de la verificación contra el código. Información que ningún archivo del repo registra, capturada en la conversación del 2026-06-05.

### Mapa de portales

El sistema scrapea actualmente **6 portales de empleo**. El más antiguo es **Bumeran**.

**Nombres específicos de los 4 portales restantes**: a relevar por Claude Code en capa 5.2.

**Crecimiento planeado**: hay en agenda **agregar más de 10 portales nuevos**. Esto importa para el diseño objetivo (capa 5.4): cualquier arquitectura sana debe escalar a ~16 portales, no quedarse en 6.

### Dónde corren los scrapers

**Mezcla de ubicaciones**: no todos los scrapers corren en el mismo lugar. Configuración conocida:
- **Bumeran**: corre en VPS.
- **Indeed**: arrancó en VPS, pero **Indeed filtra la IP del VPS**, así que se migró a **local**. Es un pato rengo operativo: la arquitectura "uniforme VPS-first" se rompió por restricción del portal, sin que esto esté documentado como decisión consciente.
- **Otros 4**: distribución a relevar por Claude Code.

Frecuencia de corrida y orquestación (paralelo vs secuencial): a relevar por Claude Code.

### Cómo se scrapea — el dato más importante de este spec

**El scraping NO es mayoritariamente por API**. Algunos scrapers pueden serlo, pero **la mayoría usa palabras clave**: cada scraper le manda al portal una búsqueda con términos de un **diccionario de palabras clave**, y procesa lo que ese portal devuelve.

Esto tiene tres consecuencias operativas importantes:

1. **El universo de ofertas del sistema no es "todas las ofertas argentinas"**. Es **"las ofertas que aparecen cuando buscás con estas palabras concretas en estos 6 portales"**. Es una decisión arquitectónica con consecuencias enormes para todo lo que viene después.

2. **El diccionario de palabras clave nunca se actualizó** desde que se creó. El mercado laboral cambia: profesiones nuevas, terminología nueva. Hay una brecha creciente entre lo que el sistema ve y lo que realmente pasa en el mercado, y nadie sabe cuán grande es esa brecha porque nunca se midió.

3. **No hay análisis de eficiencia palabra clave → ofertas traídas**. Probablemente hay palabras que traen miles de ofertas relevantes y otras que traen 5 ofertas por mes que son ruido. Sin esa métrica, es imposible optimizar.

### Control de cobertura — solo Bumeran lo tiene

Algunos portales publican **el total de ofertas disponibles** en su catálogo. Para **Bumeran** se implementó un control de cobertura que compara ese total contra cuántas ofertas el scraper efectivamente extrae. Es la única forma actual de saber si el scraper está agarrando "todo lo que hay" o solo una fracción.

**Para los otros 5 portales no se hizo este control**, aunque técnicamente sería posible donde los portales publiquen ese dato. Gerardo identifica esto explícitamente como deuda: **hay que homogeneizar el control de cobertura entre todos los scrapers**.

### Calidad y observabilidad del scraping

**No hay indicador de calidad del scraper.** El sistema sabe si el scraper corrió o no, pero no si lo que trajo es bueno.

**La causa más frecuente de scraping degradado son los cambios de HTML en los portales**. Cuando un portal cambia su estructura HTML, el scraper sigue corriendo pero trae datos malos o vacíos en silencio. El sistema no detecta el cambio. Gerardo lo dice textualmente: "muchas veces es lo que frena el scraping".

**Cuándo se entera Gerardo de un scraper roto**:
- A veces durante el procesamiento (algo más abajo en el pipeline rompe con el dato sucio y eso lanza el error).
- Otras veces **pasa silenciosamente** y no se descubre nunca, o se descubre tarde.

No hay garantía de que un scraper roto sea detectado en ventana razonable.

### UI de scraping

**Existe una sección especial de scraping en la UI**. Gerardo señala explícitamente que **Claude Code debe relevar esta sección en la capa 5.2** porque tiene información que vale la pena mapear: estado por scraper, métricas, configuración, lo que sea que esté implementado ahí.

**Funcionalidad de la UI conocida**:
- Tiene un botón para disparar scrapers manualmente. Pero **Gerardo no lo usa porque no le tiene confianza**. La herramienta existe pero está degradada.
- Tiene un botón para probar un scraper aislado, pero **no permite el nivel de precisión que Gerardo querría**: idealmente debería poder seguir el proceso completo (scraping → NLP → matching → dashboard) para un conjunto de ofertas o una sola. Hoy esa trazabilidad por oferta no existe.

### Campos extraídos

Lista exhaustiva de campos por portal: a relevar por Claude Code.

**Lo que sí se sabe**: **casi ningún portal trae salarios**. Esto significa que cualquier análisis del mercado laboral basado en salarios arranca cojo desde el scraping, no es problema del NLP ni del matcher. Cobertura baja por origen.

### Detección de duplicados y republicaciones

**Republicación dentro del mismo portal** (una empresa vuelve a publicar la misma oferta a los días): existe sistema implementado, **pero Gerardo desconfía del resultado**. No sabe si funciona bien. Mismo patrón que el botón de la UI: la funcionalidad está pero la confianza no.

**Republicación entre portales** (misma oferta en Bumeran y en otro portal): Gerardo no recuerda si existe control. Probablemente no, o exista parcialmente, o exista pero nadie lo usa. A confirmar en capa 5.2.

### Portales que andan bien vs portales que andan mal

**Bumeran es estable**. Lleva años funcionando, es el más antiguo, y Gerardo confía en él.

**Sobre los otros 5**: Gerardo no tiene información clara. Podría ser que ninguno tenga problemas conocidos, o que algunos tengan problemas que nadie está mirando porque no hay observabilidad. **El silencio aquí es ambiguo**.

Esto sugiere para la capa 5.2: cuando Claude Code releve los scrapers, conviene que **mire qué tiene Bumeran que los otros no** (manejo de errores, estructura, frecuencia de fallos en commits, edad de la última modificación). Bumeran puede ser el modelo a seguir, o puede que sea estable solo porque nadie lo tocó.

### Documentación interna

**No existe documentación interna del scraping**. Cómo agregar un portal nuevo, cómo arreglar uno cuando rompe, cómo probarlo localmente — todo es conocimiento que vive en la cabeza de Gerardo o que se pierde. Esto es deuda crítica especialmente considerando los 10+ portales nuevos en agenda.

### Cron del VPS

Qué dispara el cron del VPS además de los scrapers (limpieza de logs, backups, otros jobs): a relevar por Claude Code.

### Hipótesis tentativas para la capa 5.2

Articuladas en la conversación del 2026-06-05, **son hipótesis, no conclusiones**. La verificación de Claude Code tiene que confirmarlas, refutarlas o refinarlas:

1. **El diccionario de palabras clave probablemente tiene huecos significativos**. Profesiones del mercado actual que no están en el diccionario y por lo tanto sus ofertas nunca llegan al sistema. La brecha es ciega desde adentro.

2. **Es probable que la eficiencia palabra clave → ofertas sea muy desigual**. Algunas palabras pueden estar trayendo el 80% del volumen y otras estar generando ruido o nada. Sin datos, no se puede saber.

3. **Algunos scrapers de los 5 no-Bumeran probablemente estén degradados** sin que nadie lo note. Cambios de HTML que pasaron sin alerta, formatos cambiados, campos que ya no se extraen bien. Difícil saber cuántos sin auditar uno por uno.

### Notas para fases posteriores

Cosas que aparecieron en la conversación pero que **están fuera del alcance del spec S1.B.2** y se registran para que no se pierdan:

- **Trazabilidad por oferta a través del pipeline**: Gerardo querría poder seguir desde la UI todo el proceso (scraping → NLP → matching → dashboard) para una oferta o un conjunto. Es un principio de diseño que va a aparecer en la capa 5.4 pero también es input para el spec de UI (S1.B.7).

- **Crecimiento a ~16 portales**: el diseño objetivo de cualquier reparación tiene que considerar esta meta, no solo los 6 actuales.

---

## 5.2 Estado actual relevado

Verificación de Claude Code contra el código del repo (solo lectura, sin correr scrapers ni conectar a las BDs reales). Confirma, refuta o refina la memoria operativa de la capa 5.1. Pasada del 2026-06-05 sobre el branch `spec/s1b2-scraping`.

### 5.2.1 Los 6 scrapers

Los 6 portales activos viven en `01_sources/<portal>/scrapers/`, orquestados desde el VPS por `scripts/scraping/run_scraping_vps.sh`:

| Portal | Scraper principal | Ubicación | Método | Último commit | Madurez (#.py) |
|---|---|---|---|---|---|
| **Bumeran** | `bumeran_scraper.py` (vía `run_scheduler.py`) | VPS | API searchV2 + **keywords** | 2026-02-08 | **18** |
| **ZonaJobs** | `zonajobs_scraper_v2.py` | VPS | API searchV2 + **keywords** | 2026-03-15 | **15** |
| **ComputRabajo** | `computrabajo_scraper.py` | VPS | HTML/BS4 + **keywords** | 2026-03-11 | 9 |
| **CABA** | `caba_scraper.py` | VPS | HTML listado completo (**sin keywords**) | 2026-03-13 | 1 |
| **Portal Empleo** | `portalempleo_scraper.py` | VPS | HTML listado completo (**sin keywords**) | 2026-03-13 | 1 |
| **Indeed** | `indeed_scraper.py` | **VPS / local (ambiguo)** | curl_cffi + **keywords** | 2026-04-23 | 1 |

**Refinamientos sobre la 5.1:**
- **Método (refina "la mayoría usa keywords"):** 4 de 6 usan keywords (Bumeran, ZonaJobs, ComputRabajo, Indeed); **CABA y Portal Empleo paginan el listado completo sin keywords**. Para esos dos, el "universo" no depende del diccionario sino de la cobertura del portal.
- **Pato rengo de Indeed confirmado pero sin cerrar:** existe `scripts/scraping/run_indeed_local.py` (*"wrapper… para ejecución local… keyword cycling… para no quemar la IP"*), pero el cron `run_scraping_vps.sh` **todavía invoca `run_indeed_vps.py`** (línea 71). Cuál corre realmente en producción **no es verificable leyendo el repo** (requiere el crontab vivo del VPS). La UI tiene un botón `sendIndeedLocal` dedicado, lo que sugiere que el camino local es el vigente.
- **Disparidad de madurez (confirma a Gerardo "qué tiene Bumeran que los otros no"):** Bumeran (18 archivos) y ZonaJobs (15) tienen tooling propio (rate limiter, alertas, análisis de eficiencia, exploradores de API); **CABA, Portal Empleo e Indeed son scrapers de 1 solo archivo**. Cuantitativamente, en manejo de errores: `bumeran_scraper.py` tiene **21 referencias a retry**; CABA/Portal Empleo/Indeed tienen **0**. Ninguno tiene detección activa de cambio de HTML que alerte (solo guardas de vacío/None).
- **7º directorio:** `01_sources/linkedin/` existe pero es **legacy** (JobSpy, no integrado). No es un scraper extra en producción — los 6 activos coinciden con la 5.1.

### 5.2.2 Diccionario de palabras clave

- **Archivo principal:** `config/scraping/master_keywords.json` — **v3.2**, `ultima_actualizacion: 2025-10-31`, **59 categorías**, **~2050 keywords**.
- **No es único:** hay diccionarios por portal (`config/scraping/zonajobs_keyword_combos.json`, `zonajobs_popular_keywords.json`, `01_sources/computrabajo/config/search_keywords.json`, `01_sources/linkedin/config/search_keywords.json`) + historial de versiones en `config/archive/` (v3.0, v3.1, v3.2).
- **Sí se actualizó alguna vez (matiza "nunca se actualizó"):** la nota de versión dice *"EXPANSIÓN v3.1: +267 términos basados en análisis de 3.484 ofertas reales"*. Pero está **congelado desde hace ~7 meses (2025-10-31)**.
- **Métricas de eficiencia keyword→ofertas: EXISTEN pero son un one-shot.** Tabla local `keywords_performance` (2296 filas) con `ofertas_encontradas / ofertas_nuevas / ofertas_duplicadas / tiempo_ejecucion / exito / esco_occupation_uri` por keyword, **pero todas las filas son de un único día (2025-10-31) y solo de `fuente='bumeran'`**. Hay 3 herramientas (`analizar_eficiencia_keywords.py`, `analizar_keywords_faltantes.py`, `keyword_optimizer.py`). La capacidad de medir existe; el uso continuo no.

### 5.2.3 Cron, orquestación y UI de scraping

**Orquestación (cron VPS):** `run_scraping_vps.sh` corre los scrapers **secuencialmente** (Bumeran → ZonaJobs → ComputRabajo → CABA → Portal Empleo → Indeed) y al final `export_nuevas.py` para el sync a local. CLAUDE.md indica frecuencia Lun/Jue. El crontab vivo del VPS no está versionado → la frecuencia real **no es verificable en esta pasada**.

**Manejo de errores:** cada scraper usa `try/except` + logging a archivo; solo Bumeran tiene retry/backoff y circuit breaker. **No hay detección de cambio de HTML**: si un portal cambia su estructura, el scraper trae vacío/sucio en silencio (confirma a Gerardo). La degradación se descubre tarde o nunca.

**Control de cobertura (foco pedido):** `scripts/scraping/medir_cobertura_v3_2.py` es un **one-shot Bumeran-only**: compara cobertura de diccionario v3.1 vs v3.2 leyendo CSVs locales contra un total **hardcodeado** (`TOTAL_OFERTAS_BUMERAN = 12207 # Actualizar con valor real`), último commit 2026-01-15, no integrado al pipeline. Confirma a Gerardo: el control de cobertura existe solo para Bumeran y ni siquiera es automático.

**Alertas:** `01_sources/bumeran/scrapers/alert_manager.py` genera alertas por métricas + circuit breaker, pero **"actualmente solo registra en logs… preparado para envío por email"** (`email_enabled=False`). Capacidad construida, no cableada.

**UI de scraping** (`fase3_dashboard/mol-dashboard/app/admin/scraping/`): tres páginas + APIs (`scraping-commands`, `scraping-live-stats`, `scraping-schedule`).
- `page.tsx` (401 líneas): **monitoreo** — stats por portal (VPS + Supabase merge), histórico, toggles de visibilidad. Es vista de lectura.
- `comandos/page.tsx`: **gateway de comandos** — botones `lanzar_portal` / `pausar_portal` (el disparo manual que Gerardo no usa), `sendIndeedLocal` dedicado, y edición de `scraping_schedule`. Escribe en `scraping_commands`, que el `vps_command_poller.py` recoge (cadena vista en S1.B.1).
- `dinamica/page.tsx`: gráfico de dinámica.
- **No existe trazabilidad por oferta** (scraping → NLP → matching → dashboard): confirmado el gap que señaló Gerardo. El "probar scraper aislado" se reduce a `lanzar_portal` (portal entero), no a seguir una oferta por el pipeline.

### 5.2.4 Detección de duplicados y republicaciones

**Anti-rescrapeo intra-portal (por ID):** `02_consolidation/scripts/incremental_tracker.py` + `tracking/scraped_ids.json` por portal. Evita re-bajar IDs ya vistos. No es detección de republicación (mismo aviso con ID nuevo).

**Republicación intra-portal — ACTIVA (refuta la desconfianza como "no funciona"):** `database/detectar_republicaciones.py` agrupa por `titulo+empresa` con `id_oferta` distinto (primera = original, resto = republicación). **Está automatizado** — lo invocan `run_scheduler.py` y `sync_from_vps.py` — **tiene test** (`tests/scraping/test_republicaciones.py`) y **pobló datos reales**: 4.212 ofertas con `es_republicacion=1`, columnas `numero_republicacion`/`grupo_republicacion` en uso, 75.593 con `fecha_baja`. La desconfianza de Gerardo es sobre la **precisión** del criterio (titulo+empresa exacto), no sobre su existencia: el sistema corre y produce datos.

**Dedup cross-portal — EXISTE pero DORMIDO (refuta "probablemente no existe"; confirma "nadie lo usa"):** `scripts/db/deduplicate_cross_portal.py` (clase `CrossPortalDeduplicator`, umbral fuzzy 0.85, `--dry-run`), pero **ningún cron/pipeline/script lo invoca** (commit único 2026-01-15). Capacidad construida, nunca automatizada.

**Contador roto:** en las 311.696 filas de `keywords_performance`, `ofertas_duplicadas = 0` (nuevas == encontradas) → el contador de duplicadas **nunca se pobló**.

### 5.2.5 Hipótesis refinadas y patrón transversal

**Hipótesis 1 (huecos en el diccionario): no verificable cuantitativamente en esta pasada**, pero el contexto la hace plausible: diccionario congelado desde 2025-10-31, y existe `analizar_keywords_faltantes.py` (señal de que el hueco se sospechó y nunca se midió de forma continua). Medir la brecha real requiere correr análisis, fuera de alcance de solo-lectura.

**Hipótesis 2 (eficiencia keyword→ofertas muy desigual): parcialmente refutada en cuanto a capacidad, confirmada en cuanto a uso.** La infraestructura para medirla existe (`keywords_performance` + 3 scripts), pero solo se corrió **una vez, para Bumeran, hace 7 meses**. No hay medición continua ni por-portal, así que la desigualdad sigue sin cuantificarse.

**Hipótesis 3 (scrapers no-Bumeran degradados sin que nadie lo note): respaldada estructuralmente.** CABA/Portal Empleo/Indeed son single-file, sin retry, sin alertas, sin control de cobertura, sin detección de cambio de HTML. No se puede afirmar que estén rotos hoy (requiere correrlos), pero **la ausencia de observabilidad hace que un quiebre pasaría inadvertido** — exactamente el riesgo que describe Gerardo.

**Patrón transversal — "construido una vez y abandonado":** apareció de forma recurrente y conviene marcarlo para S1.C. Instancias detectadas en este relevamiento:
1. `keywords_performance` — medición única (2025-10-31), solo Bumeran.
2. `master_keywords.json` — expansión única (v3.1, oct 2025), congelado desde entonces.
3. `medir_cobertura_v3_2.py` — one-shot Bumeran-only, total hardcodeado, sin integrar.
4. `alert_manager.py` — alertas "solo a logs", email nunca habilitado.
5. `deduplicate_cross_portal.py` — construido (ene 2026), nunca invocado.
6. `ofertas_historial` — tabla de change-tracking con schema completo y **0 filas**, nunca usada.

Contraejemplos que **sí** siguen activos: `detectar_republicaciones.py` (automatizado + test + datos) e `incremental_tracker.py` (anti-rescrapeo por portal).

**No verificable en esta pasada:** frecuencia real del cron del VPS; qué runner de Indeed corre en producción (VPS vs local); si los scrapers single-file están trayendo datos correctos hoy; magnitud real de la brecha del diccionario y de la eficiencia por keyword.

---

## 5.3 Deuda observada

Registro de problemas detectados durante el relevamiento de Scraping, **sin priorización ni propietario asignado en esta etapa**. La priorización y el diseño de reparaciones se harán en S1.C — Master de reparación, cuando los 7 specs de relevamiento estén cerrados. Tocar el scraping aisladamente para optimizarlo sería peinar al muerto: el comportamiento de los scrapers refleja decisiones de orquestación del pipeline, decisiones de BD sobre cómo guardar las ofertas, y decisiones de UI sobre qué exponer.

Las deudas están organizadas en categorías para legibilidad, pero sin orden de prioridad entre ellas.

### Categoría A — Observabilidad y calidad

#### D-01 — Sin detección automática de cambios de HTML
Cuando un portal cambia su estructura HTML, los scrapers traen datos vacíos o sucios en silencio. El sistema no lo detecta hasta que algo más abajo en el pipeline rompe, o no lo detecta nunca.
**Componentes involucrados**: scraping, NLP (recibe los datos sucios después), pipeline operativo (no hay alertas).
**Por qué no se prioriza acá**: requiere decisión sobre infraestructura de alertas a nivel proyecto.

#### D-02 — Alert manager existe pero solo loguea
Hay infraestructura de alertas en el código pero no está conectada a un canal real (email, Slack, etc.).
**Componentes involucrados**: scraping, infraestructura de notificaciones del proyecto.
**Por qué no se prioriza acá**: requiere decisión sobre qué canal de alertas usar a nivel proyecto.

#### D-03 — Sin trazabilidad por oferta a través del pipeline
No se puede seguir una oferta específica desde el scraping hasta el dashboard. Gerardo lo identificó como gap importante: idealmente debería poder hacerse desde la UI.
**Componentes involucrados**: scraping, UI (S1.B.7), NLP, matching.
**Por qué no se prioriza acá**: requiere relevamiento de UI y de pipeline operativo para diseñar trazabilidad end-to-end.

### Categoría B — Disparidad entre scrapers

#### D-04 — Tres scrapers single-file sin tooling
CABA, Portal Empleo, Indeed: 1 archivo cada uno, cero retries, sin observabilidad propia. Contraste con Bumeran (18 archivos, 21 retries, rate limiter, alertas).
**Componentes involucrados**: scraping, arquitectura del proyecto (no hay framework común aplicado a todos).
**Por qué no se prioriza acá**: requiere decisión arquitectónica sobre framework común de scrapers.

#### D-05 — Pato rengo de Indeed
Existe wrapper local (`run_indeed_local.py`) explícitamente "para no quemar la IP", pero el cron del VPS sigue invocando `run_indeed_vps.py`. No es verificable sin ver el crontab vivo del VPS cuál corre realmente en producción.
**Componentes involucrados**: scraping, gestión de cron del VPS.
**Por qué no se prioriza acá**: requiere acceso al VPS para verificar y decisión sobre ubicación definitiva.

### Categoría C — Diccionario de palabras clave

#### D-06 — Diccionario sin proceso de actualización continua
Última actualización del `master_keywords.json`: 2025-10-31 (hace 7 meses). Existe la infraestructura para medir eficiencia y agregar términos, pero no hay práctica recurrente.
**Componentes involucrados**: scraping, proceso operativo del proyecto.
**Por qué no se prioriza acá**: requiere decisión sobre cadencia y responsabilidad de mantenimiento.

#### D-07 — Métricas de eficiencia keyword→ofertas existen pero abandonadas
Tabla `keywords_performance` (2.296 filas) + 3 scripts de análisis. Última corrida: una sola vez, solo Bumeran, 2025-10-31.
**Componentes involucrados**: scraping, decisiones operativas.
**Por qué no se prioriza acá**: ver D-15 (patrón sistémico). La infraestructura existe; lo que falta es la práctica.

#### D-08 — Múltiples diccionarios por portal sin sincronización clara
Diccionario global (`master_keywords.json`) + diccionarios específicos por portal (`zonajobs_keyword_combos.json`, `computrabajo/config/search_keywords.json`, etc.). No queda claro cómo se mantienen sincronizados ni qué pasa cuando se agrega un término al global.
**Componentes involucrados**: scraping, configuración del proyecto.
**Por qué no se prioriza acá**: requiere decisión sobre arquitectura de diccionarios.

### Categoría D — Cobertura y duplicados

#### D-09 — Control de cobertura solo en Bumeran, con total hardcodeado
`medir_cobertura_v3_2.py` es one-shot, Bumeran-only, y el total no se actualiza dinámicamente desde el portal.
**Componentes involucrados**: scraping, monitoreo del proyecto.
**Por qué no se prioriza acá**: requiere decisión sobre cómo extender a otros portales y cómo mantener el total actualizado.

#### D-10 — Deduplicación cross-portal implementada pero dormida
`deduplicate_cross_portal.py` existe con fuzzy matching 0.85, pero nadie lo invoca. La BD probablemente tiene la misma oferta replicada desde múltiples portales sin marcar.
**Componentes involucrados**: scraping, BD (S1.B.1), arquitectura de datos.
**Por qué no se prioriza acá**: requiere decisión sobre cuándo y cómo invocarlo, y validar que el criterio fuzzy 0.85 es correcto antes de aplicarlo masivamente.

#### D-11 — Republicación intra-portal funciona pero criterio no validado
El sistema detecta y marca republicaciones (4.212 detectadas, automatizado vía `detectar_republicaciones.py`). Gerardo desconfía de la precisión del criterio, no de si corre.
**Componentes involucrados**: scraping.
**Por qué no se prioriza acá**: requiere muestreo y validación humana del criterio, posiblemente con apoyo de Cynthia.

### Categoría E — Documentación y conocimiento

#### D-12 — Sin documentación interna del scraping
Cómo agregar un portal nuevo, cómo arreglar uno cuando rompe, cómo verificar que un scraper trae datos buenos: todo conocimiento concentrado en Gerardo. Especialmente crítico considerando los 10+ portales nuevos en agenda.
**Componentes involucrados**: documentación general del proyecto.
**Por qué no se prioriza acá**: requiere decisión sobre qué documentar y dónde, en sintonía con el resto de la documentación del proyecto.

### Categoría F — Sprawl

#### D-13 — LinkedIn legacy no integrado
`01_sources/linkedin/` con JobSpy. Existe código pero no está en producción.
**Componentes involucrados**: scraping.
**Por qué no se prioriza acá**: deuda menor de limpieza.

#### D-14 — Tabla `ofertas_historial` con 0 filas
Creada pero nunca usada.
**Componentes involucrados**: scraping, BD.
**Por qué no se prioriza acá**: ver D-15 (patrón sistémico).

### Categoría G — Patrón sistémico

#### D-15 — Patrón "construido una vez y abandonado"

**No es deuda de scraping específicamente — es síntoma del proceso de trabajo del proyecto.** En el relevamiento de Scraping se identificaron al menos seis instancias del mismo patrón:

1. `keywords_performance` — tabla con análisis de eficiencia, corrida una vez (Bumeran, octubre 2025).
2. `master_keywords` — diccionario expandido con datos en octubre 2025, no actualizado después.
3. `medir_cobertura_v3_2.py` — control de cobertura one-shot solo Bumeran.
4. `alert_manager` — existe pero solo loguea, no envía a canal real.
5. `deduplicate_cross_portal.py` — código completo de deduplicación, nadie lo invoca.
6. `ofertas_historial` — tabla creada con 0 filas.

Contraejemplos activos en el mismo componente: `detectar_republicaciones`, `incremental_tracker`.

**Por qué importa**: cada esfuerzo de mejora se hizo bien técnicamente, pero no se incorporó como práctica continua. Queda el código, queda la infraestructura, pero el uso muere. No es defecto de capacidad técnica; es ausencia de prácticas operativas que mantengan vivo lo que se construye.

**Componentes involucrados**: todos. Es transversal.

**Por qué no se prioriza acá**: esta deuda va a cruzarse en S1.C cuando los 7 specs de relevamiento estén cerrados. Es probable que se manifieste en cada componente, y la solución (si hay) es de proceso operativo del proyecto, no de ninguno de los componentes específicos.

---

## 5.4 Principios de diseño objetivo

Principios generales de cómo debería comportarse el sistema de Scraping cuando esté sano. **No es diseño detallado** — eso surge del master S1.C con el cuadro completo. Estos principios son el norte conceptual.

### Principio 1 — Detección activa de cambios estructurales
El sistema sano detecta cuándo un portal cambió su HTML antes de que los datos sucios contaminen el pipeline. No depende de que un humano lo note.

### Principio 2 — Uniformidad mínima entre scrapers
Cualquier scraper, sea cual sea el portal, debe tener mínimo: retries, manejo de errores, observabilidad básica, métrica de cobertura. La disparidad actual entre Bumeran (18 archivos con tooling) y los scrapers single-file es inaceptable para un sistema sano.

### Principio 3 — Trazabilidad por oferta a través del pipeline
Cualquier oferta debe poder seguirse desde el momento del scraping hasta su presencia en el dashboard. Tanto para debug como para validación. Es un principio que afecta también a UI, NLP y matching, no solo a scraping.

### Principio 4 — Cobertura medida en todos los portales que lo permitan
Donde el portal publica el total de ofertas disponibles, el scraper debe comparar contra ese total y reportar la diferencia. Bumeran es el modelo, no la excepción.

### Principio 5 — Diccionario con proceso continuo de mantenimiento
El diccionario de palabras clave necesita actualización periódica basada en datos. No esfuerzo puntual; práctica recurrente con cadencia definida.

### Principio 6 — Deduplicación cross-portal activa
Si el sistema tiene la capacidad técnica de deduplicar entre portales, debe usarla. Código zombi vs deduplicación real es inaceptable.

### Principio 7 — Documentación operativa mínima
Cómo agregar un portal nuevo, cómo arreglar uno roto, cómo verificar que un scraper trae datos buenos. Conocimiento que no vive solo en la cabeza de una persona.

### Principio 8 — Escalable a 16+ portales
Cualquier arquitectura propuesta tiene que escalar a la meta de crecimiento (10+ portales nuevos en agenda), no solo a los 6 actuales.

---

> *Spec S1.B.2 — Scraping: capas 5.1, 5.2, 5.3 y 5.4 cerradas. Las 15 deudas observadas se vuelcan al master S1.C cuando esté listo. Los 8 principios son input del diseño objetivo del sistema sano. La deuda D-15 (patrón sistémico) es transversal y se va a cruzar con los hallazgos de los otros 5 specs pendientes.*
