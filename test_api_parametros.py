"""
Test diferentes payloads para encontrar qué parámetro falta
"""

import requests
import json
import uuid

session = requests.Session()
url = 'https://www.bumeran.com.ar/api/avisos/searchV2'

headers = {
    'Content-Type': 'application/json',
    'Accept': 'application/json, text/plain, */*',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Origin': 'https://www.bumeran.com.ar',
    'Referer': 'https://www.bumeran.com.ar/',
    'x-site-id': 'BMAR',
    'x-pre-session-token': str(uuid.uuid4())
}

print("="*70)
print("TEST: Diferentes payloads para encontrar la paginacion correcta")
print("="*70)

# Test 1: Con offset en lugar de page
print("\n1. TEST: Usando 'offset' en lugar de 'page'")
print("-"*70)

payloads = [
    {"pageSize": 5, "offset": 0, "sort": "FECHA"},
    {"pageSize": 5, "offset": 5, "sort": "FECHA"},
]

for i, payload in enumerate(payloads):
    print(f"\nPayload {i}: {json.dumps(payload)}")
    r = session.post(url, json=payload, headers=headers)
    if r.status_code == 200:
        data = r.json()
        if data.get('content'):
            ids = [a.get('id') for a in data['content'][:5]]
            print(f"  -> IDs: {ids}")
    else:
        print(f"  -> Error {r.status_code}")

# Test 2: Con from/to
print("\n2. TEST: Usando 'from'/'to' (pagination estilo ElasticSearch)")
print("-"*70)

payloads = [
    {"pageSize": 5, "from": 0, "sort": "FECHA"},
    {"pageSize": 5, "from": 5, "sort": "FECHA"},
]

for i, payload in enumerate(payloads):
    print(f"\nPayload {i}: {json.dumps(payload)}")
    r = session.post(url, json=payload, headers=headers)
    if r.status_code == 200:
        data = r.json()
        if data.get('content'):
            ids = [a.get('id') for a in data['content'][:5]]
            print(f"  -> IDs: {ids}")
    else:
        print(f"  -> Error {r.status_code}")

# Test 3: Revisar qué devuelve 'number' y 'size' en la respuesta
print("\n3. TEST: Analizar 'number' y 'size' en la respuesta")
print("-"*70)

for page_num in [0, 1, 2]:
    payload = {"pageSize": 5, "page": page_num, "sort": "FECHA"}
    r = session.post(url, json=payload, headers=headers)
    if r.status_code == 200:
        data = r.json()
        print(f"\nPage={page_num}:")
        print(f"  Response 'number': {data.get('number')}")
        print(f"  Response 'size': {data.get('size')}")
        print(f"  Content length: {len(data.get('content', []))}")
        if data.get('content'):
            ids = [a.get('id') for a in data['content'][:3]]
            print(f"  First 3 IDs: {ids}")

print("\n" + "="*70)
