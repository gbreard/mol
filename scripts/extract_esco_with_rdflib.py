#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Extrae ocupaciones ESCO del RDF usando rdflib + SPARQL.

Este script lee el archivo RDF de ESCO v1.2.0 y extrae usando consultas SPARQL:
- URI de cada ocupación
- Código ESCO completo (ej: "5244.1")
- Label preferido en español
- Código ISCO (primeros 4 dígitos)
- Label ISCO en español

Output: JSON con todas las ocupaciones y sus códigos.

NOTA: Requiere ~2-3 GB de RAM para cargar el grafo RDF completo.

Uso:
    python extract_esco_with_rdflib.py             # Ejecutar extracción completa
    python extract_esco_with_rdflib.py --limit 100 # Solo primeras 100
"""

import json
import argparse
from pathlib import Path
import sys

# Check rdflib
try:
    import rdflib
except ImportError:
    print("Instalando rdflib...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "rdflib"])
    import rdflib


# Paths
DEFAULT_RDF_PATH = "/mnt/d/Trabajos en PY/EPH-ESCO/01_datos_originales/Tablas_esco/Data/esco-v1.2.0.rdf"
OUTPUT_PATH = "/mnt/d/OEDE/Webscrapping/database/embeddings/esco_occupations_full.json"


def extract_occupations(rdf_path: str, limit: int = None):
    """
    Extrae ocupaciones del RDF usando SPARQL.

    Args:
        rdf_path: Path al archivo RDF
        limit: Límite de ocupaciones (None = todas)
    """
    print(f"Cargando grafo RDF desde: {rdf_path}")
    print("Esto puede tomar varios minutos para un archivo de 1.3GB...")

    g = rdflib.Graph()
    g.parse(rdf_path, format="xml")
    print(f"Grafo cargado. Total tripletas: {len(g):,}")

    # Query para extraer ocupaciones con sus códigos y labels
    # Filtramos por ocupaciones que tienen URI con /occupation/
    limit_clause = f"LIMIT {limit}" if limit else ""

    query = f"""
    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
    PREFIX escom: <http://data.europa.eu/esco/model#>
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

    SELECT DISTINCT ?occupation ?label_es ?notation
    WHERE {{
        # Filtrar solo ocupaciones ESCO (no grupos ISCO ni skills)
        ?occupation rdf:type escom:Occupation .

        # Label preferido en español
        OPTIONAL {{
            ?occupation skos:prefLabel ?label_es .
            FILTER (lang(?label_es) = "es")
        }}

        # Notación (código)
        OPTIONAL {{
            ?occupation skos:notation ?notation .
        }}
    }}
    {limit_clause}
    """

    print("Ejecutando consulta SPARQL para ocupaciones...")
    results = g.query(query)

    occupations = []
    for row in results:
        occupation_uri = str(row.occupation) if row.occupation else ""
        label_es = str(row.label_es) if row.label_es else ""
        notation = str(row.notation) if row.notation else ""

        # Solo incluir si tiene URI de ocupación válida
        if '/esco/occupation/' not in occupation_uri:
            continue

        occupations.append({
            'uri': occupation_uri,
            'esco_code': notation,
            'esco_label': label_es,
            'isco_code': notation.split('.')[0] if '.' in notation else notation[:4] if notation else '',
        })

    print(f"Ocupaciones extraídas: {len(occupations)}")

    # Query para extraer grupos ISCO con sus labels
    print("Ejecutando consulta SPARQL para grupos ISCO...")
    isco_query = """
    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>

    SELECT DISTINCT ?isco_uri ?code ?label_es
    WHERE {
        ?isco_uri skos:notation ?code .
        FILTER (regex(str(?isco_uri), "/esco/isco/C"))
        FILTER (regex(?code, "^[0-9]{4}$"))

        OPTIONAL {
            ?isco_uri skos:prefLabel ?label_es .
            FILTER (lang(?label_es) = "es")
        }
    }
    """

    isco_results = g.query(isco_query)
    isco_labels = {}
    for row in isco_results:
        code = str(row.code) if row.code else ""
        label = str(row.label_es) if row.label_es else ""
        if code and len(code) == 4:
            isco_labels[code] = label

    print(f"Grupos ISCO con labels: {len(isco_labels)}")

    # Enriquecer ocupaciones con labels ISCO
    for occ in occupations:
        isco_code = occ.get('isco_code', '')
        occ['isco_label'] = isco_labels.get(isco_code, '')

    return occupations, isco_labels


def main():
    parser = argparse.ArgumentParser(description='Extrae ocupaciones ESCO del RDF')
    parser.add_argument('--input', type=str, default=DEFAULT_RDF_PATH,
                       help='Path al archivo RDF de ESCO')
    parser.add_argument('--output', type=str, default=OUTPUT_PATH,
                       help='Path de salida para el JSON')
    parser.add_argument('--limit', type=int, help='Límite de ocupaciones a extraer')

    args = parser.parse_args()

    occupations, isco_labels = extract_occupations(args.input, limit=args.limit)

    # Guardar resultados
    result = {
        'version': '1.2.0',
        'source': 'esco-v1.2.0.rdf',
        'total_occupations': len(occupations),
        'total_isco_groups': len(isco_labels),
        'occupations': occupations,
        'isco_labels': isco_labels
    }

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\n=== Extracción completada ===")
    print(f"Ocupaciones: {len(occupations)}")
    print(f"Grupos ISCO: {len(isco_labels)}")
    print(f"Archivo: {args.output}")

    # Mostrar muestra
    print("\nMuestra de ocupaciones con códigos:")
    sample = [o for o in occupations if o['esco_code']][:10]
    for occ in sample:
        print(f"  {occ['esco_code']:12} | {occ['isco_code']:4} | {occ['esco_label'][:50]}")


if __name__ == "__main__":
    main()
