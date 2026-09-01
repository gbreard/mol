# SPEC — Scraper Indeed headed (navegador bajo xvfb, local)

**Fecha:** 2026-09-01
**Rama:** `fix/indeed-desbloqueo` (worktree `/mnt/d/OEDE/mol-indeed`)
**Estado:** BORRADOR PARA APROBACIÓN — no se escribe código hasta el OK de Gerardo.
**Decisión previa:** Opción A (scraper headed) bajo gate go/no-go. Proxy descartado. Solo local.

---

## 0. Contexto y evidencia (por qué headed)

Diagnóstico medido 2026-08-28 → 2026-09-01 (rama, read-only):

| Vía | Listado | Descripción | Veredicto |
|---|---|---|---|
| curl_cffi (cualquier versión/fingerprint, 0.14.0 y 0.16.2) | 403 "Security Check" | — | muerto |
| Navegador **headless** | "Blocked - Indeed.com" | — | Indeed detecta headless |
| Navegador **headed** (WSLg `DISPLAY=:0` **o** xvfb) | ✅ real, 7 tarjetas | — | **pasa CF y "Blocked"** |
| headed → `/viewjob?jk=` deep-link | ✅ | ❌ redirige a login | detalle exige sesión |
| headed → **click en tarjeta** (panel `vjk`) | ✅ | ✅ `#jobDescriptionText` 2243 chars | **vía válida** |
| curl_cffi + `cf_clearance`/jar completo (ff135/chrome131/chrome142) | 403 "Security Check" | — | handoff muerto (TLS-bound) |

**Conclusiones que fijan el diseño:**
1. El "Blocked - Indeed.com" de agosto **no era baneo de IP**: era detección de *headless*. Un chromium **no-headless** en la MISMA IP local entra. (Corrige la nota de memoria 2026-08-14.)
2. El bootstrap existente `bootstrap_cookies_navegador` (cosechar cookies → curl) **es un callejón sin salida**: `cf_clearance` está atado al fingerprint TLS del chromium real; ningún `impersonate` de curl_cffi lo matchea. **Se descarta esa arquitectura.**
3. La descripción **solo** se obtiene clickeando la tarjeta (panel embebido `?...&vjk=`), nunca por deep-link a `/viewjob` (que redirige a "Iniciar sesión").
4. El challenge se **re-dispara por navegación** y tarda ~20 s en limpiar; la sesión es frágil → el pacing y el corte por re-challenge son parte del núcleo, no un extra.

---

## 1. Principio arquitectónico: mismo seam, motor nuevo

El único punto de acople con el resto del pipeline es la clase **`IndeedScraper`** de
`01_sources/indeed/scrapers/indeed_scraper.py`, consumida por:
- `scripts/scraping/run_indeed_vps.py` (mapeo `mapear_oferta_para_bd` + `insertar_en_bd`)
- `scripts/scraping/run_indeed_local.py` (reusa el mapeo/insert de arriba)
- `scripts/pipeline_command_poller.py` (lanza el runner local ante `scrape_indeed`)

**Regla dura de compatibilidad:** el motor headed debe devolver **la misma lista de dicts `oferta`** con las mismas claves que hoy, para que mapeo, insert, id-scheme, dedup y sync **no cambien**.

Claves del dict `oferta` que el mapeo espera hoy (contrato a preservar):
`job_key, titulo, empresa, ubicacion, salario_listing, url, keyword_source,
descripcion, fecha_publicacion, fecha_expiracion, tipo_empleo, empresa_jsonld,
localidad_jsonld, provincia_jsonld, pais_jsonld, salario_min, salario_max,
salario_moneda, salario_periodo, scrapeado_en, portal`.

- **id:** `8_000_000_000 + int(job_key, 16) % 1_000_000_000` (sin cambios). El `job_key` es el mismo `a[data-jk]` de la tarjeta (verificado: el `vjk` del panel = `data-jk`). Continuidad de id garantizada.
- **url_oferta:** se mantiene `https://ar.indeed.com/viewjob?jk={job_key}` como URL canónica/dedup, aunque la lectura sea por panel.
- **`INSERT OR IGNORE`** por `id_oferta` → dedup intacto.

### 1.1 Forma concreta

Módulo nuevo: `01_sources/indeed/scrapers/indeed_scraper_headed.py`
Clase `IndeedScraperHeaded` con **la misma superficie pública** que `IndeedScraper`:

