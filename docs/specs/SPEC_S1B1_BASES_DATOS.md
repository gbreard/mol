# SPEC S1.B.1 — Relevamiento de Bases de Datos

> Versión 0.1 (capa 5.1 — Memoria operativa de Gerardo) · 2026-06-04
> Primer spec de la fase S1.B — Relevamiento del sistema. Releva el estado actual de las bases de datos del proyecto MOL, la deuda detectada y el diseño objetivo. Sigue la plantilla común definida en `docs/specs/MOL_master_relevamiento.md`.

---

## 5.1 Memoria operativa de Gerardo

Lo que Gerardo aporta sobre las bases de datos antes de la verificación contra el código. **Información que ningún archivo del repo registra**, capturada en la conversación del 2026-06-04. Es input crítico para la capa 5.2 (relevamiento por Claude Code), no comentario complementario.

### Mapa de las tres BDs

El sistema tiene **tres bases de datos diferenciadas, con estructuras distintas, cada una con un rol específico**. No es replicación; es especialización.

| BD | Ubicación física | Rol funcional |
|---|---|---|
| **VPS** | Hostinger (VPS KVM2) | Scraping |
| **Local** | PC de Gerardo (SQLite) | NLP y matching |
| **Supabase** | Nube (Supabase managed Postgres) | UI / dashboard |

### Flujo de datos

Los datos viajan unidireccionalmente entre las tres BDs:

```
VPS (scraping)  →  Local (NLP + matching)  →  Supabase (UI)
```

- **VPS → Local**: sincronización disparada al final de cada corrida del scraper. No es por intervalo de tiempo fijo, es por evento ("cuando termina el scraper, sincroniza").
- **Local → Supabase**: push como paso final del pipeline local. Cuando Gerardo ejecuta el pipeline completo (un comando único), la sincronización a Supabase es la última etapa.

**Sospecha activa de Gerardo (a verificar)**: hay escrituras cruzadas entre BDs que no siguen el flujo unidireccional. No está confirmado, pero su intuición es que más de un proceso escribe en Supabase, y esa es la pista que sospecha está relacionada con el costo elevado de procesamiento.

### Estado conocido de cada BD

**VPS**:
- Solo guarda lo scrapeado desde el momento del scraping en adelante. No tiene historial scrapeado anterior.
- Cantidad de tablas: desconocida por Gerardo.
- **Implicación operativa**: si se pierde la BD del VPS, se pierde todo lo que no se haya sincronizado al local.

**Local**:
- Motor: SQLite.
- Guarda histórico (estados anteriores de procesamiento, versiones del NLP, runs viejos del matching).
- No hay política de limpieza definida — el histórico se acumula.
- **El NLP es lo más lento** del pipeline local (esperable: corre Qwen2.5:7b localmente, procesamiento pesado por oferta).

**Supabase**:
- El costo a fin de mes proviene de **procesamiento** (CPU usado en queries, RPCs, funciones), **no de storage**. Este es un dato crítico.
- Tabla más grande: desconocida por Gerardo, pero sospecha que sea la intermedia ofertas × skills.
- La tabla ofertas × skills crece sin límite, posiblemente más de 1 millón de filas. Riesgo de escalamiento.

### Operación

- **Acceso al sistema**: solo Gerardo. Sergio aún no entra al sistema. Cuando entre, va a hacer falta definir coordinación, permisos y qué toca cada uno.
- **Pipeline local**: se dispara con un comando único que orquesta todo (NLP + matching + sync a Supabase).
- **Cron del VPS**: se dispara al finalizar cada scraper, no en intervalos fijos.
- **Scripts de sincronización**: existen, pero Gerardo no recuerda nombres específicos. Hay que identificarlos en el código.

### Síntomas y problemas operativos

Lo que Gerardo experimenta hoy:

**1. "Hoy no me entero" cuando algo falla.**
La sincronización no tiene observabilidad. Si falla la sincronización VPS→Local o Local→Supabase, no hay alerta, log accesible, ni señal visible. El sistema puede estar en **estado de inconsistencia silenciosa**: data procesada localmente que no llega al dashboard, sin que nadie lo note.

**2. Problemas para enchufar ofertas con skills.**
Síntoma reportado por Gerardo. No está claro si es problema de extracción de skills, de matching, de la tabla intermedia, o de la sincronización. Es síntoma a investigar, no causa identificada.

