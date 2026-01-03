#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Verificar source_classification"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / 'bumeran_scraping.db'
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

print('=== DISTRIBUCION POR SOURCE_CLASSIFICATION ===')
cursor.execute('''
    SELECT source_classification, COUNT(*) as cnt
    FROM ofertas_esco_skills_detalle
    GROUP BY source_classification
''')
for row in cursor.fetchall():
    src = row[0] or 'NULL'
    print(f'  {src:15s}: {row[1]:5d}')

print()
print('=== COMPARACION: Lo que dice la OFERTA vs lo que dice ESCO ===')
cursor.execute('''
    SELECT
        source_classification AS oferta_dice,
        CASE
            WHEN is_essential_for_occupation = 1 THEN 'essential'
            WHEN is_optional_for_occupation = 1 THEN 'optional'
            ELSE 'sin_relacion'
        END AS esco_dice,
        COUNT(*) as cnt
    FROM ofertas_esco_skills_detalle
    WHERE esco_skill_uri IS NOT NULL
    GROUP BY source_classification, esco_dice
    ORDER BY source_classification, esco_dice
''')
print(f"{'OFERTA DICE':15s} | {'ESCO DICE':15s} | COUNT")
print('-' * 50)
for row in cursor.fetchall():
    print(f'{row[0]:15s} | {row[1]:15s} | {row[2]:5d}')

print()
print('=== EJEMPLOS DE DISCREPANCIA ===')
cursor.execute('''
    SELECT
        skill_mencionado,
        esco_skill_label,
        source_classification AS oferta_dice,
        CASE
            WHEN is_essential_for_occupation = 1 THEN 'essential'
            WHEN is_optional_for_occupation = 1 THEN 'optional'
            ELSE 'sin_relacion'
        END AS esco_dice
    FROM ofertas_esco_skills_detalle
    WHERE esco_skill_uri IS NOT NULL
      AND source_classification != (
          CASE
              WHEN is_essential_for_occupation = 1 THEN 'essential'
              WHEN is_optional_for_occupation = 1 THEN 'optional'
              ELSE source_classification
          END
      )
    LIMIT 10
''')
print(f"{'SKILL':25s} | {'OFERTA':10s} | {'ESCO':12s}")
print('-' * 60)
for row in cursor.fetchall():
    print(f"{row[0][:25]:25s} | {row[2]:10s} | {row[3]:12s}")

conn.close()
