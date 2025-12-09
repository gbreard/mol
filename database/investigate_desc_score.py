#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Investigar anomalia en score_descripcion"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / 'bumeran_scraping.db'
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# IDs v8.1
c.execute("SELECT CAST(id_oferta AS TEXT) FROM validacion_v7 WHERE nlp_version = '8.1.0'")
ids_v81 = [row[0] for row in c.fetchall()]
placeholders = ','.join(['?'] * len(ids_v81))

print('='*70)
print('INVESTIGACION: score_descripcion anomalo en v8.1')
print('='*70)

# 1. Ofertas con score_descripcion > 0
print('\n[1] OFERTAS v8.1 con score_descripcion > 0:')
print('-'*50)
c.execute(f'''
    SELECT m.id_oferta, m.score_descripcion, m.score_final_ponderado,
           LENGTH(COALESCE(o.descripcion_utf8, o.descripcion)) as len_desc
    FROM ofertas_esco_matching m
    JOIN ofertas o ON CAST(o.id_oferta AS TEXT) = m.id_oferta
    WHERE m.id_oferta IN ({placeholders}) AND m.score_descripcion > 0
    ORDER BY m.score_descripcion DESC
    LIMIT 10
''', ids_v81)

rows = c.fetchall()
print(f'Total con score_desc > 0: {len(rows)}')
for row in rows[:5]:
    print(f'  ID {row[0]}: score_desc={row[1]:.3f}, final={row[2]:.3f}, len_desc={row[3]}')

# 2. Ofertas con score_descripcion = 0 o muy bajo
print('\n[2] OFERTAS v8.1 con score_descripcion = 0 o NULL:')
print('-'*50)
c.execute(f'''
    SELECT m.id_oferta, m.score_descripcion, m.score_final_ponderado,
           LENGTH(COALESCE(o.descripcion_utf8, o.descripcion)) as len_desc
    FROM ofertas_esco_matching m
    JOIN ofertas o ON CAST(o.id_oferta AS TEXT) = m.id_oferta
    WHERE m.id_oferta IN ({placeholders}) AND (m.score_descripcion = 0 OR m.score_descripcion IS NULL)
    LIMIT 10
''', ids_v81)

rows = c.fetchall()
print(f'Total con score_desc = 0/NULL: {len(rows)}')
for row in rows[:5]:
    print(f'  ID {row[0]}: score_desc={row[1]}, final={row[2]:.3f}, len_desc={row[3]}')

# 3. Distribucion de scores v8.1
print('\n[3] DISTRIBUCION score_descripcion en v8.1:')
print('-'*50)
c.execute(f'''
    SELECT
        SUM(CASE WHEN score_descripcion IS NULL THEN 1 ELSE 0 END) as nulos,
        SUM(CASE WHEN score_descripcion = 0 THEN 1 ELSE 0 END) as ceros,
        SUM(CASE WHEN score_descripcion > 0 AND score_descripcion < 0.1 THEN 1 ELSE 0 END) as bajo,
        SUM(CASE WHEN score_descripcion >= 0.1 AND score_descripcion < 0.3 THEN 1 ELSE 0 END) as medio,
        SUM(CASE WHEN score_descripcion >= 0.3 THEN 1 ELSE 0 END) as alto,
        COUNT(*) as total
    FROM ofertas_esco_matching
    WHERE id_oferta IN ({placeholders})
''', ids_v81)

row = c.fetchone()
print(f'  NULL:    {row[0]} ofertas')
print(f'  = 0:     {row[1]} ofertas')
print(f'  0-0.1:   {row[2]} ofertas')
print(f'  0.1-0.3: {row[3]} ofertas')
print(f'  >= 0.3:  {row[4]} ofertas')
print(f'  Total:   {row[5]} ofertas')

# 4. Comparar con distribucion general
print('\n[4] DISTRIBUCION score_descripcion GENERAL:')
print('-'*50)
c.execute('''
    SELECT
        AVG(score_descripcion) as avg_desc,
        SUM(CASE WHEN score_descripcion IS NULL THEN 1 ELSE 0 END) as nulos,
        SUM(CASE WHEN score_descripcion = 0 THEN 1 ELSE 0 END) as ceros,
        SUM(CASE WHEN score_descripcion > 0 THEN 1 ELSE 0 END) as con_score,
        COUNT(*) as total
    FROM ofertas_esco_matching
''')
row = c.fetchone()
if row[0]:
    print(f'  Promedio general: {row[0]:.3f}')
print(f'  NULL:      {row[1]} ({row[1]/row[4]*100:.1f}%)')
print(f'  = 0:       {row[2]} ({row[2]/row[4]*100:.1f}%)')
print(f'  Con score: {row[3]} ({row[3]/row[4]*100:.1f}%)')
print(f'  Total:     {row[4]}')

# 5. Ver una oferta especifica con y sin score
print('\n[5] DETALLE: Oferta con score_desc > 0:')
print('-'*50)
c.execute(f'''
    SELECT m.id_oferta, o.titulo, m.score_descripcion, m.esco_occupation_label,
           SUBSTR(COALESCE(o.descripcion_utf8, o.descripcion), 1, 200) as desc
    FROM ofertas_esco_matching m
    JOIN ofertas o ON CAST(o.id_oferta AS TEXT) = m.id_oferta
    WHERE m.id_oferta IN ({placeholders}) AND m.score_descripcion > 0.1
    LIMIT 1
''', ids_v81)
row = c.fetchone()
if row:
    print(f'  ID: {row[0]}')
    print(f'  Titulo: {row[1][:60]}...' if row[1] else '  Titulo: N/A')
    print(f'  Score desc: {row[2]:.3f}')
    print(f'  ESCO: {row[3][:60]}...' if row[3] else '  ESCO: N/A')

print('\n[6] DETALLE: Oferta con score_desc = 0:')
print('-'*50)
c.execute(f'''
    SELECT m.id_oferta, o.titulo, m.score_descripcion, m.esco_occupation_label,
           LENGTH(COALESCE(o.descripcion_utf8, o.descripcion)) as len_desc
    FROM ofertas_esco_matching m
    JOIN ofertas o ON CAST(o.id_oferta AS TEXT) = m.id_oferta
    WHERE m.id_oferta IN ({placeholders}) AND m.score_descripcion = 0
    LIMIT 1
''', ids_v81)
row = c.fetchone()
if row:
    print(f'  ID: {row[0]}')
    print(f'  Titulo: {row[1][:60]}...' if row[1] else '  Titulo: N/A')
    print(f'  Score desc: {row[2]}')
    print(f'  ESCO: {row[3][:60]}...' if row[3] else '  ESCO: N/A')
    print(f'  Len descripcion: {row[4]} chars')

conn.close()
