"""
Indeed Argentina - Scraper HEADED (navegador real bajo xvfb)
============================================================

Motor alternativo a indeed_scraper.py (curl_cffi), necesario desde 2026-09
porque Cloudflare + Indeed bloquean curl_cffi (403 "Security Check") y el
modo headless ("Blocked - Indeed.com"). Un chromium HEADED (headless=False)
bajo xvfb en la IP local pasa ambos muros y ve listados reales.

Ver spec: exports/reportes/SPEC_indeed_scraper_headed_2026-09-01.md

Principio de compatibilidad: expone la MISMA superficie publica que
IndeedScraper y devuelve dicts `oferta` con las MISMAS claves, para que
run_indeed_vps.mapear_oferta_para_bd / insertar_en_bd no cambien.

Descripcion: se obtiene CLICKEANDO la tarjeta (panel embebido `&vjk=`),
NUNCA por deep-link /viewjob (que redirige a login).

Requiere: playwright + chromium (`playwright install chromium`) y correr
bajo un display: `xvfb-run -a python3 ...` (o WSLg con DISPLAY seteado).
"""

import re
import json
import time
import random
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Set

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

BASE_URL = "https://ar.indeed.com"
SEARCH_URL = f"{BASE_URL}/jobs"

# Selectores de descripcion (panel embebido), en orden de preferencia
DESC_SELECTORS = [
    '#jobDescriptionText',
    'div.jobsearch-JobComponent-description',
    '[data-testid="jobDescriptionText"]',
    'div#vjs-desc',
]

# Patron de fecha relativa en la tarjeta del listado (fallback D2)
_RE_HACE_N = re.compile(r'hace\s+m[aá]s\s+de\s+(\d+)\s*d[ií]a', re.I)
_RE_HACE = re.compile(r'hace\s+(\d+)\s*d[ií]a', re.I)
_RE_NMAS = re.compile(r'(\d+)\+?\s*d[ií]as', re.I)
_RE_HOY = re.compile(r'\b(hoy|reci[eé]n publicado|publicado hoy)\b', re.I)
_RE_AYER = re.compile(r'\bayer\b', re.I)


