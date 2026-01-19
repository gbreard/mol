"""
Analiza estructura HTML de ComputRabajo
"""

from bs4 import BeautifulSoup
import re

# Leer HTML
with open("../data/raw/computrabajo_sample.html", 'r', encoding='utf-8') as f:
    html = f.read()

soup = BeautifulSoup(html, 'html.parser')

print("="*70)
print("ANALISIS DE ESTRUCTURA HTML - COMPUTRABAJO")
print("="*70)

# 1. Buscar elementos con data-id
print("\n[*] Elementos con data-id:")
elements_with_data_id = soup.find_all(attrs={"data-id": True})
print(f"   Total encontrados: {len(elements_with_data_id)}")

if elements_with_data_id:
    print("\n   Ejemplo del primer elemento:")
    first = elements_with_data_id[0]
    print(f"   Tag: <{first.name}>")
    print(f"   Classes: {first.get('class', [])}")
    print(f"   data-id: {first.get('data-id')}")

    # Mostrar otros atributos data-*
    data_attrs = {k: v for k, v in first.attrs.items() if k.startswith('data-')}
    print(f"   Otros data-*: {list(data_attrs.keys())}")

    # Intentar extraer información
    print("\n   Contenido del elemento:")
    print(f"   Texto: {first.get_text(strip=True)[:200]}...")

# 2. Buscar artículos de ofertas
print("\n\n[*] Buscando patrones de ofertas:")
patterns = [
    ('article', {}),
    ('div', {'class': re.compile(r'.*job.*', re.I)}),
    ('div', {'class': re.compile(r'.*oferta.*', re.I)}),
    ('div', {'class': re.compile(r'.*aviso.*', re.I)}),
    ('li', {'class': re.compile(r'.*job.*', re.I)}),
]

for tag, attrs in patterns:
    elements = soup.find_all(tag, attrs)
    if elements:
        print(f"   - Encontrados {len(elements)} elementos: <{tag}> {attrs}")
        if len(elements) > 0:
            print(f"     Clases del primero: {elements[0].get('class', [])}")

# 3. Analizar primer elemento con data-id en detalle
if elements_with_data_id:
    print("\n\n[*] ANALISIS DETALLADO DEL PRIMER ELEMENTO:")
    first = elements_with_data_id[0]

    # Buscar título
    title_tags = first.find_all(['h2', 'h3', 'a'])
    if title_tags:
        print(f"   Posible título: {title_tags[0].get_text(strip=True)}")

    # Buscar empresa
    empresa_patterns = [
        first.find('span', class_=re.compile(r'.*empresa.*', re.I)),
        first.find('span', class_=re.compile(r'.*company.*', re.I)),
        first.find('strong'),
    ]
    for empresa in empresa_patterns:
        if empresa:
            print(f"   Posible empresa: {empresa.get_text(strip=True)}")
            break

    # Buscar ubicación
    ubicacion_patterns = [
        first.find('span', class_=re.compile(r'.*loc.*', re.I)),
        first.find('span', class_=re.compile(r'.*ubic.*', re.I)),
    ]
    for ubicacion in ubicacion_patterns:
        if ubicacion:
            print(f"   Posible ubicación: {ubicacion.get_text(strip=True)}")
            break

    # Mostrar HTML limpio
    print("\n   HTML del elemento (primeros 500 chars):")
    print(f"   {str(first)[:500]}...")

print("\n" + "="*70)
print("Análisis completado")
print("="*70)
