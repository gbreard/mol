#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Check and fix ISCO codes - remove C prefix"""

import sqlite3
from pathlib import Path
import sys

conn = sqlite3.connect(Path(__file__).parent / 'bumeran_scraping.db')
c = conn.cursor()

# If --fix argument, update the database
if '--fix' in sys.argv:
    print('='*70)
    print('ACTUALIZANDO ISCO CODES (quitando prefijo C)')
    print('='*70)

    # Mostrar antes
    print('\nANTES:')
    c.execute("SELECT id_oferta, isco_code, isco_nivel1, isco_nivel2 FROM ofertas_esco_matching WHERE isco_code LIKE 'C%' LIMIT 3")
    for row in c.fetchall():
        print(f'  {row[0]}: code={row[1]}, n1={row[2]}, n2={row[3]}')

    # Actualizar
    c.execute("UPDATE ofertas_esco_matching SET isco_code = SUBSTR(isco_code, 2) WHERE isco_code LIKE 'C%'")
    updated_code = c.rowcount

    c.execute("UPDATE ofertas_esco_matching SET isco_nivel1 = SUBSTR(isco_code, 1, 1) WHERE isco_code IS NOT NULL")
    c.execute("UPDATE ofertas_esco_matching SET isco_nivel2 = SUBSTR(isco_code, 1, 2) WHERE isco_code IS NOT NULL")

    conn.commit()
    print(f'\nActualizados: {updated_code} registros')

    # Mostrar despues
    print('\nDESPUES:')
    c.execute("SELECT id_oferta, isco_code, isco_nivel1, isco_nivel2 FROM ofertas_esco_matching WHERE isco_code IS NOT NULL LIMIT 3")
    for row in c.fetchall():
        print(f'  {row[0]}: code={row[1]}, n1={row[2]}, n2={row[3]}')

    conn.close()
    print('\nListo!')
    sys.exit(0)

print('=' * 70)
print('1. SCHEMA DE ofertas_esco_matching')
print('=' * 70)
c.execute('PRAGMA table_info(ofertas_esco_matching)')
cols = c.fetchall()
for col in cols:
    null_str = 'NOT NULL' if col[3] else ''
    print(f'  {col[1]:30} {col[2]:15} {null_str}')

# Check for isco columns
isco_cols = [col[1] for col in cols if 'isco' in col[1].lower()]
print(f'\nColumnas ISCO encontradas: {isco_cols}')

print()
print('=' * 70)
print('2. EJEMPLO DE 3 OFERTAS DEL GOLD SET CON ESCO E ISCO')
print('=' * 70)
c.execute('''
    SELECT id_oferta, esco_occupation_uri, esco_occupation_label,
           isco_code, isco_nivel1, isco_nivel2, score_final_ponderado
    FROM ofertas_esco_matching
    WHERE id_oferta IN ('1118026700', '1118027261', '1118028891')
''')
for row in c.fetchall():
    print(f'\nID: {row[0]}')
    esco_uri = row[1][:60] + '...' if row[1] and len(row[1]) > 60 else row[1]
    print(f'  ESCO URI:   {esco_uri}')
    print(f'  ESCO Label: {row[2]}')
    print(f'  ISCO Code:  {row[3]}')
    print(f'  ISCO Niv1:  {row[4]}')
    print(f'  ISCO Niv2:  {row[5]}')
    print(f'  Score:      {row[6]}')

print()
print('=' * 70)
print('3. TABLAS RELACIONADAS CON ESCO/ISCO')
print('=' * 70)
c.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = c.fetchall()
esco_isco_tables = [t[0] for t in tables if 'esco' in t[0].lower() or 'isco' in t[0].lower()]
for t in esco_isco_tables:
    print(f'  - {t}')

# Check esco_occupations table
c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='esco_occupations'")
if c.fetchone():
    print('\n' + '=' * 70)
    print('4. TABLA esco_occupations (mapeo ESCO -> ISCO)')
    print('=' * 70)

    c.execute('PRAGMA table_info(esco_occupations)')
    print('Schema:')
    for col in c.fetchall():
        print(f'    {col[1]:25} {col[2]}')

    print('\nEjemplo de mapeo ESCO->ISCO (3 registros):')
    c.execute('SELECT uri, label, isco_code FROM esco_occupations WHERE isco_code IS NOT NULL LIMIT 3')
    for row in c.fetchall():
        label = row[1][:35] if row[1] else 'N/A'
        print(f'    {label:35} -> ISCO: {row[2]}')

    c.execute('SELECT COUNT(*) FROM esco_occupations')
    total = c.fetchone()[0]
    c.execute('SELECT COUNT(*) FROM esco_occupations WHERE isco_code IS NOT NULL')
    with_isco = c.fetchone()[0]
    print(f'\nCobertura: {with_isco}/{total} ocupaciones ESCO tienen ISCO code')

print()
print('=' * 70)
print('5. VERIFICACION: ¿Se está poblando ISCO en matching?')
print('=' * 70)
c.execute('SELECT COUNT(*) FROM ofertas_esco_matching WHERE isco_code IS NOT NULL')
with_isco = c.fetchone()[0]
c.execute('SELECT COUNT(*) FROM ofertas_esco_matching WHERE esco_occupation_label IS NOT NULL')
with_esco = c.fetchone()[0]
print(f'  Ofertas con ESCO label: {with_esco}')
print(f'  Ofertas con ISCO code:  {with_isco}')

if with_esco > 0:
    pct = with_isco / with_esco * 100
    print(f'  Cobertura ISCO: {pct:.1f}%')

conn.close()
