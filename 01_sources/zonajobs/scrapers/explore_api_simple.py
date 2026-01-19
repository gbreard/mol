# -*- coding: utf-8 -*-
"""
Test simple de la API de ZonaJobs
Replica exactamente la llamada que funcionó en Playwright
"""

import requests
import json
import uuid

# URL y payload exactos que funcionaron
url = "https://www.zonajobs.com.ar/api/avisos/searchHomeV2"

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/json',
    'Accept-Language': 'es-AR',
    'Content-Type': 'application/json',
    'Referer': 'https://www.zonajobs.com.ar/',
    'Origin': 'https://www.zonajobs.com.ar',
    'x-site-id': 'ZJAR',
    'x-pre-session-token': str(uuid.uuid4())
}

# Payload exacto que funcionó
payload = {
    "filterData": {
        "filtros": [],
        "tipoDetalle": "full",
        "busquedaExtendida": False
    },
    "page": 0,
    "pageSize": 22,
    "sort": "RECIENTES"
}

print("Testeando API de ZonaJobs...")
print(f"URL: {url}")
print(f"Payload: {json.dumps(payload, indent=2)}")
print()

# Crear sesión y obtener cookies primero
session = requests.Session()

print("[1] Visitando página principal para obtener cookies...")
try:
    response = session.get("https://www.zonajobs.com.ar/", headers=headers, timeout=10)
    print(f"    Status: {response.status_code}")
    print(f"    Cookies: {len(session.cookies)}")
    for cookie in session.cookies:
        print(f"      - {cookie.name}: {cookie.value[:50]}...")
except Exception as e:
    print(f"    Error: {e}")

print()
print("[2] Haciendo llamada a API...")

try:
    response = session.post(url, json=payload, headers=headers, timeout=10)

    print(f"    Status Code: {response.status_code}")
    print(f"    Headers Response:")
    for key, value in response.headers.items():
        if 'content' in key.lower() or 'x-' in key.lower():
            print(f"      {key}: {value}")

    if response.status_code == 200:
        print()
        print("[SUCCESS] Respuesta exitosa!")
        data = response.json()

        print(f"\n    Keys en response: {list(data.keys())}")

        if 'avisos' in data:
            ofertas = data['avisos']
            print(f"    Total ofertas: {len(ofertas)}")

            if ofertas:
                print(f"\n    Primera oferta:")
                print(f"      ID: {ofertas[0].get('id')}")
                print(f"      Título: {ofertas[0].get('titulo')}")
                print(f"      Empresa: {ofertas[0].get('empresa')}")
                print(f"      Ubicación: {ofertas[0].get('localizacion')}")

                # Guardar respuesta completa
                with open('D:/OEDE/Webscrapping/test_api_response.json', 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                print(f"\n    [SAVED] Respuesta guardada en test_api_response.json")

    else:
        print(f"\n[ERROR] Status code: {response.status_code}")
        print(f"    Response text: {response.text[:500]}")

except Exception as e:
    print(f"\n[ERROR] Exception: {e}")
    import traceback
    traceback.print_exc()
