"""
Portal Empleo Nacional - Scraper
================================

Scraper para portalempleo.gob.ar (Ministerio de Capital Humano - Secretaría de
Trabajo de la Nación).

Portal del gobierno nacional con ofertas de TODO el país.
Datos estructurados: vacantes, tareas, beneficios, ubicación, jornada/horario,
experiencia, estudios.

Metodología: HTML Scraping server-rendered (NO requiere JavaScript).

MIGRACIÓN ~2026-09-15 (rewrite 2026-10-07, rama fix/portalempleo-sitio-migrado):
  - Rutas a minúsculas+guion: /ofertas-laborales (listado) y
    /ofertas-laborales/details/{uuid} (detalle). Antes: /OfertasLaborales[...].
  - Markup nuevo con clases `pe-*` (antes: iconos fa-* + texto plano por regex).
  - Listado: tarjeta = `a.pe-oferta-card` (ACOTADO — el HTML trae UUID de
    relacionados/destacados que NO son ofertas; el selector viejo los inflaba).
  - Contador: "Mostrando 1–10 de N ofertas" (antes: "Se encontraron N resultados").
  - UUID v4 CONSERVADOS en la migración (verificado: overlap 103/265 con BD) →
    la fórmula id_oferta = 7e9 + crc32(uuid) sigue vinculando las viejas.

Paginación: ?page-number=N (10 por página) — SIGUE funcionando.

Uso:
    scraper = PortalEmpleoScraper()
    ofertas = scraper.scrape_all()
"""

import requests
from bs4 import BeautifulSoup
import re
import time
import logging
from datetime import datetime
from typing import List, Dict, Optional

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def _txt(el) -> Optional[str]:
    """Texto limpio de un elemento bs4, o None."""
    if not el:
        return None
    t = el.get_text(' ', strip=True)
    t = re.sub(r'\s+', ' ', t).strip()
    return t or None


