# Indeed — relevamiento de alternativas de acceso (para decisión de Gerardo)

**Fecha:** 2026-10-15 · **Rama:** `relevamiento/indeed-alternativas` · **Solo relevamiento, nada ejecutado.**
El probe sigue corriendo como está; no se tocó producción ni se apagó nada.

Contexto: Indeed en 0 desde 2026-09-16. 61 probes desde 08-10, 0 GO (challenge
continuo). El motor headed (chromium/xvfb, contexto limpio cada corrida) ya no pasa
Cloudflare; además el DOM del panel cambió (SELECTORES_DESCRIPCION rotos — fix
armado pero inejecutable sin un GO). Cobertura ocupacional única de Indeed medida:
≈0 (8 ISCOs / 23 avisos). Aporte = 15,6% de volumen.

---

## 2. Prueba IP vs fingerprint (la que decide si un proxy sirve)

**Objetivo:** saber si el bloqueo es por **IP** (un proxy residencial lo resuelve)
o por **fingerprint/comportamiento** (el proxy sería plata tirada). Variable única:
cambiar SOLO la IP de egreso, con el MISMO motor headed.

**Procedimiento (10 min, para que lo corra Gerardo):**
1. En la misma máquina local (mismas deps: xvfb + playwright + chromium), **cambiar
   la IP de egreso**: tethering al hotspot del celular (lo más simple), o una VPN.
   — NO el VPS (no tiene xvfb/playwright/chromium instalado → no sirve de contraste
   con el mismo motor).
2. Con esa red activa, correr el probe (no toca offset, no escribe BD):
   ```bash
   cd /mnt/d/OEDE/Webscrapping
   xvfb-run -a /usr/bin/python3 scripts/scraping/run_indeed_headed.py \
       --no-advance --dry-run --prototipo --max-keywords 3 2>&1 \
     | grep -iE "NO-GO|PROBE|challenge|blocked|keywords_corridas|tarjetas|gate"
   ```
3. Volver a la red normal.

**Interpretación:**
- Sale **`NO-GO ... challenge`** (igual que ahora) → el bloqueo **NO es solo IP** →
  es fingerprint/comportamiento → **un proxy residencial NO alcanza** (descarta opción proxy).
- Sale un resumen con **`keywords_corridas>0` / `tarjetas>0`** (pasó el preflight) →
  el bloqueo **es por IP** → **un proxy residencial funcionaría**.

Nota: la fingerprint (chromium/xvfb/máquina) queda idéntica; solo cambia la IP →
test limpio de una variable. Dependencias ya instaladas en la local.

---

## 3. Sesión persistente (lo que NO probamos del headed)

**Hoy:** `scrape_with_keywords()` hace `p.chromium.launch()` + `browser.new_context(locale='es-AR')`
→ **contexto 100% limpio cada corrida** (sin `user_data_dir`, sin cookies, sin
`cf_clearance`). Es lo contrario de lo que hizo funcionar el bootstrap de agosto
(una sesión "tibia").

**Perfil persistente:** reemplazar ese launch por
`p.chromium.launch_persistent_context(user_data_dir=PERFIL, headless=False, args=..., locale='es-AR')`
con un `user_data_dir` FIJO → conserva cookies, `cf_clearance`, localStorage y una
fingerprint que "envejece" entre corridas. Cambio de código **chico** (~3 líneas en
`indeed_scraper_headed.py`, un solo método).

**Viabilidad y riesgos (franco):**
- ⚠️ **Chicken-and-egg:** el perfil solo sirve si se lo **siembra pasando el
  challenge UNA vez** (humano resolviéndolo a mano en ese perfil). Hoy ni headed
  pasa → habría que hacer ese paso manual una vez. Si ni a mano se puede, esta vía muere.
- ⚠️ **`cf_clearance` es efímero** (~30 min típico). El perfil conserva la fingerprint
  tibia, pero CF puede re-desafiar al expirar el clearance → re-siembra periódica.
- ⚠️ **Quema de perfil:** si CF marca el perfil/cookies, queda envenenado → rearmar a mano.
- ⚠️ **Mantenimiento + sin concurrencia:** un perfil = un proceso por vez; necesita
  re-warming manual ocasional. Es exactamente lo que funcionó en agosto, pero
  "sostenido en el tiempo" es justo la parte difícil con CF moderno.
- **Costo:** $0 de plata; trabajo = cambio chico + el ritual de siembra/mantenimiento.

---

## 1. API oficial / acceso institucional

**Hallazgo decisivo: Indeed NO entrega avisos individuales (microdatos) a NADIE hoy**
— ni OCDE, ni FMI, ni bancos centrales, ni universidades. El Publisher Program cerró
registros en 2020; la Job Search API pública quedó *deprecated* 2023 y **apagada 2024,
sin reemplazo**. Lo único que queda son APIs del lado del empleador (ATS/Sponsored/Apply),
partner-gated, para PUBLICAR avisos, no extraerlos.