**3. Costo elevado de Supabase a fin de mes.**
La factura mensual es relevante. El consumo proviene de procesamiento (no storage). Posibles fuentes hipotéticas, a verificar:
- Operaciones RPC complejas sobre la tabla ofertas × skills.
- Reintentos silenciosos de sincronización cuando algo falla.
- Queries ineficientes en el dashboard que consultan más de lo necesario.

**4. El sistema "siempre anduvo para el orto".**
Esta frase textual de Gerardo es información estructural importante: el sistema no se degradó desde un estado mejor. Nació con problemas y nunca funcionó del todo bien. La deuda es constitucional, no producto de un cambio reciente que rompió algo.

**Implicación para el método**: el relevamiento no es arqueología (qué cambió, cuándo, por qué). Es diagnóstico estructural (cómo está armado y por qué nunca funcionó bien). El diseño objetivo (capa C) no es "volver al sistema que andaba bien" — ese sistema no existió. Es diseñar lo que debería ser.

### Hipótesis tentativa de la causa central

Articulada en la conversación del 2026-06-04, **es hipótesis, no conclusión**. La capa 5.2 (verificación de Claude Code) tiene que confirmarla, refutarla o refinarla:

> El sistema sincroniza local → Supabase como push pesado al final del pipeline. La sincronización carece de observabilidad. Supabase recibe escrituras pesadas (posiblemente RPC complejos, posiblemente desde varios lados si la sospecha de "escrituras cruzadas" se confirma) que generan consumo de procesamiento. Si la sincronización falla parcialmente o se dispara más veces de las necesarias, el costo se infla sin que nadie lo note. La tabla intermedia ofertas × skills, con más de 1 millón de filas, probablemente es protagonista de las operaciones pesadas.

### Notas para fases posteriores

Cosas que aparecieron en la conversación pero que **están fuera del alcance del spec S1.B.1** y se registran para que no se pierdan:

- **Coordinación con Sergio cuando entre al sistema**: definir permisos, qué toca cada uno, cómo se comparten credenciales. Trabajo de un spec dedicado en algún momento del paraguas S1.C o posterior.
- **Riesgo operativo de capacidad concentrada**: el conocimiento técnico y operativo está hoy en una sola persona. No es trabajo del spec de BD, pero conviene marcarlo en la planificación general como deuda de organización.

---

## 5.2 Estado actual relevado

Verificación de Claude Code contra el código del repo (solo lectura, sin conectar a las BDs reales). Confirma, refuta o refina la memoria operativa de la capa 5.1. Pasada del 2026-06-04 sobre el branch `spec/s1b1-bases-datos`.

### 5.2.1 Conexiones y motores de las tres BDs

| BD | Motor | Cómo se conecta | Archivos clave | Credenciales |
|---|---|---|---|---|
| **VPS** | **SQLite** (no Postgres) | SSH con key a `root@187.124.150.28`, corre `export_nuevas.py` remoto, trae dump por SCP, importa a SQLite local | `scripts/sync_from_vps.py`, `scripts/vps_command_poller.py` | SSH key sin password; host **hardcodeado** en el script |
| **Local** | SQLite | `sqlite3.connect()` directo | `database/bumeran_scraping.db` (**3.6 GB**); los demás `.db` de `database/` están vacíos (0 bytes) | n/a (archivo local) |
| **Supabase** | Postgres (managed) | Python `create_client` (supabase-py) + TypeScript `createClient` (supabase-js) | Py: `scripts/exports/sync_to_supabase.py` + ~40 scripts. TS: `fase3_dashboard/mol-dashboard/app/api/**` | `config/supabase_config.json` (service_role_key) · `.env.local` del dashboard (anon key) |

**Refinamiento sobre la 5.1:** el flujo unidireccional VPS→Local→Supabase se confirma como diseño, pero **VPS y Local son ambos SQLite**; solo Supabase es Postgres. La 5.1 dejaba el motor del VPS como "desconocido". El sync VPS→Local **no es BD-a-BD**: es transferencia de un archivo dump por SSH/SCP.

### 5.2.2 Inventario de tablas por BD

**Local (SQLite): 54 tablas.** Las más pesadas (filas):

