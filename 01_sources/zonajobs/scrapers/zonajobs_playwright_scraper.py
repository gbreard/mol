# -*- coding: utf-8 -*-
"""
ZonaJobs Scraper con Playwright - Multi-Keyword
================================================

Scraper que usa Playwright para hacer búsquedas reales por keyword
e interceptar las llamadas a la API para capturar ofertas.

Esto permite obtener mucha más cobertura que el scraper básico de API.
"""

from playwright.sync_api import sync_playwright, Page
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Set
import time
import json
import logging
import sys
import html
import re

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Agregar path para importar incremental_tracker y keywords_loader
project_root = Path(__file__).parent.parent.parent.parent
consolidation_scripts = project_root / "02_consolidation" / "scripts"
config_dir = project_root / "config" / "scraping"

for path in [consolidation_scripts, config_dir]:
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

try:
    from incremental_tracker import IncrementalTracker
except ImportError as e:
    logger.warning(f"No se pudo importar IncrementalTracker: {e}")
    IncrementalTracker = None

try:
    from keywords_loader import load_keywords
except ImportError as e:
    logger.warning(f"No se pudo importar keywords_loader: {e}")
    load_keywords = None


class ZonaJobsPlaywrightScraper:
    """Scraper de ZonaJobs usando Playwright con búsquedas por keyword"""

    BASE_URL = "https://www.zonajobs.com.ar"

    def __init__(self, delay_between_searches: float = 3.0, headless: bool = True):
        """
        Args:
            delay_between_searches: Delay entre búsquedas por keyword
            headless: Si True, ejecuta navegador sin interfaz gráfica
        """
        self.delay = delay_between_searches
        self.headless = headless
        self.data_dir = Path(__file__).parent.parent / "data" / "raw"
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Almacenar ofertas capturadas
        self.captured_offers = []
        self.captured_ids = set()
        self.current_keyword = ""  # Para rastrear keyword actual en handler

    @staticmethod
    def clean_html(text: str) -> str:
        """Limpia HTML de una descripción"""
        if not text:
            return ""

        text = html.unescape(text)
        text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)
        text = re.sub(r'</p>', '\n\n', text, flags=re.IGNORECASE)
        text = re.sub(r'<[^>]+>', '', text)
        text = re.sub(r'\n\s*\n', '\n\n', text)
        text = re.sub(r' +', ' ', text)

        return text.strip()

    def parse_oferta(self, oferta_raw: Dict, search_keyword: str = "") -> Dict:
        """Parsea una oferta del formato crudo de la API"""
        parsed = {
            # IDs
            'id_oferta': oferta_raw.get('id'),
            'id_empresa': oferta_raw.get('idEmpresa'),

            # Información básica
            'titulo': oferta_raw.get('titulo', '').strip(),
            'empresa': oferta_raw.get('empresa', '').strip(),
            'empresa_confidencial': oferta_raw.get('confidencial', False),
            'logo_url': oferta_raw.get('logoURL'),

            # Descripción (limpiar HTML si existe)
            'descripcion': self.clean_html(oferta_raw.get('detalle', '')),
            'descripcion_raw': oferta_raw.get('detalle', ''),

            # Ubicación y modalidad
            'localizacion': oferta_raw.get('localizacion', ''),
            'modalidad_trabajo': oferta_raw.get('modalidadTrabajo'),
            'tipo_trabajo': oferta_raw.get('tipoTrabajo'),

            # Fechas
            'fecha_publicacion': oferta_raw.get('fechaPublicacion'),
            'fecha_modificacion': oferta_raw.get('fechaModificado'),

            # Detalles
            'cantidad_vacantes': oferta_raw.get('cantidadVacantes', 1),
            'apto_discapacitado': oferta_raw.get('aptoDiscapacitado', False),

            # Metadata de búsqueda
            'search_keyword_usado': search_keyword,

            # URL
            'url_oferta': f"https://www.zonajobs.com.ar/avisos/{oferta_raw.get('id')}",
            'scrapeado_en': datetime.now().isoformat()
        }

        return parsed

    def setup_response_handler(self, page: Page):
        """Configura handler para interceptar respuestas de la API"""

        def handle_response(response):
            try:
                url = response.url

                # Solo procesar llamadas a la API de búsqueda
                if '/api/avisos/searchHomeV2' not in url:
                    return

                # Solo procesar respuestas exitosas
                if response.status != 200:
                    return

                # Parsear JSON
                try:
                    data = response.json()
                except:
                    return

                # Extraer ofertas
                ofertas_raw = data.get('avisos', [])
                if not ofertas_raw:
                    return

                logger.debug(f"  Interceptada respuesta con {len(ofertas_raw)} ofertas")

                # Parsear y agregar ofertas
                for oferta_raw in ofertas_raw:
                    oferta_id = oferta_raw.get('id')

                    # Solo agregar si no la tenemos ya
                    if oferta_id and oferta_id not in self.captured_ids:
                        parsed = self.parse_oferta(oferta_raw, self.current_keyword)
                        self.captured_offers.append(parsed)
                        self.captured_ids.add(oferta_id)

            except Exception as e:
                logger.debug(f"  Error en handler: {e}")

        page.on("response", handle_response)

    def extract_ofertas_from_page(self, page: Page, keyword: str):
        """Extrae ofertas del HTML de la página actual"""
        try:
            # Esperar a que carguen los elementos de ofertas
            page.wait_for_selector('article[data-id]', timeout=10000)

            # Obtener todas las tarjetas de ofertas
            ofertas_elements = page.query_selector_all('article[data-id]')

            logger.debug(f"  Encontrados {len(ofertas_elements)} elementos de ofertas en página")

            for element in ofertas_elements:
                try:
                    # Extraer ID (atributo data-id)
                    oferta_id = element.get_attribute('data-id')

                    if not oferta_id or oferta_id in self.captured_ids:
                        continue

                    # Extraer título
                    titulo_el = element.query_selector('h3')
                    titulo = titulo_el.inner_text().strip() if titulo_el else ''

                    # Extraer empresa
                    empresa_el = element.query_selector('[class*="company"]')
                    empresa = empresa_el.inner_text().strip() if empresa_el else ''

                    # Extraer ubicación
                    location_el = element.query_selector('[class*="location"]')
                    localizacion = location_el.inner_text().strip() if location_el else ''

                    # URL de la oferta
                    link_el = element.query_selector('a[href*="/avisos/"]')
                    url_oferta = ''
                    if link_el:
                        href = link_el.get_attribute('href')
                        url_oferta = f"{self.BASE_URL}{href}" if href.startswith('/') else href

                    # Crear oferta
                    oferta = {
                        'id_oferta': oferta_id,
                        'titulo': titulo,
                        'empresa': empresa,
                        'empresa_confidencial': False,
                        'localizacion': localizacion,
                        'search_keyword_usado': keyword,
                        'url_oferta': url_oferta,
                        'scrapeado_en': datetime.now().isoformat()
                    }

                    self.captured_offers.append(oferta)
                    self.captured_ids.add(oferta_id)

                except Exception as e:
                    logger.debug(f"  Error extrayendo oferta individual: {e}")
                    continue

        except Exception as e:
            logger.debug(f"  Error extrayendo ofertas de página: {e}")

    def search_keyword(self, page: Page, keyword: str, max_scrolls: int = 5):
        """
        Realiza una búsqueda por keyword y scrollea para cargar más resultados

        Args:
            page: Página de Playwright
            keyword: Keyword a buscar
            max_scrolls: Máximo número de scrolls para cargar más resultados
        """
        try:
            # Navegar a la página de búsqueda con el keyword
            search_url = f"{self.BASE_URL}/empleos?q={keyword}"
            logger.info(f"  Navegando a: {search_url}")

            page.goto(search_url, wait_until='networkidle', timeout=60000)
            time.sleep(2)

            # Extraer ofertas iniciales
            self.extract_ofertas_from_page(page, keyword)

            # Scrollear para cargar más resultados
            for i in range(max_scrolls):
                logger.debug(f"  Scroll {i+1}/{max_scrolls}")

                # Scroll hasta el final
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(1.5)

                # Extraer nuevas ofertas que se cargaron
                self.extract_ofertas_from_page(page, keyword)

                # Intentar hacer clic en "Ver más" si existe
                try:
                    ver_mas_button = page.query_selector('button:has-text("Ver más")')
                    if ver_mas_button and ver_mas_button.is_visible():
                        ver_mas_button.click()
                        time.sleep(2)
                        # Extraer ofertas después del click
                        self.extract_ofertas_from_page(page, keyword)
                except:
                    pass

            logger.info(f"  Capturadas {len(self.captured_offers)} ofertas hasta ahora")

        except Exception as e:
            logger.error(f"  Error en búsqueda de '{keyword}': {e}")

    def scrapear_multiples_keywords(
        self,
        keywords: List[str],
        max_scrolls_per_keyword: int = 5,
        incremental: bool = True
    ) -> pd.DataFrame:
        """
        Scrapea múltiples keywords usando Playwright

        Args:
            keywords: Lista de keywords a buscar
            max_scrolls_per_keyword: Scrolls por keyword para cargar más resultados
            incremental: Si True, filtra ofertas ya scrapeadas

        Returns:
            DataFrame con ofertas únicas
        """
        logger.info("="*70)
        logger.info("SCRAPING MULTI-KEYWORD - ZONAJOBS (PLAYWRIGHT)")
        logger.info("="*70)
        logger.info(f"Keywords: {len(keywords)}")
        logger.info(f"Scrolls por keyword: {max_scrolls_per_keyword}")
        logger.info(f"Modo: {'Incremental' if incremental else 'Full'}")
        logger.info(f"Navegador: {'Headless' if self.headless else 'Con interfaz'}")
        logger.info("")

        # Inicializar tracker si modo incremental
        tracker = None
        existing_ids = set()
        if incremental:
            if IncrementalTracker is None:
                logger.warning("IncrementalTracker no disponible, ejecutando en modo full")
                incremental = False
            else:
                tracker = IncrementalTracker(source='zonajobs')
                existing_ids = tracker.load_scraped_ids()
                if existing_ids:
                    logger.info(f"Modo incremental: {len(existing_ids):,} IDs ya scrapeados")
                else:
                    logger.info("Primera ejecución: scrapeando TODO")
                logger.info("")

        # Reset captured data
        self.captured_offers = []
        self.captured_ids = set()

        with sync_playwright() as p:
            # Lanzar navegador
            logger.info("Lanzando navegador...")
            browser = p.chromium.launch(
                headless=self.headless,
                args=['--disable-blink-features=AutomationControlled']
            )

            context = browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                viewport={'width': 1920, 'height': 1080},
                locale='es-AR',
                timezone_id='America/Argentina/Buenos_Aires'
            )

            page = context.new_page()

            # Configurar handler UNA SOLA VEZ para interceptar respuestas
            self.setup_response_handler(page)
            logger.info("Handler de respuestas configurado")

            # Iterar sobre keywords
            for i, keyword in enumerate(keywords, 1):
                logger.info(f"[{i}/{len(keywords)}] Keyword: '{keyword}'")

                # Actualizar keyword actual para el handler
                self.current_keyword = keyword

                # Buscar keyword
                self.search_keyword(page, keyword, max_scrolls_per_keyword)

                # Delay entre keywords
                if i < len(keywords):
                    logger.debug(f"  Esperando {self.delay}s antes de siguiente keyword...")
                    time.sleep(self.delay)

            # Cerrar navegador
            context.close()
            browser.close()
            logger.info("Navegador cerrado")

        # Convertir a DataFrame
        logger.info("")
        logger.info("="*70)
        logger.info("CONSOLIDANDO RESULTADOS")
        logger.info("="*70)

        if not self.captured_offers:
            logger.warning("No se capturaron ofertas")
            return pd.DataFrame()

        df = pd.DataFrame(self.captured_offers)
        logger.info(f"Ofertas totales (con duplicados): {len(df)}")

        # Deduplicar por ID
        df_dedup = df.drop_duplicates(subset='id_oferta', keep='first')
        logger.info(f"Ofertas únicas: {len(df_dedup)}")
        logger.info(f"Duplicados removidos: {len(df) - len(df_dedup)}")

        # Filtrar ofertas nuevas si modo incremental
        df_final = df_dedup
        if incremental and tracker and existing_ids:
            logger.info("")
            logger.info("Filtrando ofertas nuevas (modo incremental)...")

            # Filtrar ofertas que NO están en existing_ids
            df_final = df_dedup[~df_dedup['id_oferta'].astype(str).isin(existing_ids)]

            ofertas_ya_existentes = len(df_dedup) - len(df_final)
            logger.info(f"Ofertas ya scrapeadas anteriormente: {ofertas_ya_existentes}")
            logger.info(f"Ofertas NUEVAS: {len(df_final)}")

            # Actualizar tracking con IDs nuevos
            if not df_final.empty:
                new_ids = set(df_final['id_oferta'].astype(str))
                tracker.merge_scraped_ids(new_ids)
        elif incremental and tracker:
            # Primera ejecución: todas son nuevas
            logger.info("")
            logger.info("Primera ejecución: todas las ofertas son nuevas")
            if not df_final.empty:
                new_ids = set(df_final['id_oferta'].astype(str))
                tracker.merge_scraped_ids(new_ids)

        # Stats finales
        logger.info("")
        logger.info("="*70)
        logger.info("ESTADÍSTICAS FINALES")
        logger.info("="*70)
        logger.info(f"  Keywords procesadas: {len(keywords)}")
        logger.info(f"  Ofertas únicas capturadas: {len(df_dedup)}")
        if incremental and existing_ids:
            logger.info(f"  Ofertas nuevas: {len(df_final)}")

        if 'search_keyword_usado' in df_final.columns:
            logger.info("")
            logger.info("Keywords más productivas:")
            top_kw = df_final['search_keyword_usado'].value_counts().head(10)
            for kw, count in top_kw.items():
                logger.info(f"  - {kw}: {count} ofertas")

        return df_final

    def save_to_csv(self, df: pd.DataFrame, filename: str = None) -> Path:
        """Guarda DataFrame a CSV"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"zonajobs_playwright_{timestamp}.csv"

        filepath = self.data_dir / filename
        df.to_csv(filepath, index=False, encoding='utf-8')
        logger.info(f"CSV guardado: {filepath}")
        return filepath


def main():
    """Función de prueba"""
    print("="*70)
    print("ZONAJOBS PLAYWRIGHT SCRAPER - TEST")
    print("="*70)
    print()

    # Usar estrategia 'general' del diccionario maestro (14 keywords)
    if load_keywords:
        keywords = load_keywords('general')[:5]  # Solo primeras 5 para test
        print(f"Usando {len(keywords)} keywords del diccionario maestro (test)")
    else:
        keywords = ['python', 'desarrollador', 'analista']
        print(f"Usando {len(keywords)} keywords de prueba")

    print(f"Keywords: {keywords}")
    print()

    scraper = ZonaJobsPlaywrightScraper(
        delay_between_searches=3.0,
        headless=True  # Cambiar a False para ver el navegador
    )

    df = scraper.scrapear_multiples_keywords(
        keywords=keywords,
        max_scrolls_per_keyword=3,  # 3 scrolls por keyword
        incremental=True
    )

    if not df.empty:
        # Guardar
        filepath = scraper.save_to_csv(df, "zonajobs_playwright_test.csv")

        print()
        print("="*70)
        print("SCRAPING COMPLETADO")
        print("="*70)
        print(f"Total de ofertas: {len(df)}")
        print(f"Archivo guardado: {filepath}")
    else:
        print("No se encontraron ofertas")


if __name__ == "__main__":
    main()
