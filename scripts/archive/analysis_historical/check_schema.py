#!/usr/bin/env python3
import sqlite3

conn = sqlite3.connect('bumeran_scraping.db')
cursor = conn.cursor()

print("=" * 70)
print("ESTRUCTURA TABLA: ofertas_nlp")
print("=" * 70)

cursor.execute('PRAGMA table_info(ofertas_nlp)')
cols = cursor.fetchall()
for col in cols[:50]:
    pk_marker = " [PK]" if col[5] else ""
    print(f"  {col[1]}: {col[2]}{pk_marker}")

print(f"\nTotal columnas: {len(cols)}")