| Tabla | Filas | Nota |
|---|---|---|
| `ofertas_esco_skills_detalle` | **1.569.227** | La mayor. Confirma la sospecha "ofertas × skills" de la 5.1. Origen local de `ofertas_skills` en Supabase |
| `validation_errors` | 278.565 | Inesperadamente grande para tabla de errores |
| `esco_associations` (+ backup) | 129.004 (+134.805) | El backup pesa más que la tabla viva |
| `ofertas_matching_history` | 111.357 | Histórico acumulado |
| `run_ofertas` | 99.076 | |
| `ofertas` | 79.200 | |
| `ofertas_nlp` | 69.794 | |
| `ofertas_esco_matching` | 68.241 | |

Hay **6 tablas `_backup_*` dentro del SQLite vivo** (`esco_associations_backup`, `ofertas_esco_matching_backup`, `ofertas_nlp_backup` ×2, `skills_semantico_json_backup_spec_e` con 49.297, `ofertas_matching_backup_spec_h`). **Confirma "histórico que se acumula sin política de limpieza"** de la 5.1.

**Supabase: ~62 tablas** definidas en 78 archivos SQL de `fase3_dashboard/sql/`. Solo `ofertas_dashboard` y `ofertas_skills` reciben el sync de datos procesados; el resto pertenece al dashboard / módulo OE (`casos`, `personas`, `perfiles`, `regice_*`, `catalogo_mol_*`, `issues`, etc.).

**VPS: no verificable en esta pasada** (requiere SSH al VPS). Por `export_nuevas.py` y los runners de scraping se infiere que contiene al menos `ofertas`, `metricas_scraping`, `scraping_sessions` — subconjunto de scraping.

### 5.2.3 Estado del doble dashboard

Existen **dos árboles de dashboard** en el repo, ambos llamados `mol-nextjs` en su `package.json`:

| | `dashboards/production/` | `fase3_dashboard/mol-dashboard/` |
|---|---|---|
| Último commit | 2026-01-27 (1 solo en 6 meses) | 2026-06-03 (activo) |
| Páginas (`page.tsx`) | 8 (admin/auth/login) | 118 |
| Link a Vercel | **ausente** (`.vercel/project.json` no existe) | **`mol-nextjs` (prj_vPxMX1mb)** → deploya a `mol-nextjs.vercel.app` |
| README | boilerplate de `create-next-app` | propio |
| Supabase | **misma instancia** `uywzoyhjjofsvvsrrnek` | misma instancia |

**Conclusión: `dashboards/production/` es LEGACY** — esqueleto temprano superado por `fase3_dashboard/mol-dashboard/`, no deployado. No genera tráfico salvo que alguien corra `npm run dev` localmente, en cuyo caso **consume contra la Supabase productiva** (apunta a la misma instancia). Se registra como **deuda de limpieza** en la capa 5.3.

### 5.2.4 Sincronizaciones

| Script | Origen → Destino | Qué mueve | Disparo | Manejo de errores | Reintento silencioso |
|---|---|---|---|---|---|
| `sync_from_vps.py` | VPS SQLite → Local SQLite | Ofertas nuevas (dump SCP) | Manual / evento post-scraping | `try/except` + log, sin loop de retry | No (falla visible en log) |
| `sync_to_supabase.py` | Local SQLite → Supabase | `ofertas_dashboard` (upsert batch), `ofertas_skills` (**DELETE por oferta** + upsert), 7 tablas de indicadores (wipe completo + insert), RPC `recalcular_emergentes` | **`pipeline_command_poller` (gateway admin UI)** — NO el pipeline local | `try/except` + retry ×3 con `sleep(2-3)`, logueado | **Probable**: el DELETE de skills se **traga tras 3 intentos** (warning, sigue) → inconsistencia silenciosa. El INSERT hace `raise` |
| `pipeline_command_poller.py` | Supabase `pipeline_commands` → ejecuta local + update Supabase | Lee comando pendiente, ejecuta, actualiza estado | `while True` + `sleep(interval)`, **local** | `try/except` + log | **Polling continuo 24/7** = SELECT constante a Supabase |
| `vps_command_poller.py` | Supabase `scraping_commands` → ejecuta VPS + insert/update Supabase | Lee comandos, corre scrapers, inserta comandos programados, actualiza `scraping_live_stats` | `while True` + `sleep(60)`, **en VPS** | `try/except` + log | **Polling cada 60s** = SELECT + escrituras constantes |
| `run_scraping_vps.sh` (cron VPS) | — → VPS SQLite | Corre scrapers + `export_nuevas.py` (dump) | Cron Lun/Jue | `bash >> log` | No toca Supabase |
| `run_validated_pipeline.py` | Local SQLite → Local SQLite | NLP + Gate + Matching + Validación + Excel (7 pasos) | Comando manual (el "comando único") | — | **NO sincroniza a Supabase** |

