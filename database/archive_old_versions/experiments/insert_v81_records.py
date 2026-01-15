#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Insert v8.1 offers into ofertas_esco_matching with correct schema"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / 'bumeran_scraping.db'

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# Get table schema
print("Schema ofertas_esco_matching:")
c.execute("PRAGMA table_info(ofertas_esco_matching)")
cols = [r[1] for r in c.fetchall()]
print(f"  Columnas: {cols[:10]}...")

# Get v8.1 IDs
c.execute("SELECT id_oferta FROM validacion_v7 WHERE nlp_version = '8.1.0'")
ids_v81 = [str(r[0]) for r in c.fetchall()]
print(f"\nIDs v8.1: {len(ids_v81)}")

# Insert with minimal columns
print("\nInsertando registros...")
inserted = 0
for id_oferta in ids_v81:
    try:
        c.execute("""
            INSERT OR IGNORE INTO ofertas_esco_matching (id_oferta)
            VALUES (?)
        """, (id_oferta,))
        if c.rowcount > 0:
            inserted += 1
    except Exception as e:
        print(f"  Error {id_oferta}: {e}")

conn.commit()
print(f"Registros insertados: {inserted}")

# Verify
placeholders = ','.join(['?'] * len(ids_v81))
c.execute(f"SELECT COUNT(*) FROM ofertas_esco_matching WHERE id_oferta IN ({placeholders})", ids_v81)
total = c.fetchone()[0]
print(f"Total v8.1 en matching: {total}")

conn.close()
