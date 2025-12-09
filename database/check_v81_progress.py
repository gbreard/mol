#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Check progress of v8.1 matching"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / 'bumeran_scraping.db'
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# Get v8.1 IDs
c.execute("SELECT id_oferta FROM validacion_v7 WHERE nlp_version = '8.1.0'")
ids_v81 = [str(r[0]) for r in c.fetchall()]
placeholders = ','.join(['?'] * len(ids_v81))

# Check how many have score_final_ponderado set
c.execute(f"""
    SELECT COUNT(*) FROM ofertas_esco_matching
    WHERE id_oferta IN ({placeholders}) AND score_final_ponderado IS NOT NULL
""", ids_v81)
with_score = c.fetchone()[0]

c.execute(f"""
    SELECT COUNT(*) FROM ofertas_esco_matching
    WHERE id_oferta IN ({placeholders})
""", ids_v81)
total = c.fetchone()[0]

print(f"Ofertas v8.1: {len(ids_v81)}")
print(f"En matching table: {total}")
print(f"Con score calculado: {with_score}")

if with_score > 0:
    c.execute(f"""
        SELECT AVG(score_final_ponderado), AVG(score_descripcion)
        FROM ofertas_esco_matching
        WHERE id_oferta IN ({placeholders}) AND score_final_ponderado IS NOT NULL
    """, ids_v81)
    row = c.fetchone()
    if row[0]:
        print(f"Score promedio: {row[0]:.3f}")
        print(f"Score descripcion: {row[1]:.3f}")

conn.close()
