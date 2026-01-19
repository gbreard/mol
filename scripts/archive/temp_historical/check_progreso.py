#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sqlite3
import json
from pathlib import Path
from datetime import datetime, timedelta

base = Path(__file__).parent.parent

with open(base / 'database/gold_set_manual_v2.json', 'r', encoding='utf-8') as f:
    gs = json.load(f)
ids_49 = [str(o['id_oferta']) for o in gs]

with open(base / 'database/gold_set_nlp_100_ids.json', 'r') as f:
    ids_100 = json.load(f)

ids_51 = [id for id in ids_100 if id not in ids_49]

conn = sqlite3.connect(base / 'database/bumeran_scraping.db')
c = conn.cursor()

placeholders = ','.join(['?' for _ in ids_51])

# Verificar cobertura actual de las 51
c.execute(f'''
    SELECT
        SUM(CASE WHEN provincia IS NOT NULL AND provincia != '' THEN 1 ELSE 0 END) as prov,
        SUM(CASE WHEN skills_tecnicas_list IS NOT NULL AND skills_tecnicas_list != '' THEN 1 ELSE 0 END) as skills,
        SUM(CASE WHEN tareas_explicitas IS NOT NULL AND tareas_explicitas != '' THEN 1 ELSE 0 END) as tareas
    FROM ofertas_nlp
    WHERE id_oferta IN ({placeholders})
''', ids_51)
row = c.fetchone()

print(f'Cobertura 51 ofertas:')
print(f'  provincia: {row[0]}/51')
print(f'  skills:    {row[1]}/51')
print(f'  tareas:    {row[2]}/51')
conn.close()