```
class IndeedScraperHeaded:
    def __init__(self, delay=5.0, detail_delay=4.0, fetch_details=True,
                 max_fichas=900, headless=False): ...
    def scrape_with_keywords(self, keywords, location="Argentina", fromage=14) -> list[dict]
    def scrape_with_keywords_file(self, json_path, estrategia="exhaustiva",
                                  location=..., fromage=14, max_keywords=None, offset=0) -> list[dict]
    # atributos de estado que el runner lee tras la corrida:
    #   self.detalle_bloqueado: bool     (cut por Blocked/challenge sostenido)
    #   self.preflight_ok: bool          (GO/NO-GO inicial)
    #   self.stats: dict                 (fichas, con_desc, challenges, elapsed)
```

El runner elige el motor con un flag/env (`INDEED_ENGINE=headed|curl`), default `headed` en local.
`IndeedScraper` (curl) **no se borra** todavía: queda como fallback inerte hasta que el prototipo dé GO y se estabilice.

---

## 2. Motor headed — flujo interno

**Un solo navegador, un solo `context`, reusado para toda la corrida** (continuidad de sesión = menos challenges).

```
launch chromium  headless=False  args=[--no-sandbox, --disable-blink-features=AutomationControlled]
context = new_context(locale='es-AR')            # UA nativo del chromium, no override
page = context.new_page()
```

### 2.1 PREFLIGHT (gate GO/NO-GO de la corrida)

Antes de recorrer keywords:
1. `goto` listado semilla (`?q=cajero&l=Argentina&fromage=14`), esperar tarjetas hasta ~25 s.
2. Clasificar:
   - **tarjetas presentes** → `preflight_ok=True` → GO.
   - **título contiene "Blocked"** → NO-GO duro (Indeed bloquea; probablemente detección headless o cambio de postura). Abortar, `detalle_bloqueado=True`, devolver `[]`.
   - **"Security Check" que no limpia en 25 s** → NO-GO. Abortar, devolver `[]`.
3. NO-GO ⇒ el runner **no inserta nada**, registra el motivo y respeta cooldown (no reintenta en el día).

### 2.2 Bucle de listado (por keyword, tramo de ~90)

Para cada keyword del tramo:
1. `self._wait(delay)` (pacing, ver §3).
2. `goto` `jobs?q={kw}&l=Argentina&fromage=14`, `wait_until='domcontentloaded'`.
3. Esperar tarjetas (`a[data-jk]`) con poll hasta `LISTADO_CLEAR_TIMEOUT` (§3).
4. Si aparece **"Security Check"** y no limpia → contar `challenge`; aplicar §4 (backoff / corte).
5. Si **"Blocked"** → corte duro (§4).
6. Parsear tarjetas del DOM (no HTML crudo de curl):
   - `job_key` = `a[data-jk]@data-jk`
   - `titulo` = texto del `a[data-jk]`
   - `empresa` = `[data-testid=company-name]`
   - `ubicacion` = `[data-testid=text-location]`
   - `salario_listing` = `[data-testid=attribute_snippet_testid]` (si está)
   - dedup por `job_key` en `self._seen_jks`.

### 2.3 Descripción (por ficha, vía click — NO deep-link)

Para cada tarjeta nueva (respetando `max_fichas`):
1. `self._wait(detail_delay)`.
2. **Click** en la tarjeta (`a[data-jk]`) en la misma página → carga panel embebido (`&vjk=`).
3. Esperar `#jobDescriptionText` (con fallbacks: `div.jobsearch-JobComponent-description`, `[data-testid="jobDescriptionText"]`, `div#vjs-desc`).
4. Extraer `descripcion = inner_text` (si > ~50 chars, real; si vacío/login → contar fallo, ficha sin descripción **se descarta**, no se guarda muda — misma política que hoy).
5. **JSON-LD / campos estructurados:** el panel embebido puede **no** traer el `<script type=application/ld+json>` del `/viewjob`. Estrategia:
   - intentar leer JSON-LD del DOM del panel si existe → `fecha_publicacion, tipo_empleo, salario_*` como hoy;
   - si no existe → esos campos quedan **NULL** (el schema los permite; ver §7 riesgo de fidelidad).
6. `scrapeado_en = now`, `portal='indeed'`, `url = /viewjob?jk=`.

### 2.4 Corte y retorno

