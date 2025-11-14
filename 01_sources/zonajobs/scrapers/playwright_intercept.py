"""
Script para interceptar llamadas API de ZonaJobs usando Playwright
Autor: Análisis de Web Scraping
Propósito: Descubrir endpoints API reales del sitio (alternativa más moderna a Selenium)
"""

from playwright.sync_api import sync_playwright, Route
import json
from datetime import datetime
import time


class PlaywrightAPIInterceptor:
    def __init__(self):
        self.api_calls = []
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

    def setup_browser(self, headless=False):
        """
        Configura el navegador con Playwright

        Args:
            headless: Si True, ejecuta sin interfaz gráfica
        """
        self.playwright = sync_playwright().start()

        # Lanzar navegador
        self.browser = self.playwright.chromium.launch(
            headless=headless,
            args=['--disable-blink-features=AutomationControlled']
        )

        # Crear contexto con user agent real
        self.context = self.browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080},
            locale='es-AR',
            timezone_id='America/Argentina/Buenos_Aires'
        )

        # Crear página
        self.page = self.context.new_page()

        # Configurar interceptores
        self._setup_interceptors()

        print("✓ Playwright configurado correctamente")

    def _setup_interceptors(self):
        """Configura los interceptores de requests y responses"""

        # Interceptar requests
        self.page.on("request", self._handle_request)

        # Interceptar responses
        self.page.on("response", self._handle_response)

        print("✓ Interceptores de red configurados")

    def _handle_request(self, request):
        """Maneja cada request saliente"""
        # Puedes filtrar aquí si lo deseas
        pass

    def _handle_response(self, response):
        """Maneja cada response entrante"""
        try:
            # Filtrar solo llamadas API relevantes
            if self._is_api_response(response):
                api_info = self._extract_api_info(response)
                if api_info:
                    self.api_calls.append(api_info)
                    self._print_api_call(api_info)

        except Exception as e:
            print(f"⚠️  Error procesando response: {e}")

    def _is_api_response(self, response):
        """Determina si una response es de una llamada API"""
        url = response.url.lower()

        # Excluir recursos estáticos
        static_extensions = ['.js', '.css', '.png', '.jpg', '.gif', '.svg', '.woff', '.ttf', '.ico', '.webp']
        if any(url.endswith(ext) for ext in static_extensions):
            return False

        # Incluir si tiene patrones de API
        api_patterns = ['/api/', '/graphql', '.json', '/v1/', '/v2/', '/jobs', '/search', '/offers']
        if any(pattern in url for pattern in api_patterns):
            return True

        # Incluir si es JSON
        content_type = response.headers.get('content-type', '')
        if 'application/json' in content_type:
            return True

        return False

    def _extract_api_info(self, response):
        """Extrae información relevante de la response"""
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
                'post_data': request.post_data if request.method == 'POST' else None,
                'response_body': None
            }

            # Intentar obtener el body de la response
            try:
                body_text = response.text()
                info['response_body'] = json.loads(body_text)
            except:
                # Si no es JSON válido
                info['response_body'] = "No JSON o error al parsear"

            return info

        except Exception as e:
            print(f"❌ Error extrayendo info: {e}")
            return None

    def _print_api_call(self, info):
        """Imprime información de la llamada API de forma legible"""
        print("=" * 80)
        print(f"🔹 {info['method']} {info['url']}")
        print(f"📊 Status: {info['status']} {info['status_text']}")

        if info['post_data']:
            print(f"📤 POST Data:")
            try:
                post_json = json.loads(info['post_data'])
                print(json.dumps(post_json, indent=2)[:500])
            except:
                print(info['post_data'][:500])

        if info['response_body'] and isinstance(info['response_body'], dict):
            print(f"📥 Response Preview:")
            # Mostrar estructura básica
            keys = list(info['response_body'].keys())[:10]
            print(f"   Keys: {keys}")

            # Si hay datos de trabajos, mostrar cuántos
            for key in ['jobs', 'results', 'data', 'items', 'offers']:
                if key in info['response_body'] and isinstance(info['response_body'][key], list):
                    print(f"   ✓ {key}: {len(info['response_body'][key])} items")

        print()

    def navigate_and_capture(self, url, wait_time=8):
        """
        Navega a la URL y captura todas las llamadas API

        Args:
            url: URL del sitio
            wait_time: Tiempo de espera en segundos
        """
        print(f"\n🌐 Navegando a: {url}")
        self.page.goto(url, wait_until='networkidle')

        print(f"⏳ Esperando {wait_time} segundos para capturar todas las requests...")
        time.sleep(wait_time)

        print("✓ Navegación completada")

    def simulate_search(self, search_term="python desarrollador"):
        """
        Simula una búsqueda en el sitio

        Args:
            search_term: Término a buscar
        """
        print(f"\n🔍 Simulando búsqueda: '{search_term}'")

        try:
            # Esperar a que cargue el input de búsqueda
            # Estos selectores son genéricos, ajustar según el sitio real
            search_selectors = [
                'input[type="search"]',
                'input[name="q"]',
                'input[placeholder*="Buscar"]',
                'input[placeholder*="buscar"]',
                '#search',
                '.search-input'
            ]

            search_input = None
            for selector in search_selectors:
                try:
                    search_input = self.page.wait_for_selector(selector, timeout=5000)
                    if search_input:
                        print(f"✓ Input encontrado con selector: {selector}")
                        break
                except:
                    continue

            if search_input:
                search_input.fill(search_term)
                search_input.press('Enter')

                print("⏳ Esperando resultados...")
                time.sleep(5)
                print("✓ Búsqueda completada")
            else:
                print("⚠️  No se encontró el input de búsqueda automáticamente")
                print("💡 Realiza la búsqueda manualmente en el navegador")
                input("Presiona Enter cuando hayas terminado...")

        except Exception as e:
            print(f"⚠️  Error en búsqueda automática: {e}")
            print("💡 Realiza la búsqueda manualmente")
            input("Presiona Enter cuando hayas terminado...")

    def scroll_page(self, times=3):
        """
        Hace scroll en la página para cargar más contenido

        Args:
            times: Número de veces a hacer scroll
        """
        print(f"\n📜 Haciendo scroll {times} veces para cargar más contenido...")

        for i in range(times):
            self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            print(f"   Scroll {i+1}/{times}")
            time.sleep(2)

        print("✓ Scroll completado")

    def save_results(self, filename="api_calls_playwright.json"):
        """Guarda los resultados en un archivo JSON"""
        filepath = f"D:\\OEDE\\Webscrapping\\{filename}"

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.api_calls, f, indent=2, ensure_ascii=False)

        print(f"\n💾 Resultados guardados en: {filepath}")
        print(f"📊 Total de llamadas API capturadas: {len(self.api_calls)}")

        # Crear resumen de endpoints únicos
        unique_endpoints = {}
        for call in self.api_calls:
            url = call['url']
            method = call['method']
            key = f"{method} {url.split('?')[0]}"  # URL sin query params

            if key not in unique_endpoints:
                unique_endpoints[key] = {
                    'method': method,
                    'url': url.split('?')[0],
                    'count': 0,
                    'example_full_url': url
                }
            unique_endpoints[key]['count'] += 1

        # Guardar resumen
        summary_path = f"D:\\OEDE\\Webscrapping\\api_endpoints_summary.json"
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(list(unique_endpoints.values()), f, indent=2, ensure_ascii=False)

        print(f"📋 Resumen de endpoints guardado en: {summary_path}")
        print(f"🔢 Endpoints únicos encontrados: {len(unique_endpoints)}")

    def close(self):
        """Cierra el navegador y Playwright"""
        if self.context:
            self.context.close()
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
        print("\n👋 Navegador cerrado")


