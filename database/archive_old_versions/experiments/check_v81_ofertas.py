#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Check if v8.1 offers exist in ofertas table"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / 'bumeran_scraping.db'
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# Get v8.1 IDs
c.execute("SELECT id_oferta FROM validacion_v7 WHERE nlp_version = '8.1.0'")
ids_v81 = [r[0] for r in c.fetchall()]
print(f"Total IDs v8.1: {len(ids_v81)}")

# Check how many exist in ofertas
placeholders = ','.join(['?'] * len(ids_v81))
c.execute(f"SELECT COUNT(*) FROM ofertas WHERE id_oferta IN ({placeholders})", ids_v81)
in_ofertas = c.fetchone()[0]
print(f"En tabla ofertas: {in_ofertas}")

# Check in ofertas_esco_matching
c.execute(f"SELECT COUNT(*) FROM ofertas_esco_matching WHERE id_oferta IN ({placeholders})", ids_v81)
in_matching = c.fetchone()[0]
print(f"En ofertas_esco_matching: {in_matching}")

# Sample one that exists
c.execute(f"SELECT id_oferta, titulo FROM ofertas WHERE id_oferta IN ({placeholders}) LIMIT 3", ids_v81)
print("\nEjemplos que SI existen en ofertas:")
for r in c.fetchall():
    print(f"  {r[0]}: {str(r[1])[:50]}...")

# Check if matching was deleted
c.execute("SELECT COUNT(*) FROM ofertas_esco_matching")
total_matching = c.fetchone()[0]
print(f"\nTotal registros en ofertas_esco_matching: {total_matching}")

conn.close()
