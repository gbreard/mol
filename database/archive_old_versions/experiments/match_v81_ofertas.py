#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Execute matching for v8.1 offers specifically"""

import sqlite3
import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from match_ofertas_multicriteria import ESCOMultiCriteriaMatcher

DB_PATH = Path(__file__).parent / 'bumeran_scraping.db'

print("="*70)
print("MATCHING PARA OFERTAS v8.1")
print("="*70)

# Get v8.1 IDs
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()
c.execute("SELECT id_oferta FROM validacion_v7 WHERE nlp_version = '8.1.0'")
ids_v81 = [r[0] for r in c.fetchall()]
conn.close()

print(f"Ofertas v8.1 a procesar: {len(ids_v81)}")

# Initialize matcher
matcher = ESCOMultiCriteriaMatcher()

# Process each offer
processed = 0
for id_oferta in ids_v81:
    try:
        matcher.process_single_offer(id_oferta)
        processed += 1
        if processed % 10 == 0:
            print(f"  Procesadas: {processed}/{len(ids_v81)}")
    except Exception as e:
        print(f"  Error en {id_oferta}: {e}")

print(f"\nTotal procesadas: {processed}")
print("="*70)
