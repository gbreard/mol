#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Check ESCO and ISCO table schemas"""

import sqlite3
from pathlib import Path

conn = sqlite3.connect(Path(__file__).parent / 'bumeran_scraping.db')
c = conn.cursor()

print('=' * 70)
print('1. ESCO_CODE STATS')
print('=' * 70)
c.execute('SELECT COUNT(*) FROM esco_occupations WHERE esco_code IS NOT NULL')
print(f'  Con esco_code: {c.fetchone()[0]}')
c.execute('SELECT COUNT(*) FROM esco_occupations WHERE esco_code IS NULL')
print(f'  Sin esco_code: {c.fetchone()[0]}')

print()
print('=' * 70)
print('2. ISCO HIERARCHY - EJEMPLO CODIGO 5223')
print('=' * 70)
c.execute("SELECT * FROM esco_isco_hierarchy WHERE isco_code LIKE '%5223%' OR isco_code LIKE '%522%'")
for row in c.fetchall():
    print(f'  Code: {row[0]:8} | Label: {row[1][:50] if row[1] else "NULL"}')

print()
print('=' * 70)
print('3. ISCO HIERARCHY - NIVELES')
print('=' * 70)
c.execute("SELECT isco_code, hierarchy_level, preferred_label_es FROM esco_isco_hierarchy WHERE isco_code LIKE '5%' ORDER BY isco_code LIMIT 10")
for row in c.fetchall():
    code = row[0].lstrip('C') if row[0] else ''
    label = row[2][:40] if row[2] else 'NULL'
    print(f'  {code:6} (nivel {row[1]}): {label}')

print()
print('=' * 70)
print('4. BUSCAR OCUPACION VENDEDOR EN ESCO_OCCUPATIONS')
print('=' * 70)
c.execute("SELECT occupation_uri, isco_code, preferred_label_es FROM esco_occupations WHERE preferred_label_es LIKE '%vendedor%piezas%' LIMIT 3")
for row in c.fetchall():
    print(f'  URI:   {row[0]}')
    print(f'  ISCO:  {row[1]}')
    print(f'  Label: {row[2]}')
    print()

conn.close()
