"""
ComputRabajo Scraper - HTML Parsing
====================================

Scraper para ar.computrabajo.com usando requests + BeautifulSoup.

Metodología: HTML Scraping (NO requiere JavaScript rendering)
Ofertas: ~500-1000+ disponibles
Campos: 20+ por oferta
Formato: CSV, JSON, Excel

Uso:
    scraper = ComputRabajoScraper()
    ofertas = scraper.scrapear_todo(max_paginas=10)
    scraper.save_to_csv(ofertas, "computrabajo_ofertas.csv")
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
import time
from datetime import datetime
from typing import List, Dict, Optional
import logging
import re

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ComputRabajoScraper:
    """Scraper para ar.computrabajo.com usando HTML parsing"""

    def __init__(self, delay_between_requests: float = 2.0):
        """
        Inicializa el scraper

        Args:
            delay_between_requests: Segundos entre requests (default: 2.0)
        """
        self.base_url = "https://ar.computrabajo.com"
        self.delay = delay_between_requests
        self.session = requests.Session()

        # Headers necesarios
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'es-AR,es;q=0.9',
            'Referer': 'https://ar.computrabajo.com/',
        }

        logger.info(f"Scraper inicializado")
        logger.info(f"Delay entre requests: {self.delay}s")

    def scrapear_pagina(
        self,
        query: Optional[str] = None,
        pagina: int = 1,
        ubicacion: Optional[str] = None
    ) -> List[Dict]:
        """
        Scrapea una página de ofertas

        Args:
            query: Búsqueda por keyword (opcional)
            pagina: Número de página (1-indexed)
            ubicacion: Ubicación (opcional)

        Returns:
            Lista de ofertas de la página
        """
        # Construir URL
        if query:
            url = f"{self.base_url}/trabajo-de-{query}"
        else:
            url = f"{self.base_url}/"

        # Agregar paginación si no es la primera página
        if pagina > 1:
            url += f"?p={pagina}"

        try:
            logger.info(f"Scrapeando: {url}")

            response = self.session.get(
                url,
                headers=self.headers,
                timeout=30
            )

            if response.status_code != 200:
                logger.error(f"  Error - Status code: {response.status_code}")
                return []

            # Parsear HTML
            soup = BeautifulSoup(response.content, 'html.parser')

            # Encontrar ofertas
            ofertas_html = soup.find_all('article', class_='box_offer')

            logger.info(f"  OK - {len(ofertas_html)} ofertas encontradas")

            # Extraer datos de cada oferta
            ofertas = []
            for oferta_elem in ofertas_html:
                oferta = self._extraer_oferta(oferta_elem)
                if oferta:
                    ofertas.append(oferta)

            return ofertas

        except Exception as e:
            logger.error(f"  Exception: {e}")
            return []

    def _extraer_oferta(self, oferta_elem) -> Optional[Dict]:
        """
        Extrae datos de un elemento <article>

        Args:
            oferta_elem: Elemento BeautifulSoup

        Returns:
            Dict con datos de la oferta
        """
        try:
            oferta = {}

            # ID
            oferta['id_oferta'] = oferta_elem.get('data-id')

            # Título y URL
            titulo_elem = oferta_elem.find('a', class_='js-o-link')
            if titulo_elem:
                oferta['titulo'] = titulo_elem.get_text(strip=True)
                oferta['url_relativa'] = titulo_elem.get('href', '')
                oferta['url_completa'] = self.base_url + oferta['url_relativa'] if oferta['url_relativa'] else None

            # Empresa
            empresa_container = oferta_elem.find('p', class_='dFlex')
            if empresa_container:
                empresa_link = empresa_container.find('a')
                if empresa_link:
                    oferta['empresa'] = empresa_link.get_text(strip=True)
                    oferta['empresa_url'] = empresa_link.get('href', '')

                # Rating empresa
                rating_elem = empresa_container.find('span', class_='fwB')
                if rating_elem:
                    try:
                        oferta['empresa_rating'] = float(rating_elem.get_text(strip=True).replace(',', '.'))
                    except:
                        oferta['empresa_rating'] = None

            # Ubicación (buscar el <p class="fs16 fc_base"> que contiene solo la ubicación)
            # Normalmente después de la empresa
            ubicacion_parrafos = oferta_elem.find_all('p', class_='fs16')
            for p in ubicacion_parrafos:
                # Buscar el que tiene un span con mr10 Y no contiene enlaces (no es la empresa)
                span_ubicacion = p.find('span', class_='mr10')
                if span_ubicacion and not p.find('a'):
                    # Verificar que no sea un número (rating)
                    texto = span_ubicacion.get_text(strip=True)
                    # Si contiene una coma (típico de "Ciudad, Provincia") es ubicación
                    if ',' in texto:
                        oferta['ubicacion'] = texto
                        break

            # Modalidad de trabajo (Remoto/Presencial/Híbrido)
            modalidad_container = oferta_elem.find('div', class_='fs13')
            if modalidad_container:
                # Buscar icono de home (remoto) o building (presencial)
                if modalidad_container.find('span', class_='icon i_home'):
                    oferta['modalidad'] = 'Remoto'
                elif modalidad_container.find('span', class_='icon i_building'):
                    oferta['modalidad'] = 'Presencial'
                else:
                    # Extraer texto del contenedor
                    modalidad_text = modalidad_container.get_text(strip=True)
                    if 'remoto' in modalidad_text.lower():
                        oferta['modalidad'] = 'Remoto'
                    elif 'presencial' in modalidad_text.lower():
                        oferta['modalidad'] = 'Presencial'
                    elif 'híbrido' in modalidad_text.lower() or 'hibrido' in modalidad_text.lower():
                        oferta['modalidad'] = 'Híbrido'

            # Fecha de publicación
            fecha_elem = oferta_elem.find('p', class_='fc_aux')
            if fecha_elem:
                fecha_text = fecha_elem.get_text(strip=True)
                oferta['fecha_publicacion_raw'] = fecha_text
                oferta['fecha_publicacion'] = self._parsear_fecha(fecha_text)

            # Metadata
            oferta['scrapeado_en'] = datetime.now().isoformat()
            oferta['fuente'] = 'computrabajo'

            return oferta

        except Exception as e:
            logger.warning(f"Error extrayendo oferta: {e}")
            return None

    def _parsear_fecha(self, fecha_text: str) -> Optional[str]:
        """
        Parsea fechas relativas como 'Hace 3 horas' a ISO 8601

        Args:
            fecha_text: Texto de fecha (ej: "Hace 3 horas")

        Returns:
            Fecha en formato ISO o None
        """
        try:
            from datetime import timedelta

            now = datetime.now()

            # "Hace X horas"
            if 'hora' in fecha_text.lower():
                match = re.search(r'(\d+)', fecha_text)
                if match:
                    horas = int(match.group(1))
                    fecha = now - timedelta(hours=horas)
                    return fecha.isoformat()

            # "Hace X días"
            elif 'día' in fecha_text.lower() or 'dia' in fecha_text.lower():
                match = re.search(r'(\d+)', fecha_text)
                if match:
                    dias = int(match.group(1))
                    fecha = now - timedelta(days=dias)
                    return fecha.isoformat()

            # "Hoy"
            elif 'hoy' in fecha_text.lower():
                return now.isoformat()

            # "Ayer"
            elif 'ayer' in fecha_text.lower():
                fecha = now - timedelta(days=1)
                return fecha.isoformat()

            return None

        except Exception as e:
            return None

    def scrapear_oferta_individual(self, url_oferta: str) -> Optional[Dict]:
        """
        Scrapea una oferta individual para obtener descripción completa

        Args:
            url_oferta: URL completa de la oferta

        Returns:
            Dict con campos adicionales (descripción, requisitos, etc.)
        """
        try:
            logger.debug(f"  Scrapeando oferta individual: {url_oferta}")

            response = self.session.get(
                url_oferta,
                headers=self.headers,
                timeout=30
            )

            if response.status_code != 200:
                logger.warning(f"  Error en oferta individual - Status: {response.status_code}")
                return None

            soup = BeautifulSoup(response.content, 'html.parser')

            datos_extra = {}

            # Descripción completa
            # ComputRabajo usa varios selectores posibles para la descripción
            desc_container = soup.find('div', class_='box_detail')
            if desc_container:
                # Buscar el párrafo principal con la descripción
                desc_paragraphs = desc_container.find_all('p')
                if desc_paragraphs:
                    # Juntar todos los párrafos
                    descripcion_completa = '\n\n'.join([p.get_text(strip=True) for p in desc_paragraphs if p.get_text(strip=True)])
                    datos_extra['descripcion'] = descripcion_completa

            # Intentar selector alternativo si no encontró descripción
            if not datos_extra.get('descripcion'):
                # Buscar en el contenedor principal
                main_content = soup.find('article', class_='offerDetail')
                if main_content:
                    # Extraer todo el texto, limpiando headers y footers
                    text_blocks = []
                    for elem in main_content.find_all(['p', 'li', 'div'], recursive=True):
                        text = elem.get_text(strip=True)
                        if text and len(text) > 20:  # Solo bloques con contenido significativo
                            text_blocks.append(text)

                    if text_blocks:
                        datos_extra['descripcion'] = '\n'.join(text_blocks[:10])  # Primeros 10 bloques

            # Requisitos (si están separados)
            requisitos_section = soup.find('div', class_='requisitos') or soup.find('div', string=re.compile('Requisitos', re.IGNORECASE))
            if requisitos_section:
                requisitos = []
                for li in requisitos_section.find_all('li'):
                    req_text = li.get_text(strip=True)
                    if req_text:
                        requisitos.append(req_text)
                if requisitos:
                    datos_extra['requisitos'] = requisitos

            # Beneficios (si están disponibles)
            beneficios_section = soup.find('div', class_='beneficios') or soup.find('div', string=re.compile('Beneficios', re.IGNORECASE))
            if beneficios_section:
                beneficios = []
                for li in beneficios_section.find_all('li'):
                    ben_text = li.get_text(strip=True)
                    if ben_text:
                        beneficios.append(ben_text)
                if beneficios:
                    datos_extra['beneficios'] = beneficios

            # Salario (si está visible)
            salario_elem = soup.find('span', class_='salary') or soup.find('div', class_='salario')
            if salario_elem:
                datos_extra['salario'] = salario_elem.get_text(strip=True)

            logger.debug(f"  OK - Descripción: {len(datos_extra.get('descripcion', '')) if datos_extra.get('descripcion') else 0} chars")

            return datos_extra

        except Exception as e:
            logger.warning(f"  Error scrapeando oferta individual: {e}")
            return None

    def scrapear_todo(
        self,
        max_paginas: Optional[int] = 10,
        max_resultados: Optional[int] = None,
        query: Optional[str] = None,
        fetch_description: bool = True
    ) -> List[Dict]:
        """
        Scrapea múltiples páginas de ofertas

        Args:
            max_paginas: Máximo de páginas a scrapear (None = ilimitado)
            max_resultados: Máximo de ofertas totales (None = ilimitado)
            query: Búsqueda por keyword (opcional)
            fetch_description: Si True, scrapea cada oferta individual para obtener descripción (MUY LENTO)

        Returns:
            Lista de ofertas
        """
        logger.info("="*70)
        logger.info("INICIANDO SCRAPING DE COMPUTRABAJO")
        logger.info("="*70)
        logger.info(f"Parametros:")
        logger.info(f"  Max paginas: {max_paginas or 'Ilimitado'}")
        logger.info(f"  Max resultados: {max_resultados or 'Ilimitado'}")
        logger.info(f"  Query: {query or 'Todas las ofertas'}")
        logger.info(f"  Fetch description: {fetch_description} {'[MODO LENTO]' if fetch_description else '[MODO RAPIDO]'}")
        logger.info("")

        todas_ofertas = []
        pagina = 1

        while max_paginas is None or pagina <= max_paginas:
            # Scrapear página
            ofertas_pagina = self.scrapear_pagina(
                query=query,
                pagina=pagina
            )

            if not ofertas_pagina:
                logger.warning("No hay más ofertas disponibles")
                break

            # Si fetch_description=True, scrapear cada oferta individual
            if fetch_description:
                logger.info(f"  Scrapeando {len(ofertas_pagina)} ofertas individuales...")
                for i, oferta in enumerate(ofertas_pagina, 1):
                    if oferta.get('url_completa'):
                        datos_extra = self.scrapear_oferta_individual(oferta['url_completa'])
                        if datos_extra:
                            oferta.update(datos_extra)

                        # Delay entre ofertas individuales para no saturar
                        if i < len(ofertas_pagina):
                            time.sleep(self.delay)

                logger.info(f"  OK - Ofertas con descripción: {sum(1 for o in ofertas_pagina if o.get('descripcion'))}/{len(ofertas_pagina)}")

            # Agregar ofertas
            todas_ofertas.extend(ofertas_pagina)

            # Verificar límite de resultados
            if max_resultados and len(todas_ofertas) >= max_resultados:
                todas_ofertas = todas_ofertas[:max_resultados]
                logger.info(f"Alcanzado limite de {max_resultados} ofertas")
                break

            # Si hay menos de 20 ofertas, probablemente no hay más páginas
            if len(ofertas_pagina) < 20:
                logger.info("Scrapeadas todas las ofertas disponibles")
                break

            pagina += 1

            # Rate limiting
            if max_paginas is None or pagina <= max_paginas:
                logger.debug(f"Esperando {self.delay}s...")
                time.sleep(self.delay)

        logger.info("")
        logger.info("="*70)
        logger.info(f"SCRAPING COMPLETADO: {len(todas_ofertas)} ofertas")
        logger.info("="*70)

        return todas_ofertas

    def procesar_ofertas(self, ofertas_raw: List[Dict]) -> pd.DataFrame:
        """
        Procesa ofertas crudas a DataFrame estructurado

        Args:
            ofertas_raw: Lista de ofertas

        Returns:
            DataFrame con ofertas procesadas
        """
        logger.info("Procesando ofertas...")

        df = pd.DataFrame(ofertas_raw)
        logger.info(f"OK - {len(df)} ofertas procesadas con {len(df.columns)} campos")

        return df

    def save_to_csv(self, ofertas: List[Dict], filename: str = None):
        """Guarda ofertas en CSV"""
        df = self.procesar_ofertas(ofertas)

        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"../data/raw/computrabajo_ofertas_{timestamp}.csv"

        df.to_csv(filename, index=False, encoding='utf-8-sig')
        logger.info(f"Guardado CSV: {filename}")
        return filename

    def save_to_json(self, ofertas: List[Dict], filename: str = None):
        """Guarda ofertas en JSON"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"../data/raw/computrabajo_ofertas_{timestamp}.json"

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(ofertas, f, indent=2, ensure_ascii=False)

        logger.info(f"Guardado JSON: {filename}")
        return filename

    def save_to_excel(self, ofertas: List[Dict], filename: str = None):
        """Guarda ofertas en Excel"""
        df = self.procesar_ofertas(ofertas)

        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"../data/raw/computrabajo_ofertas_{timestamp}.xlsx"

        df.to_excel(filename, index=False, engine='openpyxl')
        logger.info(f"Guardado Excel: {filename}")
        return filename

    def save_all_formats(self, ofertas: List[Dict], base_filename: str = None):
        """Guarda ofertas en todos los formatos"""
        if base_filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_filename = f"computrabajo_ofertas_{timestamp}"

        logger.info("Guardando en todos los formatos...")

        csv_file = self.save_to_csv(ofertas, f"../data/raw/{base_filename}.csv")
        json_file = self.save_to_json(ofertas, f"../data/raw/{base_filename}.json")
        excel_file = self.save_to_excel(ofertas, f"../data/raw/{base_filename}.xlsx")

        return {
            'csv': csv_file,
            'json': json_file,
            'excel': excel_file
        }


def main():
    """Función principal de ejemplo"""
    print("="*70)
    print("COMPUTRABAJO SCRAPER")
    print("="*70)
    print("\nEjemplo de uso:\n")

    # Crear scraper
    scraper = ComputRabajoScraper(delay_between_requests=2.0)

    # Opción 1: Scrapear primeras 100 ofertas
    print("\n[EJEMPLO 1] Scrapeando primeras 100 ofertas...")
    ofertas = scraper.scrapear_todo(max_paginas=5, max_resultados=100)

    # Guardar en todos los formatos
    if ofertas:
        files = scraper.save_all_formats(ofertas)
        print(f"\nArchivos guardados:")
        for fmt, filepath in files.items():
            print(f"  {fmt.upper()}: {filepath}")

    # Opción 2: Búsqueda específica
    print("\n\n[EJEMPLO 2] Buscando ofertas de 'python'...")
    ofertas_python = scraper.scrapear_todo(
        max_paginas=2,
        max_resultados=50,
        query="python"
    )

    if ofertas_python:
        scraper.save_to_csv(ofertas_python, "../data/raw/computrabajo_python.csv")

    print("\n" + "="*70)
    print("Ejemplos completados!")
    print("="*70)


if __name__ == "__main__":
    main()
