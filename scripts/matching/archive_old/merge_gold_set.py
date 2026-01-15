#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Merge validated candidates into Gold Set v2 (50 cases)"""

import json
from pathlib import Path

base = Path(__file__).parent

# Load original Gold Set (19 cases)
with open(base / 'gold_set_manual_v1.json', 'r', encoding='utf-8') as f:
    original = json.load(f)
print(f'Gold Set original: {len(original)} casos')

# Load validated candidates (31 cases)
with open(base / 'gold_set_candidates_validated.json', 'r', encoding='utf-8') as f:
    candidates = json.load(f)
print(f'Candidatos validados: {len(candidates)} casos')

# Check for duplicates
original_ids = set(str(c['id_oferta']) for c in original)
candidates_ids = set(str(c['id_oferta']) for c in candidates)
overlap = original_ids & candidates_ids
if overlap:
    print(f'ADVERTENCIA: {len(overlap)} IDs duplicados: {overlap}')
else:
    print('No hay duplicados.')

# Merge (convert candidates to same format as original)
merged = original.copy()
for c in candidates:
    entry = {
        'id_oferta': c['id_oferta'],
        'esco_ok': c['esco_ok'],
    }
    if c['tipo_error']:
        entry['tipo_error'] = c['tipo_error']
    if c['comentario']:
        entry['comentario'] = c['comentario']
    merged.append(entry)

print(f'\nGold Set mergeado: {len(merged)} casos')

# Statistics
correct = len([c for c in merged if c.get('esco_ok', True)])
errors = len([c for c in merged if not c.get('esco_ok', True)])
print(f'  Correctos (esco_ok=true):  {correct}')
print(f'  Errores (esco_ok=false):   {errors}')

# Error type distribution
error_types = {}
for c in merged:
    if not c.get('esco_ok', True):
        tipo = c.get('tipo_error', 'sin_clasificar')
        error_types[tipo] = error_types.get(tipo, 0) + 1

print(f'\nDistribucion de errores:')
for tipo, cnt in sorted(error_types.items(), key=lambda x: -x[1]):
    print(f'  {tipo}: {cnt}')

# Save as v2
output_file = base / 'gold_set_manual_v2.json'
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(merged, f, ensure_ascii=False, indent=2)
print(f'\nGuardado: {output_file}')

# Also update gold_set_ids.txt
ids_file = base / 'gold_set_ids.txt'
with open(ids_file, 'w', encoding='utf-8') as f:
    for c in merged:
        f.write(f"{c['id_oferta']}\n")
print(f'IDs guardados: {ids_file}')