class IndeedScraperHeaded:
    """Scraper headed para ar.indeed.com con playwright (drop-in de IndeedScraper)."""

    VERSION = "headed-1.0.0"

    def __init__(self, delay: float = 5.0, detail_delay: float = 4.0,
                 fetch_details: bool = True, max_fichas: int = 900,
                 headless: bool = False,
                 listado_clear_timeout: float = 25.0,
                 desc_timeout: float = 8.0):
        self.delay = delay
        self.detail_delay = detail_delay
        self.fetch_details = fetch_details
        self.max_fichas = max_fichas
        self.headless = headless
        self.listado_clear_timeout = listado_clear_timeout
        self.desc_timeout = desc_timeout

        self._seen_jks: Set[str] = set()
        self._cut = False                 # corte de la corrida (challenge/blocked/cap)
        self._consecutive_challenges = 0
        self._umbral_corte = 2            # 2 challenges consecutivos irresolubles -> cortar
        self._backoff_base = 15.0
        self._backoff_max = 45.0

        # Estado leido por el runner tras la corrida
        self.preflight_ok: Optional[bool] = None
        self.nogo_motivo: Optional[str] = None      # blocked|challenge|login|error:<x>
        self.detalle_bloqueado = False
        self.stats = {
            'keywords': 0, 'tarjetas_unicas': 0, 'fichas_intentadas': 0,
            'con_descripcion': 0, 'con_jsonld': 0, 'fecha_jsonld': 0,
            'fecha_listado': 0, 'sin_fecha': 0,
            'nav_total': 0, 'nav_fail': 0, 'challenges': 0, 'blocked': 0,
            'elapsed_seg': 0.0,
        }
        logger.info(f"IndeedScraperHeaded {self.VERSION} "
                    f"(headless={headless}, delay={delay}s, detail_delay={detail_delay}s, "
                    f"max_fichas={max_fichas})")

    # ------------------------------------------------------------------
    # utilidades
    # ------------------------------------------------------------------
    def _wait(self, base_delay: float):
        time.sleep(base_delay * random.uniform(0.5, 1.5))

    def _classify(self, page) -> tuple:
        """Devuelve (clase, titulo, n_cards). clase in real|challenge|blocked|login|vacio."""
        titulo = ''
        try:
            titulo = page.title() or ''
        except Exception:
            pass
        low_t = titulo.lower()
        if 'blocked' in low_t:
            return 'blocked', titulo, 0
        if 'iniciar sesión' in low_t or 'iniciar sesion' in low_t or 'cuentas indeed' in low_t:
            return 'login', titulo, 0
        try:
            n = len(page.query_selector_all('a[data-jk]'))
        except Exception:
            n = 0
        if n > 0:
            return 'real', titulo, n
        if 'security check' in low_t or 'just a moment' in low_t:
            return 'challenge', titulo, 0
        return 'vacio', titulo, 0

    def _goto_listado_espera(self, page, url: str) -> tuple:
        """Navega y espera a que limpie el challenge. Devuelve (clase, titulo, n_cards)."""
        self.stats['nav_total'] += 1
        try:
            page.goto(url, timeout=60000, wait_until='domcontentloaded')
        except Exception as e:
            logger.warning(f"  goto error: {type(e).__name__}: {str(e)[:80]}")
            self.stats['nav_fail'] += 1
            return 'error', '', 0
        deadline = time.time() + self.listado_clear_timeout
        clase, titulo, n = self._classify(page)
        while clase in ('challenge', 'vacio') and time.time() < deadline:
            page.wait_for_timeout(2000)
            clase, titulo, n = self._classify(page)
        if clase in ('challenge', 'blocked', 'login', 'error', 'vacio'):
            self.stats['nav_fail'] += 1
        return clase, titulo, n

    def _manejar_fallo(self, clase: str) -> bool:
        """Aplica backoff/corte segun §4. Devuelve True si hay que ABORTAR la keyword/corrida."""
        if clase == 'blocked' or clase == 'login':
            logger.error(f"  '{clase}' -> CORTE DURO")
            self.stats['blocked'] += 1
            self._cut = True
            self.detalle_bloqueado = True
            return True
        if clase in ('challenge', 'vacio', 'error'):
            self.stats['challenges'] += 1
            self._consecutive_challenges += 1
            if self._consecutive_challenges >= self._umbral_corte:
                logger.error(f"  {self._consecutive_challenges} challenges consecutivos -> CORTE")
                self._cut = True
                self.detalle_bloqueado = True
                return True
            backoff = min(self._backoff_base * self._consecutive_challenges, self._backoff_max)
            logger.warning(f"  challenge -> backoff {backoff:.0f}s (consecutivos={self._consecutive_challenges})")
            time.sleep(backoff)
            return True   # abortar esta keyword (no insistir en el mismo goto mas de eso)
        return False

    # ------------------------------------------------------------------
    # fecha del listado (fallback D2): modelo mosaic (pubDate / relativa)
    # ------------------------------------------------------------------
    @staticmethod
    def _fecha_desde_relativa(texto: str) -> Optional[str]:
        """'hace 4 días' / 'Recién publicado' / 'hoy' / 'ayer' -> YYYY-MM-DD."""
        if not texto:
            return None
        m = _RE_HACE_N.search(texto) or _RE_HACE.search(texto) or _RE_NMAS.search(texto)
        dias = None
        if m:
            try:
                dias = int(m.group(1))
            except (ValueError, IndexError):
                dias = None
        elif _RE_HOY.search(texto):
            dias = 0
        elif _RE_AYER.search(texto):
            dias = 1
        if dias is None:
            return None
        return (datetime.now() - timedelta(days=dias)).strftime('%Y-%m-%d')

    @staticmethod
    def _fecha_desde_epoch(pub_ms) -> Optional[str]:
        try:
            return datetime.fromtimestamp(int(pub_ms) / 1000).strftime('%Y-%m-%d')
        except Exception:
            return None

    @staticmethod
    def _mosaic_dates(page) -> Dict[str, dict]:
        """jobkey -> {pubDate, rel} desde el modelo mosaic del listado (una sola lectura)."""
        js = """() => {
          try {
            const pd = window.mosaic.providerData['mosaic-provider-jobcards'];
            const res = pd.metaData.mosaicProviderJobCardsModel.results;
            const out = {};
            for (const r of res) { out[r.jobkey] = {pubDate: r.pubDate, rel: r.formattedRelativeTime}; }
            return out;
          } catch(e) { return {}; }
        }"""
        try:
            return page.evaluate(js) or {}
        except Exception:
            return {}

    # ------------------------------------------------------------------
    # JSON-LD del panel (si existe)
    # ------------------------------------------------------------------
    @staticmethod
    def _parse_jsonld(page) -> Optional[Dict]:
        try:
            scripts = page.query_selector_all('script[type="application/ld+json"]')
        except Exception:
            return None
        for sc in scripts:
            try:
                raw = sc.text_content()
                data = json.loads(raw)
            except Exception:
                continue
            if isinstance(data, dict) and data.get('@type') == 'JobPosting':
                return data
        return None

    # ------------------------------------------------------------------
    # listado por keyword
    # ------------------------------------------------------------------
    def _listado(self, page, keyword: str, location: str, fromage: int) -> List[Dict]:
        url = f"{SEARCH_URL}?q={keyword}&l={location}&fromage={fromage}"
        clase, titulo, n = self._goto_listado_espera(page, url)
        if clase != 'real':
            self._manejar_fallo(clase)
            return []
        self._consecutive_challenges = 0

        mosaic = self._mosaic_dates(page)
        cards = []
        try:
            beacons = page.query_selector_all('div.job_seen_beacon')
        except Exception:
            beacons = []
        for b in beacons:
            try:
                link = b.query_selector('a[data-jk]')
                if not link:
                    continue
                jk = link.get_attribute('data-jk')
                if not jk or jk in self._seen_jks:
                    continue
                self._seen_jks.add(jk)
                titulo_c = (link.inner_text() or '').strip()
                comp = b.query_selector('[data-testid=company-name]')
                loc = b.query_selector('[data-testid=text-location]')
                sal = b.query_selector('[data-testid=attribute_snippet_testid]')
                card = {
                    'job_key': jk,
                    'titulo': titulo_c,
                    'empresa': comp.inner_text().strip() if comp else None,
                    'ubicacion': loc.inner_text().strip() if loc else None,
                    'salario_listing': sal.inner_text().strip() if sal else None,
                    'url': f"{BASE_URL}/viewjob?jk={jk}",
                    'keyword_source': keyword,
                }
                # fecha desde el modelo mosaic del listado (D2)
                md = mosaic.get(jk) or {}
                fecha = self._fecha_desde_relativa(md.get('rel')) or self._fecha_desde_epoch(md.get('pubDate'))
                if fecha:
                    card['fecha_publicacion'] = fecha
                    card['_fecha_source'] = 'listado'
                cards.append(card)
            except Exception as e:
                logger.warning(f"  error parseando tarjeta: {str(e)[:60]}")
                continue
        return cards

    # ------------------------------------------------------------------
    # descripcion por click (panel embebido)
    # ------------------------------------------------------------------
    def _detalle_click(self, page, card: Dict) -> None:
        jk = card['job_key']
        try:
            link = page.query_selector(f'a[data-jk="{jk}"]')
            if not link:
                return
            link.click(timeout=10000)
        except Exception as e:
            logger.info(f"  click fallo jk={jk[:8]}: {str(e)[:50]}")
            return

        # esperar a que aparezca la descripcion con texto real
        desc_txt = None
        deadline = time.time() + self.desc_timeout
        while time.time() < deadline:
            page.wait_for_timeout(700)
            for sel in DESC_SELECTORS:
                el = page.query_selector(sel)
                if el:
                    try:
                        t = el.inner_text()
                    except Exception:
                        t = None
                    if t and len(t.strip()) > 50:
                        desc_txt = t.strip()
                        break
            if desc_txt:
                break

        # login gate (si el click abrio /viewjob con login)
        clase, _, _ = self._classify(page)
        if clase == 'login':
            self.stats['blocked'] += 1
            self._cut = True
            self.detalle_bloqueado = True
            return

        # JSON-LD si el panel lo trae
        jsonld = self._parse_jsonld(page)
        if jsonld:
            self.stats['con_jsonld'] += 1
            if jsonld.get('datePosted'):
                card['fecha_publicacion'] = jsonld.get('datePosted')
                card['_fecha_source'] = 'jsonld'
            if jsonld.get('validThrough'):
                card['fecha_expiracion'] = jsonld.get('validThrough')
            et = jsonld.get('employmentType')
            if et:
                card['tipo_empleo'] = et if isinstance(et, list) else [et]
            sal = jsonld.get('baseSalary', {})
            if isinstance(sal, dict):
                val = sal.get('value', {})
                if isinstance(val, dict):
                    card['salario_min'] = val.get('minValue')
                    card['salario_max'] = val.get('maxValue')
                    card['salario_moneda'] = sal.get('currency')
                    card['salario_periodo'] = val.get('unitText')
            ho = jsonld.get('hiringOrganization', {})
            if isinstance(ho, dict):
                card['empresa_jsonld'] = ho.get('name')
            jl = jsonld.get('jobLocation', {})
            if isinstance(jl, dict):
                addr = jl.get('address', {})
                if isinstance(addr, dict):
                    card['localidad_jsonld'] = addr.get('addressLocality')
                    card['provincia_jsonld'] = addr.get('addressRegion')
                    card['pais_jsonld'] = addr.get('addressCountry')

        # fecha: jsonld (panel) > listado (mosaic). Contabilizar el origen final (D2).
        src = card.get('_fecha_source')
        if src == 'jsonld':
            self.stats['fecha_jsonld'] += 1
        elif src == 'listado' and card.get('fecha_publicacion'):
            self.stats['fecha_listado'] += 1
        else:
            card['_fecha_source'] = 'none'
            self.stats['sin_fecha'] += 1

        if desc_txt:
            card['descripcion'] = desc_txt
            card['_jsonld'] = bool(jsonld)

    # ------------------------------------------------------------------
    # preflight
    # ------------------------------------------------------------------
    def _preflight(self, page, location: str, fromage: int) -> bool:
        url = f"{SEARCH_URL}?q=cajero&l={location}&fromage={fromage}"
        clase, titulo, n = self._goto_listado_espera(page, url)
        if clase == 'real':
            logger.info(f"  PREFLIGHT GO (tarjetas={n})")
            return True
        self.nogo_motivo = clase if clase in ('blocked', 'login', 'challenge') else f'error:{clase}'
        logger.error(f"  PREFLIGHT NO-GO ({self.nogo_motivo}, titulo={titulo[:40]!r})")
        return False

    # ------------------------------------------------------------------
    # API publica (drop-in de IndeedScraper)
    # ------------------------------------------------------------------
    def scrape_with_keywords(self, keywords: List[str], location: str = "Argentina",
                             fromage: int = 14) -> List[Dict]:
        from playwright.sync_api import sync_playwright
        t0 = time.time()
        ofertas: List[Dict] = []
        launch_args = ['--no-sandbox', '--disable-blink-features=AutomationControlled']

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.headless, args=launch_args)
            ctx = browser.new_context(locale='es-AR')
            page = ctx.new_page()

            self.preflight_ok = self._preflight(page, location, fromage)
            if not self.preflight_ok:
                browser.close()
                self.stats['elapsed_seg'] = round(time.time() - t0, 1)
                return []

            for i, kw in enumerate(keywords, 1):
                if self._cut or self.stats['fichas_intentadas'] >= self.max_fichas:
                    break
                self.stats['keywords'] += 1
                logger.info(f"[{i}/{len(keywords)}] '{kw}'")
                self._wait(self.delay)
                cards = self._listado(page, kw, location, fromage)
                if self._cut:
                    break
                if not cards:
                    continue
                logger.info(f"  {len(cards)} tarjetas nuevas (unicas total: {len(self._seen_jks)})")

                if not self.fetch_details:
                    ofertas.extend(cards)
                    continue

                for card in cards:
                    if self._cut or self.stats['fichas_intentadas'] >= self.max_fichas:
                        break
                    self._wait(self.detail_delay)
                    self.stats['fichas_intentadas'] += 1
                    self._detalle_click(page, card)
                    card['scrapeado_en'] = datetime.now().isoformat()
                    card['portal'] = 'indeed'
                    if card.get('descripcion'):
                        self.stats['con_descripcion'] += 1
                        ofertas.append(card)
                    # sin descripcion = muda -> se descarta (no se agrega)

            browser.close()

        self.stats['tarjetas_unicas'] = len(self._seen_jks)
        self.stats['elapsed_seg'] = round(time.time() - t0, 1)
        return ofertas

    def scrape_with_keywords_file(self, json_path: str, estrategia: str = "exhaustiva",
                                  location: str = "Argentina", fromage: int = 14,
                                  max_keywords: int = None, offset: int = 0) -> List[Dict]:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        keywords = data.get('estrategias', {}).get(estrategia, {}).get('keywords', [])
        keywords = [k for k in keywords if k.strip()]
        total = len(keywords)
        if offset:
            keywords = keywords[offset:]
        if max_keywords:
            keywords = keywords[:max_keywords]
        logger.info(f"Cargadas {len(keywords)} keywords ({estrategia}) tramo "
                    f"{offset + 1}-{offset + len(keywords)} de {total}")
        return self.scrape_with_keywords(keywords, location, fromage)
