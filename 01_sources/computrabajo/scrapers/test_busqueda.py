"""
Test rápido para explorar URLs de búsqueda de ComputRabajo
"""

from playwright.sync_api import sync_playwright
import time

def test_url(url, wait_time=15):
    """Prueba una URL y reporta hallazgos"""
    print(f"\n{'='*70}")
    print(f"EXPLORANDO: {url}")
    print('='*70)

    api_calls = []

    def on_request(request):
        if request.resource_type in ['xhr', 'fetch'] or '/api' in request.url:
            info = f"{request.method} {request.url}"
            if info not in api_calls:
                api_calls.append(info)
                print(f"  [API] {info}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.on('request', on_request)

        try:
            print(f"\n>> Navegando...")
            page.goto(url, wait_until='networkidle', timeout=30000)
            print(">> OK - Pagina cargada")

            # Esperar lazy loading
            print(f">> Esperando {wait_time}s...")
            time.sleep(wait_time)

            # Scroll
            print(">> Scrolling...")
            for i in range(3):
                page.evaluate('window.scrollBy(0, window.innerHeight)')
                time.sleep(2)

            # Analizar HTML
            html = page.content()
            print(f"\n>> Tamanio HTML: {len(html)} caracteres")

            # Buscar patrones de ofertas
            if 'oferta' in html.lower() or 'trabajo' in html.lower():
                # Contar posibles ofertas
                ofertas_count = html.lower().count('data-id')
                print(f">> Posibles ofertas detectadas: ~{ofertas_count}")

        except Exception as e:
            print(f"ERROR: {e}")

        finally:
            browser.close()

    print(f"\n>> Total API calls detectadas: {len(api_calls)}")
    for call in api_calls:
        print(f"   - {call}")

# Probar diferentes URLs
urls_to_test = [
    "https://ar.computrabajo.com/trabajo-de-python",
    "https://ar.computrabajo.com/empleos/",
    "https://ar.computrabajo.com/ofertas-de-trabajo",
]

print("EXPLORACION DE URLs DE COMPUTRABAJO")
print("="*70)

for url in urls_to_test:
    try:
        test_url(url, wait_time=10)
    except Exception as e:
        print(f"ERROR en {url}: {e}")

    print("\n\n")
    time.sleep(3)  # Delay entre URLs

print("\n" + "="*70)
print("EXPLORACION COMPLETADA")
print("="*70)
