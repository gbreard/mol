#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Revision manual de tareas_explicitas del Gold Set 100 - v3"""

import sqlite3
import json
import sys
from pathlib import Path

# Fix encoding
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

base = Path(__file__).parent.parent

with open(base / 'database/gold_set_nlp_100_ids.json', 'r', encoding='utf-8') as f:
    ids = json.load(f)

conn = sqlite3.connect(base / 'database/bumeran_scraping.db')
conn.row_factory = sqlite3.Row
c = conn.cursor()
placeholders = ','.join(['?' for _ in ids])

c.execute(f'''
    SELECT n.id_oferta, o.titulo, n.tareas_explicitas,
           substr(o.descripcion, 1, 600) as desc_preview
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
for i, row in enumerate(sin_tareas, 1):
    id_oferta = row['id_oferta']
    titulo = (row['titulo'] or '')[:60]
    desc = (row['desc_preview'] or '').replace('\n', ' ').replace('\r', '')
    # Limpiar emojis y caracteres especiales
    desc = ''.join(c if ord(c) < 128 else ' ' for c in desc)[:250]

    print(f"\n{i}. [{id_oferta}] {titulo}")
    print(f"   {desc}...")

print('\n' + '=' * 80)
print(f'RESUMEN:')
print(f'  SIN TAREAS: {len(sin_tareas)}/100')
print(f'  CON TAREAS (JSON LLM): {con_tareas_json}')
print(f'  CON TAREAS (texto regex): {con_tareas_texto}')

# Verificar si hay tareas en JSON que necesitan limpiarse
print('\n' + '=' * 80)
print('EJEMPLO DE TAREAS EN FORMATO JSON (necesitan limpieza):')

c.execute(f'''
    SELECT id_oferta, titulo, tareas_explicitas
    FROM ofertas_nlp
    WHERE id_oferta IN ({placeholders})
      AND tareas_explicitas LIKE '[{{%'
    LIMIT 3
''', ids)

for row in c.fetchall():
    print(f"\n[{row['id_oferta']}] {row['titulo'][:50]}")
    try:
        tareas_json = json.loads(row['tareas_explicitas'])
        for t in tareas_json[:3]:
            if isinstance(t, dict):
                print(f"  - {t.get('valor', t.get('texto_original', str(t)))[:60]}")
            else:
                print(f"  - {str(t)[:60]}")
    except:
        print(f"  RAW: {row['tareas_explicitas'][:100]}")

conn.close()
