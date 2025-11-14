"""
Test si requests simples funcionan con ComputRabajo
o si requiere Playwright para JavaScript rendering
"""

import requests
from bs4 import BeautifulSoup

url = "https://ar.computrabajo.com/trabajo-de-python"

print("="*70)
print("TEST: requests vs Playwright")
print("="*70)
print(f"\nProbando URL: {url}\n")

# Test 1: Request simple
print("[TEST 1] Request simple con requests:")
try:
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    response = requests.get(url, headers=headers, timeout=30)
    print(f"   Status code: {response.status_code}")
    print(f"   Content-Length: {len(response.content)} bytes")

    # Parsear con BeautifulSoup
    soup = BeautifulSoup(response.content, 'html.parser')

    # Buscar ofertas
    ofertas = soup.find_all('article', class_='box_offer')
    print(f"   Ofertas encontradas: {len(ofertas)}")

    if len(ofertas) > 0:
        print("\n   >> OK: Ofertas encontradas con requests simple!")
        print("   >> METODOLOGIA RECOMENDADA: requests + BeautifulSoup")
        print("   >> Ventajas: Rapido, simple, bajo consumo de recursos")

        # Mostrar primera oferta como prueba
        primera = ofertas[0]
        titulo = primera.find('a', class_='js-o-link')
        if titulo:
            print(f"\n   Ejemplo - Titulo: {titulo.get_text(strip=True)}")
            print(f"   Ejemplo - data-id: {primera.get('data-id')}")

    elif response.status_code == 403:
        print("\n   >> ERROR 403: Sitio bloquea requests")
        print("   >> METODOLOGIA RECOMENDADA: Playwright")

    else:
        print("\n   >> WARNING: No se encontraron ofertas")
        print("   >> Posibles razones:")
        print("      - Requiere JavaScript rendering")
        print("      - Estructura HTML diferente")
        print("      - Bloqueo por User-Agent")
        print("\n   >> METODOLOGIA RECOMENDADA: Playwright")

        # Analizar HTML recibido
        print(f"\n   HTML recibido (primeros 500 chars):")
        print(f"   {response.text[:500]}")

except requests.RequestException as e:
    print(f"   ERROR: {e}")
    print("   >> METODOLOGIA RECOMENDADA: Playwright")

print("\n" + "="*70)
print("Conclusion del test")
print("="*70)
