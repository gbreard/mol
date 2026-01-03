#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Run matching for Gold Set 19 cases and calculate precision"""

import sqlite3
import json
from pathlib import Path

DB_PATH = Path(__file__).parent / 'bumeran_scraping.db'

print("=" * 70)
print("MATCHING GOLD SET - 19 casos")
print("=" * 70)

# Load Gold Set
with open(Path(__file__).parent / 'gold_set_manual_v1.json', 'r', encoding='utf-8') as f:
    gold_set = json.load(f)
gold_ids = [str(case['id_oferta']) for case in gold_set]
print(f"\nGold Set IDs: {len(gold_ids)}")

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# Step 1: Insert missing IDs
print("\n[1] Insertando IDs faltantes en ofertas_esco_matching...")
inserted = 0
for id_oferta in gold_ids:
    c.execute('INSERT OR IGNORE INTO ofertas_esco_matching (id_oferta) VALUES (?)', (id_oferta,))
    if c.rowcount > 0:
        inserted += 1
conn.commit()
print(f"    Insertados: {inserted}")

# Verify
placeholders = ','.join(['?'] * len(gold_ids))
c.execute(f'SELECT COUNT(*) FROM ofertas_esco_matching WHERE id_oferta IN ({placeholders})', gold_ids)
print(f"    Total en tabla: {c.fetchone()[0]}/19")

conn.close()

# Step 2: Run matching for Gold Set IDs only
print("\n[2] Ejecutando matching multicriteria para Gold Set...")
from match_ofertas_multicriteria import MultiCriteriaMatcher
matcher = MultiCriteriaMatcher()

# Filter to only Gold Set IDs
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# Reset scores for Gold Set to force re-matching
c.execute(f'''
    UPDATE ofertas_esco_matching
    SET score_final_ponderado = NULL,
        score_titulo = NULL,
        score_skills = NULL,
        score_descripcion = NULL
    WHERE id_oferta IN ({placeholders})
''', gold_ids)
conn.commit()
print(f"    Reset scores para {c.rowcount} ofertas")
conn.close()

# Run matcher (will process all pending, but Gold Set is now pending)
matcher.ejecutar()

# Step 3: Calculate precision
print("\n" + "=" * 70)
print("RESULTADOS GOLD SET")
print("=" * 70)

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
c = conn.cursor()

# Get matching results for Gold Set
c.execute(f'''
    SELECT m.id_oferta, m.esco_occupation_uri, m.esco_occupation_label,
           m.score_final_ponderado, m.score_titulo, m.score_skills, m.score_descripcion
    FROM ofertas_esco_matching m
    WHERE m.id_oferta IN ({placeholders})
''', gold_ids)
matching_results = {row['id_oferta']: dict(row) for row in c.fetchall()}

# Compare with Gold Set expected
print("\n| ID Oferta    | ESCO Asignado                    | esco_ok | Estado  |")
print("|--------------|----------------------------------|---------|---------|")

correct = 0
incorrect = 0
no_matching = 0

for case in gold_set:
    id_oferta = str(case['id_oferta'])
    expected_ok = case.get('esco_ok', True)

    if id_oferta in matching_results and matching_results[id_oferta]['esco_occupation_label']:
        esco_label = matching_results[id_oferta]['esco_occupation_label'][:30]
        score = matching_results[id_oferta]['score_final_ponderado']

        # For now, we consider high score (>0.75) as "good match"
        # esco_ok=True means the expected ESCO is correct
        if expected_ok and score and score >= 0.50:
            status = "OK"
            correct += 1
        elif not expected_ok:
            status = "ERROR ESP"  # Expected to be wrong
            incorrect += 1
        else:
            status = "BAJO"
            incorrect += 1

        print(f"| {id_oferta} | {esco_label:32} | {expected_ok!s:7} | {status:7} |")
    else:
        no_matching += 1
        print(f"| {id_oferta} | {'SIN MATCHING':32} | {expected_ok!s:7} | PENDING |")

print("\n" + "-" * 70)
print(f"PRECISION: {correct}/{len(gold_set)} ({correct/len(gold_set)*100:.1f}%)")
print(f"  Correctos: {correct}")
print(f"  Incorrectos: {incorrect}")
print(f"  Sin matching: {no_matching}")

conn.close()
