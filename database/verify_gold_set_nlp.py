#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Verificar NLP v8.0 en Gold Set - validacion_v7"""

import sqlite3
import json
from pathlib import Path

DB_PATH = Path(__file__).parent / 'bumeran_scraping.db'
GOLD_SET_PATH = Path(__file__).parent / 'gold_set_manual_v1.json'

def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Cargar IDs del gold set
    with open(GOLD_SET_PATH, 'r', encoding='utf-8') as f:
        gold_set = json.load(f)

    gold_ids = [str(g['id_oferta']) for g in gold_set]

    print("=" * 60)
    print("VERIFICACION NLP EN VALIDACION_V7")
    print("=" * 60)

    # Buscar los 19 casos
    placeholders = ','.join(['?'] * len(gold_ids))
    cursor.execute(f'''
        SELECT id_oferta, nlp_version, timestamp
        FROM validacion_v7
        WHERE id_oferta IN ({placeholders})
    ''', gold_ids)

    results = cursor.fetchall()
    print(f"\nGold Set en validacion_v7: {len(results)}/19")

    v8_count = sum(1 for r in results if r[1] == '8.0.0')
    print(f"Con nlp_version='8.0.0': {v8_count}")

    if results:
        print("\nDetalle:")
        for r in results:
            ts = r[2][:19] if r[2] else "N/A"
            print(f"  {r[0]}: v{r[1]} @ {ts}")

    # Verificar si falta alguno
    found_ids = set(str(r[0]) for r in results)
    missing = [gid for gid in gold_ids if gid not in found_ids]

    if missing:
        print(f"\n[!] Faltantes ({len(missing)}):")
        for m in missing:
            print(f"  - {m}")

    if v8_count == 19:
        print("\n[OK] Todos los 19 casos tienen NLP v8.0.0")

    conn.close()

if __name__ == "__main__":
    main()