- **Lo que SÍ existe (solo AGREGADOS):** Indeed **Hiring Lab** + **Policy Partners
  Program** + **Data Portal** (data.indeed.com, CC BY 4.0) + Hiring Lab API → índices
  y series de tiempo (Job Postings Index, Wage Tracker, remoto) a nivel nacional/regional.
  **Nunca avisos individuales.** Precedentes de uso agregado: OCDE, FMI, BCE, Bank of
  England, Fed. Un ministerio con uso estadístico es candidato **ideal** para esto →
  probabilidad **alta** y mayormente gratis/abierto.
- **Canal:** `hiring-lab-api@indeed.com` (verificar en docs.indeed.com/hiring-lab-api) +
  Policy Partners Program. Repos abiertos: github.com/hiring-lab/data; series en FRED.

**Implicancia para MOL:** la vía institucional **NO resuelve** la necesidad del pipeline
(avisos aviso-por-aviso para NLP/matching) — solo da agregados. Sirve como **insumo
complementario** (validar tendencias contra Hiring Lab), **no como reemplazo** del canal
de scraping. Para microdato, el camino legítimo no es Indeed sino un agregador (JSearch/
SerpApi, §5) o un proveedor comercial (Lightcast/Adzuna, caros).

## 4. Servicios anti-bot

El challenge de Indeed es **managed challenge / Turnstile** de Cloudflare (no un
JS-challenge viejo). Eso define qué sirve:

**Self-hosted:**
- **FlareSolverr: NO sirve** para este challenge (carga la página pero no genera el
  token de Turnstile; chromium plano detectable). En un test 2026 de 6 sitios CF:
  timeout en los 6. Descartado.
- **nodriver** (sucesor de undetected-chromedriver): **la única self-hosted que pasó
  un Turnstile real** en benchmark (90% CF). PERO requiere **IPs residenciales** +
  mantenimiento continuo, y reescribir el scraper a su API (no es drop-in de Playwright).
- **Byparr** (drop-in API de FlareSolverr, motor Camoufox): mejor que FlareSolverr
  pero techo ~81% CF, no apuesta fiable contra Turnstile.
- **Muertos/no fiables para esto:** undetected-chromedriver, playwright-stealth,
  patchright, rebrowser-playwright.

**Comerciales (web unlocker — toman URL, devuelven HTML resolviendo CF; integración baja):**
| Servicio | Precio 2026 | Evidencia vs este challenge | Free trial |
|---|---|---|---|
| **Bright Data Web Unlocker** | **$1,50/1k** exitosos (planes $499→$1,30/1k…) | CF+CAPTCHA+TLS; reportado para Indeed | **5.000 req gratis** |
| **Scrapfly** | ~$2,85/1k ($30≈6,6k) | **~98% CF, Turnstile explícito** (mejor en benchmark) | sí (monto incierto) |
| **ZenRows** | $16/mes→45k créditos (~$6,85/1k efectivo) | **90% éxito en Indeed.com** (el mejor para ese sitio) | **5.000 créditos/mes gratis** |
| ScraperAPI | $49/mes (~$3,72/1k) | maneja CF con flag, menos fuerte en interactivo | 5k trial |
| ScrapingBee | $19/mes→75k | **~45% CF** — flojo, no recomendado | 1k trial |
| Zyte API | $1,01–16/1k browser-rendered | escala por dificultad (tier advanced caro) | sí (incierto) |
| Oxylabs Web Unblocker | ~$9,40/GB | web unblocker genérico | sí (incierto) |

**Lo que cruza Turnstile hoy con evidencia:** Bright Data y Scrapfly (Turnstile
explícito), ZenRows (dato directo 90% en Indeed). Los **tres tienen free tier** →
se validan contra ar.indeed.com **gratis** antes de pagar. Self-hosted serio = nodriver
+ residenciales (más barato en plata, más caro en mantenimiento).

## 5. Fuentes alternativas con el mismo dato

Como la cobertura ocupacional única de Indeed era ≈0, alcanza con cobertura
**equivalente** de volumen/amplitud AR. Dos vías pagas-baratas cubren AR **y además
incluyen el inventario de Indeed vía Google for Jobs** (cierran el hueco sin pelear con CF):

