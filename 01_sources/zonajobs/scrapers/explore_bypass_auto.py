# -*- coding: utf-8 -*-
"""
Test automatizado de bypass Cloudflare
"""
from playwright.sync_api import sync_playwright
import time

print("Test automatizado de bypass Cloudflare...")

with sync_playwright() as p:
    # Intentar con headless=False (más probabilidad de éxito)
    browser = p.chromium.launch(
        headless=False,  # NO headless
        args=[
            '--disable-blink-features=AutomationControlled',
            '--disable-dev-shm-usage',
        ]
    )

    context = browser.new_context(
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        viewport={'width': 1920, 'height': 1080},
        locale='es-AR',
        timezone_id='America/Argentina/Buenos_Aires',
    )

    context.set_extra_http_headers({
        'Accept-Language': 'es-AR,es;q=0.9',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    })

    page = context.new_page()

    # Inyectar anti-detección
    page.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
    """)

    url = "https://www.zonajobs.com.ar/empleos?q=python"
    print(f"Navegando a: {url}")

    page.goto(url, wait_until='load', timeout=60000)
    print("Esperando 10 segundos...")
    time.sleep(10)

    # Verificar resultado
    titulo = page.title()
    print(f"\nTítulo: {titulo[:80]}")

    ofertas = page.query_selector_all('a[href*="/avisos/"]')
    print(f"Ofertas: {len(ofertas)}")

    if len(ofertas) > 0:
        print("\n[SUCCESS] Bypass exitoso!")
        print(f"Primera oferta: {ofertas[0].get_attribute('href')}")
        result = "OK"
    else:
        content = page.content()
        if 'Cloudflare' in content or 'blocked' in content:
            print("\n[BLOCKED] Cloudflare sigue bloqueando")
            result = "BLOCKED"
        else:
            print(f"\n[UNKNOWN] Página cargó pero no hay ofertas")
            result = "NO_OFFERS"

    # Cerrar automáticamente después de 5 segundos
    time.sleep(5)
    browser.close()

print(f"\nResultado: {result}")
