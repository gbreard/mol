"""
Test usando el JWT token de sesión que devuelve la API
"""

import requests
import json
import uuid

print("="*70)
print("TEST: Usando x-session-jwt token")
print("="*70)

session = requests.Session()
url = 'https://www.bumeran.com.ar/api/avisos/searchV2'

headers_base = {
    'accept': 'application/json, text/plain, */*',
    'content-type': 'application/json',
    'origin': 'https://www.bumeran.com.ar',
    'referer': 'https://www.bumeran.com.ar/empleos-busqueda.html',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'x-site-id': 'BMAR',
    'x-pre-session-token': str(uuid.uuid4())
}

# Paso 1: Hacer primera request para obtener el JWT
print("\n1. Primera request (obtener JWT)...")
r0 = session.post(url, json={"pageSize": 5, "page": 0, "sort": "FECHA"}, headers=headers_base)

print(f"   Status: {r0.status_code}")

# Extraer el JWT del response
jwt_token = r0.headers.get('x-session-jwt')
print(f"   JWT recibido: {jwt_token[:50]}..." if jwt_token else "   [!] No se recibio JWT")

if jwt_token:
    data0 = r0.json()
    ids0 = [o.get('id') for o in data0.get('content', [])[:5]]
    print(f"   IDs pagina 0: {ids0}")

    # Paso 2: Usar el JWT en la siguiente request (página 1)
    print("\n2. Segunda request con JWT (página 1)...")

    # Agregar el JWT a los headers
    headers_con_jwt = headers_base.copy()
    headers_con_jwt['x-session-jwt'] = jwt_token

    r1 = session.post(url, json={"pageSize": 5, "page": 1, "sort": "FECHA"}, headers=headers_con_jwt)

    print(f"   Status: {r1.status_code}")

    if r1.status_code == 200:
        data1 = r1.json()
        ids1 = [o.get('id') for o in data1.get('content', [])[:5]]
        print(f"   IDs pagina 1: {ids1}")

        if ids0 == ids1:
            print("\n   [X] Sigue devolviendo mismos IDs - JWT no ayudo")
        else:
            print("\n   [OK] IDs DIFERENTES! - JWT funciona!")
            print("\n   Probando pagina 2...")

            r2 = session.post(url, json={"pageSize": 5, "page": 2, "sort": "FECHA"}, headers=headers_con_jwt)
            if r2.status_code == 200:
                data2 = r2.json()
                ids2 = [o.get('id') for o in data2.get('content', [])[:5]]
                print(f"   IDs pagina 2: {ids2}")

                if ids2 not in [ids0, ids1]:
                    print("\n   [EXITO] Paginacion funciona con JWT!")
                else:
                    print("\n   [X] Pagina 2 tiene duplicados")

print("\n" + "="*70)
print("TEST 2: Probar con cookies de sesión")
print("="*70)

# Limpiar sesión
session2 = requests.Session()

# Primera request - esto debería setear cookies
print("\n1. Primera request (setear cookies)...")
r0 = session2.post(url, json={"pageSize": 5, "page": 0, "sort": "FECHA"}, headers=headers_base)

print(f"   Status: {r0.status_code}")
print(f"   Cookies: {dict(session2.cookies)}")

if r0.status_code == 200:
    data0 = r0.json()
    ids0 = [o.get('id') for o in data0.get('content', [])[:5]]
    print(f"   IDs pagina 0: {ids0}")

    # Segunda request con las mismas cookies
    print("\n2. Segunda request con cookies (página 1)...")
    r1 = session2.post(url, json={"pageSize": 5, "page": 1, "sort": "FECHA"}, headers=headers_base)

    if r1.status_code == 200:
        data1 = r1.json()
        ids1 = [o.get('id') for o in data1.get('content', [])[:5]]
        print(f"   IDs pagina 1: {ids1}")

        if ids0 != ids1:
            print("\n   [OK] Cookies funcionan para paginacion!")
        else:
            print("\n   [X] Cookies no ayudan")

print("\n" + "="*70)
