"""
Portal Empleo Nacional - Scraper
================================

Scraper para portalempleo.gob.ar (Ministerio de Trabajo de la Nacion).

Portal del gobierno nacional con ofertas de TODO el pais.
Datos estructurados: vacantes, salario, tareas, beneficios, ubicacion
completa (provincia/localidad/direccion), dias, horario, experiencia, estudios.

Metodologia: HTML Scraping (NO requiere JavaScript)
Ofertas activas: ~105 (variable; el contador del sitio manda. La cifra
histórica de ~400-500 quedó desactualizada — verificado 2026-09-01)
Paginacion: page-number=N (10 por pagina)
Detalle: /OfertasLaborales/Details/{uuid}

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


class PortalEmpleoScraper:
    """Scraper para portalempleo.gob.ar"""

    BASE_URL = "https://portalempleo.gob.ar"
    LISTING_URL = f"{BASE_URL}/OfertasLaborales"
    PAGE_SIZE = 10  # Ofertas por pagina (fijo del portal)

    def __init__(self, delay: float = 1.5):
        """
        Args:
            delay: Segundos entre requests
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
    # LISTING: Obtener ofertas del listado paginado
    # ----------------------------------------------------------------

    def scrape_listing_page(self, page: int = 1) -> List[Dict]:
        """
        Scrapea una pagina del listado.

        Returns:
            Lista de dicts con datos basicos de cada oferta
        """
        url = f"{self.LISTING_URL}?page-number={page}"
        soup = self._fetch(url)
        if not soup:
            return []

        ofertas = []
        # Cada oferta esta en un div.row seguido de <hr/>
        # El link "Ver Oferta" contiene el UUID
        links = soup.select('a.comp-button-ciudadanos[href*="/OfertasLaborales/Details/"]')

        for link in links:
            try:
                href = link.get('href', '')
                # Extraer UUID del href
                m = re.search(r'/OfertasLaborales/Details/([a-f0-9-]{36})', href)
                if not m:
                    continue

                uuid = m.group(1)

                # Navegar al row padre para extraer datos del listado
                row = link.find_parent('div', class_='row')
                if not row:
                    continue

                # Titulo
                titulo_el = row.select_one('h5')
                titulo = titulo_el.get_text(strip=True) if titulo_el else None

                # Empresa
                empresa_el = row.select_one('i.fa-building')
                empresa = None
                if empresa_el and empresa_el.parent:
                    empresa = empresa_el.parent.get_text(strip=True)

                # Ubicacion
                ubicacion_el = row.select_one('i.fa-map-marker-alt')
                ubicacion = None
                if ubicacion_el and ubicacion_el.parent:
                    ubicacion = ubicacion_el.parent.get_text(strip=True)

                # Disponibilidad
                disponibilidades = []
                for clock in row.select('i.fa-clock'):
                    if clock.parent:
                        disp = clock.parent.get_text(strip=True)
                        if disp:
                            disponibilidades.append(disp)

                # Fecha (float-right en el row)
                fecha_el = row.select_one('div.float-right')
                fecha_texto = fecha_el.get_text(strip=True) if fecha_el else None

                # Descripcion preview (p.lead)
                desc_el = row.select_one('p.lead')
                desc_preview = desc_el.get_text(strip=True)[:300] if desc_el else None

                ofertas.append({
                    'uuid': uuid,
                    'titulo': titulo,
                    'empresa': empresa,
                    'ubicacion': ubicacion,
                    'disponibilidad': ', '.join(disponibilidades) if disponibilidades else None,
                    'fecha_texto': fecha_texto,
                    'descripcion_preview': desc_preview,
                    'url': f"{self.BASE_URL}{href}",
                })
            except Exception as e:
                logger.warning(f"Error parseando oferta en listado: {e}")
                continue

        return ofertas

    def get_total_results(self) -> int:
        """Obtiene el total de resultados de la primera pagina."""
        soup = self._fetch(self.LISTING_URL)
        if not soup:
            return 0

        # "Se encontraron 427 resultados en 0,00 segundos"
        text = soup.get_text()
        m = re.search(r'Se encontraron (\d+) resultados', text)
        if m:
            return int(m.group(1))
        return 0

    def scrape_all_listings(self) -> List[Dict]:
        """
        Obtiene TODAS las ofertas paginando.

        Returns:
            Lista completa de ofertas del listado
        """
        all_ofertas = []
        page = 1
        seen_uuids = set()

        while True:
            logger.info(f"Listado pagina {page}...")
            page_ofertas = self.scrape_listing_page(page)

            if not page_ofertas:
                logger.info(f"Sin resultados en pagina {page}, fin del listado")
                break

            # Dedup por UUID (por si hay overlap entre paginas)
            nuevas = 0
            for o in page_ofertas:
                if o['uuid'] not in seen_uuids:
                    seen_uuids.add(o['uuid'])
                    all_ofertas.append(o)
                    nuevas += 1

            logger.info(f"  {nuevas} ofertas nuevas (total: {len(all_ofertas)})")

            if nuevas == 0:
                logger.info("Sin ofertas nuevas, fin del listado")
                break

            page += 1
            time.sleep(self.delay)

        logger.info(f"Total ofertas en listado: {len(all_ofertas)}")
        return all_ofertas

    # ----------------------------------------------------------------
    # DETAIL: Parsear pagina de detalle
    # ----------------------------------------------------------------

    def _get_detail_field(self, soup: BeautifulSoup, label: str) -> Optional[str]:
        """
        Extrae un campo del detalle buscando por texto de label.
        El formato es: label en texto seguido del valor.
        """
        # Los campos estan como texto plano en secciones
        for el in soup.find_all(['dt', 'b', 'strong', 'h6']):
            if label.lower() in el.get_text().lower():
                # Buscar el siguiente sibling o dd
                next_el = el.find_next_sibling()
                if next_el:
                    return next_el.get_text(strip=True)
        return None

    def _parse_fecha(self, texto: str) -> Optional[str]:
        """Parsea fecha DD/MM/YYYY a YYYY-MM-DD."""
        if not texto:
            return None
        m = re.search(r'(\d{1,2})/(\d{1,2})/(\d{4})', texto.strip())
        if m:
            try:
                day, month, year = int(m.group(1)), int(m.group(2)), int(m.group(3))
                return f"{year:04d}-{month:02d}-{day:02d}"
            except ValueError:
                pass
        return None

    def scrape_detail(self, uuid: str) -> Optional[Dict]:
        """
        Scrapea la pagina de detalle de una oferta.

        Args:
            uuid: UUID de la oferta

        Returns:
            Dict con campos estructurados, o None si no existe
        """
        url = f"{self.BASE_URL}/OfertasLaborales/Details/{uuid}"
        soup = self._fetch(url)
        if not soup:
            return None

        # --- Titulo y Empresa ---
        titulo_el = soup.select_one('h3.text-capitalize')
        if not titulo_el:
            # Fallback: primer h3 despues del header
            titulo_el = soup.select_one('div.container-fluid h3')
        titulo = titulo_el.get_text(strip=True) if titulo_el else None

        # Empresa: despues de fa-building
        empresa = None
        empresa_icon = soup.select_one('i.fa-building')
        if empresa_icon and empresa_icon.parent:
            empresa = empresa_icon.parent.get_text(strip=True)

        # Fecha: float-right en la pagina
        fecha_texto = None
        fecha_el = soup.select_one('div.float-right')
        if fecha_el:
            fecha_texto = fecha_el.get_text(strip=True)

        # Ubicacion del listado (header de la pagina)
        ubicacion = None
        map_icon = soup.select_one('i.fa-map-marker-alt')
        if map_icon and map_icon.parent:
            ubicacion = map_icon.parent.get_text(strip=True)

        # --- Extraer secciones por headers ---
        # Los campos estan organizados en secciones con headers h2
        all_text = soup.get_text()

        # Vacantes
        vacantes = None
        m = re.search(r'Vacantes\s*(\d+)', all_text)
        if m:
            vacantes = int(m.group(1))

        # Disponibilidad
        disponibilidad = None
        m = re.search(r'Disponibilidad horaria\s*(.*?)(?:Salario|$)', all_text, re.DOTALL)
        if m:
            disponibilidad = m.group(1).strip()
            # Limpiar
            disponibilidad = re.sub(r'\s+', ' ', disponibilidad).strip()

        # Salario
        salario = None
        m = re.search(r'Salario\s*(.*?)(?:Tareas|Resumen|$)', all_text, re.DOTALL)
        if m:
            salario = m.group(1).strip()
            salario = re.sub(r'\s+', ' ', salario).strip()

        # Resumen del puesto
        resumen = None
        m = re.search(r'Resumen del puesto\s*(.*?)(?:Principales tareas|Beneficios|Detalles|$)',
                       all_text, re.DOTALL)
        if m:
            resumen = m.group(1).strip()
            resumen = re.sub(r'\s{2,}', ' ', resumen).strip()

        # Tareas principales
        tareas = None
        m = re.search(r'Principales tareas a realizar\s*(.*?)(?:Beneficios|Detalles|$)',
                       all_text, re.DOTALL)
        if m:
            tareas = m.group(1).strip()
            tareas = re.sub(r'\s{2,}', ' ', tareas).strip()

        # Beneficios
        beneficios = None
        m = re.search(r'Beneficios\s*(.*?)(?:Detalles|Lugar de Trabajo|$)',
                       all_text, re.DOTALL)
        if m:
            beneficios = m.group(1).strip()
            beneficios = re.sub(r'\s{2,}', ' ', beneficios).strip()

        # Lugar de trabajo (detallado)
        lugar_trabajo = None
        m = re.search(r'Lugar de Trabajo\s*(.*?)(?:Disponibilidad|Dias|$)',
                       all_text, re.DOTALL)
        if m:
            lugar_trabajo = m.group(1).strip()
            lugar_trabajo = re.sub(r'\s+', ' ', lugar_trabajo).strip()

        # Dias laborales
        dias = None
        m = re.search(r'Dias laborales\s*(.*?)(?:Horario|$)', all_text, re.DOTALL)
        if m:
            dias = m.group(1).strip()
            dias = re.sub(r'\s+', ' ', dias).strip()

        # Horario
        horario_entrada = None
        horario_salida = None
        m = re.search(r'Horario de Entrada y Salida\s*(\d{1,2}:\d{2})\s*(\d{1,2}:\d{2})',
                       all_text)
        if m:
            horario_entrada = m.group(1)
            horario_salida = m.group(2)

        # Experiencia
        experiencia = None
        m = re.search(r'Experiencia Requerida\s*(.*?)(?:Estudios|Postularme|$)',
                       all_text, re.DOTALL)
        if m:
            experiencia = m.group(1).strip()
            experiencia = re.sub(r'\s+', ' ', experiencia).strip()

        # Estudios
        estudios = None
        m = re.search(r'Estudios\s*(.*?)(?:Postularme|$)', all_text, re.DOTALL)
        if m:
            estudios = m.group(1).strip()
            estudios = re.sub(r'\s+', ' ', estudios).strip()

        return {
            'uuid': uuid,
            'url': url,
            'titulo': titulo,
            'empresa': empresa,
            'fecha_publicacion': self._parse_fecha(fecha_texto),
            'fecha_publicacion_raw': fecha_texto,
            'ubicacion': ubicacion,
            'lugar_trabajo': lugar_trabajo,
            'vacantes': vacantes,
            'disponibilidad': disponibilidad,
            'salario': salario,
            'resumen': resumen,
            'tareas': tareas,
            'beneficios': beneficios,
            'dias_laborables': dias,
            'horario_entrada': horario_entrada,
            'horario_salida': horario_salida,
            'experiencia': experiencia,
            'estudios': estudios,
            'scrapeado_en': datetime.now().isoformat(),
            'portal': 'portalempleo',
        }

    # ----------------------------------------------------------------
    # MAIN: Scrape completo
    # ----------------------------------------------------------------

    def scrape_all(self, fetch_details: bool = True, max_pages: int = None) -> List[Dict]:
        """
        Scrape completo: listado + detalles.

        Args:
            fetch_details: Si True, fetch detalle de cada oferta
            max_pages: Limite de paginas del listado (None = todas)

        Returns:
            Lista de ofertas con datos completos
        """
        logger.info("=" * 60)
        logger.info("Portal Empleo Nacional - Scraping completo")
        logger.info("=" * 60)

        # Paso 1: Total
        total = self.get_total_results()
        logger.info(f"Total ofertas reportadas por el portal: {total}")
        time.sleep(self.delay)

        # Paso 2: Listings
        all_ofertas = []
        page = 1
        seen_uuids = set()

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
                if o['uuid'] not in seen_uuids:
                    seen_uuids.add(o['uuid'])
                    all_ofertas.append(o)
                    nuevas += 1

            logger.info(f"  {nuevas} ofertas nuevas (total: {len(all_ofertas)})")

            if nuevas == 0:
                break

            page += 1
            time.sleep(self.delay)

        logger.info(f"Total ofertas en listado: {len(all_ofertas)}")

        if not fetch_details:
            return all_ofertas

        # Paso 3: Detalles
        ofertas_completas = []
        for i, listing in enumerate(all_ofertas, 1):
            logger.info(f"[{i}/{len(all_ofertas)}] Detalle: {listing['titulo'][:50]}")
            time.sleep(self.delay)

            detail = self.scrape_detail(listing['uuid'])
            if detail:
                ofertas_completas.append(detail)
            else:
                logger.warning(f"  No se pudo obtener detalle de {listing['uuid']}")

        logger.info(f"\nResultado: {len(ofertas_completas)}/{len(all_ofertas)} ofertas con detalle")
        return ofertas_completas


if __name__ == '__main__':
    import json as _json

    scraper = PortalEmpleoScraper(delay=1.5)
    # Test rapido: solo 2 paginas
    ofertas = scraper.scrape_all(max_pages=2)

    print(f"\n{'=' * 60}")
    print(f"Total ofertas scrapeadas: {len(ofertas)}")
    for o in ofertas[:5]:
        print(f"  [{o['uuid'][:8]}] {o['titulo']} - {o['empresa']} ({o.get('ubicacion', '')})")

    with open('portalempleo_ofertas_test.json', 'w', encoding='utf-8') as f:
        _json.dump(ofertas, f, ensure_ascii=False, indent=2)
    print(f"\nGuardado en portalempleo_ofertas_test.json")
