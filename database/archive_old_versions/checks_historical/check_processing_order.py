#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Check which IDs have been processed"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / 'bumeran_scraping.db'
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# Get total offers
c.execute("SELECT COUNT(*) FROM ofertas")
total_ofertas = c.fetchone()[0]

# Get ofertas with matching score
c.execute("SELECT COUNT(*) FROM ofertas_esco_matching WHERE score_final_ponderado IS NOT NULL")
with_score = c.fetchone()[0]

print(f"Total ofertas: {total_ofertas}")
print(f"Con score: {with_score}")

# Check range of IDs processed
c.execute("SELECT MIN(CAST(id_oferta AS INTEGER)), MAX(CAST(id_oferta AS INTEGER)) FROM ofertas_esco_matching WHERE score_final_ponderado IS NOT NULL")
row = c.fetchone()
if row[0]:
    print(f"Rango IDs procesados: {row[0]} - {row[1]}")

# Check v8.1 IDs range
c.execute("SELECT id_oferta FROM validacion_v7 WHERE nlp_version = '8.1.0' ORDER BY CAST(id_oferta AS INTEGER)")
v81_ids = [r[0] for r in c.fetchall()]
print(f"\nIDs v8.1 (ordenados): primeros 5 = {v81_ids[:5]}")
print(f"                      últimos 5 = {v81_ids[-5:]}")

# Check ofertas table range
c.execute("SELECT MIN(id_oferta), MAX(id_oferta) FROM ofertas")
row = c.fetchone()
print(f"\nRango ofertas table: {row[0]} - {row[1]}")

conn.close()
