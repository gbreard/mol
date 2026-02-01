#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
debug_rdf_nodeliteral.py - Investigar estructura de node-literal
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

print("=== DEBUG NODE-LITERAL ===\n")

print("[1] Cargando RDF...")
graph = Graph()
graph.parse(str(RDF_PATH), format='xml')
print(f"    {len(graph):,} triples")

# Buscar un node-literal de ejemplo
NODE_LITERAL_URI = "http://data.europa.eu/esco/node-literal/3633c789-b29f-4611-aa95-47e1f5d6b8b8"
node_ref = URIRef(NODE_LITERAL_URI)

print(f"\n[2] Investigando node-literal de ejemplo:")
print(f"    URI: {NODE_LITERAL_URI}")
print(f"\n    Predicados y objetos:")
for p, o in graph.predicate_objects(node_ref):
    obj_str = str(o)
    lang = ""
    if isinstance(o, Literal) and o.language:
        lang = f" @{o.language}"
    print(f"      {p}")
    print(f"        -> {obj_str[:150]}{lang}")

# Buscar qué predicado tiene el texto
print(f"\n[3] Buscando predicados comunes en node-literals...")
node_literal_ns = Namespace("http://data.europa.eu/esco/node-literal/")
predicates_found = {}
count = 0
for s in graph.subjects():
    if str(s).startswith(str(node_literal_ns)):
        for p, o in graph.predicate_objects(s):
            pred_str = str(p)
            if pred_str not in predicates_found:
                predicates_found[pred_str] = 0
            predicates_found[pred_str] += 1
        count += 1
        if count >= 100:  # Solo analizar 100 node-literals
            break

print(f"    Predicados encontrados en {count} node-literals:")
for pred, cnt in sorted(predicates_found.items(), key=lambda x: -x[1]):
    print(f"      {pred}: {cnt}")

# Buscar descripciones en español directamente
print(f"\n[4] Buscando literales con @es...")
count_es = 0
sample = None
for s, p, o in graph:
    if isinstance(o, Literal) and o.language == 'es':
        count_es += 1
        if not sample and len(str(o)) > 50:
            sample = (str(s), str(p), str(o)[:200])
        if count_es >= 10:
            break

print(f"    Encontrados: {count_es}+ literales @es")
if sample:
    print(f"\n    Ejemplo:")
    print(f"      Subject: {sample[0]}")
    print(f"      Predicate: {sample[1]}")
    print(f"      Object: {sample[2]}...")