- Al alcanzar `max_fichas` (≤ 900) → terminar prolijo, devolver lo completo.
- Al cortar por challenge/blocked → devolver **solo fichas con descripción** (descartar mudas y pendientes), setear `detalle_bloqueado=True`. Misma filosofía que el scraper curl actual ("no guardar mudas; con `fromage=14` se recupera en la próxima").

---

## 3. Pacing (parámetros, conservador)

| Parámetro | Valor propuesto | Racional |
|---|---|---|
| `delay` (entre keywords) | 5 s (+ jitter 0.5–1.5×) | ritmo humano, evita rate-limit de listado |
| `detail_delay` (entre clicks) | 4 s (+ jitter) | idem panel |
| `LISTADO_CLEAR_TIMEOUT` | 25 s (poll 2 s) | tiempo medido para que limpie el challenge |
| `DESC_TIMEOUT` | 8 s | aparición de `#jobDescriptionText` |
| `max_fichas` (techo diario duro) | **900** | restricción no negociable |
| tramo por corrida | **~90 keywords** | ~90 × ~7 = ~630 fichas < 900 |
| corridas por día | **1** | restricción no negociable |
| cooldown | 1 corrida/día por state-file | evita quemar la sesión |

Estimación de tiempo (para el gate): por keyword ≈ `delay` + espera-listado + `n_cards × (detail_delay + desc)`.
Con 7 cards: ≈ 5 + ~6 + 7×(4+~2) ≈ **~53 s/keyword sin challenge**. 20 kw ≈ **~18 min** (holgura vs los 25 min del gate; los re-challenges de 20 s son el margen que puede romperlo).

---

## 4. Manejo de re-challenge / "Blocked" (máquina de estados)

Contadores: `consecutive_challenges`, `fichas_hechas`.

```
navegación devuelve "Security Check" y no limpia en LISTADO_CLEAR_TIMEOUT:
    consecutive_challenges += 1
    backoff = min(BACKOFF_BASE * consecutive_challenges, BACKOFF_MAX)   # p.ej. 15s,30s,45s
    sleep(backoff); reintentar la MISMA navegación una vez
    si vuelve a fallar:
        si consecutive_challenges >= UMBRAL_CORTE (=2):
            CORTAR corrida (devolver completo, detalle_bloqueado=True)   # no insistir
navegación/panel devuelve "Blocked - Indeed.com" o redirige a login:
    CORTE DURO inmediato (no reintentar)
navegación OK:
    consecutive_challenges = 0
```

Principio: **ante duda, cortar, no insistir** (restricción de Gerardo). Perder el tramo del día es barato (`fromage=14`); quemar la sesión es caro.

---

## 5. Integración con scheduler/poller local

### 5.1 Runner

Adaptar `run_indeed_local.py` (o runner nuevo `run_indeed_headed.py` que reusa `mapear_oferta_para_bd`/`insertar_en_bd` de `run_indeed_vps.py`):
- **Tramo por offset** (no el weekly-cycling actual): leer `proximo_offset` de `data/indeed_scraping_state.json` (clave `local`), tomar 90 keywords de `master_keywords.json` estrategia `exhaustiva` (mismo orden que usa el vigía hoy), correr, y avanzar `proximo_offset += 90` (wrap al total 1072). **Reusa el state-file y el esquema actuales** (restricción).
- Instanciar `IndeedScraperHeaded`. Insertar en BD con `insertar_en_bd` (sin cambios).
- Guard de cooldown: si `ultima_corrida` < 24 h → no correr.
- Escribir stats de la corrida (fichas, con_desc, challenges, elapsed) al log y al state-file.

### 5.2 Ejecución bajo xvfb

El proceso necesita un display. El runner se invoca **envuelto en xvfb**:
```
xvfb-run -a /usr/bin/python3 scripts/scraping/run_indeed_headed.py --tramo-desde-state
```
(No depende de WSLg/escritorio logueado — verificado que xvfb pasa igual.)

### 5.3 Disparo diario

Dos caminos, se mantienen ambos:
- **Automático:** una entrada de cron **1×/día** (no cada 3 h) que corre el runner headed bajo `xvfb-run`, con guard de cooldown interno. Reemplaza el rol de disparo del vigía.
- **Manual (admin UI):** el botón `scrape_indeed` → `pipeline_commands` → `pipeline_command_poller.py`. El poller debe invocar el runner **bajo xvfb** (envolver el comando indeed con `xvfb-run -a`). El resto del poller no cambia.

