#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Verificar estado del pipeline NLP - Quick check"""

import sqlite3
import json
from pathlib import Path

DB_PATH = Path(__file__).parent / 'bumeran_scraping.db'
GOLD_SET_PATH = Path(__file__).parent / 'gold_set_manual_v1.json'

def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("=" * 60)
    print("ESTADO DEL PIPELINE NLP")
    print("=" * 60)

    # 1. Total ofertas
    cursor.execute("SELECT COUNT(*) FROM ofertas")
    total = cursor.fetchone()[0]
    print(f"\n1. Total ofertas en BD: {total:,}")

    # 2. Con nlp_version = '8.0.0' (tabla ofertas_nlp)
    cursor.execute("SELECT COUNT(*) FROM ofertas_nlp WHERE nlp_version = '8.0.0'")
    v8 = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM ofertas_nlp")
    total_nlp = cursor.fetchone()[0]

    print(f"2. Con nlp_version='8.0.0': {v8:,} de {total_nlp:,} procesadas ({v8/total_nlp*100:.1f}% de procesadas)")

    # 3. Pendientes de parsing
    cursor.execute("""
        SELECT COUNT(*) FROM ofertas o
        LEFT JOIN ofertas_nlp n ON CAST(o.id_oferta AS TEXT) = n.id_oferta
        WHERE n.id_oferta IS NULL
    """)
    never_parsed = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*) FROM ofertas_nlp WHERE nlp_version != '8.0.0' OR nlp_version IS NULL
    """)
    old_version = cursor.fetchone()[0]

    print(f"3. Pendientes de parsing:")
    print(f"   - Sin procesar nunca: {never_parsed:,}")
    print(f"   - Con version anterior a 8.0.0: {old_version:,}")
    print(f"   - Total pendientes: {never_parsed + old_version:,}")

    # 4. Ultima ejecucion NLP
    cursor.execute("""
        SELECT nlp_version, MAX(nlp_extraction_timestamp) as ultima, COUNT(*) as cnt
        FROM ofertas_nlp
        WHERE nlp_extraction_timestamp IS NOT NULL
        GROUP BY nlp_version
        ORDER BY ultima DESC
        LIMIT 5
    """)
    print("\n4. Ultimas ejecuciones NLP por version:")
    for row in cursor.fetchall():
        print(f"   - Version {row[0]}: {row[1]} ({row[2]:,} ofertas)")

    # 5. Gold set cases
    with open(GOLD_SET_PATH, 'r', encoding='utf-8') as f:
        gold_set = json.load(f)

    gold_ids = [str(g['id_oferta']) for g in gold_set]
    placeholders = ','.join(['?'] * len(gold_ids))

    cursor.execute(f"""
        SELECT id_oferta, nlp_version, nlp_extraction_timestamp
        FROM ofertas_nlp
        WHERE id_oferta IN ({placeholders})
    """, gold_ids)

    results = {row[0]: (row[1], row[2]) for row in cursor.fetchall()}

    print(f"\n5. Estado de los {len(gold_set)} casos del Gold Set:")
    v8_count = sum(1 for v, _ in results.values() if v == '8.0.0')
    print(f"   - Con nlp_version='8.0.0': {v8_count}/{len(gold_set)}")

    missing = [gid for gid in gold_ids if gid not in results]
    if missing:
        print(f"   - Sin procesar NLP: {len(missing)}")
        for gid in missing[:3]:
            print(f"     * {gid}")

    outdated = [gid for gid in gold_ids if gid in results and results[gid][0] != '8.0.0']
    if outdated:
        print(f"   - Con version anterior: {len(outdated)}")
        for gid in outdated[:3]:
            print(f"     * {gid}: version={results[gid][0]}")

    if v8_count == len(gold_set):
        print("   [OK] Todos los casos del Gold Set tienen parsing actualizado")

    conn.close()
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()
