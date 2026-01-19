#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Revision manual de tareas_explicitas del Gold Set 100"""

import sqlite3
import json
from pathlib import Path

base = Path(__file__).parent.parent

with open(base / 'database/gold_set_nlp_100_ids.json', 'r', encoding='utf-8') as f:
    ids = json.load(f)

conn = sqlite3.connect(base / 'database/bumeran_scraping.db')
conn.row_factory = sqlite3.Row
c = conn.cursor()
placeholders = ','.join(['?' for _ in ids])

c.execute(f'''
    SELECT n.id_oferta, o.titulo, n.tareas_explicitas
    FROM ofertas_nlp n
    JOIN ofertas o ON n.id_oferta = o.id_oferta
    WHERE n.id_oferta IN ({placeholders})
    ORDER BY CASE WHEN n.tareas_explicitas IS NULL OR n.tareas_explicitas = '' THEN 1 ELSE 0 END,
             n.id_oferta
''', ids)

print('REVISION MANUAL - TAREAS EXPLICITAS')
print('=' * 80)

con_tareas = 0
sin_tareas = 0
ofertas_sin = []

for row in c.fetchall():
    tareas = row['tareas_explicitas'] or ''
    titulo = (row['titulo'] or '')[:55]
    id_oferta = row['id_oferta']

    if tareas:
        con_tareas += 1
        # Truncar tareas para display
        tareas_display = tareas[:150] + '...' if len(tareas) > 150 else tareas
        print(f"[{id_oferta}] {titulo}")
        print(f"  >> {tareas_display}")
        print()
    else:
        sin_tareas += 1
        ofertas_sin.append((id_oferta, titulo))

print('=' * 80)
print(f'CON TAREAS: {con_tareas}/100 ({100*con_tareas/100:.0f}%)')
print(f'SIN TAREAS: {sin_tareas}/100')

if ofertas_sin:
    print('\nOFERTAS SIN TAREAS:')
    for id_of, titulo in ofertas_sin:
        print(f"  - [{id_of}] {titulo}")

conn.close()
