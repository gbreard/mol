#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Extrae ocupaciones ESCO del RDF oficial con códigos numéricos.

Lee el archivo RDF de ESCO v1.2.0 y extrae:
- URI de cada ocupación
- Código ESCO (skos:notation) ej: "5244.1"
- Label en español (skos:prefLabel xml:lang="es")
- Código ISCO (primeros 4 dígitos del código ESCO)

Output: JSON con todas las ocupaciones y sus códigos.

Uso:
    python extract_esco_occupations_from_rdf.py --input /path/to/esco.rdf
    python extract_esco_occupations_from_rdf.py --test  # Solo primeras 100
"""

import xml.sax
import json
import argparse
from pathlib import Path
from collections import defaultdict
import re


class ESCOOccupationExtractor(xml.sax.ContentHandler):
    """Extrae ocupaciones con códigos del RDF ESCO."""

    def __init__(self, max_occupations=None):
        self.max_occupations = max_occupations

        # Estado del parsing
        self.current_element = None
        self.current_attrs = {}
        self.current_content = ""
        self.current_lang = None

        # Recurso actual
        self.current_resource_uri = None
        self.current_resource_type = None
        self.in_occupation = False

        # Buffer para ocupación actual
        self.occupation_data = {}

        # Resultados
        self.occupations = []
        self.isco_groups = {}  # ISCO URI -> {code, label_es}

        # Contadores
        self.occupation_count = 0
        self.processed_elements = 0

    def startElement(self, name, attrs):
        self.current_element = name
        self.current_attrs = dict(attrs)
        self.current_content = ""
        self.current_lang = attrs.get('xml:lang')

        self.processed_elements += 1
        if self.processed_elements % 1000000 == 0:
            print(f"  Procesados: {self.processed_elements:,} elementos, {self.occupation_count} ocupaciones...")

        # Detectar inicio de recurso (rdf:Description o elemento con rdf:about)
        uri = attrs.get('rdf:about', '')

        # Detectar si es una ocupación ESCO
        if uri and '/esco/occupation/' in uri:
            if self.max_occupations and self.occupation_count >= self.max_occupations:
                return

            self.current_resource_uri = uri
            self.in_occupation = True
            self.occupation_data = {
                'uri': uri,
                'esco_code': '',
                'esco_label': '',
                'isco_code': '',
                'labels': {},  # lang -> label
                'notations': []
            }

        # Detectar grupo ISCO
        elif uri and '/esco/isco/C' in uri:
            # Es un grupo ISCO
            self.current_resource_uri = uri
            self.current_resource_type = 'isco'
            if uri not in self.isco_groups:
                self.isco_groups[uri] = {'uri': uri, 'code': '', 'label_es': '', 'labels': {}}

    def characters(self, content):
        self.current_content += content

    def endElement(self, name):
        content = self.current_content.strip()

        # Capturar datos si estamos en una ocupación
        if self.in_occupation and self.occupation_data:

            # skos:notation - El código numérico
            if name == 'skos:notation' and content:
                self.occupation_data['notations'].append(content)
                # Si es un código con punto (ej: "5244.1"), es el código ESCO
                if '.' in content:
                    self.occupation_data['esco_code'] = content
                    # Derivar ISCO (primeros 4 dígitos)
                    self.occupation_data['isco_code'] = content.split('.')[0]
                elif content.isdigit() and len(content) == 4:
                    # Si no hay código con punto pero hay 4 dígitos, es el ISCO
                    if not self.occupation_data['isco_code']:
                        self.occupation_data['isco_code'] = content

            # skos:prefLabel - Labels preferidos
            elif name == 'skos:prefLabel' and content:
                lang = self.current_lang or 'unknown'
                self.occupation_data['labels'][lang] = content
                if lang == 'es':
                    self.occupation_data['esco_label'] = content

        # Capturar datos de grupo ISCO
        if self.current_resource_type == 'isco' and self.current_resource_uri:
            uri = self.current_resource_uri
            if uri in self.isco_groups:
                if name == 'skos:notation' and content:
                    self.isco_groups[uri]['code'] = content
                elif name == 'skos:prefLabel' and content:
                    lang = self.current_lang or 'unknown'
                    self.isco_groups[uri]['labels'][lang] = content
                    if lang == 'es':
                        self.isco_groups[uri]['label_es'] = content

        # Detectar fin de ocupación
        if name in ['rdf:Description', 'skos:Concept', 'esco:Occupation']:
            if self.in_occupation and self.occupation_data.get('uri'):
                # Guardar solo si tiene código
                if self.occupation_data.get('esco_code') or self.occupation_data.get('notations'):
                    # Si no hay esco_code explícito, tomar el primer notation válido
                    if not self.occupation_data['esco_code'] and self.occupation_data['notations']:
                        for n in self.occupation_data['notations']:
                            if '.' in n or (n.isdigit() and len(n) >= 4):
                                if '.' in n:
                                    self.occupation_data['esco_code'] = n
                                    self.occupation_data['isco_code'] = n.split('.')[0]
                                else:
                                    self.occupation_data['isco_code'] = n[:4]
                                break

                    # Si no hay label en español, tomar inglés
                    if not self.occupation_data['esco_label']:
                        self.occupation_data['esco_label'] = self.occupation_data['labels'].get('en', '')

                    self.occupations.append({
                        'uri': self.occupation_data['uri'],
                        'esco_code': self.occupation_data['esco_code'],
                        'esco_label': self.occupation_data['esco_label'],
                        'isco_code': self.occupation_data['isco_code']
                    })
                    self.occupation_count += 1

                self.in_occupation = False
                self.occupation_data = {}

            # Reset ISCO tracking
            if self.current_resource_type == 'isco':
                self.current_resource_type = None
                self.current_resource_uri = None

        self.current_content = ""
        self.current_lang = None


def extract_occupations(rdf_path: str, max_occupations: int = None, output_path: str = None):
    """
    Extrae ocupaciones del RDF de ESCO.

    Args:
        rdf_path: Path al archivo RDF
        max_occupations: Límite de ocupaciones (None = todas)
        output_path: Path de salida para el JSON
    """
    print(f"Extrayendo ocupaciones de: {rdf_path}")
    print(f"Límite: {max_occupations or 'Todas'}")

    handler = ESCOOccupationExtractor(max_occupations=max_occupations)
    parser = xml.sax.make_parser()
    parser.setContentHandler(handler)

    try:
        with open(rdf_path, 'r', encoding='utf-8') as f:
            parser.parse(f)
    except xml.sax.SAXException as e:
        print(f"Parsing completado/interrumpido: {e}")
    except Exception as e:
        print(f"Error: {e}")

    print(f"\nResultados:")
    print(f"  Ocupaciones extraídas: {len(handler.occupations)}")
    print(f"  Grupos ISCO encontrados: {len(handler.isco_groups)}")

    # Crear tabla de ISCO labels
    isco_labels = {}
    for uri, data in handler.isco_groups.items():
        if data['code'] and data['label_es']:
            isco_labels[data['code']] = data['label_es']

    # Enriquecer ocupaciones con labels ISCO
    for occ in handler.occupations:
        isco_code = occ.get('isco_code', '')
        occ['isco_label'] = isco_labels.get(isco_code, '')

    # Guardar resultados
    if not output_path:
        output_path = Path(rdf_path).parent / 'esco_occupations_extracted.json'

    result = {
        'version': '1.2.0',
        'total_occupations': len(handler.occupations),
        'total_isco_groups': len(isco_labels),
        'occupations': handler.occupations,
        'isco_labels': isco_labels
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\nGuardado en: {output_path}")

    # Mostrar muestra
    print("\nMuestra de ocupaciones:")
    for occ in handler.occupations[:10]:
        print(f"  {occ['esco_code']:10} | {occ['isco_code']:4} | {occ['esco_label'][:50]}")

    return result


def main():
    parser = argparse.ArgumentParser(description='Extrae ocupaciones ESCO del RDF')
    parser.add_argument('--input', type=str,
                       default='/mnt/d/Trabajos en PY/EPH-ESCO/01_datos_originales/Tablas_esco/Data/esco-v1.2.0.rdf',
                       help='Path al archivo RDF de ESCO')
    parser.add_argument('--output', type=str, help='Path de salida para el JSON')
    parser.add_argument('--limit', type=int, help='Límite de ocupaciones a extraer')
    parser.add_argument('--test', action='store_true', help='Modo test (100 ocupaciones)')

    args = parser.parse_args()

    limit = args.limit
    if args.test:
        limit = 100

    output = args.output
    if not output:
        output = '/mnt/d/OEDE/Webscrapping/database/embeddings/esco_occupations_with_codes.json'

    extract_occupations(args.input, max_occupations=limit, output_path=output)


if __name__ == "__main__":
    main()
