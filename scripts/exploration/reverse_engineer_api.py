"""
Reverse-engineer: Encontrar qué falta en nuestras requests
"""

import requests
import json
import uuid

print("="*70)
print("REVERSE ENGINEERING: API de Bumeran")
print("="*70)
print()
print("INSTRUCCIONES:")
print("1. Abre Chrome DevTools (F12)")
print("2. Ve a https://www.bumeran.com.ar/empleos-busqueda.html")
print("3. Ve a la pestaña 'Network' en DevTools")
print("4. Filtra por 'searchV2'")
print("5. Haz scroll para cargar más ofertas")
print("6. Click derecho en el request 'searchV2' -> Copy -> Copy as cURL")
print("7. Pega el comando curl completo aqui:")
print()
print("(O presiona Enter para probar con headers mejorados)")
print()

# Mientras tanto, probar con headers más completos
print("\n" + "="*70)
print("TEST 1: Headers más completos (simulando Chrome real)")
print("="*70)

session = requests.Session()
url = 'https://www.bumeran.com.ar/api/avisos/searchV2'

# Headers más completos basados en navegador real
headers_completos = {
    'accept': 'application/json, text/plain, */*',
    'accept-encoding': 'gzip, deflate, br',
    'accept-language': 'es-AR,es;q=0.9,en;q=0.8',
    'cache-control': 'no-cache',
    'content-type': 'application/json',
    'origin': 'https://www.bumeran.com.ar',
    'pragma': 'no-cache',
    'referer': 'https://www.bumeran.com.ar/empleos-busqueda.html',
    'sec-ch-ua': '"Google Chrome";v="119", "Chromium";v="119", "Not?A_Brand";v="24"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'x-site-id': 'BMAR',
    'x-pre-session-token': str(uuid.uuid4())
}

# Test con diferentes payloads
payloads_test = [
    # Payload básico actual
    {
        "name": "Basico actual",
        "payload": {
            "pageSize": 20,
            "page": 0,
            "sort": "FECHA"
        }
    },
    # Payload con más campos
    {
        "name": "Con filters vacio",
        "payload": {
            "pageSize": 20,
            "page": 0,
            "sort": "FECHA",
            "filters": []
        }
    },
    # Payload completo como podría enviarlo el navegador
    {
        "name": "Payload completo",
        "payload": {
            "pageSize": 20,
            "page": 0,
            "sort": "FECHA",
            "filters": [],
            "filtersApplied": [],
            "homeList": None
        }
    },
]

for test in payloads_test:
    print(f"\n{test['name']}:")
    print(f"Payload: {json.dumps(test['payload'], indent=2)}")

    r = session.post(url, json=test['payload'], headers=headers_completos)

    print(f"Status: {r.status_code}")

    if r.status_code == 200:
        data = r.json()
        content = data.get('content', [])
        print(f"  Ofertas recibidas: {len(content)}")

        if content:
            # Ver si realmente pagina
            ids = [o.get('id') for o in content[:5]]
            print(f"  Primeros 5 IDs: {ids}")

            # Probar página 1 con el mismo payload que funcionó
            payload_p1 = test['payload'].copy()
            payload_p1['page'] = 1

            r1 = session.post(url, json=payload_p1, headers=headers_completos)
            if r1.status_code == 200:
                data1 = r1.json()
                content1 = data1.get('content', [])
                ids1 = [o.get('id') for o in content1[:5]]

                if ids == ids1:
                    print(f"  [X] Pagina 1 tiene mismos IDs - NO funciona")
                else:
                    print(f"  [OK] Pagina 1 tiene IDs diferentes! - FUNCIONA")
                    print(f"       Primeros 5 IDs pagina 1: {ids1}")

print("\n" + "="*70)
print("TEST 2: Buscar endpoints alternativos")
print("="*70)

# Posibles endpoints alternativos
endpoints_alternativos = [
    'https://www.bumeran.com.ar/api/avisos/search',
    'https://www.bumeran.com.ar/api/avisos',
    'https://www.bumeran.com.ar/api/jobs',
    'https://api.bumeran.com.ar/avisos',
]

for endpoint in endpoints_alternativos:
    print(f"\nProbando: {endpoint}")
    try:
        r = session.post(endpoint, json={"pageSize": 5, "page": 0}, headers=headers_completos, timeout=5)
        print(f"  Status: {r.status_code}")

        if r.status_code == 200:
            try:
                data = r.json()
                print(f"  [OK] Responde JSON!")
                print(f"  Keys: {list(data.keys())[:5]}")
                if data.get('content'):
                    print(f"  Ofertas: {len(data.get('content'))}")
            except:
                print(f"  [X] No es JSON")
    except requests.exceptions.Timeout:
        print(f"  [X] Timeout")
    except Exception as e:
        print(f"  [X] Error: {str(e)[:50]}")

print("\n" + "="*70)
print("TEST 3: Ver estructura de response completa")
print("="*70)

r = session.post(url, json={"pageSize": 5, "page": 0, "sort": "FECHA"}, headers=headers_completos)
if r.status_code == 200:
    data = r.json()

    print("\nResponse Headers:")
    for k, v in r.headers.items():
        if 'token' in k.lower() or 'session' in k.lower() or 'auth' in k.lower():
            print(f"  {k}: {v}")

    print("\nResponse estructura:")
    print(json.dumps({
        'number': data.get('number'),
        'size': data.get('size'),
        'total': data.get('total'),
        'content_length': len(data.get('content', [])),
        'filters': len(data.get('filters', [])),
        'filtersApplied': data.get('filtersApplied'),
    }, indent=2))

print("\n" + "="*70)
