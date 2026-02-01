#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
extract_esco_descriptions.py
============================
Extrae las descripciones en español de skills/conocimientos desde el RDF de ESCO.

Estructura del RDF ESCO:
  skill_uri → dct:description → node-literal-uri
  node-literal-uri → esco:language → "es"
  node-literal-uri → esco:nodeLiteral → "texto de descripción"

Outputs:
  - database/embeddings/descriptions_es.json (mapping URI → descripción)
  - También actualiza esco_skills_full.json directamente

Uso:
    python scripts/extract_esco_descriptions.py

Tiempo estimado: 15-30 minutos (RDF de 1.35 GB)
"""

import json
import sys
from pathlib import Path
from datetime import datetime

try:
    from rdflib import Graph, Namespace, Literal, URIRef
    from rdflib.namespace import DCTERMS, SKOS, RDF
except ImportError:
    print("ERROR: rdflib no instalado. Ejecutar: pip install rdflib")
    sys.exit(1)

# Rutas
RDF_PATH = Path(r'D:\Trabajos en PY\EPH-ESCO\01_datos_originales\Tablas_esco\Data\esco-v1.2.0.rdf')
SKILLS_JSON_PATH = Path(__file__).parent.parent / 'database' / 'embeddings' / 'esco_skills_full.json'
OUTPUT_PATH = Path(__file__).parent.parent / 'database' / 'embeddings' / 'descriptions_es.json'

# Namespace ESCO
ESCO = Namespace("http://data.europa.eu/esco/model#")


def main():
    print("=" * 70)
    print("EXTRACCION DE DESCRIPCIONES ESCO EN ESPAÑOL")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    # Verificar archivos
    if not RDF_PATH.exists():
        print(f"ERROR: RDF no encontrado: {RDF_PATH}")
        sys.exit(1)

    if not SKILLS_JSON_PATH.exists():
        print(f"ERROR: esco_skills_full.json no encontrado: {SKILLS_JSON_PATH}")
        sys.exit(1)

    # Cargar skills existentes para obtener URIs
    print(f"\n[1] Cargando skills existentes de {SKILLS_JSON_PATH.name}...")
    with open(SKILLS_JSON_PATH, 'r', encoding='utf-8') as f:
        skills_data = json.load(f)

    skills_dict = skills_data.get('skills', {})
    skill_uris = set(skills_dict.keys())
    print(f"    [OK] {len(skill_uris):,} skills cargados")

    # Cargar RDF
    print(f"\n[2] Cargando RDF ({RDF_PATH.stat().st_size / 1024 / 1024:.0f} MB)...")
    print("    Esto puede tomar 15-30 minutos...")

    graph = Graph()
    graph.parse(str(RDF_PATH), format='xml')
    print(f"    [OK] {len(graph):,} triples cargados")

    # PASO 1: Construir índice node-literal → (language, text)
    print("\n[3] Indexando node-literals...")
    node_literal_ns = "http://data.europa.eu/esco/node-literal/"
    node_literals = {}  # uri -> {"es": text, "en": text, ...}

    for subj in graph.subjects():
        subj_str = str(subj)
        if subj_str.startswith(node_literal_ns):
            lang = None
            text = None

            for p, o in graph.predicate_objects(subj):
                pred_str = str(p)
                if pred_str == str(ESCO.language):
                    lang = str(o)
                elif pred_str == str(ESCO.nodeLiteral):
                    text = str(o)

            if lang and text:
                if subj_str not in node_literals:
                    node_literals[subj_str] = {}
                node_literals[subj_str][lang] = text

    print(f"    [OK] {len(node_literals):,} node-literals indexados")

    # Contar idiomas disponibles
    lang_counts = {}
    for nl in node_literals.values():
        for lang in nl.keys():
            lang_counts[lang] = lang_counts.get(lang, 0) + 1

    print("    Idiomas encontrados:")
    for lang, count in sorted(lang_counts.items(), key=lambda x: -x[1])[:5]:
        print(f"      {lang}: {count:,}")

    # PASO 2: Extraer descripciones de skills
    print("\n[4] Extrayendo descripciones de skills...")

    descriptions = {}
    stats = {
        'es': 0,
        'en_fallback': 0,
        'no_description': 0
    }

    for skill_uri in skill_uris:
        skill_ref = URIRef(skill_uri)

        # Obtener todos los node-literal URIs de las descripciones
        desc_es = None
        desc_en = None

        for node_literal_uri in graph.objects(skill_ref, DCTERMS.description):
            nl_uri = str(node_literal_uri)
            if nl_uri in node_literals:
                nl_data = node_literals[nl_uri]
                if 'es' in nl_data:
                    desc_es = nl_data['es']
                if 'en' in nl_data and not desc_en:
                    desc_en = nl_data['en']

        # Priorizar español, fallback a inglés
        if desc_es:
            descriptions[skill_uri] = desc_es
            stats['es'] += 1
        elif desc_en:
            descriptions[skill_uri] = desc_en
            stats['en_fallback'] += 1
        else:
            stats['no_description'] += 1

    print(f"    Descripciones encontradas:")
    print(f"      - Español: {stats['es']:,}")
    print(f"      - Inglés (fallback): {stats['en_fallback']:,}")
    print(f"      - Sin descripción: {stats['no_description']:,}")
    print(f"      - Total extraídas: {len(descriptions):,}")

    # Guardar mapping de descripciones
    print(f"\n[5] Guardando {OUTPUT_PATH.name}...")
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(descriptions, f, ensure_ascii=False, indent=2)
    print(f"    [OK] {OUTPUT_PATH.stat().st_size / 1024:.1f} KB")

    # Actualizar esco_skills_full.json
    print(f"\n[6] Actualizando {SKILLS_JSON_PATH.name}...")
    updated_count = 0
    for uri, desc in descriptions.items():
        if uri in skills_dict:
            skills_dict[uri]['description'] = desc
            updated_count += 1

    # Guardar actualizado
    with open(SKILLS_JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(skills_data, f, ensure_ascii=False, indent=2)
    print(f"    [OK] {updated_count:,} skills actualizados con descripción")

    # Mostrar ejemplos
    print("\n[7] Ejemplos de descripciones extraídas:")
    for i, (uri, desc) in enumerate(descriptions.items()):
        if i >= 3:
            break
        label = skills_dict.get(uri, {}).get('label', 'N/A')
        print(f"\n    {label}:")
        print(f"    {desc[:200]}{'...' if len(desc) > 200 else ''}")

    # Resumen
    print("\n" + "=" * 70)
    print("RESUMEN")
    print("=" * 70)
    print(f"  Total skills: {len(skill_uris):,}")
    print(f"  Con descripción ES: {stats['es']:,}")
    print(f"  Con descripción EN (fallback): {stats['en_fallback']:,}")
    print(f"  Sin descripción: {stats['no_description']:,}")
    print(f"  Cobertura: {len(descriptions) / len(skill_uris) * 100:.1f}%")
    print(f"\n  Archivos generados:")
    print(f"    - {OUTPUT_PATH}")
    print(f"    - {SKILLS_JSON_PATH} (actualizado)")
    print("=" * 70)


if __name__ == '__main__':
    main()