**Refinamiento crítico sobre la 5.1:** el "comando único" (`run_validated_pipeline.py`) **NO hace push a Supabase**. La 5.1 afirmaba que "la sincronización a Supabase es la última etapa del pipeline local" — **es incorrecto**. El sync a Supabase se dispara **por separado**, como comando de la admin UI (`sync_supabase` / `sync_supabase_full`) que el `pipeline_command_poller` recoge de la tabla `pipeline_commands`. El "comando único" y el sync son dos disparos distintos.

### 5.2.5 Escrituras cruzadas y RPCs

**Matriz proceso → tablas que escribe** (Supabase):

| Proceso | Tablas destino |
|---|---|
| `sync_to_supabase.py` | `ofertas_dashboard`, `ofertas_skills`, 7 tablas de indicadores, `scraping_live_stats` |
| Dashboard TS (29 rutas API, **83 escrituras**: 35 update / 25 insert / 16 delete / 7 upsert) | `issues`, `casos`, `perfiles`, `catalogo_mol_*`, `gold_set`, `audit_actions`, `config_overrides`, `validacion_humana`, `pipeline_commands` (crear) |
| `pipeline_command_poller.py` | `pipeline_commands` (update estado) |
| `vps_command_poller.py` | `scraping_commands` (insert/update), `scraping_live_stats` (upsert) |
| `sync_processing_metrics.py` / `sync_learnings.py` | `processing_metrics`, `metricas_plataforma` y afines |
| Núcleo del pipeline (`match_ofertas_v3.py`, `skills_implicit_extractor.py`) | **Ninguna — solo LEE** (RPC `get_latest_equiv_update`, equivalencias, boost de skills) |

**Sobre la sospecha de "escrituras cruzadas" de la 5.1:**
- **Como contención de datos (varios procesos peleando por la misma tabla): REFUTADA.** Cada proceso escribe su propio dominio; no hay dos escritores sobre la misma tabla de datos. En particular el **matcher y el extractor de skills NO escriben a Supabase** — solo leen equivalencias y boost (las coincidencias `.update(` del grep inicial eran `dict.update()` de Python, falsos positivos).
- **Como "múltiples escritores independientes a la misma instancia": CONFIRMADA.** Hay al menos 5 fuentes de escritura (sync + dashboard + 2 pollers + scripts de métricas), varias **corriendo en continuo**.

**RPCs definidas: 87 funciones en 57 archivos SQL.** Clasificación por costo:

| Nivel | RPCs | Por qué |
|---|---|---|
| **ALTO** | `match_skills_semantic`, `match_persona_ofertas_semantic`, `match_occupations_by_skills`, `expand_skills_semantic` (llamada ×3 desde el dashboard), `match_skills_by_embedding` | Búsqueda de similitud **pgvector** sobre embeddings; se disparan en page loads del dashboard |
| **ALTO** | `recalcular_emergentes` (**3 versiones**: `028`, `043`, `050_v3` — la v3 activa) | Recomputa emergentes sobre datos de skills; la llama el sync (`sync_to_supabase.py:2693`) **y** el dashboard |
| **MEDIO** | `reconciliar_sistemas`, `get_skills_resumen`, `buscar_ofertas_por_skill`, `get_brecha_formacion*`, `get_panorama`, `get_insights` | JOINs / agregaciones sobre tablas grandes |
| **BAJO** | `get_sidebar_counts`, `get_scraping_*`, conteos y listados | Queries simples |

**Triggers:** todos benignos (`*_updated_at` que setean timestamp + `on_auth_user_created` de auth). **Sin triggers de cascada de escritura.**
**Realtime:** **sin** `.subscribe()` / `.channel()` en el dashboard → se descartan conexiones realtime persistentes como driver de costo.
**Funciones SQL con LOOP/cursor:** ninguna → no hay procesamiento fila-por-fila dentro de Postgres.

### 5.2.6 Hipótesis refinada sobre el costo de Supabase

La hipótesis de la 5.1 ("sync pesado al final del pipeline, sin observabilidad, posibles escrituras cruzadas, tabla de 1.5M protagonista") se refina así con la evidencia:

1. **El sync NO es parte del pipeline local.** Se dispara aparte vía poller desde la UI. La 5.1 se equivocaba en ese punto. (No cambia el costo, pero corrige el modelo mental para diagnosticar.)
2. **Candidato #1 de costo — patrón N+1 de escritura en `ofertas_skills`.** El sync hace **un DELETE HTTP individual por oferta** (`sync_to_supabase.py:981`), no batch. En un sync full de ~68K ofertas son ~68K DELETEs sueltos + los upserts. La tabla de 1.5M filas **sí es protagonista**, como intuía Gerardo, pero el costo viene del **patrón de acceso**, no del tamaño en sí.
3. **Candidato #2 — RPCs pgvector y `recalcular_emergentes`.** `match_*_semantic`, `expand_skills_semantic` y `match_occupations_by_skills` escanean embeddings y se ejecutan en page loads del dashboard; `recalcular_emergentes` recomputa sobre skills y la disparan tanto el sync como el dashboard. Costo de CPU recurrente y poco visible.
4. **Candidato #3 — piso continuo de polling.** Dos pollers consultan Supabase en loop (cada 60s en VPS, cada `interval` en local) → consumo de procesamiento 24/7 aunque nadie use el dashboard.
5. **Descartados como drivers:** triggers de cascada (no hay), realtime (no hay), contención de escrituras cruzadas (refutada).

**No verificable en esta pasada** (requiere acceso al dashboard de facturación de Supabase y a métricas de uso reales): la atribución cuantitativa del costo a cada candidato; el volumen real de page-loads que disparan RPC pgvector; con qué frecuencia se corre `sync_supabase_full` vs incremental.

---

## 5.3 Deuda observada

Registro de problemas detectados durante el relevamiento de las tres BDs, **sin priorización ni propietario asignado en esta etapa**. La priorización y el diseño de reparaciones se harán en S1.C — Master de reparación, cuando los 7 specs de relevamiento estén cerrados. Tocar la BD aisladamente para optimizarla sería peinar al muerto: el comportamiento de la BD refleja decisiones del pipeline, del matcher y del dashboard, y la solución correcta no se puede pensar sin ese cuadro.

### D-01 — Patrón N+1 en sync de skills
Cada sync full ejecuta ~68K DELETEs individuales sobre `ofertas_skills` (uno por oferta) antes de re-insertar. Es probable candidato fuerte al costo elevado de Supabase.
**Componentes involucrados**: pipeline de matching (decide cómo armar el sync), arquitectura de la tabla ofertas × skills (el modelo de datos que obliga a este patrón), dashboard (consume los datos sincronizados).
**Por qué no se prioriza acá**: tocar el sync sin entender por qué el pipeline lo diseñó así puede romper el flujo de matching.

### D-02 — RPCs pgvector en page loads del dashboard
Cada apertura de página con búsqueda semántica o uso de `recalcular_emergentes` dispara RPCs costosas sobre la tabla grande de embeddings.
**Componentes involucrados**: dashboard (decide cuándo invocar), arquitectura de embeddings, modelo de Skills.
**Por qué no se prioriza acá**: requiere relevar dashboard y Skills antes para entender si la solución está en cache, en precálculo, en cambio de modelo o en cambio de UI.

### D-03 — Pollers 24/7 contra Supabase
Dos pollers (`vps_command_poller.py` y poller de admin) corren continuamente. Aunque cada query individual sea barata, el piso continuo durante 30 días suma.
**Componentes involucrados**: pipeline operativo (orquestación), arquitectura de comunicación entre VPS y local.
**Por qué no se prioriza acá**: requiere relevar pipeline operativo para entender qué eventos podrían reemplazar el polling.

### D-04 — Falta total de observabilidad en sincronizaciones
Si falla un sync, no hay alerta, log accesible ni señal visible. Gerardo se entera tarde o no se entera. El sistema puede estar en estado de inconsistencia silenciosa.
**Componentes involucrados**: todos. Es deuda transversal.
**Por qué no se prioriza acá**: anotada como crítica, pero la solución (qué herramienta usar, qué métricas, dónde mostrarlas) requiere conocer todos los componentes que necesitan observabilidad.