### 5.4 sync a Supabase

Sin cambios: las ofertas entran a `ofertas` local igual que hoy → NLP → matching → `sync_to_supabase.py`. El pipeline no se entera.

---

## 6. Adaptación / retiro del vigía (`check_indeed_unblock.py`)

El vigía hoy **prueba con curl_cffi** (`impersonate='firefox135'`) cada 3 h. Eso **ya no mide nada real** (curl siempre da 403, aun cuando headed funciona). Restricción de Gerardo: adaptarlo o retirarlo.

**Recomendación: RETIRAR el vigía** y reemplazar su función por el **preflight headed integrado** (§2.1) dentro del runner diario:
- La pregunta "¿está desbloqueado?" hoy es binaria y se responde **abriendo el navegador**, que es justo lo que el runner ya hace en el preflight. Un probe curl separado cada 3 h es ruido.
- Se elimina la entrada de cron `0 */3 * * *` del vigía y su log.

**Alternativa (si Gerardo prefiere conservar el patrón probe-then-launch):** reescribir el probe del vigía para que abra **un** listado con chromium headed bajo xvfb (contar tarjetas) en vez de curl, y sólo entonces disparar la corrida. Más piezas móviles; mismo resultado. Se documenta pero **no** es la recomendación.

En cualquier caso: **el vigía no puede seguir midiendo con curl_cffi.**

### 6.1 Limpieza VPS (fuera de alcance de ejecución, se anota)

El cron VPS (`run_scraping_vps.sh`, Lun/Jue) todavía corre Indeed por curl y se bloquea siempre. Como Indeed pasa a **local-headed**, el paso Indeed del cron VPS debe **desactivarse** para no generar ruido/falsos "Blocked". Se anota como tarea de integración; no se toca el VPS en esta rama.

---

## 7. Dependencias (env real del scraper)

Env del scraper local = **`/usr/bin/python3`** (Python 3.10; NO miniforge). Requiere:
- `playwright` (pip) + navegador: `playwright install chromium`
- `beautifulsoup4` (ya presente) — opcional si se parsea por DOM de playwright
- **xvfb** a nivel sistema (`apt-get install xvfb`) → binario `xvfb-run` (ya presente en esta máquina)

Documentar en:
- `requirements.txt` (o el requirements del scraper): `playwright>=1.62`
- `CLAUDE.md` (sección Indeed): motor headed, xvfb, comando de corrida, que corre **solo local**.
- Nota de que `chromium` de playwright vive en `~/.cache/ms-playwright`.

---

## 8. Prototipo medido y gate go/no-go (pre-registrado)

**Prototipo:** tramo de **20 keywords** (desde `proximo_offset` o tramo fijo de prueba), **corrida real contra BD** (`INSERT OR IGNORE`), motor headed bajo xvfb, pacing de §3.

**Instrumentación:** el runner emite un resumen:
`keywords, tarjetas_vistas, fichas_intentadas, insertadas, con_descripcion_real,
challenges, blocked, elapsed_seg`. Además se verifica en BD:
`SELECT COUNT(*) FROM ofertas WHERE portal='indeed' AND id_oferta IN (tramo) AND length(trim(descripcion))>0`.

**Métricas del gate:**

| Métrica | GO | Medición |
|---|---|---|
| Fichas insertadas con descripción real | **≥ 100** | count en BD, descripción no vacía |
| Tasa de fallo por challenge/blocked | **< 15 %** | `(challenges+blocked)/navegaciones` |
| Tiempo total | **≤ 25 min** | wall-clock (extrapola a ~90 kw ≤ 2 h) |

**GO** ⇔ se cumplen **las tres**. **NO-GO** ⇔ falla alguna → se reporta y **Gerardo decide** entre ajustar pacing o dar de baja Indeed.

Nota de tensión: 20 kw × ~7 cards ≈ 140 fichas potenciales; ≥100 con descripción exige ~70 % de yield neto tras dedup y fallos. El riesgo principal para el gate es el **tiempo** (los re-challenges de ~20 s) y el **yield de descripción** si el panel no carrga siempre. Ambos se miden, no se asumen.

---

## 9. Riesgos y decisiones abiertas

