# -*- coding: utf-8 -*-
import sqlite3
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

conn = sqlite3.connect('database/bumeran_scraping.db')
conn.row_factory = sqlite3.Row

# Datos NLP
cur = conn.execute('SELECT * FROM ofertas_nlp WHERE id_oferta = ?', ('2165301',))
row = cur.fetchone()
if row:
    print('=== DATOS NLP ===')
    print(f"titulo_limpio: {row['titulo_limpio']}")
    print(f"area_funcional: {row['area_funcional']}")
    print(f"nivel_seniority: {row['nivel_seniority']}")
    tareas = row['tareas_explicitas']
    print(f"tareas_explicitas: {tareas[:500] if tareas else None}")

# Datos scraping
cur = conn.execute('SELECT titulo, descripcion FROM ofertas WHERE id_oferta = ?', ('2165301',))
row2 = cur.fetchone()
if row2:
    print()
    print('=== DATOS SCRAPING ===')
    print(f"titulo_original: {row2[0]}")
    print()
    print('descripcion:')
    desc = row2[1]
    print(desc[:2000] if desc else None)

conn.close()
