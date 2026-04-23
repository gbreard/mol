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
        # chrome131 (2026-04-23): el alias 'chrome' equivale a chrome110/116 que Cloudflare ya detecta.
        # Fingerprints chrome120+ pasan el challenge. Si Cloudflare volviera a bloquear, probar chrome124/firefox.
        self.session = cffi_requests.Session(impersonate='chrome131')
        self._seen_jks: Set[str] = set()
        self._consecutive_blocks = 0
        self._max_consecutive_blocks = 5  # Parar si 5 keywords seguidos dan 403
        logger.info(f"IndeedScraper inicializado (delay={delay}s, detail_delay={detail_delay}s, "
                     f"fetch_details={fetch_details})")

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
        try:
            r = self.session.get(url,
                                  headers={'Accept-Language': 'es-AR,es;q=0.9'},
                                  timeout=30)
            if r.status_code != 200:
                return None
        except Exception as e:
            logger.error(f"  Error fetching detail {job_key}: {e}")
            return None

        soup = BeautifulSoup(r.text, 'html.parser')

        # Check for blocks
        title_tag = soup.title.string if soup.title else ''
        if 'Security Check' in title_tag or 'Iniciar sesión' in title_tag:
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
                logger.error(f"  {self._max_consecutive_blocks} blocks consecutivos, "
                              f"abortando listado")
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
        ofertas_completas = []
        detail_errors = 0

        for i, listing in enumerate(all_listings, 1):
            if i % 50 == 0:
                logger.info(f"  Progreso: {i}/{len(all_listings)} "
                              f"(OK: {len(ofertas_completas)}, errors: {detail_errors})")

            self._wait(self.detail_delay)

            detail = self.fetch_detail(listing['job_key'])
            if detail:
                # Merge listing + detail (detail overwrites if present)
                merged = {**listing, **detail}
                merged['scrapeado_en'] = datetime.now().isoformat()
                merged['portal'] = 'indeed'
                ofertas_completas.append(merged)
            else:
                detail_errors += 1
                # Keep listing data even without detail
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
                                    max_keywords: int = None) -> List[Dict]:
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

        if max_keywords:
            keywords = keywords[:max_keywords]

        logger.info(f"Cargadas {len(keywords)} keywords de '{estrategia}'")
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
