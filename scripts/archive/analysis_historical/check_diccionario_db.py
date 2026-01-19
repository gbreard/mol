#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Check diccionario_arg_esco table in database"""

import sqlite3
from pathlib import Path

base = Path(__file__).parent
conn = sqlite3.connect(base / 'bumeran_scraping.db')
c = conn.cursor()

# Check if table exists
c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='diccionario_arg_esco'")
if not c.fetchone():
    print("TABLA diccionario_arg_esco NO EXISTE")
    conn.close()
    exit()

# Get table structure
print("=" * 60)
print("ESTRUCTURA DE TABLA diccionario_arg_esco")
print("=" * 60)
c.execute("PRAGMA table_info(diccionario_arg_esco)")
for col in c.fetchall():
    print(f"  {col[1]} ({col[2]})")

# Count records
c.execute("SELECT COUNT(*) FROM diccionario_arg_esco")
total = c.fetchone()[0]
print(f"\nTotal registros: {total}")

# Search for Mozo
print("\n" + "=" * 60)
print("BUSQUEDA: Mozo, repositor, camarero")
print("=" * 60)

for termino in ['mozo', 'repositor', 'camarero', 'vendedor']:
    c.execute("""
        SELECT termino_argentino, isco_target, esco_preferred_label, notes
        FROM diccionario_arg_esco
        WHERE termino_argentino LIKE ?
        LIMIT 5
    """, (f'%{termino}%',))
    rows = c.fetchall()
    if rows:
        print(f"\n'{termino}':")
        for r in rows:
            print(f"  {r[0]} -> ISCO {r[1]} | ESCO: {r[2]} | Notas: {r[3]}")

# Show sample records
print("\n" + "=" * 60)
print("MUESTRA DE 10 REGISTROS")
print("=" * 60)
c.execute("SELECT termino_argentino, isco_target, esco_preferred_label FROM diccionario_arg_esco LIMIT 10")
for r in c.fetchall():
    print(f"  {r[0]} -> ISCO {r[1]} -> {r[2]}")

conn.close()
