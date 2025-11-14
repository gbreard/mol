# -*- coding: utf-8 -*-
"""
Test rápido para determinar el formato correcto de búsqueda por keyword en ZonaJobs API
"""

import requests
import json
import uuid

BASE_URL = "https://www.zonajobs.com.ar"
API_SEARCH = f"{BASE_URL}/api/avisos/searchHomeV2"

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'es-AR,es;q=0.9',
    'Referer': 'https://www.zonajobs.com.ar/empleos',
    'Origin': 'https://www.zonajobs.com.ar',
    'x-site-id': 'ZJAR',
    'x-pre-session-token': str(uuid.uuid4())
})

# Obtener cookies
print("[1] Obteniendo cookies...")
response = session.get(f"{BASE_URL}/empleos")
print(f"   Cookies: {len(session.cookies)} cookies obtenidas\n")

# Probar diferentes formatos de búsqueda
test_keyword = "python"

tests = [
    {
        "name": "Sin filtros (baseline)",
        "payload": {
            "filterData": {
                "filtros": [],
                "tipoDetalle": "full",
                "busquedaExtendida": False
            },
            "page": 0,
            "pageSize": 22,
            "sort": "RECIENTES"
        }
    },
    {
        "name": "busquedaExtendida con keyword directo",
        "payload": {
            "filterData": {
                "filtros": [],
                "tipoDetalle": "full",
                "busquedaExtendida": True,
                "keyword": test_keyword
            },
            "page": 0,
            "pageSize": 22,
            "sort": "RECIENTES"
        }
    },
    {
        "name": "Filtro tipo 'palabraClave'",
        "payload": {
            "filterData": {
                "filtros": [
                    {
                        "tipo": "palabraClave",
                        "valor": test_keyword
                    }
                ],
                "tipoDetalle": "full",
                "busquedaExtendida": False
            },
            "page": 0,
            "pageSize": 22,
            "sort": "RECIENTES"
        }
    },
    {
        "name": "Filtro tipo 'keyword'",
        "payload": {
            "filterData": {
                "filtros": [
                    {
                        "type": "keyword",
                        "value": test_keyword
                    }
                ],
                "tipoDetalle": "full",
                "busquedaExtendida": False
            },
            "page": 0,
            "pageSize": 22,
            "sort": "RECIENTES"
        }
    },
    {
        "name": "Filtro tipo 'search'",
        "payload": {
            "filterData": {
                "filtros": [
                    {
                        "type": "search",
                        "value": test_keyword
                    }
                ],
                "tipoDetalle": "full",
                "busquedaExtendida": False
            },
            "page": 0,
            "pageSize": 22,
            "sort": "RECIENTES"
        }
    },
    {
        "name": "Campo 'query' directo",
        "payload": {
            "filterData": {
                "filtros": [],
                "tipoDetalle": "full",
                "busquedaExtendida": False,
                "query": test_keyword
            },
            "page": 0,
            "pageSize": 22,
            "sort": "RECIENTES"
        }
    }
]

print(f"Probando {len(tests)} formatos de búsqueda con keyword: '{test_keyword}'")
print("=" * 80)

for i, test in enumerate(tests, 1):
    print(f"\n[TEST {i}] {test['name']}")
    print(f"  Payload: {json.dumps(test['payload'], indent=2)[:150]}...")

    try:
        headers = session.headers.copy()
        headers['Content-Type'] = 'application/json'

        response = session.post(
            API_SEARCH,
            json=test['payload'],
            headers=headers,
            timeout=15
        )

        if response.status_code == 200:
            data = response.json()
            ofertas = data.get('avisos', [])
            total = data.get('total', 0)

            print(f"  [OK] Status: {response.status_code}")
            print(f"  Ofertas obtenidas: {len(ofertas)}")
            print(f"  Total disponibles: {total}")

            if ofertas:
                # Verificar si las ofertas contienen el keyword en título o descripción
                keyword_matches = 0
                for oferta in ofertas[:5]:  # Solo revisar las primeras 5
                    titulo = oferta.get('titulo', '').lower()
                    detalle = oferta.get('detalle', '').lower()
                    if test_keyword.lower() in titulo or test_keyword.lower() in detalle:
                        keyword_matches += 1

                print(f"  Ofertas con keyword en título/descripción: {keyword_matches}/{min(5, len(ofertas))}")

                if keyword_matches > 0:
                    print(f"  [SUCCESS] Este formato parece funcionar!")
                    print(f"\n  Ejemplo de oferta:")
                    print(f"    Título: {ofertas[0].get('titulo', 'N/A')}")
        else:
            print(f"  [FAIL] Status: {response.status_code}")
            print(f"  Response: {response.text[:200]}")

    except Exception as e:
        print(f"  [ERROR] {e}")

print("\n" + "=" * 80)
print("Tests completados")
