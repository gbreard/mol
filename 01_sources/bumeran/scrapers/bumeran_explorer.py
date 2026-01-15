"""
Explorador Técnico de Bumeran
==============================

Script para analizar la arquitectura técnica de Bumeran.com.ar
y determinar la mejor metodología de scraping.

Analiza:
1. Llamadas de red (API REST, GraphQL, etc.)
2. Estructura HTML
3. JavaScript rendering
4. Protecciones anti-bot
5. Cookies y headers necesarios
"""

from playwright.sync_api import sync_playwright
import json
import time
from datetime import datetime
from collections import defaultdict
import re

class BumeranExplorer:
    """Explorador técnico de Bumeran"""

    def __init__(self):
        self.network_calls = []
        self.api_endpoints = defaultdict(list)
        self.xhr_calls = []
        self.fetch_calls = []
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    def on_request(self, request):
        """Callback para requests"""
        # Ignorar recursos estáticos
        if request.resource_type in ['image', 'stylesheet', 'font', 'media']:
            return

        call_info = {
            'url': request.url,
            'method': request.method,
            'resource_type': request.resource_type,
            'headers': dict(request.headers),
            'post_data': request.post_data if request.method == 'POST' else None,
            'timestamp': datetime.now().isoformat()
        }

        self.network_calls.append(call_info)

        # Clasificar por tipo
        if 'api' in request.url.lower() or request.resource_type == 'xhr':
            self.xhr_calls.append(call_info)

        if 'fetch' in request.resource_type:
            self.fetch_calls.append(call_info)

        # Detectar endpoints de API
        if '/api/' in request.url or request.resource_type in ['xhr', 'fetch']:
            endpoint_key = f"{request.method} {request.url.split('?')[0]}"
            self.api_endpoints[endpoint_key].append(call_info)

            # Imprimir headers de API para debugging
            if '/api/avisos/' in request.url:
                print(f"\n[API CALL] {request.method} {request.url}")
                print(f"[HEADERS]")
                for key, value in request.headers.items():
                    if key.lower().startswith('x-'):
                        print(f"  {key}: {value}")

    def on_response(self, response):
        """Callback para responses"""
        # Solo procesar respuestas de API/XHR
        if response.request.resource_type not in ['xhr', 'fetch', 'document']:
            return

        try:
            # Intentar parsear como JSON
            if 'application/json' in response.headers.get('content-type', ''):
                try:
                    body = response.json()

                    # Buscar si contiene datos de ofertas
                    if self._contains_job_data(body):
                        print(f"\n[!] ENCONTRADO: Datos de ofertas en {response.url}")
                        print(f"   Metodo: {response.request.method}")
                        print(f"   Status: {response.status}")

                        # Guardar para análisis
                        self._save_response_sample(response.url, body)

                except Exception as e:
                    pass

        except Exception as e:
            pass

    def _contains_job_data(self, data):
        """Detecta si una respuesta contiene datos de ofertas"""
        # Convertir a string para buscar
        data_str = json.dumps(data).lower()

        # Palabras clave que indican ofertas de trabajo
        keywords = [
            'job', 'trabajo', 'empleo', 'oferta', 'aviso',
            'empresa', 'company', 'salario', 'salary',
            'puesto', 'position', 'vacante', 'vacancy'
        ]

        return any(keyword in data_str for keyword in keywords)

    def _save_response_sample(self, url, data):
        """Guarda una muestra de respuesta para análisis"""
        filename = f"../data/raw/api_sample_{self.timestamp}.json"

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump({
                'url': url,
                'data': data,
                'timestamp': datetime.now().isoformat()
            }, f, indent=2, ensure_ascii=False)

        print(f"   OK Muestra guardada en: {filename}")

    def explore(self, url="https://www.bumeran.com.ar/empleos-busqueda-ofertas.html", wait_time=10):
        """Explora Bumeran y analiza su arquitectura"""

        print("=" * 70)
        print("EXPLORADOR TÉCNICO DE BUMERAN")
        print("=" * 70)
        print(f"\nURL a explorar: {url}")
        print(f"Tiempo de espera: {wait_time}s")
        print("\nIniciando análisis...\n")

        with sync_playwright() as p:
            # Lanzar navegador
            browser = p.chromium.launch(headless=False)
            context = browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                viewport={'width': 1920, 'height': 1080}
            )

            page = context.new_page()

            # Configurar interceptores
            page.on('request', self.on_request)
            page.on('response', self.on_response)

            # Navegar a la página
            print(f">> Navegando a {url}...")
            try:
                page.goto(url, wait_until='networkidle', timeout=30000)
                print("OK Pagina cargada\n")
            except Exception as e:
                print(f"WARNING: Error cargando pagina: {e}")
                print("   Continuando con timeout...\n")

            # Esperar para capturar lazy loading
            print(f">> Esperando {wait_time}s para capturar llamadas...")
            time.sleep(wait_time)

            # Scroll para activar lazy loading
            print(">> Haciendo scroll para activar lazy loading...")
            for i in range(3):
                page.evaluate('window.scrollBy(0, window.innerHeight)')
                time.sleep(2)

            # Capturar HTML final
            html_content = page.content()

            # Cerrar navegador
            browser.close()

        # Analizar resultados
        self._analyze_results(html_content)

    def _analyze_results(self, html_content):
        """Analiza los resultados capturados"""

        print("\n" + "=" * 70)
        print("RESULTADOS DEL ANÁLISIS")
        print("=" * 70)

        # 1. Resumen de llamadas de red
        print(f"\n[*] LLAMADAS DE RED:")
        print(f"   Total de llamadas: {len(self.network_calls)}")
        print(f"   Llamadas XHR: {len(self.xhr_calls)}")
        print(f"   Llamadas Fetch: {len(self.fetch_calls)}")

        # 2. Endpoints de API detectados
        print(f"\n[*] ENDPOINTS DE API DETECTADOS: {len(self.api_endpoints)}")
        if self.api_endpoints:
            for endpoint, calls in list(self.api_endpoints.items())[:10]:
                print(f"   - {endpoint} ({len(calls)} veces)")

        # 3. Análisis de HTML
        print(f"\n[*] ANALISIS DE HTML:")
        print(f"   Tamanio del HTML: {len(html_content)} caracteres")

        # Buscar ofertas en HTML
        job_patterns = [
            r'<div[^>]*class="[^"]*job[^"]*"',
            r'<article[^>]*class="[^"]*oferta[^"]*"',
            r'data-job-id',
            r'data-aviso-id'
        ]

        html_has_jobs = False
        for pattern in job_patterns:
            matches = re.findall(pattern, html_content, re.IGNORECASE)
            if matches:
                print(f"   OK Encontrados {len(matches)} elementos con patron: {pattern[:30]}...")
                html_has_jobs = True

        if not html_has_jobs:
            print("   WARNING: No se detectaron ofertas en HTML inicial")

        # 4. Tecnologías detectadas
        print(f"\n[*] TECNOLOGIAS DETECTADAS:")
        techs = []

        if 'react' in html_content.lower():
            techs.append("React")
        if 'angular' in html_content.lower():
            techs.append("Angular")
        if 'vue' in html_content.lower():
            techs.append("Vue.js")
        if '__NEXT_DATA__' in html_content:
            techs.append("Next.js")
        if 'graphql' in str(self.network_calls).lower():
            techs.append("GraphQL")

        for tech in techs:
            print(f"   - {tech}")

        # 5. Recomendación de metodología
        print(f"\n[!] RECOMENDACION DE METODOLOGIA:")
        self._recommend_methodology(html_has_jobs)

        # Guardar análisis completo
        self._save_analysis()

    def _recommend_methodology(self, html_has_jobs):
        """Recomienda la mejor metodología de scraping"""

        if len(self.api_endpoints) > 0:
            print("   ==> RECOMENDACION: API REST")
            print("   Razon: Se detectaron endpoints de API")
            print("   Ventajas: Rapido, estructurado, facil de mantener")
            print("   Siguiente paso: Analizar endpoints y documentar API")

        elif html_has_jobs:
            print("   ==> RECOMENDACION: HTML Scraping")
            print("   Razon: Las ofertas estan en el HTML inicial")
            print("   Ventajas: Simple, no requiere JavaScript")
            print("   Siguiente paso: Parsear HTML con BeautifulSoup")

        else:
            print("   ==> RECOMENDACION: Playwright + Rendering")
            print("   Razon: Contenido cargado dinamicamente sin API clara")
            print("   Ventajas: Obtiene todo el contenido renderizado")
            print("   Desventajas: Mas lento, mas recursos")
            print("   Siguiente paso: Scraper con Playwright headless")

    def _save_analysis(self):
        """Guarda el análisis completo en archivo"""

        analysis = {
            'timestamp': self.timestamp,
            'total_calls': len(self.network_calls),
            'xhr_calls': len(self.xhr_calls),
            'fetch_calls': len(self.fetch_calls),
            'api_endpoints': {k: len(v) for k, v in self.api_endpoints.items()},
            'network_calls_sample': self.network_calls[:20]  # Primeras 20
        }

        filename = f"../data/raw/bumeran_analysis_{self.timestamp}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, indent=2, ensure_ascii=False)

        print(f"\n[OK] Analisis completo guardado en: {filename}")


if __name__ == "__main__":
    explorer = BumeranExplorer()

    # Explorar página principal de ofertas
    explorer.explore(
        url="https://www.bumeran.com.ar/empleos-busqueda-ofertas.html",
        wait_time=10
    )

    print("\n" + "=" * 70)
    print("Exploracion completada!")
    print("Revisa los archivos generados en ../data/raw/")
    print("=" * 70)
