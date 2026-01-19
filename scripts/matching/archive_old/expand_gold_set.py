#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Select candidates to expand Gold Set from 19 to 50 cases"""

import sqlite3
import json
from pathlib import Path
from collections import defaultdict

# Load existing Gold Set
with open(Path(__file__).parent / 'gold_set_manual_v1.json', 'r', encoding='utf-8') as f:
    gold_set = json.load(f)
existing_ids = set(str(case['id_oferta']) for case in gold_set)
print(f'Gold Set actual: {len(existing_ids)} casos')

conn = sqlite3.connect(Path(__file__).parent / 'bumeran_scraping.db')
conn.row_factory = sqlite3.Row
c = conn.cursor()

# Get all valid candidates
c.execute('''
    SELECT m.id_oferta, o.titulo, m.esco_occupation_label, m.isco_code,
           m.isco_nivel1, m.isco_label, m.score_final_ponderado
    FROM ofertas_esco_matching m
    JOIN ofertas o ON CAST(m.id_oferta AS TEXT) = CAST(o.id_oferta AS TEXT)
    WHERE m.esco_occupation_label IS NOT NULL
      AND m.isco_code IS NOT NULL
      AND o.descripcion_utf8 IS NOT NULL
      AND o.descripcion_utf8 != ''
      AND m.matching_version LIKE '%v8.1%'
    ORDER BY m.score_final_ponderado DESC
''')

all_candidates = c.fetchall()
print(f'Candidatos totales (con matching v8.1): {len(all_candidates)}')

# Filter out existing gold set
candidates = [r for r in all_candidates if str(r['id_oferta']) not in existing_ids]
print(f'Candidatos disponibles (excluyendo gold set): {len(candidates)}')

# Categorize by score
high_score = [r for r in candidates if r['score_final_ponderado'] > 0.55]
mid_score = [r for r in candidates if 0.40 <= r['score_final_ponderado'] <= 0.55]
low_score = [r for r in candidates if r['score_final_ponderado'] < 0.40]

print(f'\nDistribucion por score:')
print(f'  Score > 0.55:     {len(high_score):4} candidatos')
print(f'  Score 0.40-0.55:  {len(mid_score):4} candidatos')
print(f'  Score < 0.40:     {len(low_score):4} candidatos')

# Categorize by ISCO nivel 1
by_isco = defaultdict(list)
for r in candidates:
    isco1 = r['isco_nivel1']
    if isco1:
        by_isco[isco1].append(r)

print(f'\nDistribucion por ISCO nivel 1:')
for isco in sorted(by_isco.keys()):
    print(f'  ISCO {isco}: {len(by_isco[isco]):4} candidatos')

# Select 31 candidates with balanced distribution
selected = []
used_ids = set()

def add_candidate(candidate, reason):
    if str(candidate['id_oferta']) not in used_ids:
        selected.append({
            'row': candidate,
            'reason': reason
        })
        used_ids.add(str(candidate['id_oferta']))
        return True
    return False

# Strategy: First ensure ISCO diversity, then fill by score
# Need at least 2 from each ISCO group (1-9)

print('\n' + '='*80)
print('SELECCION DE CANDIDATOS')
print('='*80)

# 1. First pass: 2 from each ISCO group (18 candidates)
isco_groups = ['1', '2', '3', '4', '5', '6', '7', '8', '9']
for isco in isco_groups:
    isco_candidates = by_isco.get(isco, [])
    # Try to get one high, one mid, one low score from each ISCO
    high_isco = [r for r in isco_candidates if r['score_final_ponderado'] > 0.55]
    mid_isco = [r for r in isco_candidates if 0.40 <= r['score_final_ponderado'] <= 0.55]
    low_isco = [r for r in isco_candidates if r['score_final_ponderado'] < 0.40]

    added = 0
    # Add one high if available
    if high_isco and added < 2:
        if add_candidate(high_isco[0], f'ISCO {isco} high'):
            added += 1
    # Add one mid if available
    if mid_isco and added < 2:
        if add_candidate(mid_isco[0], f'ISCO {isco} mid'):
            added += 1
    # Add one low if needed
    if low_isco and added < 2:
        if add_candidate(low_isco[0], f'ISCO {isco} low'):
            added += 1
    # Fill with any remaining
    for r in isco_candidates:
        if added >= 2:
            break
        if add_candidate(r, f'ISCO {isco} fill'):
            added += 1