1. **Fidelidad de campos estructurados:** si el panel embebido no trae JSON-LD, `fecha_publicacion_iso`, `tipo_trabajo`, `salario_*` quedan NULL para ofertas headed. El schema lo permite y el NLP re-deriva varios; pero es un delta vs la era curl. → Medir en prototipo cuántas traen JSON-LD; si es crítico, evaluar un `/viewjob` autenticado (rechazado por ahora) o parseo DOM del panel.
2. **Estabilidad de sesión:** re-challenge por navegación; el corte-temprano protege pero puede recortar tramos. Aceptado (fromage=14).
3. **Selectores frágiles:** Indeed cambia `data-testid`. Fallbacks múltiples + el prototipo valida los selectores vigentes al 2026-09.
4. **Detección anti-bot evolutiva:** hoy headed pasa; puede endurecerse. El preflight NO-GO lo detecta y corta sin ensuciar la BD.
5. **Concurrencia BD:** `insertar_en_bd` abre SQLite con `timeout=30`; la corrida headed es lenta (menos contención). Sin cambio.
6. **Costo de tiempo:** ~2 h/día de navegador local. Aceptado por Gerardo (1 corrida/día).

---

## 10. Resumen de archivos (qué se tocaría tras aprobación)

| Archivo | Acción |
|---|---|
| `01_sources/indeed/scrapers/indeed_scraper_headed.py` | **nuevo** — motor headed, misma interfaz |
| `scripts/scraping/run_indeed_headed.py` | **nuevo** (o adaptar `run_indeed_local.py`) — tramo por offset + xvfb + insert |
| `scripts/pipeline_command_poller.py` | invocar indeed **bajo `xvfb-run`** |
| `scripts/scraping/check_indeed_unblock.py` | **retirar** (o reescribir probe a headed) + quitar cron 3 h |
| crontab local | reemplazar 3 h-vigía por 1×/día runner headed |
| `requirements*.txt` + `CLAUDE.md` | documentar playwright/chromium/xvfb + que es solo local |
| `run_scraping_vps.sh` (VPS, fuera de rama) | anotar: desactivar paso Indeed |
| `indeed_scraper.py` (curl) | queda como fallback inerte; no se borra aún |

---

## ADDENDUM 2026-09-01 — Aprobación con ajustes (Gerardo)

Spec APROBADA con estas decisiones, que **sobrescriben** lo de arriba donde apliquen:

- **D1 — Vigía: RETIRAR** (no adaptar). Pero el **preflight NO-GO debe loggear `fecha + motivo` en el state-file** (`data/indeed_scraping_state.json`, clave `local`), preservando la función "desde cuándo está bloqueado" que daba el vigía. Campos nuevos en el state: `ultimo_nogo` (ISO) y `ultimo_nogo_motivo` (`blocked` | `challenge` | `login` | `error:<x>`). En GO se limpian.
- **D2 — Campos estructurados:** `tipo_trabajo` y `salario_*` **pueden quedar NULL**. `fecha_publicacion` **NO**: si el panel no trae JSON-LD, **fallback parseando la fecha relativa de la tarjeta del listado** ("hoy", "ayer", "hace N días", "N+ días") → `fecha_publicacion_iso`. El scraper marca el origen (`_fecha_source ∈ {jsonld, tarjeta, none}`) y el prototipo reporta **% con JSON-LD** y **% con fecha recuperada por tarjeta**.
- **A1 — Gate, métrica 1 reformulada (pre-medición):** **rendimiento = fichas con descripción real / tarjetas únicas vistas ≥ 75 %**. El conteo absoluto de fichas se **reporta** pero **no gatea**. Métricas 2 (`<15 %` fallo challenge/blocked) y 3 (`≤25 min`) **sin cambio**.
- **A2 — Desactivar Indeed en cron VPS:** **solo tras GO**, como tarea separada en `main`. No antes, no en esta rama.

**Gate efectivo tras el addendum:** GO ⇔ (rendimiento ≥ 75 %) ∧ (fallo challenge/blocked < 15 %) ∧ (tiempo ≤ 25 min). Se implementa motor + runner + prototipo de 20 keywords, se corre el gate, y **PAUSA** reportando las **tres métricas + las dos mediciones de D2** antes de cualquier paso a producción. Sin merge.

---

## PAUSA

No se escribe código hasta que Gerardo apruebe esta spec. Al aprobar: se implementa el motor headed + runner + prototipo de 20 keywords y se corre el gate go/no-go, reportando las tres métricas antes de cualquier decisión de producción. *(Cumplido: aprobado con addendum 2026-09-01; se procede a implementar.)*
