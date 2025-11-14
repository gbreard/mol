# -*- coding: utf-8 -*-
"""
Test para inspeccionar la estructura HTML de las ofertas en ZonaJobs
"""
from playwright.sync_api import sync_playwright
import time

print("Inspeccionando estructura HTML de ZonaJobs...")
print()

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    url = "https://www.zonajobs.com.ar/empleos?q=python"
    print(f"Navegando a: {url}")
    page.goto(url, wait_until='networkidle', timeout=60000)
    time.sleep(3)

    print("\nBuscando elementos de ofertas...")
    print()

    # Probar diferentes selectores
    selectores = [
        'article',
        'article[data-id]',
        'div[class*="card"]',
        'div[class*="aviso"]',
        'div[class*="job"]',
        'a[href*="/avisos/"]',
    ]

    for selector in selectores:
        elements = page.query_selector_all(selector)
        print(f"  Selector '{selector}': {len(elements)} elementos")

    # Intentar encontrar las ofertas
    print("\n" + "="*70)
    print("Intentando extraer primera oferta...")
    print("="*70)

    # Obtener el HTML de las primeras ofertas
    ofertas = page.query_selector_all('a[href*="/avisos/"]')

    if ofertas:
        print(f"\nEncontradas {len(ofertas)} links de ofertas")
        print("\nPrimera oferta:")

        first = ofertas[0]

        # URL
        href = first.get_attribute('href')
        print(f"  URL: {href}")

        # Buscar título (h3, h2, etc)
        titulo_selectors = ['h3', 'h2', 'h1', '[class*="title"]', '[class*="heading"]']
        for sel in titulo_selectors:
            el = first.query_selector(sel)
            if el:
                print(f"  Título ({sel}): {el.inner_text()[:60]}")
                break

        # Buscar empresa
        empresa_selectors = ['[class*="company"]', '[class*="empresa"]', 'p', 'span']
        for sel in empresa_selectors:
            el = first.query_selector(sel)
            if el:
                text = el.inner_text().strip()
                if len(text) < 50:  # Probablemente es el nombre de empresa
                    print(f"  Empresa ({sel}): {text}")
                    break

        # HTML completo del elemento
        print("\n  HTML del elemento (primeros 500 chars):")
        html = first.inner_html()
        print(f"  {html[:500]}")

    else:
        print("\n[PROBLEMA] No se encontraron ofertas")
        print("\nHTML de la página (primeros 2000 chars):")
        print(page.content()[:2000])

    browser.close()

print("\nInspección completada")
