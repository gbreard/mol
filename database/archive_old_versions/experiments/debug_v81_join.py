#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Debug JOIN issue for v8.1 matching"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / 'bumeran_scraping.db'
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

print("="*70)
print("DEBUG: JOIN v8.1 ofertas")
print("="*70)

# 1. Ver IDs v8.1 en validacion_v7
c.execute("SELECT id_oferta, typeof(id_oferta) FROM validacion_v7 WHERE nlp_version = '8.1.0' LIMIT 5")
print('\n[1] IDs v8.1 en validacion_v7:')
for r in c.fetchall():
    print(f'  {r[0]} (type: {r[1]})')

# 2. Ver IDs en ofertas_esco_matching
c.execute('SELECT id_oferta, typeof(id_oferta) FROM ofertas_esco_matching LIMIT 5')
print('\n[2] IDs en ofertas_esco_matching:')
for r in c.fetchall():
    print(f'  {r[0]} (type: {r[1]})')

# 3. Contar v8.1 y sus matches
c.execute("SELECT COUNT(*) FROM validacion_v7 WHERE nlp_version = '8.1.0'")
total_v81 = c.fetchone()[0]
print(f'\n[3] Total ofertas v8.1: {total_v81}')

# 4. Verificar un ID específico
c.execute("SELECT id_oferta FROM validacion_v7 WHERE nlp_version = '8.1.0' LIMIT 1")
sample_id = c.fetchone()[0]
print(f'\n[4] Sample ID: {sample_id}')

# Check if it exists in matching
c.execute('SELECT COUNT(*) FROM ofertas_esco_matching WHERE id_oferta = ?', (str(sample_id),))
as_str = c.fetchone()[0]
c.execute('SELECT COUNT(*) FROM ofertas_esco_matching WHERE id_oferta = ?', (sample_id,))
as_int = c.fetchone()[0]
print(f'  En matching como STRING: {as_str}')
print(f'  En matching como INT: {as_int}')

# 5. Try different JOIN approaches
print('\n[5] Probando diferentes JOINs:')

# Direct join
c.execute('''
    SELECT COUNT(*) FROM ofertas_esco_matching m
    JOIN validacion_v7 v ON m.id_oferta = v.id_oferta
    WHERE v.nlp_version = '8.1.0'
''')
print(f'  JOIN directo: {c.fetchone()[0]}')

# Cast to text
c.execute('''
    SELECT COUNT(*) FROM ofertas_esco_matching m
    JOIN validacion_v7 v ON m.id_oferta = CAST(v.id_oferta AS TEXT)
    WHERE v.nlp_version = '8.1.0'
''')
print(f'  JOIN con CAST a TEXT: {c.fetchone()[0]}')

# Cast both to text
c.execute('''
    SELECT COUNT(*) FROM ofertas_esco_matching m
    JOIN validacion_v7 v ON CAST(m.id_oferta AS TEXT) = CAST(v.id_oferta AS TEXT)
    WHERE v.nlp_version = '8.1.0'
''')
print(f'  JOIN con CAST ambos: {c.fetchone()[0]}')

# 6. Ver un ejemplo de matching de v8.1
print('\n[6] Ejemplo de matching para v8.1:')
c.execute('''
    SELECT m.id_oferta, m.score_final_ponderado, m.score_descripcion
    FROM ofertas_esco_matching m
    JOIN validacion_v7 v ON CAST(m.id_oferta AS TEXT) = CAST(v.id_oferta AS TEXT)
    WHERE v.nlp_version = '8.1.0'
    LIMIT 5
''')
for r in c.fetchall():
    print(f'  ID: {r[0]}, Score: {r[1]:.3f}, Desc: {r[2]:.3f}')

conn.close()
