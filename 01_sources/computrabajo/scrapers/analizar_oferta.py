"""
Analiza estructura de una oferta individual de ComputRabajo
"""

from bs4 import BeautifulSoup
import json

# Leer HTML
with open("../data/raw/computrabajo_sample.html", 'r', encoding='utf-8') as f:
    html = f.read()

soup = BeautifulSoup(html, 'html.parser')

# Encontrar todas las ofertas
ofertas = soup.find_all('article', class_='box_offer')

print("="*70)
print(f"ANALISIS DE OFERTA - COMPUTRABAJO")
print("="*70)
print(f"\nTotal de ofertas encontradas: {len(ofertas)}\n")

if ofertas:
    # Analizar primera oferta
    oferta = ofertas[0]

    print("[*] ESTRUCTURA DE LA PRIMERA OFERTA:\n")

    # Buscar todos los atributos data-*
    data_attrs = {k: v for k, v in oferta.attrs.items() if k.startswith('data-')}
    print(f"Atributos data-*:")
    for key, value in data_attrs.items():
        print(f"   {key}: {value}")

    # Buscar título/puesto
    titulo = oferta.find('a', class_='js-o-link')
    if titulo:
        print(f"\nTítulo: {titulo.get_text(strip=True)}")
        print(f"URL: {titulo.get('href', '')}")

    # Buscar empresa
    empresa = oferta.find('p', class_='fs16')
    if empresa:
        empresa_nombre = empresa.find('a')
        if empresa_nombre:
            print(f"Empresa: {empresa_nombre.get_text(strip=True)}")
            print(f"URL Empresa: {empresa_nombre.get('href', '')}")

    # Buscar ubicación
    ubicacion = oferta.find('p', class_='fs13')
    if ubicacion:
        print(f"Ubicación: {ubicacion.get_text(strip=True)}")

    # Buscar salario
    salario = oferta.find('p', class_='fc_base')
    if salario:
        print(f"Salario: {salario.get_text(strip=True)}")

    # Buscar descripción
    descripcion = oferta.find('p', class_='fs16')
    if descripcion and descripcion != empresa:
        print(f"Descripción: {descripcion.get_text(strip=True)[:200]}...")

    # Buscar fecha
    fecha = oferta.find('span', class_='fs13')
    if fecha:
        print(f"Fecha: {fecha.get_text(strip=True)}")

    # Buscar etiquetas/tags
    tags = oferta.find_all('span', class_='tag')
    if tags:
        print(f"Tags: {[tag.get_text(strip=True) for tag in tags]}")

    print("\n" + "="*70)
    print("HTML COMPLETO DE LA PRIMERA OFERTA:")
    print("="*70)
    print(oferta.prettify()[:2000] + "\n...\n")

    # Analizar TODAS las ofertas y guardar estructura
    print("="*70)
    print("EXTRAYENDO TODAS LAS OFERTAS")
    print("="*70)

    ofertas_extraidas = []

    for i, oferta in enumerate(ofertas[:5]):  # Solo primeras 5 para prueba
        oferta_data = {}

        # Extraer campos
        titulo_elem = oferta.find('a', class_='js-o-link')
        if titulo_elem:
            oferta_data['titulo'] = titulo_elem.get_text(strip=True)
            oferta_data['url'] = titulo_elem.get('href', '')

        empresa_elem = oferta.find('p', class_='fs16')
        if empresa_elem:
            empresa_link = empresa_elem.find('a')
            if empresa_link:
                oferta_data['empresa'] = empresa_link.get_text(strip=True)

        ubicacion_elem = oferta.find('p', class_='fs13')
        if ubicacion_elem:
            oferta_data['ubicacion'] = ubicacion_elem.get_text(strip=True)

        # Data attrs
        for key, value in oferta.attrs.items():
            if key.startswith('data-'):
                oferta_data[key] = value

        ofertas_extraidas.append(oferta_data)

        print(f"\nOferta {i+1}:")
        print(json.dumps(oferta_data, indent=2, ensure_ascii=False))

    # Guardar muestra
    with open("../data/raw/ofertas_muestra.json", 'w', encoding='utf-8') as f:
        json.dump(ofertas_extraidas, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*70}")
    print(f"Muestra guardada en: ../data/raw/ofertas_muestra.json")
    print(f"Total ofertas en muestra: {len(ofertas_extraidas)}")
    print("="*70)
