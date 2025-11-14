"""
Bumeran Scraper usando Selenium
=================================

Usa navegador real para bypasear protección Cloudflare.
Parsea el HTML para extraer datos de ofertas.

Uso:
    from bumeran_selenium_scraper import BumeranSeleniumScraper

    scraper = BumeranSeleniumScraper(headless=True)
    ofertas = scraper.scrapear_todo(max_ofertas=100)
"""

import time
import json
import re
import logging
from typing import List, Dict, Optional
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

logger = logging.getLogger(__name__)


class BumeranSeleniumScraper:
    """Scraper de Bumeran usando Selenium parseando HTML"""

    def __init__(self, headless: bool = True, delay: float = 2.0):
        """
        Inicializa el scraper con Selenium

        Args:
            headless: Ejecutar Chrome sin interfaz gráfica
            delay: Delay entre scrolls (segundos)
        """
        self.headless = headless
        self.delay = delay
        self.driver = None
        self.ofertas_ids_vistos = set()

        logger.info(f"BumeranSeleniumScraper inicializado (headless={headless})")

    def iniciar_navegador(self):
        """Inicia Chrome con Selenium"""
        logger.info("Iniciando navegador Chrome...")

        # Opciones de Chrome
        chrome_options = Options()

        if self.headless:
            chrome_options.add_argument('--headless=new')
            chrome_options.add_argument('--disable-gpu')

        # Opciones anti-detección
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--window-size=1920,1080')

        # User agent real
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

        try:
            # Iniciar Chrome
            self.driver = webdriver.Chrome(
                service=Service(ChromeDriverManager().install()),
                options=chrome_options
            )

            # Anti-detección: ocultar webdriver
            self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                'source': '''
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    })
                '''
            })

            logger.info("Navegador iniciado correctamente")

        except Exception as e:
            logger.error(f"Error iniciando navegador: {e}")
            raise

    def cerrar_navegador(self):
        """Cierra el navegador"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("Navegador cerrado")
            except Exception as e:
                logger.warning(f"Error cerrando navegador: {e}")

    def scrapear_todo(
        self,
        max_ofertas: Optional[int] = None,
        max_scrolls: int = 50
    ) -> List[Dict]:
        """
        Scrapea ofertas usando Selenium

        Args:
            max_ofertas: Límite de ofertas a extraer (None = todas)
            max_scrolls: Máximo de scrolls a hacer

        Returns:
            Lista de ofertas extraídas
        """
        logger.info("="*70)
        logger.info("INICIANDO SCRAPING CON SELENIUM")
        logger.info("="*70)
        logger.info(f"Max ofertas: {max_ofertas or 'Sin limite'}")
        logger.info(f"Max scrolls: {max_scrolls}")
        logger.info("")

        try:
            # Iniciar navegador
            self.iniciar_navegador()

            # Navegar a la página
            url = "https://www.bumeran.com.ar/empleos-busqueda.html"
            logger.info(f"Navegando a: {url}")
            self.driver.get(url)

            # Esperar a que cargue la página
            logger.info("Esperando carga inicial...")
            time.sleep(3)

            # Hacer scroll para cargar más ofertas
            logger.info("Iniciando scroll infinito...")

            scrolls_realizados = 0
            ofertas_anteriores = 0

            while scrolls_realizados < max_scrolls:
                # Scroll hacia abajo
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(self.delay)

                # Extraer ofertas de las requests interceptadas
                self._extraer_ofertas_de_requests()

                scrolls_realizados += 1
                ofertas_actuales = len(self.ofertas_extraidas)

                logger.info(f"Scroll {scrolls_realizados}/{max_scrolls}: {ofertas_actuales} ofertas únicas")

                # Verificar si hay límite de ofertas
                if max_ofertas and ofertas_actuales >= max_ofertas:
                    logger.info(f"Alcanzado límite de {max_ofertas} ofertas")
                    break

                # Verificar si dejó de cargar ofertas nuevas
                if ofertas_actuales == ofertas_anteriores and scrolls_realizados > 3:
                    logger.info("No se cargaron más ofertas - finalizando")
                    break

                ofertas_anteriores = ofertas_actuales

            logger.info("")
            logger.info("="*70)
            logger.info(f"SCRAPING COMPLETADO: {len(self.ofertas_extraidas)} ofertas únicas")
            logger.info("="*70)

            # Limitar si es necesario
            if max_ofertas:
                return self.ofertas_extraidas[:max_ofertas]

            return self.ofertas_extraidas

        except Exception as e:
            logger.error(f"Error durante scraping: {e}")
            raise

        finally:
            # Cerrar navegador
            self.cerrar_navegador()

    def _extraer_ofertas_de_requests(self):
        """Extrae ofertas de las requests interceptadas por selenium-wire"""
        try:
            # Buscar requests a searchV2
            for request in self.driver.requests:
                if 'searchV2' in request.url and request.response:
                    try:
                        # Decodificar response JSON
                        body = request.response.body

                        if body:
                            data = json.loads(body.decode('utf-8'))

                            # Extraer ofertas del content
                            ofertas = data.get('content', [])

                            for oferta in ofertas:
                                oferta_id = str(oferta.get('id'))

                                # Solo agregar si no la hemos visto
                                if oferta_id not in self.ofertas_ids_vistos:
                                    self.ofertas_ids_vistos.add(oferta_id)

                                    # Agregar timestamp de scraping
                                    oferta['scrapeado_en'] = datetime.now().isoformat()

                                    self.ofertas_extraidas.append(oferta)

                    except Exception as e:
                        logger.debug(f"Error procesando request: {e}")
                        continue

        except Exception as e:
            logger.debug(f"Error extrayendo ofertas: {e}")


if __name__ == "__main__":
    """Test del scraper"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s: %(message)s'
    )

    print("="*70)
    print("TEST: Bumeran Selenium Scraper")
    print("="*70)
    print()

    scraper = BumeranSeleniumScraper(headless=False)  # Con interfaz para ver qué pasa

    try:
        ofertas = scraper.scrapear_todo(max_ofertas=50, max_scrolls=10)

        print(f"\nOfertas extraídas: {len(ofertas)}")

        if ofertas:
            print("\nPrimeras 5 ofertas:")
            for i, oferta in enumerate(ofertas[:5], 1):
                print(f"{i}. ID: {oferta.get('id')} - {oferta.get('titulo', 'N/A')}")

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
