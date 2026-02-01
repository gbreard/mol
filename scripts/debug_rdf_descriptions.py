#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
debug_rdf_descriptions.py - Diagnóstico de descripciones en RDF
"""

import json
import sys
from pathlib import Path

try:
    from rdflib import Graph, Namespace, Literal, URIRef
    from rdflib.namespace import DCTERMS, SKOS, RDF
except ImportError:
    print("ERROR: rdflib no instalado")
    sys.exit(1)

RDF_PATH = Path(r'D:\Trabajos en PY\EPH-ESCO\01_datos_originales\Tablas_esco\Data\esco-v1.2.0.rdf')
SKILLS_JSON_PATH = Path(r'D:\OEDE\Webscrapping\database\embeddings\esco_skills_full.json')

print("=== DEBUG RDF DESCRIPTIONS ===\n")

# Cargar skills
print("[1] Cargando skills JSON...")
with open(SKILLS_JSON_PATH, 'r', encoding='utf-8') as f:
    skills_data = json.load(f)
skills_dict = skills_data.get('skills', {})
skill_uris = list(skills_dict.keys())[:5]  # Solo 5 para test
print(f"    Ejemplo URIs de skills:")
for uri in skill_uris:
    print(f"      {uri}")

print("\n[2] Cargando RDF (puede tardar)...")
graph = Graph()
graph.parse(str(RDF_PATH), format='xml')
print(f"    {len(graph):,} triples")

# Mostrar namespaces
print("\n[3] Namespaces en el RDF:")
for prefix, ns in graph.namespaces():
    if 'desc' in str(ns).lower() or 'dc' in str(ns).lower():
        print(f"    {prefix}: {ns}")

# Buscar predicados que contengan 'description'
print("\n[4] Predicados con 'description':")
desc_predicates = set()
for s, p, o in graph:
    if 'description' in str(p).lower():
        desc_predicates.add(str(p))
for pred in list(desc_predicates)[:10]:
    print(f"    {pred}")

# Buscar descripciones para un skill específico
print("\n[5] Buscando descripciones para primer skill...")
if skill_uris:
    test_uri = skill_uris[0]
    print(f"    URI: {test_uri}")
    skill_ref = URIRef(test_uri)

    print("\n    Todos los predicados para este skill:")
    count = 0
    for p, o in graph.predicate_objects(skill_ref):
        print(f"      {p} -> {str(o)[:100]}")
        count += 1
        if count > 20:
            print("      ... (truncado)")
            break

# Contar descripciones totales
print("\n[6] Contando dct:description totales...")
count_es = 0
count_en = 0
count_other = 0
sample_es = None

for s, p, o in graph:
    if 'description' in str(p).lower():
        if isinstance(o, Literal):
            lang = o.language
            if lang == 'es':
                count_es += 1
                if not sample_es:
                    sample_es = (str(s), str(o)[:200])
            elif lang == 'en':
                count_en += 1
            else:
                count_other += 1

print(f"    Español: {count_es:,}")
print(f"    Inglés: {count_en:,}")
print(f"    Otros: {count_other:,}")

if sample_es:
    print(f"\n    Ejemplo en español:")
    print(f"      URI: {sample_es[0]}")
    print(f"      Desc: {sample_es[1]}...")

# Verificar si las URIs de skills tienen formato diferente
print("\n[7] Comparando formatos de URI...")
print(f"    URI del JSON: {skill_uris[0] if skill_uris else 'N/A'}")

# Buscar skills en el RDF
skill_ns = Namespace("http://data.europa.eu/esco/skill/")
print(f"\n    Subjects que empiezan con {skill_ns}:")
skill_subjects = set()
for s in graph.subjects():
    if str(s).startswith(str(skill_ns)):
        skill_subjects.add(str(s))
        if len(skill_subjects) >= 5:
            break
for subj in skill_subjects:
    print(f"      {subj}")
