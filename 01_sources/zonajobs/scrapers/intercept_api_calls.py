"""
Script para interceptar llamadas API de ZonaJobs usando Selenium Wire
Autor: Análisis de Web Scraping
Propósito: Descubrir endpoints API reales del sitio
"""

from seleniumwire import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json
from datetime import datetime


class ZonaJobsAPIInterceptor:
    def __init__(self):
        self.api_calls = []
        self.setup_driver()

    def setup_driver(self):
        """Configura el driver de Selenium Wire"""
        options = webdriver.ChromeOptions()

        # Opciones para parecer un navegador real
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)

        # Descomenta para modo headless (sin interfaz gráfica)
        # options.add_argument('--headless')

        # Configuración de Selenium Wire para interceptar requests
        seleniumwire_options = {
            'disable_encoding': True  # Para poder leer el contenido
        }

        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options,
            seleniumwire_options=seleniumwire_options
        )

        print("✓ Driver configurado correctamente")

    def intercept_requests(self, url, wait_time=10):
        """
        Navega a la URL y captura todas las llamadas API

        Args:
            url: URL del sitio a visitar
            wait_time: Tiempo de espera para que cargue la página (segundos)
        """
        print(f"\n🌐 Navegando a: {url}")
        self.driver.get(url)

        # Esperar a que cargue el contenido
        print(f"⏳ Esperando {wait_time} segundos para cargar contenido...")
        time.sleep(wait_time)

        # Capturar todas las requests
        print("\n📡 Analizando solicitudes interceptadas...\n")

        for request in self.driver.requests:
            # Filtrar solo las llamadas API (XHR/Fetch)
            if self._is_api_call(request):
                api_info = self._extract_api_info(request)
                if api_info:
                    self.api_calls.append(api_info)
                    self._print_api_call(api_info)

    def _is_api_call(self, request):
        """Determina si una request es una llamada API"""
        # Filtrar por tipo de contenido o URL patterns
        api_patterns = ['/api/', '/graphql', '.json', '/v1/', '/v2/']
        url = request.url.lower()

        # Excluir recursos estáticos
        static_extensions = ['.js', '.css', '.png', '.jpg', '.gif', '.svg', '.woff', '.ttf', '.ico']
        if any(url.endswith(ext) for ext in static_extensions):
            return False

        # Incluir si tiene patrones de API
        if any(pattern in url for pattern in api_patterns):
            return True

        # Incluir si es XHR/Fetch (basado en headers)
        if request.response:
            content_type = request.response.headers.get('Content-Type', '')
            if 'application/json' in content_type:
                return True

        return False

    def _extract_api_info(self, request):
        """Extrae información relevante de la request"""
        try:
            info = {
                'timestamp': datetime.now().isoformat(),
                'method': request.method,
                'url': request.url,
                'headers': dict(request.headers),
                'query_params': self._extract_query_params(request.url),
                'request_body': None,
                'response_status': None,
                'response_body': None
            }

            # Extraer body de la request si existe
            if request.body:
                try:
                    info['request_body'] = json.loads(request.body.decode('utf-8'))
                except:
                    info['request_body'] = request.body.decode('utf-8', errors='ignore')[:500]

            # Extraer response si existe
            if request.response:
                info['response_status'] = request.response.status_code

                try:
                    body = request.response.body.decode('utf-8')
                    info['response_body'] = json.loads(body)
                except:
                    info['response_body'] = "No JSON o error al decodificar"

            return info

        except Exception as e:
            print(f"❌ Error extrayendo info: {e}")
            return None

    def _extract_query_params(self, url):
        """Extrae parámetros de query de la URL"""
        from urllib.parse import urlparse, parse_qs
        parsed = urlparse(url)
        return parse_qs(parsed.query)

    def _print_api_call(self, info):
        """Imprime información de la llamada API de forma legible"""
        print("=" * 80)
        print(f"🔹 {info['method']} {info['url']}")
        print(f"📊 Status: {info['response_status']}")

        if info['query_params']:
            print(f"📝 Query Params: {info['query_params']}")

        if info['request_body']:
            print(f"📤 Request Body:")
            print(json.dumps(info['request_body'], indent=2)[:500])

        if info['response_body'] and isinstance(info['response_body'], dict):
            print(f"📥 Response Preview:")
            # Mostrar solo las keys principales
            print(json.dumps({k: type(v).__name__ for k, v in list(info['response_body'].items())[:5]}, indent=2))

        print()

    def simulate_search(self, search_term="python", location=""):
        """
        Simula una búsqueda en el sitio para capturar la API de búsqueda

        Args:
            search_term: Término a buscar
            location: Ubicación (opcional)
        """
        print(f"\n🔍 Simulando búsqueda: '{search_term}' en '{location or 'Todas las ubicaciones'}'")

        try:
            # Esperar a que cargue el formulario de búsqueda
            wait = WebDriverWait(self.driver, 10)

            # Aquí necesitarías los selectores reales del sitio
            # Esto es un ejemplo genérico
            search_input = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='search'], input[name='q'], input[placeholder*='buscar']"))
            )

            search_input.clear()
            search_input.send_keys(search_term)

            # Buscar botón de búsqueda y hacer clic
            search_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit'], button.search-btn")
            search_button.click()

            print("⏳ Esperando resultados...")
            time.sleep(5)

            print("✓ Búsqueda completada. Revisa las llamadas API capturadas.")

        except Exception as e:
            print(f"⚠️  No se pudo simular la búsqueda automáticamente: {e}")
            print("💡 Por favor, realiza la búsqueda manualmente en el navegador abierto")
            input("Presiona Enter cuando hayas terminado...")

    def save_results(self, filename="api_calls_zonajobs.json"):
        """Guarda los resultados en un archivo JSON"""
        filepath = f"D:\\OEDE\\Webscrapping\\{filename}"

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.api_calls, f, indent=2, ensure_ascii=False)

        print(f"\n💾 Resultados guardados en: {filepath}")
        print(f"📊 Total de llamadas API capturadas: {len(self.api_calls)}")

    def close(self):
        """Cierra el navegador"""
        self.driver.quit()
        print("\n👋 Navegador cerrado")


def main():
    """Función principal"""
    print("=" * 80)
    print("🕵️  INTERCEPTOR DE API - ZONAJOBS")
    print("=" * 80)

    interceptor = ZonaJobsAPIInterceptor()

    try:
        # Paso 1: Cargar página principal
        interceptor.intercept_requests("https://www.zonajobs.com.ar/", wait_time=8)

        # Paso 2: Intentar simular búsqueda (puede requerir ajustes de selectores)
        print("\n" + "=" * 80)
        print("🔍 FASE 2: Simulación de Búsqueda")
        print("=" * 80)

        interceptor.simulate_search(search_term="desarrollador python")

        # Capturar nuevas requests después de la búsqueda
        time.sleep(3)

        # Paso 3: Guardar resultados
        interceptor.save_results()

        # Mantener el navegador abierto para inspección manual si se desea
        print("\n💡 El navegador permanecerá abierto para inspección manual.")
        print("   Puedes interactuar con el sitio y las llamadas se seguirán capturando.")
        user_input = input("\n¿Deseas cerrar el navegador? (s/n): ")

        if user_input.lower() == 's':
            interceptor.close()
        else:
            print("\n✓ Navegador abierto. Cierra este script cuando termines.")
            input("Presiona Enter para finalizar y guardar todas las llamadas...")
            interceptor.save_results("api_calls_zonajobs_final.json")
            interceptor.close()

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        if hasattr(interceptor, 'driver'):
            try:
                interceptor.close()
            except:
                pass


if __name__ == "__main__":
    main()
