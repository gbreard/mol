"""
Indeed Argentina - Scraper propio
=================================

Scraper para ar.indeed.com SIN dependencia de JobSpy.

Usa curl_cffi para bypassear Cloudflare (impersonacion TLS Chrome).
Estrategia multi-keyword (similar a ZonaJobs): como Indeed restringe
paginacion a una sola pagina para no-autenticados, se usan multiples
keywords para obtener cobertura amplia.

Metodologia: curl_cffi + BeautifulSoup (HTML parsing)
Anti-bot: Cloudflare bypass via TLS fingerprint impersonation
Paginacion: NO funciona (redirige a login). Solo pagina 1 (~15/keyword)
Detalle: /viewjob?jk={job_key} con JSON-LD estructurado

Campos extraidos del listado:
  - job_key (jk): identificador unico hex 16 chars
  - titulo, empresa, ubicacion

Campos extraidos del detalle (JSON-LD + HTML):
  - descripcion completa (#jobDescriptionText)
  - fecha_publicacion (datePosted ISO)
  - tipo_empleo (employmentType)
  - salario (baseSalary si disponible)
  - empresa y ubicacion confirmados

Dependencias:
  - curl_cffi (pip install curl_cffi)
  - beautifulsoup4

Uso:
    scraper = IndeedScraper()
    ofertas = scraper.scrape_with_keywords(['vendedor', 'administrativo'])
    ofertas = scraper.scrape_with_keywords_file('config/scraping/master_keywords.json')
"""

