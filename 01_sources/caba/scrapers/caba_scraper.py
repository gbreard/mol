"""
Portal de Trabajo Buenos Aires Ciudad - Scraper
================================================

Scraper para trabajo.buenosaires.gob.ar usando requests + BeautifulSoup.

Portal del Gobierno de la Ciudad Autonoma de Buenos Aires.
Datos MUY estructurados: industria, sector, vacantes, educacion, idiomas,
conocimientos IT, modalidad, etc.

Metodologia: HTML Scraping (NO requiere JavaScript)
Ofertas activas: ~10-50 (portal gobierno, chico pero con datos ricos)
Paginacion: offset=N (8 por pagina)
Detalle: /anuncios/{id} (campos estructurados)

Uso:
    scraper = CABAScraper()
    ofertas = scraper.scrape_all()
"""

import requests
from bs4 import BeautifulSoup
import re
import time
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CABAScraper:
    """Scraper para trabajo.buenosaires.gob.ar"""

    BASE_URL = "https://trabajo.buenosaires.gob.ar"
    LISTING_URL = f"{BASE_URL}/busqueda"
    PAGE_SIZE = 8  # Ofertas por pagina (fijo del portal)

    def __init__(self, delay: float = 1.5):
        """
        Args:
            delay: Segundos entre requests (respetar el servidor gobierno)
        """
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'es-AR,es;q=0.9',
            'Referer': self.BASE_URL,
        })
        logger.info(f"CABAScraper inicializado (delay={delay}s)")

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
    # LISTING: Obtener IDs de ofertas activas
    # ----------------------------------------------------------------

    def scrape_listing_page(self, offset: int = 0) -> List[Dict]:
        """
        Scrapea una pagina del listado.

        Returns:
            Lista de dicts con {id, titulo, empresa, ubicacion, fecha_texto, url}
        """
        url = f"{self.LISTING_URL}?job_posting_search[position]=&offset={offset}"
        soup = self._fetch(url)
        if not soup:
            return []

        ofertas = []
        cards = soup.select('div.card-trabajo')
        for card in cards:
            try:
                link = card.select_one('a[href^="/anuncios/"]')
                if not link:
                    continue

                href = link.get('href', '')
                # Extraer ID numerico del href: /anuncios/22230 o /anuncios/22230-Titulo
                match = re.match(r'/anuncios/(\d+)', href)
                if not match:
                    continue

                oferta_id = int(match.group(1))
                titulo = card.select_one('h4.busqueda')
                empresa = card.select_one('p.empresa')
                ubicacion = card.select_one('p.location')
                fecha = card.select_one('p.small')
                descripcion = card.select_one('p.description')

                ofertas.append({
                    'id': oferta_id,
                    'titulo': titulo.get_text(strip=True) if titulo else None,
                    'empresa': empresa.get_text(strip=True) if empresa else None,
                    'ubicacion': ubicacion.get_text(strip=True) if ubicacion else None,
                    'fecha_texto': fecha.get_text(strip=True) if fecha else None,
                    'descripcion_preview': descripcion.get_text(strip=True)[:200] if descripcion else None,
                    'url': f"{self.BASE_URL}{href}",
                })
            except Exception as e:
                logger.warning(f"Error parseando card: {e}")
                continue

        return ofertas

    def scrape_all_listings(self) -> List[Dict]:
        """
        Obtiene TODAS las ofertas activas paginando con offset.

        Returns:
            Lista completa de ofertas del listado
        """
        all_ofertas = []
        offset = 0

        while True:
            logger.info(f"Listado offset={offset}...")
            page_ofertas = self.scrape_listing_page(offset)

            if not page_ofertas:
                logger.info(f"Sin resultados en offset={offset}, fin del listado")
                break

            all_ofertas.extend(page_ofertas)
            logger.info(f"  {len(page_ofertas)} ofertas encontradas (total: {len(all_ofertas)})")

            # Si devolvio menos que PAGE_SIZE, es la ultima pagina
            if len(page_ofertas) < self.PAGE_SIZE:
                break

            offset += self.PAGE_SIZE
            time.sleep(self.delay)

        logger.info(f"Total ofertas en listado: {len(all_ofertas)}")
        return all_ofertas

    # ----------------------------------------------------------------
    # DETAIL: Parsear pagina de detalle completa
    # ----------------------------------------------------------------

    def _extract_field(self, soup: BeautifulSoup, label: str) -> Optional[str]:
        """Extrae un campo por su label <strong>."""
        for strong in soup.find_all('strong'):
            if label in strong.get_text():
                parent = strong.parent
                if parent:
                    text = parent.get_text(strip=True)
                    # Quitar el label del texto
                    text = text.replace(strong.get_text(), '').strip()
                    # Limpiar ":" al inicio
                    text = text.lstrip(':').strip()
                    return text if text else None
        return None

    def _extract_section_text(self, soup: BeautifulSoup, heading: str) -> Optional[str]:
        """Extrae texto de una seccion por su <h3>."""
        for h3 in soup.find_all('h3'):
            if heading.lower() in h3.get_text().lower():
                # Buscar el siguiente <p> hermano
                next_p = h3.find_next_sibling('p')
                if next_p:
                    # Reemplazar <br> con newlines
                    for br in next_p.find_all('br'):
                        br.replace_with('\n')
                    text = next_p.get_text()
                    # Limpiar multiples newlines y espacios
                    text = re.sub(r'\n{3,}', '\n\n', text)
                    text = re.sub(r' {2,}', ' ', text)
                    return text.strip()
        return None

    def _extract_list_items(self, soup: BeautifulSoup, after_label: str) -> List[str]:
        """Extrae items de una lista <ul> despues de un label."""
        for strong in soup.find_all('strong'):
            if after_label in strong.get_text():
                ul = strong.find_next('ul')
                if ul:
                    return [li.get_text(strip=True) for li in ul.find_all('li')]
        return []

    def _parse_fecha_relativa(self, texto: str) -> Optional[str]:
        """
        Parsea textos de fecha relativa a ISO.
        Ejemplos: "Hace 7 dias", "Hace 14 dias", "Hace 23 dias"
        """
        if not texto:
            return None

        texto = texto.lower().strip()
        now = datetime.now()

        m = re.search(r'hace\s+(\d+)\s+d[ií]as?', texto)
        if m:
            dias = int(m.group(1))
            fecha = now - timedelta(days=dias)
            return fecha.strftime('%Y-%m-%d')

        m = re.search(r'hace\s+(\d+)\s+horas?', texto)
        if m:
            return now.strftime('%Y-%m-%d')

        if 'hoy' in texto or 'ahora' in texto:
            return now.strftime('%Y-%m-%d')

        if 'ayer' in texto:
            return (now - timedelta(days=1)).strftime('%Y-%m-%d')

        # Fecha explícita DD/MM/YYYY
        m = re.search(r'(\d{1,2})/(\d{1,2})/(\d{4})', texto)
        if m:
            try:
                day, month, year = int(m.group(1)), int(m.group(2)), int(m.group(3))
                return f"{year:04d}-{month:02d}-{day:02d}"
            except ValueError:
                pass

        return None

    def scrape_detail(self, anuncio_id: int) -> Optional[Dict]:
        """
        Scrapea la pagina de detalle de una oferta.

        Args:
            anuncio_id: ID del anuncio (ej: 22230)

        Returns:
            Dict con todos los campos estructurados, o None si no existe
        """
        url = f"{self.BASE_URL}/anuncios/{anuncio_id}"
        soup = self._fetch(url)
        if not soup:
            return None

        # Verificar que no sea 404 (el servidor devuelve 200 con mensaje)
        not_found = soup.find(string=re.compile('No encontramos la p.gina'))
        if not_found:
            return None

        # --- Campos principales ---
        titulo_el = soup.select_one('h1.job-post-title')
        titulo = titulo_el.get_text(strip=True) if titulo_el else None

        empresa = self._extract_field(soup, 'Empresa')
        fecha_pub_texto = self._extract_field(soup, 'Fecha de publicación')

        # ID empresa desde link
        id_empresa = None
        empresa_link = soup.select_one('a[href^="/empresas/"]')
        if empresa_link:
            m = re.search(r'/empresas/(\d+)', empresa_link.get('href', ''))
            if m:
                id_empresa = int(m.group(1))

        # --- Segmento de info ---
        lugar_trabajo = self._extract_field(soup, 'Lugar de trabajo')
        vacantes_text = self._extract_field(soup, 'Vacantes')
        vacantes = None
        if vacantes_text:
            try:
                vacantes = int(vacantes_text)
            except ValueError:
                pass

        modalidad = self._extract_field(soup, 'Modalidad de Trabajo')
        industria = self._extract_field(soup, 'Industria')
        disponibilidad = self._extract_field(soup, 'Disponibilidad Horaria')
        sector = self._extract_field(soup, 'Sector')

        # --- Secciones de texto ---
        descripcion = self._extract_section_text(soup, 'Resumen del Puesto')
        beneficios = self._extract_section_text(soup, 'Beneficios')

        # --- Detalle (direccion, dias, horario) ---
        lugar_detalle = self._extract_field(soup, 'Lugar de Trabajo')
        dias_laborables = self._extract_field(soup, 'Dias Laborables')
        horario = self._extract_field(soup, 'Horario de Entrada y Salida')

        # --- Requisitos ---
        experiencia = self._extract_field(soup, 'Experiencia Excluyente')
        residencia = self._extract_field(soup, 'Lugar de Residencia')
        estudios = self._extract_field(soup, 'Grado de Estudios')
        idiomas = self._extract_list_items(soup, 'Idiomas')

        # --- Conocimientos informatica ---
        internet = self._extract_field(soup, 'Internet')
        office = self._extract_field(soup, 'Paquete Office')
        sistemas_contables = self._extract_field(soup, 'Sistemas Contables')
        programacion = self._extract_field(soup, 'Programación')
        base_datos = self._extract_field(soup, 'Base de Datos')

        # --- Parsear fecha ---
        fecha_iso = None
        if fecha_pub_texto:
            # Fecha en detalle viene como DD/MM/YYYY
            m = re.search(r'(\d{1,2})/(\d{1,2})/(\d{4})', fecha_pub_texto)
            if m:
                try:
                    day, month, year = int(m.group(1)), int(m.group(2)), int(m.group(3))
                    fecha_iso = f"{year:04d}-{month:02d}-{day:02d}"
                except ValueError:
                    pass

        return {
            # Identificacion
            'id': anuncio_id,
            'id_empresa': id_empresa,
            'url': url,

            # Basico
            'titulo': titulo,
            'empresa': empresa,
            'fecha_publicacion': fecha_iso,
            'fecha_publicacion_raw': fecha_pub_texto,

            # Ubicacion y condiciones
            'lugar_trabajo': lugar_trabajo,
            'lugar_detalle': lugar_detalle,
            'vacantes': vacantes,
            'modalidad': modalidad,
            'industria': industria,
            'sector': sector,
            'disponibilidad': disponibilidad,
            'dias_laborables': dias_laborables,
            'horario': horario,

            # Contenido
            'descripcion': descripcion,
            'beneficios': beneficios,

            # Requisitos
            'experiencia_excluyente': experiencia,
            'residencia': residencia,
            'estudios': estudios,
            'idiomas': idiomas,

            # IT
            'internet': internet,
            'paquete_office': office,
            'sistemas_contables': sistemas_contables,
            'programacion': programacion,
            'base_datos': base_datos,

            # Metadata
            'scrapeado_en': datetime.now().isoformat(),
            'portal': 'caba',
        }

    # ----------------------------------------------------------------
    # MAIN: Scrape completo (listado + detalles)
    # ----------------------------------------------------------------

    def scrape_all(self, fetch_details: bool = True) -> List[Dict]:
        """
        Scrape completo: obtiene listado y luego detalle de cada oferta.

        Args:
            fetch_details: Si True, hace fetch del detalle de cada oferta.
                          Si False, solo devuelve datos del listado.

        Returns:
            Lista de ofertas con datos completos
        """
        logger.info("=" * 60)
        logger.info("CABA Portal de Trabajo - Scraping completo")
        logger.info("=" * 60)

        # Paso 1: Obtener listado
        listings = self.scrape_all_listings()
        if not listings:
            logger.warning("No se encontraron ofertas en el listado")
            return []

        if not fetch_details:
            return listings

        # Paso 2: Fetch detalle de cada oferta
        ofertas_completas = []
        for i, listing in enumerate(listings, 1):
            logger.info(f"[{i}/{len(listings)}] Detalle ID {listing['id']}: {listing['titulo']}")
            time.sleep(self.delay)

            detail = self.scrape_detail(listing['id'])
            if detail:
                ofertas_completas.append(detail)
            else:
                logger.warning(f"  No se pudo obtener detalle de ID {listing['id']}")

        logger.info(f"\nResultado: {len(ofertas_completas)}/{len(listings)} ofertas con detalle")
        return ofertas_completas


if __name__ == '__main__':
    import json as _json

    scraper = CABAScraper(delay=1.5)
    ofertas = scraper.scrape_all()

    print(f"\n{'=' * 60}")
    print(f"Total ofertas scrapeadas: {len(ofertas)}")
    for o in ofertas:
        print(f"  [{o['id']}] {o['titulo']} - {o['empresa']} ({o['lugar_trabajo']})")

    # Guardar JSON
    with open('caba_ofertas.json', 'w', encoding='utf-8') as f:
        _json.dump(ofertas, f, ensure_ascii=False, indent=2)
    print(f"\nGuardado en caba_ofertas.json")