| Fuente | Cubre AR | Precio 2026 | ¿Trae Indeed? | Dato para NLP | Reparo |
|---|---|---|---|---|---|
| **JSearch** (RapidAPI) | **Sí** (`country=ar`) | Free 200/mes · **Pro $25/mes=10k req** · $75/$150 | **Sí** (Google for Jobs) | descripción razonable (JSON) | ToS redistribución (zona gris si se publica aviso literal) |
| **SerpApi** Google Jobs | **Sí** (`gl=ar`) | Free 250/mes · $25=1k búsq · $75/$150/$275 | **Sí** (Google for Jobs) | JSON estructurado | más caro por fila que JSearch |
| Jooble API | Sí | **Gratis** (key por proyecto) | parcial/indirecto | **snippets truncados** (flojo p/ tareas) | orientado a buscador final |
| Careerjet API | Sí | **Gratis** (affiliate_id), JSON/XML | parcial/indirecto | ok pero `offset≤999` | programa de publishers, no pipelines |
| Apify Indeed scraper | Sí | $0,07–5 /1k | **Sí** (scraping directo) | completo | **mismo problema ToS/CF, tercerizado** + PII |

**Descartados por no cubrir AR:** Adzuna, Arbeitnow (Europa), Juju (EE.UU.).
**No existe** dataset público ni feed RSS/XML de *avisos individuales* AR
(datos.gob.ar tiene solo estadística agregada de empleo registrado, no ofertas).

**Lo más eficiente costo/cobertura/legitimidad: JSearch Pro ($25/mes, 10k req,
`country=ar`)** — y encima contiene el inventario de Indeed. SerpApi es el equivalente
algo más caro. A verificar antes de decidir (como se midió Indeed): profundidad real
de resultados AR por keyword, y el ToS de redistribución si se publicaría el aviso literal.

## 6. Síntesis para decidir

Ordenadas por relación **costo/probabilidad** (mejor ratio arriba). **Gerardo decide** —
no recomiendo una sola. Recordar: el objetivo es recuperar **volumen de avisos AR**
(Indeed aportaba 15,6%, cobertura ocupacional única ≈0), no Indeed per se.

| # | Opción | Costo (plata / trabajo) | Prob. éxito | Tiempo hasta saber | Si falla |
|---|---|---|---|---|---|
| 0 | **Test IP vs fingerprint (§2)** | $0 / 10 min | — (es diagnóstico) | **10 min** | decide si la rama "proxy" vale o se descarta |
| 1 | **JSearch / SerpApi (§5)** — Google for Jobs, trae Indeed | **$25/mes** / integración API chica | **Alta** (cubre AR + Indeed) | **1-2 días** (medir profundidad AR) | probar el otro; o Jooble gratis (datos pobres) |
| 2 | **Web unlocker comercial (§4)** — Bright Data / Scrapfly / ZenRows | $0 para probar (free tier) → **$1,50-7/1k** | **Media-alta** (ZenRows 90% Indeed) | **horas** (free tier vs ar.indeed.com) | caer a otra opción; sigue siendo vs ToS Indeed |
| 3 | **Hiring Lab agregados (§1)** | $0 / gestión institucional | **Alta** pero **solo agregados** | semanas (gestión) | — (no reemplaza avisos; es complemento) |
| 4 | **Perfil persistente (§3)** | $0 / cambio chico + ritual de siembra | **Baja-media** (frágil, cf_clearance efímero) | **días** (sembrar + ver si dura) | caer a proxy/unlocker o baja de canal |
| 5 | **nodriver + proxies residenciales (§4)** | proxy (~$50-300/mes) / **reescritura media** | **Media** (único self-hosted que cruza Turnstile) | **1-2 semanas** | caer a web unlocker comercial |
| 6 | **Baja del canal** (reporte 2026-10-15 previo) | $0 / documentar | certeza | inmediato | — pierde 15,6% volumen, ~0 ocupaciones únicas |

**Lecturas transversales (sin elegir por vos):**
- El **test §2 ($0, 10 min)** conviene correrlo primero: si da *fingerprint*, borra de la
  mesa la rama proxy-solo y empuja hacia unlocker comercial o aggregator.
- La vía **más barata y legítima para recuperar el dato aviso-por-aviso** es el
  **aggregator (JSearch/SerpApi)** — además esquiva Cloudflare por completo y *contiene*
  el inventario de Indeed. Su reparo es el ToS de redistribución si se publicara el aviso
  literal (para uso estadístico interno no hay traba evidente).
- La vía **institucional (Hiring Lab)** es alta-probabilidad pero **no da microdatos** →
  no reemplaza el scraping; vale como complemento de validación de tendencias.
- Seguir peleando contra Cloudflare (perfil persistente / nodriver) es la rama de **más
  trabajo y menos certeza**; solo tiene sentido si se exige específicamente el dato de
  Indeed y se descarta pagar un aggregator/unlocker.
- Cualquiera de 1/2/5 se **valida gratis o barato en días** antes de comprometer plata.