from curl_cffi import requests as cffi_requests
from bs4 import BeautifulSoup
import json
import re
import time
import logging
import random
from datetime import datetime
from typing import List, Dict, Optional, Set
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class IndeedScraper:
    """Scraper para ar.indeed.com usando curl_cffi."""

    BASE_URL = "https://ar.indeed.com"
    SEARCH_URL = f"{BASE_URL}/jobs"

    def __init__(self, delay: float = 2.0, detail_delay: float = 2.0,
                 fetch_details: bool = True):
        """
        Args:
            delay: Segundos entre requests de listado
            detail_delay: Segundos entre requests de detalle
            fetch_details: Si True, fetch pagina de detalle para descripcion
        """
        self.delay = delay
        self.detail_delay = detail_delay
        self.fetch_details = fetch_details
        # Fingerprints en orden de preferencia. Cloudflare bloquea familias enteras:
        #   2026-04-23: 'chrome' (=chrome110/116) bloqueado -> chrome131 pasaba
        #   2026-08-06: TODA la familia chrome/edge da 403 -> firefox/safari pasan
        # Si el primero empieza a dar 403 se rota al siguiente automaticamente.
        self._fingerprints = ['firefox135', 'safari184', 'firefox133', 'safari180', 'chrome131']
        self._fp_idx = 0
        self.session = cffi_requests.Session(impersonate=self._fingerprints[0])
        self._seen_jks: Set[str] = set()
        self.detail_retries = 2      # reintentos ante 403 en el detalle
        self.detail_backoff = 12.0   # segundos base entre reintentos (x nro de intento)
        self.detalle_bloqueado = False  # True si la IP perdio acceso a /viewjob
        self._bootstrap_intentado = False  # el bootstrap con navegador se prueba 1 vez
        self._consecutive_blocks = 0
        self._max_consecutive_blocks = 5  # Rotar fingerprint si 5 keywords seguidos dan 403
        logger.info(f"IndeedScraper inicializado (delay={delay}s, detail_delay={detail_delay}s, "
                     f"fetch_details={fetch_details}, impersonate={self._fingerprints[0]})")

    def bootstrap_cookies_navegador(self, timeout_ms: int = 60000) -> bool:
        """
        Abre un navegador real, deja que resuelva el challenge de Cloudflare y
        se queda con las cookies (cf_clearance / __cf_bm) para la sesion curl.

        Para que sirve: Cloudflare puede exigir ejecutar JavaScript ("Security
        Check — Please enable JavaScript"), cosa que curl_cffi no hace por mas
        que rote fingerprints. Un navegador lo pasa una vez y sus cookies
        habilitan miles de requests baratos por curl.

        OJO: no sirve contra "Blocked - Indeed.com", que es un bloqueo de IP del
        propio Indeed, posterior al challenge. Si el navegador ve ese cartel,
        devuelve False: no hay nada que rescatar y hay que cambiar de IP.

        Returns:
            True si consiguio cookies utiles.
        """
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            logger.warning("  playwright no instalado — sin bootstrap de cookies "
                            "(pip install playwright && playwright install chromium)")
            return False

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True, args=['--no-sandbox'])
                ctx = browser.new_context(locale='es-AR')
                page = ctx.new_page()
                page.goto(f"{self.SEARCH_URL}?q=cajero&l=Argentina", timeout=timeout_ms)
                page.wait_for_timeout(12000)   # dar tiempo al challenge
                titulo = page.title()
                cookies = ctx.cookies()
                user_agent = page.evaluate("() => navigator.userAgent")
                browser.close()
        except Exception as e:
            logger.warning(f"  bootstrap con navegador fallo: {type(e).__name__}: {e}")
            return False

        if 'Blocked' in titulo:
            logger.error(f"  El navegador tambien ve '{titulo}': la IP esta bloqueada "
                          f"por Indeed, no es el challenge. Hay que cambiar de IP.")
            return False

        utiles = {c['name']: c['value'] for c in cookies
                  if c['name'] in ('cf_clearance', '__cf_bm')}
        if not utiles:
            logger.warning(f"  el navegador no dejo cookies de Cloudflare (titulo: {titulo})")
            return False

        for nombre, valor in utiles.items():
            self.session.cookies.set(nombre, valor, domain='.indeed.com')
        # El cf_clearance queda atado al user-agent que lo obtuvo
        self.session.headers.update({'User-Agent': user_agent})
        logger.info(f"  cookies de navegador cargadas: {', '.join(utiles)} (titulo: {titulo})")
        return True

    def _rotate_fingerprint(self) -> bool:
        """
        Rota al siguiente fingerprint TLS tras bloqueo sostenido.

        Returns:
            True si quedaba otro fingerprint, False si se agotaron todos.
        """
        self._fp_idx += 1
        if self._fp_idx >= len(self._fingerprints):
            # Ultimo recurso antes de rendirse: si lo que frena es el challenge
            # de Cloudflare (JS obligatorio), un navegador lo pasa y sus cookies
            # sirven para el resto de la corrida. Se intenta una sola vez.
            if not self._bootstrap_intentado:
                self._bootstrap_intentado = True
                logger.info("  Fingerprints agotados — probando bootstrap con navegador")
                if self.bootstrap_cookies_navegador():
                    self._fp_idx = 0
                    self._consecutive_blocks = 0
                    return True
            return False

        nuevo = self._fingerprints[self._fp_idx]
        logger.warning(f"  Rotando fingerprint TLS -> '{nuevo}' "
                        f"({self._fp_idx}/{len(self._fingerprints) - 1})")
        self.session = cffi_requests.Session(impersonate=nuevo)
        self._consecutive_blocks = 0
        return True

    def _wait(self, base_delay: float):
        """Delay con jitter aleatorio para parecer humano."""
        jitter = random.uniform(0.5, 1.5)
        time.sleep(base_delay * jitter)

    # ----------------------------------------------------------------
    # LISTING: Buscar ofertas por keyword
    # ----------------------------------------------------------------

    def search_keyword(self, keyword: str, location: str = "Argentina",
                       fromage: int = 14) -> List[Dict]:
        """
        Busca ofertas por keyword (solo pagina 1).

        Args:
            keyword: Termino de busqueda
            location: Ubicacion (default: Argentina)
            fromage: Dias de antiguedad maxima (default: 14)

        Returns:
            Lista de dicts con datos basicos de cada oferta
        """
        params = {
            'q': keyword,
            'l': location,
            'fromage': str(fromage),
        }
        url = self.SEARCH_URL
        try:
            r = self.session.get(url, params=params,
                                  headers={'Accept-Language': 'es-AR,es;q=0.9'},
                                  timeout=30)

            if r.status_code == 403:
                logger.warning(f"  403 para keyword '{keyword}' - Cloudflare block")
                self._consecutive_blocks += 1
                return []

            if r.status_code != 200:
                logger.warning(f"  HTTP {r.status_code} para keyword '{keyword}'")
                return []

            self._consecutive_blocks = 0  # Reset on success

        except Exception as e:
            logger.error(f"  Error en request para '{keyword}': {e}")
            return []

        soup = BeautifulSoup(r.text, 'html.parser')

        # Check for challenge/login pages
        title = soup.title.string if soup.title else ''
        if 'Security Check' in title or 'Iniciar sesión' in title:
            logger.warning(f"  Blocked/login page para '{keyword}'")
            self._consecutive_blocks += 1
            return []

        # Parse job cards
        cards = soup.select('div.job_seen_beacon')
        ofertas = []

        for card in cards:
            try:
                # Job key and title from the link
                link = card.select_one('a[data-jk]')
                if not link:
                    continue

                jk = link.get('data-jk', '')
                if not jk or jk in self._seen_jks:
                    continue

                self._seen_jks.add(jk)

                titulo = link.get_text(strip=True)

                # Company
                company_el = card.select_one('[data-testid=company-name]')
                empresa = company_el.get_text(strip=True) if company_el else None

                # Location
                loc_el = card.select_one('[data-testid=text-location]')
                ubicacion = loc_el.get_text(strip=True) if loc_el else None

                # Salary (sometimes in listing)
                sal_el = card.select_one('[data-testid=attribute_snippet_testid]')
                salario_listing = sal_el.get_text(strip=True) if sal_el else None

                ofertas.append({
                    'job_key': jk,
                    'titulo': titulo,
                    'empresa': empresa,
                    'ubicacion': ubicacion,
                    'salario_listing': salario_listing,
                    'url': f"{self.BASE_URL}/viewjob?jk={jk}",
                    'keyword_source': keyword,
                })

            except Exception as e:
                logger.warning(f"  Error parseando card: {e}")
                continue

        return ofertas

    # ----------------------------------------------------------------
    # DETAIL: Obtener descripcion completa
    # ----------------------------------------------------------------

    def fetch_detail(self, job_key: str) -> Optional[Dict]:
        """
        Fetch pagina de detalle de una oferta.

        Returns:
            Dict con campos del detalle, o None si falla
        """
        url = f"{self.BASE_URL}/viewjob?jk={job_key}"
        # Los 403 del detalle suelen ser throttling momentaneo, no bloqueo firme:
        # esperar y reintentar recupera la mayoria. Sin esto la oferta se guarda
        # muda y hay que backfillearla despues (que es lo que quema la IP).
        intentos = self.detail_retries + 1
        r = None
        for intento in range(1, intentos + 1):
            try:
                r = self.session.get(url,
                                      headers={'Accept-Language': 'es-AR,es;q=0.9'},
                                      timeout=30)
            except Exception as e:
                logger.error(f"  Error fetching detail {job_key}: {e}")
                return None

            if r.status_code == 200:
                break

            if r.status_code == 403 and intento < intentos:
                espera = self.detail_backoff * intento
                logger.info(f"  403 en detalle {job_key}, reintento {intento}/"
                             f"{intentos - 1} en {espera:.0f}s")
                time.sleep(espera)
                continue

            # 404 = oferta caida (ruido normal). 403 tras agotar reintentos =
            # bloqueo real, cuenta para la rotacion de fingerprint.
            if r.status_code == 403:
                self._consecutive_blocks += 1
            logger.warning(f"  HTTP {r.status_code} en detalle {job_key}")
            return None

        if r is None or r.status_code != 200:
            return None

        soup = BeautifulSoup(r.text, 'html.parser')

        # Check for blocks (title.string es None si el <title> tiene tags anidados)
        title_tag = (soup.title.string if soup.title else '') or ''
        if 'Security Check' in title_tag or 'Iniciar sesión' in title_tag:
            logger.warning(f"  Pagina de bloqueo/login en detalle {job_key}")
            self._consecutive_blocks += 1
            return None

        result = {}

        # --- HTML fields ---

        # Title (more reliable from detail page)
        h1 = soup.select_one('h1')
        if h1:
            result['titulo'] = h1.get_text(strip=True)

        # Description
        desc_el = soup.select_one('#jobDescriptionText')
        if desc_el:
            result['descripcion'] = desc_el.get_text(separator='\n', strip=True)

        # Company
        co_el = soup.select_one('[data-testid=inlineHeader-companyName]')
        if co_el:
            result['empresa'] = co_el.get_text(strip=True)

        # Location
        loc_el = soup.select_one('[data-testid=inlineHeader-companyLocation]')
        if not loc_el:
            loc_el = soup.select_one('[data-testid=job-location]')
        if loc_el:
            result['ubicacion'] = loc_el.get_text(strip=True)

        # Salary/Type from header
        sal_el = soup.select_one('#salaryInfoAndJobType')
        if sal_el:
            result['salario_tipo_raw'] = sal_el.get_text(strip=True)

        # --- JSON-LD structured data (best source) ---
        for script in soup.select('script[type="application/ld+json"]'):
            try:
                data = json.loads(script.string)
                if isinstance(data, dict) and data.get('@type') == 'JobPosting':
                    result['fecha_publicacion'] = data.get('datePosted')
                    result['fecha_expiracion'] = data.get('validThrough')

                    emp_type = data.get('employmentType')
                    if emp_type:
                        if isinstance(emp_type, list):
                            result['tipo_empleo'] = emp_type
                        else:
                            result['tipo_empleo'] = [emp_type]

                    # Salary
                    sal_data = data.get('baseSalary', {})
                    if sal_data and isinstance(sal_data, dict):
                        val = sal_data.get('value', {})
                        if isinstance(val, dict):
                            result['salario_min'] = val.get('minValue')
                            result['salario_max'] = val.get('maxValue')
                            result['salario_moneda'] = sal_data.get('currency')
                            result['salario_periodo'] = val.get('unitText')

                    # Company from JSON-LD
                    ho = data.get('hiringOrganization', {})
                    if ho and isinstance(ho, dict):
                        result['empresa_jsonld'] = ho.get('name')

                    # Location from JSON-LD
                    jl = data.get('jobLocation', {})
                    if isinstance(jl, dict):
                        addr = jl.get('address', {})
                        if isinstance(addr, dict):
                            result['localidad_jsonld'] = addr.get('addressLocality')
                            result['provincia_jsonld'] = addr.get('addressRegion')
                            result['pais_jsonld'] = addr.get('addressCountry')

                    break  # Found the JobPosting, no need to check more scripts
            except (json.JSONDecodeError, TypeError):
                continue

        return result

    # ----------------------------------------------------------------
    # MAIN: Scrape con keywords
    # ----------------------------------------------------------------

    def scrape_with_keywords(self, keywords: List[str],
                              location: str = "Argentina",
                              fromage: int = 14) -> List[Dict]:
        """
        Scrape usando lista de keywords.

        Args:
            keywords: Lista de terminos de busqueda
            location: Ubicacion
            fromage: Antiguedad maxima en dias

        Returns:
            Lista de ofertas con datos completos
        """
        logger.info("=" * 60)
        logger.info(f"Indeed Argentina - Scraping con {len(keywords)} keywords")
        logger.info(f"Location: {location}, fromage: {fromage} dias")
        logger.info("=" * 60)

        # Phase 1: Collect listings from all keywords
        all_listings = []
        blocked_count = 0

        for i, kw in enumerate(keywords, 1):
            if self._consecutive_blocks >= self._max_consecutive_blocks:
                # Antes de abortar, probar el siguiente fingerprint TLS
                if not self._rotate_fingerprint():
                    logger.error(f"  {self._max_consecutive_blocks} blocks consecutivos y "
                                  f"fingerprints agotados, abortando listado")
                    break

            logger.info(f"[{i}/{len(keywords)}] Keyword: '{kw}'")
            self._wait(self.delay)

            nuevas = self.search_keyword(kw, location, fromage)

            if nuevas:
                all_listings.extend(nuevas)
                logger.info(f"  {len(nuevas)} nuevas (total unicas: {len(self._seen_jks)})")
            else:
                if self._consecutive_blocks > 0:
                    blocked_count += 1
                    logger.info(f"  0 ofertas (block count: {self._consecutive_blocks})")
                else:
                    logger.info(f"  0 ofertas nuevas")

        logger.info(f"\nFase 1 completada: {len(all_listings)} ofertas unicas de "
                     f"{len(keywords)} keywords")

        if not all_listings:
            return []

        # Phase 2: Fetch details
        if not self.fetch_details:
            return all_listings

        logger.info(f"\nFase 2: Fetching detalles de {len(all_listings)} ofertas...")

        # El bloqueo del listado y el del detalle son INDEPENDIENTES (endpoints
        # distintos, limites distintos). Arrastrar el estado de la fase 1 hacia
        # aca hacia que una fase 1 que termino bloqueada abortara la fase 2 sin
        # intentar una sola ficha — y con la politica de no guardar mudas, eso
        # tiraba la corrida entera. Se entra a la fase 2 en limpio.
        self._consecutive_blocks = 0
        if self._fp_idx != 0:
            self._fp_idx = 0
            self.session = cffi_requests.Session(impersonate=self._fingerprints[0])
            logger.info(f"  Estado de bloqueo reseteado para la fase 2 "
                         f"(impersonate={self._fingerprints[0]})")

        ofertas_completas = []
        detail_errors = 0

        for i, listing in enumerate(all_listings, 1):
            if i % 50 == 0:
                logger.info(f"  Progreso: {i}/{len(all_listings)} "
                              f"(OK: {len(ofertas_completas)}, errors: {detail_errors})")

            if self._consecutive_blocks >= self._max_consecutive_blocks:
                # Mismo criterio que fase 1: rotar fingerprint antes de rendirse
                if not self._rotate_fingerprint():
                    # El detalle esta bloqueado de verdad (se agotaron todos los
                    # fingerprints intentando fichas). Se corta aca y se devuelve
                    # SOLO lo completo: las que faltan se descartan en vez de
                    # entrar mudas — jul/2026 metio 2.740 ofertas sin descripcion
                    # que el NLP no puede usar. Con fromage=14 hay ~2 semanas de
                    # margen para recuperar el resto en un reintento.
                    # Las que ya se acumularon sin descripcion (los 403 previos al
                    # corte) tambien se descartan: si se guardan, el proximo intento
                    # las ve como duplicadas y quedan mudas para siempre.
                    faltantes = len(all_listings) - i + 1
                    con_desc = [o for o in ofertas_completas if o.get('descripcion')]
                    mudas = len(ofertas_completas) - len(con_desc)
                    logger.error(f"  Detalle bloqueado (fingerprints agotados). CORTO aca: "
                                  f"guardo {len(con_desc)} ofertas completas, descarto "
                                  f"{mudas} ya bajadas sin descripcion + {faltantes} sin bajar.")
                    self.detalle_bloqueado = True
                    ofertas_completas = con_desc
                    break

            self._wait(self.detail_delay)
            detail = self.fetch_detail(listing['job_key'])

            if detail:
                self._consecutive_blocks = 0
                # Merge listing + detail (detail overwrites if present)
                merged = {**listing, **detail}
                merged['scrapeado_en'] = datetime.now().isoformat()
                merged['portal'] = 'indeed'
                ofertas_completas.append(merged)
            else:
                # 404 sueltos (oferta caida entre el listado y el detalle) son ruido
                # normal: esas si se guardan con lo que trajo el listado.
                detail_errors += 1
                listing['scrapeado_en'] = datetime.now().isoformat()
                listing['portal'] = 'indeed'
                listing['descripcion'] = None
                ofertas_completas.append(listing)

        logger.info(f"\nFase 2 completada:")
        logger.info(f"  Con detalle: {len(ofertas_completas) - detail_errors}")
        logger.info(f"  Sin detalle: {detail_errors}")
        logger.info(f"  Total: {len(ofertas_completas)}")

        return ofertas_completas

    def scrape_with_keywords_file(self, json_path: str,
                                    estrategia: str = "exhaustiva",
                                    location: str = "Argentina",
                                    fromage: int = 14,
                                    max_keywords: int = None,
                                    offset: int = 0) -> List[Dict]:
        """
        Scrape usando keywords de master_keywords.json.

        Args:
            json_path: Ruta al archivo de keywords
            estrategia: Nombre de la estrategia (default: exhaustiva)
            location: Ubicacion
            fromage: Antiguedad maxima en dias
            max_keywords: Limite de keywords (None = todos)
        """
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        keywords = data.get('estrategias', {}).get(estrategia, {}).get('keywords', [])
        if not keywords:
            logger.error(f"No se encontraron keywords en estrategia '{estrategia}'")
            return []

        # Filter empty strings
        keywords = [k for k in keywords if k.strip()]
        total = len(keywords)

        # El archivo esta ordenado alfabeticamente, asi que `keywords[:max]` sin
        # offset corre siempre de la A hacia adelante y nunca llega al resto del
        # abecedario (300 de 1072 = corta en "data-engineer"). Con offset se
        # puede recorrer el archivo por tramos entre corridas.
        if offset:
            keywords = keywords[offset:]

        if max_keywords:
            keywords = keywords[:max_keywords]

        desde = offset + 1
        hasta = offset + len(keywords)
        logger.info(f"Cargadas {len(keywords)} keywords de '{estrategia}' "
                     f"(tramo {desde}-{hasta} de {total})")
        if hasta < total:
            logger.warning(f"  Quedan {total - hasta} keywords sin consultar — "
                            f"proxima corrida con --offset {hasta}")
        return self.scrape_with_keywords(keywords, location, fromage)


if __name__ == '__main__':
    scraper = IndeedScraper(delay=2.0, detail_delay=2.0)
    # Test rapido: 5 keywords
    ofertas = scraper.scrape_with_keywords(
        ['vendedor', 'administrativo', 'programador', 'contador', 'ingeniero']
    )
    print(f"\nTotal ofertas: {len(ofertas)}")
    for o in ofertas[:5]:
        print(f"  [{o['job_key'][:8]}] {o['titulo']} - {o.get('empresa', '?')} "
              f"({o.get('ubicacion', '?')})")
        if o.get('descripcion'):
            print(f"    Desc: {len(o['descripcion'])} chars")
