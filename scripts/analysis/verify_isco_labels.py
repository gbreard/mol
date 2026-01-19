# -*- coding: utf-8 -*-
"""Verifica ISCO labels en la DB."""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "database" / "bumeran_scraping.db"

conn = sqlite3.connect(str(DB_PATH))
cursor = conn.cursor()
cursor.execute("""
    SELECT id_oferta, isco_code, isco_label
    FROM ofertas_esco_matching
    WHERE isco_label IS NOT NULL AND isco_label != ''
    LIMIT 8
""")
print("ISCO Labels en DB:")
print("-" * 80)
for row in cursor.fetchall():
    print(f"ID: {row[0]}, ISCO: {row[1]}, Label: {row[2][:50] if row[2] else 'N/A'}")
conn.close()
