"""
Investigar por qué la API de Bumeran no pagina correctamente
"""

import requests
import json
import uuid

session = requests.Session()
url = 'https://www.bumeran.com.ar/api/avisos/searchV2'

headers = {
    'Content-Type': 'application/json',
    'Accept': 'application/json, text/plain, */*',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Origin': 'https://www.bumeran.com.ar',
    'Referer': 'https://www.bumeran.com.ar/',
    'x-site-id': 'BMAR',
    'x-pre-session-token': str(uuid.uuid4())
}

print("="*70)
print("INVESTIGACION: API de Bumeran - Problema de paginacion")
print("="*70)

# Test 1: Página 0
print("\n1. TEST: Página 0 con payload básico")
print("-"*70)
payload0 = {
    "pageSize": 5,
    "page": 0,
    "sort": "FECHA"
}
print(f"Payload: {json.dumps(payload0, indent=2)}")

r0 = session.post(url, json=payload0, headers=headers)
print(f"Status: {r0.status_code}")

if r0.status_code == 200:
    data0 = r0.json()
    print(f"\nRespuesta:")
    print(f"  Total disponible: {data0.get('total', 'N/A')}")
    print(f"  Avisos en 'content': {len(data0.get('content', []))}")
    print(f"  Avisos en 'avisos': {len(data0.get('avisos', []))}")

    # Ver qué keys tiene la respuesta
    print(f"\nKeys en respuesta: {list(data0.keys())}")

    # Ver si hay avisos en algún lado
    if data0.get('content'):
        ids = [a.get('id') for a in data0['content']]
        print(f"  IDs en 'content': {ids[:5]}")

    if data0.get('avisos'):
        ids = [a.get('id') for a in data0['avisos']]
        print(f"  IDs en 'avisos': {ids[:5]}")
else:
    print(f"ERROR: {r0.status_code}")
    print(f"Response: {r0.text[:500]}")

# Test 2: Página 1
print("\n2. TEST: Página 1 con mismo payload")
print("-"*70)
payload1 = {
    "pageSize": 5,
    "page": 1,
    "sort": "FECHA"
}
print(f"Payload: {json.dumps(payload1, indent=2)}")

r1 = session.post(url, json=payload1, headers=headers)
print(f"Status: {r1.status_code}")

if r1.status_code == 200:
    data1 = r1.json()
    print(f"\nRespuesta:")
    print(f"  Total disponible: {data1.get('total', 'N/A')}")
    print(f"  Avisos en 'content': {len(data1.get('content', []))}")

    if data1.get('content'):
        ids = [a.get('id') for a in data1['content']]
        print(f"  IDs en 'content': {ids[:5]}")

        # Comparar con página 0
        if data0.get('content'):
            ids0 = [a.get('id') for a in data0['content']]
            ids1 = [a.get('id') for a in data1['content']]

            if ids0 == ids1:
                print("\n  [!!!] PROBLEMA: Página 0 y 1 tienen los MISMOS IDs")
            else:
                print("\n  [OK] Página 0 y 1 tienen IDs diferentes")

# Test 3: Ver estructura completa de UN aviso
print("\n3. TEST: Estructura de la respuesta")
print("-"*70)

if r0.status_code == 200:
    data = r0.json()
    print(f"Estructura completa de la respuesta:")
    print(json.dumps({k: type(v).__name__ for k, v in data.items()}, indent=2))

    # Si hay content, mostrar estructura de 1 aviso
    if data.get('content') and len(data['content']) > 0:
        print(f"\nEstructura de 1 aviso en 'content':")
        aviso = data['content'][0]
        print(json.dumps({k: type(v).__name__ for k, v in aviso.items()}, indent=2))

print("\n" + "="*70)
