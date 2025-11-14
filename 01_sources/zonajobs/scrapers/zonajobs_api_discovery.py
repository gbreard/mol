# -*- coding: utf-8 -*-
"""
Script automatizado para descubrir API de ZonaJobs
Enfocado en interceptar llamadas relacionadas con ofertas laborales
"""

import sys
import io
# Configurar encoding UTF-8 para Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from playwright.sync_api import sync_playwright
import json
from datetime import datetime
import time
from urllib.parse import urlparse, parse_qs


class ZonaJobsAPIDiscovery:
    """Descubre y documenta la API de ZonaJobs"""

    def __init__(self):
        self.api_calls = []
        self.job_related_calls = []
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

    def setup_browser(self, headless=True):
        """Configura el navegador con Playwright"""
        print("[INFO] Configurando navegador Playwright...")

        self.playwright = sync_playwright().start()

        self.browser = self.playwright.chromium.launch(
            headless=headless,
            args=['--disable-blink-features=AutomationControlled']
        )

        self.context = self.browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            viewport={'width': 1920, 'height': 1080},
            locale='es-AR',
            timezone_id='America/Argentina/Buenos_Aires'
        )

        self.page = self.context.new_page()
        self.page.on("response", self._handle_response)

        print("[OK] Navegador configurado correctamente")

    def _is_job_related_api(self, url):
        """Determina si la URL es relacionada con ofertas laborales"""
        job_keywords = [
            '/job', '/work', '/empleo', '/oferta', '/aviso',
            '/search', '/busqueda', '/listing', '/position',
            '/postulacion', '/applicant'
        ]
        url_lower = url.lower()
        return any(keyword in url_lower for keyword in job_keywords)

    def _is_api_response(self, response):
        """Determina si es una respuesta de API"""
        url = response.url.lower()

        # Excluir recursos estáticos
        static_ext = ['.js', '.css', '.png', '.jpg', '.gif', '.svg', '.woff', '.ttf', '.ico', '.webp']
        if any(url.endswith(ext) for ext in static_ext):
            return False

        # Incluir si tiene patrones de API
        api_patterns = ['/api/', '/graphql', '.json', '/v1/', '/v2/']
        if any(pattern in url for pattern in api_patterns):
            return True

        # Incluir si es JSON
        content_type = response.headers.get('content-type', '')
        if 'application/json' in content_type:
            return True

        return False

    def _handle_response(self, response):
        """Maneja cada response interceptada"""
        try:
            if self._is_api_response(response):
                api_info = self._extract_api_info(response)
                if api_info:
                    self.api_calls.append(api_info)

                    # Si está relacionado con trabajos, guardarlo también separadamente
                    if self._is_job_related_api(response.url):
                        self.job_related_calls.append(api_info)
                        print(f"[API-JOB] {api_info['method']} {api_info['url']}")
                    else:
                        print(f"[API] {api_info['method']} {api_info['url']}")

        except Exception as e:
            print(f"[ERROR] Procesando response: {e}")

    def _extract_api_info(self, response):
        """Extrae información de la response"""
        try:
            request = response.request

            info = {
                'timestamp': datetime.now().isoformat(),
                'method': request.method,
                'url': response.url,
                'status': response.status,
                'status_text': response.status_text,
                'headers': dict(response.headers),
                'request_headers': dict(request.headers),
                'query_params': self._extract_query_params(response.url),
                'post_data': None,
                'response_body': None,
                'is_job_related': self._is_job_related_api(response.url)
            }

            # Extraer POST data si existe
            if request.method == 'POST' and request.post_data:
                try:
                    info['post_data'] = json.loads(request.post_data)
                except:
                    info['post_data'] = request.post_data[:500]

            # Extraer response body
            try:
                body_text = response.text()
                info['response_body'] = json.loads(body_text)

                # Analizar si contiene datos de trabajos
                info['contains_jobs'] = self._check_if_contains_jobs(info['response_body'])

            except:
                info['response_body'] = "No JSON"

            return info

        except Exception as e:
            print(f"[ERROR] Extrayendo info: {e}")
            return None

    def _extract_query_params(self, url):
        """Extrae parámetros de query"""
        try:
            parsed = urlparse(url)
            return dict(parse_qs(parsed.query))
        except:
            return {}

    def _check_if_contains_jobs(self, data):
        """Verifica si los datos contienen información de trabajos"""
        if not isinstance(data, dict):
            return False

        # Buscar keys que sugieran datos de trabajos
        job_keys = ['jobs', 'results', 'offers', 'avisos', 'postings', 'positions', 'items', 'data']

        for key in job_keys:
            if key in data:
                value = data[key]
                if isinstance(value, list) and len(value) > 0:
                    return True
                elif isinstance(value, dict):
                    # Podría ser {"items": [...], "total": 100}
                    for subkey in ['items', 'results', 'list']:
                        if subkey in value and isinstance(value[subkey], list):
                            return True

        return False

    def navigate(self, url, wait_time=10):
        """Navega a una URL y espera"""
        print(f"\n[NAVIGATE] {url}")
        self.page.goto(url, wait_until='networkidle', timeout=60000)
        print(f"[WAIT] Esperando {wait_time}s...")
        time.sleep(wait_time)

    def scroll_page(self, times=3, delay=2):
        """Hace scroll para cargar contenido dinamico"""
        print(f"\n[SCROLL] Haciendo scroll {times} veces...")
        for i in range(times):
            self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(delay)
            print(f"  Scroll {i+1}/{times}")

    def try_search(self, keyword="desarrollador"):
        """Intenta hacer una búsqueda"""
        print(f"\n[SEARCH] Buscando: {keyword}")

        try:
            # Intentar con diferentes selectores comunes
            selectors = [
                'input[type="search"]',
                'input[name="q"]',
                'input[name="query"]',
                'input[name="keyword"]',
                'input[placeholder*="uscar"]',  # "Buscar" o "buscar"
                '#search-input',
                '.search-input',
                '[data-testid="search-input"]'
            ]

            search_input = None
            for selector in selectors:
                try:
                    search_input = self.page.wait_for_selector(selector, timeout=3000)
                    if search_input.is_visible():
                        print(f"  [OK] Input encontrado: {selector}")
                        break
                except:
                    continue

            if search_input:
                search_input.fill(keyword)
                search_input.press('Enter')
                print(f"  [WAIT] Esperando resultados...")
                time.sleep(5)
                print(f"  [OK] Búsqueda ejecutada")
                return True
            else:
                print(f"  [WARN] No se encontró input de búsqueda")
                return False

        except Exception as e:
            print(f"  [ERROR] En búsqueda: {e}")
            return False

    def save_results(self):
        """Guarda los resultados en archivos JSON"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Guardar TODAS las llamadas API
        all_file = f"D:\\OEDE\\Webscrapping\\api_all_calls_{timestamp}.json"
        with open(all_file, 'w', encoding='utf-8') as f:
            json.dump(self.api_calls, f, indent=2, ensure_ascii=False)
        print(f"\n[SAVE] Todas las llamadas: {all_file}")
        print(f"       Total: {len(self.api_calls)} llamadas")

        # Guardar solo llamadas relacionadas con TRABAJOS
        job_file = f"D:\\OEDE\\Webscrapping\\api_job_calls_{timestamp}.json"
        with open(job_file, 'w', encoding='utf-8') as f:
            json.dump(self.job_related_calls, f, indent=2, ensure_ascii=False)
        print(f"[SAVE] Llamadas de trabajos: {job_file}")
        print(f"       Total: {len(self.job_related_calls)} llamadas")

        # Crear resumen de endpoints
        self._save_endpoints_summary(timestamp)

        # Crear análisis de estructura de datos
        self._analyze_job_structure(timestamp)

    def _save_endpoints_summary(self, timestamp):
        """Crea un resumen de endpoints únicos"""
        unique_endpoints = {}

        for call in self.api_calls:
            url_base = call['url'].split('?')[0]
            key = f"{call['method']} {url_base}"

            if key not in unique_endpoints:
                unique_endpoints[key] = {
                    'method': call['method'],
                    'url_base': url_base,
                    'count': 0,
                    'is_job_related': call.get('is_job_related', False),
                    'contains_jobs': call.get('contains_jobs', False),
                    'example_full_url': call['url'],
                    'example_params': call.get('query_params', {})
                }
            unique_endpoints[key]['count'] += 1

        summary_file = f"D:\\OEDE\\Webscrapping\\api_endpoints_summary_{timestamp}.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(list(unique_endpoints.values()), f, indent=2, ensure_ascii=False)

        print(f"[SAVE] Resumen de endpoints: {summary_file}")
        print(f"       Endpoints únicos: {len(unique_endpoints)}")

    def _analyze_job_structure(self, timestamp):
        """Analiza la estructura de los datos de trabajos"""
        print("\n[ANALYZE] Analizando estructura de datos de trabajos...")

        structures = []

        for call in self.job_related_calls:
            if call.get('contains_jobs') and isinstance(call.get('response_body'), dict):
                body = call['response_body']

                structure = {
                    'url': call['url'],
                    'method': call['method'],
                    'response_keys': list(body.keys()),
                    'sample_job': None
                }

                # Intentar extraer un trabajo de muestra
                for key in ['jobs', 'results', 'offers', 'avisos', 'items', 'data']:
                    if key in body and isinstance(body[key], list) and len(body[key]) > 0:
                        structure['jobs_key'] = key
                        structure['total_jobs'] = len(body[key])
                        structure['sample_job'] = body[key][0]  # Primer trabajo
                        break

                structures.append(structure)

        if structures:
            struct_file = f"D:\\OEDE\\Webscrapping\\job_data_structure_{timestamp}.json"
            with open(struct_file, 'w', encoding='utf-8') as f:
                json.dump(structures, f, indent=2, ensure_ascii=False)

            print(f"[SAVE] Estructura de datos: {struct_file}")
            print(f"       Estructuras encontradas: {len(structures)}")

            # Mostrar resumen de campos encontrados en ofertas
            if structures[0].get('sample_job'):
                print("\n[INFO] Campos encontrados en oferta de trabajo:")
                for field in structures[0]['sample_job'].keys():
                    print(f"       - {field}")
        else:
            print("[WARN] No se encontraron estructuras de datos de trabajos")

    def close(self):
        """Cierra el navegador"""
        if self.context:
            self.context.close()
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
        print("\n[CLOSE] Navegador cerrado")

    def run_discovery(self):
        """Ejecuta el proceso completo de descubrimiento"""
        try:
            print("="*80)
            print("ZONAJOBS API DISCOVERY - OFERTAS LABORALES")
            print("="*80)

            self.setup_browser(headless=True)

            # Fase 1: Página principal
            print("\n" + "="*80)
            print("FASE 1: Pagina Principal")
            print("="*80)
            self.navigate("https://www.zonajobs.com.ar/", wait_time=8)

            # Fase 2: Sección de empleos
            print("\n" + "="*80)
            print("FASE 2: Seccion de Empleos")
            print("="*80)
            self.navigate("https://www.zonajobs.com.ar/empleos", wait_time=8)
            self.scroll_page(times=2)

            # Fase 3: Búsqueda
            print("\n" + "="*80)
            print("FASE 3: Busqueda de Ofertas")
            print("="*80)
            self.try_search("desarrollador python")
            self.scroll_page(times=2)

            # Otra búsqueda para más datos
            self.try_search("analista de datos")
            self.scroll_page(times=2)

            # Guardar resultados
            print("\n" + "="*80)
            print("GUARDANDO RESULTADOS")
            print("="*80)
            self.save_results()

            print("\n" + "="*80)
            print("DESCUBRIMIENTO COMPLETADO")
            print("="*80)

        except Exception as e:
            print(f"\n[ERROR] {e}")
            import traceback
            traceback.print_exc()

        finally:
            self.close()


if __name__ == "__main__":
    discovery = ZonaJobsAPIDiscovery()
    discovery.run_discovery()
