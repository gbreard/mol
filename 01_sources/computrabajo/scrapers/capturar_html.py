"""
Captura HTML de ComputRabajo para analizar estructura
"""

from playwright.sync_api import sync_playwright
import time

def capturar_html(url="https://ar.computrabajo.com/trabajo-de-python"):
    """Captura HTML renderizado"""

    print(f"Capturando HTML de: {url}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        # Navegar
        page.goto(url, wait_until='networkidle', timeout=30000)
        time.sleep(5)

        # Obtener HTML
        html = page.content()

        # Guardar
        filename = "../data/raw/computrabajo_sample.html"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html)

        print(f"HTML guardado en: {filename}")
        print(f"Tamanio: {len(html)} caracteres")

        browser.close()

if __name__ == "__main__":
    capturar_html()
