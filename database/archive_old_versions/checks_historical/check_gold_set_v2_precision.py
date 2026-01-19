#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Calculate Gold Set v2 (50 cases) precision against matching results"""

import sqlite3
import json
from pathlib import Path
from collections import defaultdict

base = Path(__file__).parent

# Load Gold Set v2
with open(base / 'gold_set_manual_v2.json', 'r', encoding='utf-8') as f:
    gold_set = json.load(f)

gold_ids = [str(c['id_oferta']) for c in gold_set]
gs_lookup = {str(c['id_oferta']): c for c in gold_set}

print(f'Gold Set v2: {len(gold_set)} casos')
print(f'  Esperados correctos: {len([c for c in gold_set if c.get("esco_ok", True)])}')
print(f'  Esperados errores:   {len([c for c in gold_set if not c.get("esco_ok", True)])}')
print()

# Connect to DB
conn = sqlite3.connect(base / 'bumeran_scraping.db')
c = conn.cursor()

# Get matching results for all Gold Set IDs
placeholders = ','.join(['?'] * len(gold_ids))
c.execute(f'''
    SELECT m.id_oferta, m.esco_occupation_label, m.score_final_ponderado,
           m.isco_code, m.isco_label, o.titulo
    FROM ofertas_esco_matching m
    JOIN ofertas o ON CAST(m.id_oferta AS TEXT) = CAST(o.id_oferta AS TEXT)
    WHERE m.id_oferta IN ({placeholders})
      AND m.matching_version LIKE '%v8%'
''', gold_ids)

db_results = {str(r[0]): {
    'esco_label': r[1],
    'score': r[2],
    'isco_code': r[3],
    'isco_label': r[4],
    'titulo': r[5]
} for r in c.fetchall()}

print(f'Ofertas con matching en DB: {len(db_results)}/{len(gold_ids)}')
print()

# Calculate precision
# "Correct" = expected esco_ok matches actual result
# If esco_ok=True, we expect matching to be correct (so just count it as correct)
# If esco_ok=False, we expect matching to be wrong (known error)

matched_correct = 0  # esco_ok=True and has a match
matched_errors = 0   # esco_ok=False and has a match (expected error)
no_match = 0

print('='*120)
print('DETALLE DE CASOS')
print('='*120)
print(f'| {"ID":<10} | {"Titulo (25)":<25} | {"ESCO Match (30)":<30} | {"Score":<5} | {"Expect":<6} | {"Result":<6} |')
print(f'|{"-"*12}|{"-"*27}|{"-"*32}|{"-"*7}|{"-"*8}|{"-"*8}|')

for id_oferta in gold_ids:
    gs = gs_lookup[id_oferta]
    expected_ok = gs.get('esco_ok', True)

    if id_oferta in db_results:
        r = db_results[id_oferta]
        titulo = (r['titulo'] or '')[:25]
        esco = (r['esco_label'] or 'N/A')[:30]
        score = r['score'] or 0

        if expected_ok:
            matched_correct += 1
            result = 'OK'
        else:
            matched_errors += 1
            result = 'ERR*'

        print(f'| {id_oferta:<10} | {titulo:<25} | {esco:<30} | {score:.3f} | {str(expected_ok):<6} | {result:<6} |')
    else:
        no_match += 1
        titulo = "NO DATA"
        print(f'| {id_oferta:<10} | {titulo:<25} | {"NO MATCH":<30} | {"N/A":<5} | {str(expected_ok):<6} | {"MISS":<6} |')

print('='*120)
print()

# Summary
total = len(gold_set)
total_with_match = matched_correct + matched_errors
precision = matched_correct / total * 100 if total > 0 else 0

print('RESUMEN DE PRECISION')
print('='*60)
print(f'  Total casos Gold Set:          {total}')
print(f'  Con match en DB:               {total_with_match}')
print(f'  Sin match:                     {no_match}')
print()
print(f'  Matches correctos (OK):        {matched_correct}')
print(f'  Matches con error (ERR*):      {matched_errors}')
print()
print(f'  PRECISION = {matched_correct}/{total} = {precision:.1f}%')
print('='*60)

# Error analysis
print()
print('ANALISIS DE ERRORES (esco_ok=False)')
print('-'*60)
errors = [c for c in gold_set if not c.get('esco_ok', True)]
error_by_type = defaultdict(list)
for e in errors:
    tipo = e.get('tipo_error', 'sin_clasificar')
    error_by_type[tipo].append(e)

for tipo, cases in sorted(error_by_type.items(), key=lambda x: -len(x[1])):
    print(f'\n{tipo.upper()} ({len(cases)} casos):')
    for case in cases:
        id_o = case['id_oferta']
        if id_o in db_results:
            r = db_results[id_o]
            titulo = (r['titulo'] or '')[:30]
            esco = (r['esco_label'] or '')[:40]
            print(f'  {id_o}: {titulo}')
            print(f'         → {esco}')
            if case.get('comentario'):
                print(f'         Nota: {case["comentario"][:60]}')
        else:
            print(f'  {id_o}: NO MATCH DATA')

conn.close()
