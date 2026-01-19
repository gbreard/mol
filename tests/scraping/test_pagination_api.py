"""
Test directo de paginación de la API de Bumeran
"""

import requests
import json
import uuid

# Setup similar al scraper
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

print("Testeando paginación de la API de Bumeran")
print("=" * 70)

# Test página 0
print("\n1. Página 0:")
payload0 = {"pageSize": 5, "page": 0, "sort": "FECHA"}
resp0 = session.post(url, json=payload0, headers=headers)
print(f"   Status: {resp0.status_code}")

if resp0.status_code == 200:
    data0 = resp0.json()
    avisos0 = data0.get('avisos', [])
    ids0 = [a['id'] for a in avisos0]
    print(f"   Total disponible: {data0.get('total', 0):,}")
    print(f"   Avisos recibidos: {len(avisos0)}")
    print(f"   IDs: {ids0}")
else:
    print(f"   ERROR: {resp0.text[:200]}")
    exit(1)

# Test página 1
print("\n2. Página 1:")
payload1 = {"pageSize": 5, "page": 1, "sort": "FECHA"}
resp1 = session.post(url, json=payload1, headers=headers)
print(f"   Status: {resp1.status_code}")

if resp1.status_code == 200:
    data1 = resp1.json()
    avisos1 = data1.get('avisos', [])
    ids1 = [a['id'] for a in avisos1]
    print(f"   Total disponible: {data1.get('total', 0):,}")
    print(f"   Avisos recibidos: {len(avisos1)}")
    print(f"   IDs: {ids1}")
else:
    print(f"   ERROR: {resp1.text[:200]}")
    exit(1)

# Test página 2
print("\n3. Página 2:")
payload2 = {"pageSize": 5, "page": 2, "sort": "FECHA"}
resp2 = session.post(url, json=payload2, headers=headers)
print(f"   Status: {resp2.status_code}")

if resp2.status_code == 200:
    data2 = resp2.json()
    avisos2 = data2.get('avisos', [])
    ids2 = [a['id'] for a in avisos2]
    print(f"   Total disponible: {data2.get('total', 0):,}")
    print(f"   Avisos recibidos: {len(avisos2)}")
    print(f"   IDs: {ids2}")
else:
    print(f"   ERROR: {resp2.text[:200]}")
    exit(1)

# Análisis
print("\n" + "=" * 70)
print("ANÁLISIS:")
print("=" * 70)

overlap_0_1 = set(ids0).intersection(set(ids1))
overlap_1_2 = set(ids1).intersection(set(ids2))
overlap_0_2 = set(ids0).intersection(set(ids2))

print(f"\nIDs en común página 0 y 1: {len(overlap_0_1)} de 5")
print(f"IDs en común página 1 y 2: {len(overlap_1_2)} de 5")
print(f"IDs en común página 0 y 2: {len(overlap_0_2)} de 5")

if len(overlap_0_1) == 5:
    print("\n[ERROR] Páginas 0 y 1 tienen LOS MISMOS IDs!")
    print("        La API NO está paginando correctamente")
elif len(overlap_0_1) > 0:
    print(f"\n[WARNING] Hay {len(overlap_0_1)} IDs duplicados entre páginas")
else:
    print("\n[OK] Paginación funciona correctamente - sin duplicados")

print("\n" + "=" * 70)
