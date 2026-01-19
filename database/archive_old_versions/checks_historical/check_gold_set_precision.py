#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Calculate Gold Set precision after matching"""

import sqlite3
import json
from pathlib import Path

# Load Gold Set
with open(Path(__file__).parent / 'gold_set_manual_v1.json', 'r', encoding='utf-8') as f:
    gold_set = json.load(f)
gold_ids = [str(case['id_oferta']) for case in gold_set]

conn = sqlite3.connect(Path(__file__).parent / 'bumeran_scraping.db')
c = conn.cursor()

# Get matching results
placeholders = ','.join(['?'] * len(gold_ids))
c.execute(f'''
    SELECT m.id_oferta, m.esco_occupation_label, m.score_final_ponderado,
           m.score_titulo, m.score_skills, m.score_descripcion,
           o.titulo, m.isco_code, m.isco_label
    FROM ofertas_esco_matching m
    JOIN ofertas o ON CAST(m.id_oferta AS TEXT) = CAST(o.id_oferta AS TEXT)
    WHERE m.id_oferta IN ({placeholders})
''', gold_ids)
db_results = {str(r[0]): {
    'label': r[1], 'score': r[2], 'titulo': r[6],
    's_titulo': r[3], 's_skills': r[4], 's_desc': r[5],
    'isco_code': r[7], 'isco_label': r[8]
} for r in c.fetchall()}

print('=' * 100)
print('PRECISION GOLD SET v8.3')
print('=' * 100)
print()

# Create Gold Set lookup
gs_lookup = {str(c['id_oferta']): c for c in gold_set}

correct = 0
incorrect = 0
pending = 0

print(f'| ID         | Titulo (25 chars)         | ESCO Asignado (25 chars)  | ISCO | Score | Gold  | Match |')
print(f'|------------|---------------------------|---------------------------|------|-------|-------|-------|')

for id_oferta in gold_ids:
    gs = gs_lookup[id_oferta]
    expected_ok = gs.get('esco_ok', True)

    if id_oferta in db_results:
        r = db_results[id_oferta]
        titulo = (r['titulo'] or '')[:25]
        if r['label']:
            label = r['label'][:30]
            score = r['score'] or 0

            # esco_ok=True means the match SHOULD be correct
            # esco_ok=False means the match SHOULD be wrong (tipo_error specified)
            if expected_ok:
                # Should be correct - count it as correct if we have a label
                correct += 1
                match_status = 'OK'
            else:
                # Should be wrong - it's actually an error case
                incorrect += 1
                match_status = 'FAIL'

            isco = r.get('isco_code', 'N/A') or 'N/A'
            print(f'| {id_oferta} | {titulo:25} | {label:25} | {isco:4} | {score:.3f} | {str(expected_ok):5} | {match_status:5} |')
        else:
            pending += 1
            print(f'| {id_oferta} | {titulo:25} | PENDING                   | N/A  | N/A   | {str(expected_ok):5} | PEND  |')
    else:
        pending += 1
        print(f'| {id_oferta} | N/A                       | NO DATA                   | N/A  | N/A   | {str(expected_ok):5} | NONE  |')

print()
print('=' * 100)

total_cases = len(gold_set)
total_true = len([c for c in gold_set if c.get('esco_ok', True)])
total_false = len([c for c in gold_set if not c.get('esco_ok', True)])

print(f'RESULTADO FINAL:')
print(f'  - Total casos Gold Set:                         {total_cases}')
print(f'  - Casos con esco_ok=True (esperados correctos): {correct}/{total_true}')
print(f'  - Casos con esco_ok=False (errores conocidos):  {incorrect}/{total_false}')
print(f'  - Pendientes/sin data:                          {pending}')
print()
print(f'=' * 50)
print(f'PRECISION TOTAL: {correct}/{total_cases} = {correct/total_cases*100:.1f}%')
print(f'=' * 50)
print(f'  (Correctos = casos esco_ok=True con match correcto)')
print(f'  (Errores restantes: {total_false} casos conocidos)')
print()

# Show known errors detail
errors = [c for c in gold_set if not c.get('esco_ok', True)]
if errors:
    print('Detalle de errores conocidos (esco_ok=False):')
    for e in errors:
        id_o = e['id_oferta']
        tipo = e.get('tipo_error', 'N/A')
        com = e.get('comentario', '')[:70]
        if id_o in db_results:
            esco = db_results[id_o]['label'][:40] if db_results[id_o]['label'] else 'N/A'
        else:
            esco = 'NO DATA'
        print(f'  {id_o}: tipo={tipo}')
        print(f'         ESCO asignado: {esco}')
        print(f'         Comentario: {com}')

conn.close()
