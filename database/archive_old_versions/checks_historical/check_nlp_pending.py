#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Check pending NLP processing"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / 'bumeran_scraping.db'

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Total ofertas
cursor.execute('SELECT COUNT(*) FROM ofertas')
total = cursor.fetchone()[0]

# Ya procesadas con v8.0.0
cursor.execute("SELECT COUNT(DISTINCT id_oferta) FROM validacion_v7 WHERE nlp_version = '8.0.0'")
v8_done = cursor.fetchone()[0]

# Ofertas sin procesar
cursor.execute("""
    SELECT COUNT(*) FROM ofertas o
    WHERE NOT EXISTS (
        SELECT 1 FROM validacion_v7 v
        WHERE CAST(o.id_oferta AS TEXT) = CAST(v.id_oferta AS TEXT)
        AND v.nlp_version = '8.0.0'
    )
""")
pending = cursor.fetchone()[0]

print(f"Total ofertas: {total:,}")
print(f"Ya con NLP v8.0.0: {v8_done}")
print(f"Pendientes: {pending:,}")

conn.close()
