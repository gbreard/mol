#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Revision manual de tareas_explicitas del Gold Set 100 - v2"""

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
    SELECT n.id_oferta, o.titulo, n.tareas_explicitas,
           substr(o.descripcion, 1, 500) as desc_preview
    FROM ofertas_nlp n
    JOIN ofertas o ON n.id_oferta = o.id_oferta
    WHERE n.id_oferta IN ({placeholders})
    ORDER BY CASE WHEN n.tareas_explicitas IS NULL OR n.tareas_explicitas = '' THEN 0 ELSE 1 END,
             n.id_oferta
''', ids)

print('OFERTAS SIN TAREAS EXPLICITAS')
print('=' * 80)

sin_tareas = []
con_tareas_json = 0
con_tareas_texto = 0

for row in c.fetchall():
    tareas = row['tareas_explicitas'] or ''
    titulo = (row['titulo'] or '')[:60]
    id_oferta = row['id_oferta']

    if not tareas:
        sin_tareas.append(row)
    elif tareas.startswith('[{'):
        con_tareas_json += 1
    else:
        con_tareas_texto += 1

# Mostrar sin tareas
for row in sin_tareas:
    id_oferta = row['id_oferta']
    titulo = (row['titulo'] or '')[:60]
    desc = (row['desc_preview'] or '').replace('\n', ' ')[:200]

    print(f"\n[{id_oferta}] {titulo}")
    print(f"  DESC: {desc}...")

print('\n' + '=' * 80)
print(f'RESUMEN:')
print(f'  SIN TAREAS: {len(sin_tareas)}/100')
print(f'  CON TAREAS (JSON): {con_tareas_json}')
print(f'  CON TAREAS (texto): {con_tareas_texto}')

conn.close()