print(f'Despues de diversificar ISCO: {len(selected)} candidatos')

# 2. Count current score distribution
current_high = len([s for s in selected if s['row']['score_final_ponderado'] > 0.55])
current_mid = len([s for s in selected if 0.40 <= s['row']['score_final_ponderado'] <= 0.55])
current_low = len([s for s in selected if s['row']['score_final_ponderado'] < 0.40])

print(f'Distribucion actual: high={current_high}, mid={current_mid}, low={current_low}')

# Target: 10 high, 11 mid, 10 low = 31 total
target_high = 10
target_mid = 11
target_low = 10

# 3. Fill remaining by score
remaining_high = [r for r in high_score if str(r['id_oferta']) not in used_ids]
remaining_mid = [r for r in mid_score if str(r['id_oferta']) not in used_ids]
remaining_low = [r for r in low_score if str(r['id_oferta']) not in used_ids]

# Add more high score
while current_high < target_high and remaining_high:
    if add_candidate(remaining_high.pop(0), 'high score fill'):
        current_high += 1

# Add more mid score
while current_mid < target_mid and remaining_mid:
    if add_candidate(remaining_mid.pop(0), 'mid score fill'):
        current_mid += 1

# Add more low score
while current_low < target_low and remaining_low:
    if add_candidate(remaining_low.pop(0), 'low score fill'):
        current_low += 1

# If still not at 31, fill with any remaining
while len(selected) < 31:
    if remaining_mid:
        if add_candidate(remaining_mid.pop(0), 'extra fill'):
            pass
    elif remaining_high:
        if add_candidate(remaining_high.pop(0), 'extra fill'):
            pass
    elif remaining_low:
        if add_candidate(remaining_low.pop(0), 'extra fill'):
            pass
    else:
        break

print(f'Seleccionados: {len(selected)} candidatos')

# Final distribution
final_high = len([s for s in selected if s['row']['score_final_ponderado'] > 0.55])
final_mid = len([s for s in selected if 0.40 <= s['row']['score_final_ponderado'] <= 0.55])
final_low = len([s for s in selected if s['row']['score_final_ponderado'] < 0.40])
print(f'Distribucion final: high={final_high}, mid={final_mid}, low={final_low}')

# Count by ISCO
final_isco = defaultdict(int)
for s in selected:
    final_isco[s['row']['isco_nivel1']] += 1
print(f'Por ISCO: {dict(sorted(final_isco.items()))}')

# Print table
print('\n' + '='*120)
print('CANDIDATOS PARA GOLD SET (31 nuevos)')
print('='*120)
print(f'| {"#":2} | {"ID":10} | {"Titulo (30 chars)":<30} | {"ESCO (30 chars)":<30} | {"ISCO":4} | {"Score":5} |')
print(f'|----|------------|--------------------------------|--------------------------------|------|-------|')

for i, s in enumerate(selected, 1):
    r = s['row']
    titulo = (r['titulo'] or '')[:30]
    esco = (r['esco_occupation_label'] or '')[:30]
    isco = r['isco_code'] or 'N/A'
    score = r['score_final_ponderado'] or 0
    print(f'| {i:2} | {r["id_oferta"]:10} | {titulo:<30} | {esco:<30} | {isco:4} | {score:.3f} |')

# Save to JSON for manual validation
candidates_json = []
for i, s in enumerate(selected, 1):
    r = s['row']
    candidates_json.append({
        'num': i,
        'id_oferta': str(r['id_oferta']),
        'titulo': r['titulo'],
        'esco_label': r['esco_occupation_label'],
        'isco_code': r['isco_code'],
        'isco_label': r['isco_label'],
        'score': round(r['score_final_ponderado'], 3) if r['score_final_ponderado'] else None,
        'esco_ok': None,  # To be filled manually
        'tipo_error': None,  # To be filled if esco_ok=False
        'comentario': ''  # To be filled manually
    })

output_file = Path(__file__).parent / 'gold_set_candidates.json'
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(candidates_json, f, ensure_ascii=False, indent=2)

print(f'\nGuardado en: {output_file}')

conn.close()