def main():
    """Función principal"""
    print("=" * 80)
    print("🎭 INTERCEPTOR DE API CON PLAYWRIGHT - ZONAJOBS")
    print("=" * 80)

    interceptor = PlaywrightAPIInterceptor()

    try:
        # Configurar navegador (headless=False para ver el navegador)
        interceptor.setup_browser(headless=False)

        # Fase 1: Cargar página principal
        print("\n" + "=" * 80)
        print("📍 FASE 1: Página Principal")
        print("=" * 80)
        interceptor.navigate_and_capture("https://www.zonajobs.com.ar/")

        # Fase 2: Navegar a sección de empleos
        print("\n" + "=" * 80)
        print("📍 FASE 2: Sección de Empleos")
        print("=" * 80)
        interceptor.navigate_and_capture("https://www.zonajobs.com.ar/empleos")

        # Fase 3: Hacer scroll para cargar más
        interceptor.scroll_page(times=3)

        # Fase 4: Simular búsqueda
        print("\n" + "=" * 80)
        print("🔍 FASE 3: Simulación de Búsqueda")
        print("=" * 80)
        interceptor.simulate_search("desarrollador python")

        # Guardar resultados
        interceptor.save_results()

        # Opción de continuar explorando
        print("\n💡 ¿Deseas explorar más el sitio manualmente?")
        user_input = input("   (s/n): ")

        if user_input.lower() == 's':
            print("\n✓ Puedes interactuar con el sitio.")
            print("   Las llamadas se seguirán capturando.")
            input("\nPresiona Enter cuando termines para guardar y cerrar...")
            interceptor.save_results("api_calls_playwright_final.json")

        interceptor.close()

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        try:
            interceptor.close()
        except:
            pass


if __name__ == "__main__":
    main()
