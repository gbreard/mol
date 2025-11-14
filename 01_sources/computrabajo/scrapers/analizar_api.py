"""
Analiza en detalle las llamadas de API de ComputRabajo
Captura payloads y responses de endpoints clave
"""

from playwright.sync_api import sync_playwright
import json
import time
from datetime import datetime

class APIAnalyzer:
    def __init__(self):
        self.api_data = []

    def on_request(self, request):
        """Captura requests de API"""
        if any(endpoint in request.url for endpoint in ['/offer/', '/ajax/', 'collector']):
            data = {
                'type': 'REQUEST',
                'method': request.method,
                'url': request.url,
                'headers': dict(request.headers),
                'timestamp': datetime.now().isoformat()
            }

            # Intentar capturar payload
            try:
                if request.method == 'POST':
                    post_data = request.post_data
                    if post_data:
                        try:
                            data['payload'] = json.loads(post_data)
                        except:
                            data['payload'] = post_data[:500]
            except:
                pass

            self.api_data.append(data)
            print(f"\n[REQUEST] {request.method} {request.url}")
            if 'payload' in data:
                print(f"  Payload: {str(data['payload'])[:200]}")

    def on_response(self, response):
        """Captura responses de API"""
        if any(endpoint in response.url for endpoint in ['/offer/', '/ajax/', 'collector']):
            data = {
                'type': 'RESPONSE',
                'method': response.request.method,
                'url': response.url,
                'status': response.status,
                'headers': dict(response.headers),
                'timestamp': datetime.now().isoformat()
            }

            # Intentar capturar response body
            try:
                if 'application/json' in response.headers.get('content-type', ''):
                    body = response.json()
                    data['body'] = body
                    print(f"\n[RESPONSE] {response.status} {response.url}")
                    print(f"  Body preview: {str(body)[:300]}")

                    # Si contiene ofertas, analizarlo
                    if isinstance(body, dict):
                        if 'offers' in body or 'results' in body or 'data' in body:
                            print(f"  >> POSIBLE LISTA DE OFERTAS!")
                        if 'id' in body or 'title' in body or 'titulo' in body:
                            print(f"  >> POSIBLE DETALLE DE OFERTA!")

            except Exception as e:
                pass

            self.api_data.append(data)

    def analyze(self):
        """Ejecuta análisis"""
        url = "https://ar.computrabajo.com/trabajo-de-python"

        print("="*70)
        print("ANALISIS DETALLADO DE API - COMPUTRABAJO")
        print("="*70)
        print(f"\nURL: {url}\n")

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            page = context.new_page()

            # Configurar interceptores
            page.on('request', self.on_request)
            page.on('response', self.on_response)

            # Navegar
            print(">> Navegando...")
            page.goto(url, wait_until='networkidle', timeout=30000)
            print("OK Pagina cargada\n")

            # Esperar para capturar todo
            print(">> Esperando 15s para capturar llamadas...")
            time.sleep(15)

            # Scroll para activar lazy loading
            print(">> Scrolling...")
            for i in range(3):
                page.evaluate('window.scrollBy(0, window.innerHeight)')
                time.sleep(2)

            browser.close()

        # Guardar análisis
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"../data/raw/api_analysis_{timestamp}.json"

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.api_data, f, indent=2, ensure_ascii=False)

        print(f"\n{'='*70}")
        print("RESUMEN")
        print("="*70)
        print(f"Total de llamadas capturadas: {len(self.api_data)}")

        # Agrupar por URL
        urls = {}
        for item in self.api_data:
            url_key = item['url'].split('?')[0]
            if url_key not in urls:
                urls[url_key] = []
            urls[url_key].append(item['type'])

        print(f"\nEndpoints unicos: {len(urls)}")
        for url, types in urls.items():
            print(f"  - {url}")
            print(f"    Requests: {types.count('REQUEST')}, Responses: {types.count('RESPONSE')}")

        print(f"\nAnalisis guardado en: {filename}")
        print("="*70)

if __name__ == "__main__":
    analyzer = APIAnalyzer()
    analyzer.analyze()
