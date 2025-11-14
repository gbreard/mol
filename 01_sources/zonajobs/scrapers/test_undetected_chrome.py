# -*- coding: utf-8 -*-
"""
Test de bypass Cloudflare con undetected-chromedriver
"""
import undetected_chromedriver as uc
import time

print("Test con undetected-chromedriver...")
print()

# Opciones de Chrome
options = uc.ChromeOptions()
# options.add_argument('--headless')  # Comentado: headless puede ser detectado
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--disable-blink-features=AutomationControlled')

# Crear driver
print("Iniciando ChromeDriver...")
driver = uc.Chrome(options=options, version_main=None)  # version_main=None para auto-detect

try:
    url = "https://www.zonajobs.com.ar/empleos?q=python"
    print(f"Navegando a: {url}")

    driver.get(url)

    # Esperar que Cloudflare procese
    print("Esperando 10 segundos para Cloudflare...")
    time.sleep(10)

    # Obtener título
    titulo = driver.title
    print(f"\nTítulo de página: {titulo}")

    # Buscar ofertas
    ofertas = driver.find_elements("css selector", 'a[href*="/avisos/"]')
    print(f"Ofertas encontradas: {len(ofertas)}")

    if len(ofertas) > 0:
        print("\n[SUCCESS] Cloudflare bypasseado!")
        print(f"Primera oferta URL: {ofertas[0].get_attribute('href')}")

        # Ver si hay más elementos
        print(f"\nHTML title tag: {driver.find_element('tag name', 'title').get_attribute('textContent')}")
        result = "OK"
    else:
        # Verificar si es bloqueo de Cloudflare
        page_source = driver.page_source
        if 'Cloudflare' in page_source or 'blocked' in page_source.lower():
            print("\n[BLOCKED] Cloudflare sigue bloqueando")
            result = "BLOCKED"
        else:
            print("\n[UNKNOWN] Página cargó pero no hay ofertas")
            print(f"HTML length: {len(page_source)} chars")
            result = "NO_OFFERS"

    # Esperar antes de cerrar
    time.sleep(5)

finally:
    driver.quit()
    print("\nDriver cerrado")

print(f"\nResultado final: {result}")
