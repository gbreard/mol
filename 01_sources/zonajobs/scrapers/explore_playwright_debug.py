# -*- coding: utf-8 -*-
"""
Test de diagnóstico para ver todas las respuestas HTTP interceptadas
"""
from playwright.sync_api import sync_playwright
import time

print("Iniciando test de diagnóstico de Playwright...")
print()

all_responses = []

def response_handler(response):
    """Handler que captura TODAS las respuestas"""
    all_responses.append({
        'url': response.url,
        'status': response.status,
        'content_type': response.headers.get('content-type', '')
    })

    # Imprimir solo respuestas que parecen ser APIs
    if '/api/' in response.url:
        print(f"[API] {response.status} - {response.url}")

        # Si es la API de búsqueda, intentar ver el JSON
        if 'searchHomeV2' in response.url or 'search' in response.url:
            try:
                data = response.json()
                avisos = data.get('avisos', [])
                print(f"      -> {len(avisos)} avisos en respuesta")
            except:
                print(f"      -> No se pudo parsear JSON")

with sync_playwright() as p:
    print("Lanzando navegador...")
    browser = p.chromium.launch(headless=True)

    context = browser.new_context(
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        viewport={'width': 1920, 'height': 1080}
    )

    page = context.new_page()

    # Registrar handler ANTES de navegar
    page.on("response", response_handler)
    print("Handler registrado")
    print()

    # Navegar a búsqueda de Python
    url = "https://www.zonajobs.com.ar/empleos?q=python"
    print(f"Navegando a: {url}")
    page.goto(url, wait_until='networkidle', timeout=60000)

    print("\nEsperando que la página cargue...")
    time.sleep(3)

    # Scroll
    print("Scrolleando...")
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    time.sleep(2)

    browser.close()
    print("\nNavegador cerrado")

print()
print("="*70)
print("RESUMEN DE RESPUESTAS INTERCEPTADAS")
print("="*70)
print(f"Total de respuestas: {len(all_responses)}")

# Filtrar APIs
api_responses = [r for r in all_responses if '/api/' in r['url']]
print(f"Respuestas de API: {len(api_responses)}")

if api_responses:
    print("\nAPIs llamadas:")
    for resp in api_responses:
        print(f"  - {resp['status']} | {resp['url'][:100]}")
else:
    print("\n[PROBLEMA] No se interceptaron llamadas a APIs")
    print("\nResponses capturadas:")
    for resp in all_responses[:10]:  # Solo primeras 10
        print(f"  - {resp['status']} | {resp['url'][:80]}")
