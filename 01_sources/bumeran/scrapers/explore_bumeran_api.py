"""
Test directo de la API de Bumeran
Probamos la API que descubrimos con el explorer
"""

import requests
import json
from datetime import datetime

def test_bumeran_api():
    """Prueba directa de la API de Bumeran"""

    print("="*70)
    print("TEST DIRECTO API BUMERAN")
    print("="*70)

    # Endpoint descubierto
    url = "https://www.bumeran.com.ar/api/avisos/searchV2"

    # Headers descubiertos con Playwright
    # x-site-id: BMAR (Bumeran Argentina)
    # x-pre-session-token: UUID (generamos uno nuevo)
    import uuid

    session_token = str(uuid.uuid4())

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Referer': 'https://www.bumeran.com.ar/empleos-busqueda-ofertas.html',
        'Origin': 'https://www.bumeran.com.ar',
        'x-site-id': 'BMAR',  # Bumeran Argentina
        'x-pre-session-token': session_token
    }

    print(f"\n[*] Headers configurados:")
    print(f"  x-site-id: BMAR")
    print(f"  x-pre-session-token: {session_token}")
    print("="*70)

    # Prueba 1: Sin filtros (obtener todas las ofertas)
    print("\n[TEST 1] Sin filtros - Todas las ofertas:")
    print("-" * 70)

    payload1 = {
        "pageSize": 20,
        "page": 0,
        "sort": "RELEVANTES"
    }

    try:
        response1 = requests.post(url, json=payload1, headers=headers, timeout=10)
        print(f"Status Code: {response1.status_code}")

        if response1.status_code == 200:
            data1 = response1.json()
            print(f"Total ofertas: {data1.get('total', 0)}")
            print(f"Ofertas en esta pagina: {len(data1.get('content', []))}")

            if len(data1.get('content', [])) > 0:
                print("\n[OK] EXITO! Encontramos ofertas")

                # Guardar muestra
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"../data/raw/bumeran_sample_{timestamp}.json"

                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(data1, f, indent=2, ensure_ascii=False)

                print(f"Muestra guardada en: {filename}")

                # Mostrar primera oferta
                first_job = data1['content'][0]
                print("\n[EJEMPLO] Primera oferta:")
                print(f"  ID: {first_job.get('id', 'N/A')}")
                print(f"  Titulo: {first_job.get('titulo', 'N/A')}")
                print(f"  Empresa: {first_job.get('empresa', 'N/A')}")
                print(f"  Ubicacion: {first_job.get('ubicacion', 'N/A')}")

                # Campos disponibles
                print(f"\n[CAMPOS] Campos disponibles en oferta:")
                for key in sorted(first_job.keys())[:15]:
                    print(f"  - {key}")

            else:
                print("[WARNING] No se encontraron ofertas")

        else:
            print(f"[ERROR] Status code: {response1.status_code}")
            print(response1.text[:500])

    except Exception as e:
        print(f"[ERROR] {e}")

    # Prueba 2: Con búsqueda específica
    print("\n\n[TEST 2] Búsqueda con keyword 'python':")
    print("-" * 70)

    payload2 = {
        "pageSize": 20,
        "page": 0,
        "sort": "RELEVANTES",
        "query": "python"
    }

    try:
        response2 = requests.post(url, json=payload2, headers=headers, timeout=10)
        print(f"Status Code: {response2.status_code}")

        if response2.status_code == 200:
            data2 = response2.json()
            print(f"Total ofertas con 'python': {data2.get('total', 0)}")
            print(f"Ofertas en esta pagina: {len(data2.get('content', []))}")
        else:
            print(f"[ERROR] Status code: {response2.status_code}")

    except Exception as e:
        print(f"[ERROR] {e}")

    # Prueba 3: Paginación
    print("\n\n[TEST 3] Prueba de paginación (página 1):")
    print("-" * 70)

    payload3 = {
        "pageSize": 20,
        "page": 1,  # Segunda página
        "sort": "RELEVANTES"
    }

    try:
        response3 = requests.post(url, json=payload3, headers=headers, timeout=10)
        print(f"Status Code: {response3.status_code}")

        if response3.status_code == 200:
            data3 = response3.json()
            print(f"Ofertas en pagina 1: {len(data3.get('content', []))}")
            print("[OK] Paginacion funciona")
        else:
            print(f"[ERROR] Status code: {response3.status_code}")

    except Exception as e:
        print(f"[ERROR] {e}")

    print("\n" + "="*70)
    print("Tests completados!")
    print("="*70)


if __name__ == "__main__":
    test_bumeran_api()
