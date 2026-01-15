#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Add isco_label column and populate from esco_isco_hierarchy"""

import sqlite3
from pathlib import Path

conn = sqlite3.connect(Path(__file__).parent / 'bumeran_scraping.db')
c = conn.cursor()

# Check current columns
c.execute('PRAGMA table_info(ofertas_esco_matching)')
cols = [col[1] for col in c.fetchall()]
isco_cols = [col for col in cols if 'isco' in col.lower()]
print(f'Columnas ISCO actuales: {isco_cols}')

# Add column if not exists
if 'isco_label' not in cols:
    print('Agregando columna isco_label...')
    c.execute('ALTER TABLE ofertas_esco_matching ADD COLUMN isco_label TEXT')
    conn.commit()
    print('Columna isco_label agregada!')
else:
    print('Columna isco_label ya existe')

# Count records to update
c.execute('SELECT COUNT(*) FROM ofertas_esco_matching WHERE isco_code IS NOT NULL AND isco_label IS NULL')
pending = c.fetchone()[0]
print(f'Registros con ISCO code pero sin label: {pending}')

# Update isco_label from esco_isco_hierarchy
# Note: isco_code in ofertas_esco_matching is without C prefix (5223)
# but in esco_isco_hierarchy it has C prefix (C5223)
print('Actualizando isco_label desde esco_isco_hierarchy...')
c.execute('''
    UPDATE ofertas_esco_matching
    SET isco_label = (
        SELECT h.preferred_label_es
        FROM esco_isco_hierarchy h
        WHERE h.isco_code = 'C' || ofertas_esco_matching.isco_code
    )
    WHERE isco_code IS NOT NULL AND isco_label IS NULL
''')
updated = c.rowcount
conn.commit()
print(f'Registros actualizados: {updated}')

# Show examples
print()
print('=' * 70)
print('EJEMPLOS (3 registros):')
print('=' * 70)
c.execute('''
    SELECT id_oferta, isco_code, isco_label, esco_occupation_label
    FROM ofertas_esco_matching
    WHERE isco_label IS NOT NULL
    LIMIT 3
''')
for row in c.fetchall():
    print(f'  ID: {row[0]}')
    print(f'    ISCO Code:  {row[1]}')
    print(f'    ISCO Label: {row[2]}')
    print(f'    ESCO Label: {row[3][:50] if row[3] else "NULL"}...')
    print()

# Stats
c.execute('SELECT COUNT(*) FROM ofertas_esco_matching WHERE isco_label IS NOT NULL')
with_label = c.fetchone()[0]
c.execute('SELECT COUNT(*) FROM ofertas_esco_matching WHERE isco_code IS NOT NULL')
with_code = c.fetchone()[0]
print(f'Cobertura: {with_label}/{with_code} ({with_label/with_code*100:.1f}%)')

conn.close()