### D-05 — Histórico que se acumula sin política
6 tablas `_backup_*` dentro del SQLite vivo (un backup pesa más que su tabla viva). ~11 archivos `.db` vacíos en `database/`. Carpeta `backups/` con dumps históricos.
**Componentes involucrados**: políticas operativas del proyecto, decisiones de retención.
**Por qué no se prioriza acá**: requiere política de retención general, no solo limpieza puntual.

### D-06 — `validation_errors` con 278K filas en local
Tamaño desproporcionado para una tabla de errores. Causa desconocida.
**Componentes involucrados**: NLP (probablemente origen de los errores), matcher.
**Por qué no se prioriza acá**: requiere relevar NLP y matcher para entender qué genera estos errores y si son errores reales o ruido.

### D-07 — `recalcular_emergentes` con 3 versiones SQL coexistiendo
Tres versiones de la misma función (028, 043, 050_v3) en `fase3_dashboard/sql/`.
**Componentes involucrados**: arquitectura de schema de Supabase, módulo OE.
**Por qué no se prioriza acá**: requiere relevar módulo OE para saber cuál versión está activa y si las otras dos son código muerto o respaldos.

### D-08 — Dashboard legacy `dashboards/production/`
No deployado pero apunta a la misma Supabase productiva. Riesgo bajo (consume solo si alguien levanta `npm run dev` local), pero deuda de limpieza.
**Componentes involucrados**: dashboard, gestión de configuraciones de entorno.
**Por qué no se prioriza acá**: deuda menor, puede atacarse en cualquier momento como cleanup.

### D-09 — Credenciales hardcodeadas
SSH key del VPS en `scripts/sync_from_vps.py` (host `root@187.124.150.28`), `service_role_key` de Supabase en `config/supabase_config.json`. Ya conocido como incidente S-01.
**Componentes involucrados**: gestión de credenciales del proyecto, todos los scripts que consumen.
**Por qué no se prioriza acá**: requiere decisión sobre infraestructura de secretos (variables de entorno, gestor de secretos, qué herramienta).

### D-10 — Dos directorios de migraciones SQL
`database/migrations/` (18 archivos, congelado desde feb 2026, archivo) y `migrations/` (12 archivos, vivo). Ya documentado en `exports/cyn_backlog/verificacion_arboles_sql_2026-06-03.md`.
**Componentes involucrados**: arquitectura de schema, scripts que leen archivos puntuales de uno y otro.
**Por qué no se prioriza acá**: requiere consolidación que toca múltiples scripts vivos.

---

## 5.4 Principios de diseño objetivo

Principios generales de cómo debería comportarse el sistema de BDs cuando esté sano. **No es diseño detallado** — eso surge del master S1.C con el cuadro completo de los 7 componentes. Estos principios son el norte conceptual hacia el cual diseñar las reparaciones cuando llegue su momento.

### Principio 1 — Observabilidad de extremo a extremo
Cada sincronización, cada escritura masiva, cada job programado debería emitir señal verificable: éxito, fracaso, métricas básicas. El sistema sano es uno donde "no me entero" no debería ser posible.

### Principio 2 — Costo predecible y mensurable
El consumo mensual de Supabase debería ser predecible mes a mes, con desglose accesible (qué proceso consume cuánto). Hoy la factura llega como sorpresa; debería ser señal anticipada.

### Principio 3 — Separación clara de responsabilidades
Cada BD con un rol definido (VPS = scraping, Local = procesamiento, Supabase = UI) y un único proceso de escritura por dominio. Las "escrituras múltiples a la misma instancia desde distintos componentes" deberían ser explícitas y justificadas, no implícitas y acumuladas.

### Principio 4 — Crecimiento controlado
Las tablas que crecen sin límite (ofertas × skills, validation_errors, backups) deberían tener política de archivado, retención o limpieza. Crecimiento perpetuo no es aceptable para un sistema sano.

### Principio 5 — Eventos sobre polling cuando sea posible
Los pollers 24/7 son patrón de "no encontré mejor opción"; el sistema sano usa eventos o webhooks donde sea factible, reservando polling para casos justificados.

### Principio 6 — Credenciales fuera del código
Variables de entorno, secretos gestionados, rotación posible. Ninguna credencial productiva en archivos versionados.

---

> *Spec S1.B.1 — Bases de Datos: capas 5.1, 5.2, 5.3 y 5.4 cerradas. Las 10 deudas observadas se vuelcan al master S1.C cuando esté listo. Los 6 principios son input del diseño objetivo del sistema sano.*