class PortalEmpleoScraper:
    """Scraper para portalempleo.gob.ar (sitio migrado ~2026-09)."""

    BASE_URL = "https://www.portalempleo.gob.ar"
    LISTING_URL = f"{BASE_URL}/ofertas-laborales"
    PAGE_SIZE = 10  # Ofertas por pagina (fijo del portal)

    # Regex del UUID en el href del detalle (case-insensitive sobre la ruta nueva)
    _UUID_RE = re.compile(
        r'/ofertas-laborales/details/([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-'
        r'[0-9a-f]{4}-[0-9a-f]{12})', re.I)

    def __init__(self, delay: float = 1.5):
        self.delay = delay
        self.ultimo_total = None       # contador del sitio en la última corrida (§11.7)
        self.ultimo_n_listado = None   # nº de ofertas en el listado (pre-detalle)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'es-AR,es;q=0.9',
            'Referer': self.BASE_URL,
        })
        logger.info(f"PortalEmpleoScraper inicializado (delay={delay}s)")

    def _fetch(self, url: str) -> Optional[BeautifulSoup]:
        """Fetch URL y devuelve BeautifulSoup, None si falla."""
        try:
            resp = self.session.get(url, timeout=30)
            if resp.status_code == 200:
                return BeautifulSoup(resp.text, 'html.parser')
            elif resp.status_code == 404:
                return None
            else:
                logger.warning(f"HTTP {resp.status_code} para {url}")
                return None
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            return None

    # ----------------------------------------------------------------
    # LISTING
    # ----------------------------------------------------------------

    def scrape_listing_page(self, page: int = 1) -> List[Dict]:
        """Scrapea una página del listado. Devuelve datos básicos por oferta."""
        url = f"{self.LISTING_URL}?page-number={page}"
        soup = self._fetch(url)
        if not soup:
            return []

        ofertas = []
        # ACOTADO: solo las tarjetas de oferta. El HTML trae otros UUID
        # (relacionados/destacados) que NO son ofertas — por eso no se barre
        # todo UUID del HTML, sino el anchor de tarjeta.
        for card in soup.select('a.pe-oferta-card'):
            try:
                href = card.get('href', '') or ''
                m = self._UUID_RE.search(href)
                if not m:
                    continue
                uuid = m.group(1).lower()

                time_el = card.select_one('time.pe-oferta-fecha')
                fecha_iso = time_el.get('datetime') if time_el else None

                ofertas.append({
                    'uuid': uuid,
                    'titulo': _txt(card.select_one('h3.pe-oferta-puesto')),
                    'empresa': _txt(card.select_one('.pe-oferta-empresa')),
                    'ubicacion': (_txt(card.select_one('.pe-oferta-loc-texto'))
                                  or _txt(card.select_one('.pe-oferta-loc'))),
                    'disponibilidad': _txt(card.select_one('.pe-oferta-badge--modalidad')),
                    'fecha_texto': _txt(time_el),
                    'fecha_iso': fecha_iso,
                    'descripcion_preview': (_txt(card.select_one('.pe-oferta-desc')) or '')[:300] or None,
                    'url': href if href.startswith('http') else f"{self.BASE_URL}{href}",
                })
            except Exception as e:
                logger.warning(f"Error parseando oferta en listado: {e}")
                continue

        return ofertas

    def get_total_results(self) -> int:
        """Total de ofertas que reporta el sitio (contador). 0 si no se encuentra.

        Textos nuevos: "Mostrando 1–10 de 169 ofertas" / "169 ofertas".
        De este número depende el flag `completa` de corridas_scraping, que el
        motor de ciclo de vida usa para confirmar bajas de Portal Empleo (§11.7).
        """
        soup = self._fetch(self.LISTING_URL)
        if not soup:
            return 0
        text = soup.get_text(' ', strip=True)
        # Preferido: "...de N ofertas" (de "Mostrando 1–10 de N ofertas")
        m = re.search(r'de\s+(\d+)\s+ofertas', text)
        if m:
            return int(m.group(1))
        # Fallback: "N ofertas" (p.ej. encabezado "169 ofertas")
        m = re.search(r'(\d+)\s+ofertas', text)
        return int(m.group(1)) if m else 0

    def scrape_all_listings(self) -> List[Dict]:
        """Obtiene TODAS las ofertas del listado paginando (dedup por UUID)."""
        all_ofertas, page, seen = [], 1, set()
        while True:
            logger.info(f"Listado pagina {page}...")
            page_ofertas = self.scrape_listing_page(page)
            if not page_ofertas:
                logger.info(f"Sin resultados en pagina {page}, fin del listado")
                break
            nuevas = 0
            for o in page_ofertas:
                if o['uuid'] not in seen:
                    seen.add(o['uuid']); all_ofertas.append(o); nuevas += 1
            logger.info(f"  {nuevas} ofertas nuevas (total: {len(all_ofertas)})")
            if nuevas == 0:
                logger.info("Sin ofertas nuevas, fin del listado")
                break
            page += 1
            time.sleep(self.delay)
        logger.info(f"Total ofertas en listado: {len(all_ofertas)}")
        return all_ofertas

    # ----------------------------------------------------------------
    # DETAIL
    # ----------------------------------------------------------------

    def _parse_fecha(self, texto: str) -> Optional[str]:
        """Parsea fecha DD/MM/YYYY a YYYY-MM-DD (fallback si no hay <time datetime>)."""
        if not texto:
            return None
        m = re.search(r'(\d{1,2})/(\d{1,2})/(\d{4})', texto.strip())
        if m:
            try:
                d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
                return f"{y:04d}-{mo:02d}-{d:02d}"
            except ValueError:
                pass
        return None

    def _secciones_h2(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Mapea cada <h2> (Resumen del puesto, Tareas principales, Beneficios...)
        al texto de sus hermanos siguientes hasta el próximo <h2>."""
        out = {}
        for h in soup.find_all('h2'):
            key = h.get_text(strip=True).lower()
            parts = []
            for sib in h.find_next_siblings():
                if getattr(sib, 'name', None) == 'h2':
                    break
                t = _txt(sib)
                if t:
                    parts.append(t)
            val = ' '.join(parts).strip()
            if val:
                out[key] = val
        return out

    def scrape_detail(self, uuid: str) -> Optional[Dict]:
        """Scrapea la página de detalle. None si no existe."""
        url = f"{self.BASE_URL}/ofertas-laborales/details/{uuid}"
        soup = self._fetch(url)
        if not soup:
            return None

        titulo = _txt(soup.select_one('h1'))
        empresa = _txt(soup.select_one('.pe-detalle-empresa'))
        modalidad = _txt(soup.select_one('.pe-oferta-badge--modalidad'))

        # Fecha: atributo datetime del <time> (absoluto); texto como raw.
        time_el = soup.select_one('time')
        fecha_iso = time_el.get('datetime') if time_el else None
        fecha_texto = _txt(time_el)
        if not fecha_iso:
            fecha_iso = self._parse_fecha(fecha_texto)

        # Ubicación: de pe-detalle-meta "LOC · LOC · <fecha>" → se quita la fecha.
        ubicacion = None
        meta = soup.select_one('.pe-detalle-meta')
        if meta:
            partes = [p.strip() for p in _txt(meta).split('·') if p.strip()]
            # el último token es la fecha relativa ("hoy", "hace 3 días")
            if partes and (partes[-1] == (fecha_texto or '') or
                           re.search(r'\bhoy\b|hace|ayer|d[ií]as?', partes[-1], re.I)):
                partes = partes[:-1]
            ubicacion = ', '.join(partes) or None

        # Stats (vacantes / días / horario) — el label va como sufijo del texto.
        vacantes = dias = h_ent = h_sal = None
        for s in soup.select('.pe-detalle-stat'):
            t = _txt(s) or ''
            low = t.lower()
            if 'vacante' in low:
                mm = re.search(r'(\d+)', t)
                if mm:
                    vacantes = int(mm.group(1))
            elif 'jornada' in low:
                dias = re.sub(r'\s*jornada\s*$', '', t, flags=re.I).strip() or None
            elif 'horario' in low:
                mm = re.search(r'(\d{1,2}:\d{2})\s*a\s*(\d{1,2}:\d{2})', t)
                if mm:
                    h_ent, h_sal = mm.group(1), mm.group(2)

        # Requisitos (tabla dt/dd): Experiencia, Estudios, Conocimientos informáticos
        req = {}
        for row in soup.select('.pe-detalle-tabla-row'):
            k = _txt(row.select_one('.pe-detalle-tabla-label'))
            v = _txt(row.select_one('.pe-detalle-tabla-valor'))
            if k:
                req[k.lower()] = v

        # Secciones por <h2>
        sec = self._secciones_h2(soup)

        def sec_get(*keys):
            for k in keys:
                for kk, vv in sec.items():
                    if k in kk:
                        return vv
            return None

        return {
            'uuid': uuid,
            'url': url,
            'titulo': titulo,
            'empresa': empresa,
            'fecha_publicacion': fecha_iso,
            'fecha_publicacion_raw': fecha_texto,
            'ubicacion': ubicacion,
            'lugar_trabajo': None,  # el sitio nuevo no expone una ubicación de detalle aparte
            'vacantes': vacantes,
            'disponibilidad': modalidad,
            'salario': sec_get('salario'),  # no visible en el markup nuevo; None salvo que aparezca
            'resumen': sec_get('resumen'),
            'tareas': sec_get('tareas'),
            'beneficios': sec_get('beneficios'),
            'dias_laborables': dias,
            'horario_entrada': h_ent,
            'horario_salida': h_sal,
            'experiencia': req.get('experiencia'),
            'estudios': req.get('estudios'),
            'conocimientos_informaticos': req.get('conocimientos informáticos'),
            'scrapeado_en': datetime.now().isoformat(),
            'portal': 'portalempleo',
        }

    # ----------------------------------------------------------------
    # MAIN
    # ----------------------------------------------------------------

    def scrape_all(self, fetch_details: bool = True, max_pages: int = None) -> List[Dict]:
        """Scrape completo: listado + detalles."""
        logger.info("=" * 60)
        logger.info("Portal Empleo Nacional - Scraping completo")
        logger.info("=" * 60)

        total = self.get_total_results()
        self.ultimo_total = total  # contador del sitio (completitud §11.7)
        logger.info(f"Total ofertas reportadas por el portal: {total}")
        time.sleep(self.delay)

        all_ofertas, page, seen = [], 1, set()
        while True:
            if max_pages and page > max_pages:
                logger.info(f"Limite de {max_pages} paginas alcanzado")
                break
            logger.info(f"Listado pagina {page}...")
            page_ofertas = self.scrape_listing_page(page)
            if not page_ofertas:
                break
            nuevas = 0
            for o in page_ofertas:
                if o['uuid'] not in seen:
                    seen.add(o['uuid']); all_ofertas.append(o); nuevas += 1
            logger.info(f"  {nuevas} ofertas nuevas (total: {len(all_ofertas)})")
            if nuevas == 0:
                break
            page += 1
            time.sleep(self.delay)

        logger.info(f"Total ofertas en listado: {len(all_ofertas)}")
        self.ultimo_n_listado = len(all_ofertas)  # pre-detalle, para completitud §11.7

        if not fetch_details:
            return all_ofertas

        ofertas_completas = []
        for i, listing in enumerate(all_ofertas, 1):
            logger.info(f"[{i}/{len(all_ofertas)}] Detalle: {(listing.get('titulo') or '')[:50]}")
            time.sleep(self.delay)
            detail = self.scrape_detail(listing['uuid'])
            if detail:
                # completar con lo del listado si el detalle no lo trajo
                for k in ('titulo', 'empresa', 'ubicacion', 'disponibilidad'):
                    if not detail.get(k) and listing.get(k):
                        detail[k] = listing[k]
                ofertas_completas.append(detail)
            else:
                logger.warning(f"  No se pudo obtener detalle de {listing['uuid']}")

        logger.info(f"\nResultado: {len(ofertas_completas)}/{len(all_ofertas)} ofertas con detalle")
        return ofertas_completas


if __name__ == '__main__':
    import json as _json
    scraper = PortalEmpleoScraper(delay=1.0)
    ofertas = scraper.scrape_all(max_pages=2)
    print(f"\n{'=' * 60}")
    print(f"Total ofertas scrapeadas: {len(ofertas)}")
    for o in ofertas[:5]:
        print(f"  [{o['uuid'][:8]}] {o['titulo']} - {o['empresa']} ({o.get('ubicacion', '')})")
    with open('portalempleo_ofertas_test.json', 'w', encoding='utf-8') as f:
        _json.dump(ofertas, f, ensure_ascii=False, indent=2)
    print("\nGuardado en portalempleo_ofertas_test.json")
