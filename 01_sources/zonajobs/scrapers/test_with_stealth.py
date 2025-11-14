# -*- coding: utf-8 -*-
"""
Test con playwright-stealth para bypass Cloudflare
"""
from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync
import time

print("Test con playwright-stealth...")
print()

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)  # NO headless para ver qué pasa
    page = browser.new_page()

    # Aplicar stealth
    stealth_sync(page)
    print("Stealth aplicado")

    url = "https://www.zonajobs.com.ar/empleos?q=python"
    print(f"Navegando a: {url}")

    try:
        page.goto(url, wait_until='networkidle', timeout=60000)
        time.sleep(5)

        # Ver título
        titulo = page.title()
        print(f"\nTítulo de página: {titulo}")

        # Buscar ofertas
        ofertas = page.query_selector_all('a[href*="/avisos/"]')
        print(f"Ofertas encontradas: {len(ofertas)}")

        if len(ofertas) > 0:
            print("\n[OK] Cloudflare bypasseado!")
            print(f"\nPrimera oferta:")
            first = ofertas[0]
            href = first.get_attribute('href')
            print(f"  URL: {href}")

            # Buscar título
            titulo_el = first.query_selector('h3, h2')
            if titulo_el:
                print(f"  Título: {titulo_el.inner_text()[:60]}")
        else:
            print("\n[PROBLEMA] No se encontraron ofertas")
            print("\nHTML (primeros 1000 chars):")
            print(page.content()[:1000])

    except Exception as e:
        print(f"\nError: {e}")

    input("\nPresiona Enter para cerrar navegador...")
    browser.close()

print("\nTest completado")
