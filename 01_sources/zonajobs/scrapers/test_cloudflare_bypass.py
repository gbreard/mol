# -*- coding: utf-8 -*-
"""
Test de bypass de Cloudflare usando técnicas de evasión manuales
"""
from playwright.sync_api import sync_playwright
import time
import random

print("Test de bypass Cloudflare con técnicas manuales...")
print()

# User agents reales
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
]

with sync_playwright() as p:
    # Lanzar navegador con args anti-detección
    browser = p.chromium.launch(
        headless=False,  # NO headless - Cloudflare detecta headless
        args=[
            '--disable-blink-features=AutomationControlled',
            '--disable-dev-shm-usage',
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-web-security',
            '--disable-features=IsolateOrigins,site-per-process',
            '--disable-site-isolation-trials',
        ]
    )

    # Context con configuración realista
    context = browser.new_context(
        user_agent=random.choice(USER_AGENTS),
        viewport={'width': 1920, 'height': 1080},
        locale='es-AR',
        timezone_id='America/Argentina/Buenos_Aires',
        geolocation={'latitude': -34.6037, 'longitude': -58.3816},  # Buenos Aires
        permissions=['geolocation'],
        color_scheme='light',
        device_scale_factor=1,
        has_touch=False,
        is_mobile=False,
        java_script_enabled=True,
    )

    # Extra headers
    context.set_extra_http_headers({
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'es-AR,es;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Cache-Control': 'max-age=0',
    })

    page = context.new_page()

    # Inyectar scripts anti-detección
    page.add_init_script("""
        // Ocultar webdriver
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });

        // Ocultar automation
        Object.defineProperty(navigator, 'plugins', {
            get: () => [1, 2, 3, 4, 5]
        });

        // Chrome runtime
        window.chrome = {
            runtime: {}
        };

        // Permissions
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ?
                Promise.resolve({ state: Notification.permission }) :
                originalQuery(parameters)
        );
    """)

    url = "https://www.zonajobs.com.ar/empleos?q=python"
    print(f"Navegando a: {url}")

    # Navegar
    page.goto(url, wait_until='load', timeout=60000)

    print("Esperando que Cloudflare procese (10 segundos)...")
    time.sleep(10)

    # Ver resultado
    titulo = page.title()
    print(f"\nTítulo de página: {titulo[:100]}")

    # Buscar ofertas
    ofertas = page.query_selector_all('a[href*="/avisos/"]')
    print(f"Ofertas encontradas: {len(ofertas)}")

    if len(ofertas) > 0:
        print("\n[OK] Cloudflare bypasseado exitosamente!")
        first = ofertas[0]
        href = first.get_attribute('href')
        print(f"  Primera oferta: {href}")
    else:
        content = page.content()
        if 'Cloudflare' in content or 'blocked' in content:
            print("\n[ERROR] Cloudflare sigue bloqueando")
            print("Se requiere modo NO headless o navegador real")
        else:
            print(f"\n[INFO] Página cargó ({len(content)} chars) pero no hay ofertas")
            # Guardar HTML para debug
            with open('zonajobs_debug.html', 'w', encoding='utf-8') as f:
                f.write(content)
            print("HTML guardado en zonajobs_debug.html")

    input("\nPresiona Enter para cerrar...")
    browser.close()

print("\nTest completado")
